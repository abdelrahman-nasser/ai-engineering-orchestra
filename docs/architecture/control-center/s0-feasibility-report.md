# ITRU Control Center S0 synthetic feasibility report

Date: October 17, 2026.

**Recommendation: NO-GO for advancing to S1 or admitting an operational read
port under unchanged P07.** S0 produced isolated definitions, synthetic contract
fragments, measurements and reviewable evidence. Correctness tests passing does
not establish operational feasibility or override this NO-GO.

## Scope, authority and repository state

The Human authorized Phase A documentation archival followed by S0 only.
The later Human disposition accepted exactly five formatting findings in the
byte-preserved plan: Markdown hard breaks at lines 3–6 and final blank line 439.
The whole-staged whitespace check returned **exit 2**, not PASS; its exact
diagnostic set was verified, with no additional findings. Authored index/decision
whitespace checks returned exit 0. Independent documentation/governance and
integrity reviews approved the narrow accepted disposition.

Phase A documentation commit:
**19a321fc0876e73b9f83109f2a58528c9d54e331**,
message: **docs: archive approved Control Center integration plan**.
Its parent is 726e11a2f2e408ee02a4981c64eaae031fb25381. The commit contains only:

- docs/architecture/control-center/README.md
- docs/architecture/control-center/human-decisions.md
- docs/architecture/control-center/integration-implementation-plan.md

The committed plan blob was read as raw bytes and verified with SHA-256
**93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d**.
Git was clean after that commit. The new branch
**feature/control-center-s0-feasibility** was created from it.
S0 changes remain unstaged and uncommitted for separate Human final review.

Architecture v2 remains unchanged at SHA-256
**c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062**.
The original investigation and addendum retain their approved archived hashes.
H2 is resolved only as the Human specified: historical event validation may use
continuation_eligible; neither query may assess/expose current eligibility,
which remains unassessed with disabled controls.

The governance audit found canonical Task-conformance requirements, but no
unconditional requirement for a Human-assigned Task ID or a separately approved
different Workflow before this scoped experiment. No Task ID or Task-conformance
claim was invented. Standard-change understanding, implementation, validation
and independent review obligations were applied; Human final acceptance remains.

## Implemented S0 artifacts

| Path | Actual scope and limits |
| --- | --- |
| itru/control_center_read_source.py | Frozen expected source/ledger/policy definitions and exact reference validation. No I/O, registry, discovery, authentication, audience grant, storage observation or query handler. |
| itru/control_center_read_budget.py | Fixed complete P07 numerical profile, deterministic logical-JSON quota encoding and pure cumulative-work assessments. No runtime admission, context/cursor registry, streaming encoder, clock enforcement or cancellation. |
| tests/test_control_center_feasibility.py | Nine scoped checks/controlled experiments and isolated child measurements; no operational owner construction or production module edits. |
| tests/fixtures/control_center/application-v1-cases.json | Explicitly synthetic identity/request/error/numeric/timestamp/continuation/payload fragments. Not complete application responses or proof of a decoder. |
| tests/fixtures/control_center/s0-measurements-4d7e21c5cadd42359380a5627c8e5617.json | First run measurements retained despite a harness assertion failure. |
| tests/fixtures/control_center/s0-measurements-a3ee3d159d7347ea98f5be26e7c3b40f.json | Second run measurements retained despite a malformed-corruption-fixture error. |
| tests/fixtures/control_center/s0-measurements-1938337ad1624a0e8cb9169a543584d5.json | Final complete nine-check run and six isolated validator measurements. |
| docs/architecture/control-center/s0-feasibility-report.md | This evidence, limitations, review dispositions and NO-GO recommendation. |

No existing production runtime/store/scheduler module, database schema, UI file,
canonical architecture, approved plan, configuration or Task artifact was edited
for S0. No S1–S8 feature, transport or live source was implemented.

## Controlled fixture and execution boundary

All synthetic database directories were freshly allocated with an ownership
marker under tests/fixtures/control_center/temporary/s0-owned-*.
Before writes, the harness verifies resolved repository containment and rejects
existing symlink/reparse ancestors. It pins fixture/control/allocated-directory
identities, rechecks them and validates every contained object before recursively
deleting only that newly allocated directory. No existing user data was reused
or deleted. The controlled temporary directory was empty after the final run.
Evidence JSON files use exclusive creation and unique names and are retained.

Measurement input accepts only journal/lifecycle and exact counts 1..10000,
before creating directories or formatting a database path. Each child has a
45-second experiment timeout. None timed out in the final run. Killing a child,
if necessary in a future run, would be NO-GO evidence, not proof of bounded
in-process cleanup. Fixture guards are cooperative synthetic-test safeguards,
not an adversarial atomic filesystem pinning implementation.

