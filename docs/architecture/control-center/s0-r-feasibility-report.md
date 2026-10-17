# ITRU S0-R corrective synthetic feasibility report

Date: October 17, 2026.

**S0 recommendation: NO-GO for reader admission or S1-S8.** The experiments
demonstrate a lifecycle component timing improvement and a substantial Python
peak reduction for the unique-subject Journal fixture. They do not establish
owner lifetime, complete capture, native memory bounds, cancellation, writer
priority, shutdown drain or a complete query under P07. No production changes
or architecture amendment were made.

## 1. Authority, initial and final state

Authority is the Human instruction `ITRU - S0-R Corrective Synthetic Feasibility
Experiment`, supplied in attachment
`a3b4530b-c019-4c83-ab54-632d1f48dab2/Pasted text.txt`. It authorizes only new
isolated experiments, synthetic execution, evidence and this report.

Repository: D:/Dev/ai-engineering-orchestra.
Branch: feature/control-center-s0-feasibility.
HEAD: **19a321fc0876e73b9f83109f2a58528c9d54e331**.
Both initial and post-experiment checks found an empty index and no tracked
differences. No branch, commit, configuration, Task ID or production file changed.

The exact initial paths, byte sizes and full SHA-256 values of all eight original
untracked artifacts are recorded in
[baseline.json](../../../tests/fixtures/control_center/s0r/baseline.json).
The corresponding paths/hashes and successful post-experiment comparisons are in
[final-state.json](../../../tests/fixtures/control_center/s0r/final-state.json).
All eight are byte-preserved, including the original S0 report and failed-run
receipts. This report supplements their interpretation rather than rewriting them.

Canonical v2 working-file SHA-256 remains
`c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062`;
approved plan remains
`93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d`.
P01-P10 and P07 are unchanged. Human H2 still permits historical replay checks
internally and forbids current eligibility assessment/exposure by either query.

New files are limited to five Python files in
tests/experiments/control_center_s0r/, five JSON artifacts in
tests/fixtures/control_center/s0r/, and this report. They remain untracked and
unstaged. Scratch was designated as tests/fixtures/control_center/s0r/scratch/;
it is empty after the completed parent and all children exited.

The existing UI baseline, original untracked readiness document and parked
SCRUM-81 reference are preserved. D6-E/B1 and operational stores were not accessed.
Final UI HEAD is 0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67; parked
ui/itru-062-contract-i18n-rtl is 61e817c1f7a2c3987710a73366b516d792402520.
The sole UI status entry remains the original untracked
ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md.

## 2. Experiment artifacts and provenance

All experiment/fixture links below are relative to this document.

| Artifact | Purpose |
| --- | --- |
| [common.py](../../../tests/experiments/control_center_s0r/common.py) | Synthetic original-schema fixtures, canonical row hashing, guarded scratch ownership and exclusive receipts. |
| [indexed_replay.py](../../../tests/experiments/control_center_s0r/indexed_replay.py) | Private indexed lifecycle experiment, canonical immutable outputs and optional timing partitions. |
| [compact_journal.py](../../../tests/experiments/control_center_s0r/compact_journal.py) | Whole-current-snapshot compact exact-state experiment; summary output, no application query. |
| [test_semantics.py](../../../tests/experiments/control_center_s0r/test_semantics.py) | Differential prefix, conflict, header, immutable-output and limit cases. |
| [run_experiments.py](../../../tests/experiments/control_center_s0r/run_experiments.py) | Serial bounded children, separate timing/allocation workers and receipt capture. |
| [semantic corpus](../../../tests/fixtures/control_center/s0r/semantic-corpus-cb09d063fdb04c538c06abf2e818f0de.json) | Exact synthetic event/document cases and explicit below-SQL row-overlay qualification. |
| [semantic results](../../../tests/fixtures/control_center/s0r/semantic-results-37017e192052479792b9716ae5486bd7.json) | Five checks, 705 outcome entries, no failures/errors/skips. |
| [full measurement receipt](../../../tests/fixtures/control_center/s0r/evidence-d2a605369ba94e7595af0dd1f5dc76a3.json) | All 21 exact child commands, working directories, exit codes, timing, memory, allocation sites, source hashes and limitations. |

