"""Package-internal validation for lexical repository resources.

This module is the single implementation source for the repository-relative
resource grammar shared by Core contracts. Validation is lexical only and
performs no discovery, path resolution, filesystem access, or normalization.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


_DRIVE_QUALIFIED_PATTERN = re.compile(r"[A-Za-z]:", flags=re.ASCII)
_URI_SCHEME_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9+.-]*:",
    flags=re.ASCII,
)
_GLOB_META = frozenset("*?[]{}")
_RESOURCE_ISSUE_CODES = (
    "resource_empty",
    "resource_control_character",
    "resource_unc_path",
    "resource_absolute_path",
    "resource_drive_qualified_path",
    "resource_uri_scheme",
    "resource_leading_tilde",
    "resource_backslash",
    "resource_trailing_slash",
    "resource_empty_segment",
    "resource_dot_segment",
    "resource_parent_segment",
    "resource_glob_meta",
)
_RESOURCE_ISSUE_ORDER = {
    code: index for index, code in enumerate(_RESOURCE_ISSUE_CODES)
}


@dataclass(frozen=True)
class RepositoryResourceValidationIssue:
    """First canonical issue for one lexical repository resource."""

    code: str
    message_suffix: str


def _repository_resource_issue_sort_key(
    issue: RepositoryResourceValidationIssue,
    resource: str,
) -> tuple[int, str]:
    """Return canonical finding-category precedence, then exact resource."""

    return (_RESOURCE_ISSUE_ORDER[issue.code], resource)


def validate_repository_resource(
    resource: str,
) -> RepositoryResourceValidationIssue | None:
    """Return the first canonical issue without accessing the resource."""

    if not resource:
        return RepositoryResourceValidationIssue(
            "resource_empty",
            "must not be empty.",
        )
    if any(
        ord(character) <= 0x1F or 0x7F <= ord(character) <= 0x9F
        for character in resource
    ):
        return RepositoryResourceValidationIssue(
            "resource_control_character",
            "must not contain control characters.",
        )
    if resource.startswith(("//", "\\\\")):
        return RepositoryResourceValidationIssue(
            "resource_unc_path",
            "must not use a UNC path.",
        )
    if resource.startswith("/"):
        return RepositoryResourceValidationIssue(
            "resource_absolute_path",
            "must be repository-relative.",
        )
    if _DRIVE_QUALIFIED_PATTERN.match(resource) is not None:
        return RepositoryResourceValidationIssue(
            "resource_drive_qualified_path",
            "must not be drive-qualified.",
        )
    if _URI_SCHEME_PATTERN.match(resource) is not None:
        return RepositoryResourceValidationIssue(
            "resource_uri_scheme",
            "must not use a URI scheme.",
        )
    if resource.startswith("~"):
        return RepositoryResourceValidationIssue(
            "resource_leading_tilde",
            "must not start with a tilde.",
        )
    if "\\" in resource:
        return RepositoryResourceValidationIssue(
            "resource_backslash",
            "must use forward-slash separators.",
        )
    if resource.endswith("/"):
        return RepositoryResourceValidationIssue(
            "resource_trailing_slash",
            "must not end with a slash.",
        )

    segments = resource.split("/")
    if "" in segments:
        return RepositoryResourceValidationIssue(
            "resource_empty_segment",
            "must not contain an empty segment.",
        )
    if "." in segments:
        return RepositoryResourceValidationIssue(
            "resource_dot_segment",
            "must not contain a dot segment.",
        )
    if ".." in segments:
        return RepositoryResourceValidationIssue(
            "resource_parent_segment",
            "must not contain a parent segment.",
        )
    if any(character in _GLOB_META for character in resource):
        return RepositoryResourceValidationIssue(
            "resource_glob_meta",
            "must not contain glob meta characters.",
        )
    return None
