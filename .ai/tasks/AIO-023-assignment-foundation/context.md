# AIO-023 Context

## Current limitation

AIO-022 completed the runtime chain from Workflow Role references through the
canonical Role Catalog to Actor competency coverage. The framework can determine
whether a supplied Actor is eligible for a Role, but it cannot record which
Actor was selected for one concrete Task/Workflow/Stage/Role responsibility.

## Locked contract

Assignment is an immutable responsibility binding with exactly `task_id`,
`workflow_id`, `stage_id`, `role_id`, and `actor_id`. Its responsibility key
excludes `actor_id`. Assignment records an externally made choice; it does not
select, rank, recommend, authorize, execute, or persist an Actor.

Individual validation uses a normalized Task, valid Workflow and Role catalogs,
caller-supplied Actors, and the existing Actor coverage evaluator. Duplicate
Actor IDs invalidate the supplied context. Ordinary data errors produce stable
findings; catalog corruption remains an infrastructure failure.

## Sequence semantics

Sequence validation rejects duplicate responsibility keys. Only individually
valid values with unique keys cover Workflow requirements. Completeness remains
separate from validity, repeated Role references in one Stage collapse to one
slot, and unassigned keys follow Stage and Role declaration order.

The only separation analysis is definite Actor-identity conflict between valid,
unique `software-engineer` and `reviewer` bindings for the same Task/Workflow.
It is evidence outside generic validity and completeness and never establishes a
Quality Gate result.

## Boundaries

AIO-023 introduces no assignment storage, lifecycle, availability, Actor
catalog, automatic selection, Provider/model/runtime data, permission, execution,
Stage state, Gate result, CLI, or AIO-024. The existing Task, Workflow, Role,
Actor, and Project Manifest schemas and `.ai/project.yaml` remain unchanged.

The governing Workflow is `architecture-change`. Separate reviewer and final
architect approvals, both required Gate outcomes, and explicit Human approval
are recorded in `review.md`.
