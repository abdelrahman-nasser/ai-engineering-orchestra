import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { ContinuationShell } from './continuation-shell';
import { RunContinuationPresentation } from '../data/models';

describe('ContinuationShell', () => {
  async function createFixture(inputs: Partial<{
    continuation: RunContinuationPresentation | null;
    runId: string;
    resultOutcome: any;
    loading: boolean;
    error: string | null;
  }> = {}): Promise<{ fixture: ComponentFixture<ContinuationShell>; element: HTMLElement }> {
    await TestBed.configureTestingModule({
      imports: [ContinuationShell],
    }).compileComponents();

    const fixture = TestBed.createComponent(ContinuationShell);
    if (inputs.continuation !== undefined) {
      fixture.componentRef.setInput('continuation', inputs.continuation);
    }
    if (inputs.runId !== undefined) {
      fixture.componentRef.setInput('runId', inputs.runId);
    }
    if (inputs.resultOutcome !== undefined) {
      fixture.componentRef.setInput('resultOutcome', inputs.resultOutcome);
    }
    if (inputs.loading !== undefined) {
      fixture.componentRef.setInput('loading', inputs.loading);
    }
    if (inputs.error !== undefined) {
      fixture.componentRef.setInput('error', inputs.error);
    }
    fixture.detectChanges();
    return { fixture, element: fixture.nativeElement as HTMLElement };
  }

  const text = (el: Element | null) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

  it('renders disclaimer banner on continuation affordance', async () => {
    const { element } = await createFixture();
    expect(text(element.querySelector('.disclaimer-banner'))).toContain(
      'Mock continuation metadata only',
    );
    expect(text(element.querySelector('.disclaimer-banner'))).toContain('No operational resume controls are connected');
  });

  it('renders missing continuation state honestly when none supplied', async () => {
    const { element } = await createFixture({ continuation: null });
    expect(text(element.querySelector('[data-testid="missing-continuation-notice"]'))).toContain(
      'No continuation metadata supplied',
    );
    expect(element.querySelector('[data-testid="continuation-resume-button"]')).toBeNull();
  });

  it('renders available continuation with disabled demo button and note', async () => {
    const continuation: RunContinuationPresentation = {
      status: 'available',
      statusLabel: 'Continuation available',
      statusTone: 'success',
      isAvailable: true,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: 'Resume from validation',
      reason: 'Validation phase paused at inspection point.',
      disclaimer: 'Continuation disclaimer',
      actionDisabled: true,
      actionDisabledReason: 'Presentation demo only · No Core resume mutation exists',
    };
    const { element } = await createFixture({ continuation });
    const btn = element.querySelector<HTMLButtonElement>('[data-testid="continuation-resume-button"]')!;
    expect(btn).not.toBeNull();
    expect(btn.disabled).toBe(true);
    expect(text(btn)).toContain('Resume from validation');
    expect(text(element.querySelector('.action-note'))).toContain('Presentation demo only');
  });

  it('renders blocked state with blocked reason', async () => {
    const continuation: RunContinuationPresentation = {
      status: 'blocked',
      statusLabel: 'Continuation blocked',
      statusTone: 'warning',
      isAvailable: false,
      isBlocked: true,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: 'Resume execution',
      blockedReason: 'Human checkpoint approval required before continuation.',
      disclaimer: 'Continuation disclaimer',
      actionDisabled: true,
      actionDisabledReason: 'Human checkpoint approval required',
    };
    const { element } = await createFixture({ continuation });
    expect(text(element.querySelector('[data-testid="continuation-blocked-notice"]'))).toContain(
      'Human checkpoint approval required',
    );
    expect(element.querySelector('[data-testid="continuation-resume-button"]')).toBeNull();
  });

  it('renders interrupted state with interruption notice', async () => {
    const continuation: RunContinuationPresentation = {
      status: 'interrupted',
      statusLabel: 'Interrupted',
      statusTone: 'danger',
      isAvailable: false,
      isBlocked: false,
      isInterrupted: true,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      interruptionNotice: 'Worker node lost lease heartbeat.',
      lastKnownActivity: 'Today · 14:15 UTC',
      disclaimer: 'Continuation disclaimer',
      actionDisabled: true,
    };
    const { element } = await createFixture({ continuation });
    expect(text(element.querySelector('[data-testid="interruption-notice"]'))).toContain(
      'Worker node lost lease heartbeat',
    );
    expect(text(element)).toContain('Today · 14:15 UTC');
  });

  it('strictly prohibits continuation when resultOutcome is effect_ambiguous', async () => {
    const continuation: RunContinuationPresentation = {
      status: 'available',
      statusLabel: 'Continuation available',
      statusTone: 'success',
      isAvailable: true,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: false,
      isMissing: false,
      label: 'Resume Run',
      disclaimer: 'Continuation disclaimer',
      actionDisabled: true,
    };
    const { element } = await createFixture({
      continuation,
      resultOutcome: 'effect_ambiguous',
    });
    const alert = element.querySelector('[data-testid="effect-ambiguous-continuation-alert"]');
    expect(alert).not.toBeNull();
    expect(text(alert)).toContain('CRITICAL EFFECT UNCERTAINTY');
    expect(text(alert)).toContain('strictly prohibit automated retry, replay, or continuation');
    expect(element.querySelector('[data-testid="continuation-resume-button"]')).toBeNull();
  });

  it('renders stale notice when continuation observation is stale', async () => {
    const continuation: RunContinuationPresentation = {
      status: 'stale',
      statusLabel: 'Stale observation',
      statusTone: 'warning',
      isAvailable: false,
      isBlocked: false,
      isInterrupted: false,
      isCompleted: false,
      isStale: true,
      isMissing: false,
      staleNotice: 'Observation timestamp was not refreshed in the last 2 hours.',
      disclaimer: 'Continuation disclaimer',
      actionDisabled: true,
    };
    const { element } = await createFixture({ continuation });
    expect(text(element.querySelector('[data-testid="stale-notice"]'))).toContain(
      'Observation timestamp was not refreshed',
    );
  });
});
