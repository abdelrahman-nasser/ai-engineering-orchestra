# AI Engineering Orchestra - Actor Availability Observation Specification

Version: 0.1.0

This document defines the canonical Actor Availability Observation contract for
AI Engineering Orchestra v0.1.

---

## 1. Purpose

An Actor Availability Observation is an immutable, Provider-neutral, ephemeral
value describing the currently known availability state of one Actor within one
caller-supplied evaluation snapshot.

It answers only whether that Actor is currently observed as available. It does
not change Actor identity or competencies and does not establish eligibility,
Assignment, authority, permission, approval, or execution.

```text
Actor
!= Actor Availability Observation

eligible
!= available

available
!= assigned
!= authorized
!= executing
```

---

## 2. Canonical Contract

The v0.1 Actor Availability Observation contains exactly these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `actor_id` | Yes | Exact reference to one Actor in the supplied Actor context |
| `state` | Yes | Currently known availability: `available`, `unavailable`, or `unknown` |

No other field is part of the contract.

```yaml
actor_id: agent-engineer-1
state: available
```

### `actor_id`

`actor_id` is a required, nonempty, opaque, case-sensitive reference to an
existing Actor in the caller-supplied Actor context. It does not create or infer
Actor identity.

The identifier does not encode an Actor kind, Provider, model, runtime,
authority, or availability claim.

### `state`

`state` is required and has exactly three values:

- `available`
- `unavailable`
- `unknown`

These values describe availability only. They are not Actor or execution
lifecycle states.

---

## 3. State Semantics

### `available`

The current observation positively indicates that the Actor may be considered
by Actor Selection from an availability perspective.

It does not establish competency eligibility, Assignment, authority,
permission, approval, or execution.

### `unavailable`

The current observation positively indicates that the Actor must not currently
be treated as available by Actor Selection.

It does not permanently disable the Actor, change Actor identity or
competencies, invalidate an Assignment, or describe an execution lifecycle.

### `unknown`

There is no current positive knowledge that the Actor is available or
unavailable.

```text
unknown != unavailable
```

Actor Selection must preserve this distinction.

---

## 4. Snapshot Validation and Normalization

The pure runtime validator consumes already structurally valid normalized Actor
Availability Observations and a caller-supplied sequence of normalized Actors.
One invocation represents one evaluation snapshot. It performs no I/O and
retains no state between invocations.

### Unique Actor context

Actor IDs must be unique within the supplied Actor context, reusing the Actor
contract's existing uniqueness invariant. Duplicate Actor IDs produce the
finding `duplicate_actor_id`. The snapshot is invalid and has no normalized
observations.

### Known Actor references

Every supplied observation must reference an Actor in the supplied context. An
unknown reference produces `actor_not_found`; it never creates or infers an
Actor.

### One observation per Actor

At most one observation may be supplied for an Actor ID in one snapshot. Any
duplicate, whether its states agree or conflict, produces
`duplicate_actor_availability`. Declaration order never establishes precedence;
there is no first-write-wins or last-write-wins behavior.

### Missing observation

A known Actor with no supplied observation normalizes to an explicit
`state: unknown` observation. Absence is valid, produces no finding, and is
never interpreted as `unavailable`.

An explicit `unknown` and a missing observation are intentionally equivalent in
the normalized result. The minimal contract does not retain provenance that
distinguishes them.

### Determinism and atomicity

With a unique Actor context, duplicate-observation findings precede unknown-Actor
findings. Each affected Actor ID is reported once per finding kind, and IDs are
ordered by exact case-sensitive sorting.

Any finding invalidates the entire snapshot and produces no partial normalized
output. A valid result contains exactly one observation per supplied Actor,
ordered by exact case-sensitive Actor ID. This ordering is canonicalization,
not ranking or selection precedence.

`valid` means only that Actor-context and observation invariants hold. It does
not mean that any Actor is available.

---

## 5. Actor, Eligibility, and Assignment Boundaries

Actor remains the stable three-field identity-and-competencies contract:

```text
id
kind
competencies
```

Availability never changes Actor identity, kind, or competencies. Human and
Agent Actors use the same observation contract and state semantics; validation
needs only the Actor `id`.

Actor-to-Role competency coverage remains a separate eligibility calculation.
An Actor may be competency-compatible and unavailable, or incompatible and
available. Availability validation does not inspect Role requirements or alter
coverage.

Assignment remains an immutable record of an externally made responsibility
choice. Assignment validity does not depend on current availability, and an
unavailable or unknown Actor may still appear in an externally supplied
historical or future Assignment.

Actor Selection may consume the normalized snapshot together with separate
competency eligibility evidence. Its outcome semantics belong to
`core/actor-selection-specification.md`; this Availability contract itself
performs no selection, ranking, recommendation, or Assignment generation.

---

## 6. Authority and Execution Boundaries

Availability grants no filesystem, shell, network, credential, permission,
approval, Human Control, or execution authority.

```text
available != authorized
available != assigned
available != executing
```

Human availability does not grant Human approval. Agent availability does not
grant execution authority. The states `busy`, `running`, `idle`, `executing`,
and `completed` are execution or lifecycle concepts and are not availability
states in this contract.

Availability is runtime evidence, not a Quality Gate result.

---

## 7. Ownership, Volatility, and Provider Neutrality

Observations may be supplied manually or by a caller, environment, organization
runtime, or future adapter. The contract does not identify or depend on the
producer.

Observations are caller-supplied and in-memory only. AIO-024 defines no Actor
catalog, availability file, Project Manifest configuration, Task field,
database, cache, history, event log, or freshness claim.

The contract requires no Provider, model, runtime, API, quota service, network
access, polling, monitoring, scheduling, reservation, load, or capacity data.
Future adapters may translate external facts into these canonical states
without changing the observation contract.

---

## 8. Exclusions

Actor Availability Observation does not define or contain:

- Actor identity or competency changes
- Provider, model, runtime, source, reason, timestamp, or provenance fields
- authority, permissions, approval, credentials, or execution policy
- reservations, schedules, load, quota, capacity, or concurrency
- persistence, availability history, Actor catalogs, or background monitoring
- competency eligibility composition
- Actor Selection logic, ranking, recommendation, or tie behavior
- Assignment creation, mutation, or validation changes
- selected, ambiguous, indeterminate, or no-candidate outcome definitions
- Task Assessment, Model Tier, Quality Gate, or CLI behavior

---

## 9. Runtime API

The immutable value objects and pure snapshot validator are defined in:

`engineering_orchestration.actor_availability`

The validator consumes supplied values and returns immutable findings and
normalized observations. It does not parse files, discover Actors, contact a
Provider, persist data, or perform selection.

---

## 10. Structural Authority

The machine-readable structural schema is:

`schemas/actor-availability.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates a semantic boundary described here.
