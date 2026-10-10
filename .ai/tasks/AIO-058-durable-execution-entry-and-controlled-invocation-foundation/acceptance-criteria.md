# AIO-058 Acceptance criteria

## Phase 1 deliverables

- [x] Exactly four Task artifacts; specification-only scope and in_progress status.
- [x] Direct predecessor/source evidence inspected without search/catalog enumeration.
- [x] Private Entry identity, nine immutable fields, atomic transaction and v4 migration designed.
- [x] Permanent cross-generation exclusion and historical-only reconciliation specified.
- [x] Original continuation, guard handoff, expiry and revocation decisions specified.
- [x] Canonical first Tool, exact resource/root mapping and native candidate specified.
- [x] Required containment experiment specified inside AIO-058, not executed.
- [x] First real effect restricted to one newly created disposable nonsecret fixture.
- [x] Exactly 128 scenario obligations with E01-E24 traceability and validation matrix.
- [x] Seven fresh independent reviews APPROVE with zero BLOCKER/HIGH.
- [x] Artifact readback/count/whitespace/index checks complete.

## Later phases (not satisfied by design)

- [x] Human authorizes exact experiment paths/commands and required preflight.
- [x] All containment experiment subcases pass and three independent scopes approve adoption.
- [x] Human approves architecture and exact production/test/migration/validation scope.
- [x] 128 scenario obligations implemented and evidenced, including every aggregate subcase.
- [x] Required predecessor regression, migration/checksum/package and native read evidence pass.
- [x] One authorized canonical production-path read succeeds on the exact disposable fixture.
- [x] Formal final documentation_consistency and independent_review Gates pass.
- [x] Final Human acceptance and explicit Task closure recorded.

Experiment X checkpoint: mandatory symlink fixture preflight failed with
WinError 1314 before any of the 54 static/3600 race attempts. No required case
is marked skipped/passed. One recorded disposable root was cleaned. Task is
blocked pending explicit Human environment authorization; all runtime/adoption
criteria remain unsatisfied. Phase-1 design approval remains historical evidence.

## Locked scenario accounting

128 distinct scenarios: A10+B10+C6+D6+E10+F10+G16+H12+I18+J8+K8+L8+M6.
Rows are future acceptance obligations, not Phase-1 executed tests. Aggregated
variants require evidence for every named branch; counts refer to scenario IDs,
not unittest methods or experiment iterations. No silent skip or representative
single-subcase PASS. E references below reproduce predecessor obligations.

