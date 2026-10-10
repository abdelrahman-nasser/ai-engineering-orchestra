# AIO-058 containment experiment findings

## Current containment evidence and adoption disposition — 2026-10-10

The Human explicitly authorizes persisting the successful revised experiment
and four fresh post-experiment adoption reviews. The final Human-reported
native run is 56/56 static PASS and 3600/3600 SAFE, with zero failures, skips,
unexecuted attempts, violations, infrastructure failures or unauthorized data
requests/returned bytes. I11's actual opaque reparse guard and all three revised
I14 orderings PASS. EXP-058-1 and EXP-058-2 are CLOSED by this reported native
confirmation. Full supplied observations are appended chronologically below.
Fresh Windows/Security/Invocation-TOCTOU/Architect adoption reviews all APPROVE,
each BLOCKER 0/HIGH 0. EXPERIMENT ADOPTION: APPROVE for the approved bounded
candidate. Production implementation remains NOT AUTHORIZED.

Evidence provenance: the Human manually executed the full revised elevated
experiment in bounded Administrator PowerShell; the normal Codex/IDE process
remained non-elevated. Codex records the supplied report without rerunning it.
No independent runtime reproduction, new run timestamp/root/OS identity or
run-source checksum is claimed. Atomic snapshot and historical link provenance
remain unproven and unclaimed. Only findings.md and Task review.md may be
updated in this evidence/review phase. No experiment/source change, production
code, migration 0004, first production effect, protected target, discovery,
staging or commit is authorized.

## Historical remediation disposition before the final Human run

The Human authorizes the bounded I14 Phase-1 design amendment on 2026-10-10.
Its new current-open exclusion plan replaces the rejected coexistence/drift
model; fresh four-scope review precedes harness changes. Revised static plan
is 56 attempts (three independent I14 records), races unchanged at 3600.
No new elevated run or Administrator command is authorized. I11's corrected
fixture/oracle remains required and native confirmation is pending. The failed
first run and prior STOP checkpoints below are preserved historical evidence;
they are not adoption PASS. See the newest amendment checkpoint at the end.

## Historical implementation checkpoint before the first full run

The experiment harness is implemented in the five authorized artifacts only.
This is static preparation, not runtime containment evidence or adoption approval.
The locked 18 cases remain exactly 54 static attempts plus 3600 race attempts.
The elevated matrix has NOT EXECUTED. No production code, package exports,
Execution Entry, migration 0004, production Tool invocation or first-effect
resource was created, modified or read. No staging, commit or push occurred.
Canonical Task artifacts remain read-only in this implementation phase.

The three Python artifacts now contain the native prototype and fixture owner,
the deterministic race harness, and the one fixed test-module entrypoint.
The two other authorized artifacts are Markdown, not additional Python files.
AST parsing applies to exactly the three Python artifacts. No additional
experiment source, package initializer, cache, script or validation file was
created in the checkout.

## Prerequisite chronology

1. The original unelevated probe used CPython 3.12.10, 64-bit, at the exact
   C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe.
   Windows reported major 10, minor 0, build 26300. Native volume information
   reported fixed local NTFS, serial 2459328365. File symlink creation returned
   WinError 1314, errno 22, required privilege not held. Directory symlink
   creation was not reached. The probe stopped with exit code 2.
2. The Human subsequently reports an independent Administrator PowerShell
   result: FILE_SYMLINK True, DIR_SYMLINK True, PASS. Codex did not repeat or
   independently execute that elevated prerequisite.
3. The symlink environment prerequisite is therefore resolved for the planned
   bounded Human-started elevated test process. This establishes no other
   fixture/native support; missing junction, short-name, custom-tag, virtual
   volume or native flag support will fail visibly during the eventual run.
4. The earlier runner preparation stopped correctly on absent executable
   bodies and issued no elevated command. The current separate authorization
   implements those bodies. Static readiness is distinct from native support
   and successful experiment results.

Production ITRU must require neither Administrator rights nor Developer Mode
nor SeCreateSymbolicLinkPrivilege. Elevation is hostile fixture enablement only.
Codex did not elevate, launch UAC, adjust tokens, assign privileges, change ACLs,
change security policy or enable Developer Mode.

## Historical disposable root record

The earlier probe created and cleaned exactly:
C:\Users\Abdelrahman\AppData\Local\Temp\aio-058-containment-759dc60c2f784df69147e1e8fa6fcd60.

Known paths only were removed, without recursion, directory enumeration or
link-target traversal. Its absence was independently checked. Created/reaped
experiment workers: 0/0. No new workspace, hostile fixture, child or matrix
attempt was created or executed in the current static implementation phase.

## Native strategy and fixture implementation

The reader uses one pinned trusted C: drive anchor and exact handle-relative
NtCreateFile filesystem components. The fixed drive-anchor bootstrap resolves
the trusted DOS device map; every subsequent filesystem component uses
OBJ_DONT_REPARSE and FILE_OPEN_REPARSE_POINT, without OBJ_CASE_INSENSITIVE.
It has no ordinary pathname-open, shell, subprocess, alternate-library or
alternate-resolution fallback. Opened-object checks use native handle metadata,
exact long path/name, root volume/file identity, disk/regular type, no reparse
or device attributes, link count one and bounded size. Pins survive all IO.

