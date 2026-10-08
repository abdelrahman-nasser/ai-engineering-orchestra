# AIO-056 Phase 1 Production Design

## Authorization, baseline, and evidence

The Human authorized Phase 1 and subsequently explicitly authorized Phase 2
implementation and matrix-governed validation on 2026-10-08. The following
production design remains locked. The exact Phase-2 file plan is authorized;
Phase 3, final Quality Gates, Human acceptance, closure, staging, commit and
push remain unauthorized. Task status remains in_progress. Phase-2 progress
and evidence are recorded in review.md without rewriting the locked scenarios.

Phase 2 now implements this design. Its canonical production semantics are in
`core/agent-execution-dispatch-claim-lease-specification.md`. review.md records
all 112 scenario nodes/subcases, focused predecessors, actual migration
checksums/fingerprints and the offline package archive. The prospective wording
below preserves the original locked design; it is not a new permission request.

All five fresh Phase-1 specialist reviews APPROVE the locked design; zero
unresolved findings. The historical Architect MEDIUM reconciliation ambiguity
was fixed and freshly re-reviewed. Final mechanical/convergence evidence is
recorded in review.md. No production readiness claim replaces Phase-2 testing.

Verified baseline: main at
`29d6a5d4f13fb60e2df1ecfd8122511e9981608a`; worktree and index were clean;
the exact AIO-056 directory was absent. AIO-055 is completed, with 34/34
acceptance recorded in its exact artifacts. No catalog was enumerated.

Selected Workflow: `workflows/architecture-change.yaml`. Explicit posture:
high Complexity, critical Risk, critical Execution Mode; these are separate
choices. The baseline AIO-055 context records no Project Rules and no relevant
Stack Module. Applicable Roles were read at exact Architect, Software Engineer,
Reviewer, and Security Reviewer YAML paths referenced by that context.

Direct dependencies: AIO-055 production Intent/ledger extension, AIO-049
canonical ownership, AIO-054 experimental evidence. AIO-047 is transitive
through AIO-055. AIO-053 integration and its AIO-050/051 process-local trust
limits remain unchanged; neither supplies worker authority after restart.

Exact evidence includes the Human's sixteen starting paths; AIO-055's exact
referenced Task/schema/Workflow/Role and ownership contracts; Store imports;
and the exact referenced ownership implementation and compatibility tests.
No broad file search, recursive search, Task/Workflow enumeration, or access
to `workflows/README.md` was used. Sources inform design, not execution of
validators, experiments, administration, or workloads.

AIO-054 supports append-only history, clock/watermark, retries, serialization,
and fencing hypotheses. Its duplicated payloads, BLOB identity encoding,
configurable experiment plumbing, 2000-ms timeout, embedded SQL, lifecycle
surrogate, and worker harness are not production authority and will not be
copied. Production retains existing TEXT COLLATE BINARY identities, parent
Admission dereference, 5000-ms default timeout, migration resources, canonical
AIO-049 operation gating, and a private adapter boundary.

## 1. Dispatch identity

Dispatch identity stays exactly:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

No dispatch_id or intent_id is required. The domain/Run uniqueness constraint
is separate. Claim and Renewal IDs name committed operation attempts; neither
creates a second dispatch identity. Domain, ledger_instance_id, domain_generation,
physical file pin, and live owned session establish the ledger relationship.
Copied keys or equal descriptive values establish no authority.

## 2. Claim identity and request

The trusted internal caller creates claim_id before its first call, retains it
through response ambiguity, and never substitutes it during exact retry.
It is an opaque cryptographically random 32-byte token encoded as exactly 64
lowercase hexadecimal ASCII characters. Validate exact str and this grammar;
reject empty, whitespace, uppercase, malformed, non-str, or coerced values.
Do not normalize. Caller here means trusted package composition, not the
untrusted Admission caller. Store does not allocate retry IDs after a write.

