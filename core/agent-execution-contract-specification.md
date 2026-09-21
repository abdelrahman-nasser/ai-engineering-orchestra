# AI Engineering Orchestra - Agent Execution Contract Specification

Status: Canonical for AIO-041

Version: 0.1.0

Scope: One exact assigned external-inference Agent action

---

## 1. Purpose and Category

An **Agent Execution Contract** is an immutable, provider-neutral,
tool-neutral, serializable Core value declaring one exact intended assigned
external-inference Agent action and its bound, already-resolved effective
Task-wide minimum Execution Mode.

The contract is declarative intent. It is stateless and non-authoritative. It
is not execution readiness, a Permission Decision, authenticated authority, an
authorization grant, an Execution Run, a tool binding, dispatch permission, or
invocation permission.

The following inequalities are mandatory:

```text
Agent Execution Contract
!= execution authorization
!= durable prerequisite satisfaction
!= Execution Run
!= tool binding
!= dispatch
!= invocation
```

Canonical preparation requires one exact observably coherent valid and
`satisfied` AIO-040 Agent Action Prerequisite result plus one explicitly
supplied effective Execution Mode. The value itself creates no authority and
performs no action.

This contract is Agent-only and external-inference-only. Human execution and
Runtime-owned or hidden inference are outside its scope; they are not declared
invalid generally.

---

## 2. Canonical Value and Field Order

`AgentExecutionContract` contains exactly these fields, in order:

| Field | Required | Meaning |
| --- | --- | --- |
| `task_id` | Yes | Exact Task identity from the Assignment |
| `workflow_id` | Yes | Exact Workflow identity from the Assignment |
| `stage_id` | Yes | Exact Workflow Stage identity from the Assignment |
| `role_id` | Yes | Exact Role identity from the Assignment |
| `actor_id` | Yes | Exact assigned Agent Actor identity |
| `runtime_option_id` | Yes | Exact Agent Runtime Option identity |
| `option_id` | Yes | Exact external Inference Option identity |
| `environment_id` | Yes | Exact caller-owned environment identity |
| `operation_id` | Yes | Exact Core operation identifier |
| `resource` | Yes | Exact lexical repository-relative resource |
| `execution_mode` | Yes | Already-resolved effective Task-wide minimum Execution Mode |

The first ten fields directly embed the existing AIO-039/AIO-040 action
subject:

```text
(
  task_id,
  workflow_id,
  stage_id,
  role_id,
  actor_id,
  runtime_option_id,
  option_id,
  environment_id,
  operation_id,
  resource,
)
```

`execution_mode` is required contract context. It is not part of the action
subject and grants no authority.

All values are exact and case-sensitive. Core does not trim, normalize,
case-fold, alias, resolve, or rewrite them. Full eleven-field dataclass equality
defines contract value equality. It does not create instance or lifecycle
identity. Repeated preparation of the same subject and mode intentionally
produces equal values.

There is no contract ID, execution ID, Run ID, attempt ID, correlation
reference, or idempotency key.

---

## 3. Execution Mode Binding

`execution_mode` is exactly one of the existing values in
`EXECUTION_MODE_ORDER`:

```text
lite
standard
deep
critical
```

It means the already-resolved effective Task-wide minimum engineering-
execution posture associated with the intended action. The caller owns Task
and Project-default resolution and supplies the result explicitly.

AIO-041 does not infer mode from Complexity, Risk, Workflow, Stage, Role,
Actor, Runtime Option, or Inference Option. It does not map mode to a Provider,
model, reasoning control, permission, authorization, or security grant.
Changing mode creates a different contract value.

---

## 4. Operation and Resource Binding

The contract carries `operation_id` and `resource` directly; it does not embed
an `OperationRequirement` object. Intrinsic validation projects those two
fields through the existing AIO-036 `OperationRequirement` validator.

The current supported operation remains exactly:

```text
repository_file_read
```

AIO-041 adds no operation and no generic operation payload. Operation syntax,
support, and resource lexical grammar remain owned by AIO-036's shared Core
helpers.

Resource validation is lexical only. It never opens, reads, writes, stats,
hashes, resolves, existence-checks, permission-inspects, or otherwise accesses
the named resource. Lexical validity does not prove existence, physical
containment, permission, authorization, or readability.

---

## 5. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_execution_contract
```

It defines these frozen public values:

```python
@dataclass(frozen=True)
class AgentExecutionContract:
    task_id: str
    workflow_id: str
    stage_id: str
    role_id: str
    actor_id: str
    runtime_option_id: str
    option_id: str
    environment_id: str
    operation_id: str
    resource: str
    execution_mode: str


@dataclass(frozen=True)
class AgentExecutionContractFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionContractValidationResult:
    valid: bool
    findings: tuple[AgentExecutionContractFinding, ...]
    contract: AgentExecutionContract | None
```

The exact public functions are:

```python
validate_agent_execution_contract(
    contract: AgentExecutionContract,
) -> AgentExecutionContractValidationResult


