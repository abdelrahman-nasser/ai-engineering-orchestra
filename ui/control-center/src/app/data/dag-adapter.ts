import {
  DagEdgePresentation,
  DagEdgeReadModel,
  DagGraphPresentation,
  DagGraphReadModel,
  DagNodePresentation,
  DagNodeReadModel,
  PresentationState,
  SchedulerPresentationState,
  Tone,
} from './models';
import { adaptContinuationReadModel } from './continuation-adapter';
import { adaptResultReadModel } from './result-adapter';
import { adaptEvidenceReadModels, adaptTimelineReadModels } from './timeline-adapter';

export const SCHEDULER_STATE_CONFIG: Readonly<
  Record<
    SchedulerPresentationState,
    { readonly label: string; readonly tone: Tone; readonly presentationState: PresentationState }
  >
> = {
  queued: {
    label: 'Queued',
    tone: 'muted',
    presentationState: 'not-started',
  },
  'ready-looking': {
    label: 'Ready (looking)',
    tone: 'info',
    presentationState: 'not-started',
  },
  'active-looking': {
    label: 'Active (looking)',
    tone: 'info',
    presentationState: 'in-progress',
  },
  'blocked-looking': {
    label: 'Blocked (looking)',
    tone: 'warning',
    presentationState: 'needs-attention',
  },
  'completed-looking': {
    label: 'Completed (looking)',
    tone: 'success',
    presentationState: 'finished',
  },
  attention: {
    label: 'Needs Attention',
    tone: 'danger',
    presentationState: 'needs-attention',
  },
};

export const SCHEDULER_DISCLAIMER_NOTICE =
  'Scheduler state supplied by current data source · Core scheduler semantics pending ITRU-063.';

export const DEPENDENCY_DISCLAIMER_NOTICE =
  'Dependency relations supplied by presentation data source · Core readiness algorithm & dispatch eligibility pending ITRU-063.';

export const EFFECT_AMBIGUOUS_DAG_WARNING =
  'WARNING: effect_ambiguous result · Automatic retry or replay is strictly prohibited. Core defines no safe recovery without external verification.';

/** Pure adapter transforming a single DAG node read-model into a presentation model. */
export function adaptDagNodeReadModel(node: DagNodeReadModel): DagNodePresentation {
  const outcome = node.resultOutcome ?? node.linkedResult?.outcome;
  const isEffectAmbiguous = outcome === 'effect_ambiguous';
  const config = SCHEDULER_STATE_CONFIG[node.schedulerState] ?? {
    label: node.schedulerState,
    tone: 'muted',
    presentationState: 'unknown',
  };

  const linkedResult = node.linkedResult ? adaptResultReadModel(node.linkedResult) : undefined;
  const linkedTimeline = node.linkedTimeline
    ? adaptTimelineReadModels(node.linkedTimeline)
    : undefined;
  const linkedEvidence = node.linkedEvidence
    ? adaptEvidenceReadModels(node.linkedEvidence)
    : undefined;
  const linkedContinuation = node.linkedContinuation
    ? adaptContinuationReadModel(node.linkedContinuation, outcome)
    : undefined;

  // effect_ambiguous always visually overrides tone to danger and presentation state to needs-attention
  const schedulerTone: Tone = isEffectAmbiguous ? 'danger' : config.tone;
  const presentationState: PresentationState = isEffectAmbiguous
    ? 'needs-attention'
    : config.presentationState;

  return {
    id: node.id,
    label: node.label,
    sublabel: node.sublabel,
    kind: node.kind,
    column: node.column,
    lane: node.lane,
    taskId: node.taskId,
    runId: node.runId,
    roleId: node.roleId,
    actorId: node.actorId,
    stageId: node.stageId,
    workflowId: node.workflowId,
    toolId: node.toolId,
    isMainFlow: node.isMainFlow ?? true,
    schedulerState: node.schedulerState,
    schedulerStateLabel: config.label,
    schedulerTone,
    attentionReason: node.attentionReason,
    upstreamNodeIds: node.upstreamNodeIds ?? [],
    downstreamNodeIds: node.downstreamNodeIds ?? [],
    blockedByNodeIds: node.blockedByNodeIds ?? [],
    hasResult: Boolean(node.hasResult || node.linkedResult),
    resultOutcome: node.resultOutcome ?? node.linkedResult?.outcome,
    isEffectAmbiguous,
    hasJournal: Boolean(node.hasJournal || (node.linkedTimeline && node.linkedTimeline.length > 0)),
    hasEvidence: Boolean(node.hasEvidence || (node.linkedEvidence && node.linkedEvidence.length > 0)),
    evidenceCount: node.evidenceCount ?? node.linkedEvidence?.length ?? 0,
    hasContinuation: Boolean(node.hasContinuation || node.linkedContinuation),
    continuationState: node.continuationState ?? node.linkedContinuation?.state,
    continuationBlockedReason: node.continuationBlockedReason ?? node.linkedContinuation?.blockedReason,
    linkedResult: linkedResult ?? undefined,
    linkedTimeline,
    linkedEvidence,
    linkedContinuation,
    presentationState,
  };
}

/** Pure adapter transforming a DAG edge read-model into a presentation model. */
export function adaptDagEdgeReadModel(edge: DagEdgeReadModel): DagEdgePresentation {
  const isTributary = edge.isTributary ?? false;
  return {
    id: edge.id,
    from: edge.from,
    to: edge.to,
    label: edge.label,
    isTributary,
    weight: isTributary ? 'tributary' : 'main',
    state: edge.state ?? 'neutral',
  };
}

/** Pure adapter transforming the complete DAG graph read-model into a presentation model. */
export function adaptDagGraphReadModel(
  model: DagGraphReadModel | undefined,
): DagGraphPresentation | null {
  if (!model) {
    return null;
  }

  const nodes = model.nodes.map(adaptDagNodeReadModel);
  const edges = model.edges.map(adaptDagEdgeReadModel);
  const nodeMap = new Map<string, DagNodePresentation>(nodes.map((node) => [node.id, node]));

  return {
    id: model.id,
    name: model.name,
    scenario: model.scenario,
    description: model.description,
    updatedLabel: model.updatedLabel,
    isStale: Boolean(model.isStale),
    nodes,
    edges,
    schedulerSummary: model.schedulerSummary,
    nodeMap,
  };
}
