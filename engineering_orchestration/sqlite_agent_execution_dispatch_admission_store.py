"""Supported same-host SQLite Agent Execution Dispatch Admission store.

This backend is deliberately narrow.  One trusted configuration pins one
absolute local database path, authorization domain, ledger instance, and
positive generation.  Operational calls never create, migrate, repair,
reactivate, or fall back to another authority store.

The durability claim applies only while every same-host consumer uses the
same correctly owned active ledger on trusted local storage.  A database can
record that it is fenced, but database-contained metadata cannot detect a
manually substituted stale active copy or prevent two copied active ledgers.
There is no same-domain restore/reactivation path in AIO-047.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
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
class _RevocationRecord:
    grant: AgentExecutionAuthorizationGrant
    revoker_kind: str
    revoker_id: str
    revocation_time: str


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


def _schema_manifest_id() -> str:
    material = "\n".join(
        f"{migration_id}:{name}:{checksum}"
        for migration_id, name, checksum, _ in _migration_bytes()
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


_EXPECTED_SCHEMA_FINGERPRINT = (
    "de080810b1d644dacf53e6bf79cbbd01343344904397a91c6dd483bd48dfad46"
)


def _schema_fingerprint(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        """
        SELECT type, name, tbl_name, sql
        FROM sqlite_schema
        WHERE name NOT LIKE 'sqlite_%'
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
    this class never authenticates arbitrary serialized values itself.
    """

    def __init__(
        self,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        *,
        clock: AgentExecutionDispatchAdmissionClock,
    ) -> None:
        self.configuration = _validate_configuration(
            configuration,
            require_file=True,
        )
        if not callable(getattr(clock, "now_utc", None)):
            raise SqliteAdmissionStoreConfigurationError(
                "clock must implement now_utc()"
            )
        self._clock = clock
        connection = self._open_existing(allow_fenced=False)
        connection.close()

    @classmethod
    def provision(
        cls,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    ) -> SqliteAdmissionStoreAdministrationResult:
        """Explicitly create a new current-schema ledger exactly once."""

        try:
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
    def migrate(
        cls,
        configuration: SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
    ) -> SqliteAdmissionStoreAdministrationResult:
        """Explicit single-owner forward migration; never used by open/calls."""

        try:
            config = _validate_configuration(configuration, require_file=True)
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

        connection: sqlite3.Connection | None = None
        commit_attempted = False
        try:
            connection = cls._connect_rw(config)
            cls._configure_connection(connection, config, establish_wal=False)
            application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if application_id != SQLITE_APPLICATION_ID:
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA,
                    "SQLite application_id does not identify an Admission ledger",
                )
            if version > SCHEMA_VERSION:
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA,
                    "ledger schema is newer; downgrade is unsupported",
                )
            if version == SCHEMA_VERSION:
                verifier = cls.__new__(cls)
                verifier.configuration = config
                verifier._clock = None
                verifier._verify_authoritative_connection(
                    connection,
                    allow_fenced=False,
                )
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.ALREADY_CURRENT
                )
            if version < 1:
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.INCOMPATIBLE_SCHEMA,
                    "an unversioned database must be provisioned, not migrated",
                )

            connection.execute("BEGIN EXCLUSIVE")
            metadata = connection.execute(
                "SELECT migration_state FROM admission_ledger_metadata WHERE singleton=1"
            ).fetchall()
            if len(metadata) != 1 or metadata[0][0] != "clean":
                connection.execute("ROLLBACK")
                return _admin_result(
                    SqliteAdmissionStoreAdministrationOutcome.MIGRATION_FAILURE,
                    "migration state is missing or dirty",
                )
            connection.execute(
                "UPDATE admission_ledger_metadata SET migration_state='dirty' WHERE singleton=1"
            )
            for migration_id, resource_name, checksum, data in migrations:
                if migration_id <= version:
                    continue
                for statement in _sql_statements(data):
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO admission_schema_migrations VALUES (?, ?, ?)",
                    (migration_id, resource_name, checksum),
                )
                connection.execute(f"PRAGMA user_version={migration_id}")
                connection.execute(
                    """
                    UPDATE admission_ledger_metadata
                    SET schema_version=?, schema_manifest_id=?
                    WHERE singleton=1
                    """,
                    (migration_id, _schema_manifest_id()),
                )
            connection.execute(
                "UPDATE admission_ledger_metadata SET migration_state='clean' WHERE singleton=1"
            )
            commit_attempted = True
            _commit(connection)
            verifier = cls.__new__(cls)
            verifier.configuration = config
            verifier._clock = None
            verifier._verify_authoritative_connection(connection, allow_fenced=False)
            return _admin_result(
                SqliteAdmissionStoreAdministrationOutcome.MIGRATED
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
        try:
            application_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
            user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if application_id != SQLITE_APPLICATION_ID:
                raise SqliteAdmissionStoreIncompatibleSchemaError(
                    "SQLite application_id does not identify an Admission ledger"
                )
            if user_version != SCHEMA_VERSION:
                direction = "newer" if user_version > SCHEMA_VERSION else "older"
                raise SqliteAdmissionStoreIncompatibleSchemaError(
                    f"Admission ledger schema is {direction}; explicit migration is required"
                )
            if _schema_fingerprint(connection) != _EXPECTED_SCHEMA_FINGERPRINT:
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
            self._verify_migration_history(connection)
            metadata = self._verify_metadata(connection, allow_fenced=allow_fenced)
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
        rows = connection.execute(
            """
            SELECT migration_id, resource_name, sha256
            FROM admission_schema_migrations
            ORDER BY migration_id
            """
        ).fetchall()
        expected = tuple(
            (migration_id, name, checksum)
            for migration_id, name, checksum, _ in _migration_bytes()
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
            or row["schema_version"] != SCHEMA_VERSION
            or row["schema_manifest_id"] != _schema_manifest_id()
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

    def watermark(self) -> tuple[str | None, int | None]:
        """Expose verified watermark evidence for focused diagnostics/tests."""

        connection = self._open_existing(allow_fenced=False)
        try:
            metadata = self._verify_metadata(connection, allow_fenced=False)
            return metadata.decision_time, metadata.decision_time_key
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
            self._verify_metadata(connection, allow_fenced=False)
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
            self._verify_metadata(connection, allow_fenced=False)
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
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "not_yet_current",
                    detail="authoritative decision time precedes Grant issuance",
                )
            if decision >= expires_at:
                self._advance_watermark(connection, decision_text, decision_key)
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "expired",
                    detail="authoritative decision time reached Grant expiry",
                )
            if revocation is not None:
                self._advance_watermark(connection, decision_text, decision_key)
                commit_attempted = True
                _commit(connection)
                self._fault("after_commit_before_response")
                return _result(
                    "revoked",
                    detail="a prior same-ledger revocation prevents Admission",
                )

            self._fault("after_checks")
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
            self._fault("after_insert_before_commit")
            self._advance_watermark(connection, decision_text, decision_key)
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
