# AIO-057 Context — Locked Phase-1 Design R2

## Authorization, baseline and phase boundary

Repository: D:\Dev\ai-engineering-orchestra. Verified branch: main.
Baseline HEAD: b6566cdb8538e63307d1bae536fb56929a2b32c3.
Phase 1 permits investigation, remediation of SEC-057-1, SEC-057-2,
INV-057-1 and INV-057-2, independent read-only review, and these four Task
artifacts after all five review scopes approve. R2 and the two explicit
protocol clarifications received all five independent approvals before any
artifact creation. No production code, tests, validators, migration, staging
or commit is authorized or performed in this phase.

The Task remains in_progress. Phase 2 needs separate Human authorization.
Formal documentation_consistency and independent_review Quality Gates remain
future final-review work against actual implementation evidence. Phase-1
design approval neither executes nor satisfies those Gates or final Human
acceptance. E01-E24 are future AIO-058 obligations, not completed or skipped
AIO-057 tests.

## Objective and preserved trust distinctions

Define the smallest private ephemeral foundation for preparing and freshly
assessing one exact current Claim subject, with subject-wide single-consumption
state and a precise future execution-entry contract. AIO-057 stops before Tool
invocation and cannot positively authorize an effect on the existing v3 ledger.

Grant, Admission, Dispatch Intent, Claim, Lease and canonical Tool Binding each
remain insufficient as continuing invocation authority. Historical Claim lookup
cannot establish current ownership or recreate an executor capability. Prepared
JIT authorization and nonconsuming diagnostic verification are not permission
to perform an effect.

Direct dependencies are AIO-049, AIO-050, AIO-051 and AIO-056. AIO-055 outbox,
AIO-047 Admission storage and canonical Core prerequisites are transitive
responsibilities; AIO-053 supplies composition/compatibility evidence.

## Physical-attempt identity decision

Option A uses the authoritative current Claim, with no new scalar
execution_attempt_id. Option B adds a scalar physical invocation ID. R2 selects
A after fresh comparison, because an additional ID cannot supply exclusion:
without a shared subject cell, distinct IDs still permit duplicate entry; with
that cell, another ID adds no safety. Crash/restart exclusion comes from the
mandatory future durable Dispatch entry, not a remembered opaque process ID.

Let D be the exact Dispatch composite
(authorization_domain, issuer_kind, issuer_id, grant_id). The physical key K is
(exact pinned ledger identity, D, claim_id, lease_generation). AIO-056 owns
claim_id creation, ledger-wide uniqueness, immutable Dispatch association and
generation fencing. Renewal retains the same Claim/generation and changes only
the authoritative effective expiry. Reclaim creates a new Claim/generation.
Run is the complete semantic occurrence, not physical invocation identity;
same run_id alone is insufficient, and semantic retry requires a new Run.

The full authorization subject S includes K, genuine executor incarnation and
capability, complete Run and canonical Binding. Internal binding additionally
fixes the genuine owned Session, exact Store, full authorization-domain identity
including generation, process/authorizer epoch, Producer and resolver snapshot.
K is only an index: every lookup compares every complete subject/binding field.
A conflicting subject cannot obtain a second cell under the same physical key.

At most one guarded entry may be authorized per exact Claim. The mandatory
future permanent UNIQUE D Entry strengthens this to at most one entry per
Dispatch across all Claims, generations and restarts, including after a
successful or failed resolved result. Each permitted physical effect is tied
to the recorded Claim, without a second scalar ID. This is exclusion, not an
exactly-once invocation/success or recovery-liveness guarantee.

## Session-wide registry, capability and lifecycle

There is exactly one process-local registry for a genuine Session, spanning
all logical workers. Composition cannot replace the registry, create a second
authorizer, close/recompose it or evict terminal cells to bypass exclusion.
The private working name ExecutionAttemptAuthorization denotes an opaque,
read-only subject handle to shared mutable consumption state; it is not a
new canonical serialized Core object or public schema.

Direct construction, forged registration, copy/deepcopy, serialization/pickle,
cross-process transfer and foreign process/session/authorizer epochs reject.
An ordinary reference alias is valid and shares the original cell. Opaque
object identity is provenance, not a new independent authorization subject.

The cell state machine is:

no cell -> PREPARING -> PREPARED -> CONSUMING -> CONSUMED

REJECTED, ABANDONED and UNCERTAIN are permanent terminal states. Successful
consumption is terminal; no state transitions back to PREPARED. Tombstones
are non-evictable for the Session lifetime.

Preparation reserves the one cell. PREPARING is never published as authority.
A racing caller receives preparation_in_progress rather than waiting while
holding operational locks. Exact retry of a published preparation, with the
same proof-object fingerprints, revisions and epochs, performs fresh checks
and returns the identical registered capability/cell. A changed proof
fingerprint returns already_prepared without another capability. Subject
conflicts never create alternative state.

Publication occurs only after the preparation watermark transaction has an
acknowledged COMMIT and the owned-operation exit/post-check succeeds. A final
cell-only publication checks that lifecycle/state still permit publication;
it does not acquire earlier locks while holding C. Interrupted or uncertain
publication burns the reservation and never leaks a capability. Historical
ledger evidence cannot publish or restore it.

Lost response or lost caller reference may recover only that identical live
object through exact retained proof fingerprints and fresh checks. Lost
proofs, a changed-proof retry or a process restart cannot recreate authority.
A pre-reservation ordinary negative outcome may be reassessed. Once final
consumption reserves CONSUMING, any failed validation, clock/Store failure,
confirmed rollback, unknown COMMIT or lost continuation terminalizes the
subject. Explicit abandonment and close invalidate all aliases. There is no
same-Claim rearm even after a confirmed entry rollback. A fresh reclaimed
Claim can enter only if the future Store proves no permanent Dispatch Entry.

