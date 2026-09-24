# AI Engineering Orchestra - Authorization Domain Ownership Specification

Status: Canonical for AIO-049

Version: 0.1.0

Scope: Provider-neutral ownership semantics for one exact authorization domain
and one authoritative Admission ledger identity

---

## 1. Purpose and Authority Boundary

The **Authorization Domain Ownership Authority** is the provider-neutral
boundary that acquires, validates, retains, and releases exclusive operational
ownership of one exact authorization domain.

Its bounded purpose is:

```text
exclusive provider-backed ownership
+ immutable domain-to-ledger binding and monotonic state evidence
+ exact domain, ledger-instance, and positive-generation agreement
+ one live process-local Owned Authorization Domain Session
+ one operation lease for each complete coordinator call
-> supported operational access to the bound authoritative ledger
```

No individual field or artifact is ownership authority. In particular, an
identity value, persistent record, process identifier, state flag, lock name,
or caller assertion is never sufficient by itself. If any required component
is absent, stale, contradictory, unsupported, or cannot be revalidated,
authority is unproven and the operation fails closed.

Ownership is a prerequisite for supported operational access. It is not:

```text
Grant authentication
issuer entitlement
Tool trust
Admission
dispatch
invocation
```

This specification defines no Grant producer, Tool resolver, dispatcher, or
invocation mechanism.

---

## 2. Canonical Concept Family

The canonical concepts are:

- **Authorization Domain Ownership Authority**: the provider-neutral
  acquisition protocol.
- **Local Authorization Domain Binding**: a private, immutable,
  adapter-owned durable binding between one domain and one exact ledger
  identity and generation. It is not a public Core schema or capability.
- **Owned Authorization Domain Session**: the live, process-local capability
  that retains provider authority and gates complete coordinator operations.
- **Authorization Domain Operation Lease**: a non-transferable, in-process
  lifecycle lease held across exactly one complete coordinator operation.
- **Windows Local Authorization Domain Owner**: the v1 provider adapter. Its
  platform and storage mechanisms are outside this provider-neutral contract.

The canonical Python names are:

```text
AuthorizationDomainIdentity
AuthorizationDomainOwnershipAuthority
AuthorizationDomainOperationLease
OwnedAuthorizationDomainSession
```

The live Owned Session is the capability. AIO-049 defines no public serialized
ownership capability and no public serialized Local Authorization Domain
Binding.

---

## 3. Immutable Identity Value

`AuthorizationDomainIdentity` is a frozen value with exactly three fields:

| Field | Requirement |
| --- | --- |
| `authorization_domain_id` | Exact nonempty string; no normalization or aliasing |
| `ledger_instance_id` | Exact nonempty string identifying the provisioned ledger instance |
| `domain_generation` | Exact positive integer fixed for the binding |

The identity is the minimum provider-neutral equality boundary shared with the
Admission Store configuration. All three fields must agree exactly.

Direct construction, equality, copying, hashing, or serialization of an equal
identity establishes no live authority. Identity is descriptive evidence only.
The adapter remains responsible for binding it to all required provider-owned
path, file, durable-state, user, and live-exclusivity evidence.

`domain_generation` is immutable for the life of the binding. It is not a
process identifier, session number, acquisition count, restart counter, or
lock count. Ordinary close, process loss, and validated reacquisition retain
the same generation. Generation advancement and authority transfer require a
future design and are not supported by AIO-049.

---

## 4. Ownership Authority Protocol

The provider-neutral protocol has one operational acquisition method:

```python
class AuthorizationDomainOwnershipAuthority(Protocol):
    def acquire(
        self,
        authorization_domain_id: str,
    ) -> OwnedAuthorizationDomainSession: ...
```

The exact domain identifier is the only ownership selector. Acquisition must
not accept a caller-selected registry root, ledger path, ledger instance,
generation, activation state, process identifier, `is_owner` flag, or similar
claim. Those values are derived from trusted state and checked by the adapter.

Trusted Grant, Tool, prerequisite, execution-mode, clock, and Store
dependencies may be installed through trusted composition. They are not
ownership evidence and do not become acquisition selectors.

Before returning a session, `acquire` must prove all adapter-specific
requirements and exact agreement of:

1. the requested domain identifier;
2. the immutable external binding;
3. the authoritative ledger instance;
4. the positive domain generation;
5. the effective external and ledger activation state;
6. live exclusive ownership; and
7. the provider resources retained by the session.

Acquisition never provisions, registers, activates, migrates, repairs, fences,
backs up, restores, rebinds, changes generation, or selects a fallback.

---

## 5. Owned Authorization Domain Session

`OwnedAuthorizationDomainSession` is an abstract provider-neutral session
contract. A conforming adapter supplies the concrete, non-caller-constructible
implementation.

A session is:

- bound immutably to one `AuthorizationDomainIdentity`;
- live only while every required provider resource remains held and valid;
- process-local, nonserializable, noncopyable, and non-transferable;
- permanently unusable after close, fencing begins, or authority is lost; and
- distinct from every later session, including a same-generation session
  acquired after ordinary close or process loss.

The required surface is:

```python
session.identity
session.operation()
session.admit(presented_grant)
session.load_authoritative_admission(presented_grant)
session.revoke(presented_grant)
session.close()
session.fence()
```

`admit`, `load_authoritative_admission`, and `revoke` are the only supported
operational Admission surfaces. They preserve the existing coordinator and
Store semantics. The raw operational Store is an internal component and must
not escape the Owned Session.

The abstract Python base prevents direct construction and rejects ordinary
copy, deep-copy, and serialization mechanisms. These are process-encapsulation
controls for conforming composition, not defenses against hostile code already
executing inside the trusted process.

---

## 6. Complete-Operation Lease

Each supported operational method obtains one fresh
`AuthorizationDomainOperationLease` and retains it across the entire
coordinator call, including:

- Grant authentication and intrinsic validation;
- trusted Tool Binding resolution and validation;
- guarded historical classification;
- fresh prerequisite collection and reconstruction;
- effective Execution Mode and expected Run reconstruction;
- the final Store operation and its committed response; and
- provider revalidation after the Store call.

The lease exposes the exact same immutable identity as the parent session. On
entry, it rejects a closing, closed, fencing, fenced, lost, stale, or otherwise
unprovable session. It retains the lifecycle gate until exit and never hides an
operation or revalidation failure.

Provider authority is revalidated before and after the complete operation. A
later identity mismatch, lost resource, invalid state, or failed post-check
irreversibly loses that session's usability.

An operation lease is neither durable nor distributed. It is not a future
service lease, fencing token, ownership record, or transferable credential.

---

## 7. Close, Loss, and Terminal Fencing

`close()` first prevents new operation leases, waits for all active complete
operations to quiesce, releases provider resources, and irreversibly closes
the session. Repeated close may be idempotent but must never reacquire or
reanimate the object. Ordinary close does not change the immutable domain
generation or durable activation state.

Authority loss immediately prevents new operations. A session that cannot
prove any part of its live composite authority becomes permanently lost; it
must not reacquire resources in place. A new validated acquisition returns a
distinct session object.

`fence()` is a trusted-administration surface, not an assertion of Human or
policy entitlement. Supported composition must keep it behind the separate
administrative boundary. Holding ownership provides serialization for the
transition but does not itself prove administrative authorization.

Fencing has these provider-neutral semantics:

1. prevent new operation leases;
2. wait for all active complete operations to quiesce;
3. enter externally durable `fencing` state;
4. terminally fence the exact bound ledger; and
5. enter externally durable `fenced` state.

Once step 1 begins, the session is permanently unusable. Failure or ambiguity
at any later point must not return it to active service. Recovery may only
reconcile the exact same binding and ledger forward toward `fenced`; it must
never reactivate, rebind, select another ledger, or infer success from partial
evidence.

The conceptual durable state ordering is:

```text
inactive -> active -> fencing -> fenced
```

`fencing` dominates `active`, and `fenced` is terminal. Persisted state is
adapter-owned; this specification intentionally defines no public state-record
schema.

---

## 8. AIO-047 Admission Integration

Supported AIO-047 operational construction binds the complete
`AuthorizationDomainIdentity` to the exact Store configuration. A private
package-internal access object may retain the exact live session to enforce
that binding, but it is not a public value, bearer token, or serialized
authority artifact.

