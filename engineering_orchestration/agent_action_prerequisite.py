"""Pure Agent Action Prerequisite Assessment for one assigned Agent action.

This derived assessment composes already-derived candidate prerequisites with
one operation requirement and caller-supplied capability, permission, and
authorization validation results. It is immutable, deterministic, ephemeral,
and in memory. Even a satisfied result is diagnostic only: it is not an
authenticated grant, execution readiness, dispatch permission, invocation
permission, or assurance of success. This module performs no I/O, discovery,
enforcement, dispatch, invocation, or persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from engineering_orchestration._operation_vocabulary import (
    supported_core_operation_ids,
    validate_core_operation_id,
)
from engineering_orchestration._repository_resource import (
    validate_repository_resource,
)
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationFinding,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteFinding,
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionFinding,
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    validate_operation_requirement,
)
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityFinding,
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
)


class AgentActionPrerequisiteOutcome(StrEnum):
    """Closed ordinary outcomes for one valid action assessment."""

    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class AgentActionPrerequisiteReason(StrEnum):
    """Stable reasons for one valid action assessment outcome."""

    CANDIDATE_PREREQUISITES_BLOCKED = "candidate_prerequisites_blocked"
    CANDIDATE_PREREQUISITES_UNRESOLVED = (
        "candidate_prerequisites_unresolved"
    )
    RUNTIME_OPERATION_CAPABILITY_ABSENT = (
        "runtime_operation_capability_absent"
    )
    RUNTIME_OPERATION_CAPABILITY_UNKNOWN = (
        "runtime_operation_capability_unknown"
    )
    ENVIRONMENT_OPERATION_PERMISSION_DENIED = (
        "environment_operation_permission_denied"
    )
    ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN = (
        "environment_operation_permission_unknown"
    )
    AGENT_EXECUTION_AUTHORIZATION_DENIED = (
        "agent_execution_authorization_denied"
    )
    AGENT_EXECUTION_AUTHORIZATION_MISSING = (
        "agent_execution_authorization_missing"
    )
    ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED = (
        "all_currently_modeled_action_prerequisites_satisfied"
    )


@dataclass(frozen=True)
class AgentActionPrerequisiteFinding:
    """Stable invalid-input or cross-context assessment finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentActionPrerequisiteResult:
    """Atomic invalid result or one immutable diagnostic assessment."""

    valid: bool
    findings: tuple[AgentActionPrerequisiteFinding, ...]
    responsibility_key: tuple[str, str, str, str] | None
    actor_id: str | None
    runtime_option_id: str | None
    option_id: str | None
    environment_id: str | None
    operation_id: str | None
    resource: str | None
    outcome: AgentActionPrerequisiteOutcome | None
    reasons: tuple[AgentActionPrerequisiteReason, ...]


_AuthorizationSubject = tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
]

_CANDIDATE_REASON_ORDER = {
    reason: index
    for index, reason in enumerate(
        (
            AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            ACTOR_AVAILABILITY_UNKNOWN,
            AgentExecutionCandidatePrerequisiteReason.
            ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED,
            AgentExecutionCandidatePrerequisiteReason.
            RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED,
            AgentExecutionCandidatePrerequisiteReason.
            AGENT_RUNTIME_OPTION_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN,
            AgentExecutionCandidatePrerequisiteReason.
            INFERENCE_OPTION_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            INFERENCE_OPTION_AVAILABILITY_UNKNOWN,
        )
    )
}
_CANDIDATE_BLOCKING_REASONS = frozenset(
    (
        AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.
        AGENT_RUNTIME_OPTION_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.INFERENCE_OPTION_UNAVAILABLE,
    )
)
_CANDIDATE_PAIR_ENDPOINT_REASONS = frozenset(
    (
        AgentExecutionCandidatePrerequisiteReason.
        AGENT_RUNTIME_OPTION_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.
        AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN,
        AgentExecutionCandidatePrerequisiteReason.INFERENCE_OPTION_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.
        INFERENCE_OPTION_AVAILABILITY_UNKNOWN,
    )
)


def _finding(code: str, message: str) -> AgentActionPrerequisiteFinding:
    return AgentActionPrerequisiteFinding(code=code, message=message)


def _invalid(
    findings: Iterable[AgentActionPrerequisiteFinding],
) -> AgentActionPrerequisiteResult:
    return AgentActionPrerequisiteResult(
        valid=False,
        findings=tuple(findings),
        responsibility_key=None,
        actor_id=None,
        runtime_option_id=None,
        option_id=None,
        environment_id=None,
        operation_id=None,
        resource=None,
        outcome=None,
        reasons=(),
    )