Synthetic schemas use the current checksummed Journal SQL and current lifecycle
DDL without modifying them. Standard-library SQLite connections create those
new fixture files. Existing unbound _verify methods run against those synthetic
connections/configuration values, avoiding operational store constructors.
Measurement children patch lifecycle/Journal constructors and provisioning
methods to raise if unexpectedly called. No owner lock, operational registry,
authoritative ledger, execution invocation or live Result/Grant/observation
membership is created.

Fixture Grant/Admission/provenance-shaped fields are descriptive synthetic
inputs for semantic validation. Their required enum spellings do not prove
controlled invocation, Human approval or real authorization.

## Toolchain and exact commands

Existing installed tools only; no download, installation, network, credential,
Codex diagnostic or D6-E/B1 execution occurred.

| Tool or clock | Recorded value |
| --- | --- |
| Python | 3.12.10, MSC v.1943, 64-bit AMD64 |
| Interpreter | C:/Users/Abdelrahman/AppData/Local/Programs/Python/Python312/python.exe |
| Platform | Windows-11-10.0.26300-SP0 |
| SQLite | 3.49.1 |
| perf_counter | QueryPerformanceCounter(), monotonic, resolution 0.0000001 seconds |
| monotonic | GetTickCount64(), monotonic, resolution 0.015625 seconds |

The initial command-name invocation of python failed because it was absent from
the sandbox PATH (exit 1). The already-installed interpreter was identified from
existing environment metadata; no environment or package was installed/changed.
Its explicit-path version command returned exit 0.

All three suite runs used this exact command from the Core repository:

~~~powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -s tests -p test_control_center_feasibility.py -v
~~~

| Run | Result and duration | Honest disposition |
| --- | --- | --- |
| 1 | Exit 1; 8 checks, 11.792 seconds; one failure | The read-only INSERT correctly failed, but the harness expected the interruption error text instead of readonly. Assertion corrected. Measurement artifact 4d7e21... retained. |
| 2 | Exit 1; 8 checks, 36.041 seconds; one error | The corrupt-row fixture used a boolean forbidden by canonical Core JSON, so encoding rejected it before insertion. Replaced with a canonical scalar string to test later semantic rejection. Artifact a3ee3d... retained. |
| 3 | **Exit 0; 9 checks, 36.759 seconds; zero failures/errors/skips** | Final corrected, containment-hardened run. Artifact 1938337... is the complete current evidence. This is synthetic check success, not P07/operational PASS. |

For each mode/count in journal/100, journal/1000, journal/10000,
lifecycle/100, lifecycle/1000 and lifecycle/10000, the suite invoked:

~~~text
<same installed Python> -B D:\Dev\ai-engineering-orchestra\tests\test_control_center_feasibility.py --measure <mode> <count>
~~~

Each final child returned exit 0. Exact command construction and 45-second
timeout are in test_08. SQLite validation timing uses perf_counter_ns.
The parent captures output and records child wall time separately.

## Measurements from the complete final run

Each measurement uses a newly created synthetic file. Timing below covers
existing whole-store semantic validation only. It excludes fixture setup,
opening the passive connection, BEGIN, rollback/close, ownership leases,
coordination wait, graph pinning/evaluation, authentication, projection and
response encoding. Therefore it is a lower bound on a future complete capture.

| Store / rows or events | Canonical metadata bytes | Untraced validation seconds | Separate Python allocation peak bytes |
| --- | --- | --- | --- |
| Journal / 100 | 148052 | 0.0653405 | 786424 |
| Journal / 1000 | 1485453 | 0.3143710 | 7581073 |
| Journal / 10000 | 14904454 | 2.7682845 | **76331067** |
| Lifecycle / 100 | 34047 | 0.0079576 | 321883 |
| Lifecycle / 1000 | 347281 | 0.0865089 | 3116054 |
| Lifecycle / 10000 | 3509615 | **1.9891229** | 29745177 |

All row/event counts and canonical metadata totals are within their 10000/16-MiB
P07 per-request limits. The lifecycle fixture uses one synthetic Task and repeated
historical successful continuations, totaling 10000 events. No operational Task
was registered. The 1.989-second validation alone exceeds the one-second capture
hold, before scheduling or cleanup; reusing this unchanged implementation cannot
satisfy the complete hold on this measured shape/environment.

Journal validation is not subject to the lifecycle one-second hold. The generic
within_one_second measurement field on Journal rows is only a timing comparison;
the approved whole-query deadline remains ten seconds and is not established
by these validation-only measurements.

