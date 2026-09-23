# AI Engineering Orchestra - Agent Execution Run Specification

Status: Canonical for AIO-042

Version: 0.1.0

Scope: Identity for one concrete attempt involving one exact Agent Execution
Contract

---

## 1. Purpose and Category

An **Agent Execution Run** is an immutable, provider-neutral, tool-neutral,
serializable Core value identifying one concrete attempt to progress one exact
Agent Execution Contract toward execution. It binds one caller-supplied opaque
`run_id` immutably to the exact nested Contract.

Creating a Run does not authorize, dispatch, start, or complete the action. The
Run is occurrence identity only. It is not a lifecycle entity, mutable record,
state snapshot, event stream, execution result, readiness decision, or authority
grant.

The following inequalities are mandatory:

```text
Agent Execution Run
!= authorization consumed
!= replay protected
!= permission current
!= lifecycle state
!= tool bound
!= dispatch started
!= invocation
!= execution success
```

This contract is Agent-only and external-inference-only because its nested
Agent Execution Contract has that boundary. Human execution and Runtime-owned
or hidden inference remain outside its scope; they are not invalid generally.

---

## 2. Canonical Value and Field Order

`AgentExecutionRun` contains exactly these fields, in order:

| Field | Required | Meaning |
| --- | --- | --- |
| `run_id` | Yes | Exact caller-supplied opaque occurrence identity |
| `contract` | Yes | Exact nested immutable `AgentExecutionContract` value |

The Contract is nested directly. Its eleven fields are not flattened, copied,
projected, or duplicated in the Run. AIO-042 introduces no Contract ID, hash,
reference, lookup, or mutation.

Full dataclass equality over `(run_id, contract)` defines Run representation
equality. Logical occurrence identity is `run_id`. These statements are related
but distinct:

```text
same run_id + same Contract
-> the same Run represented again

same run_id + different Contract
-> identity-binding conflict in an authoritative namespace

same Contract + different run_id
-> distinct Runs
```

A single-value validator cannot observe another value in an external namespace
and therefore cannot detect a cross-value Run-ID collision. Core adds no Run
inventory or registry in AIO-042.

---

## 3. Run-ID Ownership and Syntax

`run_id` is an exact concrete nonempty string. It is opaque and case-sensitive.
Core does not trim, normalize, case-fold, parse, resolve, or rewrite it.
Consequently, any exact nonempty string, including a whitespace-containing,
whitespace-only, prefixed, numeric-looking, or UUID-looking value, satisfies the
intrinsic string rule. No spelling establishes provenance or authenticity.

The caller or execution coordinator owns:

- allocation;
- namespace choice;
- operational non-reuse; and
- collision handling outside single-value validation.

Core does not generate Run IDs and uses no UUID generator, randomness, clock,
timestamp, numeric sequence, content hash, or Contract-derived identity.

Therefore:

```text
run_id accepted
!= globally unique occurrence proven
!= authenticated occurrence proven
```

Global uniqueness would require a shared allocator or authoritative registry
and persistence. Those mechanisms are outside AIO-042.

---

## 4. Attempt and Retry Semantics

One Run denotes one semantic execution attempt. There is no separate
`attempt_id`.

A semantic retry of an action requires a new `run_id` and new canonical Run
preparation. A transport retry that merely re-sends the same occurrence retains
the same Run ID and exact Contract.

AIO-042 adds no retry API, count, policy, backoff, parent relation,
`previous_run_id`, `retry_of`, lineage, or idempotency key. Future authorization
or retry policies may restrict whether another Run for an equal Contract can
progress; this identity foundation does not.

---

## 5. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_execution_run
```

It defines these frozen public values:

```python
@dataclass(frozen=True)
class AgentExecutionRun:
    run_id: str
    contract: AgentExecutionContract


@dataclass(frozen=True)
class AgentExecutionRunFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionRunValidationResult:
    valid: bool
    findings: tuple[AgentExecutionRunFinding, ...]
    run: AgentExecutionRun | None
```

The exact public functions are:

```python
validate_agent_execution_run(
    run: AgentExecutionRun,
) -> AgentExecutionRunValidationResult


