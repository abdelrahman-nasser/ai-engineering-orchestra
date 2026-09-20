# AI Engineering Orchestra - Actor-to-Runtime Applicability Specification

Version: 0.1.0

This document defines the canonical Actor-to-Runtime Applicability Evidence
contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

**Actor-to-Runtime Applicability Evidence** is an immutable, caller-supplied
positive evidence value stating that one known Agent Actor may use one known
Agent Runtime Option within the supplied evaluation context.

It answers only:

> Which supplied positive Actor-to-Runtime applicability edges does the caller
> report for this evaluation context?

Applicability is topology evidence. It is not availability, selection,
Assignment, authorization, or execution. Core validates the supplied claim but
does not independently verify the external fact. The contract has no provenance
field, and its absence must not be interpreted as independent verification.

After the canonical term has been established, **applicability evidence** and
**applicability relation** are acceptable short prose for the supplied values
and their exact edges.

---

## 2. Endpoint and Identity Boundaries

Each evidence value references one definition from each existing endpoint
context:

- `actor_id` references an Actor with exact `kind: agent`.
- `runtime_option_id` references an Agent Runtime Option Definition.

The endpoint contracts remain owned by:

- `core/actor-specification.md`
- `core/agent-runtime-option-specification.md`

Actor remains exactly `id`, `kind`, and `competencies`. Agent Runtime Option
Definition remains exactly `runtime_option_id`. The relation is separate from
both endpoints. Actor gains no Runtime list, and Runtime Option gains no Actor
list.

Both references are required, nonempty, opaque, exact, and case-sensitive. Core
does not trim, normalize, case-fold, parse, rewrite, or infer structure from
them. No identifier requires a UUID, prefix, framework name, vendor name, or
other pattern.

---

## 3. Canonical Value

The v0.1 Actor-to-Runtime Applicability Evidence value contains exactly:

| Field | Required | Purpose |
| --- | --- | --- |
| `actor_id` | Yes | Exact reference to one supplied Agent Actor |
| `runtime_option_id` | Yes | Exact reference to one supplied Agent Runtime Option Definition |

```yaml
actor_id: agent-engineer-1
runtime_option_id: primary-agent-runtime
```

The exact edge identity is:

```text
(actor_id, runtime_option_id)
```

There is no `applicability_id`. The endpoint pair is sufficient identity within
one caller-supplied relation and evaluation context.

---

## 4. Positive Agent-Only Many-to-Many Relation

The caller supplies an ordinary iterable of evidence values. That iterable is
evaluation input, not a persistent graph or Inventory domain object.

The relation is many-to-many. For example, all of these distinct edges may be
valid together:

```text
A1 -> R1
A1 -> R2
A2 -> R1
```

One Agent Actor may apply to multiple Runtime Options, and one Runtime Option may
support multiple Agent Actors. There is no one-to-one restriction, preferred or
default Runtime, automatically chosen endpoint, exhaustiveness claim, ranking,
routing, or fallback order.

Only a known Actor whose exact schema-valid kind is `agent` may be an edge
endpoint. A known Human Actor is a valid Actor but is not a valid endpoint for
this relation. This restriction does not change Human competency, availability,
selection, Assignment, or approval semantics, and Human Actors do not require a
Runtime Option.

---

## 5. Input Capture and Foundational Validation

One pure validation invocation consumes:

1. caller-supplied applicability evidence;
2. a caller-supplied Actor context; and
3. a caller-supplied Agent Runtime Option Definition inventory.

The public function accepts those arguments in that order. It captures each
input exactly once in this fixed operational order:

1. Actors;
2. Runtime Options;
3. applicability evidence.

This permits one-shot iterables and prevents later reads from observing a
different supplied sequence. Individual Actor mappings are expected to have
passed `actor.schema.json`; individual applicability values and Runtime Option
Definitions are likewise expected to have passed their structural contracts.

### Actor context

Core validates the existing Actor-context uniqueness invariant locally without
creating an Actor Inventory, registry, catalog, or service. Duplicate exact
Actor IDs produce one finding:

`duplicate_actor_id`

The exact message is:

```text
Actor IDs must be unique in the supplied context; duplicates: <sorted IDs>
```

All duplicated IDs are listed in exact case-sensitive order, separated by
comma and space.

### Runtime Option inventory

Core invokes `validate_agent_runtime_option_inventory` on the captured Runtime
Option tuple. It preserves that validator's findings, codes, messages, ordering,
normalization, and atomicity. In particular, duplicate Runtime IDs retain:

`duplicate_agent_runtime_option_id`

Both foundational checks run. Actor-context findings precede Runtime-inventory
findings. If either foundation is invalid, relation fields are not inspected,
the result is invalid, and no normalized evidence is returned.

---

## 6. Relation Validation

With valid foundations, relation findings are accumulated in this fixed
category order.

### Duplicate exact edges

Every exact pair must be unique. Each distinct duplicated pair produces:

`duplicate_actor_runtime_applicability`

The exact message is:

```text
Actor '<actor_id>' and Agent Runtime Option '<runtime_option_id>' have more than one supplied applicability evidence value.
```

Duplicated pairs are sorted by exact `(actor_id, runtime_option_id)`. There is no
first-wins, last-wins, implicit deduplication, or declaration-order precedence.

### Known Actor references

Every `actor_id` must resolve exactly in the valid Actor context. Each distinct
unknown Actor ID produces:

`actor_not_found`

The exact message is:

```text
Actor '<actor_id>' was not found in the supplied Actor context.
```

Unknown Actor findings are sorted by exact Actor ID. Core does not synthesize an
Actor, infer a kind, drop an edge, or partially normalize the relation.

### Agent Actor endpoints

Each distinct referenced known Human Actor ID produces:

`actor_runtime_applicability_requires_agent_actor`

The exact message is:

```text
Actor '<actor_id>' has kind 'human'; Actor-to-Runtime Applicability Evidence requires an Agent Actor endpoint.
```

Human-endpoint findings are sorted by exact Actor ID. Under the Actor structural
contract, `human` is the only non-Agent kind. An unsupported kind is structurally
invalid input and outside this semantic validator's normalized-input precondition.

### Known Runtime Option references

Every `runtime_option_id` must resolve exactly in the validated Runtime Option
inventory. Each distinct unknown Runtime Option ID produces:

`agent_runtime_option_not_found`

The exact message is:

```text
Agent Runtime Option '<runtime_option_id>' was not found in the supplied inventory.
```

Unknown Runtime findings are sorted by exact Runtime Option ID.

### Complete finding order

With valid foundations, finding categories always appear as:

1. duplicated exact applicability pairs;
2. unknown Actor IDs;
3. known Human Actor IDs;
4. unknown Runtime Option IDs.

This category order and exact identifier sorting make results independent of
declaration order. Source position never establishes preference or precedence.

---

## 7. Canonicalization and Atomicity

A valid result contains the supplied unique evidence ordered by exact:

```text
(actor_id, runtime_option_id)
```

Ordering exists only for deterministic representation. It is not preference,
ranking, routing, fallback, selection, authorization, or execution order.

Any foundational or relation finding invalidates the complete result. The
invalid-result convention is:

```text
valid: false
normalized_evidence: ()
```

Core returns no partially accepted relation and does not mutate Actor, Runtime,
or evidence inputs. Public values are frozen, and result collections are tuples.

---

## 8. Empty Relation and Missing-Edge Semantics

An empty applicability relation is valid whenever both endpoint contexts are
valid. This includes empty, mixed empty/nonempty, and two nonempty endpoint
contexts. Nonempty endpoint contexts do not require edges. Evidence referencing
an absent endpoint remains invalid.

The mandatory missing-edge meaning is:

```text
Missing Actor-to-Runtime edge
=
No supplied positive applicability evidence
```

A missing edge does not mean incompatible, unavailable, unauthorized, unable to
execute, or permanently unsupported. The contract contains no negative state,
boolean, score, confidence, or exhaustiveness declaration.

---

## 9. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/actor-runtime-applicability.schema.json`

It validates one evidence object, not a relation wrapper. It requires exactly
the two nonempty string fields and rejects additional properties.