prepare_agent_execution_contract(
    prerequisite_result: AgentActionPrerequisiteResult,
    *,
    execution_mode: str,
) -> AgentExecutionContractValidationResult
```

Annotations state the canonical value types; publicly callable validation
boundaries still check exact concrete types robustly at runtime.
The package root does not re-export these names. There is no serializer helper,
context object, identity type, outcome enum, lookup API, registry, or
persistence API.

---

## 6. Intrinsic Validation

`validate_agent_execution_contract` proves intrinsic value semantics only. It
validates in this fixed category order:

1. exact `AgentExecutionContract` concrete type;
2. the eight opaque identity fields in declaration order;
3. operation and resource through `validate_operation_requirement`; and
4. `execution_mode` against `EXECUTION_MODE_ORDER`.

If the supplied value has the wrong concrete type, validation returns only:

```text
agent_execution_contract_invalid_type
Agent Execution Contract must be an exact AgentExecutionContract value.
```

The eight opaque identities are `task_id`, `workflow_id`, `stage_id`,
`role_id`, `actor_id`, `runtime_option_id`, `option_id`, and `environment_id`.
Each must be an exact nonempty string. Its fixed finding is:

```text
agent_execution_contract_<field>_invalid
Agent Execution Contract <field> must be an exact nonempty string.
```

These findings aggregate in field declaration order. Operation Requirement
findings then pass through with their exact AIO-036 codes, messages,
multiplicity, and order.

Mode findings are exactly:

```text
agent_execution_contract_execution_mode_invalid_type
Agent Execution Contract execution_mode must be an exact string.

