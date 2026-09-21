# AI Engineering Orchestra - Runtime Operation Capability Observation Specification

Version: 0.1.0

This document defines the canonical Runtime Operation Capability Observation
contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

A **Runtime Operation Capability Observation** is an immutable,
caller/environment-supplied observation describing the currently known
technical-support state of one known Agent Runtime Option for one Core-defined
abstract operation within one caller-owned evaluation snapshot.

It answers only:

> What is the currently known technical-support state of this Runtime Option
> for this abstract Core operation in the supplied snapshot?

Core validates the supplied fact. It does not independently discover, probe,
or verify the Runtime.

The qualified term must not be conflated with unqualified Role capabilities,
Actor competencies, or Provider/model features. Runtime Operation Capability
Observation concerns only technical support by one Runtime Option for one Core
operation.

The following separation is mandatory:

```text
capability
!= requirement
!= availability
!= permission
!= authorization
!= execution
```

Capability describes technical support for an operation class in principle.
It does not state that the operation is required, that the Runtime is currently
available, that an environment permits an action against a resource, that a
Human or policy authorizes it, or that execution can or will occur.

---

## 2. Canonical Value and Identity

The observation contains exactly these fields, in order:

| Field | Required | Purpose |
| --- | --- | --- |
| `runtime_option_id` | Yes | Exact reference to one known Agent Runtime Option |
| `operation_id` | Yes | Exact identifier of one Core-defined abstract operation |
| `state` | Yes | Currently known technical-support state |

```yaml
runtime_option_id: primary-agent-runtime
operation_id: repository_file_read
state: present
```

Its exact identity is:

```text
(runtime_option_id, operation_id)
```

Both identity parts are exact and case-sensitive. Core does not trim,
case-fold, normalize, alias, or rewrite them. `state` is not part of identity,
and there is no synthetic capability ID.

### `runtime_option_id`

`runtime_option_id` is a required nonempty string referencing one Definition in
the supplied Agent Runtime Option inventory. An observation never creates or
synthesizes a Runtime Option.

### `operation_id`

`operation_id` is a required nonempty string in serialized values. Its
semantic grammar is the same exact ASCII lower-snake-case grammar used by
Operation Requirement:

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

The current Core vocabulary contains exactly:

```text
repository_file_read
```

The operation vocabulary is shared with Operation Requirement and Environment
Operation Permission Observation through one package-internal Core source of
truth. A capability observation does not contain or synthesize either adjacent
value and does not refer to one particular resource or environment.

### `state`

`state` is required and has exactly these values, in this order:

- `present`
- `absent`
- `unknown`

---

## 3. State Semantics

### `present`

Positive caller/environment-supplied evidence states that the Runtime Option
can technically provide the abstract operation in principle.

It does not identify a concrete tool or implementation, establish current
Runtime availability, grant resource access, or imply permission,
authorization, dispatchability, execution, or success.

### `absent`

Positive caller/environment-supplied evidence states that the Runtime Option
cannot technically provide the abstract operation.

It is explicit technical non-support. It is not Runtime unavailability,
environment denial, lack of Human approval, or a failed invocation.

### `unknown`

No reliable determination of technical support is available in the supplied
snapshot.

Unknown is not absent. A later composition may treat absent as blocking and
unknown as unresolved, but AIO-037 performs no such composition.

---

## 4. Snapshot Validation

One pure invocation consumes a caller-supplied Runtime Option inventory and a
caller-supplied observation iterable. Each iterable is captured exactly once,
and caller inputs remain unmodified.

### Runtime Option inventory

The captured Runtime Option sequence is validated through
`validate_agent_runtime_option_inventory`. Existing inventory diagnostics,
ordering, duplicate handling, and atomicity are preserved. An invalid
foundational inventory invalidates the capability snapshot and yields no
normalized observations. Observation fields are not inspected after that
foundational failure.

### Exact observation values

The runtime API accepts only exact `RuntimeOperationCapabilityObservation`
values. Any other supplied value produces, at most once:

```text
runtime_operation_capability_observation_invalid_type
```

with the fixed message:

```text
Each supplied Runtime Operation Capability Observation must be an exact RuntimeOperationCapabilityObservation value.
```

For exact observation objects, `runtime_option_id` must be an exact nonempty
string, `operation_id` must be an exact string, and `state` must be an exact
`RuntimeOperationCapabilityState` value. A malformed field or state produces,
at most once:

```text
runtime_operation_capability_observation_invalid
```

with the fixed message:

```text
A supplied Runtime Operation Capability Observation contains malformed fields or state.
```

An empty exact-string `operation_id` proceeds to operation syntax validation.
Either foundational observation finding stops relation validation and
normalization.

### Duplicate identities

