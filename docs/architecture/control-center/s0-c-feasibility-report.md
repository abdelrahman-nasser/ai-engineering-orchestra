# ITRU S0-C complete capture and safety feasibility

Date: October 17, 2026. Authorization: isolated offline synthetic experiments only.
Disposition: **NO-GO for reader admission or S1-S8. STOP AT HUMAN CONTROL.**

Successful complete synthetic captures were observed below one second. Bounded
abort is not established: two deliberately uncooperative controls held exclusion
for **1.0563137 s** and **1.0660408 s**. Both eventually failed closed and cleaned
up; eventual cleanup does not satisfy P07. Native memory and maximum-shape full
query memory remain unverified. No production code or approved contract changed.

## 1. Baseline and artifact verification

The canonical [index](README.md), [Boundary Design v2](application-boundary-v2.md),
[investigation](boundary-investigation.md), [reconciliation addendum](reconciliation-addendum.md),
[Human decisions](human-decisions.md), [approved plan](integration-implementation-plan.md),
[S0 report](s0-feasibility-report.md), and [S0-R report](s0-r-feasibility-report.md)
remain authoritative. Historical approval wording in v2 is preserved; Human
approval of P01-P10 is recorded separately in the decisions document.

| Check | Initial and final state |
| --- | --- |
| Repository | `D:\Dev\ai-engineering-orchestra` |
| Branch | `feature/control-center-s0-feasibility` |
| HEAD | `19a321fc0876e73b9f83109f2a58528c9d54e331` |
| Index / tracked changes | Empty index; no tracked changes |
| Original artifacts | All eight S0 and eleven S0-R artifacts preserved byte-for-byte |
| v2 SHA-256 | `c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062` |
| Approved plan SHA-256 | `93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d` |
| New artifacts | Twelve S0-C files, untracked and unstaged, only in the three authorized paths |
| Scratch | Empty after experiment cleanup; no synthetic database or sidecar retained |

The complete nineteen-path initial byte counts and SHA-256 values are in
[baseline.json](../../../tests/fixtures/control_center/s0c/baseline.json).
[final-state.json](../../../tests/fixtures/control_center/s0c/final-state.json)
records individual final hashes, equality checks, canonical hashes, executed-source
hash checks, Git state and scratch verification. No prior evidence was rewritten.
The baseline manifest SHA-256 is
`da58f508dd64faca415df213b31cf9bbc9efd67e53c8bc14556d89392edd3915`.

Final static checks decoded all twelve new files as strict UTF-8, found no
trailing whitespace, missing final newline or extra blank EOF line in them,
and resolved all nineteen local report links. These checks did not stage files
or rewrite the five previously accepted formatting exceptions in the approved plan.

The separate UI repository remains at
`0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67`; parked SCRUM-81 branch
`ui/itru-062-contract-i18n-rtl` remains at
`61e817c1f7a2c3987710a73366b516d792402520`. Its existing untracked readiness
document remains the only UI status entry. No UI changes or operational-store access occurred.

New code is confined to [capture.py](../../../tests/experiments/control_center_s0c/capture.py),
[coordination.py](../../../tests/experiments/control_center_s0c/coordination.py),
[resources.py](../../../tests/experiments/control_center_s0c/resources.py),
[run_experiments.py](../../../tests/experiments/control_center_s0c/run_experiments.py),
[test_concurrency.py](../../../tests/experiments/control_center_s0c/test_concurrency.py)
and [test_resources.py](../../../tests/experiments/control_center_s0c/test_resources.py).
The other six files are this report, the baseline and final-state manifests,
two run receipts and the resource receipt. This is experimental code, not a new
Core reader, owner, public API, transport or application query implementation.

## 2. Execution provenance and retained failures