Full measurement receipt SHA-256:
`4cd7f2d2447cbc8d93f8b8e23d45631b2812c3033cdb598f4b0827db8d36dcc2`.
Semantic corpus SHA-256:
`0fd268aef4ead794c70096ffb652642946cae86dd7c5cfb2e6be15b8422f89ec`.
The measurement receipt records the exact hashes of all five executed Python
files; independent reviewers compared them with the files actually reviewed.

Fixture hashes below are SHA-256 over each exact canonical UTF-8 row followed
by LF, in sequence order. They identify logical synthetic rows, not SQLite file
authenticity or authority. Corresponding canonical/prototype/timing/allocation
workers have identical hashes and byte totals.

| Fixture | Shape | Canonical bytes | SHA-256 |
| --- | --- | --- | --- |
| Lifecycle / replay | 10,000 events; one Task; 3,333 Runs, 3,332 historical continuations | 3509615 | 2ca8c785d69002b73378869c1c92eb704afef739ed14f8d218e4ad7d5864329b |
| Journal unique | 10,000 Entry records, subjects and Runs | 14904454 | 02cd8a3ef8b215568ac7d49b58a9a1015ca61ce3dc22923bc8c6cf0eb603a0a4 |
| Journal pairs | 1,000 records; 500 Entry/Result pairs | 1514013 | 2ca03a311d90e1191f34ae9c5b37e340a7994a9075308458bc086f51baf7cfb4 |
| Journal Unicode | 500 Entries; long issuer IDs and escaped Unicode provenance | 3295952 | dfb8f46e43696924891e87cf3ff7bdd86cc22ae8fc236e661a39f3faa67f4a63 |

The first two reproduce the prior S0 row/event shapes and canonical byte totals.
Pairs and Unicode add distributions; they are not exhaustive maximum-16-MiB
tests. Original schemas, fingerprints and canonical validation are reused.

## 3. Execution and measurement conditions

Installed tools only: Python **3.12.10**, MSC v.1943, x64; SQLite **3.49.1**;
Windows-11-10.0.26300-SP0. Timing uses perf_counter_ns / QueryPerformanceCounter.
Working directory for every child: D:/Dev/ai-engineering-orchestra.

The one parent command was:

~~~powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B tests/experiments/control_center_s0r/run_experiments.py
~~~

Parent exit **0**, elapsed **144.6141678 seconds**, **21 serial children, all exit
0**, no timeout. One child ran test_semantics.py. Twenty fixed workers covered
canonical/prototype x timing/allocation for lifecycle/history/10000,
replay/history/10000, journal/unique/10000, journal/pairs/1000 and
journal/unicode/500. The exact expanded argv arrays are retained in the receipt.
Worker form:

~~~text
<same Python> -B <absolute run_experiments.py> --worker <area> <variant> <shape> <count> <timing|allocation>
~~~

Each child has a 90-second experiment guard. subprocess.run kills/reaps a timed
out child; this would be NO-GO evidence, not safe in-process cancellation proof.
The parent stops on a failed job and retains its receipt. No experiment attempt
failed in this S0-R run. Original S0 failed attempts remain preserved separately.

All generated databases/temporary files were new, marked directories inside
S0-R scratch. TEMP/TMP point there for children. Paths reject reparse/symlink
ancestors; database creators require scratch containment; teardown rechecks
resolved containment, pinned identities, marker and contained objects before
removing only the owned directory. These are cooperative experiment safeguards,
not a claim of adversarial atomic filesystem pinning. No prior user data was
reused or deleted. No package install, network, inference or operational process
was involved. Measurement children reject operational Store construction and
provisioning through test mocks.

### Timing

Each timing worker records a first validation on its fresh passive connection,
a second on the same connection, then a separately instrumented pass. Fixture
creation primes OS caches: first pass does not mean cold disk. There is no
controlled OS-cache flush or statistical latency distribution. Pure replay has
predecoded input and no reader; its generic receipt condition names do not imply
that a read connection exists.

Target timing excludes explicit BEGIN, result summarization/release, ROLLBACK,
connection close, fixture deletion and startup. Timed reads can include SQLite
read-lock acquisition and I/O. Those boundaries are component measurements,
not the approved owner-lifetime exclusion interval.

Instrumented regions include grouped SQL/header work, loading, top-level JSON
decode/canonical checks, semantic validation and replay. Lifecycle header time
also includes Python schema sorting/comparison; canonical Journal SQL wrappers
measure execute/fetch; compact header includes schema-resource/comparison work.
These are not interchangeable exclusive pure-SQL cost buckets. Nested Admission
JSON work lies within record semantic validation, outside the top-level decode
bucket. Canonical immutable construction is fused with replay and cannot be
separately attributed by this instrumentation; it is explicitly unavailable.

