# ITRU Core ↔ Control Center Boundary Investigation

**Date:** 17 October 2026  
**Scope:** Static, read-only architecture investigation  
**Status:** Investigation delivered; all proposed contracts remain **unapproved**  
**Implementation authorization:** None

## 1. Executive summary

**Core contains enough implemented semantics to support a narrow, read-only Developer Alpha integration. It does not yet expose a canonical application contract that the Control Center can consume.**

The smallest useful slice is:

**Existing Run → exact lifecycle details → Task dependency graph and Core scheduler assessment → recorded Result summary and Journal evidence.**

Five findings determine the boundary:

1. **Core already implements lifecycle, continuation, DAG evaluation and scheduler decisions.** Several active UI comments still describe these capabilities as pending.
2. **Every operational UI screen currently uses fabricated data.** `ControlCenterDataSource` is a useful presentation seam, but its return types are UI models rather than Core application contracts.
3. **Read-only integration has an ownership prerequisite.** Constructing `SqliteTaskRunStateStore` acquires exclusive ownership and performs recovery, potentially changing lifecycle state. A UI query must not independently open this store.
4. **Historical Result summaries are available; historical Result payloads are not.** Journal retrieval cannot reconstruct a live `AgentExecutionResult`, its payload or its authority.
5. **Approval, execution and continuation controls require separate contracts and approval.** Their existence in UI presentation does not authorize activation.

### Verified repository baselines

| Repository/reference | Recorded baseline | Observed state |
|---|---|---|
| Core, `D:\Dev\ai-engineering-orchestra` | `e7af2c4c01645a05e6e78ccea7e845dafc455399` | HEAD matches; branch `itru-064-developer-alpha-release`; working tree clean |
| UI, `D:\Dev\itru-ui` | `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67` | HEAD matches; branch `ui/developer-alpha-integration-qa-polish` |
| UI working tree | Preserve all changes | One untracked file: `ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md` |
| Parked SCRUM-81 | `61e817c1f7a2c3987710a73366b516d792402520` | Branch `ui/itru-062-contract-i18n-rtl` still resolves to that commit |

The final Git inspection matched the opening state. No files, branches, worktrees or external records were changed. The D6-E/B1 workspace was not accessed.

Core’s [ITRU-064 task](D:/Dev/ai-engineering-orchestra/.ai/tasks/ITRU-064-developer-alpha-release/task.yaml) records `completed`; its [completion report](D:/Dev/ai-engineering-orchestra/.ai/tasks/ITRU-064-developer-alpha-release/completion-report.md) records final Human closure and a **CLI-only Developer Alpha**, explicitly excluding UI integration.

The UI checkout contains an older Python/Core snapshot. This investigation uses the designated Core repository as authoritative for current implementation.

## 2. Verified Core inventory

The following describes implemented source behavior. Test files were inspected as supporting evidence; **tests were not executed**.

### Capability contracts

