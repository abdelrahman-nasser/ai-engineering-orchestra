"""Bounded same-process production of authenticated authorization Grants.

This module constructs the existing canonical eight-field Grant only after a
trusted composition root has supplied process-local authentication proofs,
current authorization-domain ownership, issuer state, entitlement policy,
trusted time, and 256-bit CSPRNG material.  It does not establish Grant
currentness, consume a Grant, create an Admission, resolve a Tool, dispatch,
or invoke anything.

The private proof and presentation objects deliberately rely on exact object
identity and trusted same-process composition.  They are not cryptographic
bearer artifacts and are not suitable for persistence or cross-process use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import hashlib
import sys
from threading import Lock
from typing import NoReturn, Protocol

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentExecutionAuthorizationGrantAuthenticationPort,
)
from engineering_orchestration.agent_execution_run import (
    AgentExecutionRun,
    validate_agent_execution_run,
)
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainIdentity,
    AuthorizationDomainOperationLease,
    AuthorizationDomainOwnershipError,
    OwnedAuthorizationDomainSession,
    OwnedAuthorizationDomainSessionClosedError,
    OwnedAuthorizationDomainSessionLostError,
)


__all__ = (
    "AgentExecutionAuthorizationGrantAuditMaterial",
    "AgentExecutionAuthorizationGrantLifetimePolicy",
    "AgentExecutionAuthorizationGrantProducer",
    "AgentExecutionAuthorizationGrantProductionOutcome",
    "AgentExecutionAuthorizationGrantProductionResult",
    "AgentExecutionAuthorizationGrantRetryDisposition",
    "GrantIdSource",
    "HumanApprovalAuthenticationAdapter",
    "IssuerEntitlementPolicy",
    "IssuerPrincipalIdentityAdapter",
    "IssuerStateAuthority",
    "PolicyDecisionAuthenticationAdapter",
    "TrustedUtcClock",
)


class AgentExecutionAuthorizationGrantProductionOutcome(StrEnum):
    """Closed result vocabulary for one production attempt."""

    ISSUED = "issued"
    EXISTING_EXACT_ISSUANCE = "existing_exact_issuance"
    UNAUTHENTICATED_PRINCIPAL = "unauthenticated_principal"
    IDENTITY_UNAVAILABLE = "identity_unavailable"
    ISSUER_DISABLED = "issuer_disabled"
    NOT_ENTITLED = "not_entitled"
    APPROVAL_MISSING = "approval_missing"
    APPROVAL_SUBJECT_MISMATCH = "approval_subject_mismatch"
    POLICY_DENIED = "policy_denied"
    AUTHORITY_PROOF_INVALID = "authority_proof_invalid"
    INVALID_RUN = "invalid_run"
    DOMAIN_NOT_OWNED = "domain_not_owned"
    DOMAIN_MISMATCH = "domain_mismatch"
    GENERATION_MISMATCH = "generation_mismatch"
    OWNERSHIP_LOST = "ownership_lost"
    PRODUCER_CLOSED = "producer_closed"
    RUN_ALREADY_ISSUED = "run_already_issued"
    RUN_IDENTITY_CONFLICT = "run_identity_conflict"
    RUN_ISSUANCE_CONFLICT = "run_issuance_conflict"
    CLOCK_FAILURE = "clock_failure"
    LIFETIME_INVALID = "lifetime_invalid"
    GRANT_ID_GENERATION_FAILURE = "grant_id_generation_failure"
    GRANT_ID_COLLISION = "grant_id_collision"
    INTEGRITY_FAILURE = "integrity_failure"


class AgentExecutionAuthorizationGrantRetryDisposition(StrEnum):
    """Closed aggregate recovery guidance for production outcomes."""

    NO_RETRY_NEEDED = "no_retry_needed"
    RETRY_WITH_FRESH_PRINCIPAL_AND_AUTHORITY = (
        "retry_with_fresh_principal_and_authority"
    )
    RETRY_AFTER_IDENTITY_REMEDIATION = "retry_after_identity_remediation"
    RETRY_AFTER_ISSUER_REENABLE_WITH_FRESH_AUTHORITY = (
        "retry_after_issuer_reenable_with_fresh_authority"
    )
    RETRY_WITH_FRESH_HUMAN_APPROVAL = "retry_with_fresh_human_approval"
    RETRY_WITH_FRESH_POLICY_DECISION = "retry_with_fresh_policy_decision"
    RETRY_WITH_FRESH_AUTHORITY_DECISION = (
        "retry_with_fresh_authority_decision"
    )
    RETRY_WITH_FRESH_SESSION_AUTHORITY = (
        "retry_with_fresh_session_authority"
    )
    RETRY_WITH_NEW_RUN_AND_FRESH_AUTHORITY = (
        "retry_with_new_run_and_fresh_authority"
    )
    RETRY_WITH_NEW_RUN_AND_FRESH_SESSION_AUTHORITY = (
        "retry_with_new_run_and_fresh_session_authority"
    )
    RETRY_AFTER_CLOCK_REMEDIATION = "retry_after_clock_remediation"
    RETRY_AFTER_INTERNAL_REMEDIATION = "retry_after_internal_remediation"
    DO_NOT_RETRY_SAME_REQUEST = "do_not_retry_same_request"


_RETRY_FOR_OUTCOME = {
    AgentExecutionAuthorizationGrantProductionOutcome.ISSUED:
        AgentExecutionAuthorizationGrantRetryDisposition.NO_RETRY_NEEDED,
    AgentExecutionAuthorizationGrantProductionOutcome.
    EXISTING_EXACT_ISSUANCE:
        AgentExecutionAuthorizationGrantRetryDisposition.NO_RETRY_NEEDED,
    AgentExecutionAuthorizationGrantProductionOutcome.
    UNAUTHENTICATED_PRINCIPAL:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_PRINCIPAL_AND_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.IDENTITY_UNAVAILABLE:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_IDENTITY_REMEDIATION,
    AgentExecutionAuthorizationGrantProductionOutcome.ISSUER_DISABLED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_ISSUER_REENABLE_WITH_FRESH_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.NOT_ENTITLED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        DO_NOT_RETRY_SAME_REQUEST,
    AgentExecutionAuthorizationGrantProductionOutcome.APPROVAL_MISSING:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_HUMAN_APPROVAL,
    AgentExecutionAuthorizationGrantProductionOutcome.
    APPROVAL_SUBJECT_MISMATCH:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_HUMAN_APPROVAL,
    AgentExecutionAuthorizationGrantProductionOutcome.POLICY_DENIED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_POLICY_DECISION,
    AgentExecutionAuthorizationGrantProductionOutcome.
    AUTHORITY_PROOF_INVALID:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_AUTHORITY_DECISION,
    AgentExecutionAuthorizationGrantProductionOutcome.INVALID_RUN:
        AgentExecutionAuthorizationGrantRetryDisposition.
        DO_NOT_RETRY_SAME_REQUEST,
    AgentExecutionAuthorizationGrantProductionOutcome.DOMAIN_NOT_OWNED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_SESSION_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.DOMAIN_MISMATCH:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_SESSION_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.GENERATION_MISMATCH:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_SESSION_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.OWNERSHIP_LOST:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_SESSION_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.PRODUCER_CLOSED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_NEW_RUN_AND_FRESH_SESSION_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.RUN_ALREADY_ISSUED:
        AgentExecutionAuthorizationGrantRetryDisposition.
        DO_NOT_RETRY_SAME_REQUEST,
    AgentExecutionAuthorizationGrantProductionOutcome.RUN_IDENTITY_CONFLICT:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_NEW_RUN_AND_FRESH_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.RUN_ISSUANCE_CONFLICT:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_NEW_RUN_AND_FRESH_AUTHORITY,
    AgentExecutionAuthorizationGrantProductionOutcome.CLOCK_FAILURE:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_CLOCK_REMEDIATION,
    AgentExecutionAuthorizationGrantProductionOutcome.LIFETIME_INVALID:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_WITH_FRESH_AUTHORITY_DECISION,
    AgentExecutionAuthorizationGrantProductionOutcome.
    GRANT_ID_GENERATION_FAILURE:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_INTERNAL_REMEDIATION,
    AgentExecutionAuthorizationGrantProductionOutcome.GRANT_ID_COLLISION:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_INTERNAL_REMEDIATION,
    AgentExecutionAuthorizationGrantProductionOutcome.INTEGRITY_FAILURE:
        AgentExecutionAuthorizationGrantRetryDisposition.
        RETRY_AFTER_INTERNAL_REMEDIATION,
}


@dataclass(frozen=True, slots=True)
class AgentExecutionAuthorizationGrantLifetimePolicy:
    """Immutable domain-configured default and maximum Grant lifetime."""

    default_lifetime: timedelta
    maximum_lifetime: timedelta
    revision: str


@dataclass(frozen=True, slots=True)
class AgentExecutionAuthorizationGrantAuditMaterial:
    """Pure nonsecret correlation material for one production result."""

    outcome: AgentExecutionAuthorizationGrantProductionOutcome
    retry_disposition: AgentExecutionAuthorizationGrantRetryDisposition
    issuer_kind: str | None
    issuer_id: str | None
    authorization_domain_id: str
    ledger_instance_id: str
    domain_generation: int
    run_id: str | None
    run_subject_correlation: str | None
    grant_id: str | None
    provenance_reference: str | None
    issued_at: str | None
    expires_at: str | None
    lifetime_policy_revision: str | None


@dataclass(frozen=True, slots=True)
class AgentExecutionAuthorizationGrantProductionResult:
    """Atomic four-field result; only success carries a presentation."""

    outcome: AgentExecutionAuthorizationGrantProductionOutcome
    retry_disposition: AgentExecutionAuthorizationGrantRetryDisposition
    presentation: IssuedAgentExecutionAuthorizationGrant | None
    audit_material: AgentExecutionAuthorizationGrantAuditMaterial


class IssuerPrincipalIdentityAdapter(Protocol):
    """Trusted same-process source and verifier of principal proofs."""

    def current_epoch(self) -> object:
        """Return the adapter epoch used for newly minted proofs."""

    def validate_authenticated_principal(
        self,
        authenticated_principal: object,
    ) -> bool:
        """Return exact ``True`` only for a still-recognized proof."""

    def _bind_authenticated_issuer_principal_minter(
        self,
        minter: object,
    ) -> None:
        """Accept the private composition-scoped principal mint capability."""


class HumanApprovalAuthenticationAdapter(Protocol):
    """Trusted same-process source and verifier of Human approvals."""

    def current_epoch(self) -> object:
        """Return the adapter epoch used for newly minted approvals."""

    def validate_authenticated_human_approval(
        self,
        approval: object,
    ) -> bool:
        """Return exact ``True`` only for a still-recognized approval."""

    def _bind_authenticated_human_approval_minter(
        self,
        minter: object,
    ) -> None:
        """Accept the private composition-scoped approval mint capability."""


class PolicyDecisionAuthenticationAdapter(Protocol):
    """Trusted same-process source and verifier of policy decisions."""

    def current_epoch(self) -> object:
        """Return the adapter epoch used for newly minted decisions."""

    def validate_authenticated_policy_decision(
        self,
        decision: object,
    ) -> bool:
        """Return exact ``True`` only for a still-recognized decision."""

    def _bind_authenticated_policy_decision_minter(
        self,
        minter: object,
    ) -> None:
        """Accept the private composition-scoped decision mint capability."""


class IssuerStateAuthority(Protocol):
    """Serialized local issuer enablement and epoch authority."""

    def observe_issuer_state(
        self,
        *,
        issuer_kind: str,
        issuer_id: str,
    ) -> tuple[bool, object]:
        """Atomically return exact enablement plus the current opaque epoch."""


class IssuerEntitlementPolicy(Protocol):
    """Immutable exact-domain issuer entitlement boundary."""

    def is_entitled(
        self,
        *,
        run: AgentExecutionRun,
        domain_identity: AuthorizationDomainIdentity,
        issuer_kind: str,
        issuer_id: str,
    ) -> bool:
        """Return exact ``True`` only for this complete Run and issuer."""


class TrustedUtcClock(Protocol):
    """Injected trusted clock sampled once per eligible attempt."""

    def now_utc(self) -> datetime:
        """Return one exact timezone-aware UTC instant."""


class GrantIdSource(Protocol):
    """Injected source of operating-system CSPRNG bytes."""

    def random_bytes(self, length: int) -> bytes:
        """Return exactly ``length`` fresh CSPRNG bytes."""


class _ProcessLocalCapability:
    """Noncopyable, nonserializable base for private object capabilities."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> NoReturn:
        del args, kwargs
        raise TypeError(f"{cls.__name__} is minted only by trusted composition")

    def __setattr__(self, name: str, value: object) -> NoReturn:
        del name, value
        raise AttributeError("process-local capabilities are immutable")

    def __copy__(self) -> NoReturn:
        raise TypeError("process-local capabilities cannot be copied")

    def __deepcopy__(self, memo: object) -> NoReturn:
        del memo
        raise TypeError("process-local capabilities cannot be deep-copied")

    def __reduce__(self) -> NoReturn:
        raise TypeError("process-local capabilities cannot be serialized")

    def __reduce_ex__(self, protocol: object) -> NoReturn:
        del protocol
        raise TypeError("process-local capabilities cannot be serialized")

    def __getstate__(self) -> NoReturn:
        raise TypeError("process-local capabilities cannot be serialized")

    def __repr__(self) -> str:
        return f"<{type(self).__name__} process-local capability>"


