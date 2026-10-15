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
  /** UI-local, mock-only: total runs count associated with this task. */
  readonly runCount?: number;
  /** UI-local, mock-only: latest run id. */
  readonly latestRunId?: string;
  /** UI-local, mock-only: latest run visual state. */
  readonly latestRunState?: PresentationState;
  /** UI-local, mock-only: whether any associated run has a Result. */
  readonly hasResult?: boolean;
  /** UI-local, mock-only: whether continuation is available in latest run. */
  readonly continuationAvailable?: boolean;
  /** UI-local, mock-only: last activity label. */
  readonly lastActivityLabel?: string;
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
  /** UI-local, mock/read-model: source-supplied status label when available. */
  readonly statusLabel?: string;
  /** UI-local, mock/read-model: last activity label or timestamp. */
  readonly lastActivityLabel?: string;
  /** UI-local, mock/read-model: whether this run published a Result. */
  readonly hasResult?: boolean;
  /** UI-local, mock/read-model: Result outcome when published. */
  readonly resultOutcome?: AgentExecutionResultOutcome;
  /** UI-local, mock/read-model: recorded evidence count. */
  readonly evidenceCount?: number;
  /** UI-local, mock/read-model: source-supplied continuation info. */
  readonly continuation?: RunContinuationPresentation;
}

export interface RunDetail extends RunSummary {
  readonly taskTitle: string;
  /** Stages of the governing Workflow, in Core sequential order. */
  readonly stages: readonly WorkflowStageView[];
  /** All Runs the mock associates with the same Task (siblings, incl. this one). */
  readonly taskRuns: readonly RunSummary[];
  readonly timeline: readonly TimelineEntry[];
  readonly evidence: readonly EvidenceItem[];
  /** UI-local Result presentation, or null if no Result published yet. */
  readonly result: AgentExecutionResultPresentation | null;
  /** UI-local Continuation presentation. */
  readonly continuation?: RunContinuationPresentation;
}

// ---------------------------------------------------------------------------
// Continuation & Resume Affordances (UI-local; Core defines none pending ITRU-062)
// ---------------------------------------------------------------------------

export type ContinuationStatus =
  | 'available'
  | 'unavailable'
  | 'blocked'
  | 'interrupted'
  | 'completed'
  | 'missing'
  | 'stale';

/**
 * Read-model shape for continuation / resume metadata delivered by a data source.
 *
 * IMPORTANT:
 * This is a UI-local presentation assumption.
 * Core defines NO canonical continuation, checkpoint identity, resume authority,
 * or restart recovery semantics in v0.1.x Foundation (pending ITRU-062).
 */
export interface RunContinuationReadModel {
  readonly state?: ContinuationStatus;
  readonly isAvailable?: boolean;
  readonly label?: string;
  readonly reason?: string;
  readonly blockedReason?: string;
  readonly lastKnownActivity?: string;
  readonly interruptionNotice?: string;
  readonly stale?: boolean;
  readonly staleNotice?: string;
}

/**
 * UI-local presentation model for continuation / resume affordances.
 */
export interface RunContinuationPresentation {
  readonly status: ContinuationStatus;
  readonly statusLabel: string;
  readonly statusTone: Tone;
  readonly isAvailable: boolean;
  readonly isBlocked: boolean;
  readonly isInterrupted: boolean;
  readonly isCompleted: boolean;
  readonly isStale: boolean;
  readonly isMissing: boolean;
  readonly label?: string;
  readonly reason?: string;
  readonly blockedReason?: string;
  readonly lastKnownActivity?: string;
  readonly interruptionNotice?: string;
  readonly staleNotice?: string;
  readonly disclaimer: string;
  readonly actionDisabled: boolean;
  readonly actionDisabledReason?: string;
}

// ---------------------------------------------------------------------------
// Timeline (UI-local; Core defines no Journal)
// ---------------------------------------------------------------------------

export type TimelineKind = 'stage' | 'agent' | 'quality-gate' | 'approval' | 'tool' | 'note';

/** Read-model shape for a timeline entry delivered by a data source. */
export interface TimelineItemReadModel {
  readonly id: string;
  /** Mock/read-model display label (e.g. "14:02"). No ordering semantics beyond array order. */
  readonly atLabel: string;
  readonly kind: TimelineKind;
  readonly title: string;
  readonly detail?: string;
  readonly state: PresentationState;
  readonly actorId?: string;
  readonly stageId?: string;
  readonly toolId?: string;
  readonly executionEntryRef?: string;
  readonly runIdRef?: string;
  readonly result?: AgentExecutionResultReadModel | null;
  readonly evidence?: readonly EvidenceItemReadModel[];
}

