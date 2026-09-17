# AIO-021 Context

## Actor foundation

AIO has canonical Roles that describe reusable responsibilities and required
engineering competencies, but it has no canonical way to represent the concrete
Human or Agent candidate that might fulfil one. AIO-021 adds that missing **who**
boundary without selecting, assigning, authorizing, or executing the candidate.

The Actor contract is locked to `id`, `kind`, and `competencies`. Actor identity
is distinct from availability, assignment, authority, permission, approval, and
execution. `kind` is exactly `human` or `agent`; both kinds use the same
competency coverage rule, and neither value grants authority.

## Role and competency relationship

A Role remains a reusable responsibility and its required competencies. An Actor
is a concrete potential fulfiller. Actor does not contain `roles`; compatibility
is derived by subtracting `Actor.competencies` from
`Role.required_capabilities` using exact, case-sensitive set membership.

The current nine Role competency identifiers form the initial matching
vocabulary. The Actor schema does not enumerate them, so the vocabulary remains
extensible and unknown or misspelled declarations simply do not cover a required
identifier. No registry, levels, aliases, hierarchy, weights, or scores are
introduced.

An empty Role requirement set is not universal eligibility. It produces an
incompatible, explicitly diagnosed coverage result because no semantically
approved requirements exist. The Role schema remains unchanged.

## Provider, runtime, and authority boundaries

Actor answers who. A Provider is a system or platform that may supply models or
Agent Actors, and runtime describes where or how an Agent executes. Human Actors
need neither. Provider, model, runtime, reasoning, availability, status, cost,
quota, tools, credentials, permission, and authority therefore remain absent
from Actor.

Competency coverage is evidence only. It is not assignment, availability,
authorization, execution, approval, Quality Gate PASS, or independent-review
satisfaction. Equal implementer and reviewer Actor IDs will later be usable as
evidence that independence is not satisfied, but AIO-021 performs no such Gate
evaluation.

## Ownership and future boundary

The contract is framework-owned. Actual inventories are expected to be
environment-, organization-, user-, or runtime-owned. AIO-021 creates no
`.ai/actors/` directory, catalog, profile, instance, commercial Actor fixture, or
Provider integration. Future selection may combine competency compatibility with
runtime availability, but neither selection nor Assignment belongs to this Task.

The pure evaluator consumes already-normalized Actor and Role objects. It does
not discover files, parse Role Markdown, scan repositories, look up Providers,
or inspect availability. A future machine-readable Role catalog is required
before real Role-to-Actor queries can integrate with repository Role data.

## Workflow and Human control

The `architecture-change` Workflow governs this implementation. A separate
architect participates in understand, design, and final architecture review; a
separate reviewer performs independent review. Work stops at the review-stage
Human Control checkpoint with the Task still `in_progress`. No commit or AIO-022
is authorized.
