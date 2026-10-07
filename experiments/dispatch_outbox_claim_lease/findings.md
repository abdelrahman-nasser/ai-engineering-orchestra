# AIO-054 Phase 2 Experiment Findings

These findings describe a private, disposable, noncanonical SQLite
experiment. They do not establish production acceptance, canonical AIO-049
ownership integration, dispatch transport, Tool invocation, repository
resource access, credential use, Result handling, or external-effect
exactly-once behavior.

## Outcome summary

- The historical full T1 run executed all 128 scenario identities: 128 passed,
  0 failed, and 0 skipped. Later reviews found missing locked-path coverage in
  scenarios 53, 57, and 59; each gap was remediated through exact fresh nodes.
- That post-EVIDENCE-054-1 composite was 126 retained passes plus freshly
  passed scenarios 57 and 59. The later EVIDENCE-054-2 remediation reran the
  full matrix: current evidence is 128 freshly passed, 0 failed, and 0 skipped,
  with all 128 locked scenarios mapped and no locked path unmapped.
- Atomic Admission and Dispatch Intent persistence, immutable history retry,
  Claim and Renewal ordering, Lease expiry and reclaim, generation fencing,
  clock failure, crash, restart, corruption, revocation, and substitution
  cases resolved as designed inside the locked local profile.
- The experiment required no material hypothesis or architecture change. The
  original execution corrected one concrete `pathlib.Path` type check and
  three fixture expectations. Later authorized remediations added missing
  test/harness paths for 56 scenarios and corrected one scenario-41 fixture
  reset; locked identities and expected safety properties were not reduced or
  rewritten.
- The experiment remains outside the package and adds no public schema.
- The old T3 was rejected by static preflight and superseded before execution;
  it caused no process incident. Its Human-authorized experiment-only
  replacement passed with two owned children created and reaped, both handles
  closed, and one owned temporary root created and removed.
- The T3 amendment changed harness isolation and cleanup only. At that stage,
  the 128-of-128 scenario result was retained without rerunning Store semantics.
- The first Phase 3 Storage/Atomicity final review returned `CHANGES REQUIRED`
  with `STORAGE-054-1` high because scenario 53 did not execute its locked
  Claim and Renewal throwing-clock paths. That historical outcome is retained.
- Bounded Phase 2 remediation changed only scenario-53 coverage. Scenario 53
  freshly passed, two exact Claim/Renewal happy paths passed, and the other 127
  scenario results are retained; a full 128-scenario rerun was not required.
- The later Formal Independent Review returned `CHANGES REQUIRED` with
  `EVIDENCE-054-1` high for incomplete scenario-57 and scenario-59 coverage.
  Their bounded test-only remediation freshly passed T6 and T7; 126 unaffected
  results are retained and no full 128-scenario rerun was required.
- The still-later Formal Independent Review returned `CHANGES REQUIRED` with
  `EVIDENCE-054-2` high. A bounded audit found 56 incomplete evidence paths and
  zero Store/runtime defects. Test/harness-only remediation plus the final T8
  rerun produced 128 passes, 0 failures, 0 skips, and 0 unmapped locked paths.

## Hypothesis classifications

