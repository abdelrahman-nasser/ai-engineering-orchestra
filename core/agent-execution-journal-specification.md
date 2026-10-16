# ITRU — Agent Execution Journal Specification

Version: 0.1.0

Status: ITRU-061 / SCRUM-18 Phase-1 contract explicitly Human-approved and locked
on 2026-10-14. Phase-2 drafts exist after Human-approved SA-1 sequencing remediation;
the actual static audit passed and SA-1 is resolved. On 2026-10-15 F1 passed
16 tests, then F2 had two fixture cleanup errors in 18 tests (SA-2). F3/F4 and
fresh reviews are held at Human control; production acceptance is not claimed.
Task evidence owns the validation STOP, exact receipts and next authorization.
The contract body below is unchanged; this is a documentary status update only.
This specification owns Journal semantics; the Task owns phase authorization,
exact whitelists, scenarios, validation receipts and review evidence.

## 1. Concept and ownership

The Execution Journal is durable append-only evidence of accepted observations
about controlled execution. It answers which committed Entry was observed, which
genuine terminal Result was observed, and the exact subject/authority context and
closed diagnostic explaining that observation. It is not an event-sourced Task
or Run aggregate, an executor, a lifecycle controller or a replay queue.

Core owns the provider-neutral record contract and semantic validation. A trusted
local recorder owns capture of evidence; a provisioned Journal Store owns atomic
append, record coordinates and recording time. The existing authorization ledger
continues to own Admission, Claim and permanent Entry history. Human governance
owns approval. No metadata field transfers any of those responsibilities.

## 2. Minimum facts and coverage

Exactly two event kinds are defined:

| Kind | Positive fact | Does not establish |
| --- | --- | --- |
| `entry_observed` | An exact committed Execution Entry was positively observed at the identified authoritative ledger boundary | Tool start, content request, completion, Result publication or current authority |
| `result_observed` | The trusted recorder observed one genuine immutable Result from its original producer, and retained its content-free summary | Reconstructed live Result, payload availability, Task completion or replay permission |

For a normally returned genuine Result, the recorder appends Entry and Result
facts in one Journal transaction after Result publication and all original
S/G/P/W/C scopes unwind. Entry precedes Result. If an exact Entry fact already
exists, the batch only adds the missing Result fact after subject comparison.
For an acknowledged Entry without a Result, only Entry observation is eligible.
An unacknowledged Entry commit is never fabricated from a request: only subsequent
positive audited historical lookup can establish an Entry fact.

Recording is an observation boundary after execution, not a pre-effect gate.
There is no atomic commit across the authorization ledger, native content effect,
in-memory Result publication and separate Journal. Process death can leave no
Journal facts; the ledger's Entry then supplies the reconciliation anchor. Result
loss before recording is irrecoverable in this foundation. Coverage is explicit
and may be incomplete; an empty Journal proves nothing about effects.

## 3. Identity and the closed record

The serialized Journal Entry has exactly ten fields, in this documentation order:

| Field | Meaning |
| --- | --- |
| `format_version` | Integer 1; serialized record version, separate from SQL schema/framework version |
| `journal_id` | Exact opaque nonempty administrative identity pinned to one provisioned Journal instance |
| `sequence` | Store-assigned positive 64-bit integer, unique within that Journal |
| `recorded_at` | Store-owned canonical UTC recording time with exactly six fractional digits |
| `ledger_identity` | Descriptive exact authorization domain, ledger instance and original positive domain generation |
| `execution_entry` | Exact six-field descriptive projection of the immutable Entry |
| `admission` | Exact complete existing Admission including Grant and Tool Binding with both complete nested Runs |
| `event_kind` | `entry_observed` or `result_observed` |
| `provenance` | `original_controlled_invocation` or `authoritative_entry_history` |
| `result_summary` | Null for Entry facts; closed terminal summary for Result facts |

Physical Journal event identity is `(journal_id, sequence)`. No caller event ID,
UUID, hash, timestamp-derived ID or additional Run/Result identifier is allocated.
The administrative allocator owns Journal-ID non-reuse; spelling does not prove
global uniqueness or authentic storage. The Store pins that identity and one
complete exact ledger identity, including domain_generation, at provisioning.

The fact deduplication key is `(subject_identity, event_kind)`, where:

