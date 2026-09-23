"""Private SQLite vehicle for the AIO-046 admission experiment.

This module is intentionally outside the packaged ``engineering_orchestration``
library.  Its classes and outcome strings are provisional experiment helpers,
not a production store protocol or a canonical Core contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Callable

from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteOutcome,
    assess_agent_action_prerequisites,
)
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import (
    AgentExecutionRun,
    prepare_agent_execution_run,
)
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    validate_agent_operation_tool_binding,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
)
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
)


EXPERIMENT_SCHEMA_VERSION = 1
NORMAL_BUSY_TIMEOUT_MS = 5_000

FAULT_BEFORE_TRANSACTION = "before_transaction"
FAULT_AFTER_BEGIN = "after_begin"
FAULT_AFTER_CHECKS = "after_checks"
FAULT_AFTER_INSERT_BEFORE_COMMIT = "after_insert_before_commit"
FAULT_AFTER_COMMIT_BEFORE_RESPONSE = "after_commit_before_response"

_GRANT_KEYS = {
    "authorization_domain_id",
    "expires_at",
    "grant_id",
    "issued_at",
    "issuer_id",
    "issuer_kind",
    "provenance_reference",
    "run",
}
_BINDING_KEYS = {"run", "tool_id"}
_RUN_KEYS = {"contract", "run_id"}
_CONTRACT_KEYS = {
    "actor_id",
    "environment_id",
    "execution_mode",
    "operation_id",
    "option_id",
    "resource",
    "role_id",
    "runtime_option_id",
    "stage_id",
    "task_id",
    "workflow_id",
}


class ExperimentStorageError(RuntimeError):
    """Fail-closed SQLite or stored-value error."""


class ExperimentProvisioningError(ExperimentStorageError):
    """Controlled one-time ledger provisioning failed."""


class _CommitUnknown(ExperimentStorageError):
    """SQLite did not give the coordinator a known commit result."""


@dataclass(frozen=True)
class TrustedLedgerConfiguration:
    """Trusted harness mapping from one domain to one local SQLite file."""

    authorization_domain_id: str
    database_path: Path
    busy_timeout_ms: int = NORMAL_BUSY_TIMEOUT_MS

    def __post_init__(self) -> None:
        if (
            type(self.authorization_domain_id) is not str
            or not self.authorization_domain_id
        ):
            raise ValueError("authorization_domain_id must be nonempty text")
        if not isinstance(self.database_path, Path):
            raise ValueError("database_path must be a pathlib.Path")
        if not self.database_path.is_absolute():
            raise ValueError("database_path must be absolute")
        lexical_path = str(self.database_path)
        if lexical_path.startswith("\\\\") or lexical_path.startswith("//"):
            raise ValueError("network-share database paths are prohibited")
        if type(self.busy_timeout_ms) is not int or self.busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be a nonnegative integer")


@dataclass(frozen=True)
class SQLiteSettings:
    """Settings verified on an actual experiment connection."""

    sqlite_version: str
    journal_mode: str
    synchronous: int
    busy_timeout_ms: int
    foreign_keys: int
    locking_mode: str
    isolation_level: None
    transaction_mode: str


@dataclass(frozen=True)
class FreshPrerequisiteInputs:
    """New parent containers collected by the controlled synthetic source."""

    candidate_result: AgentExecutionCandidatePrerequisiteResult
    requirement: OperationRequirement
    capability_result: RuntimeOperationCapabilityValidationResult
    permission_result: EnvironmentOperationPermissionValidationResult
    authorization_result: AgentExecutionAuthorizationValidationResult
    environment_id: str
    execution_mode: str
    collection_serial: int


@dataclass(frozen=True)
class AdmissionRecord:
    """Decoded immutable admission aggregate."""

    grant: AgentExecutionAuthorizationGrant
    binding: AgentOperationToolBinding
    decision_time: str


@dataclass(frozen=True)
class RevocationRecord:
    """Decoded immutable revocation tombstone."""

    grant: AgentExecutionAuthorizationGrant
    revoker_kind: str
    revoker_id: str
    decision_time: str


@dataclass(frozen=True)
class AdmissionResult:
    """Provisional result; outcome strings are deliberately not a public enum."""

    outcome: str
    record: AdmissionRecord | None = None
    detail: str = ""
    retryable: bool = False
    indeterminate: bool = False


@dataclass(frozen=True)
class RevocationResult:
    """Provisional revocation result."""

    outcome: str
    record: RevocationRecord | None = None
    detail: str = ""
    retryable: bool = False
    indeterminate: bool = False


@dataclass(frozen=True)
class _TrustedAdmissionEnvelope:
    capability: object
    grant: AgentExecutionAuthorizationGrant
    binding: AgentOperationToolBinding
    expected_authorization_domain_id: str


@dataclass(frozen=True)
class _TrustedRevocationEnvelope:
    capability: object
    grant: AgentExecutionAuthorizationGrant
    expected_authorization_domain_id: str
    revoker_kind: str
    revoker_id: str


class SyntheticTrustCoordinator:
    """Explicit out-of-band trust stub for exact synthetic payloads.

    The private in-memory capability models a trusted coordinator boundary.  It
    is not cryptography and makes no operational authentication claim.
    """

    def __init__(self) -> None:
        self.__capability = object()
        self.__issued_admissions: dict[int, _TrustedAdmissionEnvelope] = {}
        self.__issued_revocations: dict[int, _TrustedRevocationEnvelope] = {}

    def trusted_admission(
        self,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
        *,
        expected_authorization_domain_id: str,
    ) -> object:
        """Mint one exact synthetic admission envelope."""

        envelope = _TrustedAdmissionEnvelope(
            self.__capability,
            grant,
            binding,
            expected_authorization_domain_id,
        )
        self.__issued_admissions[id(envelope)] = envelope
        return envelope

    def trusted_revocation(
        self,
        grant: AgentExecutionAuthorizationGrant,
        *,
        expected_authorization_domain_id: str,
    ) -> object:
        """Mint an issuer-owned synthetic revocation envelope."""

        envelope = _TrustedRevocationEnvelope(
            self.__capability,
            grant,
            expected_authorization_domain_id,
            grant.issuer_kind,
            grant.issuer_id,
        )
        self.__issued_revocations[id(envelope)] = envelope
        return envelope

    def _open_admission(
        self,
        supplied: object,
    ) -> _TrustedAdmissionEnvelope | None:
        if type(supplied) is not _TrustedAdmissionEnvelope:
            return None
        if supplied.capability is not self.__capability:
            return None
        if self.__issued_admissions.get(id(supplied)) is not supplied:
            return None
        return supplied

    def _open_revocation(
        self,
        supplied: object,
    ) -> _TrustedRevocationEnvelope | None:
        if type(supplied) is not _TrustedRevocationEnvelope:
            return None
        if supplied.capability is not self.__capability:
            return None
        if self.__issued_revocations.get(id(supplied)) is not supplied:
            return None
        return supplied


class FixedAuthorityClock:
    """Controlled authority-owned clock stub used by the experiment harness."""

    def __init__(
        self,
        instant: datetime | None = None,
        *,
        failure: str | None = None,
    ) -> None:
        self._instant = instant
        self._failure = failure
        self.sample_count = 0

    def now(self) -> datetime:
        """Return the controlled instant or fail without a fallback clock."""

        self.sample_count += 1
        if self._failure is not None:
            raise RuntimeError(self._failure)
        if self._instant is None:
            raise RuntimeError("authority clock has no configured instant")
        return self._instant


class SyntheticFreshPrerequisiteSource:
    """Creates genuinely new positive parent values for each collection.

    The source is a controlled trust stub.  It creates new parent result,
    observation, requirement, and evidence objects on every call and then lets
    the coordinator invoke the real AIO-040 assessment API.
    """

    def __init__(
        self,
        *,
        execution_mode: str,
        subject_overrides: dict[str, str] | None = None,
        failure: str | None = None,
    ) -> None:
        self.execution_mode = execution_mode
        self.subject_overrides = dict(subject_overrides or {})
        self.failure = failure
        self.collection_count = 0
        self.parent_identity_history: list[tuple[int, ...]] = []
        self.collected_snapshots: list[FreshPrerequisiteInputs] = []

    def collect(self, run: AgentExecutionRun) -> FreshPrerequisiteInputs:
        """Collect new synthetic parents for the supplied exact Run."""

        self.collection_count += 1
        if self.failure is not None:
            raise RuntimeError(self.failure)

        contract = run.contract

        def value(field: str) -> str:
            return self.subject_overrides.get(field, getattr(contract, field))

        responsibility_key = (
            value("task_id"),
            value("workflow_id"),
            value("stage_id"),
            value("role_id"),
        )
        actor_id = value("actor_id")
        runtime_option_id = value("runtime_option_id")
        option_id = value("option_id")
        environment_id = value("environment_id")
        operation_id = value("operation_id")
        resource = value("resource")

        candidate_result = AgentExecutionCandidatePrerequisiteResult(
            valid=True,
            findings=(),
            responsibility_key=responsibility_key,
            actor_id=actor_id,
            runtime_option_id=runtime_option_id,
            option_id=option_id,
            outcome=AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
            reasons=(
                AgentExecutionCandidatePrerequisiteReason.
                ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
            ),
        )
        requirement = OperationRequirement(operation_id, resource)
        capability_observation = RuntimeOperationCapabilityObservation(
            runtime_option_id,
            operation_id,
            RuntimeOperationCapabilityState.PRESENT,
        )
        capability_result = RuntimeOperationCapabilityValidationResult(
            True,
            (),
            (capability_observation,),
        )
        permission_observation = EnvironmentOperationPermissionObservation(
            runtime_option_id,
            environment_id,
            operation_id,
            resource,
            EnvironmentOperationPermissionState.ALLOWED,
        )
        permission_result = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (permission_observation,),
        )
        task_id, workflow_id, stage_id, role_id = responsibility_key
        authorization_evidence = AgentExecutionAuthorizationEvidence(
            task_id,
            workflow_id,
            stage_id,
            role_id,
            actor_id,
            runtime_option_id,
            option_id,
            environment_id,
            operation_id,
            resource,
            AgentExecutionAuthorizationAuthorityKind.HUMAN,
            "human::synthetic-authority",
            f"aio-046:fresh:{self.collection_count}",
            AgentExecutionAuthorizationState.GRANTED,
        )
        authorization_result = AgentExecutionAuthorizationValidationResult(
            True,
            (),
            (authorization_evidence,),
        )
        self.parent_identity_history.append(
            (
                id(candidate_result),
                id(requirement),
                id(capability_observation),
                id(permission_observation),
                id(authorization_evidence),
            )
        )
        snapshot = FreshPrerequisiteInputs(
            candidate_result,
            requirement,
            capability_result,
            permission_result,
            authorization_result,
            environment_id,
            self.execution_mode,
            self.collection_count,
        )
        self.collected_snapshots.append(snapshot)
        return snapshot


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
    return {
        "run_id": run.run_id,
        "contract": _contract_document(run.contract),
    }


def _grant_document(
    grant: AgentExecutionAuthorizationGrant,
) -> dict[str, object]:
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
    return {
        "run": _run_document(binding.run),
        "tool_id": binding.tool_id,
    }


def _canonical_json(document: object) -> str:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def encode_grant(grant: AgentExecutionAuthorizationGrant) -> str:
    """Encode one complete Grant in the private deterministic format."""

    validation = validate_agent_execution_authorization_grant(grant)
    if not validation.valid:
        raise ValueError("cannot encode an intrinsically invalid Grant")
    return _canonical_json(_grant_document(grant))


def encode_binding(binding: AgentOperationToolBinding) -> str:
    """Encode one complete Binding in the private deterministic format."""

    validation = validate_agent_operation_tool_binding(binding)
    if not validation.valid:
        raise ValueError("cannot encode an intrinsically invalid Binding")
    return _canonical_json(_binding_document(binding))


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-finite JSON token is prohibited: {value}")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load_canonical_json(text: str) -> object:
    if type(text) is not str:
        raise ValueError("stored encoding must be exact text")
    try:
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise ValueError("stored encoding is invalid JSON") from error


def _require_object(
    value: object,
    keys: set[str],
    category: str,
) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{category} has a noncanonical object shape")
    return value


def _decode_contract(document: object) -> AgentExecutionContract:
    value = _require_object(document, _CONTRACT_KEYS, "Contract")
    return AgentExecutionContract(
        task_id=value["task_id"],  # type: ignore[arg-type]
        workflow_id=value["workflow_id"],  # type: ignore[arg-type]
        stage_id=value["stage_id"],  # type: ignore[arg-type]
        role_id=value["role_id"],  # type: ignore[arg-type]
        actor_id=value["actor_id"],  # type: ignore[arg-type]
        runtime_option_id=value["runtime_option_id"],  # type: ignore[arg-type]
        option_id=value["option_id"],  # type: ignore[arg-type]
        environment_id=value["environment_id"],  # type: ignore[arg-type]
        operation_id=value["operation_id"],  # type: ignore[arg-type]
        resource=value["resource"],  # type: ignore[arg-type]
        execution_mode=value["execution_mode"],  # type: ignore[arg-type]
    )


def _decode_run(document: object) -> AgentExecutionRun:
    value = _require_object(document, _RUN_KEYS, "Run")
    return AgentExecutionRun(
        run_id=value["run_id"],  # type: ignore[arg-type]
        contract=_decode_contract(value["contract"]),
    )


def decode_grant(text: str) -> AgentExecutionAuthorizationGrant:
    """Decode, intrinsically validate, and canonicality-check one Grant."""

    document = _require_object(
        _load_canonical_json(text),
        _GRANT_KEYS,
        "Grant",
    )
    grant = AgentExecutionAuthorizationGrant(
        grant_id=document["grant_id"],  # type: ignore[arg-type]
        run=_decode_run(document["run"]),
        authorization_domain_id=document[
            "authorization_domain_id"
        ],  # type: ignore[arg-type]
        issuer_kind=document["issuer_kind"],  # type: ignore[arg-type]
        issuer_id=document["issuer_id"],  # type: ignore[arg-type]
        provenance_reference=document[
            "provenance_reference"
        ],  # type: ignore[arg-type]
        issued_at=document["issued_at"],  # type: ignore[arg-type]
        expires_at=document["expires_at"],  # type: ignore[arg-type]
    )
    validation = validate_agent_execution_authorization_grant(grant)
    if not validation.valid:
        raise ValueError("decoded Grant is intrinsically invalid")
    if encode_grant(grant) != text:
        raise ValueError("stored Grant encoding is not canonical")
    return grant


def decode_binding(text: str) -> AgentOperationToolBinding:
    """Decode, intrinsically validate, and canonicality-check one Binding."""

    document = _require_object(
        _load_canonical_json(text),
        _BINDING_KEYS,
        "Binding",
    )
    binding = AgentOperationToolBinding(
        run=_decode_run(document["run"]),
        tool_id=document["tool_id"],  # type: ignore[arg-type]
    )
    validation = validate_agent_operation_tool_binding(binding)
    if not validation.valid:
        raise ValueError("decoded Binding is intrinsically invalid")
    if encode_binding(binding) != text:
        raise ValueError("stored Binding encoding is not canonical")
    return binding


def grant_identity(
    grant: AgentExecutionAuthorizationGrant,
) -> tuple[str, str, str, str]:
    """Return the canonical composite Grant identity."""

    return (
        grant.authorization_domain_id,
        grant.issuer_kind,
        grant.issuer_id,
        grant.grant_id,
    )


def _parse_grant_instant(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except (TypeError, ValueError) as error:
        raise ValueError("validated Grant timestamp could not be parsed") from error


def _canonical_decision_time(value: object) -> tuple[datetime, str, int]:
    if type(value) is not datetime:
        raise ValueError("authority clock must return an exact datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("authority clock must return an aware UTC datetime")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError("authority clock must return a zero-offset UTC datetime")
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
    key = seconds * 1_000_000 + utc_value.microsecond
    return utc_value, text, key


def _parse_decision_time(value: str) -> tuple[datetime, int]:
    if type(value) is not str or not value.endswith("Z"):
        raise ExperimentStorageError("stored decision time is malformed")
    try:
        instant = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ExperimentStorageError("stored decision time is malformed") from error
    canonical, text, key = _canonical_decision_time(instant)
    if text != value:
        raise ExperimentStorageError("stored decision time is noncanonical")
    return canonical, key


def _is_busy(error: BaseException) -> bool:
    code = getattr(error, "sqlite_errorcode", None)
    if code in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
        return True
    lowered = str(error).lower()
    return "locked" in lowered or "busy" in lowered


def _safe_rollback(connection: sqlite3.Connection) -> None:
    try:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
    except sqlite3.Error:
        pass


def _commit(connection: sqlite3.Connection) -> None:
    try:
        connection.execute("COMMIT")
    except sqlite3.Error as error:
        raise _CommitUnknown("SQLite COMMIT result is unknown") from error


def _invoke_fault(
    fault_hook: Callable[[str], None] | None,
    point: str,
) -> None:
    if fault_hook is not None:
        fault_hook(point)


class SQLiteAuthorizationDomainLedger:
    """One private experiment coordinator for one trusted ledger mapping."""

    def __init__(
        self,
        configuration: TrustedLedgerConfiguration,
        *,
        authority_clock: object,
        trust_coordinator: SyntheticTrustCoordinator,
    ) -> None:
        if type(configuration) is not TrustedLedgerConfiguration:
            raise TypeError("configuration must be trusted ledger configuration")
        if type(trust_coordinator) is not SyntheticTrustCoordinator:
            raise TypeError("trust_coordinator must be the synthetic stub")
        self.configuration = configuration
        self.authority_clock = authority_clock
        self.trust_coordinator = trust_coordinator

    @staticmethod
    def provision(
        configuration: TrustedLedgerConfiguration,
    ) -> SQLiteSettings:
        """Provision a new database exactly once under trusted harness control."""

        if type(configuration) is not TrustedLedgerConfiguration:
            raise ExperimentProvisioningError("invalid trusted configuration")
        path = configuration.database_path
        if path.exists():
            raise ExperimentProvisioningError(
                "ledger provisioning refuses an existing database path"
            )
        if not path.parent.is_dir():
            raise ExperimentProvisioningError(
                "ledger parent directory must already exist"
            )
        schema_path = Path(__file__).with_name("schema.sql")
        try:
            ddl = schema_path.read_text(encoding="utf-8")
        except OSError as error:
            raise ExperimentProvisioningError(
                "private experiment DDL is unavailable"
            ) from error

        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                str(path),
                timeout=configuration.busy_timeout_ms / 1_000,
                isolation_level=None,
            )
            SQLiteAuthorizationDomainLedger._configure_connection(
                connection,
                configuration,
                establish_wal=True,
            )
            connection.executescript("BEGIN IMMEDIATE;\n" + ddl)
            connection.execute(
                """
                INSERT INTO ledger_metadata (
                    singleton,
                    schema_version,
                    authorization_domain_id,
                    revocation_state_complete,
                    last_decision_time,
                    last_decision_time_key
                ) VALUES (1, ?, ?, 1, NULL, NULL)
                """,
                (
                    EXPERIMENT_SCHEMA_VERSION,
                    configuration.authorization_domain_id,
                ),
            )
            _commit(connection)
            settings = SQLiteAuthorizationDomainLedger._verified_settings(
                connection,
                configuration,
            )
            SQLiteAuthorizationDomainLedger._verify_metadata(
                connection,
                configuration.authorization_domain_id,
            )
            return settings
        except _CommitUnknown as error:
            if connection is not None:
                _safe_rollback(connection)
            raise ExperimentProvisioningError(
                "ledger provisioning commit is indeterminate"
            ) from error
        except (OSError, sqlite3.Error, ExperimentStorageError) as error:
            if connection is not None:
                _safe_rollback(connection)
            raise ExperimentProvisioningError(
                "ledger provisioning failed closed"
            ) from error
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _configure_connection(
        connection: sqlite3.Connection,
        configuration: TrustedLedgerConfiguration,
        *,
        establish_wal: bool,
    ) -> None:
        connection.row_factory = sqlite3.Row
        connection.execute(
            f"PRAGMA busy_timeout={configuration.busy_timeout_ms}"
        )
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA locking_mode=NORMAL")
        if establish_wal:
            journal = connection.execute("PRAGMA journal_mode=WAL").fetchone()
            if journal is None or str(journal[0]).lower() != "wal":
                raise ExperimentStorageError("WAL mode could not be established")
        connection.execute("PRAGMA synchronous=FULL")
        SQLiteAuthorizationDomainLedger._verified_settings(
            connection,
            configuration,
        )

    @staticmethod
    def _verified_settings(
        connection: sqlite3.Connection,
        configuration: TrustedLedgerConfiguration,
    ) -> SQLiteSettings:
        journal_mode = str(
            connection.execute("PRAGMA journal_mode").fetchone()[0]
        ).lower()
        synchronous = int(
            connection.execute("PRAGMA synchronous").fetchone()[0]
        )
        busy_timeout = int(
            connection.execute("PRAGMA busy_timeout").fetchone()[0]
        )
        foreign_keys = int(
            connection.execute("PRAGMA foreign_keys").fetchone()[0]
        )
        locking_mode = str(
            connection.execute("PRAGMA locking_mode").fetchone()[0]
        ).lower()
        if journal_mode != "wal":
            raise ExperimentStorageError("ledger journal_mode is not WAL")
        if synchronous != 2:
            raise ExperimentStorageError("ledger synchronous mode is not FULL")
        if busy_timeout != configuration.busy_timeout_ms:
            raise ExperimentStorageError("ledger busy timeout is not configured")
        if foreign_keys != 1:
            raise ExperimentStorageError("ledger foreign keys are not enabled")
        if locking_mode != "normal":
            raise ExperimentStorageError("ledger locking mode is not normal")
        if connection.isolation_level is not None:
            raise ExperimentStorageError("connection is not in autocommit mode")
        return SQLiteSettings(
            sqlite3.sqlite_version,
            journal_mode,
            synchronous,
            busy_timeout,
            foreign_keys,
            locking_mode,
            None,
            "BEGIN IMMEDIATE",
        )

    def _open_existing(self) -> sqlite3.Connection:
        uri = self.configuration.database_path.as_uri() + "?mode=rw"
        try:
            connection = sqlite3.connect(
                uri,
                uri=True,
                timeout=self.configuration.busy_timeout_ms / 1_000,
                isolation_level=None,
            )
            self._configure_connection(
                connection,
                self.configuration,
                establish_wal=False,
            )
            return connection
        except (sqlite3.Error, ExperimentStorageError):
            if "connection" in locals():
                connection.close()
            raise
        except Exception as error:
            if "connection" in locals():
                connection.close()
            raise ExperimentStorageError(
                "ledger connection verification failed"
            ) from error

    @staticmethod
    def _verify_metadata(
        connection: sqlite3.Connection,
        authorization_domain_id: str,
    ) -> tuple[str | None, int | None]:
        try:
            rows = connection.execute(
                """
                SELECT
                    singleton,
                    schema_version,
                    authorization_domain_id,
                    revocation_state_complete,
                    last_decision_time,
                    last_decision_time_key
                FROM ledger_metadata
                """
            ).fetchall()
        except sqlite3.Error as error:
            raise ExperimentStorageError("ledger metadata is unavailable") from error
        if len(rows) != 1:
            raise ExperimentStorageError("ledger metadata is not singleton")
        row = rows[0]
        if (
            type(row["singleton"]) is not int
            or row["singleton"] != 1
            or type(row["schema_version"]) is not int
            or row["schema_version"] != EXPERIMENT_SCHEMA_VERSION
            or type(row["authorization_domain_id"]) is not str
            or row["authorization_domain_id"] != authorization_domain_id
            or type(row["revocation_state_complete"]) is not int
            or row["revocation_state_complete"] != 1
        ):
            raise ExperimentStorageError("ledger metadata is mismatched")
        decision_time = row["last_decision_time"]
        decision_key = row["last_decision_time_key"]
        if decision_time is None and decision_key is None:
            return None, None
        if type(decision_time) is not str or type(decision_key) is not int:
            raise ExperimentStorageError("ledger watermark is incoherent")
        _, parsed_key = _parse_decision_time(decision_time)
        if parsed_key != decision_key:
            raise ExperimentStorageError("ledger watermark encoding conflicts")
        return decision_time, decision_key

    def verified_settings(self) -> SQLiteSettings:
        """Open the configured existing ledger and verify all settings."""

        connection = self._open_existing()
        try:
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            return self._verified_settings(connection, self.configuration)
        finally:
            connection.close()

    @staticmethod
    def _admission_from_row(row: sqlite3.Row) -> AdmissionRecord:
        try:
            grant = decode_grant(row["grant_json"])
            binding = decode_binding(row["binding_json"])
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise ExperimentStorageError("stored admission cannot be decoded") from error
        if binding.run != grant.run:
            raise ExperimentStorageError("stored admission Run values conflict")
        identity = grant_identity(grant)
        indexed_identity = (
            row["authorization_domain_id"],
            row["issuer_kind"],
            row["issuer_id"],
            row["grant_id"],
        )
        if identity != indexed_identity or grant.run.run_id != row["run_id"]:
            raise ExperimentStorageError("stored admission index conflicts")
        decision_time = row["decision_time"]
        decision_key = row["decision_time_key"]
        if type(decision_time) is not str or type(decision_key) is not int:
            raise ExperimentStorageError("stored admission decision is invalid")
        _, parsed_key = _parse_decision_time(decision_time)
        if parsed_key != decision_key:
            raise ExperimentStorageError("stored admission decision conflicts")
        return AdmissionRecord(grant, binding, decision_time)

    @staticmethod
    def _revocation_from_row(row: sqlite3.Row) -> RevocationRecord:
        try:
            grant = decode_grant(row["grant_json"])
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise ExperimentStorageError("stored revocation cannot be decoded") from error
        identity = grant_identity(grant)
        indexed_identity = (
            row["authorization_domain_id"],
            row["issuer_kind"],
            row["issuer_id"],
            row["grant_id"],
        )
        if (
            identity != indexed_identity
            or grant.run.run_id != row["run_id"]
            or grant.issuer_kind != row["revoker_kind"]
            or grant.issuer_id != row["revoker_id"]
        ):
            raise ExperimentStorageError("stored revocation index conflicts")
        decision_time = row["decision_time"]
        decision_key = row["decision_time_key"]
        if type(decision_time) is not str or type(decision_key) is not int:
            raise ExperimentStorageError("stored revocation decision is invalid")
        _, parsed_key = _parse_decision_time(decision_time)
        if parsed_key != decision_key:
            raise ExperimentStorageError("stored revocation decision conflicts")
        return RevocationRecord(
            grant,
            row["revoker_kind"],
            row["revoker_id"],
            decision_time,
        )

    @staticmethod
    def _find_admission_by_identity(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AdmissionRecord | None:
        row = connection.execute(
            """
            SELECT * FROM admissions
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND issuer_kind = ? COLLATE BINARY
              AND issuer_id = ? COLLATE BINARY
              AND grant_id = ? COLLATE BINARY
            """,
            grant_identity(grant),
        ).fetchone()
        if row is None:
            return None
        return SQLiteAuthorizationDomainLedger._admission_from_row(row)

    @staticmethod
    def _find_admission_by_run(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AdmissionRecord | None:
        row = connection.execute(
            """
            SELECT * FROM admissions
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND run_id = ? COLLATE BINARY
            """,
            (grant.authorization_domain_id, grant.run.run_id),
        ).fetchone()
        if row is None:
            return None
        return SQLiteAuthorizationDomainLedger._admission_from_row(row)

    @staticmethod
    def _classify_existing_admission(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> AdmissionResult | None:
        existing = SQLiteAuthorizationDomainLedger._find_admission_by_identity(
            connection,
            grant,
        )
        if existing is not None:
            if existing.grant != grant:
                return AdmissionResult(
                    "grant_identity_conflict",
                    detail="composite Grant identity is bound to another value",
                )
            if existing.binding != binding:
                return AdmissionResult(
                    "binding_conflict",
                    detail="exact Grant is bound to another Tool Binding",
                )
            return AdmissionResult("existing_exact_admission", existing)
        run_existing = SQLiteAuthorizationDomainLedger._find_admission_by_run(
            connection,
            grant,
        )
        if run_existing is not None:
            return AdmissionResult(
                "run_conflict",
                detail="domain and Run ID are already occupied",
            )
        return None

    def _historical_precheck(
        self,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
    ) -> AdmissionResult | None:
        connection = self._open_existing()
        try:
            connection.execute("BEGIN")
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            result = self._classify_existing_admission(
                connection,
                grant,
                binding,
            )
            connection.execute("ROLLBACK")
            return result
        except Exception:
            _safe_rollback(connection)
            raise
        finally:
            connection.close()

    def _fresh_expected_run(
        self,
        grant: AgentExecutionAuthorizationGrant,
        binding: AgentOperationToolBinding,
        fresh_source: object,
    ) -> AdmissionResult | AgentExecutionRun:
        if type(fresh_source) is not SyntheticFreshPrerequisiteSource:
            return AdmissionResult(
                "invalid",
                detail="the controlled fresh prerequisite source is required",
            )
        try:
            inputs = fresh_source.collect(grant.run)
        except Exception as error:
            return AdmissionResult(
                "invalid",
                detail=f"fresh prerequisite collection failed: {error}",
            )
        if type(inputs) is not FreshPrerequisiteInputs:
            return AdmissionResult(
                "invalid",
                detail="fresh source returned a noncanonical container",
            )
        assessment = assess_agent_action_prerequisites(
            inputs.candidate_result,
            inputs.requirement,
            inputs.capability_result,
            inputs.permission_result,
            inputs.authorization_result,
            environment_id=inputs.environment_id,
        )
        if (
            not assessment.valid
            or assessment.outcome is not AgentActionPrerequisiteOutcome.SATISFIED
        ):
            codes = ",".join(finding.code for finding in assessment.findings)
            return AdmissionResult(
                "invalid",
                detail=(
                    "fresh AIO-040 prerequisites are not satisfied"
                    + (f": {codes}" if codes else "")
                ),
            )
        prepared = prepare_agent_execution_run(
            grant.run.contract,
            assessment,
            execution_mode=inputs.execution_mode,
            run_id=grant.run.run_id,
        )
        if not prepared.valid or prepared.run is None:
            codes = ",".join(finding.code for finding in prepared.findings)
            return AdmissionResult(
                "invalid",
                detail=f"fresh Run reconstruction failed: {codes}",
            )
        if grant.run != binding.run or grant.run != prepared.run:
            return AdmissionResult(
                "invalid",
                detail="full Grant/Binding/fresh expected Run equality failed",
            )
        return prepared.run

    def _sample_clock(
        self,
        connection: sqlite3.Connection,
    ) -> tuple[datetime, str, int] | AdmissionResult:
        try:
            instant = self.authority_clock.now()
            decision, text, key = _canonical_decision_time(instant)
        except Exception as error:
            return AdmissionResult(
                "clock_failure",
                detail=f"authority clock failed closed: {error}",
            )
        _, prior_key = self._verify_metadata(
            connection,
            self.configuration.authorization_domain_id,
        )
        if prior_key is not None and key < prior_key:
            return AdmissionResult(
                "clock_regression",
                detail="authority clock moved behind the committed watermark",
            )
        return decision, text, key

    @staticmethod
    def _advance_watermark(
        connection: sqlite3.Connection,
        decision_time: str,
        decision_key: int,
    ) -> None:
        cursor = connection.execute(
            """
            UPDATE ledger_metadata
            SET last_decision_time = ?, last_decision_time_key = ?
            WHERE singleton = 1
            """,
            (decision_time, decision_key),
        )
        if cursor.rowcount != 1:
            raise ExperimentStorageError("watermark update lost ledger ownership")

    @staticmethod
    def _find_revocation_by_identity(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> RevocationRecord | None:
        row = connection.execute(
            """
            SELECT * FROM revocations
            WHERE authorization_domain_id = ? COLLATE BINARY
              AND issuer_kind = ? COLLATE BINARY
              AND issuer_id = ? COLLATE BINARY
              AND grant_id = ? COLLATE BINARY
            """,
            grant_identity(grant),
        ).fetchone()
        if row is None:
            return None
        return SQLiteAuthorizationDomainLedger._revocation_from_row(row)

    @staticmethod
    def _classify_revocation_for_admission(
        connection: sqlite3.Connection,
        grant: AgentExecutionAuthorizationGrant,
    ) -> str | None:
        revocation = (
            SQLiteAuthorizationDomainLedger._find_revocation_by_identity(
                connection,
                grant,
            )
        )
        if revocation is not None:
            if revocation.grant != grant:
                raise ExperimentStorageError(
                    "revocation identity is rebound to another Grant"
                )
            return "revoked"
        return None

    def admit_or_return_existing(
        self,
        trusted_request: object,
        *,
        fresh_source: object,
        fault_hook: Callable[[str], None] | None = None,
    ) -> AdmissionResult:
        """Create one atomic admission or return the exact durable history."""

        envelope = self.trust_coordinator._open_admission(trusted_request)
        if envelope is None:
            return AdmissionResult(
                "untrusted",
                detail="synthetic trusted boundary rejected the request",
            )
        grant = envelope.grant
        binding = envelope.binding
        expected_domain = envelope.expected_authorization_domain_id

        grant_validation = validate_agent_execution_authorization_grant(grant)
        binding_validation = validate_agent_operation_tool_binding(binding)
        if not grant_validation.valid or not binding_validation.valid:
            codes = [finding.code for finding in grant_validation.findings]
            codes.extend(finding.code for finding in binding_validation.findings)
            return AdmissionResult(
                "invalid",
                detail="intrinsic validation failed: " + ",".join(codes),
            )
        if expected_domain != self.configuration.authorization_domain_id:
            return AdmissionResult(
                "domain_mismatch",
                detail="trusted expected domain does not own this ledger",
            )
        if grant.authorization_domain_id != expected_domain:
            return AdmissionResult(
                "domain_mismatch",
                detail="Grant authorization domain differs from expected domain",
            )
        if grant.run != binding.run:
            return AdmissionResult(
                "invalid",
                detail="Grant and Tool Binding complete Runs differ",
            )

        try:
            historical = self._historical_precheck(grant, binding)
        except (sqlite3.Error, ExperimentStorageError) as error:
            return self._storage_admission_failure(error)
        if historical is not None:
            return historical

        expected_run = self._fresh_expected_run(
            grant,
            binding,
            fresh_source,
        )
        if type(expected_run) is AdmissionResult:
            return expected_run
        if grant.run != binding.run or grant.run != expected_run:
            return AdmissionResult(
                "invalid",
                detail="three-way complete Run equality failed",
            )

        connection: sqlite3.Connection | None = None
        committed = False
        try:
            _invoke_fault(fault_hook, FAULT_BEFORE_TRANSACTION)
            connection = self._open_existing()
            connection.execute("BEGIN IMMEDIATE")
            _invoke_fault(fault_hook, FAULT_AFTER_BEGIN)
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            concurrent = self._classify_existing_admission(
                connection,
                grant,
                binding,
            )
            if concurrent is not None:
                if concurrent.outcome == "existing_exact_admission":
                    _commit(connection)
                    committed = True
                    _invoke_fault(
                        fault_hook,
                        FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                    )
                    return concurrent
                connection.execute("ROLLBACK")
                return concurrent

            sampled = self._sample_clock(connection)
            if type(sampled) is AdmissionResult:
                connection.execute("ROLLBACK")
                return sampled
            decision, decision_text, decision_key = sampled

            issued_at = _parse_grant_instant(grant.issued_at)
            expires_at = _parse_grant_instant(grant.expires_at)
            if decision < issued_at:
                self._advance_watermark(
                    connection,
                    decision_text,
                    decision_key,
                )
                _commit(connection)
                committed = True
                _invoke_fault(
                    fault_hook,
                    FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                )
                return AdmissionResult(
                    "not_yet_current",
                    detail="decision time precedes Grant issuance",
                )
            if decision >= expires_at:
                self._advance_watermark(
                    connection,
                    decision_text,
                    decision_key,
                )
                _commit(connection)
                committed = True
                _invoke_fault(
                    fault_hook,
                    FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                )
                return AdmissionResult(
                    "expired",
                    detail="decision time reached or passed Grant expiry",
                )

            revocation_state = self._classify_revocation_for_admission(
                connection,
                grant,
            )
            if revocation_state is not None:
                self._advance_watermark(
                    connection,
                    decision_text,
                    decision_key,
                )
                _commit(connection)
                committed = True
                _invoke_fault(
                    fault_hook,
                    FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                )
                return AdmissionResult(
                    revocation_state,
                    detail="same-ledger revocation prevents new admission",
                )

            _invoke_fault(fault_hook, FAULT_AFTER_CHECKS)
            grant_json = encode_grant(grant)
            binding_json = encode_binding(binding)
            connection.execute(
                """
                INSERT INTO admissions (
                    authorization_domain_id,
                    issuer_kind,
                    issuer_id,
                    grant_id,
                    run_id,
                    grant_json,
                    binding_json,
                    decision_time,
                    decision_time_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *grant_identity(grant),
                    grant.run.run_id,
                    grant_json,
                    binding_json,
                    decision_text,
                    decision_key,
                ),
            )
            _invoke_fault(
                fault_hook,
                FAULT_AFTER_INSERT_BEFORE_COMMIT,
            )
            self._advance_watermark(
                connection,
                decision_text,
                decision_key,
            )
            _commit(connection)
            committed = True
            _invoke_fault(
                fault_hook,
                FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
            )
            return AdmissionResult(
                "newly_admitted",
                AdmissionRecord(grant, binding, decision_text),
            )
        except _CommitUnknown as error:
            if connection is not None:
                _safe_rollback(connection)
            return AdmissionResult(
                "commit_unknown",
                detail=str(error),
                retryable=True,
                indeterminate=True,
            )
        except (sqlite3.Error, ExperimentStorageError, OSError) as error:
            if connection is not None and not committed:
                _safe_rollback(connection)
            if committed:
                return AdmissionResult(
                    "commit_unknown",
                    detail="failure occurred after a known commit",
                    retryable=True,
                    indeterminate=True,
                )
            return self._storage_admission_failure(error)
        except Exception as error:
            if connection is not None and not committed:
                _safe_rollback(connection)
            if committed:
                return AdmissionResult(
                    "commit_unknown",
                    detail="response failed after commit",
                    retryable=True,
                    indeterminate=True,
                )
            return AdmissionResult(
                "storage_failure",
                detail=f"transaction failed closed: {error}",
            )
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _storage_admission_failure(error: BaseException) -> AdmissionResult:
        if _is_busy(error):
            return AdmissionResult(
                "storage_busy",
                detail="authoritative ledger is busy",
                retryable=True,
            )
        return AdmissionResult(
            "storage_failure",
            detail=f"authoritative ledger failed closed: {error}",
        )

    def revoke(
        self,
        trusted_request: object,
        *,
        fault_hook: Callable[[str], None] | None = None,
    ) -> RevocationResult:
        """Append one immutable issuer-owned revocation tombstone."""

        envelope = self.trust_coordinator._open_revocation(trusted_request)
        if envelope is None:
            return RevocationResult(
                "untrusted",
                detail="synthetic trusted boundary rejected revocation",
            )
        grant = envelope.grant
        validation = validate_agent_execution_authorization_grant(grant)
        if not validation.valid:
            return RevocationResult(
                "invalid",
                detail="revocation Grant is intrinsically invalid",
            )
        if (
            envelope.expected_authorization_domain_id
            != self.configuration.authorization_domain_id
            or grant.authorization_domain_id
            != envelope.expected_authorization_domain_id
        ):
            return RevocationResult(
                "domain_mismatch",
                detail="revocation domain does not own this ledger",
            )
        if (
            envelope.revoker_kind != grant.issuer_kind
            or envelope.revoker_id != grant.issuer_id
        ):
            return RevocationResult(
                "untrusted",
                detail="revoker is not the original synthetic issuer",
            )

        connection: sqlite3.Connection | None = None
        committed = False
        try:
            _invoke_fault(fault_hook, FAULT_BEFORE_TRANSACTION)
            connection = self._open_existing()
            connection.execute("BEGIN IMMEDIATE")
            _invoke_fault(fault_hook, FAULT_AFTER_BEGIN)
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            admitted = self._find_admission_by_identity(connection, grant)
            if admitted is not None and admitted.grant != grant:
                connection.execute("ROLLBACK")
                return RevocationResult(
                    "revocation_identity_conflict",
                    detail=(
                        "admission identity is already bound to another Grant"
                    ),
                )
            existing = self._find_revocation_by_identity(connection, grant)
            if existing is not None:
                if (
                    existing.grant != grant
                    or existing.revoker_kind != envelope.revoker_kind
                    or existing.revoker_id != envelope.revoker_id
                ):
                    connection.execute("ROLLBACK")
                    return RevocationResult(
                        "revocation_identity_conflict",
                        detail="revocation identity is already rebound",
                    )
                _commit(connection)
                committed = True
                _invoke_fault(
                    fault_hook,
                    FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                )
                return RevocationResult("existing_exact_revocation", existing)
            try:
                instant = self.authority_clock.now()
                _, decision_text, decision_key = _canonical_decision_time(
                    instant
                )
            except Exception as error:
                connection.execute("ROLLBACK")
                return RevocationResult(
                    "clock_failure",
                    detail=f"authority clock failed closed: {error}",
                )
            _, prior_key = self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            if prior_key is not None and decision_key < prior_key:
                connection.execute("ROLLBACK")
                return RevocationResult(
                    "clock_regression",
                    detail="authority clock moved behind the watermark",
                )

            _invoke_fault(fault_hook, FAULT_AFTER_CHECKS)
            connection.execute(
                """
                INSERT INTO revocations (
                    authorization_domain_id,
                    issuer_kind,
                    issuer_id,
                    grant_id,
                    run_id,
                    grant_json,
                    revoker_kind,
                    revoker_id,
                    decision_time,
                    decision_time_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    *grant_identity(grant),
                    grant.run.run_id,
                    encode_grant(grant),
                    envelope.revoker_kind,
                    envelope.revoker_id,
                    decision_text,
                    decision_key,
                ),
            )
            _invoke_fault(
                fault_hook,
                FAULT_AFTER_INSERT_BEFORE_COMMIT,
            )
            self._advance_watermark(
                connection,
                decision_text,
                decision_key,
            )
            _commit(connection)
            committed = True
            _invoke_fault(
                fault_hook,
                FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
            )
            return RevocationResult(
                "newly_revoked",
                RevocationRecord(
                    grant,
                    envelope.revoker_kind,
                    envelope.revoker_id,
                    decision_text,
                ),
            )
        except _CommitUnknown as error:
            if connection is not None:
                _safe_rollback(connection)
            return RevocationResult(
                "commit_unknown",
                detail=str(error),
                retryable=True,
                indeterminate=True,
            )
        except (sqlite3.Error, ExperimentStorageError, OSError) as error:
            if connection is not None and not committed:
                _safe_rollback(connection)
            if committed:
                return RevocationResult(
                    "commit_unknown",
                    detail="response failed after a known commit",
                    retryable=True,
                    indeterminate=True,
                )
            if _is_busy(error):
                return RevocationResult(
                    "storage_busy",
                    detail="authoritative ledger is busy",
                    retryable=True,
                )
            return RevocationResult(
                "storage_failure",
                detail=f"authoritative ledger failed closed: {error}",
            )
        except Exception as error:
            if connection is not None and not committed:
                _safe_rollback(connection)
            if committed:
                return RevocationResult(
                    "commit_unknown",
                    detail="response failed after commit",
                    retryable=True,
                    indeterminate=True,
                )
            return RevocationResult(
                "storage_failure",
                detail=f"revocation transaction failed closed: {error}",
            )
        finally:
            if connection is not None:
                connection.close()

    def admissions(self) -> tuple[AdmissionRecord, ...]:
        """Read all experiment admissions for focused verification only."""

        connection = self._open_existing()
        try:
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            rows = connection.execute(
                """
                SELECT * FROM admissions
                ORDER BY authorization_domain_id, issuer_kind, issuer_id,
                         grant_id
                """
            ).fetchall()
            return tuple(self._admission_from_row(row) for row in rows)
        finally:
            connection.close()

    def revocations(self) -> tuple[RevocationRecord, ...]:
        """Read all experiment tombstones for focused verification only."""

        connection = self._open_existing()
        try:
            self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
            rows = connection.execute(
                """
                SELECT * FROM revocations
                ORDER BY authorization_domain_id, issuer_kind, issuer_id,
                         grant_id
                """
            ).fetchall()
            return tuple(self._revocation_from_row(row) for row in rows)
        finally:
            connection.close()

    def watermark(self) -> tuple[str | None, int | None]:
        """Return the verified decision-time watermark for focused tests."""

        connection = self._open_existing()
        try:
            return self._verify_metadata(
                connection,
                self.configuration.authorization_domain_id,
            )
        finally:
            connection.close()


def admission_record_document(record: AdmissionRecord) -> dict[str, object]:
    """Return a process-safe result mapping for the experiment worker."""

    return {
        "grant": _grant_document(record.grant),
        "binding": _binding_document(record.binding),
        "decision_time": record.decision_time,
    }


def revocation_record_document(record: RevocationRecord) -> dict[str, object]:
    """Return a process-safe revocation mapping for the experiment worker."""

    return {
        "grant": _grant_document(record.grant),
        "revoker_kind": record.revoker_kind,
        "revoker_id": record.revoker_id,
        "decision_time": record.decision_time,
    }


def grant_from_document(document: object) -> AgentExecutionAuthorizationGrant:
    """Reconstruct a Grant from a process-safe mapping through the codec."""

    return decode_grant(_canonical_json(document))


def binding_from_document(document: object) -> AgentOperationToolBinding:
    """Reconstruct a Binding from a process-safe mapping through the codec."""

    return decode_binding(_canonical_json(document))
