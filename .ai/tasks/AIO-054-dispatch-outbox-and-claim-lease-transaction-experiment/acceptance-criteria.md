# AIO-054 Acceptance Criteria

The Task is complete only when every applicable criterion is verified. Phase 1
checks establish the design lock only; they do not establish experiment or
Task completion.

## Phase 1 Task and governance

- [x] The exact AIO-054 candidate path was absent before creation.
- [x] Baseline branch is `main` at the authorized HEAD.
- [x] Baseline worktree and index were clean.
- [x] Exactly four canonical AIO-054 Task artifacts exist.
- [x] `task.yaml` declares `investigation`, `in_progress`, high Complexity,
  critical Risk, critical Execution Mode, and `architecture-change`.
- [x] The Human-selected `investigation` Task type and
  `architecture-change` Workflow are preserved as an explicit binding;
  Workflow `applicable_task_types` is advisory rather than prohibitive.
- [x] Direct dependencies are AIO-046, AIO-047, AIO-049, and AIO-053.
- [x] AIO-050 and AIO-051 are identified as transitive through AIO-053.
- [x] Phase 1 permits Task design and four reviews only.
- [x] Phase 2 experiment work requires separate Human authorization.
- [x] No predecessor or read-only-investigation review verdict is inherited.
- [x] The Validation Safety Matrix exists before any experiment validation.
- [x] Bootstrap/control actions are distinct from validation commands.
- [x] No Task or Workflow catalog enumeration occurred.
- [x] No protected target was accessed.
- [x] No staging or commit occurred.

## Atomic Admission and Intent hypothesis

- [x] Every new dispatch-enabled Admission is hypothesized to create exactly
  one immutable Agent Execution Dispatch Intent.
- [x] Admission and Intent creation use the same `BEGIN IMMEDIATE` transaction.
- [x] Admission, Intent, and sampled-now watermark commit together or not at all.
- [x] A post-Admission second transaction is explicitly rejected.
- [x] Admission is not reinterpreted as the outbox row.
- [x] Exact Admission retry returns the original Admission and Intent without
  duplicate creation, reset, or rebound.
- [x] Concurrent-winner recheck, conflict precedence, temporal rejection, and
  revocation rejection preserve canonical Admission behavior and never emit an
  orphan or extra Intent.
- [x] Missing, orphan, duplicate, or identity-mismatched Intent state fails
  integrity rather than being repaired operationally.
- [x] Production AIO-047 modification is excluded from AIO-054.

## Historical migration hypothesis

- [x] Every pre-dispatch Admission is classified as exactly one of legacy
  non-dispatchable marker or Dispatch Intent.
- [x] Marker and Intent overlap is prohibited.
- [x] Absence of both marker and Intent is prohibited.
- [x] Migration does not silently turn a historical Admission into pending work.
- [x] Exact legacy Admission retry returns history only and creates no Intent.
- [x] Migration requires exclusive quiescent administrative ownership,
  exact old-store preflight, dirty/clean lifecycle, one `BEGIN EXCLUSIVE`
  commit, and same-ledger ambiguous-commit reconciliation.
- [x] Administrative quiescence is an external unconfirmed precondition;
  WAL `BEGIN EXCLUSIVE` serializes writers but is not claimed to exclude
  readers or prove multiprocess quiescence.
- [x] Operational open rejects old, newer, dirty, partial, mismatched, or
  corrupt migration state without repair.
- [x] Experiment failure is reported without silently redesigning production migration.

## Identity and immutable state

- [x] Logical Dispatch identity is the Admission Grant composite.
- [x] No `dispatch_id` is introduced.
- [x] `run_id` remains a separate uniqueness and integrity constraint.
- [x] `claim_id` is opaque, ledger-unique, allocated before the request, and
  used as the exact-retry identity.
- [x] Claim identity binds exact Dispatch, Executor, and Lease generation.
- [x] `executor_instance_id` identifies one process incarnation only.
- [x] The coordinator derives Executor identity from an unexported,
  nonserializable process-local capability and never accepts an old serialized
  Executor ID as worker authority.
- [x] The SQLite Store alone cannot prove process incarnation; direct tuple
  replay is recorded as an unsupported coordinator bypass, not as prevented.
- [x] Executor identity is distinct from Actor, Runtime, PID, authorization,
  ownership session, and domain generation.
- [x] Worker-process restart requires a new Executor identity.
- [x] A committed `renewal_id` is the exact retry identity for one immutable
  Renewal; a no-row outcome leaves the ID unconsumed for explicit reevaluation.
