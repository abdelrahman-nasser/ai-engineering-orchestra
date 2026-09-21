"""Pure preparation dry run for one controlled repository file read.

This internal experiment composes caller-supplied evidence for one abstract
operation and one exact resource. It never opens the resource, discovers or
changes permissions, creates an execution request, dispatches work, or invokes
an Agent. Its provisional permission evidence and freshness field remain
harness-specific and are not the canonical AIO-038 Environment Operation
Permission Observation contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)


class ReadOnlyExecutionCapabilityState(StrEnum):
    """Caller-supplied technical capability state."""

    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class ReadOnlyExecutionPermissionState(StrEnum):
    """Caller-supplied environment permission state."""

    ALLOWED = "allowed"
    DENIED = "denied"
    UNKNOWN = "unknown"


class ReadOnlyExecutionPermissionFreshness(StrEnum):
    """Explicit currentness of caller-supplied permission evidence."""

    CURRENT = "current"
    STALE = "stale"
    UNKNOWN = "unknown"


class ReadOnlyExecutionAuthorizationState(StrEnum):
    """Caller-supplied Human or policy authorization state."""

    GRANTED = "granted"
    DENIED = "denied"
    MISSING = "missing"


class ReadOnlyExecutionAuthorizationSource(StrEnum):
    """Declared provenance, not machine-verified authority."""

    HUMAN_PROVIDED = "human_provided"
    POLICY_PROVIDED = "policy_provided"
    NOT_SUPPLIED = "not_supplied"


class ReadOnlyExecutionPreparationOutcome(StrEnum):
    """Closed ordinary outcomes for a valid preparation dry run."""

    POTENTIALLY_EXECUTABLE = "potentially_executable"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class ReadOnlyExecutionPreparationReason(StrEnum):
    """Stable reasons in deterministic evaluation order."""

    CANDIDATE_PREREQUISITES_BLOCKED = "candidate_prerequisites_blocked"
    CANDIDATE_PREREQUISITES_UNRESOLVED = "candidate_prerequisites_unresolved"
    CAPABILITY_SCOPE_MISMATCH = "capability_scope_mismatch"
    CAPABILITY_ABSENT = "capability_absent"
    CAPABILITY_UNKNOWN = "capability_unknown"
    PERMISSION_SCOPE_MISMATCH = "permission_scope_mismatch"
    PERMISSION_STALE = "permission_stale"
    PERMISSION_FRESHNESS_UNKNOWN = "permission_freshness_unknown"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_UNKNOWN = "permission_unknown"
    AUTHORIZATION_SCOPE_MISMATCH = "authorization_scope_mismatch"
    AUTHORIZATION_DENIED = "authorization_denied"
    AUTHORIZATION_MISSING = "authorization_missing"
    AUTHORIZED_BUT_NOT_PERMITTED = "authorized_but_not_permitted"
    PERMITTED_BUT_NOT_AUTHORIZED = "permitted_but_not_authorized"
    ALL_PREPARATION_EVIDENCE_POSITIVE = "all_preparation_evidence_positive"


@dataclass(frozen=True)
class ReadOnlyExecutionCapabilityEvidence:
    """Technical capability evidence for one Runtime and operation."""

    runtime_option_id: str
    operation_id: str
    state: ReadOnlyExecutionCapabilityState


@dataclass(frozen=True)
class ReadOnlyExecutionPermissionEvidence:
    """Provisional harness evidence, not the canonical AIO-038 observation."""

    runtime_option_id: str
    environment_id: str
    operation_id: str
    resource: str
    state: ReadOnlyExecutionPermissionState
    freshness: ReadOnlyExecutionPermissionFreshness


@dataclass(frozen=True)
class ReadOnlyExecutionAuthorizationEvidence:
    """Declared authorization evidence for one exact future action scope."""

    task_id: str
    workflow_id: str
    stage_id: str
    role_id: str
    actor_id: str
    runtime_option_id: str
    option_id: str
    environment_id: str
    operation_id: str
    resource: str
    source: ReadOnlyExecutionAuthorizationSource
    state: ReadOnlyExecutionAuthorizationState


@dataclass(frozen=True)
class ReadOnlyExecutionPreparationFinding:
    """Stable invalid-input finding."""

    code: str
    message: str


@dataclass(frozen=True)
class ReadOnlyExecutionPreparationResult:
    """Atomic invalid result or immutable preparation dry-run report."""

    valid: bool
    findings: tuple[ReadOnlyExecutionPreparationFinding, ...]
    candidate_result: AgentExecutionCandidatePrerequisiteResult | None
    operation_id: str | None
    resource: str | None
    environment_id: str | None
    capability_evidence: ReadOnlyExecutionCapabilityEvidence | None
    permission_evidence: ReadOnlyExecutionPermissionEvidence | None
    authorization_evidence: ReadOnlyExecutionAuthorizationEvidence | None
    outcome: ReadOnlyExecutionPreparationOutcome | None
    reasons: tuple[ReadOnlyExecutionPreparationReason, ...]


_OPERATION_ID = "repository_file_read"
_CONTROLLED_RESOURCE = "workflows/README.md"
_GLOB_META = "*?[]{}"

_CANDIDATE_BLOCKING_REASONS = frozenset(
    {
        AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.AGENT_RUNTIME_OPTION_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.INFERENCE_OPTION_UNAVAILABLE,
    }
)
_CANDIDATE_SUCCESS_REASON = (
    AgentExecutionCandidatePrerequisiteReason.
    ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED
)


def _finding(code: str, message: str) -> ReadOnlyExecutionPreparationFinding:
    return ReadOnlyExecutionPreparationFinding(code=code, message=message)


def _invalid(
    findings: list[ReadOnlyExecutionPreparationFinding],
) -> ReadOnlyExecutionPreparationResult:
    """Return an atomic invalid result with no partial report fields."""

    return ReadOnlyExecutionPreparationResult(
        valid=False,
        findings=tuple(findings),
        candidate_result=None,
        operation_id=None,
        resource=None,
        environment_id=None,
        capability_evidence=None,
        permission_evidence=None,
        authorization_evidence=None,
        outcome=None,
        reasons=(),
    )


def _is_exact_text(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and value == value.strip()
        and not any(ord(character) < 32 or ord(character) == 127 for character in value)
    )


def _is_operation_id(value: object) -> bool:
    return (
        _is_exact_text(value)
        and value[0].islower()
        and value[0].isascii()
        and all(
            character.isascii()
            and (character.islower() or character.isdigit() or character == "_")
            for character in value
        )
    )


def _is_resource(value: object) -> bool:
    if not _is_exact_text(value):
        return False
    if "\\" in value or value.startswith(("/", "~")) or ":" in value:
        return False
    if any(character in value for character in _GLOB_META):
        return False
    segments = value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        return False
    return segments[-1] != ".md" and value.endswith(".md")


def _candidate_issue(
    candidate_result: object,
) -> ReadOnlyExecutionPreparationFinding | None:
    if type(candidate_result) is not AgentExecutionCandidatePrerequisiteResult:
        return _finding(
            "candidate_result_invalid_type",
            "Candidate result must be an exact AIO-034 result value.",
        )
    if candidate_result.valid is not True:
        return _finding(
            "candidate_result_not_valid",
            "Candidate result must be valid before preparation is assessed.",
        )

    identity_values: tuple[object, ...] = ()
    if (
        type(candidate_result.responsibility_key) is tuple
        and len(candidate_result.responsibility_key) == 4
    ):
        identity_values = candidate_result.responsibility_key + (
            candidate_result.actor_id,
            candidate_result.runtime_option_id,
            candidate_result.option_id,
        )

    reasons_are_exact = (
        type(candidate_result.reasons) is tuple
        and bool(candidate_result.reasons)
        and all(
            type(reason) is AgentExecutionCandidatePrerequisiteReason
            for reason in candidate_result.reasons
        )
    )
    reasons_are_canonical = False
    if reasons_are_exact:
        unique_reasons = frozenset(candidate_result.reasons)
        reasons_are_canonical = (
            len(unique_reasons) == len(candidate_result.reasons)
            and candidate_result.reasons
            == tuple(
                reason
                for reason in AgentExecutionCandidatePrerequisiteReason
                if reason in unique_reasons
            )
        )

    coherent_outcome = False
    if reasons_are_canonical:
        reason_set = frozenset(candidate_result.reasons)
        if (
            candidate_result.outcome
            is AgentExecutionCandidatePrerequisiteOutcome.SATISFIED
        ):
            coherent_outcome = candidate_result.reasons == (
                _CANDIDATE_SUCCESS_REASON,
            )
        elif (
            candidate_result.outcome
            is AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
        ):
            coherent_outcome = (
                _CANDIDATE_SUCCESS_REASON not in reason_set
                and bool(_CANDIDATE_BLOCKING_REASONS.intersection(reason_set))
            )
        elif (
            candidate_result.outcome
            is AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
        ):
            coherent_outcome = (
                _CANDIDATE_SUCCESS_REASON not in reason_set
                and not _CANDIDATE_BLOCKING_REASONS.intersection(reason_set)
            )

    if (
        candidate_result.findings != ()
        or len(identity_values) != 7
        or not all(_is_exact_text(value) for value in identity_values)
        or type(candidate_result.outcome)
        is not AgentExecutionCandidatePrerequisiteOutcome
        or not coherent_outcome
    ):
        return _finding(
            "candidate_result_inconsistent",
            "Candidate result does not satisfy the AIO-034 result invariants.",
        )
    return None


def _capability_issue(
    evidence: object,
) -> ReadOnlyExecutionPreparationFinding | None:
    if type(evidence) is not ReadOnlyExecutionCapabilityEvidence:
        return _finding(
            "capability_evidence_invalid_type",
            "Capability evidence must be one exact capability evidence value.",
        )
    if (
        not _is_exact_text(evidence.runtime_option_id)
        or not _is_operation_id(evidence.operation_id)
        or type(evidence.state) is not ReadOnlyExecutionCapabilityState
    ):
        return _finding(
            "capability_evidence_invalid",
            "Capability evidence contains malformed fields or state.",
        )
    return None


def _permission_issue(
    evidence: object,
) -> ReadOnlyExecutionPreparationFinding | None:
    if type(evidence) is not ReadOnlyExecutionPermissionEvidence:
        return _finding(
            "permission_evidence_invalid_type",
            "Permission evidence must be one exact permission evidence value.",
        )
    if (
        not _is_exact_text(evidence.runtime_option_id)
        or not _is_exact_text(evidence.environment_id)
        or not _is_operation_id(evidence.operation_id)
        or not _is_resource(evidence.resource)
        or type(evidence.state) is not ReadOnlyExecutionPermissionState
        or type(evidence.freshness) is not ReadOnlyExecutionPermissionFreshness
    ):
        return _finding(
            "permission_evidence_invalid",
            "Permission evidence contains malformed fields, state, or freshness.",
        )
    return None


def _authorization_issue(
    evidence: object,
) -> ReadOnlyExecutionPreparationFinding | None:
    if type(evidence) is not ReadOnlyExecutionAuthorizationEvidence:
        return _finding(
            "authorization_evidence_invalid_type",
            "Authorization evidence must be one exact authorization evidence value.",
        )
    scope_values = (
        evidence.task_id,
        evidence.workflow_id,
        evidence.stage_id,
        evidence.role_id,
        evidence.actor_id,
        evidence.runtime_option_id,
        evidence.option_id,
        evidence.environment_id,
    )
    if (
        not all(_is_exact_text(value) for value in scope_values)
        or not _is_operation_id(evidence.operation_id)
        or not _is_resource(evidence.resource)
        or type(evidence.source) is not ReadOnlyExecutionAuthorizationSource
        or type(evidence.state) is not ReadOnlyExecutionAuthorizationState
    ):
        return _finding(
            "authorization_evidence_invalid",
            "Authorization evidence contains malformed fields, source, or state.",
        )
    source_and_state_are_coherent = (
        evidence.state is ReadOnlyExecutionAuthorizationState.MISSING
        and evidence.source is ReadOnlyExecutionAuthorizationSource.NOT_SUPPLIED
    ) or (
        evidence.state
        in {
            ReadOnlyExecutionAuthorizationState.GRANTED,
            ReadOnlyExecutionAuthorizationState.DENIED,
        }
        and evidence.source
        in {
            ReadOnlyExecutionAuthorizationSource.HUMAN_PROVIDED,
            ReadOnlyExecutionAuthorizationSource.POLICY_PROVIDED,
        }
    )
    if not source_and_state_are_coherent:
        return _finding(
            "authorization_source_state_inconsistent",
            "Authorization source and state are inconsistent.",
        )
    return None


def assess_read_only_execution_preparation(
    candidate_result: AgentExecutionCandidatePrerequisiteResult,
    *,
    operation_id: str,
    resource: str,
    environment_id: str,
    capability_evidence: ReadOnlyExecutionCapabilityEvidence,
    permission_evidence: ReadOnlyExecutionPermissionEvidence,
    authorization_evidence: ReadOnlyExecutionAuthorizationEvidence,
) -> ReadOnlyExecutionPreparationResult:
    """Assess supplied facts without accessing or preparing an invocation."""

    findings: list[ReadOnlyExecutionPreparationFinding] = []

    candidate_finding = _candidate_issue(candidate_result)
    if candidate_finding is not None:
        findings.append(candidate_finding)

    if not _is_operation_id(operation_id):
        findings.append(
            _finding(
                "operation_id_invalid",
                "Operation ID must use canonical lower-snake-case syntax.",
            )
        )
    elif operation_id != _OPERATION_ID:
        findings.append(
            _finding(
                "operation_id_not_supported",
                f"Only operation '{_OPERATION_ID}' is controlled by this harness.",
            )
        )

    if not _is_resource(resource):
        findings.append(
            _finding(
                "resource_invalid",
                "Resource must be one canonical repository-relative Markdown path.",
            )
        )
    elif resource != _CONTROLLED_RESOURCE:
        findings.append(
            _finding(
                "resource_not_controlled",
                f"Only resource '{_CONTROLLED_RESOURCE}' is controlled.",
            )
        )

    if not _is_exact_text(environment_id):
        findings.append(
            _finding(
                "environment_id_invalid",
                "Environment ID must be a nonempty opaque exact string.",
            )
        )

    capability_finding = _capability_issue(capability_evidence)
    if capability_finding is not None:
        findings.append(capability_finding)

    permission_finding = _permission_issue(permission_evidence)
    if permission_finding is not None:
        findings.append(permission_finding)

    authorization_finding = _authorization_issue(authorization_evidence)
    if authorization_finding is not None:
        findings.append(authorization_finding)

    if findings:
        return _invalid(findings)

    assert candidate_result.responsibility_key is not None
    assert candidate_result.actor_id is not None
    assert candidate_result.runtime_option_id is not None
    assert candidate_result.option_id is not None
    assert candidate_result.outcome is not None

    candidate_identity = candidate_result.responsibility_key + (
        candidate_result.actor_id,
        candidate_result.runtime_option_id,
        candidate_result.option_id,
    )
    expected_authorization_scope = candidate_identity + (
        environment_id,
        operation_id,
        resource,
    )
    authorization_scope = (
        authorization_evidence.task_id,
        authorization_evidence.workflow_id,
        authorization_evidence.stage_id,
        authorization_evidence.role_id,
        authorization_evidence.actor_id,
        authorization_evidence.runtime_option_id,
        authorization_evidence.option_id,
        authorization_evidence.environment_id,
        authorization_evidence.operation_id,
        authorization_evidence.resource,
    )

    reason_set: set[ReadOnlyExecutionPreparationReason] = set()
    if (
        candidate_result.outcome
        is AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
    ):
        reason_set.add(
            ReadOnlyExecutionPreparationReason.CANDIDATE_PREREQUISITES_BLOCKED
        )
    elif (
        candidate_result.outcome
        is AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
    ):
        reason_set.add(
            ReadOnlyExecutionPreparationReason.CANDIDATE_PREREQUISITES_UNRESOLVED
        )

    capability_scope_matches = (
        capability_evidence.runtime_option_id == candidate_result.runtime_option_id
        and capability_evidence.operation_id == operation_id
    )
    if not capability_scope_matches:
        reason_set.add(
            ReadOnlyExecutionPreparationReason.CAPABILITY_SCOPE_MISMATCH
        )
    elif capability_evidence.state is ReadOnlyExecutionCapabilityState.ABSENT:
        reason_set.add(ReadOnlyExecutionPreparationReason.CAPABILITY_ABSENT)
    elif capability_evidence.state is ReadOnlyExecutionCapabilityState.UNKNOWN:
        reason_set.add(ReadOnlyExecutionPreparationReason.CAPABILITY_UNKNOWN)

    permission_scope_matches = (
        permission_evidence.runtime_option_id == candidate_result.runtime_option_id
        and permission_evidence.environment_id == environment_id
        and permission_evidence.operation_id == operation_id
        and permission_evidence.resource == resource
    )
    if not permission_scope_matches:
        reason_set.add(
            ReadOnlyExecutionPreparationReason.PERMISSION_SCOPE_MISMATCH
        )
    elif (
        permission_evidence.freshness
        is ReadOnlyExecutionPermissionFreshness.STALE
    ):
        reason_set.add(ReadOnlyExecutionPreparationReason.PERMISSION_STALE)
    elif (
        permission_evidence.freshness
        is ReadOnlyExecutionPermissionFreshness.UNKNOWN
    ):
        reason_set.add(
            ReadOnlyExecutionPreparationReason.PERMISSION_FRESHNESS_UNKNOWN
        )
    elif permission_evidence.state is ReadOnlyExecutionPermissionState.DENIED:
        reason_set.add(ReadOnlyExecutionPreparationReason.PERMISSION_DENIED)
    elif permission_evidence.state is ReadOnlyExecutionPermissionState.UNKNOWN:
        reason_set.add(ReadOnlyExecutionPreparationReason.PERMISSION_UNKNOWN)

    authorization_scope_matches = (
        authorization_scope == expected_authorization_scope
    )
    if not authorization_scope_matches:
        reason_set.add(
            ReadOnlyExecutionPreparationReason.AUTHORIZATION_SCOPE_MISMATCH
        )
    elif (
        authorization_evidence.state
        is ReadOnlyExecutionAuthorizationState.DENIED
    ):
        reason_set.add(ReadOnlyExecutionPreparationReason.AUTHORIZATION_DENIED)
    elif (
        authorization_evidence.state
        is ReadOnlyExecutionAuthorizationState.MISSING
    ):
        reason_set.add(ReadOnlyExecutionPreparationReason.AUTHORIZATION_MISSING)

    permission_is_current_denied = (
        permission_scope_matches
        and permission_evidence.freshness
        is ReadOnlyExecutionPermissionFreshness.CURRENT
        and permission_evidence.state is ReadOnlyExecutionPermissionState.DENIED
    )
    permission_is_current_allowed = (
        permission_scope_matches
        and permission_evidence.freshness
        is ReadOnlyExecutionPermissionFreshness.CURRENT
        and permission_evidence.state is ReadOnlyExecutionPermissionState.ALLOWED
    )
    authorization_is_granted = (
        authorization_scope_matches
        and authorization_evidence.state
        is ReadOnlyExecutionAuthorizationState.GRANTED
    )
    authorization_is_missing = (
        authorization_scope_matches
        and authorization_evidence.state
        is ReadOnlyExecutionAuthorizationState.MISSING
    )
    if permission_is_current_denied and authorization_is_granted:
        reason_set.add(
            ReadOnlyExecutionPreparationReason.AUTHORIZED_BUT_NOT_PERMITTED
        )
    if permission_is_current_allowed and authorization_is_missing:
        reason_set.add(
            ReadOnlyExecutionPreparationReason.PERMITTED_BUT_NOT_AUTHORIZED
        )

    blocking_reasons = {
        ReadOnlyExecutionPreparationReason.CANDIDATE_PREREQUISITES_BLOCKED,
        ReadOnlyExecutionPreparationReason.CAPABILITY_ABSENT,
        ReadOnlyExecutionPreparationReason.PERMISSION_DENIED,
        ReadOnlyExecutionPreparationReason.AUTHORIZATION_DENIED,
    }
    if blocking_reasons.intersection(reason_set):
        outcome = ReadOnlyExecutionPreparationOutcome.BLOCKED
    elif reason_set:
        outcome = ReadOnlyExecutionPreparationOutcome.UNRESOLVED
    else:
        outcome = ReadOnlyExecutionPreparationOutcome.POTENTIALLY_EXECUTABLE
        reason_set.add(
            ReadOnlyExecutionPreparationReason.ALL_PREPARATION_EVIDENCE_POSITIVE
        )

    reasons = tuple(
        reason
        for reason in ReadOnlyExecutionPreparationReason
        if reason in reason_set
    )
    return ReadOnlyExecutionPreparationResult(
        valid=True,
        findings=(),
        candidate_result=candidate_result,
        operation_id=operation_id,
        resource=resource,
        environment_id=environment_id,
        capability_evidence=capability_evidence,
        permission_evidence=permission_evidence,
        authorization_evidence=authorization_evidence,
        outcome=outcome,
        reasons=reasons,
    )
