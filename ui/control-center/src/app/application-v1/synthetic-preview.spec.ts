import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it } from 'vitest';
import { SyntheticPreview } from './synthetic-preview';

describe('application v1.0 synthetic preview', () => {
  async function open() {
    await TestBed.configureTestingModule({
      imports: [SyntheticPreview],
      providers: [provideRouter([])],
    }).compileComponents();
    const fixture = TestBed.createComponent(SyntheticPreview);
    await fixture.whenStable();
    const element = fixture.nativeElement as HTMLElement;
    const choose = async (id: string) => {
      const select = element.querySelector<HTMLSelectElement>('#application-scenario')!;
      select.value = id;
      select.dispatchEvent(new Event('change'));
      await fixture.whenStable();
    };
    return { fixture, element, choose };
  }
  it('labels the isolated source and keeps every operational control disabled', async () => {
    const { element, choose } = await open();
    expect(element.textContent).toContain('SYNTHETIC DATA ONLY');
    expect(element.querySelector('[data-testid="approval-count"]')?.textContent).toContain(
      'Unavailable',
    );
    expect(element.querySelector('[data-testid="configured-route"]')?.textContent).toContain(
      'Unavailable',
    );
    for (const scenario of [
      'interrupted-success',
      'conflict',
      'partial-empty',
      'stale',
      'denied',
      'complete-empty',
    ]) {
      await choose(scenario);
      const buttons = Array.from(element.querySelectorAll<HTMLButtonElement>('button'));
      expect(buttons.map((button) => button.textContent)).toEqual([
        'Execute',
        'Approve',
        'Cancel',
        'Resume',
      ]);
      expect(buttons.every((button) => button.disabled)).toBe(true);
    }
    expect(element.querySelector('cc-result-shell')).toBeNull();
    expect(element.querySelector('cc-continuation-shell')).toBeNull();
  });
  it('shows independent lifecycle and Journal evidence, exact numbers, times and zero-byte success', async () => {
    const { element } = await open();
    expect(element.querySelector('[data-testid="task-state"]')?.textContent).toContain('blocked');
    expect(element.querySelector('[data-testid="run-state"]')?.textContent).toContain(
      'interrupted',
    );
    expect(element.querySelector('[data-testid="recorded-outcome"]')?.textContent).toContain(
      'succeeded',
    );
    expect(element.textContent).toContain('9007199254740993');
    expect(element.textContent).toContain('9223372036854775807');
    expect(element.textContent).toContain('2026-10-17T09:59:59.1Z');
    expect(element.textContent).toContain('byte count: 0');
    expect(element.textContent).toContain('journal_result_without_lifecycle_acceptance');
    expect(element.textContent).toContain('SYNTHETIC-disconnected-pending');
    expect(element.querySelectorAll('pre, img, [data-testid="payload-preview"]')).toHaveLength(0);
    expect(element.textContent).not.toMatch(
      /signature verified|tamper.proof|digest|payload preview|safe to resume/i,
    );
  });
  it('makes partial-empty and complete-empty evidence limits explicit', async () => {
    const { element, choose } = await open();
    await choose('partial-empty');
    expect(element.querySelector('[data-testid="journal-status"]')?.textContent).toContain(
      'partial',
    );
    expect(element.querySelector('[data-testid="coverage-notice"]')?.textContent).toContain(
      'uniqueness remain unproven',
    );
    expect(element.textContent).toContain('9007199254740994');
    await choose('complete-empty');
    expect(element.querySelector('[data-testid="journal-status"]')?.textContent).toContain(
      'complete-empty',
    );
    expect(element.querySelector('[data-testid="coverage-notice"]')?.textContent).toContain(
      'does not establish absence',
    );
  });
  it('shows all conflicting subjects and does not collapse them to a success badge', async () => {
    const { element, choose } = await open();
    await choose('conflict');
    expect(element.querySelectorAll('[data-testid="journal-record"]')).toHaveLength(4);
    expect(element.textContent).toContain('SYNTHETIC-other-grant');
    expect(element.textContent).toContain('effect_ambiguous');
    expect(element.textContent).toContain('multiple_physical_subjects');
    expect(element.querySelector('[data-testid="run-state"]')?.textContent).toContain(
      'interrupted',
    );
  });
  it('retains original stale time and removes subject metadata after denial', async () => {
    const { element, choose } = await open();
    await choose('stale');
    expect(element.querySelector('[data-testid="journal-status"]')?.textContent).toContain('stale');
    expect(element.textContent).toContain('2026-10-17T10:00:01.000000Z');
    await choose('denied');
    expect(element.querySelectorAll('[data-testid="journal-record"]')).toHaveLength(0);
    expect(element.textContent).not.toContain('SYNTHETIC-run-z');
    expect(element.textContent).not.toContain('SYNTHETIC-ledger');
    expect(element.querySelector('[data-testid="lifecycle-status"]')?.textContent).toContain(
      'denied',
    );
  });
});