class AuthenticatedIssuerPrincipal(_ProcessLocalCapability):
    """Private configured-adapter output for one authenticated issuer."""

    __slots__ = (
        "_adapter",
        "_adapter_epoch",
        "_producer_epoch",
        "_owned_session",
        "_domain_identity",
        "_issuer_kind",
        "_issuer_id",
        "_authentication_session_id",
        "_issuer_state_epoch",
        "_valid_from",
        "_valid_until",
    )


class AuthenticatedHumanApproval(_ProcessLocalCapability):
    """Private positive exact-action Human approval proof."""

    __slots__ = (
        "_adapter",
        "_adapter_epoch",
        "_producer_epoch",
        "_owned_session",
        "_domain_identity",
        "_principal",
        "_run",
        "_approval_session_id",
        "_provenance_reference",
        "_valid_from",
        "_valid_until",
        "_requested_lifetime",
    )


class AuthenticatedPolicyDecision(_ProcessLocalCapability):
    """Private exact-action policy allow/deny proof."""

    __slots__ = (
        "_adapter",
        "_adapter_epoch",
        "_producer_epoch",
        "_owned_session",
        "_domain_identity",
        "_principal",
        "_run",
        "_decision",
        "_policy_revision",
        "_provenance_reference",
        "_valid_from",
        "_valid_until",
        "_requested_lifetime",
    )


class IssuedAgentExecutionAuthorizationGrant(_ProcessLocalCapability):
    """Private process-local presentation resolved only by its paired port."""

    __slots__ = ()


class _AuthenticatedIssuerPrincipalMinter(_ProcessLocalCapability):
    """Private capability installed into one exact identity adapter."""

    __slots__ = ("_state",)

    def mint(
        self,
        *,
        issuer_kind: str,
        issuer_id: str,
        authentication_session_id: str,
        valid_from: datetime,
        valid_until: datetime,
    ) -> AuthenticatedIssuerPrincipal:
        return self._state.mint_principal(
            issuer_kind=issuer_kind,
            issuer_id=issuer_id,
            authentication_session_id=authentication_session_id,
            valid_from=valid_from,
            valid_until=valid_until,
        )


class _AuthenticatedHumanApprovalMinter(_ProcessLocalCapability):
    """Private capability installed into one exact Human approval adapter."""

    __slots__ = ("_state",)

    def mint(
        self,
        *,
        principal: AuthenticatedIssuerPrincipal,
        run: AgentExecutionRun,
        approval_session_id: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None = None,
    ) -> AuthenticatedHumanApproval:
        return self._state.mint_human_approval(
            principal=principal,
            run=run,
            approval_session_id=approval_session_id,
            provenance_reference=provenance_reference,
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )


class _AuthenticatedPolicyDecisionMinter(_ProcessLocalCapability):
    """Private capability installed into one exact policy decision adapter."""

    __slots__ = ("_state",)

    def mint(
        self,
        *,
        principal: AuthenticatedIssuerPrincipal,
        run: AgentExecutionRun,
        decision: str,
        policy_revision: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None = None,
    ) -> AuthenticatedPolicyDecision:
        return self._state.mint_policy_decision(
            principal=principal,
            run=run,
            decision=decision,
            policy_revision=policy_revision,
            provenance_reference=provenance_reference,
            valid_from=valid_from,
            valid_until=valid_until,
            requested_lifetime=requested_lifetime,
        )


def _mint_capability(
    capability_type: type[_ProcessLocalCapability],
    values: dict[str, object],
) -> _ProcessLocalCapability:
    value = object.__new__(capability_type)
    for name, item in values.items():
        object.__setattr__(value, name, item)
    return value


@dataclass(slots=True)
class _IssuanceReservation:
    run: AgentExecutionRun
    principal: AuthenticatedIssuerPrincipal
    authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision
    effective_lifetime: timedelta


@dataclass(slots=True)
class _IssuedRecord:
    run: AgentExecutionRun
    principal: AuthenticatedIssuerPrincipal
    authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision
    effective_lifetime: timedelta
    grant: AgentExecutionAuthorizationGrant
    sealed_grant: tuple[object, ...]
    presentation: IssuedAgentExecutionAuthorizationGrant
    producer_epoch: object
    owned_session: OwnedAuthorizationDomainSession
    domain_identity: AuthorizationDomainIdentity
    issuer_state_epoch: object
    audit_material: AgentExecutionAuthorizationGrantAuditMaterial
    state: str