| ID | Scenario / all required branches | Required outcome |
| --- | --- | --- |
| A01 | First valid Entry | One immutable D row and original continuation (E01). |
| A02 | Natural ledger+D identity | No scalar Entry ID; different ledger never fallback. |
| A03 | Exact entered Claim/executor/generation | Nine fields and exact FK agree. |
| A04 | Parent complete Run/Binding | Inherit exact canonical payload, no JSON duplicate. |
| A05 | Equal duplicate insert | Reject; no second continuation. |
| A06 | Conflicting duplicate insert | Integrity/conflict; no effect. |
| A07 | UPDATE, DELETE, REPLACE, conflict-ignore | Cannot mutate/rearm/ignore into effect. |
| A08 | Entry survives success and failure | Occupancy permanent (E09). |
| A09 | Entry lookup/classification | History only; no target IO or capability. |
| A10 | Missing/v3/unavailable Entry store | No proven absence or effect (E22). |
| B01 | Single final-consumption transaction | No separate positive assessment then insert. |
| B02 | Target metadata/open/read interception before COMMIT | Zero target actions (E19). |
| B03 | Lease expires before T | No Entry/effect (E02). |
| B04 | Lease/proof expires after T before COMMIT/effect | Entered original may proceed (E03). |
| B05 | Fresh authority and issuer/principal/proof exact subject; expired consumed original Grant with valid fresh proof/Claim | Denied, unknown, stale or issuance-purpose substitution rejects; original Grant expiry alone does not veto (AIO-057 F31). |
| B06 | Actor/Runtime/Inference/applicability/compatibility/capability/permission/mode | Every malformed/blocked/unknown/mismatched branch rejects. |
| B07 | Same sample/watermark equality/regression/clock faults | One canonical sample; equal allowed; bad/regressed rejects. |
| B08 | Ownership pin/Session/Store mismatch | Reject no alternate ledger. |
| B09 | Insert plus watermark/precommit audit | One COMMIT or atomic rollback. |
| B10 | W release/C cleanup ordering | W ends at COMMIT; C never reacquires W (E20). |
| C01 | Reclaim precedes Entry writer acquisition | Old generation fenced (E06). |
| C02 | N enters; N+1 reclaim afterward | Historical N+1 allowed; no new Entry (E07). |
| C03 | Unresolved prior Entry; fresh Claim | No continuation (E08). |
| C04 | Resolved completed or failed Entry | Exclusion still permanent (E09). |
| C05 | Generation used in Entry key attempt | Reject bypass; D PK unchanged. |
| C06 | AIO-056 renewal/reclaim after Entry | Existing semantics preserved; never effect authority. |
| D01 | COMMIT unknown actually committed | No effect; exact historical reconciliation (E12). |
| D02 | COMMIT unknown actually rolled back | Terminal old cell; absence only (E11). |
| D03 | Same live stack retained after unknown | Cannot invoke even after proof of commitment. |
| D04 | Confirmed rollback after CONSUMING | No same-Claim rearm (E10). |
| D05 | Reconcile wrong pin/ledger or conflicting facts | Reject; no repair/fallback. |
| D06 | Human recovery after proven absence/occupied Entry | Fresh reclaimed Claim only for absent; new semantic Run for retry. |
| E01 | Genuine original continuation | Same Entry/cell/thread/Session/root/adapter bindings (predecessor E01). |
| E02 | Two ordinary aliases | One atomic once-state. |
| E03 | Direct construction/forged membership | Reject before target action. |
| E04 | Copy/deepcopy/pickle/serialization | Reject every branch. |
| E05 | Foreign process/thread/Session/executor/epoch | Reject every branch. |
| E06 | Already started/finished/suppressed/uncertain | No reinvocation. |
| E07 | Lost acknowledged response/continuation | History cannot replace it (predecessor E16). |
| E08 | Callback, async/deferred ticket or history replay | Reject without original protected frame (E23). |
| E09 | Guard/ownership loss before effect | Suppress; Entry persists (E18). |
| E10 | Direct adapter call bypass | No native target access without continuation. |
| F01 | Two consumers same Claim | One committed Entry/continuation (E21). |
| F02 | Two Claim generations race | One D Entry; stale Claim rejected (E21). |
| F03 | Entry vs reclaim both orders | Reclaim-first fences; Entry-first excludes next generation. |
| F04 | Entry vs renewal both orders | Authoritative renewal prefix at T; no duplicate Entry. |
| F05 | Entry vs ledger revocation both orders | Revocation-first rejects; Entry-first original remains (E04). |
| F06 | Issuer disable/re-enable vs Entry | G/P serialize; epoch no revival (E05). |
| F07 | Human withdraw/logout/policy deny vs Entry | Effective mutation-first rejects; entered-first finishes (E05). |
| F08 | Ownership close/fence vs Entry/effect | S retained; terminal loss suppresses; no deadlock. |
| F09 | Reentry/lock inversion/teardown waits | Reject unsupported integration; no earlier-lock acquisition. |
| F10 | Post-Entry expiry and revocation | No retroactive cancellation, no new Entry (E17). |
| G01 | Entry without Intent | Whole-store integrity failure. |
| G02 | Entry without Admission | Whole-store integrity failure. |
| G03 | Entry with unknown Claim | Whole-store integrity failure. |
| G04 | Entry wrong generation | Whole-store integrity failure. |
| G05 | Entry wrong executor | Whole-store integrity failure. |
| G06 | Entry mismatched D | Whole-store integrity failure. |
| G07 | Equal duplicate D corruption | Reject even identical rows. |
| G08 | Conflicting duplicate D corruption | Reject; no winner selection. |
| G09 | Malformed/noncanonical time or key disagreement | Reject every branch. |
| G10 | Schema/trigger/index/FK drift | Fingerprint/integrity reject. |
| G11 | Migration prefix/checksum/metadata drift | Reject no operational repair. |
| G12 | Entry inconsistent Claim/Renewal history | Reject gaps, overlap, wrong time/expiry. |
| G13 | Two Entries across different generations | Reject D cardinality. |
| G14 | Entry watermark exceeds/regresses stored watermark | Reject no clamp. |
| G15 | Later valid reclaim/renewal/revocation | Historical Entry audit succeeds; equal later revocation time allowed. |
| G16 | Unrelated corrupt candidate or Entry | Complete snapshot rejects; no selective skipping. |
| H01 | Empty current v4 provisioning | Full audit; zero Entry history. |
| H02 | v3->v4 | Empty Entries; preserve all existing history/watermark. |
| H03 | v2->v4 | Exact 0003/0004 atomic suffix; no backfill. |
| H04 | v1->v4 | Exact 0002/0003/0004; legacy classification retained. |
| H05 | Old/newer/dirty operational open | Reject no automatic migration. |
| H06 | Current administrative exact retry | Verify whole v4 before already_current. |
| H07 | 0001/0002/0003 bytes and checksums | Byte-exact predecessor resources. |
| H08 | Missing/corrupt/reordered 0004 checksum/history | Reject; no numeric-version trust. |
| H09 | Crash before migration COMMIT | Intact exact source. |
| H10 | Unknown migration COMMIT actually committed | Verify exact v4 same pin. |
| H11 | Unknown migration COMMIT rollback/mixed state | Intact old source explicit retry; mixed reject. |
| H12 | Quiescence/fingerprint/v3 guard upgrade | Exactly Intent/Claim/Renewal version guards; preserve history predicates. |
| I01 | Exact regular nested file | Handle-relative identity and bytes equal. |
| I02 | Empty, binary NUL, invalid UTF8, BOM/newline bytes | Exact bytes, no decoding/rewrite. |
| I03 | 65536 and 65537 bytes | Boundary succeeds; oversize zero content reads. |
| I04 | Missing intermediate/final and final directory | Typed failure; no alternate target. |
| I05 | ADS colon, drive/UNC/device/pipe spellings, reserved DOS extensions/digits | Reject without opening those endpoints. |
| I06 | Trailing dot/space, case mismatch/distinct case, 8.3 alias, Unicode variants | Exact supported spelling or reject; no normalization. |
| I07 | Root rename/replacement at four fixed cuts | Pinned trusted root; no substituted traversal. |
| I08 | Intermediate rename/reparse replacement at four cuts | Retained parent or rejection; no outside traversal. |
| I09 | Final rename/replacement at four cuts | Exact contained opened object or rejection. |
| I10 | Final/intermediate symlink | Reject both; never follow. |
| I11 | Junction/mount point/other reparse tags | Reject all available fixture tags; missing fixture blocks support. |
| I12 | Existing in-root/outside hard links | nlink!=1 rejects before data. |
| I13 | Existing write/delete access handles | Sharing conflict rejects or conflicting operation blocked. |
| I14 | Current-open write/mapping exclusion: mapping-first live view after source/section close; section-first retained writable section without view; reader-first exact incompatible writer/mapping setup | Three independently logged proofs; first two exact sharing rejection before data, third protected bounded read after share/access rejection. No atomic snapshot claim. |
| I15 | Growth/truncation/same-size write/hard-link/POSIX-link/POSIX-rename races | All six variants, four cuts, bounded repetitions; no outside content. |
| I16 | Wrong volume/file ID/type/metadata failure/delete-pending | Reject all; regular-file proof mandatory. |
| I17 | 16/17 segments, 4096/4097 UTF16 units, unpaired surrogate | Exact limits and closed failures. |
| I18 | Native-call delay/failure/handle cleanup | Threshold exceeded blocks experiment support; no fake hard timeout. |
| J01 | Exact canonical native Binding/selector/root | One private adapter path only. |
| J02 | Wrong Binding/tool/route/resource/root | Reject exact mismatch, no substitution. |
| J03 | Unavailable ABI/function/root after Entry | adapter_unavailable; occupied Entry, no data. |
| J04 | Initial size and bounded read/probe calls | <=65536 output, <=65537 physical bytes, <=17 data requests. |
| J05 | Short read/native read failure | Discard partial content, closed failure. |
| J06 | Growth/identity/type/link/size metadata change | resource_changed or size failure; no partial payload. |
| J07 | First disposable canonical production-path read | Exact named fixture bytes, one invocation only. |
| J08 | Outcome/content disclosure and diagnostics | Immutable bytes only after S exit; no content/path leaks in audit. |
| K01 | Crash before Entry insert | No Entry or effect. |
| K02 | Crash after insert before COMMIT | Atomic rollback; no effect (E13). |
| K03 | Crash after COMMIT before adapter | Occupied Entry, possibly zero effects; no restart call (E14). |
| K04 | Crash during metadata/open/read | Historical unresolved Entry; no replay. |
| K05 | Crash after effect before outcome | No re-performance (E15). |
| K06 | Post-effect ownership exit failure | Ambiguous, discard content (E24). |
| K07 | Caller outcome response lost | No replacement continuation/invocation. |
| K08 | Read-only effect appears harmless to repeat | Generic no-automatic-replay contract unchanged. |
| L01 | AIO-049 operation/pin/fence lifecycle | No public API/ownership semantics change. |
| L02 | AIO-050 issuance/authentication/authority | No parallel policy engine/public Grant change. |
| L03 | AIO-051 native v1 identity/historical route | No rebind, exact Run/Binding and retirement behavior. |
| L04 | AIO-056 selection/renewal/reclaim/history | Public eligibility and half-open Lease behavior preserved. |
| L05 | AIO-057 preparation/verify/terminal cells | Provisional behavior unchanged, new private final consumption only. |
| L06 | AIO-047/AIO-055 legacy Admission/Intent | No historical Entry/Intent backfill. |
| L07 | Public schemas/package exports | No Entry/adapter/Result/public Store widening. |
| L08 | Migration resources/package fingerprints | Exact compatibility and private 0004 packaged later only. |
| M01 | Shell/subprocess/PATH interception | Zero calls in production native adapter. |
| M02 | Provider/MCP/network/dynamic import discovery | Zero calls; missing native ABI fails closed. |
| M03 | Fallback Tool/alternate root/file/case/wildcard | Reject every attempt. |
| M04 | Target writes/Git/HTTP/package/scheduler/other adapter | No unsupported effect paths. |
| M05 | Final Result/Journal/exactly-once/replay claims | None; Entry != invocation != success. |
| M06 | Phase/validation governance boundaries | No experiment/target IO/catalog discovery/unknown validator in Phase 1. |

