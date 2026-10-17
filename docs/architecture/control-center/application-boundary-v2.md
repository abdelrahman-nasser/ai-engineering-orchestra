# ITRU Core Application Boundary Design v2

**Filename:** `ITRU_Core_Application_Boundary_Design_v2.md`  
**Date:** 17 October 2026  
**Status:** NEW consolidated candidate specification; NOT an authoritative replacement  
**Authority:** Human approval pending; implementation planning has not begun  
**Transport:** Unselected  
**Implementation authorization:** None

## Executive summary

The first real integration is a content-free inspection of one explicitly selected existing Run. It exposes exactly `InspectRun` and `ReadRunJournal`. Core supplies lifecycle facts, the complete Task dependency graph and scheduler assessment; the Control Center formats those observations without acquiring operational authority.

The lifecycle query must use an already-established Core owner and owner-managed passive resources. The existing operational store constructor performs recovery and cannot be used as a query shortcut. Passive read resources, mutation/shutdown exclusion, lifetime leases and bounded query admission are new proposed Core integration facilities, not existing APIs.

Journal traversal freezes a high-water sequence, advances across matching and nonmatching records and reports completeness explicitly. It preserves full Contract, Binding, Result and ledger identities, content-free summaries, and any disagreement with the separate lifecycle observation. No historical payload or live Result can be reconstructed.

The complete Investigation and reconciliation addendum have been reconciled with current source. Preserved decisions are listed separately from P01–P10, which are **NEW UNAPPROVED proposals**. Concrete fields, references, limits, errors and UI mappings require Human approval. Transport, authentication mechanism, operational source/dataset and metadata audience remain unselected. All operational controls stay disabled; first-slice continuation eligibility stays unassessed.

This deliverable is a design specification and static review record. It does not begin implementation planning, authorize implementation, establish runtime acceptance, or claim formal Quality Gate PASS.

## 1. Purpose and authority

This document re-baselines the Core application boundary for one content-free, read-only existing-Run inspection slice. It is a new candidate, not a recovered copy or reconstruction of the missing original Core Application Boundary Design. The original is not an input or an outstanding recovery request.

The preserved decisions in section 3 come from the current Human instruction and the supplied reconciled direction, which the Human confirms was approved for planning on 17 October 2026. Existing implementation facts are identified separately. Every additional application mechanism, field, limit and policy in sections 5–14 is a **NEW PROPOSAL requiring Human approval**, even when motivated by an existing Core primitive. “Must” in those sections means a requirement of this candidate if approved; it does not assert an earlier approval. Repeated A01–A12 constraints retain their preserved status.

The candidate does not authorize repository changes, source selection, operational-store access, tests, runtime processes, transport selection, control activation or implementation. Approval of this document would establish the replacement design only within the explicitly approved scope. It would not itself authorize implementation or finalize the implementation plan.

## 2. Evidence and limitations

