# AIO-058 Phase 1 design

## Authority and current state

Human instruction authorizes design/investigation and exactly four Task files,
not production implementation, experiment execution, target IO, staging or
commit. Baseline is clean main at
a0a6930d89da947f6e033682500ec0f4539d5fed; AIO-057 is CLOSED.
Task status remains in_progress. Phase-1 approval is not final Task closure,
production readiness, experiment evidence or final Human architecture approval.

Explicit Workflow selection is architecture-change: understand/design now;
implement/validate and final review require later phase authorization. Architect,
software-engineer, reviewer and security-reviewer instructions apply to their
respective responsibilities. Required final documentation_consistency and
independent_review Gates remain pending against implementation evidence.

Direct dependencies: AIO-049 ownership, AIO-050 authenticated authority,
AIO-051 immutable registry/Binding, AIO-056 Claim/Lease, AIO-057 JIT. AIO-047
Store and AIO-055 Intent are transitive; AIO-053 supplies integration context.
Only literal relevant sources are read. No repository search, directory
traversal, Task/Workflow catalog enumeration or protected-target access occurs.

## 1. Entry identity and persistence

Canonical Task-local term: **Agent Execution Entry** (Entry). It is the immutable
fact that one exact Dispatch entered an authorized attempt; it is neither
invocation evidence nor an outcome. No independent execution_entry_id.

Identity is (exact pinned authoritative ledger, D), where D is exactly
(authorization_domain_id, issuer_kind, issuer_id, grant_id), case-sensitive.
The genuine Session binds domain, ledger_instance_id, domain_generation and
registered physical file pin; no field alone proves authority. Entry's SQL PK
is D because one ledger already supplies that namespace. Claim generation is
provenance, never an Entry identity component permitting another Entry.

Planned private table agent_execution_entries is STRICT WITHOUT ROWID with
nine immutable columns: D's four TEXT COLLATE BINARY fields, claim_id,
executor_instance_id, lease_generation, entry_time, entry_time_key. Token fields
reuse AIO-056 64 lowercase-hex constraints; generation is positive signed-64;
time uses the existing canonical 27-character UTC form and parsed microsecond
key range 0..315537897599999999. Complete decoding validates text/key equality,
not length alone. No payload, status, effect flag, Result or authority boolean.

Restrictive composite FK to Intent(D), and exact seven-field FK to existing
Claim UNIQUE(claim_id,D,executor_instance_id,lease_generation), anchor the
immutable Admission/Grant/complete Run/canonical Binding transitively. Store
decodes and compares those complete values, not IDs/hashes alone. No copied
JSON, independent Run reference, Tool identity string or ledger-column copies
are needed. No additional index is required beyond PK and referenced Claim
keys for these point operations; no public Entry enumerator is introduced.

Unconditional UPDATE/DELETE triggers and a BEFORE INSERT duplicate-D guard
reject equal and conflicting duplicate/REPLACE attempts; no conflict handler
may silently ignore insertion and publish a continuation. Insertion guards
require active clean v4, exact nonlegacy parent, highest current Claim,
executor/generation equality, no revocation, nonregressing time and live Lease
at T. Authority proof validation belongs in guarded Store consumption, not SQL.

Permanent D exclusion survives every Claim generation, restart, success,
failure, missing outcome and future resolved Result. Entry is never reset or
deleted. AIO-056 may still renew/reclaim according to its existing semantics;
generation N+1 history does not permit another Entry. Claim ownership and
Entry occupancy are separate facts. No worker skip/selection policy is added.

## 2. Atomic final consumption, linearization and locks

Do not call the existing v3 _consume_assessment and then insert elsewhere:
that burns the cell and returns provisional evidence. Extend/factor a new
private final-consumption operation using AIO-057's held-lock predicates.
Existing diagnostic paths stay diagnostic. No public predecessor signature
changes and no raw connection or effect callback escapes Store ownership.

Acquisition order remains S -> G -> P -> W -> C. S is the genuine owned
operation lease; G the install-once authority guard; P Producer state; W the
same Store BEGIN IMMEDIATE writer; C the exact Claim subject cell. Registry
reservation locks do not nest with operational locks. Proof minting precedes
the read scope; leaf checks cannot mint, mutate, await or reenter coordination.

One original synchronous orchestrator call performs:

1. Enter S, validate same Session/Store/executor/pin; acquire G/P. Pure checks
   may inspect canonical strings/objects and configured native function handles,
   but cannot touch target metadata, components, existence, content or ACLs.
2. Store opens only its owned ledger, acquires W, audits full v4 state, acquires
   C and reserves CONSUMING. Reject any Entry already occupying D before effect.
3. Revalidate exact immutable parents/current highest Claim/executor/effective
   Renewal Lease/revocation; freeze participating authority/prerequisite inputs.
4. Sample existing trusted Store UTC exactly once as T. Reuse canonical JIT
   proof, issuer/principal/entitlement, prerequisite, mode, Binding and active
   snapshot checks; require acquired_at <= T < effective_expiry and fresh proof
   half-open validity. Reject regression; never clamp or use caller time.
5. Insert Entry and advance shared watermark atomically; complete full audit
   and COMMIT once. No target effect can occur inside this transaction.
6. Acknowledged durable COMMIT releases W. Finish CONSUMED under C, seal one
   original continuation while S/G/P remain held, then release C. No W
   reacquisition under C and no C held across native IO.
7. Recheck live original guard/session and minimal adapter availability through
   held-lock leaf checks, burn continuation immediately before the first native
   target metadata/open action, and execute the fixed private adapter once.
8. Finish native handles/outcome; release P/G then exit S with its original
   ownership post-check. Disclose content only after successful exit. Postcheck
   failure after effect gives ambiguity and discards content; never reinvoke.

T is logical authorization linearization conditional on successful durable
COMMIT; COMMIT is the persistence/exclusion point. No assertion that Lease or
proof remains unexpired at physical effect time. Expiry after valid T does not
cancel the entered original continuation, including expiry before COMMIT.
The consumed original Grant's issuance/Admission interval is not a continuing
execution window. Its expiry alone must not veto an otherwise valid current
Claim and fresh entry-purpose proof, preserving AIO-057 F31. Do not replace
fresh entry authority with the historical Grant or add a parallel expiry check.

