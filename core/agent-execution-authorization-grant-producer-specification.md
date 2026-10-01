# Agent Execution Authorization Grant Producer Specification

## Status

This specification defines the AIO-050 Foundation contract for the
**Agent Execution Authorization Grant Producer**.

It is the authoritative semantic contract for the provider-neutral,
same-process component that authenticates an issuer principal, establishes
entitlement for one exact Agent Execution Run, produces the existing canonical
Agent Execution Authorization Grant, and supplies the paired authentication
port used by AIO-047.

The Producer is operational trust infrastructure. It is not a new serialized
Core value, a policy language, an identity database, a dispatch mechanism, or
an invocation mechanism.

---

## Purpose

The Producer closes the boundary between declarative Grant data and a Grant
that was issued through an authenticated and entitled authority path.

It must:

- accept only exact process-local proofs minted by configured trusted
  adapters;
- bind issuance to one exact live Owned Authorization Domain Session and its
  complete Authorization Domain Identity;
- validate one complete Agent Execution Run without projecting a weaker scope;
- derive every Grant field that conveys authority from trusted dependencies;
- serialize one issuance decision for each domain and Run identity;
- publish a private issued-Grant presentation only after the ownership
  operation has exited cleanly; and
- let AIO-047 authenticate that presentation without changing AIO-047's
  existing one-argument authentication port.

The architecture preserves these distinctions:

```text
authenticated principal != entitled issuer
entitled issuer != Human approval
Human approval != Grant
policy rule != policy decision
policy decision != Grant
intrinsically valid Grant != authenticated Grant presentation
authenticated Grant != current Grant
current Grant != non-revoked Grant
non-revoked Grant != Admission
Admission != dispatch
dispatch != invocation success
```

---

## Scope

AIO-050 covers:

- trusted, process-local issuer-principal proofs;
- trusted, process-local Human approval and policy decision proofs;
- exact entitlement evaluation for one complete Run;
- trusted time and bounded Grant lifetime selection;
- 256-bit CSPRNG Grant identifier allocation;
- construction of the existing eight-field Grant;
- private issued-Grant presentations;
- the paired AIO-047 Grant-authentication-port implementation;
- same-Run issuance serialization and exact retry;
- issuer enablement epochs;
- structured nonsecret audit material; and
- fail-closed typed outcomes and retry dispositions.

AIO-050 does not cover:

- a new Grant schema or any change to the existing Grant schema;
- a public proof, presentation, audit, or result schema;
- identity provisioning or persistence;
- a general policy language, policy database, delegation model, or quorum;
- durable issuance persistence or cross-process presentation recovery;
- a general revocation authority;
- Tool discovery, Tool registration, Tool resolution, or Tool binding;
- Admission storage or Grant consumption;
- dispatch, command execution, Tool invocation, or invocation success;
- remote transport, authenticated IPC, signing, or encryption; or
- a Windows-specific identity adapter unless separately authorized.

---

## Canonical Grant preservation

AIO-043 remains authoritative for the Agent Execution Authorization Grant.
The Producer constructs exactly the existing eight fields in this order:

```text
grant_id
run
authorization_domain_id
issuer_kind
issuer_id
provenance_reference
issued_at
expires_at
```

The Producer must not add a domain generation, signature, key identifier,
authentication flag, trust flag, state, metadata bag, or extension field to
the Grant. The existing Grant validator remains the intrinsic-value validator.
Intrinsic validity alone never establishes trusted issuance.

The Producer must intrinsically validate every newly constructed Grant before
it can be registered or published. A validation contradiction is an
`integrity_failure` and publishes no presentation.

---

## Trust and threat model

The Foundation profile is a bounded same-process design. The Producer, paired
port, AIO-047 coordinator, and exact Owned Session composition run in one
trusted process.

The design protects against:

- untrusted caller values and look-alike objects;
- direct construction of a raw Grant;
- direct construction, copying, serialization, or substitution of proofs and
  presentations by ordinary callers;
- stale principal, authority, ownership, generation, and issuer-state epochs;
- same-Run concurrent issuance and Run-ID rebound;
- accidental cross-session, cross-domain, cross-adapter, and cross-process
  reuse; and
- partial or ambiguous issuance failures.

The design does not claim resistance to arbitrary hostile code already
executing inside the trusted Python process, compromise of the same operating
system account, memory inspection by a privileged adversary, or process
replacement. Private mint markers are process-encapsulation sentinels, not
secrets or cryptographic credentials.

If the Producer and coordinator are separated by a process or trust boundary,
the Foundation design is insufficient. Authenticated IPC, a MAC or signature
envelope, or authoritative issuance lookup requires a later architecture and
Human decision.

---

## Locked callable surface

The Core-facing Producer surface is:

```python
class AgentExecutionAuthorizationGrantProducer:
    def produce(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
    ) -> AgentExecutionAuthorizationGrantProductionResult: ...

    def close(self) -> None: ...


def _compose_agent_execution_authorization_grant_producer(
    *,
    owned_session: OwnedAuthorizationDomainSession,
    identity_adapter: IssuerPrincipalIdentityAdapter,
    human_approval_adapter: HumanApprovalAuthenticationAdapter | None,
    policy_decision_adapter: PolicyDecisionAuthenticationAdapter | None,
    issuer_state_authority: IssuerStateAuthority,
    issuer_entitlement_policy: IssuerEntitlementPolicy,
    lifetime_policy: AgentExecutionAuthorizationGrantLifetimePolicy,
    utc_clock: TrustedUtcClock,
    grant_id_source: GrantIdSource,
) -> _AgentExecutionAuthorizationGrantProducerBinding: ...
```

At least one exact authority adapter must be configured. Human and policy
channels may both be configured, but the supplied proof selects exactly one
channel and failure in that channel never falls back to the other.

The exact process-local proof and result names are:

```text
AuthenticatedIssuerPrincipal
AuthenticatedHumanApproval
AuthenticatedPolicyDecision
IssuedAgentExecutionAuthorizationGrant
AgentExecutionAuthorizationGrantProductionOutcome
AgentExecutionAuthorizationGrantRetryDisposition
AgentExecutionAuthorizationGrantAuditMaterial
AgentExecutionAuthorizationGrantProductionResult
```

These are Python process-local contracts. They are not serialized public
schemas or transferable credentials.

---

## Trusted composition and the private binding

Trusted composition creates exactly one Producer, one paired authentication
port, and one atomic issuance registry for one exact Owned Authorization
Domain Session. A second composition attempt for the same session must fail;
closing the first Producer does not permit its replacement inside that same
session. Before claiming the session, composition obtains one fresh operation
lease, confirms the exact full identity, and requires a clean provider
post-check; descriptive identity alone is insufficient. The clean composition
lease exit is the liveness linearization point. A close that begins after it
may make the returned binding immediately unusable, but cannot create or
revive authority.

`_AgentExecutionAuthorizationGrantProducerBinding` contains the Producer and
its paired `AgentExecutionAuthorizationGrantAuthenticationPort`. It is private
to the trusted concrete Owned Session composition root.

The current provider-neutral `OwnedAuthorizationDomainSession` contract has no
authentication-port installation method and is not widened by AIO-050. The
private composition function therefore returns the Producer-and-port binding
to the trusted concrete composition root. That root installs the paired port
when it constructs or configures the session's AIO-047 coordinator, and it
exposes only the Producer to the authorized orchestration layer. AIO-050 must
not reach into provider-private session internals or add a public setter to the
provider-neutral session abstraction.

This is an explicit Foundation integration limit: the Producer module creates
and binds the pair, while an existing trusted concrete root performs the
coordinator wiring. Possession of the private binding outside that root does
not create a supported operational path.

---

## Trusted dependency boundaries

The dependency names in the locked composition surface are semantic trust
ports. Implementations must fail closed on exceptions, malformed responses,
wrong exact types, or contradictions.

### Issuer principal identity adapter

`IssuerPrincipalIdentityAdapter` authenticates a current principal and mints
an exact private `AuthenticatedIssuerPrincipal`. A proof is bound by exact
object identity to:

- the configured adapter instance and adapter epoch;
- the exact Producer and Owned Session epoch;
- the full Authorization Domain Identity;
- the authentication session;
- an exact issuer kind and stable opaque issuer ID;
- a structurally valid half-open validity interval; and
- the issuer-state record and epoch used when it was minted.

A caller-supplied principal identifier, SID, `authenticated` boolean, issuer
kind, provenance string, entitlement claim, or look-alike value is not a
principal proof.

The bounded Python port exposes `current_epoch()`,
`validate_authenticated_principal(proof)`, and the private one-time
`_bind_authenticated_issuer_principal_minter(minter)` composition hook. The
configured adapter alone receives the composition-scoped mint capability;
ordinary orchestration and the Producer/port binding receive neither that
capability nor a proof constructor. Adapter exceptions are
`identity_unavailable`, while a nonexact, unknown, stale-epoch, or negatively
validated proof is `unauthenticated_principal`.

Adapter mint-capability installation is fail-closed and terminal for the exact
Owned Session. If any configured adapter rejects its one-time bind hook, the
closed session claim is retained, every installed minter remains bound only to
that closed state, and recovery requires a new Owned Session rather than a
partial recomposition. Every escaping Python failure that unwinds through this
narrow binding boundary, including a `BaseException`, closes the state before
the original failure is re-raised. This does not claim cleanup for non-unwinding
termination such as `os._exit`, process kill, kernel termination, or power loss.