def _is_exact_nonempty_string(value: object) -> bool:
    return type(value) is str and bool(value)


def _findings_are_canonical(
    findings: object,
    finding_type: type[object],
) -> bool:
    if type(findings) is not tuple or not findings:
        return False
    if any(
        type(finding) is not finding_type
        or not _is_exact_nonempty_string(getattr(finding, "code"))
        or not _is_exact_nonempty_string(getattr(finding, "message"))
        for finding in findings
    ):
        return False
    return True


def _candidate_result_is_coherent(
    result: AgentExecutionCandidatePrerequisiteResult,
) -> bool:
    if type(result.valid) is not bool or type(result.findings) is not tuple:
        return False
    if type(result.reasons) is not tuple:
        return False

    if not result.valid:
        return (
            _findings_are_canonical(
                result.findings,
                AgentExecutionCandidatePrerequisiteFinding,
            )
            and result.responsibility_key is None
            and result.actor_id is None
            and result.runtime_option_id is None
            and result.option_id is None
            and result.outcome is None
            and result.reasons == ()
        )

    if result.findings != ():
        return False
    if (
        type(result.responsibility_key) is not tuple
        or len(result.responsibility_key) != 4
        or not all(
            _is_exact_nonempty_string(value)
            for value in result.responsibility_key
        )
        or not _is_exact_nonempty_string(result.actor_id)
        or not _is_exact_nonempty_string(result.runtime_option_id)
        or not _is_exact_nonempty_string(result.option_id)
        or type(result.outcome)
        is not AgentExecutionCandidatePrerequisiteOutcome
        or not result.reasons
        or any(
            type(reason) is not AgentExecutionCandidatePrerequisiteReason
            for reason in result.reasons
        )
    ):
        return False

    reasons = result.reasons
    reason_set = set(reasons)
    satisfied_reason = (
        AgentExecutionCandidatePrerequisiteReason.
        ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED
    )
    if result.outcome is AgentExecutionCandidatePrerequisiteOutcome.SATISFIED:
        return reasons == (satisfied_reason,)
    if satisfied_reason in reason_set or len(reason_set) != len(reasons):
        return False
    if tuple(sorted(reasons, key=_CANDIDATE_REASON_ORDER.__getitem__)) != reasons:
        return False

    mutually_exclusive_pairs = (
        (
            AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            ACTOR_AVAILABILITY_UNKNOWN,
        ),
        (
            AgentExecutionCandidatePrerequisiteReason.
            AGENT_RUNTIME_OPTION_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN,
        ),
        (
            AgentExecutionCandidatePrerequisiteReason.
            INFERENCE_OPTION_UNAVAILABLE,
            AgentExecutionCandidatePrerequisiteReason.
            INFERENCE_OPTION_AVAILABILITY_UNKNOWN,
        ),
    )
    if any(
        first in reason_set and second in reason_set
        for first, second in mutually_exclusive_pairs
    ):
        return False
    compatibility_missing = (
        AgentExecutionCandidatePrerequisiteReason.
        RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED
    )
    if (
        compatibility_missing in reason_set
        and reason_set.intersection(_CANDIDATE_PAIR_ENDPOINT_REASONS)
    ):
        return False

    has_blocker = bool(reason_set.intersection(_CANDIDATE_BLOCKING_REASONS))
    if result.outcome is AgentExecutionCandidatePrerequisiteOutcome.BLOCKED:
        return has_blocker
    if result.outcome is AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED:
        return not has_blocker
    return False


def _capability_result_is_coherent(
    result: RuntimeOperationCapabilityValidationResult,
) -> bool:
    if type(result.valid) is not bool or type(result.findings) is not tuple:
        return False
    if type(result.normalized_observations) is not tuple:
        return False
    if not result.valid:
        return (
            _findings_are_canonical(
                result.findings,
                RuntimeOperationCapabilityFinding,
            )
            and result.normalized_observations == ()
        )
    if result.findings != ():
        return False

    observations = result.normalized_observations
    if any(
        type(observation) is not RuntimeOperationCapabilityObservation
        or not _is_exact_nonempty_string(observation.runtime_option_id)
        or type(observation.operation_id) is not str
        or validate_core_operation_id(observation.operation_id) is not None
        or type(observation.state) is not RuntimeOperationCapabilityState
        for observation in observations
    ):
        return False
    identities = tuple(
        (observation.runtime_option_id, observation.operation_id)
        for observation in observations
    )
    runtime_option_ids = tuple(sorted({identity[0] for identity in identities}))
    expected_identities = tuple(
        (runtime_option_id, operation_id)
        for runtime_option_id in runtime_option_ids
        for operation_id in supported_core_operation_ids()
    )
    return identities == expected_identities


