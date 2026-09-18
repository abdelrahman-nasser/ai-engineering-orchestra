"""Pure validation of caller-supplied Inference Option definitions.

An Inference Option is only an opaque operational inference identity. It does
not describe a runtime, credentials, capabilities, authorization, selection,
or invocation, and this module performs no discovery, I/O, or persistence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class InferenceOptionDefinition:
    """One immutable, Provider-neutral inference-access identity."""

    option_id: str
    provider_id: str
    model_id: str


@dataclass(frozen=True)
class InferenceOptionFinding:
    """Stable semantic finding from Inference Option inventory validation."""

    code: str
    message: str


@dataclass(frozen=True)
class InferenceOptionInventoryValidationResult:
    """Validation result and, when valid, canonicalized supplied options."""

    valid: bool
    findings: tuple[InferenceOptionFinding, ...]
    normalized_options: tuple[InferenceOptionDefinition, ...]


def validate_inference_option_inventory(
    options: Sequence[InferenceOptionDefinition],
) -> InferenceOptionInventoryValidationResult:
    """Validate one caller-supplied Inference Option inventory.

    Inputs are expected to have passed the structural schema. ``option_id`` is
    the sole inventory identity: duplicate IDs invalidate the whole inventory,
    while repeated ``provider_id``/``model_id`` pairs are valid. A valid result
    is sorted by exact case-sensitive option ID for deterministic consumption;
    the ordering is canonicalization, never preference or selection.
    """

    supplied = tuple(options)
    option_counts = Counter(option.option_id for option in supplied)
    duplicate_ids = tuple(
        sorted(
            option_id
            for option_id, count in option_counts.items()
            if count > 1
        )
    )

    if duplicate_ids:
        return InferenceOptionInventoryValidationResult(
            valid=False,
            findings=(
                InferenceOptionFinding(
                    code="duplicate_inference_option_id",
                    message=(
                        "Inference Option IDs must be unique in the supplied "
                        "inventory; duplicates: " + ", ".join(duplicate_ids)
                    ),
                ),
            ),
            normalized_options=(),
        )

    return InferenceOptionInventoryValidationResult(
        valid=True,
        findings=(),
        normalized_options=tuple(
            sorted(supplied, key=lambda option: option.option_id)
        ),
    )
