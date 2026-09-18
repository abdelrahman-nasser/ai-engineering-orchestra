# AIO-024 Context

## Current limitation

AIO can resolve Workflow Roles, evaluate supplied Actor competency eligibility,
and validate an externally selected Assignment. It cannot yet represent whether
one Actor is currently observed as available for consideration by a future
selector.

AIO-024 adds that missing runtime input without performing selection. Actor
identity remains stable, while availability remains a volatile observation.

## Observation contract

The canonical term is **Actor Availability Observation**: a provider-neutral,
ephemeral observation describing the currently known availability state of one
Actor.

The design stage locked the smallest serialized shape, using the existing
referenced-identity convention and one closed state value:

```yaml
actor_id: agent-engineer-1
state: available
```

The state set is exactly `available`, `unavailable`, and `unknown`.
`available` is positive availability-only evidence that the Actor may be
considered by a future selector; `unavailable` is a current negative observation
rather than permanent disablement; and `unknown` means availability is not
currently known. Unknown is not unavailable.

## Snapshot semantics

One evaluation snapshot accepts caller-supplied Actors and availability
observations. A known Actor without an explicit observation is treated as
availability-equivalent to `unknown`, never `unavailable`; the normalized result
does not retain provenance distinguishing absence from explicit `unknown`.

An observation naming an unknown Actor is invalid and never creates Actor
identity. The existing unique-Actor-ID invariant is reused. Multiple
observations for one Actor in the same snapshot are rejected without using
declaration order or last-write-wins behavior, whether their states agree or
conflict.

## Architectural boundaries

Actor Availability Observation is separate from Actor identity, Actor-Role
competency coverage, Assignment, authority, permission, approval, reservation,
and execution. Availability does not modify Actor competencies or Assignment
validity, and it produces no selection outcome or proposed Assignment.

Human and Agent Actors use the same observation contract. The contract requires
no Provider, model, runtime, source, timestamp, quota, capacity, calendar, or
network integration. Observations are supplied in memory; AIO-024 adds no Actor
catalog, persistence, history, polling, monitoring service, or project
configuration.

## Workflow and Human control

The `architecture-change` Workflow governs this Task. An architect must lock the
contract and boundaries before implementation, a software engineer implements
the approved design, and genuinely separate reviewer and architect reviews
evaluate the result. Work stops at the review-stage Human Control checkpoint
with the Task still `in_progress`. No commit or AIO-025 is authorized.