Difference from a separate warm pass is recorded as an overhead observation,
including negative differences. This includes run variation; it is not an
isolated instrumentation-overhead calibration.

### Allocation

Allocation workers are fresh, separate children, without a preceding target
result. Inherited PYTHONTRACEMALLOC is removed by the parent. All ten workers
recorded startup tracing **false**, inherited setting null, and explicit new
tracing baseline current/peak **0/0**. Setup/imports/fixtures occur before trace
start; target-triggered lazy imports remain included. BEGIN precedes tracing.

Target current/peak are captured immediately after target return, BEFORE taking
the allocation-site snapshot or computing summaries/statistics. The target peak
therefore excludes that later reporting machinery. Snapshot sites describe live
allocations at return, not historical sites at peak. Compact internal maps have
already been freed by return; their peak sites cannot be inferred from that live
snapshot. Peak-minus-current is not total allocation traffic.

Post-release current includes later site/statistics/summary allocations and is
not a clean target-only retained-memory value. Process counters are separate
whole-child measurements, with allocator, fixture, tracing and reporting effects.
They are not query-attributable native peaks. Native-only peak measurement is
**unavailable**. Raw peaks must not be converted to native bounds by subtracting
RSS samples. Pure replay trace excludes its already-decoded input; the full
lifecycle experiment includes event loading/decoding allocations.

## 4. Corrected lifecycle and replay results

Seconds below are untraced target times. Python peaks come from separate first
target allocation children and include target-triggered allocations.

| Component | Canonical first / second seconds | Indexed first / second seconds | Canonical / indexed Python peak bytes |
| --- | --- | --- | --- |
| Full validation pipeline, 10,000 events | 1.9019340 / 2.2736179 | **0.7833017 / 0.7834584** | 29872495 / **30348915** |
| Pure replay, same predecoded history | 1.4214623 / 1.5488711 | **0.3291362 / 0.3377286** | 2367604 / **2844420** |

Measured: indexed replay reduces elapsed component work on this fixture.
Measured: its full-validation peak is **476420 bytes higher**, not lower.
Both full-validation live-at-return measurements are approximately 24.93 MB.
The exact peak difference cannot be assigned to one builder/index category from
the at-return sites alone.

The full indexed pipeline is a test-only transcription of original header,
load, decode and validate-before-replay ordering. Production _verify and
reconstruct remain unchanged. The indexed pure reducer calls canonical event
validation, maintains permanent exact global Run/Result sets and per-Task state
counts, mutates only private construction state, and freezes original immutable
TaskSnapshot/RunSnapshot types once after success.
Index lookups have expected/amortized behavior; identifier hashing/byte lengths,
canonical validation and final construction still cost work. This is not a hard
linear worst-case runtime guarantee.

Actual grouped instrumented full-pipeline regions, seconds:

| Region | Canonical instrumented pass | Indexed instrumented pass |
| --- | --- | --- |
| Header checks including quick_check/schema/metadata | 0.0068501 | 0.0028126 |
| Event fetchall | 0.0183360 | 0.0071338 |
| Decode + canonical roundtrip | 0.1919647 | 0.1573223 |
| Row semantic validation | 0.2921049 | 0.2447850 |
| Replay including construction | **2.0447589** | **0.3815073** |
| Outer instrumented target total | 2.5591673 | 0.7976557 |

The indexed replay partition inside that pass separately records event validation
0.2440753 s, reduction 0.1294799 s, final freeze **0.0022947 s**, and residual
loop/instrumentation 0.0053775 s. Canonical freeze time remains unavailable.
These figures are from a separate instrumented run and must not be subtracted
from the first uninstrumented pass as a causal decomposition of that pass.

This evidence supports the root-cause hypothesis that repeated historical
copying/searching is material for the long-history fixture. It does not isolate
the savings of each individual index or eliminate repeated canonical validation.
Full graph/scheduler evaluation was not included.

First-pass explicit BEGIN / ROLLBACK were 0.0080 / 0.0344 ms canonical and
0.0070 / 0.0802 ms indexed. Result release was 4.1050 / 7.3204 ms respectively.
Combined reader-plus-fixture-writer close at the end of each timing worker was
0.8179 / 1.0981 ms. These narrow fixture observations are not ownership, wait,
lease or shutdown-drain guarantees; production established resources have a
different lifetime.