G/P continue through the entire bounded synchronous adapter attempt, ordering
issuer disable, logout, Human withdrawal, policy changes and current-source
publication after the entered attempt. A request waiting for G is not effective
revocation. Store revocation can commit after W releases: **it does not cancel
this committed original Entry, even before the first target action**. This is
an explicit fresh decision preserving E17, rather than an assumed cancellation
policy. Revocation-first rejects; writer-serialized Entry-first accepts and
later tombstone stays historical. Native OS permission denial still rejects
access; Entry cannot override ACLs. Detected actual guard/ownership loss before
target action suppresses the continuation and leaves Entry occupied.

S prevents resource release during the complete operation; close/fence waits
outside locks needed by it. Any detected terminal session state before native
action suppresses effect. Native adapter is a leaf: no Session/Producer/Store
entry, callbacks, authority mutations, locks earlier than P, async ticket or
delayed work. Root capability is provisioned before participants publish and
retained over the operation; lifecycle teardown waits outside operational
protections. These constraints, rather than lock names alone, exclude inversion.

## 3. Continuation and uncertainty

Original Execution Continuation is private, process-local, nonconstructible,
noncopyable, nonserializable and same-thread/same-call only. Its sealed bindings
include exact committed Entry and immutable parent values, original AIO-057
cell/consumption, authorizer and guard epochs, genuine Session/Store/file pin,
executor capability/incarnation, Producer/resolver snapshot, native adapter and
trusted root capability. Alias references share one atomic once-state.

States are sealed -> started -> finished, or terminal suppressed/uncertain.
No returned bearer continuation, callable callback, generic factory, public
mint helper, deferred transfer, restart recovery or historical constructor.
Publishing one is not required: the protected stack frame carries it straight
to the fixed adapter. Direct adapter calls without it reject before target IO.
No Entry or diagnostic result alone can authorize invocation.

Confirmed rollback after CONSUMING terminalizes that Claim subject. Unknown
COMMIT always terminalizes UNCERTAIN and performs zero target actions, even
when the original stack survives and later proves commitment. Thus no automatic
invocation after uncertainty and no same-Claim rearm. Reconcile only the same
registered ledger/pin/D and exact original Claim facts, using a later new S
scope after C/G/P unwind; never reacquire W while C is held.

Reconciliation returns history-only exact Entry, verified absence, conflict or
infrastructure/integrity failure. Committed Entry permanently blocks D.
Verified absence permits only explicitly initiated fresh reclaimed Claim with
new executor/proofs and guarded consumption; not automatic replay. Same live
terminal Claim remains burned. Unknown/mixed/corrupt state suppresses effect.
Human/future recovery may audit, fence and use existing explicit remediation,
or authorize a new semantic Run/Grant/Admission/Intent. It cannot revive old
continuation, erase Entry, switch ledger or treat benign repeated reads as a
generic replay guarantee. Process dies during/after read or before outcome:
historical Entry does not say whether effect occurred; no automatic retry.

## 4. Private Store seam and migration design

Conceptual private methods (names may be refined without public widening):
_enter_execution(request, guarded_operation), _classify_execution_entry(request),
_load_execution_entry_history(request). Classification supplies already-entered,
verified-absent, exact historical/rebound conflict or fail-closed failure. Requests
are privately minted through original same-Session authority; IDs/booleans are
not capabilities. Reconciliation/load never mint a continuation. No external raw
SQL, generic writer callback, public Store widening or public Entry schema.

Planned 0004_execution_entry.sql adds the empty Entry table and guards. It also
replaces exactly the existing Intent/Claim/Renewal active-clean-v3 operational
insert guards with equivalent v4 guards, preserving their history predicates.
0001/0002/0003 bytes and checksums remain exact. Store's established allowlisted
checksum resources, contiguous migration history, prefix manifest and exact
version-specific DDL fingerprints extend to v4; numeric version alone is unsafe.
Retain verified v1/v2/v3 fingerprints for source validation.

Explicit AIO-049 trusted administrative entitlement, registered-file pin and
complete process/operation quiescence precede BEGIN EXCLUSIVE. Audit full source
before and inside it; mark dirty, apply exact suffix, preserve existing payloads,
classification, revocations, Claims/Renewals and watermark; append exact history,
publish clean v4 metadata and audit complete destination before one COMMIT.
v3->v4 adds zero Entries. v2->v4 applies 0003/0004; v1->v4 applies
0002/0003/0004 atomically, retaining legacy-only migration classification. No
Entry/Claim backfill or implicit reinterpretation. Current provisioning creates
v4 with empty histories. Operational v3/old/newer/dirty opens reject; no repair,
auto-migration, fallback or downgrade. Crash precommit keeps original source;
unknown commit recognizes fully verified v4 or intact old source only, permitting
an explicitly authorized administrative retry in the latter case.

Full audit occurs at operational open/read/write/precommit, including unrelated
Entry chains. Entry without Admission/Intent/Claim, unknown Claim, wrong
executor/generation/D, duplicate/conflicting Entry, malformed time/key, schema
or migration drift, inconsistent chains or two Entries for D all fail closed.
Historical audit reconstructs effective Lease from Renewals at/before T,
requires acquired_at <= T < effective_expiry(T), no successor Claim acquired
at/before T, Entry time >= Admission and watermark >= Entry time. Later reclaim
and renewal are legitimate, not corruption. Later revocation may have time >= T;
equal timestamps are allowed by existing clock policy and ordered by insertion
serialization, not a fictional total timestamp order. SQL insertion prevents
revocation-first Entry; retrospective time checks cannot attest hostile raw
same-timestamp injection. Malicious local administrator tamper resistance and
manual split/stale active-copy detection remain outside supported guarantees.

## 5. Claim/Entry state matrix

Prepare means fresh positive AIO-058 orchestration, not standalone AIO-057
diagnostic execution. AIO-058 may classify occupancy early; standalone predecessor
diagnostics remain nonauthoritative and unchanged. Every Yes requires all
other genuine ownership, proof, prerequisite and integrity checks.

