# Core Contract Questions for ITRU Control Center

This document tracks unresolved Core dependencies encountered while building the ITRU Control Center UI foundation (SCRUM-17).

## Strict Boundary Principles

1. The UI lane MUST NOT invent Core contracts, lifecycle transitions, scheduler semantics, or transport protocols.
2. When the UI requires a domain concept not yet authored in Core (`core/*.md`, `schemas/*.json`), it is modeled strictly as a UI-local presentation assumption and recorded here.
3. Every item below uses the canonical 4-part structure:
   - `QUESTION:`
   - `UI NEED:`
   - `CURRENT MOCK ASSUMPTION:`
   - `CORE CONTRACT NEEDED FROM:`

---

## 1. Run Lifecycle & Execution State

QUESTION:
How does Core model the operational lifecycle and execution state of an Agent Execution Run?

UI NEED:
The Runs list, Run detail screen, and Overview need to communicate whether a run is queued, preparing, executing, waiting for input, completed successfully, failed, or cancelled. Users need to filter runs by active vs completed vs failed status.

CURRENT MOCK ASSUMPTION:
Core defines an Agent Execution Run (`core/agent-execution-run-specification.md`, AIO-042) as an immutable binding of a caller-supplied Run ID to an Agent Execution Contract, but defines no lifecycle state or status transitions. The UI defines a presentation-only `PresentationState` enum (`'not-started' | 'in-progress' | 'needs-attention' | 'finished' | 'unknown'`) that carries zero scheduler or state-machine semantics.

CORE CONTRACT NEEDED FROM:
Core Architecture / Execution Lifecycle specification (future AIO milestone or v0.2 execution model).

---

## 2. Run Querying, Listing & Chronological Metadata

QUESTION:
What is the authoritative mechanism for listing historical and active Runs, and what temporal/provenance metadata (creation timestamp, dispatch timestamp, completion timestamp, duration) accompanies a Run?

UI NEED:
The UI needs to list all runs across the workspace, paginate/sort them by recency, and present human-readable time labels (e.g., "Started 5m ago", "Duration: 42s").

CURRENT MOCK ASSUMPTION:
The UI assumes a `RunSummary` model containing a mock string label (`startedLabel`) and reads from an in-memory list in `MockControlCenterDataSource`. Core currently provides no query API, no index of runs, and no timestamp fields on Agent Execution Runs.

CORE CONTRACT NEEDED FROM:
Core Run persistence / Execution Store / Task execution journal specification.

---

## 3. Task-to-Run Association & Hierarchy

QUESTION:
How are Agent Execution Runs officially associated with their governing Task and Stage, and how is the set of runs executed in service of a Task discovered?

UI NEED:
The Task detail screen must show all Runs executed for that Task. The Run detail screen must link back to its parent Task and sibling Runs within the same Task workflow.

CURRENT MOCK ASSUMPTION:
The UI mock manually correlates Tasks and Runs by embedding `runIds: readonly string[]` inside `TaskDetail` and `taskRuns: readonly RunSummary[]` inside `RunDetail`. Core's `AgentExecutionContract` contains `task_id` and `stage_id`, but Core has no bi-directional query contract linking a Task definition to its execution occurrences.

CORE CONTRACT NEEDED FROM:
Core Task specification (`core/task-specification.md`) and Run Indexing / Ledger specification.

---

## 4. Run Result Semantics & Transport/Persistence (PARTIALLY ANSWERED BY ITRU-060)

QUESTION:
What is the formal contract for an Agent Execution Result produced by an Agent Execution Run, and what mechanism governs its transport, persistence, and querying?

UI NEED:
The UI needs to present the outcome of a Run, distinguishing validated completion from failures before side-effects and from uncertain effect boundaries. It needs to present bounded payload previews (for safe text vs raw binary), failure diagnostics, and exact evidence provenance (derived identity, Execution Entry, Tool binding) without inventing backend transport or persistence contracts.