```text
subject_identity =
(ledger_identity.ledger_instance_id,
 execution_entry.identity[0],   # authorization_domain_id
 execution_entry.identity[1],   # issuer_kind
 execution_entry.identity[2],   # issuer_id
 execution_entry.identity[3])   # grant_id
```

This is exactly ITRU-060's derived Result identity and ledger-scoped Entry
identity. Domain generation is immutable captured provenance, not a namespace
for another event of the same kind. Maximum two accepted facts per subject in
version 1. Subject identity and immutable evidence must both match.

## 4. Exact binding and authority evidence

Acceptance validates all of the following together, without normalization:

1. Ledger domain equals Entry identity domain and Admission Grant domain.
2. Entry four-part identity equals the complete Grant identity in Admission.
3. Admission Grant Run equals Admission Tool Binding Run, including run_id and
   all eleven Contract fields. Task identity is the existing contract.task_id;
   no Task catalog lookup, fabricated Task identity or persistent Task state.
4. Entry Claim ID, executor instance, generation, time and exact time key match
   the authoritative ledger's stored Entry and its audited Admission/Claim
   history. The lexical resource, environment, Runtime, operation, mode and Tool
   remain exact. Grant provenance_reference is retained opaque and never resolved.
5. For Result recording, ledger identity, Entry and Tool Binding equal the genuine
   Result's complete fields; its derived identity equals the subject key.
6. Both event kinds for a subject bind the same exact ledger generation, Entry
   and Admission. The Store rejects a Run ID rebound to a different complete
   Contract anywhere within its pinned ledger history, without creating a
   persistent Run lifecycle entity or a global Run registry.
7. Original generation is retained exactly. For historical reconciliation the
   audited ledger metadata must establish the same provisioned generation; the
   Entry row alone has no generation field. A different/missing generation makes
   reconciliation unavailable/conflicting, never a guessed replacement. This
   foundation defines no same-ledger generation transition or continuity protocol.

Admission/Grant fields are descriptive retained authority evidence, not newly
issued Grants or permission. Entry captures the exact Claim/generation reference;
no credential, authentication proof, handle, session, continuation, private
Result seal or ephemeral JIT assessment is persisted. Absence of a durable
ephemeral assessment snapshot cannot be filled with invented evidence. This
Journal explains execution within the evidence already captured, not every
unmodeled policy deliberation.

## 5. Result summary and privacy

The summary contains exactly `outcome`, `diagnostic_code` and `byte_count`:

| Outcome | diagnostic_code | byte_count |
| --- | --- | --- |
| `succeeded` | Null | Exact success count 0 through 65536 |
| `failed_before_effect` | Exact allowed ITRU-060 before-effect code | Null |
| `effect_ambiguous` | Exact allowed ITRU-060 ambiguous code | Null |

Before-effect codes: adapter_unavailable, containment_rejected, resource_missing,
resource_changed, size_limit_exceeded, read_failure, guard_lost, ownership_lost.
Ambiguous codes: the first six of that list plus effect_ambiguous. Code never
overrides outcome. Empty successful content remains succeeded with count 0.
An absent summary means no recorded Result, not a Result with absent payload.

The summary is deliberately lossy. No bytes, base64, content hash, content preview,
exception text, stack trace, OS error, absolute target path or arbitrary metadata
is retained. No Journal entry is a six-field serialized canonical Result; no live
Result deserializer is permitted. The immutable Result and its private trust
membership are unchanged by capture, append failure or later history reads.

Full Contract resource, Actor identifiers, Grant provenance_reference and byte
count can themselves be sensitive. Before enabling recording the caller must
explicitly authorize persistence and audience for this exact metadata set and
provision access-restricted storage. Execution permission alone is insufficient.
If that metadata cannot be retained, recording must be disabled/refused with an
explicit durability gap; do not redact bound identity or log sensitive failure
data through another channel. Phase 1 grants no runtime retention permission.

## 6. Provenance and trusted construction

The sole supported live Result source is ITRU-060's original native
repository_file_read chain, bound to tool::itru-native-repository-file-read::v1.
No generic producer registry or alternate route is introduced. Historical Entry
observations retain their stored Tool identity without reactivating that Tool.

For original capture the recorder must authenticate the genuine Result through
the existing passive exact-object, unchanged-state, process-local membership
check. For acknowledged Entry-only capture it must use an original trusted
coordinator observation, not a caller-populated `_EntryResult`. These checks
create historical observation evidence only, never execution authority.