@dataclass(slots=True)
class _BurnedIssuance:
    run: AgentExecutionRun


@dataclass(slots=True)
class _ProductionAttempt:
    result: AgentExecutionAuthorizationGrantProductionResult | None
    provisional_record: _IssuedRecord | None
    reserved_key: tuple[str, str] | None
    run: AgentExecutionRun
    principal: AuthenticatedIssuerPrincipal | None
    authority_proof: (
        AuthenticatedHumanApproval | AuthenticatedPolicyDecision | None
    )
    sampled_time: datetime | None


_MAX_GRANT_ID_ATTEMPTS = 4
_COMPOSITION_LOCK = Lock()
_COMPOSITION_CLAIMS: list[
    tuple[OwnedAuthorizationDomainSession, _AgentExecutionAuthorizationGrantProducerBinding]
] = []


def _grant_snapshot(grant: AgentExecutionAuthorizationGrant) -> tuple[object, ...]:
    return (
        grant.grant_id,
        grant.run,
        grant.authorization_domain_id,
        grant.issuer_kind,
        grant.issuer_id,
        grant.provenance_reference,
        grant.issued_at,
        grant.expires_at,
    )


def _normalized_utc(value: object) -> datetime | None:
    if type(value) is not datetime or value.tzinfo is None:
        return None
    try:
        if value.utcoffset() != timedelta(0):
            return None
        normalized = value.astimezone(timezone.utc)
        if normalized.astimezone(value.tzinfo) != value:
            return None
    except Exception:
        return None
    return normalized


def _exact_utc(value: object) -> bool:
    return _normalized_utc(value) is not None


def _format_utc(value: datetime) -> str:
    normalized = _normalized_utc(value)
    if normalized is None:
        raise ValueError("timestamp is not losslessly convertible UTC")
    timespec = "microseconds" if normalized.microsecond else "seconds"
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def _run_correlation(run: object) -> str | None:
    if type(run) is not AgentExecutionRun:
        return None
    validation = validate_agent_execution_run(run)
    if not validation.valid or validation.run is not run:
        return None
    contract = run.contract
    values = (
        run.run_id,
        contract.task_id,
        contract.workflow_id,
        contract.stage_id,
        contract.role_id,
        contract.actor_id,
        contract.runtime_option_id,
        contract.option_id,
        contract.environment_id,
        contract.operation_id,
        contract.resource,
        contract.execution_mode,
    )
    canonical = "".join(f"{len(value)}:{value}" for value in values)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_intrinsically_valid_exact_run(value: object) -> bool:
    """Reject malformed authority subjects before any Run equality."""

    if type(value) is not AgentExecutionRun:
        return False
    try:
        result = validate_agent_execution_run(value)
    except Exception:
        return False
    return result.valid and result.run is value


def _build_audit_material(
    *,
    outcome: AgentExecutionAuthorizationGrantProductionOutcome,
    identity: AuthorizationDomainIdentity,
    run: object,
    principal: AuthenticatedIssuerPrincipal | None,
    authority_proof: (
        AuthenticatedHumanApproval | AuthenticatedPolicyDecision | None
    ),
    grant: AgentExecutionAuthorizationGrant | None,
    issued_at: str | None,
    expires_at: str | None,
    policy_revision: object,
) -> AgentExecutionAuthorizationGrantAuditMaterial:
    retry = _RETRY_FOR_OUTCOME[outcome]
    issuer_kind = None
    issuer_id = None
    if type(principal) is AuthenticatedIssuerPrincipal:
        issuer_kind = principal._issuer_kind
        issuer_id = principal._issuer_id
    provenance = None
    if type(authority_proof) in (
        AuthenticatedHumanApproval,
        AuthenticatedPolicyDecision,
    ):
        provenance = authority_proof._provenance_reference
    run_id = (
        run.run_id
        if type(run) is AgentExecutionRun
        and type(run.run_id) is str
        and bool(run.run_id)
        else None
    )
    revision = (
        policy_revision
        if type(policy_revision) is str and bool(policy_revision)
        else None
    )
    return AgentExecutionAuthorizationGrantAuditMaterial(
        outcome=outcome,
        retry_disposition=retry,
        issuer_kind=issuer_kind,
        issuer_id=issuer_id,
        authorization_domain_id=identity.authorization_domain_id,
        ledger_instance_id=identity.ledger_instance_id,
        domain_generation=identity.domain_generation,
        run_id=run_id,
        run_subject_correlation=_run_correlation(run),
        grant_id=grant.grant_id if grant is not None else None,
        provenance_reference=provenance,
        issued_at=issued_at,
        expires_at=expires_at,
        lifetime_policy_revision=revision,
    )


def _minimal_integrity_audit(
    identity: AuthorizationDomainIdentity,
    run: object,
) -> AgentExecutionAuthorizationGrantAuditMaterial:
    outcome = AgentExecutionAuthorizationGrantProductionOutcome.INTEGRITY_FAILURE
    return AgentExecutionAuthorizationGrantAuditMaterial(
        outcome=outcome,
        retry_disposition=_RETRY_FOR_OUTCOME[outcome],
        issuer_kind=None,
        issuer_id=None,
        authorization_domain_id=identity.authorization_domain_id,
        ledger_instance_id=identity.ledger_instance_id,
        domain_generation=identity.domain_generation,
        run_id=(
            run.run_id
            if type(run) is AgentExecutionRun
            and type(run.run_id) is str
            and bool(run.run_id)
            else None
        ),
        run_subject_correlation=None,
        grant_id=None,
        provenance_reference=None,
        issued_at=None,
        expires_at=None,
        lifetime_policy_revision=None,
    )


