# AI Engineering Orchestra - Local Operational Trust Integration Specification

Status: Canonical for AIO-053

Version: 0.1.0

Scope: Same-process composition of local authorization-domain ownership,
Grant production, immutable Tool resolution, and authoritative Dispatch
Admission

---

## 1. Purpose

The **Local Operational Trust Coordinator** is the narrow trusted composition
root for one local operational-authorization path. It joins:

- one live AIO-049 Owned Authorization Domain Session;
- one real AIO-050 Grant Producer and its paired Grant-authentication port;
- one real AIO-051 immutable Tool Registry snapshot and resolver; and
- one real AIO-047 Dispatch Admission Coordinator backed by its supported
  local SQLite Admission Store.

The coordinator asks AIO-050 to produce one private opaque issued-Grant
presentation for one exact complete Run. On successful or exact-retry
issuance, it passes that exact presentation unchanged to the existing
AIO-049-owned Admission operation and returns the resulting predecessor value
unchanged.

The operational boundary ends after Admission. It performs no dispatch, Tool
invocation, operation execution, repository resource read, lifecycle
execution, result recording, delivery, or telemetry.

The following distinctions are mandatory:

```text
Grant issued != Admission created
Admission created != dispatch occurred
Admission created != Tool invocation occurred
Admission created != operation succeeded
```

---

## 2. Responsibility Boundary

The Local Operational Trust Coordinator owns only trusted construction,
sequencing, lifecycle, and unchanged result routing. It does not:

- authenticate a principal or authority proof;
- decide entitlement or policy;
- construct, authenticate, or validate a Grant;
- resolve or select a Tool;
- collect or assess prerequisites;
- determine effective Execution Mode;
- construct a Contract or Run;
- choose authoritative decision time;
- consume a Grant or persist an Admission;
- provision an alternate Store or select a fallback ledger; or
- dispatch or invoke anything.

Those responsibilities remain with their canonical predecessor components.
AIO-050 owns Grant production and authentication. AIO-051 owns immutable Tool
registration and Binding resolution. AIO-047 owns Admission ordering,
reconstruction, exact equality, decision time, Grant consumption, history,
revocation ordering, and authoritative persistence. AIO-049 owns the local
authorization domain, its generation, the live session, and operation leases.

No predecessor contract is widened or reinterpreted by this integration.

---

## 3. Real Components and Synthetic Edges

The integrated production-path components are real:

- AIO-049 administration, owner, live session, and operation leases;
- AIO-050 Producer and paired authentication port;
- AIO-051 immutable registry snapshot and resolver;
- AIO-047 coordinator and official local SQLite backend; and
- the canonical Grant, Tool Binding, and Admission values produced by that
  path.

The bounded integration evidence uses synthetic or disposable external edges:

- authenticated-principal evidence;
- exact Human-approval or policy-decision evidence;
- issuer-state and entitlement authorities consumed by AIO-050;
- fresh prerequisite and effective-mode sources consumed through AIO-047's
  existing ports;
- independent original-issuer revocation authentication;
- deterministic or test-controlled clock and entropy only where predecessor
  contracts permit them; and
- disposable authorization domains, ownership metadata, and SQLite ledgers.

Synthetic authority inputs do not make the production components fake. No
production principal, production approval system, production policy system,
production authorization domain, or production ledger is used.

---

## 4. Trusted Construction and Private Authentication Latch

The predecessor interfaces form a construction cycle. AIO-049 needs a
Grant-authentication port while constructing the session's AIO-047
coordinator, but AIO-050 can produce the exact paired port only after the
corresponding live session exists.

A private process-local forwarding latch resolves this cycle. The latch is an
implementation detail of the trusted composition root and implements the
AIO-047 Grant-authentication-port shape:

```python
authenticate_grant(presented_grant: object) \
    -> AgentExecutionAuthorizationGrant | None
```

The latch:

- begins `UNBOUND` and returns `None` while unbound;
- accepts exactly the paired AIO-050 port returned for the acquired session;
- binds once and atomically publishes one sealed target;
- rejects a foreign-session target, look-alike target, second bind, losing
  bind race, unbind, replacement, or fallback;