Claim request contains claim_id and the exact live executor capability; its
immutable semantic payload is claim_id plus capability-derived executor ID
plus the bound domain/ledger identity. It contains no caller-selected Intent,
time, duration, generation, authority flag, Tool/Run/Actor override, or SQL.
Successful selection binds the ID permanently to one chosen dispatch composite,
executor, generation, acquired time, and initial expiry. claim_id is unique
over the entire pinned ledger. A collision with a different executor is a
claim_identity_conflict, never last-writer-wins. Exact same committed request
returns the original immutable Claim, regardless of its current expiry or
supersession, with history-only semantics and no clock/watermark change.

No-row outcomes do not reserve claim_id. Explicit reevaluation of the same
no-row attempt can choose the then-first eligible Intent. This is not an exact
reproduction of the original negative response. A new attempt, including
reclaim, uses a fresh ID. Replaying an old committed claim_id never reclaims.

## 3. Executor incarnation and trust boundary

executor_instance_id identifies one concrete logical worker incarnation in
one process, not Actor, Runtime, PID, machine, Grant, ledger, or authority.
An internal factory generates a fresh opaque 64-character lowercase hex token
using 32 random bytes; no factory accepts an old ID. Each new worker and every
restart/reacquisition creates a new capability and ID. Multiple logical
workers may coexist under one live domain session in the same process.

The private capability is exact-type, internally minted, immutable,
noncopyable, nonpickleable, and nonserializable. It is bound to its creating
process and exact live owned-session object. PID may supplement the local
process check; it is neither durable identity nor proof of ownership. Closing,
loss, or fencing of that session permanently invalidates the capability.
Public methods accept no executor ID as authority. Store request opening checks
the private marker and live capability; renewal derives the executor ID from
that capability and compares it with durable history.

The Store cannot authenticate arbitrary SQL writers or hostile code inside
its trusted Python process. The capability deters conforming composition
bypass; it is not a credential, sandbox, transferable token, or invocation
authority. Durable records can be inspected as history after restart by a
new independently acquired authorized session. They cannot recreate an old
executor capability or resume its renewal rights.

## 4. Lease generation

lease_generation is an exact int (bool rejected), in 1 through
9223372036854775807, scoped to one dispatch composite. First successful Claim
gets 1. Each reclaim gets precisely highest committed generation + 1.
No allocation/reservation occurs outside the transaction. Rollback consumes
no generation; commit survives restart and WAL recovery. Contiguous history
1..N is mandatory. No reset, rollback, gap, wrap, reuse, or ledger switch.

At maximum generation, an expired Claim cannot be reclaimed: return private
generation_exhausted, no mutation, no skipping that eligible candidate to
conceal exhaustion, and require explicit operational disposition. Existing
generation MAX may renew while valid; renewal_sequence exhaustion separately
fails closed. Historical evidence never changes. Every authoritative current
assessment and fresh renewal requires the highest generation and exact Claim
and executor tuple. Stale requests reject before clock mutation. Future
progress APIs must repeat fencing under Store serialization; this Task creates
no progress, acknowledgment, invocation, or Result API.

## 5. Durable clock and 6. Claim eligibility

Reuse AgentExecutionDispatchAdmissionClock.now_utc and canonical production
parsing: exact UTC-aware datetime, lossless integer microseconds from ordinal
day 1, `YYYY-MM-DDTHH:MM:SS.ffffffZ` text paired with its exact key. No floating
time conversion or process-monotonic expiry. Fixed Store-owned duration D is
30,000,000 microseconds. No request/config duration override. Persist no D
column; audit all expiry calculations against this fixed contract. Changing D
later requires a separately versioned persistence design.

All fresh timed decisions sample once after BEGIN IMMEDIATE and complete
schema/history validation and exact retry classification. The sample must be
at least the existing durable admission_ledger_metadata last-decision watermark.
Equality is valid. Regression returns clock_regression without mutation; never
clamp, tolerate skew, repair, reset, or fall back. Exceptions, wrong type,
naive/non-UTC values, loss, invalid calendar values, or clock unavailability
return clock_failure without mutation. Expiry addition must fit canonical
datetime range and signed-64 key; overflow fails closed without history or
watermark change. No rounding/truncation.