`authoritative_entry_history` is permitted only for Entry observations obtained
through an audited passive lookup of the exact pinned ledger, including complete
stored subject binding. It never produces a Result fact. A copied historical
Entry cannot satisfy the original invocation provenance requirement.

The serialized provenance enum records which accepted boundary supplied the fact;
it is not authentication. Structural schema validation, matching IDs, a trusted
flag, PID, copied record or arbitrary producer argument prove no provenance.
Trusted Store consumers require the configured writer boundary and validated
pinned storage. Importing an arbitrary JSON entry into authoritative history is
unsupported. Hostile privileged writers and arbitrary code inside the trusted
interpreter remain outside this local trust model.

## 7. Append-only and idempotency

Committed entries cannot be updated, deleted, replaced, reordered or superseded.
SQL uniqueness and mutation guards must supplement writer checks; INSERT OR
IGNORE and REPLACE cannot conceal conflicts. There is no last/latest/stricter
wins rule and no correction event kind in version 1.

Append requests contain evidence facts, not caller sequence or recording time.
Under one writer transaction, first compare fact keys and complete evidence
including provenance and summary. Exact duplicates return the original entries
and coordinates unchanged, without sampling time or allocating sequence. A
differing fact with the same key produces conflict and no partial batch append.
An exact existing Entry plus a new matching Result is allowed; an orphan Result
is forbidden. A batch cannot include repeated/conflicting keys.

A historical reconciliation operation first queries existing facts and compares
the complete subject. If the Entry fact exists, it returns that unchanged fact,
including its original provenance; it does not submit a changed-provenance retry.
Only a missing Entry fact may be appended as authoritative_entry_history.
Original observation arriving later cannot replace that provenance; if its subject
matches, it may add a Result fact with original_controlled_invocation provenance.
Transport deduplication covers Journal facts only. It proves no exactly-once
execution and authorizes no new operation or invocation.

## 8. Ordering and trusted timestamps

The Journal's committed sequence is its sole total recording order. Start at 1,
allocate max+1 transactionally and preserve a contiguous sequence over committed
records; failed transactions allocate nothing visible. No SQLite rowid ordering.
Writers on the same host serialize allocation, uniqueness checks and append in
one BEGIN IMMEDIATE transaction. Entry precedes Result for each subject.
Cross-subject sequence expresses recording order, not causal execution order.
Historical reconciliation may record an old Entry after newer observations.
No global order across Journals or distributed workers is claimed.

Store samples its configured trusted UTC clock under serialization after duplicate
checks. Validate a real Gregorian instant (years 1-9999), six fractional digits,
and representability. Never use caller time, file mtime, adapter time or an
untrusted source field. Nonregression is against the last committed recorded_at
in that Journal; equal instants are allowed and sequence breaks the tie. Clock
failure/regression rejects append; no clamping, fabricated tick or alternate clock.
One atomic batch uses one sample, so its two facts share recorded_at. Reaching
the positive signed-64-bit sequence ceiling fails explicitly; it never wraps.

recorded_at is receipt time, not effect/start/completion time. Historical
Entry/Admission/Grant times retain their own original ownership. Entry time/key
coherence and Grant issued_at < expires_at are semantic checks; no new cross-clock
comparison with Journal receipt time is invented. The Journal clock is not an
authorization freshness decision and never extends an expired/revoked Grant.

## 9. Restart retrieval and reconciliation

Operational open uses only the explicitly provisioned Journal and pinned ledger
identity, including generation. It validates schema/migration fingerprints, canonical records, keys,
sequences and subject consistency in one read snapshot. Read APIs return immutable
descriptive Journal entries, not live Results or capabilities. Lookup accepts
the exact complete subject or derived subject identity in the pinned namespace;
when a full subject is supplied all bindings must match. Task/Run-ID filtering
is a convenience projection, never proof of exact binding.

Paginated traversal fixes a high-water sequence H at its initial validated read.
Every page retains `(journal_id, H, last_sequence)` and reads only last_sequence
< sequence <= H in increasing order from validated snapshots. Append-only history
makes H stable across restarts; a changed Journal identity or missing historical
prefix invalidates the cursor. New appends above H appear in a new traversal.

Explicit reconciliation compares separately audited ledger history and Journal
history without holding their locks together. Entry history is immutable; a
coherent pinned ledger snapshot supplies its exact Admission/Entry. If a safe
history read is unavailable, reconciliation reports unavailable; it never repairs
storage or reconstructs executor context. Journal facts claiming an absent or
mismatched ledger Entry cause integrity_failure, never guessed success.

