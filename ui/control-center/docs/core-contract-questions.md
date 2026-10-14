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

## 5. Execution Timeline & Journal / Event Log

QUESTION:
What is the authoritative schema for fine-grained execution events (stage transitions, agent dispatches, tool invocations, quality gate runs, human reviews) associated with a Task or Run?

UI NEED:
The Execution Timeline component on the Run detail screen needs an ordered stream of discrete events to display step-by-step progress, duration, and error locations.

CURRENT MOCK ASSUMPTION:
The UI defines `TimelineEntry` (`kind: 'stage' | 'agent' | 'quality-gate' | 'approval' | 'note'`, `atLabel`, `title`, `detail`, `state`). This is an arbitrary presentation model backed by static mock arrays; Core defines no Journal or event stream.

CORE CONTRACT NEEDED FROM:
Core Journal / Audit Trail specification (referenced under `core/terminology.md` as Journal).

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

## 7. Structured Quality Gate & Evidence Serialization

QUESTION:
How are Quality Gate evaluation outcomes and general execution evidence collected, serialized, and attached to Runs and Tasks?

UI NEED:
The Evidence panel on Run detail needs structured data on gate pass/fail/skip outcomes, evaluator identity, logs/traces, and diff snippets.

CURRENT MOCK ASSUMPTION:
The UI models `EvidenceItem` with `EvidenceOutcome` (`'passed' | 'failed' | 'skipped' | 'unverified'`) and mock text lines. Core defines Quality Gate names in `quality-gates/`, but has no runtime schema for gate execution reports or telemetry capture.

CORE CONTRACT NEEDED FROM:
Core Quality Gate evaluation contract and Evidence artifact schema.

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