For the bounded local Human profile, the adapter may bind a stable opaque,
installation-scoped Human principal ID to the current Windows user SID and a
fresh local authentication session. The SID is identity evidence only. It is
not entitlement, approval, or preferably the public issuer ID. Provisioning
and protected persistence of the opaque-ID-to-SID binding belong to the
identity adapter, not the Producer or the AIO-049 ownership registry.

### Human approval authentication adapter

`HumanApprovalAuthenticationAdapter` mints an exact private positive
`AuthenticatedHumanApproval` bound to:

- the exact authenticated Human principal object;
- the exact complete Run;
- the exact full Authorization Domain Identity and generation;
- the exact Owned Session and Producer/adapter epoch;
- an explicit positive approval decision;
- the short-lived approval-session identity;
- an opaque trusted provenance reference;
- a structurally valid half-open validity interval; and
- an optional authenticated shorter positive Grant duration.

Task approval prose, governance approval, a caller boolean, or an AIO-039
value cannot be converted into this proof.

The bounded Python port exposes `current_epoch()`,
`validate_authenticated_human_approval(proof)`, and the private one-time
`_bind_authenticated_human_approval_minter(minter)` composition hook. The
configured adapter alone receives that composition-scoped capability; it is
not exposed through the Producer/port binding or to ordinary callers.

### Policy decision authentication adapter

`PolicyDecisionAuthenticationAdapter` mints an exact private
`AuthenticatedPolicyDecision` bound to:

- the exact authenticated configured policy principal object;
- the exact complete Run;
- the exact full Authorization Domain Identity and generation;
- the exact Owned Session and Producer/adapter epoch;
- an exact `allow` or `deny` decision;
- the applicable immutable policy/configuration revision;
- an opaque trusted provenance reference;
- a structurally valid half-open validity interval; and
- an optional authenticated shorter positive Grant duration.

Only `allow` can satisfy the decision component of entitlement. A policy rule
is not a policy decision, and a policy decision is not a Grant.

The bounded Python port exposes `current_epoch()`,
`validate_authenticated_policy_decision(proof)`, and the private one-time
`_bind_authenticated_policy_decision_minter(minter)` composition hook. Human
and policy mint capabilities, proof types, registries, and validation calls
are disjoint.

For both authority channels, the Run subject must be the exact
`AgentExecutionRun` runtime type and pass canonical intrinsic Run validation
before it is stored in a proof. Verification repeats those checks before any
Run equality comparison. A wrong-type or intrinsically invalid embedded
subject cannot participate in equality and fails as `authority_proof_invalid`;
an adapter cannot supply a subclass, proxy, mapping, duck-typed value, or
custom-equality object as authority-bearing Run state.

### Issuer state authority

`IssuerStateAuthority` owns enabled/disabled state and a monotonically changing
process-local epoch for each configured issuer. Disable and re-enable both
change the epoch. It serializes each state transition, Producer validation,
and authentication-port validation at an explicit linearization point.
`observe_issuer_state(issuer_kind=..., issuer_id=...)` atomically returns one
exact `(enabled, epoch)` tuple used by proof minting, production, and the
paired port.

### Issuer entitlement policy

`IssuerEntitlementPolicy` is immutable for the Producer lifetime. It answers
whether the exact enabled principal, issuer kind, complete Run, and exact
authorization domain are configured as entitled. It is not supplied by the
untrusted caller and cannot widen the Run or resource.
The bounded Python port is `is_entitled(run=..., domain_identity=...,
issuer_kind=..., issuer_id=...) -> bool` and only exact `True` authorizes.

### Lifetime policy

`AgentExecutionAuthorizationGrantLifetimePolicy` is immutable for the
Producer lifetime and supplies:

- one explicit positive default lifetime;
- one explicit positive maximum lifetime; and
- one opaque policy revision.

The default must not exceed the maximum. A selected authority proof may carry
a shorter positive duration no greater than the default (and therefore no
greater than the maximum). There is no caller-supplied duration or absolute
expiry.

### Trusted UTC clock

`TrustedUtcClock` supplies the single issuance instant. There is no system
clock fallback. Its bounded Python port is `now_utc() -> datetime`.

### Grant identifier source

`GrantIdSource` supplies exactly 256 fresh random bits from an operating-system
CSPRNG for each allocation attempt. The Producer applies one fixed opaque,
injective textual encoding compatible with the AIO-043 scalar contract. UUIDv4
does not satisfy this requirement because its random payload is smaller than
the locked 256-bit entropy target.
Its bounded Python port is `random_bytes(length) -> bytes`; production always
requests 32 and rejects a nonexact or wrong-length result.