agent_execution_contract_execution_mode_not_supported
Agent Execution Contract execution_mode must be one of: lite, standard, deep, critical.
```

An exact string outside the closed vocabulary, including empty, case-varied,
or whitespace-varied text, receives the not-supported finding. No value is
normalized.

Intrinsic validation may prove exact runtime value structure, nonempty opaque
identities, supported operation semantics, lexical resource validity, and a
supported mode. It does not prove:

- canonical preparation occurred;
- AIO-040 was actually run;
- assessor provenance or caller truth;
- reference inventories remain current;
- authority authenticity;
- permission remains current;
- Runtime or Inference Option availability; or
- dispatch or invocation permission.

Public direct construction is intentional. An intrinsically valid copied or
deserialized value has valid intent semantics but no authenticated preparation
provenance.

---

## 7. Canonical Preparation

`prepare_agent_execution_contract` accepts only one exact
`AgentActionPrerequisiteResult` and one explicitly supplied effective mode.
It checks observable AIO-040 invariants but never reruns AIO-034 or AIO-037
through AIO-039.

The fixed preparation category order is:

1. prerequisite result type, coherence, invalid findings, or ordinary outcome;
2. execution mode; and
3. intrinsic validation, only after the first two categories are clean.

Wrong prerequisite result type produces:

```text
agent_execution_contract_prerequisite_result_invalid_type
prerequisite_result must be an exact AgentActionPrerequisiteResult value.
```

An exact result object that violates observable canonical invariants produces:

```text
agent_execution_contract_prerequisite_result_incoherent
prerequisite_result does not satisfy canonical AgentActionPrerequisiteResult invariants.
```

An incoherent result never contributes embedded findings or subject data. A
coherent invalid AIO-040 result contributes its findings with exact code,
message, multiplicity, and order. They are rejection diagnostics only and
create no authority.

A coherent valid `blocked` outcome produces:

```text
agent_execution_contract_prerequisites_blocked
Agent Execution Contract preparation requires prerequisite_result outcome 'satisfied'; received 'blocked'.
```

A coherent valid `unresolved` outcome produces:

```text
agent_execution_contract_prerequisites_unresolved
Agent Execution Contract preparation requires prerequisite_result outcome 'satisfied'; received 'unresolved'.
```

Mode findings follow the prerequisite category and use the same two intrinsic
mode codes and messages.

Preparation succeeds only for this exact ordinary AIO-040 state:

```text
valid = true
findings = ()
outcome = satisfied
reasons = (
  all_currently_modeled_action_prerequisites_satisfied,
)
```

The ten subject values are projected only from that result. The supplied mode
is added as the eleventh field, and the new value is routed through intrinsic
validation.

---

## 8. Observable AIO-040 Coherence

The prerequisite result gate requires:

- the exact `AgentActionPrerequisiteResult` class, not a subclass;
- an exact `bool` `valid` flag;
- exact tuple containers for findings, responsibility key, and reasons where
  applicable;
- exact finding, outcome, and reason value classes;
- nonempty exact-string finding codes and messages;
- coherent atomic invalid shape; or
- coherent valid identity, operation, resource, outcome, and reason shape.

A coherent invalid result has nonempty canonical findings, all subject fields
and `outcome` set to `None`, and `reasons == ()`.

A coherent valid result has no findings; an exact four-part nonempty-string
responsibility key; exact nonempty Actor, Runtime Option, Inference Option, and
environment identifiers; a supported operation; a lexically valid resource;
an exact AIO-040 outcome; and a nonempty exact tuple of AIO-040 reasons.

Non-satisfied reasons must be unique and in AIO-040 declaration order. The two
reasons within each candidate, capability, permission, and authorization
category are mutually exclusive. A blocked outcome requires at least one
blocking reason. An unresolved outcome permits no blocker. A satisfied outcome
requires exactly the singleton positive reason.

These are observable coherence checks only. Public result construction means:

```text
contract canonically prepared
!= assessor provenance authenticated
!= caller truth authenticated
```

Preparation cannot prove that the value was returned by AIO-040, authenticate
external evidence, or establish freshness. Stronger provenance requires a
separately designed future boundary.

---

## 9. Atomicity, Immutability, and Determinism

All three public value classes are frozen dataclasses and findings are tuples.
Inputs are not mutated.

A valid result has:

```text
valid: true
findings: ()
contract: the exact validated or newly prepared AgentExecutionContract
```

An invalid result has:

```text
valid: false
findings: one or more deterministic findings
contract: null
```

Any finding atomically prevents a contract. There is no partial contract,
correction, fallback, normalization, inferred mode, or inferred identity.

Preparation and validation are pure functions of supplied values. They use no
filesystem, network, subprocess, clock, randomness, database, cache,
environment discovery, Runtime probing, Provider discovery, or tool discovery.

---

## 10. Authorization, Staleness, and Future Execution

Contract preparation consumes no authorization and copies no authority or
provenance from AIO-039. The contract stores no candidate, capability,
permission, or authorization state and no AIO-040 outcome, reason, assessment,
or reference.

A contract may be durable as intent, but it carries no durable readiness:

```text
contract remains intrinsically valid
!= prerequisites remain current
```

Any future Run or dispatch design must:

1. freshly resolve the effective Task-wide mode;
2. freshly collect current prerequisite evidence;
3. produce a fresh exact AIO-040 assessment;
4. freshly prepare the eleven-field contract;
5. compare it with intended or stored contract values where appropriate; and
6. obtain separately designed authenticated, Run-bound authority.

Fresh value equality is a necessary condition only. Even a fresh satisfied
AIO-040 result is insufficient for actual invocation. AIO-041 implements none
of the future Run decision, lifecycle, replay, consumption, revocation,
enforcement, dispatch, or invocation behavior.

---

## 11. Serialization and Structural Schema

The Draft 2020-12 structural schema is:

```text
schemas/agent-execution-contract.schema.json
```

It is a closed object with exactly the eleven required fields in canonical
order. Every field is a nonempty string. `execution_mode` additionally has the
four-value enum, and `additionalProperties` is `false`.

The schema owns object shape, required fields, string/nonempty constraints,
the mode enum, and rejection of additional properties. Runtime validation owns
exact Python type robustness, operation syntax and support, lexical resource
semantics, deterministic finding order, coherence, and preparation gating.
The schema intentionally has no operation pattern or enum and no resource path
pattern or format.

Standard mapping and JSON serialization can round-trip the eleven values.
Deserializing into a new contract and passing intrinsic validation can prove
value equality and current intrinsic semantics only:

```text
round-trip success != canonical preparation provenance
```

Core adds no contract repository, persistent store, database, cache, queue, or
history. External transport or storage does not create a Core lifecycle.

---

## 12. Explicit Exclusions

The Agent Execution Contract contains no:

- generic payload, parameters, arguments, body, or data;
- tool, adapter, Provider, model, endpoint, credential, or command binding;
- authority, provenance, authorization state, permission state, capability
  state, prerequisite state, outcome, reason, or assessment reference;
- contract, correlation, idempotency, Run, attempt, or lifecycle identity;
- status, timestamp, freshness, expiry, result, error, token, cost, duration,
  telemetry, metadata, or extension field; or
- Permission Decision, policy composition, mutation, enforcement, dispatch,
  invocation, or execution behavior.

Future operations that require additional arguments must introduce explicit,
typed operation-specific contracts when justified. Tool binding, Run identity,
retry behavior, authorization consumption, replay protection, and execution
lifecycle require separately authorized future contracts.

AIO-042 supplies the first of those contracts without changing this value: an
immutable Agent Execution Run occurrence identity containing one caller-
supplied opaque `run_id` and this exact nested Contract. Canonical Run
preparation freshly reuses this specification's preparation API and requires
exact fresh/intended Contract equality. Run existence still creates no
authority, durable readiness, lifecycle, consumption, binding, dispatch, or
invocation semantics. See `core/agent-execution-run-specification.md`.

---

## 13. Adjacent Contract Preservation

AIO-041 consumes but does not modify:

- AIO-026 Execution Mode semantics and ordering;
- AIO-036 operation vocabulary and resource grammar; or
- AIO-040 diagnostic assessment behavior.

AIO-040 remains diagnostic only. Contract creation is a separate higher layer
and is never performed inside AIO-040. The package root remains unchanged.