The watermark advances atomically to sampled now, never to lease_until.
Every committed Claim/Renewal and current-state timed assessment advances it;
timed no-eligible-active, expired-Claim, and nonextending decisions also do so.
Untimed invalid/conflict/stale/revoked/empty outcomes, exact history, clock or
integrity failures, exhaustion, and migration do not. Negative receipts are
not persisted: their exact responses are not recoverable after ambiguity.
Admission/revocation watermark rules retain their existing contract.

Valid lease interval is acquired_at <= now < effective_lease_until.
At now == expiry it is expired and reclaimable, never renewable. Large trusted
forward jumps can expire/reclaim early; the old generation stays fenced and
subsequent rollback rejects below the shared watermark. No inferred skew cap.
Process/WAL restart preserves time and history; a fresh trusted UTC provider
must meet the same durable watermark. Malformed persisted times fail as
integrity_failure, not clock_failure.

Claimable means: exact active clean v3 configured/pinned ledger; complete valid
Admission/Intent XOR legacy classification; real Intent with no legacy marker;
verified complete parent Grant/Run/Binding; complete canonical revocation state;
no exact Grant revocation; no prior Claim, or highest Claim's effective expiry
at or before now; and no malformed, overlapping, or inconsistent history.
Legacy Admissions never become candidates. An ordinary request supplies no
old claimant tuple; exact-type incarnation validation prevents stale capability
use. Existing unexpired ownership cannot be displaced, including by its owner.

No new Grant expiry/issuance check is introduced for Claim: the consumed Grant's
validity interval governs Admission, not an invented post-Admission invocation
window. Claim consults exact persisted revocation and ledger authority only.
It does not assert continuing execution permission or current prerequisites.
Future JIT execution authority must be separately designed.

Candidate order is Admission.decision_time_key ascending, then all four dispatch
identity columns ascending under BINARY. In that order, select the first
nonrevoked unclaimed/expired Intent after full history verification and one
time sample. Equal times have explicit identity tie-breaking. Exhaustion of
the selected candidate rejects. No fairness, starvation, polling, or scheduler
guarantee. If no unrevoked Intent exists, return empty/authority_ineligible
untimed with no mutation; if all eligible Intents are active, commit sampled
watermark only and return temporarily_unavailable.

Transaction: owned-operation entry -> capability/request validation ->
BEGIN IMMEDIATE -> full audit -> exact history/conflict -> revocation/candidates
-> one clock sample -> eligible deterministic selection -> allocate generation
-> insert Claim -> advance sampled watermark -> full final audit -> COMMIT
-> owned-operation post-check -> disclose result. Competing writers' lock
acquisition order determines the winner; no promise that a particular worker
wins. Given one serialized snapshot/time, selection is deterministic.

## 7. Renewal and 8. Reclaim

Renewal request binds fresh caller-created renewal_id (same 64-hex grammar),
exact dispatch composite, claim_id, lease_generation, and the exact live
executor capability. Executor ID is derived, never supplied as proof. The
renewal_id is unique ledger-wide in its own namespace. Request contains no
expiry, extension amount, sequence, decision time, or payload overrides.

BEGIN IMMEDIATE -> full audit -> exact renewal_id history/conflict -> exact
Claim tuple -> require highest generation -> complete revocation/current-ledger
checks -> one trusted clock sample -> require now < previous effective expiry
-> compute proposed expiry now + D. If proposed expiry <= previous effective
expiry, commit sampled watermark only, return nonextending, and consume no
renewal_id/sequence. Equality of now after initial Claim commonly takes this
branch. Never extend from previous expiry plus D: that would stack retries or
bank future time. Positive renewal strictly increases expiry, gets per-Claim
contiguous sequence 1..N, inserts immutable row, advances sampled watermark,
audits, commits, and passes owned-operation post-check before response.

An exact committed renewal retry returns its original row before live
generation, expiry, revocation, or clock checks; it makes no authoritative
progress and never extends twice. A reused renewal_id with any different
request field is renewal_identity_conflict. A fresh old-generation renewal
returns stale_generation without mutation. Expired highest Claim returns
expired_claim with sampled watermark only; it is permanently unsuitable for
renewal under non-regressing time. Use a fresh claim_id to reclaim.

