# AIO-054 Context

## Phase 1 authorization and verified baseline

The Human authorized Phase 1 only: create exactly the four canonical AIO-054
Task artifacts, lock the experiment design and Validation Safety Matrix, and
obtain four fresh design reviews. Experiment implementation, experiment
execution, production changes, validation commands, staging, and commit remain
unauthorized.

The bounded baseline was checked using only the Human-authorized Git and exact
candidate-path commands:

- branch: `main`;
- HEAD: `7ddf47fb8f8e17a98e687fd30afa9c02f8759dd7`;
- worktree: clean;
- index: clean; and
- exact AIO-054 candidate path: absent and available before creation.

No Task or Workflow catalog was enumerated.

## Evidence and dependency boundary

AIO-054 is a new `investigation` Task. Its direct dependencies are AIO-046,
AIO-047, AIO-049, and AIO-053. AIO-050 and AIO-051 remain transitive through
AIO-053.

The prior read-only investigation provided authorization to create this Task,
not reusable AIO-054 review evidence. Each Phase 1 specialist must inspect the
current AIO-054 snapshot afresh. AIO-046 through AIO-053 remain canonical
architectural and implementation context, but their prior review verdicts do
not approve AIO-054.

```text
prior investigation recommendation != AIO-054 design approval
predecessor review evidence != AIO-054 review evidence
Phase 1 design approval != Phase 2 experiment authorization
```

## Explicit Workflow binding

The Human explicitly selected and bound the `architecture-change` Workflow
while also selecting Task type `investigation`. These values are intentional
and are not inferred from one another. Under
`core/workflow-specification.md`, `applicable_task_types` is advisory only; it
does not select, authorize, or prohibit a Workflow. The binding is preserved
exactly as authorized.

## Experiment objective and boundary

The experiment will produce bounded disposable evidence for the future
dispatch architecture before any production AIO-047 persistence change. It
will evaluate SQLite transaction, identity, claim, lease, time, crash,
restart, and local ownership hypotheses only.

The experiment is private, nonpackaged, and noncanonical. Its representations,
SQL, outcomes, and APIs cannot become Core contracts merely because a test
passes. Production modules must not import experiment modules. Any read-only
experiment import of an existing production value or ownership component must
be explicitly included in Phase 2, statically preflighted, and leave production
files unchanged.

The private model must reproduce these canonical AIO-047 invariants rather
than inventing weaker substitutes:

- complete Grant-composite Admission identity;
- separate authorization-domain/Run uniqueness;
- immutable Admission history and exact complete-value retry;
- history classification before fresh time or state work;
- one pinned authorization-domain ledger with no fallback;
- trusted Store-owned UTC and non-regressing watermark;
- explicit writer serialization and atomic commit ambiguity; and
- fail-closed schema, identity, payload, and corruption checks.

Findings must separately label backend-neutral semantics, SQLite-specific
mechanisms, experiment-only choices, confirmed hypotheses, rejected
hypotheses, and remaining production integration work. Passing private SQL or
Python behavior never establishes a future backend contract.

The canonical AIO-049 owner is coupled to the canonical AIO-047 Store and its
exact schema fingerprint. It cannot open the private extended experiment
ledger, and Phase 1 does not authorize changing either production component.
Accordingly, Phase 2 may use only a visibly experiment-only lifecycle
surrogate for the relevant acquire/enter/revalidate/fence/quiesce ordering.
That lane can test the proposed coordinator boundary but cannot confirm real
AIO-049 integration. Real owner/extended-Store integration remains an explicit
production-design gap for a later Human-authorized Task.

Every path stops before dispatch transport, adapter execution, Tool
invocation, `repository_file_read`, protected-resource access, or Result.

## Atomic Admission and Dispatch Intent hypothesis

For every new dispatch-enabled Admission, exactly one immutable **Agent
Execution Dispatch Intent** must be created inside the same authoritative
SQLite transaction. Exact history is classified first:

```text
BEGIN IMMEDIATE
-> verify ledger and immutable history
-> exact Admission + exact Intent: return history
   without clock sampling, watermark advance, or write
-> exact legacy Admission: return history only
   without clock sampling, watermark advance, or Intent
-> no history: continue to the new-Admission path
```

The genuinely new path is:

```text
already-held BEGIN IMMEDIATE
-> sample trusted UTC now
-> create Admission
-> create exactly one Dispatch Intent
-> advance the shared decision-time watermark to sampled now
-> COMMIT
```

The required outcome is:

```text
Admission durable AND Intent durable
OR
neither durable
```

A post-Admission second transaction is not acceptable. Admission is not
reinterpreted as an outbox row, and the experiment must not modify production
AIO-047.

Exact retry of a new dispatch-enabled Admission must recover the same
Admission and same Intent even when the clock is unavailable or behind the
watermark, without creating, resetting, or rebinding either.
Admission without its required Intent, an orphan Intent, duplicate logical
Intent, or identity mismatch is experiment integrity failure rather than an
operational repair opportunity.

The private extended transaction must preserve canonical Admission admission
semantics rather than testing only the happy path. Under writer serialization
it performs the predecessor in-transaction winner recheck and conflict
precedence before creating either row. Concurrent identical requests converge
on one exact Admission/Intent pair. Same-Grant/different-Binding,
different-Grant/same-Run, invalid temporal authority, incomplete revocation
evidence, and already-revoked authority reject without an Intent, orphan, or
watermark change beyond whatever canonical predecessor decision explicitly
requires. The experiment must report any divergence rather than weakening the
predecessor behavior.

## Historical Admission migration hypothesis

The experiment locks this partition for every pre-dispatch Admission:

```text
exactly one of:
  immutable legacy non-dispatchable marker
  immutable Dispatch Intent
```

Never both and never neither. The migration transaction must classify every
pre-dispatch Admission as legacy without silently turning it into pending
work. Exact retry of a legacy Admission returns history only and creates no
Intent.

The experiment must report a failed hypothesis rather than silently redesign
production migration. Production migration design belongs to a later
Human-authorized Task.

## Identity model

The logical Dispatch identity is the existing Admission natural Grant
composite:

```text
(
  authorization_domain_id,
  issuer_kind,
  issuer_id,
  grant_id
)
```

`run_id` remains a separate uniqueness and integrity constraint. There is no
`dispatch_id`.

One opaque, ledger-unique `claim_id` is created before a claim request. At the
private Store boundary, the claim-next request contains only `claim_id` and
`executor_instance_id`; domain, ledger, selection ordering, and lease duration
are trusted Store configuration, not caller inputs. The coordinator does not
accept an Executor ID from a worker. It creates the ID at process start, binds
it to an unexported nonserializable process-local capability object, and
derives the Store request from possession of that object. On successful
commit, the Claim immutably binds that request to the Store-selected logical
Dispatch and allocated `lease_generation`. Reuse with a different Executor is
an identity conflict; stored rebound to another Dispatch or generation is
integrity failure.

If no Claim commits, including a committed watermark-only no-row decision, the
ID remains unconsumed and a later call may select whatever Intent is then first
eligible because no prior selection became authoritative. That call is a safe
reevaluation, not exact outcome recovery. If a Claim committed, lookup by
`claim_id` must recover that exact Dispatch and generation before any new
selection.

`executor_instance_id` identifies exactly one conforming worker-process
incarnation. It is not an Actor, Runtime, PID, authorization identity,
ownership session, domain generation, or serialized credential. Every new
worker process receives a new internally derived value and cannot reconstruct
the former process-local capability. The SQLite Store alone cannot prove
process incarnation: direct replay of an old serialized tuple is an
unsupported coordinator bypass, must be exposed as that boundary in the
findings, and must never be reported as cryptographically prevented.

One opaque `renewal_id` is allocated for a Lease Renewal attempt and becomes
ledger-unique/consumed only if a Renewal row commits. It is then the exact retry
identity. Its request tuple is logical Dispatch identity, `claim_id`,
`executor_instance_id`, `lease_generation`, and `renewal_id`. A no-row outcome
leaves it unconsumed and eligible only for explicit reevaluation.

## Durable state model

The append-only dispatch-lifecycle state uses only:

```text
immutable Dispatch Intent
+ append-only Claims
+ append-only Lease Renewals
```

Operational state is derived:

- `pending`: an Intent has no Claim;
- `claimed`: its highest generation has an unexpired Lease; and
- `available-for-reclaim`: its highest generation has expired.

No mutable authoritative state enum or mutable authoritative current-head row
is allowed. A future verified cache is outside AIO-054. The experiment defines
no `invoking`, `completed`, `failed`, acknowledgement, progress, or Result
state.

The complete durable experiment inventory also includes the immutable source
Admission, predecessor immutable Grant-revocation tombstones and their
completeness metadata, exactly one immutable legacy marker or Intent
classification per Admission, schema/migration identity, and the mutable
non-regressing shared watermark. Revocation is serialized with Claim decisions
under the same writer order and advances the shared watermark according to the
predecessor clock rules. Those records are not mutable dispatch lifecycle
states and do not weaken the append-only Claim/Renewal rule.