---

## Exact entitlement

Entitlement is the conjunction of:

```text
exact intrinsically valid complete Run
+ exact live Owned Authorization Domain Session
+ exact full Authorization Domain Identity and current generation
+ authenticated enabled issuer principal
+ immutable configured issuer entitlement for that exact domain and issuer kind
+ exact positive Human approval OR exact positive policy decision
```

The complete Run already binds Task, Workflow, Stage, Role, Actor, Runtime
Option, Inference Option, environment, operation, exact lexical resource, and
effective Execution Mode. The Producer must compare the complete Run and must
not introduce a weaker projected scope.

`issuer_kind`, `issuer_id`, and `provenance_reference` are derived from the
validated proofs. `authorization_domain_id` and generation are derived from
the live Owned Session. `issued_at`, `expires_at`, and `grant_id` are owned by
the Producer.

---

## Ownership, identity, and generation

`AuthorizationDomainIdentity` is descriptive evidence, not authority. The
Producer is permanently bound to one exact `OwnedAuthorizationDomainSession`
object and the full identity captured during trusted composition:

```text
authorization_domain_id
ledger_instance_id
domain_generation
```

Each production attempt must acquire one fresh `owned_session.operation()`
lease. The Producer holds that lease across the complete issuance critical
section. It checks that the session and lease identities match the captured
full identity exactly.

The ownership lease gates lifecycle transitions, but it is not assumed to
serialize concurrent production calls. The Producer therefore maintains its
own session-scoped synchronization for registry reservation and publication.

Closing or fencing the session prevents new supported operations and waits for
active operations to quiesce. The Producer must not infer ownership from a
domain ID, generation number, SID, PID, path, persisted flag, or `is_owner`
boolean.

---

## Trusted time and lifetime

After non-temporal proof provenance, exact subject, session, domain, and
generation checks, and while holding the operation lease, the Producer samples
its injected trusted clock exactly once.

The instant must be timezone-aware UTC and losslessly convertible to AIO-043's
canonical UTC representation. Naive, non-UTC, invalid, unrepresentable, or
exceptional samples fail as `clock_failure`. There is no implicit skew.

The same instant is:

- the temporal linearization point for the principal proof;
- the temporal linearization point for the selected authority proof; and
- the Grant's `issued_at`.

Each proof window is half-open:

```text
valid_from <= issued_at < valid_until
```

The proof window controls when the proof may mint a Grant. It does not
implicitly cap the Grant's separately authorized lifetime. A shorter Grant is
selected only by an authenticated duration inside the selected proof;
otherwise the immutable default applies.

The Producer fails closed on zero or negative duration, duration above the
configured default or maximum, invalid policy ordering, arithmetic overflow,
timestamp conversion loss, or `issued_at >= expires_at`.

---

## Grant identifier allocation

The encoded identifier carries 256 bits of fresh OS-CSPRNG entropy and provides
approximately 128-bit birthday-collision security. It has no ordering,
timestamp, routing, secrecy, identity-provider, or business meaning.

The canonical Grant identity namespace remains:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

The session-scoped registry retains every allocated Grant ID for the complete
Producer/session lifetime. A collision permits a bounded number of internal
regeneration attempts. Source failure or malformed output produces
`grant_id_generation_failure`. Exhausting the bounded collision attempts
produces `grant_id_collision`. An identifier is never rebound or overwritten.

No cross-restart absolute non-reuse guarantee is claimed. AIO-047 remains the
authoritative conflict detector when a Grant reaches its ledger.

---

## Issuance ordering and publication

One production call follows this order:

1. reject a closed Producer;
2. acquire one fresh AIO-049 operation lease and confirm the complete identity;
3. establish exact input types and intrinsic complete-Run validity;
4. validate principal and authority-proof provenance, object bindings,
   selected channel, subject, session, domain, and generation without reading
   time;
5. sample the trusted UTC clock exactly once;
6. validate both proof windows at that instant;
7. validate current issuer state and exact entitlement;
8. derive the effective lifetime;
9. reserve `(authorization_domain_id, run_id)` in the session registry;
10. allocate and collision-check the Grant ID;
11. construct and intrinsically validate the exact canonical Grant;
12. construct nonsecret audit material;
13. create a provisional private presentation and sealed issuance record;
14. permit the ownership provider's lease-exit post-check to run;
15. after clean lease exit, atomically install the successful registry record;
    and
16. publish the result and presentation.

No presentation reference may escape before step 15. Audit construction is
before publication, so there is no `issued but audit failed` state.

Successful lease exit is the ownership-authority linearization point for that
already-started issuance. The Producer retains its own registry mutex across
the provider post-check and immediate success-record installation. If close or
fencing begins after the clean exit but before the caller receives the result,
the issuance is not retroactively revoked, but the supported outer session
gate makes that presentation unusable. This narrow consequence follows from
the unchanged AIO-049 lease surface and does not authorize issuance that starts
after close or fencing begins.

