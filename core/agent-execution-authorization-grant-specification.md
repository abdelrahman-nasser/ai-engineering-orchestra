# AI Engineering Orchestra - Agent Execution Authorization Grant Specification

Status: Canonical for AIO-043

Version: 0.1.0

Scope: Positive, time-bounded authority artifact for one exact Agent Execution
Run within one authorization domain

---

## 1. Purpose and Category

An **Agent Execution Authorization Grant** is an immutable, serializable,
positive authorization artifact issued through an authenticated authority-
producer boundary, uniquely identified within one authorization domain, bound
to one exact Agent Execution Run, time-bounded, and intended for at most one
future atomic consumption toward dispatch admission.

The concept category is:

```text
Positive authority artifact
```

The Grant itself does not prove current prerequisites, authenticate its issuer,
consume authority, admit dispatch, or perform invocation. The following
separations are mandatory:

```text
Grant != Agent Execution Authorization Evidence
Grant != Permission
Grant != Permission Decision
Grant != Agent Execution Run
Grant != consumption
Grant != dispatch admission
Grant != invocation
```

AIO-043 defines the trustworthy *shape and intrinsic semantics* that a future
consumer may identify and consume. It does not implement the external trust
boundary or the consumer. Grant definition and Grant consumption are separate
foundations.

---

## 2. Canonical Value and Exact Field Order

`AgentExecutionAuthorizationGrant` contains exactly these eight fields, in
this order:

| Field | Required | Meaning |
| --- | --- | --- |
| `grant_id` | Yes | Opaque issuer-allocated issuance identity |
| `run` | Yes | Exact complete nested `AgentExecutionRun` |
| `authorization_domain_id` | Yes | Exact future consumer/audience and shared-ledger domain |
| `issuer_kind` | Yes | Exact issuer category, `human` or `policy` |
| `issuer_id` | Yes | Opaque issuer principal identity |
| `provenance_reference` | Yes | Opaque audit-oriented provenance reference |
| `issued_at` | Yes | Canonical UTC issuance timestamp |
| `expires_at` | Yes | Canonical UTC exclusive expiry timestamp |

No field may be flattened out of `run`, inferred, normalized, or silently
added. In particular, the Grant has no `state`, `consumed`, `used`, `revoked`,
`single_use`, `reusable`, `remaining_uses`, tool, adapter, Provider, dispatch,
result, status, signature, key, algorithm, authentication, metadata, or
extension field.

Full dataclass equality over all eight fields defines representation equality.
It does not prove issuer authenticity, integrity protection, currentness,
non-reuse, or consumption state.

---

## 3. Grant Identity and Grant-ID Ownership

The effective Grant identity is exactly:

```text
(
  authorization_domain_id,
  issuer_kind,
  issuer_id,
  grant_id,
)
```

`run_id` and `provenance_reference` are not Grant identity. `grant_id` is an
exact, opaque, case-sensitive, nonempty string allocated by the external
authenticated authority producer. Core does not generate it and imposes no
UUID, numeric, prefix, or normalization convention.

The producer owns non-reuse within its exact
`(authorization_domain_id, issuer_kind, issuer_id)` namespace. AIO-043 has no
authoritative registry and cannot prove global uniqueness:

```text
grant_id accepted
!= globally unique Grant proven
```

The same lexical `grant_id` may identify independent Grants when the issuer or
authorization domain differs. Within one supplied domain snapshot, reuse of the
complete composite identity for a differing value is an identity-binding
conflict and fails closed.

---

## 4. Exact Run Binding

`run` is the exact nested AIO-042 `AgentExecutionRun`, not a Run ID or a copied
subset. This transitively binds:

- Run ID;
- Task, Workflow, and Stage;
- Role and Actor;
- Runtime Option and Inference Option;
- environment, operation, and lexical resource; and
- the already-resolved Task-wide Execution Mode.

Run ID alone is insufficient because AIO-042 logical identity still requires
the complete immutable Contract binding to detect a Run identity rebound in a
supplied authoritative namespace. The Grant has no separate `run_id` or
`contract` field.

Intrinsic validation delegates the nested value directly to
`validate_agent_execution_run` and preserves every Run finding's code, message,
multiplicity, and order. AIO-043 does not duplicate Run or Contract validation.

---

## 5. Authorization Domain

`authorization_domain_id` is an exact, opaque, case-sensitive, nonempty string.
It identifies the future acceptance audience and shared consumption-ledger
domain in which Grant identity, one-Grant-per-Run constraints, consumption, and
replay state must eventually be authoritative.