- forwards the original presentation unchanged;
- returns only the exact paired-port result;
- never constructs, copies, caches, validates, widens, or independently trusts
  a Grant; and
- is never exposed as a public setter or authority API.

Its state is monotonic:

```text
UNBOUND -> BOUND -> CLOSED
       \-> FAILED
```

`FAILED` and `CLOSED` are terminal. Neither the session nor the Local
Operational Trust Coordinator may be published while the latch is unbound.

The trusted root binds only the canonical Producer/paired-port composition
artifact returned for the exact acquired session. It does not infer pairing
from caller-supplied identifiers or accept a freely supplied callable.

---

## 5. Construction Order

Disposable administrative setup uses the real AIO-049 administration path to
provision, register, and activate one disposable AIO-047 SQLite ledger.

Trusted composition then follows this order:

1. Construct the AIO-051 registration for the exact
   Runtime/environment/operation route and the native
   `repository_file_read` Tool identity.
2. Atomically construct the immutable registry snapshot and real resolver.
3. Construct the unbound latch.
4. Construct the AIO-049 owner with the real resolver, fresh prerequisite and
   mode ports, trusted clock, and independent revocation-authentication port.
5. Acquire one live Owned Authorization Domain Session by exact domain ID.
6. Compose one AIO-050 Producer/paired-authentication binding for that exact
   session.
7. Bind and seal the latch to that exact paired port.
8. Publish the Local Operational Trust Coordinator only after all preceding
   steps succeed.

No partially constructed coordinator, unbound session, raw Store, or
authentication port is published.

### 5.1 Construction failure cleanup

Every construction failure triggers all-attempt cleanup of every capability
acquired by that point. Cleanup ownership follows the predecessor contracts:

- the AIO-050 Producer's canonical `close` operation closes its paired
  authentication port; the integration does not invent a second direct
  paired-port close operation;
- the latch is terminally failed or closed as appropriate; and
- the AIO-049 session is closed so ownership and the pinned ledger are
  released.

Producer close, latch cleanup, and session close are each attempted even when
an earlier cleanup step raises. The primary construction failure and every
cleanup failure remain observable for diagnosis. Repeated cleanup is safe and
cannot publish or restore a capability.

If a predecessor construction function fails before returning an owned
capability, cleanup of its private partial state remains that predecessor's
responsibility. The integration never fabricates a handle in order to clean it.

---

## 6. Operational Sequence and Ownership Leases

One Admission attempt follows this exact order:

1. Enter one registered outer coordinator operation while the coordinator is
   `LIVE`.
2. Establish one synthetic authenticated principal and exactly one Human or
   policy authority proof for the same complete Run.
3. Call the real AIO-050 Producer.
4. AIO-050 acquires its own fresh AIO-049 operation lease for issuance.
5. AIO-050 validates its authority inputs, issues or recovers the exact
   process-local opaque presentation, and publishes it only after clean lease
   exit.
6. On `issued` or `existing_exact_issuance`, pass that exact presentation to
   `owned_session.admit(...)`.
7. `owned_session.admit(...)` acquires a second fresh AIO-049 operation lease
   for the same exact session.
8. Under that lease, AIO-047 authenticates through the sealed latch and paired
   AIO-050 port.
9. AIO-047 resolves the Tool Binding through the real AIO-051 resolver.
10. AIO-047 classifies guarded authoritative history.
11. Only when history is absent, AIO-047 collects fresh parents, assesses
    prerequisites, resolves effective mode, prepares the Contract, and
    reconstructs the expected Run.
12. AIO-047 enforces exact Run equality and calls the official SQLite Store.
13. Return the exact predecessor result unchanged.
14. Leave the registered outer operation and stop.

Issuance and Admission use two distinct, sequential leases. There is no
nested, shared, third, or transaction-spanning integration lease. The gap
between the leases carries only the opaque presentation and grants no
authority by itself.

Close, fencing, ownership loss, session identity drift, or generation drift
in the gap makes the second lease fail before Grant authentication or Store
access. The integration does not retry issuance to replace the presentation.

---

## 7. Grant and Authority Integrity

The Grant path is:

```text
synthetic authenticated authority
-> AIO-050 private proof
-> AIO-050 Producer
-> opaque issued presentation
-> exact AIO-049 session
-> sealed paired AIO-050 authentication port
-> canonical Grant
```

Only AIO-050 may recover the canonical Grant from its opaque presentation. A
raw, copied, reconstructed, fabricated, tampered, foreign, or
`trusted = true` value is not trusted.

AIO-050 must accept authority only when it is well formed, unexpired, and
bound to the exact authenticated principal, authority channel and kind,
issuer, authorization domain, domain generation, complete Run, Producer, and
session epoch. A validly formed proof with any foreign binding is rejected
before presentation creation or issuance-state mutation.

The Local Operational Trust Coordinator never calls the paired authentication
port directly outside an AIO-049-owned operation. It passes only the opaque
presentation to the owned session.

---

## 8. Tool Identity and Resolution

The first integrated route uses this exact Tool identity:

```text
tool::aeo-native-repository-file-read::v1
```

The registration has identity only. It contains no callable adapter or
repository-read behavior. The integration constructs an immutable AIO-051
snapshot and uses the real historical resolver to produce the canonical
two-field Agent Operation Tool Binding.

The Local Operational Trust Coordinator accepts no caller Binding, Tool ID,
alias, route override, or fallback. Unknown routes, mismatched Runtime,
environment, operation, or resource, Tool-ID rebinding, and alternate-Tool
selection fail at their owning boundary.

Retirement applies at the AIO-051 pre-Run selection boundary. Because this
coordinator receives an already complete Run, retained historical resolution
remains total and is not reinterpreted as a new selection.

No Tool is invoked and no repository resource is opened.

---

## 9. Exact Run Invariant

The complete invariant is:

```text
Producer-approved Run == Grant.run == Binding.run
                      == freshly reconstructed expected Run
```

AIO-051 constructs the Binding from the authenticated Grant's exact Run.
AIO-047 reconstructs the expected Run from fresh prerequisite and mode inputs,
reuses `grant.run.run_id`, and enforces complete value equality before Store
Admission.

There is no partial comparison, coercion, normalization, resource widening,
replacement Run, alternate Tool, Runtime Option substitution, Inference
Option substitution, or post-Run Provider override. The Run has no separate
Provider field.

---

## 10. Result Boundary

The coordinator introduces no integration outcome taxonomy. Its return family
is exactly:

```text
AgentExecutionAuthorizationGrantProductionResult
|
AgentExecutionDispatchAdmissionStoreResult
```

An AIO-050 non-issuance result is returned unchanged and processing stops.
For `issued` and `existing_exact_issuance`, the successful production result
and opaque presentation remain private; the presentation is passed to the
owned Admission operation and the exact AIO-047 result is returned unchanged.

The integration does not translate failures, synthesize an Admission result,
change retry dispositions, or expose a successful presentation in its return
value.

---

## 11. Admission Ownership

The only Admission path is:

```text
owned_session.admit(opaque_presentation)
```

AIO-047 remains the sole owner of:

- Grant authentication ordering;
- intrinsic Grant and Binding validation;
- exact authorization-domain checks;
- Tool Binding resolution;
- guarded history before freshness work;
- fresh AIO-040 assessment;
- AIO-041 Contract preparation;
- AIO-042 Run reconstruction;
- exact three-way Run equality;
- authoritative decision time and currentness;
- revocation ordering;
- atomic Grant and Run consumption; and
- exact historical retry and persistence.

The integration never calls the SQLite Store directly, never mints an
AIO-047 authority-internal request, and never moves freshness work ahead of
guarded history.

---

## 12. Retry and Restart

### 12.1 Pre-Admission exact retry

While the exact process, Producer, and session remain live, retrying the
identical Run, authenticated principal proof, authority proof, and lifetime
may recover AIO-050's identical opaque presentation as
`existing_exact_issuance`. No replacement Grant or presentation is issued.

### 12.2 Post-Admission exact retry

The same presentation re-enters the same live session. AIO-047
re-authenticates it, reproduces the exact Binding, and returns exact
authoritative history before fresh-parent collection, mode resolution, clock
sampling, or another write.

### 12.3 Inter-lease loss

