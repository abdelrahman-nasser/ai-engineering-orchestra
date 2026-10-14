/**
 * UI-local presentation models for the ITRU Control Center.
 *
 * IMPORTANT BOUNDARY
 * ------------------
 * These types are owned by the UI lane. They are NOT Core contracts.
 *
 * - Types marked "Core vocabulary" reuse values that already exist in a Core
 *   specification or schema (`core/*.md`, `schemas/*.json`). They are copied
 *   here read-only so the UI never imports from or edits Core.
 * - Types marked "UI-local" are presentation inventions made only so screens
 *   can render. They carry NO scheduler, lifecycle, persistence, transport,
 *   Result, or Journal semantics. Every such assumption is recorded in
 *   `ui/control-center/docs/core-contract-questions.md`.
 */

// ---------------------------------------------------------------------------
// Core vocabulary (read-only mirrors of existing Core values)
// ---------------------------------------------------------------------------

/** Core vocabulary: `core/task-specification.md` §10, `schemas/task.schema.json`. */
export type TaskStatus = 'planned' | 'in_progress' | 'blocked' | 'completed' | 'cancelled';

/** Core vocabulary: `schemas/task.schema.json` (`risk`, `complexity`). */
export type Level = 'low' | 'medium' | 'high' | 'critical';

/** Core vocabulary: `core/human-control.md` §4. */
export type ApprovalLevel = 'none' | 'review' | 'explicit' | 'protected';

/** Core vocabulary: `schemas/task.schema.json` (`execution.mode`). */
export type ExecutionMode = 'lite' | 'standard' | 'deep' | 'critical';

/** Core vocabulary: availability observation states (Actor / Runtime / Inference). */
export type AvailabilityState = 'available' | 'unavailable' | 'unknown';

/** Core vocabulary: Actor kind (`core/actor-specification.md`). */
export type ActorKind = 'human' | 'agent';

/** Core vocabulary: Agent Execution Authorization Evidence `state` (AIO-039). */
export type AuthorizationEvidenceState = 'granted' | 'denied';

// ---------------------------------------------------------------------------
// UI-local presentation vocabulary
// ---------------------------------------------------------------------------

/**
 * UI-local. A purely visual state used to colour stages, runs and branches.
 *
 * It is NOT a Core Run/Stage lifecycle state (Core defines none) and implies
 * no scheduling, queueing, dispatch or ordering of any kind.
 */
export type PresentationState =
  | 'not-started'
  | 'in-progress'
  | 'needs-attention'
  | 'finished'
  | 'unknown';

/** UI-local tone used by the shared status badge. */
export type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'muted' | 'accent';

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

/** UI-local summary of a Core Task (fields mirror `task.yaml`). */
export interface TaskSummary {
  /** Core `id`. */
  readonly id: string;
  /** Core `title`. */
  readonly title: string;
  /** Core `type` (open vocabulary). */
  readonly type: string;
  /** Core `status`. */
  readonly status: TaskStatus;
  readonly risk: Level;
  readonly complexity: Level;
  readonly executionMode: ExecutionMode;
  /** Core `workflow` (stable Workflow id). */
  readonly workflowId: string;
  /** Highest Human approval level applying to this Task. */
  readonly approvalLevel: ApprovalLevel;
  /** UI-local, mock-only label (Core Tasks carry no timestamp). */
  readonly updatedLabel: string;
}

export interface TaskDetail extends TaskSummary {
  /** Core `objective`. */
  readonly objective: string;
  /** Core `scope.included`. */
  readonly scopeIncluded: readonly string[];
  /** Core `scope.excluded`. */
  readonly scopeExcluded: readonly string[];
  /** Core `dependencies` (Task ids). */
  readonly dependencies: readonly string[];
  /** Names of Quality Gates the Task requires. */
  readonly qualityGates: readonly string[];
  /** Ids of Runs the mock associates with this Task. */
  readonly runIds: readonly string[];
  /** Workflow stages as defined by the governing Workflow (Core, sequential). */
  readonly stages: readonly WorkflowStageView[];
  /** Blocking reason, when `status === 'blocked'` (Core: recorded in context). */
  readonly blockedReason?: string;
}

// ---------------------------------------------------------------------------
// Workflow
// ---------------------------------------------------------------------------

/** Core vocabulary: one Stage of a Workflow (`core/workflow-specification.md` §4). */
export interface WorkflowStageView {
  readonly id: string;
  readonly purpose: string;
  readonly requiredRoles: readonly string[];
  /** Core `human_control_checkpoint`. */
  readonly humanControlCheckpoint: boolean;
}

// ---------------------------------------------------------------------------
// Runs
// ---------------------------------------------------------------------------

/**
 * Mirrors the public fields of a Core Agent Execution Contract (AIO-041).
 * Core defines one Run as exactly one assigned action: one Stage, one Role,
 * one Actor.
 */
export interface RunContractView {
  readonly taskId: string;
  readonly workflowId: string;
  readonly stageId: string;
  readonly roleId: string;
  readonly actorId: string;
  readonly runtimeOptionId: string;
  readonly optionId: string;
  readonly environmentId: string;
  readonly operationId: string;
  readonly resource: string;
  readonly executionMode: ExecutionMode;
}

/** A Run as listed on screen. `runId` is an opaque Core identifier. */
export interface RunSummary {
  /** Core: opaque, caller-supplied `run_id`. */
  readonly runId: string;
  readonly contract: RunContractView;
  /** UI-local visual state; Core defines no Run status. */
  readonly presentationState: PresentationState;
  /** UI-local, mock-only. Core Runs carry no timestamp. */
  readonly startedLabel: string;
}

