import {
  AgentExecutionResultDiagnosticCode,
  AgentExecutionResultOutcome,
  AgentExecutionResultPresentation,
  AgentExecutionResultReadModel,
  ResultDiagnosticPresentation,
  ResultPayloadPresentation,
  Tone,
} from './models';

/**
 * Closed canonical explanations for ITRU-060 diagnostic codes.
 * Mirrors core/agent-execution-result-specification.md §7.
 */
const DIAGNOSTIC_DEFINITIONS: Record<
  AgentExecutionResultDiagnosticCode,
  { readonly title: string; readonly explanation: string }
> = {
  containment_rejected: {
    title: 'Containment Rejected',
    explanation: 'Target resource path violated strict repository containment boundaries.',
  },
  resource_missing: {
    title: 'Resource Missing',
    explanation: 'Declared repository resource could not be found at the designated path.',
  },
  resource_changed: {
    title: 'Resource Changed',
    explanation: 'Resource metadata or content changed unexpectedly during validation checks.',
  },
  adapter_unavailable: {
    title: 'Adapter Unavailable',
    explanation: 'Native adapter support or execution capability was unavailable.',
  },
  size_limit_exceeded: {
    title: 'Size Limit Exceeded',
    explanation: 'Content size exceeded the bounded maximum limit (65,536 bytes).',
  },
  read_failure: {
    title: 'Read Failure',
    explanation: 'An underlying I/O error occurred during content-data acquisition.',
  },
  guard_lost: {
    title: 'Guard Lost',
    explanation: 'Execution guard context was lost before operation completed.',
  },
  ownership_lost: {
    title: 'Ownership Lost',
    explanation: 'Resource ownership verification failed during post-execution checks.',
  },
  effect_ambiguous: {
    title: 'Effect Ambiguous',
    explanation: 'Operation progress evidence was interrupted; effect boundary status is unknown.',
  },
};

interface OutcomeMetadata {
  readonly label: string;
  readonly tone: Tone;
  readonly headline: string;
  readonly description: string;
  readonly retryNotice?: string;
}

const OUTCOME_METADATA: Record<AgentExecutionResultOutcome, OutcomeMetadata> = {
  succeeded: {
    label: 'Succeeded',
    tone: 'success',
    headline: 'Operation completed successfully',
    description:
      'All operation phases, mandatory cleanup, and post-execution ownership checks passed. Safe immutable payload captured.',
  },
  failed_before_effect: {
    label: 'Failed Before Effect',
    tone: 'neutral',
    headline: 'Terminated before content-data effect',
    description:
      'The trusted boundary positively proves that no content-data read request began and no content effect occurred.',
    retryNotice:
      'Execution Entry is permanently consumed. Any subsequent execution requires fresh authorization under standard governance; no automatic retry.',
  },
  effect_ambiguous: {
    label: 'Effect Ambiguous',
    tone: 'warning',
    headline: 'Uncertain effect boundary',
    description:
      'Content-data read request was initiated, but validated completion is unavailable, or post-operation cleanup uncertainty was observed. Validated completion or no-effect cannot be claimed.',
    retryNotice:
      'CRITICAL: Do NOT automatically retry or replay. Execution Entry is permanently consumed. Automatic retry/replay is strictly prohibited to prevent duplicate reads or corrupted state.',
  },
};

/**
 * Pure adapter mapping an {@link AgentExecutionResultReadModel} into a screen-ready
 * {@link AgentExecutionResultPresentation}.
 *
 * This functions as the presentation boundary:
 * - Formats the derived 5-part Result identity tuple.
 * - Enforces ITRU-060 payload absence on failures and diagnostic absence on success.
 * - Formats bounded payload sizes and truncation summaries.
 * - Supplies canonical diagnostic explanations from the closed ITRU-060 table.
 * - Communicates effect-boundary uncertainty and permanent entry consumption without
 *   inventing transport or persistence contracts.
 */
export function adaptResultReadModel(
  readModel: AgentExecutionResultReadModel | null | undefined,
): AgentExecutionResultPresentation | null {
  if (!readModel) {
    return null;
  }

  const meta = OUTCOME_METADATA[readModel.outcome];
  const derived = readModel.derivedIdentity;
  const derivedIdentityFormatted = `(${derived.ledgerInstanceId}, ${derived.authorizationDomainId}, ${derived.issuerKind}, ${derived.issuerId}, ${derived.grantId})`;

  let payload: ResultPayloadPresentation | null = null;
  if (readModel.outcome === 'succeeded' && readModel.payload) {
    const p = readModel.payload;
    payload = {
      byteCount: p.byteCount,
      formattedByteCount: `${p.byteCount.toLocaleString()} bytes`,
      isText: p.isText,
      textPreview: p.textPreview,
      bytesSampleHex: p.bytesSampleHex,
      isTruncated: p.isTruncated,
      truncationNotice: p.isTruncated
        ? `Showing first ${p.previewByteCount.toLocaleString()} of ${p.byteCount.toLocaleString()} bytes (bounded preview).`
        : undefined,
    };
  }

  let diagnostic: ResultDiagnosticPresentation | null = null;
  if (readModel.outcome !== 'succeeded' && readModel.diagnostic) {
    const code = readModel.diagnostic.code;
    const def = DIAGNOSTIC_DEFINITIONS[code] ?? {
      title: code,
      explanation: 'Canonical execution diagnostic code recorded by trusted coordinator.',
    };
    diagnostic = {
      code,
      title: def.title,
      explanation: def.explanation,
    };
  }

  return {
    outcome: readModel.outcome,
    outcomeLabel: meta.label,
    outcomeTone: meta.tone,
    semanticEffect: {
      headline: meta.headline,
      description: meta.description,
      retryNotice: meta.retryNotice,
    },
    identity: {
      derivedIdentityFormatted,
      ledgerInstanceId: derived.ledgerInstanceId,
      domainId: derived.authorizationDomainId,
      issuer: `${derived.issuerKind}:${derived.issuerId}`,
      grantId: derived.grantId,
      claimId: readModel.executionEntry.claimId,
      executorInstanceId: readModel.executionEntry.executorInstanceId,
      leaseGeneration: readModel.executionEntry.leaseGeneration,
      entryTimeLabel: readModel.executionEntry.entryTimeLabel,
      timeKey: readModel.executionEntry.timeKey,
      toolIdentity: readModel.toolBinding.toolIdentity,
      configuredRoute: readModel.toolBinding.configuredRoute,
    },
    payload,
    diagnostic,
  };
}
