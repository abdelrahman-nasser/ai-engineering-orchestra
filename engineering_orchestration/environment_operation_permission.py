"""Pure validation of Environment Operation Permission Observation snapshots.

Permission observations are caller/environment-supplied evidence about the
currently known environment permission for one exact Runtime, environment,
Core operation, and lexical repository resource. They are not Permission
Decisions, Human or policy authorization, enforcement, or execution. This
module performs no discovery, I/O, permission mutation, or persistence.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from engineering_orchestration._operation_vocabulary import (
    validate_core_operation_id,
)
from engineering_orchestration._repository_resource import (
    RepositoryResourceValidationIssue,
    _repository_resource_issue_sort_key,
    validate_repository_resource,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)


class EnvironmentOperationPermissionState(StrEnum):
    """Closed states for one environment-permission observation."""

    ALLOWED = "allowed"
    DENIED = "denied"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EnvironmentOperationPermissionObservation:
    """One immutable Runtime/environment/operation/resource observation."""

    runtime_option_id: str
    environment_id: str
    operation_id: str
    resource: str
    state: EnvironmentOperationPermissionState


@dataclass(frozen=True)
class EnvironmentOperationPermissionFinding:
    """Stable semantic finding from permission snapshot validation."""

    code: str
    message: str


@dataclass(frozen=True)
class EnvironmentOperationPermissionValidationResult:
    """Atomic result with canonically ordered supplied observations."""

    valid: bool
    findings: tuple[EnvironmentOperationPermissionFinding, ...]
    normalized_observations: tuple[
        EnvironmentOperationPermissionObservation, ...
    ]


_PermissionIdentity = tuple[str, str, str, str]


def _finding(
    code: str,
    message: str,
) -> EnvironmentOperationPermissionFinding:
    return EnvironmentOperationPermissionFinding(code=code, message=message)


def _invalid(
    findings: Iterable[EnvironmentOperationPermissionFinding],
) -> EnvironmentOperationPermissionValidationResult:
    return EnvironmentOperationPermissionValidationResult(
        valid=False,
        findings=tuple(findings),
        normalized_observations=(),
    )


def _identity(
    observation: EnvironmentOperationPermissionObservation,
) -> _PermissionIdentity:
    return (
        observation.runtime_option_id,
        observation.environment_id,
        observation.operation_id,
        observation.resource,
    )


def _identity_message(identity: _PermissionIdentity) -> str:
    runtime_option_id, environment_id, operation_id, resource = identity
    return (
        "Environment Operation Permission Observation identity "
        f"(runtime_option_id={runtime_option_id!r}, "
        f"environment_id={environment_id!r}, "
        f"operation_id={operation_id!r}, resource={resource!r})"
    )


def validate_environment_operation_permission(
    observations: Iterable[EnvironmentOperationPermissionObservation],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
    environment_id: str,
) -> EnvironmentOperationPermissionValidationResult:
    """Validate one caller-supplied environment-permission snapshot.

    Runtime Options and observations are captured exactly once, in that order.
    Runtime inventory and snapshot environment validation are foundational.
    Repeated identities are classified as either identical duplicates or
    conflicts; neither category is resolved. Any finding atomically invalidates
    the snapshot. Valid output contains only supplied objects, ordered by exact
    four-part identity, with no Cartesian synthesis.
    """

    captured_runtime_options = tuple(runtime_options)
    captured_observations = tuple(observations)

    inventory_result = validate_agent_runtime_option_inventory(
        captured_runtime_options
    )
    if not inventory_result.valid:
        return _invalid(
            EnvironmentOperationPermissionFinding(
                finding.code,
                finding.message,
            )
            for finding in inventory_result.findings
        )

    if type(environment_id) is not str or not environment_id:
        return _invalid(
            (
                _finding(
                    "environment_operation_permission_environment_id_invalid",
                    "Environment Operation Permission snapshot environment_id "
                    "must be an exact nonempty string.",
                ),
            )
        )

    has_invalid_type = any(
        type(observation) is not EnvironmentOperationPermissionObservation
        for observation in captured_observations
    )
    has_invalid_fields = any(
        type(observation) is EnvironmentOperationPermissionObservation
        and (
            type(observation.runtime_option_id) is not str
            or not observation.runtime_option_id
            or type(observation.environment_id) is not str
            or not observation.environment_id
            or type(observation.operation_id) is not str
            or type(observation.resource) is not str
            or (
                type(observation.state)
                is not EnvironmentOperationPermissionState
            )
        )
        for observation in captured_observations
    )
    type_findings: list[EnvironmentOperationPermissionFinding] = []
    if has_invalid_type:
        type_findings.append(
            _finding(
                "environment_operation_permission_observation_invalid_type",
                "Each supplied Environment Operation Permission Observation "
                "must be an exact "
                "EnvironmentOperationPermissionObservation value.",
            )
        )
    if has_invalid_fields:
        type_findings.append(
            _finding(
                "environment_operation_permission_observation_invalid",
                "A supplied Environment Operation Permission Observation "
                "contains malformed fields or state.",
            )
        )
    if type_findings:
        return _invalid(type_findings)

    typed_observations = tuple(
        observation
        for observation in captured_observations
        if type(observation) is EnvironmentOperationPermissionObservation
    )
    observations_by_identity: dict[
        _PermissionIdentity,
        list[EnvironmentOperationPermissionObservation],
    ] = defaultdict(list)
    for observation in typed_observations:
        observations_by_identity[_identity(observation)].append(observation)

    duplicate_identities: list[_PermissionIdentity] = []
    conflicting_identities: list[_PermissionIdentity] = []
    for identity, matching_observations in observations_by_identity.items():
        if len(matching_observations) <= 1:
            continue
        states = {observation.state for observation in matching_observations}
        if len(states) == 1:
            duplicate_identities.append(identity)
        else:
            conflicting_identities.append(identity)

    findings: list[EnvironmentOperationPermissionFinding] = []
    for identity in sorted(duplicate_identities):
        findings.append(
            _finding(
                "duplicate_environment_operation_permission",
                _identity_message(identity)
                + " has more than one supplied observation with the same state.",
            )
        )
    for identity in sorted(conflicting_identities):
        findings.append(
            _finding(
                "conflicting_environment_operation_permission",
                _identity_message(identity) + " has conflicting supplied states.",
            )
        )

    known_runtime_option_ids = {
        option.runtime_option_id
        for option in inventory_result.normalized_options
    }
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
                f"Agent Runtime Option '{runtime_option_id}' was not found "
                "in the supplied inventory.",
            )
        )

    for observed_environment_id in sorted(
        {
            observation.environment_id
            for observation in typed_observations
            if observation.environment_id != environment_id
        }
    ):
        findings.append(
            _finding(
                "environment_operation_permission_environment_mismatch",
                "Environment Operation Permission Observation environment_id "
                f"{observed_environment_id!r} does not match snapshot "
                f"environment_id {environment_id!r}.",
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
                "Environment Operation Permission Observation operation_id "
                "must use ASCII lower_snake_case syntax.",
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

    resource_issues: list[
        tuple[str, RepositoryResourceValidationIssue]
    ] = []
    for resource in {
        observation.resource for observation in typed_observations
    }:
        resource_issue = validate_repository_resource(resource)
        if resource_issue is not None:
            resource_issues.append((resource, resource_issue))
    for resource, resource_issue in sorted(
        resource_issues,
        key=lambda item: _repository_resource_issue_sort_key(
            item[1], item[0]
        ),
    ):
        findings.append(
            _finding(
                resource_issue.code,
                "Environment Operation Permission Observation resource "
                f"{resource!r} {resource_issue.message_suffix}",
            )
        )

    if findings:
        return _invalid(findings)

    return EnvironmentOperationPermissionValidationResult(
        valid=True,
        findings=(),
        normalized_observations=tuple(sorted(typed_observations, key=_identity)),
    )