Reclaim is the ordinary claim operation selecting expired history, not a new
API or history mutation. It allocates generation N+1 inside the same writer
transaction and preserves every old Claim/Renewal. Renew-first can extend the
old lease and make a later reclaimer ineligible. Reclaim-first makes every
fresh old-generation renewal stale. Expiry itself appends nothing and changes
no status column. No deletion, overwrite, or automatic reclaim background job.

## 9. Revocation and 10. AIO-049

Consult only existing authoritative exact domain/ledger activation, complete
revocation evidence/tombstones, and verified immutable parent history. Revoke,
Claim, Renewal, and fresh current-state assessment serialize as ledger writers.
Revocation-first blocks new Claim/Renewal. Claim/Renewal-first retains committed
history; later revocation blocks further fresh Store ownership progress.
An exact historical retry remains history after revocation and supersession.
No new revocation mechanism, JIT authorizer, issuer entitlement check, Tool
resolver, prerequisite collector, or resource dereference is introduced.

Admission != permanent execution authority; Claim != invocation authority;
Lease != invocation authority; generation != permission. A positive current
assessment is point-in-time Store ownership evidence, not reusable authority
for a later effect. AIO-056 does not establish exactly-once invocation.

AIO-049's domain_generation and process-local AuthorizationDomainOperationLease
remain distinct from per-Intent lease_generation and durable Dispatch Lease.
No ownership contract/API or implementation change is required or planned.

Use a new private local adapter module,
`engineering_orchestration/_local_dispatch_claim_lease.py`, to compose the
existing concrete owned session with its already-owned `_store` and unchanged
`session.operation()`. The adapter factory requires the genuine exact adapter
session type; a Protocol look-alike or copied identity is insufficient. Inside
operation entry it verifies that captured Store is exactly session._store and
its configured identity is exactly session.identity. It exposes an opaque
private facade, never the session Store/connection. Each facade operation holds
one unchanged operation lease across capability validation, Store transaction,
result verification, and lease-exit revalidation. Return to its caller only
after successful exit. Provider-specific checks live in this local adapter,
not in generic Store history values or public Core contracts.

Factory/Store request minting are internal markers, bound to that composition;
direct construction/serialization fails. Adapter accepts no external Store,
path, ownership bool, live registry selector, or executor ID restoration.
Owned close/loss/fencing rejects new operations. Post-check failure suppresses
positive/current evidence even if the commit happened; retain the private
commit uncertainty/reconciliation disposition. No reanimation or rollback claim.

Canonical owner permits one process owner per domain. Supported logical worker
contention is within that process/session. Spawned raw SQLite probes test
storage atomicity only. Success in those probes does not establish independent
cross-process operational-worker ownership. Restart uses a new genuine session
and new executor; it reads old history only and waits for expiry before a new
Claim. No cross-process delegation or lifecycle surrogate is introduced.

## 11. Persistence and 12. Planned migration 0003

Design only:
`engineering_orchestration/_sqlite_admission_migrations/0003_dispatch_claim_lease.sql`.
No SQL file exists or is created in Phase 1.

All new identity columns are NOT NULL TEXT COLLATE BINARY. Dispatch columns
retain exact nonempty canonical identities and human/policy issuer vocabulary;
new tokens have the exact 64-hex check. Integer columns are STRICT INTEGER with
positive generation/sequence and bounded key checks; Store rejects bool before
SQLite coercion. Time columns are nonempty canonical TEXT paired with INTEGER
keys bounded inclusively to 0..315537897599999999 (the supported datetime
microsecond range). Canonical text is exactly 27 characters; full calendar,
UTC-form and text-key validation is a Store invariant.

| Table | Exact columns | Keys and references |
| --- | --- | --- |
| agent_execution_dispatch_claims | claim_id; authorization_domain_id; issuer_kind; issuer_id; grant_id; executor_instance_id; lease_generation; acquired_at; acquired_at_key; lease_until; lease_until_key | PK claim_id; UNIQUE four dispatch columns + lease_generation; UNIQUE claim_id + four dispatch columns + executor_instance_id + lease_generation for exact Renewal FK; restrictive four-column FK to Intents |
| agent_execution_dispatch_renewals | renewal_id; claim_id; authorization_domain_id; issuer_kind; issuer_id; grant_id; executor_instance_id; lease_generation; renewal_sequence; renewed_at; renewed_at_key; lease_until; lease_until_key | PK renewal_id; UNIQUE claim_id + renewal_sequence; restrictive seven-column FK to the matching Claim tuple |

