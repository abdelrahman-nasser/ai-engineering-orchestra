"""Pure per-edge Runtime-to-Inference Pair Availability Assessment.

The assessment composes caller-supplied positive compatibility evidence with
normalized endpoint availability. It does not infer compatibility, select or
authorize a configuration, invoke an Agent, perform discovery or I/O, or
persist state.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
    validate_agent_runtime_option_availability,
)
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
    validate_inference_option_availability,
)
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
    validate_runtime_inference_compatibility,
)


class RuntimeInferencePairAvailabilityOutcome(StrEnum):
    """Closed outcomes for one supplied compatible endpoint pair."""

    ESTABLISHED = "established"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class RuntimeInferencePairAvailabilityAssessment:
    """Immutable endpoint states and computed outcome for one supplied edge."""

    runtime_option_id: str
    option_id: str
    runtime_availability_state: AgentRuntimeOptionAvailabilityState
    inference_availability_state: InferenceOptionAvailabilityState

    def __post_init__(self) -> None:
        """Reject cross-domain enums and raw strings at construction time."""

        self._validate_state_types()

    def _validate_state_types(self) -> None:
        if (
            type(self.runtime_availability_state)
            is not AgentRuntimeOptionAvailabilityState
        ):
            raise ValueError(
                "runtime_availability_state must be an "
                "AgentRuntimeOptionAvailabilityState value."
            )
        if (
            type(self.inference_availability_state)
            is not InferenceOptionAvailabilityState
        ):
            raise ValueError(
                "inference_availability_state must be an "
                "InferenceOptionAvailabilityState value."
            )

    @property
    def outcome(self) -> RuntimeInferencePairAvailabilityOutcome:
        """Compute the outcome from the two exact availability state types."""

        self._validate_state_types()

        if (
            self.runtime_availability_state
            is AgentRuntimeOptionAvailabilityState.UNAVAILABLE
            or self.inference_availability_state
            is InferenceOptionAvailabilityState.UNAVAILABLE
        ):
            return RuntimeInferencePairAvailabilityOutcome.BLOCKED
        if (
            self.runtime_availability_state
            is AgentRuntimeOptionAvailabilityState.AVAILABLE
            and self.inference_availability_state
            is InferenceOptionAvailabilityState.AVAILABLE
        ):
            return RuntimeInferencePairAvailabilityOutcome.ESTABLISHED
        return RuntimeInferencePairAvailabilityOutcome.UNRESOLVED


@dataclass(frozen=True)
class RuntimeInferencePairAvailabilityFinding:
    """Stable finding converted from an existing input-domain validator."""

    code: str
    message: str


@dataclass(frozen=True)
class RuntimeInferencePairAvailabilityResult:
    """Atomic validation result and deterministic per-edge assessments."""

    valid: bool
    findings: tuple[RuntimeInferencePairAvailabilityFinding, ...]
    assessments: tuple[RuntimeInferencePairAvailabilityAssessment, ...]


def assess_runtime_inference_pair_availability(
    evidence: Sequence[RuntimeInferenceCompatibilityEvidence],
    runtime_options: Sequence[AgentRuntimeOptionDefinition],
    inference_options: Sequence[InferenceOptionDefinition],
    runtime_availability_observations: Sequence[
        AgentRuntimeOptionAvailabilityObservation
    ],
    inference_availability_observations: Sequence[
        InferenceOptionAvailabilityObservation
    ],
) -> RuntimeInferencePairAvailabilityResult:
    """Validate all inputs and assess only supplied positive compatibility edges.

    Caller sequences are captured once. Compatibility validation runs first
    and short-circuits on failure. After valid compatibility, both availability
    validators run so their findings can be returned in Runtime-then-Inference
    order. Any finding makes the result atomic: no assessments are returned.
    """

    captured_evidence = tuple(evidence)
    captured_runtime_options = tuple(runtime_options)
    captured_inference_options = tuple(inference_options)
    captured_runtime_observations = tuple(runtime_availability_observations)
    captured_inference_observations = tuple(inference_availability_observations)

    compatibility_result = validate_runtime_inference_compatibility(
        captured_evidence,
        captured_runtime_options,
        captured_inference_options,
    )
    if not compatibility_result.valid:
        return RuntimeInferencePairAvailabilityResult(
            valid=False,
            findings=tuple(
                RuntimeInferencePairAvailabilityFinding(
                    finding.code,
                    finding.message,
                )
                for finding in compatibility_result.findings
            ),
            assessments=(),
        )

    runtime_availability_result = validate_agent_runtime_option_availability(
        captured_runtime_observations,
        captured_runtime_options,
    )
    inference_availability_result = validate_inference_option_availability(
        captured_inference_observations,
        captured_inference_options,
    )
    availability_findings = tuple(
        RuntimeInferencePairAvailabilityFinding(finding.code, finding.message)
        for finding in (
            *runtime_availability_result.findings,
            *inference_availability_result.findings,
        )
    )
    if availability_findings:
        return RuntimeInferencePairAvailabilityResult(
            valid=False,
            findings=availability_findings,
            assessments=(),
        )

    runtime_states = {
        observation.runtime_option_id: observation.state
        for observation in runtime_availability_result.normalized_observations
    }
    inference_states = {
        observation.option_id: observation.state
        for observation in inference_availability_result.normalized_observations
    }

    assessments: list[RuntimeInferencePairAvailabilityAssessment] = []
    for edge in compatibility_result.normalized_evidence:
        assessment = RuntimeInferencePairAvailabilityAssessment(
            runtime_option_id=edge.runtime_option_id,
            option_id=edge.option_id,
            runtime_availability_state=runtime_states[edge.runtime_option_id],
            inference_availability_state=inference_states[edge.option_id],
        )
        # Force exact state-type validation before publishing a valid result.
        _ = assessment.outcome
        assessments.append(assessment)

    return RuntimeInferencePairAvailabilityResult(
        valid=True,
        findings=(),
        assessments=tuple(assessments),
    )
