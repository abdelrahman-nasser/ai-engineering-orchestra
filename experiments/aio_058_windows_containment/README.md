# AIO-058 Windows containment experiment

This noncanonical, nonproduction, nonpackaged experiment evaluates the locked
native candidate. It creates no Execution Entry, production adapter, migration,
canonical Tool invocation or future first-effect resource.

The first full Human run FAILED: 52/54 static PASS (I11/I14 FAIL), 3600/3600
races SAFE, zero violations/unauthorized data or bytes, workers 3601/3601 and
roots 1/1. Its chronology remains in [findings.md](findings.md). Those results
are historical evidence and do not approve adoption or a later revision.

## Current authorized amendment

The Human reopens Phase 1 on 2026-10-10 for I14 only. The rejected model tried
to make a writable mapping coexist with the readonly reader and then detect
mutation. The revised invariant is current-open mutual exclusion: existing
incompatible write access/write-capable mapping state prevents reader
acquisition; the retained reader prevents subsequent incompatible writer
access and writable-mapping setup during its owned bounded read window.

The candidate still uses retained RootDirectory NtCreateFile components,
minimal final access 0x00100081, FILE_SHARE_READ=1 only, FILE_OPEN,
FILE_NON_DIRECTORY_FILE, FILE_OPEN_REPARSE_POINT and synchronous nonalert IO.
FILE_SHARE_WRITE is not permitted. The same verified final handle stays live
through all chunks, EOF and final metadata; it closes only after those native
operations finish. No release/reopen/read gap or ordinary pathname fallback.

Atomic content snapshot REQUIRED/CLAIMED: NO/NO. Historical link provenance
REQUIRED/PROVEN: NO/NO. Exclusion is an ordinary Windows access/share guarantee
in the supported local NTFS profile during the current handle lifetime.
It does not prove a historical byte version, immutable link topology, hostile
same-user/admin isolation, privileged/kernel protection or a hard time bound.
Detected drift still rejects, but timestamps do not prove every mapped change.
Link count one is only a current topology restriction.

## Revised I14 plan and accounting

There remain 18 security cases. Revised static total is 56 (old total 54):
I01(1), I02(4), I03(2), I04(3), I05(12), I06(8), I10(2), I11(3), I12(2),
I13(2), I14(3), I16(6), I17(5), I18(3). Races remain nine variants times four
cuts times 100 = 3600. Revised complete total is 3656.

I14 is one canonical case with three independent static records against the
same owned fixtures/mapped.bin, initially 4096 ASCII A bytes:

| Slot | Required observable proof |
| --- | --- |
| mapping_first (I14-A) | Exact native read/write source -> PAGE_READWRITE section -> FILE_MAP_WRITE view; verify live writable view; close writer and section handles, retain view. Exact final candidate NtCreateFile must reject with c0000043 / WinError32 before data. Verify unmap/cleanup. |
| section_first (I14-A2) | Same writable section, calibrated by a temporary writable view; restore byte, unmap view, close writer, retain section without a view. Exact final candidate acquisition must reject with c0000043 / WinError32 before data. Close section and verify cleanup. |
| reader_first (I14-B) | Exact writer-open succeeds as a control before acquisition. At verified reader's pre-read cut, same writer-open must fail with WinError32 while reader lives; mapping from that failed prerequisite is not claimed executed. Separately PAGE_READWRITE mapping from the readonly reader must fail with access-denied5. Read original bytes/EOF/postmetadata under the same live handle, close it, then prove same writer-open succeeds and closes. |

The additional section-first record checks a route that does not require a new
writer-open: mapping an already-held write-capable section. No independent
reader attempt is hidden in setup or a combined opaque assertion. Native view
calibration and before/after writer controls are logged fixture-control actions,
not extra reader attempts or workers. CPython mmap duplicate behavior is not
the security contract. Arbitrary share/access/native errors cannot pass a slot.

The exact API constants, failure attribution and lifetimes are authoritative in
[context.md](../../.ai/tasks/AIO-058-durable-execution-entry-and-controlled-invocation-foundation/context.md).
Native compatibility is still a candidate requiring the future complete run;
unexpected success or unsupported section/mapping semantics fail support.

## I11 and unchanged containment obligations

I11 retains its corrected final-file opaque GUID object, tag 0x00000042,
GUID 05805858-0058-4058-8058-005800580058, AIOX payload and exact query-back.
Its result requires the actual final-component OBJ_DONT_REPARSE guard or
queried reparse attribute/exact-tag rejection before data. An incidental
directory/type/native failure is insufficient. Native confirmation is pending,
and the next full run must execute I11 again.

Other lexical/naming/type/link/root/volume checks, known sentinel identity
interception, bounds, nine race variants and owned fixture recipes are unchanged.
Reader work is at most 16 target opens, 12 metadata queries per handle,
253 native calls, 48 retained reader handles, 17 data requests, 65537
requested/physical bytes and 65536 immutable output bytes. Five seconds is
only a support observation threshold, not safe cancellation or hard realtime.

## Ownership and execution boundary

Only synthetic known paths inside one fresh
C:\Users\Abdelrahman\AppData\Local\Temp\aio-058-containment-<uuid32hex>
root with repo/, outside/ and evidence/ are allowed. Required hostile fixtures
include actual links/reparse tags and a second disposable NTFS VHD; unavailable
fixtures fail visibly. The one fixed System32 formatter operates only on the
owned VHD identity derived from its retained native handle. No unrelated disk
selection, process lookup, directory enumeration or recursive link traversal.
Exact known-path cleanup, all owned native handles/views, formatter child and
non-daemon race threads must be accounted for and released/reaped.

Codex remains non-admin. No privilege/policy/ACL/Developer Mode changes,
protected resource, network Tool, production import, extra artifact, staging or
commit. Four fresh design scopes must APPROVE before harness remediation:
Windows Containment, Security, Invocation/TOCTOU and Architect. Then only the
three exact experiment Python files may change and be statically preflighted.
No own source import, native fixture or elevated matrix is run in this phase.

No Administrator command is issued. STOP before elevated execution.
A later authorization must run the complete final 56-static/3600-race revision;
the first run's SAFE results cannot substitute for that run, fresh adoption
reviews or Human production approval.

## Current amendment checkpoint — 2026-10-10

All four fresh design scopes APPROVE, each BLOCKER 0/HIGH 0, before harness
edits. The three exact experiment Python sources have been remediated.
Independent read-only implementation review also APPROVE, BLOCKER 0/HIGH 0.
Fixed stdin AST parsing/in-memory compilation and static accounting, strict
I11/I14 paths, handle/view cleanup and worker ownership checks PASS. Revised
plan: 56 unique static attempts, including three independent I14 records,
and 3600 races. Source hashes and evidence are in findings.md.

This is static preparation only. No amended native attempt or elevated matrix
was executed, and neither I11 confirmation nor Windows mapping compatibility
is claimed. Production adoption and final Gates/Human approval remain pending.
STOP before elevated execution; the complete revised run needs later explicit
authorization. No Administrator command is supplied in this phase.