Both are STRICT, WITHOUT ROWID, append-only. No payload JSON, duplicated Run,
Tool, mutable current_owner/status, completion bit, worker registry, invocation
token, or extra logical dispatch ID. Indexed UNIQUE dispatch/generation permits
highest generation lookup; UNIQUE claim/sequence permits effective expiry
lookup. These composite indexes plus PKs are sufficient; no redundant queue or
executor lookup index. CHECK `expiry_key = acquired_at_key + D` or
`renewed_at_key + D`, plus expiry strictly after that decision; signed-64/range overflow is
checked before insertion. Generation/sequence allocation is serialized.

For each of the two full table names, append the exact trigger suffixes
`_no_update`, `_no_delete`, `_no_duplicate`, `_operational_insert`, and
`_history_insert_guard`. The first three enforce immutability/duplicate guards;
operational_insert enforces active clean v3; history_insert_guard enforces the
following temporal, revocation, parent, and sequence rules. All trigger bodies
and their precise DDL text will be reviewed with the actual migration bytes.

Planned triggers on both tables reject every UPDATE/DELETE and duplicate
INSERT/REPLACE by operation ID or unique generation/sequence, including
conflicting exact fields. Operational INSERT requires active clean schema v3.
Claim guard requires the exact Intent, no legacy marker/revocation, acquired
time >= parent Admission and prior watermark, next contiguous generation, and
acquired time >= previous effective expiry. Renewal guard requires exact
matching highest Claim tuple, no revocation, next contiguous sequence,
renewed time >= Claim acquisition/prior Renewal/watermark, renewed time < prior
effective expiry, and strictly greater new expiry. Constraints/FKs/triggers
are defense in depth; complete Store audits remain mandatory. Arbitrary SQL
writers with disabled/changed constraints are outside the supported authority.

0003 drops and recreates only the exact
agent_execution_dispatch_intents_operational_insert trigger to require active
clean v3 instead of v2. This is necessary to preserve NEW Admission + Intent
on v3: 0002 hardcodes schema_version = 2. No other existing guard is weakened.
Legacy marker dirty-v1-only guard stays byte-equivalent in destination behavior.
0001 and 0002 resources/checksums and prior migration-history entries stay
byte-exact. Source fingerprints remain v1
`de080810b1d644dacf53e6bf79cbbd01343344904397a91c6dd483bd48dfad46`
and v2 `cce9d5c375da37c40eb6a73458f519f2840192500fb64ce1a20126383d2944e3`.

Append manifest migration_id 3/resource name above/SHA-256 of final canonical
UTF-8 LF bytes. Compute and pin v3 DDL fingerprint with the existing ordered
sqlite_schema algorithm, and prefix manifest IDs with the unchanged newline
algorithm. No fabricated checksum/fingerprint is asserted before SQL exists.
Phase 2 must calculate/review stable bytes before acceptance. Numeric version
alone never authorizes open. Preserve exact version-indexed source audits.

Explicit administration retains existing entitled AIO-049 domain lock and
same-file pin, quiescence, source-snapshot verification, BEGIN EXCLUSIVE,
repeat source verification, dirty transition, checksummed statements, complete
destination audit, append history, version/manifest/user_version publication,
clean transition, final audit, one COMMIT, and post-pin verification.
BEGIN EXCLUSIVE under WAL does not establish process/reader quiescence.