| State | Prepare JIT | Commit Entry | Invoke | Reclaim | Replay old D |
| --- | --- | --- | --- | --- | --- |
| Intent pending, no Claim | No | No | No | Acquire generation 1 only | No |
| Live highest Claim, no Entry | Yes | Yes | Only after acknowledged commit plus original continuation | Only after expiry | No |
| Expired Claim, no Entry | No | No | No | Yes, fresh Claim | No |
| Reclaimed, no Entry | Highest live Claim only | Highest live Claim only | Original newly entered continuation only | After that Claim expiry | No |
| Live Claim, Entry committed | No new preparation | No second Entry | Original live continuation once | After expiry per AIO-056 | No |
| Claim expires after Entry | No | No | Original accepted continuation once | Yes | No |
| Later Claim after Entry | No | No | No new continuation; original may finish | Per AIO-056 | No |
| Revocation after Entry | No | No | Original accepted continuation may finish | No fresh revoked Claim/Renewal | No |
| Restart after Entry | No | No | No | If unrevoked and expired, history only | No |

## 6. First Tool and trusted root

repository_file_read is confirmed: sole current Core operation; least scope
needed to demonstrate the boundary with no write Tool, shell or Provider call.
Use exact AIO-051 tool::aeo-native-repository-file-read::v1 and selector
AEO_NATIVE_REPOSITORY_FILE_READ_V1 with its original Runtime/environment/operation
route and canonical two-field Binding. Filling the reserved native family is
not registry rebinding. Production must independently verify implementation
meaning against this locked profile; a changed containment/configuration meaning
requires a new Tool ID and distinct complete route, never silent v1 reuse.

No AIO-049 or AIO-050 production changes are planned. AIO-051 registry/resolver
and AIO-056 public semantics stay unchanged. AIO-057 needs only the private final
consumer factoring described above; public diagnostic behavior remains. Store
v4 extension changes the AIO-056 private persistence implementation, not its
public Claim eligibility/renewal/reclaim contract. No public Entry/adapter/Result
API or schema is necessary. Full Result/Journal remains future work.

Root is an explicit trusted composition capability bound to exact environment,
same process/session and native profile, not CWD, caller root string or Run
field. Control-plane provisioning pins an existing absolute local fixed NTFS
root by native directory handle and volume/file identity, rejects root/ancestor
reparse substitution and retains required ancestor handles. It may predate
Entry only without any resource-derived target access. Root identity cannot
hot swap under an environment ID; change requires teardown/new environment
authority chain. No resource lookup/stat/ACL/open/read before Entry COMMIT.
Supported roots require trusted ACL/configuration preventing untrusted writers
from installing links, changing security or replacing descendants. AIO-058 is
not a hostile same-user/admin filesystem sandbox. Root provisioning checks
this control-plane support profile; unsupported/unprovable profiles fail closed.
The experiment challenges cooperative native races; it does not expand the
supported hostile-code threat model.

## 7. Windows containment candidate and review boundary

PREIMPLEMENTATION CONTAINMENT EXPERIMENT REQUIRED: YES, retained inside AIO-058
as separately authorized preimplementation subphase X. This document selects
a reviewed candidate for experimental evaluation only. Production adoption is
conditional on X evidence and fresh Windows/Security/TOCTOU approval; no proven
Win32 strategy or actual native reader is claimed in Phase 1.

Lexical Core validation stays unchanged. Adapter additionally rejects Windows
ambiguous/unsupported names without rewriting: any colon/ADS, trailing dot or
space, reserved DOS/device component (including documented extension variants),
invalid UTF-16/surrogates, Win32 reserved punctuation, absolute/drive-relative,
UNC/device/extended prefixes, backslash and . or .. segments. Maximum 16
segments and 4096 UTF-16 resource units, excluding terminating NUL. No NFC/NFD,
case folding, short-name expansion, percent decoding, trim or normalization.
Known 8.3 alias spellings must not select a differently named target: verify
actual long component name matches requested UTF-16 units exactly. Different
case target is rejected even on case-insensitive NTFS. Unicode unsupported by
an exact native roundtrip rejects rather than replacing characters.

Proposed open primitive is component-relative NtCreateFile using a trusted
parent handle as RootDirectory, one component per call, no OBJ_CASE_INSENSITIVE,
OBJ_DONT_REPARSE where supported, FILE_OPEN_REPARSE_POINT, FILE_OPEN disposition
and appropriate directory/non-directory options. Evaluate supported API/ABI
availability explicitly; no ordinary absolute open(path) fallback. Every
component requires no reparse attribute/tag and exact long name. Keep root and
all ancestor directory handles until final IO ends, denying delete/write
sharing and requesting only minimal metadata/traverse rights. Parent handle
traversal and retained pins are the containment mechanism; string prefix check
alone is insufficient. If supported semantics cannot be established, unavailable.

Final handle opens the exact final component with minimal read/metadata rights,
FILE_NON_DIRECTORY_FILE and no write/delete sharing. Query handle properties:
local fixed NTFS volume equal to root; final normalized path and exact component
sequence below pinned root; volume serial plus FILE_ID_INFO/FileId identity;
GetFileType == FILE_TYPE_DISK; non-directory, non-reparse, non-device regular
data file; NumberOfLinks exactly 1. Reject symlinks, junctions/mount points and
all reparse tags at root, ancestors and final file. Reject directories, pipes,
devices and cross-volume/remote files. Reject hard links (including in-root
aliases) conservatively; no outside-link enumeration. File ID is current opened
object provenance, not a presumed pre-Entry content version. No stat-then-open.
Metadata/open are already target effects and require the consumed continuation.

Authorized resource maps by preserving each exact slash segment as a relative
native component under the pinned root; separator conversion has no alternate
target meaning. Full Run/Binding equality and root/environment association
precede native action. No nearest file, root, wildcard, alternate casing target,
alias or fallback. Root handle plus retained ancestry proves traversal from the
authorized root; final path/identity are independent cross-checks. GetFinalPathName
cannot alone close ancestor replacement races or prove provenance.