/** UI-local presentation entry. NOT a Journal record. */
export interface TimelineItemPresentation {
  readonly id: string;
  readonly atLabel: string;
  readonly kind: TimelineKind;
  readonly title: string;
  readonly detail?: string;
  readonly state: PresentationState;
  readonly stateLabel: string;
  readonly stateTone: Tone;
  readonly actorId?: string;
  readonly stageId?: string;
  readonly toolId?: string;
  readonly executionEntryRef?: string;
  readonly runIdRef?: string;
  readonly hasResult: boolean;
  readonly result: AgentExecutionResultPresentation | null;
  readonly evidenceCount: number;
  readonly hasEvidence: boolean;
  readonly hasUnavailableEvidence: boolean;
  readonly evidence: readonly EvidenceItemPresentation[];
}

/** Backwards-compatible alias for timeline entries. */
export type TimelineEntry = TimelineItemPresentation;

// ---------------------------------------------------------------------------
// Evidence (UI-local)
// ---------------------------------------------------------------------------

export type EvidenceCategory =
  | 'quality-gate'
  | 'command-output'
  | 'diff-summary'
  | 'review-note'
  | 'authorization'
  | 'diagnostic'
  | 'audit-trail'
  | 'payload-sample';

/** Backwards-compatible alias for evidence categories. */
export type EvidenceKind = EvidenceCategory;

/** Outcome vocabulary mirrors AGENTS.md: report failed or skipped validation. */
export type EvidenceOutcome = 'passed' | 'failed' | 'skipped' | 'unverified';

/** Integrity status only when explicitly supplied by the data source. */
export type EvidenceIntegrityStatus = 'verified' | 'unverified' | 'mismatch' | 'tampered';

/** Read-model shape for an evidence item delivered by a data source. */
export interface EvidenceItemReadModel {
  readonly id: string;
  readonly category: EvidenceCategory;
  readonly title: string;
  readonly summary: string;
  readonly outcome: EvidenceOutcome;
  /** Opaque source/provenance label (e.g. command, gate name, guard identity). */
  readonly source: string;
  /** Reference or identity text supplied by read model (e.g. claim ref, file path). */
  readonly referenceId?: string;
  /** Monospace lines (command output, diff summary...). */
  readonly lines?: readonly string[];
  /** Bounded text preview if applicable. */
  readonly textPreview?: string;
  /** Whether the preview is bounded/truncated. */
  readonly isTruncated?: boolean;
  /** Known byte count of payload/artifact. */
  readonly byteCount?: number;
  /** Formatted hex sample snippet if binary/non-text. */
  readonly binaryHexSample?: string;
  /** Whether this evidence record is currently unavailable in the source. */
  readonly isUnavailable?: boolean;
  /** Reason why evidence is unavailable (when isUnavailable is true). */
  readonly unavailableReason?: string;
  /** Integrity status only when explicitly supplied. */
  readonly integrityStatus?: EvidenceIntegrityStatus;
  /** Recorded timestamp label when supplied. */
  readonly recordedAtLabel?: string;
}

export interface EvidenceItemPresentation {
  readonly id: string;
  readonly category: EvidenceCategory;
  readonly categoryLabel: string;
  /** Backwards-compatible alias for kind. */
  readonly kind: EvidenceCategory;
  readonly title: string;
  readonly summary: string;
  readonly outcome: EvidenceOutcome;
  readonly outcomeLabel: string;
  readonly outcomeTone: Tone;
  readonly source: string;
  readonly referenceId?: string;
  readonly lines?: readonly string[];
  readonly textPreview?: string;
  readonly isTruncated: boolean;
  readonly truncationNotice?: string;
  readonly byteCount?: number;
  readonly formattedByteCount?: string;
  readonly binaryHexSample?: string;
  readonly isBinary: boolean;
  readonly isUnavailable: boolean;
  readonly unavailableReason?: string;
  readonly integrityStatus?: EvidenceIntegrityStatus;
  readonly integrityBadge?: { readonly label: string; readonly tone: Tone };
  readonly recordedAtLabel?: string;
}

/** Backwards-compatible alias for evidence items. */
export type EvidenceItem = EvidenceItemPresentation;

// ---------------------------------------------------------------------------
// Result (UI-local, aligned with ITRU-060 canonical semantics)
// ---------------------------------------------------------------------------