Process restart destroys capabilities, proofs, executor incarnation, guard
scopes and continuation authority. Genuine ownership may restart through the
existing AIO-049 lifecycle, but identity/history does not restore authority.
Existing Entry history supports classification only and cannot mint an effect
continuation.

## Exact current-state composition and ownership

AIO-049 owns the genuine owned Session, OS ownership protection, pinned ledger
and complete operation lifecycle lease. Retain session.operation() throughout
the applicable trusted operation. Identity fields alone do not establish
ownership. Session close/fence waits for quiescence without holding protections
needed by the in-flight operation; no AIO-049 change is proposed.

AIO-056/its owned Store establishes the exact immutable Admission/Intent/Claim
association, complete Run and Binding, highest current generation, exact
claim_id, genuine current executor capability, authoritative effective
half-open Lease interval, revocation state, complete Store audit and pinned
ledger integrity. Current query results are point-in-time evidence, not
continuing invocation authority. No historical lookup, copied PID/ID or raw
connection substitutes for this check. New private held-lock/current-assessment
scope may be factored at session._store; it must retain Store ownership, time,
watermark and audit behavior. No raw Store/SQL connection escapes. Public
Claim/Lease/renewal APIs remain unchanged.

AIO-050 owns principal and decision proof provenance, enabled issuer epoch,
exact entitlement and decision validity. A new private entry-purpose decision
must bind execution_entry and exact S. Existing private Run proof payloads may
be reused with separate private purpose/subject metadata and registration;
issuance proofs, authenticated Grant presentations and consumed Grants do not
become entry proofs. Entry-purpose proofs are minted in participating
mutation/mint scopes before preparation/read/consumption scopes.

Factor and reuse the existing provenance, principal, enabled-epoch,
Human/policy allow, window and exact entitlement predicates. Do not call
_prepare_attempt or any issuance/ID-generation path. The original consumed
Grant interval governs issuance/Admission, not a new continuing execution
window; its expiry alone does not veto otherwise valid fresh entry authority.
Fresh entry-purpose proof and Lease windows must hold at the new authorization
time. No parallel issuer authority, entitlement or policy engine is permitted.

Fresh current Actor/Runtime/Inference availability, applicability,
compatibility, Runtime operation capability, exact environment/resource
permission and effective Task-wide Execution Mode are composed by the
canonical pure prerequisite/mode logic. The complete reconstructed Run must
equal the immutable parent Run; blocked/unknown does not become allowed.
No reassignment, routing substitution or inference fallback occurs.

AIO-051 owns canonical Binding (complete Run, exact tool_id), permanent exact
runtime/environment/operation route and deeply immutable configured registry
snapshot. Resolve through the captured canonical resolver and compare the
complete Binding. Historical resolution remains total for retired routes;
JIT retirement rejection is a separate snapshot check. Missing, mismatched or
corrupt registration rejects. There is no live mutable retirement state or
retirement guard to invent. Retirement/configuration change takes effect
through terminal teardown and a new snapshot/binding/process lifecycle, never
hot replacement of an active resolver. The existing identity-only native
repository-read registration does not gain a callable in AIO-057.

## Private authority guard protocol

G is the private AIO-057 coordination root bound install-once to one genuine
Session/Producer epoch. It is a mechanical exclusive guard, reentrant only on
the owning thread, not a new policy/authority engine. Registration occurs
before participant publication.

Ownership attaches to each underlying authoritative mutable state partition,
including aliases and proxies, not merely a wrapper object. A mutable
partition can belong to only one live G; composition rejects a different live
guard owner. Immutable snapshots can be shared. Multi-domain/multi-guard
sharing or an uncoordinated external mutation source is unsupported and fails
closed. Every mutation alias must participate.

Conceptual private APIs, not public runtime signatures:

| Operation | Required contract |
| --- | --- |
| compose_execution_authority_guard(bound_session, producer_binding, participants) | Reserve composition without nested operational locks; bind once; validate exact participants/underlying partitions before publication. |
| read_scope(owned_operation) | Verify genuine active same-thread S; acquire G then P; yield a sealed nontransferable scope with exact binding/revisions. |
| mutation_scope(exact_participant, kind) | Acquire G and the applicable participant/P protection in order; apply the existing authoritative mutation and publish revision/invalidation atomically. |
| locked_current_validation(scope, S, principal, entry_decision, T) | Reuse canonical and AIO-050 leaf predicates at caller-supplied authoritative T; require protections already held; no issuance or hidden earlier acquisition. |
| close/invalidate | Terminalize the binding and outstanding cells; quiescence waits occur outside protections required by in-flight work. |

Every effective mutation in the following sources participates separately:
issuer enable, disable and re-enable/epoch change; principal logout, session
invalidation and adapter epoch; Human approval withdrawal, membership and
epoch; policy deny, decision revision, invalidation and configuration change;
Producer/authentication-port close; proof mint/recognizer membership
registration; publication of fresh availability, applicability, compatibility,
Runtime capability, exact resource permission and effective Task mode.
Immutable entitlement/configuration changes require terminal teardown and a
new binding rather than in-place replacement.

Successful writes atomically update underlying authority and its registered
revision/invalidation. Failed or ambiguous updates never leave a silently
retained allow: inability to prove coordinated current state terminalizes the
binding. Acquisition failure yields no authority; guard loss, integrity
failure or uncertain source state fails closed and suppresses any not-yet-
started effect. Restart invalidates the entire old guard epoch.

Leaf getters/validators operate under the supplied scope. They cannot mutate,
mint/register proof, await, perform Tool IO, schedule delayed work or call
back into Producer, Session or Store. Leaf-local locks cannot acquire earlier
protections. External/asynchronous sources that cannot provide this cooperative
state and mutation contract are unsupported; an observe_issuer_state call or
boolean observation is not a lease. Queued but not yet effective mutations do
not count as effective revocation.

