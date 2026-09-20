# AI Engineering Orchestra - Inference Option Availability Specification

Version: 0.1.0

This document defines the canonical Inference Option Availability Observation
contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

An **Inference Option Availability Observation** is an immutable, ephemeral,
Provider-neutral value describing the currently known availability state of one
Inference Option within one caller-supplied evaluation snapshot.

It is operational evidence separate from the relatively stable identity defined
by `core/inference-option-specification.md`.

```text
Inference Option Definition
!= Inference Option Availability Observation

available
!= authorized
!= selected
!= executable
```

---

## 2. Canonical Contract

The v0.1 observation contains exactly these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `option_id` | Yes | Exact reference to one option in the supplied inventory |
| `state` | Yes | Currently known availability state |

No other field is part of the contract.

```yaml
option_id: primary-engineer-inference
state: available
```

### `option_id`

`option_id` is a required, nonempty, opaque, case-sensitive reference. It does
not create or infer an Inference Option.

### `state`

`state` is required and has exactly three values:

- `available`
- `unavailable`
- `unknown`

These values describe option availability only. They are not model lifecycle,
account, authorization, runtime, or execution states.

---

## 3. State Semantics

### `available`

Positive availability-only evidence indicates that the Inference Option may
currently be considered by a future option selector or configuration evaluator.

It does not mean authorized, selected, assigned, executable, within quota,
affordable, compatible with Task Execution Mode, or paired with an available
Agent Runtime Option.

### `unavailable`

Positive current evidence indicates that the Inference Option must not
presently be treated as available.

It does not imply permanent model retirement, deprecation, deletion, or loss of
identity.

### `unknown`

There is no current positive knowledge that the Inference Option is available
or unavailable.

```text
unknown != unavailable
```

---

## 4. Snapshot Validation and Normalization

One pure invocation consumes structurally valid normalized definitions and
observations. It performs no I/O and retains no state between invocations.

### Valid option inventory

The underlying supplied option inventory must satisfy the Inference Option
Specification. Duplicate `option_id` values invalidate the foundational context
before observations are inspected.

### Known option references

Every supplied observation must reference a known option. Each distinct unknown
reference produces `inference_option_not_found`; no observation synthesizes an
option.

### One observation per option

At most one observation may be supplied for an option in one snapshot. Any
duplicate, whether states agree or conflict, produces
`duplicate_inference_option_availability`. Declaration order never establishes
precedence because this contract defines no timestamps or temporal ordering.

### Missing observation

A known option without an observation normalizes to an explicit `unknown`
observation. Absence is valid and never means `unavailable`. Missing and
explicit `unknown` are intentionally equivalent in the normalized result; this
minimal contract retains no provenance distinguishing them.

### Determinism and atomicity

Duplicate-observation findings precede unknown-option findings. Each affected
option ID is reported once per finding kind, with IDs ordered by exact
case-sensitive sorting.

Any finding invalidates the whole snapshot and yields no partial normalized
observations. A valid result contains exactly one observation per supplied
option ordered by exact option ID. The ordering is canonicalization, not
selection preference.

`valid` means only that inventory and observation invariants hold. It does not
mean that any option is available or usable.

---

## 5. Identity, Runtime, and Authorization Boundaries

Availability never changes `option_id`, `provider_id`, or `model_id` and does
not select a Provider or model.

Agent Runtime Option availability is separate and is defined by
`core/agent-runtime-option-availability-specification.md`. This observation does
not define an Agent Runtime Option, Agent Service, tool executor, session owner,
or state owner. It does not inspect Actor identity, Actor Selection, Assignment,
or Task Execution Mode. Runtime-to-Inference Compatibility Evidence is defined
separately by `core/runtime-inference-compatibility-specification.md`; this
availability observation neither consumes nor implies that relation.

Availability grants no credential, permission, approval, Human Control, network,
or execution authority and creates no Execution Contract or invocation.

---

## 6. Ownership, Volatility, and Provider Neutrality

The environment owns operational reality and the caller owns the evaluation
snapshot. Observations may be supplied manually or translated by a future
adapter, but the contract does not identify or depend on their producer.

Observations are in-memory only. AIO-028 defines no project configuration,
timestamp, freshness guarantee, reservation, persistence, history, cache,
polling, monitoring, Provider SDK, or network access.

Availability validation does not inspect credentials, endpoint configuration,
price, quota, account access, lifecycle, latency, region, capabilities, or
reasoning controls.

---

## 7. Runtime API

The immutable value objects and pure snapshot validator are defined in:

`engineering_orchestration.inference_option_availability`

The validator performs no discovery, selection, authorization, execution,
network access, or persistence.

---

## 8. Structural Authority

The machine-readable structural schema is:

`schemas/inference-option-availability.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates a snapshot invariant or semantic
boundary described here.
