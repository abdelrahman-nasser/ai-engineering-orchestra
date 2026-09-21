"""Package-internal Core operation vocabulary.

This module is the single implementation source for Core operation identifier
syntax and support. Public contracts own their contextual findings and remain
responsible for exact input types.
"""

from __future__ import annotations

import re


_OPERATION_ID_PATTERN = re.compile(
    r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*",
    flags=re.ASCII,
)
_SUPPORTED_OPERATION_IDS = ("repository_file_read",)
_SUPPORTED_OPERATION_ID_SET = frozenset(_SUPPORTED_OPERATION_IDS)


def validate_core_operation_id(operation_id: str) -> str | None:
    """Return the canonical semantic issue code for one exact operation ID."""

    if _OPERATION_ID_PATTERN.fullmatch(operation_id) is None:
        return "operation_id_invalid_syntax"
    if operation_id not in _SUPPORTED_OPERATION_ID_SET:
        return "operation_id_not_supported"
    return None


def supported_core_operation_ids() -> tuple[str, ...]:
    """Return Core-supported operation IDs in canonical exact order."""

    return _SUPPORTED_OPERATION_IDS
