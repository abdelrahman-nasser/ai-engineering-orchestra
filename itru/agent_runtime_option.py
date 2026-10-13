"""Pure validation of caller-supplied Agent Runtime Option definitions.

An Agent Runtime Option is only an opaque execution-surface identity. It does
not describe an Actor, Agent Definition, Inference Option, credentials,
capabilities, authorization, selection, or invocation, and this module
performs no discovery, I/O, or persistence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class AgentRuntimeOptionDefinition:
    """One immutable identity for a caller-supplied Agent execution surface."""

    runtime_option_id: str


@dataclass(frozen=True)
class AgentRuntimeOptionFinding:
    """Stable semantic finding from Runtime Option inventory validation."""

    code: str
    message: str


@dataclass(frozen=True)
class AgentRuntimeOptionInventoryValidationResult:
    """Validation result and, when valid, canonicalized supplied options."""

    valid: bool
    findings: tuple[AgentRuntimeOptionFinding, ...]
    normalized_options: tuple[AgentRuntimeOptionDefinition, ...]


def validate_agent_runtime_option_inventory(
    options: Sequence[AgentRuntimeOptionDefinition],
) -> AgentRuntimeOptionInventoryValidationResult:
    """Validate one caller-supplied Agent Runtime Option inventory.

    Inputs are expected to have passed the structural schema. Duplicate exact,
    case-sensitive ``runtime_option_id`` values invalidate the whole inventory.
    A valid result is sorted by Runtime Option ID for deterministic consumption;
    the ordering is canonicalization, never preference or selection.
    """

    supplied = tuple(options)
    option_counts = Counter(option.runtime_option_id for option in supplied)
    duplicate_ids = tuple(
        sorted(
            runtime_option_id
            for runtime_option_id, count in option_counts.items()
            if count > 1
        )
    )

    if duplicate_ids:
        return AgentRuntimeOptionInventoryValidationResult(
            valid=False,
            findings=(
                AgentRuntimeOptionFinding(
                    code="duplicate_agent_runtime_option_id",
                    message=(
                        "Agent Runtime Option IDs must be unique in the supplied "
                        "inventory; duplicates: " + ", ".join(duplicate_ids)
                    ),
                ),
            ),
            normalized_options=(),
        )

    return AgentRuntimeOptionInventoryValidationResult(
        valid=True,
        findings=(),
        normalized_options=tuple(
            sorted(supplied, key=lambda option: option.runtime_option_id)
        ),
    )
