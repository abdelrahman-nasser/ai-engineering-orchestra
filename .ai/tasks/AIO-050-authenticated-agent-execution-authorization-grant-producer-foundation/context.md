# AIO-050 Context

## Phase 1 authorization and verified baseline

Direct Human instruction authorizes Phase 1 only: create the new AIO-050 Task,
lock its trust, security, ownership/integration, and process-safety design, and
prepare the Human Phase 2 checkpoint. Implementation, runtime or test files,
tests, validators, package smoke, final Quality Gates, staging, commit, and
AIO-051 creation are not authorized.

The verified starting point is clean `main` at
`145ac55215f272ecf8b94de95af9fd34e201ae25`. The index is clean. AIO-049 is
completed at 81/81, AIO-048 remains cancelled at 94/100, AIO-047 is completed
at 105/105, AIO-030 remains parked, and the exact AIO-050 and AIO-051 Task
paths were absent.

AIO-050 is a new immutable Task identity. Its direct dependencies are AIO-043,
AIO-047, and AIO-049. AIO-039 through AIO-042 and Human Control are semantic
context, not additional direct dependencies. AIO-051 is a future independent
Task and is neither created nor designed here.

Exactly four AIO-050 Task artifacts are created in Phase 1:

```text
task.yaml
context.md
acceptance-criteria.md
review.md
```

No runtime, test, schema, package, or non-Task file may be created or modified
in Phase 1. If one becomes necessary, work stops for Human review.

## Purpose and architecture boundary

The canonical term is **Agent Execution Authorization Grant Producer**.

The Producer authenticates one issuer principal through a configured identity
boundary, establishes exact entitlement over one complete Agent Execution Run
in one currently owned authorization domain, constructs the existing canonical
eight-field Agent Execution Authorization Grant, and hands it to AIO-047
through an integrity-preserving same-process trust boundary.

The fixed responsibility split is:

| Layer | Responsibility |
| --- | --- |
| Identity adapter | Authenticate the principal and mint a private principal proof |
| Grant Producer | Establish exact entitlement and construct the Grant |
| AIO-047 authentication port | Authenticate the produced Grant presentation |
| AIO-047 authoritative Store | Establish currentness, revocation ordering, and consumption |
| Future delivery and invocation layers | Dispatch and invoke |

The architecture preserves these inequalities:

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

AIO-039 evidence, Task-level Human Control, approval prose, policy source text,
provenance text, and direct Grant construction never manufacture an
operationally trusted Grant.

## Canonical Grant preservation

AIO-043 remains authoritative. AIO-050 does not change the Grant's exact field
order or semantics:

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

There is no new Grant field, `domain_generation`, signature, key identifier,
authentication flag, trusted flag, state, or extension bag. The existing
Grant schema remains unchanged. A proposal to change that shape is outside
AIO-050 Phase 1 and requires an immediate stop and Human review.

## Locked Producer surface

The Phase 2 Producer is a trusted-composition component bound permanently at
construction to one exact live AIO-049 `OwnedAuthorizationDomainSession`, its
full `AuthorizationDomainIdentity`, one exact identity-adapter instance and
epoch, one identity/issuer-state authority, one immutable issuer-entitlement
policy, one immutable lifetime policy and revision, one injected clock, one
injected CSPRNG Grant-ID source, one session-scoped issuance registry, and its
paired AIO-047 authentication-port implementation.

Trusted composition creates exactly one Producer/port pair for an Owned
Session. Construction is not a public caller surface. A second Producer for
the same session is rejected; it cannot obtain an independent issuance
registry. This invariant and the session-scoped registry prevent multiple
Producer objects from bypassing same-Run serialization.

The exact Core-facing Python names and callable surface are locked as:

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

`_AgentExecutionAuthorizationGrantProducerBinding` is private to the exact
Owned Session composition root. It contains the Producer and paired
`AgentExecutionAuthorizationGrantAuthenticationPort`. The composition root
installs the port into that session's AIO-047 coordinator and exposes only the
Producer to the authorized orchestration layer. Producer, port, proof, and
presentation constructors are not public caller surfaces. At least one exact
authority adapter is configured; selecting the Human or policy channel is
explicit and never falls back.

The exact private proof/result names are:

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

They are Python process-local contracts, not serialized public schemas. The
frozen result has exactly four fields in this order:

```text
outcome
retry_disposition
presentation
audit_material
```

`presentation` is the exact `IssuedAgentExecutionAuthorizationGrant` object
only for `issued` or `existing_exact_issuance`; it is `None` for every other
outcome. The result never exposes a raw Grant or free-form diagnostic field.
`audit_material` is always the nonsecret pure structured value described below.

The authority rules are fixed:

- the Producer derives the authorization domain and generation from its live
  Owned Session, never caller fields;
- `authority_proof` is exactly one private `AuthenticatedHumanApproval` or
  `AuthenticatedPolicyDecision` minted by the configured trusted adapter;
- it accepts only exact private principal and authority proofs minted by the
  configured same-process boundaries and bound to this Producer/session epoch;
- `issuer_kind`, `issuer_id`, and `provenance_reference` are derived from those
  proofs;
- an optional shorter lifetime is carried inside the authenticated authority
  proof; it is not an independent caller value;
- `issued_at`, `expires_at`, and `grant_id` are Producer-owned;
- the complete Run is validated and compared without projecting another scope
  model; and
- success returns one private issued presentation and nonsecret audit material,
  not a freely trusted raw Grant.

The Producer holds a fresh AIO-049 operation lease across the complete issuance
critical section. Ordering is exact: structural proof provenance and Run/domain
binding checks; one trusted UTC sample; temporal validity checks for the
principal and selected authority proof using that sample; entitlement;
same-Run reservation; ID allocation; Grant construction with that same sample
as `issued_at`; audit construction; provisional presentation registration;
ownership provider post-check; clean lease exit; then atomic successful-record
installation and external publication of the result. No presentation reference
may escape before clean lease exit. An ambiguous ownership/post-check failure
after reservation burns that Run in the session registry and requires a new
Run.

AIO-047 authentication is supported only inside the exact Owned Session's
coordinator, such as `session.admit(presentation)`, while that coordinator
already holds AIO-049's complete-operation lease. The private paired port
neither opens a nested lease nor independently observes or proves its call
context or session liveness. The outer owned-session gate alone rejects close,
loss, or fencing before the coordinator/port is reached and prevents ownership
change while its lease is held. Once reached, the port verifies exact
presentation object, session-object, full-identity, issuer-state, and Grant
binding. Standalone port invocation is unsupported and non-operational; no
standalone liveness guarantee is claimed.

## Local principal model

The bounded Free/Pro profile uses:

```text
stable opaque installation-scoped Human principal ID
+ immutable trusted binding to the current Windows user SID
+ current-user/session authentication
+ short-lived action-approval session
```

The current Windows SID is identity evidence. It is not entitlement and is
preferably not the public `issuer_id`. The opaque `issuer_id` comes from
trusted installation configuration supplied to the identity adapter and is
bound there to the exact SID. The physical provisioning and persistence of
that installation configuration are not a Producer database and are not
implemented by AIO-050 unless separately authorized.

The AIO-049 ownership registry is not an identity registry. Its SID and domain
evidence must not be repurposed to authenticate a Human or establish issuer
entitlement.

An `AuthenticatedIssuerPrincipal`-like private proof is an unforgeable-by-
ordinary-caller output of the configured identity adapter. It is process-local,
nonserializable, noncopyable where practical, bound by object identity to the
exact adapter instance and epoch, bound to the current Producer/session epoch,
and tied to the current authentication session and issuer-state record. A
caller-provided principal ID, SID, `authenticated` boolean, issuer kind,
provenance value, entitlement rule, or look-alike object is rejected.