It is distinct from the Run Contract's `environment_id`:

```text
authorization_domain_id != environment_id
```

Core never derives one from the other. The domain exists so that one authentic
Grant cannot be independently accepted by execution coordinators maintaining
unrelated consumption ledgers while each believes it owns the single use.
AIO-043 creates no ledger and proves cardinality only inside one explicitly
supplied domain snapshot.

The collection validator therefore requires one explicit
`authorization_domain_id` and rejects every valid Grant whose domain differs.
An empty collection is valid when that supplied domain is valid.

---

## 6. Issuer, Provenance, and External Trust Boundary

`issuer_kind` is exactly one of, in this order:

- `human`
- `policy`

`issuer_id` is an exact, opaque, case-sensitive, nonempty string naming the
issuer principal that the external authentication boundary must bind to the
complete payload. A present issuer ID is not authentication by Core.

AIO-039's `authority_kind` and `authority_id` remain caller-attested evidence
attributes. AIO-043 deliberately uses `issuer_kind` and `issuer_id`; it does
not alias or silently strengthen AIO-039:

```text
AIO-039 granted != Agent Execution Authorization Grant
```

`provenance_reference` is an exact, opaque, case-sensitive, nonempty audit
reference. Core does not dereference it. It is neither Grant identity,
authentication proof, a signature, nor integrity protection.

A Grant may become operationally trusted only when supplied across a real
authenticated and integrity-protected producer boundary. That producer must:

1. authenticate the issuer;
2. establish the issuer's entitlement to issue for the exact domain and Run;
3. bind the authenticated principal to `issuer_kind` and `issuer_id`;
4. bind and integrity-protect all eight Grant fields; and
5. issue within the correct authorization domain.

AIO-043 implements none of those producer responsibilities. Consequently:

```text
direct construction
or schema validity
or intrinsic validity
or serialization round-trip
or provenance_reference
!= authenticated or trusted Grant
```

Core does not issue a Grant, authenticate an issuer, maintain an authority
registry, call a Human UI or policy service, verify a signature, manage a key,
or introspect a bearer token. An `authenticated`, `verified`, or `trusted`
field would remain a caller assertion and is therefore prohibited.

Human Control approval, Task state, review prose, chat, and Git history are
governance evidence, not Grant issuance. Permission Decisions (`allow`, `ask`,
`always-ask`, `deny`) remain separate. Core never parses or converts any of
those values into a Grant.

---

## 7. Positive-Only and Fixed Single-Use Intent

A Grant represents positive authority by existing. It has no internal
`granted`, `denied`, or `unknown` state. Explicit denial remains AIO-039
evidence or future authority-decision state outside this value.

Every Grant has fixed semantic intent for at most one future atomic
consumption. That invariant is not a serialized flag or counter. A Grant cannot
authorize multiple Runs or repeated execution of the same Run. A future
transport retry may retrieve the same durable consumption outcome, but that is
not Grant reuse.

AIO-043 neither consumes nor marks the Grant. Therefore:

```text
Grant exists
!= consumed
!= replay protected
```

There is no `consume`, `redeem`, `mark_used`, mutable consumed state, durable
record, or replay claim.

---

## 8. Grant/Run Cardinality and Conflicts

The v1 relationship is:

```text
one Grant -> exactly one Run
one Run -> zero or at most one accepted Grant per authorization domain
```

Multiple accepted Grants for one Run, Human-plus-policy composition,
replacement, and reissue for the same Run are unsupported. New authority
requires a new Run and new Grant.

Collection validation fails closed and never deduplicates, reconciles, merges,
or selects a winner. Collision classification is:

1. For one composite Grant identity, any differing complete value is one
   `agent_execution_authorization_grant_identity_binding_conflict`; this takes
   precedence over duplicate classification for that identity.
2. Otherwise, repeated identical complete values produce one
   `duplicate_agent_execution_authorization_grant`.
3. Within the supplied domain, equal `run_id` values with differing nested
   Contracts produce one
   `agent_execution_authorization_grant_run_identity_binding_conflict`.
4. Distinct Grant identities targeting one exact Run produce
   `unsupported_multi_authority_agent_execution_authorization_grant` when the
   issuer pairs differ; otherwise they produce
   `unsupported_multiple_agent_execution_authorization_grants_for_run`.