STATUS & CORE CONTRACT RESOLUTION:
- **Canonical Result Semantics: ANSWERED by ITRU-060** (`core/agent-execution-result-specification.md`, commit 55e8001).
  Core formalizes an Agent Execution Result as immutable terminal evidence of one controlled execution attempt with a committed Execution Entry:
  - Exactly three terminal outcomes: `succeeded`, `failed_before_effect`, `effect_ambiguous`.
  - Closed six-field readable evidence contract: `ledger_identity`, `execution_entry`, `tool_binding`, `outcome`, `payload`, `diagnostic`.
  - Derived Result identity: 5-part tuple `(ledger_instance_id, domain_id, issuer_kind, issuer_id, grant_id)`.
  - Bounded binary payload on success (`RepositoryFileReadResultPayload`: `data: bytes`, `byte_count: int` <= 65,536). No inferred UTF-8 decoding in Core.
  - Diagnostic code on unsuccessful outcomes (`AgentExecutionResultDiagnostic`: closed table of 9 canonical codes).
  - Strict effect boundary: `failed_before_effect` proves no content-data request was issued; `effect_ambiguous` indicates content access commenced or post-read cleanup uncertainty was encountered.
  - Permanent Entry consumption: No outcome permits automatic retry or replay.
- **Result Transport, Persistence & Query Mechanism: UNRESOLVED**.
  ITRU-060 intentionally specifies:
  - NO public serialized Result schema
  - NO Result persistence (Result disappears with its process unless retained by an authorized consumer)
  - NO backend/API transport contract (no REST, WebSocket, or wire schema)
  - NO Task-level Result contract

CURRENT UI ADAPTER ASSUMPTION:
The UI maintains a strict boundary:
1. It does not invent a canonical JSON Result shape or REST/WebSocket transport contract.
2. It defines a UI-local read-model (`AgentExecutionResultReadModel`) and presentation model (`AgentExecutionResultPresentation`) mapped via a pure adapter (`adaptResultReadModel`).
3. The Result presentation shell (`cc-result-shell`) renders the three canonical outcomes, bounded text/binary payload previews, truncation warnings, closed diagnostic codes, and derived identity tuples.
4. An explicit disclaimer banner informs operators: *"Canonical ITRU-060 in-memory evidence · Transport & persistence uninvented"*.

CORE CONTRACT STILL NEEDED FROM:
Future Journal / Execution Store / API Transport specification (v0.2+) to define how Results are serialized, stored, and queried over the wire.

---

## 5. Execution Timeline & Journal / Event Log (PARTIALLY ANSWERED BY ITRU-061 PHASE 1)

QUESTION:
What is the canonical contract for an Execution Journal entry, and what rules govern event identity, authoritative ordering, timestamp authority, durability, persistence, query, replay, and tamper detection?

UI NEED:
The Execution Timeline and Evidence Explorer components need to present ordered, step-by-step operator visibility into actions, stage transitions, agent dispatches, tool invocations, quality gate results, diagnostic outputs, and linked Results. The operator needs compact chronological views, expandable event details, filtering, bounded text previews, and binary previews without inventing unfinished Core semantics.

STATUS & CORE CONTRACT RESOLUTION:
- **Canonical Execution Journal Contract: ANSWERED & LOCKED by ITRU-061 Phase 1**:
  Human-approved and locked Phase 1 decisions establish the canonical Journal contract:
  - **Canonical event identity**: Two-part key tuple `(journal_id, sequence)`.
  - **Event taxonomy**: Closed two-event taxonomy:
    - `entry_observed`: Captures observation of a committed Execution Entry.
    - `result_observed`: Captures observation of a terminal Agent Execution Result.
  - **Committed-recording ordering**: Monotonic integer `sequence` orders committed Journal recordings within a Journal instance.
  - **Timestamp authority**: Store-owned UTC timestamp represents receipt time when recorded by the trusted coordinator/Store (not agent-claimed or client clock).
  - **Durable Journal-entry schema**: Closed, content-free Journal-entry schema exists.
  - **Persistence decision**: Separate provisioned local SQLite Journal database (`journal.db`), operated in WAL journal mode with synchronous `FULL`. Existing v4 authorization-ledger migrations remain completely unchanged.
  - **Replay boundary**: No automatic effect replay; no exactly-once execution claims. Journal entries are strictly historical audit recordings.
  - **Corruption / restart / duplicate-conflict contract**: Formally defined by ITRU-061 Phase 1 (strict conflict rejection on duplicate sequence or incompatible duplicate entry recording, deterministic restart recovery).
  - **Task/Run relationship**: The Journal records discrete event occurrences only; it does NOT establish persistent Task/Run lifecycle state or scheduling state machines.