## 5. Corrected Journal results

| Fixture | Canonical first / second seconds | Compact first / second seconds | Canonical / compact Python peak bytes |
| --- | --- | --- | --- |
| Unique / 10000 | 3.3324644 / 4.4095611 | 3.8705477 / 4.5599367 | **77611152 / 20578294** |
| Pairs / 1000 | 0.2988927 / 0.2608694 | 0.3270355 / 0.2897928 | **8200842 / 8190523** |
| Unicode / 500 | 0.2087724 / 0.1476394 | 0.2150581 / 0.1883419 | **9370586 / 8205465** |

Measured: the unique-subject Python peak falls substantially. Pairs have almost
no peak reduction at this size; Unicode has a more modest reduction. Compact is
slower on both uninstrumented passes for these fixtures. No universal speed or
memory improvement is claimed.

The corrected canonical unique peak exceeds 64 MiB (67108864 bytes) by
**10502288 bytes** under the explicit controlled target tracing boundary. This
resolves the earlier missing-initial-trace attribution question for this new
experiment; it does not retrospectively certify the older tracing session.

Unique live traced bytes at return are canonical **77512370**, compact
**1348418**. The compact maps are query-local validation state and are freed
before return; it returns statistics/digest, whereas canonical returns all
records/maps. It is not a drop-in replacement or implemented page projection.
Selection, buffering, exact application subject matching, comparison and
encoding would add work and memory. No usable page is emitted by this prototype.

Canonical unique live-site evidence includes:

| Allocation line | Live bytes at return |
| --- | --- |
| stdlib json/decoder.py:354 | 32745560 |
| sqlite_agent_execution_journal_store.py:256 row iteration | 15315278 |
| agent_execution_journal.py:115 JSON pair dictionary insertion | 12161080 |
| agent_execution_journal.py:111 JSON pair dictionary creation | 5760064 |

These lines substantiate substantial retained decoded/row representation cost;
they do not partition every peak allocation or count shared objects twice.
Source confirms facts/records alias JournalRecord objects, subjects shallowly
retain decoded subtrees, and Run-map Contract values alias those subtrees.

The compact validator keeps exact canonical subject/Contract strings and event
flags, not approximate identity hashes. SHA-256 is only an experiment output
comparison. It retains original schema/fingerprint/metadata checks, quick_check,
canonical nested validation, JSON-to-column equality, sequence/time integrity,
physical-subject equality, duplicate facts, Run/Contract consistency and prior
Entry requirement. The existing Core Contract-only Run collision rule is
preserved; later application Binding/ledger checks are not silently added here.

It adds a length/count preflight followed by one full semantic row pass inside
the same explicit transaction. SQL CAST/native allocations remain unbounded by
this experiment. Distinct JournalBudgetLimit outcomes for approved row/byte
overflow are component admission behavior, not canonical semantic-parity claims.

Unique instrumented canonical regions: SQL header calls 0.0454762 s, row loading
0.0747820 s, top-level decoding/canonicality 0.6639863 s, record semantic
validation **3.1432213 s**, other bookkeeping/instrumentation 0.3673791 s.
Compact groups: header 0.0218888 s, length precheck 0.0217687 s, row fetch
0.0872599 s, decode/semantics **3.8981090 s**, bookkeeping **0.7690314 s**.
Nested Admission work remains inside semantic validation. Compact bookkeeping
includes exact compact encodings and row digest; canonical comparison-summary
digest is outside its timed target. Their full component contracts differ.

First unique BEGIN / ROLLBACK were canonical 0.0088 / 0.0533 ms and compact
0.0067 / 0.0267 ms. Result release was 16.6690 / 0.0006 ms. Combined reader and
fixture-writer close at timing-worker end was 47.2915 / 50.7171 ms, including
synthetic writer teardown; this is not a production per-query close requirement.
Base/WAL/SHM were 4096 / 21300432 / 65536 bytes for the unique fixture.

Tracing inflates unique target duration to 26.0923220 s canonical and 27.0492885 s
compact. These are instrumentation runs, not untraced ten-second deadline tests.
Whole-process traced-worker lifetime working-set peaks were 389820416 and
78893056 bytes, including tracer/reporting effects. They are not native-query
peaks or P07 process RSS limits. No native-memory or sidecar bound is proved.