Minimum AIO-050 private extension: optional install-once guard binding through
private composition; participating state/produce/mint/authenticate/close paths
use G-before-P when attached; factor a held-lock entry validation helper reusing
existing predicates; add the private entry-purpose registration described
above. Public Producer/port signatures, eight-field Grant, issuance
cardinality, lifetime and burned issuance registry remain unchanged. Actual
factoring viability is unverified implementation work.

## Acquisition order, release and deadlock prevention

Global acquisition order:

S owned operation -> G exclusive authority guard -> P Producer-state lock
-> W Store writer BEGIN IMMEDIATE -> C subject-cell mutex

Every path uses the ordered applicable subset. Never acquire an earlier
protection while holding a later one. Mutation paths use G/P and never acquire
S afterward. Existing produce composition uses S/G/P; an authentication
coordinator acquires S then G/P before Store work. Held-lock helpers do not
call public methods that acquire another owned lease or nonreentrant P.
Proof minting precedes read/prepare/consume; leaf callbacks cannot mint.

Composition reservation locks never nest with operational locks: reserve,
release, compose, then publish. No blocking wait for PREPARING publication or
teardown under locks required by the publisher/operation. No provider callback
reentry. These rules exclude reverse acquisition cycles rather than assuming
that lock names alone prevent deadlock.

Cleanup releases still-held resources in reverse order, with the explicit
SQLite COMMIT exception: COMMIT necessarily releases W while C is still
finishing its terminal transition. Known success marks CONSUMED and releases
C; failure/unknown terminalizes and releases C. Never reacquire W while C is
held. Do not claim that W survives COMMIT.

Future physical effect retains S/G/P and the sealed thread-bound continuation
once-state through its first irreversible action, conservatively through the
entire bounded synchronous effect. C is not held across Tool IO. Permanent
durable UNIQUE D exclusion protects against later entries after W releases.
After the effect/terminal exit, release P/G/S; any loss or exit ambiguity is
reported conservatively without rollback or rearm.

## Logical authorization time and irreversible boundary

Tprep and diagnostics are point-in-time checks only. A prepared capability does
not reserve wall-clock validity. AIO-057 v3 has no positive durable-entry or
effect API and cannot infer Entry absence from a schema with no Entry table.

In the future trusted entry transaction, hold S/G/P/W/C, establish complete
audited immutable parent/current Claim facts and frozen current authority
snapshots, reserve CONSUMING, then sample authoritative Store UTC time T once.
Use this same T for the Lease and fresh entry-proof half-open windows,
revocation/current generation assessment and durable watermark. No TTL,
untrusted clock, resampling fiction, regression clamping or altered watermark
semantics substitutes for it.

T is the successful Entry's logical authorization point, conditional on an
acknowledged successful durable Entry COMMIT. Checks before COMMIT are
provisional. W serializes effective generation/revocation mutations and G/P
serializes effective authority mutations through COMMIT. Lease/proof expiry
before T rejects. Expiry after valid T, even before COMMIT or physical effect,
does not retroactively invalidate a successfully committed Entry. This is not
a promise of unexpired Lease at physical effect time.

The irreversible effect boundary is the first action capable of accessing
target metadata, opening or reading the target, or any external Tool action.
Adapter naming does not postpone that boundary. No such action is permitted
before acknowledged Entry COMMIT. Only pure pre-effect checks are permitted
before it. Later effective revocation or reclaim blocks future entry and does
not retroactively cancel the accepted original Entry; detected actual
ownership/guard loss before effect suppresses its original continuation.

## Mandatory future AIO-058 durable entry and consumer state machine

This persistence is mandatory future AIO-058 work, not an AIO-057 migration.
AIO-058 must implement a trusted same-ledger Store capability and audit its
presence/integrity before any effect. Current v3, absent/corrupt/ambiguous
Entry storage, or unverifiable absence must fail closed.

Consumer states:

PREPARED -> CONSUMING / ENTRY_AUTHORIZING -> ENTRY_COMMITTED
-> EFFECT_STARTED -> RESULT_OR_AMBIGUITY

The future immutable Entry has permanent UNIQUE D and exact immutable
Claim/Admission references. Minimal semantic facts are D, claim_id,
lease_generation, executor_instance_id and authorization T in the Store's
canonical text/key form. Complete Run and Binding are inherited from fully
verified immutable Admission rather than duplicated. No additional scalar
attempt ID is required. The Entry is never deleted, reset or rebound,
including after successful, failed or resolved Result.

The future Store transaction audits exact current subject and Entry absence,
reserves CONSUMING, takes final T, checks all current facts, inserts Entry and
watermark, completes final audit and performs one COMMIT. No target IO occurs
inside these diagnostics or transaction.

Only acknowledged successful COMMIT creates one original same-process,
same-thread sealed once-only bounded synchronous continuation. The cell becomes
CONSUMED and C releases. The continuation retains S/G/P and its private
once-state, is neither transferable nor an async/deferred callback ticket,
and cannot be derived from Entry history. Claim, capability or diagnostic
verification alone cannot dispatch a Tool.

| Cut or event | Required behavior |
| --- | --- |
| Confirmed rollback after consumption starts | Terminal Claim subject; no effect or same-Claim rearm. |
| COMMIT unknown, actual rollback or actual commit | UNCERTAIN; no effect. Later reconciliation cannot mint the lost continuation, even when commit is proven. |
| Crash before Entry COMMIT | Atomic rollback implies no compliant authorized effect; new Claim still needs fresh authority and audited absence. |
| Crash after Entry COMMIT before Tool call | Permanent occupied Entry; possibly zero effects; no automatic call after restart. |
| Crash after effect before Result | Unresolved Entry; no re-performance. |
| Lost acknowledged response or continuation | History-only classification; no replacement effect authority. |
| Detected ownership/guard loss before effect | Suppress continuation; keep Entry occupied; no replay. |
| Failure during/after effect or owned exit | Ambiguity; never rollback effect, rearm or reinvoke. |

