# AI Engineering Orchestra - Agent Runtime Option Availability Specification

Version: 0.1.0

This document defines the canonical Agent Runtime Option Availability
Observation contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

An **Agent Runtime Option Availability Observation** is an immutable, ephemeral
observation describing the currently known availability state of one Agent
Runtime Option within one caller-supplied evaluation snapshot.

It is operational evidence separate from the relatively stable identity defined
by `core/agent-runtime-option-specification.md`.

```text
Agent Runtime Option Definition
!= Agent Runtime Option Availability Observation

available
!= Actor-to-Runtime applicable
!= Inference Option available
!= compatible
!= authorized
!= selected
!= executing
```

---

## 2. Canonical Contract

The v0.1 observation contains exactly two fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `runtime_option_id` | Yes | Exact reference to one option in the supplied Runtime Option inventory |
| `state` | Yes | Currently known availability state |

No other field is part of the contract.

```yaml
runtime_option_id: primary-agent-runtime
state: available
```

### `runtime_option_id`

`runtime_option_id` is a required, nonempty, opaque, case-sensitive reference.
It does not create or infer an Agent Runtime Option.

### `state`

`state` is required and has exactly three values:

- `available`
- `unavailable`
- `unknown`

These values describe Runtime Option availability only. They are not Actor,
Inference Option, compatibility, authorization, selection, capacity, lifecycle,
session, invocation, or execution states.

---

## 3. State Semantics

### `available`

Positive availability-only evidence indicates that the Agent Runtime Option may
currently be considered operationally available. A future configuration
evaluator may consume that evidence.

It does not mean:

- an Actor is compatible
- an Inference Option is available or compatible
- tools or capabilities are sufficient
- capacity is available
- the Runtime Option is selected
- execution is authorized
- Task Execution Mode is satisfied
- an Agent is executing

### `unavailable`

Positive current evidence indicates that the Agent Runtime Option must not
presently be treated as available.

It does not imply permanent disablement, deletion, retirement, loss of identity,
or removal from a future configuration.

### `unknown`

There is no reliable current determination that the Agent Runtime Option is
available or unavailable.

```text
unknown != unavailable
```

Unknown must not be normalized to unavailable.

---

## 4. Snapshot Validation and Normalization

One pure invocation consumes structurally valid normalized definitions and
observations. It performs no I/O and retains no state between invocations.

### Valid Runtime Option inventory

The underlying supplied inventory must satisfy the Agent Runtime Option
Specification. Duplicate `runtime_option_id` values invalidate the foundational
context before observations are inspected.

Inventory findings are preserved using their original stable code and message.
An invalid foundational inventory yields no normalized observations.

### Known Runtime Option references

Every supplied observation must reference a known Runtime Option. Each distinct
unknown reference produces:

`agent_runtime_option_not_found`

No observation synthesizes a Runtime Option Definition.

### Duplicate observations

At most one observation may be supplied for each `runtime_option_id`. Identical
and conflicting duplicates are equally invalid because the snapshot defines no
temporal or declaration-order precedence.

Each duplicated ID produces:

`duplicate_agent_runtime_option_availability`

### Missing observations

A known Runtime Option without an observation normalizes to an explicit
`unknown` observation. Absence is valid and never means `unavailable`. Missing
and explicit `unknown` normalize identically; the minimal contract retains no
provenance distinguishing them.

### Determinism and atomicity

Foundational inventory validation runs first. For a valid inventory,
duplicate-observation findings precede unknown-reference findings. Each
affected ID is reported once per finding kind, with IDs ordered by exact
case-sensitive sorting.

Any finding invalidates the complete snapshot and yields no partial normalized
observations. A valid result contains exactly one observation per supplied
Runtime Option ordered by exact `runtime_option_id`. Ordering is
canonicalization, not preference or selection.

`valid` means only that inventory and observation invariants hold. It does not
mean that any Runtime Option is available, compatible, authorized, selected, or
usable.

---

## 5. Identity, Compatibility, and Execution Boundaries

Availability never changes `runtime_option_id` or creates a Runtime Option.

```text
Runtime compatible
!= Runtime available

Runtime available
!= Actor-to-Runtime applicable
!= Inference Option available
!= authorized
!= executing
```

Even the following combined evidence is insufficient:

```text
Actor-to-Runtime applicable
+ Runtime available
+ Inference Option available
!= authorized execution
```

Actor-to-Runtime Applicability Evidence is a separate positive relation defined
by `core/actor-runtime-applicability-specification.md`. This availability
contract neither consumes nor implies that relation, and an applicability edge
does not prove Runtime availability.

Runtime-to-Inference Compatibility Evidence is a separate positive relation
defined by `core/runtime-inference-compatibility-specification.md`. This
availability contract neither consumes nor implies that relation. A Runtime
Option may expose zero externally selectable Inference Options, so absence of an
edge must not imply that it cannot execute.

The separate derived composition is defined by
`core/runtime-inference-pair-availability-specification.md`. It may consume this
contract's normalized state without changing Runtime availability semantics.
This standalone availability contract itself performs no pair assessment.

Availability does not inspect or change Actor identity, Actor Availability,
Actor Selection, Assignment, Inference Option identity or availability, Task
Execution Mode, Quality Gate state, or Human Control.

It grants no credential, permission, approval, network, tool, or execution
authority and creates no execution configuration, Execution Contract, dispatch,
session, invocation, or execution instance.

---

## 6. Ownership, Volatility, and Provider Neutrality

The environment owns operational reality and the caller owns the evaluation
snapshot. Observations may be supplied manually or translated by a future
adapter, but the contract does not identify or depend on their producer.

Observations are in-memory only. AIO-029 defines no project configuration,
timestamp, freshness guarantee, reservation, persistence, history, cache,
polling, monitoring, Provider SDK, or network access.

Availability validation does not inspect Provider or model identity,
credentials, endpoint configuration, capacity, load, price, quota, account
access, tools, capabilities, lifecycle, latency, region, or reasoning controls.

---

## 7. Runtime API

The immutable value objects and pure snapshot validator are defined in:

`engineering_orchestration.agent_runtime_option_availability`

The API exposes `AgentRuntimeOptionAvailabilityState`,
`AgentRuntimeOptionAvailabilityObservation`,
`AgentRuntimeOptionAvailabilityFinding`,
`AgentRuntimeOptionAvailabilityValidationResult`, and
`validate_agent_runtime_option_availability`.

The validator performs no discovery, selection, authorization, execution,
network access, or persistence.

---

## 8. Structural Authority

The machine-readable structural schema is:

`schemas/agent-runtime-option-availability.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates a snapshot invariant or semantic
boundary described here.