| Hypothesis | Classification | Bounded conclusion |
| --- | --- | --- |
| Admission and Intent atomicity | SUPPORTED | One `BEGIN IMMEDIATE` transaction commits one new Admission, one immutable Intent, and sampled-now watermark together, or commits none. |
| Legacy migration | SUPPORTED | A nonempty legacy ledger migrates atomically to exactly one marker-or-Intent classification per Admission without activating historical work; malformed, partial, and ambiguous states fail closed. Administrative quiescence remains an external precondition. |
| Exact Admission retry | SUPPORTED | Exact committed retry returns the original Admission and Intent without clock dependence, duplication, reset, or rebound. |
| Claim idempotency | SUPPORTED | A committed `claim_id` returns immutable history exactly; rebound conflicts fail closed. No-row outcomes leave the ID unconsumed for explicit reevaluation. |
| Response-loss recovery | SUPPORTED | Committed Admission, Claim, and Renewal history is recovered by exact retry. No-row outcomes are reevaluated, and terminal fencing permits only non-authoritative audit. |
| Lease expiry and reclaim | SUPPORTED | Half-open expiry permits a new Claim after exact expiry, requires a new `claim_id`, and preserves every prior Claim as history. |
| Generation fencing | SUPPORTED | Reclaim allocates the next contiguous per-Intent generation; stale, malformed, rebound, gapped, and exhausted generations fail closed on modeled authority paths. |
| Renewal idempotency | SUPPORTED | A committed `renewal_id` returns one immutable Renewal without extending twice; no-row expired or nonextending outcomes remain explicitly reevaluable. |
| Concurrent Claim serialization | SUPPORTED | Same-host local SQLite `BEGIN IMMEDIATE` ordering produces one authoritative current generation under thread and spawned-process races. No multi-machine claim is made. |
| Clock rollback | SUPPORTED | Unavailable, malformed, naive, non-UTC, lossy, or below-watermark time fails closed without repair, clamping, or unauthorized mutation. |
| Watermark semantics | SUPPORTED | The shared watermark advances only to sampled decision time, never to Lease expiry; equality is accepted and regression is rejected. |
| Crash recovery | SUPPORTED | Precommit fault cuts roll back; postcommit response ambiguity is reconciled by exact history; normal local crash recovery requires no Human repair. |
| Restart behavior | SUPPORTED | SQLite/WAL and process restart preserve history, while a restarted worker receives a fresh process-local Executor capability. Storage-process and lifecycle evidence remain separate lanes. |
| Stale claimant rejection | SUPPORTED | Superseded generations cannot renew or obtain current-Claim evidence; old Executor tuple replay is rejected at the coordinator capability boundary. The raw Store alone cannot prove process incarnation. |
| Lifecycle surrogate | PARTIALLY SUPPORTED | The in-process surrogate demonstrates concurrent guards, complete-operation post-checks, loss, fencing, and quiescence. It is not the canonical AIO-049 owner and is not combined with spawned workers. |
| Post-Admission revocation | SUPPORTED | Same-ledger revocation serializes with Claim and Renewal decisions, preserves immutable history, and blocks later modeled authority. External JIT permission remains future work. |
| Substitution and widening resistance | SUPPORTED | Wrong Admission, Run, Tool, Runtime, Actor, operation, and resource relationships cannot override stored authority-bearing content and fail closed. |
| No invocation path | SUPPORTED | No experiment API reaches dispatch transport, Tool execution, repository resource I/O, availability probes, credentials, Result attachment, or an external side effect. |
| Production suitability | PARTIALLY SUPPORTED | The experiment provides technical evidence for reconsideration after a fresh Phase 3. It does not establish production-design readiness or authorize implementation, and it leaves canonical ownership integration, production migration administration, future action authority, transport, and backend portability unresolved. |

## Detailed evidence

### Atomic persistence and migration

Crash cuts before the transaction, after Admission insertion, after Intent
insertion, and after watermark update left neither half of the pair durable.
Both ambiguous-commit branches were distinguishable by exact retry. Concurrent
identical Admissions converged on one exact pair, while temporal, revocation,
binding, Run, and conflict-precedence rejection emitted no orphan Intent.

Legacy migration used one same-ledger transaction and preserved historical
Admissions as non-dispatchable markers. Dirty, old, newer, partial, missing,
overlapping, orphaned, duplicate, and checksum-mismatched states failed closed.
This is storage evidence only: WAL `BEGIN EXCLUSIVE` serializes writers but
does not itself prove reader or multiprocess administrative quiescence.

### Claim, Lease, Renewal, and fencing

The fixed Lease duration was 30,000,000 microseconds. Claims and Renewals were
append-only; pending, claimed, and reclaimable status was derived. Exact
history never asserted live authority. Separate current-Claim assessment
checked highest generation, effective expiry, revocation, trusted time, the
watermark, and lifecycle post-check before returning point-in-time evidence.

Reclaim produced monotonically increasing generations over repeated cycles.
Stale generations, expired Claims, rebound identities, sequence gaps,
duplicates, nonpositive values, and signed-64-bit exhaustion failed closed.
Concurrent Claim and Renewal-versus-reclaim races reduced to one serialized
SQLite writer order.

### Clock, crash, and restart

Lease validity followed `acquired_at <= now < lease_until`. New decisions
sampled trusted UTC after writer serialization and advanced the watermark to
that sample only. Exact committed-history retries did not sample the clock.
A trusted forward jump can expire a Lease early; fencing still prevents the
older generation from later modeled authority.

Spawned raw-storage probes exercised hard exits, commit ambiguity, busy
writers, WAL reopen, and process restart against disposable ledgers. They are
not operational workers. The lifecycle surrogate exercised authority entry
and post-check in-process. The two lanes cannot be composed into a canonical
multiprocess ownership guarantee.

### Revocation and negative boundary