## AIO-057 obligation traceability

| Predecessor | AIO-058 scenario IDs |
| --- | --- |
| E01 | A01, B01, E01 |
| E02 | B03 |
| E03 | B04 |
| E04 | F05 |
| E05 | F06, F07 |
| E06 | C01 |
| E07 | C02, F03 |
| E08 | C03 |
| E09 | A08, C04 |
| E10 | D04 |
| E11 | D02, D06 |
| E12 | D01, D03 |
| E13 | K02 |
| E14 | K03 |
| E15 | K05 |
| E16 | E07, K07 |
| E17 | F10 |
| E18 | E09 |
| E19 | B02 |
| E20 | B10 |
| E21 | F01, F02 |
| E22 | A10, G01-G16, H05 |
| E23 | E08, E10 |
| E24 | K06, K08 |

## Bounded I14 Phase-1 amendment — 2026-10-10

The Human explicitly reopens Phase 1 for EXP-058-2 only. Earlier checkpoints
remain historical. The first full Human experiment executed 54 static attempts
(52 PASS, two FAIL: I11/I14) and 3600 SAFE races, with zero violations or
unauthorized data/bytes and complete worker/root cleanup. It is not adoption
PASS. I11's opaque final-file fixture and strict native reparse guard remain
required; native confirmation is still pending.