An unambiguous failure before any possible publication releases a provisional
reservation. An ambiguity after reservation or any possible publication point
installs a permanent `run_issuance_conflict` tombstone. That Run cannot be
retried; recovery requires a new Run and fresh authority.

---

## Private issued-Grant presentation

`IssuedAgentExecutionAuthorizationGrant` is a private process-local object
capability. It encapsulates or resolves to the exact canonical Grant, but it is
not itself a Grant or a serialized envelope.

It has:

- no public caller constructor;
- no public schema;
- no bearer token or secret;
- no signature or key field;
- no `trusted` or `authenticated` flag; and
- no copy, deep-copy, pickle, or serialization support.

A second reference to the same object is an alias, not a second presentation.
The presentation is bound to the exact Producer instance and epoch, exact
Owned Session object, full Authorization Domain Identity, issuer-state epoch,
and one sealed all-eight-field canonical Grant record.

---

## AIO-047 authentication-port integration

The paired implementation preserves the unchanged AIO-047 surface:

```python
AgentExecutionAuthorizationGrantAuthenticationPort.authenticate_grant(
    presented_grant: object,
) -> AgentExecutionAuthorizationGrant | None
```

It returns the exact canonical Grant only when all of the following hold:

1. the value is the exact registered presentation object;
2. its sealed record belongs to the exact Producer and Producer epoch;
3. it belongs to the exact Owned Session object and full captured domain
   identity;
4. the Producer/port binding is not closed;
5. the issuer remains enabled at the exact recorded issuer-state epoch;
6. all eight Grant fields equal the sealed issuance record exactly;
7. the Grant remains intrinsically valid; and
8. there is no registry or integrity contradiction.

Raw or directly constructed Grants, look-alikes, serialized values,
presentations from another Producer/session/domain/generation, stale issuer
epochs, and altered values return `None`.

Operational authentication is supported only when the exact Owned Session's
coordinator invokes the port while already holding the complete-operation
ownership lease, for example through `session.admit(presentation)`. The outer
Owned Session gate alone establishes current ownership liveness and rejects
close, loss, or fencing before the port is reached. The port does not open a
nested lease and the one-argument contract carries no hidden lease witness.

Calling the port directly is unsupported and non-operational. Even if its
process-local object checks return a Grant, that call does not establish the
outer ownership-liveness half of the trust boundary and must not be treated as
authorization for a Store operation.

The port does not check Grant currentness, decide revocation, consume a Grant,
or provide replay protection. Repeated or concurrent authentication of the
same live presentation may proceed to AIO-047. The authoritative AIO-047 Store
alone owns atomic Grant/Run consumption, currentness, revocation ordering, and
exact historical Admission retry.

Only the raw Grant returned by the port may enter AIO-047's internal Store
request. The private presentation never enters Store serialization,
persistence, lookup keys, or Admission bytes.

---

## Same-Run issuance registry

The registry key is:

```text
(authorization_domain_id, run_id)
```

Each entry retains the exact complete Run and normalized issuance-request
identity, including the exact principal proof object, exact selected authority
proof object, and effective lifetime.

Registry behavior is:

- the first exact valid request returns `issued` with one newly published
  presentation;
- an exact retry with the same complete Run, same principal proof object, same
  authority proof object, and same effective lifetime returns
  `existing_exact_issuance` with the identical presentation object;
- the same complete Run with a different proof object or effective lifetime
  returns `run_already_issued` with no presentation;
- the same domain and Run ID bound to a different complete Run returns
  `run_identity_conflict` with no presentation;
- a burned entry returns `run_issuance_conflict` with no presentation; and
- successful and burned entries are non-evictable for the binding lifetime.

Expiry, issuer disablement, rejection, Admission, consumption, or revocation
does not permit another issuance for the same Run.

---

## Close, restart, and persistence

`close()` is idempotent and terminal. It closes the Producer and paired port,
makes every issued presentation unusable, retains the inaccessible registry
until composition teardown, and makes every later `produce` call return
`producer_closed`.

A closed Producer cannot be replaced in the same Owned Session. Recovery
requires a new Run, a new Owned Session and Producer, a freshly authenticated
principal, and a fresh proof in the same selected authority channel.

AIO-050 has no Producer database. Proofs, presentations, issuer-state epochs,
and the issuance registry are process-local and do not survive restart. After
restart, the trusted caller must use a fresh principal proof, fresh Human
approval or policy decision, new Run, and new Grant. The no-persistence profile
cannot technically detect a caller that improperly reuses a pre-restart Run;
new-Run-after-restart is a required trusted-composition rule.

