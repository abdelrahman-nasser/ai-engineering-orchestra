# AI Engineering Orchestra - Agent Execution Dispatch Admission Specification

Status: Canonical for AIO-047

Version: 0.1.0

Scope: Immutable positive authorization-consumption Admission for one exact
Agent Execution Run and one exact trusted non-widening Tool Binding

---

## 1. Purpose and Category

An **Agent Execution Dispatch Admission** is an immutable serializable record
which, when created or retrieved through the authoritative authorization-domain
admission store, establishes that one operationally trusted Agent Execution
Authorization Grant was current and had no earlier authoritative revocation in
the applicable serial order, and was atomically consumed for one exact Agent
Execution Run and one exact trusted non-widening Agent Operation Tool Binding.

It is a positive historical security fact. It is not a request, decision
input, bearer credential, mutable status, execution attempt, delivery record,
dispatch, invocation, result, or proof of success. The durable operational
claim comes from the configured authoritative store or service boundary, not
from the shape of the value.

```text
direct construction
or schema validity
or intrinsic validity
or serialization round-trip
!= authoritative Agent Execution Dispatch Admission provenance
```

---

## 2. Exact Value Shape

The value contains exactly these fields in this order:

```text
grant
tool_binding
decision_time
```

`grant` is the complete AIO-043 Agent Execution Authorization Grant.
`tool_binding` is the complete AIO-045 Agent Operation Tool Binding.
`decision_time` is the authoritative admission boundary's canonical UTC
decision instant.

There is no Admission ID. There is no status, state, lifecycle, attempt,
request key, result, error, lease, delivery, claim, or metadata field. Full
representation equality is ordinary frozen-value equality over:

```text
(grant, tool_binding, decision_time)
```

---

## 3. Identity and Uniqueness

The natural Admission identity is the complete Grant composite identity:

```text
(
  grant.authorization_domain_id,
  grant.issuer_kind,
  grant.issuer_id,
  grant.grant_id,
)
```

The pair below is a separate authoritative-store uniqueness key:

```text
(grant.authorization_domain_id, grant.run.run_id)
```

Neither key is serialized a second time in the Admission. Grant identity and
authorization-domain/Run uniqueness are operational store constraints; the
pure single-value validator does not claim that no conflicting record exists.
An Admission ID or request idempotency key must not be synthesized.

---

## 4. Exact Run Binding

Every intrinsically valid Admission requires:

```text
grant.run == tool_binding.run
```

For creation of a new authoritative Admission, the trusted coordinator and
store boundary additionally require:

```text
grant.run == tool_binding.run == freshly reconstructed expected Run
```

Fresh reconstruction reuses `grant.run.run_id`; it does not allocate another
occurrence identity. Equality is complete frozen Run equality, including the
entire nested Contract. Equal Run IDs with differing Contracts are not equal
Runs. The Admission contains no alternate Runtime, Inference Option,
environment, operation, resource, Execution Mode, Actor, or Role field through
which the Tool Binding could widen the Run.

---

## 5. Decision Time

`decision_time` is required and uses exactly:

```text
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

It uses ASCII digits, uppercase `T`, uppercase `Z`, Gregorian years `0001`
through `9999`, hours `00..23`, minutes and seconds `00..59`, and exactly six
fractional-second digits. Calendar dates must exist. Numeric offsets, local
times, lowercase markers, missing seconds, absent or non-six-digit fractions,
trailing whitespace, and leap-second `60` are invalid.

The fixed representation is a serialization rule; comparisons use parsed UTC
instants, not lexical strings. The authoritative store owns and persists this
value. It is never supplied by an admission request. Store sampling,
serialization, non-regression, and transaction ordering are defined by the
Agent Execution Dispatch Admission Store specification.

---

## 6. Static Half-Open Interval Coherence

Intrinsic validation requires, over parsed instants:

```text
grant.issued_at <= decision_time < grant.expires_at
```

Issuance is inclusive and expiry is exclusive. A decision exactly at
`issued_at` is coherent; one exactly at `expires_at` is not. Grant timestamps
retain their AIO-043 canonical grammar with an optional one-to-six digit
fraction. Parsing therefore matters when two valid representations denote the
same instant.

This check proves static coherence inside one value. It does not sample a
clock or prove that the supplied `decision_time` came from an authority-owned
clock. Authoritative currentness for a newly created Admission is a store
operation under its serial order.

---

## 7. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_execution_dispatch_admission
```

It defines these frozen public values:

```python
@dataclass(frozen=True)
class AgentExecutionDispatchAdmission:
    grant: AgentExecutionAuthorizationGrant
    tool_binding: AgentOperationToolBinding
    decision_time: str


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionDispatchAdmissionValidationResult:
    valid: bool
    findings: tuple[AgentExecutionDispatchAdmissionFinding, ...]
    admission: AgentExecutionDispatchAdmission | None
```

The exact pure function is:

```python
validate_agent_execution_dispatch_admission(
    admission: AgentExecutionDispatchAdmission,
) -> AgentExecutionDispatchAdmissionValidationResult
```

The package root does not re-export these names. This module has no create,
issue, authenticate, resolve, lookup, revoke, consume, persist, dispatch, or
invoke API.

---

## 8. Intrinsic Validation

A wrong top-level concrete type stops with exactly:

```text
agent_execution_dispatch_admission_invalid_type
```

For an exact Admission, validation proceeds deterministically:

1. delegate complete Grant validation and preserve every nested finding code
   and message;
2. delegate complete Tool Binding validation and preserve every nested finding
   code and message;