The stable opaque issuer-ID-to-SID binding, including any protected persistence
needed for installation stability, belongs to the trusted identity adapter. It
does not belong to the Producer or AIO-049. A current SID proves account context
only; it proves neither fresh Human presence nor entitlement.

Future Team/Enterprise adapters may use OIDC, passkeys, workload identity,
mTLS, or an external authorization service behind the same principal boundary.
AIO-050 defines no such implementation.

## Human approval and policy decision proofs

Task-level Human Control remains governance evidence. Runtime action approval
is a separate operational Producer input.

The private `AuthenticatedHumanApproval` concept is positive-only and binds:

- the exact authenticated Human principal proof;
- the exact complete Run;
- the exact `AuthorizationDomainIdentity`, including generation;
- the exact Owned Session instance and Producer/adapter epoch;
- the exact positive decision;
- the short-lived approval-session identity;
- an opaque trusted provenance reference;
- an explicit validity interval; and
- an optional shorter positive lifetime request.

Any complete-Run, domain-identity, generation, principal, decision, or approval-
session, epoch, or validity mismatch rejects issuance. It has no public schema,
is minted only by the configured trusted approval adapter, and cannot be
constructed from Task approval prose or a caller boolean.

The private `AuthenticatedPolicyDecision` concept binds:

- one authenticated configured policy principal;
- the exact complete Run;
- the exact domain identity and generation;
- the exact Owned Session instance and Producer/adapter epoch;
- an exact `allow` or `deny` result;
- the applicable policy/configuration revision;
- an opaque trusted provenance reference;
- an explicit validity interval; and
- an optional shorter positive lifetime request.

Only `allow` can establish the decision component of entitlement. `deny`
produces a typed rejection. A policy rule is not a decision and a decision is
not a Grant. The proof is minted only by the configured trusted policy adapter.
AIO-050 implements no general policy language, policy database, delegation,
quorum, or policy engine.

Both proof types retain or reference the exact authenticated principal object,
so a separately supplied equal-looking principal cannot be paired with another
decision. Possessing either proof outside its configured Producer boundary
does not establish authority. The Human and policy channels are disjoint: a
missing, invalid, expired, or denied proof in one channel never falls back to
the other channel.

## Exact entitlement

Entitlement is the conjunction of:

```text
exact intrinsically valid complete Run
+ exact live Owned Authorization Domain Session
+ exact full AuthorizationDomainIdentity and current generation
+ authenticated enabled issuer principal
+ immutable configured issuer entitlement for that exact domain and issuer kind
+ exact positive Human approval OR exact positive policy decision
```

The complete Run already binds Task, Workflow, Stage, Role, Actor, Runtime
Option, Inference Option, environment, operation, resource, and Execution
Mode. AIO-050 adds no duplicated entitlement-scope value. Equality is complete
Run equality, not Run-ID-only or field projection.

## Ownership, generation, and operation ordering

`AuthorizationDomainIdentity` alone is descriptive evidence, not authority.
The Producer requires the exact live Owned Session and derives the domain ID,
ledger instance, and positive generation from it under a fresh operation
lease. SID, PID, ledger path, generation number, or `is_owner` cannot replace
that session. The Producer and paired port use AIO-049's supported session and
coordinator surfaces; they do not reach into private ownership internals,
duplicate ownership truth, or invent another liveness flag.

The private presentation is bound to:

```text
Producer instance
+ exact Owned Session instance
+ full AuthorizationDomainIdentity
+ current issuer-state epoch
+ exact canonical Grant
```

The ordering is fail closed:

| Event | New issuance | Outstanding presentation | Historical Admission |
| --- | --- | --- | --- |
| Session begins closing | Rejected | Unusable; supported outer gate rejects before port | Unchanged |
| Session is closed or lost | Rejected | Unusable; supported outer gate rejects before port | Unchanged |
| Domain begins fencing | Rejected | Unusable; supported outer gate rejects before port | Unchanged |
| Domain is fenced | Rejected | Unusable; supported outer gate rejects before port | Unchanged |
| New owner session appears | Old Producer rejected | Unusable through old supported coordinator | Unchanged |
| Domain generation changes | Old Producer rejected | Unusable through old supported coordinator | Unchanged |

Ordinary process restart may retain the same durable domain generation, but it
creates a distinct Producer and Owned Session. Old process-local presentations
remain invalid.

## Grant ID semantics

The Producer allocates 256 fresh random bits from an OS CSPRNG and encodes them
as an opaque value satisfying the existing AIO-043 `grant_id` scalar contract.
This gives 256 bits of entropy and an approximately 128-bit birthday-collision
security bound. UUIDv4 is not the locked format because its 122 random bits do
not meet that literal collision-security target. The ID has no order,
timestamp, routing, secrecy, or business meaning. The canonical identity
namespace remains:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

The session-scoped issuance registry records allocated IDs for the complete
Producer/session lifetime. Collision detection is bounded to that live local
registry; no cross-restart claim is made. A collision detected before
publication permits bounded internal regeneration. Exhaustion, source failure,
or a repeated collision fails closed without publishing a Grant. An ID is never
rebound or overwritten.

Without durable Producer allocation state, absolute mathematical non-reuse
across restarts is not claimed. AIO-047 remains the authoritative conflict
detector when a Grant reaches its ledger. Requiring absolute durable allocation
would materially expand scope and triggers a stop.

## Trusted time and lifetime

Under the issuance lease, the Producer samples its injected trusted UTC clock
exactly once after non-temporal provenance/subject checks and before any
temporal proof or entitlement decision. The sample must be timezone-aware UTC
and must convert losslessly to the AIO-043 canonical UTC form. There is no
system-clock fallback. The same instant is the temporal linearization point and
the Grant's `issued_at`.

Every authenticated principal and selected authority proof has a structurally
valid half-open issuance window and is current only when:

```text
valid_from <= issued_at < valid_until
```

Invalid ordering or a sample outside either required window produces the typed
proof/authentication rejection before reservation or publication. The proof
window limits when the proof may mint a Grant; it does not silently cap the
Grant's separately authorized lifetime. If a Human or policy authority intends
a shorter Grant, that exact duration must be authenticated inside its proof.
The Grant therefore may expire after `valid_until`, but only according to that
proof-bound duration or the immutable domain default/maximum policy.

Domain issuance policy supplies an explicit positive default lifetime,
positive maximum lifetime, and opaque policy revision fixed at Producer
construction. A trusted Human or policy proof may carry a shorter positive
duration. A caller cannot independently supply a duration, `issued_at`, or an
absolute `expires_at`, and no proof can exceed the configured maximum.

The Producer fails closed on clock exception or unavailability, naive/non-UTC
time, lossy or invalid conversion, overflow, zero or negative duration, or
`issued_at >= expires_at`. It introduces no implicit skew. AIO-047 independently
samples its authoritative decision time and owns admission-time currentness,
clock non-regression, and revocation ordering.

## Private issued-Grant presentation

The exact private term is **Issued Agent Execution Authorization Grant**, and
the locked Python type name is `IssuedAgentExecutionAuthorizationGrant`.

It is a private, process-local, nonserializable, noncopyable object-capability
that encapsulates or resolves to the exact canonical Grant. It has no public
constructor, schema, secret bearer token, `trusted`, `authenticated`, or
signature field. The security claim is process encapsulation and trusted
composition, not cryptographic resistance to hostile code already executing in
the trusted Python process or compromise of the same Windows account.