class _ProducerState:
    __slots__ = (
        "owned_session",
        "identity",
        "identity_adapter",
        "human_approval_adapter",
        "policy_decision_adapter",
        "issuer_state_authority",
        "issuer_entitlement_policy",
        "lifetime_policy",
        "utc_clock",
        "grant_id_source",
        "producer_epoch",
        "lock",
        "closed",
        "principal_proofs",
        "authority_proofs",
        "issuances",
        "presentations",
        "allocated_grant_ids",
        "producer",
        "authentication_port",
        "jit_guard",
        "jit_entry_proofs",
    )

    def __init__(
        self,
        *,
        owned_session: OwnedAuthorizationDomainSession,
        identity: AuthorizationDomainIdentity,
        identity_adapter: IssuerPrincipalIdentityAdapter,
        human_approval_adapter: HumanApprovalAuthenticationAdapter | None,
        policy_decision_adapter: PolicyDecisionAuthenticationAdapter | None,
        issuer_state_authority: IssuerStateAuthority,
        issuer_entitlement_policy: IssuerEntitlementPolicy,
        lifetime_policy: AgentExecutionAuthorizationGrantLifetimePolicy,
        utc_clock: TrustedUtcClock,
        grant_id_source: GrantIdSource,
    ) -> None:
        self.owned_session = owned_session
        self.identity = identity
        self.identity_adapter = identity_adapter
        self.human_approval_adapter = human_approval_adapter
        self.policy_decision_adapter = policy_decision_adapter
        self.issuer_state_authority = issuer_state_authority
        self.issuer_entitlement_policy = issuer_entitlement_policy
        self.lifetime_policy = lifetime_policy
        self.utc_clock = utc_clock
        self.grant_id_source = grant_id_source
        self.producer_epoch = object()
        self.lock = Lock()
        self.jit_guard = None
        self.jit_entry_proofs = {}
        self.closed = False
        self.principal_proofs: dict[int, AuthenticatedIssuerPrincipal] = {}
        self.authority_proofs: dict[
            int,
            AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
        ] = {}
        self.issuances: dict[
            tuple[str, str],
            _IssuanceReservation | _IssuedRecord | _BurnedIssuance,
        ] = {}
        self.presentations: dict[int, _IssuedRecord] = {}
        self.allocated_grant_ids: set[str] = set()
        self.producer = _new_producer(self)
        self.authentication_port = _new_authentication_port(self)

    def result(
        self,
        outcome: AgentExecutionAuthorizationGrantProductionOutcome,
        *,
        run: object,
        principal: AuthenticatedIssuerPrincipal | None = None,
        authority_proof: (
            AuthenticatedHumanApproval | AuthenticatedPolicyDecision | None
        ) = None,
        grant: AgentExecutionAuthorizationGrant | None = None,
        presentation: IssuedAgentExecutionAuthorizationGrant | None = None,
        issued_at: str | None = None,
        expires_at: str | None = None,
        audit_material: AgentExecutionAuthorizationGrantAuditMaterial | None = None,
    ) -> AgentExecutionAuthorizationGrantProductionResult:
        retry = _RETRY_FOR_OUTCOME[outcome]
        if outcome not in (
            AgentExecutionAuthorizationGrantProductionOutcome.ISSUED,
            AgentExecutionAuthorizationGrantProductionOutcome.
            EXISTING_EXACT_ISSUANCE,
        ):
            presentation = None
        try:
            audit = audit_material or _build_audit_material(
                outcome=outcome,
                identity=self.identity,
                run=run,
                principal=principal,
                authority_proof=authority_proof,
                grant=grant,
                issued_at=issued_at,
                expires_at=expires_at,
                policy_revision=self.lifetime_policy.revision,
            )
        except Exception:
            outcome = (
                AgentExecutionAuthorizationGrantProductionOutcome.
                INTEGRITY_FAILURE
            )
            retry = _RETRY_FOR_OUTCOME[outcome]
            presentation = None
            audit = _minimal_integrity_audit(self.identity, run)
        return AgentExecutionAuthorizationGrantProductionResult(
            outcome=outcome,
            retry_disposition=retry,
            presentation=presentation,
            audit_material=audit,
        )

    def observe_enabled_epoch(
        self,
        principal: AuthenticatedIssuerPrincipal,
    ) -> bool:
        observed = self.issuer_state_authority.observe_issuer_state(
            issuer_kind=principal._issuer_kind,
            issuer_id=principal._issuer_id,
        )
        if type(observed) is not tuple or len(observed) != 2:
            raise TypeError("issuer state observation is not canonical")
        enabled, epoch = observed
        if type(enabled) is not bool:
            raise TypeError("issuer state enablement is not an exact boolean")
        return enabled and epoch == principal._issuer_state_epoch

    def mint_principal(
        self,
        *,
        issuer_kind: str,
        issuer_id: str,
        authentication_session_id: str,
        valid_from: datetime,
        valid_until: datetime,
    ) -> AuthenticatedIssuerPrincipal:
        with self.lock:
            if self.closed:
                raise RuntimeError("the Producer binding is closed")
            if (
                type(issuer_kind) is not str
                or issuer_kind not in ("human", "policy")
            ):
                raise ValueError("issuer_kind must be 'human' or 'policy'")
            for value, name in (
                (issuer_id, "issuer_id"),
                (authentication_session_id, "authentication_session_id"),
            ):
                if type(value) is not str or not value:
                    raise ValueError(f"{name} must be an exact nonempty string")
            adapter_epoch = self.identity_adapter.current_epoch()
            observed = self.issuer_state_authority.observe_issuer_state(
                issuer_kind=issuer_kind,
                issuer_id=issuer_id,
            )
            if type(observed) is not tuple or len(observed) != 2:
                raise TypeError("issuer state observation is not canonical")
            enabled, issuer_state_epoch = observed
            if type(enabled) is not bool:
                raise TypeError("issuer state enablement is not an exact boolean")
            principal = _mint_capability(
                AuthenticatedIssuerPrincipal,
                {
                    "_adapter": self.identity_adapter,
                    "_adapter_epoch": adapter_epoch,
                    "_producer_epoch": self.producer_epoch,
                    "_owned_session": self.owned_session,
                    "_domain_identity": self.identity,
                    "_issuer_kind": issuer_kind,
                    "_issuer_id": issuer_id,
                    "_authentication_session_id": authentication_session_id,
                    "_issuer_state_epoch": issuer_state_epoch,
                    "_valid_from": valid_from,
                    "_valid_until": valid_until,
                },
            )
            assert type(principal) is AuthenticatedIssuerPrincipal
            self.principal_proofs[id(principal)] = principal
            return principal

    def mint_human_approval(
        self,
        *,
        principal: AuthenticatedIssuerPrincipal,
        run: AgentExecutionRun,
        approval_session_id: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None,
    ) -> AuthenticatedHumanApproval:
        with self.lock:
            if self.closed:
                raise RuntimeError("the Producer binding is closed")
            if self.human_approval_adapter is None:
                raise RuntimeError("no Human approval adapter is configured")
            if (
                type(principal) is not AuthenticatedIssuerPrincipal
                or self.principal_proofs.get(id(principal)) is not principal
                or principal._issuer_kind != "human"
            ):
                raise TypeError("approval principal is not configured Human proof")
            if type(run) is not AgentExecutionRun:
                raise TypeError(
                    "approval subject must be an exact AgentExecutionRun"
                )
            if not _is_intrinsically_valid_exact_run(run):
                raise ValueError("approval subject Run is intrinsically invalid")
            for value, name in (
                (approval_session_id, "approval_session_id"),
                (provenance_reference, "provenance_reference"),
            ):
                if type(value) is not str or not value:
                    raise ValueError(f"{name} must be an exact nonempty string")
            adapter_epoch = self.human_approval_adapter.current_epoch()
            proof = _mint_capability(
                AuthenticatedHumanApproval,
                {
                    "_adapter": self.human_approval_adapter,
                    "_adapter_epoch": adapter_epoch,
                    "_producer_epoch": self.producer_epoch,
                    "_owned_session": self.owned_session,
                    "_domain_identity": self.identity,
                    "_principal": principal,
                    "_run": run,
                    "_approval_session_id": approval_session_id,
                    "_provenance_reference": provenance_reference,
                    "_valid_from": valid_from,
                    "_valid_until": valid_until,
                    "_requested_lifetime": requested_lifetime,
                },
            )
            assert type(proof) is AuthenticatedHumanApproval
            self.authority_proofs[id(proof)] = proof
            return proof

    def mint_policy_decision(
        self,
        *,
        principal: AuthenticatedIssuerPrincipal,
        run: AgentExecutionRun,
        decision: str,
        policy_revision: str,
        provenance_reference: str,
        valid_from: datetime,
        valid_until: datetime,
        requested_lifetime: timedelta | None,
    ) -> AuthenticatedPolicyDecision:
        with self.lock:
            if self.closed:
                raise RuntimeError("the Producer binding is closed")
            if self.policy_decision_adapter is None:
                raise RuntimeError("no policy decision adapter is configured")
            if (
                type(principal) is not AuthenticatedIssuerPrincipal
                or self.principal_proofs.get(id(principal)) is not principal
                or principal._issuer_kind != "policy"
            ):
                raise TypeError("decision principal is not configured policy proof")
            if type(run) is not AgentExecutionRun:
                raise TypeError(
                    "policy subject must be an exact AgentExecutionRun"
                )
            if not _is_intrinsically_valid_exact_run(run):
                raise ValueError("policy subject Run is intrinsically invalid")
            if type(decision) is not str or decision not in ("allow", "deny"):
                raise ValueError("decision must be exactly 'allow' or 'deny'")
            for value, name in (
                (policy_revision, "policy_revision"),
                (provenance_reference, "provenance_reference"),
            ):
                if type(value) is not str or not value:
                    raise ValueError(f"{name} must be an exact nonempty string")
            adapter_epoch = self.policy_decision_adapter.current_epoch()
            proof = _mint_capability(
                AuthenticatedPolicyDecision,
                {
                    "_adapter": self.policy_decision_adapter,
                    "_adapter_epoch": adapter_epoch,
                    "_producer_epoch": self.producer_epoch,
                    "_owned_session": self.owned_session,
                    "_domain_identity": self.identity,
                    "_principal": principal,
                    "_run": run,
                    "_decision": decision,
                    "_policy_revision": policy_revision,
                    "_provenance_reference": provenance_reference,
                    "_valid_from": valid_from,
                    "_valid_until": valid_until,
                    "_requested_lifetime": requested_lifetime,
                },
            )
            assert type(proof) is AuthenticatedPolicyDecision
            self.authority_proofs[id(proof)] = proof
            return proof