The three lifecycle labels describe immutable dispatch history only.
`claimable` is a separate derived predicate requiring both lifecycle
availability and current authority eligibility, including complete revocation
evidence. A revoked Intent can remain historically pending or reclaimable but
is not claimable; revocation never deletes or rewrites its history.

## Trusted lease configuration and effective expiry

Lease duration is Store-owned configuration, never a worker input. The
experiment fixes both initial Claim and Renewal duration to exactly
`30_000_000` positive integer microseconds. Construction and open reject every
other value before ledger access or mutation; there is no variable-duration
experiment profile.

For a new Claim:

```text
initial_lease_until = sampled_now + 30_000_000 microseconds
```

For a Renewal:

```text
candidate_lease_until = sampled_now + 30_000_000 microseconds
candidate_lease_until > current_effective_lease_until
```

A non-extending Renewal records no Renewal. Checked integer and timestamp
arithmetic must reject overflow, out-of-range values, precision loss, or
noncanonical conversion before mutation.

For the highest Claim generation, effective expiry is its initial
`lease_until` or the greatest strictly increasing Renewal `lease_until`.
Renewals additionally receive a Store-owned per-Claim positive signed 64-bit
`renewal_sequence`. The first committed Renewal is exactly 1 and every later
committed Renewal is exactly `max(renewal_sequence) + 1`, allocated under
writer serialization. Rollback consumes no value. Exhaustion at
`9_223_372_036_854_775_807`, a gap, duplicate, nonpositive value, rebound to a
different Claim, or disagreement with expiry order is integrity failure with
no mutation. The sequence is not a caller/request field. Lower Claim
generations can never contribute to the current effective expiry.

## Claim model

One claim attempt follows this semantic order under a fresh experiment-only
complete-operation lifecycle guard. The guard models the relevant AIO-049
lifecycle ordering but is not a canonical AIO-049 operation lease:

1. open the disposable pinned experiment ledger;
2. enter `BEGIN IMMEDIATE`;
3. validate ledger, domain, schema, and all experiment invariants;
4. classify an exact `claim_id` retry before selecting new work;
5. for committed exact history, verify identity and return the immutable Claim
   without new selection, clock sampling, watermark mutation, or any statement
   of current Lease authority;
6. when history is absent, derive non-time authority eligibility, including
   revocation completeness, before clock work;
7. classify zero Intents or zero authority-eligible Intents as no-row outcomes;
8. otherwise sample the trusted UTC clock once and reject failure/regression;
9. apply highest-generation effective expiry and deterministically select the
   first claimable Intent; a current unexpired generation makes an Intent
   temporarily unavailable;
10. if every authority-eligible Intent is temporarily unavailable, commit only
    sampled `now` to the watermark and return a no-row outcome;
11. allocate `max(lease_generation) + 1` for the selected Intent;
12. compute checked `lease_until` from trusted configuration;
13. insert one immutable Claim;
14. advance the shared watermark only to sampled `now`; and
15. commit.

An actually empty Intent set is classified before clock sampling. It returns a
private `empty` outcome, rolls back the no-write transaction, leaves the
watermark unchanged, and does not consume `claim_id`. A nonempty set with no
authority-eligible Intent returns private `authority_ineligible` before clock
sampling with the same no-write behavior. If authority-eligible Intents exist
but all have current unexpired Claims, the time-based
`temporarily_unavailable` decision commits sampled `now` to the watermark but
inserts no Claim and does not consume `claim_id`. Revoked or
revocation-incomplete Intents are not claimable and cannot be used to infer an
active Lease.

No-row outcomes are deliberately non-durable and safely re-evaluable. Loss or
commit ambiguity of a watermark-only response does not have an exact outcome
receipt: retry under the same unconsumed `claim_id` repeats the full decision
and may later create a Claim if eligibility changes. The response must label
this as reevaluation, never exact committed-history recovery.

Experiment selection ordering is deterministic by ascending exact integer
Admission decision-time key, then component-wise unsigned lexicographic bytes
of the four non-null canonical UTF-8 logical-identity components in declared
tuple order. SQLite stores/compares those tie-break components as bytes, never
locale text. Only the one-winner safety property is proposed as
backend-neutral; this fairness ordering remains an experiment choice unless a
later Core contract adopts it.

A failure at or after a possible Claim commit is `commit_unknown`. Ordinary
recoverable lifecycle loss uses the exact same `claim_id` against the same
pinned ledger under a newly proven guard to recover immutable history. A
separate current-Claim assessment is required before describing that history
as active. A terminal fence after the possible commit cannot be operationally
recovered: immutable bytes may be inspected only by an explicitly
non-authoritative same-ledger administrative test path, and no operational
Lease authority is returned. Real AIO-049 recovery remains deferred with
production integration.

Only a committed Claim consumes `claim_id` and gains exact-history retry.
An exact Claim retry returns the original history without extending it and
without declaring it active. An expired or superseded Claim remains
recoverable as history but cannot be resurrected. A restarted process with a
new Executor identity may load that history only through the private
non-authoritative reconciliation surface; it cannot recover active capability
or reuse the old Executor-bound coordinator request. Reclaim requires a new
`claim_id` and, after process restart, a new `executor_instance_id`.

## Current Claim authority assessment

Current Lease status is separate derived in-memory evidence, never a field on
historical Claim/Renewal return values. A private assessment operation requires
the current process-local Executor capability and a fresh lifecycle guard,
then under `BEGIN IMMEDIATE`:

1. validates the pinned ledger and exact Claim/Dispatch/Executor/generation;
2. requires complete revocation evidence and no applicable tombstone;
3. requires the Claim generation to remain highest and derives its effective
   expiry from the validated Renewal chain;
4. samples trusted UTC once and rejects unavailable, malformed, lossy, or
   regressing time without returning current authority;
5. evaluates the half-open Lease interval, advances the watermark to sampled
   `now`, and commits that time decision whether active or inactive; and
6. performs lifecycle-surrogate post-Store revalidation before returning an
   `active` assessment.

The assessment does not extend a Lease and is only point-in-time scheduling
evidence; it is not continuing invocation authority. Response loss or ordinary
commit ambiguity safely repeats the assessment and its watermark decision.
Terminal post-check fencing returns no active assessment and permits only the
non-authoritative administrative reconciliation already bounded above.

## Renewal and fencing model

Lease Renewal is append-only. Its complete operation uses this order:

1. acquire and retain one fresh experiment-only complete-operation lifecycle
   guard through the process-local Executor capability;
2. enter `BEGIN IMMEDIATE` and verify the same ledger and all invariants;
3. classify `renewal_id` first;
4. verify the complete stored request tuple, then return an exact committed
   Renewal as immutable history without inserting or extending again;
   historical return never by itself proves a current Lease;
5. reject identity rebound, a non-highest generation, a mismatched Executor,
   or absence of the current process-local capability;
6. require complete revocation evidence and no applicable tombstone under the
   same writer order; authority-ineligible rejection occurs before clock
   sampling and leaves the watermark and `renewal_id` unchanged;
7. sample trusted UTC once for a new Renewal decision;
8. reject clock failure/regression and determine half-open expiry;
9. for expired or non-extending requests, advance the watermark to sampled
   `now` and commit the time decision without inserting a Renewal;
10. allocate the next `renewal_sequence`, compute the checked bounded
   `lease_until`, insert one immutable Renewal, and advance the watermark to
   sampled `now` in the same transaction;
11. commit and perform the lifecycle-surrogate post-Store revalidation.

Only an inserted committed Renewal consumes `renewal_id` and has exact-history
retry. Expired and nonextending decisions commit only the watermark, create no
request-bound receipt, leave `renewal_id` unconsumed, and are deliberately
re-evaluable. A response loss or ambiguous watermark-only commit may therefore
be retried and produce a later Renewal if conditions change; it must never be
reported as recovery of the earlier negative outcome.

Failure at or after a possible inserted-Renewal commit is `commit_unknown`.
Ordinary recoverable lifecycle loss uses the same `renewal_id` and ledger under
a newly proven guard. Exact retry returns an existing original Renewal even if
it later expired or was superseded, but returns history rather than renewed
authority. After terminal fencing, the record remains immutable but
operational retry/recovery fails closed. Only an explicitly non-authoritative
same-ledger administrative test may establish whether the commit occurred; it
does not return Lease authority. A stale identity rejection before a clock
sample makes no watermark change.

`lease_generation` is the per-Intent monotonic fencing token. Every future
authoritative renewal, acknowledgement, progress write, completion, or Result
attachment would have to prove:

```text
exact logical Dispatch identity
+ exact claim_id
+ exact executor_instance_id
+ exact lease_generation
+ generation is highest
+ Lease is unexpired
+ revocation evidence is complete and no tombstone applies
+ domain and ledger remain active and owned
```

AIO-054 implements only Claim and Renewal evidence. It must prove that an old
generation cannot authoritatively renew or advance after a higher generation
commits, while preserving the old Claim as immutable history. It does not add
acknowledgement, progress, completion, or Result APIs.

## Clock and lease model

Durable expiration uses trusted UTC wall time with canonical timestamp text
and an exact integer microsecond ordering key. Lease validity is half-open:

```text
acquired_at <= now < lease_until
```

The shared watermark advances to sampled `now`, never future `lease_until`.
Unavailable, throwing, naive, non-UTC, malformed, lossy, or regressing clocks
fail closed. Time is not clamped and no caller or system fallback is used.

A large forward jump cannot be distinguished locally from legitimate elapsed
time. Trusted forward correctness is therefore an explicit experiment
precondition and bounded limitation. The experiment must show that a forward
jump can expire and reclaim a Lease early while generation fencing still
prevents the old claimant from authoritative progress; it must not claim that
the database prevents an already-started external side effect.

Process-monotonic time may schedule a local wake-up but is never authoritative
for durable expiry. Restart recovery uses persisted UTC timestamps, ordering
keys, watermark, Claims, and Renewals.

## AIO-049 ownership and authority boundary

The future production coordinator requires a fresh AIO-049 operation lease
around each complete Admission/Intent, Claim, or Renewal operation: request
validation, trust checks, history classification, selection or reconstruction,
Store transaction, response construction, and mandatory post-Store provider
revalidation. Operation leases are lifecycle/revalidation guards and multiple
operations may coexist. They do **not** serialize Store writers; SQLite
`BEGIN IMMEDIATE` supplies experiment writer serialization. The short-lived
operation lease is not the durable Dispatch Lease and is not retained for the
worker Lease duration.

The canonical owner cannot open the private extended schema. Phase 2 therefore
does not call its guard an AIO-049 lease and does not claim integration. It uses
an experiment-only in-process lifecycle surrogate with the minimum modeled
states needed to test enter, concurrent active operations, authority loss,
post-Store revalidation, terminal fence, quiescence, and clean reacquisition
where canonically allowed. Surrogate deviations or assumptions are recorded in
findings; production integration remains unproven and deferred.

Raw operational worker SQLite access that bypasses the future coordinator is
unsupported. The experiment uses two explicitly separate evidence lanes:

1. spawned-process raw SQLite **storage-mechanism probes** evaluate writer
   contention, crash, restart, busy, and exact transaction behavior only;
   those processes are not conforming operational workers and establish no
   AIO-049-integrated multiworker guarantee; and
2. in-process lifecycle-surrogate and private coordinator scenarios evaluate
   process-local capability gating, concurrent operation entry, ownership
   loss, post-check, fencing, and quiescence without IPC or canonical Store
   integration.

The findings must never compose those lanes into a claim that multiple worker
processes hold proven AIO-049 authority over the extended ledger. A future
canonical Store/owner integration, owner-process broker, IPC contract, or
transient-owner worker composition requires separate design.

Admission and Claim are historical or scheduling records, not continuing
invocation authority. Fence or authoritative revocation before Claim makes
Claim fail closed. If fencing or revocation occurs after Claim, history
remains immutable and later Renewal or authoritative progress fails. Terminal
fencing also prevents operational exact-retry entry; immutable commit
reconciliation then belongs only to the non-authoritative administrative test
surface and never revives a Lease.

Future invocation must perform separately specified just-in-time ownership,
revocation, permission, Runtime/Inference availability, Tool mapping,
credential, endpoint, and native-containment checks. AIO-054 does not design
or implement those checks.

## Supported experiment profile

The supported storage-experiment profile is Windows, the current Windows user,
one host, a fixed local NTFS SQLite file, WAL, `synchronous=FULL`, foreign keys
enabled, normal locking, autocommit outside explicit transactions, exact
`busy_timeout=2000` milliseconds, SQLite `3.37.0` or newer, explicit writer
serialization, and spawned local-process storage probes. Open records the
observed SQLite library version and effective pragma values and fails closed
when the version or any setting is outside the pinned profile. The
ownership-lifecycle evidence profile is the in-process surrogate only; it does
not include canonical AIO-049 integration or worker IPC.

The exact 2000 ms value is a configured/read-back busy-handler bound, not a
promise of exact elapsed wall time. A held-writer probe requires the typed busy
outcome, no fallback or partial write, and a documented broad observation
window of 0.5 through 15.0 seconds; elapsed time outside that diagnostic window
fails the experiment profile without redefining SQLite's timing contract.

The experiment does not support network shares, cloud-sync folders,
replicated writable copies, multi-machine guarantees, distributed consensus,
automatic failover, or copied active ledgers.

## Migration administration hypothesis

The private legacy-classification migration assumes exclusive, quiescent
administrative ownership as an external precondition and also uses
`BEGIN EXCLUSIVE`. In WAL mode that transaction mode serializes writers but
does not exclude readers or prove process quiescence. The in-process surrogate
cannot prove multiprocess administrative exclusion, so Phase 2 must label that
precondition unconfirmed rather than infer it from SQLite locking. Before
mutation the migration verifies the exact old application/store identity,
schema version and fingerprint, contiguous migration history and checksums,
domain/ledger/generation metadata, clean migration state, Admissions,
revocation tombstones and completeness metadata, payloads, foreign keys,
integrity, and watermark.

It marks migration dirty, installs the new schema and invariants, writes one
legacy marker for every existing Admission, verifies the XOR partition,
updates migration history/version/fingerprint metadata, returns migration to
clean, and commits once. Operational open rejects old, newer, dirty, partial,
checksum-mismatched, fingerprint-mismatched, or corrupt state.

Precommit failure leaves the exact old ledger unchanged. Failure at or after
commit uses same-ledger administrative reconciliation and never another file,
repair, fallback, or pending-work backfill.

## Proposed Phase 2 artifacts

Phase 2 may propose and create only after separate Human authorization:

```text
experiments/dispatch_outbox_claim_lease/README.md
experiments/dispatch_outbox_claim_lease/findings.md
experiments/dispatch_outbox_claim_lease/schema.sql
experiments/dispatch_outbox_claim_lease/store.py
experiments/dispatch_outbox_claim_lease/worker_harness.py
tests/test_dispatch_outbox_claim_lease_experiment.py
```

They remain private, nonpackaged, noncanonical, and unreachable from the
production package. No public schema is introduced.

## Locked 128-scenario matrix

The minimum matrix is fixed at 128 scenarios. Reducing or materially combining
entries requires Human review.