| Evidence | Actual use and limitations |
| --- | --- |
| Current Human re-baselining instruction | Authoritative for the preserved decisions and current scope restrictions. It does not approve the new details below. |
| `ITRU_Core_UI_Boundary_Investigation.txt`, dated 17 October 2026 | Complete text read. The supplied attachment matches the previously inspected copy. SHA-256: `1f736d4c0158c6781627b3abd9b95979b4f1279c92d270773d163f7e9cc12596`. Inventory, gaps and semantic constraints were used; its proposals remain proposals. |
| `ITRU_Core_Application_Boundary_Reconciliation_Addendum.md` | Complete supplied text read, 47 lines. SHA-256: `8d816aefda08b9542cb448eca467c3fde3d32bf081ec2cfb52caae4f7b380d94`. Its ownership, query, identity, traversal, observation and five UI corrections are incorporated. Its `UNAPPROVED` heading records its status when written. |
| Current Human clarification | The reconciled direction was subsequently Human-approved for planning on 17 October 2026. This establishes that direction’s planning status; it does not approve v2, its newly proposed fields/mechanisms/budgets, or implementation. |
| Core checkout | `D:\Dev\ai-engineering-orchestra`, HEAD `e7af2c4c01645a05e6e78ccea7e845dafc455399`; static source/specification review. Working tree unchanged. |
| Active UI checkout | `D:\Dev\itru-ui`, HEAD `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67`; static UI review. Existing untracked readiness document preserved. Its claims do not override current Core. |
| Documented Human-approved release decisions | [Decisions & Evidence, Confluence version 31](https://abdelrahmann-hegab.atlassian.net/wiki/spaces/ITRU/pages/458753/Decisions+Evidence): CLI-only Alpha; active UI baseline; parked SCRUM-81 isolation; action-specific authorization. Historical approvals do not authorize this integration. |
| Supporting reference | [Results, Journal & State, version 2](https://abdelrahmann-hegab.atlassian.net/wiki/spaces/ITRU/pages/753666/Results+Journal+State). Repository semantic contracts/source govern technical details. Confluence Markdown conversion is lossy for macros/dates, so missing converted dates are not inferred. |

The supplied files are located in:

`C:\Users\Abdelrahman\Downloads\ITRU_Architecture_Design_Inputs (1)\`

No operational dataset was opened. Its existence, integrity, volume and suitability for the proposed budget are unknown. No current test-pass, runtime safety, deployment readiness or end-to-end integration claim follows from static source verification.

The earlier missing-addendum evidence hold is resolved by reading the supplied complete text and reconciling this candidate. No original design recovery is required. The addendum’s account of historical architecture/safety approvals is limited to the design packet, supplied final-text excerpts, the complete Investigation and targeted static source checks; it is not a review of this v2 specification or executable integration. Fresh v2 reviews are recorded separately in section 16.

## 3. Preserved Human decisions

| ID | Preserved decision |
| --- | --- |
| A01 | The lifecycle reader is Core-owned. It introduces no competing ownership and no read-triggered recovery. |
| A02 | The first slice exposes exactly two semantic queries: `InspectRun` and `ReadRunJournal`. |
| A03 | Lifecycle, Task dependency DAG and scheduling decisions remain authoritative in Core. |
| A04 | Complete Contract, Binding, physical Result and ledger identity are preserved exactly. |
| A05 | Journal traversal has a stable high-water boundary and explicit completeness. |
| A06 | Lifecycle and Journal are independent observations; disagreement remains visible. |
| A07 | Evidence is content-free. Historical payload recovery is excluded. |
| A08 | There are no execution, approval, cancellation or continuation commands. |
| A09 | Transport remains unselected. |
| A10 | Existing UI operational controls remain disabled. |
| A11 | First-slice continuation eligibility remains unassessed. Interrupted or ambiguous history must never appear eligible or available. |
| A12 | `configuredRoute` is omitted or unavailable unless separately supplied by an approved mapping; it is not canonical Binding data. |

The documented CLI-only Alpha and parked SCRUM-81 decisions remain applicable. Neither parked code transfer nor release-scope expansion is implied.

## 4. Reconciliation corrections and verified implementation facts

These correct assumptions; they do not supply unobserved approval text. Their proposed application/UI treatment is specified later.

| Correction | Verified meaning |
| --- | --- |
| `configuredRoute` | Not a third canonical Binding field. Binding is exactly `{run, tool_id}`. The registry route is the exact Contract-derived tuple `(runtime_option_id, environment_id, operation_id)`. A UI route label neither proves current registry configuration nor grants authority. |
| Run ordering | Persisted `TaskSnapshot.runs` preserves registration order; its final item identifies the latest registered Run for that Task. Store Run pages are separately ordered lexically by opaque `run_id`. ID order, filtered array order and Journal recording times do not establish Run recency. There is no verified global chronological Run list. |
| Interrupted continuation | `continuation_eligible` rejects a Task with any unfinished, `interrupted` or `effect_ambiguous` Run. Fresh approval does not override interrupted uncertainty. The addendum imposes the stricter first-slice rule: eligibility remains unassessed and no continuation operation is exposed. |
| Integrity badges | Core performs schema, identity, sequence and semantic validation. It does not establish cryptographic signatures, universal tamper resistance, rollback detection, no effects, execution success or evidence completeness merely by validating a page. |
| Unavailable approval counts | No supported persistent pending-approval queue backs this slice. Unavailable approval information is not zero pending approvals or an all-clear state. |

Other relevant facts:

- Constructing `SqliteTaskRunStateStore` acquires exclusive ownership, opens read/write and performs recovery. Existing `get_task`, `get_run` and `page` paths do not constitute an approved passive reader.
- Core already implements lifecycle, continuation eligibility, DAG validation and deterministic scheduling. Stale UI comments do not make those capabilities absent.
- Only persisted Task `completed` satisfies a dependency. Run success does not complete a Task. Scheduler selection reserves nothing and authorizes nothing.
- Journal page cursors contain `(journal_id, high_water, last_sequence)`. Existing Alpha history recaptures high water across calls and is not the proposed frozen application traversal.
- Existing Journal page validation scans the whole current Journal; an output record limit does not bound validation work.
- Lifecycle/Journal reconciliation is diagnostic, not recovery. In particular, Core can report `recorded_result` while lifecycle remains `interrupted`; this must not become a unified success state.

## 5. P01 — Core ownership and mutation coordination — NEW PROPOSAL

Core provides a distinct recovery-free lifecycle read port. It does not expose SQLite, filesystem handles or private capability objects to the UI. It must not construct another lifecycle owner, call the existing operational constructor as a query shortcut, take over a lock, provision, migrate, enroll, recover or repair.

For this slice, the read port operates through an already-established sole Core mutation owner and its already-established, owner-managed passive read connection. The connection is recovery-free and read-only; its establishment belongs to separately authorized owner setup, not query handling. A query does not independently open lifecycle storage or establish another ownership session. Owner startup/recovery, if independently authorized, must finish before query admission and must never be caused by a query. If a suitable owner, passive connection or coordination boundary is unavailable, return an explicit unavailable/busy error. Query-triggered reconnection and cold-owner passive access are not proposed for this slice.

The current owner has a read/write connection, recovery-on-open behavior and `BEGIN IMMEDIATE` operations. It does not already implement this passive read session, lease protocol, writer priority or query deadline contract. Those facilities are proposed prerequisites. Existing CLI startup or `open_state` cannot be invoked to make an owner available for a UI read.

The owner supplies one coordination boundary covering **every lifecycle mutation and shutdown** in the configured scheduling domain, including enrollment, registration, start, Result acceptance, transitions, continuation, recovery, close and loss of ownership. Query capture takes a bounded owner-lifetime lease and read exclusion; mutations require exclusive access. A waiting mutation or shutdown has priority: no later reader may enter ahead of it. Read capture has the bounded hold time in P07 and must abort/release on deadline or owner loss. Process topology and synchronization implementation remain unselected. A logical guard that some writers or shutdown paths bypass does not satisfy this contract.

Under that exclusion and lease, the owner uses its established passive connection to begin a recovery-free read-only snapshot transaction, validates the complete lifecycle store and its event reduction, captures the full domain and computes Core scheduling over the captured immutable values. No first-slice continuation eligibility assessment is performed. Snapshot capture, definition/graph pinning and evaluation have one coherent revision set. Release exclusion and the lease before Journal traversal or delivery. Any owner loss, identity change or coordination failure invalidates the entire lifecycle observation.

Shutdown first marks the owner closing and bars new lifecycle query admission. Existing captures must complete or be safely aborted within their capture deadline; shutdown waits for their leases to release before closing storage resources. It never closes a handle beneath an active reader. If bounded cancellation/drain cannot be guaranteed, the read port is not admitted. Once closed/lost, the owner cannot supply a new lifecycle observation. Already completed immutable inspections retain their original meaning for separate Journal observation until expiration; actual application/context loss makes their references expire. No query restarts the owner to satisfy a shutdown race.

The new read path preserves the semantic validation guarantees of the existing store without reusing its write transaction/recovery behavior. No clean prefix or best-effort lifecycle result is usable after integrity failure. Failure must not trigger recovery, fallback direct SQL, or a second owner.

No transaction is promised across lifecycle, Journal, authorization ledger and native effects. The read boundary does not open the operational authorization ledger: Journal ledger identity is compared with the pinned source and lifecycle subject, not presented as a fresh ledger observation.

Journal reads likewise use Core-managed, established read resources with an independent resource-lifetime lease. Closing those resources bars new reads, safely drains/aborts active transactions, and releases handles only after their leases end. A query never provisions, migrates, recovers or repairs a Journal. Journal-resource unavailability is reported independently of lifecycle-owner availability.

## 6. P02 — Source and identity — NEW PROPOSAL

A Human-approved, trusted configuration registers one immutable source revision. Client input identifies that revision by opaque `source_id` and `source_revision`; neither is a path, endpoint, credential or bearer capability.

The private descriptor contains:

| Field | Required semantics |
| --- | --- |
| `source_id`, `source_revision` | Exact identifiers for one registered configuration revision. Never silently repoint a revision. |
| `project_id`, `store_id` | Expected lifecycle scope, independently verified against the actual snapshot. |
| `journal_id` | Expected Journal identity; verified by the Journal query, not asserted as observed by `InspectRun`. |
| `ledger_identity` | Exact `{authorization_domain_id, ledger_instance_id, domain_generation}` expected for this slice. |
| `definition_set_reference` | Immutable identity for the explicit Alpha work/definition set. No inferred join to repository `task.yaml`. |
| `graph_reference` | Immutable identity for the complete graph and capacity domain. |
| `max_concurrency` | Trusted configured value. Existing Alpha permits one or two advisory workers; this slice does not expand that limit. |
| `metadata_policy_reference`, `budget_profile_reference` | Exact approved policies for delivery audience and resource limits. |

Filesystem configuration remains private to Core. UI-supplied paths, directory traversal, store auto-discovery and cross-source ID lookup are rejected. The first slice uses one explicit Alpha source whose complete capacity domain is its configured Task set, including disconnected Tasks. Extra lifecycle Tasks outside that graph are a domain mismatch; missing graph Task observations produce Core `incomplete_snapshot`, never fabricated selection.

The application locator is `(source_id, source_revision, project_id, store_id, run_id)` and resolves to the unchanged complete Core Run/Binding and ledger subject. This adds namespace context without redefining Core Run identity `{run_id, contract}`. Exact identifiers are case-sensitive opaque text: no trimming, case folding, Unicode normalization, path normalization or alias replacement. Source identity mismatch is an error, not a substitute source.

The eleven Contract fields are exactly:

```text
task_id, workflow_id, stage_id, role_id, actor_id,
runtime_option_id, option_id, environment_id,
operation_id, resource, execution_mode
```

Canonical Binding remains exactly `{run: {run_id, contract}, tool_id}`. Ledger identity preserves all three fields, including generation. Physical Result identity remains exactly `(ledger_instance_id, authorization_domain_id, issuer_kind, issuer_id, grant_id)`; no replacement `result_id` is introduced.

A new source, definition set, graph, ledger generation or storage identity requires a new source revision and new inspection/traversal. A UI route containing only a Run ID cannot establish scope.

## 7. P03 — Metadata audience and retention — NEW PROPOSAL

Both queries require an independently authenticated read principal and explicit entitlement to the **whole metadata set** of this slice. Authentication mechanism is deferred with transport selection. No delivery may begin until that mechanism and audience configuration are approved. Source IDs, observation references, approval digests and UI `authorityId` fields confer no entitlement.

Approval covers full graph-domain Task IDs and definition references; complete Run/Contract/Binding and ledger identity; lifecycle revisions and Run history; Journal Entry/Admission/Grant provenance; issuer/Actor identifiers, lexical resources, timestamps, diagnostics and byte counts. These can be sensitive despite being content-free. Existing execution permission is insufficient.

Authorize before disclosing whether a source/Run exists, reauthorize every page, and recheck policy revision. Changed/revoked policy invalidates retained observations and cursors. If the principal cannot receive complete bound identity, withhold the observation. Do not redact identity and still describe the resulting object as exact evidence. Authorization to display the entire scheduling domain is a prerequisite; silently trimming it would change the scheduling question.

Recheck entitlement and policy revision before publishing a successful response. A detected principal, policy or source-context change invalidates the bound Core references and clears the corresponding UI display/cache references; `access_denied` must never retain the subject as stale readable data. Historical display after ordinary busy/unavailable refresh failure is allowed only for the same principal with continuing entitlement. This requires reference removal, not a claim of secure physical-memory erasure.

Excluded response/retention fields include payload bytes, previews, text/hex samples, source-content hashes, serialized live Results, arbitrary exception text, command output, diffs, review notes, credentials, session proofs, physical storage paths and full configuration. Historical payload status is always `unavailable_not_retained`. No payload-recovery fallback exists.

Only bounded in-memory descriptive observations/cursors may be retained for query composition. No browser persistent/offline cache, analytics payload, export or additional durable metadata retention is authorized by this slice. Error/audit logging must not copy source metadata. Loss of the in-memory query context causes explicit expiration, not reconstruction from untrusted client state.

## 8. P04 — Application value conventions and query contracts — NEW PROPOSAL

The application owns descriptive projections; UI models remain UI-owned. These are proposed semantic fields, not an implemented API or a transport selection. All objects below are closed for application version `1.0`; unknown fields and enum values are errors. Required nullable fields use explicit null; omission is reserved for fields explicitly called optional. Canonical Core records are validated before projection. A projection containing decimal strings is not canonical persisted Core JSON and must never be accepted as an original Result, trusted capability or live authority artifact.

All unbounded/64-bit integers, revisions, sequences, generations, counts and numeric time keys cross this boundary as canonical decimal strings: `0` or a nonzero digit followed by digits, with no sign or leading zero. Core validates each underlying range; boolean is not an integer. Bounded request `limit`, `format_version` and configured concurrency use exact small integers. No JavaScript `number` round-trip is permitted for lossless fields.

Preserve existing timestamp text exactly. Grant `issued_at`/`expires_at` permit no fraction or 1–6 fractional digits; do not pad, normalize or reformat them. Journal `recorded_at`, Entry `entry_time`, Admission `decision_time` and new response receipt/expiry timestamps use canonical UTC strings with six fractional digits. Recording/receipt time is not Tool execution time. Core-held monotonic elapsed time controls expiry, deadlines and charged active time; displayed UTC times and client clocks cannot extend a reference’s lifetime.

Every request contains `application_version`, `source_id`, `source_revision`. Operation identity is exactly `InspectRun` or `ReadRunJournal`; there is no generic operation dispatcher. Every success contains `outcome: ok`, those three request fields, Core-generated `request_id`, `received_at`, `completed_at`, and all operation-specific fields below. Failures use the separate shape in section 12. Request IDs and receipt times provide correlation, not authority or freshness guarantees. There is no polling, subscription, enumeration or command operation in this contract.

### 8.1 `InspectRun`

Additional request field: exact `run_id`.

| Success field | Meaning |
| --- | --- |
| `inspection_ref`, `expires_at` | Opaque reference to this immutable Core-produced inspection, retained under P07 limits and bound to principal, policy, source/version and exact subject. It is descriptive context, never bearer authority. |
| `source_observation` | Exactly `{project_id, store_id, definition_set_reference, graph_reference, metadata_policy_reference, budget_profile_reference, observed_at, expected_journal_id, expected_ledger_identity}`. Store/project and lifecycle subject are verified by this query; Journal identity is only a configured expectation until separately observed. |
| `lifecycle` | `task_id`, `definition_reference`, `task_state`, `task_revision`, `run_state`, `run_revision`, exact `binding`, exact observed `ledger_identity`, nullable `accepted_result_identity`. |
| `task_run_history` | Exactly `{entries, order: registration_order, latest_run_id, complete: true}`. Entries are complete registration-ordered summaries `{run_id, state, revision, accepted_result_identity}`. Scoped to this Task/store; no timestamps or global recency invented. Target existence means this history is nonempty and `latest_run_id` names its final entry. |
| `definition_metadata` | `{status: unavailable, reason: not_in_first_slice}`. Rich title/risk/complexity/scope/approval metadata is not inferred from Alpha work. The exact definition reference is available above. |
| `graph` | Exact Core `TaskGraph`: nodes `{task_id, definition_reference}`, dependencies `{task_id, prerequisite_task_id}`, canonical `topological_order`. Edge `(A,B)` means A waits for B. |
| `scheduling` | Core decision `state`, configured `max_concurrency`, `occupied_run_ids`, per-Task evaluations, `selected_task_ids`, and `snapshot_coverage` below. Selection is advisory evidence only. |
| `continuation` | Exactly `{eligibility: unassessed, action_available: false}` for every Run. The read path does not call `continuation_eligible`, prepare continuation intent or compute an availability boolean. |
| `payload` | `{status: unavailable_not_retained}`. |

`scheduling` is exactly `{state, max_concurrency, occupied_run_ids, evaluations, selected_task_ids, snapshot_coverage}`. Each evaluation is `{task_id, state, dependencies: {task_id, state, unsatisfied_task_ids}}`.

`snapshot_coverage` is exactly `{expected_task_ids, observed_tasks, missing_task_ids}`; each observed entry is `{task_id, definition_reference, state, revision}`. Arrays retain Core canonical order; missing IDs are exact and sorted. Captured complete Run histories remain Core-internal for the evaluator; response size limits must not cause a smaller evaluation domain. These are Task dependency evaluations, not Workflow Stage facts.

Canonical vocabularies are preserved:

- Task: `planned`, `in_progress`, `blocked`, `completed`, `cancelled`.
- Run: `pending`, `running`, `succeeded`, `failed_before_effect`, `effect_ambiguous`, `interrupted`, `cancelled`.
- Scheduler decision: `evaluated`, `incomplete_snapshot`, `over_capacity`.
- Task evaluation: `unresolved`, `unsafe`, `terminal`, `active`, `manual`, `blocked`, `ready`.
- Dependency evaluation: `ready`, `blocked`, `unresolved`.

The targeted Run must exist in a fully validated lifecycle snapshot. Not found is returned only after authorized successful inspection of that source. Missing graph observations are a valid Core incomplete decision with no selection. Invalid graph, definition mismatch, extra domain Tasks or invalid snapshots are errors with no partial scheduling result.

This query does not read the Journal. A lifecycle accepted Result identity is lifecycle evidence, not proof that a Journal summary exists. Retained inspections are immutable; reading the Journal later never refreshes their lifecycle state silently.

### 8.2 `ReadRunJournal`

Additional request fields:

- `inspection_ref`.
- Optional `limit`: exact integer in `1..100`, default 50.
- Optional `cursor`: absent starts a new traversal.

Resolve the inspection from Core-owned memory, check its principal/policy/source/version binding and use its exact Binding/ledger subject. A client-created snapshot is not accepted as an authoritative inspection. No live lifecycle reread is required: Journal observation remains usable against the explicitly dated inspection even if the lifecycle owner later becomes unavailable. Expiration instead requires a new inspection, not an invented equivalent reference.

| Success field | Meaning |
| --- | --- |
| `inspection_ref`, `subject` | `subject` is exactly `{binding, ledger_identity, accepted_result_identity}` from the retained inspection; identifies the historical lifecycle observation being compared. |
| `journal_observation` | Exactly `{journal_id, ledger_identity, started_at, completed_at, current_high_water, validation_scope: whole_current_snapshot_semantic_validation, ledger_observation: not_performed}`. The current snapshot may extend beyond frozen traversal `H`. |
| `records` | This page’s complete matching Core Journal records, with exact identities/Entry/Admission/Grant/provenance fields and lossless numeric representation; content-free summary only. No live Result capability is reconstructed. |
| `traversal` | `high_water`, `last_scanned_sequence`, cumulative `scanned_count`, cumulative `matched_count`, `complete`, `stop_reason`, nullable `next_cursor`, `expires_at`. |
| `comparison` | Lifecycle state/revision at inspection, comparison coverage, nullable Core reconciliation result and explicit discrepancies as defined in section 10. |
| `payload` | `{status: unavailable_not_retained}`. |

### 8.3 Complete nested Journal projection

The following lists all nested fields. Strings preserve exact Core values; integer projection follows the lossless rules above. A record remains descriptive evidence even when it contains a historical Grant or Admission.

| Value | Exact fields |
| --- | --- |
| Journal record | `{format_version: 1, journal_id, sequence, recorded_at, ledger_identity, execution_entry, admission, event_kind, provenance, result_summary}`. |
| Ledger identity | `{authorization_domain_id, ledger_instance_id, domain_generation}`. Generation remains separate from physical Result identity. |
| Execution Entry | `{identity, claim_id, executor_instance_id, lease_generation, entry_time, entry_time_key}`. `identity` is the ordered tuple `[authorization_domain_id, issuer_kind, issuer_id, grant_id]`. |
| Admission | `{grant, tool_binding, decision_time}`. |
| Grant | `{grant_id, run, authorization_domain_id, issuer_kind, issuer_id, provenance_reference, issued_at, expires_at}`. |
| Run | `{run_id, contract}`. |
| Tool Binding | `{run, tool_id}`. |
| Contract | Exactly the eleven fields in section 6. |
| Result summary | Null for Entry observations; otherwise `{outcome, diagnostic_code, byte_count}` with required nullable fields. |

Journal event kinds are exactly `entry_observed` and `result_observed`. Provenance is `original_controlled_invocation` or `authoritative_entry_history`; Result observations require the former. Issuer kind is exactly `human` or `policy`.

Claim/executor IDs are exact 64-character lowercase hexadecimal identifiers. Sequences and lease generations are positive and at most `9223372036854775807`; Entry time keys are in `0..315537897599999999` and must exactly agree with Entry calendar time. Domain generation is a positive Core integer; no narrower application range is invented.

Core validation must establish:

- Grant Run equals Binding Run.
- Entry’s four-part identity equals the Grant’s domain/issuer/Grant tuple.
- Ledger domain equals Entry domain.
- `issued_at <= decision_time < expires_at`.
- Admission time does not exceed Entry time.
- Every observation of the same physical subject has identical bound Entry/Admission/ledger data.
- A Result observation has its corresponding prior Entry observation.

Physical Result identity is exactly `(ledger_instance_id, *execution_entry.identity)`.

Summary semantics:

| Outcome | Diagnostic / byte count |
| --- | --- |
| `succeeded` | Null diagnostic; decimal-string count `0..65536`, including `0` for an empty successful read. |
| `failed_before_effect` | Null count; diagnostic exactly one of `adapter_unavailable`, `containment_rejected`, `resource_missing`, `resource_changed`, `size_limit_exceeded`, `read_failure`, `guard_lost`, `ownership_lost`. |
| `effect_ambiguous` | Null count; diagnostic exactly one of `adapter_unavailable`, `containment_rejected`, `resource_missing`, `resource_changed`, `size_limit_exceeded`, `read_failure`, `effect_ambiguous`. |

There is no payload, arbitrary diagnostic message, signature, digest or extra evidence field. Nested provenance text is retained only under the approved exact-metadata audience; it is never dereferenced. If an exact field cannot be safely delivered under that policy, withhold the observation rather than rewrite it.

## 9. P05 — Stable traversal, exact matching and completeness — NEW PROPOSAL

On the first Journal page, validate the whole current Journal snapshot, independently verify its configured identity and ledger generation, and capture its high water `H`. Empty Journal means `H=0`. The selected records are those at sequences `1..H`; later appends are outside this traversal.

The opaque cursor is a Core-held, integrity-protected reference binding application version, principal/policy revision, source revision, inspection/exact subject, Journal/ledger identities, fixed `H`, global scan position and cumulative comparison state. It is not an execution capability. Foreign, altered, expired or inconsistent cursors fail explicitly. Never restart silently or raise `H` under the same traversal.

Repeating a valid cursor/limit yields the same logical page provided its context and source identity remain valid and whole-current-snapshot validation, admission and budgets still pass; later growth/corruption can produce an explicit error instead. Receipt times may differ. A changed limit is permitted within the cap but advances from the same scan position.

Inspection references and cursors are opaque Core-held references, not client-supplied serialized state. Binding mismatches fail without revealing a foreign reference. Missing cursor starts a new traversal but shares the same inspection-level charged-work budget; it cannot reset that budget. Replays, branches and failed admitted attempts also share that budget. Logical scan/match counters describe frozen-prefix coverage and are distinct from cumulative charged work.

Walk increasing **global** sequences. Advance the scan position over nonmatching records as well as matches. Stop before consuming a matching record that would exceed the requested output count; do not skip it. An empty filtered page can have a continuation cursor.

`complete=true` is allowed only when every sequence through `H` has been scanned after successful validation. Then `next_cursor=null` and `stop_reason=high_water_reached`. Otherwise `complete=false`, a valid next cursor is required, and `stop_reason` is `page_limit` or `scan_limit`.

Matching requires the complete exact Run/Contract/Binding and ledger identity. If lifecycle supplies a physical Result identity, preserve it in the comparison; it is not permission to hide other physical subjects for the same complete Run subject. Detect Run-ID reuse with a different Binding/ledger in the scoped source as an identity mismatch. Detect multiple physical Entry/Result subjects for the exact Run as a reported conflict; never choose the newest summary.

The five-part physical identity groups Entry/Result evidence. Full Entry/Admission/Binding equality is checked within each group. No Run-ID-only join, fuzzy matching or latest-wins resolution is permitted. Existing exact-subject lookup can assist, but cannot replace coverage of the frozen traversal where competing subjects might exist.

Revalidate the whole current Journal snapshot on each page with existing semantic guarantees. This may include newly appended records beyond `H`; those records do not enter the traversal, but any integrity failure invalidates that request. A shortened/replaced Journal or a high water that cannot be honored invalidates continuation. Semantic validation cannot prove absence of a coherent rewrite/rollback under unchanged IDs; no stronger authenticity claim is made.

**“Complete with no matching records” means only no matching recorded evidence in this Journal at this `H`.** It never establishes no Entry, no invocation, no native effect, no lost Result or no evidence elsewhere. Partial traversal, timeout, budget failure and unavailable Journal never establish absence.

## 10. P06 — Independent observations and disagreement — NEW PROPOSAL

`InspectRun` produces a lifecycle observation; `ReadRunJournal` produces a later independent Journal observation against that retained inspection. Neither claims a cross-store transaction, current liveness or a common execution timestamp. The UI always identifies the two observation scopes/times separately.

`comparison` is exactly:

```text
{
  lifecycle_state_at_inspection,
  lifecycle_revision_at_inspection,
  coverage,
  core_reconciliation,
  discrepancies
}
```

Coverage is exactly `partial` or `complete`; discrepancy codes form a deterministically sorted unique array.

While traversal is incomplete:

- `coverage=partial`.
- `core_reconciliation=null`.
- Final absence/agreement/subject-uniqueness claims are suppressed.
- Already observed multiple subjects or conflicting outcomes may be displayed as provisional positive findings.

Once complete, Core applies its diagnostic reconciliation to the full exact matching set and returns `coverage=complete` and:

```text
core_reconciliation = {
  state,
  lifecycle_state,
  recorded_outcome
}
```

This preserves the helper’s unchanged fields and state: `missing`, `entry_only`, `recorded_result`, `conflict`, `inconsistent`.

The recorded outcome is null or exactly `succeeded`, `failed_before_effect`, `effect_ambiguous`; null is not a synthesized Result. `lifecycle_revision_at_inspection` is the inspected Run revision, not the owning Task revision; both remain available from the inspection.

The application additionally reports a set of explicit discrepancy codes:

- `journal_result_without_lifecycle_acceptance`
- `lifecycle_result_without_journal_result`
- `different_outcomes`
- `different_result_identity`
- `multiple_physical_subjects`
- `state_inconsistent_with_recorded_evidence`

These are comparisons, not new lifecycle states. They are computed in Core over the retained inspection and validated traversal; they cannot mutate either source.

| Observations | Required presentation |
| --- | --- |
| Lifecycle `interrupted`; Journal success | Show both. Mark Journal Result without lifecycle acceptance, even if the helper says `recorded_result`. Run remains interrupted. Continuation is unavailable and first-slice eligibility remains unassessed; it never appears eligible. |
| Lifecycle success; complete Journal without Result | Show accepted lifecycle success and missing recorded Journal Result separately. No payload recovery or automatic repair. |
| Journal Entry only | Entry observed; completion/effect outcome unproven. |
| Multiple physical subjects/different outcomes | Show conflict and all observed subjects within limits. No chosen winner or merged Result. |
| Journal unavailable or validation fails | Preserve the separate lifecycle panel with its original observation time; evidence panel shows the specific failure. No clean prefix or empty-success replacement. |
| Lifecycle owner unavailable before inspection | No invented lifecycle result. This contract cannot create a new inspection; an unexpired prior inspection may still support a separately authorized Journal query. |

No observation restores original Result membership, authorization proofs, ownership, ability to retry, or permission to continue.

## 11. P07 — Bounded work and retention profile — NEW PROPOSAL

The following are concrete candidate limits, not historical decisions or measured capacity. Human must approve or revise this entire profile. They do not raise existing Core maxima.

| Resource | Candidate limit |
| --- | --- |
| Query admission | At most 1 active query per source, 1 per principal, and 2 application-wide; no pending application-query queue. Admit after authorization and before validation/materialization. Reject excess with `source_busy`; never silently queue or evict a live query. |
| Request envelope | At most 16 KiB encoded input, before parsing into an application request. |
| Graph | Existing Core maximum 1,000 Tasks / 10,000 dependencies; configured Alpha input may be smaller. |
| Lifecycle validation | At most 10,000 events and 16 MiB aggregate encoded metadata; preserve existing per-event 1 MiB cap. |
| Journal validation per request | At most 10,000 current records and 16 MiB aggregate encoded metadata, including records beyond pinned `H`; existing per-record 1 MiB cap remains. |
| Journal scan per page | At most 1,000 global records after validation, independently of 50 default / 100 maximum returned matches. |
| Response | At most 2 MiB encoded descriptive metadata, including envelope and complete identities. |
| Database preflight | At most 64 MiB per current database file, checked before database-wide validation such as `quick_check`; no sidecar/provisioning fallback. |
| Active working memory | At most 64 MiB per query / 128 MiB application-wide, including decoded structures, validation, comparison and encoding buffers; separate from the bounded retained context below. |
| Coordination wait | At most 1 second. |
| Lifecycle capture hold | At most 1 second of owner-lifetime lease and mutation exclusion, inside the whole-query deadline; waiting writers/shutdown bar new readers. Deadline abort releases both and returns no lifecycle prefix. Shutdown drains/aborts captures before resource close within this bound. |
| Whole query | At most 10 seconds including wait, validation, evaluation and encoding; this is a work deadline, not a latency SLA. |
| Retained context | Inspection/cursors expire 15 minutes after inspection creation, without sliding extension; at most 8 live inspections per principal/source and 64 application-wide, with at most 2 MiB retained descriptive state per inspection including its traversal/comparison state. |
| Traversal contexts | At most 2 live traversals per inspection; all cursor branches, replay records and accumulated comparisons count within its 2 MiB retained-state cap. |
| Cumulative Journal attempts | At most 128 admitted page attempts per inspection, including first pages, cursor replay, branches and failed attempts across both traversals. |
| Cumulative Journal validation | At most 1,000,000 validated records and 256 MiB encoded source metadata per inspection, including repeated full-snapshot validation and records beyond `H`. |
| Cumulative Journal output | At most 64 MiB encoded response metadata per inspection, including replayed successful pages. |
| Cumulative Journal active time | At most 120 seconds charged active query time per inspection, including admitted failed attempts; elapsed-time counters are Core-held and cannot be reset by a new cursor. |

Limits apply before unbounded materialization. Validation scans must count bytes/rows incrementally, use bounded reads, and support deadline interruption, including database-wide checks. Admission and bounded allocation account for simultaneously active queries; per-request limits alone are insufficient.

Existing whole-store validation routines do not already prove compliance; a future implementation must show bounded behavior without weakening semantic validation. If the selected runtime cannot enforce interruption, memory admission and prompt exclusion release, it cannot serve this proposed profile.

Source metadata bytes mean the existing canonical UTF-8 Core record bytes. For transport-neutral request/response quota accounting, measure UTF-8 bytes of a deterministic logical JSON representation:

- Keys sorted by Unicode scalar-value order.
- No optional whitespace.
- Exact strings without normalization.
- Decimal-string integers as specified above.
- Booleans/null in their standard lowercase spelling.
- Bounded small integers in ordinary decimal form.
- No floats/non-finite values.
- Escape quotes/backslashes and use the standard short escapes for backspace, form feed, newline, carriage return and tab.
- Encode other ASCII controls as lowercase `\u00xx`.
- Leave other ASCII, including solidus, unescaped.
- Escape all non-ASCII as lowercase `\uxxxx`, using a UTF-16 surrogate pair for a supplementary scalar.
- Reject unpaired surrogates.

This is a quota reference encoding only, not a selection of delivery encoding or transport. Delivery overhead needs separate limits when a transport is independently considered.

Whole-snapshot validation, identity or deadline failure returns an error with **no usable records/prefix from that request**. A scan limit after successful whole-snapshot validation returns an ordinary incomplete page and cursor. If a complete identity, record, graph or response cannot fit, return `metadata_limit`; never truncate identities, drop graph nodes or omit records while advancing a cursor. No empty-progress cursor is returned for an oversized next record.

Reference pressure produces `context_limit` for new inspections/traversals; it does not silently evict a live reference. Expired references may be removed. Per-request raw work is not retained beyond completion; retained metadata stays inside the explicit in-memory budget.

A later page may fail validation budgets after Journal growth beyond `H`; that failure means unavailable continuation, not a completed traversal. Retrying a read is explicit and bounded; no internal retry loop is implied.

Charge attempted work across all cursor branches and both traversals before admitting work that would exceed a known remaining allowance; increment byte/row/time counters as work occurs. Failed requests do not refund consumed work. Cumulative exhaustion returns `work_budget_exceeded` without records or a new scan position. It cannot establish completeness, absence or uniqueness.

A conforming dataset may be unable to finish under this candidate profile, especially with tiny requested pages or repeated full-store verification. That limitation requires explicit presentation and Human budget review, never relaxed validation or a silently smaller `H`.

## 12. P08 — Versions and errors — NEW PROPOSAL

Document version `v2` identifies this candidate. Application version `1.0` separately identifies the proposed projection contract. Neither changes framework `0.1.0`, Core record `format_version`, SQLite schema versions or release versions. Nested record versions are retained and independently validated.

Requests require an exact supported application version. Unsupported versions/enums/closed fields fail; there is no silent downgrade or field dropping. A contract change requires a new explicit application version and compatibility review. Cursor/inspection versions cannot be mixed. Storage incompatibility never triggers migration through a query.

Error shape is exactly:

```text
{
  outcome: error,
  application_version,
  request_id,
  received_at,
  completed_at,
  error: {
    code,
    component,
    retry_advice,
    safe_message
  }
}
```

The error envelope uses supported application version `1.0`, including when rejecting an unsupported requested version.

`component` is `request`, `source`, `lifecycle`, `journal` or `context`.

`retry_advice` is `do_not_retry`, `retry_query_later` or `restart_inspection`.

`safe_message` comes from fixed public text, never raw exceptions. No failed response includes records, success fields or a usable component prefix. A prior successful independent observation remains explicitly historical.

| Public code | Meaning / treatment |
| --- | --- |
| `invalid_request` | Invalid type, range, duplicate/unknown field, malformed selector. |
| `unsupported_version` | Application version unsupported; no fallback. |
| `access_denied` | Authentication/entitlement absent or revoked. Does not reveal target existence. |
| `source_unavailable` | Unknown/unconfigured source or inaccessible source, normalized to avoid enumeration. |
| `source_revision_changed` | Exact source revision cannot be served; new inspection required. |
| `run_not_found` | Authorized, validated lifecycle source has no exact requested Run. |
| `source_busy` | Immediate query-admission cap rejection or coordination wait expiry; query may be retried later. |
| `owner_unavailable` | Established lifecycle owner/passive resources/coordination absent, closing or lost. No takeover. |
| `identity_mismatch` | Store/project/ledger/Binding/definition/graph domain mismatch. Withhold affected observation. |
| `incompatible_source_version` | Unsupported storage/event format; no migration. |
| `integrity_failure` | Any complete-snapshot integrity failure. No clean prefix. |
| `metadata_limit` | Complete field/record/response exceeds allowed encoded size. |
| `work_budget_exceeded` | Per-request or cumulative inspection validation, attempt, output or active-work budget exhausted. |
| `deadline_exceeded` | Query budget elapsed before a valid response. |
| `inspection_expired` | Inspection missing/expired after context loss; restart inspection. |
| `invalid_cursor` | Altered, foreign or inconsistent cursor; no automatic reset. |
| `cursor_expired` | Cursor context expired; restart inspection/traversal. |
| `context_limit` | Retained-state admission would exceed the approved limit. |
| `internal_error` | Sanitized unexpected read-path failure; no success substitution. |

Check envelope/version first, authenticate and authorize next, then resolve source and validate identities before data access. Unsupported source versions map before generic integrity failure. Core store-busy errors map to busy; incompatible schemas to incompatible-source-version; integrity errors to integrity failure; metadata caps to metadata limit. Unexpected write/commit paths are internal failures and violate this reader contract; no command is repeated or recovery attempted.

Retry advice is fixed by error category:

- `source_busy`, `owner_unavailable` and `deadline_exceeded` use `retry_query_later`.
- `inspection_expired`, `cursor_expired` and `source_revision_changed` use `restart_inspection`.
- All other codes use `do_not_retry`.

In particular, the normalized `source_unavailable` uses the same advice for both unknown/unconfigured and inaccessible sources so it does not reveal the hidden cause. Source configuration/access must be checked outside this query contract. No advice triggers an automatic retry. Access checks are repeated on every new request.

## 13. P09 — UI mapping — NEW PROPOSAL

The first slice connects only an explicitly selected existing Run detail and its Task-dependency/scheduler and Journal panels. Source/Run selection is provided out of band; no Run catalog or source enumeration query is added. The nine existing mock data-source methods do not expand this two-query application contract.

| UI area | Required mapping |
| --- | --- |
| Data seam | Adapt Core projections into UI models after strict validation. No generic adapter that assumes every mock field exists. Live source identity is always visible; mock and observed facts are never mixed in one operational claim. |
| Run/Task badges | Retain canonical underlying Task and Run values separately; display scheduler evaluation separately. `interrupted`, missing evidence and `effect_ambiguous` remain distinct. |
| Run history/latest | Use `task_run_history` and explicit `latest_run_id`. Filters and sort changes cannot redefine latest. No global “recent Runs” claim. |
| `configuredRoute` | Omit the field/display or show unavailable. Do not fabricate a route label from Contract, registry assumptions or mock values. The three exact route components remain visible as ordinary Contract fields. A separately approved mapping would be future scope. |
| Continuation | Display eligibility as unassessed for every Run and keep continuation unavailable. Interrupted/ambiguous history must never appear eligible/available. No eligibility computation, resume intent or “click to approve/resume” flow is introduced. |
| Journal timeline | Only the two Journal kinds, their exact provenance and recording time. Do not convert them to Workflow stages, command logs or gate outcomes. Show page/traversal coverage explicitly. |
| Result shell | Recorded content-free summary, physical identity and its observation source. No text/hex preview, payload availability guess or reconstructed live Result. |
| Integrity | Suppress signature/digest/tamper badges. A label may say “Journal snapshot semantically validated,” accompanied by its scope/time and separate traversal completeness. It is not authenticity, rollback proof or safety approval. |
| Approval navigation/counts | Show unavailable / an em dash with explanatory text. Never initialize an unknown real-source count as `[]`/zero or show “no pending approvals.” No queue/decision view is fabricated. |
| DAG | Render Core Task nodes/edges and decision fields; filters affect presentation only. Include disconnected capacity consumers in the underlying decision. Never derive readiness, selection or Task completion in UI. |
| Workflow river | A separate drawing, not the Task DAG, live progress, Stage lifecycle or Quality Gate result. Unsupported Stage facts are unavailable. |
| Other screens | Overview aggregation, Task catalogs, Actor roster, approval queue and advanced mock scenarios remain outside real-data integration. Mock demonstrations must be explicitly labeled and separate. |
| Loading/failure/staleness | Loading, not found, unavailable, denied, incompatible, invalid, partial and complete-empty states remain distinct. After ordinary busy/unavailable refresh failure, historical values may remain with original time and a stale notice only for the same still-entitled principal/context. On access denial, revocation or principal/policy/source-context change, remove the previous subject display/cache references. No persistent offline cache. |
| Controls | Existing execute, approval, cancel, continue/resume controls remain disabled. No hidden command path, keyboard alternative or automatic dispatch is added. |

UI may format labels/colors and draw layouts. It cannot upgrade a summary into lifecycle success, infer approval from absence, repair evidence, or run a second scheduling policy.

### Exact current component responsibilities

Paths are relative to `ui/control-center/src/app/` in the active UI checkout. This is a responsibility mapping, not a file-change plan.

| Existing files/components | Proposed boundary responsibility |
| --- | --- |
| `data/control-center-data-source.ts`, `app.config.ts` | Existing presentation seam and mock source binding. The real slice must represent only the two approved semantic reads; unsupported catalog methods cannot be fabricated from them. |
| `data/models.ts`, `features/runs/run-detail.ts` | Separate canonical lifecycle, recorded summaries, source coordinates, independent observation times and evidence coverage. Current required mock fields do not become Core fields. |
| `data/result-adapter.ts`, `shared/result-shell.ts` | Render a recorded summary with exact physical Result/Binding/ledger identity; unavailable route and payload; no live Result assertion. |
| `data/timeline-adapter.ts`, `shared/execution-timeline.ts`, `shared/evidence-panel.ts` | Map the two Journal event kinds and provenance with explicit partial/complete/error state; suppress generic evidence previews and unsupported integrity assertions. |
| `data/continuation-adapter.ts`, `shared/continuation-shell.ts` | Always-unassessed first-slice eligibility and disabled action; no supplied mock flag can enable availability. |
| `data/dag-adapter.ts`, `shared/nile/dag-flow.ts`, `shared/nile/dag-node-inspector.ts`, `shared/nile/scheduler-panel.ts` | Layout/filter/inspect the Core Task graph and unchanged scheduler assessment. Drawing edges may run prerequisite-to-dependent while canonical pair meaning remains explicit. |
| `shared/nile/nile-topology.ts` | Workflow river remains a distinct presentation; no Stage execution, scheduler or gate facts derived from colors/topology. |
| `features/tasks/task-detail.ts`, `data/mock/mock-control-center-data-source.ts` | Do not carry array-last/latest assumptions into the real source. The selected real Run and explicit latest registration ID come from `InspectRun`. |
| `app.ts`, `features/overview/overview.ts`, `features/approvals/approvals.ts` | Unsupported approval count/source is unavailable. Real Run data does not authorize overview/approval aggregation. |
| `shared/load-state.ts`, `shared/state-panel.ts` | Preserve denied, unavailable, incompatible, integrity failure, partial, complete-empty, expired and historical/stale data distinctions beyond loading/ready/error. |

## 14. P10 — Acceptance obligations after separate authorization — NEW PROPOSAL

These are design acceptance criteria, not an implementation plan or permission to run checks now.

- Demonstrate no writes/recovery/ownership takeover/independent lifecycle-storage open across normal reads, missing owner/connection, contention, identity change, malformed stores and errors.
- Demonstrate complete-domain coordination across every writer and shutdown path, including disconnected capacity consumers; reject mixed revisions and definition/source mismatches. Verify lifetime leases, close races, ownership loss and bounded capture drain without closing resources beneath a reader.
- Preserve every Contract/Binding/ledger field and exact large numeric value across projection and UI adaptation.
- Verify stable `H`, nonmatching-record progress, empty partial pages, replayed/foreign/expired cursors, multiple physical subjects, Journal growth and complete-empty semantics.
- Enforce query-admission, database-preflight, working-memory, validation-work, scan, byte, response, deadline and retained-context limits before unbounded allocation; reject oversized exact identities without truncation. Verify writer priority and bounded reader hold under sustained concurrent read requests.
- Cover interrupted lifecycle plus Journal success, lifecycle success with missing Journal, Entry-only evidence, conflict and independent component failures.
- Verify audience denial/revocation, metadata-only responses, sanitized errors and absence of payload/proof/path leakage.
- Verify the five section-4 UI corrections, especially always-unassessed first-slice continuation eligibility and unavailable/omitted `configuredRoute`, and that every operational control remains disabled.
- Obtain independent architecture, safety and documentation consistency review of the actual implementation if later authorized; prior static design review cannot substitute.

### Negative-test requirements for future authorization

These cases specify required behavior. None was executed in this exercise.

| Negative case | Required result |
| --- | --- |
| No owner, passive connection missing, owner closing, lost ownership | Explicit unavailable/busy failure; no independent open, owner startup, recovery or reconnection. |
| Writer or shutdown races a capture; sustained new reads arrive | Writer/shutdown priority, bounded active capture drain, transaction cleanup and lease release before handles close; no mixed revision snapshot. |
| Cross-source Run-ID collision, changed generation, wrong Binding/tool, definition mismatch | Identity failure; no alternate source, fuzzy match or partial subject. |
| Valid source has missing graph Tasks versus invalid extra domain Tasks | Core incomplete decision with no selection for missing observations; error for extra/mismatched domain. |
| Result success but Task still `in_progress`; disconnected pending Run occupies capacity | No inferred Task completion/dependency satisfaction; capacity consumer retained in Core assessment. |
| Empty matching page before `H`, matches after long nonmatching prefix, new appends | Cursor advances globally; partial stays partial; unchanged `H`; new appends belong to a new traversal. |
| Foreign/altered/expired cursor, replay/branch, changed page size, missing cursor restart | Validate all bindings; never silently reset; replay/branch/restart charges shared inspection budgets. |
| Entry only, interrupted lifecycle plus Journal success, different physical subjects/outcomes | Preserve separate observations and discrepancies; no repair, winner selection or execution availability. |
| Malformed later Journal row, truncated history, oversized next matching record | Whole request fails without usable prefix; no row skip or cursor advance past withheld evidence. |
| Valid records exceed row/byte/deadline/memory/cumulative budget | Explicit exhaustion; no completeness/absence/uniqueness claim and no internal retry loop. |
| Numeric value above JavaScript safe integer; zero-byte success; fractional Grant timestamps | Exact decimal values, count `0`, and original timestamp text preserved. |
| Principal changes, policy revokes, reference copied to another reader | Reauthorization failure/context invalidation; clear prior subject display/cache references. No stale-readable metadata under a revoked or foreign principal. |
| Payload/preview/proof/physical-storage-path/exception injected into a projection | Reject closed-field/metadata contract; do not display or retain unauthorized material. Exact lexical Contract resources remain subject to the approved metadata policy. |
| Read failure reaches UI count/Result/integrity/continuation adapters | Unavailable stays unavailable; no zero approvals, success promotion, signature badge or enabled control. |

## 15. Source verification register

Paths below are relative to the pinned Core checkout unless prefixed `UI/`, which means:

`D:\Dev\itru-ui\ui\control-center\src\app\`

Line references identify the inspected source, not proof of runtime behavior.

| Claim | Inspected source |
| --- | --- |
| Mutating owner open; existing read transaction behavior | `itru/sqlite_task_run_state.py:121`, `:216`, `:341`; `core/task-run-state-specification.md:133`. |
| Store identity and complete validation | `itru/sqlite_task_run_state.py:181`; `itru/sqlite_agent_execution_journal_store.py:201`, `:238`. |
| Contract/Binding/ledger structure | `itru/agent_execution_contract.py:38`; `itru/task_run_state.py:176`; `itru/authorization_domain_ownership.py:49`. |
| Route tuple | `core/agent-operation-tool-registry-and-resolver-specification.md:225`; `UI/data/models.ts:428`; `UI/shared/result-shell.ts:504`. |
| Registration order versus lexical pages | `itru/task_run_state.py:283`; `itru/sqlite_task_run_state.py:366`; `UI/features/tasks/task-detail.ts:322`, `:331`. |
| Unsafe continuation and stricter unassessed first slice | `itru/task_run_state.py:250`; `UI/data/continuation-adapter.ts:127`; complete reconciliation addendum, UI-mapping table. |
| DAG and scheduler | `itru/task_dependency.py:31`; `itru/task_scheduler.py:24`, `:158`; `core/task-scheduler-specification.md:47`, `:85`. |
| Stable Journal traversal and unfiltered page | `itru/sqlite_agent_execution_journal_store.py:41`, `:357`, `:372`; `core/agent-execution-journal-specification.md:241`; `itru/developer_alpha.py:224`. |
| Journal summary/provenance validation | `itru/agent_execution_journal.py:172`, `:214`; `core/agent-execution-journal-specification.md:127`. |
| Metadata audience and integrity limits | `core/agent-execution-journal-specification.md:147`, `:355`, `:364`. |
| Diagnostic reconciliation and disagreement | `itru/task_run_state.py:338`; `tests/test_developer_alpha.py::test_06_running_restart_interrupted_no_journal_success_repair` — static evidence only. |
| Mock seam, false-zero and integrity labels | `UI/app.config.ts:13`; `UI/app.ts:44`; `UI/data/timeline-adapter.ts:28`. |

## 16. Independent reviews and validation record

This candidate received separate independent architecture and safety/governance reviews of its text and relevant source. Reviewers are distinct agent execution instances, using the same available Provider/model; no different-Provider or Human review is implied.

Initial reviews preceded receipt of the complete addendum and are superseded by the fresh reviews below. Reading the complete addendum required removing first-slice eligibility assessment, making `configuredRoute` omitted/unavailable, and clarifying owner-internal reads and shutdown coordination.

The earlier post-addendum review covered a smaller candidate. This expanded candidate adds complete nested contracts, exact timestamp handling, cumulative work budgets, component mappings, negative-test requirements and risks/open questions. Earlier approvals are not presented as approval of these additions.

Both reviewers freshly evaluated the complete corrected 513-line candidate, SHA-256:

`2528c5e086f060d2c30a27265d64b2c402bd96ae9a98be50fa93060434a98ee9`

That hash identifies the reviewed packet; subsequent edits to the review record record their outcomes and dispositions. It is not a self-hash of the document containing these receipts.

| Reviewer execution | Outcome and actual scope |
| --- | --- |
| `/root/core_evidence` — architecture | **APPROVE; no unresolved architecture findings.** Read complete expanded/corrected text, supplied addendum, relevant Investigation material and targeted current Core source. Checked owner/passive-session prerequisites, shutdown, nested identities/timestamps, graph coverage, cumulative budgets, cursor completeness, fields and errors. Did not independently re-audit UI/Confluence evidence, inspect operational data, run tests/runtime/imports, evaluate implementation or select/validate transport. |
| `/root/ui_safety_evidence` — safety/governance | **APPROVE as a scoped static-design judgment; no unresolved material safety/governance findings.** Read complete expanded/corrected text, supplied Investigation/addendum and targeted current UI/Core/governance source. Checked metadata entitlement/revocation, authority isolation, provenance, resource lifetimes, cumulative budgets, full-H coverage and UI corrections. Excluded executable implementation, authentication/transport mechanisms, operational datasets and runtime acceptance. |

| Finding | Original outcome | Resolution |
| --- | --- | --- |
| A-01 — comparison field precision | Architecture minor | Section 10 closes the comparison object, coverage vocabulary, reconciliation fields, outcome nullability and Run-revision meaning. Reviewer confirmed closed. |
| A-02 — source-unavailable retry ambiguity | Architecture minor | Section 12 uses uniform conservative retry advice for normalized source-unavailable errors. Reviewer confirmed closed. |
| S1 — concurrent work and reader starvation | Safety material; initial **CHANGES REQUIRED** | Sections 5 and 11 bound active admissions, working memory, request/database preflight and capture hold, give waiting mutations priority and require interruptible validation. Section 14 requires future sustained-reader/writer verification. Reviewer confirmed closed. These additions are NEW PROPOSALS. |
| S2 — cursor replay qualification | Safety minor | Section 9 makes repeatability conditional on source identity, current whole-snapshot validation, admission and budgets. Reviewer confirmed closed. |
| Addendum conformance corrections | Evidence reconciliation | Sections 3, 5, 8–10 and 13–14 preserve unassessed eligibility, unavailable/omitted route, no independent lifecycle open/reconnect, shutdown coordination and full-H absence/uniqueness policy. Both fresh reviewers confirmed conformance. |
| A-03 — minimum page limit | Architecture minor | Section 8.2 explicitly requires an exact integer in `1..100`. Reviewer confirmed closed. |
| A-04 — deterministic quota encoding | Architecture minor | Section 11 specifies exact key ordering, escaping and numeric conventions for quota accounting, independently of transport. Reviewer confirmed closed. |
| A-05 — busy admission semantics | Architecture minor | Section 12 includes immediate admission-cap rejection as well as coordination timeout. Reviewer confirmed closed. |
| S3 — stale metadata after revocation/context change | Safety/governance medium; initially changes required | Sections 7/13 require prepublication entitlement checks and clearing bound/display references on denial or principal/policy/source change. Historical display is limited to continuing entitlement; section 14 includes the negative case. Reviewer confirmed closed. |
| D1 — exact component paths | Documentation low | Section 13 names the complete `shared/nile/` paths. Reviewer confirmed closed. |

All reported findings are closed in the revised text; no unresolved review finding remains within the stated scopes. The complete addendum is available and its evidence hold is resolved.

Reviewer judgments confer no Human approval, authoritative replacement status, implementation authorization or runtime acceptance. **No formal Quality Gate outcome is assigned and no formal Quality Gate PASS is claimed.**

| Validation/control | Status |
| --- | --- |
| Investigation and relevant current Core/UI static verification | Performed; no current runtime/test-pass claim. |
| Complete reconciliation-addendum comparison | Complete text read and incorporated; former evidence hold resolved. |
| Documentation consistency | Manual static comparison performed against supplied evidence and current source; no formal Quality Gate outcome claimed. |
| Independent review | Separate architecture and safety/governance judgments are APPROVE for the corrected static specification, with findings closed. No formal Quality Gate outcome claimed. |
| Tests, builds, imports, CLI/runtime/services and operational stores | Not executed/opened, as explicitly prohibited for this exercise. |
| Repository modifications | None. |
| Transport / implementation planning | Transport unselected; implementation planning not begun. |
| Human architecture approval | Required; not obtained. |

## 17. Risks, open questions and implementation prerequisites

The proposed semantic contract is complete enough for architecture review. The following are explicit approval or feasibility questions; they are not permission to discover data, select a transport or prepare implementation tasks.

| Risk / open question | Candidate treatment and required Human decision |
| --- | --- |
| Suitable owner may rarely be available under the current CLI lifecycle | No query-triggered startup, recovery or independent open. Human must accept unavailable-owner behavior and later authorize an owner integration arrangement. No persistent service/process topology is chosen here. |
| Proposed passive session, coordination and deadlines do not exist today | Treat them as prerequisites, not working guarantees. Any future inability to enforce bounded interruption/cleanup blocks admission of the read port. |
| Exact metadata may expose resources, people, authority provenance and the whole scheduling domain | Human must approve source, existing dataset, precise audience and retention. If complete identity cannot be disclosed, withhold the observation. |
| Authentication and entitlement mechanism remains unspecified | It must enforce principal/policy binding and revocation before any real delivery. Selecting it is future separately authorized design work tied to transport; source IDs/cursors are never bearer authority. |
| Numerical limits may reject the intended dataset or prevent reaching `H` | Proposed profile is unmeasured. Human must approve/revise its complete set; resource exhaustion remains explicit and never changes completeness policy. |
| Repeated whole-Journal validation amplifies work and later appends can break a traversal budget | Cumulative budgets include validation/replay/failure. No index shortcut or weaker validator is assumed. Optimizing that contract requires a separate decision. |
| Coherent privileged substitution/rollback may evade semantic validation | No signatures, hash chain, external checkpoint or rollback-proof badge is asserted. Stronger authenticity would require a new scope/contract. |
| Lifecycle and Journal can disagree or be observed at different times | Preserve both observations and their limits; no repair, replay or lifecycle promotion. The UI must tolerate unresolved evidence. |
| Retained query context can expire or disappear while lifecycle owner is unavailable | Explicit expiry; a new inspection requires a suitable established owner. No reconstructing contexts from client claims. |
| Rich UI fields and unsupported screens lack authoritative producers | Mark unavailable or keep clearly separate mock demonstrations. No fabricated approvals, recency, payload, progress or Stage outcomes. |
| Reader audience may be narrower than a complete capacity domain | This slice requires entitlement to the complete domain; no silently filtered scheduling decision. A narrower future product view needs a separate approved contract. |

The addendum’s remaining operational prerequisites are retained:

| Prerequisite | Current disposition |
| --- | --- |
| Approved source, existing dataset and metadata audience | Not selected, opened or authorized by this exercise. P02/P03 define proposed semantics only. |
| Human acceptance of unavailable reads without a suitable owner | Explicit P01 proposal awaiting approval; no fallback open/takeover. |
| Complete lifecycle mutation and shutdown coordination | Specified by P01/P07; absent from the current application boundary and not implemented here. |
| Journal resource handling and exact operational budgets | Concrete P05/P07 proposals awaiting Human approval; operational suitability is unmeasured. |
| Future implementation validation and scoped authorization | Not granted/performed. Section 14 defines acceptance obligations without preparing an implementation plan. |

## 18. Human decision record and stop

The concrete approval set is P01–P10:

- Reader/mutation/shutdown coordination.
- Source identity and complete scheduling domain.
- Metadata audience and retention.
- Application fields and lossless values.
- Retained inspection references.
- Frozen traversal and comparison.
- Numerical budgets.
- Versions and errors.
- UI mapping.
- Acceptance obligations.

Approval may accept or revise each proposal. None is labeled as a recovered original decision.

Before authority promotion, close or explicitly disposition material post-addendum independent-review findings and obtain explicit Human approval of the exact final candidate revision and proposals. Record the replacement scope so dependent documentation can later be updated under separate authorization. Existing authoritative contracts continue to govern meanwhile. The approved planning direction and resolved evidence prerequisites do not promote v2 automatically.

Approval must identify this exact candidate and explicitly accept or revise P01–P10, including unavailable-owner behavior, metadata/audience rules, retention, numerical budgets, projection version and UI limitations. Dataset/audience selection remains a distinct prerequisite. No past planning or release authorization silently approves these new details.

Approval of v2 would establish its authority only for the accepted architecture scope. Implementation planning, transport/authentication selection, code changes, runtime validation, Task creation and implementation each remain outside this exercise. No such work has begun. No formal Quality Gate PASS or runtime acceptance is asserted.

No Human instruction supplied so far approves this new document as the replacement. The current authorization is **DESIGN WORK ONLY**.

**STOP AT HUMAN CONTROL.**