v2 -> v3 preserves every existing Intent and marker and creates zero Claims
or Renewals. The existing migrate() blanket zero-Intent check becomes an
exact migration-2-only check; migration 3 compares the pre/post classification
and parent snapshots instead. v1 -> v3 applies exact 0002 and 0003 in one
administrative transaction, marks only historical v1 Admissions as legacy,
and creates no historical Intent/Claim/Renewal. Update intermediate metadata
to v2 before 0003 while still dirty. Source validation must audit XOR for every
version >= 2, not only schema_version == latest (the current code's predicate).
Fresh v3 provision applies all three migrations in one transaction on an empty
ledger, then publishes verified clean v3. No new provisioning API.

Migration crashes before COMMIT leave the original intact v1/v2, including
DDL, histories, watermark and metadata. Post-COMMIT response ambiguity is
reconciled on that same pinned ledger only: intact verified source permits
explicit admin retry; complete verified v3 means already_current; mixed,
dirty, unknown/newer, checksum/history/fingerprint mismatch rejects without
repair. Operational open accepts only exact active clean current v3 and never
silently migrates, backfills, repairs, reactivates, or changes ledger. A valid
old ledger requires explicit migration. Fenced ledgers remain nonoperational.

## 13. Compatibility and 14. Minimal private API

AIO-055 classification/dereference is sufficient as immutable parent evidence,
not sufficient for Claim selection/mutation. Minimal private extension adds
controlled ordered selection, Claim/Renewal row decoding, derived history
verification/effective expiry, and owned writer transactions. Public four-method
Admission protocol, three-field Admission, public outcomes/retry vocabulary,
coordinator, JSON schema and exports stay unchanged. Private frozen result
types must not be shoehorned into the public Admission result taxonomy.

Private Store semantic operations are `_claim_dispatch_intent(request)`,
`_renew_dispatch_claim(request)`, and `_query_dispatch_claim(request)`.
Private names may be organized without widening this semantic surface.
Query has exact closed modes history/current. History request contains only
claim_id, in addition to the factory-bound ledger and closed history mode.
It returns one exact Claim and its verified ordered Renewals under a genuine
owned composition, with no currentness claim, clock, or mutation. Dispatch
composite and executor are derived from the fully audited stored row, not
required as request fields or proof. This explicitly permits reconciliation
after post-COMMIT response loss when the caller retained claim_id but never
received the automatically selected dispatch tuple. A new genuine session can
query old-incarnation history without the old executor capability. The ordered
Renewals include renewal_id so the original exact Renewal can be identified
without introducing a fourth operation. Missing claim_id returns no history;
corrupt or mismatched chain fails closed. Current mode requires
the live matching capability, Claim ID/generation/dispatch tuple, and uses
BEGIN IMMEDIATE and the fresh clock/watermark/revocation/fencing rules; its
immutable result is only point-in-time evidence. No public enumerator.

Private outcomes distinguish newly_claimed/newly_renewed, existing Claim/
Renewal history, current/expired/stale/revoked, empty/authority_ineligible/
temporarily_unavailable, nonextending, exact-ID conflict/invalid input,
generation/sequence exhaustion, clock_failure/regression, ownership_lost,
storage_busy/unavailable, incompatible_schema/integrity_failure, and
commit_unknown. Validate exact result type, payload, operation-specific shape,
and request equality before facade disclosure. Failures carry no current
evidence. History return cannot be used as permission. Keep all new values,
request makers, facade, and capability outside __all__ and public schemas.

No AIO-049 source edit, public owned-session method, public Claim/Lease API,
public Intent change, or AIO-053 Producer/presentation change is needed. If
implementation proves otherwise, stop as MATERIAL DESIGN CHANGE.

## 15. Retry and commit uncertainty

| Operation | Exact retry/reconciliation | Forbidden behavior |
| --- | --- | --- |
| Claim | Same ID, live incarnation and bound ledger; full audit then original row if committed, otherwise current reevaluation | New ID during ambiguity; another ledger; duplicate history; claim history as current proof |
| Renewal | Same renewal_id and exact immutable request tuple; return original row if committed, otherwise fresh checks | Double extension, sequence reservation, generation revival |
| Reclaim | Ordinary fresh Claim ID; committed retry returns that original generation | Reclaim with previous committed claim_id; deleting predecessor |
| Claim/Renewal commit_unknown | Reopen/audit exact original pinned ledger; original row or intact no-row with explicit reevaluation; corruption rejects | Repair, switch, assume rollback after COMMIT, silently mint replacement identity |
| Restart/incarnation loss | New genuine session may query exact history; cannot renew/replay old capability; fresh Claim after expiry with new ID | Serialize capability, restore old executor ID, integrated presentation resurrection |

Before a COMMIT attempt, rollback-confirmed failure means no new history or
watermark. From a COMMIT attempt through response loss, failures are
commit_unknown unless commit fact is independently proven; exact history
reconciliation determines it. Facade post-check failure removes ownership
evidence regardless of the durable fact. A lost/closed session cannot retry
operationally in place. Terminal fencing permits no operational read or write;
any later non-authoritative administrative forensic audit remains an existing
separately entitled boundary, not a new AIO-056 operational fallback.

## 16. Crash expectations

For a fresh operation let H/W denote pretransaction immutable history and
watermark. Hard process loss releases the SQLite lock; conforming ownership
reacquisition must independently validate unchanged ledger identity.

| Operation and cut | Durable expectation after recovery |
| --- | --- |
| Claim before transaction | H/W unchanged; no ID or generation allocated |
| Claim after candidate selection | H/W unchanged; candidate still available subject to fresh time |
| Claim after Claim insert | H/W unchanged; uncommitted Claim absent |
| Claim after watermark update | H/W unchanged; Claim and watermark roll back together |
| Claim before COMMIT | H/W unchanged; no partial Claim |
| Claim after COMMIT before response | One exact Claim and sampled watermark; exact history recovers original generation/expiry |
| Renew before transaction | H/W and effective expiry unchanged |
| Renew after validation | H/W unchanged; no sequence allocated |
| Renew after Renewal insert | H/W unchanged; no extension durable |
| Renew after watermark update | H/W unchanged; row and extension/watermark roll back |
| Renew before COMMIT | H/W unchanged; ID/sequence still unconsumed |
| Renew after COMMIT before response | One exact Renewal and sampled watermark; retry does not extend again |
| Reclaim with old lease expired before transaction | Old history stays immutable; expiry is derived; no new row |
| Reclaim after generation allocation | Old history/W unchanged; N+1 uncommitted and reusable |
| Reclaim after new Claim insert | Old history/W unchanged; N+1 absent |
| Reclaim before COMMIT | Old history/W unchanged; no current owner is invented |
| Reclaim after COMMIT before response | Old history plus exactly N+1 and sampled watermark; old tuple fenced |

Explicit injected commit ambiguity must test both actual branches: commit
did not happen vs did happen, same original IDs and same ledger. Timed
watermark-only decisions similarly reconcile watermark but have no historical
receipt; do not assert exact negative-response recovery. Test hard crash,
controlled exceptions, and post-check failure separately.

## 17. Corruption closure and 18. Concurrency

At every operational open, consistent read/history disclosure, fresh decision,
and same-transaction successful precommit, verify exact schema fingerprint,
checksummed contiguous history, application/user/metadata version agreement,
clean activation/configured identity, integrity/FKs, complete parent canonical
payload/index equality, XOR classification, revocation completeness, and time
watermark. Extend the full audit with all Claim/Renewal chains.

Audit orphan Claim/Intent and Renewal/Claim; exact dispatch, executor, claim_id,
generation FK/index equality; duplicate/conflicting IDs and sequences;
positive bounded exact integer/token/time types; contiguous generations and
renewal sequences; Claim acquisition >= parent Admission; initial expiry =
acquisition + D; Renewal acquisition/decision order, renewal before previous
effective expiry and new expiry = renewal time + D > previous effective expiry;
next Claim acquisition >= complete previous effective expiry; no Claim/Renewal
decision later than an exact persisted revocation decision; no Renewal at
or after supersession or changing a superseded effective interval; and watermark
>= every durable Admission/revocation/Claim/Renewal DECISION key, not expiry.
Malformed/noncanonical text-key pairs, overlapping active generations,
generation/sequence gaps or regression, history beyond allowed state, unknown
migration, dirty/partial state, checksum/DDL disagreement all fail closed.

Revocation history equality at identical timestamps cannot prove SQL insertion
order; legitimate Claim-first then revoke at the same time is allowed.
Operational ordering derives from BEGIN IMMEDIATE/guards, not inference from
equal time keys. No tamper resistance against a hostile administrator who can
forge history while disabling safeguards is claimed. Operational audit never
repairs or silently skips corrupt rows, even when corruption is not in the
selected candidate. Migration 0003 must never hide source corruption.

SQLite guarantees relied on: one writer at a time, serialization before fresh
snapshot selection with BEGIN IMMEDIATE, atomic transactions, FK/UNIQUE/
trigger enforcement on supported configured connections, committed consistent
snapshots, and process-crash recovery on the existing local NTFS WAL/FULL
profile (SQLite >= 3.37, foreign_keys ON, normal locking, configured finite
busy_timeout). No multi-machine/network-filesystem or power-loss guarantee
beyond the existing trusted storage profile. No reliance on BEGIN EXCLUSIVE
to stop WAL readers. Busy failure consumes no ID/generation/sequence.

Race tests must exercise both serial orders for two claims, claim/renew,
renew/expiry-reclaim, two reclaimers, and exact retry/fresh mutation. New
logical workers share canonical owned session; raw-process probes are a
separate mechanics lane. Process crash while lock held releases uncommitted
state; next same-ledger operation reevaluates. WAL reopen preserves all history,
watermark, checksums, generation and derived expiry. Many Intents use the exact
time/composite ordering, including equal-time and revoked/active candidates.

## 19. Endpoint, Phase-2 file plan, and stop conditions

Endpoint: immutable Intent -> authoritative Claim -> durable Dispatch Lease ->
renewal/expiry/reclaim -> generation fencing -> STOP. No exactly-once Tool
invocation, dispatch transport, Tool invocation, Result or execution performed.

Prospective Phase-2 changes only, requiring separate authorization:

| Exact path | Planned minimum change |
| --- | --- |
| engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py | Private transactions/rows/audits, v3 manifest/fingerprint verification and version-specific migration preservation |
| engineering_orchestration/_local_dispatch_claim_lease.py | Private canonical-session facade and incarnation capability; no owner changes or launch path |
| engineering_orchestration/_sqlite_admission_migrations/0003_dispatch_claim_lease.sql | Two append-only tables, keys/guards and exact Intent insert-trigger replacement |
| engineering_orchestration/_sqlite_admission_migrations/__init__.py | Append stable migration-3 checksum |
| core/agent-execution-dispatch-claim-lease-specification.md | Canonical private Claim/Lease semantic contract |
| core/agent-execution-dispatch-intent-specification.md | Narrow endpoint/private consumption consistency |
| core/agent-execution-dispatch-admission-store-specification.md | Local v3 history/clock/migration and private ownership consistency |
| core/terminology.md | Distinguish Dispatch Lease/generation from AIO-049 concepts |
| tests/test_dispatch_claim_lease_foundation.py | Production scenario identities in acceptance-criteria.md, isolated fixture/probe support |
| tests/test_atomic_durable_dispatch_outbox.py | v3 compatibility expectations preserving all 60 AIO-055 scenarios |
| tests/test_sqlite_agent_execution_dispatch_admission_store.py | Current-version migration/admission compatibility expectations |
| tests/test_windows_local_authorization_domain_owner.py | Synthetic unchanged canonical ownership integration expectations |
| tests/test_local_operational_trust.py | Unchanged public integrated endpoint/presentation compatibility |
| Four exact AIO-056 Task artifacts | Phase evidence only |

No edits to 0001, 0002, AIO-049 source, public coordinator, package metadata,
exports, experiments, or other Tasks. Existing package `*.py` and explicit
migration-package `*.sql` declarations should suffice; inspect exact
pyproject.toml before Phase-2 packaging under review.md safety locks. Packaging
has to include the private module and new resource without experiment/test
imports or assets. No schema export for private Claim/Renewal.

Stop for Human design disposition if a new dispatch identity, AIO-049 API/
semantics change, public contract expansion, additional authority system,
unproven migration safety, unsafe validator closure, or unreferenced required
existing path emerges. No preimplementation experiment is needed or authorized.
Scenario and safety matrices plus fresh reviews live in the other two Task
Markdown artifacts; no fifth file is created.