| Evidence | Derived reconciliation report |
| --- | --- |
| Ledger Entry and matching Result fact | `recorded_result`, with the recorded terminal summary |
| Ledger Entry, no Result fact | `unresolved_result`, including any Entry observation; possible effect remains unresolved |
| Verified Entry absent, no Journal facts | `no_entry_evidence`; no effect/lifecycle inference or replay permission |
| Ledger query/Journal commit unresolved or unavailable | `evidence_unavailable`; absence cannot be claimed |
| Binding mismatch, orphan fact or corrupt store | `integrity_failure`; no authoritative reconciliation projection |

These reports are derived presentation, not serialized events, canonical Result
outcomes or persisted Task/Run states. Optional reconciliation may append a missing
Entry observation only; no result backfill from diagnostics, file contents, a
successful private outcome or history is allowed. Retrieving a historical summary
does not recover successful content.

## 10. Durability failures and ambiguous execution

Store append dispositions are `appended`, `existing`, `conflict`, `metadata_limit`,
`clock_failure`, `storage_unavailable`, `commit_unknown`, `integrity_failure` and
`incompatible_schema`. They are Journal durability diagnostics, never terminal
execution outcomes. A caller-facing receipt must bind its requested subject and
fact kinds and expose whether persistence was acknowledged, already present or
unresolved. Receipts are ephemeral and introduce no third durable event kind.

Before COMMIT is attempted, a positively rolled-back failure proves that batch
was not accepted. After a COMMIT attempt with no reliable acknowledgement, return
commit_unknown even if rollback is attempted; reconnect and query exact fact keys
on the same verified Journal. Presence yields unchanged existing records; verified
absence permits only resubmitting the same evidence while its trusted source is
still available. If original Result provenance was lost, only Entry history can
be reconciled. A Journal request retry must never call the Tool.

A Journal failure after a genuine Result is produced does not change, suppress,
replace or reclassify that Result, disclose its bytes, or turn it into a Journal
failure Result. The composition reports Result and durability separately. Journal
exceptions cannot flow backward into the original producer's effect mapping.
Fatal interruption preserves existing propagation; no durable report is guaranteed.

`effect_ambiguous` is recorded only from a genuine Result. Missing Result is
different: it includes fatal interruption, construction failure, failed Journal
recording and death at any boundary. It cannot be relabeled effect_ambiguous,
failed_before_effect or succeeded. Both cases forbid automatic ambiguous replay.

## 11. Schema and canonical serialization

The subordinate structural schema is schemas/agent-execution-journal-entry.schema.json,
JSON Schema draft 2020-12. It reuses the exact Admission/Grant/Binding/Run/Contract
schemas through explicit offline resource resolution. No schema catalog loader,
remote fetch, new Result schema or packaging registration is created in Phase 1.

Persisted records use canonical JSON: exact string-key dictionaries, lists,
strings, null and exact integers; bool is rejected where integers are required.
UTF-8 encoding of json.dumps with ensure_ascii=True, sort_keys=True,
separators=(',', ':'), allow_nan=False, no trailing newline or BOM. Reject duplicate
keys, floating/nonfinite numbers, malformed Unicode/unpaired surrogates, extra
fields and noncanonical encodings. No trimming, casefolding, NFC or identifier
normalization. Key order in section 3 is explanatory; canonical bytes sort keys.

Encoded record size is at most 1048576 bytes, including Store coordinates/time.
Oversize metadata refuses recording; no truncation or mutation of Result/Run
values. The schema expresses structure and closed outcome/code/count branches;
semantic validation separately owns date/key arithmetic, nested value equality,
resource/operation rules, source membership, pinned storage, version support,
size bounds and historical invariants. Passing a schema restores no authority.

## 12. Persistence and migration boundary

Decision: one separate dedicated local SQLite Journal per pinned ledger instance,
on explicitly supported local storage, with a provisioned journal_id. Same-host
serialized writers are supported by the design; remote/distributed/cloud-sync
storage, alternate-file fallback and automatic recreation are unsupported.
The existing v4 Admission ledger, immutable migrations 0001-0004, Entry rows and
watermark remain byte/semantically unchanged. There is no v5 ledger migration.