An old presentation cannot drive AIO-047 historical retry after restart,
including response loss after an Admission commit. Delivery and dispatch must
not rely on cross-restart presentation recovery.

---

## Issuer disablement ordering

Issuer-state behavior is linearized as follows:

```text
disable before Producer state validation
  -> reject issuance as issuer_disabled

Producer state validation before disable
  -> issuance may publish; a later port check observes the changed epoch

disable before port state validation
  -> port returns None

port state validation before disable
  -> that exact already-owned coordinator operation may continue

disable followed by re-enable
  -> epoch changes again; old presentations never revive

disable after authoritative Admission
  -> immutable historical Admission remains unchanged
```

Because the unchanged AIO-047 port returns a raw Grant and carries no
issuer-state lease, disablement immediately after a successful port return may
race with that same coordinator's Store commit. AIO-050 does not claim
retroactive cancellation. The surrounding AIO-049 lease still prevents
ownership loss or fencing from racing that coordinator operation.

---

## Production result

`AgentExecutionAuthorizationGrantProductionResult` is frozen and has exactly
these four fields in this order:

```text
outcome
retry_disposition
presentation
audit_material
```

`presentation` is the exact private presentation only for `issued` and
`existing_exact_issuance`. It is `None` for every other outcome. The result
never exposes a raw Grant, a free-form diagnostic field, or a generic retry
boolean. `audit_material` is always a nonsecret structured value.

---

## Closed outcome taxonomy

`AgentExecutionAuthorizationGrantProductionOutcome` has exactly 24 values:

```text
issued
existing_exact_issuance
unauthenticated_principal
identity_unavailable
issuer_disabled
not_entitled
approval_missing
approval_subject_mismatch
policy_denied
authority_proof_invalid
invalid_run
domain_not_owned
domain_mismatch
generation_mismatch
ownership_lost
producer_closed
run_already_issued
run_identity_conflict
run_issuance_conflict
clock_failure
lifetime_invalid
grant_id_generation_failure
grant_id_collision
integrity_failure
```

No implementation-specific exception text or new outcome may widen this
closed contract.

---

## Closed retry taxonomy

`AgentExecutionAuthorizationGrantRetryDisposition` has exactly 13 values:

```text
no_retry_needed
retry_with_fresh_principal_and_authority
retry_after_identity_remediation
retry_after_issuer_reenable_with_fresh_authority
retry_with_fresh_human_approval
retry_with_fresh_policy_decision
retry_with_fresh_authority_decision
retry_with_fresh_session_authority
retry_with_new_run_and_fresh_authority
retry_with_new_run_and_fresh_session_authority
retry_after_clock_remediation
retry_after_internal_remediation
do_not_retry_same_request
```

These are aggregate mandatory actions. A channel-specific retry must remain in
the already selected Human or policy channel; it does not authorize fallback.

---

## Exact outcome-to-retry mapping

| Outcome | Retry disposition | Presentation |
| --- | --- | --- |
| `issued` | `no_retry_needed` | Newly published exact object |
| `existing_exact_issuance` | `no_retry_needed` | Identical previously published object |
| `unauthenticated_principal` | `retry_with_fresh_principal_and_authority` | None |
| `identity_unavailable` | `retry_after_identity_remediation` | None |
| `issuer_disabled` | `retry_after_issuer_reenable_with_fresh_authority` | None |
| `not_entitled` | `do_not_retry_same_request` | None |
| `approval_missing` | `retry_with_fresh_human_approval` | None |
| `approval_subject_mismatch` | `retry_with_fresh_human_approval` | None |
| `policy_denied` | `retry_with_fresh_policy_decision` | None |
| `authority_proof_invalid` | `retry_with_fresh_authority_decision` | None |
| `invalid_run` | `do_not_retry_same_request` | None |
| `domain_not_owned` | `retry_with_fresh_session_authority` | None |
| `domain_mismatch` | `retry_with_fresh_session_authority` | None |
| `generation_mismatch` | `retry_with_fresh_session_authority` | None |
| `ownership_lost` | `retry_with_fresh_session_authority` | None |
| `producer_closed` | `retry_with_new_run_and_fresh_session_authority` | None |
| `run_already_issued` | `do_not_retry_same_request` | None |
| `run_identity_conflict` | `retry_with_new_run_and_fresh_authority` | None |
| `run_issuance_conflict` | `retry_with_new_run_and_fresh_authority` | None |
| `clock_failure` | `retry_after_clock_remediation` | None |
| `lifetime_invalid` | `retry_with_fresh_authority_decision` | None |
| `grant_id_generation_failure` | `retry_after_internal_remediation` | None |
| `grant_id_collision` | `retry_after_internal_remediation` | None |
| `integrity_failure` | `retry_after_internal_remediation` | None |