Content profile: at most 65536 bytes output. Check initial EOF size first;
reject oversized file without content reads. Read from same verified handle
at fixed offsets in at most 16 requests of <=4096 bytes, plus one private
one-byte EOF/growth probe at initial length. Short/failed reads discard all
partial content; overflow/growth rejects. Zero-byte file succeeds with empty
bytes after EOF check. Recheck final file ID/type/reparse/link count, size and
change/write metadata; detected drift yields resource_changed. No text decode,
newline/BOM conversion, binary sniffing or content logging: output is immutable
bytes with byte_count, and binary/invalid UTF-8 succeeds identically.

The 2026-10-10 Human-authorized I14 amendment replaces the rejected
mapping/reader-coexistence-and-drift model with current-open mutual exclusion.
The target reader requests FILE_READ_DATA | FILE_READ_ATTRIBUTES | SYNCHRONIZE
(0x00100081), ShareAccess FILE_SHARE_READ (0x00000001) only, FILE_OPEN,
FILE_NON_DIRECTORY_FILE | FILE_OPEN_REPARSE_POINT | FILE_SYNCHRONOUS_IO_NONALERT.
FILE_SHARE_WRITE is not permitted. In the supported local NTFS profile,
preexisting incompatible write access or a writable mapping must prevent
reader acquisition with an explicit sharing conflict before content reads.
Conversely, an acquired reader target handle must prevent a subsequent
incompatible write-data open, including the writer prerequisite for creating
a PAGE_READWRITE file mapping, while that reader handle remains live.
Minimal read-only reader access cannot itself create a writable file mapping.
The same exact acquired handle and its share protection remain live through
all chunks, the EOF probe and final metadata verification, and close only
after the final native operation completes. No release/reopen/read gap exists.

This is exclusion of ordinary incompatible Windows file access in the current
owned read window, not historical content immutability. Atomic content snapshot
is neither required nor claimed. It does not cover privileged kernel actions,
hostile same-user/admin code, a stronger filesystem sandbox, historical byte
versions or unsupported filesystems. Success means bytes from this contained
opened object. Detected size/identity/type/link/write/change drift still rejects;
timestamp comparison is not promoted to detection of every mapped mutation.
The previous unconditional known-mapping-drift obligation is superseded only
for I14 by the explicitly authorized mutual-exclusion proof; other read and
containment checks remain unchanged. Missing native support or an ordering that
violates the specified exclusion fails the experiment/adoption gate.
Pre/post nlink==1 also does not prove immutable or historical link topology.
Native link creation may use zero/metadata-access handles; share modes alone
are not a hard-link exclusion proof. Test create/remove and POSIX replacement,
retain the outside sentinel and its ancestry without delete sharing, and reject
outside alias reads while that sentinel remains an outside object. Stronger
historical provenance requires a separately approved contract.

Bounded synchronous means bounded work, handles, requests and output, **not a
hard wall-clock guarantee**: <=17 data requests, <=16 target opens, <=12
metadata queries per root/component (204 total including final recheck), and
<=16 target-handle closes: 253 native calls maximum per attempt, no retry/poll
loops. Root capability retains <=32 provisioned ancestor/root handles; target
walk adds <=16, so <=48 total retained handles. Fixed-size native name buffers
cover the accepted root+resource; insufficient buffer fails closed, no dynamic
retry. S/G/P stay held until
actual native completion and cleanup. No overlapped worker/deferred authority,
timeout return with live IO or unsafe cancellation-buffer release. 5 seconds
is only an experiment observation failure threshold, not a production realtime
promise. Windows native open/read can stall; guard-holding denial-of-service is
a residual supported-environment limitation. If a hard duration bound is
required, stop for a separately approved architecture redesign.

Minimal JIT availability is process-local supported Windows ABI/function
bindings, exact fixed adapter/selector, live root capability and exact immutable
active route/Binding/profile. Check after Entry immediately before native action;
no PATH, shell, subprocess, plugin/Provider discovery, credentials or health
framework. Target existence/access/containment failures are invocation outcomes,
not pre-Entry probes. Unavailable still leaves committed Entry permanently
occupied and consumes/suppresses its original continuation.

## 8. Exact bounded experiment X

X is designed only; separate Human authorization must name temporary paths,
prototype source, fixed interpreter/launcher and reviewed native dependencies.
No source/probe/test fixture is created or executed in Phase 1. X cannot import
production invocation entry points or use operational domain/ledger/root.

One nonce-owned disposable workspace contains repo/, outside/ and evidence/,
all nonsecret. Host root/volume metadata needed for this trusted fixture setup
is control-plane authorization, not arbitrary target access. Every file is
created by X: regular bytes, empty, binary, Unicode/case variants, oversized,
reparse/link targets and outside sentinel. A bounded host-control setup may
create junction/symlink/hard-link fixtures only at these exact paths; failures
are reported unsupported, not silently passed. No network/UNC/device/pipe
endpoint is opened: such spellings reject lexically before native dispatch.

X executes exactly the 18 I01-I18 matrix cases, every listed subcase mandatory.
Static variants run once each. I07/I08/I09 each have one race variant and I15
has exactly six (growth, truncation, same-size write, hard-link create/remove,
POSIX link replacement, POSIX rename replacement). Each variant runs 100
iterations at each of four fixed cuts: immediately before relevant component
open, after its ancestor pin, after final handle open before final metadata,
and before first content read. Thus exactly 3600 scheduled race attempts;
inapplicable/unreachable cuts are failures requiring review, never omitted.
Finite loops, not random stress alone. Attacker helper
threads use only X fixtures and are not authority continuations. Log only case,
cut, accepted/rejected, native status category, volume/file identity and byte
count; accepted synthetic bytes compare internally. Outside sentinel content
must never be read by reader; identity/origin checks precede data requests.

Oracles: exact requested regular contained identity or rejection; zero outside
sentinel content reads; zero data reads for rejected type/link/oversize cases;
no alias/case substitution; known writer/rename conflict rejects or is blocked;
<=65536 output, <=65537 physically read bytes, bounded requests/handles; zero
handle leaks on success/failure; no live IO at normal return; no fallback.
Instrumented data-call interception counts and asserts opened ID before reads,
and deterministic barriers prove races actually reached their intended cuts.