The Journal's measured Python allocation peak exceeds the 64-MiB query limit
(67108864 bytes) by **9222203 bytes**, before any unmeasured native allocation,
application comparison or encoding. The source snapshot is below 16 MiB.
This establishes a concrete memory problem with the current materializing
validator on this fixture, not merely a large-file hypothesis.

Allocation peaks come from a separate tracemalloc pass. Journal/10000 took
16.2913272 seconds with tracing; lifecycle/10000 took 7.5528395 seconds.
These tracing-inflated durations are not substituted for the untraced timing.
tracemalloc does not prove complete native/per-query allocation accounting.
Windows current-process working-set/private/lifetime peaks are also recorded:
Journal/10000 after untraced validation had working set 128671744 bytes and
private bytes 116850688. These include interpreter/allocator effects and are
not a clean per-query native peak or application-wide concurrency proof.

No whole-query ten-second claim follows from sub-ten-second validation alone.
Only three sizes and specified synthetic shapes were measured, without repeated
statistical distributions, hostile I/O, all 16-MiB shapes, graph maxima or a
real owner. Small-case timings are not evidence that full operational P07 works.

## Journal traversal, cancellation and SQLite sidecars

The 2000-row traversal experiment revalidates the entire current Journal for
each modeled page. It freezes H=2000:

- First page scans 1000 global rows, matches none, position becomes 1000,
  and remains partial.
- Second page scans to 2000, returns the synthetic match at sequence 1501,
  and reaches the frozen high water.
- A newly appended malformed semantic row at 2001 makes subsequent complete
  current validation fail, despite lying beyond H.
- Additional model cases cover H=0 and stopping before skipping the next match
  when a requested output count is reached. Read-only DML is rejected.

The scanner is test-only, matches a synthetic Run ID and iterates/decodes an
already materialized validated tuple. It is **not** full P05 exact-subject
matching, a physically work-bounded SQL scan, cursor/context implementation,
subject-uniqueness proof, application query or authorization boundary.

| Narrow cancellation experiment | Measured interruption plus rollback/close | Observed result |
| --- | --- | --- |
| DELETE mode SQL recursive computation | 20.0894 ms | Specific interrupted error; subsequent writer transaction succeeded. |
| WAL mode SQL recursive computation | 20.1047 ms | Specific interrupted error; subsequent writer transaction succeeded. |

These use an SQLite progress handler and a 20-ms synthetic deadline. They do
not prove cancellation of Python decoding/reduction/scheduling/encoding,
blocked OS filesystem I/O, every SQLite operation or arbitrary resource close.
No one-second owner lease or actual shutdown protocol exists in S0.
Connections have unconditional teardown and setup-failure cleanup in the harness.

DELETE mode showed no WAL/SHM and a rollback journal during the writer
transaction. WAL mode showed established WAL/SHM and no DELETE journal.
In the 10000-row Journal fixture the base database was **4096 bytes**, WAL
**21300432 bytes**, SHM **65536 bytes**. Thus a small base file does not establish
a small current WAL-backed snapshot. This experiment does not prove absence of
shared-memory bookkeeping writes or total sidecar/native/I/O bounds.
No query checkpoint, migration, sidecar repair, immutable-mode shortcut or
provisioning fallback was introduced.

## Coordination and complete mutation/shutdown inventory

The controlled condition-variable model recorded writer before late-reader,
with elapsed time 0.4744 ms. It models one deliberately scheduled ordering.
Its two-second test guards are failure guards, not the approved capture bound.
It does not exercise owner shutdown, every writer, unfair OS scheduling, hostile
contention or one-second safe drain. Existing production RLock remains unchanged.

Source lines below refer to the unchanged existing implementation.