| Capability | Source and entry point | Input → output | Persistence | Authority requirements and limitations |
|---|---|---|---|---|
| Repository Task inspection | [itru/inspect_task.py](D:/Dev/ai-engineering-orchestra/itru/inspect_task.py), `inspect_task`; [itru/list_tasks.py](D:/Dev/ai-engineering-orchestra/itru/list_tasks.py), `discover_tasks` | Task directory/catalog configuration → `TaskInspectionResult` or `TaskInventoryResult`, including definition status, Workflow resolution, effective gates and Human controls | Reads repository artifacts | Definition inspection does not enroll Tasks, supply operational Run state, execute gates or establish closure |
| Alpha work definition | [itru/alpha_config.py](D:/Dev/ai-engineering-orchestra/itru/alpha_config.py), `load_config`, `validate_work`; [itru/developer_alpha.py](D:/Dev/ai-engineering-orchestra/itru/developer_alpha.py), `load_work`, `context` | Closed configuration and 1–100 explicit work definitions → validated graph; `context` adds persisted snapshot and scheduler decision | `load_work` writes immutable `work.json` and enrolls Tasks | Alpha work contains `id`, `objective`, `resource`, `dependencies`; it is not a complete repository `task.yaml`. No automatic catalog discovery |
| Immutable Run identity | [itru/agent_execution_run.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_run.py), `AgentExecutionRun`; [itru/agent_execution_contract.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_contract.py), `AgentExecutionContract` | Opaque Run ID plus exact eleven-field Contract → immutable attempt identity | No persistence in these value modules | Identity alone grants no authority and contains no lifecycle state |
| Lifecycle queries | [itru/sqlite_task_run_state.py](D:/Dev/ai-engineering-orchestra/itru/sqlite_task_run_state.py), `get_task`, `get_run`, `checkpoint`, `page` | Exact IDs or bounded keyset cursor → immutable `TaskSnapshot`, `RunSnapshot`, `Checkpoint`, tuples, or absent lookup | Dedicated SQLite state store, reconstructed from validated append-only events | Requires a live owned session. Pages contain 1–100 items; Task pages and per-Task Run pages are individually transactional. No global chronological Run listing |
| Lifecycle changes | Same store: `enroll`, `register_run`, `start_run`, `record_result`, `transition`; [itru/task_run_state.py](D:/Dev/ai-engineering-orchestra/itru/task_run_state.py), `apply_event` | Definition/subject, expected Task revision, original Result or explicit transition/reference → updated `TaskSnapshot` | Atomic event append and Task-wide revision CAS | `record_result` requires genuine unchanged original Result membership. Completion requires governance reference and lifecycle eligibility; the store does not evaluate external governance |
| Task DAG | [itru/task_dependency.py](D:/Dev/ai-engineering-orchestra/itru/task_dependency.py), `build_task_graph`, `validate_task_graph`, `prerequisites` | Explicit node/edge tuples → canonical `TaskGraph` and prerequisite IDs | None | Closed graph; rejects duplicates, missing endpoints, self-edges and cycles. Maximum 1,000 Tasks/10,000 dependencies. No inferred Stage or subagent edges |
| Dependency readiness and scheduling | [itru/task_scheduler.py](D:/Dev/ai-engineering-orchestra/itru/task_scheduler.py), `evaluate_schedule` | Graph, coherent `SchedulingSnapshot`, explicit concurrency → frozen `SchedulerDecision` | None | Decisions describe selection; they reserve no capacity, create no Runs and grant no authority. Missing observations suppress all new selection |
| Assignment handoff | Same scheduler, `prepare_assignment_handoff`; [itru/assignment.py](D:/Dev/ai-engineering-orchestra/itru/assignment.py), `validate_assignment`, `validate_assignment_set` | Selected Task and explicit Assignment/context → checkpoint-bearing handoff or validation findings | None | Handoff checks selection and Assignment shape; contextual validation remains necessary. No Actor choice, Grant, admission or invocation |
| Actor selection | [itru/actor_selection.py](D:/Dev/ai-engineering-orchestra/itru/actor_selection.py), `select_actor`; [itru/actor_coverage.py](D:/Dev/ai-engineering-orchestra/itru/actor_coverage.py), `evaluate_actor_role_coverage` | Supplied Task/Workflow/Role, Actors and availability observations → competency/availability findings and selection result | None | Outcomes are `selected`, `ambiguous`, `indeterminate`, `no_candidate`. No ranking, reservation, persistent roster or health monitoring |
| Execution prerequisites | [itru/agent_action_prerequisite.py](D:/Dev/ai-engineering-orchestra/itru/agent_action_prerequisite.py), `assess_agent_action_prerequisites`, with candidate/capability/permission/authorization modules | Coherent supplied observations for one exact action → prerequisite assessment | None | Availability, capability, environment permission and authorization evidence remain separate. Positive assessment is not an authenticated execution credential |
| Authorization evidence | [itru/agent_execution_authorization_evidence.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_authorization_evidence.py), `validate_agent_execution_authorization_evidence` | Exact action-scoped caller assertions → normalized `granted`/`denied` evidence and findings | None | Assertions are not authenticated Human decisions. Missing evidence means unproven authorization, not denial. No approval queue |
| Authenticated authority and admission | [itru/agent_execution_authorization_grant_producer.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_authorization_grant_producer.py), `AgentExecutionAuthorizationGrantProducer.produce`; [itru/local_operational_trust.py](D:/Dev/ai-engineering-orchestra/itru/local_operational_trust.py), `LocalOperationalTrustCoordinator.admit`, `load_authoritative_admission`, `revoke` | Exact Run, authenticated principal and action-bound proof → production/admission/history/revocation result | Admission, dispatch, claim and Entry facts use the authorization ledger | Trusted composition, ownership, entitlement and freshness remain mandatory. Process-local proofs cannot be reconstructed from UI JSON or persisted evidence |
| Controlled Tool execution | [itru/alpha_authority.py](D:/Dev/ai-engineering-orchestra/itru/alpha_authority.py), `AlphaExecution.invoke`; private [itru/_execution_entry_and_controlled_invocation.py](D:/Dev/ai-engineering-orchestra/itru/_execution_entry_and_controlled_invocation.py), `_ControlledInvocationCoordinator.invoke` | Fresh approved Run through admission, claim and JIT preparation → Entry disposition, invocation observation, optional original Result and Journal receipt | Permanent Entry in ledger; optional separate Journal recording | Supported Alpha Tool is bounded native `repository_file_read`. No general public Tool execution operation. Entry consumption does not prove completion |
| Agent Execution Result | [itru/agent_execution_result.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_result.py), `AgentExecutionResult` | Original controlled invocation → immutable six-field terminal evidence | Live, process-local evidence; no Result persistence or restoration API | Outcomes: `succeeded`, `failed_before_effect`, `effect_ambiguous`. Success payload is raw bytes, maximum 65,536. Disclosure requires separate audience authorization |
| Execution Journal | [itru/agent_execution_journal.py](D:/Dev/ai-engineering-orchestra/itru/agent_execution_journal.py), `ExecutionJournalRecorder.observe_result`, `reconcile`; [itru/sqlite_agent_execution_journal_store.py](D:/Dev/ai-engineering-orchestra/itru/sqlite_agent_execution_journal_store.py), `lookup`, `page` | Trusted observations → receipts; exact subject/cursor → validated descriptive `JournalRecord`s | Separate append-only SQLite Journal; stable high-water traversal | Only `entry_observed` and `result_observed`. Result summaries exclude content. Metadata persistence/audience authorization is separate from execution permission |
| Governed continuation | Lifecycle store `continue_task`; `task_run_state.continuation_eligible` | Exact current Checkpoint, new complete Binding/ledger subject, reason, fresh trusted authorizer → new pending Run and updated Task | One serialized lifecycle transaction | Never reopens an old Run. Interrupted or ambiguous history blocks continuation. Authorizer receipt does not grant downstream execution authority |
| Lifecycle/Journal comparison | `task_run_state.reconcile_run` | Run snapshot and exact validated Journal subset → `EvidenceReconciliation` | None | States: `missing`, `entry_only`, `recorded_result`, `conflict`, `inconsistent`. Diagnostic only; cannot repair lifecycle or manufacture a Result |
| Alpha application composition | `developer_alpha.make_plan`, `execute`, `history`, `command`; [itru/cli.py](D:/Dev/ai-engineering-orchestra/itru/cli.py) | Explicit configuration/work/action and fresh approval digest → plans, execution summaries or descriptive history | Composes the existing stores | Existing executable composition, but no canonical Control Center contract, application DTO schema or transport |