Both parent invocations used the installed Python executable, repository working
directory, no dependencies or network, and this command:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B tests/experiments/control_center_s0c/run_experiments.py
```

| Run | Actual result | Retained receipt / SHA-256 |
| --- | --- | --- |
| Initial | Parent exit 1; only concurrency child ran; 14 tests, two failure entries, no errors | [evidence-a6d0a4f5d35a4dbd9c0fae3690820671.json](../../../tests/fixtures/control_center/s0c/evidence-a6d0a4f5d35a4dbd9c0fae3690820671.json); `913bf787aec37ea5d7bafac278c817625a8ab51251811f191c0583647787d91d` |
| Corrected complete run | Parent exit 0; 21 serial children, all exit 0; 15.8963789 s parent wall time | [evidence-b3a5e1dd9e5e4e048435b86fa5cb57bd.json](../../../tests/fixtures/control_center/s0c/evidence-b3a5e1dd9e5e4e048435b86fa5cb57bd.json); `5d5a78177c9c6e3750eb2b48a52677ad22db85ab7f49d08a57bfa2d6ccc7870d` |
| Resource detail | Seven tests, zero failures/errors/skips; ten observations | [resource-results-83042869c2a3491fa930748b00b7317f.json](../../../tests/fixtures/control_center/s0c/resource-results-83042869c2a3491fa930748b00b7317f.json); `dbfae8bfad81d447cd883ff08e264342468b1e426dd68cfdd4f6272f9937e363` |

The initial pressure test exhausted its 0.25-second arrival window before the
required second batch of ten attempts; its writer's 0.8-second synchronization
gate then timed out during teardown. Both failure entries concern test 14.
Earlier thirteen scenarios completed; threads were joined. The receipt retains
both tracebacks. This is evidence of an inadequate finite harness synchronization
window under observed scheduling, not evidence that a later reader overtook the
writer. Windows wait rounding is a plausible contributor, not a measured timing
breakdown. The arrival window became 0.6 seconds; no P07 limit increased. The
corrected suite also includes a separately reviewed shutdown regression test.

The final 21 children comprise concurrency and resource suites, four untraced
timing jobs, two allocation jobs, one two-query job and twelve fault jobs. Each
child has a 60-second parent containment timeout. No containment timeout or forced
child-exit fallback occurred. Child command, working directory, elapsed time,
stdout/stderr and exit status are retained. Exit zero confirms that assertions
and expected counterexamples executed; it is **not** feasibility or Quality Gate PASS.

Environment: Python 3.12.10, SQLite 3.49.1, Windows 11 x64
`Windows-11-10.0.26300-SP0`. Phase and actual held-interval measurements use
`perf_counter_ns`; cooperative coordination deadlines use `monotonic`, whose
reported Windows resolution is approximately 15.625 ms. Their differing
resolution matters near a deadline. Independent measured holds above one second
remain failures even if a cooperative clock check would miss them.

## 3. Synthetic architecture and fixture scope

Setup explicitly creates new synthetic SQLite files using existing lifecycle DDL,
opens a passive read-only/query-only connection, builds a deterministic full Task
graph and pins file identity **before query admission**. Operational constructors
and provisioning entry points are replaced with failure guards in workers.
Only experiment-created resources in `tests/fixtures/control_center/s0c/scratch/`
are opened. This does not open or acquire an operational owner.

Inside immediate admission, an experimental coordinator acquires one combined
lifetime/read-exclusion lease. Within it, capture checks the file envelope and
setup-pinned identity, begins a read transaction, validates the full current
store, loads and decodes ordered events, performs semantic replay and immutable
Task/Run construction, verifies complete Task/definition and graph coverage,
evaluates the unchanged Core scheduler, checks identity again, rolls back, and
closes the passive connection. Only then does it release exclusion and lease.
No mandatory capture work is moved outside this boundary.

After lease release but before admission release, it creates an allocation
projection of the full scheduler result and quota-encodes it. This is **not**
P04 `InspectRun`, a closed application DTO or `ReadRunJournal`. Actual current
continuation eligibility remains unassessed; historical validation still uses
existing Core semantics as permitted by H2. There is no execution authority.

Whole-store validation includes application/schema versions, `quick_check`, exact
schema and metadata, ordered event/index agreement, Core decoding and event
validation, followed by the unchanged S0-R indexed reducer's semantic checks.
Replay therefore still repeats event validation. This report does not attribute
separate SQLite, JSON, validator and reducer subcosts where no instrumentation exists.

| Shape | Tasks | Events | Dependencies | Encoded event metadata bytes | Scope |
| --- | ---: | ---: | ---: | ---: | --- |
| representative | 20 | 78 | 0 | 18,695 | Small multi-Task domain |
| long | 1 | 10,000 | 0 | 3,709,595 | Maximum event count in one history |
| alpha_max | 100 | 9,998 | 4,753 | 3,383,505 | Configured Alpha Task cap, dense acyclic graph |
| core_max | 1,000 | 3,998 | 10,000 | 960,513 | Existing Core graph maximum stress; exceeds Alpha's 100-Task cap |

The last two Tasks in every multi-Task fixture have running Runs, are disconnected
from the DAG, and consume both configured scheduling slots (`max_concurrency=2`).
They remain in the complete scheduler domain. The long history includes 3,333 Runs
and 3,332 historical continuations. Fixture hashes below identify exact inputs;
S0-C prefixes Run/Result identities with Task identity, so long-history bytes are
not identical to the earlier S0-R fixture.

| Shape | Canonical rows SHA-256 | Graph SHA-256 |
| --- | --- | --- |
| representative | `db5a1acd2d5904f88e9e90f76b66fc1016757c03370cafde727df4a0b00beaf1` | `4fee8c35c06c03fe2dd3373423588db37605eb22a6d8f96c6a261bf97bfc4c18` |
| long | `c238efe6269484e5a8384150da4105923a30b4764c27233c31bd930357e54671` | `c5eda390d7b5f1304ca23761f2fefcdef9ba1c9571b7a1bf64e6792f624dd000` |
| alpha_max | `6a6130f5e11680b7195740bdd295bab95a24ae267a0a44e09b318d09ede58e17` | `536a29c38ee7fa03299dbdbcc08f2af74d3ddd40cbd1f0b878271e262aa39271` |
| core_max | `24b4558418991299689da5b1b688bde4eff7335175bf74d6e5d4210c840e81cf` | `74609e6fd271c11587d9852014fdf002ed630508a84fa3c496245301d5803a23` |

These labels maximize selected dimensions, not the entire joint P07 envelope.
No fixture approaches 16 MiB metadata or an individual 1 MiB event; hostile shape,
escape and subject distributions remain untested. `core_max` changes no supported
Alpha configuration. Setup primes the OS cache; these are single observations,
not cold-disk, worst-case, repeated statistical or production-owner measurements.

## 4. Complete capture timing

Measured values below are **milliseconds**, rounded to four decimal places, from
the untraced timing jobs. Phase rows are grouped operation timings, not an invented
internal attribution. Checkpoints and harness overhead mean rows need not sum to
the held interval. Admission and wait precede hold; projection follows release.

| Operation | representative | long | alpha_max | core_max |
| --- | ---: | ---: | ---: | ---: |
| Admission | 0.0128 | 0.0126 | 0.0160 | 0.0137 |
| Coordination wait and combined lease/exclusion acquisition | 0.0269 | 0.0238 | 0.0341 | 0.0249 |
| Resource preflight | 4.5245 | 4.1298 | 4.4233 | 4.1957 |
| Read transaction BEGIN | 0.0143 | 0.0119 | 0.0155 | 0.0128 |
| Whole-store header/schema/metadata/SQL validation, ordered loading, decode/event validation | 3.0478 | 428.4683 | 408.0084 | 132.9356 |
| Indexed semantic replay and immutable Task/Run construction | 2.5001 | 332.8567 | 375.2355 | 110.4929 |
| Complete domain and graph verification | 0.0484 | 0.0235 | 31.4714 | 12.2364 |
| Unchanged Core scheduler evaluation | 0.7631 | 81.8332 | 96.6464 | 44.0443 |
| Final resource identity/envelope check | 5.3311 | 4.9386 | 5.3732 | 4.9784 |
| Rollback, inactive check and passive close | 0.0740 | 0.3420 | 0.3249 | 0.2076 |
| **Actual held interval, acquisition through release** | **16.3472** | **852.6486** | **921.5573** | **309.1511** |
| Request start through capture release, including admission/wait | 16.3796 | 852.6801 | 921.5972 | 309.1844 |
| Synthetic projection and quota encoding after release | 0.8666 | 83.0087 | 90.6982 | 71.0350 |
| Total synthetic query | 17.2772 | 935.7463 | 1,012.3552 | 380.2752 |

All four captures completed successfully and closed their passive handles before
lease release. Output sizes were 16,584 / 1,744,507 / 1,932,463 / 1,412,284 bytes,
respectively. Alpha total query time exceeds one second, but its measured hold
does not; P07's whole-query deadline remains ten seconds. Long and Alpha have
only about 147 ms and 78 ms of observed hold headroom. These results establish
successful synthetic examples, not reliable deadline enforcement for all inputs.

## 5. Python and native memory

Allocation jobs start a fresh `tracemalloc` after fixture construction and record
an explicit `(current, peak) = (0, 0)` baseline. Setup graph, fixture payloads,
already-established handles and some caches predate tracing; the trace cannot
account for their full active-query attribution. Tracing alters timing, so timing
and allocation runs are separate. All values below are bytes.

| Traced workload | Python peak | Current after queries | Outcome and coverage |
| --- | ---: | ---: | --- |
| representative | 310,692 | 86,409 | Complete capture and synthetic projection; hold 0.0547945 s |
| alpha_max | 9,040,243 | 435,135 | **Aborted during whole-store validation**, before replay, graph, scheduler or projection; hold 0.9932493 s |
| Two representative queries in one process | 583,663 shared peak | 150,395 | Both complete; holds 0.0983845 / 0.0944025 s |

The traced Alpha attempt returned `CaptureDeadlineExceeded`, no observation and
acknowledged cleanup. Its 9,040,243-byte peak measures an attempted prefix plus
cleanup, **not a complete maximum-query memory result**. Its sub-second QPC hold
and deadline exception reflect the cooperative clock's coarser resolution; this
is not evidence that a larger traced capture would fit either budget.

The concurrent job uses two distinct preestablished sources, connections and
coordinators with one shared admission object. A barrier retains both projections
and encoded buffers while admission records two queries (`s0/s1`, `p0/p1`). Both
threads join and final active admission is zero. This establishes overlap at
projection retention, not simultaneous worst-case lifecycle allocation peaks,
per-query native attribution or a 128 MiB maximum-data guarantee.

Windows `GetProcessMemoryInfo` provides these process-wide endpoint observations:

| Job | Working set before / after query / after cleanup | Private bytes before / after query / after cleanup | Lifetime peak working set |
| --- | --- | --- | ---: |
| representative allocation | 43,036,672 / 43,708,416 / 43,708,416 | 27,185,152 / 28,680,192 / 28,680,192 | 43,708,416 |
| Alpha allocation, aborted | 58,134,528 / 57,724,928 / 55,169,024 | 41,873,408 / 42,135,552 / 38,445,056 | 76,804,096 |
| Two representative queries | 43,347,968 / 44,097,536 / 43,360,256 | 27,582,464 / 28,065,792 / 26,951,680 | 44,900,352 |
| Long untraced | 51,097,600 / 79,724,544 / 71,430,144 | 34,676,736 / 64,229,376 / 55,701,504 | 87,408,640 |
| Alpha untraced | 56,770,560 / 81,289,216 / 70,434,816 | 42,475,520 / 66,600,960 / 54,886,400 | 90,382,336 |

Endpoint differences are not allocation peaks or exact released-byte accounting.
Lifetime peaks include interpreter, setup, retained fixtures, allocator and tracer
effects. Process RSS is not P07's per-query active-memory metric, and the 128 MiB
active-query budget is not a whole-process RSS limit.

Native SQLite status/cache allocation is explicitly **UNAVAILABLE**: a safe status
interface for the exact SQLite library backing this Python was not established.
No guessed or unrelated DLL was loaded. Native page caches, temporary VM buffers,
SQLite/OS mappings, filesystem I/O buffers and sidecar effects are not attributed
to queries. Thus neither 64 MiB/query nor 128 MiB/application is established.

Source-supported allocation causes remain: loaded decoded event dictionaries,
reducer maps/indexes and frozen snapshots coexist; scheduler output retains a full
snapshot; `asdict`, recursive tuple-to-list projection and quota encoding create
additional structures/buffers. SQL text becomes Python text before row byte checks,
and `quick_check`, schema and metadata use `fetchall`. The synthetic 2 MiB response
check occurs after projection/encoding allocation. These are not production-safe
preallocation guards or hostile-database bounds.

S0-C does not rerun a complete Journal query. S0-R's compact unique 10,000-record
validator Python peak was 20,578,294 bytes, versus canonical 77,611,152 bytes;
this remains component evidence, with no full Journal comparison/response/native
or two-query guarantee. Whole-current-snapshot semantics and exact identities,
sequence checks and conflicts remain required. Cumulative amplification is
unchanged: 100 pages at maximum match limit require at least 1,000,000 validation
row visits, and 100 full 16 MiB validations charge 1,600 MiB, beyond 256 MiB.
Default limit 50 requires at least 200 attempts, beyond 128. Explicit exhaustion
is legitimate; cached validation, refunds or silently resetting budgets are not.

## 6. Cancellation and cleanup

All twelve fault workers exited zero because expected failure/error classes and
cleanup assertions matched. Every fault returned `success=false`, no observation
and no usable lifecycle prefix. This does not make the two overrun controls safe.

| Controlled fault | Held seconds | Returned error | Disposition |
| --- | ---: | --- | --- |
| Decode function-entry cancellation gate | 0.0352730 | `CoordinationCancelled` | Controlled fail-closed cleanup observed |
| Replay inner-validation entry gate | 0.0415175 | `CoordinationCancelled` | Same; no arbitrary mid-reducer preemption proof |
| Scheduler inner-validation entry gate | 0.0416039 | `CoordinationCancelled` | Same; no arbitrary mid-scheduler preemption proof |
| Transaction phase cancellation | 0.0041668 | `CoordinationCancelled` | Transaction cleanup observed |
| Encoding cancellation after capture | 0.0166468 | `RuntimeError` | Capture complete; total 0.0471353 s; no projection published |
| 3 MiB synthetic allocation pressure | 0.0135639 | `ValueError` | Capture complete; 2 MiB response cap rejects oversized projection after allocation |
| Cleanup cancellation gate | 0.0441588 | `CoordinationCancelled` | Cleanup finishes before acknowledgement |
| Ownership loss | 0.0104031 | `OwnershipLost` | No observation; no new owner acquisition |
| Uncooperative decode, 1.05 s injected delay | **1.0563137** | `CaptureDeadlineExceeded` | **Blocking P07 hold failure** despite eventual cleanup |
| Uncooperative cleanup, 1.05 s injected delay | **1.0660408** | `CoordinationCancelled` | **Blocking P07 hold failure** despite eventual cleanup |
| Wrong setup-pinned expected identity | 0.0014174 | `ResourceIdentityChanged` | Explicit mismatch; no live path-swap proof |
| Deliberately preclosed connection | 0.0040716 | `ProgrammingError` | Already-closed handle; no reopen/fallback |

Decode/replay/scheduler gates set cancellation at the first selected inner Core
function entry, sleep 30 ms, then permit that synchronous call to return. Checks
detect cancellation afterwards. They exercise cleanup but cannot interrupt
arbitrary Python/native/OS calls in progress. The uncooperative delays are
deliberate counterexamples to the model's checkpoint-only hard-bound claim,
not measured naturally occurring Core stalls or proof those stalls are impossible.

Acknowledgement follows synchronous phase completion, rollback/inactive inspection,
successful passive close, and release of this query's lease/source/principal
permit. All fault results satisfy that observation. The preclosed-connection case
has `transaction_inactive_observed=false`, `connection_already_closed=true`;
the report does not substitute a transaction-property measurement that could not
be made. No receipt reports a handle closed beneath an active synchronous phase.
There is no internal detached worker in `capture`; these observations do not prove
arbitrary native I/O or production asynchronous work has stopped.

The concurrent measurement runner joins controlled workers before closing fixture
resources. Its untriggered failed-drain fallback writes blocking evidence where
possible and exits the owned child in a `finally` path before `ExitStack` could
close resources under a live worker. The parent reaps that child. That is outer
experiment containment, **not** safe in-process cancellation and not a proposed
production mechanism. No worker kill, failed drain or residual scratch occurred.

## 7. Writer priority and shutdown model

The corrected concurrency suite ran **15 tests, zero failures/errors/skips**.
It exercises atomic immediate admission (one/source, one/principal, two/global,
no pending query queue), simultaneous readers, queued-writer priority, coherent
paired revisions, reader/writer cancellation, ownership loss, closing barriers,
active-reader/writer drain, timeout, close failure and bound-input rejection.

In the explicit ordering case, two initial readers exit, the writer enters, then
all six later readers enter; mixed revisions and hold overruns are zero. Under
finite continuous arrival pressure, 21 attempts occurred over approximately
0.312 seconds within the 0.6-second window; later-reader overtaking is zero and
the writer enters during pressure. This is finite model evidence, not a fairness
proof under every scheduler or a claim that actual Core writers participate.

Shutdown marks closing before waiting, rejects waiting/new readers and writers,
and invokes its fake owner close callback only after zero active leases/writers.
An uncooperative-reader control times out with the handle deliberately left open,
then closes on a safe retry after real reader exit. Another 20 ms artificial hold
control actually lasts 61.8797 ms and reports overrun; the assertion passing means
the negative control was detected, not that its configured bound was satisfied.
Close failure remains sticky and is not reported as successfully closed.

Independent review found that an already-closed concurrent-shutdown return branch
could miss a timeout while reacquiring its lock. It now rechecks elapsed time.
Test 15 simulates a 0.2-second wait against a 0.1-second requested timeout and
requires explicit timeout, with one close call. This deterministic fake-clock
regression is not measured runtime shutdown latency.

The complete-capture runner's later `shutdown_after_capture` has a no-op owner
callback: actual passive SQLite close already happened inside capture. Its
reported zero coarse-clock elapsed time is not instantaneous real owner shutdown.
The separate coordination tests use controlled fake callbacks; resource tests
use actual synthetic SQLite handles. A production owner coordinating every real
mutation, recovery, ownership-loss and resource-close path remains unimplemented.
Short Python lock acquisition and arbitrary callbacks are not preemptible here.

## 8. SQLite resources, sidecars and containment

Seven resource tests produced ten observations in the linked resource receipt.
They use mode=ro/query_only connections to existing synthetic files, no query-side
provisioning, reconnect, recovery or explicit checkpoint/repair.

| Scenario | Measured observation | Limit of evidence |
| --- | --- | --- |
| SQL VM cancellation, DELETE / WAL | Progress-handler cancellation plus cleanup 20.1333 / 20.1444 ms; later writer succeeds | Interrupts controlled recursive SQL VM work, not all OS I/O or Python phases |
| Interrupted ROLLBACK | First interruption leaves transaction active; no acknowledgement then; handler is disabled and final rollback/close verifies inactive | Cleanup is mandatory; no general rollback/close interruption guarantee |
| DELETE writer lock | SELECT returns busy after **260.7386 ms**, with configured SQLite timeout 20 ms; cleanup 0.1093 ms | Busy timeout is not a hard elapsed-time limit |
| WAL writer active | Committed snapshot remains readable; SELECT 0.2271 ms; cleanup 0.0582 ms | Finite synthetic snapshot consistency only |
| DELETE sidecar | Base 8,192 bytes; active journal 4,616 bytes; read-only DML rejected | Logical sizes, not resident/native bounds |
| WAL sidecars | Base 4,096, WAL 12,392, SHM 32,768 bytes; pinned snapshot and read-only DML checks succeed | No proof of zero SHM bookkeeping or bounded future sidecar growth |
| Identity replacement | Only closed between-query synthetic fixture replaced; mismatch rejected | No adversarial live path-swap/native-handle pinning proof |
| File growth | Logical base extended to 67,108,865 bytes (64 MiB + 1); rejected before SQLite open | Allocated disk bytes unavailable; sidecar/native envelope unproved |
| Missing / closed connection | Missing file not created; preclosed handle fails; no new owner or reconnection | Permissions and arbitrary OS failure profiles unverified |
| Containment negatives | Actual non-scratch-parent rejection and mocked symlink rejection; source guards cover reparse ancestors and nonsingle-link files | No real reparse/hardlink attack trial or all-filesystem-races proof |

Root/parent identities and ownership markers constrain recursive cleanup to
experiment-created directories. Worker TEMP/TMP and scratch point inside the
authorized area. Source guards reject unsafe ancestors and nonsingle-link files.
No retained database, WAL, SHM, journal, temp log or live experimental worker is
part of the final state. Identity checks and logical-size observations do not
establish an interruptible physical I/O bound or an additional approved sidecar
policy. Choosing such a policy would require separate architecture review.

## 9. P07 comparison

| Approved requirement | S0-C evidence | Disposition |
| --- | --- | --- |
| Lifecycle hold <=1 second, including abort/cleanup/release | Four successful full synthetic timing captures below bound; two >1 s fault controls | **NO-GO: bounded failure release not established** |
| Coordination wait <=1 second; writer/shutdown priority | Input caps, cancellation/timeouts and finite priority scenarios observed | Model evidence only; hard OS/lock and production guarantee unverified |
| Whole query <=10 seconds | All actual query attempts below bound | Cooperative checks only; arbitrary in-call overrun unverified |
| Active memory <=64 MiB/query | Representative complete Python trace; Alpha trace aborts early; native unavailable | **Unverified** |
| Active memory <=128 MiB/application | Two representative queries admitted/retained simultaneously | **Unverified** for maximum shapes/native memory |
| One query/source/principal, two/application; no pending queue | Atomic admission and overlap observations | Observed in model; labels are synthetic, not authentication |
| Complete lifecycle validation / Task graph / scheduler | All mandatory phases inside lease for successful captures, disconnected occupied Runs included | Observed shapes only; not a production-equivalence or malformed-input coverage suite |
| 10,000 events / 16 MiB total / 1 MiB individual event | Count/total checks and existing Core event semantics; selected count-max fixture | Native/text preallocation, byte-max shapes and hostile header/schema bounds unverified |
| Base database <=64 MiB before wide validation | Size+identity preflight; 64 MiB+1 rejection before connect in resource test | Controlled logical-base checks only; physical/sidecar bounds unverified |
| Response <=2 MiB with bounded working allocations | Four successful encoded examples; 3 MiB pressure rejected | Postallocation cap only; production preallocation bound unverified |
| Whole current Journal and cumulative charged work | Prior S0-R component evidence retained; no skipped current records proposed | Full application Journal query/accounting unimplemented; amplification unresolved |
| No prefix after validation/budget/cancel error | Every controlled fault returns no observation | Observed controlled cases only |
| Shutdown drains before owner resources close | Finite fake owner model and actual synchronous passive close tests | General bounded abort and real owner integration **unverified** |
| Context/reference authority, retention and metadata entitlement | No application context, credentials or P04/P05 query built | Not implemented or claimed; H2 current eligibility remains unassessed |

No P01-P10 or P07 limit, retention rule, identity, persistence, consistency or
authority contract changed. A valid maximum-size dataset need not complete if it
exhausts an approved work budget, but failure must still release safely within
the required bounds. The present counterexamples prevent admission.

## 10. Independent reviews and findings

Two distinct agents authored disjoint experimental modules. The root authored
capture/runner/report. Each reviewer excludes approval of their own modules:

| Reviewer | Authorship excluded | Independent review scope / disposition |
| --- | --- | --- |
| `/root/archive_integrity` - Core concurrency/lifecycle safety | `resources.py`, `test_resources.py` | **APPROVE within scoped evidence/report review; no unresolved required finding.** Read complete report, other-author coordination/tests, root capture/runner and actual timing/allocation/concurrent/fault receipts. Independently verified manifest, nineteen preserved artifacts, six executed sources, canonical hashes, Core Git state and empty scratch. UI fields checked against root's evidence, without opening that repository. Retains NO-GO; no formal Quality Gate PASS. |
| `/root/locate_architecture` - Journal/resources/containment | `coordination.py`, `test_concurrency.py` | **APPROVE within scoped evidence/report review; no required textual finding.** Read complete report, other-author resources/tests, root capture/runner and actual memory/SQLite/sidecar receipts. Independently verified nineteen preserved artifacts and six executed sources. Optional containment-test precision incorporated: mocked symlink versus source-reviewed reparse/hardlink guards. Retains NO-GO; no formal Quality Gate PASS. |

Both inspected actual source, fixtures and receipts and confirmed the six
executed-source hashes. Core review also independently verified all nineteen
preserved artifacts against the baseline. Neither substitutes component authorship
for independent approval. Their pre-execution approval was limited to bounded
synthetic execution; actual-results review retains NO-GO.

| Finding | Correction / retained limitation |
| --- | --- |
| Resource identity pin and initial check could fall outside guaranteed query cleanup | Pin identity in explicit setup; require it and perform query checks under cleanup protection |
| Failed worker join could allow runner cleanup beneath live work | Bounded joins, blocking evidence and unconditional owned-child exit fallback before fixture closers; fallback untriggered and not in-process safety proof |
| Concurrent shutdown already-closed return could ignore elapsed timeout | Recheck elapsed time and add deterministic regression test 15 |
| Cleanup acknowledgement needed actual evidence | Inspect rollback state or explicitly record preclosed handle, successful close, released lease/permits and synchronous phase completion |
| Fault receipt needed assertions, not just logged errors | Require expected error classes, no observation, cleanup and explicit blocking hold classification |
| Initial continuous-pressure synchronization failure | Retain failed receipt; widen only finite arrival window; rerun complete job grid |
| Ambiguous memory/timing attribution | Explicitly mark partial traced Alpha, process-wide peaks, projection-only overlap, busy-timeout overshoot, coarse deadline clock and unavailable native attribution |

All code changes from review precede the final executed-source hashes. This report
is evidence consolidation, not formal Quality Gate PASS. Production tests, actual
owner integration, operational dataset suitability and UI/runtime readiness were
outside authorization and were not run or inferred.

## 11. Remaining risks and architecture boundaries

The leading source-supported limitation is cooperative checking around work that
can block inside a Core function, SQLite call, filesystem call or cleanup. Current
prototypes cannot guarantee all such calls stop, rollback and release inside one
second. The injected counterexamples establish this model limitation directly;
they do not provide a frequency estimate for real stalls.

Other unresolved risks are complete maximal metadata/graph/subject distributions,
native and temporary allocation attribution, preallocation response guards,
schema/metadata hostile materialization, real file-handle identity pinning, storage
growth races, retained contexts and all real writer/shutdown paths. The setup
helper closes its writer on setup failure but has no separately tested failure
in the narrow interval after passive open and before returning its fixed row
factory assignment; do not generalize these experiments to arbitrary setup failure.

Adding bounded checkpoints/chunks while preserving exact validation and immutable
results is a plausible compatible direction, **not a proven optimization**.
Treating timeouts as success, releasing exclusion while work continues, closing
under active work, skipping full validation, cached-validation shortcuts or
changing source identities/authority would violate the approved contract.
Increasing limits, weakening guarantees, selecting process topology as a workaround
or introducing a new numerical sidecar policy needs explicit architecture review
and Human approval. No such decision was made here.

## 12. Recommendation and smallest corrective evidence scope

**Retain NO-GO.** Successful whole synthetic capture is now demonstrated for the
listed cache-primed shapes, improving on the S0-R component-only evidence. The
approved admission decision still requires bounded failure cleanup and complete
resource accounting, which these experiments do not establish.

The smallest next experiment, only if separately authorized, should retain the
current fixtures and receipts and focus first on the two failed hold controls:
design an isolated cancellable/chunked reducer/scheduler adapter and explicit
cleanup reserve, preserving all semantic checks and full-domain evaluation; inject
cancellation within chunks and near deadline boundaries; verify actual release,
transaction inactivity and no publication with a high-resolution common deadline.
Keep production modules unchanged. It must also state which SQLite/filesystem
operations remain noninterruptible; unsupported profiles cannot be admitted by
assuming a busy timeout or worker kill proves safety. No exact reserve or chunk
size is established by this run.

Then obtain safe native observability for the exact installed SQLite or another
independently reviewed complete attribution method, and complete maximum-query
memory measurements without bypassing the unchanged capture deadline. Measure
all active live setup resources, replay/scheduler/projection overlap, native
temporary buffers and cleanup, with two demanding queries and bounded response
generation. If these cannot be measured/enforced within the existing profile,
retain NO-GO and bring the unresolved assumption to Human Control.

Future evidence must also include repeated supported-shape and byte-max trials,
defined cold/warm and contention profiles, high-resolution deadline-edge cases,
actual supported runtime SQL interruption/rollback/close behavior, adversarial
metadata/identity/size cases, and an independently reviewed inventory covering
every real mutation/recovery/ownership-loss/shutdown path before production
integration. A full Journal application query still needs its own cancellation,
native memory and cumulative accounting evidence. No S1 work follows automatically.

## 13. Human decisions and final control

Human review is required to accept this evidence and retained failures, decide
whether to authorize the narrowly scoped further S0 experiment, or separately
request architecture reconsideration for any guarantee that cannot be enforced.
No increase in P07, new Task ID, transport choice or production approach is implied.
Any future archival/staging/commit requires separate Human direction; all S0,
S0-R and S0-C artifacts remain untracked and unstaged.

The authorized S0-C experiment and report are complete; feasibility is **NO-GO**.
No formal Quality Gate PASS or production readiness is claimed. Human approval
remains required. **STOP AT HUMAN CONTROL.**