- **Operational Integration, Query & Transport: IMPLEMENTATION PENDING (ITRU-061 Phase 2)**:
  ITRU-061 Phase 1 intentionally scopes the semantic contract, leaving operational realization to Phase 2:
  - **Concrete runtime/query integration**: Pending ITRU-061 Phase 2 implementation.
  - **Public transport/API contract**: UNRESOLVED (no REST, WebSocket, streaming, or wire protocol defined).
  - **UI-to-Core query mechanism**: UNRESOLVED (no wire query API, polling, or pagination protocol defined).
  - **Implementation-dependent runtime storage/query behavior**: Not yet finalized until Phase 2 closes.

CURRENT UI ADAPTER ASSUMPTION (SCRUM-23):
The UI maintains a strict contract-safe boundary:
1. **Presentation inputs only**: The UI consumes generic UI-local presentation read models (`TimelineItemReadModel`, `EvidenceItemReadModel`) and presentation models (`TimelineItemPresentation`, `EvidenceItemPresentation`) mapped via pure adapters (`adaptTimelineReadModel`, `adaptEvidenceReadModel`).
2. **Explicit order disclaimer**: The UI explicitly disclaims ordering authority with the visible banner:
   *"Display order supplied by current data source · Core defines no canonical Journal ordering yet"*.
3. **No invented authority**: Timestamps, agent labels, tool labels, and entry claims are rendered only when supplied by the data source. Absence of an event or timestamp carries zero authoritative meaning.
4. **Result integration**: Reuses canonical ITRU-060 Result presentation (`cc-result-shell`) directly rather than duplicating Result semantics.
5. **Finalization path**: The UI presentation adapter (`adaptTimelineReadModel`) will be finalized and wired to the Core Journal query mechanism once ITRU-061 Phase 2 implementation completes.

CORE CONTRACT NEEDED FROM:
ITRU-061 Phase 2 (Runtime SQLite Journal realization, query integration, and transport protocol).

---

## 6. Human Approval Queue & Interactive Decision Contract

QUESTION:
What contract governs the discovery and queueing of pending Human Approvals, and how are approval/denial decisions submitted and validated?

UI NEED:
The Approvals screen needs an inventory of checkpoints currently awaiting human intervention across all tasks, plus history of granted/denied decisions. Operators eventually need to approve or deny requests directly from this screen.

CURRENT MOCK ASSUMPTION:
The Approvals screen is strictly read-only and displays `ApprovalItem` objects with a presentation state of `awaiting`, `granted`, or `denied`. The UI strictly respects that absence of authorization evidence means authorization is unproven—not denied. However, Core currently only defines the evidence artifact (`AgentExecutionAuthorizationEvidence`, AIO-039) and Grant artifact (AIO-043), with no approval request queue or interactive submission protocol.

CORE CONTRACT NEEDED FROM:
Core Human Control model (`core/human-control.md`) and Human Approval interaction protocol (v0.2+).

---

## 7. Structured Quality Gate & Evidence Explorer (SCRUM-23 CONTRACT-SAFE PRESENTATION LAYER)

QUESTION:
How are Quality Gate evaluation outcomes, diagnostic captures, command logs, diffs, and general execution evidence collected, serialized, and attached to Runs, Tasks, and Journal entries?

UI NEED:
The Evidence Explorer panel on Run detail and within Timeline items needs structured data on gate pass/fail/skip outcomes, evaluator identity, bounded text previews, non-text/binary representations, unavailable evidence states, and integrity badges.

CURRENT MOCK ASSUMPTION (SCRUM-23):
The UI models `EvidenceItemReadModel` and `EvidenceItemPresentation` with:
- Categories: `quality-gate`, `command-output`, `diff-summary`, `review-note`, `authorization`, `diagnostic`, `audit-trail`, `payload-sample`.
- Bounded text preview with truncation notices for large outputs.
- Binary hex sample representation without assuming UTF-8 decodability.
- Explicit unavailable evidence state (`isUnavailable: true`) surfacing retention policy expiration or missing telemetry honestly.
- Integrity status badges (`verified`, `mismatch`, `tampered`) rendered only when explicitly supplied by the data source.
- Pure adapter boundary (`adaptEvidenceReadModel`) decouples presentation from data origin.