export interface RunDetail extends RunSummary {
  readonly taskTitle: string;
  /** Stages of the governing Workflow, in Core sequential order. */
  readonly stages: readonly WorkflowStageView[];
  /** All Runs the mock associates with the same Task (siblings, incl. this one). */
  readonly taskRuns: readonly RunSummary[];
  readonly timeline: readonly TimelineEntry[];
  readonly evidence: readonly EvidenceItem[];
  /** UI-local, provisional. `null` when the mock has nothing to show yet. */
  readonly result: ProvisionalResult | null;
}

// ---------------------------------------------------------------------------
// Timeline (UI-local; Core defines no Journal)
// ---------------------------------------------------------------------------

export type TimelineKind = 'stage' | 'agent' | 'quality-gate' | 'approval' | 'note';

/** UI-local presentation entry. NOT a Journal record. */
export interface TimelineEntry {
  readonly id: string;
  /** Mock-only display label (e.g. "14:02"). No ordering semantics beyond array order. */
  readonly atLabel: string;
  readonly kind: TimelineKind;
  readonly title: string;
  readonly detail?: string;
  readonly state: PresentationState;
  readonly actorId?: string;
  readonly stageId?: string;
}

// ---------------------------------------------------------------------------
// Evidence (UI-local)
// ---------------------------------------------------------------------------

export type EvidenceKind =
  | 'quality-gate'
  | 'command-output'
  | 'diff-summary'
  | 'review-note'
  | 'authorization';

/** Outcome vocabulary mirrors AGENTS.md: report failed or skipped validation. */
export type EvidenceOutcome = 'passed' | 'failed' | 'skipped' | 'unverified';

export interface EvidenceItem {
  readonly id: string;
  readonly kind: EvidenceKind;
  readonly title: string;
  readonly summary: string;
  readonly outcome: EvidenceOutcome;
  /** Opaque source label, e.g. a gate name or command. Display only. */
  readonly source: string;
  /** Monospace lines (command output, diff summary...). */
  readonly lines?: readonly string[];
}

// ---------------------------------------------------------------------------
// Result (UI-local, provisional)
// ---------------------------------------------------------------------------

/**
 * UI-local, PROVISIONAL Result presentation. Core defines no Result contract.
 * This shape exists only so the Result shell can be laid out and reviewed.
 */
export interface ProvisionalResult {
  readonly headline: string;
  readonly summary: string;
  readonly changedAreas: readonly string[];
  readonly openItems: readonly string[];
}

// ---------------------------------------------------------------------------
// Agents (Actors)
// ---------------------------------------------------------------------------

export interface AgentAssignmentView {
  readonly taskId: string;
  readonly stageId: string;
  readonly roleId: string;
}

/** UI-local view of a Core Actor with its read-only observed context. */
export interface AgentSummary {
  readonly actorId: string;
  readonly name: string;
  readonly kind: ActorKind;
  /** Role ids the Actor competency covers. */
  readonly roleIds: readonly string[];
  /** Core availability observation state. */
  readonly availability: AvailabilityState;
  /** Opaque Runtime Option ids with positive applicability evidence (agents only). */
  readonly runtimeOptionIds: readonly string[];
  readonly assignments: readonly AgentAssignmentView[];
}

// ---------------------------------------------------------------------------
// Approvals (UI-local; Core defines no approval queue contract)
// ---------------------------------------------------------------------------

/**
 * UI-local. `awaiting` is presentational: Core evidence is only `granted` or
 * `denied`; absence of evidence means authorization is unproven.
 */
export type ApprovalPresentationState = 'awaiting' | AuthorizationEvidenceState;

export interface ApprovalItem {
  readonly id: string;
  readonly taskId: string;
  readonly runId?: string;
  readonly stageId: string;
  readonly level: ApprovalLevel;
  /** Human-readable description of the exact action in question. */
  readonly action: string;
  readonly state: ApprovalPresentationState;
  /** Opaque authority id (Human or policy), when evidence exists. */
  readonly authorityId?: string;
  readonly requestedLabel: string;
}

// ---------------------------------------------------------------------------
// Overview
// ---------------------------------------------------------------------------

export interface OverviewPresentation {
  readonly tasks: readonly TaskSummary[];
  readonly runs: readonly RunSummary[];
  readonly agents: readonly AgentSummary[];
  readonly approvals: readonly ApprovalItem[];
}

// ---------------------------------------------------------------------------
// Nile topology (UI-local, presentation only)
// ---------------------------------------------------------------------------

export type NileNodeKind = 'task' | 'stage' | 'run' | 'confluence' | 'outcome';

/** Layout-only hint: which side of its node a label is drawn on. */
export type NileLabelSide = 'above' | 'below' | 'left' | 'right';

export interface NileNode {
  readonly id: string;
  readonly label: string;
  readonly sublabel?: string;
  readonly kind: NileNodeKind;
  /** Horizontal reach index (0 = upstream); may be fractional. Layout only. */
  readonly column: number;
  /** Vertical offset from the trunk. 0 = trunk, negative = above, positive = below. */
  readonly lane: number;
  readonly state: PresentationState;
  /** Optional label placement override. Layout only. */
  readonly labelSide?: NileLabelSide;
}

export interface NileEdge {
  readonly from: string;
  readonly to: string;
}

/**
 * Presentation topology: which things are drawn connected to which.
 * It makes no claim about scheduling, concurrency, ordering between branches,
 * progress rate, or dependency semantics.
 */
export interface NileTopology {
  readonly nodes: readonly NileNode[];
  readonly edges: readonly NileEdge[];
}