- [x] Dispatch-lifecycle state consists only of immutable Intent, append-only
  Claims, and append-only Lease Renewals.
- [x] The complete durable inventory separately accounts for source Admission,
  immutable revocation tombstones/completeness metadata,
  legacy-marker/Intent classification, schema/migration identity, and the
  shared decision-time watermark.
- [x] Revocation is an orthogonal `claimable` predicate serialized with Claim
  decisions; it never rewrites immutable dispatch lifecycle history.
- [x] Pending, claimed, and available-for-reclaim are derived states.
- [x] No mutable authoritative state enum or current-head row is introduced.
- [x] No invoking, completed, failed, acknowledgement, progress, or Result
  state is introduced.

## Claim, Renewal, and fencing

- [x] Each Claim operation uses one fresh experiment-only lifecycle guard
  spanning request checks through response construction and post-check.
- [x] The surrogate is never represented as a canonical AIO-049 operation
  lease or proof that the canonical owner accepts the extended schema.
- [x] Claim uses `BEGIN IMMEDIATE` and validates the pinned experiment ledger.
- [x] Exact `claim_id` history is classified before new work selection.
- [x] Trusted UTC is sampled after writer serialization.
- [x] Eligible Intent selection is deterministic.
- [x] Selection ties use exact integer decision time followed by
  component-wise canonical UTF-8 byte order; only the one-winner safety
  property is proposed as backend-neutral.
- [x] A current unexpired highest generation blocks another Claim.
- [x] New generation is `max(lease_generation) + 1` under serialization.
- [x] Claim insertion and sampled-now watermark advancement commit together.
- [x] Ordinary Claim `commit_unknown` recovery uses the same `claim_id` and
  ledger; terminal fencing permits only non-authoritative administrative audit.
- [x] Empty, authority-ineligible, and all-active no-row Claim outcomes define
  clock, watermark, ID-consumption, response-loss, and safe-reevaluation
  semantics explicitly.
- [x] Only a committed Claim consumes `claim_id` and gains exact-history retry.
- [x] Exact Claim retry returns history only, never current Lease authority,
  and never extends the Lease implicitly.
- [x] A separate writer-serialized current-Claim assessment validates identity,
  highest generation, effective expiry, revocation, trusted time, watermark,
  lifecycle post-check, and terminal-fence behavior.
- [x] Current-Claim assessment is point-in-time scheduling evidence and not
  continuing invocation authority.
- [x] Expired or superseded Claim history cannot be resurrected.
- [x] Reclaim requires a new `claim_id`.
- [x] Renewal is append-only and bound to an exact `renewal_id`.
- [x] Lease duration is fixed Store-owned configuration of exactly
  `30_000_000` microseconds, is never a worker input, and every other value is
  rejected before ledger access.
- [x] Claim expiry is checked `sampled_now + duration`; Renewal expiry uses
  the same formula and must strictly extend current effective expiry.
- [x] Effective expiry derives from the highest Claim generation and its
  strictly increasing, serialized `renewal_sequence` chain only.
- [x] Store-owned `renewal_sequence` starts at 1, increments exactly by 1 only
  on commit, consumes nothing on rollback, and fails closed on signed-64-bit
  exhaustion or sequence corruption.
- [x] Only an inserted committed Renewal consumes `renewal_id`; its exact retry
  returns history without extending twice or declaring current Lease authority.
- [x] Expired/nonextending no-row Renewal outcomes leave the ID unconsumed and
  are explicitly re-evaluable after response loss or watermark-only ambiguity.
- [x] Renewal uses one serialized transaction for history classification,
  identity/current-generation checks, clock decision, optional insert,
  watermark update, and commit.
- [x] A new Renewal requires complete revocation evidence and no tombstone
  under the same writer order before clock sampling or insertion.
- [x] Stale-generation and expired-Claim Renewals are rejected; a valid sampled
  time decision advances the watermark even when expiry or nonextension means
  no Renewal row is inserted.
- [x] `lease_generation` is the monotonic per-Intent fencing token.
- [x] Lower generations cannot authoritatively advance after a higher
  generation commits.
- [x] Old Claims remain immutable history.

## Clock, ownership, and authority

- [x] Durable lease expiry uses trusted UTC wall time.
- [x] Lease validity is `acquired_at <= now < lease_until`.
- [x] Canonical timestamps and integer microsecond ordering keys are persisted.
- [x] The shared watermark advances to sampled `now`, not `lease_until`.
- [x] Unavailable, naive, non-UTC, malformed, lossy, or regressing time fails closed.
- [x] Time is never clamped or replaced by caller time.
- [x] Process-monotonic time is non-authoritative.
- [x] A trusted forward wall-clock jump is an explicit bounded limitation:
  it may cause early expiry/reclaim, while generation fencing still blocks
  the stale claimant from later authoritative progress.