## 6. Differential semantics and negative results

The suite completed **5 checks, 0 failures, 0 errors, 0 skips**, with **705**
recorded outcome entries:

- 670 lifecycle prefix comparisons, accepted output equality or exact rejection
  class/message equality, across valid/invalid histories.
- One 10000-event successful pure-reducer full-output parity and immutable-output
  check. Full pipeline workers compare fixture identities and record matching
  Task/Run/revision summaries; they do not perform an additional full Store-output
  differential assertion.
- 23 adversarial Journal row-stream cases: six accepted and seventeen rejected,
  matching canonical acceptance/rejection and accepted row digest/counts.
- Three real original-schema SQLite shapes with matching row digest/counts.
- Five real SQL-header/metadata failure cases with matching rejections.
- Three component/constraint limit outcomes, explicitly distinct from semantic
  equivalence claims.

Lifecycle cases include interleaved Tasks, global Run/Result collisions, revisions,
registration/continuation, pending/running transitions, recovery, cancellation,
interrupted/ambiguous history, completion prerequisites and terminal restrictions.
Every prefix in the small corpus is compared; the 10000-event case compares full
output, not every one of its 10001 prefixes. Permanent indexes preserve prior
identities; latest-only unfinished handling relies on invariants established
from the empty state and all preceding validated transitions.

Journal cases include unique Entries, pairs, complete same-Run multiple physical
subjects, different ToolBindings with identical Run/Contract (accepted by Core),
true differing Result outcomes, duplicate facts, subject/Contract conflicts,
sequence gaps, backwards recording time, malformed/noncanonical/raw-type data,
ledger generation, long/Unicode data and semantic corruption near the end.
Duplicate SQL facts are also rejected by the original schema constraint.

Some malformed streams cannot exist through original STRICT/UNIQUE constraints.
They are explicitly labeled adversarial row overlays below those constraints,
delegating actual header checks to a real synthetic database; they are not claims
of physically constructing those corrupt original-schema databases. Budget
preflight cases exercise record-size, total-row and aggregate-byte overflow
before the semantic row materialization pass.

The full lifecycle load/decode adapter preserves validate-all-documents before
reduction ordering. Tested cases and source review support equivalence; this is
not a proof for all possible inputs, error combinations or future Core changes.
No partial state/records are returned on tested failures.

## 7. P07 comparison and unresolved risks

| Requirement | Evidence / disposition |
| --- | --- |
| Lifecycle hold <=1 s | Indexed validation component observed ~0.783 s. Complete graph pinning/evaluation, owner lease/exclusion and bounded abort/drain remain absent. **NOT established.** |
| Active memory <=64 MiB/query | Compact unique Python peak 20578294 B, below numerical threshold; canonical 77611152 B exceeds it. Native/response/comparison/concurrent allocation is unproved. **NOT established.** |
| Application active memory <=128 MiB | No simultaneous two-query enforcement/measurement. **NOT established.** |
| Whole query <=10 s | Untraced Journal component below10 s for measured shapes. No complete query or enforceable deadline. **NOT established.** |
| Whole current Journal | Both passes pinned to same read transaction; original complete semantic checks retained in tested corpus. No frozen-prefix/cache shortcut. |
| Per-request rows/bytes | All measured shapes within10000/16MiB; compact preflight checks individual1MiB/total16MiB/rows10000. Physical/native bounded reads are not proved. |
| Cumulative work | No runtime inspection/context accounting. Extra length pass, row visits, decoding, exact encoding and digest work remain real costs requiring charging. No refund/reset/cached-validation assumption. |
| Memory retention | Compact validation maps disappear before return; later bounded pages/inspection/context storage are not implemented or measured. |
| Cancellation and cleanup | No phase-aware interruption, writer-priority owner, lease, closing barrier or shutdown race experiment implemented. Safe bounded release remains unproved. |
| Database/sidecar envelope | Original schemas/DELETE lifecycle/WAL Journal; observed sizes only. No hard I/O, mmap, page-cache or WAL-growth proof. |

The length preflight visits every current row in addition to the semantic pass;
it does not make those costs disappear. Conservative future charging must
account for the additional work. Current per-snapshot cardinality is distinct
from total row visits. The pre-existing dense-traversal cumulative budget
limitations remain: repeated full-current validation can exhaust approved work
before a traversal finishes. No limit or validation guarantee was changed.