Measure per native call and per attempt. Any attempt >5s, hanging call, abnormal
termination, unreachable required race cut, unavailable fixture privilege,
unverifiable containment/type/exact-case property or sentinel-origin violation
fails the support gate. A trusted externally supervised experiment may stop a
hung prototype under its later explicit authorization; timeout is failure, never
proof of safe cancellation or production bounded duration. Evidence records
Windows build, NTFS/volume features, API/ABI, case-sensitive directory modes,
privileges, sharing outcomes and all subcase counts. No unsupported subcase is
silently treated as PASS. Static variants are fixed by the I rows: I01(1),
I02(4), I03(2), I04(3), I05(12 exact lexical attack strings), I06(8 exact naming
variants), I10(2), I11(3), I12(2), I13(2), I14(3), I16(6), I17(5), I18(3:
delay, native failure, cleanup). Revised total 56 static attempts plus 3600 race
attempts = 3656 planned attempts. The original 54/3654 totals remain historical
first-revision accounting. I14 is one canonical security case with three distinct,
individually logged static attempts; neither ordering is hidden in an opaque
combined assertion. Later authorization must bind exact fixture
spellings/flag constants to these slots without dropping an obligation.
Additional OS-specific reparse tags require an explicit matrix amendment;
three initial I11 variants are symlink-independent junction, mount point and
one supported other reparse-tag fixture. Phase-1 matrix counts scenarios, not
experiment iterations, and contains no runtime PASS claims.

Static slots are exact (absolute nonce prefix is the only deferred path value):

| Case | Fixed fixtures / variants, one attempt each |
| --- | --- |
| I01 | repo/fixtures/nested/plain.bin, bytes AIO058. |
| I02 | empty.bin; binary.bin bytes 00 FF 01; invalid-utf8.bin bytes C3 28; bom-newline.bin bytes EF BB BF 0D 0A. |
| I03 | boundary.bin with 65536 bytes 41; oversize.bin with 65537 bytes 41. |
| I04 | missing-dir/file.bin; fixtures/missing.bin; fixtures/dir (directory). |
| I05 | fixtures/file.bin:stream; C:file.bin; C:/file.bin; //server/share/file.bin; \\server\share\file.bin; \\?\C:\file.bin; \\.\pipe\aio058; CON; con.txt; COM1.txt; LPT9; fixtures/AUX.bin. All lexical/adapter rejection, no endpoint opened. |
| I06 | fixtures/plain.bin. (trailing dot); fixtures/plain.bin plus trailing U+0020; fixtures/Plain.bin against only plain.bin; case-sensitive directory containing a.bin and A.bin with exact a.bin requested; explicit 8.3 alias PLAINL~1.BIN for PlainLongName.bin; NFC caf\u00e9.bin; NFD cafe\u0301.bin; fixtures/bad<name.bin. Unicode slots use actual named code points, no backslash escape reinterpretation. |
| I10 | final-link -> outside/sentinel.bin; intermediate-link -> outside directory, both native symlinks. |
| I11 | junction -> outside directory (MOUNT_POINT tag); volume-mount directory for a second disposable local NTFS test volume (same tag, distinct mount semantics); final-file opaque custom tag 0x00000042 with GUID 05805858-0058-4058-8058-005800580058 and four-byte AIOX payload through REPARSE_GUID_DATA_BUFFER/FSCTL_SET_REPARSE_POINT, no driver/handler installed. Opaque PASS requires an actual final-component OBJ_DONT_REPARSE guard or queried reparse attribute/exact-tag rejection with zero data reads; incidental directory/native failure is insufficient. Missing volume/tag/privilege support fails gate; no tag substitution. |
| I12 | two in-root names to same file; in-root alias to outside/sentinel.bin, with retained outside sentinel handle. |
| I13 | preexisting FILE_WRITE_DATA handle; preexisting DELETE handle, each retained during reader open. |
| I14 | I14-A mapping_first, I14-A2 section_first and I14-B reader_first, three separate static records against fixtures/mapped.bin (4096 ASCII A bytes); exact native lifecycle and predicates below. |
| I16 | injected mismatched volume; mismatched FILE_ID_INFO; nondisk type; malformed metadata structure; native metadata query failure; delete-pending FileStandardInfo. Six fixed fault predicates, no device endpoint opening. |
| I17 | 16 and 17 components; 4096 and 4097 UTF16 units; one unpaired high surrogate U+D800. Underlying filesystem component/path limits may reject a lexical-boundary slot safely; it cannot change the adapter bound. |
| I18 | one injected >5-second native call (support gate failure demonstrated); one native-call error; one normal failure cleanup with handle-count return to baseline. Injected threshold-negative is expected rejection evidence, not slow real native operation PASS. |

### Revised I14 exact native proof plan — 2026-10-10

One canonical I14 case has three individually observable reader attempts,
increasing the static total by two. Section-first is necessary because a
preexisting write-capable section can supply a later MapViewOfFile without
opening a new writer. Testing only a blocked new writer would miss that route.
All three use only the exact owned fixtures/mapped.bin; no Python mmap or
incidental duplicate handle is part of the security contract. Mapping helpers
are explicit fixture control, never reader fallback or production APIs.

