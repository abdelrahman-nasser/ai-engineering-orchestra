# AIO-055 Acceptance Criteria

## Phase-1 criteria

- [x] Exact requested Git baseline and absent candidate path verified without Task catalog enumeration.
- [x] Task is implementation, architecture-change, high Complexity, critical Risk, critical Execution Mode, and in_progress.
- [x] Only AIO-047, AIO-049, AIO-053, and AIO-054 are direct dependencies.
- [x] Production objective, precise Store transaction seam, minimum private keys, immutable relationship, legacy migration, ownership and retry model documented.
- [x] Fresh production outbox/migration scenario matrix and prospective Validation Safety Matrix created.
- [x] Exactly four canonical Task artifacts exist and no production path changed.
- [x] Fresh Architect, Security, Storage/Atomicity, Migration/Compatibility, and Operational Trust design reviews all APPROVE.
- [x] Zero unresolved blocker/high findings, implementation NOT STARTED, clean index, no staging or commit confirmed.
- [x] Phase 1 complete and ready for separate Phase-2 Human authorization.

Checked design criteria record documentation, not verified production behavior.

## Production acceptance (Phase 2 complete; final stage pending)

- [x] Canonical Agent Execution Dispatch Intent specification and terminology describe immutable history without execution authority.
- [x] New Admission and exactly one keys-only Intent commit in the existing AIO-047 SQLite transaction, or neither commits.
- [x] All supported operational reads/mutations and precommit verification enforce complete XOR classification and exact immutable parent relationships.
- [x] Public three-field Admission, public coordinator protocol, result/retry taxonomy and Run/Grant/Binding contracts remain unchanged.
- [x] No public Dispatch Intent value/schema or allocated dispatch_id is introduced.
- [x] Explicit checksummed forward-only migration 2 preserves exact migration-1 bytes/history and validates source prefix/fingerprint before mutation.
- [x] Empty and nonempty valid v1 migration is atomic; every historical Admission is permanently legacy non-dispatchable and zero Intents are backfilled.
- [x] Destination schema/history/fingerprint/classification is completely verified before migration commit.
- [x] Operational open rejects old/newer/dirty/partial/corrupt schema without migration or repair.
- [x] Existing AIO-049 administrative entitlement/ownership/pin and complete owned-operation lifetime are respected.
- [x] Exact new and legacy retries create nothing and retain original decision time, watermark and classification.
- [x] Commit-unknown recovery is limited to the exact same configured pinned ledger and complete immutable request.
- [x] AIO-047 watermark/currentness/revocation/conflict precedence remains unchanged.
- [x] Storage/WAL restart evidence is separate from AIO-053's process-local opaque-presentation retry limits.
- [x] All 60 locked scenarios below have fresh mapped evidence, including applicable negative/crash branches; none are inferred from AIO-054's passes.
- [x] Production tests exercise canonical Store/owned/integrated seams with audited synthetic authority and disposable exact local ledgers.
- [x] Exact migration package resources and all changed explicit package surfaces pass approved validation.
- [x] Optional smoke runs only after its dedicated safe mode and full closure have been reviewed, if needed.
- [x] No Claim/Lease, worker identity/selection, transport, consumer, invocation, Result or external effect is reachable.
- [x] Future AIO-056 seam remains internal immutable classification/dereference without mutable SQLite exposure.
- [x] Exact-path approved validation passes; every failed/skipped check is recorded honestly.
- [x] Final documentation_consistency and independent_review Quality Gates pass at the authorized final stage.
- [x] Fresh final specialist/formal review resolves all required findings.
- [x] Required Human architecture/final approval is recorded before closure.
- [x] Only then is Task status changed to completed.

## Production scenario matrix

Scenario count: **60**. These are the unchanged locked AIO-055-specific
production requirements. Phase 1 evidence was NOT RUN. Fresh Phase-2 node,
branch and durable-state evidence is mapped in review.md: **60 PASS / 0 FAIL /
0 SKIP**. O55's mandatory built-archive branch passed using the verified local
setuptools wheelhouse with no validation network. Phase 2 is COMPLETE.
Claim/Lease scenarios from the 128-scenario experiment are excluded.