CORE CONTRACT STILL NEEDED FROM:
ITRU-061 Phase 2 and future Core Quality Gate telemetry contract / durable evidence attachment schema.

---

## 8. Dynamic Workflow Branching & Concurrency Topology

QUESTION:
Does Core support concurrent/parallel stage execution or dynamic branching, and what schema describes inter-stage dependencies or branch merges?

UI NEED:
The Nile flow visualization renders workflow stages as a river with split and merge points. The UI needs to know which stages can execute in parallel vs strictly sequentially.

CURRENT MOCK ASSUMPTION:
Core Workflows (`core/workflow-specification.md`) define stages as a strictly sequential array. The UI-local `NileTopology` builds a visual tree where stages are columns and multi-role stages or sibling runs are rendered across visual lanes with cubic bezier curves, representing pure presentation topology with no concurrency or scheduler semantics.

CORE CONTRACT NEEDED FROM:
Core Workflow specification (`core/workflow-specification.md`) if parallel stage branching is ever introduced.

---

## 9. Persistent Runs, Tasks & Resume UX (SCRUM-24 / UNRESOLVED PENDING ITRU-062)

QUESTION:
What are the canonical Core contracts governing Task persistence, Run persistence, lifecycle state machines, continuation/resume eligibility, checkpoint identity, restart recovery, durability, and operational resumption?

UI NEED:
The operator needs to browse historical and active Tasks and Runs, inspect the hierarchical relationship (`Task ├─ Run A ├─ Run B └─ Run C`), filter by execution status and continuation affordance, review source-supplied continuation availability or blocked reasons, and safely inspect linked Results and Journal evidence without misleading operators into unsafe replay or assuming Core eligibility.

STATUS & CORE CONTRACT RESOLUTION:
- **Locked Prior Decisions Preserved**:
  - ITRU-060 canonical terminal Result outcomes (`succeeded`, `failed_before_effect`, `effect_ambiguous`) and strict side-effect boundaries remain authoritative. Specifically, `effect_ambiguous` strictly prohibits automated retry, replay, or continuation.
  - ITRU-061 Phase 1 canonical Journal model (two-event taxonomy `entry_observed` and `result_observed`, SQLite WAL `FULL` persistence, monotonic sequencing, and audit-only boundary) remains authoritative. Display of Journal entries or evidence does not prove resume safety.
- **ITRU-062 Scope: NOT STARTED / COMPLETELY UNRESOLVED**:
  The following 13 items are explicitly unresolved in Core pending ITRU-062 (SCRUM-19):
  1. **Canonical Task identity & persistence contract**: Core defines declarative tasks (`.ai/tasks/*.yaml`), but defines no runtime or durable identity contract, storage layout, or database schema.
  2. **Canonical Run identity & persistence contract**: Core defines `AgentExecutionRun` (`run_id`, `AgentExecutionContract`) as in-memory declarative intent, but has no durable runtime identity or storage schema.
  3. **Task & Run lifecycle state machines**: Neither Tasks nor Runs have authoritative lifecycle states, valid state transitions, terminal conditions, or cancellation state machines in Core.
  4. **Continuation / resume eligibility**: Core defines no rules determining whether a Run or Task is resumable, who decides eligibility, or under what conditions continuation is safe.
  5. **Checkpoint & continuation identity**: Core has no concept of execution checkpoints, snapshot identities, continuation tokens, or resume capabilities.
  6. **Restart recovery semantics**: How a crashed, pre-empted, or interrupted worker/process recovers state or re-establishes execution context is completely unspecified.
  7. **State reconstruction rules**: Whether state is reconstructed from Journal replay, filesystem artifacts, SQLite transactions, or external state stores is undefined.
  8. **Persistence schema & storage technology**: No schema, migrations, or database technology (SQLite, PostgreSQL, file ledger) has been selected or specified for Tasks and Runs.
  9. **Task↔Run durability & association rules**: How parent Tasks durably track execution Runs, branch attempts, retry sequences, or historical runs across process boundaries is undefined.
  10. **Resume authority**: What role, policy, or Human approval is required to authorize continuation/resumption, and whether a dedicated Grant is required, is undefined.
  11. **Query API, indexing & pagination**: No query API, sorting, cursor pagination, or filtering protocol exists for retrieving Tasks or Runs across workspace boundaries.
  12. **Concurrency & lease semantics**: No distributed or local concurrency controls, fencing tokens, or execution leases exist to prevent concurrent conflicting runs of the same Task.
  13. **Interrupted, abandoned, & stale execution definitions**: Core provides no heartbeat, timeout, or criteria for declaring a Run interrupted, abandoned, orphaned, or stale.

