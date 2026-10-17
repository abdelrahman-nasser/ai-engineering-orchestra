# ITRU_Read_Only_Integration_Implementation_Plan.md

**Date:** October 17, 2026  
**Phase:** Implementation planning only  
**Architecture:** Approved ITRU Core Application Boundary Design v2, P01–P10  
**Implementation authorization:** NOT GRANTED  
**Final checkpoint:** STOP AT HUMAN CONTROL

## 1. Executive summary

The first integration is **Existing Run → Lifecycle → Task DAG → Core Scheduler Assessment → Recorded Result and Journal Evidence**. It exposes exactly **InspectRun** and **ReadRunJournal**, application version **1.0**.

Existing Core semantics support lifecycle reconstruction, Task graphs, scheduling and content-free Journal evidence. They do not yet provide the approved passive sessions, shared mutation/shutdown coordination, bounded validation, application contexts, audience checks or UI projections. Connecting the UI directly to existing constructors/history methods would violate v2.

Recommend authorizing **S0 only**, initially using synthetic fixtures and feasibility work. The highest-risk prerequisite is proving complete lifecycle validation, scheduling and safe cleanup within the one-second capture exclusion. Repeated whole-Journal validation and cumulative budgets can prevent traversal completion even for individually permitted snapshots.

This plan selects no process topology, transport, authentication mechanism, operational dataset or metadata audience. It creates no implementation Tasks or Jira IDs. Slice, command and matrix labels below are local report references only.

## 2. Approved architectural baseline and exact identity

