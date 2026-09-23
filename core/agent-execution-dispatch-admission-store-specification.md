# AI Engineering Orchestra - Agent Execution Dispatch Admission Store Specification

Status: Canonical for AIO-047

Version: 0.1.0

Scope: Trusted coordination and backend-neutral authoritative storage for
atomic Grant consumption and Agent Execution Dispatch Admission

---

## 1. Purpose and Security Category

The **Agent Execution Dispatch Admission Store** is the authoritative,
authorization-domain-bound serialization boundary that atomically consumes
one operationally trusted Agent Execution Authorization Grant by creating one
immutable Agent Execution Dispatch Admission.

The canonical protocol name is:

```text
AgentExecutionDispatchAdmissionStore
```

The Store is not a general database abstraction, Grant producer, Tool
resolver, policy engine, dispatcher, invocation engine, Run lifecycle store,
delivery queue, or result store. Its bounded operation is:

```text
authenticated complete Grant
+ trusted complete Tool Binding
+ freshly reconstructed exact expected Run
-> authoritative serialization
-> one durable Admission or one typed non-Admission outcome
```

The Admission row or equivalent immutable record is the consumption fact.
There is no separate mutable `consumed` flag or state transition.

Mandatory inequalities are:

```text
Admission created != dispatch occurred
Admission created != Tool invocation occurred
Admission created != operation succeeded
authorization-consumption replay protection != invocation replay protection
```

---

## 2. Trusted Coordinator Boundary

`AgentExecutionDispatchAdmissionCoordinator` is the sole untrusted-facing
orchestration boundary in AIO-047. The Store protocol is authority-internal.
It is not exposed as a bearer API and its request objects are not credentials.

The coordinator receives only a presented Grant value for Admission, lookup,
or revocation. Admission accepts no caller-supplied:

- trust or authentication boolean;
- trusted wrapper or serialized provenance assertion;
- Tool Binding;
- AIO-040 result;
- effective Execution Mode;
- expected Run;
- decision time; or
- retry/idempotency key.

Configured typed ports establish the operational boundaries:

| Port | Responsibility |
| --- | --- |
| `AgentExecutionAuthorizationGrantAuthenticationPort` | Authenticate a presented complete Grant through the configured producer boundary |
| `AgentOperationToolBindingResolverPort` | Resolve one trusted immutable, non-widening complete Tool Binding |
| `FreshAgentActionPrerequisiteSourcePort` | Newly collect the parent values consumed by AIO-040 |
| `EffectiveExecutionModeResolverPort` | Freshly resolve the effective Task-wide Execution Mode |
| `OriginalIssuerRevocationAuthenticationPort` | Authenticate the original issuer for a revocation request |

The output of calling a configured port is the trust boundary. No value field,
wrapper, `provenance_reference`, spelling, serialized object, or
`trusted: true` / `authenticated: true` flag establishes that trust.
AIO-047 supplies only the ports and synthetic tests. Real Grant-producer and
Tool-resolver integrations remain absent and are blocking prerequisites for
operational use.

`AgentActionPrerequisiteParentInputs` is a frozen transport container for the
five AIO-040 parent inputs and `environment_id`. Direct construction of that
container proves no freshness. Freshness derives only from the configured
source integration collecting current values for this coordinator call.

---

## 3. Authority-Internal Requests

The coordinator mints opaque, exact-type authority-internal request objects
only after the applicable trust and intrinsic checks. Store implementations
open them through package-internal accessors that verify a module-private
object-identity marker. The request categories carry:

| Operation | Exact semantic payload |
| --- | --- |
| Guarded history | Expected domain, complete Grant, complete Tool Binding |
| New Admission | Expected domain, complete Grant, complete Tool Binding, freshly reconstructed complete expected Run |
| Authoritative lookup | Expected domain, complete Grant, complete trusted Tool Binding |
| Revocation | Expected domain, complete original-issuer-authenticated Grant |

The new-Admission request contains no time and no prerequisite outcome. An
arbitrary object, directly constructed look-alike, decoded JSON value, or
caller-supplied boolean must fail as `invalid_input`.

This encapsulation prevents accidental bypass inside the configured
application composition. It is deliberately not claimed as a security
boundary against arbitrary code executing in the same Python process. A real
deployment must keep the authority-internal Store behind the configured
process or service boundary and must not expose private mint/open helpers to
untrusted extensions.

---

## 4. Protocol Operations

The backend-neutral protocol has exactly four semantic operations:

```python
class AgentExecutionDispatchAdmissionStore(Protocol):
    def classify_guarded_history(request) -> StoreResult: ...
    def admit_or_return_existing(request) -> StoreResult: ...
    def load_authoritative_admission(request) -> StoreResult: ...
    def revoke_or_return_existing(request) -> StoreResult: ...
```

### 4.1 Guarded history classification

`classify_guarded_history` determines whether the exact complete Grant and
Binding already produced an authoritative Admission. It is available only
after Grant authentication, intrinsic Grant and Binding validation, configured
domain equality, and exact `grant.run == tool_binding.run` have succeeded.

The backend must verify its active authoritative ledger, configured domain,
schema/integrity state, canonical payload decoding, stored index/payload
agreement, complete Grant equality, and complete Tool Binding equality before
returning an Admission. It returns the original `decision_time`.

An exact historical return performs no:

- new clock sample;
- currentness evaluation;
- revocation evaluation;
- parent-evidence collection;
- AIO-040/041/042 recomputation; or
- time-watermark advance.

This exception is necessary so a committed outcome remains recoverable after
response loss, expiry, later revocation, or prerequisite change.

`no_existing_admission` is an authority-internal continuation outcome. The
top-level Admission operation never returns it as a final decision.

### 4.2 Admit or return existing

`admit_or_return_existing` enters the backend's writer serialization point and
repeats history/conflict classification. This in-transaction recheck permits a
concurrent winner to be returned as `existing_exact_admission`.

If no exact history exists, the Store must atomically own:

1. active-ledger and configured-domain validation;
2. safe canonical decoding and integrity validation;
3. Grant-identity, Binding, and domain/Run conflict classification;
4. exact three-way Run equality recheck;
5. revocation ordering;
6. one authoritative clock sample;
7. Grant currentness and non-regression evaluation;
8. Grant composite and domain/Run uniqueness enforcement; and
9. immutable Admission insertion as the consumption fact.

The required equality is:

```text
grant.run == tool_binding.run == freshly_reconstructed_expected_run
```

The expected Run must reuse `grant.run.run_id`. No alternate Run ID may be
allocated for Admission.

### 4.3 Authoritative load

`load_authoritative_admission` is the future-consumer read boundary. The
coordinator first authenticates and intrinsically validates the complete Grant,
checks the domain, resolves and intrinsically validates the trusted complete
Binding, and requires Grant/Binding Run equality. The Store then loads by the
Grant composite identity and checks complete stored Grant and Binding equality
before disclosure.

An equal directly constructed or deserialized Admission remains descriptive
only. Operational authority derives from creation or retrieval through the
configured authoritative Store for that domain.

### 4.4 Revoke or return existing

`revoke_or_return_existing` records an immutable internal tombstone containing
the complete Grant after the configured original-issuer port authenticates it.
The tombstone identity is the complete Grant composite identity. AIO-047 adds
no public serialized Revocation value or schema, domain-admin revocation,
delegation, or multi-authority composition.

Admission and revocation share one serialization order:

```text
revocation commits first -> a new Admission is rejected as revoked
Admission commits first -> Admission remains historical; revocation is recorded
```

A later revocation never mutates, deletes, or invalidates an existing
historical Admission.

---

## 5. Coordinator Algorithm

For Admission, the coordinator performs the following order:

1. call the configured Grant authentication port;
2. intrinsically validate the exact returned Grant;
3. require its domain to equal the configured expected domain;
4. call the configured trusted Tool Binding resolver;
5. intrinsically validate the exact returned complete Binding;
6. require exact Grant/Binding Run equality;
7. call guarded history classification;
8. return exact committed history immediately, or stop on any conflict/failure;
9. only when history is absent, newly collect parent inputs;
10. call AIO-040 itself over those parent values;
11. require a valid `satisfied` AIO-040 result;
12. freshly resolve the effective Execution Mode;
13. call AIO-041 and require exact Contract equality with `grant.run.contract`;
14. call AIO-042 using the same prerequisite result, mode, intended Contract,
    and `grant.run.run_id`;
15. require exact three-way complete Run equality; and
16. issue the authority-internal Admission request.

The coordinator never accepts a serialized or freely constructed `satisfied`
AIO-040 result from its caller. Calling AIO-040 again does not by itself prove
freshness; the configured source integrations own the bounded currency of
their newly collected parent facts.