This specification is the semantic authority. JSON Schema does not validate
endpoint inventories, foreign references, Actor kind, duplicate pairs, relation
ordering, missing-edge meaning, or atomic result behavior. The runtime API owns
those semantic checks while reusing Runtime Option inventory validation.

---

## 10. Availability and Inference Independence

Applicability evidence is independent from all availability evidence:

```text
Actor-to-Runtime applicability
!= Actor availability
!= Runtime availability
!= Runtime-to-Inference pair availability
```

The validator consumes no availability observations and performs no freshness,
polling, health, capacity, quota, or availability composition.

It also consumes no Inference Option and creates no Actor-to-Inference edge or
Actor/Runtime/Inference triple. Runtime-to-Inference Compatibility Evidence and
Runtime-to-Inference Pair Availability Assessment remain separate contracts. An
applicable Runtime may own inference internally and need no externally supplied
Runtime-to-Inference edge.

---

## 11. Selection, Assignment, and Planning Boundaries

Applicability does not select or assign an Actor or Runtime. Actor Selection and
Assignment remain responsibility decisions, and Assignment gains no
`runtime_option_id`. A valid Assignment does not prove Runtime applicability; a
valid applicability edge does not create an Assignment.

The relation has no Task, Workflow, Stage, Role, Complexity, Risk, or Execution
Mode input. It does not establish Task/Role suitability, mode fit, runtime
capability, tool support, filesystem or shell access, MCP access, permission,
credential presence, Human approval, safety, quality, cost, or latency fitness.

The separation is mandatory:

```text
applicable
!= available
!= selected
!= preferred
!= authorized
!= reserved
!= dispatched
!= executing
```

Agent Execution Candidate Prerequisite Assessment may consume the complete
validated relation and ask whether its one exact assigned-Actor-to-Runtime edge
was supplied. A missing edge contributes unresolved evidence and retains the
meaning defined here. That separate composition is defined in
`core/agent-execution-candidate-prerequisite-specification.md`.

Broader viability, selection, ranking, routing, fallback, authorization,
Execution Contract construction, dispatch, and invocation remain future work.

---

## 12. Ownership, Persistence, and External Verification

Ownership remains:

```text
Framework
-> value semantics, deterministic validation, normalization

Environment/caller
-> endpoint contexts and supplied positive applicability claims

Future adapter
-> possible discovery or translation of external facts
```

The caller owns context coherence, truth, and freshness. Core does not
independently verify the claim and defines no global registry, graph service,
repository, database, cache, history, project-local applicability file, Project
Manifest section, discovery process, Provider integration, network call,
credential, environment-variable contract, or native runtime configuration.
Evidence and results remain in memory for one supplied evaluation context.

---

## 13. Runtime API

Immutable values and pure deterministic validation are defined in:

`engineering_orchestration.actor_runtime_applicability`

The module exposes:

- `ActorRuntimeApplicabilityEvidence`
- `ActorRuntimeApplicabilityFinding`
- `ActorRuntimeApplicabilityValidationResult`
- `validate_actor_runtime_applicability`

The validation function takes `evidence`, `actors`, and `runtime_options`, in that
public argument order. The result fields are exactly `valid`, `findings`, and
`normalized_evidence`. The package root does not re-export these names.

---

## 14. Exclusions

The first contract contains no:

- applicability ID, negative state, compatibility boolean, completeness claim,
  provenance, confidence, timestamp, priority, weight, metadata, or extension;
- Task, Workflow, Stage, Role, Inference Option, Provider, model, tool,
  permission, credential, endpoint, session, or native configuration field;
- Actor schema, Runtime Option schema, Assignment, Selection, or availability
  change;
- Actor-to-Inference relation or Actor/Runtime/Inference triple;
- Task suitability, Execution Mode fit, capability or permission assessment;
- candidate viability, selection, ranking, routing, fallback, authorization,
  reservation, dispatch, execution, or invocation;
- adapter, discovery, network, filesystem, process, clock, environment access,
  persistence, registry, cache, CLI, or Project Manifest behavior.

Future contracts may add separate layers only through separately authorized
work. They must not silently change the positive-evidence or missing-edge
semantics defined here.