3. when both nested values are valid, require exact complete Run equality;
4. parse and validate the fixed canonical `decision_time`; and
5. when the Grant and decision time are valid, enforce the parsed half-open
   interval.

Admission-owned finding codes are:

```text
agent_execution_dispatch_admission_run_mismatch
agent_execution_dispatch_admission_decision_time_invalid
agent_execution_dispatch_admission_currentness_invalid
```

Any finding produces:

```text
valid = false
findings != ()
admission = null
```

Success preserves the exact supplied Admission object. The validator is a pure
deterministic function over supplied values. It does no I/O and consults no
current clock, authority, resolver, revocation state, registry, store, or
mutable process state.

---

## 9. Proof Boundary

Intrinsic validation proves only:

- exact top-level value type;
- complete nested Grant intrinsic validity;
- complete nested Tool Binding intrinsic validity;
- exact Grant/Binding Run equality;
- `decision_time` syntax and calendar validity; and
- static half-open interval coherence over parsed instants.

It does not prove:

- issuer identity, entitlement, authentication, or Grant integrity;
- Tool resolver trust, Tool existence, availability, or behavior;
- that prerequisites, permission, Runtime capability, or Execution Mode were
  freshly recomputed;
- authority-domain ownership or authoritative-store provenance;
- actual current time, clock health, clock non-regression, or clock ownership;
- non-revocation, uniqueness, atomic Grant consumption, commit, durability, or
  exact-retry classification;
- dispatch, invocation, delivery, completion, or success.

An arbitrary decoded or directly constructed value is descriptive data. A
future dispatcher must load the Admission through the configured authoritative
store/service and must not elevate arbitrary bytes based on this validator.

---

## 10. Structural Schema and Offline Resolution

The Draft 2020-12 schema is:

```text
schemas/agent-execution-dispatch-admission.schema.json
```

It is a closed object with exactly the three required properties in canonical
order. `grant` references the canonical Grant schema, `tool_binding` references
the canonical Tool Binding schema, and both reference the existing Run and
Contract schemas transitively. `decision_time` carries the fixed six-digit UTC
pattern.

The packaged loader resolves the complete reference graph from a closed
in-memory registry. Missing resources, canonical-ID mismatches, or unknown
references fail closed without HTTP, HTTPS, network, CWD, active-project, or
external source-checkout fallback.

Schema validation owns JSON structure and timestamp string shape. Runtime
validation owns exact Python types, nested intrinsic semantics, calendar
validity, exact Run equality, parsed interval coherence, and atomic result
construction. Serialization proves neither provenance nor persistence.

---

## 11. Authoritative Provenance and Historical Meaning

Only creation or retrieval through the configured authoritative
authorization-domain Admission store/service can establish operational
provenance. A newly committed Admission records that, at its decision point in
the authoritative serial order, the authenticated Grant was current, no
earlier authoritative revocation existed, uniqueness constraints held, and
Grant consumption plus Admission insertion committed indivisibly.

Later retrieval is recovery of that historical fact. It is not proof that the
Grant remains unexpired or unrevoked, that prerequisites remain satisfied, or
that a fresh dispatch is authorized. A later revocation does not mutate the
Admission.

```text
Admission != continuing permission
Admission != dispatch
Admission != invocation
Admission != success
```

Authorization-consumption replay protection is not invocation replay
protection. A future dispatch-intent/outbox layer may use authoritative
Admissions as input, but no delivery lifecycle belongs in this value.

---

## 12. Scenario Coverage

Focused value and schema coverage establishes, using only synthetic values:

1. the exact three-field frozen shape;
2. full equality and serialization round-trip behavior;
3. delegated Grant and Binding findings;
4. differing Run IDs and same-ID/different-Contract Run mismatches;
5. inclusive issuance and exclusive expiry boundaries;
6. parsed-instant comparison across valid Grant timestamp precisions;
7. fixed decision-time grammar and calendar validation;
8. closed-schema rejection of Admission IDs, state, result, or metadata;
9. offline nested Grant/Binding/Run/Contract reference resolution;
10. fail-closed missing, mismatched, and unknown schema resources;
11. deterministic purity without clock, filesystem, network, database, Tool,
    Provider, Runtime, dispatch, or invocation access; and
12. explicit direct-construction and serialization provenance limitations.

No scenario consumes a real Grant, resolves a real Tool, creates an
authoritative Admission, accesses a protected target, dispatches an Agent, or
invokes a Tool.

---

## 13. Explicit Exclusions and Preservation

This value layer contains no:

- Grant issuance, authentication, signature, key, token, or policy service;
- Tool discovery, probing, resolver implementation, adapter, Provider,
  credential, command, argument, or payload;
- prerequisite collection, AIO-040 composition, Contract/Run preparation, or
  effective-mode resolution;
- current-clock acquisition, skew, fallback, clamping, or non-regression
  state;
- revocation operation or tombstone;
- registry, ledger, persistence, transaction, queue, outbox, or database;
- consumption operation, concurrency control, retry, conflict, or commit
  classification;
- delivery, dispatch, execution, invocation, cancellation, result, error,
  event, usage, cost, or telemetry;
- new Core operation, PostgreSQL backend, AIO-030, AIO-044, Full Control
  Center/UI, or protected-target behavior.

AIO-047 does not alter AIO-040 prerequisite semantics, AIO-041 Contract
semantics, AIO-042 Run semantics, AIO-043 Grant semantics, or AIO-045 Tool
Binding semantics. The separate store contract composes these values without
widening them.