| Proof / static slot | Exact ordering and native operations | Required evidence |
| --- | --- | --- |
| I14-A / mapping_first | CreateFileW on owned mapped.bin with GENERIC_READ\|GENERIC_WRITE (0xC0000000), share READ\|WRITE\|DELETE (7), OPEN_EXISTING, OPEN_REPARSE_POINT; verify known file ID and 4096-byte regular fixture. CreateFileMappingW PAGE_READWRITE (4), unnamed, exact 4096 length; MapViewOfFile FILE_MAP_WRITE (2), offset 0, 4096 bytes. Write/read-back/restore one synthetic byte to verify writable live view. CloseHandle writer AND section, verifying both closures; keep and recheck the writable view before reader acquisition. Attempt one exact candidate read while the view stays live. | Actual final-component NtCreateFile STATUS_SHARING_VIOLATION (0xC0000043) / ERROR_SHARING_VIOLATION (32), matching readonly access/share/options, with zero content requests and no returned bytes. View remains live for the attempt and is verified unmapped in finally. Existing mapping-state exclusion is tested directly, not inherited source-handle sharing. |
| I14-A2 / section_first | Establish the same PAGE_READWRITE section; prove it is writable through one temporary calibration view, restore byte, then UnmapViewOfFile that view. CloseHandle writer, retain the section handle with no live view. Attempt one exact candidate read. | Same explicit final-component sharing-conflict/zero-content predicate; section handle is genuinely live and view ledger is zero at attempt. Afterward close the section and prove baseline restored. This covers write-capable section reuse before a view exists. |
| I14-B / reader_first | Positive control: exact GENERIC_READ\|GENERIC_WRITE/share7 writer-open succeeds before reader and closes. Acquire candidate final readonly handle and verify ID/type/path. At before_first_content_read, while this same handle remains live, attempt that exact writer-open; require CreateFileW error32. No writable mapping is created from that failed writer prerequisite. Separately attempt CreateFileMappingW PAGE_READWRITE on the reader's readonly handle; require access-denied5, not sharing proof. Continue exactly 4096 A bytes plus one EOF probe and final metadata from the same live protected handle; close only afterward. Positive control: same writer-open succeeds after reader closure and closes. | Cut reached, both exact incompatibility predicates observed with live reader handle, original bytes/identity returned, no content request after protection release, post-read verification before CloseHandle, and all control handles/views restored to baseline. Mapping setup is writer-prerequisite-blocked; the readonly-handle mapping check is separately labeled access rejection. |

Setup, calibration and positive controls are separately logged within their
own proof record; they add no hidden reader attempt or worker. Native API errors,
missing fixtures, access denial instead of required share32, stale/nonlive
mapping/section/reader, unverified cleanup or unexpected successful open fail
that proof. A mapping denied because of some unrelated handle or an unattempted
writer is insufficient. No file content or native address is logged.

Mapped views can persist after file/section handles close; the original source
share mask is not their protection mechanism. The documented existing writable
mapping rule and common NtCreateFile sharing contract are the candidate's
technical basis, still an inference requiring this complete future experiment.
Primary sources: [CreateFileW sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile),
[CreateFileMappingW](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-createfilemappingw),
[MapViewOfFile](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-mapviewoffile),
[UnmapViewOfFile](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-unmapviewoffile).
Any failure, including section-first allowing the reader, rejects support for
this candidate; no exception/fallback or adoption approval is manufactured.

I07 attacks root rename then replacement with an outside-directory junction;
I08 attacks the selected intermediate directory identically; I09 attacks final
rename then replacement with an outside-sentinel symlink. I15's hard-link
variant adds/removes a link from a retained zero/metadata-access handle using
native link information, and its POSIX variants use the documented POSIX
replacement flags for native link/rename information. Unsupported flags fail
the gate, no legacy-operation substitution. Those races retain outside sentinel
identity/ancestry throughout. Barrier actors must prove mutation happened or
record the precise expected share/ACL rejection; a blocked mutation is valid
evidence, an unattempted mutation is not. The six metadata fault slots supplement
the real handle/path/type checks; they do not replace native property evidence.

The scheduled injected slow/error cases establish failure handling, not a
requirement that the support test accept those faults. Uninjected operations
exceeding threshold or abnormal exits are unsupported; all prescribed negative
fixtures pass only by producing their required closed rejection. Experiment
report distinguishes expected negative outcomes from failed/inconclusive cases.

Pass requires complete all-subcase evidence plus independent Windows, Security
and Invocation/TOCTOU review; only then may the Human authorize production
adapter implementation. Failure stays in AIO-058 for bounded design remediation;
fundamentally missing native safety/hard-time requirements require an explicit
material design decision, not a guessed fallback or compulsory separate Task.

## 9. Invocation outcomes and first real effect

Private frozen outcome has status (completed, failed_before_content,
failed_after_content, ambiguous), closed reason, optional bytes only on completed
and byte_count. Reasons include effect_completed, adapter_unavailable,
containment_rejected, resource_missing, resource_changed, size_limit_exceeded,
read_failure, guard_lost, ownership_lost and effect_ambiguous. Entry failures
have their own typed category and never carry content/continuation. Diagnostic
text is bounded/nonsecret; no resource/absolute path/content/exception dump.
Target metadata/open counts as effect even when no content was read: do not
mislabel containment or missing-file probing as effect_failed_before_effect.
No durable Result schema/status column, outcome sink or complete Journal.

Crash/failed exit may mean no caller-visible outcome; future audit reports
unresolved Entry, not invented failure or success. Exactly-once invocation is
not claimed. At most one committed Entry plus at most one original compliant
adapter attempt does not imply an invocation happens or an outcome is delivered.

First later production-path test uses exactly resource fixtures/aio-058-first-read.bin
in a new nonce-owned disposable repo root, containing exactly ASCII bytes
"AIO-058 disposable nonsecret fixture\n". Test creates it specifically; expected
bytes are held in memory. Root, ledger, domain and authority fixtures are
disposable and explicitly authorized, using genuine canonical owner/JIT/Binding
composition. Exactly one permitted production-path invocation; later history
or generation attempts assert no extra invocation. No arbitrary user source,
credentials, protected target or operational repository content is used. Test
bootstrap writes/ledger operations are separate control effects, not native
reader capabilities. No such fixture is created/read in Phase 1.

## 10. Validation Safety Matrix

Human-authorized bootstrap/control commands != matrix-governed validation.
The shell used to read/write design evidence is not the designed production
Tool. "No resource read" means no authorized Run target IO; literal task/core/
implementation evidence reads are authorized investigation. Sandbox startup
failed for exec and node_repl; reviewed require_escalated literal reads worked.
No auto-review rejection occurred, and escalation did not widen Task scope.

