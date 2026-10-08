# AIO-056 Acceptance Criteria and Production Scenario Matrix

## Phase-1 checkpoint

- [x] Verify main/authoritative HEAD, initial clean worktree/index, and exact candidate absence.
- [x] Read exact authorized sources; use no catalog enumeration or recursive search.
- [x] Create exactly the four requested Task artifacts and no implementation.
- [x] Resolve all nineteen design questions in context.md.
- [x] Preserve dispatch composite identity; require no dispatch_id.
- [x] Specify Claim/Executor identities, generation, clock, half-open Lease, retry and reclaim.
- [x] Specify minimal private owned composition with unchanged AIO-049 semantics/API.
- [x] Design explicit 0003, preserving byte-exact 0001/0002 and public Admission/Intent contracts.
- [x] Lock corruption, crash, concurrency, packaging and validation safety expectations.
- [x] Define all 112 individually identifiable production scenarios below.
- [x] Five fresh design scopes APPROVE with zero unresolved BLOCKER/HIGH findings.
- [x] Final bounded Task-format/documentation checks pass; worktree changes are exactly four Task artifacts and index stays clean.

Phase-1 checkboxes do not close the production Task. Review and mechanical
evidence must be recorded in review.md before design convergence is reported.

## Production acceptance through Phase 2

- [x] Human explicitly authorizes Phase 2 under the converged design.
- [x] Implement only the approved private Store/adapter/migration/specification/test file plan.
- [x] Stable migration-3 checksum, prefix manifest IDs and v3 DDL fingerprint are computed and pinned from actual reviewed bytes.
- [x] All 112 scenarios pass, with a per-ID exact test-node and executed-branch evidence map.
- [x] No required branch is inferred from a scenario name, another lane, or predecessor evidence.
- [x] Explicit v1/v2-to-v3 migration and fresh-v3 provisioning retain all parent history and watermark.
- [x] 0001/0002 hashes remain baseline-exact in source and built package.
- [x] Canonical owned-session entry and exit cover every private operation without AIO-049 source/API changes.
- [x] Fresh worker capabilities cannot restore another incarnation or gain authority from equal values.
- [x] Claim/Renewal history is immutable and every fresh progress path is generation fenced.
- [x] Clock/watermark failures and generation/sequence/time exhaustion fail closed.
- [x] Exact retries and both commit-unknown branches reconcile the original same-ledger operation without duplicate extension/history.
- [x] Every crash cut in context.md executes; precommit rollback and postcommit response loss are distinguished.
- [x] Complete-snapshot corruption checks reject all listed malformed histories without repair.
- [x] Both required serial race orders execute; raw multiprocess storage probes remain distinct from canonical operation evidence.
- [x] Existing Admission, atomic Intent, legacy retry, conflict and integrated presentation contracts regress cleanly.
- [x] Offline package archive contains exact new private module/0003 and excludes experiments/tests/Tasks.
- [x] Every validation command passes fresh static safety preflight; no unknown validator, help probing, discovery or protected target.
- [x] Owned disposable probes use finite waits, handle-specific reaping, and nonce/realpath-contained cleanup.
- [x] No invocation, command/resource execution, transport, Result, scheduler or worker launch API exists.
- [x] Report every failed/skipped validation and its acceptance consequence.
- [x] Separately authorized final specialist/Formal Independent Review and documentation_consistency/independent_review Gates pass.
- [x] Required Human architecture/final approval and explicit Task closure are recorded.

## Locked scenario matrix

Exactly **112 production scenario identities**, C001 through C112. Each will
have an individually selected unittest method in the planned exact module
`tests/test_dispatch_claim_lease_foundation.py`. Multiple branches within one
row are all mandatory subcases, individually reported. Phase 1 designs these
tests; it creates and executes none. Raw storage and canonical owned-session
lanes must be labeled separately. Baseline test passes are historical evidence,
not fresh AIO-056 results.

