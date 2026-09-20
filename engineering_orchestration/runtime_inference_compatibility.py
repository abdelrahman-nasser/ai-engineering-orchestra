"""Pure validation of Runtime-to-Inference Compatibility Evidence.

Compatibility is caller-supplied positive evidence connecting an Agent Runtime
Option to an externally selectable Inference Option. It is not availability,
configuration viability, selection, authorization, or invocation, and this
module performs no discovery, I/O, or persistence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)
from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    validate_inference_option_inventory,
)


@dataclass(frozen=True)
class RuntimeInferenceCompatibilityEvidence:
    """One immutable positive compatibility edge between supplied endpoints."""

    runtime_option_id: str
    option_id: str


@dataclass(frozen=True)
class RuntimeInferenceCompatibilityFinding:
    """Stable semantic finding from compatibility-relation validation."""

    code: str
    message: str


@dataclass(frozen=True)
class RuntimeInferenceCompatibilityValidationResult:
    """Validation result and, when valid, canonicalized supplied evidence."""

    valid: bool
    findings: tuple[RuntimeInferenceCompatibilityFinding, ...]
    normalized_evidence: tuple[RuntimeInferenceCompatibilityEvidence, ...]


def validate_runtime_inference_compatibility(
    evidence: Sequence[RuntimeInferenceCompatibilityEvidence],
    runtime_options: Sequence[AgentRuntimeOptionDefinition],
    inference_options: Sequence[InferenceOptionDefinition],
) -> RuntimeInferenceCompatibilityValidationResult:
    """Validate one caller-supplied positive compatibility relation.

    Both endpoint inventories are validated before the evidence is inspected.
    Invalid inventories preserve their existing findings in Runtime-then-
    Inference order. Otherwise duplicate edges precede unknown Runtime and then
    unknown Inference findings, with exact case-sensitive sorting inside each
    category. Any finding invalidates the complete relation. Valid evidence is
    sorted by ``(runtime_option_id, option_id)`` for canonicalization only.
    """

    runtime_inventory = validate_agent_runtime_option_inventory(runtime_options)
    inference_inventory = validate_inference_option_inventory(inference_options)

    inventory_findings = tuple(
        RuntimeInferenceCompatibilityFinding(finding.code, finding.message)
        for finding in (*runtime_inventory.findings, *inference_inventory.findings)
    )
    if inventory_findings:
        return RuntimeInferenceCompatibilityValidationResult(
            valid=False,
            findings=inventory_findings,
            normalized_evidence=(),
        )

    supplied_evidence = tuple(evidence)
    edge_counts = Counter(
        (item.runtime_option_id, item.option_id) for item in supplied_evidence
    )
    known_runtime_option_ids = {
        option.runtime_option_id for option in runtime_inventory.normalized_options
    }
    known_option_ids = {
        option.option_id for option in inference_inventory.normalized_options
    }

    findings: list[RuntimeInferenceCompatibilityFinding] = []
    for runtime_option_id, option_id in sorted(
        edge for edge, count in edge_counts.items() if count > 1
    ):
        findings.append(
            RuntimeInferenceCompatibilityFinding(
                code="duplicate_runtime_inference_compatibility",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' and Inference "
                    f"Option '{option_id}' have more than one supplied "
                    "compatibility evidence value."
                ),
            )
        )

    for runtime_option_id in sorted(
        {item.runtime_option_id for item in supplied_evidence}
        - known_runtime_option_ids
    ):
        findings.append(
            RuntimeInferenceCompatibilityFinding(
                code="agent_runtime_option_not_found",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' was not found "
                    "in the supplied inventory."
                ),
            )
        )

    for option_id in sorted(
        {item.option_id for item in supplied_evidence} - known_option_ids
    ):
        findings.append(
            RuntimeInferenceCompatibilityFinding(
                code="inference_option_not_found",
                message=(
                    f"Inference Option '{option_id}' was not found in the "
                    "supplied inventory."
                ),
            )
        )

    if findings:
        return RuntimeInferenceCompatibilityValidationResult(
            valid=False,
            findings=tuple(findings),
            normalized_evidence=(),
        )

    return RuntimeInferenceCompatibilityValidationResult(
        valid=True,
        findings=(),
        normalized_evidence=tuple(
            sorted(
                supplied_evidence,
                key=lambda item: (item.runtime_option_id, item.option_id),
            )
        ),
    )
