import {
  EvidenceCategory,
  EvidenceIntegrityStatus,
  EvidenceItemPresentation,
  EvidenceItemReadModel,
  TimelineItemPresentation,
  TimelineItemReadModel,
  Tone,
} from './models';
import { EVIDENCE_OUTCOME, PRESENTATION_STATE } from '../shared/presentation';
import { adaptResultReadModel } from './result-adapter';

/**
 * Human-readable presentation labels for evidence categories.
 */
const CATEGORY_LABELS: Readonly<Record<EvidenceCategory, string>> = {
  'quality-gate': 'Quality Gate',
  'command-output': 'Command Output',
  'diff-summary': 'Diff Summary',
  'review-note': 'Review Note',
  authorization: 'Authorization Evidence',
  diagnostic: 'Diagnostic Failure',
  'audit-trail': 'Audit Trail',
  'payload-sample': 'Payload Sample',
};

/**
 * Integrity status badges when explicitly supplied by the data source.
 * Core defines no general evidence integrity contract yet; these are
 * presentation labels rendered only when a read model asserts a status.
 */
const INTEGRITY_BADGES: Readonly<Record<EvidenceIntegrityStatus, { readonly label: string; readonly tone: Tone }>> = {
  verified: { label: 'Integrity Verified', tone: 'success' },
  unverified: { label: 'Unverified Signature', tone: 'muted' },
  mismatch: { label: 'Digest Mismatch', tone: 'danger' },
  tampered: { label: 'Potential Tamper', tone: 'danger' },
};

/**
 * Pure adapter mapping an {@link EvidenceItemReadModel} into an {@link EvidenceItemPresentation}.
 *
 * Rules:
 * - Category labels map to human-friendly title casing.
 * - Outlines outcome tones via canonical {@link EVIDENCE_OUTCOME}.
 * - Enforces bounded text and binary representations without inventing authoritative proof.
 * - Formats unavailable evidence states with a clear descriptive message.
 * - Preserves integrity badges only when explicitly supplied.
 */
export function adaptEvidenceReadModel(readModel: EvidenceItemReadModel): EvidenceItemPresentation {
  const categoryLabel = CATEGORY_LABELS[readModel.category] ?? readModel.category;
  const outcomeMeta = EVIDENCE_OUTCOME[readModel.outcome];
  const isTruncated = Boolean(readModel.isTruncated);
  const isUnavailable = Boolean(readModel.isUnavailable);
  const isBinary = Boolean(readModel.binaryHexSample);

  let truncationNotice: string | undefined;
  if (isTruncated) {
    truncationNotice = readModel.byteCount
      ? `Showing bounded preview of ${readModel.byteCount.toLocaleString()} bytes.`
      : 'Showing bounded preview of output lines.';
  }

  let formattedByteCount: string | undefined;
  if (readModel.byteCount !== undefined) {
    formattedByteCount = `${readModel.byteCount.toLocaleString()} bytes`;
  }

  const unavailableReason = isUnavailable
    ? readModel.unavailableReason ?? 'Evidence record could not be resolved from current data source.'
    : undefined;

  const integrityBadge = readModel.integrityStatus ? INTEGRITY_BADGES[readModel.integrityStatus] : undefined;

  return {
    id: readModel.id,
    category: readModel.category,
    categoryLabel,
    kind: readModel.category,
    title: readModel.title,
    summary: readModel.summary,
    outcome: readModel.outcome,
    outcomeLabel: outcomeMeta.label,
    outcomeTone: outcomeMeta.tone,
    source: readModel.source,
    referenceId: readModel.referenceId,
    lines: readModel.lines,
    textPreview: readModel.textPreview,
    isTruncated,
    truncationNotice,
    byteCount: readModel.byteCount,
    formattedByteCount,
    binaryHexSample: readModel.binaryHexSample,
    isBinary,
    isUnavailable,
    unavailableReason,
    integrityStatus: readModel.integrityStatus,
    integrityBadge,
    recordedAtLabel: readModel.recordedAtLabel,
  };
}

/**
 * Adapts an array of {@link EvidenceItemReadModel} into {@link EvidenceItemPresentation} objects.
 */
export function adaptEvidenceReadModels(
  items: readonly EvidenceItemReadModel[] | undefined,
): readonly EvidenceItemPresentation[] {
  if (!items || items.length === 0) {
    return [];
  }
  return items.map(adaptEvidenceReadModel);
}

/**
 * Pure adapter mapping a {@link TimelineItemReadModel} into a {@link TimelineItemPresentation}.
 *
 * Rules:
 * - Maps state labels and tones via canonical {@link PRESENTATION_STATE}.
 * - Connects linked Result presentation via {@link adaptResultReadModel}.
 * - Connects associated evidence records via {@link adaptEvidenceReadModels}.
 * - Computes helper flags (`hasResult`, `hasEvidence`, `hasUnavailableEvidence`).
 * - Never claims presentation order is canonical Journal ordering.
 */
export function adaptTimelineReadModel(readModel: TimelineItemReadModel): TimelineItemPresentation {
  const stateMeta = PRESENTATION_STATE[readModel.state];
  const result = adaptResultReadModel(readModel.result);
  const evidence = adaptEvidenceReadModels(readModel.evidence);
  const evidenceCount = evidence.length;
  const hasEvidence = evidenceCount > 0;
  const hasUnavailableEvidence = evidence.some((e) => e.isUnavailable);

  return {
    id: readModel.id,
    atLabel: readModel.atLabel,
    kind: readModel.kind,
    title: readModel.title,
    detail: readModel.detail,
    state: readModel.state,
    stateLabel: stateMeta.label,
    stateTone: stateMeta.tone,
    actorId: readModel.actorId,
    stageId: readModel.stageId,
    toolId: readModel.toolId,
    executionEntryRef: readModel.executionEntryRef,
    runIdRef: readModel.runIdRef,
    hasResult: Boolean(result),
    result,
    evidenceCount,
    hasEvidence,
    hasUnavailableEvidence,
    evidence,
  };
}

/**
 * Adapts an array of {@link TimelineItemReadModel} into {@link TimelineItemPresentation} objects.
 */
export function adaptTimelineReadModels(
  items: readonly TimelineItemReadModel[] | undefined,
): readonly TimelineItemPresentation[] {
  if (!items || items.length === 0) {
    return [];
  }
  return items.map(adaptTimelineReadModel);
}