| ID | Scenario and mandatory expected evidence |
| --- | --- |
| C001 | Fresh v3 provisioning/reopen: exact clean schema/history, empty Claim/Renewal/Intent/legacy sets, unchanged public construction. |
| C002 | Empty v2 -> v3: exact append-only migration 3, no backfill, identity/watermark preserved. |
| C003 | Nonempty v2 -> v3: Intents and legacy markers, including revoked parents, preserved byte-exact; zero Claims/Renewals. |
| C004 | Empty v1 -> v3 in one transaction: exact 0002 then 0003, clean contiguous history. |
| C005 | Nonempty v1 -> v3: every pre-v2 Admission remains legacy only; zero historical Intents/Claims/Renewals. |
| C006 | Valid v2 source XOR audit: missing classification/overlap rejects before dirty mutation despite latest version 3. |
| C007 | Replaced Intent insert guard: new v3 Admission atomically inserts Intent; dirty/fenced/wrong-version insertion rejects. |
| C008 | 0001/0002 source bytes and history-prefix IDs/checksums remain exact; changed bytes reject. |
| C009 | Stable migration-3 resource checksum/manifest/v3 fingerprint agreement; each mismatch rejects. |
| C010 | Operational open of valid v1/v2 rejects without migration or changed files/history. |
| C011 | Unknown older/newer version, app/user/metadata version contradiction rejects. |
| C012 | Missing/extra/reordered/rebound migration history or dirty/partial state rejects with no repair. |
| C013 | Migration crash before transaction and after dirty transition: intact original v1 and v2 sources. |
| C014 | Migration crash after tables/trigger replacement and before publication: original complete DDL restored. |
| C015 | Migration crash after history/metadata publication and before COMMIT: intact original source; no partial v3. |
| C016 | Migration after COMMIT response loss and explicit committed/uncommitted ambiguity: only same-pinned-source retry or verified v3 already_current. |
| C017 | Current-v3 explicit migration retry: full verified already_current, exact snapshot invariant. |
| C018 | Missing/wrong admin entitlement, wrong physical pin, terminal domain rejects before migration mutation. |
| C019 | Canonical admin quiescence: live owner/active operation blocks; WAL reader demonstrates EXCLUSIVE alone is insufficient. |
| C020 | Source parent/payload/revocation/watermark corruption and destination DDL drift: fail closed and preserve source. |
| C021 | First owned Claim selects actual Intent, generation 1, initial expiry now + D, one immutable row/watermark. |
| C022 | Admission time ordering and equal-time BINARY composite tie-break among many Intents. |
| C023 | Empty Intent set: no time sample/history/watermark; legacy-only parents never selected. |
| C024 | All candidate parents revoked: untimed authority_ineligible, no Claim/watermark. |
| C025 | Mixed revoked/active/pending/reclaimable candidates: first eligible ordered candidate selected without fairness claim. |
| C026 | All unrevoked candidates active: temporarily_unavailable, sampled watermark only, attempt ID unconsumed. |
| C027 | Exact Claim retry after expiry/supersession/revocation: original history, zero clock/watermark, no new generation. |
| C028 | Reused committed claim_id with another executor: conflict, zero mutation and no unauthorized current evidence. |
| C029 | No-row attempt later explicitly reevaluates: may select current first eligible Intent, one eventual committed row. |
| C030 | Invalid token grammar/types/capability/look-alike/serialized request rejects before database progress. |
| C031 | Claim requests expose no target/time/duration/generation/Run/Tool override or ownership bool. |
| C032 | Exact expiry reclaim: fresh claim_id, generation 2, predecessor immutable; before expiry cannot displace it. |
| C033 | Multiple reclaim cycles/restarts: contiguous 1..N, no generation rollback or reuse. |
| C034 | Reuse of predecessor committed claim_id returns old history only; fresh reclaim needs new ID. |
| C035 | Generation MAX exhaustion: fail closed without wrapping/reservation/watermark/skipping selected Intent. |
| C036 | Same executor attempts fresh Claim on its unexpired Intent: cannot displace ownership. |
| C037 | Already-consumed Grant interval elapsed: Claim follows locked ledger/revocation policy, supplies no JIT authority. |
| C038 | Wrong bound domain/instance/domain generation/file pin: reject before selection, no ledger fallback. |
| C039 | Positive Renewal binds exact Claim/dispatch/executor/generation, sequence 1 and expiry now + D. |
| C040 | Multiple positive Renewals: contiguous sequences, strictly increasing effective expiry, immutable predecessors. |
| C041 | Exact renewal_id retry at later time: original row/expiry, zero clock/watermark or double extension. |
| C042 | Exact Renewal history after supersession/revocation/expiry: historical disclosure only. |
| C043 | Renewal ID rebound for each claim/composite/executor/generation field: conflict, no mutation. |
| C044 | Missing Claim and fresh mismatched Claim tuple: typed rejection, no row or watermark. |
| C045 | Fresh old-generation Renewal after reclaim: stale_generation before time/watermark mutation. |
| C046 | Fresh highest-Claim Renewal at expiry and after expiry: expired_claim, sampled watermark only, no revival. |
| C047 | Same sampled time as Claim/previous Renewal: nonextending; ID and sequence remain unconsumed. |
| C048 | No-row nonextending request later succeeds once with its original ID; no receipt/retry stacking. |
| C049 | Renewal time advanced: expiry uses now + D, never old expiry + D. |
| C050 | Revocation-first blocks fresh Renewal without mutating history; Renewal-first then revoke preserves row. |
| C051 | Sequence MAX exhaustion: no overflow or partial history/watermark; generation MAX can renew if sequence permits. |
| C052 | Exact request from wrong live executor/new incarnation rejects; knowing stored ID is insufficient. |
| C053 | Request grammar, bool/non-int generation and malformed token/renewal values reject without coercion. |
| C054 | Renewal accepts no caller timestamp/extension/sequence/duration/authority override. |
| C055 | Positive/equal watermark samples valid in Claim, Renewal and fresh current query. |
| C056 | Below-watermark Claim/Renewal/current query rejects without clamping/history/watermark. |
| C057 | Throwing clock in each of the three timed operations: fresh failure path executes; later valid attempt succeeds. |
| C058 | Wrong type, naive, non-UTC and lossy clock values reject in each timed operation. |
| C059 | Large forward jump: expire -> reclaim -> old-generation rejection -> new-generation Renewal -> later rollback rejection. |
| C060 | Time addition outside datetime/signed-64 range: no history, generation/sequence, or watermark mutation. |
| C061 | Fixed canonical microsecond text/key exactness, leap/calendar boundary and equal-time handling. |
| C062 | Shared Admission/revocation/Claim/Renewal/current-query watermark interleaving; audit decisions rather than future expiry. |
| C063 | Half-open interval: before acquisition, just before expiry, exact expiry and after expiry. |
| C064 | Historical Claim/Renewal query and exact retry under failing clock: history only, zero sample/mutation. |
| C065 | Timed negative watermark-only decision commit ambiguity: no durable denial receipt or exact-negative-response promise. |
| C066 | UTC/watermark/history survive process and WAL restart; no process-monotonic lease recovery. |
| C067 | Claim without Intent, Claim against legacy parent, and missing parent classification: full audit failure. |
| C068 | Renewal without Claim: restrictive FK rejects and corrupted snapshot audit fails. |
| C069 | Each mismatched dispatch-composite field on Claim/Renewal: FK or audit failure, no repair. |
| C070 | Renewal mismatched claim_id/executor_instance_id/generation: exact composite FK and snapshot audit. |
| C071 | Duplicate operation IDs with exact/conflicting fields; duplicate dispatch generation and claim sequence: reject INSERT/REPLACE. |
| C072 | Claim/Renewal UPDATE/DELETE/rebind attempts: unconditional immutable guards, every column protected. |
| C073 | Generation zero/negative/bool/overflow/type errors, regression, missing first generation and illegal jump reject. |
| C074 | Renewal sequence zero/negative/overflow/regression/gap/duplicate rejects. |
| C075 | Overlapping active generations: next acquisition before prior complete effective expiry fails audit. |
| C076 | Renewal after supersession, at/after prior expiry, or invalid decision ordering rejects full history. |
| C077 | Nonextending/incorrect D/expiry arithmetic and time-key disagreement rejects stored rows. |
| C078 | Malformed calendar/canonical timestamp/ID/token/issuer vocabulary in persisted records: integrity_failure. |
| C079 | Watermark behind each durable Claim/Renewal decision rejects; watermark before future expiry remains valid. |
| C080 | Corrupt unrelated candidate or historical chain cannot be skipped during selection/disclosure. |
| C081 | Complete stored Grant/Run/Binding index/payload mismatch on dereference rejects without weakening equality. |
| C082 | Schema extra/missing index/trigger/table, mismatched migration bytes/history, dirty operational state rejects. |
| C083 | Revocation payload/completeness/domain corruption rejects; equal-time Claim-first/revoke-later remains valid history. |
| C084 | Injection-like identity text is bound as data, not SQL; unknown query mode/request result shape rejects. |
| C085 | Claim crash all six cuts: before transaction, selection, insert, watermark, before COMMIT, after COMMIT response loss. |
| C086 | Renewal crash all six cuts: before transaction, validation, insert, watermark, before COMMIT, after COMMIT response loss. |
| C087 | Reclaim crash all five cuts: expired baseline, allocation, insert, before COMMIT, after COMMIT response loss. |
| C088 | Claim commit_unknown did-commit branch: same-ID reconciliation returns exact original generation/expiry; claim_id-only history recovers unknown automatically selected dispatch tuple. |
| C089 | Claim commit_unknown did-not-commit branch: intact no-row state reevaluates current eligibility without reserving generation. |
| C090 | Renewal commit_unknown did-commit branch: one row/sequence, exact return never extends twice. |
| C091 | Renewal commit_unknown did-not-commit branch: no-row reevaluation observes later reclaim/expiry/revocation. |
| C092 | Crash while SQLite writer lock held: child reaped, lock releases, no partial row/watermark, later writer succeeds. |
| C093 | WAL checkpoint/reopen preserves Claim, every Renewal, effective expiry, generation, migration state and watermark. |
| C094 | Same-ledger no-row/corrupt/mixed reconciliation cases: never repair, switch path or silently mint another ID. |
| C095 | Pre-entry ownership loss and post-COMMIT post-check failure: no current evidence; respectively zero or committed history. |
| C096 | Worker/process restart after lost Claim response: new capability/ID, claim_id-only old history query even when tuple unknown, fresh reclaim after expiry. |
| C097 | Two logical workers claim one Intent: exactly one generation/current owner; loser active-unavailable. |
| C098 | Claim vs Renewal: both writer orders; active predecessor extension vs fresh expired selection observed correctly. |
| C099 | Renewal vs exact-expiry reclaim: both allowed serialized clock histories; no renewal revival or overlap. |
| C100 | Two reclaimers: one N+1, loser cannot allocate N+2 while N+1 active. |
| C101 | Exact retry racing fresh Claim/reclaim/Renewal: exact original history and one fresh serialized mutation. |
| C102 | Two identical Claim attempts and two identical Renewal attempts: one new result plus exact history, no duplicates. |
| C103 | Busy timeout/transient unavailable: typed result, no ID/generation/sequence consumed, later exact reevaluation. |
| C104 | Raw multiprocess contention lane and many ordered Intents: storage guarantees proven without multiprocess operational-worker claim. |
| C105 | Genuine canonical operation lease spans facade request/Store/result/post-check; concurrent logical operations/close quiescence preserved. |
| C106 | Counterfeit/copy/pickle/forked-process/restored-ID capabilities and fake owned sessions rejected; no raw mutable Store escapes facade. |
| C107 | Closed/lost/fencing/fenced sessions cannot operate or reanimate; new session never resumes old worker identity. |
| C108 | Current query checks exact highest live tuple, effective expiry, revocation/time/watermark; history mode conveys no current authority. |
| C109 | AIO-055 full exact compatibility plus public Admission/protocol/outcomes/schema/exports unchanged; atomic new pair and legacy historical retry retained. |
| C110 | AIO-053 same-live-presentation path and lost-on-restart boundary unchanged; no authentication reconstructed from Claim history. |
| C111 | Offline built-package exact resources/module/checksums/history and full declared surface; no experiments/tests/Tasks/public Claim schemas or packaging declaration changes. |
| C112 | Validation/process closure and no invocation paths: all owned crash probes/timeouts reaped, contained roots cleaned, no discovery/catalog/network/protected target/resource/Tool/transport/Result launch. |

## Evidence discipline

All seventeen crash rows in context.md map to C085/C086/C087 subcases, not
merely a generic exception test. C088-C091 additionally require explicit
commit-ambiguity branches. C059 and C066/C093 require the complete forward-jump
and restart chains, not only an opening or clock assertion. C057 must actually
throw on each timed path. C109 requires all 60 AIO-055 scenario identities
with fresh compatibility evidence; predecessor success is not a substitute.
Every failed or skipped required scenario keeps production acceptance open.

MAX generation/sequence arithmetic cannot be exercised by fabricating an
otherwise invalid gapped history and calling that an exhaustion pass. C035/C051
must cover the actual signed-64 arithmetic boundary directly with production
private arithmetic helpers, and a separately labeled test-only lowered limit
through a short valid contiguous transactional chain to verify no-mutation
handling. Neither lowered-limit evidence nor raw snapshot mocking claims that
9223372036854775807 durable rows were created. No public limit override is added.