Trust does not follow from its class name or fields. The paired authentication
port checks:

1. exact presentation object identity in the session-scoped private issuance
   registry;
2. exact Producer instance, Producer epoch, and private sealed issuance record;
3. binding to the exact Owned Session object and full domain identity captured
   by its private coordinator composition;
4. current issuer enablement epoch;
5. exact equality of all eight Grant fields with the sealed record plus
   intrinsic Grant validity; and
6. absence of any integrity contradiction.

The outer Owned Session gate, not the unchanged one-argument port, establishes
current ownership liveness and that its complete-operation lease is held.

Ordinary copy, deep-copy, pickle, or serialization must fail. A second Python
reference to the same live object is only an alias, not a new presentation or
new Grant. Hostile introspection by arbitrary code already executing inside the
trusted process is outside the local threat model; accidental substitution,
copying, stale reuse, and untrusted caller input remain in scope. Private mint
markers are implementation sentinels, not secrets and never appear in audit.

## AIO-047 authentication-port integration

AIO-050 eventually supplies the paired implementation of:

```python
AgentExecutionAuthorizationGrantAuthenticationPort.authenticate_grant(
    presented_grant: object,
) -> AgentExecutionAuthorizationGrant | None
```

The signature does not change. Required behavior is:

| Presented value | Result |
| --- | --- |
| Raw or directly constructed Grant | `None` |
| Look-alike or serialized presentation | `None` |
| Copy from ordinary copy/deep-copy/pickle | Copy operation fails; otherwise `None` |
| Presentation from another Producer | `None` |
| Presentation for another session/domain/generation | `None` |
| Presentation whose Grant differs from the issuance record | `None` |
| Presentation submitted after ownership loss, close, or fencing through the supported session surface | Outer gate rejects; port is not reached |
| Presentation after issuer disablement or epoch change | `None` |
| Exact live valid Producer-issued presentation | Exact canonical Grant |

The presentation does not self-attest trust. On the supported path, trust is
established jointly by the outer gate's live ownership lease and the paired
configured port's successful object-identity, private-registry, integrity,
issuer-state, exact-session, and full-identity checks. The port is not a
standalone public authenticator, does not verify a hidden lease witness, and
does not reacquire or nest an ownership lease. This preserves AIO-047's
prohibition on caller-supplied trusted wrappers.

The authentication port does not decide Grant currentness or revocation and
does not consume the presentation. Concurrent or repeated authentication of
the same exact live presentation may proceed to AIO-047; the authoritative
Store owns atomic Grant/Run consumption and exact historical retry.

The issued presentation is passed only to the supported owned coordinator
surface; the coordinator passes it to `authenticate_grant`. Only the returned
raw canonical Grant may enter the AIO-047 Store request. The private
presentation itself never reaches Store serialization, lookup, consumption, or
Admission bytes.

## Same-Run concurrent issuance

The bounded local design maintains one atomic process-local issuance registry
for the exact Owned Session, not merely one guard per freely constructible
Producer object. Trusted composition permits exactly one Producer/port pair for
that session. Registry keys are `(authorization_domain_id, run_id)`; every
entry retains the exact complete Run and exact normalized issuance-request
identity so Run-ID rebound cannot hide a different Contract.

The reservation and publication transitions serialize deterministically under
the live ownership operation lease:

- two concurrent exact requests yield at most one `issued` result and one
  canonical Grant/presentation;
- after atomic publication, an exact same-process retry using the identical
  principal proof object, authority proof object, complete Run, and effective
  lifetime returns the identical presentation as `existing_exact_issuance`;
- the same complete Run with a different proof or effective lifetime is
  `run_already_issued` and returns no presentation;
- the same `(authorization_domain_id, run_id)` with a different complete Run is
  `run_identity_conflict` and returns no presentation;
- an ambiguity after reservation or any possible publication point installs a
  `run_issuance_conflict` tombstone, returns no presentation, and requires a
  new Run; and
- an unambiguous failure before any possible publication releases its
  reservation according to the exact typed retry mapping.

A successful or burned entry is non-evictable for the Producer/session
lifetime. Expiry, issuer disablement, rejection, Admission, or consumption does
not permit reissuance for that Run. This is one issuance and one presentation,
not two Grants. AIO-047 remains the sole authority for replay, Grant/Run
consumption races, and Admission retry.

`close()` is idempotent and terminal. It closes the Producer/paired-port
binding, makes every presentation unusable, retains the inaccessible registry
until session-composition teardown, and makes every later `produce` call return
`producer_closed`. Trusted composition never replaces a closed Producer inside
the same Owned Session. Recovery requires a new Run, new Owned Session and
Producer, fresh principal authentication, and a fresh proof in the same
authority channel.

## Restart and persistence

AIO-050 has no Producer database. Unconsumed presentations are intentionally
ephemeral and do not survive Producer or process restart.

After restart, a new attempt requires:

```text
fresh principal authentication
+ fresh Human approval or policy decision
+ new Run
+ new Grant
```

The Producer must not issue another Grant for an already-existing old Run to
recreate a lost presentation. This is a required trusted-caller/composition
rule, not a fact that no-persistence v1 can prove after the old process state is
gone. The local technical guarantee is only one issuance per live
Producer/session epoch. A caller that violates the new-Run-after-restart rule
cannot be detected without durable issuance provenance.

Consumed Grants remain durably represented in AIO-047 Admission records, but
the current coordinator reauthenticates before Store load. Consequently an old
ephemeral presentation cannot drive AIO-047 exact historical retry after
Producer/process restart, including response-loss-after-commit. Dispatch or
delivery must not rely on such cross-restart recovery. This profile does not
promise recovery of an outstanding or response-ambiguous presentation. A hard
requirement needs an authoritative issuance store or authenticated durable
envelope and causes an AIO-050 scope stop.

## Issuer disablement

The trusted local issuer authority maintains a process-local enablement state
and monotonically changing in-process epoch. Any disable or re-enable transition
changes the epoch so an old presentation cannot revive. Disable/re-enable,
Producer issuer-state validation, and port authentication-state validation are
serialized by that authority and each has an explicit linearization point.

```text
disable linearizes before Producer state validation -> reject issuance
Producer validation linearizes first -> issuance may publish, but a later port check observes the newer epoch and rejects
disable linearizes before port authentication check -> reject presentation
port authentication check linearizes first -> that already-owned coordinator operation may continue
re-enabled later -> prior presentations remain rejected because epoch changed
disabled after authoritative Admission -> historical Admission unchanged
```

The port's successful issuer-state check is the disablement boundary. Because
AIO-047's unchanged port returns a raw Grant and carries no issuer-state lease,
disablement immediately after successful port return may race with that same
coordinator's Store commit; AIO-050 does not claim retroactive cancellation.
The surrounding AIO-049 operation lease still prevents ownership loss/fencing
from racing that coordinator operation. No historical Grant or Admission is
mutated or deleted, and later coordinator retrieval can fail if presentation
reauthentication no longer succeeds.

## Outcome and retry taxonomy

The frozen Producer result has exactly the locked four fields: one outcome, one
retry disposition, an optional private presentation, and nonsecret audit
material. Only `issued` and `existing_exact_issuance` carry a presentation.

The retry dispositions are aggregate mandatory actions, not generic hints:

