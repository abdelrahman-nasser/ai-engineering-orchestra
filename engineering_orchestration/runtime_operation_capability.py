"""Pure validation and normalization of Runtime operation capability.

Capability observations are caller/environment-supplied facts about whether a
known Agent Runtime Option can technically provide one Core-defined abstract
operation in principle. They are not requirements, availability, permissions,
authorization, tool bindings, execution contracts, or invocations. This module
performs no discovery, I/O, polling, or persistence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from engineering_orchestration._operation_vocabulary import (
    supported_core_operation_ids,
    validate_core_operation_id,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)


class RuntimeOperationCapabilityState(StrEnum):
    """Closed states for one Runtime operation capability observation."""

    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RuntimeOperationCapabilityObservation:
    """One immutable Runtime/operation technical-support observation."""

    runtime_option_id: str
    operation_id: str
    state: RuntimeOperationCapabilityState


@dataclass(frozen=True)
class RuntimeOperationCapabilityFinding:
    """Stable semantic finding from capability snapshot validation."""

    code: str
    message: str


@dataclass(frozen=True)
class RuntimeOperationCapabilityValidationResult:
    """Atomic validation result with normalized observations when valid."""

    valid: bool
    findings: tuple[RuntimeOperationCapabilityFinding, ...]
    normalized_observations: tuple[RuntimeOperationCapabilityObservation, ...]


def _finding(code: str, message: str) -> RuntimeOperationCapabilityFinding:
    return RuntimeOperationCapabilityFinding(code=code, message=message)


def _invalid(
    findings: Iterable[RuntimeOperationCapabilityFinding],
) -> RuntimeOperationCapabilityValidationResult:
    return RuntimeOperationCapabilityValidationResult(
        valid=False,
        findings=tuple(findings),
        normalized_observations=(),
    )


def validate_runtime_operation_capability(
    observations: Iterable[RuntimeOperationCapabilityObservation],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
) -> RuntimeOperationCapabilityValidationResult:
    """Validate and normalize one caller-supplied capability snapshot.

    Both input iterables are captured once. Runtime inventory validation is
    foundational. With valid typed observations, duplicate pairs precede
    unknown Runtime references, malformed operations, and unsupported
    operations. Any finding invalidates the complete snapshot. Missing known
    Runtime/Core-operation pairs normalize to ``unknown``.
    """

    captured_runtime_options = tuple(runtime_options)
    captured_observations = tuple(observations)

    inventory_result = validate_agent_runtime_option_inventory(
        captured_runtime_options
    )
    if not inventory_result.valid:
        return _invalid(
            RuntimeOperationCapabilityFinding(finding.code, finding.message)
            for finding in inventory_result.findings
        )

    has_invalid_type = any(
        type(observation) is not RuntimeOperationCapabilityObservation
        for observation in captured_observations
    )
    has_invalid_fields = any(
        type(observation) is RuntimeOperationCapabilityObservation
        and (
            type(observation.runtime_option_id) is not str
            or not observation.runtime_option_id
            or type(observation.operation_id) is not str
            or type(observation.state) is not RuntimeOperationCapabilityState
        )
        for observation in captured_observations
    )
    type_findings: list[RuntimeOperationCapabilityFinding] = []
    if has_invalid_type:
        type_findings.append(
            _finding(
                "runtime_operation_capability_observation_invalid_type",
                "Each supplied Runtime Operation Capability Observation must "
                "be an exact RuntimeOperationCapabilityObservation value.",
            )
        )
    if has_invalid_fields:
        type_findings.append(
            _finding(
                "runtime_operation_capability_observation_invalid",
                "A supplied Runtime Operation Capability Observation contains "
                "malformed fields or state.",
            )
        )
    if type_findings:
        return _invalid(type_findings)

    typed_observations = tuple(
        observation
        for observation in captured_observations
        if type(observation) is RuntimeOperationCapabilityObservation
    )
    pair_counts = Counter(
        (observation.runtime_option_id, observation.operation_id)
        for observation in typed_observations
    )
    known_runtime_option_ids = {
        option.runtime_option_id
        for option in inventory_result.normalized_options
    }

    findings: list[RuntimeOperationCapabilityFinding] = []
    for runtime_option_id, operation_id in sorted(
        pair for pair, count in pair_counts.items() if count > 1
    ):
        findings.append(
            _finding(
                "duplicate_runtime_operation_capability",
                (
                    f"Agent Runtime Option '{runtime_option_id}' and Operation "
                    f"ID '{operation_id}' have more than one supplied Runtime "
                    "Operation Capability Observation."
                ),
            )
        )

    for runtime_option_id in sorted(
        {
            observation.runtime_option_id
            for observation in typed_observations
        }
        - known_runtime_option_ids
    ):
        findings.append(
            _finding(
                "agent_runtime_option_not_found",
                (
                    f"Agent Runtime Option '{runtime_option_id}' was not found "
                    "in the supplied inventory."
                ),
            )
        )

    operation_issues = {
        operation_id: validate_core_operation_id(operation_id)
        for operation_id in {
            observation.operation_id for observation in typed_observations
        }
    }
    for operation_id in sorted(
        operation_id
        for operation_id, issue in operation_issues.items()
        if issue == "operation_id_invalid_syntax"
    ):
        findings.append(
            _finding(
                "operation_id_invalid_syntax",
                "Runtime Operation Capability Observation operation_id must "
                "use ASCII lower_snake_case syntax.",
            )
        )

    for operation_id in sorted(
        operation_id
        for operation_id, issue in operation_issues.items()
        if issue == "operation_id_not_supported"
    ):
        findings.append(
            _finding(
                "operation_id_not_supported",
                f"Operation ID '{operation_id}' is not supported by Core.",
            )
        )

    if findings:
        return _invalid(findings)

    supplied_by_pair = {
        (observation.runtime_option_id, observation.operation_id): observation
        for observation in typed_observations
    }
    normalized = tuple(
        supplied_by_pair.get(
            (option.runtime_option_id, operation_id),
            RuntimeOperationCapabilityObservation(
                runtime_option_id=option.runtime_option_id,
                operation_id=operation_id,
                state=RuntimeOperationCapabilityState.UNKNOWN,
            ),
        )
        for option in inventory_result.normalized_options
        for operation_id in supported_core_operation_ids()
    )
    return RuntimeOperationCapabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=normalized,
    )
