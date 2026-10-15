import {
  AgentExecutionResultOutcome,
  RunContinuationPresentation,
  RunContinuationReadModel,
} from './models';
import { CONTINUATION_STATUS } from '../shared/presentation';

export const CONTINUATION_DISCLAIMER =
  'Continuation availability supplied by current data source · Core defines no canonical continuation/resume contract yet (pending ITRU-062).';

/**
 * Pure adapter mapping a {@link RunContinuationReadModel} into a screen-ready
 * {@link RunContinuationPresentation}.
 *
 * Strict boundary rules:
 * 1. If result outcome is 'effect_ambiguous', continuation is strictly PROHIBITED:
 *    Core semantics prohibit automated retry, replay, or unguided continuation.
 * 2. If read model is undefined, returns 'missing' state with honest notice.
 * 3. Never defines what makes a Run resumable or canonical checkpoint/resume tokens.
 * 4. Actions are presentation-only / disabled demo behaviors.
 */
export function adaptContinuationReadModel(
  readModel: RunContinuationReadModel | undefined,
  resultOutcome?: AgentExecutionResultOutcome,
): RunContinuationPresentation {
  // Rule 1: effect_ambiguous strictly prohibits continuation, retry, or replay
  if (resultOutcome === 'effect_ambiguous') {
    return {
      status: 'blocked',
      statusLabel: 'Continuation Prohibited',
      statusTone: 'danger',
      isAvailable: false,
      isBlocked: true,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: 'Continuation Prohibited',
      reason: 'Result ended in uncertain effect boundary (effect_ambiguous).',
      blockedReason:
        'CRITICAL: Execution ended in effect_ambiguous outcome. Core semantics strictly prohibit automated retry, replay, or unguided continuation to prevent duplicate side effects.',
      interruptionNotice: undefined,
      lastKnownActivity: readModel?.lastKnownActivity,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason: 'Continuation strictly prohibited for effect_ambiguous outcomes.',
    };
  }

  // Rule 2: missing continuation information
  if (!readModel) {
    return {
      status: 'missing',
      statusLabel: CONTINUATION_STATUS.missing.label,
      statusTone: CONTINUATION_STATUS.missing.tone,
      isAvailable: false,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: true,
      label: undefined,
      reason: 'No continuation metadata supplied by current data source.',
      blockedReason: undefined,
      interruptionNotice: undefined,
      lastKnownActivity: undefined,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason: 'No continuation metadata supplied by current data source.',
    };
  }

  // Rule 3: stale observation
  if (readModel.stale) {
    return {
      status: 'stale',
      statusLabel: CONTINUATION_STATUS.stale.label,
      statusTone: CONTINUATION_STATUS.stale.tone,
      isAvailable: false,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: true,
      isMissing: false,
      label: readModel.label,
      reason: readModel.reason,
      blockedReason: readModel.blockedReason,
      interruptionNotice: readModel.interruptionNotice,
      lastKnownActivity: readModel.lastKnownActivity,
      staleNotice:
        readModel.staleNotice ??
        'Observation timestamp is unrefreshed; current runner status cannot be confirmed.',
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason: 'Cannot continue from stale observation data.',
    };
  }

  // Rule 4: blocked continuation
  if (readModel.blockedReason || readModel.state === 'blocked') {
    return {
      status: 'blocked',
      statusLabel: CONTINUATION_STATUS.blocked.label,
      statusTone: CONTINUATION_STATUS.blocked.tone,
      isAvailable: false,
      isBlocked: true,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: readModel.label,
      reason: readModel.reason,
      blockedReason:
        readModel.blockedReason ?? 'Continuation is blocked by current data source.',
      interruptionNotice: readModel.interruptionNotice,
      lastKnownActivity: readModel.lastKnownActivity,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason:
        readModel.blockedReason ?? 'Continuation is blocked by current data source.',
    };
  }

  // Rule 5: interrupted run
  if (readModel.state === 'interrupted' || readModel.interruptionNotice) {
    const isAvail = Boolean(readModel.isAvailable);
    return {
      status: 'interrupted',
      statusLabel: CONTINUATION_STATUS.interrupted.label,
      statusTone: CONTINUATION_STATUS.interrupted.tone,
      isAvailable: isAvail,
      isBlocked: false,
      isInterrupted: true,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: readModel.label ?? (isAvail ? 'Resume from Interruption' : undefined),
      reason: readModel.reason,
      blockedReason: undefined,
      interruptionNotice:
        readModel.interruptionNotice ?? 'Execution was interrupted and requires operator attention.',
      lastKnownActivity: readModel.lastKnownActivity,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason:
        'Presentation demo only · Core persistence and resume mutation is uninvented pending ITRU-062.',
    };
  }

  // Rule 6: completed historical run
  if (readModel.state === 'completed') {
    return {
      status: 'completed',
      statusLabel: CONTINUATION_STATUS.completed.label,
      statusTone: CONTINUATION_STATUS.completed.tone,
      isAvailable: false,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: true,
      isStale: false,
      isMissing: false,
      label: undefined,
      reason: readModel.reason ?? 'Run has reached completed terminal state.',
      blockedReason: undefined,
      interruptionNotice: undefined,
      lastKnownActivity: readModel.lastKnownActivity,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason: 'Historical run already completed.',
    };
  }

  // Rule 7: available
  if (readModel.isAvailable || readModel.state === 'available') {
    return {
      status: 'available',
      statusLabel: CONTINUATION_STATUS.available.label,
      statusTone: CONTINUATION_STATUS.available.tone,
      isAvailable: true,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: readModel.label ?? 'Resume Run',
      reason: readModel.reason,
      blockedReason: undefined,
      interruptionNotice: undefined,
      lastKnownActivity: readModel.lastKnownActivity,
      staleNotice: undefined,
      disclaimer: CONTINUATION_DISCLAIMER,
      actionDisabled: true,
      actionDisabledReason:
        'Presentation demo only · Core persistence and resume mutation is uninvented pending ITRU-062.',
    };
  }

  // Rule 8: unavailable
  return {
    status: 'unavailable',
    statusLabel: CONTINUATION_STATUS.unavailable.label,
    statusTone: CONTINUATION_STATUS.unavailable.tone,
    isAvailable: false,
    isBlocked: false,
    isInterrupted: false,
    isCompleted: false,
    isStale: false,
    isMissing: false,
    label: undefined,
    reason: readModel.reason ?? 'Continuation is not available for this run.',
    blockedReason: undefined,
    interruptionNotice: undefined,
    lastKnownActivity: readModel.lastKnownActivity,
    staleNotice: undefined,
    disclaimer: CONTINUATION_DISCLAIMER,
    actionDisabled: true,
    actionDisabledReason: 'Continuation is not available.',
  };
}