Revocation-first blocked Claim or Renewal. Claim/Renewal-first retained
immutable history but supplied no continuing authority after revocation.
Terminal fencing likewise restricted reconciliation to read-only,
non-authoritative same-ledger audit.

The experiment accepts no Tool, Runtime, Actor, operation, or resource
override and contains no transport or invocation surface. Scenario 75 walks
the bounded helper closure of the exact experiment modules, and scenario 120
inspects loaded experiment objects and signatures. Neither exposes repository
resource access or claims canonical AIO-049 compatibility.

## Validation record

| ID | Result |
| --- | --- |
| A1 | PASS; the three exact experiment Python files parsed successfully, including the EVIDENCE-054-2 rerun. |
| T1 | HISTORICAL PASS; 128 tests ran, 128 passed, 0 failed, 0 skipped before the bounded scenario-53, scenario-57, and scenario-59 coverage remediations. |
| T2 | PASS; 48 exact production Admission Store compatibility tests passed. |
| T3 (OLD) | REJECTED BY STATIC PREFLIGHT BEFORE EXECUTION; SUPERSEDED BEFORE EXECUTION; no process incident and no unsafe command execution. |
| T3 (AMENDED) | PASS; one exact non-discoverable test, 2 children created and reaped, 2 handles closed, and 1 owned temporary root created and removed. |
| T4 (STORAGE-054-1) | PASS; exact scenario 53 freshly exercised Claim and Renewal throwing-clock failure plus exact later-success paths. |
| T5 (AFFECTED CLAIM/RENEWAL) | PASS; exact scenarios 18 and 38 passed, 2 tests total. |
| T6 (EVIDENCE-054-1 SCENARIO 57) | PASS; the exact amended scenario freshly executed early expiry, reclaim, generation fencing, stale rejection, current authority, immutable history, and watermark behavior. |
| T7 (EVIDENCE-054-1 SCENARIO 59) | PASS; the exact amended scenario freshly executed Intent, Claim, Renewal, migration-state, and watermark survival across SQLite/WAL restart. |
| T8 (EVIDENCE-054-2 MATRIX) | PASS; the final fresh exact module run executed 128 scenarios, with 128 passed, 0 failed, and 0 skipped. |
| V1 | PASS; the exact AIO-054 Task document validates against the Task schema, including the EVIDENCE-054-2 rerun. |
| V2 | PASS; the exact architecture-change Workflow validates against the Workflow schema. |
| M1 | PASS; the fixed offline `markdownlint-cli2@0.23.3` command reports no errors for the five exact Markdown paths, including the EVIDENCE-054-2 rerun. |
| P1 | NOT REQUIRED; package metadata and package surface were not changed. |
| S1 | NOT REQUIRED; the experiment is nonpackaged and no package smoke was applicable. |

The first T1 execution exposed an experiment configuration defect that
rejected a valid concrete Windows `Path`. After that narrow correction, a
second full run passed 125 scenarios and exposed one lifecycle assertion and
two corruption-fixture errors. The lifecycle assertion was aligned with the
locked terminal-fence post-check semantics, and the corruptions were changed
to pass the row-level check before reaching the integrity audit. The final
full run passed all 128 scenario identities. That full run is historical:
subsequent bounded coverage remediations freshly executed the missing locked
paths without changing any hypothesis, scenario identity, or expected safety
property.

The amended T3 used the approved absolute Python interpreter and worker path,
one fixed external local-NTFS temporary parent, one invocation-owned
nonce-marked root, an explicit minimal environment, finite waits, and retained
handles for only its two children. It used no shell, process enumeration,
wildcard termination, network, production authority, protected target, or
repository runtime storage. The exact test left no owned root or repository
runtime artifact.

## STORAGE-054-1 remediation

The interrupted Phase 3 record remains:

- STORAGE/ATOMICITY FINAL REVIEW: `CHANGES REQUIRED`;
- STORAGE-054-1: `HIGH`; and
- finding: locked scenario 53 did not execute its required throwing-clock
  paths for Claim and Lease Renewal.

STORAGE-054-1 REMEDIATION: Scenario 53 now samples and raises exact controlled
clock exceptions in both paths. Claim returns `clock_failure`, commits no row,
generation, or watermark change, preserves the immutable Intent, and then
commits the same request at generation 1. Renewal returns `clock_failure`,
commits no row, effective-expiry, sequence, watermark, or Claim change, and
then commits the same request at sequence 1.

CLAIM THROWING-CLOCK: **PASS**

RENEWAL THROWING-CLOCK: **PASS**