The rejected I14 mapping/reader-coexistence-and-drift model is superseded by
current-open mutual exclusion, without FILE_SHARE_WRITE or production change.
I14 now requires three independently recorded native reader attempts:
mapping_first, section_first and reader_first, as specified in context.md.
The extra section-first proof covers a retained writable section that could be
mapped without a new write-open. Static total changes 54 -> 56, I14(1) -> I14(3),
while 18 containment case IDs, 3600 races, 128 overall scenario IDs and all
E01-E24 mappings remain unchanged. Setup/calibration/cleanup controls do not
hide additional reader attempts.

- [x] Exact revised invariant, Windows access/share operations, both orderings,
  section reuse, full handle lifetime and limitations documented.
- [x] Fresh Windows Containment, Security, Invocation/TOCTOU and Architect design
  reviews all APPROVE with zero BLOCKER/HIGH.
- [x] Only after all four approvals, revise the exact experiment harness and
  statically preflight I11 and all three I14 paths, counts, cleanup and ownership.
- [x] Later separately authorized full revised 56-static/3600-race experiment
  passes, including native I11 confirmation and every I14 proof.

Atomic content snapshot REQUIRED/CLAIMED: NO/NO. Historical link provenance
REQUIRED/PROVEN: NO/NO. Link count one is only a current topology restriction.
No old race PASS substitutes for the required fresh coherent revision/run.
No elevated execution, production implementation, staging or commit is
authorized by this amendment. Final adoption Gates/Human approval remain pending.

## Final Human acceptance and closure - 2026-10-10

HUMAN APPROVAL: APPROVE. HUMAN APPROVAL DATE: 2026-10-10.
The Human explicitly accepts AIO-058 and authorizes completed Task state and
one local closure commit. All 23 existing checklist criteria are now PASS:
TOTAL 23, PASS 23, FAIL 0, NOT APPLICABLE 0. The final Human acceptance/closure
criterion is satisfied by this separate approval and canonical completed state.
Engineering criterion evidence remains in review.md's criterion reconciliation;
no validation was rerun for closure. Both required final Gates remain
2/2 PASS WITHOUT WAIVER. LOW-058-1 remains ACCEPTED - NON-BLOCKING, unfixed.

Earlier failed experiments, blockers, phase restrictions and pending statements
above remain historical. This dated closure checkpoint supersedes their current
status without deleting their evidence or changing any locked scenario.