Bounded Grant-ID collision regeneration is internal and is not an uncontrolled
caller retry. `grant_id_collision` is returned only after the bounded internal
attempts are exhausted.

---

## Audit material and secret boundary

Every result carries pure, frozen, nonsecret
`AgentExecutionAuthorizationGrantAuditMaterial`. When the corresponding data
is available, it contains:

- the exact outcome and retry disposition;
- issuer kind and opaque issuer ID;
- authorization domain ID, ledger instance ID, and generation;
- Run ID and a safe correlation for the complete Run subject;
- the Grant composite identity for an issuance;
- the opaque provenance reference;
- `issued_at` and `expires_at`; and
- the lifetime-policy revision.

Unavailable fields remain structurally absent or explicitly empty according to
the implementation's fixed frozen shape; they must never be populated from
untrusted fallback text. Audit material is not authority, an authentication
proof, a public schema, a sink side effect, or a durable Journal record.

Passwords, authentication tokens, private keys, bearer material,
approval-session secrets, and adapter secrets must never enter the Grant,
presentation, audit material, result, Task evidence, or logs.

Audit construction failure returns `integrity_failure` and publishes no
presentation.

---

## Revocation boundary

AIO-047's `OriginalIssuerRevocationAuthenticationPort` remains separate from
Grant-presentation authentication. AIO-050 does not implement a general
revocation authority and does not make AIO-047 revocation operational.

An issuance proof or issued-Grant presentation cannot authorize revocation.
A future revocation path must independently require a freshly authenticated
exact original issuer, exact Grant and domain, live Owned Session and current
identity, explicit revocation intent, and separate provenance.

---

## Thirty-scenario disposition matrix

In every scenario, **dispatch is No**. Successful issuance permits only a
conditional handoff to AIO-047 through the supported owned coordinator path;
it never proves Admission, dispatch, invocation, or success.

1. **Local Human with exact approval.** An exact current Human principal,
   exact positive approval, exact Run, live matching session, entitlement,
   valid time, lifetime, and fresh ID produce `issued` and one presentation.
   AIO-047 may subsequently authenticate it through the owned coordinator.
2. **Unauthenticated Human.** A missing, caller-constructed, stale, or
   otherwise unauthenticated principal produces `unauthenticated_principal`.
   No Grant or presentation is published.
3. **Authenticated but not entitled.** Authentication does not imply
   entitlement. The result is `not_entitled`, with no presentation.
4. **Approval missing.** Selecting the Human channel without the exact
   positive approval produces `approval_missing`; no policy fallback occurs.
5. **Run changed after approval.** Any mismatch between the approval's complete
   Run and the supplied complete Run produces `approval_subject_mismatch`.
6. **Wrong authorization domain.** A proof or Run binding for another domain,
   or a session identity with another domain ID, produces `domain_mismatch`.
7. **Generation mismatch.** A proof, captured identity, session, or lease bound
   to another generation produces `generation_mismatch`.
8. **Domain not owned.** A descriptive identity, flag, or failed initial
   operation lease cannot substitute for a live Owned Session. The result is
   `domain_not_owned`, with no publication.
9. **Policy permitted.** An exact authenticated policy principal, exact current
   `allow` decision, entitlement, and all other prerequisites produce `issued`.
10. **Policy denied.** An exact `deny` decision produces `policy_denied`; it is
    not converted to Human approval and no channel fallback occurs.
11. **Clock failure.** Exception, unavailable time, naive/non-UTC time, or
    lossy canonical conversion produces `clock_failure` before reservation.
12. **Invalid lifetime.** Invalid policy ordering, nonpositive or excessive
    proof duration, overflow, or nonpositive Grant interval produces
    `lifetime_invalid` and publishes nothing.
13. **Duplicate or colliding Grant ID.** A locally allocated collision is
    regenerated internally within a fixed bound. Exhaustion produces
    `grant_id_collision`; an ID is never rebound.
14. **Producer restart.** Old proofs, presentations, registry state, and exact
    retry are unavailable. Trusted recovery requires a new session/Producer,
    fresh principal and authority proof, new Run, and new Grant.
15. **Direct Grant.** A raw or directly constructed canonical Grant may be
    intrinsically valid but the paired port returns `None`; it carries no
    Producer provenance.
16. **Tampered Grant or presentation.** Any sealed-record, object-identity, or
    all-eight-field contradiction is rejected by the port; issuance-time
    contradictions fail as `integrity_failure`.
17. **Approval cast directly to Grant.** Approval evidence, approval prose, or
    a look-alike object is not an authority proof and cannot become a Grant;
    the request fails closed as `authority_proof_invalid` or the more specific
    missing/subject-mismatch Human outcome.
