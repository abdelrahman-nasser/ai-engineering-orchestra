"""Pure validation and normalization of Agent Runtime Option availability.

Availability is ephemeral evidence about supplied Agent Runtime Options. It
does not change runtime identity, establish Actor or Inference compatibility,
select or authorize an execution surface, invoke an Agent, contact a Provider,
or persist state.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)


class AgentRuntimeOptionAvailabilityState(StrEnum):
    """Closed states for one Agent Runtime Option availability observation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class AgentRuntimeOptionAvailabilityObservation:
    """One immutable availability observation for an Agent Runtime Option."""

    runtime_option_id: str
    state: AgentRuntimeOptionAvailabilityState


@dataclass(frozen=True)
class AgentRuntimeOptionAvailabilityFinding:
    """Stable semantic finding from Runtime Option availability validation."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentRuntimeOptionAvailabilityValidationResult:
    """Validation result and, when valid, normalized observations."""

    valid: bool
    findings: tuple[AgentRuntimeOptionAvailabilityFinding, ...]
    normalized_observations: tuple[
        AgentRuntimeOptionAvailabilityObservation, ...
    ]


def validate_agent_runtime_option_availability(
    observations: Sequence[AgentRuntimeOptionAvailabilityObservation],
    options: Sequence[AgentRuntimeOptionDefinition],
) -> AgentRuntimeOptionAvailabilityValidationResult:
    """Validate and normalize one caller-supplied availability snapshot.

    The foundational Runtime Option inventory is validated first. Otherwise
    duplicate observations precede unknown-option findings, with affected IDs
    reported in exact case-sensitive order. Any finding invalidates the whole
    snapshot. A valid result contains one observation per Runtime Option,
    sorted by Runtime Option ID; absence normalizes to ``unknown``.
    """

    inventory_result = validate_agent_runtime_option_inventory(options)
    if not inventory_result.valid:
        return AgentRuntimeOptionAvailabilityValidationResult(
            valid=False,
            findings=tuple(
                AgentRuntimeOptionAvailabilityFinding(
                    finding.code,
                    finding.message,
                )
                for finding in inventory_result.findings
            ),
            normalized_observations=(),
        )

    supplied_observations = tuple(observations)
    observation_counts = Counter(
        observation.runtime_option_id for observation in supplied_observations
    )
    known_runtime_option_ids = {
        option.runtime_option_id for option in inventory_result.normalized_options
    }

    findings: list[AgentRuntimeOptionAvailabilityFinding] = []
    for runtime_option_id in sorted(
        runtime_option_id
        for runtime_option_id, count in observation_counts.items()
        if count > 1
    ):
        findings.append(
            AgentRuntimeOptionAvailabilityFinding(
                code="duplicate_agent_runtime_option_availability",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' has more than "
                    "one supplied availability observation."
                ),
            )
        )

    for runtime_option_id in sorted(
        set(observation_counts) - known_runtime_option_ids
    ):
        findings.append(
            AgentRuntimeOptionAvailabilityFinding(
                code="agent_runtime_option_not_found",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' was not found "
                    "in the supplied inventory."
                ),
            )
        )

    if findings:
        return AgentRuntimeOptionAvailabilityValidationResult(
            valid=False,
            findings=tuple(findings),
            normalized_observations=(),
        )

    observations_by_option = {
        observation.runtime_option_id: observation
        for observation in supplied_observations
    }
    normalized = tuple(
        observations_by_option.get(
            option.runtime_option_id,
            AgentRuntimeOptionAvailabilityObservation(
                option.runtime_option_id,
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
            ),
        )
        for option in inventory_result.normalized_options
    )
    return AgentRuntimeOptionAvailabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=normalized,
    )