- [x] Future AIO-049 operation leases are short-lived lifecycle/revalidation
  guards, may coexist, do not serialize SQLite writers, and remain distinct
  from durable Dispatch Leases.
- [x] Phase 2 uses only an in-process lifecycle surrogate because the canonical
  AIO-049 owner rejects the private extended Store schema; real integration is
  explicitly deferred.
- [x] Raw spawned-process SQLite probes establish storage-mechanism evidence
  only and are not conforming operational workers.
- [x] Ownership/fencing hypotheses are evaluated separately through the
  in-process lifecycle surrogate, without worker IPC or a claim of canonical
  AIO-049 integration.
- [x] The two evidence lanes are never composed into a multiprocess AIO-049
  operational guarantee; raw operational bypass remains unsupported.
- [x] Terminal fencing blocks operational retry/recovery; any same-ledger
  administrative reconciliation is read-only, non-authoritative, and cannot
  revive a Lease.
- [x] Fence or revocation before Claim fails closed.
- [x] Fence or revocation after Claim preserves history while blocking later
  Renewal or authoritative progress.
- [x] Admission and Claim are not continuing invocation authority.
- [x] Future JIT authority checks are required but excluded from AIO-054.

## Experiment profile and negative boundary

- [x] Supported scope is Windows, current user, same host, fixed local NTFS,
  SQLite `3.37.0` or newer, WAL/FULL, foreign keys, exact 2000 ms busy timeout,
  and local storage-probe processes.
- [x] Phase 2 records and enforces the observed SQLite version and effective
  connection pragmas before experiment mutation.
- [x] The exact 2000 ms busy timeout is configuration, not exact elapsed-time
  behavior; the held-writer probe requires a typed busy result, no fallback,
  and the documented 0.5–15.0 second diagnostic window.
- [x] Network shares, cloud sync, replicated writers, multi-machine guarantees,
  distributed consensus, failover copies, and active-ledger copying are excluded.
- [x] Six Phase 2 experiment artifacts are proposed but not created in Phase 1.
- [x] The proposed experiment remains private, nonpackaged, and noncanonical.
- [x] No public schema is introduced.
- [x] Production modules do not import experiment modules.
- [x] No Tool invocation, dispatch transport, `repository_file_read`, protected
  resource access, availability probe, credential handling, or Result path exists.

## Scenario and validation safety locks

- [x] The locked minimum scenario matrix contains exactly 128 rows.
- [x] Matrix reduction or material combination requires Human review.
- [x] Atomicity, retry, crash, migration, races, expiry, reclaim, renewal,
  fencing, time, restart, corruption, substitution, and negative execution
  boundaries are represented.
- [x] At Phase 1 design lock, all Phase 2 validation commands were prospective
  and unexecuted.
- [x] `markdownlint-cli2@0.23.3` is prospectively pinned through the fixed
  offline executable, exact paths, and `--no-globs`.
- [x] Test commands use exact modules and prohibit broad discovery.
- [x] Every prospective Python command uses the fixed interpreter with
  `-E -s -B`, an exact repository working directory, and requires startup,
  system-site `.pth`, and import-closure inspection before execution.
- [x] Package-surface validation is inapplicable unless a prohibited package
  change first triggers a stop and matrix amendment.
- [x] Any future smoke requires a dedicated `--aio-054-safe` mode, explicit
  allowlists, disposable environments, and pip `--isolated --no-index
  --no-deps --no-cache-dir`.
- [x] Generic `--target-safe` is not treated as sufficient preflight.

## Phase 1 design reviews

- [x] Fresh Architect design review approves the common Phase 1 snapshot.
- [x] Fresh Security design review approves the common Phase 1 snapshot.
- [x] Fresh Storage/Atomicity design review approves the common Phase 1 snapshot.
- [x] Fresh Operational Trust design review approves the common Phase 1 snapshot.
- [x] No unresolved blocker or high-severity Phase 1 finding remains.
- [x] Phase 1 review evidence is recorded accurately in `review.md`.
- [x] AIO-054 is ready for separate Phase 2 experiment authorization.

## Phase 2 experiment evidence

- [x] Separate Human Phase 2 authorization is recorded before any experiment artifact is created.
- [x] The six proposed experiment artifacts are implemented within scope.
- [x] The experiment remains outside the production package and public schemas.
- [x] All 128 locked scenarios execute every locked path and pass, or failures
  are reported without silently changing the hypotheses.