def _permission_result_is_coherent(
    result: EnvironmentOperationPermissionValidationResult,
) -> bool:
    if type(result.valid) is not bool or type(result.findings) is not tuple:
        return False
    if type(result.normalized_observations) is not tuple:
        return False
    if not result.valid:
        return (
            _findings_are_canonical(
                result.findings,
                EnvironmentOperationPermissionFinding,
            )
            and result.normalized_observations == ()
        )
    if result.findings != ():
        return False

    observations = result.normalized_observations
    if any(
        type(observation) is not EnvironmentOperationPermissionObservation
        or not _is_exact_nonempty_string(observation.runtime_option_id)
        or not _is_exact_nonempty_string(observation.environment_id)
        or type(observation.operation_id) is not str
        or validate_core_operation_id(observation.operation_id) is not None
        or type(observation.resource) is not str
        or validate_repository_resource(observation.resource) is not None
        or type(observation.state) is not EnvironmentOperationPermissionState
        for observation in observations
    ):
        return False
    identities = tuple(
        (
            observation.runtime_option_id,
            observation.environment_id,
            observation.operation_id,
            observation.resource,
        )
        for observation in observations
    )
    represented_environments = {
        observation.environment_id for observation in observations
    }
    return (
        len(set(identities)) == len(identities)
        and identities == tuple(sorted(identities))
        and len(represented_environments) <= 1
    )


def _authorization_subject(
    evidence: AgentExecutionAuthorizationEvidence,
) -> _AuthorizationSubject:
    return (
        evidence.task_id,
        evidence.workflow_id,
        evidence.stage_id,
        evidence.role_id,
        evidence.actor_id,
        evidence.runtime_option_id,
        evidence.option_id,
        evidence.environment_id,
        evidence.operation_id,
        evidence.resource,
    )


def _authorization_result_is_coherent(
    result: AgentExecutionAuthorizationValidationResult,
) -> bool:
    if type(result.valid) is not bool or type(result.findings) is not tuple:
        return False
    if type(result.normalized_evidence) is not tuple:
        return False
    if not result.valid:
        return (
            _findings_are_canonical(
                result.findings,
                AgentExecutionAuthorizationFinding,
            )
            and result.normalized_evidence == ()
        )
    if result.findings != ():
        return False

    evidence_values = result.normalized_evidence
    if any(
        type(evidence) is not AgentExecutionAuthorizationEvidence
        or not _is_exact_nonempty_string(evidence.task_id)
        or not _is_exact_nonempty_string(evidence.workflow_id)
        or not _is_exact_nonempty_string(evidence.stage_id)
        or not _is_exact_nonempty_string(evidence.role_id)
        or not _is_exact_nonempty_string(evidence.actor_id)
        or not _is_exact_nonempty_string(evidence.runtime_option_id)
        or not _is_exact_nonempty_string(evidence.option_id)
        or not _is_exact_nonempty_string(evidence.environment_id)
        or type(evidence.operation_id) is not str
        or validate_core_operation_id(evidence.operation_id) is not None
        or type(evidence.resource) is not str
        or validate_repository_resource(evidence.resource) is not None
        or type(evidence.authority_kind)
        is not AgentExecutionAuthorizationAuthorityKind
        or not _is_exact_nonempty_string(evidence.authority_id)
        or not _is_exact_nonempty_string(evidence.provenance_reference)
        or type(evidence.state) is not AgentExecutionAuthorizationState
        for evidence in evidence_values
    ):
        return False
    subjects = tuple(_authorization_subject(evidence) for evidence in evidence_values)
    represented_environments = {
        evidence.environment_id for evidence in evidence_values
    }
    return (
        len(set(subjects)) == len(subjects)
        and subjects == tuple(sorted(subjects))
        and len(represented_environments) <= 1
    )