The multi-authority category takes precedence over the ordinary multiple-Grant
category for one exact Run. There is no first-, last-, latest-, Human-, policy-,
shorter-expiry-, longer-expiry-, quorum-, majority-, or stricter-wins rule.

The collision categories are emitted in stable order: exact duplicate, Grant
identity binding, Run identity binding, unsupported multiple Grants, then
unsupported multi-authority. Keys sort lexically and case-sensitively inside a
category.

---

## 9. Time Syntax, Ordering, and Currentness

Both `issued_at` and `expires_at` are required strings using exactly:

```text
YYYY-MM-DDTHH:MM:SS[.fraction]Z
```

The grammar uses ASCII digits, uppercase `T`, uppercase `Z`, Gregorian years
`0001` through `9999`, hours `00..23`, minutes and seconds `00..59`, and an
optional one-to-six digit fractional second. Calendar dates must exist. Local
times, numeric UTC offsets, lowercase markers, spaces, missing seconds, empty
fractions, fractions longer than six digits, and leap-second `60` are invalid.

The pure validator enforces only static syntax, calendar validity, and:

```text
issued_at < expires_at
```

Equal or reversed timestamps are invalid. No maximum lifetime or skew policy is
defined.

Operational validity would require a future trusted-clock check equivalent to:

```text
issued_at <= trusted_now < expires_at
```

AIO-043 never obtains `trusted_now` and never calls a system clock API:

```text
time-bounded Grant != currently valid Grant proven
```

Revocation is likewise absent. Future revocation must be a trusted immutable
authority-state record or online trusted result composed correctly with
consumption and admission.

---

## 10. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_execution_authorization_grant
```

It defines these frozen public values:

```python
@dataclass(frozen=True)
class AgentExecutionAuthorizationGrant:
    grant_id: str
    run: AgentExecutionRun
    authorization_domain_id: str
    issuer_kind: str
    issuer_id: str
    provenance_reference: str
    issued_at: str
    expires_at: str


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantValidationResult:
    valid: bool
    findings: tuple[AgentExecutionAuthorizationGrantFinding, ...]
    grant: AgentExecutionAuthorizationGrant | None


@dataclass(frozen=True)
class AgentExecutionAuthorizationGrantCollectionValidationResult:
    valid: bool
    findings: tuple[AgentExecutionAuthorizationGrantFinding, ...]
    normalized_grants: tuple[AgentExecutionAuthorizationGrant, ...]
```

The exact public functions are:

```python
validate_agent_execution_authorization_grant(
    grant: AgentExecutionAuthorizationGrant,
) -> AgentExecutionAuthorizationGrantValidationResult