| Retry disposition | Mandatory action before another production call |
| --- | --- |
| `no_retry_needed` | Use the returned exact presentation; do not issue again |
| `retry_with_fresh_principal_and_authority` | Authenticate a fresh principal and mint a fresh proof in the same selected Human/policy channel |
| `retry_after_identity_remediation` | Repair the trusted identity boundary, then obtain a fresh principal and fresh same-channel authority proof |
| `retry_after_issuer_reenable_with_fresh_authority` | Wait for trusted re-enable, then obtain a fresh principal and fresh same-channel authority proof under the new issuer epoch |
| `retry_with_fresh_human_approval` | Mint a new exact Human proof for the same current principal/session/Run |
| `retry_with_fresh_policy_decision` | Mint a new exact policy decision for the same current principal/session/Run |
| `retry_with_fresh_authority_decision` | Mint a new exact proof in the already selected channel; no channel fallback |
| `retry_with_fresh_session_authority` | Acquire a new Owned Session and Producer, then obtain fresh principal authentication and a fresh same-channel authority proof bound to them |
| `retry_with_new_run_and_fresh_authority` | Construct a new Run and mint a fresh same-channel authority proof for it; reauthenticate too if the principal proof is no longer current |
| `retry_with_new_run_and_fresh_session_authority` | Construct a new Run, acquire a new Owned Session and Producer, then obtain fresh principal authentication and a fresh same-channel authority proof |
| `retry_after_clock_remediation` | Repair the trusted clock; all existing proofs are revalidated at the next single sample and may require their own typed fresh-proof path |
| `retry_after_internal_remediation` | Repair the named internal component; retry only if no issuance/tombstone exists and all proofs remain current |
| `do_not_retry_same_request` | The same request cannot validly progress |

The outcome-to-retry relation is closed and exact:

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

`retry_with_fresh_authority_decision` is the common category; the Human- and
policy-specific dispositions require the same channel that was selected and
never permit fallback. Bounded Grant-ID collision regeneration is internal and
is not uncontrolled caller retry. `grant_id_collision` is exposed only after
the bounded internal attempts are exhausted. No free-form diagnostic field or
separate diagnostic payload is exposed.

## Audit and secret boundary

Every result exposes nonsecret structured audit material containing, when
available:

- outcome and retry disposition;
- issuer kind and opaque issuer ID;
- exact domain ID, ledger instance, and generation;
- exact Run ID and a safe correlation for the complete Run subject;
- Grant composite identity for an issuance;
- provenance reference;
- `issued_at` and `expires_at`; and
- lifetime-policy revision.

Audit material is a pure structured result value constructed before atomic
publication. It is not a sink side effect, authority, authentication proof,
public schema, or durable Journal record. Audit-construction failure is an
`integrity_failure` and publishes nothing, so there is no ambiguous
"issued but audit write failed" state. A future Execution Journal owns durable
persistence.

Passwords, authentication tokens, private keys, bearer material, approval-
session secrets, and identity-adapter secrets never enter the Grant,
presentation, audit material, diagnostic text, Task artifacts, or logs.

## Original-issuer revocation boundary

AIO-047's `OriginalIssuerRevocationAuthenticationPort` remains distinct from
Grant presentation authentication. AIO-050 Phase 2 does not implement a general
revocation authority and does not make AIO-047 original-issuer revocation
operational by itself.

The future seam may reuse the same principal-authentication and issuer-state
boundary, but it must independently require:

- a freshly authenticated principal;
- exact equality with the Grant's original `issuer_kind` and `issuer_id`;
- exact Grant and authorization domain;
- a live Owned Session and current domain identity; and
- explicit revocation intent and provenance.

An issued-Grant presentation alone cannot authorize revocation. Delegated or
domain-admin revocation remains outside scope. A future private revocation
proof must be minted for a fresh, separately authenticated exact revoke action;
an issuance proof or presentation cannot be reused as that authority.

## Local cryptographic and remote boundary

No local cryptographic Grant signature is required because the supported v1
profile requires:

- Producer and AIO-047 coordinator in one trusted process;
- no presentation persistence or cross-process transfer;
- raw Grant rejection;
- exact private issuance-registry membership;
- live ownership and issuer-state checks; and
- an explicitly bounded same-process threat model.

If any assumption fails, work stops for architecture and Human review.
Authenticated IPC, mTLS, a MAC/signature envelope, or authoritative issuance
lookup are future remote options. They do not add fields to the Grant in
AIO-050.

## Public and private contract boundary

No new public serialized schema is introduced for:

- the Grant Producer;
- Issued Agent Execution Authorization Grant;
- authenticated principal;
- Human approval proof;
- policy decision proof;
- audit material; or
- retry/result transport.

The existing Grant schema remains unchanged. Python protocols, frozen result
values, private proof types, and private presentation types may be implemented
later without claiming a cross-process serialized contract.

## Scenario matrix

`Conditional` means AIO-050 succeeds but Tool resolution, fresh prerequisites,
currentness, revocation, uniqueness, and authoritative Store behavior must
still pass. Dispatch is `NO` in every scenario.

| # | Scenario | Principal authenticated? | Issuer entitled? | Grant issued? | Presentation trusted? | AIO-047 authentication | Admission path | Dispatch |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Local Human with exact approval | Yes | Yes | Yes | Yes | Exact Grant | Conditional | No |
| 2 | Unauthenticated Human | No | No | No | No | Reject | Stop | No |
| 3 | Authenticated but not entitled | Yes | No | No | No | Reject | Stop | No |
| 4 | Approval missing | Yes | No | No | No | Reject | Stop | No |
| 5 | Run changed after approval | Yes | No; complete-Run mismatch | No | No | Reject | Stop | No |
| 6 | Wrong authorization domain | Identity only | No | No | No | Reject/domain mismatch | Stop | No |
| 7 | Generation mismatch | Identity only | No | No | No | Reject | Stop | No |
| 8 | Domain not owned | Yes | Not exercisable | No | No | Reject | Stop | No |
| 9 | Policy issuer permitted | Yes | Yes | Yes | Yes | Exact Grant | Conditional | No |
| 10 | Policy issuer denied | Yes | No | No | No | Reject | Stop | No |
| 11 | Clock failure | Yes | Yes before time | No | No | Reject | Stop | No |
| 12 | Invalid lifetime | Yes | Yes before lifetime | No | No | Reject | Stop | No |
| 13 | Duplicate or colliding Grant ID | Yes | Yes | No second issuance; bounded regeneration or fail | Original only | No conflicting Grant | Stop on failure | No |
| 14 | Producer restart | Fresh proof only | Fresh decision for new Run only | No recovery for old Run | Old presentation: No | Reject old | New Run only | No |
| 15 | Direct-constructed Grant | No Producer provenance | Unproven | No | No | Reject | Stop | No |
| 16 | Tampered Grant or presentation | No; integrity contradiction | Unproven | No | No | Reject | Stop | No |
| 17 | Approval cast directly to Grant | Principal may exist | Approval alone insufficient | No | No | Reject | Stop | No |
| 18 | Presentation crosses process boundary | No under local profile | Unproven | No local cross-process issuance | No | Reject | Stop | No |
| 19 | Issuer disabled | Identity may remain recognizable | No | No new Grant | Outstanding presentation: No | Reject | No new Admission | No |
| 20 | Domain fenced after issuance | Historical identity only | No current authority | No new Grant | Outstanding presentation unusable | Outer gate rejects; port not reached | Historical record only | No |
| 21 | Concurrent identical same-Run requests | Yes | Yes | Exactly one new Grant | One identical object | Exact Grant | Conditional once | No |
| 22 | Sequential exact retry | Yes; exact same proof | Yes | No second Grant | Same object | Exact Grant | Conditional/exact retry | No |
| 23 | Same complete Run, different proof or lifetime | Proof differs | No exact-request match | No second Grant | No new presentation | Reject production | Stop | No |
| 24 | Same Run ID, different Contract | Proof may be valid for other subject | No | No | No | `run_identity_conflict` | Stop/new Run | No |
| 25 | Second Producer for same Owned Session | Not admitted by composition | No | No | No | Reject construction/use | Stop | No |
| 26 | Producer/session closes | Prior proof is stale | No | No | No | Outer gate rejects; port not reached | New Run/session/authority | No |
| 27 | Expired or foreign-adapter authority proof | Principal may be recognizable | No | No | No | Reject | Fresh same-channel proof | No |
| 28 | Disable before vs. immediately after port check | State serialized at check | Point-in-time only | No new issuance after disable | Before: No; after: already authenticated operation may continue | Before: reject; after: exact Grant already returned | Conditional race boundary | No |
| 29 | ID source failure/exhaustion | Yes | Yes before ID | No | No | Reject | Internal remediation | No |
| 30 | Audit material cannot be constructed | Yes | Yes before publication | No | No | Reject | Internal remediation | No |

