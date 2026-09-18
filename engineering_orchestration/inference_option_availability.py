"""Pure validation and normalization of Inference Option availability.

Availability is ephemeral evidence about supplied Inference Options. It does
not change option identity, select or authorize an option, describe runtime
availability, invoke a model, contact a Provider, or persist state.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence

from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    validate_inference_option_inventory,
)


class InferenceOptionAvailabilityState(StrEnum):
    """Closed states for one Inference Option availability observation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InferenceOptionAvailabilityObservation:
    """One immutable, Provider-neutral availability observation."""

    option_id: str
    state: InferenceOptionAvailabilityState


@dataclass(frozen=True)
class InferenceOptionAvailabilityFinding:
    """Stable semantic finding from option-availability validation."""

    code: str
    message: str


@dataclass(frozen=True)
class InferenceOptionAvailabilityValidationResult:
    """Validation result and, when valid, normalized option observations."""

    valid: bool
    findings: tuple[InferenceOptionAvailabilityFinding, ...]
    normalized_observations: tuple[InferenceOptionAvailabilityObservation, ...]


def validate_inference_option_availability(
    observations: Sequence[InferenceOptionAvailabilityObservation],
    options: Sequence[InferenceOptionDefinition],
) -> InferenceOptionAvailabilityValidationResult:
    """Validate and normalize one caller-supplied availability snapshot.

    The foundational option inventory is validated first. Otherwise duplicate
    observations precede unknown-option findings, with affected IDs reported in
    exact case-sensitive order. Any finding invalidates the complete snapshot.
    A valid result contains one observation per option, sorted by option ID;
    absence normalizes to ``unknown``.
    """

    inventory_result = validate_inference_option_inventory(options)
    if not inventory_result.valid:
        return InferenceOptionAvailabilityValidationResult(
            valid=False,
            findings=tuple(
                InferenceOptionAvailabilityFinding(finding.code, finding.message)
                for finding in inventory_result.findings
            ),
            normalized_observations=(),
        )

    supplied_observations = tuple(observations)
    observation_counts = Counter(
        observation.option_id for observation in supplied_observations
    )
    known_option_ids = {
        option.option_id for option in inventory_result.normalized_options
    }

    findings: list[InferenceOptionAvailabilityFinding] = []
    for option_id in sorted(
        option_id for option_id, count in observation_counts.items() if count > 1
    ):
        findings.append(
            InferenceOptionAvailabilityFinding(
                code="duplicate_inference_option_availability",
                message=(
                    f"Inference Option '{option_id}' has more than one supplied "
                    "availability observation."
                ),
            )
        )

    for option_id in sorted(set(observation_counts) - known_option_ids):
        findings.append(
            InferenceOptionAvailabilityFinding(
                code="inference_option_not_found",
                message=(
                    f"Inference Option '{option_id}' was not found in the "
                    "supplied inventory."
                ),
            )
        )

    if findings:
        return InferenceOptionAvailabilityValidationResult(
            valid=False,
            findings=tuple(findings),
            normalized_observations=(),
        )

    observations_by_option = {
        observation.option_id: observation
        for observation in supplied_observations
    }
    normalized = tuple(
        observations_by_option.get(
            option.option_id,
            InferenceOptionAvailabilityObservation(
                option.option_id,
                InferenceOptionAvailabilityState.UNKNOWN,
            ),
        )
        for option in inventory_result.normalized_options
    )
    return InferenceOptionAvailabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=normalized,
    )
