import { describe, expect, it } from 'vitest';
import { adaptContinuationReadModel, CONTINUATION_DISCLAIMER } from './continuation-adapter';
import { RunContinuationReadModel } from './models';

describe('adaptContinuationReadModel', () => {
  it('returns missing state when read model is undefined', () => {
    const result = adaptContinuationReadModel(undefined);
    expect(result.status).toBe('missing');
    expect(result.isMissing).toBe(true);
    expect(result.isAvailable).toBe(false);
    expect(result.statusTone).toBe('muted');
    expect(result.actionDisabled).toBe(true);
    expect(result.disclaimer).toBe(CONTINUATION_DISCLAIMER);
  });

  it('strictly prohibits continuation when resultOutcome is effect_ambiguous regardless of read model', () => {
    const readModel: RunContinuationReadModel = {
      state: 'available',
      isAvailable: true,
      label: 'Resume Now',
    };
    const result = adaptContinuationReadModel(readModel, 'effect_ambiguous');
    expect(result.status).toBe('blocked');
    expect(result.statusLabel).toBe('Continuation Prohibited');
    expect(result.statusTone).toBe('danger');
    expect(result.isAvailable).toBe(false);
    expect(result.isBlocked).toBe(true);
    expect(result.blockedReason).toContain('CRITICAL');
    expect(result.blockedReason).toContain('effect_ambiguous');
    expect(result.actionDisabled).toBe(true);
    expect(result.actionDisabledReason).toContain('strictly prohibited');
  });

  it('handles stale observation state', () => {
    const readModel: RunContinuationReadModel = {
      stale: true,
      staleNotice: 'Runner heartbeat lost 3 hours ago.',
      label: 'Resume execution',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('stale');
    expect(result.isStale).toBe(true);
    expect(result.statusTone).toBe('warning');
    expect(result.staleNotice).toBe('Runner heartbeat lost 3 hours ago.');
    expect(result.actionDisabled).toBe(true);
  });

  it('handles blocked continuation state with source-supplied reason', () => {
    const readModel: RunContinuationReadModel = {
      state: 'blocked',
      blockedReason: 'Awaiting explicit Human checkpoint approval before dispatch.',
      label: 'Resume verification',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('blocked');
    expect(result.isBlocked).toBe(true);
    expect(result.statusTone).toBe('warning');
    expect(result.blockedReason).toBe('Awaiting explicit Human checkpoint approval before dispatch.');
    expect(result.actionDisabled).toBe(true);
  });

  it('handles interrupted run state with interruption notice', () => {
    const readModel: RunContinuationReadModel = {
      state: 'interrupted',
      isAvailable: true,
      interruptionNotice: 'Worker process lost connection to runner daemon.',
      lastKnownActivity: 'Today · 14:15 UTC',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('interrupted');
    expect(result.isInterrupted).toBe(true);
    expect(result.isAvailable).toBe(true);
    expect(result.statusTone).toBe('danger');
    expect(result.interruptionNotice).toContain('Worker process lost connection');
    expect(result.lastKnownActivity).toBe('Today · 14:15 UTC');
    expect(result.actionDisabled).toBe(true);
    expect(result.actionDisabledReason).toContain('Presentation demo only');
  });

  it('handles completed historical run state', () => {
    const readModel: RunContinuationReadModel = {
      state: 'completed',
      reason: 'All workflow stages reached terminal success.',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('completed');
    expect(result.isCompleted).toBe(true);
    expect(result.isAvailable).toBe(false);
    expect(result.statusTone).toBe('neutral');
  });

  it('handles available continuation state with presentation demo behavior', () => {
    const readModel: RunContinuationReadModel = {
      state: 'available',
      isAvailable: true,
      label: 'Resume from validate stage',
      reason: 'Validation phase paused at inspection point.',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('available');
    expect(result.isAvailable).toBe(true);
    expect(result.statusTone).toBe('success');
    expect(result.label).toBe('Resume from validate stage');
    expect(result.actionDisabled).toBe(true);
    expect(result.actionDisabledReason).toContain('Presentation demo only');
  });

  it('handles unavailable continuation state', () => {
    const readModel: RunContinuationReadModel = {
      state: 'unavailable',
      reason: 'Run cannot be resumed from current checkpoint.',
    };
    const result = adaptContinuationReadModel(readModel);
    expect(result.status).toBe('unavailable');
    expect(result.isAvailable).toBe(false);
    expect(result.statusTone).toBe('muted');
  });
});