## Expected Phase 2 artifacts

Phase 1 proposes but does not create:

```text
core/agent-execution-authorization-grant-producer-specification.md
engineering_orchestration/agent_execution_authorization_grant_producer.py
tests/test_agent_execution_authorization_grant_producer.py
```

Only if separately confirmed by the Phase 2 authorization and identity design:

```text
engineering_orchestration/windows_local_issuer_identity.py
tests/test_windows_local_issuer_identity.py
```

Focused changes may be required in `core/terminology.md`, AIO-047
specification/regression coverage, and package/import metadata. No other path
is implicitly authorized.

## Validation-safety policy

Before any validator, test, smoke, packaging, lint, or verification command is
executed, its exact executable, arguments, scope, and protected-target safety
must be established from already approved syntax or static inspection of the
exact source revision.

```text
unknown command -> do not execute
unknown validator -> do not execute
legacy validator --help discovery -> prohibited
command absent from this matrix -> not authorized
```

An absent or changed command requires static review, a matrix amendment, and
explicit Human authorization before execution. Phase 1 executes none of the
Python, test, validator, Markdown, or package commands below.

### Validation Safety Matrix

| ID | Validation | Exact prospective scope | Safety basis | Phase 1 status |
| --- | --- | --- | --- | --- |
| V1 | AIO-050 Task schema | Exact AIO-050 `task.yaml` and Task schema only | Direct two-file loader; no catalog traversal | Locked; not executed |
| V2 | `architecture-change` Workflow schema | Exact Workflow YAML and Workflow schema only | Direct two-file loader; no Workflow/Role catalog traversal | Locked; not executed |
| T1 | Producer tests | `tests.test_agent_execution_authorization_grant_producer` only | Exact unittest module after complete static source review | Planned; not authorized |
| T2 | Optional Windows identity tests | `tests.test_windows_local_issuer_identity` only, if created | Exact unittest module after design and source review | Conditional; not authorized |
| T3 | AIO-043 regression | `tests.test_agent_execution_authorization_grant` only | Exact existing module, statically re-reviewed first | Planned; not authorized |
| T4 | AIO-047 integration regression | `tests.test_agent_execution_dispatch_admission` only | Exact existing module, statically re-reviewed first | Planned; not authorized |
| T5 | AIO-049 ownership regression | `tests.test_authorization_domain_ownership` only | Exact existing module, statically re-reviewed first | Planned; not authorized |
| T6 | Optional Windows ownership regression | `tests.test_windows_local_authorization_domain_owner` only if touched by integration | Exact module; requires matrix amendment confirming necessity | Conditional; not authorized |
| A1 | AST parsing | Explicit final changed Python paths only | `ast.parse`; no glob or discovery | Planned; paths locked after Phase 2 scope confirmation |
| M1 | Markdown | Exact AIO-050 Task files, new specification, and `core/terminology.md` only if changed | Explicit paths; no glob or broad traversal | Planned; not authorized |
| S1 | Package smoke | Exact `tests/package_installation_smoke.py --target-safe` only | Entire exact script revision must be re-read first | Planned; not authorized |
| G1-G7 | Git metadata/diff | Exact branch, HEAD, status, name-status, stat, diff check, cached stat | Bounded repository metadata and current diff | Authorized as explicitly requested |
| P1 | Python verification | Exact fixed interpreter path with approved version diagnostics only | Environment-only, no discovery | Phase 2 must freshly authorize and execute |
| X1 | Legacy Task validator | Prohibited | Catalog-wide behavior | Not authorized |
| X2 | Legacy Workflow validator | Prohibited | Workflow/Role catalog behavior | Not authorized |
| X3 | Legacy validator `--help` | Prohibited | Discovery execution forbidden | Not authorized |
| X4 | Repository-wide verification | Prohibited | Broad scope and protected-target risk | Not authorized |
| X5 | Bare unittest/pytest discovery | Prohibited | Unbounded test discovery | Not authorized |
| X6 | Recursive repository search | Prohibited | Unknown-file traversal | Not authorized |
| X7 | Broad Markdown traversal | Prohibited | Unknown-file traversal | Not authorized |
| X8 | Bare package smoke | Prohibited | Non-target-safe checkout behavior | Not authorized |
| X9 | Unknown command | Prohibited | No static safety basis | Not authorized |

The exact proposed structural commands are recorded for later authorization:

`V1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/task.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/task.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact AIO-050 task schema')"
```

`V2`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/workflow.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'workflows/architecture-change.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact architecture-change workflow schema')"
```

The current environment fact is
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`,
previously observed as CPython 3.12.10 and executable by the Codex sandbox
through a Human-granted Read+Execute ACL. Phase 2 must freshly verify it. This
path and ACL are execution-environment facts, not product architecture.

AIO-050 has no inherent real-symlink or elevation requirement. AIO-049's
privileged symlink criterion is not inherited.

## Protected-target boundary

During AIO-050, the protected target must not be opened, read, searched,
grepped, recursively enumerated, specifically listed, statted, hashed,
resolved, permission-inspected, or used as a fixture. Its identity must not be
investigated. Categorical AIO-050 non-access must remain certifiable.

No broad Task validation, Task catalog enumeration, Workflow catalog
enumeration, repository-wide verification, recursive repository search, broad
Markdown traversal, unknown-safety validator, bare package smoke, legacy
validator `--help`, or command absent from the approved matrix is permitted.

## Phase boundaries and Human checkpoint

Phase 1 ends when the exact four Task artifacts are present and fresh
Architect, Security, and Ownership/Integration design reviews all approve the
same final design with zero unresolved blocker or high-severity finding.

Phase 1 does not run final `documentation_consistency` or
`independent_review` Gates. Those require fresh post-implementation evidence.

Even after Phase 1 locks, AIO-050 Phase 2 intentionally remains pending until
AIO-051 Phase 1 is separately authorized and locked. AIO-051 is not created by
this Task.

The recommended program sequence remains:

```text
AIO-050 Phase 1 -> Human checkpoint
AIO-051 Phase 1 -> Human checkpoint
AIO-050 implementation and closure
-> rebaseline
-> AIO-051 implementation and closure
-> Local Operational Trust Integration
-> Dispatch Delivery
```

No later Task ID is allocated here.

## Phase 2 implementation checkpoint

### Authorization and scope separation

Direct Human instruction separately authorized AIO-050 Phase 2 after both
AIO-050 and AIO-051 Phase 1 design locks. The authorized work is limited to
the AIO-050 Producer foundation, focused synthetic validation, and this
technical checkpoint. AIO-051 remains an independent, unmodified Task whose
implementation has not started.