CURRENT UI ADAPTER ASSUMPTION (SCRUM-24):
The UI lane maintains a strict presentation-only, contract-safe boundary:
1. **Presentation inputs only**: All Task and Run history fields (`runCount`, `latestRunId`, `hasResult`, `statusLabel`, `lastActivityLabel`, `continuation`) are modeled as UI-local read models (`TaskSummary`, `RunSummary`, `RunDetail`, `RunContinuationReadModel`) supplied by `ControlCenterDataSource`.
2. **Generic presentation models**: Mapped via a pure presentation adapter (`adaptContinuationReadModel`) to `RunContinuationPresentation`.
3. **Explicit source attribution**: Every continuation affordance is framed with the prominent notice:
   *"Continuation availability supplied by current data source · Core defines no canonical continuation/resume contract yet (pending ITRU-062)"*.
4. **No fake mutations**: All resume actions are presentation-only / disabled demo controls (`[disabled]="true"`, `aria-disabled="true"`). Zero backend mutations or mock state modifications are executed.
5. **Strict effect_ambiguous prohibition**: If a Run ended in `effect_ambiguous`, continuation is unconditionally blocked, danger alerts are rendered, and resume controls are strictly omitted.
6. **No Journal safety proofs**: The UI explicitly alerts operators:
   *"Notice: Display of Journal entries or evidence does not prove continuation safety · Core defines no resume safety proofs."*
7. **Task Run tree hierarchy**: The Task detail view displays the full hierarchical history (`Task ├─ Run A ├─ Run B └─ Run C`) with selectable prior runs and embedded inspection of continuation affordances, ResultShell (SCRUM-22), ExecutionTimeline (SCRUM-23), and EvidencePanel (SCRUM-23).

CORE CONTRACT NEEDED FROM:
ITRU-062 / SCRUM-19 (Core Persistent Runs, Tasks, Lifecycle, and Resumption Specification). When ITRU-062 closes, the finalized Core contract will plug directly into the `ControlCenterDataSource` / adapter boundary without redesigning the UI.

---

## 10. DAG & Scheduler Semantics (SCRUM-25 / UNRESOLVED PENDING ITRU-063)

QUESTION:
What are the canonical Core contracts governing task dependency graphs (DAGs), scheduler state machines, readiness evaluation, dependency satisfaction, dispatch eligibility, admission store interaction, and execution flow recovery?

UI NEED:
The operator needs an interactive Nile dependency graph and scheduler overview panel to visualize multi-stage workflows, parent/dependency relationships, fan-out/fan-in tributaries, blocking constraints, linked Results, Journal timelines, and execution evidence without inventing unfinished Core scheduler, lifecycle, or dispatch semantics.

STATUS & CORE CONTRACT RESOLUTION:
- **Locked Prior Decisions Preserved**:
  - **ITRU-060 Canonical Results**: Terminal outcomes (`succeeded`, `failed_before_effect`, `effect_ambiguous`) and side-effect boundaries remain authoritative. Visualization never implies that graphical representation makes retry or replay safe on `effect_ambiguous` nodes. Automatic retry/replay is strictly prohibited.
  - **ITRU-061 Phase 1 Canonical Journal**: Canonical two-event audit taxonomy (`entry_observed`, `result_observed`), monotonic sequencing, and SQLite WAL `FULL` persistence remain locked. The UI's display order disclaimer remains active: display of events or evidence provides zero proof of scheduler readiness or resume safety.
  - **ITRU-062 Task/Run Persistence & Resumption Boundary**: Task and Run durable identities, checkpoints, and resume state machines remain unresolved pending ITRU-062.