The semantic sources for these implemented foundations are:

- [core/task-run-state-specification.md](D:/Dev/ai-engineering-orchestra/core/task-run-state-specification.md)
- [core/task-scheduler-specification.md](D:/Dev/ai-engineering-orchestra/core/task-scheduler-specification.md)
- [core/agent-execution-result-specification.md](D:/Dev/ai-engineering-orchestra/core/agent-execution-result-specification.md)
- [core/agent-execution-journal-specification.md](D:/Dev/ai-engineering-orchestra/core/agent-execution-journal-specification.md)
- [docs/developer-alpha.md](D:/Dev/ai-engineering-orchestra/docs/developer-alpha.md)

### Lifecycle, failure and terminal semantics

| Subject | Implemented semantics |
|---|---|
| Task states | `planned`, `in_progress`, `blocked`, `completed`, `cancelled` |
| Run progression | `pending → running → succeeded / failed_before_effect / effect_ambiguous` |
| Stop/recovery | Pending becomes `cancelled`; running becomes `interrupted`; affected Task becomes blocked |
| Task cancellation | Terminal Task cancellation preserves unresolved effects; it does not prove a running operation had no effect |
| Run terminal states | `succeeded`, `failed_before_effect`, `effect_ambiguous`, `interrupted`, `cancelled`; no reopening |
| Successful Run | Leaves its Task `in_progress`; does not establish governance completion |
| Dependency satisfaction | Only persisted Task `completed` satisfies a prerequisite |
| Continuation | Eligible Task receives a new unique Run; never restores the old executor or capability |
| Uncertainty | Missing Result, interrupted state and ambiguous outcome remain distinct; none permits automatic replay |
| Stale state | Revision/checkpoint conflict, not a persisted lifecycle state |

### Scheduler semantics

`evaluate_schedule` exposes three decision states:

- `evaluated`
- `incomplete_snapshot`
- `over_capacity`

Per-Task evaluation states are:

`unresolved`, `unsafe`, `terminal`, `active`, `manual`, `blocked`, `ready`.

Pending and running Runs occupy capacity. Selection uses lexical Task-ID order and applies only to eligible initial work. The foundation accepts concurrency 1–100; the Alpha configuration restricts advisory workers to **one or two**, with **serialized Tool execution**.

There is no persistent ready queue, autonomous scheduling loop, streaming execution progress, percentage-complete model, timeout lifecycle or distributed scheduler.

### Result and Journal distinctions

A Result identity is:

```text
(ledger_instance_id, authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

It is not a newly allocated `result_id`.

Journal records retain exact subject/authority context and a content-free outcome summary. They do not retain payload bytes, a serialized live Result or its private membership.

`ExecutionJournalRecorder.reconcile` additionally supports ledger/Journal comparison using `recorded_result`, `unresolved_result`, `no_entry_evidence`, `evidence_unavailable`, and `integrity_failure`. These are distinct from `task_run_state.reconcile_run` results.

### Existing query constraints

- Lifecycle store construction performs recovery; it is not a passive read-only open.
- Lifecycle queries validate the complete store, and its history is bounded to 10,000 events.
- Lifecycle pages are keyset ordered by IDs, not execution recency.
- Journal pages preserve `(journal_id, high_water, last_sequence)`.
- `developer_alpha.history` returns Task/Run snapshots, selected Task IDs and up to 100 Journal records.
- The Alpha CLI history response returns an `after` sequence but does not preserve its initial high-water value across separate commands. It therefore cannot be treated as an existing frozen multi-request application traversal.
- No transaction spans lifecycle, Journal, authorization ledger and native effects.

### Static test evidence

Relevant inspected tests include:

| Area | Evidence |
|---|---|
| Lifecycle, recovery, continuation, CAS and ownership | `tests/test_task_run_state.py`, `tests/test_sqlite_task_run_state.py`, `tests/test_controlled_task_run_state.py` |
| DAG closure, cycles, missing snapshots and capacity | `tests/test_task_dependency.py`, `tests/test_task_scheduler.py` |
| Original Result provenance and effect classification | `tests/test_agent_execution_result.py`, `tests/test_controlled_execution_result.py` |
| Journal ordering, pagination, conflicts and missing Results | `tests/test_agent_execution_journal.py`, `tests/test_sqlite_execution_journal.py`, `tests/test_controlled_execution_journal.py` |
| Alpha approval, governed completion, fresh resume and recovery | `tests/test_developer_alpha.py`, notably `test_03_stale_approval_and_fresh_resume` and `test_06_running_restart_interrupted_no_journal_success_repair` |

These establish available test coverage, not a newly verified passing result.

## 3. Verified UI inventory

In this section, paths below `src/app/` are relative to:

`D:\Dev\itru-ui\ui\control-center`.

### Data-source boundary

[src/app/data/control-center-data-source.ts](D:/Dev/itru-ui/ui/control-center/src/app/data/control-center-data-source.ts) declares exactly nine query methods:

```text
getOverview
listRuns
getRun
listTasks
getTask
listAgents
listApprovals
listDagScenarios
getDagGraph
```

All return RxJS Observables. Single-item `undefined` means not found in that source.

The boundary has:

- no commands;
- no source-context argument;
- no revisions or pagination contract;
- no application error taxonomy;
- no freshness guarantee;
- no polling or event delivery guarantee.

[src/app/app.config.ts](D:/Dev/itru-ui/ui/control-center/src/app/app.config.ts) binds it exclusively to `MockControlCenterDataSource`.

### Screens and direct consumers

| Consumer | Data-source operation | Required operational data and behavior |
|---|---|---|
| `src/app/app.ts`, `App` | `listApprovals`; `originLabel` | Source label and awaiting-approval navigation count |
| `features/overview/overview.ts`, `Overview` | `getOverview` | Tasks, Runs, Actors and approvals; derives counts, attention lists, “recent” Tasks and portfolio river |
| `features/runs/runs.ts`, `Runs` | `listRuns` | Contract identity, presentation state, activity labels, Result/continuation flags; local filters |
| [features/runs/run-detail.ts](D:/Dev/itru-ui/ui/control-center/src/app/features/runs/run-detail.ts), `RunDetailPage` | `getRun(runId)` | Complete Contract, parent Task title, Workflow stages, sibling Runs, timeline, evidence, Result and continuation presentation |
| `features/tasks/tasks.ts`, `Tasks` | `listTasks` | Task metadata/status, risk, complexity, mode, Workflow, approval level, Run associations and activity labels |
| [features/tasks/task-detail.ts](D:/Dev/itru-ui/ui/control-center/src/app/features/tasks/task-detail.ts), `TaskDetailPage` | `getTask`, `listRuns`, selected `getRun` | Definition/scope/dependencies/gates/stages, Task Run history and selected Run evidence |
| `features/agents/agents.ts`, `Agents` | `listAgents` | Actor identity/name/kind, covered Roles, availability, runtime applicability and assignments |
| `features/approvals/approvals.ts`, `Approvals` | `listApprovals` | Presentational awaiting/granted/denied groups, action description, subject links and authority ID; no decision submission |
| [features/flow/flow.ts](D:/Dev/itru-ui/ui/control-center/src/app/features/flow/flow.ts), `Flow` | `listDagScenarios`, `getDagGraph` | Scenario graph, node/edge identity, scheduler-looking states/counts, stale flag and linked evidence; local filtering and inspection |
| `features/not-found/not-found.ts` | None | Routing fallback only |

### Shared components, adapters and hooks

| Files/symbols | Operational inputs and responsibilities |
|---|---|
| `shared/result-shell.ts`, `ResultShell` | Renders outcome, diagnostic, provenance and optional text/binary payload preview |
| `shared/execution-timeline.ts`, `ExecutionTimeline` | Timeline entries, local filters and selected entry; current model is not a canonical Journal record |
| `shared/evidence-panel.ts`, `EvidencePanel` | Evidence categories/outcomes, previews, unavailable notices and asserted integrity badges |
| `shared/continuation-shell.ts`, `ContinuationShell` | Continuation presentation, Result outcome, loading/error inputs; displayed resume button is hard-disabled |
| `shared/nile/nile-flow.ts`, `NileFlow` | Presentation topology, selection, decorative flow and navigation events |
| `shared/nile/nile-topology.ts` | `buildRunTopology`, `buildPortfolioTopology`; creates drawing topology and derives visual Stage states from Run presentation |
| `shared/nile/dag-flow.ts`, `DagFlow` | Graph layout, selection, dependency highlighting, zoom and list view |
| `shared/nile/dag-node-inspector.ts`, `DagNodeInspector` | Subject identity, related nodes and embedded Result/timeline/evidence/continuation shells |
| `shared/nile/scheduler-panel.ts`, `SchedulerPanel` | Supplied counts and node states; emits filter/selection events |
| `shared/status-badge.ts`, `shared/stat-tile.ts`, `shared/page-header.ts` | Leaf rendering of supplied operational labels/counts/identity |
| `shared/state-panel.ts`, `StatePanel` | Loading, empty, error, absent, unavailable, unknown, blocked and no-evidence presentation |
| [data/result-adapter.ts](D:/Dev/itru-ui/ui/control-center/src/app/data/result-adapter.ts), `adaptResultReadModel` | Formats UI Result models and outcome explanations; suppresses failure payload presentation |
| `data/timeline-adapter.ts` | `adaptTimelineReadModel(s)`, `adaptEvidenceReadModel(s)`; formats supplied evidence and links |
| [data/continuation-adapter.ts](D:/Dev/itru-ui/ui/control-center/src/app/data/continuation-adapter.ts), `adaptContinuationReadModel` | Maps supplied continuation metadata; blocks ambiguous outcomes and disables all actions |
| [data/dag-adapter.ts](D:/Dev/itru-ui/ui/control-center/src/app/data/dag-adapter.ts) | `adaptDagNodeReadModel`, `adaptDagEdgeReadModel`, `adaptDagGraphReadModel`; visual mapping and linked presentations |
| [shared/load-state.ts](D:/Dev/itru-ui/ui/control-center/src/app/shared/load-state.ts) | `loadState$`, `toLoadState`, `toLoadStateFor`; loading/ready/error wrapping and key-change rereads |

There are no separate operational hook files. Angular signals, computed values, effects and the load-state helpers provide that behavior.

`ThemeService` persists theme preference only; it is not an operational state store.

### View-model inventory

[data/models.ts](D:/Dev/itru-ui/ui/control-center/src/app/data/models.ts) owns these UI model families:

- Task: `TaskSummary`, `TaskDetail`, `WorkflowStageView`.
- Run: `RunContractView`, `RunSummary`, `RunDetail`.
- Continuation: `RunContinuationReadModel`, `RunContinuationPresentation`.
- Timeline/evidence: `TimelineItemReadModel`, `TimelineItemPresentation`, `EvidenceItemReadModel`, `EvidenceItemPresentation`.
- Result: `AgentExecutionResultReadModel`, `AgentExecutionResultPresentation` and identity/payload/diagnostic submodels.
- Actors/approvals/overview: `AgentSummary`, `AgentAssignmentView`, `ApprovalItem`, `OverviewPresentation`.
- Drawing: `NileTopology`, `DagGraphReadModel`, node/edge read models and presentations, `SchedulerSummaryReadModel`.

These types are explicitly UI-owned. They must not become canonical merely by attaching a real data source.

### Mock implementation and update behavior

`data/mock/mock-control-center-data-source.ts` implements every query using `of(...)` and optional simulated latency, defaulting to 160 ms.

`mock-data.ts` fabricates Task/Run associations, activity labels, Results, timeline entries, evidence, Actors, approvals and continuation metadata. `mock-dag-data.ts` supplies eleven graph scenarios, including subagents, joins, stale data and empty graphs.

No operational HTTP client, polling loop, event subscription protocol or offline cache was found. Observables can support future repeated delivery, but current implementation does not establish such behavior.

### Unsupported assumptions and alignment gaps

1. **Lifecycle vocabulary is stale.** UI comments say Core defines no Run status, continuation or scheduler semantics. Current Core implements all three.
2. **Interrupted continuation is incompatible.** `adaptContinuationReadModel` can present interrupted work as available when its input says so. Current Core blocks continuation for interrupted history.
3. **Result availability is underspecified.** A nullable Result cannot distinguish a recorded summary, unavailable live evidence, lost payload, disabled recording or an unfinished attempt.
4. **`configuredRoute` is not a canonical Result Binding field.** Core `AgentOperationToolBinding` contains only `run` and `tool_id`; the UI requires an additional route label.
5. **Generic timeline/evidence exceeds Journal coverage.** Stage transitions, gate outcomes, command output, diffs and review notes are not the Journal’s two event kinds.
6. **Integrity labels exceed current guarantees.** The UI can display signature/digest/tamper labels; Core Journal provides no cryptographic authenticity or rollback proof.
7. **Recency is fabricated.** Mock ordering and labels cannot be replaced with Run-ID sorting. `TaskDetailPage` takes the last listed Run as latest; Core keyset Run pages are ID ordered.
8. **Alpha work lacks several required Task presentation fields.** Title, risk, complexity, scope and approval-level aggregation cannot be invented to fill the existing model.
9. **Adapters are presentation functions, not validation boundaries.** For example, preview formatting does not itself enforce authoritative provenance or input size limits.
10. **Offline/freshness handling is partial.** Graph and continuation stale notices exist, but there is no common freshness envelope or retained-data policy. Shell approval and scenario-list subscriptions also bypass the common load-state wrapper.

The existing untracked readiness document was inspected as contextual evidence. Its claimed scheduler names such as `TaskDag` and uppercase lifecycle-like scheduler states do not match current `TaskGraph`/`SchedulerDecision` implementation. Its earlier test-pass statements were not adopted as fresh validation.

## 4. Contract gap matrix

**Status meaning:** Available = Core semantic primitive exists; Partial = application projection/composition remains; Missing = required semantic contract absent; Unknown = cannot establish through this static investigation.

Here, `U/` abbreviates UI repository path `ui/control-center/src/app/`.

| UI capability | Core capability | Core evidence | UI evidence | Integration status | Authority concerns | Missing contract | Priority |
|---|---|---|---|---|---|---|---|
| Exact Run details | Exact persisted Run lookup | `itru/sqlite_task_run_state.py::get_run`; `task_run_state.py::RunSnapshot` | `U/features/runs/run-detail.ts::RunDetailPage` | Partial | Query through approved owner; exact namespace | Application projection/context and evidence availability | P0 |
| Task operational state | Persisted Task snapshot | `sqlite_task_run_state.py::get_task` | `U/data/models.ts::TaskDetail` | Partial | Separate operational state from definition mirror | Definition association and optional metadata | P0 |
| Canonical Run state | Seven implemented lifecycle states | `task_run_state.py::RUN_STATES`, `apply_event` | `U/data/models.ts::PresentationState` | Partial | UI cannot infer transitions | Lossless canonical-state presentation | P0 |
| Task DAG | Closed Task dependency graph | `task_dependency.py::build_task_graph` | `U/data/dag-adapter.ts`; `U/shared/nile/dag-flow.ts` | Partial | Graph is evidence, not authority | Scope identity, edge orientation and layout projection | P0 |
| Scheduler display | Readiness, occupancy, selection | `task_scheduler.py::evaluate_schedule` | `U/shared/nile/scheduler-panel.ts` | Partial | Selection reserves nothing; no dispatch permission | Exact decision/evaluation projection and revision coverage | P0 |
| Recorded Result outcome | Lifecycle Result identity plus Journal summary | `record_result`; `SqliteExecutionJournalStore.lookup` | `U/shared/result-shell.ts` | Partial | Summary cannot become live Result | Recorded-summary model and gap states | P0 |
| Historical payload preview | No retained payload retrieval | `agent_execution_result.py::AgentExecutionResult`; Result spec §10 | `U/data/models.ts::ResultPayloadReadModel` | Missing | Content disclosure/retention needs separate authorization | Payload availability and authorized disclosure contract | P2 |
| Journal/history | Validated records and stable cursor | `sqlite_agent_execution_journal_store.py::page`, `lookup` | `U/shared/execution-timeline.ts` | Partial | Preserve provenance and metadata audience | Subject-scoped projection, cursor/completeness and error semantics | P0 |
| Lifecycle/Journal disagreement | Pure reconciliation | `task_run_state.py::reconcile_run` | `U/features/runs/run-detail.ts` | Partial | Journal cannot repair lifecycle | Dual-state reconciliation presentation | P0 |
| Workspace-wide Run list/recency | Per-Task Runs and ID pages | `sqlite_task_run_state.py::page`; `developer_alpha.py::history` | `U/features/runs/runs.ts`; Task latest-Run selection | Partial | No cross-project ID joins | Scope, aggregation, ordering and pagination | P1 |
| Rich Task definition view | Repository inspection or limited Alpha work | `inspect_task.py::inspect_task`; `alpha_config.py::validate_work` | `U/features/tasks/task-detail.ts` | Partial | Do not conflate repository and Alpha Projects | Definition-source association and missing-field policy | P1 |
| Actor roster/availability | Supplied Actor/availability assessment | `actor_selection.py::select_actor`; `alpha_authority.py::_Facts` | `U/features/agents/agents.ts` | Partial | Availability is an observation, not liveness or entitlement | Inventory source, observation freshness and assignment projection | P1 |
| Awaiting approvals | No persistent pending-request queue | Authorization evidence validator; `developer_alpha.py::make_plan` | `U/features/approvals/approvals.ts`; App badge | Missing | No evidence ≠ denial; plan ≠ grant | Request identity/lifecycle and authenticated decision handling | P2 |
| Approval submission | Local Alpha digest/proof composition | `require_approval`; `AlphaExecution.invoke` | Data source has no command | Partial | Local OS-user assumption cannot silently extend to a UI caller | Action-bound authentication, freshness and receipts | P2 |
| Resume/continuation | Fresh new-Run continuation | `continue_task`; `make_plan(action='resume')` | `U/data/continuation-adapter.ts` | Partial | Exact checkpoint, fresh authorizer, then fresh execution authority | UI command contract and canonical eligibility display | P2; safe disabled state P0 |
| Subagent/join/checkpoint DAG | No equivalent execution DAG | `task_dependency.py::TaskGraph` | `U/data/models.ts::DagNodeKind`; mock DAGs | Missing | Drawing topology must not imply governed execution | Separate future semantic model, if needed | P2 |
| Runtime progress | Coarse durable markers and terminal observations | `start_run`; `developer_alpha.py::execute` | Run activity labels and animated flow | Missing for detailed progress | Animation cannot establish liveness | Progress taxonomy, timestamps and observation guarantees | P2 |
| Generic evidence/gate outcomes | Journal does not provide these | `agent_execution_journal.py` event taxonomy | `U/shared/evidence-panel.ts` | Missing | Cannot manufacture gate PASS or integrity proof | Approved evidence producers and provenance contracts | P2 |
| Error/stale/offline handling | Core exceptions, revisions and Journal cursors | State/Journaling modules | `U/shared/load-state.ts`; Flow stale banner | Partial | Unavailable data must not become empty success | Application errors, freshness and incomplete-read semantics | P0 |
| Real persisted dataset | No workspace/store opened here | Static source only | Mock implementation only | Unknown | Existing metadata audience and workspace access must be authorized | Explicit approved source and existing Run selection | P0 |

## 5. Proposed transport-neutral application boundary

**Everything in this section is an unapproved proposal.**

The boundary should expose descriptive application values while retaining Core ownership of lifecycle, scheduling, authority, invocation, persistence, continuation eligibility and terminal outcomes.

It should not expose Python capability objects, database handles, filesystem paths supplied by the UI, private execution APIs or generic operation dispatch.

### Minimum first-slice queries

Two semantic query operations are sufficient for the proposed vertical slice.

| Proposed query | Request semantics | Response semantics |
|---|---|---|
| `InspectRun` | Approved source-context reference and exact Run ID | Exact Run/Contract/Binding, owning Task state and revision, definition reference, approved definition metadata, complete Task graph and Core scheduler assessment for the configured domain |
| `ReadRunJournal` | Same context and exact Run subject; optional traversal cursor; bounded limit | Descriptive matching Journal records, retained Journal coordinates/provenance, recorded summaries, traversal completeness and explicit evidence gaps/conflicts |

`InspectRun` must preserve canonical lifecycle values. The UI may derive colors and labels, but it must retain the underlying states and the distinction between Task state, Run state and scheduler evaluation.

`ReadRunJournal` requires a new application projection contract. Existing Core supports exact subject lookup and whole-Journal pagination; it does not already provide this complete Run-scoped application operation.

Where lifecycle contains a physical Result identity, lookup can use it directly. Otherwise, a validated traversal must match complete Binding/ledger evidence. Run-ID equality alone is insufficient. Multiple conflicting physical subjects must be reported rather than resolved by choosing the latest.

A completed traversal with no matching records means no matching recorded evidence in that traversal. It does not prove no execution or effect.

### Additional queries only when their screens enter scope

- Task page/detail and per-Task Run page.
- Graph assessment as a separately reusable query.
- Actor observations from an explicitly configured source.
- Overview aggregation with declared coverage.
- Approval evidence views after defining their source and meaning.

The first slice need not reproduce every existing mock screen.

### Identity, versioning and consistency

| Concern | Proposed semantics and evidence basis |
|---|---|
| Source identity | Trusted configuration resolves an approved context to exact Project/Store and relevant ledger/Journal identities. UI routes must not rely on globally unique Run IDs |
| Task identity | Exact Project-scoped ID plus pinned definition reference |
| Run identity | Store-scoped Run ID and unchanged complete Contract/Binding |
| Result identity | Preserve the existing five-part tuple; introduce no replacement `result_id` |
| Journal identity | Preserve `journal_id`, sequence, provenance and pinned ledger identity |
| Versioning | Define an application projection version separately from framework, SQL and event-format versions; unsupported versions fail explicitly |
| Lifecycle consistency | Collect the complete scheduling domain under exclusion from every mutation in that domain; include the observed Task revision set |
| Journal consistency | Preserve high-water traversal and distinguish partial traversal from verified absence |
| Cross-store consistency | Report lifecycle and Journal observations separately; do not promise a global atomic snapshot |
| Freshness | Return observed revision/cursor coverage. Any query receipt timestamp describes observation time, not Tool execution time |
| Numeric fidelity | Preserve exact large integer values. Current JavaScript `number` fields are insufficient for all Core timestamp/64-bit sequence ranges; representation requires agreement |
| Errors | Explicitly distinguish invalid input, not found, busy/unavailable source, incompatible version, identity/definition mismatch and integrity failure |
| Partial availability | A readable lifecycle snapshot with unavailable Journal evidence remains explicitly incomplete; it must not become “no Journal” |
| Authority | Read access covers an approved metadata audience. Query responses confer no execution or continuation authority |

No latency SLA, polling interval, event delivery guarantee or stream ordering contract is supported by current evidence.

### State-changing commands

**No command is necessary or proposed for activation in the first slice.**

If later approved, commands should remain action-specific:

| Future unapproved operation | Existing semantic basis | Required constraints |
|---|---|---|
| Prepare initial-run intent | `make_plan(action='run')` | Exact configuration/work/revisions; descriptive intent only |
| Execute approved initial work | `execute` | Fresh exact Human authority and unchanged upstream gates; restricted native read work |
| Continue Task | `continue_task`, Alpha resume checks | Exact current checkpoint, eligible history, new Run identity, fresh continuation authority and fresh execution authority |
| Attest Task completion | `transition(operation='complete')` | Current revision, lifecycle eligibility and meaningful governance closure reference |
| Stop unfinished Task | `transition(operation='stop')` | Explicit subject/reference; retain interruption uncertainty; respect owner availability |

There is no basis for a general-purpose execution endpoint or a generic `approve(id)` operation.

Alpha initialization and work loading are separate administrative mutations. They do not belong implicitly in the read boundary.

### Transport-relevant constraints

A future delivery mechanism must accommodate:

- the process-owned lifecycle store;
- process-local authority and Result provenance;
- exact identifiers and lossless integers;
- bounded pages and incomplete traversals;
- independent lifecycle/Journal observations;
- metadata confidentiality;
- sanitized errors;
- explicit command authority, if commands are separately approved.

**No REST, HTTP, SSE, WebSocket, IPC, local-server or streaming choice is made here.**

## 6. Authority and consistency analysis

### Lifecycle ownership is the first architectural decision

`SqliteTaskRunStateStore.__init__`:

1. acquires the exclusive owner lock;
2. validates storage;
3. recovers unfinished Runs;
4. commits resulting lifecycle changes.

Consequently, spawning an independent reader through `open_state` is not an acceptable implementation of a read-only UI query.

The least disruptive direction is an application query layer operating through an already established Core-owned session with explicit mutation exclusion. The current CLI does not expose such a UI query facility.

A separate recovery-free snapshot reader would require a newly approved ownership and consistency contract. Direct SQLite inspection from the UI would bypass existing semantic validation.

### Scheduling must remain descriptive until fresh execution checks

Core scheduling requires a complete domain, including disconnected Tasks whose Runs consume capacity. Collecting individually transactional pages without mutation exclusion does not establish that snapshot.

A displayed `selected_task_ids` value:

- reserves no slot;
- authorizes no Actor;
- grants no permission;
- produces no admission;
- cannot be reused as an execution credential.

The UI must display Core’s decision rather than rerun readiness logic over filtered nodes.

### Result, lifecycle and Journal can disagree legitimately

`tests/test_developer_alpha.py::test_06_running_restart_interrupted_no_journal_success_repair` explicitly covers:

- a successful recorded Journal summary;
- a lost lifecycle Result acceptance;
- recovery to `interrupted`.

The application must preserve both facts. It cannot promote the Run to succeeded or permit continuation using Journal success.

Likewise:

- missing Journal evidence does not invalidate an already accepted lifecycle Result;
- missing Result evidence is not an `effect_ambiguous` Result;
- Entry observation is not proof the Tool completed.

### UI access changes the authority boundary

Alpha’s approval mechanism assumes the current OS user in a private local workspace supplies control-plane intent. Its digest is an exact-state attestation, not a secret credential.

A new UI caller requires an explicit decision about authenticated identity and entitlement. Automatically forwarding a digest or accepting `authorityId`/`granted` fields would not preserve the existing trust boundary.

### Metadata and payload audiences are separate

Journal records can contain sensitive resources, Actor identities, Grant provenance and byte counts. The Journal specification requires explicit authorization for that metadata set and audience.

Execution approval does not automatically authorize:

- exposing the Journal to a browser;
- returning full configuration;
- retaining payloads;
- forwarding content;
- expanding the audience.

The first slice should use approved content-free evidence and avoid raw Result payload disclosure.

### Failures must remain visible

- Commit uncertainty requires exact state/evidence inspection, not automatic command repetition.
- Busy ownership is not an empty store.
- Integrity failure must not yield a usable clean prefix.
- Read failure must not become “no approvals,” “no Runs” or “no evidence.”
- Existing conforming owners prevent a concurrent Alpha stop command from opening the lifecycle store. The UI must not promise immediate cancellation.
- Decorative flow and Stage color aggregation establish no runtime progress or Quality Gate result.

### Documentation discrepancies

Current source implements Journal/lifecycle/scheduler capabilities that some UI comments still call pending. The Journal specification’s opening status note also retains an earlier Phase-2 hold, while later Task evidence records completion.

These discrepancies should be reconciled in separately approved documentation work. They were not edited or treated as evidence that implemented functionality is absent.

## 7. Recommended minimal integration slice

**Recommendation: approve a read-only, content-free existing-Run inspection slice first.**

### Preconditions

1. Human selects an existing Alpha workspace and Run whose metadata may be displayed.
2. The lifecycle ownership/read arrangement is approved.
3. The exact application projection and UI availability states are approved.
4. Delivery mechanism selection remains a separate decision.

This investigation did not open a store, so the existence and condition of a suitable persisted dataset remain **unknown**.

### Proposed slice

1. Resolve the approved source context.
2. Read the exact existing Run through the approved Core owner.
3. Show its unchanged Contract, Binding, lifecycle state and owning Task revision.
4. Obtain the explicitly configured complete Task graph and Core scheduler assessment.
5. Render Task dependencies and canonical evaluations.
6. Read matching Journal evidence with exact subject checking and stable traversal.
7. Display recorded outcomes, provenance and lifecycle/Journal discrepancies.
8. Mark payloads and unsupported evidence categories unavailable.
9. Keep approval, resume, execution and cancellation controls disabled.

The Run-detail Workflow river and the Task dependency DAG must remain distinguishable. A drawing of Workflow stages and associated Runs is not the scheduler’s Task DAG.

### Feasibility judgment

| Element | Finding |
|---|---|
| Exact persisted Run/Task facts | Implemented |
| Explicit Task graph | Implemented |
| Core scheduler assessment | Implemented |
| Content-free recorded Result/Entry evidence | Implemented |
| Application query projection | Missing |
| Safe lifecycle-reader composition | Requires architectural approval |
| UI canonical-state/evidence alignment | Required |
| Historical payload recovery | Unsupported |
| Existing end-to-end UI integration | Absent |

This is feasible as bounded composition and UI alignment. It is not currently a ready-to-connect API.

### Proposed future validation

After implementation authorization, meaningful checks should establish:

- queries perform no recovery, enrollment, invocation or lifecycle mutation;
- namespace/Binding mismatches fail closed;
- interrupted and ambiguous history remain unsafe;
- Journal success cannot repair missing lifecycle acceptance;
- partial evidence traversal is not reported as absence;
- large identifiers/numeric coordinates retain exact values;
- busy, unavailable, corrupt and not-found sources remain distinguishable;
- no credentials or unauthorized payload content enter responses;
- UI presentation preserves canonical states and evidence gaps.

None of these execution checks was run during this investigation.

## 8. Dependency-ordered implementation roadmap

This is sequencing guidance, **not implementation tasks or authorization**.

| Order | Work requiring approval | Dependency and outcome |
|---|---|---|
| 1 | Approve scope, source context and metadata audience | Establishes which existing workspace/Run may be inspected |
| 2 | Resolve lifecycle ownership and passive-query composition | Required before calling any store-opening/query path from integration code |
| 3 | Approve minimal application query contracts | Fix identity, versions, errors, consistency, evidence availability and traversal semantics |
| 4 | Implement Core-owned descriptive projections | Reuse validated lifecycle, DAG, scheduler and Journal behavior; preserve authority boundaries |
| 5 | Align active UI models and affected components | Add canonical lifecycle/decision states and recorded-summary/gap handling; remove unsupported claims |
| 6 | Separately select and approve delivery mechanism | Apply the constraints above after semantic contract agreement |
| 7 | Implement the read-only data-source adapter and vertical slice | Connect approved query results to the selected screens |
| 8 | Run scoped integration, consistency and security checks; obtain independent review | Required before claiming integration readiness |
| 9 | Human acceptance | Explicit approval of the completed read-only slice |
| Later | Consider operational commands separately | New authority design and approval; no automatic extension from read access |

No parked SCRUM-81 transfer is required to define this boundary. Any transfer or reuse of that branch remains separately scoped.

## 9. Open architecture decisions

| Decision | Evidence-grounded recommendation |
|---|---|
| Lifecycle read ownership | Prefer queries through an explicitly established Core owner; approve a separate passive-reader contract only if necessary |
| Operational domain | Start with one explicit Alpha workspace, not an inferred repository-wide execution catalog |
| Repository Task association | Keep Alpha work and repository Task definitions distinct unless an exact binding is approved |
| Application response model | Define Core-owned descriptive projections; retain `ControlCenterDataSource` as the UI adaptation seam |
| Evidence availability | Distinguish lifecycle acceptance, recorded summary, live Result, payload availability and missing/unavailable evidence |
| Scheduler display | Preserve actual Core evaluation states and decision coverage; retain layout as presentation |
| Journal pagination | Preserve high-water identity and scoped traversal completeness |
| Numeric representation | Agree a lossless representation before crossing into JavaScript models |
| Reader authentication/audience | Define the trusted caller and metadata audience explicitly |
| Freshness/offline behavior | Define receipt/revision semantics and unavailable-state presentation before promising live updates |
| Future approval/resume controls | Defer activation; current UI types are insufficient authority contracts |
| Transport | Leave unselected until the semantic boundary is approved |
| Existing documentation drift | Reconcile affected current claims in approved scope, preserving historical evidence |

## 10. Final Human Control checkpoint

**No source, report or configuration files were written. No implementation tasks were created.**

| Validation/control item | Outcome |
|---|---|
| Baseline and working-tree inspection | Performed; final state matches opening state |
| Source/specification/schema/test inspection | Performed statically |
| Runtime, CLI execution, agents, diagnostics or services | Not launched |
| Tests, builds and automated validation gates | Not run under the requested static-only scope |
| Documentation consistency | Discrepancies identified; no formal gate PASS claimed |
| Independent review | Not performed; no independent approval claimed |
| Architecture/implementation approval | Still required |

The explicit investigation request requires **“STOP AT HUMAN CONTROL.”** The [Project Manifest](D:/Dev/ai-engineering-orchestra/.ai/project.yaml) also requires approval for architecture changes and final Human review.

**Recommended next authorization:** review and approve or revise the proposed read-only scope, lifecycle ownership model and application query contracts before any implementation or delivery-mechanism work.

**STOP AT HUMAN CONTROL.**