# AI Engineering Orchestra - Agent Runtime Option Specification

Version: 0.1.0

This document defines the canonical Agent Runtime Option Definition contract
for AI Engineering Orchestra v0.1.

---

## 1. Purpose

An **Agent Runtime Option** is an opaque, caller/environment-supplied configured
execution surface through which an Agent execution can be run or delegated.

It identifies the execution/Agent-loop boundary for one evaluation context and
answers only:

> Through which configured execution surface can an Agent execution run or be
> delegated?

A concrete implementation may own or delegate some combination of:

- execution-loop lifecycle
- environment or sandbox
- tools
- state
- sessions
- scheduling
- inference access

The Definition does not claim that every Agent Runtime Option owns all of those
concerns, and none is a field in the v0.1 contract.

After the canonical term has been established, **Runtime Option** is acceptable
short prose. It must not be confused with a Python runtime, .NET runtime,
process, execution ID, session ID, or invocation ID.

---

## 2. Architectural Boundaries

The following concepts remain distinct:

```text
Actor
!= executable Agent definition
!= Agent Runtime Option
!= execution instance

Agent Runtime Option
!= Inference Option
!= Agent Service
!= authorization
!= credentials
```

An **Actor** is logical Human or Agent identity that may fulfill a Role. Actor
answers who; it does not contain an executable Agent definition or runtime
binding.

An **executable Agent definition** would configure instructions, tools, memory,
state, model policy, runtime binding, environment, sessions, or permissions.
AIO-029 defines no such contract.

An **Agent Runtime Option** identifies the configured execution surface. It is
not one execution occurrence, session, invocation, or process.

An **Inference Option** identifies one caller/environment-accessible way to
address a model through a Provider boundary. It answers which configured
inference access identity exists, not where an Agent loop executes.

A **Provider** is an operational access boundary for inference or external
service access. An Agent Runtime Option is the surface running or delegating an
Agent loop. The same external product or service may participate in both
concepts without collapsing their Core identities. The Runtime Option
Definition therefore contains no `provider_id`.

An **Agent Service** is a descriptive external managed implementation that may
expose or realize one or more Agent Runtime Options. It is not a subtype,
schema, or field in AIO-029.

---

## 3. Canonical Contract

The v0.1 Agent Runtime Option Definition contains exactly one field:

| Field | Required | Purpose |
| --- | --- | --- |
| `runtime_option_id` | Yes | Opaque identity within one supplied Runtime Option sequence |

No other field is part of the contract.

```yaml
runtime_option_id: primary-agent-runtime
```

### `runtime_option_id`

`runtime_option_id` is a required nonempty string. It is exact, opaque, and
case-sensitive. It must be unique within one caller-supplied Runtime Option
sequence or evaluation context; it is not a globally registered identifier.

Core does not parse, normalize, trim, case-fold, or infer structure from the
value. It does not encode:

- Actor or executable Agent identity
- Provider, model, or Inference Option identity
- implementation, framework, vendor, or Runtime Option type
- process, execution, session, or invocation identity
- tools, capabilities, sandbox, state, scheduling, or capacity
- endpoint, credential, authorization, or ownership

`runtime_option_id` is preferred over `runtime_id` because the latter may be
mistaken for a process, execution, session, or invocation identifier.

The identity-only contract is useful because it provides:

1. a distinct typed identity for configured Agent execution surfaces;
2. an anchor for Agent Runtime Option availability;
3. an anchor for separate Runtime Operation Capability Observations;
4. an endpoint for separate Runtime-to-Inference Compatibility Evidence; and
5. a future reference for execution-configuration evaluation or dispatch.

The identity itself claims no vendor, implementation, capabilities, tools,
model access, availability, authorization, or execution readiness.

---

## 4. Inventory Validation

One pure validation invocation consumes a caller-supplied sequence of already
structurally valid normalized Agent Runtime Option Definitions. An empty
sequence is valid.

### Unique identity

Every `runtime_option_id` must be unique within the supplied sequence. Duplicate
IDs invalidate the complete inventory. There is no first-wins, last-wins, or
declaration-order precedence.

All duplicated IDs are reported together in exact case-sensitive sorted order
using the stable finding code:

`duplicate_agent_runtime_option_id`

An invalid result contains no partial normalized options.

### Determinism

A valid result contains the supplied definitions sorted by exact
`runtime_option_id`. Sorting is canonicalization for deterministic consumption;
it establishes no preference, priority, ranking, selection, fallback, or
execution order.

The validator performs no discovery, file access, project lookup, network call,
persistence, selection, authorization, dispatch, or execution.

---

## 5. Identity, Availability, and Capability

Agent Runtime Option identity is relatively stable input. Current availability
is separate ephemeral evidence defined by:

`core/agent-runtime-option-availability-specification.md`

```text
Agent Runtime Option Definition
!= Agent Runtime Option Availability Observation

Runtime compatible
!= Runtime available

Runtime available
!= Actor-to-Runtime applicable
!= Inference Option available
!= authorized
!= executing
```

Availability never changes `runtime_option_id` and is never embedded in the
Definition.

Technical support for a Core-defined abstract operation is separate
caller/environment-supplied evidence defined by:

`core/runtime-operation-capability-specification.md`

```text
Agent Runtime Option Definition
!= Runtime Operation Capability Observation

capability present
!= Runtime available
!= permitted
!= authorized
!= executing
```