validate_agent_execution_authorization_grant_collection(
    grants: Iterable[AgentExecutionAuthorizationGrant],
    *,
    authorization_domain_id: str,
) -> AgentExecutionAuthorizationGrantCollectionValidationResult
```

The package root does not re-export these names. There is no issue,
authenticate, currentness, lookup, consumption, revocation, persistence,
dispatch, or invocation API.

---

## 11. Intrinsic Validation

A wrong top-level concrete type stops with exactly:

```text
agent_execution_authorization_grant_invalid_type
```

For an exact Grant, findings aggregate in eight-field declaration order:

1. exact nonempty `grant_id`;
2. exact nested Run intrinsic findings;
3. exact nonempty `authorization_domain_id`;
4. exact `human | policy` `issuer_kind`;
5. exact nonempty `issuer_id`;
6. exact nonempty `provenance_reference`;
7. canonical and calendar-valid `issued_at`;
8. canonical and calendar-valid `expires_at`; then
9. static ordering when both timestamps parsed.

The Grant-owned field codes are:

```text
agent_execution_authorization_grant_grant_id_invalid
agent_execution_authorization_grant_authorization_domain_id_invalid
agent_execution_authorization_grant_issuer_kind_invalid
agent_execution_authorization_grant_issuer_id_invalid
agent_execution_authorization_grant_provenance_reference_invalid
agent_execution_authorization_grant_issued_at_invalid
agent_execution_authorization_grant_expires_at_invalid
agent_execution_authorization_grant_time_order_invalid
```

Any finding produces:

```text
valid = false
findings != ()
grant = null
```

Success preserves the exact supplied Grant object. Intrinsic validation proves
only currently defined value semantics. It does not prove producer provenance,
issuer entitlement, authentication, payload integrity, currentness,
cardinality outside supplied data, consumption, or replay safety.

---

## 12. Collection Validation

Collection validation captures the caller iterable exactly once and never
mutates the caller or supplied values. A non-iterable produces
`agent_execution_authorization_grant_collection_invalid`. An invalid supplied
domain produces
`agent_execution_authorization_grant_collection_authorization_domain_id_invalid`.

It then applies these dependency-aware phases:

1. intrinsic validation for every captured item;
2. exact authorization-domain matching;
3. composite Grant-identity duplicate/conflict classification;
4. Run-ID/Contract binding checks;
5. exact-Run Grant cardinality and multi-authority checks; and
6. canonical normalization only when every earlier phase is clean.

Foundational invalid inputs stop before relationship interpretation. Intrinsic
collection findings sort deterministically by exact code and message.
Distinct mismatched domain values produce
`agent_execution_authorization_grant_domain_mismatch` in exact lexical order.

Valid output contains the exact supplied objects ordered by:

```text
(
  authorization_domain_id,
  issuer_kind,
  issuer_id,
  grant_id,
)
```

Declaration order and timestamps never create preference. Invalid output is
atomic:

```text
valid = false
findings != ()
normalized_grants = ()
```

An empty iterable with a valid explicit domain produces a valid empty tuple.
This is an in-memory validation result, not a Grant registry, acceptance
decision, or ledger.

---

## 13. Structural Schema and Serialization

The Draft 2020-12 structural schema is:

```text
schemas/agent-execution-authorization-grant.schema.json
```

It is a closed object with exactly the eight required properties in canonical
order. `issuer_kind` is the exact `human | policy` enum. Identifier fields are
nonempty strings. Timestamp properties carry the locked canonical UTC pattern.
`run` references the canonical AIO-042 schema identifier:

```text
https://ai-engineering-orchestra.dev/schemas/agent-execution-run.schema.json
```

The Run and Contract properties are not duplicated. The packaged loader uses a
closed in-memory registry containing the Run schema and its transitive Contract
schema. It defines no generic retriever. Missing, mismatched, or unregistered
references fail closed without HTTP, HTTPS, network, CWD, active-project, or
external source-checkout fallback.

Schema validation owns JSON structure and the timestamp string shape. Runtime
validation owns exact Python types, nested intrinsic semantics, calendar
validity, time ordering, domain scope, collisions, cardinality, canonical
ordering, and atomicity.

Standard mapping and JSON serialization may round-trip exact value equality,
but:

```text
serialization success
!= issuer authenticated
!= Grant currently valid
!= Grant consumed
```

Serialization creates no persistence or store.

---

## 14. Adjacent Contracts and Future Admission

AIO-039 remains caller-attested positive or negative evidence. It has no Grant
identity, Run binding, expiry, authenticated producer, single-use intent, or
consumption semantics. AIO-043 neither changes nor upgrades it.

AIO-040 remains diagnostic prerequisite composition. Blocked, unresolved, or
later-changed prerequisites do not become Grant state. Grant existence does not
make an old prerequisite result current.

AIO-041 remains immutable declarative intent. AIO-042 remains immutable Run
occurrence identity with no Grant, authorization, consumed state, or lifecycle.
AIO-043 sits above the complete Run without modifying it.

A future separately authorized admission layer must combine, at minimum:

- an operationally trusted Grant received from the authenticated producer;
- exact expected domain and complete Run equality across the Grant, one valid
  AIO-045 Agent Operation Tool Binding, and the freshly prepared expected Run;
- trusted current time and any explicit revocation result;
- freshly satisfied prerequisites and permission state;
- an exact immutable/version-stable `tool_id` supplied by the external trusted
  resolver without widening any field of the Run Contract; and
- durable atomic Grant consumption coordinated with dispatch admission.

The required equality is:

```text
binding.run == grant.run == freshly prepared expected Run
```

Tool Binding must succeed before the single-use Grant is consumed, and neither
intrinsic nor schema validity proves Tool existence, trust, availability,
executability, or semantic behavior. Ordering must prevent dispatch before
successful consumption. Crash, no-response, transaction failure, concurrent
consumers, retries, and Tool failure around consumption require durable
semantics. AIO-043 and AIO-045 implement and claim none of them.

---

## 15. Scenario Boundary

The required scenario coverage establishes, without dispatch or invocation:

- a Run or AIO-039 `granted` evidence can exist without a Grant;
- an intrinsically valid Run-bound Grant remains unauthenticated;
- a Grant for another Run or the same Run ID with another Contract is not
  authority for the expected complete Run;
- exact duplicates, Grant-identity rebounds, Run-identity rebounds, multiple
  Grants for one Run, and Human/policy composition fail closed;
- a short valid lifetime is intrinsically valid while currentness remains
  unknown, and missing expiry is structurally invalid;
- expiry-at-current-time, clock skew, revocation, permission changes, fresh
  prerequisite changes, and mode mismatch are not converted into Grant logic;
- at-most-one-use intent does not implement consumption, replay protection,
  crash recovery, concurrent-worker safety, or durable retry outcomes;
- provenance, direct construction, or serialization cannot establish trust;
- bearer-token and signed-Grant models are absent; and
- Grant existence implies neither admission, invocation, nor success.

All examples and tests use synthetic lexical resources. Read-only and write-
operation replay remain equally outside this foundation; the current Core
operation vocabulary does not widen for AIO-043.

The complete investigated scenario disposition is:

1. A Run without a Grant remains a Run only.
2. AIO-039 `granted` evidence without a Grant remains evidence only.
3. An intrinsically valid Run-bound Grant proves intrinsic semantics only.
4. A Grant for another Run cannot authorize the expected Run.
5. Equal Run ID with another Contract is a Run identity-binding conflict.
6. A Grant carries intent for one future atomic consumption only.
7. Supplying the same complete Grant twice is an invalid duplicate.
8. Two-worker consumption requires a future durable atomic consumer.
9. Rebinding one composite Grant identity to another Run is invalid.
10. Two distinct Grants for one exact Run/domain are invalid.
11. Human and policy Grants for one Run/domain cannot be composed.
12. Whether the current time is past expiry cannot be decided here.
13. Revocation is not modeled.
14. Consumption followed by a crash requires future durable semantics.
15. Future ordering must prohibit dispatch before successful consumption.
16. Future admission must reject Tool Binding failure before consumption.
17. Tool Binding success followed by consumption failure is a future concern.
18. Blocked fresh prerequisites do not become Grant logic.
19. Unresolved fresh prerequisites do not become Grant logic.
20. A later permission change is not disproved by Grant existence.
21. A fresh mode mismatch remains a Run/preparation issue.
22. A future consumption transport retry does not mean Grant reuse.
23. No response after consumption requires a future durable outcome record.
24. Concurrent consumption requires future serialization or transactions.
25. No persistence means no replay guarantee.
26. Transaction failure semantics remain future work.
27. An in-memory store could not claim durability.
28. A forged directly constructed Grant remains unauthenticated.
29. A composite Grant-identity collision fails closed.
30. An unauthenticated issuer is not operationally trusted.
31. Provenance cannot establish trust.
32. No bearer-token model is implemented.
33. No signed-Grant model is implemented.
34. A pre-verified external authenticated producer boundary is required.
35. A missing expiry is structurally invalid.
36. A short correctly ordered lifetime is valid while currentness is unproven.
37. Read-only invocation replay remains outside Grant validation.
38. Write-operation replay remains outside Grant validation.
39. The protected target is never used.
40. Grant existence does not mean consumption occurred.
41. Dispatch admission is absent.
42. Grant existence does not imply execution success.

---

## 16. Purity, Persistence, and Explicit Exclusions

Both validators are deterministic pure functions over supplied values. They
perform no filesystem or protected-target access, network access, subprocess
invocation, current-clock access, randomness, database/cache/queue/store
access, authority lookup, signature or key operation, token introspection,
policy evaluation, permission mutation, tool discovery, dispatch, or
invocation.

AIO-043 contains no:

- Grant issuance or issuer authentication;
- authority registry, signature, key, algorithm, certificate, bearer token, or
  network authority service;
- currentness, clock-skew, maximum-lifetime, or revocation evaluation;
- registry, persistence, database, cache, queue, ledger, repository, or
  transaction;
- consumption, replay protection, mutable used state, or reusable semantics;
- Permission Decision or permission enforcement;
- tool, adapter, Provider, endpoint, credential, command, parameter, or payload
  binding;
- dispatch admission, dispatch, execution, invocation, result, error, event,
  usage, cost, or telemetry;
- Run lifecycle, cancellation, retry mechanics, or state transition; or
- AIO-030, AIO-044, Full Control Center/UI, or protected-target behavior.

Any such capability requires separate explicit authorization and a new
contract with its own architecture, security, validation, review, and Human
Control requirements.