| ID | Scenario | Required evidence |
| --- | --- | --- |
| 1 | New Admission | Exactly one Admission and one Intent commit atomically |
| 2 | Exact Admission retry with unavailable clock | Original Admission and Intent return without clock access or duplicate |
| 3 | Exact Admission retry with regressing clock | Original pair returns before watermark comparison or mutation |
| 4 | Admission crash before transaction | Neither Admission nor Intent exists |
| 5 | Admission crash after begin | Rollback leaves neither record |
| 6 | Admission crash after Admission insert | Rollback leaves neither record |
| 7 | Admission crash after Intent insert | Rollback leaves neither record |
| 8 | Admission crash after watermark update | Rollback leaves neither record and no watermark advance |
| 9 | Admission ambiguous commit, not committed | Exact retry creates one coherent pair |
| 10 | Admission ambiguous commit, committed | Exact retry recovers the one committed pair |
| 11 | Existing-Admission migration | Every old Admission receives exactly one legacy marker and no Intent |
| 12 | Migration preflight mismatch | Wrong version, fingerprint, checksum, domain, or payload leaves old store unchanged |
| 13 | Operational open of old, newer, dirty, or partial schema | Fail closed without repair or mutation |
| 14 | Migration crash before commit | Reopen observes the unchanged old schema and data |
| 15 | Migration ambiguous commit | Same-ledger reconciliation proves exactly old or complete new state |
| 16 | Legacy exact Admission retry | Returns historical Admission without clock access, marker rewrite, or Intent |
| 17 | Outbox XOR corruption | Missing, orphan, duplicate, or overlapping marker/Intent fails integrity checks |
| 18 | One pending Intent | Deterministic Claim receives generation 1 |
| 19 | Multiple eligible Intents | Canonical ordering selects exactly the expected Intent |
| 20 | Raw SQLite two-process Claim race | Storage-mechanism probe commits exactly one current Claim |
| 21 | Concurrent lifecycle-surrogate operations | Guards coexist; SQLite alone serializes writers and fence waits for quiescence |
| 22 | Claim race winner | Exactly one current Claim commits for the selected Intent |
| 23 | Active Lease | A second distinct request cannot claim the same Intent |
| 24 | Exact Claim retry after lost response | Same `claim_id` recovers history; separate assessment may prove point-in-time active status |
| 25 | Exact Claim retry after expiry | Historical Claim returns but conveys no current authority |
| 26 | Exact Claim retry after supersession | Historical Claim returns but conveys no current authority |
| 27 | Claim ID and Executor rebound | Reuse with a changed `executor_instance_id` conflicts |
| 28 | Stored Claim binding rebound | Changed Dispatch or generation for one `claim_id` is an integrity failure |
| 29 | Exact Claim expiry boundary | `now == lease_until` is expired and reclaimable |
| 30 | Different-worker reclaim | New Claim receives generation plus one |
| 31 | Same-worker reclaim | Requires a new `claim_id` and receives generation plus one |
| 32 | Stale old claimant | Lower generation cannot advance after reclaim |
| 33 | Claim crash before transaction | Intent remains eligible and no Claim exists |
| 34 | Claim crash after begin or Claim insert | Rollback leaves no Claim |
| 35 | Claim crash after watermark update | Rollback leaves no Claim and no watermark advance |
| 36 | Claim ambiguous commit | Exact retry distinguishes and recovers both commit outcomes |
| 37 | Worker crash after receiving Claim | Lease expires and work becomes reclaimable |
| 38 | Valid Renewal | Effective expiry is `now + 30,000,000` microseconds and strictly extends |
| 39 | Nonextending Renewal | No row is inserted, ID stays unconsumed, and sampled valid `now` advances the watermark |
| 40 | Exact committed-Renewal retry | Same consumed `renewal_id` returns the original record without extending again |
| 41 | Committed Renewal retry after expiry or supersession | Under a valid guard, history returns but conveys no current authority |
| 42 | Renewal response loss | Exact retry recovers the committed immutable Renewal |
| 43 | Renewal ID rebound | Changed Claim, generation, or Executor conflicts; sequence is not caller input |
| 44 | Stale-generation Renewal | Rejected without a Renewal mutation |
| 45 | Expired Claim Renewal | Rejected; valid sampled `now` advances the watermark |
| 46 | Concurrent Renewals | Serialization yields strict sequences and strictly increasing effective expiry |
| 47 | Renewal versus reclaim race | One authoritative transaction order wins |
| 48 | Renewal crash before transaction | No Renewal exists |
| 49 | Renewal crash after insert | Rollback leaves no Renewal |
| 50 | Renewal crash after watermark update | Rollback leaves no Renewal and no watermark advance |
| 51 | Inserted-Renewal ambiguous commit | Exact retry distinguishes and recovers both commit outcomes absent terminal fence |
| 52 | Renewal-chain corruption | Duplicate ID/sequence, rebound key, malformed timestamp, or invalid effective chain fails closed |
| 53 | Unavailable or throwing clock | New Claim/Renewal path fails closed with no durable mutation |
| 54 | Naive, non-UTC, malformed, or lossy clock | Fails closed with no durable mutation |
| 55 | Clock rollback below watermark | Fails closed without clamping or mutation |
| 56 | Watermark semantics | Advances only to sampled `now`, never to `lease_until` |
| 57 | Forward wall-clock jump | Early expiry is documented; stale generations remain fenced after reclaim |
| 58 | Process restart during active Lease | Durable Claim remains current only until its effective expiry |
| 59 | SQLite/WAL restart | Intent, Claims, Renewals, migration state, and watermark survive |
| 60 | Worker-process restart | New internal ID/capability cannot reuse the old coordinator request; audit remains non-authoritative |
| 61 | Repeated reclaim | Generations remain strictly increasing |
| 62 | Malformed, gapped, rebound, or exhausted generation | Fails closed as an integrity failure |
| 63 | Complete lifecycle-surrogate guard | Guard spans request checks through response/post-check without claiming AIO-049 integration |
| 64 | Domain fenced before Claim | Claim fails closed and immutable history remains |
| 65 | Fencing racing with operations | Concurrent guards quiesce under the surrogate lifecycle order; SQLite orders writes |
| 66 | Terminal fence after Claim | Operational retry/Renewal fails; administrative history conveys no authority |
| 67 | Post-Admission revocation | Tombstone/completeness ordering blocks Claim or later progress without rewriting history |
| 68 | Wrong Admission identity | Claim fails without disclosure or mutation |
| 69 | Wrong Run or index/payload relationship | Integrity failure without mutation |
| 70 | Tool substitution | No override is accepted; stored identity remains exact |
| 71 | Runtime substitution | No override is accepted; stored Run remains exact |
| 72 | Actor, operation, or resource widening | No override is accepted |
| 73 | Corrupt or newer experiment schema | Operational open fails closed without repair |
| 74 | SQLite connection-profile pressure | Exact timeout config reads back; held writer yields typed busy/no fallback within 0.5–15.0 seconds |
| 75 | Negative execution boundary | No transport, invocation, resource I/O, credential, probe, or Result path is reachable |
| 76 | Concurrent identical Admissions | Writer winner creates one pair; loser returns that exact Admission/Intent pair |
| 77 | Same Grant with different Binding | Canonical conflict precedence rejects without another Admission or Intent |
| 78 | Different Grant with same Run | Run conflict rejects without Admission, Intent, or orphan |
| 79 | Not-yet-valid Grant | Temporal rejection creates neither Admission nor Intent |
| 80 | Expired Grant | Temporal rejection creates neither Admission nor Intent |
| 81 | Pre-revoked Grant | Revocation rejection creates neither Admission nor Intent |
| 82 | Incomplete revocation evidence | Fails closed and creates neither Admission nor Intent |
| 83 | Multiple Admission conflicts | Canonical predecessor precedence is preserved and no Intent is emitted |
| 84 | Admission post-check recoverable loss | Possible commit becomes ordinary `commit_unknown` and exact retry recovers one pair |
| 85 | Admission post-check terminal fence | Operational recovery fails; administrative same-ledger inspection returns no authority |
| 86 | Migration crash after dirty transition | Transaction rollback reopens as exact clean old ledger |
| 87 | Migration crash after schema installation | Transaction rollback reopens as exact clean old ledger |
| 88 | Migration crash after legacy population | Transaction rollback reopens as exact clean old ledger |
| 89 | Migration crash after metadata/clean transition | Precommit rollback is old; committed branch is complete new ledger |
| 90 | Empty Intent queue | No clock sample, watermark mutation, Claim, or consumed `claim_id` |
| 91 | Only authority-ineligible Intents | No clock sample or Claim; private no-row outcome discloses no work identity |
| 92 | All authority-eligible Intents actively leased | Sampled `now` commits to watermark; no Claim and ID remains unconsumed |
| 93 | Lost all-active response | Retry reevaluates rather than claiming exact negative-outcome recovery |
| 94 | Lost empty-queue response | Retry repeats structural classification with no durable change |
| 95 | No-row Claim later becomes eligible | Same unconsumed ID may bind exactly once to the later selected Intent |
| 96 | Claim post-check recoverable loss | Committed Claim history is recovered exactly; current status requires separate assessment |
| 97 | Claim post-check terminal fence | Operational recovery fails; audit establishes history without Lease authority |
| 98 | Lost nonextending-Renewal response | Later reevaluation may consume the formerly unconsumed ID in one Renewal |
| 99 | Lost expired-Renewal response | Reevaluation remains rejection; no exact negative receipt is claimed |
| 100 | Renewal crash after begin | Rollback leaves no Renewal or watermark advance |
| 101 | Renewal crash after invariant validation | Rollback leaves no Renewal or watermark advance |
| 102 | Renewal crash after time sample | Rollback leaves no Renewal or watermark advance |
| 103 | Renewal post-check recoverable loss | Inserted Renewal history is recovered exactly without implying current authority |
| 104 | Renewal post-check terminal fence | Operational recovery fails; audit proves history without authority |
| 105 | Old Executor tuple replay through coordinator | Missing process-local capability rejects before Store access |
| 106 | Old Executor tuple replay at raw Store boundary | Demonstrates Store-only non-enforcement and records unsupported bypass limitation |
| 107 | Invalid lease-duration configuration | Every value other than exact integer `30_000_000` rejects before ledger access |
| 108 | Equal-time selection tie | Canonical UTF-8 byte tuple order chooses the deterministic experiment winner |
| 109 | SQLite below minimum version | Open fails before schema access or mutation |
| 110 | Effective connection-profile verification | Observed version and every required pragma are recorded and enforced |
| 111 | Claim crash after invariant validation | Rollback leaves eligibility and watermark unchanged |
| 112 | Claim crash after clock sample | Rollback leaves no Claim or watermark advance |
| 113 | Rejected Admission concurrent with valid winner | Winner pair remains exact; rejected request emits no Intent |
| 114 | Revocation versus Claim writer order | Revocation-first blocks; Claim-first leaves history but later authority fails |
| 115 | Admission post-insert pre-watermark crash | One transaction rolls back both Admission and Intent |
| 116 | Multiple equal-time eligible Intents | Byte ordering is stable across restart and insertion order |
| 117 | Legacy retry after completed migration | Marker yields history only with no clock, watermark, or Intent mutation |
| 118 | Revocation versus Renewal writer order | Revocation-first rejects; Renewal-first remains history without continuing authority |
| 119 | Terminal-fence administrative reconciliation | Same-ledger audit is read-only, explicitly non-operational, and cannot repair or revive |
| 120 | Canonical-integration boundary | Evidence records that surrogate success does not prove canonical AIO-049/extended-Store compatibility |
| 121 | Exact Claim history-only retry | Returns immutable row without clock, watermark change, extension, or live-authority claim |
| 122 | Exact Renewal history-only retry | Returns immutable row without clock, watermark change, extension, or live-authority claim |
| 123 | Active current-Claim assessment | Validates authority/highest generation, samples time, commits watermark, and returns point-in-time active evidence |
| 124 | Inactive current-Claim assessment | Superseded fails before clock; highest-but-expired commits sampled time and returns inactive |
| 125 | Assessment clock failure or regression | Returns no active evidence and makes no watermark mutation |
| 126 | Assessment terminal post-check fence | Possible watermark commit yields no operational active result; audit stays non-authoritative |
| 127 | Renewal-sequence allocation and rollback | First is 1, later values increment exactly, and rollback consumes no value |
| 128 | Renewal-sequence exhaustion or corruption | Maximum exhaustion, gap, duplicate, nonpositive value, rebound, or order mismatch fails closed |

