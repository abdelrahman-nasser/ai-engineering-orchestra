"""Pure Actor-to-Role competency coverage over already-normalized data.

Coverage is compatibility evidence only. It does not perform selection,
assignment, availability, authority, permission, execution, independent-review,
or Quality Gate evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, cast


EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC = "role_required_capabilities_empty"


@dataclass(frozen=True)
class ActorRoleCoverage:
    """Minimal deterministic evidence from one Actor and one Role."""

    actor_id: str
    role_id: str
    compatible: bool
    missing_competencies: tuple[str, ...]
    diagnostic: str | None = None


def evaluate_actor_role_coverage(
    actor: Mapping[str, object],
    role: Mapping[str, object],
) -> ActorRoleCoverage:
    """Compare normalized Role requirements with declared Actor competencies.

    Structural validation belongs at the input boundary. This evaluator neither
    mutates nor enriches its inputs and deliberately ignores Actor kind and all
    runtime, Provider, availability, authority, and permission concerns.
    """

    actor_id = cast(str, actor["id"])
    role_id = cast(str, role["id"])
    actor_competencies = cast(list[str] | tuple[str, ...], actor["competencies"])
    required_capabilities = cast(
        list[str] | tuple[str, ...], role["required_capabilities"]
    )

    if not required_capabilities:
        return ActorRoleCoverage(
            actor_id=actor_id,
            role_id=role_id,
            compatible=False,
            missing_competencies=(),
            diagnostic=EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC,
        )

    missing = tuple(sorted(set(required_capabilities) - set(actor_competencies)))
    return ActorRoleCoverage(
        actor_id=actor_id,
        role_id=role_id,
        compatible=not missing,
        missing_competencies=missing,
    )
