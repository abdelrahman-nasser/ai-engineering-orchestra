"""Pure validation for the canonical Operation Requirement value.

An Operation Requirement states only that one Core-defined abstract operation
is needed against one exact lexical repository-relative resource. It does not
establish capability, permission, authorization, or execution, and this module
performs no discovery, I/O, path resolution, or persistence.
"""

from __future__ import annotations

from dataclasses import dataclass

from engineering_orchestration._operation_vocabulary import (
    validate_core_operation_id,
)
from engineering_orchestration._repository_resource import (
    validate_repository_resource,
)


@dataclass(frozen=True)
class OperationRequirement:
    """One immutable declaration of an abstract operation/resource need."""

    operation_id: str
    resource: str

    @property
    def identity(self) -> tuple[str, str]:
        """Return the exact case-sensitive operation/resource identity."""

        return (self.operation_id, self.resource)


@dataclass(frozen=True)
class OperationRequirementFinding:
    """Stable semantic finding from Operation Requirement validation."""

    code: str
    message: str


@dataclass(frozen=True)
class OperationRequirementValidationResult:
    """Atomic validation result for one supplied Operation Requirement."""

    valid: bool
    findings: tuple[OperationRequirementFinding, ...]
    requirement: OperationRequirement | None


def _finding(code: str, message: str) -> OperationRequirementFinding:
    return OperationRequirementFinding(code=code, message=message)


def _invalid(
    findings: list[OperationRequirementFinding],
) -> OperationRequirementValidationResult:
    return OperationRequirementValidationResult(
        valid=False,
        findings=tuple(findings),
        requirement=None,
    )


def validate_operation_requirement(
    requirement: object,
) -> OperationRequirementValidationResult:
    """Validate one exact declaration without normalizing or accessing it."""

    if type(requirement) is not OperationRequirement:
        return _invalid(
            [
                _finding(
                    "operation_requirement_invalid_type",
                    "Operation Requirement must be an exact OperationRequirement value.",
                )
            ]
        )

    operation_id = requirement.operation_id
    resource = requirement.resource
    findings: list[OperationRequirementFinding] = []

    if type(operation_id) is not str:
        findings.append(
            _finding(
                "operation_id_invalid_type",
                "Operation Requirement operation_id must be an exact string.",
            )
        )
    if type(resource) is not str:
        findings.append(
            _finding(
                "resource_invalid_type",
                "Operation Requirement resource must be an exact string.",
            )
        )
    if findings:
        return _invalid(findings)

    operation_issue = validate_core_operation_id(operation_id)
    if operation_issue == "operation_id_invalid_syntax":
        findings.append(
            _finding(
                "operation_id_invalid_syntax",
                "Operation Requirement operation_id must use ASCII lower_snake_case syntax.",
            )
        )
    elif operation_issue == "operation_id_not_supported":
        findings.append(
            _finding(
                "operation_id_not_supported",
                f"Operation ID '{operation_id}' is not supported by Core.",
            )
        )

    resource_issue = validate_repository_resource(resource)
    if resource_issue is not None:
        findings.append(
            _finding(
                resource_issue.code,
                "Operation Requirement resource "
                f"{resource_issue.message_suffix}",
            )
        )

    if findings:
        return _invalid(findings)
    return OperationRequirementValidationResult(
        valid=True,
        findings=(),
        requirement=requirement,
    )