AIO-056 reclaim can remain unchanged and may produce generation N+1 after
Entry COMMIT, while the original invocation is in-flight or unresolved.
Permanent UNIQUE D blocks N+1 and every other claimant from a second Entry,
even if the first Result later resolves. W release does not open a second
invocation path. Reclaim before first Entry fences the older Claim through the
fresh current-generation check. Future recovery can permit a first entry
for a fresh reclaimed Claim only after a complete pinned-store audit proves
no committed Entry. Under the compliant gate, no Entry means no effect was
authorized. Intentional semantic retry requires a new Run/Grant/Admission/
Intent and explicit fresh authority, never replay of the old Dispatch.

This model permits zero effects after accepted Entry and unresolved effects
without Result. It makes no exactly-once success or automatic recovery/liveness
claim. Actual invocation, transport, Result and Journal belong outside
AIO-057.

## Smallest API and deterministic failure taxonomy

Private composition, prepare, nonconsuming diagnostic verify, abandon/close
and held-lock subject transitions form the foundation. Future trusted Store
consumer uses those transitions but must implement its own durable entry
capability before receiving any positive effect continuation. No standalone
verify result permits invocation; no public JIT schema, raw Store API or
Claim/Lease widening is introduced.

Closed outcome categories remain distinct:

- Preparation: prepared, exact_retry, preparation_in_progress,
  already_prepared and subject_conflict.
- Current Claim: no_active_claim, lease_expired, stale_generation,
  superseded_claim, wrong_dispatch, wrong_run, wrong_executor,
  executor_capability_unavailable and foreign_ledger/session.
- Authority/current facts: denied or unresolved current authority,
  issuer_disabled, revoked, invalid entry-purpose proof, invalid principal
  provenance, wrong issuer/channel/subject, stale epoch/revision, unsupported
  source, changed mode and blocked/unknown prerequisite/capability/permission.
- Binding: wrong_binding, missing_registration, retired_route, route_mismatch
  and corrupt_snapshot.
- Capability lifecycle: unregistered/forged/copied/transferred/foreign_epoch,
  abandoned, consumed, rejected, uncertain or closed.
- Malformed/integrity: incoherent predecessor proof, corrupt authoritative
  state, pin mismatch and invalid integration/guard/lock graph.
- Infrastructure: authoritative state unavailable/busy/wrong schema,
  ownership loss, guard acquisition/loss and trusted clock failure/regression.

Malformed/integrity state is never collapsed into ordinary policy denial;
infrastructure uncertainty is not a valid negative history proof. Exact private
enum spelling is implementation work subject to these category distinctions,
not a widening of public Admission outcomes. Future entry_existing,
entry_store_unavailable, commit_unknown and effect_ambiguous belong to the
separately implemented consumer seam.

No AIO-049 change, AIO-051 change or AIO-056 public change is required.
AIO-050 private cooperation and AIO-056 private Store assessment factoring
remain Phase-2 proposals only. No AIO-057 authorization persistence or migration
is required. If implementation needs public predecessor redesign, schema
widening or durable Entry inside AIO-057, STOP as MATERIAL DESIGN CHANGE before
implementation.

## Locked scenario matrix

Exact total: 96 rows = 72 foundation rows F01-F72 + 24 future consumer rows
E01-E24. Rows are acceptance obligations, not executed tests. Aggregate rows
require separate future evidence for every named mutation participant and
failure branch; a single representative subcase is insufficient.

### AIO-057 foundation — 72 obligations