Trust, intrinsic validation, expected-domain checks, and exact Grant/Binding
Run equality precede every Admission-history lookup or disclosure. Expected
failures from configured Store operations are returned as typed results.
Malformed Store results or mismatched returned payloads fail closed as
`integrity_failure`.

---

## 6. Identity, Uniqueness, and Conflict Precedence

The Admission natural identity is the Grant composite:

```text
(
  grant.authorization_domain_id,
  grant.issuer_kind,
  grant.issuer_id,
  grant.grant_id,
)
```

The Store separately enforces uniqueness of:

```text
(
  grant.authorization_domain_id,
  grant.run.run_id,
)
```

The latter is a cardinality constraint, not an Admission ID. There is no
Admission ID and no request idempotency key.

Conflict precedence is fixed:

1. same Grant composite identity but different complete Grant:
   `grant_identity_conflict`;
2. same complete Grant but different complete Tool Binding:
   `binding_conflict`; and
3. different Grant targeting an already admitted domain/Run identity:
   `run_conflict`.

Same complete Grant plus same complete Tool Binding is exact retry and returns
the historical Admission. Stored corruption, duplicate rows violating schema
invariants, noncanonical payload, or index/payload disagreement is always
`integrity_failure`, never an ordinary conflict.

---

## 7. Currentness, Authoritative Time, and Non-Regression

Currentness for a new Admission is evaluated inside the authoritative Store
serialization point with parsed instants and the half-open predicate:

```text
grant.issued_at <= decision_time < grant.expires_at
```

`decision_time` is Store-owned and never request-supplied. The local backend
uses `AgentExecutionDispatchAdmissionClock.now_utc()` only after acquiring its
writer serialization and completing the in-transaction history/conflict
recheck. The returned instant must be UTC-aware and valid. Store persistence
emits the canonical fixed form:

```text
YYYY-MM-DDTHH:MM:SS.ffffffZ
```

Clock unavailability, exceptions, naive/non-UTC values, invalid values, or
lossy conversion fail closed as `clock_failure`. There is no caller-time or
system-time fallback.

Within one active authorization-domain generation, a new authoritative
decision time may equal but must never precede the persisted last decision
watermark. Regression fails closed as `clock_regression`; time is never
clamped or replaced and there is zero implicit skew tolerance.

The following committed decisions advance the watermark atomically:

- `newly_admitted`;
- the first `newly_revoked` tombstone;
- `not_yet_current`;
- `expired`; and
- `revoked`.

Trust/validation failures, domain/conflict outcomes, exact history, clock
failure/regression, and Store/integrity failures do not advance it. AIO-047
does not persist durable request-bound denial receipts; an ambiguous negative
decision may be safely reevaluated but its exact original response is not
recoverable.

---

## 8. Operational Outcome Taxonomy

`AgentExecutionDispatchAdmissionStoreOutcome` is a closed typed vocabulary.

Positive Admission outcomes:

```text
newly_admitted
existing_exact_admission
```

Positive revocation outcomes:

```text
newly_revoked
existing_exact_revocation
```

Authority-internal continuation:

```text
no_existing_admission
```

Security, currentness, and conflict outcomes:

```text
not_yet_current
expired
revoked
domain_mismatch
grant_identity_conflict
binding_conflict
run_conflict
```

Coordinator rejection outcomes:

```text
invalid_input
unauthenticated_grant
untrusted_tool_binding
unsatisfied_prerequisites
```

Infrastructure or indeterminate outcomes:

```text
storage_busy
storage_unavailable
incompatible_schema
integrity_failure
clock_failure
clock_regression
commit_unknown
```

`AgentExecutionDispatchAdmissionStoreResult` contains exactly one outcome,
one typed retry disposition, an optional Admission, and a nonempty diagnostic
detail. Only the two positive Admission outcomes carry an intrinsically valid
Admission. All other outcomes carry none. Diagnostic detail is not a stable
programmatic identity and must not disclose unauthorized history.

Outcome validity is operation-specific as well as globally shaped. Guarded
history and authoritative load cannot report newly created, temporal,
revocation, clock, or commit outcomes. Admission creation cannot report a
revocation success. Revocation cannot report an Admission, a currentness
result, a Binding conflict, or a Run conflict. The coordinator converts any
well-formed but operation-incoherent Store result to `integrity_failure`
rather than propagating it across the authority boundary.

---

## 9. Retry Taxonomy

`AgentExecutionDispatchAdmissionStoreRetryDisposition` replaces a boolean
retry flag:

| Disposition | Meaning |
| --- | --- |
| `no_retry_needed` | The operation has a positive result, or guarded history is absent and coordinator processing may continue |
| `retry_exact_request` | Retry the exact complete request against the same pinned ledger after bounded busy/transient failure or `commit_unknown` |
| `retry_at_or_after_issuance` | Retry `not_yet_current` only at or after the Grant issuance instant |
| `recollect_fresh_state` | Collect new parent evidence and resolve mode again; do not blindly loop an unsatisfied prerequisite result |
| `retry_after_remediation` | Schema, integrity, or clock failure requires explicit remediation before retry |
| `reconcile_administrative_state` | An explicit administration operation crossed an ambiguous durable point; inspect and reconcile only the same configured path and destination |
| `do_not_retry_same_request` | Expiry, revocation, conflict, invalid input, or failed trust makes the same request unsuitable |

After `commit_unknown`, an exact retry must target the same pinned ledger and
must use the same complete Grant and Tool Binding. It must not choose another
Store, ledger, domain, or backend. The Store then returns exact history,
performs one new attempt if none committed, or returns a conflict/failure.

---

## 10. Administrative Outcomes

Provisioning, migration, fencing, and consistent-backup operations are
explicit administration, not ordinary Admission decisions. Their typed
`AgentExecutionDispatchAdmissionStoreAdministrationOutcome` vocabulary is:

```text
provisioned
already_current
migrated
fenced
fenced_backup_created
migration_failure
storage_busy
storage_unavailable
incompatible_schema
integrity_failure
commit_unknown
```

The corresponding result has one typed retry disposition and diagnostic
detail. Successful administration needs no retry and a busy result permits an
exact same-operation retry. Administrative storage unavailability and
migration, compatibility, or integrity failures require remediation. An
administrative `commit_unknown` uses `reconcile_administrative_state`: inspect
and reconcile only the same configured path, domain, ledger identity, and
destination. It never authorizes a fallback ledger or destination.

Fencing idempotently recognizes its already-fenced terminal state, and
migration may recognize an already-current schema. Provisioning and backup do
not attribute an arbitrary pre-existing path to a prior ambiguous attempt, so
their reconciliation may require explicit operator inspection. This narrower
administrative rule does not weaken operational Admission/revocation
`commit_unknown`, which still requires exact retry against the same pinned
ledger with the same complete Grant and Binding.

The operational four-method Store protocol does not provision, create,
migrate, repair, activate, change storage profiles, fence, back up, restore,
or fall back. Backend-specific explicit administration APIs own those actions.

---

## 11. Backend Conformance Requirements

Every conforming backend must provide equivalent semantics for:

- exact Grant and Binding historical retry;
- conflict precedence and both uniqueness constraints;
- writer-serialized currentness, revocation, and first Admission creation;
- authoritative Store-owned time and non-regression;
- revocation-first and Admission-first race orders;
- exact retry after response loss and `commit_unknown`;
- restart durability;
- bounded busy and unavailable outcomes;
- active-domain, schema/version, decoding, and integrity failure closure; and
- authoritative retrieval without trusting arbitrary Admission bytes.

These semantics are exercised through a backend-neutral reusable conformance
harness. A backend supplies only its fresh-store, clock-control, concurrency,
and unavailable-storage adapter. The same scenario methods run against the
official SQLite backend in AIO-047 and are intended to run unchanged against a
future PostgreSQL implementation. Backend-specific hard-crash, migration,
corruption, and backup tests remain additional evidence.

A reusable conformance suite may use a synthetic in-memory model solely to
exercise coordinator/protocol behavior. Such a model is not a production
backend, persistence fallback, recovery path, or operationally authoritative
Store. Backend-specific concurrency, crash, migration, corruption, and backup
tests remain additional requirements.

PostgreSQL and central/multi-machine services are deferred. A future backend
must implement this semantic protocol without importing SQLite-specific SQL,
PRAGMAs, file paths, or transaction APIs into the Core protocol.

---

## 12. Official Local SQLite Realization Boundary

The AIO-047 SQLite implementation is the only supported local backend. It is
restricted to one dedicated ledger on supported local storage for one
correctly owned authorization-domain context and same-host multiprocess use.
It has a pinned domain, ledger-instance identity, and positive generation.
There is no memory, temporary, alternate-file, recreation, network-share,
cloud-sync, replicated-writer, multi-machine, or copy-as-failover fallback.