class AgentExecutionAuthorizationGrantProducer(_ProcessLocalCapability):
    """Trusted-composition Producer bound to one exact Owned Session."""

    __slots__ = ("_state",)

    def produce(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
    ) -> AgentExecutionAuthorizationGrantProductionResult:
        """Produce or exactly retry one Run-bound private Grant presentation."""

        state = self._state
        with state.lock:
            if state.closed:
                return state.result(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    PRODUCER_CLOSED,
                    run=run,
                )

        try:
            operation = state.owned_session.operation()
        except Exception as error:
            outcome = (
                AgentExecutionAuthorizationGrantProductionOutcome.
                OWNERSHIP_LOST
                if isinstance(error, OwnedAuthorizationDomainSessionLostError)
                else AgentExecutionAuthorizationGrantProductionOutcome.
                DOMAIN_NOT_OWNED
            )
            with state.lock:
                return state.result(outcome, run=run)
        if not isinstance(operation, AuthorizationDomainOperationLease):
            with state.lock:
                return state.result(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    DOMAIN_NOT_OWNED,
                    run=run,
                )
        try:
            lease = operation.__enter__()
        except Exception as error:
            outcome = (
                AgentExecutionAuthorizationGrantProductionOutcome.
                OWNERSHIP_LOST
                if isinstance(error, OwnedAuthorizationDomainSessionLostError)
                else AgentExecutionAuthorizationGrantProductionOutcome.
                DOMAIN_NOT_OWNED
            )
            with state.lock:
                return state.result(outcome, run=run)

        lock_acquired = False
        exit_attempted = False
        candidate_key: tuple[str, str] | None = None
        entry_before: _IssuanceReservation | _IssuedRecord | _BurnedIssuance | None = None
        attempt: _ProductionAttempt | None = None
        try:
            state.lock.acquire()
            lock_acquired = True
            candidate_key = (
                (state.identity.authorization_domain_id, run.run_id)
                if type(run) is AgentExecutionRun
                and type(run.run_id) is str
                and bool(run.run_id)
                else None
            )
            entry_before = (
                state.issuances.get(candidate_key)
                if candidate_key is not None
                else None
            )
            internal_error: Exception | None = None

            if state.closed:
                attempt = _ProductionAttempt(
                    result=state.result(
                        AgentExecutionAuthorizationGrantProductionOutcome.
                        PRODUCER_CLOSED,
                        run=run,
                    ),
                    provisional_record=None,
                    reserved_key=None,
                    run=run,
                    principal=None,
                    authority_proof=None,
                    sampled_time=None,
                )
            else:
                try:
                    attempt = _prepare_attempt(
                        state,
                        lease=lease,
                        run=run,
                        authenticated_principal=authenticated_principal,
                        authority_proof=authority_proof,
                    )
                except Exception as error:
                    internal_error = error
                except BaseException:
                    raise

            exit_error: Exception | None = None
            try:
                exit_attempted = True
                operation.__exit__(
                    type(internal_error) if internal_error is not None else None,
                    internal_error,
                    (
                        internal_error.__traceback__
                        if internal_error is not None
                        else None
                    ),
                )
            except Exception as error:
                exit_error = error

            transitioned_entry = (
                state.issuances.get(candidate_key)
                if candidate_key is not None
                else None
            )
            transition_requires_burn = (
                candidate_key is not None
                and transitioned_entry is not None
                and transitioned_entry is not entry_before
                and type(transitioned_entry)
                in (_IssuanceReservation, _IssuedRecord)
            )
            reserved_key = (
                attempt.reserved_key if attempt is not None else None
            )
            burn_key = reserved_key or (
                candidate_key if transition_requires_burn else None
            )

            if exit_error is not None:
                if burn_key is not None:
                    if attempt is not None and attempt.provisional_record is not None:
                        state.presentations.pop(
                            id(attempt.provisional_record.presentation),
                            None,
                        )
                        attempt.provisional_record.state = "burned"
                    state.issuances[burn_key] = _BurnedIssuance(run=run)
                    return state.result(
                        AgentExecutionAuthorizationGrantProductionOutcome.
                        RUN_ISSUANCE_CONFLICT,
                        run=run,
                        principal=(attempt.principal if attempt is not None else None),
                        authority_proof=(
                            attempt.authority_proof
                            if attempt is not None
                            else None
                        ),
                        issued_at=(
                            _format_utc(attempt.sampled_time)
                            if attempt is not None
                            and attempt.sampled_time is not None
                            else None
                        ),
                    )
                return state.result(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    OWNERSHIP_LOST,
                    run=run,
                )

            if internal_error is not None:
                if burn_key is not None:
                    if type(transitioned_entry) is _IssuedRecord:
                        state.presentations.pop(
                            id(transitioned_entry.presentation),
                            None,
                        )
                        transitioned_entry.state = "burned"
                    state.issuances[burn_key] = _BurnedIssuance(run=run)
                    return state.result(
                        AgentExecutionAuthorizationGrantProductionOutcome.
                        RUN_ISSUANCE_CONFLICT,
                        run=run,
                    )
                return state.result(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    INTEGRITY_FAILURE,
                    run=run,
                )

            assert attempt is not None
            if attempt.provisional_record is not None:
                record = attempt.provisional_record
                key = (
                    state.identity.authorization_domain_id,
                    record.run.run_id,
                )
                try:
                    record.state = "issued"
                    state.issuances[key] = record
                    state.presentations[id(record.presentation)] = record
                    result = state.result(
                        AgentExecutionAuthorizationGrantProductionOutcome.ISSUED,
                        run=record.run,
                        principal=record.principal,
                        authority_proof=record.authority_proof,
                        grant=record.grant,
                        presentation=record.presentation,
                        issued_at=record.grant.issued_at,
                        expires_at=record.grant.expires_at,
                        audit_material=record.audit_material,
                    )
                    if (
                        result.outcome
                        is not AgentExecutionAuthorizationGrantProductionOutcome.
                        ISSUED
                        or result.presentation is not record.presentation
                    ):
                        raise RuntimeError("issued result lost canonical integrity")
                except Exception:
                    state.presentations.pop(id(record.presentation), None)
                    record.state = "burned"
                    state.issuances[key] = _BurnedIssuance(run=record.run)
                    return state.result(
                        AgentExecutionAuthorizationGrantProductionOutcome.
                        RUN_ISSUANCE_CONFLICT,
                        run=record.run,
                        principal=record.principal,
                        authority_proof=record.authority_proof,
                    )
                return result
            assert attempt.result is not None
            return attempt.result
        finally:
            try:
                if not exit_attempted:
                    exit_attempted = True
                    exception_type, exception, traceback = sys.exc_info()
                    operation.__exit__(
                        exception_type,
                        exception,
                        traceback,
                    )
            finally:
                if lock_acquired:
                    if sys.exc_info()[0] is not None and candidate_key is not None:
                        transitioned = state.issuances.get(candidate_key)
                        if (
                            transitioned is not None
                            and transitioned is not entry_before
                            and type(transitioned)
                            in (_IssuanceReservation, _IssuedRecord)
                        ):
                            if type(transitioned) is _IssuedRecord:
                                state.presentations.pop(
                                    id(transitioned.presentation),
                                    None,
                                )
                                transitioned.state = "burned"
                            state.issuances[candidate_key] = _BurnedIssuance(
                                run=run
                            )
                    state.lock.release()

    def close(self) -> None:
        """Idempotently close the Producer and paired authentication port."""

        state = self._state
        with state.lock:
            state.closed = True


class _AgentExecutionAuthorizationGrantAuthenticationPort(
    _ProcessLocalCapability
):
    __slots__ = ("_state",)

    def authenticate_grant(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        state = self._state
        with state.lock:
            if state.closed:
                return None
            if type(presented_grant) is not IssuedAgentExecutionAuthorizationGrant:
                return None
            record = state.presentations.get(id(presented_grant))
            try:
                issuance_key = None
                if record is not None:
                    issuance_key = (
                        state.identity.authorization_domain_id,
                        record.run.run_id,
                    )
                if (
                    record is None
                    or record.presentation is not presented_grant
                    or record.state != "issued"
                    or state.issuances.get(issuance_key) is not record
                    or record.producer_epoch is not state.producer_epoch
                    or record.owned_session is not state.owned_session
                    or record.domain_identity != state.identity
                    or record.issuer_state_epoch
                    != record.principal._issuer_state_epoch
                    or state.principal_proofs.get(id(record.principal))
                    is not record.principal
                    or state.authority_proofs.get(id(record.authority_proof))
                    is not record.authority_proof
                    or record.authority_proof._principal is not record.principal
                    or not _is_intrinsically_valid_exact_run(
                        record.authority_proof._run
                    )
                    or record.authority_proof._run != record.run
                    or record.grant.run != record.run
                    or record.grant.authorization_domain_id
                    != state.identity.authorization_domain_id
                    or record.grant.issuer_kind != record.principal._issuer_kind
                    or record.grant.issuer_id != record.principal._issuer_id
                    or record.grant.provenance_reference
                    != record.authority_proof._provenance_reference
                ):
                    return None
                if state.owned_session.identity != state.identity:
                    return None
                if _grant_snapshot(record.grant) != record.sealed_grant:
                    return None
                grant_result = validate_agent_execution_authorization_grant(
                    record.grant
                )
                if (
                    not grant_result.valid
                    or grant_result.grant is not record.grant
                ):
                    return None
            except Exception:
                return None
            try:
                if not state.observe_enabled_epoch(record.principal):
                    return None
            except Exception:
                return None
            return record.grant


class _AgentExecutionAuthorizationGrantProducerBinding(_ProcessLocalCapability):
    """Private Producer/port bundle for a trusted concrete root."""

    __slots__ = ("_state",)

    @property
    def producer(self) -> AgentExecutionAuthorizationGrantProducer:
        return self._state.producer

    @property
    def grant_authentication(
        self,
    ) -> AgentExecutionAuthorizationGrantAuthenticationPort:
        return self._state.authentication_port


def _new_producer(
    state: _ProducerState,
) -> AgentExecutionAuthorizationGrantProducer:
    producer = object.__new__(AgentExecutionAuthorizationGrantProducer)
    object.__setattr__(producer, "_state", state)
    return producer


def _new_authentication_port(
    state: _ProducerState,
) -> _AgentExecutionAuthorizationGrantAuthenticationPort:
    port = object.__new__(_AgentExecutionAuthorizationGrantAuthenticationPort)
    object.__setattr__(port, "_state", state)
    return port


def _new_binding(
    state: _ProducerState,
) -> _AgentExecutionAuthorizationGrantProducerBinding:
    binding = object.__new__(_AgentExecutionAuthorizationGrantProducerBinding)
    object.__setattr__(binding, "_state", state)
    return binding


def _new_adapter_minter(
    minter_type: type[_ProcessLocalCapability],
    state: _ProducerState,
) -> _ProcessLocalCapability:
    minter = object.__new__(minter_type)
    object.__setattr__(minter, "_state", state)
    return minter


def _verified_principal(
    state: _ProducerState,
    principal: object,
) -> AgentExecutionAuthorizationGrantProductionOutcome | None:
    if (
        type(principal) is not AuthenticatedIssuerPrincipal
        or state.principal_proofs.get(id(principal)) is not principal
        or principal._adapter is not state.identity_adapter
        or principal._producer_epoch is not state.producer_epoch
        or principal._owned_session is not state.owned_session
        or principal._domain_identity != state.identity
    ):
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            UNAUTHENTICATED_PRINCIPAL
        )
    try:
        adapter_epoch = state.identity_adapter.current_epoch()
        valid = state.identity_adapter.validate_authenticated_principal(
            principal
        )
    except Exception:
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            IDENTITY_UNAVAILABLE
        )
    if adapter_epoch != principal._adapter_epoch or type(valid) is not bool or not valid:
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            UNAUTHENTICATED_PRINCIPAL
        )
    return None