| ID | Scenario | Required outcome |
| --- | --- | --- |
| F01 | First-generation current Claim | One prepared capability. |
| F02 | Renewed highest generation | Use current effective expiry; retain Claim identity. |
| F03 | Reclaimed highest generation without prior Entry | New Claim subject; old capability is ineligible. |
| F04 | Frozen complete subject | Preserve exact Run, Binding, ledger, session and executor. |
| F05 | Same physical key; conflicting full Run | Subject conflict; no second cell. |
| F06 | Same physical key; conflicting Binding | Subject conflict; no second cell. |
| F07 | Same physical key; different executor | Conflict or ownership rejection; no second cell. |
| F08 | Wrong Dispatch | Reject exact parent/Claim mismatch. |
| F09 | Foreign pinned ledger/domain generation | Reject; no fallback. |
| F10 | Copied identity/PID/executor ID | Reject without genuine executor capability. |
| F11 | Simultaneous same-subject preparations | One cell and original capability; in-progress or exact alias only. |
| F12 | Exact repeated published preparation | Return identical capability after fresh checks. |
| F13 | Two aliases | Share one atomic consumption state. |
| F14 | Concurrent consumption reservations | One winner; no two entry authorizations. |
| F15 | Different proof fingerprint for same subject | already_prepared; no replacement capability. |
| F16 | Lost preparation response | Exact live retry can recover only the identical registered capability. |
| F17 | Lost caller capability reference | Exact live retry returns identical object; no new state. |
| F18 | Lost proofs or changed-proof retry | No capability recovery or rearm. |
| F19 | Failure before preparation reservation | No cell/capability; ordinary negative reassessment allowed. |
| F20 | Interrupted PREPARING publication | No leaked capability; uncertain commit/post-check terminalizes reservation. |
| F21 | Explicit abandonment | Permanent subject tombstone; reject all aliases. |
| F22 | Failed final pre-entry validation after reservation | Terminal REJECTED; no rearm. |
| F23 | Consumed/uncertain capability reused or reprepared | Reject terminal subject. |
| F24 | Process restart after preparation | No old capability/executor restoration; new Claim needs fresh authority. |
| F25 | Lease expired before preparation | Reject. |
| F26 | Time equals effective expiry | Reject half-open interval. |
| F27 | Stale generation | Reject despite valid-looking historical row/time. |
| F28 | Superseded claim_id | Reject; history remains nonauthoritative. |
| F29 | Missing active Claim | Reject. |
| F30 | Historical/current-query evidence offered as capability | Reject provenance/membership. |
| F31 | Consumed original Grant interval expired; fresh entry proof valid | Do not invent continuing original Grant-expiry veto. |
| F32 | Lease expires after preparation, before fresh assessment | Reject at diagnostic/final authorization time. |
| F33 | Clock equals durable watermark | Allow only with live Claim/proof windows. |
| F34 | Trusted clock regression | Fail closed; no clamp or reset. |
| F35 | Clock malformed, unavailable or overflowing | Fail closed; no substitute. |
| F36 | Lease renewed after preparation | Use authoritative effective expiry; preserve immutable Claim/cell. |
| F37 | Valid Human entry-purpose approval | Prepared eligibility only; no Grant issuance. |
| F38 | Valid policy entry-purpose allow | Prepared eligibility only; no Grant issuance. |
| F39 | Issuance proof/presentation/Grant offered for entry | Reject purpose substitution. |
| F40 | Wrong issuer/channel/Run/subject in entry decision | Reject. |
| F41 | Issuer disable before guard acquisition | Reject. |
| F42 | Disable/re-enable changes epoch | Old proof/capability cannot revive. |
| F43 | Principal logout/session invalidation/adapter epoch change | Old principal proof fails. |
| F44 | Human approval withdrawal/membership invalidation | Reject. |
| F45 | Policy deny/revision/configuration change | Reject old decision; no channel fallback. |
| F46 | Registered mutation racing read/entry scope | Serialize effective ordering; no uncovered transition. |
| F47 | Uncoordinated/external mutable source | Unsupported; no positive JIT composition/entry. |
| F48 | Acquisition/source/write/guard failure | No authority; terminalize binding on loss/integrity/ambiguous update. |
| F49 | Current Actor/Runtime/Inference candidate sources | Canonical exact assessment; no reassignment. |
| F50 | Blocked/unknown availability or applicability | Blocked/unresolved; no entry. |
| F51 | Absent/unknown runtime capability | No positive entry. |
| F52 | Denied/unknown exact environment/resource permission | No positive entry. |
| F53 | Changed effective Task mode | Full Run mismatch; new semantic preparation required. |
| F54 | Malformed/incoherent parent or decision results | Invalid/integrity failure, not ordinary denial. |
| F55 | Exact canonical AIO-051 Binding | Preserve full Run and exact Tool identity. |
| F56 | Wrong tool_id or same run_id with different Contract | Reject full equality mismatch. |
| F57 | Missing historical registration | Fail closed; no routing fallback. |
| F58 | Retired route in immutable snapshot | Historical Binding resolves; JIT rejects. |
| F59 | Runtime/environment/operation mismatch | Exact route rejection; no substitution. |
| F60 | Unknown selector/corrupt snapshot/hot replacement | Fail closed; configuration change requires teardown. |
| F61 | Capability directly constructed/forged membership | Reject. |
| F62 | Copy/deepcopy | Reject; ordinary alias retains same cell. |
| F63 | Serialization/pickle/cross-process transfer | Reject. |
| F64 | Foreign authorizer/session/process epoch | Reject. |
| F65 | Second registry/authorizer for genuine Session | Composition conflict; no independent cells. |
| F66 | Authorizer/Producer/Session close or fence | Terminal old epoch; no same-Session revival. |
| F67 | Malformed Store proof/authoritative corruption | Integrity failure; no positive state. |
| F68 | Store busy/unavailable/wrong schema | Fail closed; no alternate ledger. |
| F69 | Lock inversion/provider reentrancy | Reject unsupported integration; no wait cycle. |
| F70 | Owned post-check fails after preparation watermark COMMIT | No publication; terminal reservation. |
| F71 | AIO-057 v3 preparation/verification/helper paths | No Tool, target IO, transport, Result, command or positive durable-entry API. |
| F72 | Persistence/public/process boundaries | No JIT migration/record, Claim/Renewal mutation, public widening, discovery or protected-target access; owned watermark behavior only. |

### Future AIO-058 consumer — 24 obligations

These are design obligations only: neither implemented/PASS nor skipped
AIO-057 tests. Their execution requires separately authorized AIO-058 work.