def assess_agent_action_prerequisites(
    candidate_result: AgentExecutionCandidatePrerequisiteResult,
    requirement: OperationRequirement,
    capability_result: RuntimeOperationCapabilityValidationResult,
    permission_result: EnvironmentOperationPermissionValidationResult,
    authorization_result: AgentExecutionAuthorizationValidationResult,
    *,
    environment_id: str,
) -> AgentActionPrerequisiteResult:
    """Assess all currently modeled prerequisites for one exact action.

    Parent result containers are checked for exact type and observable
    canonical coherence, but their provenance and caller truth cannot be
    authenticated here. Coherent invalid-parent findings retain their source
    codes, messages, and order. Ordinary outcomes are derived only when every
    input and cross-context relation is valid.
    """

    findings: list[AgentActionPrerequisiteFinding] = []

    candidate_is_valid = False
    if type(candidate_result) is not AgentExecutionCandidatePrerequisiteResult:
        findings.append(
            _finding(
                "agent_action_prerequisite_candidate_result_invalid_type",
                "candidate_result must be an exact "
                "AgentExecutionCandidatePrerequisiteResult value.",
            )
        )
    elif not _candidate_result_is_coherent(candidate_result):
        findings.append(
            _finding(
                "agent_action_prerequisite_candidate_result_incoherent",
                "candidate_result does not satisfy canonical "
                "AgentExecutionCandidatePrerequisiteResult invariants.",
            )
        )
    elif not candidate_result.valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in candidate_result.findings
        )
    else:
        candidate_is_valid = True

    requirement_result = validate_operation_requirement(requirement)
    requirement_is_valid = requirement_result.valid
    if not requirement_is_valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in requirement_result.findings
        )

    environment_is_valid = (
        type(environment_id) is str and bool(environment_id)
    )
    if not environment_is_valid:
        findings.append(
            _finding(
                "agent_action_prerequisite_environment_id_invalid",
                "Agent Action Prerequisite Assessment environment_id must be "
                "an exact nonempty string.",
            )
        )

    capability_is_valid = False
    if type(capability_result) is not RuntimeOperationCapabilityValidationResult:
        findings.append(
            _finding(
                "agent_action_prerequisite_capability_result_invalid_type",
                "capability_result must be an exact "
                "RuntimeOperationCapabilityValidationResult value.",
            )
        )
    elif not _capability_result_is_coherent(capability_result):
        findings.append(
            _finding(
                "agent_action_prerequisite_capability_result_incoherent",
                "capability_result does not satisfy canonical "
                "RuntimeOperationCapabilityValidationResult invariants.",
            )
        )
    elif not capability_result.valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in capability_result.findings
        )
    else:
        capability_is_valid = True

    permission_is_valid = False
    if (
        type(permission_result)
        is not EnvironmentOperationPermissionValidationResult
    ):
        findings.append(
            _finding(
                "agent_action_prerequisite_permission_result_invalid_type",
                "permission_result must be an exact "
                "EnvironmentOperationPermissionValidationResult value.",
            )
        )
    elif not _permission_result_is_coherent(permission_result):
        findings.append(
            _finding(
                "agent_action_prerequisite_permission_result_incoherent",
                "permission_result does not satisfy canonical "
                "EnvironmentOperationPermissionValidationResult invariants.",
            )
        )
    elif not permission_result.valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in permission_result.findings
        )
    else:
        permission_is_valid = True

    authorization_is_valid = False
    if (
        type(authorization_result)
        is not AgentExecutionAuthorizationValidationResult
    ):
        findings.append(
            _finding(
                "agent_action_prerequisite_authorization_result_invalid_type",
                "authorization_result must be an exact "
                "AgentExecutionAuthorizationValidationResult value.",
            )
        )
    elif not _authorization_result_is_coherent(authorization_result):
        findings.append(
            _finding(
                "agent_action_prerequisite_authorization_result_incoherent",
                "authorization_result does not satisfy canonical "
                "AgentExecutionAuthorizationValidationResult invariants.",
            )
        )
    elif not authorization_result.valid:
        findings.extend(
            _finding(finding.code, finding.message)
            for finding in authorization_result.findings
        )
    else:
        authorization_is_valid = True

    if candidate_is_valid and requirement_is_valid and capability_is_valid:
        required_capability_pair = (
            candidate_result.runtime_option_id,
            requirement_result.requirement.operation_id,
        )
        capability_pairs = {
            (observation.runtime_option_id, observation.operation_id)
            for observation in capability_result.normalized_observations
        }
        if required_capability_pair not in capability_pairs:
            runtime_option_id, operation_id = required_capability_pair
            findings.append(
                _finding(
                    "agent_action_prerequisite_capability_pair_missing",
                    "capability_result does not contain the required normalized "
                    "Runtime Operation Capability pair "
                    f"(runtime_option_id={runtime_option_id!r}, "
                    f"operation_id={operation_id!r}).",
                )
            )

    if environment_is_valid and permission_is_valid:
        permission_environments = sorted(
            {
                observation.environment_id
                for observation in permission_result.normalized_observations
                if observation.environment_id != environment_id
            }
        )
        for represented_environment in permission_environments:
            findings.append(
                _finding(
                    "agent_action_prerequisite_permission_environment_mismatch",
                    "permission_result represents environment_id "
                    f"{represented_environment!r}, which does not match "
                    f"assessment environment_id {environment_id!r}.",
                )
            )

    if environment_is_valid and authorization_is_valid:
        authorization_environments = sorted(
            {
                evidence.environment_id
                for evidence in authorization_result.normalized_evidence
                if evidence.environment_id != environment_id
            }
        )
        for represented_environment in authorization_environments:
            findings.append(
                _finding(
                    "agent_action_prerequisite_authorization_environment_mismatch",
                    "authorization_result represents environment_id "
                    f"{represented_environment!r}, which does not match "
                    f"assessment environment_id {environment_id!r}.",
                )
            )

    if findings:
        return _invalid(findings)

    responsibility_key = candidate_result.responsibility_key
    runtime_option_id = candidate_result.runtime_option_id
    operation_id = requirement_result.requirement.operation_id
    resource = requirement_result.requirement.resource

    capability_observation = next(
        observation
        for observation in capability_result.normalized_observations
        if observation.runtime_option_id == runtime_option_id
        and observation.operation_id == operation_id
    )
    permission_observation = next(
        (
            observation
            for observation in permission_result.normalized_observations
            if observation.runtime_option_id == runtime_option_id
            and observation.environment_id == environment_id
            and observation.operation_id == operation_id
            and observation.resource == resource
        ),
        None,
    )
    authorization_subject: _AuthorizationSubject = (
        responsibility_key[0],
        responsibility_key[1],
        responsibility_key[2],
        responsibility_key[3],
        candidate_result.actor_id,
        runtime_option_id,
        candidate_result.option_id,
        environment_id,
        operation_id,
        resource,
    )
    authorization_evidence = next(
        (
            evidence
            for evidence in authorization_result.normalized_evidence
            if _authorization_subject(evidence) == authorization_subject
        ),
        None,
    )

    reasons: list[AgentActionPrerequisiteReason] = []
    if (
        candidate_result.outcome
        is AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
    ):
        reasons.append(
            AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED
        )
    elif (
        candidate_result.outcome
        is AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
    ):
        reasons.append(
            AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED
        )

    if capability_observation.state is RuntimeOperationCapabilityState.ABSENT:
        reasons.append(
            AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT
        )
    elif (
        capability_observation.state
        is RuntimeOperationCapabilityState.UNKNOWN
    ):
        reasons.append(
            AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN
        )

    if permission_observation is None or (
        permission_observation.state
        is EnvironmentOperationPermissionState.UNKNOWN
    ):
        reasons.append(
            AgentActionPrerequisiteReason.
            ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN
        )
    elif (
        permission_observation.state
        is EnvironmentOperationPermissionState.DENIED
    ):
        reasons.append(
            AgentActionPrerequisiteReason.
            ENVIRONMENT_OPERATION_PERMISSION_DENIED
        )

    if authorization_evidence is None:
        reasons.append(
            AgentActionPrerequisiteReason.
            AGENT_EXECUTION_AUTHORIZATION_MISSING
        )
    elif (
        authorization_evidence.state
        is AgentExecutionAuthorizationState.DENIED
    ):
        reasons.append(
            AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_DENIED
        )

    blocking_reasons = {
        AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
        AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,
        AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_DENIED,
        AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_DENIED,
    }
    if blocking_reasons.intersection(reasons):
        outcome = AgentActionPrerequisiteOutcome.BLOCKED
    elif reasons:
        outcome = AgentActionPrerequisiteOutcome.UNRESOLVED
    else:
        outcome = AgentActionPrerequisiteOutcome.SATISFIED
        reasons.append(
            AgentActionPrerequisiteReason.
            ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED
        )

    return AgentActionPrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=responsibility_key,
        actor_id=candidate_result.actor_id,
        runtime_option_id=runtime_option_id,
        option_id=candidate_result.option_id,
        environment_id=environment_id,
        operation_id=operation_id,
        resource=resource,
        outcome=outcome,
        reasons=tuple(reasons),
    )
