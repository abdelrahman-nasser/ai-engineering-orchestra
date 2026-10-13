"""Pure validation and normalization of supplied Actor availability observations.

Availability is ephemeral evidence about one Actor. It does not change Actor
identity or competency coverage, select or assign an Actor, grant authority or
permission, execute work, poll a Provider, or persist state.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Sequence, cast


class AvailabilityState(StrEnum):
    """Closed canonical states for one Actor availability observation."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ActorAvailabilityObservation:
    """One immutable, Provider-neutral availability observation."""

    actor_id: str
    state: AvailabilityState


@dataclass(frozen=True)
class ActorAvailabilityFinding:
    """Stable semantic finding from availability-context validation."""

    code: str
    message: str


@dataclass(frozen=True)
class ActorAvailabilityValidationResult:
    """Validation result and, when valid, normalized Actor observations."""

    valid: bool
    findings: tuple[ActorAvailabilityFinding, ...]
    normalized_observations: tuple[ActorAvailabilityObservation, ...]


def _duplicate_actor_ids(actor_ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        sorted(
            actor_id
            for actor_id, count in Counter(actor_ids).items()
            if count > 1
        )
    )


def validate_actor_availability(
    observations: Sequence[ActorAvailabilityObservation],
    actors: Sequence[Mapping[str, object]],
) -> ActorAvailabilityValidationResult:
    """Validate and normalize one caller-supplied availability context.

    Inputs are expected to have passed their structural schemas. Duplicate Actor
    IDs invalidate the foundational context before observations are inspected.
    Otherwise duplicate observations and references to unknown Actors are
    reported deterministically. A valid result contains exactly one observation
    per Actor, ordered by Actor ID; absence normalizes to ``unknown``.
    """

    actor_ids = tuple(cast(str, actor["id"]) for actor in actors)
    duplicate_actor_ids = _duplicate_actor_ids(actor_ids)
    if duplicate_actor_ids:
        return ActorAvailabilityValidationResult(
            valid=False,
            findings=(
                ActorAvailabilityFinding(
                    code="duplicate_actor_id",
                    message=(
                        "Actor IDs must be unique in the supplied context; "
                        "duplicates: " + ", ".join(duplicate_actor_ids)
                    ),
                ),
            ),
            normalized_observations=(),
        )

    actors_by_id = dict(zip(actor_ids, actors, strict=True))
    observation_counts = Counter(observation.actor_id for observation in observations)

    findings: list[ActorAvailabilityFinding] = []
    for actor_id in sorted(
        actor_id for actor_id, count in observation_counts.items() if count > 1
    ):
        findings.append(
            ActorAvailabilityFinding(
                code="duplicate_actor_availability",
                message=(
                    f"Actor '{actor_id}' has more than one supplied availability "
                    "observation."
                ),
            )
        )

    for actor_id in sorted(set(observation_counts) - set(actors_by_id)):
        findings.append(
            ActorAvailabilityFinding(
                code="actor_not_found",
                message=(
                    f"Actor '{actor_id}' was not found in the supplied Actor context."
                ),
            )
        )

    if findings:
        return ActorAvailabilityValidationResult(
            valid=False,
            findings=tuple(findings),
            normalized_observations=(),
        )

    observations_by_actor = {
        observation.actor_id: observation
        for observation in observations
    }
    normalized = tuple(
        observations_by_actor.get(
            actor_id,
            ActorAvailabilityObservation(actor_id, AvailabilityState.UNKNOWN),
        )
        for actor_id in sorted(actors_by_id)
    )
    return ActorAvailabilityValidationResult(
        valid=True,
        findings=(),
        normalized_observations=normalized,
    )