def _verified_authority_structure(
    state: _ProducerState,
    *,
    run: AgentExecutionRun,
    principal: AuthenticatedIssuerPrincipal,
    authority_proof: object,
) -> AgentExecutionAuthorizationGrantProductionOutcome | None:
    if principal._issuer_kind == "human":
        if authority_proof is None:
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                APPROVAL_MISSING
            )
        if type(authority_proof) is not AuthenticatedHumanApproval:
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        if (
            state.human_approval_adapter is None
            or state.authority_proofs.get(id(authority_proof)) is not authority_proof
            or authority_proof._adapter is not state.human_approval_adapter
            or authority_proof._producer_epoch is not state.producer_epoch
            or authority_proof._owned_session is not state.owned_session
        ):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        proof_run = getattr(authority_proof, "_run", None)
        if not _is_intrinsically_valid_exact_run(proof_run):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        if (
            authority_proof._principal is not principal
            or proof_run != run
        ):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                APPROVAL_SUBJECT_MISMATCH
            )
    elif principal._issuer_kind == "policy":
        if type(authority_proof) is not AuthenticatedPolicyDecision:
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        if (
            state.policy_decision_adapter is None
            or state.authority_proofs.get(id(authority_proof)) is not authority_proof
            or authority_proof._adapter is not state.policy_decision_adapter
            or authority_proof._producer_epoch is not state.producer_epoch
            or authority_proof._owned_session is not state.owned_session
            or authority_proof._principal is not principal
        ):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        decision = getattr(authority_proof, "_decision", None)
        if type(decision) is not str or decision not in ("allow", "deny"):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
        proof_run = getattr(authority_proof, "_run", None)
        if (
            not _is_intrinsically_valid_exact_run(proof_run)
            or proof_run != run
        ):
            return (
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
    else:
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            UNAUTHENTICATED_PRINCIPAL
        )
    if authority_proof._domain_identity != state.identity:
        if (
            authority_proof._domain_identity.authorization_domain_id
            != state.identity.authorization_domain_id
            or authority_proof._domain_identity.ledger_instance_id
            != state.identity.ledger_instance_id
        ):
            return AgentExecutionAuthorizationGrantProductionOutcome.DOMAIN_MISMATCH
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            GENERATION_MISMATCH
        )
    return None


def _validate_authority_adapter(
    state: _ProducerState,
    proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
) -> bool:
    if type(proof) is AuthenticatedHumanApproval:
        adapter = state.human_approval_adapter
        assert adapter is not None
        if adapter.current_epoch() != proof._adapter_epoch:
            return False
        valid = adapter.validate_authenticated_human_approval(proof)
    else:
        adapter = state.policy_decision_adapter
        assert adapter is not None
        if adapter.current_epoch() != proof._adapter_epoch:
            return False
        valid = adapter.validate_authenticated_policy_decision(proof)
    return type(valid) is bool and valid


def _valid_window(start: object, end: object) -> bool:
    normalized_start = _normalized_utc(start)
    normalized_end = _normalized_utc(end)
    return (
        normalized_start is not None
        and normalized_end is not None
        and normalized_start < normalized_end
    )


def _effective_lifetime(
    state: _ProducerState,
    proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
) -> timedelta | None:
    policy = state.lifetime_policy
    if (
        type(policy) is not AgentExecutionAuthorizationGrantLifetimePolicy
        or type(policy.default_lifetime) is not timedelta
        or type(policy.maximum_lifetime) is not timedelta
        or policy.default_lifetime <= timedelta(0)
        or policy.maximum_lifetime <= timedelta(0)
        or policy.default_lifetime > policy.maximum_lifetime
        or type(policy.revision) is not str
        or not policy.revision
    ):
        return None
    requested = proof._requested_lifetime
    if requested is None:
        return policy.default_lifetime
    if (
        type(requested) is not timedelta
        or requested <= timedelta(0)
        or requested > policy.default_lifetime
        or requested > policy.maximum_lifetime
    ):
        return None
    return requested


def _allocate_grant_id(
    state: _ProducerState,
) -> tuple[str | None, AgentExecutionAuthorizationGrantProductionOutcome | None]:
    collision = False
    for _ in range(_MAX_GRANT_ID_ATTEMPTS):
        try:
            material = state.grant_id_source.random_bytes(32)
        except Exception:
            return (
                None,
                AgentExecutionAuthorizationGrantProductionOutcome.
                GRANT_ID_GENERATION_FAILURE,
            )
        if type(material) is not bytes or len(material) != 32:
            return (
                None,
                AgentExecutionAuthorizationGrantProductionOutcome.
                GRANT_ID_GENERATION_FAILURE,
            )
        candidate = material.hex()
        if candidate in state.allocated_grant_ids:
            collision = True
            continue
        state.allocated_grant_ids.add(candidate)
        return candidate, None
    assert collision
    return (
        None,
        AgentExecutionAuthorizationGrantProductionOutcome.GRANT_ID_COLLISION,
    )


def _identity_outcome(
    expected: AuthorizationDomainIdentity,
    observed: object,
) -> AgentExecutionAuthorizationGrantProductionOutcome | None:
    if type(observed) is not AuthorizationDomainIdentity:
        return AgentExecutionAuthorizationGrantProductionOutcome.DOMAIN_NOT_OWNED
    if (
        observed.authorization_domain_id != expected.authorization_domain_id
        or observed.ledger_instance_id != expected.ledger_instance_id
    ):
        return AgentExecutionAuthorizationGrantProductionOutcome.DOMAIN_MISMATCH
    if observed.domain_generation != expected.domain_generation:
        return (
            AgentExecutionAuthorizationGrantProductionOutcome.
            GENERATION_MISMATCH
        )
    return None