If issuance succeeds but the second lease cannot be acquired, only the same
presentation may be retried, and only while the exact session remains live.
A closed, fenced, lost, restarted, or generation-changed session requires the
existing AIO-050 new-session/new-Run recovery rule.

### 12.4 Restart boundaries

Before Admission, process restart loses proofs, issuance registry, Producer,
session, and presentation. Recovery requires a new session, new Run, fresh
authority, and new Grant.

After Admission, the AIO-047 SQLite record remains durable and authoritative,
but the integrated path cannot reload it without the lost AIO-050
presentation. The integration does not invent durable presentation storage.

An identically reconstructed append-only AIO-051 snapshot can reproduce the
historical Binding for an old Run and Grant. It cannot authenticate an old
Grant or recover a lost presentation or Admission.

There is no integration retry ID, presentation persistence, Producer
persistence, or unsupported cross-restart retrieval path.

---

## 13. Revocation

Revocation uses an independently authenticated synthetic original-issuer
edge. Its private revocation presentation binds:

- the independent original-issuer proof;
- the original opaque AIO-050 issued presentation;
- the exact session, authorization domain, and generation;
- explicit revocation intent; and
- fresh provenance.

Under `owned_session.revoke(...)` and its own AIO-049 operation lease, the
revocation-authentication port validates those bindings. It then forwards the
embedded issued presentation unchanged through the sealed latch and paired
AIO-050 port. Only AIO-050 recovers the canonical Grant.

The issuance presentation alone does not authorize revocation. The
integration constructs or caches no raw Grant and performs no direct Store
seeding. A missing, stale, foreign, or malformed revocation proof returns no
authenticated Grant and leaves the Store untouched.

AIO-047 owns the serialization order. Revocation before a new Admission makes
that Admission fail as revoked. Revocation after an Admission preserves the
immutable historical Admission while recording the tombstone.

---

## 14. Coordinator Lifecycle

The published coordinator has this monotonic lifecycle:

```text
LIVE -> CLOSING -> CLOSED
```

Each public operation registers as in flight only while state is `LIVE`.
Entering `CLOSING` rejects new operations and waits for registered outer
operations to quiesce without holding a lock required by those operations.

After quiescence, close independently attempts these canonical cleanup units:

1. AIO-050 Producer close, which canonically closes the paired authentication
   port;
2. latch close; and
3. AIO-049 session close.

Every unit receives an attempt even when an earlier unit raises. Cleanup
errors are preserved together. State remains terminal, repeated close is
safe, and no capability can be rebound or republished. Session close releases
the Windows ownership lock and pinned-ledger ownership.

Operations attempted after close fail before Producer, resolver, AIO-047
coordinator, or Store use.

---

## 15. Public Contract and Persistence Decisions

AIO-053 introduces no new public schema or durable integration state:

- new Run schema: **NO**;
- new Grant schema: **NO**;
- new Tool Binding schema: **NO**;
- new Admission schema: **NO**;
- new integration schema: **NO**;
- Integration Admission or Integration ID: **NO**;
- public proof or presentation schema: **NO**;
- Producer, presentation, latch, or coordinator persistence: **NO**; and
- AIO-047, AIO-049, AIO-050, or AIO-051 contract change: **NO**.

The latch, coordinator lifecycle, and result union are process-local
implementation details. They are not serialized authority or public schema.

If implementation evidence requires a predecessor-contract change, public
schema, hidden persistence, alternate ownership authority, fallback path, or
cross-restart presentation recovery, implementation must stop for Human
architecture review.

---

## 16. Negative Operational Boundary

Every success and failure path must preserve:

```text
DISPATCH: NO
INVOCATION: NO
REPOSITORY RESOURCE READ: NO
```

Disposable SQLite ledger and AIO-049 ownership-metadata I/O are allowed and
are not Tool resource access. The identity-only `repository_file_read` Tool
has no callable behavior in the integration or its fixtures.

The integration must not open, read, search, enumerate, stat, hash, resolve,
permission-inspect, or use any protected target as a fixture. Abstract Tool
identity registration and Binding construction do not access a resource.

The path ends immediately after returning the unchanged AIO-050 non-issuance
or AIO-047 Admission result.
