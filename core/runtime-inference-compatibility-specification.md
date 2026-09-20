# AI Engineering Orchestra - Runtime-to-Inference Compatibility Specification

Version: 0.1.0

This document defines the canonical Runtime-to-Inference Compatibility Evidence
contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

**Runtime-to-Inference Compatibility Evidence** is an immutable,
caller-supplied positive evidence value reporting that one Agent Runtime Option
supports invoking one externally selectable Inference Option within the
supplied evaluation context.

It answers only:

> Which supplied positive Runtime-to-Inference support edges does the caller
> report for this evaluation context?

The evidence is not live verification of an external integration. It does not
prove current availability, configuration viability, selection, authority, or
successful invocation. The contract has no provenance field, and its absence
must not be interpreted as independent verification by Core.

After the canonical term has been established, **compatibility evidence** and
**compatibility relation** are acceptable short prose for the supplied values
and their set of exact edges.

---

## 2. Endpoint and Identity Boundaries

Each evidence value references one definition from each existing endpoint
inventory:

- `runtime_option_id` references an Agent Runtime Option Definition.
- `option_id` references an Inference Option Definition.

The endpoint contracts remain owned by:

- `core/agent-runtime-option-specification.md`
- `core/inference-option-specification.md`

Agent Runtime Option Definition remains exactly `runtime_option_id`. Inference
Option Definition remains exactly `option_id`, `provider_id`, and `model_id`.
The relation is separate from both Definitions. Neither Definition gains an
embedded option list, Runtime list, compatibility state, or inverse relation.

Both references are required, nonempty, opaque, exact, and case-sensitive.
Core does not trim, normalize, case-fold, parse, rewrite, or infer structure
from them. In particular, `provider_id` or `model_id` is never a substitute for
`option_id`, and no identifier requires a UUID, prefix, or pattern.

---

## 3. Canonical Value

The v0.1 Runtime-to-Inference Compatibility Evidence value contains exactly:

| Field | Required | Purpose |
| --- | --- | --- |
| `runtime_option_id` | Yes | Exact reference to one supplied Agent Runtime Option Definition |
| `option_id` | Yes | Exact reference to one supplied Inference Option Definition |

No other field is part of the contract.

```yaml
runtime_option_id: primary-agent-runtime
option_id: primary-inference
```

The exact edge identity is:

```text
(runtime_option_id, option_id)
```

There is no `compatibility_id`. The endpoint pair is sufficient identity within
one caller-supplied relation and evaluation context.

---

## 4. Positive Many-to-Many Relation

The caller supplies an ordinary sequence of evidence values. That sequence is
evaluation input, not a persistent graph or Inventory domain object.

The relation is many-to-many. For example, all of these distinct edges may be
valid together:

```text
R1 -> O1
R1 -> O2
R2 -> O1
```

One Runtime Option may support multiple Inference Options, and one Inference
Option may be supported by multiple Runtime Options. There is no one-to-one
restriction, preferred edge, default edge, automatically chosen endpoint, or
requirement to supply every possible pair.

The relation reports only positive evidence. It contains no negative
compatibility state, confidence, score, priority, weight, ranking, routing, or
fallback order.

---

## 5. Validation Sequence

One pure validation invocation consumes:

1. a caller-supplied compatibility evidence sequence;
2. a caller-supplied Agent Runtime Option Definition sequence; and
3. a caller-supplied Inference Option Definition sequence.

Values are expected to have passed their structural schemas. Relation
validation follows this fixed sequence.

### Foundational inventories first

Core invokes both existing inventory APIs before inspecting or materializing
compatibility evidence:

1. `validate_agent_runtime_option_inventory`
2. `validate_inference_option_inventory`

Both validators run even when the first inventory is invalid. This preserves
their definition validation, duplicate-identity rejection, diagnostic
conventions, and invalid-result behavior without reimplementing weaker checks.

If either inventory is invalid, existing finding codes and messages are
converted to the compatibility finding type. Runtime inventory findings appear
first, followed by Inference inventory findings, while each validator's own
deterministic order is preserved. Relation semantics are not processed, and no
partial normalized evidence is returned.

Foundational duplicate codes remain:

- `duplicate_agent_runtime_option_id`
- `duplicate_inference_option_id`

### Duplicate edges

After valid endpoint inventories are established, every exact pair must be
unique. Each distinct duplicated pair produces:

`duplicate_runtime_inference_compatibility`

The exact message is:

```text
Agent Runtime Option '<runtime_option_id>' and Inference Option '<option_id>' have more than one supplied compatibility evidence value.
```

Duplicated pairs are reported in exact case-sensitive
`(runtime_option_id, option_id)` order. Identical values remain duplicates;
there is no first-wins, last-wins, implicit deduplication, or
declaration-order precedence.

### Known endpoint references

Each `runtime_option_id` must resolve exactly once in the valid normalized
Runtime Option inventory. Every distinct unknown Runtime Option ID produces:

`agent_runtime_option_not_found`

Each `option_id` must resolve exactly once in the valid normalized Inference
Option inventory. Every distinct unknown Inference Option ID produces:

`inference_option_not_found`

Unknown Runtime findings are sorted by exact Runtime Option ID and precede
unknown Inference findings, which are sorted by exact Inference Option ID. A
reference that differs only by case remains unknown. Core does not synthesize
an endpoint, drop an edge, or select one duplicate endpoint definition.

### Finding order

With valid endpoint inventories, finding categories are always:

1. duplicate exact pairs;
2. unknown Runtime Option IDs;
3. unknown Inference Option IDs.

This order and exact identifier sorting make results independent of declaration
order. A source position does not establish precedence.

---

## 6. Canonicalization and Atomicity

A valid result contains the supplied unique evidence ordered by exact:

```text
(runtime_option_id, option_id)
```

Ordering exists only for deterministic representation. It is not ranking,
preference, routing, fallback, selection, authorization, or execution order.

Any endpoint-inventory or relation finding invalidates the complete result.
The invalid-result convention is:

```text
valid: false
normalized_evidence: ()
```

Core returns no partially accepted relation and does not mutate endpoint or
evidence inputs.

---

## 7. Empty Relation and Missing-Edge Semantics

An empty compatibility relation is valid whenever both endpoint inventories
are valid. This includes:

- two empty inventories;
- a nonempty Runtime Option inventory and empty Inference Option inventory;
- an empty Runtime Option inventory and nonempty Inference Option inventory;
- two nonempty inventories with no supplied evidence.

Nonempty inventories do not require edges. An evidence value referencing an
absent endpoint is still invalid.

The mandatory missing-edge meaning is:

```text
Missing edge
=
No supplied positive external compatibility evidence
```

A missing edge does not mean:

- explicit incompatibility;
- Runtime, Inference Option, or Actor unavailability;
- inability to execute; or
- execution prohibition.

No helper or result boolean collapses absence into proven incompatibility.

Some Runtime Options select or bind inference internally or hide it behind an
external Agent definition or managed Agent Service. Such a Runtime Option may
have zero externally selectable Inference Options and therefore no external
edge. Core creates no synthetic internal option, wildcard edge, null endpoint,
ownership field, or managed/unmanaged classification.

---

## 8. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/runtime-inference-compatibility.schema.json`

It validates one evidence object, not a relation wrapper. It requires exactly
the two nonempty string fields and rejects additional properties.

This specification is the semantic authority. The standalone schema cannot
validate endpoint inventories, foreign references, duplicate pairs, relation
ordering, missing-edge meaning, or atomic result behavior. The runtime API owns
those semantic checks by composing the existing inventory validators.

---

## 9. Availability Separation

Compatibility evidence is separate from all availability evidence:

```text
Compatibility evidence
!= Agent Runtime Option available
!= Inference Option available
!= Actor available
```

A positive edge does not claim that either endpoint is currently operational.
The validator does not consume Actor Availability, Agent Runtime Option
Availability, or Inference Option Availability observations and performs no
intersection, freshness, polling, health, capacity, or quota check.

Existing availability Definitions, schemas, normalization, and missing-value
semantics remain unchanged.

The additive Runtime-to-Inference Pair Availability Assessment contract is
defined separately by
`core/runtime-inference-pair-availability-specification.md`. It composes a
validated positive relation with both normalized endpoint-availability results
without changing this standalone compatibility validator or its evidence.