Phase 2 does not authorize Phase 3 final reviews, either final Quality Gate,
Human acceptance or closure, staging, commit, push, merge, release, AIO-052,
Tool work, dispatch, invocation, real Grant consumption or Admission, or any
protected-target access. The Task remains `in_progress` at this checkpoint.

The verified Phase 2 baseline remained `main` at
`145ac55215f272ecf8b94de95af9fd34e201ae25`, with a clean index and exactly
the eight expected untracked AIO-050/AIO-051 Phase 1 Task artifacts. No
AIO-051 artifact was changed during AIO-050 implementation.

### Implemented artifacts and boundary

Phase 2 created:

```text
core/agent-execution-authorization-grant-producer-specification.md
engineering_orchestration/agent_execution_authorization_grant_producer.py
tests/test_agent_execution_authorization_grant_producer.py
```

It also made three bounded consistency changes:

- `core/terminology.md` now defines the Producer and distinguishes Producer
  allocation from intrinsic Grant validation; and
- `engineering_orchestration/agent_execution_authorization_grant.py` now
  describes that module as the intrinsic value layer rather than implying
  that no trusted Producer can allocate Grant IDs or timestamps; and
- `tests/package_installation_smoke.py` now includes and imports the Producer
  module in its exact closed wheel-payload and installed-module probes.

No schema, package metadata, AIO-047 signature, AIO-049 authority surface, or
optional Windows identity-adapter file changed. The optional adapter remained
out of scope and was not created.

The implementation preserves the canonical eight-field AIO-043 Grant and
provides the exact locked Producer API, private composition factory, 24 closed
outcomes, 13 aggregate retry dispositions, frozen four-field result, private
adapter-minted principal/Human/policy proofs, private issued presentation,
pure nonsecret audit material, and paired unchanged one-argument AIO-047
authentication port.

Trusted composition claims one Producer/port pair permanently for one exact
Owned Session, including terminal composition failure. Proofs and
presentations are process-local, nonconstructible through their private
types, noncopyable, and nonserializable. Adapter minting is installed through
private one-time binding hooks and is bound to the exact Producer, adapter,
session, identity, generation, epoch, complete Run, and validity interval.

Production holds a fresh AIO-049 operation lease before entering the
session-scoped issuance registry. One trusted losslessly normalized UTC sample
drives both half-open proof-window checks and `issued_at`. The configured
default/maximum lifetime and any proof-authenticated shorter lifetime must be
positive, ordered, and bounded. Grant IDs use exactly 32 CSPRNG bytes encoded
as 64 hexadecimal characters, with four bounded allocation attempts and no
ID rebind.

The registry serializes same-Run issuance, retains allocated IDs, returns the
identical presentation only for exact retry, rejects changed requests and
Run-ID rebound, and retains non-evictable tombstones for ambiguous or terminal
post-reservation failure. Publication occurs only after ownership post-check,
clean operation-lease exit, and atomic successful-record installation.

The paired port authenticates only the exact registered presentation under
the supported session-owned coordinator path. It validates presentation and
record identity, exact session/full domain identity, issuer epoch, complete
Run, and all eight sealed Grant fields. Any registry contradiction fails
closed. It does not decide Grant currentness, revocation, consumption,
Admission, dispatch, or invocation.

### Phase 2 technical review loop

Bounded defect-focused architecture/integration and security inspection was
used during implementation. It identified and resolved lock ordering, fatal
lease cleanup, permanent session claiming, partial adapter-binding semantics,
exact audit correlation, exact string typing, existing-record coherence, and
port-integrity fail-closed handling. The final technical delta inspection had
zero unresolved blocker and zero unresolved high-severity finding.

This was implementation-time technical validation only. It is not any Phase
3 final Architect, Security, Ownership/Integration, or Independent Review and
does not satisfy either final Quality Gate.

### Phase 2 validation evidence

All executed tests are synthetic or in-memory. They perform no real Human or
policy authentication, real Grant issuance or consumption, authoritative
Admission, Tool resolution, dispatch, invocation, or protected-target access.
The selected interpreter is exactly
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`,
freshly verified as Python 3.12.10.

Completed focused evidence:

| Matrix ID | Result |
| --- | --- |
| P1 | PASS; exact interpreter reported Python 3.12.10 |
| V1 | PASS; exact AIO-050 Task schema |
| V2 | PASS; exact `architecture-change` Workflow schema |
| T1 | PASS; 18 Producer tests, including all 30 locked scenarios |
| T3 | PASS; 84 AIO-043 regression tests |
| T4 | PASS; 27 focused AIO-047 integration regression tests |
| T5 | PASS; 11 focused AIO-049 ownership regression tests |
| A1 | PASS; exact four changed Python paths parsed with `ast.parse` |
| M1 | PASS; five exact Markdown paths, zero issues |
| S1 | PASS; target-safe editable and wheel installation/import smoke |

T3, T4, and T5 were executed only after complete static inspection of their
exact source modules. The target-safe package-smoke source was likewise read
completely before execution; its later three-line semantic delta was inspected
before the affected check was rerun. Final Git evidence is collected only
after this evidence text passes its final explicit-path Markdown check.

The first completed S1 run exposed a closed-payload expectation that omitted
the new Producer module even though the built wheel correctly contained it.
Phase 2 added the module to that expectation and installed-import probe, reran
A1, and reran only S1. One intermediate rerun was transiently blocked by
Windows Application Control for a generated temporary `aio.exe`; the identical
final rerun passed both editable and wheel modes. The initial network-restricted
sandbox attempts were stopped after repeated ten-minute silence and supplied
no pass evidence.

The exact commands used for completed executable validation were:

`P1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B --version
```

`V1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/task.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/task.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact AIO-050 task schema')"
```

`V2`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/workflow.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'workflows/architecture-change.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact architecture-change workflow schema')"
```

`T1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_authorization_grant_producer -v
```

`T3`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_authorization_grant -v
```

`T4`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_dispatch_admission -v
```

`T5`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_authorization_domain_ownership -v
```

`A1` (final changed-path form):

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import ast,pathlib; paths=(r'engineering_orchestration/agent_execution_authorization_grant.py',r'engineering_orchestration/agent_execution_authorization_grant_producer.py',r'tests/test_agent_execution_authorization_grant_producer.py',r'tests/package_installation_smoke.py'); [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in paths]; print('PASS exact changed-path AST parse')"
```

`M1`:

```powershell
npx --yes markdownlint-cli2 'core/agent-execution-authorization-grant-producer-specification.md' 'core/terminology.md' '.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/context.md' '.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/acceptance-criteria.md' '.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/review.md'
```

`S1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B tests/package_installation_smoke.py --target-safe
```

`G1` through `G7`:

```powershell
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git diff --name-status
git diff --stat
git diff --check
git diff --cached --stat
```

## Phase 2 security remediation checkpoint

### Authorization and preserved review state

Direct Human authorization reopened Phase 2 solely to remediate the two medium
findings from the first fresh Phase 3 Security final review. That historical
review remains **CHANGES REQUIRED** with zero blocker, zero high, two medium,
and zero low findings. Its result is not rewritten as an approval.

The earlier Phase 3 Architect approval predates this remediation and is not
reusable. Ownership/Integration did not complete, and no Independent Review,
Quality Gate, final Human approval, closure, staging, or commit occurred. All
eight criteria 105 through 112 remain pending, so acceptance remains 104/112
and Phase 3 must restart from fresh final reviews.

AIO-051 remains `in_progress` at its locked Phase 1 baseline. Its four Task
files were not modified and implementation did not start.

### Bounded security changes