STORAGE-054-1 STATUS: **REMEDIATED**

No Store, runtime, worker-harness, schema, algorithm, retry-identity, scenario
number, production, or public-contract semantics changed. Current composite
scenario evidence is the other 127 prior passes plus the fresh scenario-53
pass. A fresh Phase 3 restart is required; no prior Phase 3 approval is reused.

## EVIDENCE-054-1 remediation

The subsequent fresh Phase 3 preserved four fresh specialist approvals and
confirmed `STORAGE-054-1` closed, but its Formal Independent Review returned
`CHANGES REQUIRED`. `EVIDENCE-054-1` was high because scenario 57 omitted the
Lease-expiry, reclaim, and stale-generation chain required by its locked
forward-jump wording, while scenario 59 omitted Claim, Renewal, migration-state,
and watermark survival required by its locked SQLite/WAL restart wording. The
Quality Gates did not run.

The Human returned only that finding to Phase 2. Scenario 57 now executes an
active generation 1 before the jump, expired classification, generation-2
reclaim, stale generation-1 Renewal and current-authority rejection, active and
renewable generation 2, immutable generation-1 history, and nonregressing
watermark behavior. Scenario 59 now executes and exactly audits Intent, Claim,
Renewal, clean migration state, and the Renewal watermark through bounded fresh
spawned processes and a post-chain WAL reopen.

SCENARIO 57: **PASS**

SCENARIO 59: **PASS**

EVIDENCE-054-1 STATUS: **REMEDIATED**

Only the two scenario handlers changed. Store, worker harness, schema,
algorithms, numbering, production code, and public contracts did not change.
The composite evidence is 126 retained passes plus fresh scenario 57 and
scenario 59 passes: 128 passed, 0 failed, and 0 skipped. A fresh Phase 3 is
required; the historical Formal Independent Review remains `CHANGES REQUIRED`.

## EVIDENCE-054-2 remediation

The later fresh Phase 3 permanently recorded FORMAL INDEPENDENT REVIEW:
`CHANGES REQUIRED`, EVIDENCE-054-2: `HIGH`, STORAGE-054-1: `CLOSED`, and
EVIDENCE-054-1: `CLOSED`. It identified 12 incomplete scenarios and stopped
before Quality Gates. A subsequent authorized static audit mapped all 128
locked scenarios before executing tests. The before-state was 72 complete, 56
requiring test/harness evidence remediation, and zero Store/runtime defects.

The 56 remediated scenarios are:

`12, 13, 17, 21, 24, 28, 33, 39, 41, 42, 52, 56, 58, 60, 64, 65,
66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 81, 82, 83,
84, 85, 89, 91, 92, 94, 96, 97, 98, 99, 103, 104, 105, 110, 111,
113, 114, 118, 119, 121, 122, 124, 126, 128`.

The first fresh full-matrix run exposed one test-fixture reset defect in
scenario 41. After that bounded correction, the exact scenario passed and the
final fresh full matrix passed 128 scenarios, with zero failures and zero
skips. Every locked scenario is now mapped to executed evidence and no locked
path remains unmapped.

EVIDENCE-054-2 STATUS: **REMEDIATED**

No Store semantics, schema, Claim or Renewal algorithm, clock model,
generation model, migration model, revocation model, scenario identity,
production code, or public contract changed. A1, V1, and M1 freshly passed.
There are zero unresolved blockers and highs. Phase 2 is complete including
EVIDENCE-054-2 remediation, and a fresh Phase 3 is required.

## Production recommendation

READY FOR AIO-055 PRODUCTION OUTBOX DESIGN?: YES - DESIGN ONLY

READY FOR AIO-056 CLAIM-LEASE DESIGN?: YES - DESIGN ONLY

Any future recommendation may authorize design work only. Production design must
resolve all of the following before implementation acceptance:

- canonical AIO-049 ownership and extended-Store integration;
- enforceable administrative quiescence for production migration;
- process-incarnation authority at every future acknowledge, progress,
  invocation, and Result boundary;
- production backend, deployment, and multi-process containment semantics;
- JIT permission and revocation checks at future external-effect boundaries;
  and
- bounded production process containment and operational cleanup semantics.

Phase 2 is complete including all bounded evidence remediations. The final
fresh Phase 3 specialist and Formal Independent Reviews approved the evidence
with blocker 0, high 0, medium 0, and low 0. AIO-055 and AIO-056 are ready for
production design only; no production implementation is authorized by this
recommendation. AIO-054 remains `in_progress` pending Human final approval and
closure controls.