- **ITRU-063 Scope: NOT STARTED / COMPLETELY UNRESOLVED**:
  The following 16 items are explicitly UNRESOLVED in Core pending ITRU-063 (SCRUM-20):
  1. **Canonical DAG identity**: Core defines no runtime or durable identity contract for execution graphs or workflow instance topologies.
  2. **Canonical node identity**: Core defines `AgentExecutionContract` (AIO-041) and `AgentExecutionRun` (AIO-042) as in-memory declarative intent, but defines no canonical DAG node identity, node schema, or node type taxonomy.
  3. **Canonical edge / dependency contract**: Core Workflows (`core/workflow-specification.md`) define sequential stages only; Core defines no inter-stage edge schema, branch-join descriptor, or cross-task dependency contract.
  4. **Dependency satisfaction rules**: Core provides no rules or algorithms determining whether an upstream dependency is satisfied (e.g. strict success vs allowable failure, payload validation, condition predicates).
  5. **Scheduler lifecycle / state machine**: Core defines zero scheduler lifecycle states, transitions, or queue states (e.g. queued, ready, running, blocked, complete, cancelled).
  6. **Readiness rules**: Core defines no rules determining when a node transitions from queued/blocked to ready for dispatch.
  7. **Scheduling authority**: What component, process, policy, or Human authority makes scheduling decisions, assigns priorities, or triggers dispatches is undefined in Core.
  8. **Dispatch / admission interaction**: How the scheduler coordinates with the Dispatch Admission Store (AIO-045 / ITRU-046) and consumes Grants without race conditions is undefined.
  9. **Concurrency semantics**: Core defines no limits or semantics for parallel branch execution, worker pool limits, or global/local execution concurrency.
  10. **Fairness policy**: No queueing discipline, priority weighting, starvation avoidance, or multi-task fairness policy exists in Core.
  11. **Retry / failover policy**: Core defines no retry policies, backoff mechanisms, worker failover, or transient fault handling for scheduled DAG nodes.
  12. **Graph persistence**: No database schema, migration, or storage technology has been selected or specified for persisting DAG structures.
  13. **Scheduler persistence**: How active scheduler state, queue positions, and in-flight lease reservations survive process restarts is completely undefined.
  14. **Query / index / pagination model**: Core defines no query protocol, cursor pagination, or index layout for querying graph topologies or scheduler queues.
  15. **Cycle handling**: Core defines no cycle detection, validation, or rejection algorithm for dependency graphs.
  16. **Cancellation semantics and scheduler recovery after restart**: How ongoing or downstream DAG branches are aborted upon task cancellation, and how a restarted scheduler reconstructs in-flight execution flow, is completely unspecified.

CURRENT UI ADAPTER ASSUMPTION (SCRUM-25):
The UI lane maintains a strict presentation-only, contract-safe boundary:
1. **Presentation inputs only**: All graph structures and scheduler fields (`DagGraphReadModel`, `DagNodeReadModel`, `DagEdgeReadModel`, `SchedulerSummaryReadModel`) are UI-local read-models supplied by `ControlCenterDataSource`. They carry ZERO Core scheduler or lifecycle authority.
2. **Prominent scheduler disclaimer**: The operator panel displays the prominent notice:
   *"Scheduler state supplied by current data source · Core scheduler semantics pending ITRU-063."*
3. **Prominent dependency disclaimer**: The dependency inspector displays the notice:
   *"Dependency relations supplied by presentation data source · Core readiness algorithm & dispatch eligibility pending ITRU-063."*
4. **No invented algorithms**: The UI evaluates no readiness algorithms, computes no dispatch eligibility, triggers no state mutations, and defines no canonical scheduler enums.
5. **Nile visual metaphor**: Trunk represents principal execution path; tributaries represent dependent sub-agent work; convergence represents joins. Animated water highlights are purely decorative (`prefers-reduced-motion` supported).
6. **Strict effect_ambiguous handling**: Any node associated with an `effect_ambiguous` outcome renders distinct hazard markings (striped borders, warning icons) and surfaces the strict notice that automatic retry or replay is prohibited.
7. **Clean adapter decoupling**: Mapped through `adaptDagGraphReadModel` in `dag-adapter.ts`. When ITRU-063 formalizes the canonical Core scheduler and DAG contracts, they will connect through data-source presentation adapters without requiring UI redesign.

CORE CONTRACT NEEDED FROM:
ITRU-063 / SCRUM-20 (Core DAG, Dependency Resolution, and Scheduler Specification).