| ID | Scenario | Required outcome |
| --- | --- | --- |
| E01 | Acknowledged first Entry COMMIT at T | Exactly one original protected synchronous effect continuation. |
| E02 | Lease expires while protected, before T | Reject; no Entry or effect. |
| E03 | Lease/proof expires after valid T, before COMMIT/effect | Accepted Entry remains authorized if COMMIT succeeds; no current-at-effect assertion. |
| E04 | Revocation effective before T | Reject. |
| E05 | Issuer/policy mutation races entry | Shared guard orders mutation-first rejection versus entry-first acceptance. |
| E06 | Reclaim before entry writer acquisition | Old generation rejects. |
| E07 | Reclaim immediately after Entry COMMIT | New Claim may exist; permanent Dispatch record blocks new entry. |
| E08 | Prior unresolved Entry; new claimant | Reject new entry; no second effect. |
| E09 | Prior resolved successful/failed Entry | Permanent Dispatch exclusion remains; retry requires new Run/Dispatch. |
| E10 | Consumed reservation; confirmed DB rollback | Terminal old subject; no effect or same-Claim rearm. |
| E11 | COMMIT unknown; actual rollback | No effect; terminal old subject; audited absence may permit fresh reclaimed Claim. |
| E12 | COMMIT unknown; actual commit | No effect; Dispatch occupied; reconciliation cannot mint continuation. |
| E13 | Crash before Entry COMMIT | No durable Entry/effect after atomic rollback; fresh Claim requires recovery and absence proof. |
| E14 | Crash after Entry COMMIT, before adapter call | Entry survives; no automatic call/replay after restart. |
| E15 | Crash after effect, before Result | Entry survives unresolved; no re-performance. |
| E16 | Acknowledged COMMIT response/continuation lost | History-only recovery; no replacement effect capability. |
| E17 | Lease expiry/revocation after accepted entry | No retroactive cancellation; no new Dispatch entry. |
| E18 | Detected guard/ownership loss before effect | Suppress original continuation; retain occupied Entry; no replay. |
| E19 | Physical effect boundary | No target metadata/open/read or external Tool action before committed Entry. |
| E20 | COMMIT releases writer protection | Use permanent Entry exclusion thereafter; never assume writer still held. |
| E21 | Consumers/Claims/generations race first Entry | Unique Dispatch key allows at most one committed Entry/continuation. |
| E22 | Entry Store missing/v3-only/corrupt/unavailable/ambiguous | Fail closed; never infer absence; no effect. |
| E23 | Callback/async/deferred stage/historical replay tries effect | Reject without original sealed synchronous continuation. |
| E24 | Post-effect exit/Result failure | Ambiguity; never rollback, rearm or reinvoke; no exactly-once success claim. |

## Task-local Validation Safety Matrix

Human-authorized bootstrap/control commands are distinct from matrix-governed
validation. Approval to read predecessor evidence or write these four artifacts
does not authorize Phase-2 code execution, test creation or a final Gate.
No search/discovery validation, Task/Workflow catalog enumeration or protected
target access is permitted.

| ID | Exact scope / prospective command | Safety and phase decision |
| --- | --- | --- |
| B0 | Literal attachment/predecessor/bootstrap source reads already authorized; exact existence checks; creation of the four explicit AIO-057 files | Bootstrap/control only, not Quality Gate PASS. No new read surface is inferred from this row. |
| B1 | git branch --show-current; git rev-parse HEAD; git status --short; git diff --cached --quiet; exact-path git status --short --untracked-files=all -- .ai/tasks/AIO-057-jit-execution-attempt-authorization-foundation | Read-only repository metadata/control. No staging or commit. Exact target status checks do not enumerate Task catalogs. |
| P1 | Literal ReadAllText of only task.yaml, context.md, acceptance-criteria.md and review.md under the exact AIO-057 directory; compare to in-memory drafts and mechanically count IDs/check whitespace | Authorized Phase-1 artifact integrity check; no code imports/execution, YAML/schema validation, tests or final Gate. |
| V1 | Fixed interpreter and direct two-file Task schema loader below | Future Phase 2 only; authorize/preflight exact interpreter and yaml/jsonschema modules first, no discovery/install/legacy validator. |
| V2 | Fixed interpreter and direct two-file selected Workflow schema loader below | Future Phase 2 only; exact selected Workflow file, no Workflow catalog/README access; same module preflight. |
| T1 | Fixed interpreter -B -m unittest tests.test_jit_execution_attempt_authorization -v; proposed exact file tests/test_jit_execution_attempt_authorization.py | Future Phase 2 only after explicit path authorization, static source/import/IO preflight and bounded fixtures; no test discovery. Path is proposed, not created or executed. |
| T2 | Focused predecessor regression tests | DEFERRED until exact needed paths/modules are supplied, statically inspected and matrix amendment authorized. No guessed test command. |
| T3 | E01-E24 future consumer scenarios | Outside AIO-057 implementation validation; no invocation/effect harness in this phase. |
| A1 | Fixed interpreter -B with ast.parse on explicit affected source paths only | Future Phase 2 after path list and literal command are locked; no imports/globs/recursive traversal. |
| M1 | Exact affected Markdown paths only | Future authorized phase after the exact safe tool/command is locked; no npx/network/broad repository scan. |
| K1 | Packaging smoke | DEFERRED: no exact approved package command in this remediation; no guessed build/import/network command. |
| Q1 | documentation_consistency and independent_review | Future formal final-review phase only against implementation evidence and required Human authorization. Phase-1 reviews do not satisfy them. |

Prospective fixed interpreter:
C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe

The following exact loaders are proposals, not commands run in Phase 1. Their
interpreter/module availability and direct input safety must be established
using separately authorized exact diagnostics before Phase-2 execution. No
fallback interpreter/package installation or discovery is authorized.

V1:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c 'from pathlib import Path; import json,yaml; from jsonschema import Draft202012Validator; s=json.loads(Path("schemas/task.schema.json").read_text(encoding="utf-8")); Draft202012Validator.check_schema(s); d=yaml.safe_load(Path(".ai/tasks/AIO-057-jit-execution-attempt-authorization-foundation/task.yaml").read_text(encoding="utf-8")); Draft202012Validator(s).validate(d)'
```

V2:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c 'from pathlib import Path; import json,yaml; from jsonschema import Draft202012Validator; s=json.loads(Path("schemas/workflow.schema.json").read_text(encoding="utf-8")); Draft202012Validator.check_schema(s); d=yaml.safe_load(Path("workflows/architecture-change.yaml").read_text(encoding="utf-8")); Draft202012Validator(s).validate(d)'
```

Required pre-implementation evidence includes V1/V2, focused foundation and
predecessor tests, documentation/packaging validation, and fresh actual final
reviews. This phase runs none of them. Report failed/skipped required validation
when that phase executes; deferred work is not current PASS evidence.