P07 can return an explicit fail-closed deadline/budget error; it does not promise
all maximum-size datasets succeed. Safe abort and cleanup must still fit its
bounds. Faster successful components cannot establish those properties.

## 8. Independent review and findings

Two distinct agent executions authored one isolated prototype each. They
cross-reviewed the other author's prototype and independently inspected the
root-authored harness, actual corpus and receipts. No author is sole approver
of their own implementation. Different Providers or Human signatures are not
implied.

| Reviewer / independent actual scope | Outcome |
| --- | --- |
| /root/archive_integrity - Core performance/correctness: indexed replay, root harness, prefix corpus, timing/allocation attribution and actual receipts | **APPROVE scoped S0-R evidence/report; NO-GO to advance.** Complete actual report and receipts reviewed. All required findings resolved. Own compact Journal code excluded. |
| /root/locate_architecture - Journal/resource safety: compact validator, root harness, exact identity/conflict corpus, resource attribution and actual receipts | **APPROVE scoped S0-R evidence/report; NO-GO to advance.** Complete actual report, code, corpus and receipts reviewed; original-byte preservation independently verified. All required findings resolved. Own indexed replay code excluded. |

Both reviewed the complete report draft identified by SHA-256
`d64b9dcd9d9449322c5ac4c85c68673796869eef834e3c1a5b2ca44eb8e7bd5c`.
Subsequent report edits record these actual outcomes and final read-only state
checks; experimental code and receipts remain identical to the executed versions.
No unresolved required review finding remains. Scoped approval is not runtime
proof, universal equivalence, a formal operational Gate PASS or Human acceptance.

Required findings resolved before execution:

- M1: restrict temporary parent/database paths to designated S0-R scratch.
- M2/R-J1: add genuine differing outcomes, accepted multiple physical subjects
  for the same Run/Contract, different ToolBindings, interleaved Tasks/global
  Result collisions, and real header/metadata negatives.
- R-J2: guard exact record text type before encoding, matching canonical rejection.

Reviewer-required reporting qualifications are retained: current-at-return and
peak have different meanings; live sites do not identify all transient peak
causes; post-release reporting allocations contaminate that later field; grouped
header regions differ; first-connection is not cold disk; compact summary and
canonical full-output contracts differ; no P07/operational proof follows.

## 9. Validation disposition and next Human Control

Scoped experiments succeeded on the tested corpus. Full project tests/builds,
operational Alpha/CLI, UI tests, real data, diagnostics and network checks were
not run and are not claimed passing. No formal operational Quality Gate PASS,
Task closure, production optimization approval or universal equivalence is claimed.

One read-only PowerShell summary extraction emitted nonterminating null-array
errors while mixing timing and allocation records (process exit0); that affected
extraction was discarded and corrected with allocation-only filtering, exit0.
Raw experiment receipts and all experiment exit statuses were unaffected.

Final scoped raw UTF-8 formatting inspection of all eleven new S0-R files found
no trailing whitespace, extra final blank lines or missing final newlines.
All ten relative document links resolve. The nineteen untracked paths comprise
the eight preserved originals plus eleven authorized new files; tracked/index
differences remain empty. Executed-source hashes and protected document hashes
were rechecked without rerunning experiments.

Proposed next action: retain the NO-GO and review this evidence. A separately
authorized corrective iteration could study complete supported-graph capture
cost and bounded cancellation/cleanup using isolated models, and extend native
allocation/shape evidence for compact validation including selection/encoding.
Production extraction/sharing of validation would need its own explicit scope,
compatibility regressions and independent review. Neither course is started here.

Human decisions required:

1. Accept or revise the tested-corpus equivalence and component findings.
2. Decide whether to authorize another precisely scoped synthetic iteration for
   remaining resource/concurrency questions. Existing evidence does not authorize
   an actual owner, read session or production optimization.
3. Keep P01-P10/P07 unchanged unless separately authorizing an architecture-change
   proposal. No raised limit, reduced validation, alternate snapshot or changed
   storage policy is recommended as an automatic workaround.
4. Separately disposition unstaged S0/S0-R artifacts; no staging/commit is
   authorized by this report. S1-S8 still require separate authorization.

**NO-GO for reader admission and S1-S8. All S0/S0-R artifacts remain untracked
and unstaged. STOP AT HUMAN CONTROL.**