Operational open must use an already provisioned compatible active ledger and
must not create, migrate, repair, activate, or silently change its storage
profile. Explicit administration owns forward-only, checksummed migration and
one-way `active -> fenced` transitions. A supported consistent backup is
published only after the backup destination is made permanently fenced and
validated. AIO-047 provides no same-domain restore/reactivation path.

Open-time verification of schema, metadata, migration history, watermark, and
all security payloads uses one consistent SQLite read snapshot. It must not
mix autocommit reads across a concurrent valid append. Admission and revocation
write paths repeat full verification under their `BEGIN IMMEDIATE`
serialization; new Admission also repeats the complete request and exact
three-way Run invariant after its in-transaction history/conflict recheck.

Database-contained identity, generation, and fencing cannot detect a manually
substituted stale active copy or prevent manually copied active ledgers from
operating independently. Global stale-restore, failover, migration, and
split-ledger prevention require a future external ownership/generation
authority. Raw active-file copying is unsupported.

The backend's exact SQLite version floor, durability profile, DDL, migration
manifest, schema fingerprint, canonical JSON codec, and file checks are
implementation-owned conformance mechanisms rather than protocol fields.

---

## 13. Failure and Exception Boundary

Expected operational failures are typed results, not booleans. The backend
must fail closed on unsupported or incompatible schema, dirty or partial
migration state, checksum/fingerprint disagreement, corruption, malformed or
noncanonical stored payload, duplicate JSON keys, non-finite values, identity
index mismatch, unavailable clock, regression, storage errors, or ambiguous
commit outcome.

No failure may silently:

- trust caller time;
- select another ledger;
- create an alternate domain;
- recreate or repair a missing Store;
- ignore revocation;
- weaken full-value equality to IDs;
- clamp time;
- rebind a Tool ID;
- dispatch or invoke; or
- claim that an operation succeeded.

The coordinator treats an exception from an operational Store call as
`storage_unavailable` and an incoherent returned result or mismatched
Admission as `integrity_failure`. Backends should nevertheless return the
more precise typed result whenever the commit state is known. If commit state
is genuinely ambiguous, they must return `commit_unknown`.

---

## 14. TOCTOU and Future Delivery Boundary

Admission records the point-in-time facts evaluated at the authoritative
decision. It does not freeze filesystem ACLs, sandbox/OS permission,
environment state, Runtime availability, Inference Option availability, Tool
availability, configured Tool mapping, credentials, endpoints, or native
containment.

A future adapter must use just-in-time or native enforcement, and a future
dispatcher must handle changed Runtime/Inference availability and verify the
configured immutable Tool mapping. A future delivery/outbox system may use an
authoritative Admission as its immutable source record, but AIO-047 adds no
pending/claimed/dispatching/sent/failed/completed state, claim, lease, delivery
attempt, acknowledgement, event, result, error, usage, cost, or telemetry.

---

## 15. Production Claim and Limitations

The only approved production claim is:

> The supported local SQLite backend provides process-crash-durable atomic
> at-most-once Grant and Run consumption, duplicate suppression, and
> exact-retry recovery for same-host processes within one correctly owned
> authorization domain when every consumer uses the same pinned active
> authoritative ledger on supported local storage and all Grant, Tool, clock,
> filesystem, configuration, and domain-ownership trust preconditions hold.

It does not establish unqualified end-to-end authorization replay protection,
invocation replay protection, multi-machine safety, malicious-local-admin
tamper resistance, globally safe backup restore/failover/migration, TOCTOU
closure, dispatch, invocation, or success.

---

## 16. Explicit Exclusions

AIO-047 does not implement or authorize:

- a real Grant issuer, Human/policy Grant issuance, or issuer authentication;
- a real Tool resolver, Tool discovery, Tool execution, or Provider call;
- a caller trust/authentication field or serialized trusted envelope;
- caller-supplied prerequisite satisfaction or decision time;
- a public Revocation value/schema or delegated/domain-admin revocation;
- durable denial receipts or a request idempotency key;
- a mutable consumption flag or Admission lifecycle;
- PostgreSQL, central service, cross-machine consensus, or backend migration;
- same-domain restore/reactivation or split-ledger prevention;
- dispatch, outbox delivery, lease, invocation, result, event, or telemetry;
- Run lifecycle or cancellation; or
- AIO-030, AIO-044, Full Control Center/UI, or protected-target behavior.

All AIO-047 tests use synthetic Grants, domains, Bindings, parent facts, and
disposable temporary ledgers. No real Grant is consumed and no real Admission,
dispatch, or invocation occurs.
