import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it } from 'vitest';
import { SyntheticPreview } from './synthetic-preview';
import { scenarios } from './fixtures';

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
    for (const [scenario] of scenarios) {
      await choose(scenario);
      const buttons = Array.from(element.querySelectorAll<HTMLButtonElement>('[aria-label="Operational controls"] button'));
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
  it('announces concise observation state changes and labels keyboard-scrollable scheduler columns', async () => {
    const { element, choose } = await open();
    const status = element.querySelector<HTMLElement>('[data-testid="scenario-status"]')!;
    expect(status.getAttribute('role')).toBe('status');
    expect(status.getAttribute('aria-atomic')).toBe('true');
    expect(element.querySelector('label[for="application-scenario"]')).not.toBeNull();
    const region = element.querySelector<HTMLElement>('.table-scroll')!;
    expect(region.tabIndex).toBe(0);
    expect(region.getAttribute('aria-label')).toContain('Supplied scheduler evaluations');
    expect(Array.from(region.querySelectorAll('th')).every((th) => th.scope === 'col')).toBe(true);
    await choose('partial-empty');
    expect(status.textContent).toContain('Journal observation: partial');
    await choose('denied');
    expect(status.textContent).toContain('Lifecycle observation: denied');
    expect(status.textContent).toContain('Operational controls unavailable');
    expect(status.textContent).not.toContain('SYNTHETIC-run');
  });
  it('renders exact long synthetic identities and resource without weakening decoding', async () => {
    const { element, choose } = await open();
    await choose('long-text');
    expect(element.querySelector('[data-testid="lifecycle-status"]')?.textContent).toBe('ready');
    expect(element.querySelector('[data-testid="journal-status"]')?.textContent).toBe('ready');
    expect(element.textContent).toContain(`SYNTHETIC-run-${'identity'.repeat(24)}`);
    expect(element.textContent).toContain(`SYNTHETIC-grant-${'physical'.repeat(24)}`);
    element.querySelector('details')!.open = true;
    expect(element.textContent).toContain(`synthetic/${'resource'.repeat(24)}/example.txt`);
    expect(element.querySelectorAll('[data-testid="journal-record"]')).toHaveLength(2);
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

  it('walks all five stops, moves focus and returns to Task without changing observations', async () => {
    const { fixture, element } = await open();
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    const steps = guide.querySelectorAll<HTMLButtonElement>('nav button');
    expect(Array.from(steps).map((button) => button.textContent?.trim().slice(1))).toEqual([
      'Task', 'Approval preview', 'Run', 'Result', 'Journal',
    ]);
    for (let index = 0; index < steps.length; index++) {
      steps[index].click();
      await fixture.whenStable();
      expect(guide.querySelectorAll('[aria-current="step"]')).toHaveLength(1);
      expect(steps[index].getAttribute('aria-current')).toBe('step');
      expect(guide.querySelector('h3')?.textContent).toBe(['Task', 'Approval preview', 'Run', 'Result', 'Journal'][index]);
      expect(document.activeElement).toBe(guide.querySelector('h3'));
      expect(element.querySelector('[data-testid="run-state"]')?.textContent).toContain('interrupted');
    }
    guide.querySelector<HTMLButtonElement>('footer .next')!.click();
    await fixture.whenStable();
    expect(steps[0].getAttribute('aria-current')).toBe('step');
    expect(guide.querySelector<HTMLButtonElement>('footer button')?.disabled).toBe(true);
    guide.querySelector<HTMLButtonElement>('footer .next')!.click();
    await fixture.whenStable();
    expect(steps[1].getAttribute('aria-current')).toBe('step');
    guide.querySelector<HTMLButtonElement>('footer button')!.click();
    await fixture.whenStable();
    expect(steps[0].getAttribute('aria-current')).toBe('step');
  });

  it('previews the exact selected subject without claiming approval or executable authority', async () => {
    const { fixture, element } = await open();
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    guide.querySelectorAll<HTMLButtonElement>('nav button')[1].click();
    await fixture.whenStable();
    expect(guide.textContent).toContain('no authorization is requested or granted');
    expect(guide.textContent).toContain('SYNTHETIC-task-a / SYNTHETIC-run-z');
    expect(guide.textContent).toContain('SYNTHETIC-runtime / SYNTHETIC-inference');
    expect(guide.textContent).toContain('repository_file_read / synthetic/example.txt');
    expect(guide.textContent).toContain('Continuation remains unassessed');
    expect(guide.querySelectorAll('input, select, form')).toHaveLength(0);
  });

  it('keeps all 18 original scenarios discoverable and clears guided references on denial at every stop', async () => {
    const { fixture, element, choose } = await open();
    expect(element.querySelectorAll('#application-scenario option')).toHaveLength(18);
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    for (const [id] of scenarios) {
      await choose(id);
      expect(guide.querySelector('.explore')?.textContent).not.toContain('Explore the supplied synthetic observations.');
    }
    const steps = guide.querySelectorAll<HTMLButtonElement>('nav button');
    for (let index = 0; index < steps.length; index++) {
      await choose('interrupted-success');
      steps[index].click();
      await fixture.whenStable();
      await choose('denied');
      expect(steps[index].getAttribute('aria-current')).toBe('step');
      expect(guide.textContent).not.toMatch(/SYNTHETIC-(task|run|grant|ledger|actor|runtime|inference)/);
      expect(guide.textContent).toContain('denied');
    }
  });

  it('explains lifecycle examples without fabricating state changes or continuation permission', async () => {
    const { fixture, element } = await open();
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    guide.querySelectorAll<HTMLButtonElement>('nav button')[2].click();
    await fixture.whenStable();
    const glossary = guide.querySelector('details')!;
    expect(glossary.querySelectorAll('dt')).toHaveLength(7);
    expect(glossary.textContent).toContain('not a transition sequence');
    expect(glossary.textContent).toContain('No operation content-data request began');
    expect(glossary.textContent).toContain('blocks continuation and automatic retry or replay');
    expect(glossary.textContent).toContain('No original Result was durably accepted');
    expect(guide.textContent).toContain('Supplied Run state: Interrupted');
  });

  it('preserves independent Result acceptance, multiple subjects and missing Result summaries', async () => {
    const { fixture, element, choose } = await open();
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    guide.querySelectorAll<HTMLButtonElement>('nav button')[3].click();
    await fixture.whenStable();
    expect(guide.textContent).toContain('Lifecycle accepted Result identity: Unavailable');
    expect(guide.querySelectorAll('[data-testid="guided-result"]')).toHaveLength(1);
    expect(guide.textContent).toContain('byte count: 0');
    await choose('conflict');
    expect(guide.querySelectorAll('[data-testid="guided-result"]')).toHaveLength(2);
    expect(guide.textContent).toContain('SYNTHETIC-other-grant');
    expect(guide.textContent).toContain('effect_ambiguous');
    await choose('entry-only');
    expect(guide.querySelectorAll('[data-testid="guided-result"]')).toHaveLength(0);
    expect(guide.textContent).toContain('No Result summary is displayed');
    await choose('stale');
    expect(guide.textContent).toContain('Historical summaries');
    expect(guide.textContent).toContain('2026-10-17T10:00:01.000000Z');
    await choose('invalid');
    expect(guide.querySelectorAll('[data-testid="guided-result"]')).toHaveLength(0);
  });

  it('retains distinct bounded Journal coverage claims while switching scenarios in place', async () => {
    const { fixture, element, choose } = await open();
    const guide = element.querySelector<HTMLElement>('cc-guided-journey')!;
    guide.querySelectorAll<HTMLButtonElement>('nav button')[4].click();
    await fixture.whenStable();
    await choose('partial-empty');
    expect(guide.textContent).toContain('subject uniqueness remain unproven');
    await choose('complete-empty');
    expect(guide.textContent).toContain('this Journal at this high water');
    expect(guide.textContent).toContain('does not establish absence of invocation');
    expect(guide.querySelector('h3')?.textContent).toBe('Journal');
  });
});
