"""Supported same-host SQLite Agent Execution Dispatch Admission store.

This backend is deliberately narrow.  One trusted configuration pins one
absolute local database path, authorization domain, ledger instance, and
positive generation.  Operational calls never create, migrate, repair,
reactivate, or fall back to another authority store.

Every new Admission commits one immutable keys-only Dispatch Intent in the
same transaction. Explicit forward migration classifies existing Admissions
as immutable legacy history; it never activates historical work.

Construction consumes one package-internal owner capability bound to that
exact identity.  Provisioning and migration consume a distinct one-use
administrative capability; neither access form is caller-supplied authority.

The durability claim applies only while every same-host consumer uses the
same correctly owned active ledger on trusted local storage.  A database can
record that it is fenced, but database-contained metadata cannot detect a
manually substituted stale active copy or prevent two copied active ledgers.
There is no same-domain restore/reactivation path in AIO-047.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from engineering_orchestration._sqlite_admission_migrations import (
    MIGRATIONS,
    SCHEMA_VERSION,
)
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
    validate_agent_execution_dispatch_admission,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    AgentExecutionDispatchAdmissionStoreAdministrationResult,
    AgentExecutionDispatchAdmissionClock,
    AgentExecutionDispatchAdmissionStoreResult,
    _claim_store_access,
    _open_admission_request,
    _open_authoritative_lookup_request,
    _open_guarded_history_request,
    _open_revocation_request,
    make_agent_execution_dispatch_admission_store_administration_result,
)
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    validate_agent_operation_tool_binding,
)


MINIMUM_SQLITE_VERSION = (3, 37, 0)
SQLITE_APPLICATION_ID = 0x41494F47
STORE_ID = "engineering_orchestration.agent_execution_dispatch_admission.sqlite"
MIGRATION_PACKAGE = "engineering_orchestration._sqlite_admission_migrations"
DEFAULT_BUSY_TIMEOUT_MS = 5_000
_DECISION_TIME = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:"
    r"[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)

__all__ = (
    "DEFAULT_BUSY_TIMEOUT_MS",
    "MINIMUM_SQLITE_VERSION",
    "SqliteAdmissionStoreConfigurationError",
    "SqliteAdmissionStoreIncompatibleSchemaError",
    "SqliteAdmissionStoreIntegrityError",
    "SqliteAdmissionStoreSettings",
    "SqliteAgentExecutionDispatchAdmissionStore",
    "SqliteAgentExecutionDispatchAdmissionStoreConfiguration",
)


class SqliteAdmissionStoreError(RuntimeError):
    """Base fail-closed local Admission-store error."""


class SqliteAdmissionStoreConfigurationError(SqliteAdmissionStoreError):
    """Trusted store configuration is invalid or unsupported."""


class SqliteAdmissionStoreIntegrityError(SqliteAdmissionStoreError):
    """Authoritative schema, metadata, or payload integrity failed."""


class SqliteAdmissionStoreIncompatibleSchemaError(SqliteAdmissionStoreError):
    """The configured ledger schema cannot be opened by this version."""


class _CommitUnknown(SqliteAdmissionStoreError):
    """A failure occurred at or after a SQLite COMMIT attempt."""


SqliteAdmissionStoreAdministrationOutcome = (
    AgentExecutionDispatchAdmissionStoreAdministrationOutcome
)
SqliteAdmissionStoreAdministrationResult = (
    AgentExecutionDispatchAdmissionStoreAdministrationResult
)


def _admin_result(
    outcome: AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    detail: str | None = None,
) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
    return make_agent_execution_dispatch_admission_store_administration_result(
        outcome,
        detail=detail,
    )


@dataclass(frozen=True)
class SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
    """Trusted immutable mapping to exactly one local authority ledger."""

    database_path: Path
    authorization_domain_id: str
    ledger_instance_id: str
    domain_generation: int
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS


@dataclass(frozen=True)
class SqliteAdmissionStoreSettings:
    """Verified operational SQLite profile."""

    sqlite_version: str
    journal_mode: str
    synchronous: int
    foreign_keys: int
    locking_mode: str
    busy_timeout_ms: int
    isolation_level: None
    write_begin: str


@dataclass(frozen=True)
class _LedgerMetadata:
    schema_version: int
    schema_manifest_id: str
    activation_state: str
    migration_state: str
    decision_time: str | None
    decision_time_key: int | None


@dataclass(frozen=True)
class _DispatchClassification:
    """Private immutable history reference, never present execution authority."""

    admission: AgentExecutionDispatchAdmission
    kind: str


@dataclass(frozen=True)
class _RevocationRecord:
    grant: AgentExecutionAuthorizationGrant
    revoker_kind: str
    revoker_id: str
    revocation_time: str


_DISPATCH_TOKEN = re.compile(r"^[0-9a-f]{64}$")
_DISPATCH_REQUEST_AUTHORITY = object()
_DISPATCH_LEASE_US = 30_000_000
_DISPATCH_MAX_INTEGER = 9_223_372_036_854_775_807
_DISPATCH_MAX_TIME_KEY = 315_537_897_599_999_999
_DISPATCH_ID_COLUMNS = (
    "authorization_domain_id", "issuer_kind", "issuer_id", "grant_id",
)
_DISPATCH_CLAIMS = "agent_execution_dispatch_claims"
_DISPATCH_RENEWALS = "agent_execution_dispatch_renewals"


def _dispatch_token(value: object) -> str:
    if type(value) is not str or _DISPATCH_TOKEN.fullmatch(value) is None:
        raise ValueError("attempt/executor identity must be exact lowercase 64-hex text")
    return value


def _dispatch_identity(value: object) -> tuple[str, str, str, str]:
    if (type(value) is not tuple or len(value) != 4
            or any(type(part) is not str or not part for part in value)
            or value[1] not in ("human", "policy")):
        raise ValueError("Dispatch identity must be the exact four-part Grant composite")
    return value


def _dispatch_integer(value: object) -> int:
    if type(value) is not int or not 1 <= value <= _DISPATCH_MAX_INTEGER:
        raise ValueError("generation/sequence must be an exact positive signed-64 integer")
    return value


def _next_dispatch_integer(previous: int) -> int:
    if type(previous) is not int or not 0 <= previous < _DISPATCH_MAX_INTEGER:
        raise OverflowError("Dispatch generation/sequence is exhausted")
    return previous + 1


def _dispatch_expiry(now: datetime) -> tuple[str, int]:
    expiry = now + timedelta(microseconds=_DISPATCH_LEASE_US)
    _, text, key = _canonical_decision_time(expiry)
    if key > _DISPATCH_MAX_TIME_KEY:
        raise OverflowError("Dispatch Lease time is exhausted")
    return text, key


@dataclass(frozen=True)
class _DispatchClaim:
    claim_id: str
    identity: tuple[str, str, str, str]
    executor_instance_id: str
    lease_generation: int
    acquired_at: str
    acquired_at_key: int
    lease_until: str
    lease_until_key: int


@dataclass(frozen=True)
class _DispatchRenewal:
    renewal_id: str
    claim_id: str
    identity: tuple[str, str, str, str]
    executor_instance_id: str
    lease_generation: int
    renewal_sequence: int
    renewed_at: str
    renewed_at_key: int
    lease_until: str
    lease_until_key: int


@dataclass(frozen=True)
class _DispatchResult:
    """Private immutable point-in-time evidence; never invocation permission."""

    outcome: str
    retry: str
    claim: _DispatchClaim | None = None
    renewal: _DispatchRenewal | None = None
    renewals: tuple[_DispatchRenewal, ...] = ()
    effective_lease_until: str | None = None
    history_only: bool = False
    detail: str = ""


def _dispatch_result(outcome: str, **values: object) -> _DispatchResult:
    retry = (
        "retry_exact_request" if outcome in ("commit_unknown", "storage_busy", "storage_unavailable")
        else "reconcile_history" if outcome == "ownership_lost"
        else "retry_after_remediation" if outcome in (
            "incompatible_schema", "integrity_failure", "clock_failure", "clock_regression",
            "generation_exhausted", "sequence_exhausted",
        )
        else "reevaluate" if outcome in ("empty", "temporarily_unavailable", "nonextending")
        else "no_retry_needed" if outcome in (
            "newly_claimed", "newly_renewed", "existing_claim_history",
            "existing_renewal_history", "claim_history", "current_claim",
        )
        else "do_not_retry_same_request"
    )
    return _DispatchResult(outcome, retry, **values)


class _DispatchRequest:
    """Internally minted, immutable, nonserializable owned-operation request."""

    __slots__ = ("operation", "session", "store", "capability", "claim_id",
                 "renewal_id", "identity", "generation", "mode", "_authority")

    def __new__(cls):
        raise TypeError("Dispatch requests are privately minted")

    def __setattr__(self, name, value):
        raise TypeError("Dispatch requests are immutable")

    def __reduce_ex__(self, protocol):
        raise TypeError("Dispatch requests cannot be serialized")

    def __copy__(self):
        raise TypeError("Dispatch requests cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Dispatch requests cannot be copied")


def _mint_dispatch_request(operation, session, store, *, capability=None,
                           claim_id=None, renewal_id=None, identity=None,
                           generation=None, mode=None):
    request = object.__new__(_DispatchRequest)
    for name, value in locals().copy().items():
        if name != "request":
            object.__setattr__(request, name, value)
    object.__setattr__(request, "_authority", _DISPATCH_REQUEST_AUTHORITY)
    return request


def _open_dispatch_request(request, store, operation):
    if (type(request) is not _DispatchRequest
            or getattr(request, "_authority", None) is not _DISPATCH_REQUEST_AUTHORITY
            or request.operation != operation or request.store is not store):
        raise ValueError("invalid or rebound private Dispatch request")
    # Local provider/session checks stay behind the private local adapter.
    from engineering_orchestration._local_dispatch_claim_lease import (
        _validate_owned_dispatch_context, _validate_executor,
    )
    _validate_owned_dispatch_context(request.session, store)
    _dispatch_token(request.claim_id)
    if operation == "query" and request.mode == "history":
        if any(value is not None for value in (
                request.capability, request.renewal_id, request.identity, request.generation)):
            raise ValueError("history request contains only claim_id")
        return request, None
    executor_id = _validate_executor(request.capability, request.session)
    if operation == "claim":
        if any(value is not None for value in (
                request.renewal_id, request.identity, request.generation, request.mode)):
            raise ValueError("Claim request accepts no overrides")
    else:
        _dispatch_identity(request.identity)
        _dispatch_integer(request.generation)
        if request.identity[0] != store.configuration.authorization_domain_id:
            raise ValueError("Dispatch request domain mismatch")
        if operation == "renew":
            _dispatch_token(request.renewal_id)
            if request.mode is not None:
                raise ValueError("Renewal accepts no query mode")
        elif request.mode != "current" or request.renewal_id is not None:
            raise ValueError("unknown Dispatch query mode")
    return request, executor_id


def _result(outcome: str, *, admission=None, detail: str = ""):
    """Construct a canonical protocol result without duplicating retry policy."""

    from engineering_orchestration.agent_execution_dispatch_admission_store import (
        AgentExecutionDispatchAdmissionStoreOutcome,
        make_agent_execution_dispatch_admission_store_result,
    )

    return make_agent_execution_dispatch_admission_store_result(
        AgentExecutionDispatchAdmissionStoreOutcome(outcome),
        admission=admission,
        detail=detail,
    )


def _grant_identity(
    grant: AgentExecutionAuthorizationGrant,
) -> tuple[str, str, str, str]:
    return (
        grant.authorization_domain_id,
        grant.issuer_kind,
        grant.issuer_id,
        grant.grant_id,
    )


def _contract_document(contract: AgentExecutionContract) -> dict[str, str]:
    return {
        "task_id": contract.task_id,
        "workflow_id": contract.workflow_id,
        "stage_id": contract.stage_id,
        "role_id": contract.role_id,
        "actor_id": contract.actor_id,
        "runtime_option_id": contract.runtime_option_id,
        "option_id": contract.option_id,
        "environment_id": contract.environment_id,
        "operation_id": contract.operation_id,
        "resource": contract.resource,
        "execution_mode": contract.execution_mode,
    }


def _run_document(run: AgentExecutionRun) -> dict[str, object]:
    return {"run_id": run.run_id, "contract": _contract_document(run.contract)}


def _grant_document(grant: AgentExecutionAuthorizationGrant) -> dict[str, object]:
    return {
        "grant_id": grant.grant_id,
        "run": _run_document(grant.run),
        "authorization_domain_id": grant.authorization_domain_id,
        "issuer_kind": grant.issuer_kind,
        "issuer_id": grant.issuer_id,
        "provenance_reference": grant.provenance_reference,
        "issued_at": grant.issued_at,
        "expires_at": grant.expires_at,
    }


def _binding_document(binding: AgentOperationToolBinding) -> dict[str, object]:
    return {"run": _run_document(binding.run), "tool_id": binding.tool_id}


def _admission_document(
    admission: AgentExecutionDispatchAdmission,
) -> dict[str, object]:
    return {
        "grant": _grant_document(admission.grant),
        "tool_binding": _binding_document(admission.tool_binding),
        "decision_time": admission.decision_time,
    }


def _canonical_json(document: object) -> str:
    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON token is prohibited: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_canonical_json(text: object) -> object:
    if type(text) is not str:
        raise ValueError("stored JSON must be exact text")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError("stored JSON is malformed") from error
    if _canonical_json(value) != text:
        raise ValueError("stored JSON is not canonical")
    return value


def _require_object(
    value: object,
    keys: frozenset[str],
    category: str,
) -> dict[str, object]:
    if type(value) is not dict or frozenset(value) != keys:
        raise ValueError(f"stored {category} object shape is not canonical")
    return value


_CONTRACT_KEYS = frozenset(
    (
        "task_id",
        "workflow_id",
        "stage_id",
        "role_id",
        "actor_id",
        "runtime_option_id",
        "option_id",
        "environment_id",
        "operation_id",
        "resource",
        "execution_mode",
    )
)
_RUN_KEYS = frozenset(("run_id", "contract"))
_GRANT_KEYS = frozenset(
    (
        "grant_id",
        "run",
        "authorization_domain_id",
        "issuer_kind",
        "issuer_id",
        "provenance_reference",
        "issued_at",
        "expires_at",
    )
)
_BINDING_KEYS = frozenset(("run", "tool_id"))
_ADMISSION_KEYS = frozenset(("grant", "tool_binding", "decision_time"))


def _decode_contract(document: object) -> AgentExecutionContract:
    value = _require_object(document, _CONTRACT_KEYS, "Contract")
    return AgentExecutionContract(**value)  # type: ignore[arg-type]


def _decode_run(document: object) -> AgentExecutionRun:
    value = _require_object(document, _RUN_KEYS, "Run")
    return AgentExecutionRun(
        run_id=value["run_id"],  # type: ignore[arg-type]
        contract=_decode_contract(value["contract"]),
    )


def _decode_grant_document(document: object) -> AgentExecutionAuthorizationGrant:
    value = _require_object(document, _GRANT_KEYS, "Grant")
    grant = AgentExecutionAuthorizationGrant(
        grant_id=value["grant_id"],  # type: ignore[arg-type]
        run=_decode_run(value["run"]),
        authorization_domain_id=value["authorization_domain_id"],  # type: ignore[arg-type]
        issuer_kind=value["issuer_kind"],  # type: ignore[arg-type]
        issuer_id=value["issuer_id"],  # type: ignore[arg-type]
        provenance_reference=value["provenance_reference"],  # type: ignore[arg-type]
        issued_at=value["issued_at"],  # type: ignore[arg-type]
        expires_at=value["expires_at"],  # type: ignore[arg-type]
    )
    if not validate_agent_execution_authorization_grant(grant).valid:
        raise ValueError("stored Grant is intrinsically invalid")
    return grant


def _decode_binding_document(document: object) -> AgentOperationToolBinding:
    value = _require_object(document, _BINDING_KEYS, "Tool Binding")
    binding = AgentOperationToolBinding(
        run=_decode_run(value["run"]),
        tool_id=value["tool_id"],  # type: ignore[arg-type]
    )
    if not validate_agent_operation_tool_binding(binding).valid:
        raise ValueError("stored Tool Binding is intrinsically invalid")
    return binding


def _encode_grant(grant: AgentExecutionAuthorizationGrant) -> str:
    if not validate_agent_execution_authorization_grant(grant).valid:
        raise ValueError("cannot encode an invalid Grant")
    return _canonical_json(_grant_document(grant))


def _encode_binding(binding: AgentOperationToolBinding) -> str:
    if not validate_agent_operation_tool_binding(binding).valid:
        raise ValueError("cannot encode an invalid Tool Binding")
    return _canonical_json(_binding_document(binding))


def _encode_admission(admission: AgentExecutionDispatchAdmission) -> str:
    if not validate_agent_execution_dispatch_admission(admission).valid:
        raise ValueError("cannot encode an invalid Admission")
    return _canonical_json(_admission_document(admission))


def _decode_grant(text: object) -> AgentExecutionAuthorizationGrant:
    document = _load_canonical_json(text)
    grant = _decode_grant_document(document)
    if _encode_grant(grant) != text:
        raise ValueError("stored Grant did not round-trip canonically")
    return grant


def _decode_binding(text: object) -> AgentOperationToolBinding:
    document = _load_canonical_json(text)
    binding = _decode_binding_document(document)
    if _encode_binding(binding) != text:
        raise ValueError("stored Tool Binding did not round-trip canonically")
    return binding


def _decode_admission(text: object) -> AgentExecutionDispatchAdmission:
    value = _require_object(
        _load_canonical_json(text),
        _ADMISSION_KEYS,
        "Admission",
    )
    admission = AgentExecutionDispatchAdmission(
        grant=_decode_grant_document(value["grant"]),
        tool_binding=_decode_binding_document(value["tool_binding"]),
        decision_time=value["decision_time"],  # type: ignore[arg-type]
    )
    if not validate_agent_execution_dispatch_admission(admission).valid:
        raise ValueError("stored Admission is intrinsically invalid")
    if _encode_admission(admission) != text:
        raise ValueError("stored Admission did not round-trip canonically")
    return admission


def _canonical_decision_time(value: object) -> tuple[datetime, str, int]:
    if type(value) is not datetime:
        raise ValueError("authority clock must return an exact datetime")
    offset = value.utcoffset() if value.tzinfo is not None else None
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("authority clock must return a UTC-aware instant")
    utc_value = value.astimezone(timezone.utc)
    text = (
        f"{utc_value.year:04d}-{utc_value.month:02d}-{utc_value.day:02d}T"
        f"{utc_value.hour:02d}:{utc_value.minute:02d}:"
        f"{utc_value.second:02d}.{utc_value.microsecond:06d}Z"
    )
    seconds = (
        (utc_value.toordinal() - 1) * 86_400
        + utc_value.hour * 3_600
        + utc_value.minute * 60
        + utc_value.second
    )
    return utc_value, text, seconds * 1_000_000 + utc_value.microsecond


def _parse_decision_time(value: object) -> tuple[datetime, int]:
    if type(value) is not str or _DECISION_TIME.fullmatch(value) is None:
        raise ValueError("stored decision time is not canonical")
    try:
        instant = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError("stored decision time is invalid") from error
    parsed, canonical, key = _canonical_decision_time(instant)
    if canonical != value:
        raise ValueError("stored decision time is not canonical")
    return parsed, key


def _parse_grant_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError) as error:
        raise ValueError("validated Grant timestamp could not be parsed") from error


def _migration_bytes() -> tuple[tuple[int, str, str, bytes], ...]:
    loaded: list[tuple[int, str, str, bytes]] = []
    package = files(MIGRATION_PACKAGE)
    for migration in MIGRATIONS:
        try:
            data = package.joinpath(migration.resource_name).read_bytes()
        except (FileNotFoundError, ModuleNotFoundError, OSError) as error:
            raise SqliteAdmissionStoreIncompatibleSchemaError(
                f"packaged migration is unavailable: {migration.resource_name}"
            ) from error
        if b"\r" in data:
            raise SqliteAdmissionStoreIncompatibleSchemaError(
                "packaged migration is not canonical UTF-8/LF"
            )
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise SqliteAdmissionStoreIncompatibleSchemaError(
                "packaged migration is not canonical UTF-8"
            ) from error
        digest = hashlib.sha256(data).hexdigest()
        if digest != migration.sha256:
            raise SqliteAdmissionStoreIncompatibleSchemaError(
                f"packaged migration checksum mismatch: {migration.resource_name}"
            )
        loaded.append(
            (
                migration.migration_id,
                migration.resource_name,
                migration.sha256,
                data,
            )
        )
    if tuple(item[0] for item in loaded) != tuple(range(1, SCHEMA_VERSION + 1)):
        raise SqliteAdmissionStoreIncompatibleSchemaError(
            "packaged migration manifest is not contiguous"
        )
    return tuple(loaded)


def _schema_manifest_id(schema_version: int = SCHEMA_VERSION) -> str:
    migrations = _migration_bytes()
    if type(schema_version) is not int or not 1 <= schema_version <= SCHEMA_VERSION:
        raise SqliteAdmissionStoreIncompatibleSchemaError(
            "unsupported schema manifest prefix"
        )
    material = "\n".join(
        f"{migration_id}:{name}:{checksum}"
        for migration_id, name, checksum, _ in migrations[:schema_version]
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _sql_statements(data: bytes) -> tuple[str, ...]:
    text = data.decode("utf-8")
    statements: list[str] = []
    pending = ""
    for line in text.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            if statement:
                statements.append(statement)
            pending = ""
    if pending.strip():
        raise SqliteAdmissionStoreIncompatibleSchemaError(
            "packaged migration contains an incomplete SQL statement"
        )
    return tuple(statements)


def _is_busy(error: BaseException) -> bool:
    code = getattr(error, "sqlite_errorcode", None)
    if code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
        return True
    message = str(error).lower()
    return "locked" in message or "busy" in message


def _safe_rollback(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _commit(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("COMMIT")
    except BaseException as error:
        raise _CommitUnknown("SQLite COMMIT result is unknown") from error


def _normalized_path(path: Path, *, require_file: bool) -> Path:
    if not isinstance(path, Path) or not path.is_absolute():
        raise SqliteAdmissionStoreConfigurationError(
            "database_path must be an exact absolute pathlib.Path"
        )
    raw = str(path)
    if raw.startswith("\\\\") or raw.startswith("//"):
        raise SqliteAdmissionStoreConfigurationError(
            "UNC and network-share paths are unsupported"
        )
    parent = path.parent
    try:
        resolved_parent = parent.resolve(strict=True)
    except OSError as error:
        raise SqliteAdmissionStoreConfigurationError(
            "database parent must be an existing local directory"
        ) from error
    if not resolved_parent.is_dir():
        raise SqliteAdmissionStoreConfigurationError(
            "database parent must be an existing directory"
        )
    for component in (parent, *parent.parents):
        is_junction = getattr(component, "is_junction", lambda: False)
        if component.is_symlink() or is_junction():
            raise SqliteAdmissionStoreConfigurationError(
                "symlink or junction path aliases are unsupported"
            )
    if require_file:
        try:
            resolved_file = path.resolve(strict=True)
        except OSError as error:
            raise SqliteAdmissionStoreConfigurationError(
                "configured Admission ledger does not exist"
            ) from error
        if not resolved_file.is_file():
            raise SqliteAdmissionStoreConfigurationError(
                "configured Admission ledger is not a regular file"
            )
        file_is_junction = getattr(path, "is_junction", lambda: False)
        if path.is_symlink() or file_is_junction():
            raise SqliteAdmissionStoreConfigurationError(
                "symlink or junction database aliases are unsupported"
            )
    return path


def _validate_configuration(
    configuration: object,
    *,
    require_file: bool,
) -> SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
    if type(configuration) is not SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
        raise SqliteAdmissionStoreConfigurationError(
            "configuration must be the exact SQLite Admission-store type"
        )
    _normalized_path(configuration.database_path, require_file=require_file)
    if (
        type(configuration.authorization_domain_id) is not str
        or not configuration.authorization_domain_id
        or type(configuration.ledger_instance_id) is not str
        or not configuration.ledger_instance_id
        or type(configuration.domain_generation) is not int
        or configuration.domain_generation <= 0
        or type(configuration.busy_timeout_ms) is not int
        or configuration.busy_timeout_ms < 0
    ):
        raise SqliteAdmissionStoreConfigurationError(
            "domain, ledger instance, generation, or busy timeout is invalid"
        )
    if sqlite3.sqlite_version_info < MINIMUM_SQLITE_VERSION:
        raise SqliteAdmissionStoreConfigurationError(
            "SQLite 3.37.0 or newer with STRICT tables is required"
        )
    return configuration


def _claim_configuration_access(
    configuration: object,
    access: object,
    *,
    administrative: bool,
) -> None:
    """Consume exact-identity access before any configured path is touched."""

    if type(configuration) is not SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
        raise SqliteAdmissionStoreConfigurationError(
            "configuration must be the exact SQLite Admission-store type"
        )
    try:
        _claim_store_access(
            access,
            configuration.authorization_domain_id,
            configuration.ledger_instance_id,
            configuration.domain_generation,
            administrative=administrative,
        )
    except (TypeError, ValueError) as error:
        raise SqliteAdmissionStoreConfigurationError(str(error)) from error


_EXPECTED_SCHEMA_FINGERPRINTS = {
    1: "de080810b1d644dacf53e6bf79cbbd01343344904397a91c6dd483bd48dfad46",
    2: "cce9d5c375da37c40eb6a73458f519f2840192500fb64ce1a20126383d2944e3",
    3: "8fb9c0473441babaaee7b322aa010a46f0481a6c7513bd1a0fd9e01c0d6009b7",
}
_EXPECTED_SCHEMA_FINGERPRINT = _EXPECTED_SCHEMA_FINGERPRINTS[SCHEMA_VERSION]


def _schema_fingerprint(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE substr(name, 1, 7) <> 'sqlite_'
        ORDER BY type COLLATE BINARY, name COLLATE BINARY
        """
    ).fetchall()
    material = _canonical_json(
        [
            [row["type"], row["name"], row["tbl_name"], row["sql"]]
            for row in rows
        ]
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


class SqliteAgentExecutionDispatchAdmissionStore:
    """One pinned, authoritative local Admission ledger.

    The object implements the backend-neutral authority-internal store
    protocol.  Request authority is minted only by the trusted coordinator;
    Store access is minted only by trusted package composition.  This class
    never authenticates arbitrary serialized values itself.
    """

    def __init__(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
        access: object,
    ) -> None:
        self._initialize_owned(
            configuration,
            clock=clock,
            access=access,
            allow_fenced=False,
            administrative=False,
        )

    @classmethod
    def _open_for_ownership(
        cls,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
        access: object,
        allow_fenced: bool = False,
        administrative: bool = False,
    ) -> SqliteAgentExecutionDispatchAdmissionStore:
        """Open with exact owner operational/admin access for recovery work."""

        if type(allow_fenced) is not bool or type(administrative) is not bool:
            raise SqliteAdmissionStoreConfigurationError(
                "allow_fenced and administrative must be exact booleans"
            )
        store = cls.__new__(cls)
        store._initialize_owned(
            configuration,
            clock=clock,
            access=access,
            allow_fenced=allow_fenced,
            administrative=administrative,
        )
        return store

    def _initialize_owned(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
        access: object,
        allow_fenced: bool,
        administrative: bool,
    ) -> None:
        _claim_configuration_access(
            configuration,
            access,
            administrative=administrative,
        )
        self.configuration = _validate_configuration(
            configuration,
            require_file=True,
        )
        if not callable(getattr(clock, "now_utc", None)):
            raise SqliteAdmissionStoreConfigurationError(
                "clock must implement now_utc()"
            )
        self._clock = clock
        connection = self._open_existing(allow_fenced=allow_fenced)
        connection.close()

    @classmethod
    def provision(
        cls,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        access: object,
    ) -> SqliteAdmissionStoreAdministrationResult:
        """Explicitly create a new current-schema ledger exactly once."""

        try:
            _claim_configuration_access(
                configuration,
                access,
                administrative=True,
            )
            config = _validate_configuration(configuration, require_file=False)
            migrations = _migration_bytes()
        except SqliteAdmissionStoreConfigurationError as error:
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE,
                str(error),
            )
        except SqliteAdmissionStoreIncompatibleSchemaError as error:
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.MIGRATION_FAILURE,
                str(error),
            )

        path = config.database_path
        if path.exists():
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE,
                "provisioning refuses an existing database path",
            )

        connection: sqlite3.Connection | None = None
        created = False
        commit_attempted = False
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            created = True
            connection = sqlite3.connect(
                path.as_uri() + "?mode=rw",
                uri=True,
                timeout=config.busy_timeout_ms / 1_000,
                isolation_level=None,
            )
            cls._configure_connection(connection, config, establish_wal=True)
            connection.execute("BEGIN IMMEDIATE")
            for migration_id, resource_name, checksum, data in migrations:
                for statement in _sql_statements(data):
                    connection.execute(statement)
                connection.execute(
                    """
                    INSERT INTO admission_schema_migrations (
                        migration_id, resource_name, sha256
                    ) VALUES (?, ?, ?)
                    """,
                    (migration_id, resource_name, checksum),
                )
            connection.execute(
                """
                INSERT INTO admission_ledger_metadata (
                    singleton,
                    store_id,
                    application_id,
                    authorization_domain_id,
                    schema_version,
                    schema_manifest_id,
                    ledger_instance_id,
                    domain_generation,
                    activation_state,
                    migration_state,
                    revocation_state_complete,
                    last_decision_time,
                    last_decision_time_key
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, 'active', 'clean', 1, NULL, NULL)
                """,
                (
                    STORE_ID,
                    SQLITE_APPLICATION_ID,
                    config.authorization_domain_id,
                    SCHEMA_VERSION,
                    _schema_manifest_id(),
                    config.ledger_instance_id,
                    config.domain_generation,
                ),
            )
            connection.execute(f"PRAGMA application_id={SQLITE_APPLICATION_ID}")
            connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
            verifier = cls.__new__(cls)
            verifier.configuration = config
            verifier._clock = None
            verifier._verify_authoritative_connection(connection, allow_fenced=False)
            commit_attempted = True
            _commit(connection)
            connection.close()
            connection = None
            verifier = cls.__new__(cls)
            verifier.configuration = config
            verifier._clock = None
            verified = verifier._open_existing(allow_fenced=False)
            verified.close()
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.PROVISIONED
            )
        except _CommitUnknown as error:
            _safe_rollback(connection)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN,
                str(error),
            )
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted:
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN,
                    "provisioning failed at or after commit",
                )
            outcome = (
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_BUSY
                if _is_busy(error)
                else SqliteAdmissionStoreAdministrationOutcome.MIGRATION_FAILURE
            )
            return _admin_result(outcome, str(error))
        finally:
            if connection is not None:
                connection.close()
            if created and not commit_attempted:
                for candidate in (
                    path,
                    Path(str(path) + "-wal"),
                    Path(str(path) + "-shm"),
                ):
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass

    @classmethod
    def _administration_fault(cls, point: str) -> None:
        """Private inert fault seam for bounded administrative crash tests."""

    @classmethod
    def migrate(
        cls,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        access: object,
    ) -> SqliteAdmissionStoreAdministrationResult:
        """Explicit owned, quiescent forward migration of the exact bound ledger."""

        try:
            _claim_configuration_access(configuration, access, administrative=True)
            config = _validate_configuration(configuration, require_file=True)
            migrations = _migration_bytes()
        except SqliteAdmissionStoreConfigurationError as error:
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE, str(error)
            )
        except SqliteAdmissionStoreIncompatibleSchemaError as error:
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.MIGRATION_FAILURE, str(error)
            )

        connection: sqlite3.Connection | None = None
        commit_attempted = False
        try:
            connection = cls._connect_rw(config)
            cls._configure_connection(connection, config, establish_wal=False)
            verifier = cls.__new__(cls)
            verifier.configuration = config
            verifier._clock = None
            connection.execute("BEGIN")
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            verifier._verify_versioned_connection(
                connection, allow_fenced=False, schema_version=version
            )
            connection.execute("ROLLBACK")
            if version == SCHEMA_VERSION:
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.ALREADY_CURRENT
                )

            cls._administration_fault("migration.before_transaction")
            connection.execute("BEGIN EXCLUSIVE")
            cls._administration_fault("migration.after_begin")
            # Repeat all source checks after serialization, before dirty mutation.
            verifier._verify_versioned_connection(
                connection, allow_fenced=False, schema_version=version
            )
            connection.execute(
                "UPDATE admission_ledger_metadata SET migration_state='dirty' WHERE singleton=1"
            )
            cls._administration_fault("migration.after_dirty")
            for migration_id, resource_name, checksum, data in migrations:
                if migration_id <= version:
                    continue
                preserved = None
                if migration_id == 3:
                    preserved = tuple(
                        tuple(tuple(row) for row in connection.execute(
                            f"SELECT * FROM {table} ORDER BY authorization_domain_id,issuer_kind,issuer_id,grant_id"
                        ).fetchall()) for table in (
                            "agent_execution_dispatch_admissions", "agent_execution_grant_revocations",
                            "agent_execution_dispatch_intents", "legacy_admission_markers",
                        )
                    )
                for statement in _sql_statements(data):
                    backfill = statement.startswith("INSERT INTO legacy_admission_markers")
                    if backfill:
                        cls._administration_fault("migration.after_schema")
                    connection.execute(statement)
                    if backfill:
                        cls._administration_fault("migration.after_legacy_population")
                if migration_id == 2 and connection.execute(
                    "SELECT 1 FROM agent_execution_dispatch_intents LIMIT 1"
                ).fetchone() is not None:
                    raise SqliteAdmissionStoreIntegrityError(
                        "migration must not create historical Dispatch Intents"
                    )
                if migration_id == 3:
                    cls._administration_fault("migration3.after_schema")
                    after = tuple(
                        tuple(tuple(row) for row in connection.execute(
                            f"SELECT * FROM {table} ORDER BY authorization_domain_id,issuer_kind,issuer_id,grant_id"
                        ).fetchall()) for table in (
                            "agent_execution_dispatch_admissions", "agent_execution_grant_revocations",
                            "agent_execution_dispatch_intents", "legacy_admission_markers",
                        )
                    )
                    if after != preserved or any(connection.execute(
                            f"SELECT 1 FROM {table} LIMIT 1").fetchone() is not None
                            for table in (_DISPATCH_CLAIMS, _DISPATCH_RENEWALS)):
                        raise SqliteAdmissionStoreIntegrityError("migration 3 changed preserved history or backfilled Claims")
                # Audit the additive classification before publishing v2 metadata.
                source_keys = {
                    tuple(row) for row in connection.execute(
                        "SELECT authorization_domain_id, issuer_kind, issuer_id, grant_id "
                        "FROM agent_execution_dispatch_admissions"
                    ).fetchall()
                }
                verifier._verify_dispatch_classifications(connection, source_keys)
                if (
                    _schema_fingerprint(connection)
                    != _EXPECTED_SCHEMA_FINGERPRINTS[migration_id]
                ):
                    raise SqliteAdmissionStoreIntegrityError(
                        "destination DDL fingerprint disagrees before publication"
                    )
                connection.execute(
                    "INSERT INTO admission_schema_migrations VALUES (?, ?, ?)",
                    (migration_id, resource_name, checksum),
                )
                cls._administration_fault("migration.after_history_before_version")
                connection.execute(f"PRAGMA user_version={migration_id}")
                connection.execute(
                    """
                    UPDATE admission_ledger_metadata
                    SET schema_version=?, schema_manifest_id=?
                    WHERE singleton=1
                    """,
                    (migration_id, _schema_manifest_id(migration_id)),
                )
                cls._administration_fault("migration.after_version_publication")
            connection.execute(
                "UPDATE admission_ledger_metadata SET migration_state='clean' WHERE singleton=1"
            )
            cls._administration_fault("migration.after_clean_transition")
            verifier._verify_authoritative_connection(connection, allow_fenced=False)
            cls._administration_fault("migration.before_commit")
            commit_attempted = True
            _commit(connection)
            cls._administration_fault("migration.after_commit_before_response")
            connection.execute("BEGIN")
            verifier._verify_authoritative_connection(connection, allow_fenced=False)
            connection.execute("ROLLBACK")
            return _admin_result(SqliteAdmissionStoreAdministrationOutcome.MIGRATED)
        except _CommitUnknown as error:
            _safe_rollback(connection)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN, str(error)
            )
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted:
                outcome = SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN
            elif _is_busy(error):
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_BUSY
            elif isinstance(error, SqliteAdmissionStoreIntegrityError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INTEGRITY_FAILURE
            elif isinstance(error, SqliteAdmissionStoreIncompatibleSchemaError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA
            elif isinstance(error, SqliteAdmissionStoreConfigurationError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE
            else:
                outcome = SqliteAdmissionStoreAdministrationOutcome.MIGRATION_FAILURE
            return _admin_result(outcome, str(error))
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _connect_rw(
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    ) -> sqlite3.Connection:
        uri = configuration.database_path.as_uri() + "?mode=rw"
        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=configuration.busy_timeout_ms / 1_000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _configure_connection(
        connection: sqlite3.Connection,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        establish_wal: bool,
    ) -> SqliteAdmissionStoreSettings:
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={configuration.busy_timeout_ms}")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA locking_mode=NORMAL")
        if establish_wal:
            row = connection.execute("PRAGMA journal_mode=WAL").fetchone()
            if row is None or str(row[0]).lower() != "wal":
                raise SqliteAdmissionStoreConfigurationError(
                    "WAL mode could not be established"
                )
        connection.execute("PRAGMA synchronous=FULL")
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        locking_mode = str(connection.execute("PRAGMA locking_mode").fetchone()[0]).lower()
        busy_timeout = int(connection.execute("PRAGMA busy_timeout").fetchone()[0])
        if (
            journal_mode != "wal"
            or synchronous != 2
            or foreign_keys != 1
            or locking_mode != "normal"
            or busy_timeout != configuration.busy_timeout_ms
            or connection.isolation_level is not None
        ):
            raise SqliteAdmissionStoreConfigurationError(
                "required WAL/FULL/foreign-key/NORMAL/autocommit profile is absent"
            )
        return SqliteAdmissionStoreSettings(
            sqlite_version=sqlite3.sqlite_version,
            journal_mode=journal_mode,
            synchronous=synchronous,
            foreign_keys=foreign_keys,
            locking_mode=locking_mode,
            busy_timeout_ms=busy_timeout,
            isolation_level=None,
            write_begin="BEGIN IMMEDIATE",
        )

    def _open_existing(self, *, allow_fenced: bool) -> sqlite3.Connection:
        _validate_configuration(self.configuration, require_file=True)
        connection: sqlite3.Connection | None = None
        try:
            connection = self._connect_rw(self.configuration)
            self._configure_connection(
                connection,
                self.configuration,
                establish_wal=False,
            )
            # Verification must observe metadata, migration history, schema,
            # and every security payload from one WAL snapshot.  Autocommit
            # SELECTs could otherwise straddle a healthy concurrent append and
            # falsely report that the old watermark trails the new row.
            connection.execute("BEGIN")
            try:
                self._verify_authoritative_connection(
                    connection,
                    allow_fenced=allow_fenced,
                )
            except BaseException:
                _safe_rollback(connection)
                raise
            connection.execute("ROLLBACK")
            return connection
        except sqlite3.DatabaseError as error:
            if connection is not None:
                connection.close()
            if _is_busy(error):
                raise
            lowered = str(error).lower()
            if any(
                marker in lowered
                for marker in (
                    "unable to open",
                    "readonly database",
                    "disk i/o error",
                )
            ):
                raise SqliteAdmissionStoreConfigurationError(
                    "configured Admission ledger is unavailable"
                ) from error
            raise SqliteAdmissionStoreIntegrityError(
                "configured Admission ledger is corrupt or structurally invalid"
            ) from error
        except BaseException:
            if connection is not None:
                connection.close()
            raise

    def _verify_authoritative_connection(
        self,
        connection: sqlite3.Connection,
        *,
        allow_fenced: bool,
    ) -> _LedgerMetadata:
        """Operational verification accepts only the current schema."""

        return self._verify_versioned_connection(
            connection, allow_fenced=allow_fenced, schema_version=SCHEMA_VERSION
        )

    def _verify_versioned_connection(
        self,
        connection: sqlite3.Connection,
        *,
        allow_fenced: bool,
        schema_version: int,
    ) -> _LedgerMetadata:
        """Administration alone may verify an exact supported older prefix."""

        try:
            if (
                type(schema_version) is not int
                or schema_version not in _EXPECTED_SCHEMA_FINGERPRINTS
            ):
                raise SqliteAdmissionStoreIncompatibleSchemaError(
                    "unsupported Admission ledger schema; no downgrade or inference"
                )
            application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if application_id != SQLITE_APPLICATION_ID:
                raise SqliteAdmissionStoreIncompatibleSchemaError(
                    "SQLite application_id does not identify an Admission ledger"
                )
            if user_version != schema_version:
                direction = "newer" if user_version > schema_version else "older"
                raise SqliteAdmissionStoreIncompatibleSchemaError(
                    f"Admission ledger schema is {direction}; explicit migration is required"
                )
            if (
                _schema_fingerprint(connection)
                != _EXPECTED_SCHEMA_FINGERPRINTS[schema_version]
            ):
                raise SqliteAdmissionStoreIntegrityError(
                    "sqlite_schema object/DDL fingerprint mismatch"
                )
            integrity = connection.execute("PRAGMA integrity_check").fetchall()
            if len(integrity) != 1 or integrity[0][0] != "ok":
                raise SqliteAdmissionStoreIntegrityError(
                    "SQLite integrity_check failed"
                )
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise SqliteAdmissionStoreIntegrityError(
                    "SQLite foreign_key_check failed"
                )
            if schema_version == SCHEMA_VERSION:
                self._verify_migration_history(connection)
                metadata = self._verify_metadata(connection, allow_fenced=allow_fenced)
            else:
                self._verify_versioned_migration_history(connection, schema_version)
                metadata = self._verify_versioned_metadata(
                    connection, allow_fenced=allow_fenced, schema_version=schema_version
                )
            self._verify_all_payloads(connection, metadata)
            return metadata
        except (
            SqliteAdmissionStoreIncompatibleSchemaError,
            SqliteAdmissionStoreIntegrityError,
        ):
            raise
        except (sqlite3.Error, KeyError, TypeError, ValueError) as error:
            raise SqliteAdmissionStoreIntegrityError(
                "Admission ledger verification failed closed"
            ) from error

    @staticmethod
    def _verify_migration_history(connection: sqlite3.Connection) -> None:
        SqliteAgentExecutionDispatchAdmissionStore._verify_versioned_migration_history(
            connection, SCHEMA_VERSION
        )

    @staticmethod
    def _verify_versioned_migration_history(
        connection: sqlite3.Connection, schema_version: int
    ) -> None:
        rows = connection.execute(
            """
            SELECT migration_id, resource_name, sha256
            FROM admission_schema_migrations
            ORDER BY migration_id
            """
        ).fetchall()
        expected = tuple(
            (migration_id, name, checksum)
            for migration_id, name, checksum, _ in _migration_bytes()[:schema_version]
        )
        actual = tuple(
            (row["migration_id"], row["resource_name"], row["sha256"])
            for row in rows
        )
        if actual != expected:
            raise SqliteAdmissionStoreIntegrityError(
                "migration history is missing, noncontiguous, or checksum-mismatched"
            )

    def _verify_metadata(
        self,
        connection: sqlite3.Connection,
        *,
        allow_fenced: bool,
    ) -> _LedgerMetadata:
        return self._verify_versioned_metadata(
            connection, allow_fenced=allow_fenced, schema_version=SCHEMA_VERSION
        )

    def _verify_versioned_metadata(
        self,
        connection: sqlite3.Connection,
        *,
        allow_fenced: bool,
        schema_version: int,
    ) -> _LedgerMetadata:
        rows = connection.execute(
            "SELECT * FROM admission_ledger_metadata"
        ).fetchall()
        if len(rows) != 1:
            raise SqliteAdmissionStoreIntegrityError(
                "Admission ledger metadata is not singleton"
            )
        row = rows[0]
        expected = self.configuration
        if (
            type(row["singleton"]) is not int
            or row["singleton"] != 1
            or row["store_id"] != STORE_ID
            or row["application_id"] != SQLITE_APPLICATION_ID
            or row["authorization_domain_id"] != expected.authorization_domain_id
            or row["schema_version"] != schema_version
            or row["schema_manifest_id"] != _schema_manifest_id(schema_version)
            or row["ledger_instance_id"] != expected.ledger_instance_id
            or row["domain_generation"] != expected.domain_generation
            or row["migration_state"] != "clean"
            or row["revocation_state_complete"] != 1
        ):
            raise SqliteAdmissionStoreIntegrityError(
                "Admission ledger metadata is malformed or mismatched"
            )
        activation_state = row["activation_state"]
        if activation_state not in ("active", "fenced"):
            raise SqliteAdmissionStoreIntegrityError(
                "Admission ledger activation state is invalid"
            )
        if activation_state != "active" and not allow_fenced:
            raise SqliteAdmissionStoreIncompatibleSchemaError(
                "fenced Admission ledger is permanently non-authoritative"
            )
        decision_time = row["last_decision_time"]
        decision_key = row["last_decision_time_key"]
        if decision_time is None and decision_key is None:
            pass
        elif type(decision_time) is str and type(decision_key) is int:
            _, parsed_key = _parse_decision_time(decision_time)
            if parsed_key != decision_key:
                raise SqliteAdmissionStoreIntegrityError(
                    "Admission ledger watermark text/key mismatch"
                )
        else:
            raise SqliteAdmissionStoreIntegrityError(
                "Admission ledger watermark is incoherent"
            )
        return _LedgerMetadata(
            schema_version=row["schema_version"],
            schema_manifest_id=row["schema_manifest_id"],
            activation_state=activation_state,
            migration_state=row["migration_state"],
            decision_time=decision_time,
            decision_time_key=decision_key,
        )

    @staticmethod
    def _admission_from_row(row: sqlite3.Row) -> AgentExecutionDispatchAdmission:
        try:
            grant = _decode_grant(row["grant_json"])
            binding = _decode_binding(row["binding_json"])
            admission = _decode_admission(row["admission_json"])
            _, decision_key = _parse_decision_time(row["decision_time"])
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise SqliteAdmissionStoreIntegrityError(
                "stored Admission payload cannot be decoded canonically"
            ) from error
        indexed_identity = (
            row["authorization_domain_id"],
            row["issuer_kind"],
            row["issuer_id"],
            row["grant_id"],
        )
        if (
            grant != admission.grant
            or binding != admission.tool_binding
            or _grant_identity(grant) != indexed_identity
            or grant.run != binding.run
            or grant.run.run_id != row["run_id"]
            or admission.decision_time != row["decision_time"]
            or type(row["decision_time_key"]) is not int
            or decision_key != row["decision_time_key"]
        ):
            raise SqliteAdmissionStoreIntegrityError(
                "stored Admission indexes or duplicate payloads disagree"
            )
        return admission

    @staticmethod
    def _revocation_from_row(row: sqlite3.Row) -> _RevocationRecord:
        try:
            grant = _decode_grant(row["grant_json"])
            _, decision_key = _parse_decision_time(row["revocation_time"])
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise SqliteAdmissionStoreIntegrityError(
                "stored revocation payload cannot be decoded canonically"
            ) from error
        indexed_identity = (
            row["authorization_domain_id"],
            row["issuer_kind"],
            row["issuer_id"],
            row["grant_id"],
        )
        if (
            _grant_identity(grant) != indexed_identity
            or grant.run.run_id != row["run_id"]
            or grant.issuer_kind != row["revoker_kind"]
            or grant.issuer_id != row["revoker_id"]
            or type(row["revocation_time_key"]) is not int
            or decision_key != row["revocation_time_key"]
        ):
            raise SqliteAdmissionStoreIntegrityError(
                "stored revocation indexes or issuer ownership disagree"
            )
        return _RevocationRecord(
            grant=grant,
            revoker_kind=row["revoker_kind"],
            revoker_id=row["revoker_id"],
            revocation_time=row["revocation_time"],
        )

    def _verify_all_payloads(
        self,
        connection: sqlite3.Connection,
        metadata: _LedgerMetadata,
    ) -> None:
        highest_key: int | None = None
        admitted_grants: dict[
            tuple[str, str, str, str],
            tuple[AgentExecutionAuthorizationGrant, int],
        ] = {}
        for row in connection.execute(
            "SELECT * FROM agent_execution_dispatch_admissions"
        ).fetchall():
            admission = self._admission_from_row(row)
            admitted_grants[_grant_identity(admission.grant)] = (
                admission.grant,
                row["decision_time_key"],
            )
            key = row["decision_time_key"]
            highest_key = key if highest_key is None else max(highest_key, key)
        for row in connection.execute(
            "SELECT * FROM agent_execution_grant_revocations"
        ).fetchall():
            revocation = self._revocation_from_row(row)
            key = row["revocation_time_key"]
            admitted = admitted_grants.get(_grant_identity(revocation.grant))
            if admitted is not None:
                admitted_grant, admission_key = admitted
                if admitted_grant != revocation.grant:
                    raise SqliteAdmissionStoreIntegrityError(
                        "Grant identity rebounds across Admission and revocation records"
                    )
                if key < admission_key:
                    raise SqliteAdmissionStoreIntegrityError(
                        "revocation serial time precedes its historical Admission"
                    )
            highest_key = key if highest_key is None else max(highest_key, key)
        if highest_key is not None and (
            metadata.decision_time_key is None
            or metadata.decision_time_key < highest_key
        ):
            raise SqliteAdmissionStoreIntegrityError(
                "watermark precedes a durable security record"
            )

        if metadata.schema_version >= 2:
            self._verify_dispatch_classifications(connection, set(admitted_grants))
        if metadata.schema_version >= 3:
            self._verify_dispatch_lease_history(connection, metadata, admitted_grants)

    @staticmethod
    def _dispatch_time_from_row(row, text_column, key_column):
        _, key = _parse_decision_time(row[text_column])
        if (type(row[key_column]) is not int or row[key_column] != key
                or not 0 <= key <= _DISPATCH_MAX_TIME_KEY):
            raise ValueError("Dispatch time text/key disagree")
        return key

    @staticmethod
    def _dispatch_claim_from_row(row) -> _DispatchClaim:
        try:
            acquired = SqliteAgentExecutionDispatchAdmissionStore._dispatch_time_from_row(
                row, "acquired_at", "acquired_at_key")
            expiry = SqliteAgentExecutionDispatchAdmissionStore._dispatch_time_from_row(
                row, "lease_until", "lease_until_key")
            if expiry != acquired + _DISPATCH_LEASE_US:
                raise ValueError("Claim duration disagrees")
            return _DispatchClaim(
                _dispatch_token(row["claim_id"]),
                _dispatch_identity(tuple(row[name] for name in _DISPATCH_ID_COLUMNS)),
                _dispatch_token(row["executor_instance_id"]),
                _dispatch_integer(row["lease_generation"]),
                row["acquired_at"], acquired, row["lease_until"], expiry,
            )
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise SqliteAdmissionStoreIntegrityError("malformed immutable Dispatch Claim") from error

    @staticmethod
    def _dispatch_renewal_from_row(row) -> _DispatchRenewal:
        try:
            renewed = SqliteAgentExecutionDispatchAdmissionStore._dispatch_time_from_row(
                row, "renewed_at", "renewed_at_key")
            expiry = SqliteAgentExecutionDispatchAdmissionStore._dispatch_time_from_row(
                row, "lease_until", "lease_until_key")
            if expiry != renewed + _DISPATCH_LEASE_US:
                raise ValueError("Renewal duration disagrees")
            return _DispatchRenewal(
                _dispatch_token(row["renewal_id"]), _dispatch_token(row["claim_id"]),
                _dispatch_identity(tuple(row[name] for name in _DISPATCH_ID_COLUMNS)),
                _dispatch_token(row["executor_instance_id"]),
                _dispatch_integer(row["lease_generation"]),
                _dispatch_integer(row["renewal_sequence"]),
                row["renewed_at"], renewed, row["lease_until"], expiry,
            )
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise SqliteAdmissionStoreIntegrityError("malformed immutable Dispatch Renewal") from error

    def _verify_dispatch_lease_history(self, connection, metadata, admitted_grants):
        claims = {}
        chains = {}
        latest = {}
        highest_time = None
        for row in connection.execute(
                "SELECT * FROM agent_execution_dispatch_claims ORDER BY "
                "authorization_domain_id COLLATE BINARY, issuer_kind COLLATE BINARY, "
                "issuer_id COLLATE BINARY, grant_id COLLATE BINARY, lease_generation").fetchall():
            claim = self._dispatch_claim_from_row(row)
            if claim.claim_id in claims or claim.identity not in admitted_grants:
                raise SqliteAdmissionStoreIntegrityError("duplicate/orphan Dispatch Claim")
            admission = self._find_admission_by_identity(connection, admitted_grants[claim.identity][0])
            if self._classify_admission_dispatch(connection, admission).kind != "intent":
                raise SqliteAdmissionStoreIntegrityError("legacy history cannot own a Claim")
            previous = latest.get(claim.identity)
            if (claim.lease_generation != (1 if previous is None else previous.lease_generation + 1)
                    or claim.acquired_at_key < admitted_grants[claim.identity][1]):
                raise SqliteAdmissionStoreIntegrityError("Dispatch generation/time regresses or jumps")
            claims[claim.claim_id] = claim
            chains[claim.claim_id] = []
            latest[claim.identity] = claim
            highest_time = max(highest_time or 0, claim.acquired_at_key)
        renewal_ids = set()
        for row in connection.execute(
                "SELECT * FROM agent_execution_dispatch_renewals ORDER BY claim_id COLLATE BINARY, renewal_sequence"
        ).fetchall():
            renewal = self._dispatch_renewal_from_row(row)
            claim = claims.get(renewal.claim_id)
            if (claim is None or renewal.renewal_id in renewal_ids
                    or (renewal.identity, renewal.executor_instance_id, renewal.lease_generation)
                    != (claim.identity, claim.executor_instance_id, claim.lease_generation)):
                raise SqliteAdmissionStoreIntegrityError("orphan/duplicate/rebound Dispatch Renewal")
            chain = chains[claim.claim_id]
            previous = chain[-1] if chain else None
            effective = claim.lease_until_key if previous is None else previous.lease_until_key
            previous_time = claim.acquired_at_key if previous is None else previous.renewed_at_key
            if (renewal.renewal_sequence != len(chain) + 1
                    or not previous_time <= renewal.renewed_at_key < effective
                    or renewal.lease_until_key <= effective):
                raise SqliteAdmissionStoreIntegrityError("Renewal sequence/time/extension is inconsistent")
            chain.append(renewal)
            renewal_ids.add(renewal.renewal_id)
            highest_time = max(highest_time or 0, renewal.renewed_at_key)
        effective_by_identity = {}
        for claim in claims.values():
            prior_expiry = effective_by_identity.get(claim.identity)
            if prior_expiry is not None and claim.acquired_at_key < prior_expiry:
                raise SqliteAdmissionStoreIntegrityError("Dispatch generations overlap or Renewal follows supersession")
            chain = chains[claim.claim_id]
            effective_by_identity[claim.identity] = chain[-1].lease_until_key if chain else claim.lease_until_key
            revoked = self._find_revocation_by_identity(connection, admitted_grants[claim.identity][0])
            if revoked is not None:
                _, revoked_key = _parse_decision_time(revoked.revocation_time)
                if max([claim.acquired_at_key] + [value.renewed_at_key for value in chain]) > revoked_key:
                    raise SqliteAdmissionStoreIntegrityError("Dispatch decision follows durable revocation")
        if highest_time is not None and (
                metadata.decision_time_key is None or metadata.decision_time_key < highest_time):
            raise SqliteAdmissionStoreIntegrityError("watermark precedes durable Dispatch decision")

    @staticmethod
    def _find_dispatch_claim(connection, claim_id):
        row = connection.execute(
            "SELECT * FROM agent_execution_dispatch_claims WHERE claim_id=?", (claim_id,)
        ).fetchone()
        return None if row is None else SqliteAgentExecutionDispatchAdmissionStore._dispatch_claim_from_row(row)

    @staticmethod
    def _dispatch_highest_claim(connection, identity):
        row = connection.execute(
            "SELECT * FROM agent_execution_dispatch_claims WHERE "
            "authorization_domain_id=? AND issuer_kind=? AND issuer_id=? AND grant_id=? "
            "ORDER BY lease_generation DESC LIMIT 1", identity
        ).fetchone()
        return None if row is None else SqliteAgentExecutionDispatchAdmissionStore._dispatch_claim_from_row(row)

    @staticmethod
    def _dispatch_renewals(connection, claim_id):
        return tuple(SqliteAgentExecutionDispatchAdmissionStore._dispatch_renewal_from_row(row)
                     for row in connection.execute(
                         "SELECT * FROM agent_execution_dispatch_renewals WHERE claim_id=? ORDER BY renewal_sequence",
                         (claim_id,)).fetchall())

    @staticmethod
    def _dispatch_effective_expiry(connection, claim):
        renewals = SqliteAgentExecutionDispatchAdmissionStore._dispatch_renewals(connection, claim.claim_id)
        return (renewals[-1].lease_until, renewals[-1].lease_until_key) if renewals else (
            claim.lease_until, claim.lease_until_key)

    @staticmethod
    def _verify_dispatch_classifications(
        connection: sqlite3.Connection,
        admission_keys: set[tuple[str, str, str, str]],
    ) -> None:
        """Prove complete, disjoint immutable classification in this snapshot."""

        classified: list[set[tuple[str, str, str, str]]] = []
        for table in ("agent_execution_dispatch_intents", "legacy_admission_markers"):
            rows = connection.execute(f"SELECT * FROM {table}").fetchall()
            keys: set[tuple[str, str, str, str]] = set()
            for row in rows:
                key = tuple(row[name] for name in (
                    "authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"
                ))
                if (
                    any(type(value) is not str or not value for value in key)
                    or key[1] not in ("human", "policy")
                    or key in keys
                    or key not in admission_keys
                ):
                    raise SqliteAdmissionStoreIntegrityError(
                        "classification identity is malformed, duplicated, or orphaned"
                    )
                if table == "legacy_admission_markers" and (
                    type(row["migration_id"]) is not int or row["migration_id"] != 2
                ):
                    raise SqliteAdmissionStoreIntegrityError(
                        "legacy classification does not name migration 2"
                    )
                keys.add(key)
            classified.append(keys)
        intents, markers = classified
        if intents & markers or intents | markers != admission_keys:
            raise SqliteAdmissionStoreIntegrityError(
                "every Admission requires exactly one Intent or legacy marker"
            )

    @staticmethod
    def _classify_admission_dispatch(
        connection: sqlite3.Connection,
        admission: AgentExecutionDispatchAdmission,
    ) -> _DispatchClassification:
        """Dereference one verified immutable history record, never live authority."""

        stored = SqliteAgentExecutionDispatchAdmissionStore._find_admission_by_identity(
            connection, admission.grant
        )
        if stored is None or stored != admission:
            raise SqliteAdmissionStoreIntegrityError(
                "dispatch classification does not match its complete immutable Admission"
            )
        identity = _grant_identity(stored.grant)
        where = (
            "authorization_domain_id=? COLLATE BINARY AND issuer_kind=? COLLATE BINARY "
            "AND issuer_id=? COLLATE BINARY AND grant_id=? COLLATE BINARY"
        )
        intent = connection.execute(
            f"SELECT * FROM agent_execution_dispatch_intents WHERE {where}", identity
        ).fetchall()
        markers = connection.execute(
            f"SELECT * FROM legacy_admission_markers WHERE {where}", identity
        ).fetchall()
        if len(intent) + len(markers) != 1:
            raise SqliteAdmissionStoreIntegrityError(
                "Admission history has missing, duplicate, or overlapping classification"
            )
        if markers:
            marker = markers[0]
            if type(marker["migration_id"]) is not int or marker["migration_id"] != 2:
                raise SqliteAdmissionStoreIntegrityError("legacy migration provenance disagrees")
            history = connection.execute(
                "SELECT migration_id, resource_name, sha256 FROM admission_schema_migrations "
                "WHERE migration_id=2"
            ).fetchall()
            expected = _migration_bytes()[1][:3]
            if len(history) != 1 or tuple(history[0]) != expected:
                raise SqliteAdmissionStoreIntegrityError("legacy migration history disagrees")
        return _DispatchClassification(stored, "legacy" if markers else "intent")

    def verified_settings(self) -> SqliteAdmissionStoreSettings:
        """Return the verified operational profile without changing state."""

        connection = self._open_existing(allow_fenced=False)
        try:
            return self._configure_connection(
                connection,
                self.configuration,
                establish_wal=False,
            )
        finally:
            connection.close()

    def _verified_activation_state_for_ownership(self) -> str:
        """Return fully verified active/fenced state for owner recovery."""

        connection = self._open_existing(allow_fenced=True)
        try:
            connection.execute("BEGIN")
            metadata = self._verify_authoritative_connection(
                connection,
                allow_fenced=True,
            )
            connection.execute("ROLLBACK")
            return metadata.activation_state
        except BaseException:
            _safe_rollback(connection)
            raise
        finally:
            connection.close()

    def watermark(self) -> tuple[str | None, int | None]:
        """Expose verified watermark evidence for focused diagnostics/tests."""

        connection = self._open_existing(allow_fenced=False)
        try:
            connection.execute("BEGIN")
            metadata = self._verify_authoritative_connection(connection, allow_fenced=False)
            connection.execute("ROLLBACK")
            return metadata.decision_time, metadata.decision_time_key
        except BaseException:
            _safe_rollback(connection)
            raise
        finally:
            connection.close()

    def _fault(self, point: str) -> None:
        """Protected test seam; production request data cannot inject faults."""

        del point

    @staticmethod
    def _find_admission_by_identity(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentExecutionDispatchAdmission | None:
        row = connection.execute(
            """
            SELECT *
            FROM agent_execution_dispatch_admissions
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND issuer_kind = ? COLLATE BINARY
              AND issuer_id = ? COLLATE BINARY
              AND grant_id = ? COLLATE BINARY
            """,
            _grant_identity(grant),
        ).fetchone()
        if row is None:
            return None
        return SqliteAgentExecutionDispatchAdmissionStore._admission_from_row(row)

    @staticmethod
    def _find_admission_by_run(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentExecutionDispatchAdmission | None:
        row = connection.execute(
            """
            SELECT *
            FROM agent_execution_dispatch_admissions
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND run_id = ? COLLATE BINARY
            """,
            (grant.authorization_domain_id, grant.run.run_id),
        ).fetchone()
        if row is None:
            return None
        return SqliteAgentExecutionDispatchAdmissionStore._admission_from_row(row)

    @staticmethod
    def _find_revocation_by_identity(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> _RevocationRecord | None:
        row = connection.execute(
            """
            SELECT *
            FROM agent_execution_grant_revocations
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND issuer_kind = ? COLLATE BINARY
              AND issuer_id = ? COLLATE BINARY
              AND grant_id = ? COLLATE BINARY
            """,
            _grant_identity(grant),
        ).fetchone()
        if row is None:
            return None
        return SqliteAgentExecutionDispatchAdmissionStore._revocation_from_row(row)

    @staticmethod
    def _classify_existing(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> AgentExecutionDispatchAdmissionStoreResult | None:
        existing = (
            SqliteAgentExecutionDispatchAdmissionStore.
            _find_admission_by_identity(connection, grant)
        )
        if existing is not None:
            if existing.grant != grant:
                return _result(
                    "grant_identity_conflict",
                    detail="Grant composite identity is bound to another complete Grant",
                )
            if existing.tool_binding != binding:
                return _result(
                    "binding_conflict",
                    detail="the complete Grant is bound to another Tool Binding",
                )
            SqliteAgentExecutionDispatchAdmissionStore._classify_admission_dispatch(
                connection, existing
            )
            return _result(
                "existing_exact_admission",
                admission=existing,
                detail="the exact historical Admission already exists",
            )
        revocation = (
            SqliteAgentExecutionDispatchAdmissionStore.
            _find_revocation_by_identity(connection, grant)
        )
        if revocation is not None and revocation.grant != grant:
            return _result(
                "grant_identity_conflict",
                detail="revocation identity is bound to another complete Grant",
            )
        run_existing = (
            SqliteAgentExecutionDispatchAdmissionStore.
            _find_admission_by_run(connection, grant)
        )
        if run_existing is not None:
            return _result(
                "run_conflict",
                detail="authorization domain and Run ID are already consumed",
            )
        return None

    def _validate_request_values(
        self,
        expected_domain: object,
        grant: object,
        binding: object | None = None,
        expected_run: object | None = None,
    ) -> AgentExecutionDispatchAdmissionStoreResult | None:
        if (
            type(expected_domain) is not str
            or not expected_domain
            or type(grant) is not AgentExecutionAuthorizationGrant
            or not validate_agent_execution_authorization_grant(grant).valid
        ):
            return _result(
                "invalid_input",
                detail="authority-internal request values are intrinsically invalid",
            )
        if (
            expected_domain != self.configuration.authorization_domain_id
            or grant.authorization_domain_id != expected_domain
        ):
            return _result(
                "domain_mismatch",
                detail="request, Grant, and configured authorization domains differ",
            )
        if binding is not None:
            if (
                type(binding) is not AgentOperationToolBinding
                or not validate_agent_operation_tool_binding(binding).valid
                or grant.run != binding.run
            ):
                return _result(
                    "invalid_input",
                    detail="Grant and trusted Tool Binding are invalid or Run-mismatched",
                )
        if expected_run is not None and (
            type(expected_run) is not AgentExecutionRun
            or binding is None
            or grant.run != binding.run
            or grant.run != expected_run
        ):
            return _result(
                "invalid_input",
                detail="Grant, Tool Binding, and fresh expected Run must be exactly equal",
            )
        return None

    @staticmethod
    def _operational_failure(error: BaseException):
        if isinstance(error, SqliteAdmissionStoreIncompatibleSchemaError):
            return _result("incompatible_schema", detail=str(error))
        if isinstance(error, SqliteAdmissionStoreIntegrityError):
            return _result("integrity_failure", detail=str(error))
        if _is_busy(error):
            return _result(
                "storage_busy",
                detail="the pinned authoritative Admission ledger is busy",
            )
        return _result(
            "storage_unavailable",
            detail="the pinned authoritative Admission ledger is unavailable",
        )

    def _sample_clock(
        self,
        metadata: _LedgerMetadata,
    ) -> tuple[datetime, str, int] | AgentExecutionDispatchAdmissionStoreResult:
        try:
            sampled = self._clock.now_utc()
            decision, decision_text, decision_key = _canonical_decision_time(sampled)
        except BaseException as error:
            return _result(
                "clock_failure",
                detail=f"the authoritative UTC clock failed closed: {error}",
            )
        if (
            metadata.decision_time_key is not None
            and decision_key < metadata.decision_time_key
        ):
            return _result(
                "clock_regression",
                detail="the authoritative clock precedes the committed domain watermark",
            )
        return decision, decision_text, decision_key

    @staticmethod
    def _advance_watermark(
        connection: sqlite3.Connection,
        decision_time: str,
        decision_time_key: int,
    ) -> None:
        cursor = connection.execute(
            """
            UPDATE admission_ledger_metadata
            SET last_decision_time=?, last_decision_time_key=?
            WHERE singleton=1
              AND activation_state='active'
              AND migration_state='clean'
            """,
            (decision_time, decision_time_key),
        )
        if cursor.rowcount != 1:
            raise SqliteAdmissionStoreIntegrityError(
                "watermark update lost active ledger ownership"
            )

    def _dispatch_failure(self, error, commit_attempted):
        if commit_attempted or isinstance(error, _CommitUnknown):
            return _dispatch_result("commit_unknown", detail="reconcile original operation on the same pinned ledger")
        failure = self._operational_failure(error)
        return _dispatch_result(failure.outcome.value, detail=failure.detail)

    def _dispatch_sample(self, metadata):
        sampled = self._sample_clock(metadata)
        if type(sampled) is AgentExecutionDispatchAdmissionStoreResult:
            return _dispatch_result(sampled.outcome.value, detail=sampled.detail)
        return sampled

    def _claim_dispatch_intent(self, request) -> _DispatchResult:
        """Claim one ordered eligible Intent; no launch, invocation or permission."""
        try:
            request, executor = _open_dispatch_request(request, self, "claim")
        except (ValueError, TypeError, AttributeError) as error:
            return _dispatch_result("invalid_input", detail=str(error))
        connection = None
        commit_attempted = False
        try:
            self._fault("claim.before_transaction")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN IMMEDIATE")
            self._fault("claim.after_begin")
            metadata = self._verify_authoritative_connection(connection, allow_fenced=False)
            historical = self._find_dispatch_claim(connection, request.claim_id)
            if historical is not None:
                connection.execute("ROLLBACK")
                if historical.executor_instance_id != executor:
                    return _dispatch_result("claim_identity_conflict")
                return _dispatch_result("existing_claim_history", claim=historical, history_only=True)
            rows = connection.execute(
                "SELECT a.* FROM agent_execution_dispatch_intents AS i "
                "JOIN agent_execution_dispatch_admissions AS a USING "
                "(authorization_domain_id,issuer_kind,issuer_id,grant_id) "
                "ORDER BY a.decision_time_key, i.authorization_domain_id COLLATE BINARY, "
                "i.issuer_kind COLLATE BINARY, i.issuer_id COLLATE BINARY, i.grant_id COLLATE BINARY"
            ).fetchall()
            parents = [self._admission_from_row(row) for row in rows]
            eligible = [parent for parent in parents
                        if self._find_revocation_by_identity(connection, parent.grant) is None]
            if not eligible:
                connection.execute("ROLLBACK")
                return _dispatch_result("empty" if not parents else "authority_ineligible")
            sampled = self._dispatch_sample(metadata)
            if type(sampled) is _DispatchResult:
                connection.execute("ROLLBACK")
                return sampled
            now, text, key = sampled
            selected = None
            previous = None
            for parent in eligible:
                identity = _grant_identity(parent.grant)
                highest = self._dispatch_highest_claim(connection, identity)
                if highest is None or key >= self._dispatch_effective_expiry(connection, highest)[1]:
                    selected, previous = identity, highest
                    break
            self._fault("claim.after_candidate_selection")
            if selected is None:
                # This flag includes a watermark-only commit's ambiguity.
                self._fault("claim.before_watermark")
                self._advance_watermark(connection, text, key)
                self._fault("claim.after_watermark")
                self._verify_authoritative_connection(connection, allow_fenced=False)
                self._fault("claim.before_commit")
                commit_attempted = True
                _commit(connection)
                self._fault("claim.after_commit_before_response")
                return _dispatch_result("temporarily_unavailable")
            try:
                generation = _next_dispatch_integer(0 if previous is None else previous.lease_generation)
            except OverflowError:
                connection.execute("ROLLBACK")
                return _dispatch_result("generation_exhausted")
            self._fault("claim.after_generation_allocation")
            try:
                expiry_text, expiry_key = _dispatch_expiry(now)
            except (OverflowError, ValueError):
                connection.execute("ROLLBACK")
                return _dispatch_result("clock_failure", detail="Lease expiry is outside the canonical time range")
            claim = _DispatchClaim(request.claim_id, selected, executor, generation,
                                   text, key, expiry_text, expiry_key)
            connection.execute(
                "INSERT INTO agent_execution_dispatch_claims VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (claim.claim_id, *claim.identity, claim.executor_instance_id, claim.lease_generation,
                 claim.acquired_at, claim.acquired_at_key, claim.lease_until, claim.lease_until_key),
            )
            self._fault("claim.after_insert")
            self._advance_watermark(connection, text, key)
            self._fault("claim.after_watermark")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            self._fault("claim.before_commit")
            commit_attempted = True
            _commit(connection)
            self._fault("claim.after_commit_before_response")
            return _dispatch_result("newly_claimed", claim=claim)
        except BaseException as error:
            _safe_rollback(connection)
            return self._dispatch_failure(error, commit_attempted)
        finally:
            if connection is not None:
                connection.close()

    def _renew_dispatch_claim(self, request) -> _DispatchResult:
        """Append one exact current-Claim extension; retry returns history only."""
        try:
            request, executor = _open_dispatch_request(request, self, "renew")
        except (ValueError, TypeError, AttributeError) as error:
            return _dispatch_result("invalid_input", detail=str(error))
        connection = None
        commit_attempted = False
        try:
            self._fault("renew.before_transaction")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN IMMEDIATE")
            self._fault("renew.after_begin")
            metadata = self._verify_authoritative_connection(connection, allow_fenced=False)
            row = connection.execute(
                "SELECT * FROM agent_execution_dispatch_renewals WHERE renewal_id=?", (request.renewal_id,)
            ).fetchone()
            if row is not None:
                historical = self._dispatch_renewal_from_row(row)
                connection.execute("ROLLBACK")
                if (historical.claim_id, historical.identity, historical.executor_instance_id,
                    historical.lease_generation) != (request.claim_id, request.identity, executor, request.generation):
                    return _dispatch_result("renewal_identity_conflict")
                return _dispatch_result("existing_renewal_history", renewal=historical, history_only=True)
            claim = self._find_dispatch_claim(connection, request.claim_id)
            rejected = self._dispatch_current_tuple(connection, request, executor, claim)
            if rejected is not None:
                connection.execute("ROLLBACK")
                return rejected
            self._fault("renew.after_validation")
            sampled = self._dispatch_sample(metadata)
            if type(sampled) is _DispatchResult:
                connection.execute("ROLLBACK")
                return sampled
            now, text, key = sampled
            effective_text, effective_key = self._dispatch_effective_expiry(connection, claim)
            if key >= effective_key:
                outcome = "expired_claim"
            else:
                try:
                    expiry_text, expiry_key = _dispatch_expiry(now)
                except (OverflowError, ValueError):
                    connection.execute("ROLLBACK")
                    return _dispatch_result("clock_failure", detail="Renewal expiry is outside the canonical time range")
                outcome = "nonextending" if expiry_key <= effective_key else "newly_renewed"
            renewal = None
            if outcome == "newly_renewed":
                renewals = self._dispatch_renewals(connection, claim.claim_id)
                try:
                    sequence = _next_dispatch_integer(0 if not renewals else renewals[-1].renewal_sequence)
                except OverflowError:
                    connection.execute("ROLLBACK")
                    return _dispatch_result("sequence_exhausted")
                renewal = _DispatchRenewal(request.renewal_id, claim.claim_id, claim.identity, executor,
                                          claim.lease_generation, sequence, text, key, expiry_text, expiry_key)
                connection.execute(
                    "INSERT INTO agent_execution_dispatch_renewals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (renewal.renewal_id, renewal.claim_id, *renewal.identity, renewal.executor_instance_id,
                     renewal.lease_generation, renewal.renewal_sequence, renewal.renewed_at,
                     renewal.renewed_at_key, renewal.lease_until, renewal.lease_until_key),
                )
                self._fault("renew.after_insert")
            self._advance_watermark(connection, text, key)
            self._fault("renew.after_watermark")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            self._fault("renew.before_commit")
            commit_attempted = True
            _commit(connection)
            self._fault("renew.after_commit_before_response")
            return _dispatch_result(outcome, renewal=renewal)
        except BaseException as error:
            _safe_rollback(connection)
            return self._dispatch_failure(error, commit_attempted)
        finally:
            if connection is not None:
                connection.close()

    def _dispatch_current_tuple(self, connection, request, executor, claim):
        if claim is None:
            return _dispatch_result("claim_not_found")
        if (claim.identity, claim.executor_instance_id, claim.lease_generation) != (
                request.identity, executor, request.generation):
            return _dispatch_result("claim_identity_conflict")
        highest = self._dispatch_highest_claim(connection, claim.identity)
        if highest is None or highest.claim_id != claim.claim_id:
            return _dispatch_result("stale_generation")
        row = connection.execute(
            "SELECT * FROM agent_execution_grant_revocations WHERE "
            "authorization_domain_id=? AND issuer_kind=? AND issuer_id=? AND grant_id=?", claim.identity
        ).fetchone()
        return None if row is None else _dispatch_result("revoked")

    def _query_dispatch_claim(self, request) -> _DispatchResult:
        """Private exact history or serialized point-in-time ownership assessment."""
        try:
            request, executor = _open_dispatch_request(request, self, "query")
        except (ValueError, TypeError, AttributeError) as error:
            return _dispatch_result("invalid_input", detail=str(error))
        connection = None
        commit_attempted = False
        try:
            self._fault("query.before_transaction")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN" if request.mode == "history" else "BEGIN IMMEDIATE")
            metadata = self._verify_authoritative_connection(connection, allow_fenced=False)
            claim = self._find_dispatch_claim(connection, request.claim_id)
            if request.mode == "history":
                renewals = () if claim is None else self._dispatch_renewals(connection, claim.claim_id)
                connection.execute("ROLLBACK")
                return (_dispatch_result("claim_not_found") if claim is None else
                        _dispatch_result("claim_history", claim=claim, renewals=renewals, history_only=True))
            rejected = self._dispatch_current_tuple(connection, request, executor, claim)
            if rejected is not None:
                connection.execute("ROLLBACK")
                return rejected
            sampled = self._dispatch_sample(metadata)
            if type(sampled) is _DispatchResult:
                connection.execute("ROLLBACK")
                return sampled
            _, text, key = sampled
            effective_text, effective_key = self._dispatch_effective_expiry(connection, claim)
            active = claim.acquired_at_key <= key < effective_key
            self._advance_watermark(connection, text, key)
            self._fault("query.after_watermark")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            self._fault("query.before_commit")
            commit_attempted = True
            _commit(connection)
            self._fault("query.after_commit_before_response")
            return (_dispatch_result("current_claim", claim=claim, effective_lease_until=effective_text)
                    if active else _dispatch_result("expired_claim"))
        except BaseException as error:
            _safe_rollback(connection)
            return self._dispatch_failure(error, commit_attempted)
        finally:
            if connection is not None:
                connection.close()


    def _assess_jit_dispatch(self, request, operation):
        """Private held-authority assessment; commits watermark only, never Entry."""
        from engineering_orchestration._jit_execution_attempt_authorization import (
            _JitAssessmentOperation, _JitFailure, _JitResult,
        )
        connection = None
        commit_attempted = False
        try:
            request, executor = _open_dispatch_request(request, self, "query")
            if (type(operation) is not _JitAssessmentOperation
                    or operation.authorizer.session is not request.session
                    or operation.authorizer.store is not self):
                raise _JitFailure("invalid_integration")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN IMMEDIATE")
            self._fault("jit.after_begin")
            metadata = self._verify_authoritative_connection(connection, allow_fenced=False)
            claim = self._find_dispatch_claim(connection, request.claim_id)
            # W precedes C; consume reservation precedes every final validation.
            with operation._cell_scope(self):
                rejected = self._dispatch_current_tuple(connection, request, executor, claim)
                if rejected is not None:
                    raise _JitFailure(rejected.outcome)
                row = connection.execute(
                    "SELECT * FROM agent_execution_dispatch_admissions WHERE "
                    "authorization_domain_id=? AND issuer_kind=? AND issuer_id=? AND grant_id=?",
                    claim.identity).fetchone()
                if row is None:
                    raise SqliteAdmissionStoreIntegrityError("Claim has no exact Admission")
                parent = self._admission_from_row(row)
                _, effective_key = self._dispatch_effective_expiry(connection, claim)
                operation._freeze(parent)
                sampled = self._dispatch_sample(metadata)
                if type(sampled) is _DispatchResult:
                    raise _JitFailure(sampled.outcome)
                now, text, key = sampled
                result = operation._check(parent, claim, effective_key, now, text, key)
                self._advance_watermark(connection, text, key)
                self._fault("jit.after_watermark")
                self._verify_authoritative_connection(connection, allow_fenced=False)
                self._fault("jit.before_commit")
                commit_attempted = True
                _commit(connection)  # Releases W while C finishes terminal cleanup.
                self._fault("jit.after_commit_before_response")
                return result
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted or isinstance(error, _CommitUnknown):
                return _JitResult("commit_unknown", category="infrastructure")
            if isinstance(error, _JitFailure):
                return _JitResult(error.outcome, category=error.category)
            if isinstance(error, (ValueError, TypeError, AttributeError)):
                return _JitResult("integrity_failure", category="integrity")
            failure = self._operational_failure(error)
            return _JitResult(failure.outcome.value, category=(
                "integrity" if failure.outcome.value == "integrity_failure" else "infrastructure"))
        finally:
            if connection is not None:
                connection.close()

    def classify_guarded_history(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Classify exact trusted history without clock or revocation reevaluation."""

        opened = _open_guarded_history_request(request)
        if opened is None:
            return _result(
                "invalid_input",
                detail="guarded-history request was not coordinator-minted",
            )
        expected_domain, grant, binding = opened
        invalid = self._validate_request_values(expected_domain, grant, binding)
        if invalid is not None:
            return invalid
        connection: sqlite3.Connection | None = None
        try:
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            historical = self._classify_existing(connection, grant, binding)
            connection.execute("ROLLBACK")
            if historical is not None:
                return historical
            return _result(
                "no_existing_admission",
                detail="no Admission exists for the trusted Grant and Binding",
            )
        except BaseException as error:
            _safe_rollback(connection)
            return self._operational_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def load_authoritative_admission(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Load exact authoritative history after coordinator trust checks."""

        opened = _open_authoritative_lookup_request(request)
        if opened is None:
            return _result(
                "invalid_input",
                detail="authoritative lookup request was not coordinator-minted",
            )
        expected_domain, grant, binding = opened
        invalid = self._validate_request_values(expected_domain, grant, binding)
        if invalid is not None:
            return invalid
        connection: sqlite3.Connection | None = None
        try:
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            historical = self._classify_existing(connection, grant, binding)
            connection.execute("ROLLBACK")
            if historical is not None:
                return historical
            return _result(
                "no_existing_admission",
                detail="no authoritative Admission exists for the exact request",
            )
        except BaseException as error:
            _safe_rollback(connection)
            return self._operational_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def admit_or_return_existing(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Atomically consume one current non-revoked Grant or return history."""

        opened = _open_admission_request(request)
        if opened is None:
            return _result(
                "invalid_input",
                detail="Admission request was not coordinator-minted",
            )
        expected_domain, grant, binding, expected_run = opened
        invalid = self._validate_request_values(
            expected_domain,
            grant,
            binding,
            expected_run,
        )
        if invalid is not None:
            return invalid

        connection: sqlite3.Connection | None = None
        commit_attempted = False
        try:
            self._fault("before_transaction")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN IMMEDIATE")
            self._fault("after_begin")
            metadata = self._verify_authoritative_connection(
                connection,
                allow_fenced=False,
            )
            concurrent = self._classify_existing(connection, grant, binding)
            if concurrent is not None:
                connection.execute("ROLLBACK")
                return concurrent

            # Repeat the complete request check after writer serialization and
            # the exact-history/conflict recheck.  Frozen values are the normal
            # API boundary, but the Store contract owns this transactional
            # invariant rather than relying on a pre-transaction observation.
            transactional_invalid = self._validate_request_values(
                expected_domain,
                grant,
                binding,
                expected_run,
            )
            if transactional_invalid is not None:
                connection.execute("ROLLBACK")
                return transactional_invalid

            revocation = self._find_revocation_by_identity(connection, grant)
            if revocation is not None and revocation.grant != grant:
                connection.execute("ROLLBACK")
                return _result(
                    "grant_identity_conflict",
                    detail="revocation identity is bound to another complete Grant",
                )

            sampled = self._sample_clock(metadata)
            if type(sampled) is AgentExecutionDispatchAdmissionStoreResult:
                connection.execute("ROLLBACK")
                return sampled
            decision, decision_text, decision_key = sampled
            issued_at = _parse_grant_time(grant.issued_at)
            expires_at = _parse_grant_time(grant.expires_at)

            if decision < issued_at:
                self._advance_watermark(connection, decision_text, decision_key)
                self._verify_authoritative_connection(connection, allow_fenced=False)
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "not_yet_current",
                    detail="authoritative decision time precedes Grant issuance",
                )
            if decision >= expires_at:
                self._advance_watermark(connection, decision_text, decision_key)
                self._verify_authoritative_connection(connection, allow_fenced=False)
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "expired",
                    detail="authoritative decision time reached Grant expiry",
                )
            if revocation is not None:
                self._advance_watermark(connection, decision_text, decision_key)
                self._verify_authoritative_connection(connection, allow_fenced=False)
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "revoked",
                    detail="a prior same-ledger revocation prevents Admission",
                )

            self._fault("after_checks")
            self._fault("before_admission_insert")
            admission = AgentExecutionDispatchAdmission(
                grant=grant,
                tool_binding=binding,
                decision_time=decision_text,
            )
            if not validate_agent_execution_dispatch_admission(admission).valid:
                raise SqliteAdmissionStoreIntegrityError(
                    "new Admission failed intrinsic validation"
                )
            connection.execute(
                """
                INSERT INTO agent_execution_dispatch_admissions (
                    authorization_domain_id,
                    issuer_kind,
                    issuer_id,
                    grant_id,
                    run_id,
                    grant_json,
                    binding_json,
                    admission_json,
                    decision_time,
                    decision_time_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *_grant_identity(grant),
                    grant.run.run_id,
                    _encode_grant(grant),
                    _encode_binding(binding),
                    _encode_admission(admission),
                    decision_text,
                    decision_key,
                ),
            )
            self._fault("after_admission_insert_before_intent")
            connection.execute(
                """
                INSERT INTO agent_execution_dispatch_intents (
                    authorization_domain_id, issuer_kind, issuer_id, grant_id
                ) VALUES (?, ?, ?, ?)
                """,
                _grant_identity(grant),
            )
            self._fault("after_intent_insert_before_watermark")
            self._fault("after_insert_before_commit")
            self._advance_watermark(connection, decision_text, decision_key)
            self._fault("after_watermark_before_commit")
            self._verify_authoritative_connection(connection, allow_fenced=False)
            self._fault("before_commit")
            commit_attempted = True
            _commit(connection)
            self._fault("after_commit_before_response")
            return _result(
                "newly_admitted",
                admission=admission,
                detail="Grant and Run were atomically consumed into Admission",
            )
        except _CommitUnknown as error:
            _safe_rollback(connection)
            return _result("commit_unknown", detail=str(error))
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted:
                return _result(
                    "commit_unknown",
                    detail="response failed at or after COMMIT; exact retry is required",
                )
            return self._operational_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def revoke_or_return_existing(
        self,
        request: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Serialize one immutable original-issuer revocation tombstone."""

        opened = _open_revocation_request(request)
        if opened is None:
            return _result(
                "invalid_input",
                detail="revocation request was not coordinator-minted",
            )
        expected_domain, grant = opened
        invalid = self._validate_request_values(expected_domain, grant)
        if invalid is not None:
            return invalid

        connection: sqlite3.Connection | None = None
        commit_attempted = False
        try:
            self._fault("before_transaction")
            connection = self._open_existing(allow_fenced=False)
            connection.execute("BEGIN IMMEDIATE")
            self._fault("after_begin")
            metadata = self._verify_authoritative_connection(
                connection,
                allow_fenced=False,
            )
            admitted = self._find_admission_by_identity(connection, grant)
            if admitted is not None and admitted.grant != grant:
                connection.execute("ROLLBACK")
                return _result(
                    "grant_identity_conflict",
                    detail="Admission identity is bound to another complete Grant",
                )
            existing = self._find_revocation_by_identity(connection, grant)
            if existing is not None:
                if existing.grant != grant:
                    connection.execute("ROLLBACK")
                    return _result(
                        "grant_identity_conflict",
                        detail="revocation identity is bound to another complete Grant",
                    )
                connection.execute("ROLLBACK")
                return _result(
                    "existing_exact_revocation",
                    detail="the exact original-issuer revocation already exists",
                )

            sampled = self._sample_clock(metadata)
            if type(sampled) is AgentExecutionDispatchAdmissionStoreResult:
                connection.execute("ROLLBACK")
                return sampled
            _, decision_text, decision_key = sampled
            self._fault("after_checks")
            connection.execute(
                """
                INSERT INTO agent_execution_grant_revocations (
                    authorization_domain_id,
                    issuer_kind,
                    issuer_id,
                    grant_id,
                    run_id,
                    grant_json,
                    revoker_kind,
                    revoker_id,
                    revocation_time,
                    revocation_time_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *_grant_identity(grant),
                    grant.run.run_id,
                    _encode_grant(grant),
                    grant.issuer_kind,
                    grant.issuer_id,
                    decision_text,
                    decision_key,
                ),
            )
            self._fault("after_insert_before_commit")
            self._advance_watermark(connection, decision_text, decision_key)
            self._verify_authoritative_connection(connection, allow_fenced=False)
            commit_attempted = True
            _commit(connection)
            self._fault("after_commit_before_response")
            return _result(
                "newly_revoked",
                detail="the original issuer revocation was durably recorded",
            )
        except _CommitUnknown as error:
            _safe_rollback(connection)
            return _result("commit_unknown", detail=str(error))
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted:
                return _result(
                    "commit_unknown",
                    detail="revocation response failed at or after COMMIT",
                )
            return self._operational_failure(error)
        finally:
            if connection is not None:
                connection.close()

    def fence(self) -> SqliteAdmissionStoreAdministrationResult:
        """Irreversibly transition this active ledger to fenced/inert state."""

        connection: sqlite3.Connection | None = None
        commit_attempted = False
        try:
            # An exact retry after an ambiguous successful fence must be able
            # to reconcile the already-fenced terminal state. Operational
            # construction and every Admission call still refuse fenced stores.
            connection = self._open_existing(allow_fenced=True)
            connection.execute("BEGIN IMMEDIATE")
            metadata = self._verify_authoritative_connection(
                connection,
                allow_fenced=True,
            )
            if metadata.activation_state == "fenced":
                connection.execute("ROLLBACK")
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.FENCED,
                    "Admission ledger was already permanently fenced",
                )
            cursor = connection.execute(
                """
                UPDATE admission_ledger_metadata
                SET activation_state='fenced'
                WHERE singleton=1 AND activation_state='active'
                """
            )
            if cursor.rowcount != 1:
                raise SqliteAdmissionStoreIntegrityError(
                    "active ledger fencing lost ownership"
                )
            self._verify_authoritative_connection(connection, allow_fenced=True)
            commit_attempted = True
            _commit(connection)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.FENCED
            )
        except _CommitUnknown as error:
            _safe_rollback(connection)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN,
                str(error),
            )
        except BaseException as error:
            _safe_rollback(connection)
            if commit_attempted:
                outcome = SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN
            elif _is_busy(error):
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_BUSY
            elif isinstance(error, SqliteAdmissionStoreIntegrityError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INTEGRITY_FAILURE
            elif isinstance(error, SqliteAdmissionStoreIncompatibleSchemaError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA
            else:
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE
            return _admin_result(outcome, str(error))
        finally:
            if connection is not None:
                connection.close()

    def create_fenced_backup(
        self,
        destination: Path,
    ) -> SqliteAdmissionStoreAdministrationResult:
        """Publish one SQLite-consistent permanently fenced snapshot.

        The temporary destination is mode-restricted and never exposed before
        the copied ledger is durably fenced and fully validated.  This is the
        only supported backup path.  Raw main-file copies are unsupported and
        no backup produced here can be reactivated by AIO-047.
        """

        try:
            _normalized_path(destination, require_file=False)
        except SqliteAdmissionStoreConfigurationError as error:
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE,
                str(error),
            )
        if destination.exists():
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE,
                "fenced backup refuses an existing destination",
            )

        source: sqlite3.Connection | None = None
        target: sqlite3.Connection | None = None
        temporary_path: Path | None = None
        fencing_commit_attempted = False
        published = False
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{destination.name}.aio047-",
                suffix=".inert",
                dir=destination.parent,
            )
            os.close(descriptor)
            temporary_path = Path(temporary_name)
            try:
                os.chmod(temporary_path, 0o600)
            except OSError:
                pass

            source = self._open_existing(allow_fenced=False)
            target = sqlite3.connect(
                temporary_path.as_uri() + "?mode=rw",
                uri=True,
                timeout=self.configuration.busy_timeout_ms / 1_000,
                isolation_level=None,
            )
            target.row_factory = sqlite3.Row
            source.backup(target)
            temporary_configuration = (
                SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
                    database_path=temporary_path,
                    authorization_domain_id=self.configuration.authorization_domain_id,
                    ledger_instance_id=self.configuration.ledger_instance_id,
                    domain_generation=self.configuration.domain_generation,
                    busy_timeout_ms=self.configuration.busy_timeout_ms,
                )
            )
            self._configure_connection(
                target,
                temporary_configuration,
                establish_wal=False,
            )
            temporary_verifier = self.__class__.__new__(self.__class__)
            temporary_verifier.configuration = temporary_configuration
            temporary_verifier._clock = None
            target.execute("BEGIN IMMEDIATE")
            temporary_verifier._verify_authoritative_connection(
                target,
                allow_fenced=False,
            )
            cursor = target.execute(
                """
                UPDATE admission_ledger_metadata
                SET activation_state='fenced'
                WHERE singleton=1 AND activation_state='active'
                """
            )
            if cursor.rowcount != 1:
                raise SqliteAdmissionStoreIntegrityError(
                    "backup fencing lost copied ledger ownership"
                )
            temporary_verifier._verify_authoritative_connection(target, allow_fenced=True)
            fencing_commit_attempted = True
            _commit(target)
            target.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            target.close()
            target = None
            source.close()
            source = None

            verified = temporary_verifier._open_existing(allow_fenced=True)
            verified.close()
            os.link(temporary_path, destination)
            published = True
            temporary_path.unlink()
            temporary_path = None

            destination_configuration = (
                SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
                    database_path=destination,
                    authorization_domain_id=self.configuration.authorization_domain_id,
                    ledger_instance_id=self.configuration.ledger_instance_id,
                    domain_generation=self.configuration.domain_generation,
                    busy_timeout_ms=self.configuration.busy_timeout_ms,
                )
            )
            destination_verifier = self.__class__.__new__(self.__class__)
            destination_verifier.configuration = destination_configuration
            destination_verifier._clock = None
            opened = destination_verifier._open_existing(allow_fenced=True)
            opened.close()
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.FENCED_BACKUP_CREATED
            )
        except _CommitUnknown as error:
            _safe_rollback(target)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN,
                str(error),
            )
        except BaseException as error:
            _safe_rollback(target)
            if fencing_commit_attempted:
                outcome = SqliteAdmissionStoreAdministrationOutcome.COMMIT_UNKNOWN
            elif _is_busy(error):
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_BUSY
            elif isinstance(error, SqliteAdmissionStoreIntegrityError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INTEGRITY_FAILURE
            elif isinstance(error, SqliteAdmissionStoreIncompatibleSchemaError):
                outcome = SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA
            else:
                outcome = SqliteAdmissionStoreAdministrationOutcome.STORAGE_UNAVAILABLE
            return _admin_result(outcome, str(error))
        finally:
            if target is not None:
                target.close()
            if source is not None:
                source.close()
            if temporary_path is not None:
                for candidate in (
                    temporary_path,
                    Path(str(temporary_path) + "-wal"),
                    Path(str(temporary_path) + "-shm"),
                ):
                    try:
                        candidate.unlink(missing_ok=True)
                    except OSError:
                        pass
            if not published and destination.exists():
                # Publication uses an atomic hard link.  If a racing owner
                # created the path, it is not ours and is deliberately kept.
                pass
