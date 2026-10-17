import { describe, expect, it } from 'vitest';
import {
  errorFixture,
  inspectionFixture,
  journalFixture,
  previewContext,
  scenarioSession,
  scenarios,
} from './fixtures';
import { PreviewSession, unsupported } from './presentation';

describe('synthetic observation display state', () => {
  it('decodes every published fixture through the application boundary', () => {
    for (const [id] of scenarios) {
      const session = scenarioSession(id);
      if (id !== 'invalid') expect(session.journal.status, id).not.toBe('invalid');
    }
  });
  it('retains interrupted lifecycle, blocked Task and recorded success separately', () => {
    const session = scenarioSession('interrupted-success');
    expect(session.inspection.value?.lifecycle.run_state).toBe('interrupted');
    expect(session.inspection.value?.lifecycle.task_state).toBe('blocked');
    expect(session.journal.value?.comparison.core_reconciliation?.recorded_outcome).toBe(
      'succeeded',
    );
    expect(session.inspection.value?.continuation).toEqual({
      eligibility: 'unassessed',
      action_available: false,
    });
    expect(session.inspection.value?.scheduling.occupied_run_ids).toContain(
      'SYNTHETIC-disconnected-pending',
    );
    expect(session.inspection.value?.scheduling.evaluations[1].state).toBe('blocked');
  });
  it('does not promote a Task to completed from a successful historical Run or redefine latest', () => {
    const session = scenarioSession('success-task-active');
    expect(session.inspection.value?.lifecycle.run_state).toBe('succeeded');
    expect(session.inspection.value?.lifecycle.task_state).toBe('in_progress');
    expect(session.inspection.value?.task_run_history.latest_run_id).toBe('SYNTHETIC-run-a');
    expect(session.inspection.value?.lifecycle.binding.run.run_id).toBe('SYNTHETIC-run-z');
    expect(session.inspection.value?.scheduling.evaluations[1].dependencies.state).toBe('blocked');
  });
  it('distinguishes empty partial pages from complete-empty evidence', () => {
    const partial = scenarioSession('partial-empty').journal;
    expect(partial.status).toBe('partial');
    expect(partial.value?.records).toEqual([]);
    expect(partial.value?.traversal.high_water).toBe('9007199254740994');
    expect(partial.value?.traversal.next_cursor).not.toBeNull();
    expect(partial.value?.comparison.core_reconciliation).toBeNull();
    expect(scenarioSession('complete-empty').journal.status).toBe('complete-empty');
  });
  it('does not choose a winning physical subject or outcome', () => {
    const session = scenarioSession('conflict');
    expect(session.journal.value?.records).toHaveLength(4);
    expect(session.journal.value?.comparison.discrepancies).toEqual([
      'different_outcomes',
      'multiple_physical_subjects',
    ]);
    expect(session.journal.value?.comparison.core_reconciliation?.recorded_outcome).toBeNull();
    expect(session.inspection.value?.lifecycle.run_state).toBe('interrupted');
  });
  it('preserves Core incomplete decision and missing observation without creating selection', () => {
    const schedule = scenarioSession('incomplete').inspection.value?.scheduling;
    expect(schedule?.state).toBe('incomplete_snapshot');
    expect(schedule?.snapshot_coverage.missing_task_ids).toEqual(['SYNTHETIC-task-b']);
    expect(schedule?.selected_task_ids).toEqual([]);
  });
  it('preserves the supplied over-capacity decision and disconnected occupied Run', () => {
    const schedule = scenarioSession('over-capacity').inspection.value?.scheduling;
    expect(schedule?.state).toBe('over_capacity');
    expect(schedule?.max_concurrency).toBe(1);
    expect(schedule?.occupied_run_ids).toEqual([
      'SYNTHETIC-run-a',
      'SYNTHETIC-disconnected-pending',
    ]);
    expect(schedule?.selected_task_ids).toEqual([]);
  });
  it('preserves original time and scope after busy refresh under continuing entitlement', () => {
    const session = scenarioSession('interrupted-success');
    const original = session.journal.value;
    session.receiveJournal(errorFixture('source_busy'), session.deliveryContext);
    expect(session.journal.status).toBe('stale');
    expect(session.journal.value).toBe(original);
    session.receiveInspection(errorFixture('owner_unavailable'), session.deliveryContext);
    expect(session.inspection.status).toBe('stale');
    expect(session.inspection.value?.source_observation.observed_at).toBe(
      '2026-10-17T10:00:00.000000Z',
    );
  });
  for (const field of ['principal', 'policy', 'source', 'revision'] as const) {
    it(`clears all retained references when ${field} changes`, () => {
      const session = scenarioSession('stale');
      const delivery = session.deliveryContext;
      session.changeContext({ ...previewContext, [field]: 'OTHER-context' });
      expect(session.inspection.value).toBeNull();
      expect(session.journal.value).toBeNull();
      expect(JSON.stringify(session)).not.toContain('SYNTHETIC-inspection');
      session.receiveInspection(inspectionFixture(), delivery);
      session.receiveJournal(journalFixture(), delivery);
      expect(session.inspection.value).toBeNull();
      expect(session.journal.value).toBeNull();
    });
  }
  it('clears denial/revocation immediately and rejects late successful responses', () => {
    const session = scenarioSession('stale');
    const delivery = session.deliveryContext;
    session.receiveJournal(errorFixture('access_denied'), delivery);
    expect(session.inspection.status).toBe('denied');
    expect(session.journal.status).toBe('denied');
    session.receiveInspection(inspectionFixture(), delivery);
    session.receiveJournal(journalFixture(), delivery);
    expect(session.inspection.value).toBeNull();
    expect(session.journal.value).toBeNull();
    const revoked = scenarioSession('stale');
    revoked.changeContext({ ...previewContext, entitled: false });
    expect(revoked.inspection.value).toBeNull();
    expect(revoked.journal.value).toBeNull();
  });
  it('withholds invalid Journal records without removing the independent lifecycle observation', () => {
    const session = scenarioSession('stale');
    session.receiveJournal(
      { ...journalFixture(), raw_exception: 'private' },
      session.deliveryContext,
    );
    expect(session.journal.status).toBe('invalid');
    expect(session.journal.value).toBeNull();
    expect(session.inspection.value?.lifecycle.run_state).toBe('interrupted');
    expect(JSON.stringify(session)).not.toContain('private');
  });
  it('keeps failure classes distinct, with no empty-success substitution', () => {
    const expected = {
      unavailable: 'unavailable',
      denied: 'denied',
      incompatible: 'incompatible',
      invalid: 'invalid',
      expired: 'expired',
      exhausted: 'exhausted',
    };
    for (const [scenario, status] of Object.entries(expected)) {
      const session = scenarioSession(scenario);
      expect(session.journal.status).toBe(status);
      expect(session.journal.value).toBeNull();
    }
    expect(scenarioSession('not-found').inspection.status).toBe('not-found');
    expect(new PreviewSession(previewContext).inspection.status).toBe('loading');
    expect(unsupported.approvals).toContain('Unavailable');
    expect(unsupported.configuredRoute).toContain('Unavailable');
  });
  it('clears stale Journal references on a newly captured inspection', () => {
    const session = scenarioSession('stale');
    session.receiveInspection(inspectionFixture(), session.deliveryContext);
    expect(session.journal.status).toBe('loading');
    expect(session.journal.value).toBeNull();
  });
  it('invalidates old-source deliveries after a source revision error', () => {
    const session = scenarioSession('stale');
    const delivery = session.deliveryContext;
    session.receiveJournal(errorFixture('source_revision_changed'), delivery);
    session.receiveInspection(inspectionFixture(), delivery);
    expect(session.inspection.status).toBe('expired');
    expect(session.inspection.value).toBeNull();
    expect(session.journal.value).toBeNull();
  });
  it('does not revive old responses after switching away and back to an identical principal', () => {
    const session = scenarioSession('stale');
    const oldDelivery = session.deliveryContext;
    session.changeContext({ ...previewContext, principal: 'OTHER-principal' });
    session.changeContext(previewContext);
    session.receiveInspection(inspectionFixture(), oldDelivery);
    expect(session.inspection.value).toBeNull();
    session.receiveInspection(inspectionFixture(), session.deliveryContext);
    expect(session.inspection.status).toBe('ready');
  });
});