| Path / symbol | Mutation or lifecycle responsibility a future shared boundary must cover |
| --- | --- |
| sqlite_task_run_state.py:121 constructor | Exclusive owner acquisition, read/write open, validation and startup recovery. Complete before admission; no query startup. |
| :153 provision | Directory/lock/database creation, DDL/metadata commit and constructor; independently authorized administration only. |
| :217 _transaction | Shared mutex, session checks, BEGIN IMMEDIATE, validation, commit/rollback. |
| :243 _append | CAS, event reduction and append; no direct bypass. |
| :261 enroll | Enrollment and exact retry transaction. |
| :271 register_run | Initial registration and historical exact retry. |
| :280 transition | All block/cancel/complete/stop operations, including unfinished Run changes. |
| :286 start_run | Run-start append. |
| :290 record_result | Original Result membership/subject/outcome validation and result append. |
| :306 continue_task | Checkpoint, current revision, trusted authorizer callback and continuation append; preserve fresh authority and recursion rejection. |
| :341–367 get_task/get_run/checkpoint/page | Existing operational read transactions also use BEGIN IMMEDIATE; their names do not make them passive readers. |
| :369 close | Connection/lock teardown; must publish closing/bar admission before waiting on future leases. |
| :178 _check_session | PID, storage/security/lock identity and ownership-loss failure. |
| Constructor failure and _connect failure | Partial initialization/connection cleanup must join resource lifecycle. |
| Process/context loss | Ownership ends; no query restart or reconstructing references from client state. |
| developer_alpha.initialize/load_work/open_state | Provisioning, work-file writes/enrollment and operational owner construction; never reader availability fallbacks. |
| developer_alpha.execute | Registration/continuation, provider-failure stop, start, missing-Result stop, Result acceptance and closing(open_state(...)). |
| developer_alpha.command | Operational open, explicit complete/stop commands, and close. |
| alpha_authority.AlphaExecution.close | Distinct native-root/authorizer/trust teardown, not a passive-resource manager. |

The existing SQLite busy timeout is five seconds; RLock lacks explicit writer
priority/timed acquisition; close sets closed only after acquiring the mutex.
Validation uses quick_check/materialization and Python reduction without
integrated cancellation. These remain verified source gaps, not fixed features.
The inventory is complete for the inspected current source/callsites; future
changes require re-audit rather than relying permanently on this list.

## Definitions, numeric fixtures and accounting

SourceRevision preserves exact opaque source/project/store/Journal/definition/
graph/policy/budget references, three ledger fields and Alpha concurrency 1..2.
It rejects invalid Unicode, empty identifiers, boolean generation/concurrency
and wrong types without trimming/normalizing. Positive generation is not
artificially limited to 64 bits. Policy reference equality declares neither
freshness nor entitlement. Full audience approval and immutable registry mapping
remain absent; no actual dataset or metadata audience is registered/granted.

The fixed P07BudgetProfile exposes all approved bounds unchanged, including:
1/source, 1/principal, 2/global, no queue; request 16 KiB; Core graph 1000/10000;
lifecycle/Journal 10000/16 MiB and 1-MiB record caps; 1000 global scan rows,
50 default/100 max returned; response 2 MiB; database 64 MiB; active memory
64/128 MiB; one-second wait/hold, ten-second query; fixed 15 minutes,
8/64 inspections, 2-MiB context, two traversals; cumulative 128 attempts,
1000000 rows, 256-MiB source, 64-MiB output and 120 active seconds.

InspectionWork tests cover exact-inclusive and one-over cumulative boundaries,
reject negative/boolean/noninteger counters, and retain charged work after
failed/replayed/branched/restarted/both-traversal-labeled synthetic attempts.
The pure helper has no context registry or admission enforcement; future trusted
composition must actually share counters and precheck known work.

Dense 10000-match traversal needs at least 200 default-50 pages, exceeding
128 attempts. At 100 matches it needs at least 100 pages; repeated 16-MiB
validation would charge 1600 MiB, above the 256-MiB cumulative source cap.
These are arithmetic compatibility limits, not an executed 100-page benchmark.
No budget reset, refund, reduced H or weakened validation was introduced.

Quota encoding tests cover Unicode scalar-value key ordering, required lowercase
ASCII escapes/surrogate pairs, short control escapes, literal solidus, rejection
of floats/nonstring keys/unpaired surrogates/cycles, and exact decimal strings
above JavaScript's safe-integer boundary. Timestamp fixtures preserve absent/
1-/6-digit Grant fractions; zero-byte success and exact identity mismatch/
payload-field rejection use current pure validators.

The generic encoder materializes its result. It is not preparse envelope
admission, a bounded streaming encoder, field-aware decimal conversion or a
closed version-1.0 request/response validator. Error/request fragments are
fixtures only; no query or transport implementation is claimed.

## Mandatory acceptance disposition