**SEC-050-1** arose because configured Human and policy adapters could pass a
malformed proof subject into authority-bearing state before exact type and
intrinsic Run validation. A later equality check could then invoke equality
controlled by that malformed object.

The remediation uses the existing canonical
`validate_agent_execution_run(...)` contract. Both authority-proof minters now
require `type(run) is AgentExecutionRun` and successful canonical intrinsic
validation before sampling an adapter epoch or storing a proof. Production,
existing-issuance coherence, and paired-port verification repeat validation
before equality. A malformed embedded subject fails through the existing
`authority_proof_invalid` surface and cannot participate in Run comparison.

Focused Human and policy tests cover ordinary non-Run values, custom-equality
objects, exact Runs with intrinsically invalid scalar state, corrupted stored
proof subjects, and unchanged success for normal exact valid subjects. A
paired-port test also proves that corrupted Human and policy subjects fail
closed without invoking their equality methods.

**SEC-050-2** arose because the permanent AIO-049 session claim preceded
adapter binding while cleanup covered `Exception` only. A hook could retain a
minter and escape with `KeyboardInterrupt`, `SystemExit`, or another
`BaseException`, bypassing terminal closure.

Only the narrow adapter-binding block now catches escaping `BaseException`.
It closes the partially composed state under the existing state lock and then
uses a bare re-raise. The permanent session claim remains installed, retained
minters converge on the closed state, and the same session cannot be claimed
again. Tests cover the original exact `KeyboardInterrupt` and `SystemExit`
objects, closed state, invalid retained minter, empty proof/issuance/
presentation/allocated-ID registries, permanent claim retention, and absence
of port, load, revoke, or Admission-related session calls.

This cleanup guarantee applies to Python failures that unwind through the
composition boundary. It makes no claim for non-unwinding termination such as
`os._exit`, process kill, kernel termination, or power loss.

The remediation adds no public API or schema, changes no Grant field, leaves
the AIO-047 authentication-port signature and AIO-049 ownership/session/
generation semantics intact, introduces no persistence, and preserves the 24
outcomes and 13 retry dispositions.

### Fresh affected remediation evidence

All tests remain synthetic or in-memory. No real authentication, Grant,
Admission, Tool resolution, dispatch, invocation, or protected-target access
occurred.

| Matrix ID | Remediation result |
| --- | --- |
| P1 | PASS; exact interpreter reported Python 3.12.10 |
| T1 | PASS; 22 Producer tests, including all 30 locked scenarios |
| T3 | PASS; 84 AIO-043 regression tests |
| T4 | PASS; 27 focused AIO-047 integration regression tests |
| T5 | PASS; 11 focused AIO-049 ownership regression tests |
| A1 | PASS; exact two remediation-changed Python paths parsed with `ast.parse` |
| M1 | PASS; exact three remediation-changed Markdown paths, zero issues |
| V1 | PASS; exact AIO-050 Task schema |
| V2 | Not rerun; no Workflow semantic or file change |
| S1 | Not rerun; package membership, metadata, import expectations, and smoke source are unchanged |

The prior fully reviewed target-safe package-smoke source and its editable and
wheel PASS evidence remain applicable to package membership. The remediation
matrix does not require smoke after every runtime-only change. No bare smoke
was used.

The exact fresh commands were:

`P1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B --version
```

`T1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_authorization_grant_producer -v
```

`T3`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_authorization_grant -v
```

`T4`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_dispatch_admission -v
```