At most one observation may be supplied for each exact
`(runtime_option_id, operation_id)` pair. Identical-state and conflicting-state
duplicates are equally invalid. Each duplicated exact pair produces one:

```text
duplicate_runtime_operation_capability
```

with the fixed message shape:

```text
Agent Runtime Option '<runtime_option_id>' and Operation ID '<operation_id>' have more than one supplied Runtime Operation Capability Observation.
```

There is no first-wins, last-wins, deduplication, temporal precedence, or
declaration-order preference.

### Runtime references

An observation referencing a Runtime Option absent from the supplied validated
inventory is invalid and uses the established finding code:

```text
agent_runtime_option_not_found
```

with the fixed message shape:

```text
Agent Runtime Option '<runtime_option_id>' was not found in the supplied inventory.
```

One finding is emitted for each distinct unknown Runtime Option ID. No unknown
reference is discarded or synthesized.

### Operation syntax and support

A malformed `operation_id` produces:

```text
operation_id_invalid_syntax
```

with the fixed message:

```text
Runtime Operation Capability Observation operation_id must use ASCII lower_snake_case syntax.
```

One syntax finding is emitted for each distinct malformed operation ID. A
malformed identifier is not support-checked. A well-formed identifier absent
from the Core vocabulary produces:

```text
operation_id_not_supported
```

with the fixed message shape:

```text
Operation ID '<operation_id>' is not supported by Core.
```

One support finding is emitted for each distinct well-formed unsupported
operation ID.

### Deterministic order and atomicity

Runtime validation uses this order:

1. capture the Runtime Option inventory once;
2. capture the supplied observations once;
3. validate the complete Runtime Option inventory;
4. validate exact observation value types, fields, and states;
5. report duplicate exact pairs;
6. report unknown Runtime Option references;
7. report malformed operation identifiers;
8. report well-formed unsupported operation identifiers;
9. when there are no findings, normalize missing known pairs to unknown; and
10. sort normalized output by exact `(runtime_option_id, operation_id)`.

Finding categories follow the order above. Values within one category use exact
case-sensitive sorting. Declaration order never establishes preference.

Any finding invalidates the complete snapshot:

```text
valid: false
findings: nonempty tuple
normalized_observations: ()
```

No invalid result contains partial normalization.

---

## 5. Missing Observations and Canonical Normalization

A valid result contains exactly one normalized observation for every pair in:

```text
known Agent Runtime Options x Core-supported operations
```

A missing pair normalizes to `unknown`, never `absent`. An explicit unknown and
a synthesized unknown are semantically indistinguishable in normalized output;
the minimal contract retains no provenance indicating which form supplied it.
This missing-pair rule is a canonical AIO-037 decision.

With the current one-operation vocabulary, each known Runtime Option receives
one normalized observation. An empty Runtime Option inventory with no supplied
observations is valid and produces an empty normalized tuple. Future explicit
Core vocabulary expansion will add synthesized unknown pairs deterministically.

A valid result has:

```text
valid: true
findings: ()
normalized_observations: complete canonically ordered tuple
```

Normalized observations are ordered by exact case-sensitive
`(runtime_option_id, operation_id)`. Ordering is canonicalization only; it
creates no preference, ranking, selection, routing, or fallback.

---

## 6. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/runtime-operation-capability.schema.json`

It validates one object with exactly the three required fields, nonempty string
IDs, a closed `present`/`absent`/`unknown` state enum, an object root, and no
additional properties.

The schema does not validate Runtime inventory references, operation syntax or
support, duplicates across a sequence, missing-pair normalization, ordering, or
result atomicity. This specification is the semantic authority, and the pure
runtime validator owns those semantic rules.

---

## 7. Ownership and Snapshot Coherence

Ownership remains:

```text
Framework/Core
-> operation vocabulary, state meaning, validation, and normalization

Environment/caller
-> supplied capability truth and evaluation-snapshot coherence
```

The observation is snapshot-scoped rather than eternal Runtime identity. It
contains no timestamp, freshness, expiry, provenance, source, reason, history,
or cache status. Core cannot determine whether a caller improperly reused an
old snapshot.

A future Provider or Runtime adapter may discover native capability facts and
translate them into this contract. Discovery, polling, verification, and
adapter behavior are outside AIO-037.

---

## 8. Requirement, Resource, and Tool Boundaries

Operation Requirement describes demand against one exact resource. Runtime
Operation Capability Observation describes supplied technical support for an
operation class. Environment Operation Permission Observation separately
describes an environment-scoped permission fact for one exact Runtime,
operation, and resource. None implies another, and each may exist
independently. The permission-observation contract is defined in
`core/environment-operation-permission-specification.md`.

Resource is deliberately absent from capability. These later facts can be
coherent together:

```text
capability present for repository_file_read
+ environment permission denied for docs/spec.md
```

Tool identity is also absent. A built-in, host tool, MCP integration, adapter,
or another implementation may realize the abstract operation. AIO-037 neither
selects nor binds any concrete implementation.

The shared operation vocabulary defines abstract Core meaning only. It is not
a tool registry, permission catalog, or execution mechanism.

---

## 9. Availability, Permission, and Authorization Boundaries

Runtime capability and Runtime availability are independent:

```text
capability present
!= Runtime available
```

A capable Runtime may currently be unavailable. An available Runtime may lack
the operation.

Capability also grants no filesystem, shell, network, credential, environment,
permission, approval, Human Control, policy, or execution authority. In
particular:

```text
capability present
!= environment permission allowed
!= Human or policy authorization
!= dispatchable
!= executable
!= execution succeeded
```

No permission or authorization composition occurs in AIO-037. The separately
defined Environment Operation Permission Observation consumes the same Core
operation vocabulary without changing or composing this capability contract.
Agent Action Prerequisite Assessment may privately look up one exact normalized
Runtime/operation pair from a coherent AIO-037 result; it does not change,
revalidate, or extend this observation contract. Its separate derived contract
is defined in `core/agent-action-prerequisite-specification.md`.

---

## 10. Actor, Candidate, and Execution Boundaries

A capability observation does not establish or change:

- Actor identity, competency coverage, or availability;
- Actor-to-Runtime applicability;
- Assignment or Actor Selection;
- Inference Option identity or availability;
- Runtime-to-Inference compatibility or pair availability;
- Agent Execution Candidate Prerequisite Assessment;
- configuration viability, selection, ranking, or reservation;
- Execution Mode satisfaction or Quality Gate state; or
- an Execution Contract, request, dispatch, session, invocation, or execution.

Agent Runtime Option Definition remains identity-only. Operation Requirement
remains demand-only. Agent Runtime Option Availability remains operational
availability-only. AIO-037 changes none of those contracts.

---

## 11. Runtime and Package API

Immutable values and pure deterministic snapshot validation are defined in:

`engineering_orchestration.runtime_operation_capability`

The submodule exposes:

- `RuntimeOperationCapabilityState`
- `RuntimeOperationCapabilityObservation`
- `RuntimeOperationCapabilityFinding`
- `RuntimeOperationCapabilityValidationResult`
- `validate_runtime_operation_capability(observations, runtime_options)`

The exact value and function shapes are:

```python
RuntimeOperationCapabilityObservation(
    runtime_option_id: str,
    operation_id: str,
    state: RuntimeOperationCapabilityState,
)

RuntimeOperationCapabilityFinding(
    code: str,
    message: str,
)

RuntimeOperationCapabilityValidationResult(
    valid: bool,
    findings: tuple[RuntimeOperationCapabilityFinding, ...],
    normalized_observations: tuple[
        RuntimeOperationCapabilityObservation, ...
    ],
)

validate_runtime_operation_capability(
    observations: Iterable[RuntimeOperationCapabilityObservation],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
) -> RuntimeOperationCapabilityValidationResult
```

Runtime values and result containers are frozen and tuple-backed. The package
root does not re-export these names.

The shared package-internal vocabulary is implemented by:

`engineering_orchestration._operation_vocabulary`

It exposes only:

```python
validate_core_operation_id(operation_id: str) -> str | None
supported_core_operation_ids() -> tuple[str, ...]
```

The former returns `None`, `operation_id_invalid_syntax`, or
`operation_id_not_supported`; the latter returns exactly:

```python
("repository_file_read",)
```

Operation Requirement, Runtime Operation Capability, and Environment Operation
Permission Observation validation consume this source of truth without
changing AIO-036 or AIO-037 public behavior.

The validators perform no filesystem or environment inspection, Provider call,
network access, subprocess, clock read, persistence, discovery, polling,
permission change, dispatch, or invocation.

---

## 12. Exclusions

The first contract contains no:

- capability ID, resource, tool ID, Provider, model, environment, timestamp,
  freshness, source, reason, permission, authorization, metadata, or extension
  field;
- Runtime Option capability list or change to Runtime Option identity;
- requirement, availability, permission, authorization, candidate, or
  execution composition;
- concrete tool binding, configuration viability, selection, routing,
  reservation, or Execution Contract;
- discovery, probing, polling, host inspection, adapter, Provider integration,
  persistence, registry, cache, history, Project Manifest field, or CLI; or
- permission change, target access, request, dispatch, execution, or
  invocation.

The separately authorized Environment Operation Permission Observation contract
preserves this contract's technical-support-only meaning and performs no
capability composition. Future authorization or execution-layer contracts
require separately authorized design and must preserve the same boundary.