Forbidden: Get-ChildItem/dir/ls/rg/grep/find/discovery or recursive repository
search; Task/Workflow catalog reads; read/stat/hash of workflows/README.md;
unknown-safety validators; unittest/pytest discovery; operational target IO;
Tool, transport or network calls; automatic repair/migration; alternate
ledger fallback; staging, commit or push.

## Exact predecessor evidence and review linkage

The authorized predecessor surface is precisely task.yaml, context.md,
acceptance-criteria.md and review.md in each of these exact directories:

- .ai/tasks/AIO-049-local-authorization-domain-ownership-and-fencing-foundation/
- .ai/tasks/AIO-050-authenticated-agent-execution-authorization-grant-producer-foundation/
- .ai/tasks/AIO-051-trusted-agent-operation-tool-registry-and-resolver-foundation/
- .ai/tasks/AIO-053-local-operational-trust-integration-foundation/
- .ai/tasks/AIO-055-atomic-durable-dispatch-outbox-foundation/
- .ai/tasks/AIO-056-dispatch-claim-lease-and-fencing-foundation/

AIO-051's supplied literal candidate was verified earlier before treating it
as authoritative. No alternative path discovery was used. Root retained
predecessor/source investigation; independent reviewers were restricted to
the predecessor Task artifacts and retained bounded evidence. Exact review
provenance, original rejection and fresh R2 verdicts are in review.md.

## Authorized Phase-2 implementation checkpoint

Phase 2 was explicitly authorized after R2 design convergence. Subsequent
Human supplements supplied exact production/test/dependency paths and bounded
validation commands, including read-only execution_mode.py. A further explicit
Human reply authorized isolated checkout import bootstrapping because
`python -I -B -m unittest tests.<module>` cannot import this checkout.
These authorizations permit implementation and validation; they do not grant
Phase-3 review, final Human acceptance, Task closure, staging or commit.

The private implementation is
engineering_orchestration/_jit_execution_attempt_authorization.py, with the
72 executable scenario identities in
tests/test_jit_execution_attempt_authorization.py.
The only predecessor production edits are private Producer coordination and
entry-proof validation in
engineering_orchestration/agent_execution_authorization_grant_producer.py and
the Store-owned assessment seam in
engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py.
The existing _local_dispatch_claim_lease.py, AIO-049, AIO-051, AIO-053 and
execution_mode.py remain unchanged.

### Concrete private coordination

The install-once factory _compose_jit_execution_attempt_authorizer reserves one
registry per genuine Session. Strong partition references prevent object-ID
reuse or concurrent incompatible guards. Closed/failed Session reservations
are not evicted. Each participant must declare its underlying mutable
partitions through `_jit_mutable_partitions()` and bind every writer alias through
`_bind_jit_authority_guard(guard)`. Unsupported participants reject composition.
This is a trusted cooperative process protocol, not enforcement against hostile
Python code or an uncoordinated external authority.

Authority mutations use guard.mutation_scope(participant, kind). Participants
cover identity/logout/epochs, Human withdrawal/membership, policy deny/revision,
issuer disable/re-enable, entitlement and current candidate/capability/
permission/mode publications. Ambiguous mutation or configuration changes
close the binding. `_ProducerCoordinationLock` adds G before the original P
without changing public signatures. Proof minting occurs before read scope;
leaf callbacks cannot mint, mutate or reenter public coordination. Composition
happens before participant publication; attachment is not safe hot replacement.

_ExecutionAttemptAuthorization is an immutable, process-local, noncopyable and
nonserializable capability registered against the exact shared cell. Physical
identity is the pinned Session ledger identity plus Store instance and existing
Dispatch composite, claim_id and lease_generation. Complete Run, Binding and
genuine executor object/incarnation additionally constrain the subject.
Exact published retries recover the original object after fresh checks;
changed fingerprints cannot replace its state. Concurrent PREPARING reports
in-progress. Terminal cells remain tombstones.

Entry decisions are newly minted by _mint_jit_entry_decision and registered
with exact subject/guard/principal purpose. _validate_jit_entry_decision reuses
the Producer's authentication, epoch, issuer and exact entitlement predicates
without issuance or another time sample. Issuance proofs do not become Entry
proofs; Entry proofs cannot issue Grants. Existing issuance and presentation
semantics remain unchanged for ordinary issuance proofs.

### Store-owned assessment and v3 endpoint

Under S/G/P, _assess_jit_dispatch opens only the bound existing ledger,
acquires W with BEGIN IMMEDIATE, audits authoritative metadata/history and
acquires C before the consume reservation and final validation.
The immutable parent Admission/Run/Binding and current highest Claim/executor/
revocation facts are checked. Current prerequisite inputs are frozen through a
guarded leaf before the existing trusted clock sample; canonical
assess_agent_action_prerequisites and execution_mode_satisfies are reused.
Effective mode must also equal the complete Run's resolved mode. No parallel
mode ranking/composition exists. Canonical resolver equality and active-route
selection from the same immutable snapshot are separate checks.

Preparation and verification commit only the existing trusted-clock watermark.
Owned-operation post-check succeeds before capability/result disclosure.
Claim/Renewal rows and schemas are unchanged. No connection, SQL or target
effect callback leaves Store ownership. COMMIT releases W; C cleanup never
reacquires W.

The current _consume_assessment returns a provisional assessment and burns the
shared cell to UNCERTAIN because v3 has no Entry backend. It never reports
Entry committed or grants an effect continuation. CONSUMED is implemented
terminal state mechanics for the future authorized consumer; no AIO-057 path
claims a durable Entry through that state. Failed final validations reject;
ambiguous failures never rearm. All E01-E24 remain separately authorized
AIO-058 obligations, including permanent Dispatch uniqueness and the original
protected synchronous continuation before any target metadata/open/read.

### Phase-2 Validation Safety Matrix amendment