18. **Presentation crosses a process boundary.** Copying or serialization is
    unsupported, and a value reconstructed in another process is rejected. No
    cross-process trust claim exists.
19. **Issuer disabled.** Disablement before Producer validation yields
    `issuer_disabled`. Disablement or epoch change after issuance makes the
    outstanding presentation fail the next port state check.
20. **Domain fenced after issuance.** The supported Owned Session gate rejects
    the operation before the port is reached. Historical Admission, if any,
    remains unchanged.
21. **Concurrent identical same-Run requests.** At most one request returns
    `issued`; the other observes the installed exact issuance and returns
    `existing_exact_issuance` with the identical presentation object.
22. **Sequential exact retry.** The identical complete Run, exact principal
    proof object, exact authority proof object, and lifetime return
    `existing_exact_issuance` with the identical presentation.
23. **Same complete Run with different proof or lifetime.** The result is
    `run_already_issued`, with no presentation and no reissue.
24. **Same Run ID with a different Contract.** Complete Run equality fails and
    the result is `run_identity_conflict`; no first/latest winner is selected.
25. **Second Producer for the same Owned Session.** Trusted composition rejects
    the second binding. It cannot obtain an independent registry or bypass
    same-Run serialization.
26. **Producer or session closes.** Producer close is idempotent and terminal;
    later production returns `producer_closed`, existing presentations are
    unusable, and the same session cannot receive a replacement Producer. The
    outer session gate rejects a closed/lost session.
27. **Expired or foreign-adapter proof.** A principal proof that is no longer
    authenticated/current produces `unauthenticated_principal`; an expired,
    foreign, wrong-epoch, or wrong-adapter authority proof produces
    `authority_proof_invalid` unless the exact Human subject-mismatch outcome
    applies. No fallback occurs.
28. **Disable before versus immediately after port check.** Disable before the
    port's state linearization point returns `None`. If the port linearizes
    first, that exact already-owned coordinator operation may continue; later
    operations reject the stale epoch.
29. **Grant-ID source failure or exhaustion.** Exception, unavailable source,
    malformed entropy, or inability to obtain exactly 256 random bits produces
    `grant_id_generation_failure`; bounded repeated valid collisions produce
    `grant_id_collision`.
30. **Audit material construction failure.** The result is
    `integrity_failure`; neither successful registry installation nor external
    presentation publication occurs.

---

## Security invariants

An implementation conforms only if all of these remain true:

- no untrusted caller can construct an accepted principal proof, authority
  proof, or presentation through an ordinary public constructor;
- exact proof object and adapter provenance are checked, not merely value
  equality;
- no caller controls issuer identity, provenance, domain, generation, time,
  expiry, or Grant ID;
- one trusted time sample drives proof currentness and `issued_at`;
- a presentation is not externally visible before the ownership post-check
  succeeds;
- one exact session has one Producer/port/registry binding;
- same-Run issuance is atomic even if ownership leases overlap;
- old issuer epochs never revive after disable/re-enable;
- the authentication port preserves its one-argument AIO-047 signature;
- the port does not consume, dispatch, invoke, or establish standalone
  ownership liveness;
- private presentations never enter persistent Store or Admission data;
- raw Grants remain untrusted at the coordinator boundary; and
- no operation in this specification authorizes Tool work, dispatch, or
  invocation.

---

## Failure and recovery rules

Failures are represented only by the closed outcome and retry taxonomies.
Dependencies may raise internally, but exceptions must not become authority,
leak secrets, publish partial state, or widen retry behavior.

The Producer may release a reservation only when it can prove no presentation
was or could have been published. When publication state is ambiguous, it must
burn the Run with `run_issuance_conflict`. Recovery actions must follow the
exact retry disposition and must not silently switch Human/policy channels.

---

## Provider independence

The Producer is provider-neutral. Windows SID authentication, OIDC, passkeys,
workload identity, mTLS, remote policy services, and future provider adapters
belong behind the identity and authority ports. No provider becomes a permanent
architectural dependency of Orchestra Core.

---

## Foundation limitations

The bounded Foundation realization intentionally accepts these limits:

- trust is same-process and process-local;
- issuance state is not durable;
- absolute cross-restart Grant-ID non-reuse is not claimed;
- old presentations cannot recover exact historical Admission after restart;
- the private binding requires a trusted concrete composition root because the
  provider-neutral Owned Session API has no installation hook;
- standalone port calls cannot establish live ownership;
- disablement after a successful port check cannot retroactively cancel that
  already-owned coordinator operation; and
- no protected target, Tool, dispatch, invocation, or real authority operation
  is part of this specification.

Changing any of these limits requires a later architecture decision and Human
authorization rather than an implicit AIO-050 extension.