| S0 acceptance item | Evidence and result |
| --- | --- |
| Complete mutation/shutdown inventory | Provided above and independently source-reviewed; no production path changed. |
| Recovery-free reader feasibility | Standard-library read-only synthetic connections and unbound validators worked without owner constructors. An established owner-managed production resource is not implemented/proven. |
| One-second capture and safe cleanup | **NOT established.** Current lifecycle validation alone exceeded one second; actual leases, scheduling and bounded Python/OS cleanup remain absent. |
| Journal semantic validation under approved bounds | Current original-schema validator exercised up to 10000 records/14904454 bytes; later corruption rejected. Semantic checks preserved; operational bounded implementation absent. |
| Memory/byte/row/cumulative accounting | Definitions and synthetic accounting checked; measured Journal Python peak exceeds 64 MiB. Complete native/concurrent/retained enforcement unproved. |
| SQLite resource/sidecar behavior | WAL/SHM/DELETE observations and narrow SQL cancellation measured; base file alone insufficient; arbitrary I/O/sidecar growth bounds unproved. |
| Cancellation/writer priority | SQL VM and one controlled ordering demonstrated only; actual owner-wide cancellation, shutdown and starvation prevention unproved. |
| Source/policy/budget compatibility | Pure exact definitions/fixtures checked; no actual registry, principal, audience, source or auth mechanism. |
| Unsupported capabilities and prerequisites | Explicitly listed; no operational query, cursor, live Result, payload, UI or transport implemented. |

The required NO-GO is therefore based on both concrete limit problems and
unestablished mandatory safety properties. It is not converted to GO by the
nine successful synthetic correctness checks.

## Independent review and findings

Two distinct agent execution instances contributed one isolated definition
module each; they cross-reviewed the other's module and independently reviewed
the root-authored harness and this report. No author is the sole approver of
their own material changes. Different Providers or Human signatures are not
implied.

| Reviewer / actual independent scope | Current outcome |
| --- | --- |
| /root/locate_architecture — Core concurrency, other author's budget module, root-owned harness/report | **APPROVE scoped S0 evidence/report; NO-GO to advance.** Complete report, final evidence, current harness and budget module reviewed. R1 containment and R2 interruption findings resolved; obsolete helper cleanup concern withdrawn after direct re-read. No required findings remain. Approval excludes this reviewer's own source module. |
| /root/archive_integrity — Journal/resource security, other author's source module, root-owned harness/report | **APPROVE scoped S0 evidence/report; NO-GO to advance.** Complete report, all three evidence artifacts, current harness and source module reviewed; reported measurements match the evidence. Medium input-bound/cleanup findings closed. No required findings remain. Approval excludes this reviewer's own budget module. |

Initial failed run receipts are retained. Review fixes stayed in the authorized
test file: pre-write containment/pinning, exact experiment-input bounds,
unconditional connection cleanup and specific interruption evidence.
No scope expansion, runtime hook, limit increase or architectural revision was
used to resolve a finding.

Both reviewers explicitly retained the concrete lifecycle hold-time and Journal
memory failures and the unproved cancellation, native-memory, owner-coordination
and operational guarantees. Their scoped approvals authorize no operational
admission or S1 work, imply no formal operational Quality Gate PASS, and do not
replace Human final review.

## Validation limits and final Human Control

Only scoped S0 tests ran. Full project tests/builds, operational CLI/Alpha,
runtime services, real data, network probes, UI validation and D6-E/B1 were
neither executed nor claimed passing. They are outside this authorization.
No formal operational Quality Gate PASS or Task closure is claimed.
The Phase A mechanical whitespace check remains exit 2 with exactly the five
Human-accepted exceptions; it is never reported as PASS.

Final read-only checks returned exit 0: Core HEAD is the documentation commit,
the branch is feature/control-center-s0-feasibility, the index is empty, no
tracked files differ and exactly the eight authorized S0 paths listed above
are untracked. Raw UTF-8 whitespace inspection of all eight S0 files found no
trailing whitespace, extra final blank lines or missing final newlines.
Synthetic temporary directories are empty. The four preserved technical/plan
files match their expected SHA-256 values in both working files and raw
committed blobs.

UI HEAD remains 0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67 and the parked
SCRUM-81 branch remains 61e817c1f7a2c3987710a73366b516d792402520. Its original
untracked ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md
is the only UI status entry. An initial incorrect relative UI path and then
Git's sandbox-user ownership guard each returned exit 1; the corrected absolute
path with command-scoped safe.directory returned exit 0 and the expected state.
No persistent Git configuration or UI file was changed.

**NO-GO to advance to S1/read-port admission under unchanged P07.** Human review
must disposition these measurements and authorize any further work. Options
include separately scoped investigation of semantic-equivalent bounded
validation/cancellation/allocation, or an explicit architecture-change proposal;
neither option is implemented or automatically selected here. Do not relax
limits or bypass validation to make the fixture pass.

The existing UI baseline and untracked readiness document, parked SCRUM-81
reference and separate D6-E/B1 workspace are preserved. No source/audience
registration, access grant, transport/authentication choice, S1–S8 or UI
development occurred.

**All S0 files remain unstaged and uncommitted. STOP AT HUMAN CONTROL.**