This amendment records the explicit Phase-2 path/command supplements and the
approved bounded import bootstrap. Earlier rows remain historical Phase-1
decisions; the following rows govern the authorized implementation checkpoint.

| ID | Exact execution boundary | Evidence / constraint |
| --- | --- | --- |
| V1/V2 | Previously inspected direct Task/selected Workflow schema loaders | PASS before implementation; not rerun for the added mode dependency. |
| T1 | Fixed Python -I -B -c; insert only the checkout into sys.path; unittest on tests.test_jit_execution_attempt_authorization | 72 exact named tests; no discovery; disposable mechanics fixtures; no target effects. |
| T2 | Same bootstrap, only eight explicitly authorized regression modules listed below | Existing imported fixture dependencies were statically inspected; bounded synthetic and disposable canonical-owner lanes; no broad suite. |
| T3 | E01-E24 | Preserved design obligations only; neither runtime PASS nor foundation SKIP. |
| A1 | ast.parse over the four modified/new Python paths only | No imports, traversal or globbing. |
| M1 | Pinned external markdownlint-cli2 0.23.3 API, --no-globs and colon-prefixed literal modified Markdown paths | Guarded virtual filesystem supplies only explicit contents; configuration reads return synthetic absence; directory enumeration denied; no npx/network/config imports. |
| K1 | Fixed isolated Python/pip wheel --isolated --no-index --find-links exact local backend parent --no-deps --no-cache-dir | Nonce-owned external stage; declared package surfaces only; setuptools 77.0.3 SHA-256 checked; no global installation or legacy smoke. |
| K2 | Wheel archive/source-manifest comparison plus C111 declared-package-input regression | JIT module included; exact payload hashes; no tests/Tasks/experiments/temp/unexpected entries. |
| B1 | git status --short; git diff --check; git diff --cached --check; git diff -- exact authorized paths | No staging, commit, push or catalog enumeration. |
| Q1 | Formal documentation_consistency / independent_review and Human acceptance | Deferred to separately authorized Phase 3; not executed here. |

T2 exact modules:

- tests.test_agent_execution_authorization_grant_producer
- tests.test_agent_operation_tool_registry
- tests.test_agent_operation_tool_resolver
- tests.test_local_operational_trust
- tests.test_dispatch_claim_lease_foundation
- tests.test_windows_local_authorization_domain_owner
- tests.test_authorization_domain_ownership
- tests.test_agent_action_prerequisite

The bootstrap uses only
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`.
Its Python body is `import sys, unittest`,
`sys.path.insert(0, r'D:\Dev\ai-engineering-orchestra')`, then
`unittest.main(module=None, argv=['unittest', <exact authorized module names>])`.
No Execution Mode regression module is required by the locked matrix or
inferred from the added read path.

K1 reuses the reviewed offline packaging model: direct members of the four
package surfaces declared by pyproject.toml and their explicit package-data,
with no repository/Task/Workflow traversal or path discovery. The local
backend is the supplied setuptools-77.0.3-py3-none-any.whl, with expected SHA-256
67122e78221da5cf550ddd04cf8742c8fe12094483749a792d56cd669d6cf58c.
Package evidence uses nonce-owned aio-056-package-* staging because the
unchanged predecessor C111 fixture requires that marker convention.

## SEC-057-3 bounded Phase-2 remediation

Phase 3A stopped on the HIGH finding SEC-057-3: a reconstructed subject could
extend its caller-supplied key while later validation checked only fixed
positions. Two different registry keys could therefore represent the same
physical Claim. That review is historical evidence; Phase 3 must restart in
full against the remediated implementation under separate authorization.

The private subject now stores canonical named ledger identity, exact Store,
Dispatch composite, claim_id and lease_generation components. Constructor
checks reuse the existing exact Dispatch component validators. Its read-only
`physical_key` property derives the sole registry identity from those facts;
neither `key` nor `physical_key` is a constructor/dataclass field. No malformed
key is truncated, normalized or accepted. Run, Binding and executor remain
full-subject conflict checks rather than alternate registry indices.

Preparation and capability lookup use the same derived identity. A shared
private subject validator checks canonical shape and exact Session/Store
binding before registry or entry-proof writes, including direct Producer
registration. Store assessment consumes the named Claim facts and compares
their complete values; it no longer interprets positional key prefixes.

Locked F04 is strengthened with the exact exploit and bounded representation
attacks. The foundation remains F01-F72; no separate scenario was added.
Fresh focused F04, full foundation and affected AIO-050 regression results are
recorded in review.md. All original F/E matrix rows above remain unchanged.

Current status: in_progress. Phase 2 is COMPLETE — REMEDIATED. Phase 3 reviews,
formal Quality Gates, Human final acceptance and closure remain pending.
No durable Entry, migration, public API, Tool/effect, Result, new attempt ID,
Claim/Lease persistence or acquisition-order change is part of this fix.

## Final closure checkpoint — 2026-10-09

The Human explicitly authorized Task closure after recorded architecture and
final acceptance approval. Fresh Phase-3A specialist reviews and Formal
Independent Review APPROVE; independent process is COMPLIANT; both required
Quality Gates PASS without waiver; SEC-057-3 is independently verified CLOSED.
Existing evidence remains 72/72 foundation PASS and 24/24 preserved future
AIO-058 obligations, with BLOCKER 0, HIGH 0, MEDIUM 0 and LOW 0.

Completion date: 2026-10-09. Task status: completed. Acceptance: 29/29.
AIO-057: CLOSED. No acceptance criterion remains pending. This checkpoint
supersedes earlier phase-pending status statements while preserving all design,
remediation and review history. No validation or review is rerun for closure.
AIO-058 remains separately authorized future work; no durable Entry, migration
0004, Tool invocation, resource effect, Result or exactly-once claim is added.
The Human authorizes one local AIO-057 commit and no push.