- [x] Atomic Admission/Intent commit or rollback is demonstrated at every fault cut point.
- [x] Legacy migration classification is demonstrated without pending-work backfill.
- [x] Same-host spawned-process raw SQLite storage races are demonstrated
  separately from in-process lifecycle-surrogate behavior.
- [x] Exact committed Claim/Renewal response-loss recovery, no-row safe
  reevaluation, and terminal-fence limitations are demonstrated distinctly.
- [x] Expiry, reclaim, monotonic fencing, and stale-claimant rejection are demonstrated.
- [x] Clock rollback and restart behavior are demonstrated.
- [x] The negative no-transport/no-invocation boundary is demonstrated.
- [x] The old T3 was rejected by static preflight, never executed, caused no
  process incident, and is recorded as superseded before execution.
- [x] The Human-authorized amended T3 passed fresh static preflight and its one
  exact test with two children created, reaped, and handle-closed plus one
  owned temporary root created and removed.
- [x] Every executed command passed its recorded static safety preflight.
- [x] Applicable exact validation commands pass.
- [x] Phase 2 experiment evidence is complete across every locked scenario
  requirement.
- [x] The interrupted Storage/Atomicity final review remains recorded as
  `CHANGES REQUIRED` with `STORAGE-054-1` high.
- [x] Scenario 53 freshly proves actual controlled clock exceptions for both
  Claim and Renewal, no durable mutation, and later success with the same IDs.
- [x] `STORAGE-054-1` is remediated without Store, runtime, schema, algorithm,
  numbering, production, or public-contract changes; the other 127 scenario
  results are retained and a fresh Phase 3 restart is required.
- [x] The fresh Formal Independent Review remains permanently recorded as
  `CHANGES REQUIRED` with `EVIDENCE-054-1` high and `STORAGE-054-1` closed.
- [x] Scenario 57 executes a pre-jump active Lease, early expiry, reclaim at the
  next generation, stale-generation Renewal/current-authority rejection,
  current-generation authority, immutable history, and watermark behavior.
- [x] Scenario 59 executes exact Intent, Claim, Renewal, clean migration-state,
  and watermark survival across its SQLite/WAL restart boundary.
- [x] Only the scenario-57 and scenario-59 test handlers changed; Store, worker
  harness, schema, algorithms, scenario identities, and production semantics
  remain unchanged.
- [x] The 126 unaffected prior passes plus fresh scenario 57 and scenario 59
  passes yield 128 passed, 0 failed, and 0 skipped without a full matrix rerun.
- [x] `EVIDENCE-054-1` is remediated with no unresolved blocker or high finding,
  and a fresh Phase 3 is required.
- [x] The later historical Formal Independent Review remains permanently
  `CHANGES REQUIRED` with `EVIDENCE-054-2` high, `STORAGE-054-1` closed, and
  `EVIDENCE-054-1` closed.
- [x] A corrected bounded static traceability audit maps all 128 locked
  scenarios to exact executed paths and assertions without Task enumeration,
  repository-wide search, or test discovery.
- [x] The EVIDENCE-054-2 before-state records 72 complete scenarios, 56
  requiring evidence remediation, and zero Store/runtime defects before any
  test execution.
- [x] All 56 recorded deficiencies are remediated through test or bounded
  harness evidence without changing Store, schema, algorithms, scenario
  identities, production code, or public contracts.
- [x] The final fresh full-matrix execution passes 128 scenario methods, with
  0 failures and 0 skips.
- [x] Scenario 116 executes equal-time byte-order winner selection after a
  restart for each insertion order, rather than only auditing a Claim selected
  before restart.
- [x] Every locked scenario has zero unmapped locked paths.
- [x] EVIDENCE-054-2 exact A1, V1, and M1 reruns pass.
- [x] `EVIDENCE-054-2` is closed with no unresolved blocker or high finding.
- [x] Experiment findings distinguish confirmed, rejected, and bounded hypotheses.

## Final review and closure

- [x] Fresh final Architect review approves the experiment evidence.
- [x] Fresh final Security review approves the experiment evidence.
- [x] Fresh final Storage/Atomicity review approves the experiment evidence.
- [x] Fresh final Operational Trust review approves the experiment evidence.
- [x] Formal Independent Review approves.
- [x] `documentation_consistency` passes without an unresolved finding.
- [x] `independent_review` passes without an unresolved finding.
- [x] Required Human final approval is recorded.
- [x] No required Quality Gate failed or was skipped at closure.
- [x] Task status is changed to `completed` only after every closure requirement is met.