## Validation Safety Matrix

This matrix exists before Phase 2 implementation or validation. All commands
are prospective and `NOT RUN` in Phase 1 unless explicitly identified as a
Human-authorized bootstrap/control action or read-only Phase 1 review. Before
execution, each command requires complete static inspection of its bounded
runtime-reachable code, configuration, fixture, import, subprocess, network,
and protected-target closure. Any changed command or target requires a matrix
amendment and Human authorization.

| ID | Exact command or scope | Required preflight | Current result |
| --- | --- | --- | --- |
| V1 | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -c "import json; from pathlib import Path; import yaml; from jsonschema import Draft202012Validator; schema=json.loads(Path('schemas/task.schema.json').read_text(encoding='utf-8')); document=yaml.safe_load(Path('.ai/tasks/AIO-054-dispatch-outbox-and-claim-lease-transaction-experiment/task.yaml').read_text(encoding='utf-8')); Draft202012Validator.check_schema(schema); Draft202012Validator(schema).validate(document); print('AIO-054 TASK SCHEMA: PASS')"` | Exact schema and Task files; fixed interpreter and repository cwd; inspect startup, system-site `.pth`, and import closure; no validator catalog or discovery | PHASE 2 PASS / STORAGE-054-1 RERUN PASS / EVIDENCE-054-1 RERUN PASS / EVIDENCE-054-2 RERUN PASS / FINAL RECONCILIATION PASS |
| V2 | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -c "import json; from pathlib import Path; import yaml; from jsonschema import Draft202012Validator; schema=json.loads(Path('schemas/workflow.schema.json').read_text(encoding='utf-8')); document=yaml.safe_load(Path('workflows/architecture-change.yaml').read_text(encoding='utf-8')); Draft202012Validator.check_schema(schema); Draft202012Validator(schema).validate(document); print('ARCHITECTURE WORKFLOW SCHEMA: PASS')"` | Exact schema and Workflow files; fixed interpreter and repository cwd; inspect startup, system-site `.pth`, and import closure; no Workflow catalog | PHASE 2 PASS |
| T1 | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment -v` | Inspect complete experiment, test, startup, system-site `.pth`, and import closure; fixed interpreter, cwd, and module; no discovery, production mutation, network, or protected target | PHASE 2 PASS / 128 PASSED / 0 FAILED / 0 SKIPPED |
| T2 | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_agent_execution_dispatch_admission_store_conformance tests.test_sqlite_agent_execution_dispatch_admission_store -v` | Inspect complete module, startup, system-site `.pth`, and import closure; fixed interpreter and repository cwd; disposable stores only; no discovery | PHASE 2 PASS / 48 PASSED |
| T3 (OLD) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_authorization_domain_ownership tests.test_windows_local_authorization_domain_owner -v` | Inspect complete module, startup, system-site `.pth`, and import closure; fixed interpreter and repository cwd; disposable domains only; no discovery | REJECTED BY STATIC PREFLIGHT BEFORE EXECUTION / SUPERSEDED BEFORE EXECUTION / PROCESS INCIDENT: NO / UNSAFE COMMAND EXECUTED: NO |
| T3 (AMENDED) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.aio054_t3_child_process_safety_suite -v` | Exact non-discoverable FunctionTestCase and reachable harness closure; fixed interpreter and cwd; two fixed no-descendant child modes; absolute worker entry point; one internally created nonce-marked external temp root; retained exact child handles; finite cooperative/terminate/kill/reap waits; explicit minimal environment; no shell, network, production authority, protected target, or repository runtime storage | PHASE 2 PASS / 1 TEST PASSED / 2 CHILDREN CREATED AND REAPED / 2 HANDLES CLOSED / 1 ROOT CREATED AND REMOVED |
| T4 (STORAGE-054-1) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s053_unavailable_or_throwing_clock -v` | Exact generated scenario-53 method; fixed interpreter and repository cwd; no discovery; in-process disposable SQLite only; controlled Claim and Renewal clock exceptions; no child process, network, production mutation, or protected target | PHASE 2 REMEDIATION PASS / 1 TEST PASSED |
| T5 (AFFECTED CLAIM/RENEWAL) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s018_one_pending_intent tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s038_valid_renewal -v` | Two exact existing happy-path scenario methods affected by the amended Claim/Renewal assertions; fixed interpreter and repository cwd; no discovery, child process, network, production mutation, or protected target | PHASE 2 REMEDIATION PASS / 2 TESTS PASSED |
| T6 (EVIDENCE-054-1 SCENARIO 57) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s057_forward_wall_clock_jump -v` | Exact generated scenario-57 method; fixed interpreter and repository cwd; in-process disposable SQLite only; no discovery, child process, network, production mutation, or protected target | PHASE 2 EVIDENCE-054-1 REMEDIATION PASS / 1 TEST PASSED |
| T7 (EVIDENCE-054-1 SCENARIO 59) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s059_sqlite_wal_restart -v` | Exact generated scenario-59 method; fixed interpreter and repository cwd; existing bounded spawned raw-storage probes only; disposable test-owned database; finite waits and owned-process cleanup; no shell, discovery, network, production authority, or protected target | PHASE 2 EVIDENCE-054-1 REMEDIATION PASS / 1 TEST PASSED |
| T8 (EVIDENCE-054-2 MATRIX) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment -v` | Exact 128-scenario experiment module after a complete static map; fixed interpreter and repository cwd; required because 56 scenarios and shared scenario helpers plus bounded worker-harness evidence are amended; no discovery, shell, network, production mutation, or protected target | PHASE 2 EVIDENCE-054-2 REMEDIATION PASS / 128 PASSED / 0 FAILED / 0 SKIPPED |
| T9 (SCENARIO 116 POST-RESTART SELECTION) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s116_multiple_equal_time_eligible_intents -v` | Exact generated scenario-116 method; existing bounded spawned storage-probe mechanism; fixed interpreter and repository cwd; disposable SQLite only; finite owned-child waits and handle cleanup; no discovery, shell, network, production mutation, or protected target | PHASE 2 FINAL EVIDENCE-054-2 REMEDIATION PASS / 1 PASSED |
| T10 (SCENARIO 62 GENERATION EXHAUSTION) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s062_malformed_gapped_rebound_or_exhausted_generation -v` | Exact generated scenario-62 method; in-process disposable SQLite; controlled test-only highest-Claim observation at the existing signed-64 maximum; fixed interpreter and repository cwd; no discovery, child process, network, production mutation, or protected target | PHASE 2 FINAL RECONCILIATION PASS / 1 PASSED |
| T11 (SCENARIO 93 LOST ALL-ACTIVE RESPONSE) | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -m unittest tests.test_dispatch_outbox_claim_lease_experiment.DispatchOutboxClaimLeaseExperimentTests.test_s093_lost_all_active_response -v` | Exact generated scenario-93 method; in-process disposable SQLite; controlled existing `claim.after_commit` response-loss fault; stable Claim request identity; fixed interpreter and repository cwd; no discovery, child process, network, production mutation, or protected target | FINAL PHASE 2 RECONCILIATION PASS / 1 PASSED; INITIAL ASSERTION RUN FAILED AND WAS CORRECTED |
| A1 | `& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -E -s -B -c "import ast; from pathlib import Path; paths=(Path('experiments/dispatch_outbox_claim_lease/store.py'),Path('experiments/dispatch_outbox_claim_lease/worker_harness.py'),Path('tests/test_dispatch_outbox_claim_lease_experiment.py')); [ast.parse(path.read_text(encoding='utf-8'), filename=str(path)) for path in paths]; print('AIO-054 AST: PASS')"` | Three explicit future Python paths; fixed interpreter and repository cwd; inspect startup and system-site `.pth`; no glob, target import, or target execution | PHASE 2 PASS / STORAGE-054-1 RERUN PASS / EVIDENCE-054-1 RERUN PASS / EVIDENCE-054-2 RERUN PASS / FINAL RECONCILIATION PASS |
| M1 | `& 'D:\Dev.aio-tools\markdownlint-cli2\0.23.3\node_modules\.bin\markdownlint-cli2.cmd' --config '.markdownlint.json' --no-globs -- '.ai/tasks/AIO-054-dispatch-outbox-and-claim-lease-transaction-experiment/context.md' '.ai/tasks/AIO-054-dispatch-outbox-and-claim-lease-transaction-experiment/acceptance-criteria.md' '.ai/tasks/AIO-054-dispatch-outbox-and-claim-lease-transaction-experiment/review.md' 'experiments/dispatch_outbox_claim_lease/README.md' 'experiments/dispatch_outbox_claim_lease/findings.md'` | Fixed offline executable and version `0.23.3`; exact config and paths; no package runner, implicit acquisition, plugin, glob, or traversal | PHASE 2 PASS / STORAGE-054-1 RERUN PASS / EVIDENCE-054-1 RERUN PASS / EVIDENCE-054-2 RERUN PASS / FINAL RECONCILIATION PASS |
| P1 | Exact AIO-054 package-surface test only if package metadata changes unexpectedly | Stop first; define and inspect an explicit bounded module proving experiment exclusion, with no existing broad packaging test or catalog access | NOT REQUIRED; NO PACKAGE CHANGE |
| S1 | Dedicated `--aio-054-safe` smoke mode only if package smoke becomes relevant | Stop first; require explicit source allowlist, disposable environments, and pip `--isolated --no-index --no-deps --no-cache-dir`; inspect the full reachable path; generic `--target-safe` is insufficient | NOT REQUIRED; NONPACKAGED EXPERIMENT |
| G1 | Human-authorized bounded branch, HEAD, status, exact candidate check, and explicit approved-path diff inspection | No history traversal, catalog listing, staging, commit, or unapproved paths | BASELINE RUN; BOOTSTRAP/CONTROL ONLY |
| R1 | Fresh Architect review of exactly the four AIO-054 Task artifacts | Read-only exact paths; relevant canonical sources only; no inherited verdict | COMPLETED / APPROVE / 0 BLOCKER / 0 HIGH |
| R2 | Fresh Security review of exactly the four AIO-054 Task artifacts | Read-only exact paths; relevant canonical sources only; no inherited verdict | COMPLETED / APPROVE / 0 BLOCKER / 0 HIGH |
| R3 | Fresh Storage/Atomicity review of exactly the four AIO-054 Task artifacts | Read-only exact paths; relevant canonical sources only; no inherited verdict | COMPLETED / APPROVE / 0 BLOCKER / 0 HIGH |
| R4 | Fresh Operational Trust review of exactly the four AIO-054 Task artifacts | Read-only exact paths; relevant canonical sources only; no inherited verdict | COMPLETED / APPROVE / 0 BLOCKER / 0 HIGH |