| ID | Scenario | Required observable evidence |
| --- | --- | --- |
| O01 | Empty v1 migration and fresh current-v2 provisioning/reopen | Both exact paths produce complete clean v2 metadata/history; zero Admissions, markers, and Intents; full precommit and reopen audit. |
| O02 | Nonempty v1 migration | Every prior Admission has exactly one migration-2 legacy marker. |
| O03 | No historical Intent backfill | Migration creates zero Intents; exact preexisting payloads remain unchanged. |
| O04 | Atomic migration publication | Readers observe intact v1 or complete v2, never a committed partial extension. |
| O05 | Migration crash before transaction | Source v1 unchanged; no suffix/history/marker persists. |
| O06 | Migration crash after DDL | All schema, metadata, history and marker changes roll back to exact v1. |
| O07 | Migration crash after marker population | All markers and suffix objects roll back; old security history preserved. |
| O08 | Migration crash before COMMIT | Full source remains v1 with original watermark and checksum history. |
| O09 | Migration response loss | Same pinned ledger classifies complete v2 or intact v1; no duplicate history/markers. |
| O10 | Migration-1 checksum mismatch | Reject before mutation; original entry is never rewritten. |
| O11 | Migration-2 packaged checksum mismatch | Reject unsupported bytes; no source mutation. |
| O12 | Source v1 fingerprint mismatch | Reject extra/missing/altered objects before mutation. |
| O13 | Destination v2 fingerprint mismatch | Reject before successful migration commit or operational disclosure. |
| O14 | History-prefix gap/rebound/extra entry | Reject missing, reordered, changed, gapped or unrecognized migration history. |
| O15 | Unknown newer schema | Fail closed; no downgrade or automatic repair. |
| O16 | Dirty or partial schema | Fail closed; no completion-by-guessing. |
| O17 | Application/user/metadata version disagreement | Fail closed; no schema inferred from a numeric version alone. |
| O18 | Exact current-v2 administration retry | Return already_current only after full same-file v2 verification. |
| O19 | Wrong/missing administrative authority or file pin | No migration mutation; lock ownership alone is not entitlement. |
| O20 | New owned Admission | Exactly one Admission and one matching immutable Intent commit together. |
| O21 | Exact new Admission retry | Return unchanged historical Admission; create zero Intent/Admission rows. |
| O22 | Crash before Admission insertion | No new pair or positive-branch watermark becomes durable. |
| O23 | Crash after Admission before Intent | Neither half commits; retry may create the pair through existing fresh path. |
| O24 | Crash after Intent before watermark/COMMIT | Both rows and watermark update roll back. |
| O25 | Crash after watermark before COMMIT | Pair and positive-decision watermark roll back together. |
| O26 | Committed Admission response loss | Exact same-ledger retry returns original pair without a second clock sample. |
| O27 | Uncommitted Admission response ambiguity | No pair is invented; existing fresh preparation/currentness path governs retry. |
| O28 | SQLite/WAL reopen | Pair, marker history, migration metadata and watermark survive supported reopen. |
| O29 | Storage process restart | Durable history survives; exact retry needs independently valid original authentication. |
| O30 | Legacy Admission exact retry | Historical Admission returned with marker only; no Intent or clock call. |
| O31 | Missing classification | Admission with neither row yields integrity_failure without repair. |
| O32 | Intent plus marker overlap | Constraint rejects insertion; externally corrupted snapshot fails closed. |
| O33 | Orphan Intent | FK rejects insertion; corrupted snapshot audit fails closed. |
| O34 | Orphan marker | Parent/history FKs reject insertion; corrupted snapshot fails closed. |
| O35 | Duplicate Intent or duplicate marker | PK/duplicate guards reject plain/REPLACE insertion; no overwrite. |
| O36 | Wrong Admission identity | Index/payload disagreement or wrong-parent reference fails closed. |
| O37 | Run mismatch | Parent Grant/Binding/nested Run and domain/Run identity mismatch fails closed. |
| O38 | Grant-composite conflict | Existing AIO-047 full-Grant conflict precedence retained; no extra Intent. |
| O39 | Domain/ledger/instance/generation mismatch | Reject wrong configured ledger identity without switching files. |
| O40 | Immutable update/delete/rebind attempts | Intent/marker and inherited Admission relationships remain immutable. |
| O41 | Positive watermark | Pair uses one sampled decision time; equality allowed, regression rejected. |
| O42 | Temporal/revocation denial watermark | Preserve not_yet_current/expired/revoked watermark rules; no pair emitted. |
| O43 | Retry/migration watermark invariance | Exact history and migration leave watermark and historical decision time unchanged. |
| O44 | Revocation ordering and history | Prior revocation blocks new pair; later revocation preserves immutable Admission/Intent. |
| O45 | Concurrent identical Admission writers | Serialized conforming requests converge on one exact pair, no duplicate Intent. |
| O46 | Busy/storage/clock failure | Preserve typed outcomes; no partial pair, identity consumption or unauthorized watermark. |
| O47 | No Claim/Lease API | No claim_id, executor identity, Lease, Renewal, reclaim or worker selection is reachable. |
| O48 | No invocation/Result path | No transport, consumer, probe, resource read, credential, Tool invocation, Result or external effect. |
| O49 | Public compatibility | Admission fields/schema, coordinator protocol and result taxonomy unchanged; no public dispatch schema. |
| O50 | Private future seam | Only immutable Store-owned classification/dereference; no raw mutable connection or public enumerator. |
| O51 | Ownership loss around durable commit | Existing post-check fails closed; committed pair stays immutable; no live-authority claim or replacement ledger. |
| O52 | Integrated live-session retry | Same AIO-053 Producer/session/presentation returns exact Admission and creates nothing. |
| O53 | Integrated presentation lost on restart | No reconstructed historical presentation, persisted proof or cross-restart retry promise. |
| O54 | Administrative quiescence | Reject unsupported concurrent administration; WAL lock is not evidence of complete reader/process quiescence. |
| O55 | Packaged migration resources | Explicit package contains exact unchanged 0001 and checksummed 0002; no experimental imports/assets. |
| O56 | Validation target/process safety | Audited tests use owned disposable roots, bounded children/handles/timeouts and cleanup; zero protected targets. |
| O57 | Operational legacy-marker creation | Ordinary v2 paths cannot label a new Admission legacy or accept a caller classification flag. |
| O58 | Corrupt source canonical payload/revocation/watermark | Complete v1 verifier rejects before dirty mutation and preserves source evidence. |
| O59 | Missing migration marker before COMMIT | Destination completeness audit prevents commit; source rollback is intact v1. |
| O60 | Untrusted/blocked fresh prerequisites or Binding | Existing coordinator rejects before new pair; no bypass using descriptive Intent/Admission. |

Each production test record must identify its O-number, exact test node,
executed branches, observed durable state, and pass/fail/skip result.
A row covering multiple negative branches requires evidence for each named
branch; a happy-path-only run cannot satisfy it. Raw disposable storage crash
probes do not establish canonical multiprocess ownership or operational workers.