prepare_agent_execution_run(
    intended_contract: AgentExecutionContract,
    prerequisite_result: AgentActionPrerequisiteResult,
    *,
    execution_mode: str,
    run_id: str,
) -> AgentExecutionRunValidationResult
```

Annotations state canonical types; public boundaries still check exact concrete
types robustly at runtime. The package root does not re-export these names.
There is no serializer helper, status enum, context value, identity generator,
lookup API, inventory API, registry, persistence API, dispatch API, or lifecycle
API.

---

## 6. Intrinsic Validation

`validate_agent_execution_run` proves intrinsic value semantics only. A wrong
top-level concrete type stops validation with exactly:

```text
agent_execution_run_invalid_type
Agent Execution Run must be an exact AgentExecutionRun value.
```

For an exact Run, findings aggregate in this fixed category order:

1. `run_id`; and
2. nested Agent Execution Contract intrinsic findings.

An invalid Run ID produces:

```text
agent_execution_run_run_id_invalid
Agent Execution Run run_id must be an exact nonempty string.
```

The nested value is passed directly to
`validate_agent_execution_contract`. Every Contract finding is converted to an
`AgentExecutionRunFinding` while preserving its exact code, message,
multiplicity, and order. AIO-042 does not duplicate Contract validation.

Intrinsic validation may prove exact Run type, the opaque nonempty Run-ID rule,
and current intrinsic Contract semantics. It does not prove:

- canonical Run preparation occurred;
- parent evidence was newly collected or remains current;
- the effective mode was freshly resolved;
- assessor provenance or caller truth;
- authority authenticity or authorization consumption;
- Run-ID authenticity, global uniqueness, or non-reuse;
- current permission, Runtime availability, or Inference availability;
- lifecycle state, tool binding, dispatch, invocation, or success.

Public direct construction is intentional. A copied or deserialized value may
be intrinsically valid without having canonical preparation provenance.

---

## 7. Canonical Preparation

Canonical preparation consumes:

```text
one intended AgentExecutionContract
+ one caller-supplied fresh AgentActionPrerequisiteResult
+ one caller-supplied freshly resolved effective Execution Mode
+ one caller-supplied run_id
```

It performs these deterministic categories in order:

1. validate `run_id`;
2. intrinsically validate `intended_contract`;
3. call `prepare_agent_execution_contract` directly with the supplied
   prerequisite result and mode; and
4. only when the first three categories are clean, require exact equality
   between freshly prepared and intended Contracts.

The first three independent categories aggregate findings in that order.
AIO-041 findings retain their exact code, message, multiplicity, and order.
Contract inequality produces only:

```text
agent_execution_run_contract_mismatch
Freshly prepared Agent Execution Contract must exactly equal intended_contract.
```

Mismatch is not added when either Contract is invalid or unavailable. Any
finding produces no Run. Only exact equality across all eleven Contract fields
permits construction. The successful Run binds the exact supplied intended
Contract object and is routed through intrinsic Run validation.

Blocked, unresolved, invalid, incoherent, and wrong-type prerequisite results
produce no Run through the reused AIO-041 preparation semantics. An invalid or
unsupported mode likewise produces no Run. There is no fallback,
normalization, field substitution, inferred identity, or inferred mode.

---

## 8. Freshness and TOCTOU

Canonical preparation requires a fresh prerequisite result and freshly resolved
effective mode. **Fresh** means the caller collected new or current parent
observations and evidence and then produced the supplied AIO-040 result. Calling
AIO-040 again over knowingly cached parent result containers does not establish
freshness.

AIO-042 receives only supplied values. It cannot authenticate collection time,
temporal truth, snapshot simultaneity, assessor provenance, or continued
currency. A raw candidate Run ID may be allocated before checks, but allocation
alone is not a canonical Run. Canonical construction occurs only after fresh
AIO-041 preparation and exact Contract equality succeed.

Facts may change immediately afterward:

```text
canonical Run prepared
!= prerequisites remain current
```

TOCTOU is therefore unsolved. A future separately authorized dispatch-admission
layer must use another just-in-time assessment or trusted bounded evidence and
must define atomic authorization consumption and dispatch admission. A
timestamp alone cannot close the race.

---

## 9. Authorization and Non-Execution Boundary

Run preparation consumes no authorization and copies no AIO-039 authority or
provenance into the Run. AIO-039 `granted` remains a caller-attested,
unauthenticated assertion. Its `provenance_reference` remains opaque provenance;
it is not a grant, authorization, token, consumption, or replay identity.

Run identity is necessary for Run-bound authority but is not sufficient for
replay safety. AIO-043 adds a separate immutable Agent Execution Authorization
Grant containing the complete nested Run, issuer/domain-scoped Grant identity,
static lifetime, and fixed single-use intent. It does not change this Run value
and does not implement producer authentication, currentness, durable atomic
consumption, or crash and ambiguous-dispatch semantics. See
`core/agent-execution-authorization-grant-specification.md`.

Both Run APIs are non-executing. They do not bind a concrete tool, adapter,
Provider, model, endpoint, credential, command, parameter, or payload. They do
not dispatch or invoke anything and produce no result, error, output, event, or
telemetry.

---

## 10. Atomicity, Immutability, and Purity

All three public values are frozen dataclasses and findings are tuples. Inputs
are not mutated.

A valid result is exactly:

```text
valid = true
findings = ()
run = the exact validated or newly prepared AgentExecutionRun
```

An invalid result is exactly:

```text
valid = false
findings != ()
run = null
```

There is no partial Run. Validation and preparation are deterministic pure
functions over supplied values. They perform no filesystem or protected-target
access, network access, subprocess invocation, clock access, randomness,
database/cache/queue/store access, environment discovery, Runtime or Provider
probing, schema loading, policy evaluation, permission or authorization
mutation, tool discovery, dispatch, or invocation.

---

## 11. Serialization and Structural Schema

The Draft 2020-12 structural schema is:

```text
schemas/agent-execution-run.schema.json
```

It is a closed object with exactly two required properties in canonical order:
`run_id` and `contract`. `run_id` is a string with `minLength: 1`. `contract`
uses `$ref` to the canonical AIO-041 schema identifier:

```text
https://ai-engineering-orchestra.dev/schemas/agent-execution-contract.schema.json
```

The eleven Contract properties are not duplicated. Runtime validation owns
exact Python type robustness and semantic validation; the schemas own JSON
structure.

The packaged schema loader resolves this reference from explicit bundled
resources through a closed in-memory registry. It defines no generic remote
retriever. Missing or unknown references fail closed and never trigger HTTP,
HTTPS, network, CWD, active-project, or external source-checkout lookup.

Source checkout, editable installation, and normal wheel installation expose
the same direct module and packaged schemas. Standard mapping and JSON
serialization can round-trip the nested value, but:

```text
round-trip success
!= canonical preparation provenance
!= global Run-ID uniqueness
!= execution authority
```

Serialization creates no Core persistence, registry, database, cache, queue,
repository, or history store.

---

## 12. Lifecycle and Adjacent Boundaries

Run identity and lifecycle are separate foundations. The Run has no status—not
even `created`—and existence is not a lifecycle state. AIO-042 defines no
transition owner or state machine and no pending, ready, running, succeeded,
failed, cancelled, expired, started, or completed value.

Cancellation request and acknowledgement, failure, retry mechanics, results,
and events require future contracts grounded in real runtime and dispatch
ownership. Any future lifecycle evidence must use immutable Run identity as its
anchor without mutating the two-field Run value.

AIO-045 Agent Operation Tool Binding nests this exact complete Run, not bare
`run_id`, together with one immutable/version-stable configured implementation
identity. Complete nesting preserves the Contract binding and prevents a Tool
Binding from altering the Assignment, Runtime Option, Inference Option,
environment, operation, resource, or Execution Mode. The binding remains
non-authoritative and non-executing. A future Execution Result should likewise
reference the Run rather than adding output to this identity value. Event and
telemetry vocabularies follow stable lifecycle and invocation semantics.

---

## 13. Explicit Exclusions and Preservation

AIO-042 contains no:

- lifecycle, status, transition, mutable record, snapshot, or event sourcing;
- `attempt_id`, retry count, retry lineage, parent Run, or idempotency key;
- timestamp, clock, duration, freshness, expiry, or temporal ordering;
- persistence, registry, database, cache, queue, repository, or history store;
- Contract ID, Contract hash, flattened Contract field, or Run-ID generator;
- authenticated authority, grant/token identity, authorization consumption,
  replay protection, revocation, Permission Decision, enforcement, or mutation;
- tool, adapter, Provider, model, endpoint, credential, command, payload, or
  parameter binding;
- cancellation, failure, result, error, output, event, cost, token usage,
  duration, or telemetry; or
- dispatch, execution, invocation, protected-target access, AIO-030, or Full
  Control Center behavior.

AIO-042 consumes but does not modify AIO-040 diagnostic assessment semantics or
AIO-041 Contract meaning and public behavior. AIO-043 nests this exact Run in a
separate Grant without adding Grant, consumed, or authorization state to the
Run. AIO-045 separately nests this exact Run in an Agent Operation Tool Binding
without adding Tool state, authority, discovery, admission, or invocation to
the Run. Any future lifecycle, authorization-consumption, replay, dispatch,
invocation, result, event, telemetry, or persistence contract requires separate
explicit authorization.
