from __future__ import annotations


EXECUTION_MODE_ORDER: tuple[str, ...] = (
    "lite",
    "standard",
    "deep",
    "critical",
)

_EXECUTION_MODE_RANK = {
    mode: rank for rank, mode in enumerate(EXECUTION_MODE_ORDER)
}


def execution_mode_satisfies(actual: str, required: str) -> bool:
    """Return whether ``actual`` satisfies the minimum ``required`` posture."""
    if actual not in _EXECUTION_MODE_RANK:
        raise ValueError(f"invalid actual execution mode: {actual!r}")
    if required not in _EXECUTION_MODE_RANK:
        raise ValueError(f"invalid required execution mode: {required!r}")
    return _EXECUTION_MODE_RANK[actual] >= _EXECUTION_MODE_RANK[required]