def _prepare_attempt(
    state: _ProducerState,
    *,
    lease: AuthorizationDomainOperationLease,
    run: AgentExecutionRun,
    authenticated_principal: AuthenticatedIssuerPrincipal,
    authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
) -> _ProductionAttempt:
    def failure(
        outcome: AgentExecutionAuthorizationGrantProductionOutcome,
        *,
        principal: AuthenticatedIssuerPrincipal | None = None,
        proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision | None = None,
        sampled: datetime | None = None,
        reserved_key: tuple[str, str] | None = None,
    ) -> _ProductionAttempt:
        return _ProductionAttempt(
            result=state.result(
                outcome,
                run=run,
                principal=principal,
                authority_proof=proof,
                issued_at=_format_utc(sampled) if sampled is not None else None,
            ),
            provisional_record=None,
            reserved_key=reserved_key,
            run=run,
            principal=principal,
            authority_proof=proof,
            sampled_time=sampled,
        )

    try:
        current_identity = state.owned_session.identity
        lease_identity = lease.identity
    except Exception:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.OWNERSHIP_LOST
        )
    for observed in (current_identity, lease_identity):
        identity_failure = _identity_outcome(state.identity, observed)
        if identity_failure is not None:
            return failure(identity_failure)

    run_result = validate_agent_execution_run(run)
    if not run_result.valid or run_result.run is not run:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.INVALID_RUN
        )

    principal_failure = _verified_principal(state, authenticated_principal)
    if principal_failure is not None:
        return failure(principal_failure)
    principal = authenticated_principal

    # JIT decisions share the authentication predicates, never issuance purpose.
    if id(authority_proof) in state.jit_entry_proofs:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.AUTHORITY_PROOF_INVALID,
            principal=principal,
        )

    authority_failure = _verified_authority_structure(
        state,
        run=run,
        principal=principal,
        authority_proof=authority_proof,
    )
    if authority_failure is not None:
        return failure(authority_failure, principal=principal)
    proof = authority_proof
    assert type(proof) in (
        AuthenticatedHumanApproval,
        AuthenticatedPolicyDecision,
    )

    if not _valid_window(principal._valid_from, principal._valid_until):
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            UNAUTHENTICATED_PRINCIPAL,
            principal=principal,
            proof=proof,
        )
    if not _valid_window(proof._valid_from, proof._valid_until):
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            AUTHORITY_PROOF_INVALID,
            principal=principal,
            proof=proof,
        )

    try:
        if not _validate_authority_adapter(state, proof):
            return failure(
                AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID,
                principal=principal,
                proof=proof,
            )
    except Exception:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            AUTHORITY_PROOF_INVALID,
            principal=principal,
            proof=proof,
        )

    try:
        sampled = state.utc_clock.now_utc()
    except Exception:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.CLOCK_FAILURE,
            principal=principal,
            proof=proof,
        )
    sampled_utc = _normalized_utc(sampled)
    if sampled_utc is None:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.CLOCK_FAILURE,
            principal=principal,
            proof=proof,
        )
    sampled = sampled_utc

    principal_valid_from = _normalized_utc(principal._valid_from)
    principal_valid_until = _normalized_utc(principal._valid_until)
    proof_valid_from = _normalized_utc(proof._valid_from)
    proof_valid_until = _normalized_utc(proof._valid_until)
    assert principal_valid_from is not None
    assert principal_valid_until is not None
    assert proof_valid_from is not None
    assert proof_valid_until is not None

    if not (principal_valid_from <= sampled < principal_valid_until):
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            UNAUTHENTICATED_PRINCIPAL,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    if not (proof_valid_from <= sampled < proof_valid_until):
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            AUTHORITY_PROOF_INVALID,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )

    try:
        issuer_enabled = state.observe_enabled_epoch(principal)
    except Exception:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            IDENTITY_UNAVAILABLE,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    if not issuer_enabled:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.ISSUER_DISABLED,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )

    if type(proof) is AuthenticatedPolicyDecision:
        decision = getattr(proof, "_decision", None)
        if type(decision) is not str or decision != "allow":
            outcome = (
                AgentExecutionAuthorizationGrantProductionOutcome.POLICY_DENIED
                if type(decision) is str and decision == "deny"
                else AgentExecutionAuthorizationGrantProductionOutcome.
                AUTHORITY_PROOF_INVALID
            )
            return failure(
                outcome,
                principal=principal,
                proof=proof,
                sampled=sampled,
            )

    try:
        entitled = state.issuer_entitlement_policy.is_entitled(
            run=run,
            domain_identity=state.identity,
            issuer_kind=principal._issuer_kind,
            issuer_id=principal._issuer_id,
        )
    except Exception:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            INTEGRITY_FAILURE,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    if type(entitled) is not bool:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            INTEGRITY_FAILURE,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    if not entitled:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.NOT_ENTITLED,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )

    effective_lifetime = _effective_lifetime(state, proof)
    if effective_lifetime is None:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.LIFETIME_INVALID,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    try:
        expires = sampled + effective_lifetime
    except (OverflowError, ValueError):
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.LIFETIME_INVALID,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )
    if not _exact_utc(expires) or sampled >= expires:
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.LIFETIME_INVALID,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )

    key = (state.identity.authorization_domain_id, run.run_id)
    existing = state.issuances.get(key)
    if existing is not None:
        if existing.run != run:
            return failure(
                AgentExecutionAuthorizationGrantProductionOutcome.
                RUN_IDENTITY_CONFLICT,
                principal=principal,
                proof=proof,
                sampled=sampled,
            )
        if type(existing) is _BurnedIssuance:
            return failure(
                AgentExecutionAuthorizationGrantProductionOutcome.
                RUN_ISSUANCE_CONFLICT,
                principal=principal,
                proof=proof,
                sampled=sampled,
            )
        if type(existing) is _IssuedRecord:
            try:
                existing_validation = (
                    validate_agent_execution_authorization_grant(existing.grant)
                )
                coherent_existing = (
                    existing.state == "issued"
                    and state.presentations.get(id(existing.presentation))
                    is existing
                    and existing.presentation is not None
                    and existing.run == existing.grant.run
                    and existing.domain_identity == state.identity
                    and existing.owned_session is state.owned_session
                    and existing.producer_epoch is state.producer_epoch
                    and existing.issuer_state_epoch
                    == existing.principal._issuer_state_epoch
                    and state.principal_proofs.get(id(existing.principal))
                    is existing.principal
                    and state.authority_proofs.get(id(existing.authority_proof))
                    is existing.authority_proof
                    and existing.authority_proof._principal
                    is existing.principal
                    and _is_intrinsically_valid_exact_run(
                        existing.authority_proof._run
                    )
                    and existing.authority_proof._run == existing.run
                    and _grant_snapshot(existing.grant)
                    == existing.sealed_grant
                    and existing_validation.valid
                    and existing_validation.grant is existing.grant
                )
            except Exception:
                coherent_existing = False
            if not coherent_existing:
                state.presentations.pop(id(existing.presentation), None)
                existing.state = "burned"
                state.issuances[key] = _BurnedIssuance(run=run)
                return failure(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    RUN_ISSUANCE_CONFLICT,
                    principal=principal,
                    proof=proof,
                    sampled=sampled,
                )
            if (
                existing.principal is principal
                and existing.authority_proof is proof
                and existing.effective_lifetime == effective_lifetime
            ):
                result = state.result(
                    AgentExecutionAuthorizationGrantProductionOutcome.
                    EXISTING_EXACT_ISSUANCE,
                    run=run,
                    principal=principal,
                    authority_proof=proof,
                    grant=existing.grant,
                    presentation=existing.presentation,
                    issued_at=existing.grant.issued_at,
                    expires_at=existing.grant.expires_at,
                )
                return _ProductionAttempt(
                    result=result,
                    provisional_record=None,
                    reserved_key=None,
                    run=run,
                    principal=principal,
                    authority_proof=proof,
                    sampled_time=sampled,
                )
            return failure(
                AgentExecutionAuthorizationGrantProductionOutcome.
                RUN_ALREADY_ISSUED,
                principal=principal,
                proof=proof,
                sampled=sampled,
            )
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            RUN_ISSUANCE_CONFLICT,
            principal=principal,
            proof=proof,
            sampled=sampled,
        )

    state.issuances[key] = _IssuanceReservation(
        run=run,
        principal=principal,
        authority_proof=proof,
        effective_lifetime=effective_lifetime,
    )

    grant_id, id_failure = _allocate_grant_id(state)
    if id_failure is not None:
        state.issuances.pop(key, None)
        return failure(
            id_failure,
            principal=principal,
            proof=proof,
            sampled=sampled,
            reserved_key=key,
        )
    assert grant_id is not None

    issued_at = _format_utc(sampled)
    expires_at = _format_utc(expires)
    grant = AgentExecutionAuthorizationGrant(
        grant_id=grant_id,
        run=run,
        authorization_domain_id=state.identity.authorization_domain_id,
        issuer_kind=principal._issuer_kind,
        issuer_id=principal._issuer_id,
        provenance_reference=proof._provenance_reference,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    validation = validate_agent_execution_authorization_grant(grant)
    if not validation.valid or validation.grant is not grant:
        state.issuances.pop(key, None)
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            INTEGRITY_FAILURE,
            principal=principal,
            proof=proof,
            sampled=sampled,
            reserved_key=key,
        )

    try:
        audit = _build_audit_material(
            outcome=AgentExecutionAuthorizationGrantProductionOutcome.ISSUED,
            identity=state.identity,
            run=run,
            principal=principal,
            authority_proof=proof,
            grant=grant,
            issued_at=issued_at,
            expires_at=expires_at,
            policy_revision=state.lifetime_policy.revision,
        )
    except Exception:
        state.issuances.pop(key, None)
        return failure(
            AgentExecutionAuthorizationGrantProductionOutcome.
            INTEGRITY_FAILURE,
            principal=principal,
            proof=proof,
            sampled=sampled,
            reserved_key=key,
        )

    presentation = _mint_capability(
        IssuedAgentExecutionAuthorizationGrant,
        {},
    )
    assert type(presentation) is IssuedAgentExecutionAuthorizationGrant
    record = _IssuedRecord(
        run=run,
        principal=principal,
        authority_proof=proof,
        effective_lifetime=effective_lifetime,
        grant=grant,
        sealed_grant=_grant_snapshot(grant),
        presentation=presentation,
        producer_epoch=state.producer_epoch,
        owned_session=state.owned_session,
        domain_identity=state.identity,
        issuer_state_epoch=principal._issuer_state_epoch,
        audit_material=audit,
        state="provisional",
    )
    state.issuances[key] = record
    return _ProductionAttempt(
        result=None,
        provisional_record=record,
        reserved_key=key,
        run=run,
        principal=principal,
        authority_proof=proof,
        sampled_time=sampled,
    )



