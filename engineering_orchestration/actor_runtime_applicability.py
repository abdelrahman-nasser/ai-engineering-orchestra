"""Pure validation of Actor-to-Runtime Applicability Evidence.

Applicability is caller-supplied positive topology evidence connecting a known
Agent Actor to an Agent Runtime Option. It is not availability, selection,
assignment, authorization, or execution, and this module performs no discovery,
I/O, or persistence.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, cast

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)


@dataclass(frozen=True)
class ActorRuntimeApplicabilityEvidence:
    """One immutable positive applicability edge between supplied endpoints."""

    actor_id: str
    runtime_option_id: str


@dataclass(frozen=True)
class ActorRuntimeApplicabilityFinding:
    """Stable semantic finding from applicability-relation validation."""

    code: str
    message: str


@dataclass(frozen=True)
class ActorRuntimeApplicabilityValidationResult:
    """Validation result and, when valid, canonicalized supplied evidence."""

    valid: bool
    findings: tuple[ActorRuntimeApplicabilityFinding, ...]
    normalized_evidence: tuple[ActorRuntimeApplicabilityEvidence, ...]


def validate_actor_runtime_applicability(
    evidence: Iterable[ActorRuntimeApplicabilityEvidence],
    actors: Iterable[Mapping[str, object]],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
) -> ActorRuntimeApplicabilityValidationResult:
    """Validate one caller-supplied positive applicability relation.

    Each input iterable is captured once, in Actor, Runtime, then evidence order.
    Actor-context and Runtime-inventory foundations are validated before relation
    semantics. With valid foundations, duplicate edges precede unknown Actors,
    Human Actor endpoints, and unknown Runtimes. Exact identifier sorting makes
    findings independent of declaration order. Any finding invalidates the
    complete relation; valid evidence is pair-sorted only for canonicalization.

    Individual Actor mappings are expected to have passed ``actor.schema.json``.
    This validator owns only Actor-context uniqueness and the relation's
    Agent-only endpoint rule.
    """

    supplied_actors = tuple(actors)
    supplied_runtime_options = tuple(runtime_options)
    supplied_evidence = tuple(evidence)

    actor_ids = tuple(cast(str, actor["id"]) for actor in supplied_actors)
    actor_id_counts = Counter(actor_ids)
    duplicate_actor_ids = tuple(
        sorted(
            actor_id
            for actor_id, count in actor_id_counts.items()
            if count > 1
        )
    )
    runtime_inventory = validate_agent_runtime_option_inventory(
        supplied_runtime_options
    )

    foundational_findings: list[ActorRuntimeApplicabilityFinding] = []
    if duplicate_actor_ids:
        foundational_findings.append(
            ActorRuntimeApplicabilityFinding(
                code="duplicate_actor_id",
                message=(
                    "Actor IDs must be unique in the supplied context; "
                    "duplicates: " + ", ".join(duplicate_actor_ids)
                ),
            )
        )
    foundational_findings.extend(
        ActorRuntimeApplicabilityFinding(finding.code, finding.message)
        for finding in runtime_inventory.findings
    )
    if foundational_findings:
        return ActorRuntimeApplicabilityValidationResult(
            valid=False,
            findings=tuple(foundational_findings),
            normalized_evidence=(),
        )

    actors_by_id = dict(zip(actor_ids, supplied_actors, strict=True))
    known_runtime_option_ids = {
        option.runtime_option_id for option in runtime_inventory.normalized_options
    }
    edge_counts = Counter(
        (item.actor_id, item.runtime_option_id) for item in supplied_evidence
    )

    findings: list[ActorRuntimeApplicabilityFinding] = []
    for actor_id, runtime_option_id in sorted(
        edge for edge, count in edge_counts.items() if count > 1
    ):
        findings.append(
            ActorRuntimeApplicabilityFinding(
                code="duplicate_actor_runtime_applicability",
                message=(
                    f"Actor '{actor_id}' and Agent Runtime Option "
                    f"'{runtime_option_id}' have more than one supplied "
                    "applicability evidence value."
                ),
            )
        )

    referenced_actor_ids = {item.actor_id for item in supplied_evidence}
    for actor_id in sorted(referenced_actor_ids - set(actors_by_id)):
        findings.append(
            ActorRuntimeApplicabilityFinding(
                code="actor_not_found",
                message=(
                    f"Actor '{actor_id}' was not found in the supplied Actor "
                    "context."
                ),
            )
        )

    for actor_id in sorted(
        actor_id
        for actor_id in referenced_actor_ids & set(actors_by_id)
        if actors_by_id[actor_id]["kind"] == "human"
    ):
        findings.append(
            ActorRuntimeApplicabilityFinding(
                code="actor_runtime_applicability_requires_agent_actor",
                message=(
                    f"Actor '{actor_id}' has kind 'human'; Actor-to-Runtime "
                    "Applicability Evidence requires an Agent Actor endpoint."
                ),
            )
        )

    for runtime_option_id in sorted(
        {item.runtime_option_id for item in supplied_evidence}
        - known_runtime_option_ids
    ):
        findings.append(
            ActorRuntimeApplicabilityFinding(
                code="agent_runtime_option_not_found",
                message=(
                    f"Agent Runtime Option '{runtime_option_id}' was not found "
                    "in the supplied inventory."
                ),
            )
        )

    if findings:
        return ActorRuntimeApplicabilityValidationResult(
            valid=False,
            findings=tuple(findings),
            normalized_evidence=(),
        )

    return ActorRuntimeApplicabilityValidationResult(
        valid=True,
        findings=(),
        normalized_evidence=tuple(
            sorted(
                supplied_evidence,
                key=lambda item: (item.actor_id, item.runtime_option_id),
            )
        ),
    )
