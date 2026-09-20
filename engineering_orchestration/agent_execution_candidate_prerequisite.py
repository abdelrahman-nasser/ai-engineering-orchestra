"""Pure prerequisite assessment for one explicit Agent execution candidate.

The assessment composes existing responsibility, availability, applicability,
and pair-availability contracts in one caller-owned evaluation context. It does
not discover or select candidates, grant authority, construct an Execution
Contract, invoke an Agent, perform I/O, or persist state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable, Mapping, cast

from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
    validate_actor_availability,
)
from engineering_orchestration.actor_runtime_applicability import (
    ActorRuntimeApplicabilityEvidence,
    validate_actor_runtime_applicability,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
)
from engineering_orchestration.assignment import Assignment, validate_assignment
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
)
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
)
from engineering_orchestration.runtime_inference_pair_availability import (
    assess_runtime_inference_pair_availability,
)
from engineering_orchestration.workflow_catalog import WorkflowCatalog


class AgentExecutionCandidatePrerequisiteOutcome(StrEnum):
    """Closed ordinary outcomes for one valid Agent candidate assessment."""

    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class AgentExecutionCandidatePrerequisiteReason(StrEnum):
    """Stable reasons for a valid candidate's ordinary outcome."""

    ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED = (
        "all_currently_modeled_prerequisites_satisfied"
    )
    ACTOR_UNAVAILABLE = "actor_unavailable"
    ACTOR_AVAILABILITY_UNKNOWN = "actor_availability_unknown"
    ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED = (
        "actor_runtime_applicability_not_supplied"
    )
    RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED = (
        "runtime_inference_compatibility_not_supplied"
    )
    AGENT_RUNTIME_OPTION_UNAVAILABLE = "agent_runtime_option_unavailable"
    AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN = (
        "agent_runtime_option_availability_unknown"
    )
    INFERENCE_OPTION_UNAVAILABLE = "inference_option_unavailable"
    INFERENCE_OPTION_AVAILABILITY_UNKNOWN = (
        "inference_option_availability_unknown"
    )


