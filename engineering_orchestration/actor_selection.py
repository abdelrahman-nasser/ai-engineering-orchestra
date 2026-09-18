"""Pure deterministic Actor Selection over caller-supplied runtime evidence.

Selection resolves hard competency and availability constraints for one valid
Task/Workflow/Stage/Role responsibility.  It does not rank, assign, authorize,
reserve, execute, persist, or evaluate Quality Gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping, Sequence, cast

from engineering_orchestration._responsibility import (
    _resolve_task_responsibility,
)
from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
    validate_actor_availability,
)
from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.workflow_catalog import WorkflowCatalog


class ActorSelectionOutcome(StrEnum):
    """Closed outcomes for a valid Actor Selection evaluation."""

    SELECTED = "selected"
    AMBIGUOUS = "ambiguous"
    INDETERMINATE = "indeterminate"
    NO_CANDIDATE = "no_candidate"


class ActorSelectionReason(StrEnum):
    """Closed reasons explaining valid Actor Selection outcomes."""

    UNIQUE_AVAILABLE_ACTOR = "unique_available_actor"
    MULTIPLE_AVAILABLE_ACTORS = "multiple_available_actors"
    AVAILABILITY_UNKNOWN = "availability_unknown"
    CANDIDATE_SET_EMPTY = "candidate_set_empty"
    NO_ELIGIBLE_ACTOR = "no_eligible_actor"
    ALL_ELIGIBLE_UNAVAILABLE = "all_eligible_unavailable"


@dataclass(frozen=True)
class ActorSelectionFinding:
    """Stable invalid-context evidence from Actor Selection."""

    code: str
    message: str


@dataclass(frozen=True)
class ActorSelectionResult:
    """Immutable decision evidence for one responsibility."""

    valid: bool
    responsibility_key: tuple[str, str, str, str] | None
    outcome: ActorSelectionOutcome | None
    reason: ActorSelectionReason | None
    selected_actor_id: str | None
    eligible_actor_ids: tuple[str, ...]
    available_actor_ids: tuple[str, ...]
    unknown_actor_ids: tuple[str, ...]
    findings: tuple[ActorSelectionFinding, ...]


def _invalid(
    findings: tuple[ActorSelectionFinding, ...],
) -> ActorSelectionResult:
    return ActorSelectionResult(
        valid=False,
        responsibility_key=None,
        outcome=None,
        reason=None,
        selected_actor_id=None,
        eligible_actor_ids=(),
        available_actor_ids=(),
        unknown_actor_ids=(),
        findings=findings,
    )


def select_actor(
    task: Mapping[str, object],
    stage_id: str,
    role_id: str,
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Sequence[Mapping[str, object]],
    availability_observations: Sequence[ActorAvailabilityObservation],
) -> ActorSelectionResult:
    """Resolve hard Actor constraints for exactly one responsibility.

    Inputs are expected to be structurally valid normalized values.  Ordinary
    caller-context problems return an atomic invalid result.  Corrupt framework
    catalogs retain their existing infrastructure exception semantics.
    """

    availability = validate_actor_availability(
        availability_observations,
        actors,
    )
    if not availability.valid:
        return _invalid(tuple(
            ActorSelectionFinding(finding.code, finding.message)
            for finding in availability.findings
        ))

    responsibility_key, role, resolution_failure = _resolve_task_responsibility(
        task,
        stage_id,
        role_id,
        workflow_catalog,
        role_catalog,
        catalog_consumer="Actor Selection",
    )
    if resolution_failure is not None:
        return _invalid((ActorSelectionFinding(*resolution_failure),))

    assert responsibility_key is not None
    assert role is not None

    eligible_actor_ids = tuple(sorted(
        cast(str, actor["id"])
        for actor in actors
        if evaluate_actor_role_coverage(actor, role).compatible
    ))
    availability_by_actor_id = {
        observation.actor_id: observation.state
        for observation in availability.normalized_observations
    }
    available_actor_ids = tuple(
        actor_id for actor_id in eligible_actor_ids
        if availability_by_actor_id[actor_id] == AvailabilityState.AVAILABLE
    )
    unknown_actor_ids = tuple(
        actor_id for actor_id in eligible_actor_ids
        if availability_by_actor_id[actor_id] == AvailabilityState.UNKNOWN
    )

    selected_actor_id: str | None = None
    if not actors:
        outcome = ActorSelectionOutcome.NO_CANDIDATE
        reason = ActorSelectionReason.CANDIDATE_SET_EMPTY
    elif not eligible_actor_ids:
        outcome = ActorSelectionOutcome.NO_CANDIDATE
        reason = ActorSelectionReason.NO_ELIGIBLE_ACTOR
    elif len(available_actor_ids) >= 2:
        outcome = ActorSelectionOutcome.AMBIGUOUS
        reason = ActorSelectionReason.MULTIPLE_AVAILABLE_ACTORS
    elif unknown_actor_ids:
        outcome = ActorSelectionOutcome.INDETERMINATE
        reason = ActorSelectionReason.AVAILABILITY_UNKNOWN
    elif len(available_actor_ids) == 1:
        outcome = ActorSelectionOutcome.SELECTED
        reason = ActorSelectionReason.UNIQUE_AVAILABLE_ACTOR
        selected_actor_id = available_actor_ids[0]
    else:
        outcome = ActorSelectionOutcome.NO_CANDIDATE
        reason = ActorSelectionReason.ALL_ELIGIBLE_UNAVAILABLE

    return ActorSelectionResult(
        valid=True,
        responsibility_key=responsibility_key,
        outcome=outcome,
        reason=reason,
        selected_actor_id=selected_actor_id,
        eligible_actor_ids=eligible_actor_ids,
        available_actor_ids=available_actor_ids,
        unknown_actor_ids=unknown_actor_ids,
        findings=(),
    )