Every operational Store or coordinator call must obtain a fresh operation
lease from that same session. Checking identity only once at construction is
insufficient because the session may later close, begin fencing, or lose live
authority.

The following Store semantics remain unchanged:

```text
classify_guarded_history
admit_or_return_existing
load_authoritative_admission
revoke_or_return_existing
```

Ownership does not authenticate Grants, establish issuer entitlement, trust a
Tool Binding, supply prerequisite satisfaction, choose Execution Mode, sample
decision time, or weaken exact Grant/Binding/Run equality.

An operational ownership/session failure maps fail closed to the existing
Store infrastructure outcome appropriate to the known failure. A structural
identity or integrity contradiction maps to the existing integrity failure
boundary. No ownership-specific Admission outcome, retry rule, currentness
rule, conflict rule, or revocation rule is added.

---

## 9. Error Taxonomy

Expected ownership failures use typed exceptions rather than booleans or
caller-provided status fields:

| Error | Meaning |
| --- | --- |
| `AuthorizationDomainAlreadyOwnedError` | Another conforming owner holds the exact domain |
| `AuthorizationDomainOwnershipUnavailableError` | Required live evidence or infrastructure is unavailable |
| `AuthorizationDomainOwnershipUnsupportedError` | The platform or storage profile is unsupported |
| `AuthorizationDomainOwnershipIntegrityError` | Binding, identity, durable state, or integrity evidence disagrees |
| `AuthorizationDomainOwnershipStateError` | The domain is not in the state required by the operation |
| `OwnedAuthorizationDomainSessionClosedError` | The session is closed or a terminal transition has begun |
| `OwnedAuthorizationDomainSessionLostError` | Complete live authority can no longer be proven |

All derive from `AuthorizationDomainOwnershipError`; the two session errors
also derive from `OwnedAuthorizationDomainSessionError`.

An adapter may define narrower provider-specific subclasses, but it must not
convert unsupported, corrupt, stale, ambiguous, or unproven state into a
successful ownership result. Diagnostic exception text is not stable identity
or authority.

---

## 10. Crash, Reacquisition, and Stale Objects

After ordinary process loss, the provider releases process-owned resources. A
later process may acquire only after proving the same complete binding,
identity, generation, active state, and provider profile again. Ordinary crash
recovery does not advance generation.

The required stale-object ordering is:

```text
session A closes or its process ends
-> session B independently acquires and validates the same generation
-> every retained A object remains permanently closed or lost
```

No process identifier comparison, object equality, identity-value equality, or
generation equality can reanimate session A. Session B's liveness does not
confer authority on A.

---

## 11. Provider Adapter Obligations

The provider adapter owns the concrete mechanisms for:

- live domain-keyed exclusivity independent of ledger location;
- immutable binding and monotonic durable-state evidence;
- canonical target identity and replacement/alias detection;
- supported local-storage and access-control validation;
- retention and liveness checking of provider resources;
- exact ledger metadata, instance, generation, and state validation;
- lifecycle-gate synchronization and operation quiescence;
- durable state publication and same-target ambiguity reconciliation; and
- forward-only terminal fencing recovery.

Those mechanisms must satisfy the adapter's separately reviewed supported
profile. They are not fields in `AuthorizationDomainIdentity`, public Core
schemas, or caller inputs.

Operational acquisition validates and fails closed. It does not repair,
delete, replace, migrate, recreate, or silently broaden provider state.

---

## 12. No Fallback and Future Boundary

There is no in-memory, alternate-ledger, alternate-registry, alternate-backend,
automatic-backup, recreation, restore, or failover path. If the exact bound
authority cannot be proven, operational access stops.

AIO-049 does not implement:

- cross-host or machine-global ownership;
- distributed consensus or a central ownership service;
- durable service leases or transferable fencing tokens;
- authority transfer or generation advancement;
- restore activation or automatic failover;
- Grant production or authentication;
- Tool registry or resolution;
- dispatch, delivery, invocation, Result, event, or telemetry; or
- real domain provisioning, activation, acquisition, fencing, Admission, or
  invocation as part of its synthetic tests.

A future central authority may implement this protocol's domain, ledger,
generation, liveness, and complete-operation gating semantics through a
different provider. The local process-lifetime session and operation lease
must not be represented as that future distributed design.
