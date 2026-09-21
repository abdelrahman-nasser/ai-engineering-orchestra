"""Pure validation for the canonical Operation Requirement value.

An Operation Requirement states only that one Core-defined abstract operation
is needed against one exact lexical repository-relative resource. It does not
establish capability, permission, authorization, or execution, and this module
performs no discovery, I/O, path resolution, or persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


_OPERATION_ID_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*",
    flags=re.ASCII,
)
_DRIVE_QUALIFIED_PATTERN = re.compile(r"[A-Za-z]:", flags=re.ASCII)
_URI_SCHEME_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9+.-]*:",
    flags=re.ASCII,
)
_SUPPORTED_OPERATION_IDS = frozenset({"repository_file_read"})
_GLOB_META = frozenset("*?[]{}")


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


def _resource_finding(resource: str) -> OperationRequirementFinding | None:
    if not resource:
        return _finding(
            "resource_empty",
            "Operation Requirement resource must not be empty.",
        )
    if any(
        ord(character) <= 0x1F or 0x7F <= ord(character) <= 0x9F
        for character in resource
    ):
        return _finding(
            "resource_control_character",
            "Operation Requirement resource must not contain control characters.",
        )
    if resource.startswith(("//", "\\\\")):
        return _finding(
            "resource_unc_path",
            "Operation Requirement resource must not use a UNC path.",
        )
    if resource.startswith("/"):
        return _finding(
            "resource_absolute_path",
            "Operation Requirement resource must be repository-relative.",
        )
    if _DRIVE_QUALIFIED_PATTERN.match(resource) is not None:
        return _finding(
            "resource_drive_qualified_path",
            "Operation Requirement resource must not be drive-qualified.",
        )
    if _URI_SCHEME_PATTERN.match(resource) is not None:
        return _finding(
            "resource_uri_scheme",
            "Operation Requirement resource must not use a URI scheme.",
        )
    if resource.startswith("~"):
        return _finding(
            "resource_leading_tilde",
            "Operation Requirement resource must not start with a tilde.",
        )
    if "\\" in resource:
        return _finding(
            "resource_backslash",
            "Operation Requirement resource must use forward-slash separators.",
        )
    if resource.endswith("/"):
        return _finding(
            "resource_trailing_slash",
            "Operation Requirement resource must not end with a slash.",
        )

    segments = resource.split("/")
    if "" in segments:
        return _finding(
            "resource_empty_segment",
            "Operation Requirement resource must not contain an empty segment.",
        )
    if "." in segments:
        return _finding(
            "resource_dot_segment",
            "Operation Requirement resource must not contain a dot segment.",
        )
    if ".." in segments:
        return _finding(
            "resource_parent_segment",
            "Operation Requirement resource must not contain a parent segment.",
        )
    if any(character in _GLOB_META for character in resource):
        return _finding(
            "resource_glob_meta",
            "Operation Requirement resource must not contain glob meta characters.",
        )
    return None


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

    if _OPERATION_ID_PATTERN.fullmatch(operation_id) is None:
        findings.append(
            _finding(
                "operation_id_invalid_syntax",
                "Operation Requirement operation_id must use ASCII lower_snake_case syntax.",
            )
        )
    elif operation_id not in _SUPPORTED_OPERATION_IDS:
        findings.append(
            _finding(
                "operation_id_not_supported",
                f"Operation ID '{operation_id}' is not supported by Core.",
            )
        )

    resource_finding = _resource_finding(resource)
    if resource_finding is not None:
        findings.append(resource_finding)

    if findings:
        return _invalid(findings)
    return OperationRequirementValidationResult(
        valid=True,
        findings=(),
        requirement=requirement,
    )
