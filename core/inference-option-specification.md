# AI Engineering Orchestra - Inference Option Specification

Version: 0.1.0

This document defines the canonical Inference Option Definition contract for
AI Engineering Orchestra v0.1.

---

## 1. Purpose

An **Inference Option** is a Provider-neutral identity describing one
caller/environment-accessible way to address a model for inference.

It answers only:

> Which inference access option can potentially be invoked?

It does not establish current availability, selection, authorization, runtime
ownership, or execution.

```text
Model
!= Inference Option

Inference Option
!= Runtime Option
!= Agent Service
```

---

## 2. Provider, Model, and Option Boundaries

A **Provider** is the opaque operational access boundary through which a model
is addressed. It need not be the organization that developed the model.

A **Model** is a Provider-addressable inference capability. A model locator is
meaningful only inside its Provider namespace.

An **Inference Option** identifies one accessible operational way to address
that capability. A bare model locator is insufficient because the same logical
model may be exposed through multiple operational surfaces.

A **Runtime Option** would answer where and how the Agent loop executes and who
owns tools, state, sessions, and lifecycle. An **Agent Service** may provide a
managed Runtime Option and may choose models internally. AIO-028 defines neither
concept and includes no runtime or Agent Service field.

---

## 3. Canonical Contract

The v0.1 Inference Option Definition contains exactly these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `option_id` | Yes | Stable opaque identity within one supplied inventory |
| `provider_id` | Yes | Opaque operational Provider/access-boundary identity |
| `model_id` | Yes | Opaque Provider-scoped model locator |

No other field is part of the contract.

```yaml
option_id: primary-engineer-inference
provider_id: provider-a
model_id: model-x
```

All identifiers are required nonempty strings. They are exact, opaque, and
case-sensitive. None requires a UUID or encoded structure.

### `option_id`

`option_id` is the canonical identity within one caller-supplied inventory. It
is not globally unique and must not be parsed as a Provider/model/deployment
tuple.

### `provider_id`

`provider_id` identifies the operational Provider/access boundary. Core defines
no closed Provider vocabulary, Provider object, Provider catalog, or Provider
registry.

### `model_id`

`model_id` is scoped by `provider_id`; there is no global model namespace. Core
does not parse family, version, date, tier, region, lifecycle, or capability
from the value and defines no Model object or catalog.

---

## 4. Supplied Inventory Semantics

The caller supplies an ordinary sequence of definitions. The sequence is an
evaluation input, not a persisted Inventory domain object.

### Unique option identity

`option_id` must be unique within the supplied inventory. Any repeated option
ID produces `duplicate_inference_option_id`, invalidates the complete inventory,
and yields no partial normalized options. Declaration order never creates
first-write-wins or last-write-wins behavior.

### Provider/model pairs are not identity

Multiple options may contain the same `provider_id` and `model_id` pair. Such
definitions are valid when their `option_id` values differ. They can represent
distinct operational configuration or access paths whose native details remain
outside the first contract.

### Determinism

A valid result contains the supplied options ordered by exact case-sensitive
`option_id`. This is deterministic canonicalization, not ranking, routing,
preference, or selection. An empty supplied inventory is valid.

Structural schema validation establishes the three required nonempty fields.
The pure inventory validator consumes normalized values and establishes
cross-definition uniqueness.

---

## 5. Definition and Availability Separation

Inference Option Definition is relatively stable identity. Current operational
availability is separate ephemeral evidence governed by:

`core/inference-option-availability-specification.md`

```text
Inference Option exists
!= available
!= authorized
!= selected
!= executable
```

Availability is never embedded in the definition.

---

## 6. Ownership and Persistence

The framework owns contract semantics and validation. The environment owns
configured access and deployment reality. The caller supplies normalized
definitions for one evaluation context. A future adapter may translate native
Provider configuration into these values.

AIO-028 defines no project-owned option file, Project Manifest section,
database, cache, catalog, history, discovery process, or live Provider call.
Future adapters may map `option_id` to native or secret-bearing configuration
outside this contract.

---

## 7. Security, Authorization, and Execution Boundaries

An Inference Option grants no filesystem, shell, network, credential,
permission, approval, Human Control, or execution authority. The contract never
contains API keys, tokens, secrets, connection strings, authorization headers,
endpoints, or secret-bearing native configuration.

An Inference Option is not an Assignment and does not change Actor identity,
Actor Selection, Assignment, Task Execution Mode, or Quality Gate state. It
does not select a Provider or model, rank options, route traffic, create an
Execution Contract, or invoke inference.

---

## 8. Exclusions

The first contract contains no:

- deployment, endpoint, base URL, resource, region, or credential field
- Provider-specific metadata or untyped extension dictionary
- model family, version, tier, lifecycle, context, output, or modality field
- structured-output, function-tool, hosted-tool, MCP, code-execution, or
  computer-use capability
- streaming, background, reasoning-control, price, quota, access, latency, or
  compliance field
- Runtime Option, Agent Service, session, state-owner, or tool-executor field
- capability registry or Execution Mode capability
- Provider/model discovery, adapter, persistence, selection, routing, fallback,
  authorization, execution contract, or invocation behavior

If capability evidence is later introduced, absent evidence must not silently
mean unsupported. That future pressure does not create capability fields in
this contract.

---

## 9. Runtime API

Immutable values and pure deterministic inventory validation are defined in:

`engineering_orchestration.inference_option`

The runtime API consumes supplied normalized values. It performs no file access,
network access, Provider discovery, persistence, selection, or execution.

---

## 10. Structural Authority

The machine-readable structural schema is:

`schemas/inference-option.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates an inventory invariant or semantic
boundary described here.
