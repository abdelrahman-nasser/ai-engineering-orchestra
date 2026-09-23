"""Backend-neutral authoritative Dispatch Admission coordination contracts.

This module separates an untrusted-facing coordinator from an authority-
internal store protocol.  It defines no persistence backend and performs no
dispatch or Tool invocation.  The configured authentication, resolver,
fresh-evidence, and mode ports are trust boundaries; no supplied value can
self-attest that it is trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteOutcome,
    assess_agent_action_prerequisites,
)
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    prepare_agent_execution_contract,
)
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
    validate_agent_execution_dispatch_admission,
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
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityValidationResult,
)


__all__ = (
    "AgentActionPrerequisiteParentInputs",
    "AgentExecutionAuthorizationGrantAuthenticationPort",
    "AgentExecutionDispatchAdmissionClock",
    "AgentExecutionDispatchAdmissionCoordinator",
    "AgentExecutionDispatchAdmissionStore",
    "AgentExecutionDispatchAdmissionStoreAdministrationOutcome",
    "AgentExecutionDispatchAdmissionStoreAdministrationResult",
    "AgentExecutionDispatchAdmissionStoreOutcome",
    "AgentExecutionDispatchAdmissionStoreResult",
    "AgentExecutionDispatchAdmissionStoreRetryDisposition",
    "AgentOperationToolBindingResolverPort",
    "EffectiveExecutionModeResolverPort",
    "FreshAgentActionPrerequisiteSourcePort",
    "OriginalIssuerRevocationAuthenticationPort",
    "make_agent_execution_dispatch_admission_store_administration_result",
    "make_agent_execution_dispatch_admission_store_result",
)


class AgentExecutionDispatchAdmissionStoreOutcome(StrEnum):
    """Closed operational outcomes across coordinator and store operations."""

    NEWLY_ADMITTED = "newly_admitted"
    EXISTING_EXACT_ADMISSION = "existing_exact_admission"
    NEWLY_REVOKED = "newly_revoked"
    EXISTING_EXACT_REVOCATION = "existing_exact_revocation"

    # Authority-internal continuation used only by guarded history/load calls.
    NO_EXISTING_ADMISSION = "no_existing_admission"

    NOT_YET_CURRENT = "not_yet_current"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DOMAIN_MISMATCH = "domain_mismatch"
    GRANT_IDENTITY_CONFLICT = "grant_identity_conflict"
    BINDING_CONFLICT = "binding_conflict"
    RUN_CONFLICT = "run_conflict"

    INVALID_INPUT = "invalid_input"
    UNAUTHENTICATED_GRANT = "unauthenticated_grant"
    UNTRUSTED_TOOL_BINDING = "untrusted_tool_binding"
    UNSATISFIED_PREREQUISITES = "unsatisfied_prerequisites"

    STORAGE_BUSY = "storage_busy"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    INTEGRITY_FAILURE = "integrity_failure"
    CLOCK_FAILURE = "clock_failure"
    CLOCK_REGRESSION = "clock_regression"
    COMMIT_UNKNOWN = "commit_unknown"


class AgentExecutionDispatchAdmissionStoreRetryDisposition(StrEnum):
    """Typed guidance for a result; never an ambiguous retry boolean."""

    NO_RETRY_NEEDED = "no_retry_needed"
    DO_NOT_RETRY_SAME_REQUEST = "do_not_retry_same_request"
    RETRY_EXACT_REQUEST = "retry_exact_request"
    RETRY_AT_OR_AFTER_ISSUANCE = "retry_at_or_after_issuance"
    RECOLLECT_FRESH_STATE = "recollect_fresh_state"
    RETRY_AFTER_REMEDIATION = "retry_after_remediation"
    RECONCILE_ADMINISTRATIVE_STATE = "reconcile_administrative_state"


class AgentExecutionDispatchAdmissionStoreAdministrationOutcome(StrEnum):
    """Administrative outcomes, separate from Admission decisions."""

    PROVISIONED = "provisioned"
    ALREADY_CURRENT = "already_current"
    MIGRATED = "migrated"
    FENCED = "fenced"
    FENCED_BACKUP_CREATED = "fenced_backup_created"
    MIGRATION_FAILURE = "migration_failure"
    STORAGE_BUSY = "storage_busy"
    STORAGE_UNAVAILABLE = "storage_unavailable"
    INCOMPATIBLE_SCHEMA = "incompatible_schema"
    INTEGRITY_FAILURE = "integrity_failure"
    COMMIT_UNKNOWN = "commit_unknown"


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionStoreAdministrationResult:
    """Typed result for an explicit backend administration operation."""

    outcome: AgentExecutionDispatchAdmissionStoreAdministrationOutcome
    retry_disposition: AgentExecutionDispatchAdmissionStoreRetryDisposition
    detail: str


def make_agent_execution_dispatch_admission_store_administration_result(
    outcome: AgentExecutionDispatchAdmissionStoreAdministrationOutcome,
    *,
    detail: str | None = None,
) -> AgentExecutionDispatchAdmissionStoreAdministrationResult:
    """Build one canonical explicit-administration result."""

    if (
        type(outcome)
        is not AgentExecutionDispatchAdmissionStoreAdministrationOutcome
    ):
        raise TypeError("outcome must be an exact administration outcome")
    if detail is None:
        detail = outcome.value
    if type(detail) is not str or not detail:
        raise TypeError("detail must be an exact nonempty string")

    if (
        outcome
        is AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        STORAGE_BUSY
    ):
        retry = (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_EXACT_REQUEST
        )
    elif (
        outcome
        is AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        COMMIT_UNKNOWN
    ):
        retry = (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RECONCILE_ADMINISTRATIVE_STATE
        )
    elif outcome in (
        AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        MIGRATION_FAILURE,
        AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        STORAGE_UNAVAILABLE,
        AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        INCOMPATIBLE_SCHEMA,
        AgentExecutionDispatchAdmissionStoreAdministrationOutcome.
        INTEGRITY_FAILURE,
    ):
        retry = (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_AFTER_REMEDIATION
        )
    else:
        retry = (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            NO_RETRY_NEEDED
        )
    return AgentExecutionDispatchAdmissionStoreAdministrationResult(
        outcome=outcome,
        retry_disposition=retry,
        detail=detail,
    )


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionStoreResult:
    """One atomic operational result with optional authoritative Admission."""

    outcome: AgentExecutionDispatchAdmissionStoreOutcome
    retry_disposition: AgentExecutionDispatchAdmissionStoreRetryDisposition
    admission: AgentExecutionDispatchAdmission | None
    detail: str


_POSITIVE_ADMISSION_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
        AgentExecutionDispatchAdmissionStoreOutcome.EXISTING_EXACT_ADMISSION,
    )
)
_NO_RETRY_NEEDED_OUTCOMES = frozenset(
    (
        *_POSITIVE_ADMISSION_OUTCOMES,
        AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        AgentExecutionDispatchAdmissionStoreOutcome.EXISTING_EXACT_REVOCATION,
        AgentExecutionDispatchAdmissionStoreOutcome.NO_EXISTING_ADMISSION,
    )
)
_EXACT_RETRY_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
        AgentExecutionDispatchAdmissionStoreOutcome.COMMIT_UNKNOWN,
    )
)
_REMEDIATION_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.INCOMPATIBLE_SCHEMA,
        AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_REGRESSION,
    )
)

_READ_STORE_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.EXISTING_EXACT_ADMISSION,
        AgentExecutionDispatchAdmissionStoreOutcome.NO_EXISTING_ADMISSION,
        AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH,
        AgentExecutionDispatchAdmissionStoreOutcome.GRANT_IDENTITY_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.BINDING_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.RUN_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
        AgentExecutionDispatchAdmissionStoreOutcome.INCOMPATIBLE_SCHEMA,
        AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
    )
)
_ADMIT_STORE_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_ADMITTED,
        AgentExecutionDispatchAdmissionStoreOutcome.EXISTING_EXACT_ADMISSION,
        AgentExecutionDispatchAdmissionStoreOutcome.NOT_YET_CURRENT,
        AgentExecutionDispatchAdmissionStoreOutcome.EXPIRED,
        AgentExecutionDispatchAdmissionStoreOutcome.REVOKED,
        AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH,
        AgentExecutionDispatchAdmissionStoreOutcome.GRANT_IDENTITY_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.BINDING_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.RUN_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
        AgentExecutionDispatchAdmissionStoreOutcome.INCOMPATIBLE_SCHEMA,
        AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_REGRESSION,
        AgentExecutionDispatchAdmissionStoreOutcome.COMMIT_UNKNOWN,
    )
)
_REVOKE_STORE_OUTCOMES = frozenset(
    (
        AgentExecutionDispatchAdmissionStoreOutcome.NEWLY_REVOKED,
        AgentExecutionDispatchAdmissionStoreOutcome.EXISTING_EXACT_REVOCATION,
        AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH,
        AgentExecutionDispatchAdmissionStoreOutcome.GRANT_IDENTITY_CONFLICT,
        AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_BUSY,
        AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
        AgentExecutionDispatchAdmissionStoreOutcome.INCOMPATIBLE_SCHEMA,
        AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_FAILURE,
        AgentExecutionDispatchAdmissionStoreOutcome.CLOCK_REGRESSION,
        AgentExecutionDispatchAdmissionStoreOutcome.COMMIT_UNKNOWN,
    )
)
_STORE_OPERATION_OUTCOMES = {
    "classify_guarded_history": _READ_STORE_OUTCOMES,
    "load_authoritative_admission": _READ_STORE_OUTCOMES,
    "admit_or_return_existing": _ADMIT_STORE_OUTCOMES,
    "revoke_or_return_existing": _REVOKE_STORE_OUTCOMES,
}


def _retry_disposition_for(
    outcome: AgentExecutionDispatchAdmissionStoreOutcome,
) -> AgentExecutionDispatchAdmissionStoreRetryDisposition:
    if outcome in _NO_RETRY_NEEDED_OUTCOMES:
        return (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            NO_RETRY_NEEDED
        )
    if outcome in _EXACT_RETRY_OUTCOMES:
        return (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_EXACT_REQUEST
        )
    if outcome is AgentExecutionDispatchAdmissionStoreOutcome.NOT_YET_CURRENT:
        return (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_AT_OR_AFTER_ISSUANCE
        )
    if (
        outcome
        is AgentExecutionDispatchAdmissionStoreOutcome.
        UNSATISFIED_PREREQUISITES
    ):
        return (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RECOLLECT_FRESH_STATE
        )
    if outcome in _REMEDIATION_OUTCOMES:
        return (
            AgentExecutionDispatchAdmissionStoreRetryDisposition.
            RETRY_AFTER_REMEDIATION
        )
    return (
        AgentExecutionDispatchAdmissionStoreRetryDisposition.
        DO_NOT_RETRY_SAME_REQUEST
    )


def make_agent_execution_dispatch_admission_store_result(
    outcome: AgentExecutionDispatchAdmissionStoreOutcome,
    *,
    admission: AgentExecutionDispatchAdmission | None = None,
    detail: str | None = None,
) -> AgentExecutionDispatchAdmissionStoreResult:
    """Build one canonical store result and enforce its atomic shape."""

    if type(outcome) is not AgentExecutionDispatchAdmissionStoreOutcome:
        raise TypeError("outcome must be an exact store outcome")
    if detail is None:
        detail = outcome.value
    if type(detail) is not str or not detail:
        raise TypeError("detail must be an exact nonempty string")

    if outcome in _POSITIVE_ADMISSION_OUTCOMES:
        if type(admission) is not AgentExecutionDispatchAdmission:
            raise TypeError("positive Admission outcomes require an Admission")
        if not validate_agent_execution_dispatch_admission(admission).valid:
            raise ValueError(
                "positive outcomes require an intrinsically valid Admission"
            )
    elif admission is not None:
        raise ValueError("non-Admission outcomes must not carry an Admission")

    return AgentExecutionDispatchAdmissionStoreResult(
        outcome=outcome,
        retry_disposition=_retry_disposition_for(outcome),
        admission=admission,
        detail=detail,
    )


def _store_result_is_canonical(
    result: object,
) -> bool:
    if type(result) is not AgentExecutionDispatchAdmissionStoreResult:
        return False
    if (
        type(result.outcome) is not AgentExecutionDispatchAdmissionStoreOutcome
        or type(result.retry_disposition)
        is not AgentExecutionDispatchAdmissionStoreRetryDisposition
        or result.retry_disposition is not _retry_disposition_for(result.outcome)
        or type(result.detail) is not str
        or not result.detail
    ):
        return False
    if result.outcome in _POSITIVE_ADMISSION_OUTCOMES:
        return (
            type(result.admission) is AgentExecutionDispatchAdmission
            and validate_agent_execution_dispatch_admission(
                result.admission
            ).valid
        )
    return result.admission is None


@dataclass(frozen=True)
class AgentActionPrerequisiteParentInputs:
    """Parent values consumed by a fresh AIO-040 composition.

    Direct construction does not establish freshness.  Currency and source
    provenance derive only from the configured fresh-source port call.
    """

    candidate_result: AgentExecutionCandidatePrerequisiteResult
    requirement: OperationRequirement
    capability_result: RuntimeOperationCapabilityValidationResult
    permission_result: EnvironmentOperationPermissionValidationResult
    authorization_result: AgentExecutionAuthorizationValidationResult
    environment_id: str


class AgentExecutionAuthorizationGrantAuthenticationPort(Protocol):
    """Configured producer boundary that authenticates one presented Grant."""

    def authenticate_grant(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        """Return the authenticated exact Grant, or ``None`` on rejection."""


class AgentOperationToolBindingResolverPort(Protocol):
    """Configured trusted resolver for one immutable Tool Binding."""

    def resolve_tool_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentOperationToolBinding | None:
        """Resolve one trusted non-widening Binding for the exact Grant Run."""


class FreshAgentActionPrerequisiteSourcePort(Protocol):
    """Configured source of newly collected AIO-040 parent values."""

    def collect_fresh_parent_results(
        self,
        grant: AgentExecutionAuthorizationGrant,
        tool_binding: AgentOperationToolBinding,
    ) -> AgentActionPrerequisiteParentInputs | None:
        """Collect current parent values; never accept a supplied AIO-040 result."""


class EffectiveExecutionModeResolverPort(Protocol):
    """Configured source of the freshly resolved Task-wide effective mode."""

    def resolve_effective_execution_mode(
        self,
        grant: AgentExecutionAuthorizationGrant,
        tool_binding: AgentOperationToolBinding,
    ) -> str | None:
        """Return one freshly resolved mode, or ``None`` when unresolved."""


class OriginalIssuerRevocationAuthenticationPort(Protocol):
    """Configured original-issuer authentication boundary for revocation."""

    def authenticate_original_issuer_revocation(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        """Return the exact issuer-authenticated Grant, or ``None``."""


class AgentExecutionDispatchAdmissionClock(Protocol):
    """Trusted clock sampled by a store only inside its serialization point."""

    def now_utc(self) -> datetime:
        """Return an aware UTC instant; backends fail closed otherwise."""


_STORE_REQUEST_AUTHORITY = object()


class _AuthorityInternalStoreRequest:
    __slots__ = ()

    def __new__(cls) -> _AuthorityInternalStoreRequest:
        raise TypeError(
            "authority-internal Store requests are coordinator-minted"
        )


@dataclass(frozen=True, slots=True, init=False, repr=False)
class _AgentExecutionDispatchAdmissionHistoryRequest(
    _AuthorityInternalStoreRequest
):
    expected_authorization_domain_id: str
    grant: AgentExecutionAuthorizationGrant
    tool_binding: AgentOperationToolBinding
    _authority: object


@dataclass(frozen=True, slots=True, init=False, repr=False)
class _AgentExecutionDispatchAdmissionRequest(_AuthorityInternalStoreRequest):
    expected_authorization_domain_id: str
    grant: AgentExecutionAuthorizationGrant
    tool_binding: AgentOperationToolBinding
    expected_run: AgentExecutionRun
    _authority: object


@dataclass(frozen=True, slots=True, init=False, repr=False)
class _AgentExecutionDispatchAdmissionLookupRequest(
    _AuthorityInternalStoreRequest
):
    expected_authorization_domain_id: str
    grant: AgentExecutionAuthorizationGrant
    tool_binding: AgentOperationToolBinding
    _authority: object


@dataclass(frozen=True, slots=True, init=False, repr=False)
class _AgentExecutionAuthorizationRevocationRequest(
    _AuthorityInternalStoreRequest
):
    expected_authorization_domain_id: str
    grant: AgentExecutionAuthorizationGrant
    _authority: object


def _mint_request(request_type: type[object], **values: object) -> object:
    request = object.__new__(request_type)
    for name, value in values.items():
        object.__setattr__(request, name, value)
    object.__setattr__(request, "_authority", _STORE_REQUEST_AUTHORITY)
    return request


def _mint_guarded_history_request(
    expected_authorization_domain_id: str,
    grant: AgentExecutionAuthorizationGrant,
    tool_binding: AgentOperationToolBinding,
) -> _AgentExecutionDispatchAdmissionHistoryRequest:
    return _mint_request(
        _AgentExecutionDispatchAdmissionHistoryRequest,
        expected_authorization_domain_id=expected_authorization_domain_id,
        grant=grant,
        tool_binding=tool_binding,
    )  # type: ignore[return-value]


def _mint_admission_request(
    expected_authorization_domain_id: str,
    grant: AgentExecutionAuthorizationGrant,
    tool_binding: AgentOperationToolBinding,
    expected_run: AgentExecutionRun,
) -> _AgentExecutionDispatchAdmissionRequest:
    return _mint_request(
        _AgentExecutionDispatchAdmissionRequest,
        expected_authorization_domain_id=expected_authorization_domain_id,
        grant=grant,
        tool_binding=tool_binding,
        expected_run=expected_run,
    )  # type: ignore[return-value]


def _mint_authoritative_lookup_request(
    expected_authorization_domain_id: str,
    grant: AgentExecutionAuthorizationGrant,
    tool_binding: AgentOperationToolBinding,
) -> _AgentExecutionDispatchAdmissionLookupRequest:
    return _mint_request(
        _AgentExecutionDispatchAdmissionLookupRequest,
        expected_authorization_domain_id=expected_authorization_domain_id,
        grant=grant,
        tool_binding=tool_binding,
    )  # type: ignore[return-value]


def _mint_revocation_request(
    expected_authorization_domain_id: str,
    grant: AgentExecutionAuthorizationGrant,
) -> _AgentExecutionAuthorizationRevocationRequest:
    return _mint_request(
        _AgentExecutionAuthorizationRevocationRequest,
        expected_authorization_domain_id=expected_authorization_domain_id,
        grant=grant,
    )  # type: ignore[return-value]


def _open_guarded_history_request(
    request: object,
) -> tuple[
    str,
    AgentExecutionAuthorizationGrant,
    AgentOperationToolBinding,
] | None:
    if (
        type(request) is not _AgentExecutionDispatchAdmissionHistoryRequest
        or request._authority is not _STORE_REQUEST_AUTHORITY
    ):
        return None
    return (
        request.expected_authorization_domain_id,
        request.grant,
        request.tool_binding,
    )


def _open_admission_request(
    request: object,
) -> tuple[
    str,
    AgentExecutionAuthorizationGrant,
    AgentOperationToolBinding,
    AgentExecutionRun,
] | None:
    if (
        type(request) is not _AgentExecutionDispatchAdmissionRequest
        or request._authority is not _STORE_REQUEST_AUTHORITY
    ):
        return None
    return (
        request.expected_authorization_domain_id,
        request.grant,
        request.tool_binding,
        request.expected_run,
    )


def _open_authoritative_lookup_request(
    request: object,
) -> tuple[
    str,
    AgentExecutionAuthorizationGrant,
    AgentOperationToolBinding,
] | None:
    if (
        type(request) is not _AgentExecutionDispatchAdmissionLookupRequest
        or request._authority is not _STORE_REQUEST_AUTHORITY
    ):
        return None
    return (
        request.expected_authorization_domain_id,
        request.grant,
        request.tool_binding,
    )


def _open_revocation_request(
    request: object,
) -> tuple[str, AgentExecutionAuthorizationGrant] | None:
    if (
        type(request) is not _AgentExecutionAuthorizationRevocationRequest
        or request._authority is not _STORE_REQUEST_AUTHORITY
    ):
        return None
    return request.expected_authorization_domain_id, request.grant


class AgentExecutionDispatchAdmissionStore(Protocol):
    """Authority-internal backend-neutral admission-ledger protocol.

    Request objects are minted only after configured trust checks.  They are
    process-encapsulation guards, not bearer credentials or a replacement for
    an actual process/service security boundary.
    """

    def classify_guarded_history(
        self,
        request: _AgentExecutionDispatchAdmissionHistoryRequest,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Classify exact committed history without sampling time or freshness."""

    def admit_or_return_existing(
        self,
        request: _AgentExecutionDispatchAdmissionRequest,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Atomically admit once or return the exact committed Admission."""

    def load_authoritative_admission(
        self,
        request: _AgentExecutionDispatchAdmissionLookupRequest,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Load authoritative history by the complete Grant identity/binding."""

    def revoke_or_return_existing(
        self,
        request: _AgentExecutionAuthorizationRevocationRequest,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Serialize one immutable original-issuer revocation tombstone."""


def _result(
    outcome: AgentExecutionDispatchAdmissionStoreOutcome,
    detail: str,
) -> AgentExecutionDispatchAdmissionStoreResult:
    return make_agent_execution_dispatch_admission_store_result(
        outcome,
        detail=detail,
    )


def _finding_detail(prefix: str, findings: tuple[object, ...]) -> str:
    codes = tuple(
        finding.code
        for finding in findings
        if type(getattr(finding, "code", None)) is str
    )
    if not codes:
        return prefix
    return f"{prefix}: {', '.join(codes)}"


class AgentExecutionDispatchAdmissionCoordinator:
    """Trusted orchestration boundary for Admission and revocation requests."""

    def __init__(
        self,
        *,
        authorization_domain_id: str,
        store: AgentExecutionDispatchAdmissionStore,
        grant_authentication: AgentExecutionAuthorizationGrantAuthenticationPort,
        tool_binding_resolver: AgentOperationToolBindingResolverPort,
        fresh_prerequisite_source: FreshAgentActionPrerequisiteSourcePort,
        execution_mode_resolver: EffectiveExecutionModeResolverPort,
        revocation_authentication: OriginalIssuerRevocationAuthenticationPort,
    ) -> None:
        if type(authorization_domain_id) is not str or not authorization_domain_id:
            raise ValueError(
                "authorization_domain_id must be an exact nonempty string"
            )
        self._authorization_domain_id = authorization_domain_id
        self._store = store
        self._grant_authentication = grant_authentication
        self._tool_binding_resolver = tool_binding_resolver
        self._fresh_prerequisite_source = fresh_prerequisite_source
        self._execution_mode_resolver = execution_mode_resolver
        self._revocation_authentication = revocation_authentication

    def _authenticate_grant(
        self,
        presented_grant: object,
        *,
        for_revocation: bool = False,
    ) -> tuple[
        AgentExecutionAuthorizationGrant | None,
        AgentExecutionDispatchAdmissionStoreResult | None,
    ]:
        try:
            if for_revocation:
                grant = (
                    self._revocation_authentication.
                    authenticate_original_issuer_revocation(presented_grant)
                )
            else:
                grant = self._grant_authentication.authenticate_grant(
                    presented_grant
                )
        except Exception:
            grant = None
        if grant is None:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNAUTHENTICATED_GRANT,
                "Configured Grant authentication rejected the request.",
            )
        if type(grant) is not AgentExecutionAuthorizationGrant:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                "Configured Grant authentication returned a noncanonical value.",
            )

        grant_result = validate_agent_execution_authorization_grant(grant)
        if not grant_result.valid:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                _finding_detail(
                    "Authenticated Grant is intrinsically invalid",
                    grant_result.findings,
                ),
            )
        if grant.authorization_domain_id != self._authorization_domain_id:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.DOMAIN_MISMATCH,
                "Authenticated Grant does not belong to the configured domain.",
            )
        return grant, None

    def _resolve_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> tuple[
        AgentOperationToolBinding | None,
        AgentExecutionDispatchAdmissionStoreResult | None,
    ]:
        try:
            binding = self._tool_binding_resolver.resolve_tool_binding(grant)
        except Exception:
            binding = None
        if binding is None:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNTRUSTED_TOOL_BINDING,
                "Configured Tool resolver did not return a trusted Binding.",
            )
        if type(binding) is not AgentOperationToolBinding:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                "Configured Tool resolver returned a noncanonical value.",
            )
        binding_result = validate_agent_operation_tool_binding(binding)
        if not binding_result.valid:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                _finding_detail(
                    "Trusted Tool Binding is intrinsically invalid",
                    binding_result.findings,
                ),
            )
        if binding.run != grant.run:
            return None, _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INVALID_INPUT,
                "Authenticated Grant and trusted Tool Binding Runs differ.",
            )
        return binding, None

    @staticmethod
    def _checked_store_result(
        result: object,
        *,
        expected_grant: AgentExecutionAuthorizationGrant | None = None,
        expected_binding: AgentOperationToolBinding | None = None,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        if not _store_result_is_canonical(result):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
                "The authoritative store returned an incoherent result.",
            )
        assert type(result) is AgentExecutionDispatchAdmissionStoreResult
        if result.admission is not None:
            if (
                expected_grant is not None
                and result.admission.grant != expected_grant
            ):
                return _result(
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    INTEGRITY_FAILURE,
                    "The authoritative Admission Grant differs from the request.",
                )
            if (
                expected_binding is not None
                and result.admission.tool_binding != expected_binding
            ):
                return _result(
                    AgentExecutionDispatchAdmissionStoreOutcome.
                    INTEGRITY_FAILURE,
                    "The authoritative Admission Binding differs from the request.",
                )
        return result

    def _call_store(
        self,
        operation: str,
        request: object,
        *,
        expected_grant: AgentExecutionAuthorizationGrant | None = None,
        expected_binding: AgentOperationToolBinding | None = None,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        try:
            method = getattr(self._store, operation)
            result = method(request)
        except Exception:
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.STORAGE_UNAVAILABLE,
                "The configured authoritative store operation was unavailable.",
            )
        checked = self._checked_store_result(
            result,
            expected_grant=expected_grant,
            expected_binding=expected_binding,
        )
        allowed_outcomes = _STORE_OPERATION_OUTCOMES.get(operation)
        if (
            allowed_outcomes is None
            or checked.outcome not in allowed_outcomes
        ):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
                "The authoritative store returned an outcome that is "
                f"incoherent for {operation}.",
            )
        return checked

    def admit(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Authenticate, resolve, recover exact history, or freshly admit.

        No caller-supplied AIO-040 result, decision time, trust flag, or
        authenticated wrapper is accepted.
        """

        grant, rejection = self._authenticate_grant(presented_grant)
        if rejection is not None:
            return rejection
        assert grant is not None

        binding, rejection = self._resolve_binding(grant)
        if rejection is not None:
            return rejection
        assert binding is not None

        history_request = _mint_guarded_history_request(
            self._authorization_domain_id,
            grant,
            binding,
        )
        history_result = self._call_store(
            "classify_guarded_history",
            history_request,
            expected_grant=grant,
            expected_binding=binding,
        )
        if (
            history_result.outcome
            is AgentExecutionDispatchAdmissionStoreOutcome.
            EXISTING_EXACT_ADMISSION
        ):
            return history_result
        if (
            history_result.outcome
            is not AgentExecutionDispatchAdmissionStoreOutcome.
            NO_EXISTING_ADMISSION
        ):
            return history_result

        try:
            parents = (
                self._fresh_prerequisite_source.collect_fresh_parent_results(
                    grant,
                    binding,
                )
            )
        except Exception:
            parents = None
        if type(parents) is not AgentActionPrerequisiteParentInputs:
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES,
                "Fresh prerequisite parent values were not available.",
            )

        prerequisite_result = assess_agent_action_prerequisites(
            parents.candidate_result,
            parents.requirement,
            parents.capability_result,
            parents.permission_result,
            parents.authorization_result,
            environment_id=parents.environment_id,
        )
        if (
            not prerequisite_result.valid
            or prerequisite_result.outcome
            is not AgentActionPrerequisiteOutcome.SATISFIED
        ):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES,
                _finding_detail(
                    "Fresh AIO-040 assessment was not satisfied",
                    prerequisite_result.findings,
                ),
            )

        try:
            execution_mode = (
                self._execution_mode_resolver.resolve_effective_execution_mode(
                    grant,
                    binding,
                )
            )
        except Exception:
            execution_mode = None

        contract_result = prepare_agent_execution_contract(
            prerequisite_result,
            execution_mode=execution_mode,  # type: ignore[arg-type]
        )
        if (
            not contract_result.valid
            or contract_result.contract != grant.run.contract
        ):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES,
                _finding_detail(
                    "Fresh AIO-041 Contract did not match the Grant Run",
                    contract_result.findings,
                ),
            )
        assert contract_result.contract is not None

        run_result = prepare_agent_execution_run(
            contract_result.contract,
            prerequisite_result,
            execution_mode=execution_mode,  # type: ignore[arg-type]
            run_id=grant.run.run_id,
        )
        if not run_result.valid or run_result.run is None:
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES,
                _finding_detail(
                    "Fresh AIO-042 Run reconstruction failed",
                    run_result.findings,
                ),
            )
        expected_run = run_result.run
        if not (
            grant.run == binding.run == expected_run
        ):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.
                UNSATISFIED_PREREQUISITES,
                "Grant, Binding, and freshly reconstructed Runs differ.",
            )

        admission_request = _mint_admission_request(
            self._authorization_domain_id,
            grant,
            binding,
            expected_run,
        )
        result = self._call_store(
            "admit_or_return_existing",
            admission_request,
            expected_grant=grant,
            expected_binding=binding,
        )
        if (
            result.outcome
            is AgentExecutionDispatchAdmissionStoreOutcome.
            NO_EXISTING_ADMISSION
        ):
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
                "Admission transaction returned an internal continuation outcome.",
            )
        return result

    def load_authoritative_admission(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Load a historical Admission only after configured Grant trust checks."""

        grant, rejection = self._authenticate_grant(presented_grant)
        if rejection is not None:
            return rejection
        assert grant is not None
        binding, rejection = self._resolve_binding(grant)
        if rejection is not None:
            return rejection
        assert binding is not None
        request = _mint_authoritative_lookup_request(
            self._authorization_domain_id,
            grant,
            binding,
        )
        return self._call_store(
            "load_authoritative_admission",
            request,
            expected_grant=grant,
            expected_binding=binding,
        )

    def revoke(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Authenticate the original issuer and serialize one revocation."""

        grant, rejection = self._authenticate_grant(
            presented_grant,
            for_revocation=True,
        )
        if rejection is not None:
            return rejection
        assert grant is not None
        request = _mint_revocation_request(
            self._authorization_domain_id,
            grant,
        )
        result = self._call_store(
            "revoke_or_return_existing",
            request,
            expected_grant=grant,
        )
        if result.admission is not None:
            return _result(
                AgentExecutionDispatchAdmissionStoreOutcome.INTEGRITY_FAILURE,
                "A revocation operation returned an Admission payload.",
            )
        return result
