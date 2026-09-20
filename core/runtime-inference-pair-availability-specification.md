# AI Engineering Orchestra - Runtime-to-Inference Pair Availability Assessment Specification

Version: 0.1.0

This document defines the canonical Runtime-to-Inference Pair Availability
Assessment contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

A **Runtime-to-Inference Pair Availability Assessment** is an immutable, pure,
deterministic assessment of one explicitly supplied positive external
Runtime-to-Inference compatibility edge against the normalized availability
states of its exact endpoints within one caller-owned evaluation context.

It answers only:

> What availability outcome follows for each supplied compatible endpoint pair
> from the endpoint inventories and availability observations supplied now?

It does not discover or infer compatibility, create pairs for missing edges,
select a pair, prove a complete execution configuration viable, grant authority,
or invoke anything.

After the canonical term is established, **pair availability assessment** is an
acceptable short form.

---

## 2. Composed Inputs

One assessment invocation accepts exactly five sequences, in this order:

1. Runtime-to-Inference Compatibility Evidence values;
2. Agent Runtime Option Definitions;
3. Inference Option Definitions;
4. Agent Runtime Option Availability Observations; and
5. Inference Option Availability Observations.

The composed contracts remain owned by:

- `core/runtime-inference-compatibility-specification.md`
- `core/agent-runtime-option-specification.md`
- `core/inference-option-specification.md`
- `core/agent-runtime-option-availability-specification.md`
- `core/inference-option-availability-specification.md`

The assessment adds no field, state, or changed standalone validation meaning
to any of those contracts. Inputs are expected to be typed, structurally valid
values. The function captures each caller sequence once as a tuple and reuses
the captured endpoint inventories throughout the composed validation.

No Actor, Task, Assignment, Execution Mode, policy, prevalidated result, or
snapshot identifier is an input.

---

## 3. Assessment Value and Identity

Each assessment stores exactly:

| Field | Type | Purpose |
| --- | --- | --- |
| `runtime_option_id` | `str` | Exact Runtime endpoint reference from the supplied edge |
| `option_id` | `str` | Exact Inference endpoint reference from the supplied edge |
| `runtime_availability_state` | `AgentRuntimeOptionAvailabilityState` | Normalized state of the exact Runtime endpoint |
| `inference_availability_state` | `InferenceOptionAvailabilityState` | Normalized state of the exact Inference endpoint |

Pair identity remains the exact, case-sensitive tuple:

```text
(runtime_option_id, option_id)
```

`outcome` is a computed, read-only property. It is not stored independently and
cannot diverge from the two normalized endpoint states. An assessment and the
top-level result are frozen values; top-level findings and assessments are
tuples.

Direct Python construction with a raw string, the other endpoint's enum type,
or any other value in either state field raises `ValueError`. Reading `outcome`
also preserves the exact-type invariant. `StrEnum` value equality must not
silently turn a malformed programming value into an ordinary domain outcome.
This guard is a Python API invariant, not a new validation finding or serialized
structural rule.

---

## 4. Closed Outcomes

The outcome set is exactly:

- `established`
- `blocked`
- `unresolved`

### `established`

The caller supplied a validated positive compatibility edge and both exact
endpoints normalized to `available` in the supplied context.

`established` is deliberately narrow. It does not prove Actor applicability,
Task suitability, capability or Execution Mode satisfaction, capacity, quota,
authorization, reservation, dispatchability, or successful execution.

### `blocked`

At least one exact endpoint normalized to `unavailable`. Positive unavailable
evidence dominates an available or unknown state at the other endpoint.

`blocked` applies only to the assessed pair in this supplied context. It does
not retire an endpoint, negate compatibility, prohibit every configuration, or
grant authority to change external state.

### `unresolved`

Neither endpoint is unavailable and at least one endpoint normalized to
`unknown`. Missing and explicit unknown observations therefore have the same
effect.

`unresolved` must not be collapsed to `blocked`, `unavailable`, or incompatible.

---

## 5. Complete Truth Table

The computed outcome for every endpoint-state combination is:

| Runtime state | Inference state | Outcome |
| --- | --- | --- |
| `available` | `available` | `established` |
| `available` | `unavailable` | `blocked` |
| `available` | `unknown` | `unresolved` |
| `unavailable` | `available` | `blocked` |
| `unavailable` | `unavailable` | `blocked` |
| `unavailable` | `unknown` | `blocked` |
| `unknown` | `available` | `unresolved` |
| `unknown` | `unavailable` | `blocked` |
| `unknown` | `unknown` | `unresolved` |

The table is exhaustive. It contains no precedence beyond unavailable
dominance and the positive two-available requirement for `established`.

---

## 6. Validation Composition

Validation follows one fixed sequence.

### Compatibility first

Core first invokes `validate_runtime_inference_compatibility` with the captured
evidence and captured endpoint inventories.

If compatibility validation is invalid:

- availability validators do not run;
- compatibility finding codes, messages, and order are converted unchanged;
- `valid` is `false`; and
- `assessments` is empty.

This preserves compatibility's Runtime-then-Inference inventory findings,
duplicate-edge findings, unknown-reference findings, canonical ordering, and
atomicity without reimplementing them.

### Both availability validators after valid compatibility

After valid compatibility, Core invokes both validators in this order:

1. `validate_agent_runtime_option_availability`
2. `validate_inference_option_availability`

Both receive the same captured inventories used for compatibility validation.
Both validators run even when Runtime availability is invalid, so independent
Inference findings are not hidden.

All Runtime availability findings precede all Inference availability findings.
Within each group, the source validator's exact code, message, and deterministic
order are preserved. If either result has a finding, the complete assessment
result is invalid and contains no assessments.

Invalid input is never converted to `blocked` or `unresolved`. Those are valid
per-edge outcomes, not validation-error substitutes.

---

## 7. Assessment Construction and Ordering

After every composed input validates, Core builds exactly one assessment for
each normalized supplied compatibility edge. It looks up each endpoint's state
in the normalized availability results and computes the outcome from Section 5.

Assessments retain compatibility's exact pair ordering:

```text
(runtime_option_id, option_id)
```

There is no Cartesian product, inferred edge, default pair, wildcard, or pair
for a Runtime or Inference Option that has no supplied edge. Ordering is
canonical representation only; it is not ranking, preference, fallback, or
selection.

One-to-many and many-to-one relations are valid. Mixed outcomes are valid and
do not cause Core to select a winner.

---

## 8. Empty Relation and Missing Observations

A valid empty compatibility relation still requires both availability inputs
and both endpoint inventories to pass their existing validators. When every
input is valid, the result is valid with empty findings and empty assessments.

Missing availability observations normalize to `unknown` under the existing
availability contracts. Explicit `unknown` and absence therefore yield the
same pair outcome. The assessment does not retain provenance distinguishing
them.

A Runtime Option with no supplied external compatibility edge receives no
assessment. In particular, no edge may mean that inference is selected or
bound internally. It does not mean blocked, unavailable, incompatible, unable
to execute, or misconfigured.

---

## 9. Result Contract and Atomicity

The top-level result fields are exactly:

- `valid`
- `findings`
- `assessments`

A valid result has no findings and zero or more deterministic assessments. An
invalid result has one or more findings and no assessments. Partial assessment
results are forbidden.

The assessment function does not mutate its inputs. Capturing the caller's
five sequences once allows one-shot iterables used at the Python boundary to be
materialized once before composed validators reread the resulting tuples.

---

## 10. Snapshot Ownership and Freshness

The environment owns operational reality and the caller owns the supplied
evaluation context. The framework neither discovers nor refreshes availability
or compatibility facts.

The assessment contains no timestamp, expiry, provenance, snapshot ID, polling,
monitoring, capacity, quota, or health check. Two availability sequences in one
call are composed as supplied; Core does not prove that observations were made
simultaneously or remain current after return.

Results are derived in memory and are not a registry, durable decision, cache,
reservation, or promise about future execution.

---

## 11. Actor, Selection, Authority, and Execution Boundaries

Pair availability assessment is separate from Actor applicability, Actor
Availability, Actor Selection, Assignment, Task suitability, and Execution Mode
matching. It introduces no Actor-to-Runtime or Actor-to-Inference relation and
does not change any existing selection or responsibility binding.

The mandatory separation is:

```text
validated positive edge + endpoint availability
!= complete viable execution configuration
!= selected configuration
!= authorized
!= reserved
!= dispatched
!= executing
```

The assessment performs no ranking, routing, fallback, Runtime selection,
Inference Option selection, Provider selection, model selection, authorization,
reservation, dispatch, Execution Contract creation, execution, or invocation.

It also performs no file, network, process, clock, discovery, Provider SDK,
credential, endpoint, persistence, cache, registry, or global-state operation.

---

## 12. Structural Authority and Persistence

This is a derived, in-memory semantic result. AIO-032 adds no assessment schema,
schema fixture, schema resource, serialized request, Project Manifest field,
CLI command, persistent inventory, or package-root re-export.

The five existing input schemas remain the structural authorities for their
respective serialized values. This specification is the semantic authority for
validation composition, outcome calculation, assessment ordering, atomicity,
and boundaries.

---

## 13. Runtime API

The immutable values and pure deterministic function are defined in:

`engineering_orchestration.runtime_inference_pair_availability`

The module exposes:

- `RuntimeInferencePairAvailabilityOutcome`
- `RuntimeInferencePairAvailabilityAssessment`
- `RuntimeInferencePairAvailabilityFinding`
- `RuntimeInferencePairAvailabilityResult`
- `assess_runtime_inference_pair_availability`

The function parameters are exactly `evidence`, `runtime_options`,
`inference_options`, `runtime_availability_observations`, and
`inference_availability_observations`, in that order.

---

## 14. Exclusions

The first contract contains no:

- new endpoint, compatibility, or availability field or state;
- negative compatibility evidence, inferred compatibility, or totality rule;
- Actor, Task, Assignment, Execution Mode, capability, tool, safety, cost,
  latency, reasoning-strength, or policy input;
- score, preference, ranking, routing, fallback, or selection;
- complete configuration viability, authorization, reservation, dispatch,
  Execution Contract, execution, or invocation;
- adapter, discovery, network, credentials, Provider SDK, polling, monitoring,
  clock, persistence, history, cache, or registry;
- schema, schema resource, serialized assessment contract, Project Manifest
  field, CLI command, package-root export, or third-party dependency.

Any broader execution-configuration viability layer requires separate future
authorization and must preserve the narrow meanings defined here.