Canonical directory: **D:/Dev/ai-engineering-orchestra/docs/architecture/control-center/**.

| Document | Revision / SHA-256 / authority |
| --- | --- |
| README.md | Canonical index and historical-status explanation. |
| application-boundary-v2.md | Complete v2, 75,711 bytes; SHA-256 **c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062**. |
| boundary-investigation.md | Preserved original, 50,565 bytes; SHA-256 **1f736d4c0158c6781627b3abd9b95979b4f1279c92d270773d163f7e9cc12596**. |
| reconciliation-addendum.md | Preserved original, 3,670 bytes; SHA-256 **8d816aefda08b9542cb448eca467c3fde3d32bf081ec2cfb52caae4f7b380d94**. |
| human-decisions.md | Actual Human approval of the exact v2 and P01–P10 in full, dated October 17, 2026; architecture and subsequent planning only. |

All three technical SHA-256 values were verified against the canonical files during this planning task. The complete canonical documents were read. Historical candidate/unapproved wording is preserved evidence; the separate later Human decision establishes current approved architecture status. The historical review-packet hash inside v2 is not its final document hash.

No architectural text was changed. Existing Core governance and semantic contracts continue to apply.

## 3. Verified repositories and source evidence

| Repository / reference | Observed state |
| --- | --- |
| Core HEAD | 726e11a2f2e408ee02a4981c64eaae031fb25381 |
| Core branch / worktree | itru-064-developer-alpha-release; clean |
| Historical Core release | e7af2c4c01645a05e6e78ccea7e845dafc455399; retained ancestor, CLI-only Alpha |
| UI HEAD / branch | 0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67; ui/developer-alpha-integration-qa-polish |
| UI existing work | Only untracked ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md; preserved |
| Parked SCRUM-81 | ui/itru-062-contract-i18n-rtl = 61e817c1f7a2c3987710a73366b516d792402520; unchanged |
| D6-E/B1 | Separate workstream; not accessed |

UI Git inspection required a command-local safe.directory setting for the explicitly designated checkout because of the sandbox user identity. No global or repository configuration changed.

Core paths below are relative to D:/Dev/ai-engineering-orchestra. UI paths prefixed **U/** are relative to D:/Dev/itru-ui/ui/control-center/src/app/. New filenames in this report are proposed implementation boundaries, not existing APIs or authorized changes.

| Evidence | Verified implication |
| --- | --- |
| itru/sqlite_task_run_state.py:121,153,193,217,369 | Owner construction recovers; provisioning writes; validation materializes history; operational reads use BEGIN IMMEDIATE; close is separately coordinated today. |
| itru/developer_alpha.py:79,99,150,224 | open_state establishes operational ownership; context reads graph Tasks separately and hides extra enrolled Tasks; history does not provide the approved retained traversal. |
| itru/task_run_state.py:250,257,323,338 | Historical reduction, continuation checks and pure diagnostic reconciliation already exist. |
| itru/task_dependency.py:48; itru/task_scheduler.py:158 | Canonical closed DAG and deterministic complete-domain scheduling already exist; selection grants no authority. |
| itru/alpha_config.py:60,91 | Alpha configuration/work validation is available; source revision and metadata-policy registry are new requirements. |
| itru/sqlite_agent_execution_journal_store.py:201,225,238,357,372 | Existing reads open a fresh connection per operation, validate the current whole Journal and materialize records; page size does not bound validation work. |
| itru/agent_execution_journal.py:123,174,229,506 | Canonical validation is reusable semantics. Recorder reconciliation accesses ledger history and may append; it is excluded from this read composition. |
| U/data/control-center-data-source.ts; U/app.config.ts | Nine presentation queries; only mock provider bound. No live application contract implementation. |
| U/data/models.ts:155,414,428 | Real lifecycle/evidence distinctions are missing; generation/time-key fields use number; configuredRoute is required mock presentation data. |
| U/features/tasks/task-detail.ts:322–339; U/app.ts:44 | Array-last recency and initial empty approvals would misstate real evidence. |
| U/data/continuation-adapter.ts:127,178; U/data/timeline-adapter.ts:28 | Existing availability/integrity presentation can exceed first-slice authority. |

Relevant existing tests were inspected as source, not executed: lifecycle/domain/SQLite/controlled state; Task dependency/scheduler; Journal contract/SQLite/controlled Journal; controlled Result; developer Alpha; UI adapters, shells, screens and scheduler specs.

## 4. P01–P10 traceability

| Approved requirement | Planned ownership / slices | Acceptance evidence |
| --- | --- | --- |
| P01: established owner, passive resources, mutation/shutdown exclusion and leases | Core S0/S1; independent Journal resource lifecycle S3 | Every mutation/close path covered; no query startup/open/recovery; bounded drain; matrix N01–N05 |
| P02: immutable trusted source revision, complete domain and exact identity | Core S0/S2/S4; UI S5/S7 | Exact source/project/store/definition/graph/Journal/ledger matching; N06–N09 |
| P03: complete metadata audience, revocation, retention and no disclosure | Core S0/S2/S4; transport gate S6; UI S5/S7 | Auth before existence disclosure, every page and publication; reference invalidation; N10–N12 |
| P04: closed version-1.0 values, InspectRun and ReadRunJournal projections | Core S2/S4; UI S5 | Exact fields/nullability/enums, eleven-field Contract, lossless values; N13–N16 |
| P05: frozen H, global scan, exact subjects and honest completeness | Core S3/S4 | No Run-ID-only join, no skipped matches, shared budget; N17–N23 |
| P06: independent observations and diagnostic discrepancies | Core S4; UI S5/S7 | Unchanged helper result plus discrepancy set; interrupted remains interrupted; N24–N26 |
| P07: bounded admission, validation, memory, deadlines and retained work | Core S0–S4; delivery/UI S6/S7 | Full numerical profile in section 10; boundary and contention measurements; N27–N32 |
| P08: versioning, closed errors and fixed retry advice | Core S2/S4; delivery/UI S5–S7 | Exact supported-version error envelope, no prefix/raw exception or automatic retry; N13,N16,N26,N33 |
| P09: canonical UI mapping and disabled operations | UI S5/S7, reviewed in S8 | Required component inventory below; N34–N38 |
| P10: future acceptance and independent implementation review | Both repositories S0–S8 | Complete matrix, runtime evidence when separately authorized, independent reviews and Human acceptance |

## 5. Remaining prerequisites and Human decisions

| Gate | Required resolution, evidence and approach | Dependencies / risks / verification |
| --- | --- | --- |
| H1: scoped implementation authorization | Approve S0 change scope and future synthetic execution explicitly. This report grants neither. | Blocks code/harness/test execution; verify fresh baselines and exact authorized changed-path inventory. |
| H2: historical continuation validation tension | v2 prohibits first-slice eligibility assessment; apply_event validates historical continue events by calling continuation_eligible. Human must confirm whether unchanged historical integrity validation is permitted while no new current assessment/output occurs. | Blocks S1/S2 finalization. Proposed distinction preserves full validation and always-unassessed output. A literal ban on every helper invocation conflicts with historical validation; requires approved clarification/revision, not bypassing checks. |
| H3: owner integration arrangement | Identify an independently established sole owner, setup/shutdown responsibility and resource lifetime. Existing CLI sessions are command-scoped. | S0 feasibility and separate owner-setup authorization precede S1 admission. No process topology selected. Absent owner remains owner_unavailable; no cold-owner fallback. |
| H4: trusted source / metadata configuration | Define immutable source registration, full Alpha definition/graph/capacity domain, expected identities, budget and metadata-policy references; later Human approves actual source, existing Run/dataset and complete audience. | Synthetic descriptors can be implemented first. Actual registration/access is withheld until separately approved. No inferred repository task.yaml association. |
| H5: P07 feasibility / change control | Demonstrate bounded SQL, Python, encoding, allocation and cleanup against approved limits using synthetic data. | Blocks reader admission and dependent operational integration. Any raised limit, validation weakening, alternate snapshot policy or stronger WAL policy needs explicit architecture approval. |
| H6: transport and authentication | Separately approve mechanism, topology, authenticated principal, full-metadata entitlement, policy revision/revocation, delivery overhead and disconnect behavior. | S6 only after separate selection authorization. No real delivery before this gate and H4. Read IDs/digests/cursors are never credentials. |
| H7: release and acceptance | Scope the eventual integration independently of the closed CLI-only Alpha; require actual independent implementation review and final Human acceptance. | Blocks release/readiness claims. No reopening historical release Tasks or transferring parked SCRUM-81. |

Configuration must preserve exact source_id/source_revision, project_id/store_id, definition_set_reference, graph_reference, expected journal_id and all three ledger fields; trusted max_concurrency stays within Alpha's one-or-two limit. New source/definition/graph/storage/ledger-generation or policy context requires new references as v2 specifies. Do not select an actual dataset or grant metadata access during planning.

## 6. Dependency-ordered slices

The graph is sequencing guidance, not implementation authorization. S3 may run alongside S1 once S0 resource/source contracts are settled. S5 can proceed with approved synthetic fixtures. S6 has its own Human decision gate.

~~~mermaid
flowchart TD
  S0["S0: prerequisites and feasibility"] --> S1["S1: owner passive lifecycle capture"]
  S0 --> S3["S3: bounded Journal resources"]
  S0 --> S5["S5: UI canonical adaptation"]
  S1 --> S2["S2: InspectRun"]
  S2 --> S4["S4: ReadRunJournal"]
  S3 --> S4
  S2 --> S6["S6: separately approved transport/auth"]
  S4 --> S6
  S5 --> S7["S7: real Run detail slice"]
  S6 --> S7
  S4 --> S7
  S7 --> S8["S8: integration evidence and acceptance"]
~~~

Every slice requires its own scoped authorization, acceptance evidence, independent review and Human checkpoint. No slice automatically authorizes its successor.

### S0 — Configuration, baseline and feasibility prerequisites — L

- **Objective/outcome:** Produce an agreed implementation prerequisite package and measured synthetic feasibility evidence; identify whether P07 is enforceable before product reader work.
- **Scope/exclusions:** Source/policy/budget contracts, mutation inventory, cancellation/allocation/sidecar experiments on synthetic fixtures, contract fixtures and decision records. No operational source selection, access grant, production delivery or transport choice.
- **Files/ownership:** Core owns proposed itru/control_center_read_source.py, itru/control_center_read_budget.py, tests/test_control_center_feasibility.py and proposed application-contract documentation; UI owns synthetic version-1.0 fixture definitions. Existing alpha_config.py is an integration reference, not authority to broaden its public schema.
- **Dependencies:** Approved v2, fresh baselines and H1; resolve H2, document H3/H4/H5 decisions. Actual source/audience may remain unselected.
- **Acceptance:** Exact source descriptor and quota encoding; all writers inventoried; no hidden dataset access; representative maximum-size/escape/history shapes assessed; explicit go/no-go for bounded cancellation and safe resource cleanup.
- **Negative tests:** N01,N06,N10,N13,N27–N32; especially worker timeout without cleanup must fail feasibility.
- **Future validation:** V0,V1 with test_control_center_feasibility.py; review instrumentation and captured resource measurements.
- **Risks:** Prototype success on a small fixture is not proof for full limits; native allocations, filesystem stalls and WAL growth can invalidate assumptions.
- **Independent review:** Core ownership/concurrency reviewer and Journal/resource/security reviewer must challenge the feasibility claim and its measurement envelope.
- **Human checkpoint:** Accept prerequisites and any explicit architecture clarification; separately authorize S1/S3/S5. No real-data access follows.

### S1 — Core owner-session passive reading and mutation coordination — XL

- **Objective/outcome:** A recovery-free lifecycle capture capability supplied only by an already-established owner.
- **Scope/exclusions:** Owner-managed passive connection established during authorized setup; writer-priority coordination, lifetime leases, cancellation, ownership loss and shutdown. No query-triggered open/reconnect, provision, recovery, service startup or independent owner.
- **Files/ownership:** Core: proposed itru/control_center_read_session.py and tests/test_control_center_read_session.py; narrowly reviewed hooks/refactoring in sqlite_task_run_state.py and shared validator/budget utilities. developer_alpha.py/alpha_authority.py are composition/teardown callsites, not read shortcuts.
- **Dependencies:** S0 go/no-go; H2/H3/H5 resolved for supported setup.
- **Acceptance:** Every path in the mutation inventory below participates; complete coherent validation/capture/evaluation and cleanup fit the one-second hold; wait ≤1 second; no later reader overtakes a waiting writer/shutdown; no handle closes beneath a lease.
- **Negative tests:** N01–N05,N08,N27,N30–N32 across every mutation path and each SQL/Python/cleanup cancellation point.
- **Future validation:** V1 for test_control_center_read_session.py; V2 lifecycle/recovery/controlled-state regressions plus synthetic concurrency instrumentation.
- **Risks:** Bypassed direct store operations, callback recursion, lost ownership and uninterruptible validation could invalidate all consistency guarantees.
- **Independent review:** Reviewer separate from session implementer must audit all writer and teardown paths and observe race/cleanup evidence.
- **Human checkpoint:** Approve bounded passive capability before S2 uses it; inability to prove safe drain keeps admission disabled.

**Mandatory S1 mutation/teardown inventory:** sqlite_task_run_state.py constructor/startup recovery; provision; _transaction and _append; enroll; register_run; start_run; record_result; transition for block/cancel/complete/stop; continue_task and trusted-authorizer callback; existing get_task/get_run/checkpoint/page operational transactions; close and constructor-failure cleanup; _check_session identity/PID/security/ownership loss; process/context loss. Audit all developer_alpha.initialize/load_work/open_state/execute/command callsites, including provider-failure/missing-Result stop paths. Preserve Result membership, revision CAS, authority checks and recursion rejection. Provisioning/recovery are completed before admission and never query fallbacks.

### S2 — Core InspectRun projection and contract validation — L

- **Objective/outcome:** Exact immutable version-1.0 lifecycle/Task/DAG/scheduling inspection and retained reference.
- **Scope/exclusions:** Trusted source resolution, full-domain capture, canonical scheduler evaluation, registration-order history, closed DTOs and errors. Opens neither Journal nor authorization ledger; no current eligibility assessment, rich Task metadata inference or enumeration query.
- **Files/ownership:** Core: proposed itru/control_center_read_contract.py, itru/control_center_read_context.py, itru/control_center_inspect_run.py; proposed tests/test_control_center_inspect_run.py and test_control_center_contract.py. Reuse task_dependency.py/task_scheduler.py and validated state values. Existing persisted schemas remain unchanged.
- **Dependencies:** S1; S0 source/policy/context contracts; H2.
- **Acceptance:** Validate all enrolled Tasks before graph comparison; extras/definition mismatch fail, missing graph observations yield Core incomplete_snapshot without selection; preserve exact Contract/Binding/ledger, Task and Run revisions, complete history and explicit latest_run_id; bounded retained reference; release lifecycle lease before delivery.
- **Negative tests:** N06–N16,N27–N32; disconnected capacity, Run success without Task completion, oversized exact graphs/history and source changes.
- **Future validation:** V1 for test_control_center_inspect_run.py and test_control_center_contract.py; V2 DAG/scheduler/state regressions.
- **Risks:** Reusing developer_alpha.context would collect separate transactions and omit extra Tasks. Raw asdict/config dumps would disclose unapproved fields.
- **Independent review:** Core consistency/identity reviewer and metadata-authority reviewer.
- **Human checkpoint:** Approve actual version-1.0 projection and synthetic evidence before dependent Journal composition or delivery.

### S3 — Journal resources, validation and bounded-work infrastructure — XL

- **Objective/outcome:** Established Core-managed Journal read resources that preserve complete-current-snapshot validation while enforcing P07.
- **Scope/exclusions:** Independent resource leases, read-only snapshot lifecycle, file preflight, interruptible incremental validation, allocation/accounting and cancellation/close. No query-time provisioning, repair, migration, resource opening/reconnection, ledger read or weakened validation.
- **Files/ownership:** Core: proposed itru/control_center_journal_reader.py and tests/test_control_center_journal_reader.py; reviewed validation-sharing hooks in sqlite_agent_execution_journal_store.py and agent_execution_journal.py; shared budget utilities. Existing canonical Journal schema is not converted to application decimal strings.
- **Dependencies:** S0 source/resource/budget decisions; shares lease/admission conventions with S1 but does not require a live lifecycle owner for every later Journal page.
- **Acceptance:** Preserve schema fingerprints, metadata/identity, all current rows, sequence/time/index/subject consistency and Entry-before-Result checks; bounded reads before materialization; no sidecar fallback; whole-snapshot failure produces no prefix.
- **Negative tests:** N17,N21–N23,N26–N32; corruption beyond frozen H, later growth, physical sidecars and close/cancel races.
- **Future validation:** V1 for test_control_center_journal_reader.py; V3 Journal/Result semantic and storage regressions; synthetic memory/I/O/cancellation measurements.
- **Risks:** Current _snapshot opens each connection afresh and _verify retains full records/maps; wrapping page(limit=...) does not establish compliance.
- **Independent review:** Journal validation-equivalence reviewer and resource-lifetime/security reviewer.
- **Human checkpoint:** Approve bounded semantic-equivalent reader and its supported storage/runtime envelope before S4 admission.

### S4 — Core ReadRunJournal traversal and reconciliation — XL

- **Objective/outcome:** Exact-subject, frozen-high-water, content-free Journal pages and honest comparison with the retained inspection.
- **Scope/exclusions:** Opaque Core-held cursors, shared cumulative charging, matching/grouping, full-H completion, pure reconciliation and P08 errors. No lifecycle refresh, live Result reconstruction, payload recovery, winner selection, ledger query or recorder reconciliation.
- **Files/ownership:** Core: proposed itru/control_center_read_journal.py, shared control_center_read_context.py/read_contract.py/read_budget.py, tests/test_control_center_read_journal.py and test_control_center_read_context.py. Use task_run_state.reconcile_run unchanged.
- **Dependencies:** S2 and S3; shared trusted source/policy contexts; no operational delivery before H4/H6.
- **Acceptance:** First successful validated snapshot freezes H, including H=0; scan global sequences across nonmatches; retain the next matching record if output count would overflow; complete only through H; exact subject/ledger/generation/physical identities; repeated whole-current validation and all shared budgets; independent observations and explicit discrepancies.
- **Negative tests:** N10–N16,N17–N33; altered/foreign/replayed/branched cursors, size changes, competing subjects and interrupted lifecycle plus Journal success.
- **Future validation:** V1 for test_control_center_read_journal.py and test_control_center_read_context.py; V3 reconciliation/Journal regressions and measured charging.
- **Risks:** Partial evidence cannot establish absence/uniqueness. Multiple subjects may yield helper inconsistent; preserve that result and add multiple_physical_subjects rather than rewriting helper semantics.
- **Independent review:** Journal identity/completeness reviewer and audience/budget/failure-isolation reviewer.
- **Human checkpoint:** Approve traversal/comparison and exhaustion evidence before transport binding.

### S5 — UI canonical model and presentation alignment — L

- **Objective/outcome:** Strict version-1.0 decoding and honest presentation using approved synthetic fixtures; safe parallel UI preparation.
- **Scope/exclusions:** Separate Core facts from UI labels/layout, lossless numbers, unsupported-data states and disabled controls. No real data connection, transport, catalog fabrication, readiness policy or parked-branch transfer.
- **Files/ownership:** UI owns U/data/control-center-data-source.ts, models.ts, new application-v1-contract.ts/application-v1-decoder.ts, result/timeline/continuation/dag adapters and their specs; shared load-state/state-panel, result-shell, execution-timeline, evidence-panel, continuation-shell, shared/nile/dag-flow/dag-node-inspector/scheduler-panel/nile-topology; affected templates/styles/specs.
- **Dependencies:** Approved v2 and S0 fixture/error/quota decisions. Can run alongside S1–S4; final conformance waits for actual S2/S4 output fixtures.
- **Acceptance:** All component obligations in section 7; source-aware seam supports only two real reads and explicit unsupported capabilities; never fake empty catalogs to satisfy nine mock methods.
- **Negative tests:** N13–N16,N24–N26,N34–N38; hostile mock availability flags cannot enable commands or promote evidence.
- **Future validation:** V4; adapter/decoder/shell/screens specs with lossless and denied-context fixtures.
- **Risks:** Old models require invented title/stages/route/payload and number conversions; reusing them unchanged would corrupt meaning.
- **Independent review:** UI semantic-fidelity reviewer plus Core contract reviewer; test keyboard/indirect command paths as well as disabled buttons.
- **Human checkpoint:** Approve UI-only preparation and synthetic conformance; no provider swap to a real source yet.

### S6 — Separately approved transport/authentication integration — L/XL, conditional

- **Objective/outcome:** Deliver the two queries through a separately selected and approved mechanism with authenticated metadata access.
- **Scope/exclusions:** Mechanism-specific request/delivery framing, identity/policy integration, quotas, cancellation and sanitized errors. No selection in this plan, no generic dispatch, source enumeration, subscriptions, commands or credential forwarding from execution approval.
- **Files/ownership:** Joint Core/UI. Existing seams: U/app.config.ts, U/data/control-center-data-source.ts and app.routes.ts; new Core delivery adapter and UI client adapter filenames remain selection-dependent. Mechanism-specific tests/configuration are specified only after the decision.
- **Dependencies:** S2/S4 semantics and resource evidence; H4 source/audience approval; separate H6 design authorization and approval. S5 decoder ready before UI use.
- **Acceptance:** Only approved operations; authenticate before existence disclosure; reauthorize each request and prepublication; account request/delivery overhead, disconnects and buffers; bind policy/source/principal and invalidate contexts; no fallback transport or auto-owner start.
- **Negative tests:** N10–N13,N16,N27,N30,N33,N38, plus selected mechanism's origin/session/credential/replay controls once designed.
- **Future validation:** V5; exact delivery/security commands are intentionally pending the H6 decision. V1/V4 remain applicable.
- **Risks:** Process topology may not support the owner lifetime; execution trust cannot silently become browser metadata authority.
- **Independent review:** Authentication/authorization and owner-topology reviewers separate from implementers; Core/UI contract compatibility review.
- **Human checkpoint:** Explicit approval of chosen mechanism and actual audience before any operational delivery or S7.

### S7 — Real Control Center existing-Run vertical slice — L

- **Objective/outcome:** One explicitly supplied source revision and existing Run can be inspected with separate lifecycle/DAG/scheduler and Journal panels.
- **Scope/exclusions:** Source-aware Run detail, manual bounded Journal continuation, historical/error indicators and context clearing. No Run/source catalog, overview aggregation, Actor roster, approval queue, live progress, operational commands or automatic retries/polling.
- **Files/ownership:** UI owns U/features/runs/run-detail.ts, app.routes.ts, app.config.ts and real data-source adapter, U/app.ts; U/features/tasks/task-detail.ts and overview/approvals/flow entry points receive scoped guards/unavailable states where they would otherwise imply real unsupported data. Core composition wires only approved S2/S4 handlers.
- **Dependencies:** S4/S5/S6; Human-approved source/existing Run/full audience; independently established operational resources. Existing untracked readiness document remains contextual work, not authority.
- **Acceptance:** Real source identity visible; lifecycle remains useful if Journal fails; dates/coverage displayed independently; latest means explicit latest registered Run of the inspected Task; mocks stay separately labeled; controls disabled and no unsupported background calls.
- **Negative tests:** N06,N10–N12,N24–N26,N33–N38; source switches, permission loss, expired inspection and unsupported navigation.
- **Future validation:** V4/V5 and separately authorized manual inspection of approved existing data; no data creation, recovery or repair to manufacture a demo.
- **Risks:** Operational evidence/dataset may be absent or exceed P07; report unavailable/exhausted rather than substituting mocks.
- **Independent review:** End-to-end Core/UI identity, metadata-authority and semantic presentation reviewers.
- **Human checkpoint:** Review actual vertical slice before final integration acceptance work or any release claim.

### S8 — Integration validation, independent review and Human acceptance — L

- **Objective/outcome:** Evidence-backed acceptance of the implemented read-only slice within an explicitly documented supported environment.
- **Scope/exclusions:** All acceptance/negative cases, resource/race measurements, regression checks, independent implementation review and Human acceptance. No automatic deployment, publication, operational command expansion or release rewrite.
- **Files/ownership:** Joint Core tests/test_control_center_integration.py and scoped test suites; UI decoder/adapter/component/integration specs; separately authorized acceptance/review documentation. Actual test filenames and transport harness are finalized in prior slices.
- **Dependencies:** S7; all earlier evidence current; H4/H6/H7 approvals.
- **Acceptance:** Matrix complete with exact tested revisions/configuration, zero unresolved required failures, approved findings dispositions, operational corroboration where claimed and explicit limitations where unmeasured.
- **Negative tests:** Entire N01–N38 matrix, including sustained contention, largest supported shapes and non-disclosure after revocation.
- **Future validation:** V1–V6 as applicable; repeat only affected evidence after changes. No historical test-pass receipt substitutes for this implementation.
- **Risks:** Static review cannot prove timing, memory, OS/SQLite cancellation or audience enforcement. Unavailable operational evidence blocks operational acceptance, not just a report checkbox.
- **Independent review:** Separate Core consistency/concurrency, Journal/resource, authority/security, UI semantic and documentation/traceability judgments; implementer cannot be sole approver.
- **Human checkpoint:** Final Human acceptance required. Stop; release/deployment and future operations require separate authorization.

## 7. Detailed acceptance criteria and UI inventory

**InspectRun:** Closed P04 request/success/error shapes; exact version/source locator; authorized exact Run resolution; complete validated lifecycle reduction; whole graph including disconnected capacity consumers; graph definition coherence; canonical topological order; unchanged Core scheduler state, per-Task/dependency evaluations, occupied/selected IDs and coverage. Preserve Task state/revision separately from Run state/revision. History is complete registration order with explicit latest_run_id. Definition metadata remains unavailable/not_in_first_slice; payload unavailable_not_retained; continuation always unassessed/action_available=false. Expected Journal identity is configured expectation, not an observed Journal fact. No Journal/ledger open.

**ReadRunJournal:** Resolve only Core-retained inspection subject; exact complete Binding and three-field ledger identity; accepted physical identity does not hide competing subjects. Validate nested ten-field Journal record, Entry/Admission/Grant/Run/eleven-field Contract, canonical versions, provenance, identity/time relationships and outcome-specific diagnostic/null/count rules from v2 §8.3. Physical Result identity remains the five-part ledger-instance/domain/issuer-kind/issuer/Grant tuple; domain generation remains a separate exact field. No substitute result_id.

Freeze H after successful whole-current validation; later appends stay outside traversal but inside each current validation. Global positions/counts are distinct from charged work. Empty partial pages can advance; oversized records never get skipped. At H, complete=true/next_cursor=null/high_water_reached; otherwise valid continuation and page_limit/scan_limit. Errors return no usable prefix or new scan position. Absence means only no matching recorded evidence in this Journal at H.

Retained context binds principal, policy, source revision, application version and exact subject. Maximum lifetime is fixed from inspection creation; owner shutdown alone does not rewrite/expire a completed retained observation, while context loss does. Partial comparison has null core_reconciliation; final comparison preserves reconcile_run fields and one of missing/entry_only/recorded_result/conflict/inconsistent, plus sorted unique discrepancy codes from P06. No repair or state promotion.

**Value/error fidelity:** Unbounded/64-bit revisions, sequences, generations, counts and numeric time keys use canonical unsigned decimal strings; no boolean, sign, leading zero, float or JavaScript number round-trip. Preserve underlying Core ranges, including sequence/lease maximum 9223372036854775807 and Entry key maximum 315537897599999999. Bounded limit/format-version/concurrency remain exact small integers. Preserve Grant timestamp text, including absent or 1–6 fractional digits; other specified timestamps retain canonical six-digit UTC. Monotonic Core clocks govern expiry/deadlines.

P08 errors are exactly invalid_request, unsupported_version, access_denied, source_unavailable, source_revision_changed, run_not_found, source_busy, owner_unavailable, identity_mismatch, incompatible_source_version, integrity_failure, metadata_limit, work_budget_exceeded, deadline_exceeded, inspection_expired, invalid_cursor, cursor_expired, context_limit and internal_error. No added public error enum. Components and safe messages are closed/fixed; errors use supported version 1.0. Busy/owner/deadline advise retry_query_later; expired inspection/cursor/source revision advise restart_inspection; all others do_not_retry. Advice never launches a retry. Journal failure stays independent of lifecycle.

| UI files / area | Required implementation behavior |
| --- | --- |
| U/data/models.ts and new strict decoder | Distinct canonical Task/Run/scheduler/evidence models; decimal strings throughout; no required mock-only fields filled with inventions. Reject unknown fields/enums and malformed nested identity. |
| U/data/control-center-data-source.ts; app.config.ts | Keep UI-owned presentation seam; distinguish real two-read capability from mock catalogs. Unsupported capability is explicit unavailable, never []/zero/undefined-not-found substitution. |
| U/features/runs/run-detail.ts; app.routes.ts | Source-revision-aware explicit Run selection supplied out of band; show exact source and two observation times; no new catalog operation. |
| result-adapter.ts; shared/result-shell.ts | Content-free recorded summary and exact physical identity; payload unavailable; configuredRoute omitted/unavailable; no live Result assertion. |
| timeline-adapter.ts; shared/execution-timeline.ts; evidence-panel.ts | Only entry_observed/result_observed, exact provenance/recording time, global coverage/completeness and discrepancies. No preview, command log, Stage/gate or cryptographic badge. |
| continuation-adapter.ts; shared/continuation-shell.ts | Unassessed for every first-slice Run, always disabled regardless of supplied legacy/mock flags. |
| dag-adapter.ts; shared/nile/dag-flow.ts, dag-node-inspector.ts, scheduler-panel.ts | Render canonical Task nodes/edges and unchanged Core evaluations. Pair (A,B) means A waits for B; drawing reversal for layout is labeled. Filters do not recompute scheduling or shrink its domain. |
| shared/nile/nile-topology.ts | Workflow river remains separate from Task dependency DAG; colors/animation establish no Stage lifecycle, liveness, progress or gate outcome. |
| features/tasks/task-detail.ts; data/mock/mock-control-center-data-source.ts | Use explicit latest registered Run for real inspected history; remove array-last/global-recency assumptions from shared real path. Keep mock demonstrations distinct. No rich Task detail integration implied. |
| app.ts; features/overview/overview.ts; features/approvals/approvals.ts | Real-source approval count unavailable/em dash; unsupported pages explicit unavailable/separate demos. No fabricated zero approvals, all-clear, aggregation or progress. |
| shared/load-state.ts; state-panel.ts | Distinguish loading/not-found/denied/unavailable/incompatible/integrity failure/expired/partial/complete-empty/historical-stale. Only same still-entitled principal/context may retain historical data after ordinary busy/unavailable refresh. Revocation or principal/policy/source change clears display/cache references. |
| All operational affordances | Execute/approve/cancel/continue/resume disabled; no click, keyboard, service, background or indirect command path. No persistent/offline cache, export or analytics metadata retention. |

## 8. Acceptance and negative-test matrix

All checks below are **future execution**, not results. Use synthetic fixtures and controlled race/fault scheduling first. “Operational” means additional separately authorized evidence from the eventual supported environment and approved existing source.

| Ref | Property / method and negative stimulus | Required result / subsequent blocker |
| --- | --- | --- |
| N01 | Spy prohibited opens/constructor/recovery/provision/invocation paths during reads; missing owner/passive connection | Zero calls/writes; owner_unavailable/busy. Blocks S1/S2. |
| N02 | Independently held owner; read attempted from another composition | No competing ownership or takeover. Synthetic OS-lock evidence; operational arrangement corroboration. Blocks S1. |
| N03 | Race capture against each inventoried mutation, including legacy queries and close | Single coherent revision set; no bypass. Instrument transaction/lease boundaries. Blocks S1/S2. |
| N04 | Sustained readers with waiting writer/shutdown; cancellation in SQL/decode/reduction/scheduler/cleanup | Writer priority; ≤1-second capture/drain; lease released before handle close. Measured supported-runtime evidence. Blocks S1. |
| N05 | Owner/PID/file identity loss or context/process loss | Entire capture fails, no reconnect; retained historical inspection behavior follows context lifetime. Blocks S1/S4. |
| N06 | Cross-source Run-ID collision, changed project/store/definition/graph/ledger generation/tool | identity_mismatch/source revision handling, no alternate-source join. Blocks S2/S4/S7. |
| N07 | Missing graph Task versus extra enrolled Task/definition mismatch | Missing => incomplete_snapshot/no selection; extras/mismatch => error. Blocks S2. |
| N08 | Disconnected pending/running capacity consumer; Run succeeds but Task remains in_progress | Complete capacity assessment; dependency needs persisted completed Task. Blocks S2/S5. |
| N09 | Reordered lexical IDs/history filters and Unicode/case variants | Registration order/latest explicit; identifiers unchanged, no normalization/global recency. Blocks S2/S5. |
| N10 | Denied/unauthenticated request for existing and nonexistent target | No existence disclosure; full-metadata entitlement before lookup. Blocks delivery. |
| N11 | Revocation/policy/principal/source change during request, between pages and before publication | Deny/invalidate Core refs; clear UI subject refs; no stale-readable revoked data. Blocks S6/S7. |
| N12 | Inject payload, preview, content hash, proof, path, config, raw exception or metadata logging | Closed projection rejects; no response/cache/log/export disclosure. Exact authorized Contract resource is preserved. Blocks S2/S4/S6. |
| N13 | Wrong app version, duplicate/unknown field, malformed enum/type/limit; floats/bools | Fixed P08 error, supported-version envelope, no downgrade. Blocks S2/S4/S5. |
| N14 | Values around 2^53, maximum sequence/time key, large generation/count/revision | Exact decimal-string round-trip through Python/decoder/UI, no Number coercion. Blocks S5/S7. |
| N15 | Zero-byte success, null fields, all diagnostic/outcome combinations, fractional Grant timestamps | Exact count 0, nullability/allowlists, original timestamp text; reject malformed combinations. Blocks S4/S5. |
| N16 | Unsupported schema/record versions; store busy; unexpected exception | Exact P08 classification/advice; no migration/raw exception/success fields/prefix. Blocks S2/S4/S6. |
| N17 | Append after first page, including corrupt/oversized row beyond H | H unchanged; current whole-snapshot validation still required; bad later row fails request. Blocks S3/S4. |
| N18 | Long nonmatching prefix and empty filtered partial pages | Global scan advances within cap; valid next cursor; no fabricated absence. Blocks S4. |
| N19 | Changed limit, replay, branch, cursor omission/new traversal | Same valid logical position; shared inspection budgets charged; no reset of H within traversal. Blocks S4. |
| N20 | Altered/foreign/expired cursor; missing/expired inspection; lost context | Closed errors; no silent restart or client-state reconstruction. Blocks S4/S7. |
| N21 | Empty Journal H=0; last record at H; shrink/replacement/high-water loss | Honest complete-empty or explicit invalid continuation; no stronger absence claim. Blocks S4. |
| N22 | Multiple physical subjects, conflicting outcomes, Run ID reused with changed Binding/ledger | Changed Binding/ledger for reused Run ID => identity_mismatch; multiple physical subjects for exact Run => reported conflict/discrepancy, preserving all observed subjects within bounds. No latest-wins. Blocks S4. |
| N23 | Next matching record exceeds output count or byte budget | Stop before count overflow; oversized exact data errors with no skip/new position. Blocks S4. |
| N24 | Interrupted lifecycle with recorded success; accepted lifecycle Result missing from complete Journal | Preserve both facts/identities and discrepancy; no lifecycle repair/eligibility. Blocks S4/S7. |
| N25 | Entry-only, partial traversal, helper inconsistent/conflict | No final agreement/absence/uniqueness until complete; helper result unchanged. Blocks S4. |
| N26 | Journal missing/inaccessible/corrupt while lifecycle succeeds | Independent Journal error; keep historical lifecycle only under continuing entitlement. Blocks S7. |
| N27 | Every P07 numerical bound: below/at/above; oversize first/next row/response/graph | Preallocation admission and explicit failure, never trim identity/domain or usable prefix. Blocks relevant producer. |
| N28 | Repeated full validation, replay, failed admitted requests and both traversals | Correct shared records/bytes/output/attempt/time charges; no refunds/reset. Blocks S4. |
| N29 | Eight/64 inspections, two traversals, 2-MiB state, fixed 15-minute expiry | context_limit without live eviction; no sliding lifetime; monotonic clock authoritative. Blocks S2/S4. |
| N30 | Admission 1/source,1/principal,2/global; no-queue pressure | Immediate source_busy; active memory ≤64/128 MiB; no writer starvation. Blocks S1/S3/S6. |
| N31 | SQL lock/stall, slow quick_check, Python/encoding/allocation work and native memory | Supported-runtime deadline/cancellation/cleanup proof; no surviving worker holding exclusion. Blocks read-port admission. |
| N32 | DELETE rollback sidecar and WAL/SHM growth/checkpoint/read-only failure on synthetic files | No query writes/recovery/sidecar fallback; full validation stays bounded or explicitly fails. Operational filesystem corroboration required. Blocks S1/S3. |
| N33 | Denial/expiry/budget error reaches UI and retry controls | No automatic retry, empty-success replacement, new cursor or foreign/stale retention. Blocks S7. |
| N34 | Legacy continuation flags and click/keyboard/service/background attempts | Eligibility always unassessed; no command dispatch. Blocks S5/S7. |
| N35 | Unknown approvals/title/risk/stages/progress and failure counts | Unavailable remains unavailable; no fabricated metadata, zero/all-clear or percentages. Blocks S5/S7. |
| N36 | Semantic validation badge, payload Result shell and evidence injection | No signature/digest/tamper/rollback claim, preview or reconstructed Result. Blocks S5/S7. |
| N37 | DAG filters, edge-layout reversal and Workflow river animation | Core decision/domain preserved; no Stage/gate/live-progress inference. Blocks S5/S7. |
| N38 | Source switch, unsupported navigation and mixed mock/real content | Context cleared, unsupported capability explicit, real provenance visible, no hidden catalog/command request. Blocks S7/S8. |

## 9. Future validation commands and review strategy

**None of these execution commands ran during planning.** New test filenames are proposed; invoke them only after implementation and explicit execution authorization, using an approved installed toolchain. Commands do not authorize dependency installation or network access.

| Command group | Future command / evidence |
| --- | --- |
| V0: baseline/identity | git rev-parse HEAD; git status --porcelain=v1 --untracked-files=all; Get-FileHash -Algorithm SHA256 -LiteralPath docs/architecture/control-center/application-boundary-v2.md. Run separately; inspect parked UI ref and preserved work too. |
| V1: new scoped Core tests | python -B -m unittest discover -s tests -p "test_control_center_*.py" -v. Use the individual named slice file pattern for scoped runs; add measured resource/race evidence to assertions. |
| V2: existing lifecycle/DAG regressions | python -B -m unittest discover -s tests -p "test_sqlite_task_run_state.py" -v; repeat separately for test_task_run_state.py, test_controlled_task_run_state.py, test_task_dependency.py, test_task_scheduler.py and test_developer_alpha.py. |
| V3: existing Journal/Result regressions | Same unittest discover form, separately for test_agent_execution_journal.py, test_sqlite_execution_journal.py, test_controlled_execution_journal.py, test_agent_execution_result.py and test_controlled_execution_result.py. |
| V4: UI preparation/integration | In D:/Dev/itru-ui/ui/control-center: npm run typecheck; npm run test:ci; npm run build, each separately. Existing scripts verified in package.json. Test selected decoder/adapter/component specs and actual delivered fixture conformance. |
| V5: delivery/operational acceptance | Commands and harness remain pending H6 mechanism selection. Define authenticated-denial/revocation/disconnect/size/race checks and an approved existing-Run read-only smoke before execution. No speculative service/CLI/network command is prescribed now. |
| V6: final project checks | python -B -m unittest discover -s tests -p "test_*.py" -v; git diff --check; applicable manifest schema/document checks under their future authorized scope. No cached release-pass claim. |

Mechanical checks do not substitute for the required documentation_consistency and independent_review gates. Future implementations need actual changed files, exact source revisions, matrix evidence, supported-platform/resource measurements and separate reviewer judgments. Require architecture/owner consistency, Journal identity/completeness/resource, authority/audience, UI fidelity and documentation sequencing coverage. Do not waive a failed gate because the design was approved.

Canonical archived originals stay byte-preserved; any future lint disagreement with their historical formatting must not be “fixed” by rewriting them under an implementation task.

## 10. P07 resource feasibility and complexity risks

The entire approved profile is retained; no number is increased or validation removed.

| Resource | Approved bound |
| --- | --- |
| Active admission | 1/source, 1/principal, 2/application; no pending query queue |
| Request envelope | 16 KiB before request parsing |
| Graph | Core maximum 1,000 Tasks / 10,000 dependencies; current Alpha work input remains 1..100 Tasks |
| Lifecycle validation | 10,000 events / 16 MiB canonical encoded metadata; 1 MiB/event remains |
| Journal validation/request | 10,000 current records / 16 MiB canonical encoded metadata, including records beyond H; 1 MiB/record remains |
| Journal global scan/page | 1,000 records; returned matches default 50, exact limit 1..100 |
| Response | 2 MiB encoded descriptive metadata, including complete identities/envelope |
| Database preflight | 64 MiB/current database file, before database-wide checks; no sidecar/provisioning fallback |
| Active working memory | 64 MiB/query, 128 MiB/application, including native/decoded/validation/comparison/encoding buffers |
| Coordination wait / capture hold | ≤1 second each; capture hold includes owner lease/exclusion, validation, evaluation and safe cleanup |
| Whole query | ≤10 seconds, including wait/validation/evaluation/encoding; work deadline, not latency SLA |
| Retained observations | Fixed 15 minutes from inspection creation; 8/principal/source, 64/application; ≤2 MiB/inspection including both traversal/comparison/replay state |
| Traversals | 2 live/inspection |
| Cumulative admitted attempts | 128/inspection, including failed attempts, replays, branches and first pages |
| Cumulative validation | 1,000,000 records AND 256 MiB canonical source metadata/inspection |
| Cumulative output | 64 MiB encoded response metadata/inspection, including replay |
| Cumulative active time | 120 seconds/inspection; monotonic Core-held accounting |

Source bytes use existing canonical UTF-8 Core records. Request/response quota encoding follows P07 exactly: deterministic logical JSON, Unicode-scalar key order, no whitespace/floats, canonical decimal-string large numbers, specified ASCII/control escaping, lowercase non-ASCII UTF-16 escapes/surrogate pairs, and rejection of unpaired surrogates. This chooses no transport encoding. Measure expansion and all temporary buffers before oversized allocation; delivery overhead awaits H6.

**Static conclusions:**

- Current lifecycle SQLite timeout is five seconds; ordinary RLock is unbounded and lacks writer priority. close marks closed only after mutex acquisition. Current quick_check/fetchall/reduction/scheduler code has no integrated deadline/cancellation proof. Existing functions cannot simply be advertised as one-second capture.
- Whole-store validation, complete-domain graph pinning and Core scheduler evaluation must occur under capture exclusion. Cleanup must release transaction/lease/exclusion within that hold; returning a timeout while a worker continues is a failure.
- Current Journal validates a whole current snapshot per page and retains records/maps. Incremental row/byte accounting and bounded allocation need semantic-equivalent implementation work and regression comparison.
- At 10,000 matching records and limit 100, at least 100 pages are needed. Full validation repeated 100 times charges 1,000,000 rows. If each snapshot is 16 MiB, it charges 1,600 MiB, exceeding the 256-MiB allowance. Default limit 50 needs at least 200 pages, exceeding 128 attempts. Thus valid per-request data need not be traversable under the cumulative profile.
- At 16 MiB of validation per request, at most 16 such validations fit the cumulative byte budget before other charges. At most 32 maximal 2-MiB responses fit the output allowance. Failed/replayed requests consume the same remaining allowance.
- Sixty-four full retained contexts allow up to 128 MiB retained descriptive state, separate from 128 MiB active working memory. They do not imply a 128-MiB whole-process RSS limit. Runtime baseline/allocator/native overhead must be measured. A 2-MiB inspection cannot always retain a maximum graph plus all comparison/replay state; context_limit is legitimate and no live context may be silently evicted.
- Lifecycle currently uses DELETE journaling; Journal uses WAL. The 64-MiB database-file cap alone does not bound WAL/SHM size, I/O or native mapping. Do not ignore WAL, use immutable mode to bypass current state, checkpoint/repair through a read, or invent a silent sidecar fallback.

**Future measured evidence required:** Supported-runtime SQL interruption and Python cancellation across every phase; rollback/lease release and shutdown under contention; writer wait behavior under sustained readers; native/Python/encoding peak allocations; sidecar/WAL growth and current-snapshot validation cost; fixed-context expiry and accounting; representative and worst supported data/escape/subject distributions. Synthetic fixtures come first. Actual dataset suitability remains unknown until H4 authorizes observation.

**Decision rule:** Keep P07 unchanged unless a Human approves revision. If enforceable but too restrictive for the intended dataset, show explicit exhaustion and recommend a separately reviewed budget/architecture change. If bounded interruption/cleanup or resource accounting cannot be demonstrated, do not admit the reader. Any additional numerical sidecar policy or alternative validation strategy is an architecture decision, not an implementation workaround.

| Risk | Severity / relative effort | Gate / treatment |
| --- | --- | --- |
| Owner availability and one-second safe capture | Highest; S1 XL | S0 measurement and H3/H5; keep unavailable if unsupported |
| Whole-Journal revalidation and traversal amplification | High; S3/S4 XL | Full charge/explicit exhaustion; no cached-prefix shortcut |
| Historical continuation validation interpretation | High decision dependency; small textual clarification may unblock substantial work | H2 before S1/S2; preserve historical validator |
| Metadata authorization/revocation and mechanism topology | High; S6 conditional L/XL | H4/H6 approval, prepublication checks and clearing |
| Exact identities / numeric / observation fidelity | High; S2/S4/S5 L–XL | Closed contracts, parity fixtures and independent review |
| UI mock assumptions | Medium–high; S5/S7 L | Unsupported capabilities explicit; source-aware separate models |
| Dataset suitability / operational evidence | Unknown until approved access | H4/H7; no invented demo or readiness claim |

S/M/L/XL estimate engineering/review demand only. These estimates imply no calendar dates, staffing allocation or authority. Total effort is not the sum of parallel elapsed durations.

## 11. Critical path and safe parallel work

Minimum Core prerequisites before real UI integration are trusted source/policy/budget semantics; admitted owner-managed passive lifecycle capture; InspectRun; established bounded Journal resources; retained contexts/frozen traversal; ReadRunJournal; then the separately approved delivery/authentication boundary. Existing CLI history is not an intermediate integration shortcut.

Critical path: **S0 → S1 → S2 → S4 → S6 → S7 → S8**, with S3 required before S4. S1 and S3 are the highest implementation risks, and H2/H3/H5/H6 can extend the path.

Safe parallel implementation after separate authorization:

- S1 lifecycle owner coordination and S3 Journal resource work, once shared admission/lease/budget interfaces are agreed.
- S5 synthetic canonical decoders, adapters, unavailable states, disabled controls and layout tests alongside Core development. Fixtures must be explicitly approved contract examples, not operational facts.
- Independent threat/acceptance review and definition of the future H6 decision packet. Selection itself still needs separate authorization.
- Core/UI conformance fixture review once S2/S4 produce actual outputs.

Do not transfer parked SCRUM-81, reuse the UI's older Core copy as current authority, activate the real provider prematurely or use mocks to fill absent operational facts.

## 12. Recommended first implementation authorization

Authorize **S0 only — synthetic feasibility and prerequisite package**.

The concrete proposed scope is: new isolated synthetic feasibility/contract fixtures and tests; source/policy/budget interface definitions; full mutation/teardown audit; measurement instrumentation for one-second capture/cancellation/cleanup, repeated Journal validation, allocation, quota encoding and retained contexts; documented H2/H3/H5 decisions. Any production-file hook required by a feasibility experiment must first be identified in the scoped authorization; do not broaden the approved changed-path set silently.

Acceptance of S0 requires a reviewable go/no-go report with measured conditions, exact limits, unresolved risks and Human decision requests. It does not select/open an operational source, establish a production owner, grant an audience, select a transport, expose either query or enable UI operations.

If H2 or feasibility requires architecture revision, return that decision before S1/S2 implementation. After S0 acceptance, request separate authorization for the next independently reviewable slices. No completion date is proposed without capacity evidence.

## 13. Independent planning review

Two distinct reviewer executions evaluated the actual complete 438-line draft against the complete approved v2 and relevant source, after contributing source-analysis notes. Their full-plan judgments are separate from those earlier notes. The reviewed draft SHA-256 was **71e7eeb3254cff5cd9ab2e9280507a65322e4db55f8225fa963f1dd1eca021db**; it identifies that review packet, not this final report containing the receipts.

| Reviewer execution / scope | Outcome / findings / disposition |
| --- | --- |
| /root/locate_architecture — Core ownership, all mutation/recovery/shutdown paths, consistency, UI fidelity, disabled commands, P01–P10 traceability, all 12 slice dimensions and sequencing | **APPROVE for static planning.** No material or required-change findings. Optional low clarification: distinguish reused Run ID with changed Binding/ledger from competing physical subjects for the exact Run. N22 now explicitly assigns identity_mismatch to the former and conflict/discrepancy to the latter. |
| /root/archive_integrity — Journal identities, frozen-H coverage, current whole-snapshot validation, all P07 limits/encoding/charging, metadata authority/revocation, failure isolation, dependencies and future validation | **APPROVE for static planning; no findings.** Confirmed static amplification arithmetic and separation from unmeasured feasibility, S0-only recommendation, explicit H2 decision and admission-blocking resource proof. |

Both reviewers read the complete plan and complete v2; neither implemented product changes or relied solely on the author's summary. They are distinct agent executions, not Human signatories or a claim of a different Provider. The final edits record these review results, sharpen N22 and explicitly retain the existing Alpha input maximum; they do not revise approved architecture.

No unresolved required planning-review finding remains. H2 and the other explicit Human/feasibility gates remain outstanding decisions, not waived findings. This planning exercise assigns **no formal Quality Gate PASS, implementation authorization or runtime acceptance**. Future implementation still requires all applicable actual Quality Gates and final Human review.

## 14. Outstanding decisions and blockers

- H1 implementation authorization remains absent; all S0–S8 entries are proposals.
- H2 historical-validation/eligibility wording requires explicit Human clarification before S1/S2.
- Owner setup/topology and safe bounded capture are unproven; no suitable live owner is assumed.
- Actual source/dataset/Run, full metadata audience, policy revisions and deployment environment remain unselected/unapproved.
- P07 enforceability and intended-dataset completion are unmeasured; static budget limitations above are established.
- Transport/authentication mechanism and mechanism-specific files/validation commands await H6.
- No operational evidence, tests, builds, services, runtime/import/CLI/diagnostic processes or network probes were run for this plan.
- Existing tests and prior design/archive approvals establish available evidence, not current implementation acceptance.

No repository, product, schema, configuration, Task, UI, Git branch/ref/index or external application changes are authorized by or performed for this planning report. No operational store or D6-E/B1 workspace was accessed.

## 15. Final Human Control status

**Planning deliverable only. No implementation authorization, operational-data permission or transport decision is granted.**

The recommended first slice is **S0**. Please separately authorize its precise implementation and synthetic validation scope before any code changes or execution. Resolve H2 before dependent reader implementation. Human review of this plan and each subsequent slice remains required.

**STOP AT HUMAN CONTROL.**