Human-authorized attachment reading, baseline inspection, exact candidate-path
checking, creation and maintenance of these four Task artifacts, and the four
Phase 1 reviews are bootstrap/control actions. They are not validation or
Quality Gate results.

Explicitly prohibited are Task or Workflow catalog enumeration, test
discovery, recursive repository search, repository-wide verification, broad
Markdown traversal, unknown-safety validation, bare package smoke, mutable
package acquisition, and any command not covered by phase authorization and
this matrix. `markdownlint-cli2@0.23.3` is pinned to the fixed offline
executable; `npx --yes` and implicit download are prohibited.

## Phase 2 execution evidence

The Human separately authorized Phase 2 against the locked baseline. Exactly
the six approved private experiment artifacts were created, and production
AIO-047, production AIO-049, package exports, and public schemas were not
modified.

The final T1 execution ran all 128 locked scenarios: 128 passed, 0 failed, and
0 skipped. Earlier full executions exposed one concrete `pathlib.Path` type
check and three test-fixture defects. Those defects were corrected without
changing a scenario identity, reducing the matrix, or altering a locked
hypothesis. The final A1 parser gate passed after the corrections.

V1, V2, T2, A1, and M1 passed. P1 and S1 were not required because no package
metadata or package surface changed and the experiment remains nonpackaged.
The old T3 was not executed: two independent static reviews found that its child
`sys.executable -c` process omits the parent command's `-E -s -B`, can create
production-package bytecode, and uses unbounded `stdout.readline()` and
`stderr.read()` calls whose deferred cleanup cannot bound a hang. No in-scope
file-free workaround preserves the exact locked command and resolves those
risks. It caused no process incident or unsafe command execution and remains
recorded as `SUPERSEDED BEFORE EXECUTION`.

The Human-authorized amended T3 subsequently passed both fresh static reviews
and its one exact non-discoverable test. It created and reaped two owned child
processes, explicitly closed both retained handles, and created and removed one
owned temporary root. It affected no unrelated process and left no repository
runtime artifact. Because only harness isolation and cleanup changed, the
128-of-128 scenario result was retained and not rerun.

### T3 child-process safety amendment

The Human subsequently authorized a prospective replacement for only the T3
child-process isolation and bounded-cleanup surface. The old T3 remains in the
matrix as rejected and superseded before execution. No process incident
occurred, and the unsafe command was never executed.

The amended command targets one non-discoverable experiment FunctionTestCase.
Its fixed harness path accepts no caller cleanup root or executable. It uses
the approved absolute Python 3.12 interpreter with `-E -s -B`, `shell=False`,
an explicit minimal environment, two fixed child modes that create no
descendants, and one invocation-owned external temp root. Cleanup requires
the captured root path, directory identity, nonce-bearing marker identity and
content, excluded broad roots, and complete child reap/handle closure before
removing that exact root. Every wait is finite; fallback termination acts only
through the retained handle for the child created by that invocation.

Two fresh static reviews approved the exact amended closure with zero blocker
and zero high findings. The required safety answers before execution are:

- shell used: no;
- global process enumeration: no;
- wildcard process kill: no;
- unowned PID termination possible: no;
- cleanup path caller-controllable: no;
- cleanup limited to the owned temporary root: yes;
- finite timeout: yes;
- child handle and PID retained: yes;
- network possible: no;
- production authority possible: no; and
- protected target reachable: no.

The amended T3 passed its exact target: one test passed, with two child
processes created and reaped, two retained process handles closed, and one
owned temporary root created and removed. No unrelated process was affected,
and no repository runtime artifact remained. The existing 128-scenario result
remains 128 passed, 0 failed, and 0 skipped. Because the amendment changes
harness isolation and cleanup only, no scenario rerun was required or run.

### STORAGE-054-1 interrupted review and remediation

The first Phase 3 attempt preserved these outcomes before stopping:

- Architect final review: `APPROVE`, blocker 0, high 0, medium 0, low 0;
- Security final review: `APPROVE`, blocker 0, high 0, medium 0, low 0;
- Storage/Atomicity final review: `CHANGES REQUIRED`;
- `STORAGE-054-1`: `HIGH` because scenario 53 did not execute its locked Claim
  and Lease Renewal throwing-clock paths;
- Operational Trust final review: not completed because the stop rule fired;
- specialist convergence: no;
- Formal Independent Review: not run; and
- both required Quality Gates: not run.

The Human returned only `STORAGE-054-1` to Phase 2. Scenario 53 now makes the
Claim and Renewal clocks actually raise distinct controlled exceptions and
proves the existing fail-closed model. The failed Claim commits no row,
generation, or watermark change; leaves the Intent unchanged and claimable;
and permits the same request to commit at generation 1. The failed Renewal
commits no row, expiry, sequence, watermark, or Claim change; and permits the
same request to commit at sequence 1.

The exact amended scenario passed, as did the two exact existing Claim and
Renewal happy-path tests. Only missing test coverage changed. The other 127
scenario results are retained; the full 128-scenario module was not rerun.
`STORAGE-054-1` is remediated, Phase 2 is complete including remediation, and
a fresh Phase 3 restart is required. No prior Phase 3 approval is reusable.

The experiment hypotheses are recorded in
`experiments/dispatch_outbox_claim_lease/findings.md`. Successful experiment
evidence does not establish canonical AIO-049 integration or production
acceptance. A fresh Phase 3 was not started automatically.

## Protected-target boundary

No protected target may be opened, read, searched, enumerated, statted,
hashed, resolved, permission-inspected, or used as a fixture. The abstract
`repository_file_read` identity is not registered or invoked by AIO-054.
Categorical protected-target non-access must remain certifiable.

## Phase boundaries and current state

Phase 1 succeeds only when exactly four Task artifacts contain one coherent
design, all four fresh specialist reviews approve that common design, and no
blocker or high finding remains.

Phase 2 requires separate explicit Human authorization before creating any
experiment artifact or running any validation command. Phase 3 final reviews,
Quality Gates, Human final approval, closure, staging, and commit require later
authorization.

Current Phase 1 state at Task creation:

- Task status: `in_progress`;
- Task artifacts: exactly four;
- experiment artifacts: not created;
- experiment: not run;
- production files changed: no;
- AIO-047 changed: no;
- validation commands run: no;
- Quality Gates run: no;
- staging or commit: no.

Phase 1 design-lock result after correction cycles:

- Architect: `APPROVE`;
- Security: `APPROVE`;
- Storage/Atomicity: `APPROVE`;
- Operational Trust: `APPROVE`;
- unresolved blocker findings: 0;
- unresolved high findings: 0; and
- ready for separate Phase 2 experiment authorization: yes.

Phase 2 evidence state after STORAGE-054-1 remediation and before the next
fresh Phase 3:

- Human authorization: recorded;
- Task status: `in_progress`;
- experiment artifacts: exactly six approved paths;
- final scenarios: 128 passed, 0 failed, 0 skipped;
- production files changed: no;
- canonical AIO-049 integration claimed: no;
- old T3: rejected and superseded before execution, with no process incident;
- amended T3: static preflight passed and the exact target passed;
- interrupted Storage/Atomicity final review: `CHANGES REQUIRED` with
  `STORAGE-054-1` high;
- `STORAGE-054-1`: remediated by fresh scenario-53 Claim and Renewal
  throwing-clock evidence;
- current scenario evidence: 127 prior results retained plus scenario 53
  freshly passed;
- full 128-scenario rerun required: no;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- command outside the approved matrix: no;
- unresolved blocker findings: 0;
- unresolved high findings: 0;
- staging or commit: no; and
- ready for fresh Phase 3: yes.

At that point, Phase 2 was complete including `STORAGE-054-1` remediation and a
fresh Phase 3 restart was required.

### Fresh Phase 3 stop and EVIDENCE-054-1 remediation

The next fresh Phase 3 used one frozen remediated snapshot. All four fresh
specialists approved with zero findings, and `STORAGE-054-1` was independently
confirmed closed. The fresh Formal Independent Review nevertheless returned
`CHANGES REQUIRED` with `EVIDENCE-054-1` high. Scenario 57 did not exercise its
pre-jump Lease, early expiry, reclaim, or post-reclaim stale-generation chain.
Scenario 59 did not exercise Claim, Renewal, migration-state, or watermark
survival across its WAL restart. The independent Security assessment approved,
the independent process assessment was compliant, both Quality Gates remained
not run, and Phase 3 stopped.

The Human returned only `EVIDENCE-054-1` to Phase 2. The exact locked wording
remains unchanged:

- scenario 57: `Early expiry is documented; stale generations remain fenced
  after reclaim`; and
- scenario 59: `Intent, Claims, Renewals, migration state, and watermark
  survive`.

Only the two existing scenario handlers changed. Scenario 57 now creates an
active generation 1 before a twelve-hour trusted-clock jump, classifies that
Lease expired, reclaims generation 2, rejects generation-1 Renewal and current
authority without clock or watermark movement, proves generation 2 active and
renewable, preserves generation-1 history, and rejects a below-watermark clock.
Scenario 59 now persists Intent, generation-1 Claim, and sequence-1 Renewal
through successive bounded spawned SQLite probes, reopens after that full
chain, and verifies exact audit history, clean migration state, and the exact
Renewal watermark from newly opened processes and Store state.

T6 and T7 each freshly passed one exact scenario. Store, worker harness, schema,
algorithms, clock, migration, revocation, scenario identities, production code,
AIO-047, AIO-049, and public contracts did not change. A1, V1, and M1 freshly passed.
The full matrix was not rerun because only the two scenario handlers changed:
126 prior passes are retained plus fresh scenario 57 and scenario 59 passes,
yielding 128 passed, 0 failed, and 0 skipped.

Current state after EVIDENCE-054-1 remediation:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- historical `EVIDENCE-054-1`: high;
- current `EVIDENCE-054-1` status: remediated;
- unresolved blocker findings: 0;
- unresolved high findings: 0;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no; and
- ready for a fresh Phase 3: yes.

### Fresh Phase 3 stop and EVIDENCE-054-2 remediation

The next fresh Phase 3 permanently recorded FORMAL INDEPENDENT REVIEW:
`CHANGES REQUIRED`, EVIDENCE-054-2: `HIGH`, STORAGE-054-1: `CLOSED`, and
EVIDENCE-054-1: `CLOSED`. It identified incomplete locked-path execution in
scenarios 12, 17, 28, 52, 58, 60, 66, 68, 74, 76, 89, and 105 and stopped
without a Quality Gate, staging action, or commit.

The Human returned only EVIDENCE-054-2 to Phase 2. Before any test change or
execution, the bounded static audit mapped all 128 locked rows to their exact
handlers and assertions. It found 72 fully exercised scenarios, 56 requiring
test/harness evidence remediation, zero unmapped scenario rows, and zero
Store/runtime defects. In addition to the 12 known gaps, it found 44:

`13, 21, 24, 33, 39, 41, 42, 56, 64, 65, 67, 69, 70, 71, 72,
73, 75, 77, 78, 81, 82, 83, 84, 85, 91, 92, 94, 96, 97, 98,
99, 103, 104, 110, 111, 113, 114, 118, 119, 121, 122, 124, 126,
128`.

All 56 gaps were remediated without changing Store semantics, schema,
algorithms, clock or watermark rules, migration or revocation models,
scenario numbering or wording, production code, or public contracts. The only
harness change adds a bounded fresh-child coordinator probe for scenario 60;
capability and coordinator objects are created inside each owned child, every
wait is finite, and cleanup operates only through retained handles.

The first fresh full-matrix execution exposed one scenario-41 fixture reset
defect after all 128 tests ran. The exact scenario was corrected and passed.
The final fresh T8 run then passed 128 scenarios, with 0 failures and 0 skips.
A1, V1, and M1 also freshly passed.

Final Task-local evidence manifest:

- total locked scenarios: 128;
- fully mapped to executed evidence: 128;
- scenarios with unmapped locked paths: 0;
- pass: 128;
- fail: 0; and
- skip: 0.

Current state after EVIDENCE-054-2 remediation:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- `EVIDENCE-054-1`: closed;
- historical `EVIDENCE-054-2`: high;
- current `EVIDENCE-054-2` status: remediated;
- unresolved blocker findings: 0;
- unresolved high findings: 0;
- implementation semantics changed: no;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no; and
- ready for a fresh Phase 3: yes.

### Fresh Phase 3 Storage/Atomicity stop after EVIDENCE-054-2 remediation

The fresh Architect and Security final reviews approved the frozen snapshot
with zero findings, and Security reported EVIDENCE-054-2 closed. The fresh
Storage/Atomicity final review then returned `CHANGES REQUIRED` with one high
finding. It confirmed STORAGE-054-1 and EVIDENCE-054-1 closed but reported
EVIDENCE-054-2 open.

Scenario 116 is locked to prove stable byte ordering across restart **and**
insertion order. Its current handler varies insertion order, selects and
commits the winner, then reopens only to audit that committed Claim. It does
not perform selection after restart. The fresh review therefore establishes
127 fully exercised scenarios, one scenario with an unmapped locked path, and
one unresolved high evidence finding. The 128-pass execution record remains
valid as a test count but cannot establish complete locked-path coverage.

The Phase 3 stop rule fired. Operational Trust was interrupted without a
verdict; specialist convergence is no; Formal Independent Review was not run;
both Quality Gates were not run; and Human final approval remains pending.
No experiment or production file was changed, and no staging or commit
occurred.

Current state after the fresh Phase 3 stop:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- `EVIDENCE-054-1`: closed;
- `EVIDENCE-054-2`: open;
- locked scenarios fully exercised: 127 of 128;
- unmapped locked paths: 1;
- unresolved blocker findings: 0;
- unresolved high findings: 1;
- ready for AIO-055 production design: no;
- ready for AIO-056 production design: no;
- ready for Human final approval: no;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no.

### Phase 2 final Scenario-116 evidence remediation

The Human returned only scenario 116's post-restart winner-selection path to
Phase 2. Before the test amendment, the exact locked requirement remained:
`Multiple equal-time eligible Intents | Byte ordering is stable across restart
and insertion order`. The handler already exercised two insertion orders and
the exact canonical UTF-8 byte minimum, but selected before reopen; its single
missing path was post-restart winner selection.

Scenario 116 now uses the existing bounded spawned storage-probe mechanism. For
each insertion order, one fresh child opens the persisted Store and exits, and
a later distinct fresh child performs the Claim. Both children exit cleanly,
and their positive process IDs differ. The post-restart Claim chooses
`domain::aio054 / human / issuer::a / grant::a` at generation 1 for both
orders. A further fresh child audits the exact committed Claim, and fresh
audits prove every losing Admission and Intent unchanged. Exactly one Claim is
present, so the losing candidates remain unclaimed.

Only the scenario-116 test handler changed. No shared harness, Store,
production, schema, algorithm, deterministic-selection, Lease-generation,
clock/watermark, migration, scenario-numbering, or public-contract semantics
changed. T9 passed one exact test, and A1, V1, and M1 passed freshly. A full
matrix rerun is not required: the other 127 fresh passes are retained,
producing 128 passed, 0 failed, and 0 skipped.

Current state after the final EVIDENCE-054-2 remediation:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- `EVIDENCE-054-1`: closed;
- historical `EVIDENCE-054-2`: high;
- current `EVIDENCE-054-2` status: remediated;
- locked scenarios mapped to executed evidence: 128 of 128;
- unmapped locked paths: 0;
- crash/restart evidence: complete;
- implementation semantics changed: no;
- implementation defect discovered: no;
- unresolved blocker findings: 0;
- unresolved high findings: 0;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no; and
- ready for a fresh Phase 3: yes.

### Final fresh Phase 3 Formal Independent Review stop

The final fresh Phase 3 used the frozen post-scenario-116 snapshot. Architect,
Security, Storage/Atomicity, and Operational Trust each independently returned
`APPROVE` with blocker 0, high 0, medium 0, and low 0. Specialist reviews
converged, and all three previously known remediation findings were closed at
that checkpoint.