---

## 10. Actor, Selection, Assignment, and Execution Mode Boundaries

Runtime-to-Inference compatibility is not Actor applicability, Actor Selection,
or Assignment. This contract neither defines nor consumes the separate
Actor-to-Runtime Applicability Evidence relation, adds no Actor-to-Inference
relation, and does not change Actor identity, competencies, availability,
selection outcomes, Assignment fields, completeness, or separation evidence.
Human Actors require no Runtime Option or Inference Option. Actor-to-Runtime
semantics are owned by
`core/actor-runtime-applicability-specification.md`.

Compatibility also does not establish Execution Mode satisfaction, reasoning
strength, tool or MCP support, filesystem or shell access, safety, quality,
cost, or latency suitability. It defines no capability registry, model tier,
score, or mode mapping.

An existing Agent Actor selection remains valid independently of whether a
future planner can construct a viable execution configuration.

---

## 11. Configuration, Authority, and Invocation Boundaries

The separation is mandatory:

```text
Compatibility evidence
!= viable execution configuration
!= selected configuration
!= authorized
!= reserved
!= dispatched
!= executing
```

This contract does not select a Runtime Option, Inference Option, Provider, or
model. It does not create an execution-configuration candidate, Agent
Definition, Agent Profile, Agent Service contract, Execution Contract,
permission, session, dispatch, or invocation.

The bounded evidence layers are:

```text
Actor-to-Runtime Applicability Evidence (separate)

Runtime-to-Inference Compatibility Evidence
+ endpoint availability
-> Runtime-to-Inference Pair Availability Assessment

future only:
Actor-to-Runtime applicability + pair availability
-> configuration viability
-> authorization
-> Execution Contract
-> invocation
```

Only Runtime-to-Inference Compatibility Evidence is represented by this
contract. The Actor-to-Runtime relation and pair assessment are separately
defined; configuration viability and every later step remain future work. No
evidence layer authorizes a later one.

---

## 12. Ownership, Persistence, and External Verification

Ownership remains:

```text
Framework
-> relation semantics and validation

Environment/caller
-> endpoint inventories and supplied positive evidence

Future adapter
-> possible discovery or translation of external facts
```

The framework does not independently verify the supplied external claim. The
contract defines no global registry, graph service, repository, database,
cache, history, project-local compatibility file, Project Manifest section,
discovery process, Provider SDK integration, network call, credential, endpoint,
or native configuration field.

Evidence and normalized results remain in memory for one supplied evaluation
context.

---

## 13. Runtime API

Immutable values and pure deterministic validation are defined in:

`engineering_orchestration.runtime_inference_compatibility`

The module exposes:

- `RuntimeInferenceCompatibilityEvidence`
- `RuntimeInferenceCompatibilityFinding`
- `RuntimeInferenceCompatibilityValidationResult`
- `validate_runtime_inference_compatibility`

The validation function takes `evidence`, `runtime_options`, and
`inference_options`, in that order. The result fields are exactly `valid`,
`findings`, and `normalized_evidence`.

---

## 14. Exclusions

The first contract contains no:

- compatibility ID, state, negative evidence, exhaustiveness declaration, or
  compatibility boolean;
- Actor, Provider, model, source, reason, provenance, confidence, timestamp,
  expiry, priority, weight, metadata, or extension field;
- credential, endpoint, native configuration, session, tool, permission, or
  capability field;
- embedded Runtime Option or Inference Option list on either endpoint;
- availability composition inside this compatibility validator, freshness,
  polling, health, capacity, or quota behavior; the separate pair assessment
  may consume normalized endpoint availability without changing this contract;
- Actor applicability input or composition, Actor Selection, Assignment, or
  Execution Mode matching;
- configuration viability, selection, ranking, routing, fallback,
  authorization, reservation, dispatch, execution, or invocation;
- adapter, discovery, network, persistence, registry, graph service, or project
  inventory behavior.

Future contracts may add separate layers only through separately authorized
work. They must not silently change the positive-evidence or missing-edge
semantics defined here.