`T5`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_authorization_domain_ownership -v
```

`A1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import ast,pathlib; paths=(r'engineering_orchestration/agent_execution_authorization_grant_producer.py',r'tests/test_agent_execution_authorization_grant_producer.py'); [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in paths]; print('PASS exact remediation changed-path AST parse')"
```

`V1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/task.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/task.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact AIO-050 task schema')"
```

`M1`:

```powershell
npx --yes markdownlint-cli2 'core/agent-execution-authorization-grant-producer-specification.md' '.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/context.md' '.ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/review.md'
```

Final G1 through G7 use the already recorded exact bounded Git commands. No
other validation category was executed. Phase 2 is complete including this
security remediation, AIO-050 remains `in_progress`, and fresh Phase 3
authorization is required before any final review resumes.

## Phase 2 Independent-Review policy-decision remediation checkpoint

### Authorization and preserved review state

Direct Human authorization returned AIO-050 to Phase 2 only to remediate the
single HIGH finding from the latest Formal Independent Review. That Formal
Independent Review remains **CHANGES REQUIRED** with zero blocker, one high,
zero medium, and zero low findings. It is preserved separately from the first
historical Security review and its remediated SEC-050-1 and SEC-050-2 findings.

No fresh Phase 3 review, Independent Review, Quality Gate, Human approval,
closure, staging, commit, AIO-051 change, Tool work, dispatch, invocation, or
protected-target access was authorized or performed. Criteria 105 through 112
remain pending, acceptance remains 104/112, and AIO-050 remains `in_progress`.

### Independent Review HIGH finding and remediation

The Independent Review found that policy proof minting accepted only exact
`allow` or `deny`, but stored proof verification did not independently
revalidate `_decision`. Production rejected only literal `deny`, so a malformed
non-deny value could continue as positive authority. The root cause was a
negative deny check instead of an exact positive allow requirement.

The minting boundary remains unchanged and continues to require the exact
built-in strings `allow` or `deny`. The policy-proof structural verifier now
independently requires an exact built-in canonical `allow` or `deny`; every
malformed, missing, subclassed, or custom decision fails as the existing
`authority_proof_invalid` outcome before adapter validation or time sampling.
The production decision seam then requires exact `allow` to continue. Exact
canonical `deny` retains the existing `policy_denied` outcome, while every
other value fails as `authority_proof_invalid`.

Focused tests cover exact `allow`, exact `deny`, `ALLOW`, `Allow`, `yes`, an
empty string, `None`, an equal-looking string subclass, and a custom object
whose equality, truthiness, and `lower()` operations would spoof approval.
They also mutate a valid stored `allow` proof to every malformed value and
prove rejection before adapter validation, clock sampling, or Grant-ID use.
The normal policy-allow issuance path remains successful.

This remediation does not change the Grant, Grant schema, AIO-047 port,
AIO-049 ownership semantics, Producer persistence, 24 outcomes, or 13 retry
dispositions. SEC-050-1 exact-Run validation-before-equality and SEC-050-2
narrow `BaseException` binding cleanup remain unchanged and pass in the same
Producer suite.

### Focused remediation evidence

| Matrix ID | Result |
| --- | --- |
| P1 | PASS; exact interpreter reported Python 3.12.10 |
| T1 | PASS; 24 Producer tests, including all 30 locked scenarios |
| T4 | PASS; 27 focused AIO-047 integration regressions |
| A1 | PASS; exact two remediation-changed Python paths parsed with `ast.parse` |
| M1 | PASS; exact allowlisted AIO-050 Markdown paths, zero issues |
| V1 | PASS; exact AIO-050 Task schema |
| T3 | Not rerun; the canonical Grant and its intrinsic validator did not change |
| T5 | Not rerun; AIO-049 ownership code and semantics did not change |
| S1 | Not rerun; package membership, metadata, imports, and smoke source did not change |

Package smoke is not required for this runtime-and-test-only remediation. The
prior target-safe editable and wheel PASS remains the applicable packaging
evidence, and bare smoke remains prohibited. A future fresh Phase 3 review must
independently determine whether the HIGH finding is closed.

## Fresh post-remediation Phase 3 checkpoint

### Authorization, baseline, and historical evidence

Direct Human authorization permitted only fresh final specialist reviews, a
new Formal Independent Review, the two required Quality Gates, bounded
AIO-050 evidence reconciliation, and preparation for Human Control. It did
not authorize implementation or remediation, AIO-051 work, final Human
approval, Task closure, staging, commit, push, merge, tag, release,
publication, AIO-052, operational trust integration, real authority
operations, dispatch, invocation, or protected-target access.

The bounded baseline inspection confirmed branch `main`, HEAD
`145ac55215f272ecf8b94de95af9fd34e201ae25`, a clean index, and only the
expected scoped AIO-050 paths plus the four untouched AIO-051 Phase 1 Task
paths. AIO-050 remained `in_progress` at 104/112 before this review sequence.
AIO-051 remained `in_progress`, its Phase 1 design lock remained intact, and
its implementation remained unauthorized and unstarted.

The first historical Security final review remains **CHANGES REQUIRED** with
SEC-050-1 and SEC-050-2 each recorded at MEDIUM. The historical Formal
Independent Review remains **CHANGES REQUIRED** with IR-050-1 recorded at
HIGH. These failed reviews are preserved separately and are not rewritten as
approvals by the fresh evidence below.

### Fresh specialist review convergence

The required sequence completed against the final post-remediation snapshot:

| Review | Result | SEC-050-1 | SEC-050-2 | IR-050-1 | Findings |
| --- | --- | --- | --- | --- | --- |
| Architect final review | APPROVE | CLOSED | CLOSED | CLOSED | 0 blocker, 0 high, 0 medium, 0 low |
| Security final review | APPROVE | CLOSED | CLOSED | CLOSED | 0 blocker, 0 high, 0 medium, 0 low |
| Ownership/Integration final review | APPROVE | Not separately required | CLOSED | Integration impact: NONE | 0 blocker, 0 high, 0 medium, 0 low |

The reviews confirmed the unchanged eight-field Grant and schema, exact
complete-Run authority, separation of authentication, entitlement, authority
proof, presentation, currentness, revocation, Admission, dispatch, and
invocation, and preservation of the AIO-047 and AIO-049 responsibility
boundaries. They also confirmed no Producer persistence, 24 outcomes, 13 retry
dispositions, and no new public schema or concrete real identity adapter.

SEC-050-1 is closed: exact `AgentExecutionRun` type and canonical intrinsic
validation precede equality on Human and policy paths, so malformed or
custom-equality subjects fail closed. SEC-050-2 is closed: the narrow
adapter-binding boundary catches escaping `BaseException`, terminally closes
state, invalidates retained minters, preserves the permanent session claim,
rejects same-session recomposition, and re-raises the original
`KeyboardInterrupt` or `SystemExit`; no non-unwinding cleanup guarantee is
claimed.

IR-050-1 is closed: minting and independent stored-proof verification require
the exact built-in canonical strings `allow` or `deny`. Only exact `allow` can
continue authorization. Exact `deny` produces `policy_denied`; case variants,
aliases, empty or missing values, string subclasses, custom objects, and
tampered stored decisions produce `authority_proof_invalid`. No negative-deny,
truthiness, case-folding, alias, or custom-equality authorization path remains.

### Fresh Formal Independent Review

After specialist convergence, a new independent Reviewer inspected the
current artifacts rather than reusing the historical failed result. The
Reviewer independently confirmed all three historical defects were valid and
all three remediations were present and complete.

- Independent technical assessment: **APPROVE**
- Independent security assessment: **APPROVE**
- Independent process assessment: **COMPLIANT**
- SEC-050-1 independent status: **CLOSED**
- SEC-050-2 independent status: **CLOSED**
- IR-050-1 independent status: **CLOSED**
- Formal Independent Review: **APPROVE**
- Findings: none
- Severity counts: 0 blocker, 0 high, 0 medium, 0 low

The independent process assessment recorded `NO` for legacy validator help,
unknown-safety validation, broad Task or Workflow catalog enumeration,
repository-wide verification, recursive repository search, broad Markdown
traversal, non-target-safe smoke, matrix-unauthorized validation, protected-
target access, and AIO-051 modification. Categorical AIO-050 protected-target
non-access remains certifiable.

### Quality Gates, acceptance, and Human Control

`documentation_consistency` is **PASS** with no waiver. Exact target-safe
comparison found the canonical specification, terminology, implementation
status, and Task-local evidence consistent about exact positive `allow`,
canonical `deny`, malformed-decision rejection, exact Run proof validation,
the narrow `BaseException` cleanup boundary, same-process trust, unchanged
Grant and public-schema surfaces, no persistence, restart and fencing limits,
the operational exclusions, and AIO-051 separation.

`independent_review` is **PASS** with no waiver. A different Agent execution
instance reviewed the complete current snapshot with sufficient context,
approved the technical, security, and process assessments, independently
closed SEC-050-1, SEC-050-2, and IR-050-1, and reported no finding.

Acceptance criteria 105 through 110 are therefore complete without changing
their wording. Acceptance is 110/112. Criterion 111, final Human architecture,
security, schema, trust-boundary, and acceptance approval, remains pending.
Criterion 112, separate Human Task-closure and local-commit authorization,
also remains pending. AIO-050 remains `in_progress` and is ready for Human
final approval, but no Human approval or closure is recorded here.

No technical test, schema validator, AST check, or package smoke was rerun for
ceremony. The retained current evidence remains Producer 24/24 PASS, all 30
locked scenarios PASS, SEC-050-1 and SEC-050-2 regressions PASS, AIO-047
27/27 PASS, AST PASS, Task schema PASS, and prior target-safe editable and
wheel smoke PASS. The latest remediation changed no package membership, so the
matrix does not require another smoke run. The exact explicit-path Markdown
check was rerun only for the newly reconciled Task documentation and passed
with zero issues across all five approved paths.

No real authentication, Grant issuance, Tool resolution, Admission, dispatch,
invocation, or protected-target access occurred. AIO-051 remains untouched at
its locked Phase 1 baseline. No staging, commit, push, merge, tag, release,
publication, AIO-052 creation, or Task closure occurred. The required stopping
point is Human Control.

## Final Human approval record

On 2026-10-01, the Human gave final architecture, security, schema,
trust-boundary, and acceptance approval for AIO-050 on the basis of the
completed three phases, closed SEC-050-1, SEC-050-2, and IR-050-1 findings,
approved specialist and Formal Independent Reviews, both Quality Gates passing
without waiver, clean process-safety evidence, certifiable protected-target
non-access, and successful index reconciliation without working-tree content
change.

- Human final approval: **APPROVED**
- Final Human acceptance: **APPROVED**
- Acceptance: **111/112**
- Criterion 112: **PENDING**
- Task status: `in_progress`
- Ready for separate closure authorization: **YES**

This dated record supersedes only the pending Human-approval state at the
preceding Phase 3 stopping point. It does not authorize Task closure, a status
change, staging, commit, or AIO-051 implementation.

## Final closure record

On 2026-10-01, the Human separately authorized AIO-050 Task closure, the status
change to `completed`, and exactly one local commit containing only the ten
approved AIO-050 paths. This authorization satisfies criterion 112 using its
existing wording.

- Closure date: 2026-10-01
- Human final approval: **APPROVED**
- Final Human acceptance: **APPROVED**
- Acceptance: **112/112**
- Task status: `completed`
- AIO-051 modification or staging authorized: **NO**
- Push, merge, tag, release, or publication authorized: **NO**

All historical failed-review evidence remains preserved. The fresh final
reviews and both Quality Gates remain approved and passed without waiver.
AIO-051 remains `in_progress` at its locked Phase 1 baseline, with its four
Task artifacts excluded from this closure commit.