Future Journal SQL schema v1 needs metadata (identity, pinned ledger, schema and
migration fingerprint) and immutable event rows. Exact columns/indexes/triggers
and checksummed 0001 DDL will be produced/reviewed in authorized Phase 2 before
execution. Row indexes must agree with canonical payload coordinates, subject key,
event kind and time; derive next sequence from validated committed history, not
a mutable Task/Run record. No persistent lifecycle column, head state or Result
payload table is authorized. A SQL index is retrieval machinery, not lifecycle.

Durability requires SQLite >= 3.37.0 (the existing local Store floor), with verified
foreign_keys=ON, synchronous=FULL and journal_mode=WAL, atomic batch commit and
bounded connection cleanup. WAL sidecars belong to the same protected Journal
storage boundary; copying a main file alone is not a coherent backup. The precise
supported OS/storage profile, file containment,
permissions, lock acquisition and durability capability checks are Phase-2
implementation review obligations. Unsupported profiles fail, with no weakened
fallback. No experiment, database provisioning or PRAGMA execution occurs here.

Provisioning/migration is explicit administration, never operational open. A new
Journal starts empty: no synthesized old Result, inferred event or bulk backfill.
An existing Entry can be observed later with truthful history provenance and
current receipt time. A known version is read under its exact contract; unknown
record/SQL version, dirty/partial migration or missing Store fails closed.
Future migration must be forward-only, checksummed, transactional, explicit and
preserve old records/identity/order. Phase 1 defines no upgrade execution or
schema repair mechanism and no future record version is accepted speculatively.

## 13. Corruption, tamper and retention limits

Before trusted retrieval or append, validate the complete pinned Journal snapshot:
known metadata/schema, migration manifest, sequence continuity, canonical payloads,
unique fact keys, index agreement, Entry-before-Result and consistent full subjects.
Orphan/malformed/duplicate/rebound evidence blocks authoritative retrieval and
append with integrity_failure. No partial clean prefix is reported as complete
history, no automatic repair, row skipping, conflict resolution or target replay.
An administrative forensic read, if separately authorized later, is not trusted
history and belongs outside this foundation.

Database guards, fingerprints and access controls detect modeled structural
corruption and ordinary writer misuse. No signatures, hash chain, external
checkpoint or cryptographic authenticity is claimed. A privileged attacker can
substitute a coherent old Journal copy, alter a complete consistent history or
copy its identity. Such tampering/rollback may be undetectable. This local trust
limit must accompany any claim of authoritative history. Journal content never
overrides the independently authoritative ledger and never authorizes effects.

Version 1 retains accepted entries indefinitely, with no TTL, pruning, compaction,
rotation, deletion, redaction or same-identity restore/reactivation. Exhaustion
reports storage failure; it does not drop history. Backup/export is descriptive
only and no backup, restore or cross-Journal continuity mechanism is implemented
or authorized here. A future retention or migration policy requires Human
authorization and a separately reviewed continuity/privacy contract.

## 14. Authority of history and ITRU-062 boundary

Within validated pinned storage and the stated writer/threat boundary, Journal
facts are authoritative history of what those boundaries accepted as observed.
They are not derived from mutable Task status or UI. Displays, filtered views and
reconciliation reports are derived presentation and must retain coordinates,
provenance, exact subject and evidence gaps. The Journal is not the sole source
of truth for Entry/authority and cannot prove universal coverage or effects.

ITRU-062 may later derive evidence-only views: exact recorded terminal summaries,
entries without recorded Results, recording chronology, Task/Run grouping from
existing bindings, and explicit unresolved/unavailable/conflicting evidence.
It must not infer Task completion, an authoritative Run lifecycle transition,
pending/running/cancelled states, new authority, payload recovery, retry eligibility,
budget/cost, scheduling or automatic resume. Persistent Task/Run lifecycle state
requires its own approved ownership, transition, concurrency and reconciliation
contract; Journal v1 supplies evidence rather than that contract.

Replay means read/reduce historical observations for presentation only. No event
invokes a Tool, recreates a continuation, reconsumes a Grant or repeats an effect.
No exactly-once claim. A new operation must obtain its own separately governed
occurrence and authority; even failed_before_effect does not reopen a permanent
Entry. Persistent Task/Run state, resume implementation, DAG/scheduler,
retry/failover policy, budget/cost, adaptive routing, UI and distributed workers
remain explicitly deferred.