/** Core vocabulary: canonical Result outcome (`core/agent-execution-result-specification.md` §3, §5). */
export type AgentExecutionResultOutcome =
  | 'succeeded'
  | 'failed_before_effect'
  | 'effect_ambiguous';

/** Core vocabulary: canonical Result diagnostic code (`core/agent-execution-result-specification.md` §7). */
export type AgentExecutionResultDiagnosticCode =
  | 'adapter_unavailable'
  | 'containment_rejected'
  | 'resource_missing'
  | 'resource_changed'
  | 'size_limit_exceeded'
  | 'read_failure'
  | 'guard_lost'
  | 'ownership_lost'
  | 'effect_ambiguous';

/** Derived Result identity 5-part tuple (`core/agent-execution-result-specification.md` §3). */
export interface ResultDerivedIdentity {
  readonly ledgerInstanceId: string;
  readonly authorizationDomainId: string;
  readonly issuerKind: string;
  readonly issuerId: string;
  readonly grantId: string;
}

export interface ResultLedgerIdentityReadModel {
  readonly domainId: string;
  readonly ledgerInstanceId: string;
  readonly domainGeneration: number;
}

export interface ResultExecutionEntryReadModel {
  readonly claimId: string;
  readonly executorInstanceId: string;
  readonly leaseGeneration: number;
  readonly entryTimeLabel: string;
  readonly timeKey: number;
}

export interface ResultToolBindingReadModel {
  readonly toolIdentity: string;
  readonly configuredRoute: string;
}

export interface ResultPayloadReadModel {
  readonly byteCount: number;
  /** Whether the read-model explicitly certified this payload as safe text. */
  readonly isText: boolean;
  /** Safe text preview (when isText is true). */
  readonly textPreview?: string;
  /** Formatted hex sample snippet (for binary inspection). */
  readonly bytesSampleHex?: string;
  /** Whether this preview is bounded/truncated from the full payload. */
  readonly isTruncated: boolean;
  /** Number of bytes represented in this preview. */
  readonly previewByteCount: number;
}

export interface ResultDiagnosticReadModel {
  readonly code: AgentExecutionResultDiagnosticCode;
}

/**
 * Read-model shape for an Agent Execution Result as delivered by a data source.
 * NOT a Core contract; ITRU-060 defines no serialized schema or transport.
 */
export interface AgentExecutionResultReadModel {
  readonly derivedIdentity: ResultDerivedIdentity;
  readonly ledgerIdentity: ResultLedgerIdentityReadModel;
  readonly executionEntry: ResultExecutionEntryReadModel;
  readonly toolBinding: ResultToolBindingReadModel;
  readonly outcome: AgentExecutionResultOutcome;
  readonly payload?: ResultPayloadReadModel | null;
  readonly diagnostic?: ResultDiagnosticReadModel | null;
}

export interface ResultPayloadPresentation {
  readonly byteCount: number;
  readonly formattedByteCount: string;
  readonly isText: boolean;
  readonly textPreview?: string;
  readonly bytesSampleHex?: string;
  readonly isTruncated: boolean;
  readonly truncationNotice?: string;
}

export interface ResultDiagnosticPresentation {
  readonly code: AgentExecutionResultDiagnosticCode;
  readonly title: string;
  readonly explanation: string;
}

export interface ResultIdentityPresentation {
  readonly derivedIdentityFormatted: string;
  readonly ledgerInstanceId: string;
  readonly domainId: string;
  readonly issuer: string;
  readonly grantId: string;
  readonly claimId: string;
  readonly executorInstanceId: string;
  readonly leaseGeneration: number;
  readonly entryTimeLabel: string;
  readonly timeKey: number;
  readonly toolIdentity: string;
  readonly configuredRoute: string;
}

export interface ResultSemanticEffectPresentation {
  readonly headline: string;
  readonly description: string;
  readonly retryNotice?: string;
}

/**
 * UI-local presentation model for an Agent Execution Result, adapted for screen rendering.
 */
export interface AgentExecutionResultPresentation {
  readonly outcome: AgentExecutionResultOutcome;
  readonly outcomeLabel: string;
  readonly outcomeTone: Tone;
  readonly semanticEffect: ResultSemanticEffectPresentation;
  readonly identity: ResultIdentityPresentation;
  readonly payload: ResultPayloadPresentation | null;
  readonly diagnostic: ResultDiagnosticPresentation | null;
}

/** Backwards-compatible alias for provisional references. */
export type ProvisionalResult = AgentExecutionResultPresentation;

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