The fresh Formal Independent Review directly retraced the locked rows against
their executable branches and found one high evidence-completeness finding
covering two previously unmapped paths:

1. Scenario 62's exhausted-generation fixture persists only generation
   `MAX_SIGNED_64` and reopens. Static contiguous-generation validation rejects
   it as gapped before Claim allocation can execute the distinct Lease
   generation-exhaustion branch.
2. Scenario 93's all-active branch performs ordinary
   `temporarily_unavailable` and later `newly_claimed` calls. It never creates
   a lost response or executes the committed no-row `commit_unknown` result
   with `retry="reevaluate"`.

The Formal Independent Review returned technical, security, and
Storage/Atomicity `CHANGES REQUIRED`, process `COMPLIANT`, and
`EVIDENCE-054-2` open. Severity is blocker 0, high 1, medium 0, low 0. The
recorded tests remain 128 passed, 0 failed, and 0 skipped, but direct locked-
path traceability is 126 of 128 with two unmapped paths. No implementation
defect or semantic change was established.

The mandatory stop fired before either Quality Gate. No implementation,
experiment, AIO-055, or AIO-056 change occurred. Current state is:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- `EVIDENCE-054-1`: closed;
- `EVIDENCE-054-2`: open;
- specialist reviews converged: yes;
- Formal Independent Review: changes required;
- locked scenarios mapped to executed evidence: 126 of 128;
- unmapped locked paths: 2;
- scenario result: 128 passed, 0 failed, 0 skipped;
- `documentation_consistency`: not run;
- `independent_review`: not run;
- ready for AIO-055 production design: no;
- ready for AIO-056 production design: no;
- ready for Human final approval: no;
- Human final approval: pending;
- acceptance criteria verified: 160 of 171;
- acceptance criteria pending: 11;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no.

### Final Phase 2 scenarios 62 and 93 evidence reconciliation

The Human returned only the remaining scenario-62 exhausted-generation
allocation path and scenario-93 lost all-active response path to Phase 2.
Their exact locked wording and deficient before-state were recorded before any
test change or execution.

Scenario 62 now retains a valid persisted generation-1 Claim and uses a
controlled test-only projection of that real highest Claim to the existing
signed-64 maximum. At exact expiry, the real Claim operation executes the
distinct generation-allocation exhaustion guard. Assertions prove the exact
typed failure, no wrap, no new Claim, no watermark or complete-ledger mutation,
immutable original history, and no ID or real generation consumption. The same
request then succeeds normally at generation 2 after the projection is removed.

Scenario 93 now establishes two simultaneously active Claims over two eligible
Intents. A third stable request commits the all-active watermark-only decision
and loses its response at `claim.after_commit`. Assertions prove
`commit_unknown`/`reevaluate`, the exact committed watermark, no Claim or
negative-history receipt, unchanged active history, same-ID reevaluation, no
duplicate state, and one later generation-2 Claim with that ID after expiry.

T10 and final T11 each passed one exact scenario node. T11's first execution
exposed and corrected only an over-specified assertion about the ordinary
reevaluated result's advisory `retry` field. A1, V1, and M1 passed after the
final reconciliation. No Store or shared harness semantics changed, so the
other 126 fresh passes are retained and no full matrix rerun is required.

The final static branch-level reconciliation inspected every clause, generated
node, invoked branch, direct assertion, applicable durable-state assertion, and
PASS record for scenarios 1 through 128. It found 128 fully mapped scenarios
and zero unmapped locked paths. The composite scenario result is 128 passed, 0
failed, and 0 skipped.

The 171 acceptance criteria classify as 161 verified, 7 pending fresh Phase 3,
and 3 pending Human/closure. No Phase-2 evidence criterion is unresolved. The
four prior specialist approvals are historical and cannot be reused after the
scenario-62 and scenario-93 test amendments.

Current state after final Phase 2 reconciliation:

- Task status: `in_progress`;
- `STORAGE-054-1`: closed;
- `EVIDENCE-054-1`: closed;
- historical `EVIDENCE-054-2`: open / high;
- current `EVIDENCE-054-2`: remediated;
- locked scenarios mapped to executed evidence: 128 of 128;
- unmapped locked paths: 0;
- scenario result: 128 passed, 0 failed, 0 skipped;
- Phase-2 evidence criteria unresolved: 0;
- pending fresh Phase 3 criteria: 7;
- pending Human/closure criteria: 3;
- implementation semantics changed: no;
- implementation defect discovered: no;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- staging or commit: no; and
- ready for a fresh Phase 3: yes.

### Final fresh Phase 3 review result

The Human authorized review of the completed evidence manifest without any
test, experiment, implementation, staging, or commit change. No scenario was
rerun. All historical `CHANGES REQUIRED` and high-severity findings remain in
the chronological record rather than being rewritten.

Fresh Architect, Security, Storage/Atomicity, and Operational Trust reviews
each returned **APPROVE** with blocker 0, high 0, medium 0, and low 0. The
specialists independently confirmed the final architecture, security,
atomicity, retry, fencing, clock, restart, noncanonical-boundary, and process
safety evidence. They closed current `STORAGE-054-1`, `EVIDENCE-054-1`, and
`EVIDENCE-054-2` and converged without a finding.

A separate fresh Formal Independent Review traced the exact 128 locked rows to
the registry, generated nodes, invoked branches, direct assertions, durable
state assertions, and recorded results. It explicitly rechecked scenarios 53,
57, 59, 62, 93, and 116; Admission plus Intent atomicity; migration; Claim and
Renewal retry; expiry and reclaim; generation fencing; stale-claimant
rejection; clock and watermark behavior; response loss; crash and restart;
deterministic winner selection; revocation; lifecycle-surrogate limitations;
absence of invocation; and amended-T3 process compliance.

The independent technical, security, and Storage/Atomicity assessments are
**APPROVE**; the process assessment is **COMPLIANT**; current
`EVIDENCE-054-2` is independently **CLOSED**; and the Formal Independent Review
is **APPROVE** with blocker 0, high 0, medium 0, and low 0. It independently
established 128 locked scenarios, 128 fully mapped, zero unmapped, and 128
passed, 0 failed, 0 skipped. No Phase-2 evidence criterion remains unresolved,
and no experiment semantics changed during remediation.

The evidence is ready for AIO-055 and AIO-056 production design only. Neither
Task was created. The Task remains `in_progress`, and Human final approval
remains pending.

### Final fresh Phase 3 Quality Gates and control state

The first `documentation_consistency` execution found two Task-local current-
state reconciliation defects. They were corrected without changing historical
evidence, experiment behavior, or tests. A complete fresh rerun passed without
waiver. A separate fresh `independent_review` execution inspected the gate
contract, Task scope, complete acceptance checklist, locked matrix and
registry, implementation, critical remediated branches, execution record, and
review evidence. It also passed without waiver, with blocker 0, high 0, medium
0, and low 0.

Both required Quality Gates therefore pass without waiver. Acceptance is 168
of 171 verified. The remaining three criteria are Human final approval, the
closure-time no-failed-or-skipped-Gate confirmation, and the final status
transition after all closure controls are met. Current control state is:

- Task status: `in_progress`;
- Human final approval: pending;
- ready for Human final approval: yes;
- process safety clean: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no;
- index clean: yes; and
- staging or commit: no.

### Final Human approval

The Human granted final approval and final Human acceptance on **2026-10-07**.
This approval rests on completed Phases 1 through 3, all three findings closed,
128 of 128 locked scenarios fully mapped, 128 passed with no failures or skips,
all final reviews approved, both Quality Gates passing without waiver, and the
confirmed atomicity, fencing, clock, restart, and process-safety evidence.

Only the existing Human-final-approval criterion is newly complete. Current
control state is:

- Task status: `in_progress`;
- Human final approval: approved;
- final Human acceptance: approved;
- acceptance criteria verified: 169 of 171;
- pending criteria: closure-time Gate confirmation and final completed-status
  transition;
- ready for closure authorization: yes;
- Task/Workflow catalog enumeration used: no;
- protected-target access: no; and
- staging or commit: no.

### Final closure

On **2026-10-07**, the authorized closure-time inspection confirmed from the
existing Task-local evidence that `documentation_consistency` and
`independent_review` remain **PASS WITHOUT WAIVER**, the Formal Independent
Review remains **APPROVE**, and no required Quality Gate failed or was skipped.
No Gate or other validation was rerun.

The two remaining criteria are complete. Final control state is:

- Task status: `completed`;
- acceptance criteria verified: 171 of 171;
- Human final approval: approved;
- closure-time Gate confirmation: complete;
- final completed-status criterion: complete;
- closure date: 2026-10-07;
- production AIO-047 and AIO-049: unchanged;
- AIO-055 and AIO-056: not created; and
- push, merge, or publication: no.

All historical findings, `CHANGES REQUIRED` decisions, remediations,
superseded-before-execution T3 history, M1/P1/S1 safety amendments, and final
128-of-128 scenario evidence remain preserved. No experiment semantics changed
during closure.