def _attach_jit_authority_guard(state, guard):
    """Private install-once cooperative extension; no public contract change."""
    from engineering_orchestration._jit_execution_attempt_authorization import (
        _AuthorityGuard, _ProducerCoordinationLock,
    )
    if (type(guard) is not _AuthorityGuard or guard.state is not state
            or guard.session is not state.owned_session):
        raise TypeError("entry guard must be the exact Session/Producer coordinator")
    if state.jit_guard is not None or state.closed:
        raise RuntimeError("Producer already guarded or closed")
    # Trusted root attaches under S/G before publication; P serializes installation.
    original = state.lock
    with original:
        if state.jit_guard is not None or state.closed:
            raise RuntimeError("Producer already guarded or closed")
        state.jit_guard = guard
        state.lock = _ProducerCoordinationLock(guard, original)


def _mint_jit_entry_decision(state, guard, subject, principal, **fields):
    """Mint a NEW authenticated proof for entry, never repurpose issuance proof."""
    from engineering_orchestration._jit_execution_attempt_authorization import _validate_jit_subject
    _validate_jit_subject(subject, guard)
    if state.jit_guard is not guard:
        raise RuntimeError("foreign entry guard")
    with guard.mutation_scope(state, "proof_mint"):
        if principal._issuer_kind == "human":
            proof = state.mint_human_approval(
                principal=principal, run=subject.run, requested_lifetime=None, **fields)
        elif principal._issuer_kind == "policy":
            proof = state.mint_policy_decision(
                principal=principal, run=subject.run, requested_lifetime=None, **fields)
        else:
            raise ValueError("unsupported issuer kind")
        with state.lock:
            state.jit_entry_proofs[id(proof)] = (proof, subject, guard, principal)
        return proof


def _validate_jit_entry_decision(state, guard, subject, principal, proof, now):
    """Held-G/P leaf validation; performs no issuance or independent time sample."""
    from engineering_orchestration._jit_execution_attempt_authorization import _validate_jit_subject
    _validate_jit_subject(subject, guard)
    if state.closed or state.jit_guard is not guard:
        return "producer_closed"
    registered = state.jit_entry_proofs.get(id(proof))
    if (registered is None or registered[0] is not proof or registered[1] != subject
            or registered[2] is not guard or registered[3] is not principal):
        return "invalid_entry_proof"
    failure = _verified_principal(state, principal)
    if failure is not None:
        return failure.value
    _, issuer_kind, issuer_id, _ = subject.dispatch_identity
    if (principal._issuer_kind, principal._issuer_id) != (issuer_kind, issuer_id):
        return "wrong_issuer"
    if not state.observe_enabled_epoch(principal):
        return "issuer_disabled"
    failure = _verified_authority_structure(
        state, run=subject.run, principal=principal, authority_proof=proof)
    if failure is not None:
        return failure.value
    if not _validate_authority_adapter(state, proof):
        return "authority_proof_invalid"
    if type(proof) is AuthenticatedPolicyDecision and proof._decision != "allow":
        return "policy_denied"
    for value in (principal, proof):
        if (not _valid_window(value._valid_from, value._valid_until)
                or (now is not None and not (
                    _normalized_utc(value._valid_from) <= now < _normalized_utc(value._valid_until)))):
            return "authority_expired"
    if state.issuer_entitlement_policy.is_entitled(
        run=subject.run, domain_identity=state.identity,
        issuer_kind=principal._issuer_kind, issuer_id=principal._issuer_id) is not True:
        return "not_entitled"
    return None


def _require_callable(value: object, method_name: str, dependency: str) -> None:
    if not callable(getattr(value, method_name, None)):
        raise TypeError(f"{dependency} must implement {method_name}()")


def _compose_agent_execution_authorization_grant_producer(
    *,
    owned_session: OwnedAuthorizationDomainSession,
    identity_adapter: IssuerPrincipalIdentityAdapter,
    human_approval_adapter: HumanApprovalAuthenticationAdapter | None,
    policy_decision_adapter: PolicyDecisionAuthenticationAdapter | None,
    issuer_state_authority: IssuerStateAuthority,
    issuer_entitlement_policy: IssuerEntitlementPolicy,
    lifetime_policy: AgentExecutionAuthorizationGrantLifetimePolicy,
    utc_clock: TrustedUtcClock,
    grant_id_source: GrantIdSource,
) -> _AgentExecutionAuthorizationGrantProducerBinding:
    """Create one private Producer/port binding for one exact Owned Session.

    A trusted concrete composition root must install ``grant_authentication``
    into the same session's AIO-047 coordinator before exposing only
    ``producer`` to orchestration.  The provider-neutral Owned Session API is
    intentionally not widened with a public installation hook.
    """

    if not isinstance(owned_session, OwnedAuthorizationDomainSession):
        raise TypeError("owned_session must be an OwnedAuthorizationDomainSession")
    try:
        identity = owned_session.identity
    except Exception as error:
        raise TypeError("owned_session identity is unavailable") from error
    if type(identity) is not AuthorizationDomainIdentity:
        raise TypeError("owned_session identity must be exact canonical identity")
    if human_approval_adapter is None and policy_decision_adapter is None:
        raise ValueError("at least one authority adapter must be configured")

    _require_callable(identity_adapter, "current_epoch", "identity_adapter")
    _require_callable(
        identity_adapter,
        "validate_authenticated_principal",
        "identity_adapter",
    )
    _require_callable(
        identity_adapter,
        "_bind_authenticated_issuer_principal_minter",
        "identity_adapter",
    )
    if human_approval_adapter is not None:
        _require_callable(
            human_approval_adapter,
            "current_epoch",
            "human_approval_adapter",
        )
        _require_callable(
            human_approval_adapter,
            "validate_authenticated_human_approval",
            "human_approval_adapter",
        )
        _require_callable(
            human_approval_adapter,
            "_bind_authenticated_human_approval_minter",
            "human_approval_adapter",
        )
    if policy_decision_adapter is not None:
        _require_callable(
            policy_decision_adapter,
            "current_epoch",
            "policy_decision_adapter",
        )
        _require_callable(
            policy_decision_adapter,
            "validate_authenticated_policy_decision",
            "policy_decision_adapter",
        )
        _require_callable(
            policy_decision_adapter,
            "_bind_authenticated_policy_decision_minter",
            "policy_decision_adapter",
        )
    _require_callable(
        issuer_state_authority,
        "observe_issuer_state",
        "issuer_state_authority",
    )
    _require_callable(
        issuer_entitlement_policy,
        "is_entitled",
        "issuer_entitlement_policy",
    )
    if type(lifetime_policy) is not AgentExecutionAuthorizationGrantLifetimePolicy:
        raise TypeError("lifetime_policy must be the exact immutable policy type")
    _require_callable(utc_clock, "now_utc", "utc_clock")
    _require_callable(grant_id_source, "random_bytes", "grant_id_source")

    with _COMPOSITION_LOCK:
        if any(session is owned_session for session, _ in _COMPOSITION_CLAIMS):
            raise RuntimeError(
                "an authorization Grant Producer is already bound to this session"
            )
        operation = owned_session.operation()
        if not isinstance(operation, AuthorizationDomainOperationLease):
            raise TypeError(
                "owned_session must return an AuthorizationDomainOperationLease"
            )
        with operation as lease:
            lease_identity = lease.identity
            if type(lease_identity) is not AuthorizationDomainIdentity:
                raise TypeError("operation lease identity must be canonical")
            if lease_identity != identity or owned_session.identity != identity:
                raise RuntimeError(
                    "owned_session identity changed during Producer composition"
                )
        state = _ProducerState(
            owned_session=owned_session,
            identity=identity,
            identity_adapter=identity_adapter,
            human_approval_adapter=human_approval_adapter,
            policy_decision_adapter=policy_decision_adapter,
            issuer_state_authority=issuer_state_authority,
            issuer_entitlement_policy=issuer_entitlement_policy,
            lifetime_policy=lifetime_policy,
            utc_clock=utc_clock,
            grant_id_source=grant_id_source,
        )
        binding = _new_binding(state)
        _COMPOSITION_CLAIMS.append((owned_session, binding))
        try:
            identity_adapter._bind_authenticated_issuer_principal_minter(
                _new_adapter_minter(
                    _AuthenticatedIssuerPrincipalMinter,
                    state,
                )
            )
            if human_approval_adapter is not None:
                human_approval_adapter._bind_authenticated_human_approval_minter(
                    _new_adapter_minter(
                        _AuthenticatedHumanApprovalMinter,
                        state,
                    )
                )
            if policy_decision_adapter is not None:
                policy_decision_adapter._bind_authenticated_policy_decision_minter(
                    _new_adapter_minter(
                        _AuthenticatedPolicyDecisionMinter,
                        state,
                    )
                )
        except BaseException:
            with state.lock:
                state.closed = True
            raise
        return binding