Capability observations reference the opaque `runtime_option_id`; they do not
add `supported_operations`, capabilities, or tools to this identity-only
Definition.

---

## 6. Actor and Inference Independence

The Runtime Option Definition itself defines no Actor-to-Runtime or
Actor-to-Inference relation. Actor remains exactly `id`, `kind`, and
`competencies`, and Human Actors require no Agent Runtime Option.

The separate Actor-to-Runtime Applicability Evidence contract lets a caller
supply validated positive edges between known Agent Actors and Runtime Options.
It neither embeds Actor IDs in this Definition nor causes Core to independently
verify why an external applicability claim is true. Core defines no global Actor
topology. The canonical relation is defined in
`core/actor-runtime-applicability-specification.md`.

The existing Human path remains unchanged:

```text
Role
-> Human Actor eligibility
-> Human availability
-> Actor Selection
-> Assignment
-> Human execution
```

The Agent direction is layered rather than a direct mapping:

```text
Role
-> Agent Actor eligibility
-> Actor availability
-> logical Agent Actor

logical Agent Actor
+ caller-scoped Agent Runtime Options
-> supplied positive Actor-to-Runtime Applicability Evidence

caller-scoped Agent Runtime Options
+ Runtime availability
+ caller-scoped Inference Options
+ Inference availability
+ supplied positive Runtime-to-Inference Compatibility Evidence
-> Runtime-to-Inference Pair Availability Assessment

Actor-to-Runtime Applicability Evidence
+ Runtime-to-Inference Pair Availability Assessment
-> future configuration viability
```

Actor Selection remains a pure logical selector. A selected Agent may have zero
viable execution configurations at that layer. Runtime availability does not
feed back into Actor Selection; a future higher-level planner may reconsider
Actor candidates when no viable execution path exists.

For Runtime Options exposing external inference selection, future evaluation may
compose an Actor-to-Runtime edge with separate Runtime-to-Inference and pair
availability evidence. AIO-033 does not create a canonical
Actor/Runtime/Inference triple or a viable execution candidate. For
Runtime-owned inference, the two-endpoint applicability relation remains usable
without a synthetic Inference Option.

A separate positive relation is defined by
`core/runtime-inference-compatibility-specification.md`. A Runtime Option may
expose zero externally selectable Inference Options because inference may be
selected internally, bound in an external Agent definition, or hidden behind a
managed Agent Service.

The separate derived composition is defined by
`core/runtime-inference-pair-availability-specification.md`. It assesses only
supplied external edges and does not turn a Runtime without such an edge into a
blocked or non-executable Runtime.

Therefore, absence of Runtime-to-Inference compatibility edges must not be
interpreted as proof that a Runtime Option cannot execute. The many-to-many
compatibility evidence remains a separate relation rather than an embedded list
on either Definition.

---

## 7. Ownership and Persistence

The framework owns contract semantics and validation. The environment owns the
actual configured execution surfaces. The caller supplies normalized
definitions for one evaluation context. A future adapter may translate or
discover native runtime information, but it is not part of AIO-029.

The contract defines no project-owned Runtime Option file, Project Manifest
section, database, registry, catalog, cache, history, discovery service, or live
Provider call. In particular, it creates none of:

- `.ai/runtimes`
- `.ai/runtime-options`
- `.ai/agent-runtimes`

Credentials and secret-bearing native configuration remain external
environment or adapter concerns.

---

## 8. Security, Authorization, and Execution Boundaries

An Agent Runtime Option grants no filesystem, shell, network, credential,
permission, approval, Human Control, or execution authority. Availability and
Runtime Operation Capability Observations do not change that boundary.

Even positive Actor-to-Runtime applicability, Runtime availability, and Inference
Option availability together would not establish authorized execution.

The Definition does not select a Runtime Option, select an Inference Option,
select a model, assess Execution Mode satisfaction, construct an execution
configuration, create an Execution Contract, dispatch an Actor, or invoke an
Agent.

---

## 9. Exclusions

The first contract contains no:

- `kind`, runtime type, vendor, implementation, framework, or managed flag
- Provider, model, Inference Option, Actor, or Agent Definition field
- tools, MCP, filesystem, shell, web, computer use, or capability field
- environment, sandbox, state, session, memory, scheduling, capacity, or load field
- endpoint, credential, token, secret, or connection information
- execution-owner, state-owner, session-owner, or inference-selection-owner field
- Agent Definition, AgentProfile, ActorProfile, or ActorInstance contract
- ExecutionTarget or generic inventory/catalog abstraction
- embedded Actor mapping or Actor-to-Runtime applicability field on the Definition
- embedded option lists or compatibility state on the Definition
- discovery, persistence, selection, routing, fallback, authorization, dispatch,
  execution contract, or invocation behavior

No closed enum of local, managed, remote, SDK, service, vendor, or framework
types is defined.

---

## 10. Runtime API

Immutable values and pure deterministic inventory validation are defined in:

`engineering_orchestration.agent_runtime_option`

The API exposes `AgentRuntimeOptionDefinition`,
`AgentRuntimeOptionFinding`,
`AgentRuntimeOptionInventoryValidationResult`, and
`validate_agent_runtime_option_inventory`.

---

## 11. Structural Authority

The machine-readable structural schema is:

`schemas/agent-runtime-option.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates an inventory invariant or semantic
boundary described here.