All hostile fixture recipes are implemented: real file/directory symlinks,
junction query-back, second disposable NTFS mount, the exact custom GUID tag
0x00000042 with AIOX payload and query-back, actual hard links, distinct case
and Unicode files, explicit PLAINL~1.BIN alias, write/delete sharing conflicts,
preexisting writable mapping, fault predicates and lexical/read boundaries.

The mount recipe creates a fresh 64 MiB VHD inside the recorded workspace.
Native CreateVirtualDisk/AttachVirtualDisk retain its identity and attachment
without assigning a drive letter. GetVirtualDiskPhysicalPath derives the exact
owned virtual-disk number; the mapping and pinned image ID are rechecked before
one fixed C:\Windows\System32\diskpart.exe child initializes/formats only that
disk and assigns the exact owned mount directory. There is no disk/volume
enumeration, guessed focus, noerr, shell wrapper or policy change. Native mount
verification proves distinct local NTFS identity before creating its synthetic
sentinel. Cleanup removes the mount, detaches the owned image, closes handles
and deletes only known owned paths. All child output is directed to an owned
log, checked against 64 KiB; its stdin is an exact owned empty file and its
working directory is evidence/. No NUL/device stdin or repository working
directory is used by that child. Output is not copied into canonical evidence.

This fixture helper is separate from the reader and implements no reader
fallback. The control recipe is based on
[CreateVirtualDisk](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-createvirtualdisk),
[AttachVirtualDisk](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-attachvirtualdisk),
[GetVirtualDiskPhysicalPath](https://learn.microsoft.com/en-us/windows/win32/api/virtdisk/nf-virtdisk-getvirtualdiskphysicalpath)
and [DiskPart](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/diskpart).
Its actual fixture support remains unexecuted; documentation is not proof.

## Accounting and result oracles

Each static slot is individually classified PASS or FAIL. No SKIP path exists.
Negative slots require the intended closed predicate; unrelated API/ABI/query
errors cannot satisfy them. Six metadata faults supplement real queries and
record fault-hit evidence. The delay slot models a native call over five
seconds and requires support rejection, rather than manufacturing a slow PASS.

The race loop is nine variants, four exact cuts and 100 repetitions each.
Owned non-daemon threads use events, not timing guesses. A cut holds the reader
until a real mutation or precise share/access denial is recorded. Missing cuts,
unsupported flags and unknown errors are INFRASTRUCTURE_FAILURE, not SAFE.
Every actor is joined before pins close. The outside sentinel and ancestry
stay pinned; identity checks occur before every content request, including EOF.
A rare unsupported pending native result is drained while buffers remain live;
unverified completion aborts the matrix with buffers retained through process
teardown. It cannot produce a SAFE/PASS result or continue the matrix.

The reader instruments opens, per-handle metadata queries, native calls/time,
reader-owned retained handles, requested/actual bytes and data requests.
Maximums are 16 opens, 12 metadata queries per handle, 253 native calls,
48 reader-owned retained handles, 17 requests, 65537 requested/actual bytes and
65536 output bytes. The exact boundary asserts 16 chunks plus one EOF probe;
empty asserts one probe and zero returned physical bytes. Short/failed reads
discard partial content; byte fixtures preserve NUL, invalid UTF-8, BOM and
newlines as immutable bytes.

There is no hard wall-clock or cancellation guarantee. Native completion can
stall; observation overruns fail support. Link count one proves neither
historical path provenance nor immutable topology. Sharing/metadata checks do
not establish an atomic snapshot against a preexisting writable mapping.
I14 performs the actual known mapping mutation after closing its source handle;
if metadata misses that drift and the reader accepts it, I14 is a real FAIL.
No hook notification or artificial timestamp update is added to force PASS.
Hostile same-user/admin or kernel-code isolation is outside the threat model.

The eventual output contains 54 static rows, 36 race buckets, up to eight race
failure details and one AIO058_SUMMARY. Actual totals, unexecuted counts,
per-case security outcomes, maxima, unauthorized data/bytes, child/thread
created/reaped counts, native handles remaining and root created/cleaned records
remain visible. No fixture bytes or arbitrary target paths are logged.
Any fixture prerequisite failure stops with actual unexecuted counts.

## Static validation and review

Static AST, exact imports, matrix counts, executable body presence, owned-worker
joins and exact-path cleanup are reviewed without source execution. An independent
read-only static reviewer approved the three code bodies with BLOCKER 0 and
HIGH 0 after identified interface, fixture, ownership and oracle defects were
corrected. This is implementation readiness review only, not native adoption
or a final canonical Task Quality Gate. Final exact-file readback and whitespace
checks are recorded below.

Runtime accounting for the current authorization remains:

| Matrix | Planned | Executed | PASS / SAFE | FAIL / VIOLATION | SKIP / infrastructure failure | Unexecuted |
| --- | --- | --- | --- | --- | --- | --- |
| Static | 54 | 0 | 0 | 0 | 0 | 54 |
| Race | 3600 | 0 | 0 | 0 | 0 | 3600 |

EXPERIMENT ADOPTION: PENDING EXECUTION.
Production readiness: NOT ASSESSED. Formal final Gates, fresh post-experiment
Windows/Security/TOCTOU adoption reviews and Human production approval remain
pending. No claim of 54 PASS, 3600 SAFE, successful cleanup in this unexecuted
matrix, exactly-once invocation or Task closure is made.

## Historical final static preflight before the first full run

PASS: exact three-file AST parsing and in-memory compilation; no source imported
or executed. PASS: five exact artifact readbacks and trailing-whitespace checks.
PASS: 54 unique static slots with the exact locked distribution; 18-case union;
nine variants times four cuts times 100 repetitions equals 3600 races. PASS:
reader, fixture, test, race, shared API and cleanup body presence inspection.
Direct dependencies are standard library, the two exact own modules, explicit
System32 native DLLs and the one fixed owned-volume formatter child only.

PASS: independent final static review of all five artifacts, BLOCKER 0, HIGH 0.
PASS: fixed Human launcher Python AST and PowerShell parser checks; the latter
confirmed exactly one command. Neither launcher nor matrix was executed. Exact
SourceFileLoader paths and process-local namespace modules pin all three own
imports; no checkout-wide import lookup, test/directory discovery, network,
persistent environment or package configuration change is needed.

PASS: exact-five-path git diff --check; these files remain untracked, so the
literal artifact whitespace check additionally covers their complete contents.
Cached diff is empty. HEAD remains
a0a6930d89da947f6e033682500ec0f4539d5fed. No staging or commit. Only the five
experiment artifacts were written in this implementation phase.

HARNESS STATIC READINESS: APPROVE FOR HUMAN MANUAL ELEVATED RUN.
Runtime support/adoption: STILL NOT EXECUTED. This checkpoint does not close
the canonical Task or authorize production implementation.

## First full elevated experiment, Human report recorded 2026-10-09

The Human reports that the complete first elevated matrix executed and correctly
FAILED. Codex did not execute or independently reproduce it. This is the first
full-run evidence, appended after the historical preparation checkpoints.

| Observation | First full run |
| --- | --- |
| Static total / PASS / FAIL / SKIP | 54 / 52 / 2 / 0 |
| Race total / SAFE / VIOLATION / infrastructure failure | 3600 / 3600 / 0 / 0 |
| Unauthorized data requests / unauthorized bytes | 0 / 0 |
| Owned children created / reaped | 3601 / 3601 |
| Temporary roots created / cleaned | 1 / 1 |
| COMPLETE SUCCESS | false |
| ATOMIC CONTENT SNAPSHOT PROVEN | false |
| HISTORICAL LINK PROVENANCE PROVEN | false |

All 54 static and all 3600 race attempts executed; none was skipped. Both
static failures remain failures. Owned children were fully reaped and the owned
root fully cleaned. A runtime nonce path, timestamp or new OS/build metadata
was not supplied with this report and is not invented here. The earlier probe's
specific root and host observations must not be attributed to this full run.

| Finding | Case / slot | Actual reason | Failure |
| --- | --- | --- | --- |
| EXP-058-1 | I11 / opaque_guid_tag | native_status_c00000ba_winerror_5 | unrelated native failure cannot satisfy expected rejection |
| EXP-058-2 | I14 / writable_mapping | native_status_c0000043_winerror_32 | mapping cut unreachable |

The opaque fixture was successfully created and queried in prerequisites. Its
attempt still failed to demonstrate the intended containment check. The I14
early sharing conflict demonstrated neither the required cut nor its mutation.
EXPERIMENT ADOPTION: CHANGES REQUIRED. The 3600 SAFE results are historical
evidence for the first revision only; they cannot be carried forward as final
adoption evidence after changing the experiment implementation.

## EXP-058-1 remediation: opaque GUID reparse

Root cause is fixture topology/component placement, not an accepted containment
outcome. The old opaque-reparse fixture was a directory requested as the final
file component. The locked NtCreateFile FILE_NON_DIRECTORY_FILE option rejected
that type with STATUS_FILE_IS_A_DIRECTORY before reparse verification.

The fixture is now an owned zero-length file at the exact same slot/path. Its
non-Microsoft tag 0x00000042, GUID 05805858-0058-4058-8058-005800580058 and AIOX
payload are unchanged, including exact FSCTL_SET_REPARSE_POINT/query-back.
The file is enrolled in the existing known-path cleanup ledger as a file.
Reader access, sharing, disposition, handle-relative traversal and open options
are unchanged; no alternate open strategy is introduced.

The attempt must record a final-component reparse_security_check event. Only
two explicit paths satisfy the tightened opaque predicate: documented
STATUS_REPARSE_POINT_ENCOUNTERED from OBJ_DONT_REPARSE with the locked relative
open flags; or actual opened-handle metadata containing the reparse attribute,
exact custom tag and non-directory type, followed by containment_rejected.
Both require rejection, zero data requests and no injected fault. Arbitrary
native failures, STATUS_FILE_IS_A_DIRECTORY, and unrelated containment reasons
cannot satisfy this slot. The event is diagnostic evidence of the actual guard,
not an injected rejection or an additional canonical attempt.

Static control-flow reachability is repaired: final-file type matches the
fixture and both native-guard/metadata paths are checked before any data call.
Native security check reached / explicit outcome: NOT YET RERUN OR PROVEN.
EXP-058-1 disposition: CODE REMEDIATED, RUNTIME CONFIRMATION PENDING.
Primary contracts: [NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
and [OBJECT_ATTRIBUTES](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes).

## EXP-058-2 investigation: mapping and locked sharing conflict

The exact locked I14 obligation is a writable mapping of mapped.bin established
before reader acquisition, originating write handle closed, mapping retained,
and actual mutation at before_first_content_read. The current mutation replaces
4096 mapped A bytes with 4096 B bytes and flushes the view. Only a reached cut,
performed mutation and genuine resource_changed rejection can satisfy its
strict oracle. An early WinError 32 remains FAIL.

The source uses Python r+b, which CPython FileIO maps to _wopen with O_RDWR,
O_BINARY and O_NOINHERIT. It is a read/write source; the fixture does not
explicitly select a Windows sharing mask and the first-run report does not
capture that mask. No exact observed mask is invented. ACCESS_WRITE maps to
PAGE_READWRITE and FILE_MAP_WRITE, without copy-on-write. The duplicate preserves
the source access. The reader independently requests FILE_READ_DATA |
FILE_READ_ATTRIBUTES | SYNCHRONIZE (0x00100081), SHARE_READ (0x00000001), FILE_OPEN,
FILE_NON_DIRECTORY_FILE, FILE_OPEN_REPARSE_POINT and synchronous nonalert IO.
[CPython FileIO mode/open](https://github.com/python/cpython/blob/v3.12.10/Modules/_io/fileio.c#L328)
and [Microsoft _wopen](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/open-wopen?view=msvc-170).

There are two distinct problems:

1. CPython 3.12.10 Windows mmap duplicates the originating writer handle with
   DUPLICATE_SAME_ACCESS and retains that duplicate until mmap.close(). Closing
   source therefore leaves an ordinary conflicting writer open. The observed
   first-run rejection is consistent with this fixture defect and cannot
   isolate section-only behavior. The closed original handle is not proof that
   all writer handles closed. [CPython 3.12.10 source](https://github.com/python/cpython/blob/v3.12.10/Modules/mmapmodule.c#L1381).
2. Microsoft documents that absence of FILE_SHARE_WRITE conflicts with an
   existing mapping having write access. The locked reader requests read/data
   and metadata rights with SHARE_READ=1, excluding write/delete sharing.
   Applying the common Windows sharing contract to this component-relative
   NtCreateFile profile is an architectural inference from the cited sources,
   not a new native experiment result. A native mapped-view fixture can close
   its file and section handles while keeping the view, but that does not remove
   the documented writable-view condition. [CreateFileW sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
   [NtCreateFile sharing](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile),
   [mapping lifetime](https://learn.microsoft.com/en-us/windows/win32/memory/closing-a-file-mapping-object),
   [writable views after handle closure](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-mmdoesfilehaveuserwritablereferences).

A direct native-view rewrite is therefore not presented as a remedy or proof
of reachability. Adding FILE_SHARE_WRITE would change ordinary-writer exclusion
and I13, a material design change. Moving mapping creation after reader open
does not preserve I14 and cannot create PAGE_READWRITE from the reader's current
read-only access. Copy-on-write would not mutate the underlying file. None is
implemented. No kernel API, timestamp update, reader hook notification, forced
rejection or relaxed oracle is introduced.

The existing historical I14 fixture is retained solely as the unresolved locked
obligation. Its diagnostics now preserve mapping establishment, originating
handle closure, cut reached, mutation attempted/performed, genuine rejection
observed and mapping cleanup even on failure. They award no additional attempt
or PASS. They do not claim that the CPython duplicate is closed independently.
Reader flags and the strict resource_changed predicate remain unchanged.

WRITABLE MAPPING CUT REACHABLE UNDER LOCKED PROFILE: NOT ESTABLISHED; documented
sharing conflicts with the required lifecycle. INTENDED MUTATION EXERCISED:
NO in the first run, and no new run performed. SECURITY OUTCOME OBSERVED: NO
for the required mutation. PHASE-1 CONTAINMENT DESIGN REVISION REQUIRED: YES.
EXP-058-2 disposition: BLOCKER. A Human design decision and independent native
review must reconcile I14's required cut with the sharing profile before rerun.

## Architectural interpretation and current validation boundary

Atomic snapshot interpretation is A: the locked context section 7 explicitly
accepts that sharing/metadata do not establish an atomic historical content
snapshot; success identifies bytes from the contained opened object. Atomic
snapshot is NOT required and remains NOT proven. This does not waive the
separate sentence requiring known writable-map drift rejection or the I14
cut/mutation obligation. Windows mapped writes may leave timestamps unchanged,
and FlushViewOfFile does not flush metadata. Even with redesigned sharing,
size/write/change comparison cannot be promoted to an unconditional rejection
guarantee for same-size mapped mutation. [Mapped-write/coherence limitations](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-createfilemappingw),
[FlushViewOfFile](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-flushviewoffile).

Historical link provenance is an accepted limitation: it is NOT required and
NOT proven. Pre/post link-count checks establish neither historic path
provenance nor immutable link topology. Both false summary fields remain false.

The final revised experiment must still execute all 18 cases, 54 static
attempts and 3600 races in one fresh coherent full run. This remediation does
not remove, merge, skip or weaken a slot. No native fixture or matrix was
executed by Codex; no second full run was started. No production code, migration
0004, future first-effect resource, canonical Task edit, staging or commit.
Only the five existing authorized artifact paths are in scope; race_harness.py
requires no change.

Static reachability preflight cannot be a full PASS while I14 is unresolved.
AST/count/whitespace checks and independent remediation review are recorded in
the next checkpoint. Complete native support/adoption and final canonical
Quality Gates are not passed. Human Phase-1 design approval is required before
dependent work; production approval remains separately pending.

## Remediation static checkpoint, 2026-10-09

PASS: exact three-file AST parsing and in-memory compilation with the fixed
Python 3.12 interpreter, -I -B, and a fixed stdin static-analysis body. No own
source was imported or executed; no native setup or matrix attempt occurred.
PASS: 54 unique static slots and exact locked distribution; I11 and I14 slot,
path and expectation unchanged; 18-case union; 9 x 4 x 100 = 3600 races.
PASS: I11 corrected final-file control flow and strict actual-guard predicate;
the native outcome remains unexecuted. PASS: unchanged I14 resource_changed
oracle, required cut/mutation assertions and finally-guarded mapping cleanup.
PASS: owned-thread creation/join/reaping, owned formatter wait/kill/reaping and
known-path reverse root cleanup inspection; no new runtime cleanup claim.

FAIL / BLOCKED: the mandatory I14 mapping-cut reachability preflight cannot be
established under the locked sharing profile. Overall rerun-readiness preflight
does not pass. This is not reported as a passed, skipped or waived obligation.

Independent read-only remediation reviewer: APPROVE for code/documentation and
the STOP disposition, new BLOCKER 0, HIGH 0. Existing EXP-058-2 design BLOCKER 1
remains. This review is neither native adoption approval nor second-run readiness.
Formal final canonical Quality Gates and Human production acceptance remain
pending; complete native validation is not executed and cannot be claimed PASS.

Exact code revision hashes (SHA-256):

| Artifact | Hash |
| --- | --- |
| windows_containment_probe.py | 512c022534e35d0b4b9d4de06ccffc069fd37fc863f07804340d9a6c6ac82c70 |
| race_harness.py | 48a976fa2fe0002b840a25f95b0f79317041e74416c1c314957ed4e4888f9f43 |
| test_aio_058_windows_containment_experiment.py | dfeb8e461012b30239c250cb47f45d8bd1cdbef1ee1fdf77c329c34bcd1ec87f |

PASS: all five exact artifact readbacks, trailing-whitespace and final-newline
checks. PASS: exact-five-path git diff --check. All five remain untracked, so
the complete literal-content whitespace check supplements Git's tracked diff.
Cached diff is empty; HEAD is a0a6930d89da947f6e033682500ec0f4539d5fed.
Only README.md, findings.md, windows_containment_probe.py and the exact test
module changed during this remediation; race_harness.py was inspected unchanged.
No staging or commit. No Administrator command was prepared or run.

PHASE-1 CONTAINMENT DESIGN REVISION REQUIRED: YES.
READY FOR SECOND FULL ELEVATED RUN: NO.
STOP before any further elevated run or production implementation.

## Human-authorized bounded I14 design amendment — 2026-10-10

The Human reopens Phase 1 for EXP-058-2 only. The old mapping/reader coexistence
and mutation-detection model is explicitly REJECTED and superseded by ordinary
Windows current-open write/mapping mutual exclusion. FILE_SHARE_WRITE remains
forbidden. Existing incompatible write or write-capable mapping state must
block reader acquisition before content; reader-first acquisition must block
later incompatible writer/mapping setup while its same target handle lives
through content, EOF and final metadata. Read-only reader access cannot itself
supply the write rights for PAGE_READWRITE mapping creation.

The exact new plan is in canonical context.md section 8. One I14 case has three
separate auditable reader attempts: mapping_first (live writable view after
writer/section handle closure), section_first (writable section retained with
writer closed and no live view), and reader_first (verified reader denies exact
later writer-open; readonly-handle writable mapping separately access-denied;
bounded read and before/after writer controls). Section-first is needed because
MapViewOfFile can consume a preexisting section without a new file write-open.
The correct static total is 56 rather than forcing the old 54; I14(1) -> I14(3).
Case IDs remain 18 and races remain 3600; all other slots are unchanged. Controls
and calibration are separately reported inside their ordering record and add
no extra reader attempt or worker.

The guarantee is bounded current-open exclusion in the supported ordinary local
NTFS access/share profile. No atomic/historical byte immutability, privileged
kernel/hostile-admin isolation, immutable/historical link topology or hard time
bound is claimed. Atomic snapshot REQUIRED/CLAIMED: NO/NO. Historical link
provenance REQUIRED/PROVEN: NO/NO. Detected drift still rejects; timestamps do
not guarantee every mapped mutation is detected. Link count one remains a
current topology restriction. All false summary claim fields remain false.

The documented mapping/sharing contract is a source-based candidate inference;
the complete new run must verify every native ordering. Unexpected acceptance,
unrelated error, absent cut/live state or cleanup failure fails support. An old
WinError32 row is not reused as new proof. I11 must be rerun on its corrected
explicit reparse guard. All first-run counts/errors/cleanup stay unchanged above.

Four fresh read-only design scopes are required: Windows Containment, Security,
Invocation/TOCTOU and Architect, all APPROVE with zero BLOCKER/HIGH before
experiment code remediation. No elevated/native execution occurs during this
amendment. Production adoption is NOT APPROVED. Only the four exact Task files
and five existing experiment artifacts are in scope; no production or migration
0004, package/init/cache/extra file, real resource, staging or commit.

### Four-scope design convergence before harness changes

| Scope | Fresh read-only reviewer | Verdict | BLOCKER | HIGH |
| --- | --- | --- | --- | --- |
| Windows Containment | /root/amend_windows | APPROVE | 0 | 0 |
| Security | /root/amend_security | APPROVE | 0 | 0 |
| Invocation / TOCTOU | /root/amend_invocation | APPROVE | 0 | 0 |
| Architect | /root/amend_architect | APPROVE | 0 | 0 |

All four approvals were returned before any amended Python harness edits.
EXP-058-2: RESOLVED AT DESIGN LEVEL, not native proof. New BLOCKER/HIGH 0/0.
The three-slot plan resolves the invalid old observation cut; it preserves the
exact share profile and tests each incompatible ordering directly. Section
reuse, view lifetime after visible handle closure, exact failure attribution,
positive controls and uninterrupted reader protection are explicit obligations.
No broader Entry/Store/public-contract/future-version change is required.
Native compatibility, I11 confirmation and full revised adoption evidence remain
pending. A later Human authorization must execute all 56 static and 3600 race
attempts on one coherent final revision; no old result is carried forward.

### Final amended harness static checkpoint — 2026-10-10

Only after the four approvals, the exact three existing experiment Python
sources were remediated. Native CreateFileMappingW/MapViewOfFile/UnmapViewOfFile
fixture controls replace incidental Python mmap handle behavior. I14 has three
independent records, each making exactly one authoritative reader attempt:
mapping_first, section_first and reader_first. The first two calibrate actual
writable view/section state before reader acquisition; the third uses exact
before/after writer-open controls, attributed live-reader sharing rejection,
separate readonly-handle mapping denial and one uninterrupted bounded read.
Strict I11 final-file opaque reparse setup/guard is preserved.

Fresh independent read-only harness implementation review by
/root/amend_harness_review: APPROVE, BLOCKER 0, HIGH 0. No source import,
execution or native fixture was used by the reviewer or root static checks.

Root fixed CPython 3.12 -I -B stdin checks PASS:

- AST parse and in-memory compile of exactly the three approved sources.
- Closed AST constant evaluation: 56 unique static case/slot pairs; exact
  distribution with I14=3; 18 containment case IDs; nine race variants times
  four cuts times 100 = 3600; revised total 3656.
- Strict I11 and all I14 setup/oracle/control paths; exact native access/share
  profiles; same live reader handle through data, EOF and post-read metadata.
- Fixture-control API accounting kept separate from bounded reader counters;
  writable calibration restores the known byte; handle/view releases remain
  owned and verified, with balanced view counters required for success.
- Owned non-daemon worker join and formatter child kill/wait paths precede
  pinned-root release; exact known-path cleanup and nine-artifact whitespace.
- Task accounting: unchanged 128 scenario IDs and 24 E01-E24 predecessor
  mappings. An initial static counting expression also counted traceability
  rows; correction to the exact scenario/traceability sections passed. It did
  not execute source or alter any scenario/mapping.

| Source | SHA-256 of statically reviewed revision |
| --- | --- |
| windows_containment_probe.py | a0e2af8cc8c920062c3099e01edf431c5d6e1a890e873811eb0ad6928b888815 |
| race_harness.py | 83cca3fdadddf561240514070c52654b343ef31545dddc195136e210d8510e3d |
| test_aio_058_windows_containment_experiment.py | 95bb9075a7553bccdd5100a5349ea42b8a80e4d29fb5366e28353c27ce132c6e |

Current amended revision runtime evidence, separate from the preserved first
failed full Human experiment above:

| Evidence | Planned | Executed | PASS/SAFE | FAIL/VIOLATION | SKIP/Infrastructure failure | Unexecuted |
| --- | --- | --- | --- | --- | --- | --- |
| Static | 56 | 0 | 0 | 0 | 0 | 56 |
| Race | 3600 | 0 | 0 | 0 | 0 | 3600 |

All three new I14 records and remediated I11 native confirmation are NOT
EXECUTED. No native handles/views, experiment root, child or worker were
created during this amendment. Zero current runtime counts are not containment
proof. No old PASS/SAFE result is reused for this revision.

The bounded design amendment and authorized static harness preparation are
complete, with no required amendment review/static check failed or skipped.
Native compatibility remains a required future gate: 56/56 static PASS,
3600/3600 SAFE, zero violations/unauthorized data/bytes, every I11/I14 oracle
PASS and complete owned handles/views/workers/roots cleanup on one coherent
revision. Adoption reviews and final Quality Gates/Human approval remain
pending, not waived. Production adoption is NOT APPROVED.

No elevated execution or Administrator command, production or migration 0004
change, extra artifact, staging or commit. STOP before the later separately
authorized complete revised experiment.

Final documentation consistency confirmation (/root/amend_harness_review):
APPROVE, BLOCKER 0/HIGH 0. Exact nine-artifact final UTF-8/whitespace/readback,
Task counts and recorded source hashes PASS. Exact-path git diff --check PASS;
cached diff empty; HEAD unchanged at
a0a6930d89da947f6e033682500ec0f4539d5fed. The four Task and five experiment
artifacts remain untracked; no staging or commit. Native/adoption boundary
unchanged: STOP before later separately authorized execution.

## Final revised native experiment — Human report recorded 2026-10-10

The Human reports COMPLETE SUCCESS true for the full revised experiment,
manually executed in bounded Administrator PowerShell. The normal Codex/IDE
process remained non-elevated. Codex did not execute, rerun or independently
reproduce this experiment. This report succeeds the failed first full run and
the I11 remediation/I14 design-amendment/static checkpoints above; none of
those historical observations is rewritten as success.

| Supplied final native observation | Result |
| --- | --- |
| COMPLETE SUCCESS | true |
| Static planned / total / PASS / FAIL / SKIP / unexecuted | 56 / 56 / 56 / 0 / 0 / 0 |
| Race planned / total / SAFE / VIOLATION / infrastructure failure / unexecuted | 3600 / 3600 / 3600 / 0 / 0 / 0 |
| Unauthorized bytes returned | false |
| Unauthorized data requests | 0 |
| Owned children created / reaped | 3601 / 3601 |
| Temporary roots created / cleaned | 1 / 1 |
| Native handles remaining | 0 |
| Mapped views created / unmapped / remaining | 2 / 2 / 0 |
| Production Tool invocation | false |
| Production requires Administrator / Developer Mode | false / false |
| Atomic content snapshot proven | false |
| Historical link provenance proven | false |

The report identifies the full revised 56-static/3600-race matrix. No exact
runtime nonce path, execution timestamp, fresh OS/volume metadata, raw per-row
transcript or run-source checksum was supplied; none is invented. Earlier
static source hashes and the initial probe's host/root observations are not
represented as independently captured final-run identity. Review is of this
Human-supplied final report against the approved exact matrix and oracles.

### I11 genuine native guard confirmation — EXP-058-1 CLOSED

I11 planned/executed/PASS: 3/3/3. The opaque GUID attempt reports
opaque_reparse_security_check_reached true, explicit_reparse_rejection true,
reason containment_rejected. The approved final-file opaque fixture and strict
reparse/containment predicate therefore have affirmative native confirmation
in this report; an unrelated type/native failure is not the passing evidence.
The other two approved I11 slots are the junction and distinct-volume mount
fixtures. No fixture substitution or missing/unsupported slot is reported.

### I14 mutual-exclusion native confirmation — EXP-058-2 CLOSED

I14 planned/executed/PASS: 3/3/3. Reported model:
current_open_mutual_exclusion. Each independently recorded subproof PASS:

| Subproof | Reported native outcome |
| --- | --- |
| mapping_first | Preexisting writable mapping caused explicit reader final-open sharing conflict. |
| section_first | Preexisting writable section caused explicit reader final-open sharing conflict. |
| reader_first | Reader acquired and remained live; later incompatible writer failed with sharing violation, later writable mapping creation failed, and bounded read completed while reader protection remained held. |

These are the approved native ordering slots, not reuse of the first run's
unreachable mapping cut or arbitrary sharing failure. Their approved controls
distinguish a retained writable view after writer/section closure, a retained
writable section without a live view, and the exact reader-first writer-open.
In reader_first, failure of the writer prerequisite is sharing evidence;
the separately attempted PAGE_READWRITE mapping on the readonly reader is an
access-rights check, not a second sharing proof or mapping from a failed writer.
The supplied summary does not add new numeric API statuses beyond the approved
oracles; it reports each complete ordering PASS. FILE_SHARE_WRITE stays
NOT PERMITTED. Reader protection is retained through content, EOF and final
metadata, with no release/reopen gap in the approved passing slot.

### Observed bounds and retained limitations

| Supplied observed maximum | Value | Approved work/output limit |
| --- | --- | --- |
| Returned bytes | 65536 | 65536 |
| Physical bytes | 65536 | 65537 |
| Data requests | 17 | 17 |
| Retained handles/state metric | 24 | 48 reader-owned retained handles |
| Native calls | 151 | 253 per reader attempt |

The report's retained handles/state metric is preserved under its supplied
label, not promoted to a stronger measurement definition. The reported
maxima are consistent with the approved ceilings. No unauthorized data request
occurred. No wall-clock maximum was supplied; the five-second support
observation threshold remains distinct from a hard duration/cancellation
guarantee. Exact bytes and bounded requests are evaluated by the locked matrix;
these aggregate maxima alone are not a new production guarantee.

The supported security statement remains bounded exclusion of incompatible
ordinary writers/writable mappings during the owned reader window, under the
trusted-root, local fixed NTFS/native access-share profile. It is not atomic
historical content immutability or hostile same-user/admin/kernel isolation.
ATOMIC CONTENT SNAPSHOT REQUIRED/CLAIMED/PROVEN: NO/NO/false.
HISTORICAL LINK PROVENANCE REQUIRED/CLAIMED/PROVEN: NO/NO/false.
Link count one is only a current topology restriction; no immutable/historical
link topology claim. Detected drift still rejects. No hard time guarantee.
Experimental elevation manufactured hostile fixtures only; the candidate
production reader requires neither Administrator nor Developer Mode.

### Fresh adoption-review boundary

Four fresh independent read-only reviews now assess this final report against
the approved containment design: Windows Containment, Security,
Invocation/TOCTOU and Architect. No rerun, source change, experiment fixture,
production module, migration 0004 or first production effect is authorized.
Experiment adoption requires all four APPROVE and BLOCKER 0/HIGH 0. Even
then, production implementation, canonical invocation/Entry/migration proof,
final Task Quality Gates and Human final acceptance remain separately gated.
The experiment does not establish durable Entry, exactly-once Tool invocation,
Result semantics or generic write-Tool replay safety. Task remains in_progress;
task.yaml/context.md/acceptance-criteria.md are read-only in this phase.

### Four fresh post-experiment adoption reviews — final convergence

All four independent reviewers read the Human final report, persisted evidence
and approved Task design/oracles read-only. Reviews used only the supplied
attachment and the five permitted repository artifacts, without source import,
rerun, discovery, protected-target access or edits. Prior implementation/static
reviews support the native mechanism/lifetime assessment; reviewers do not
claim independently captured runtime rows or final-run identity/checksum.

| Adoption scope | Fresh independent reviewer | Verdict | BLOCKER | HIGH |
| --- | --- | --- | --- | --- |
| Windows Containment | /root/adopt_windows | APPROVE | 0 | 0 |
| Security | /root/adopt_security | APPROVE | 0 | 0 |
| Invocation / TOCTOU | /root/adopt_invocation | APPROVE | 0 | 0 |
| Architect | /root/adopt_architect | APPROVE | 0 | 0 |

Windows review finds the final report matches all locked lexical/spelling,
exact-byte/size, type/identity, final/intermediate symlink, junction,
distinct-volume mount, opaque reparse, hard-link and native-fault obligations.
Root/ancestor pins, native handle-relative traversal and absence of an ordinary
pathname-open security fallback are supported by the approved implementation
review plus complete matrix/race PASS. I11's actual opaque guard is genuine
security evidence. The controlled experiment supports the trusted-root model;
it does not certify arbitrary deployment ACLs or expand its trust assumptions.

Security review attempted invalidation across unauthorized reads/bytes,
reparse/junction/mount/hard-link bypass, identity/resource spelling rebound,
writer/mapping coexistence, race substitution and leaks. No BLOCKER/HIGH finding:
all strict slots pass, all 3600 races are SAFE, all unauthorized counters are
clear and reported ownership/cleanup is balanced. I14's view-first and
section-first states independently block acquisition, and reader-first writer
controls attribute exclusion while the same reader remains protected. Mapping
access denial from the readonly reader is kept distinct from sharing evidence.

Invocation/TOCTOU review accepts the future containment boundary: same verified
handle through bounded content/EOF/postmetadata, no path reopen or unprotected
gap, current object identity and coverage of all locked substitution cuts.
This experiment proves neither durable Entry nor exactly-once invocation,
Result semantics or generic write-Tool replay safety. Original continuation
and Entry architecture remain unchanged.

Architect review confirms the first Tool remains repository_file_read under
the exact AIO-051 native v1 identity/selector/route. The native containment
candidate needs no new public API, additional abstraction or another redesign.
Private Entry/storage, S/G/P, W/C, COMMIT uncertainty, predecessor semantics
and roadmap are unchanged. Production Administrator/Developer Mode are not
design requirements; elevated prototype success does not demonstrate a
canonical unelevated production integration. Phase 2 must still validate
ordinary configured read access in the supported root environment.

EXPERIMENT ADOPTION: APPROVE. Aggregate BLOCKER 0, HIGH 0. EXP-058-1 and
EXP-058-2 CLOSED on the supplied successful native evidence. Approval covers
only the bounded trusted-root/local NTFS candidate and current-open ordinary
writer/mapping exclusion. Atomic snapshot and historical link provenance remain
false/unclaimed; no hostile same-user/admin/kernel or hard-time guarantee.

READY FOR AIO-058 PRODUCTION PHASE-2 AUTHORIZATION: YES. This is readiness for
a separate Human decision, not production authorization or Task completion.
No production implementation, migration 0004, canonical production Tool read
or future first effect has started. Task stays in_progress. The read-only
supporting Task files retain earlier pending checkboxes/checkpoints; this
latest review records final experiment/adoption satisfaction without modifying
those files or waiving later implementation/regression/migration/128-scenario,
formal final Quality Gates or Human final acceptance. No required evidence/
adoption review in this phase failed or was skipped. STOP before Phase 2.

### Final evidence persistence and process checks

Fresh read-only documentation consistency confirmation by /root/adopt_windows:
APPROVE, BLOCKER 0/HIGH 0. Literal two-file UTF-8, whitespace, exact final count,
four-review convergence and limitation/authorization readbacks PASS. The entire
previous historical body in each file is preserved. SHA-256 comparison confirms
the three supporting Task files are unchanged. An initial literal-match check
did not recognize the first-run table's 54/52/2/0 presentation; the corrected
check accepts that table and wrapped prose, and final verification PASS.

Exact-two-path git diff --check PASS. Both evidence files remain untracked;
literal whitespace checks cover their complete contents. Cached diff empty;
index CLEAN. HEAD unchanged at a0a6930d89da947f6e033682500ec0f4539d5fed.
Only the two authorized evidence files were written in this phase. No rerun,
production implementation, migration 0004, first effect, source change,
search/discovery, Task/Workflow catalog enumeration, protected-target access,
staging or commit. All required final evidence/adoption checks PASS; full Task
implementation/final Gates/Human acceptance remain pending. STOP before Phase 2.