@dataclass(frozen=True)
class AgentExecutionCandidatePrerequisiteFinding:
    """Stable invalid-input or Agent-assessment-boundary finding."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionCandidatePrerequisiteResult:
    """Atomic validation result or one immutable candidate assessment."""

    valid: bool
    findings: tuple[AgentExecutionCandidatePrerequisiteFinding, ...]
    responsibility_key: tuple[str, str, str, str] | None
    actor_id: str | None
    runtime_option_id: str | None
    option_id: str | None
    outcome: AgentExecutionCandidatePrerequisiteOutcome | None
    reasons: tuple[AgentExecutionCandidatePrerequisiteReason, ...]


def _invalid(
    findings: Iterable[object],
) -> AgentExecutionCandidatePrerequisiteResult:
    """Convert parent findings into one atomic top-level invalid result."""

    return AgentExecutionCandidatePrerequisiteResult(
        valid=False,
        findings=tuple(
            AgentExecutionCandidatePrerequisiteFinding(
                code=cast(str, getattr(finding, "code")),
                message=cast(str, getattr(finding, "message")),
            )
            for finding in findings
        ),
        responsibility_key=None,
        actor_id=None,
        runtime_option_id=None,
        option_id=None,
        outcome=None,
        reasons=(),
    )


def assess_agent_execution_candidate_prerequisites(
    assignment: Assignment,
    runtime_option_id: str,
    option_id: str,
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Iterable[Mapping[str, object]],
    actor_availability_observations: Iterable[ActorAvailabilityObservation],
    actor_runtime_applicability_evidence: Iterable[
        ActorRuntimeApplicabilityEvidence
    ],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
    inference_options: Iterable[InferenceOptionDefinition],
    runtime_inference_compatibility_evidence: Iterable[
        RuntimeInferenceCompatibilityEvidence
    ],
    runtime_availability_observations: Iterable[
        AgentRuntimeOptionAvailabilityObservation
    ],
    inference_availability_observations: Iterable[
        InferenceOptionAvailabilityObservation
    ],
) -> AgentExecutionCandidatePrerequisiteResult:
    """Assess one explicit external-inference Agent candidate.

    Every caller-supplied iterable is captured exactly once, in public
    parameter order. Existing validators receive those same captured contexts.
    Invalid parent input short-circuits atomically; ordinary outcomes are
    derived only after every parent input and both explicit endpoints validate.
    """

    captured_actors = tuple(actors)
    captured_actor_observations = tuple(actor_availability_observations)
    captured_applicability = tuple(actor_runtime_applicability_evidence)
    captured_runtime_options = tuple(runtime_options)
    captured_inference_options = tuple(inference_options)
    captured_compatibility = tuple(runtime_inference_compatibility_evidence)
    captured_runtime_observations = tuple(runtime_availability_observations)
    captured_inference_observations = tuple(inference_availability_observations)

    assignment_result = validate_assignment(
        assignment,
        task,
        workflow_catalog,
        role_catalog,
        captured_actors,
    )
    if not assignment_result.valid:
        return _invalid(assignment_result.findings)

    assigned_actor = next(
        actor
        for actor in captured_actors
        if actor["id"] == assignment.actor_id
    )
    if assigned_actor["kind"] == "human":
        return _invalid(
            (
                AgentExecutionCandidatePrerequisiteFinding(
                    code=(
                        "agent_execution_candidate_not_applicable_to_human_actor"
                    ),
                    message=(
                        f"Actor '{assignment.actor_id}' has kind 'human'; Agent "
                        "Execution Candidate Prerequisite Assessment does not "
                        "apply to Human Assignments."
                    ),
                ),
            )
        )

    actor_availability_result = validate_actor_availability(
        captured_actor_observations,
        captured_actors,
    )
    if not actor_availability_result.valid:
        return _invalid(actor_availability_result.findings)

    applicability_result = validate_actor_runtime_applicability(
        captured_applicability,
        captured_actors,
        captured_runtime_options,
    )
    if not applicability_result.valid:
        return _invalid(applicability_result.findings)

    pair_result = assess_runtime_inference_pair_availability(
        captured_compatibility,
        captured_runtime_options,
        captured_inference_options,
        captured_runtime_observations,
        captured_inference_observations,
    )
    if not pair_result.valid:
        return _invalid(pair_result.findings)

    known_runtime_option_ids = {
        item.runtime_option_id for item in captured_runtime_options
    }
    known_option_ids = {item.option_id for item in captured_inference_options}
    endpoint_findings: list[AgentExecutionCandidatePrerequisiteFinding] = []
    if runtime_option_id not in known_runtime_option_ids:
        endpoint_findings.append(
            AgentExecutionCandidatePrerequisiteFinding(
                code="agent_runtime_option_not_found",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' was not found "
                    "in the supplied inventory."
                ),
            )
        )
    if option_id not in known_option_ids:
        endpoint_findings.append(
            AgentExecutionCandidatePrerequisiteFinding(
                code="inference_option_not_found",
                message=(
                    f"Inference Option '{option_id}' was not found in the "
                    "supplied inventory."
                ),
            )
        )
    if endpoint_findings:
        return _invalid(endpoint_findings)

    actor_state = next(
        observation.state
        for observation in actor_availability_result.normalized_observations
        if observation.actor_id == assignment.actor_id
    )
    applicability_supplied = any(
        item.actor_id == assignment.actor_id
        and item.runtime_option_id == runtime_option_id
        for item in applicability_result.normalized_evidence
    )
    pair_assessment = next(
        (
            item
            for item in pair_result.assessments
            if item.runtime_option_id == runtime_option_id
            and item.option_id == option_id
        ),
        None,
    )

    reasons: list[AgentExecutionCandidatePrerequisiteReason] = []
    if actor_state is AvailabilityState.UNAVAILABLE:
        reasons.append(AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE)
    elif actor_state is AvailabilityState.UNKNOWN:
        reasons.append(
            AgentExecutionCandidatePrerequisiteReason.ACTOR_AVAILABILITY_UNKNOWN
        )

    if not applicability_supplied:
        reasons.append(
            AgentExecutionCandidatePrerequisiteReason.
            ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED
        )

    if pair_assessment is None:
        reasons.append(
            AgentExecutionCandidatePrerequisiteReason.
            RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED
        )
    else:
        if (
            pair_assessment.runtime_availability_state
            is AgentRuntimeOptionAvailabilityState.UNAVAILABLE
        ):
            reasons.append(
                AgentExecutionCandidatePrerequisiteReason.
                AGENT_RUNTIME_OPTION_UNAVAILABLE
            )
        elif (
            pair_assessment.runtime_availability_state
            is AgentRuntimeOptionAvailabilityState.UNKNOWN
        ):
            reasons.append(
                AgentExecutionCandidatePrerequisiteReason.
                AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN
            )

        if (
            pair_assessment.inference_availability_state
            is InferenceOptionAvailabilityState.UNAVAILABLE
        ):
            reasons.append(
                AgentExecutionCandidatePrerequisiteReason.
                INFERENCE_OPTION_UNAVAILABLE
            )
        elif (
            pair_assessment.inference_availability_state
            is InferenceOptionAvailabilityState.UNKNOWN
        ):
            reasons.append(
                AgentExecutionCandidatePrerequisiteReason.
                INFERENCE_OPTION_AVAILABILITY_UNKNOWN
            )

    unavailable_reasons = {
        AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.AGENT_RUNTIME_OPTION_UNAVAILABLE,
        AgentExecutionCandidatePrerequisiteReason.INFERENCE_OPTION_UNAVAILABLE,
    }
    if unavailable_reasons.intersection(reasons):
        outcome = AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
    elif reasons:
        outcome = AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
    else:
        outcome = AgentExecutionCandidatePrerequisiteOutcome.SATISFIED
        reasons.append(
            AgentExecutionCandidatePrerequisiteReason.
            ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED
        )

    return AgentExecutionCandidatePrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=assignment.key,
        actor_id=assignment.actor_id,
        runtime_option_id=runtime_option_id,
        option_id=option_id,
        outcome=outcome,
        reasons=tuple(reasons),
    )