| ID | Exact surface | Phase / rule |
| --- | --- | --- |
| B0 | Literal attachment, AGENTS instructions, .ai/project.yaml; core/principles.md, terminology.md, precedence.md, task-specification.md, human-control.md | Bootstrap governance only. |
| B1 | git branch --show-current; git rev-parse HEAD; git status --short; git diff --cached --quiet; git show -1 --format=fuller --stat a0a6930; git show -1 --format= --name-only a0a6930 | Single identified baseline commit/control; no catalog traversal, staging or commit. |
| B2 | workflows/architecture-change.yaml, standard-change.yaml; roles/architect.yaml, reviewer.yaml, security-reviewer.yaml, software-engineer.yaml; quality-gates/independent-review.md, documentation-consistency.md; schemas/task.schema.json; README.md; pyproject.toml | Literal governing evidence only; no workflow catalog or workflows/README.md. |
| B3 | Exact core ownership, admission-store, Claim/Lease, Tool-registry/resolver, operation-requirement specifications referenced above; exact AIO-057 Task's four files; exact AIO-049/AIO-051 context.md | Dependency investigation; no other catalog or target resource. |
| B4 | engineering_orchestration/_jit_execution_attempt_authorization.py, _local_dispatch_claim_lease.py, sqlite_agent_execution_dispatch_admission_store.py; _sqlite_admission_migrations/0003_dispatch_claim_lease.sql | Literal implementation evidence; no imports/execution or target IO. |
| B5 | Official Microsoft API documentation URLs | Read-only technical research; no network Tool adapter or operational service calls. |
| P1 | Literal creation/readback of exactly four AIO-058 files | Authorized Phase 1; fixed UTF-8 writes, no temp artifact or production source. |
| P2 | Fixed PowerShell ReadAllText and in-memory regex counts over acceptance-criteria.md; exact four literal file hashes/readback; git diff --check; git diff --cached --quiet | Phase-1 artifact integrity only; no imports, validator, tests or Gate substitute. |
| R1 | Seven independent design reviews of literal authorized evidence and four Task artifacts | Phase 1 authorized; no mutation by reviewers, no runtime invocation. |
| X1 | 18-case bounded native experiment above | NOT EXECUTED; separately authorize fixed prototype/dependency/fixture paths and command after safety preflight. No guessed launcher or experiment. |
| V1 | Direct Task/selected Workflow two-file schema loading | DEFERRED; exact interpreter/modules/command and direct file closure must be preflighted and authorized. No legacy validator/help or aio verify. |
| T1 | New 128-scenario tests and targeted predecessor regression | DEFERRED; exact source/tests/import fixtures and fixed module command require safety amendment before execution. No discovery. |
| M1 | Literal four-artifact Markdown check | Manual consistency now; automated lint deferred until exact pinned tool with no config/glob/discovery is approved. No npx. |
| K1 | Offline packaging/checksum compatibility | DEFERRED until exact command and declared package inputs are approved; no build/install now. |
| Q1 | Formal final Gates and Human acceptance | PENDING later implementation/final-review phases; Phase-1 reviews are design evidence only. |

Project manifest broad checks are not invoked: discover tests, Task/Workflow
validators and aggregate structural validation enumerate prohibited surfaces;
markdown glob/npx adds unknown execution. None is represented as passed or
waived. No new shell/PowerShell command becomes an authorized production Tool.
Any later validation needs a reviewed exact command and transitive IO/import
closure before execution, not authorization inferred from a check declaration.

## 11. Evidence links and design limitations

Literal dependency contracts, also within B3's read allowlist:
[ownership](../../../core/authorization-domain-ownership-specification.md),
[Claim/Lease](../../../core/agent-execution-dispatch-claim-lease-specification.md),
[Store](../../../core/agent-execution-dispatch-admission-store-specification.md).

Predecessor obligations and lock rules:
[AIO-057 context](../AIO-057-jit-execution-attempt-authorization-foundation/context.md).
Canonical native identity and no-rebind rules:
[registry contract](../../../core/agent-operation-tool-registry-and-resolver-specification.md).
Public lexical resource grammar remains
[Operation Requirement](../../../core/operation-requirement-specification.md).

Windows candidate draws on primary Microsoft documentation:
[NtCreateFile](https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-ntcreatefile)
describes handle-relative names and reparse options;
[CreateFile sharing](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
describes access/share constraints;
[GetFinalPathNameByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfinalpathnamebyhandlew)
describes handle-derived paths;
[FILE_LINK_INFORMATION](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_link_information)
limits claims about link creation access;
[ReadFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile)
and [CancelIoEx](https://learn.microsoft.com/en-us/windows/win32/api/ioapiset/nf-ioapiset-cancelioex)
do not establish a hard in-process duration/cancellation bound. The complete
handle/identity composition remains an inference requiring the experiment and
explicit native review; these references alone are not containment proof.

No prototype experiment, target metadata/open/read, production migration/code,
tests, shell Tool, Provider calls, automatic recovery or exactly-once claim is
performed in Phase 1. Review.md records actual independent verdicts and changes.

## Phase-1 completion checkpoint — 2026-10-09

All seven fresh specialist design scopes APPROVE, BLOCKER 0, HIGH 0.
Windows W-H1 is independently CLOSED; its historical rejection is retained.
128 exact scenario IDs and 24 unique predecessor mappings were mechanically
verified over literal artifacts. Four files read back without trailing
whitespace; HEAD remains baseline and index clean. Phase 1 COMPLETE.
Task remains in_progress. Next authorization is experiment X, with fixed
launcher/source/fixture paths and safety preflight; production adoption still
requires complete X evidence, independent native reviews and Human approval.
Formal final Gates and Human acceptance/closure remain pending. No commit.

## Experiment X authorization checkpoint — 2026-10-09

The Human separately authorizes the locked noncanonical containment experiment,
not production implementation. Its 18 cases, 54 static attempts and 3600 races
remain unchanged. Exactly these additional artifact paths are authorized:
experiments/aio_058_windows_containment/README.md, findings.md,
windows_containment_probe.py, race_harness.py; and
tests/test_aio_058_windows_containment_experiment.py. No other experiment artifact.

X Validation Safety Matrix amendment:

| ID | Exact command/surface | Authorization and safety |
| --- | --- | --- |
| XB0 | Fixed CPython C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe -I -B -c with sys/os/ctypes interpreter diagnostics only | Human-authorized bootstrap prerequisite; observed CPython 3.12.10, Windows, exact executable. No discovery/install or production import. |
| X0 | Same fixed interpreter -I -B experiments/aio_058_windows_containment/windows_containment_probe.py --preflight | Reviewed own source, stdlib imports only; exact local Temp parent; nonce-owned repo/outside/evidence fixtures; native filesystem metadata and mandatory symlink creation; exact cleanup. Zero static/race PASS counts. Required symlink creation failure means STOP, no elevation/fallback. |
| XA | Same fixed interpreter -I -B - with a fixed stdin ast.parse body over only windows_containment_probe.py, race_harness.py and tests/test_aio_058_windows_containment_experiment.py | Static parse only, no imports/discovery/test execution; does not prove native containment. Inline -c transport initially failed quoting; stdin correction passed before X0. |
| XM | Literal README.md/findings.md/Task evidence readback and whitespace checks | Manual Markdown verification only; no external lint/config/glob. |
| XR | Locked 54 static/3600 race runtime | Gated by mandatory fixture/native preflight; no command inferred until implementation and complete safety review. |

Exact temporary parent: C:\Users\Abdelrahman\AppData\Local\Temp. Owned roots
are fresh aio-058-containment-<32 lowercase hex> children, recorded at creation
and after cleanup. No recursively computed deletion, no directory catalog,
global process lookup, operational root/ledger or future first-effect fixture.
Only native OS DLL/stdlib dependencies and own source are loaded. pyproject.toml
was read literally to verify experiment/tests are outside all declared packages.

### Experiment X mandatory stop

Required symlink fixture creation returned WinError 1314 (required privilege
not held) on observed Windows build 26300, fixed local NTFS Temp volume. No
self-elevation, Developer Mode/account-policy change, alternate fixture or
native fallback was attempted. One recorded disposable root
C:\Users\Abdelrahman\AppData\Local\Temp\aio-058-containment-759dc60c2f784df69147e1e8fa6fcd60
was cleaned using exact known-path deletion before the probe completed. No
experiment worker child/thread was created. The fixed three-file AST check
passed after correction of its initial PowerShell quoting transport failure.

All 54 static and 3600 race attempts are NOT EXECUTED: PASS/SAFE 0, FAIL/
VIOLATION 0, SKIP/race infrastructure failure 0; one prerequisite BLOCKER,
HIGH 0. Those zeroes do not prove containment. Reviewed native strategy and
all native/type/byte/bound assertions remain unproven. The five authorized
experiment files exist but contain only prerequisite code, locked planning and
honest blocked evidence; full reader/test/race implementation remains gated.

Current Task status is blocked; Phase 1 remains COMPLETE. Experiment adoption:
CHANGES REQUIRED. Fresh post-experiment adoption reviews are not ready.
Explicit Human environment authorization is needed before resuming the
original required symlink prerequisite. Production implementation, Entry,
migration 0004 and real repository resource reads remain unauthorized.
Detailed observations and exact case accounting are in
../../../experiments/aio_058_windows_containment/findings.md.

## Bounded Phase-1 containment amendment checkpoint — 2026-10-10

The Human explicitly authorizes reopening only I14 after EXP-058-2. The earlier
mandatory-stop and Phase-1 approval checkpoints above remain historical. The
subsequent first full Human run executed 54 static attempts (52 PASS, I11/I14
FAIL) and 3600 SAFE races with zero violations/unauthorized data/bytes and full
3601/3601 worker and 1/1 root cleanup. Detailed failed-run chronology is retained
in experiment findings.md. I11 is code-remediated, still pending native proof.

Current authoritative I14 is the section 7 exclusion contract and section 8
three-slot native plan. Static total is now 56, races 3600, total 3656; historical
first-run totals are not overwritten. No broader Entry/storage/authority/Tool
architecture changes, public contract changes or future-version implementation.
Task returns to in_progress for the authorized amendment; no Task closure.

Safety amendment: exact four AIO-058 Task artifacts and five existing experiment
artifacts only. Design/experiment-document changes first; fresh read-only Windows,
Security, Invocation/TOCTOU and Architect review must all APPROVE before any
harness edits. After convergence, only the exact three experiment Python files
may be remediated and statically parsed/compiled in memory with the fixed Python
3.12 -I -B stdin body; no own source import or execution. Literal nine-file
readback/whitespace/128-ID/24-mapping checks and exact-path git diff --check/index/
HEAD checks are permitted. No catalog/discovery/validator/install/network Tool,
privilege changes, native fixture setup, elevated matrix, production code,
migration 0004, staging or commit. A later explicit authorization must run the
fresh complete final matrix before native adoption reviews/production approval.

### Amendment completion and static preflight

All four fresh design scopes APPROVE with zero BLOCKER/HIGH, before harness
remediation. The exact three experiment sources now implement I14's three
independent records and retain the strict remediated I11 guard. Independent
read-only harness review (/root/amend_harness_review): APPROVE, BLOCKER 0,
HIGH 0. Fixed stdin AST parsing/in-memory compilation and static control-path
checks PASS; no source import, fixture setup or native experiment execution.
Static accounting is 56 unique attempts, I14 three slots, 18 containment case
IDs and 3600 races. All 128 scenario IDs and 24 predecessor mappings remain.
Reader/fixture handle and view ownership, uninterrupted protected read window,
strict failure attribution, worker reaping and exact cleanup paths were
statically inspected. This proves the implementation structure only; native
I11 and I14 compatibility are still pending. Detailed hashes and evidence are
recorded in experiment findings.md and the final review.md checkpoint.

The bounded amendment and authorized harness preparation are complete. Task
status remains in_progress; production adoption, the fresh full native matrix,
adoption reviews, final Quality Gates and Human acceptance remain pending.
No required amendment review/static check failed or was skipped. STOP before
elevated execution; a later explicit authorization is required for that run.
