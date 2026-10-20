import { Location } from '@angular/common';
import { provideLocationMocks } from '@angular/common/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { vi } from 'vitest';
import { of } from 'rxjs';
import { App } from '../app';
import { ControlCenterDataSource } from '../data/control-center-data-source';
import { buildRunDetail } from '../data/mock/mock-data';
import { testProviders } from '../../testing/providers';

describe('Inspection route ownership', () => {
  let fixture: ComponentFixture<App>;
  let router: Router;
  let el: HTMLElement;
  async function settle() {
    await fixture.whenStable();
    await fixture.whenStable();
  }
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [...testProviders(), provideLocationMocks()],
    }).compileComponents();
    fixture = TestBed.createComponent(App);
    el = fixture.nativeElement;
    router = TestBed.inject(Router);
    router.initialNavigation();
    await settle();
  });
  it('restores Task filters through detail, Back and Forward and removes absent/invalid filter state', async () => {
    await router.navigateByUrl('/tasks');
    await settle();
    el.querySelector<HTMLButtonElement>('[data-testid="task-filter-blocked"]')!.click();
    await settle();
    expect(router.url).toBe('/tasks?taskFilter=blocked');
    el.querySelector<HTMLAnchorElement>('table[aria-label="Tasks"] .row-link')!.click();
    await settle();
    expect(router.url).toBe('/tasks/DEMO-103');
    TestBed.inject(Location).back();
    await vi.waitFor(async () => {
      await settle();
      expect(router.url).toBe('/tasks?taskFilter=blocked');
    });
    expect(router.url).toBe('/tasks?taskFilter=blocked');
    expect(
      el.querySelector('[data-testid="task-filter-blocked"]')?.getAttribute('aria-pressed'),
    ).toBe('true');
    expect(el.querySelectorAll('table[aria-label="Tasks"] tbody tr')).toHaveLength(1);
    TestBed.inject(Location).forward();
    await vi.waitFor(async () => {
      await settle();
      expect(router.url).toBe('/tasks/DEMO-103');
    });
    expect(router.url).toBe('/tasks/DEMO-103');
    for (const url of ['/tasks?taskFilter=unknown', '/tasks']) {
      await router.navigateByUrl(url);
      await settle();
      expect(
        el.querySelector('[data-testid="task-filter-all"]')?.getAttribute('aria-pressed'),
      ).toBe('true');
      expect(el.querySelectorAll('table[aria-label="Tasks"] tbody tr')).toHaveLength(10);
    }
  });
  it('reconciles selected Run through dependency links and Back/Forward with the same detail component', async () => {
    await router.navigateByUrl('/tasks/DEMO-102');
    await settle();
    el.querySelector<HTMLButtonElement>('[data-testid="run-tree-item-run_a41c07e2"]')!.click();
    await settle();
    el.querySelector<HTMLAnchorElement>('a[href="/tasks/DEMO-101"]')!.click();
    await settle();
    expect(el.querySelector('[data-testid="run-inspection-card"]')?.textContent).toContain(
      'run_3c81f0a7',
    );
    TestBed.inject(Location).back();
    await vi.waitFor(async () => {
      await settle();
      expect(router.url).toBe('/tasks/DEMO-102');
    });
    expect(router.url).toBe('/tasks/DEMO-102');
    expect(el.querySelector('[data-testid="run-inspection-card"]')?.textContent).not.toContain(
      'run_3c81f0a7',
    );
    TestBed.inject(Location).forward();
    await vi.waitFor(async () => {
      await settle();
      expect(router.url).toBe('/tasks/DEMO-101');
    });
    expect(el.querySelector('[data-testid="run-inspection-card"]')?.textContent).not.toContain(
      'run_a41c07e2',
    );
    expect(el.querySelector('[data-testid="run-inspection-card"]')?.textContent).toContain(
      'Task DEMO-101',
    );
  });
  it('keeps empty event evidence distinct from Run-wide records and resets event selection on Run navigation', async () => {
    await router.navigateByUrl('/runs/run_3c81f0a7');
    await settle();
    const event = Array.from(el.querySelectorAll<HTMLButtonElement>('button.entry-trigger')).find(
      (x) => x.textContent?.includes('Stage "implement" entered'),
    )!;
    event.click();
    await settle();
    const evidenceCard = Array.from(el.querySelectorAll('.card')).find(
      (x) => x.querySelector('h2')?.textContent === 'Evidence Explorer',
    )!;
    expect(evidenceCard.textContent).toContain('Event-scoped evidence');
    expect(evidenceCard.textContent).toContain('No evidence supplied for this event');
    expect(evidenceCard.querySelector('cc-evidence-panel')).toBeNull();
    const runWide = evidenceCard.querySelector<HTMLButtonElement>('button')!;
    runWide.focus();
    runWide.click();
    await settle();
    expect(document.activeElement).toBe(runWide);
    expect(runWide.getAttribute('aria-pressed')).toBe('true');
    expect(evidenceCard.textContent).toContain('Run-wide evidence');
    expect(evidenceCard.querySelectorAll('details')).toHaveLength(3);
    event.click();
    await settle();
    await router.navigateByUrl('/runs/run_a41c07e2');
    await settle();
    expect(el.querySelector('.timeline-detail-pane')).toBeNull();
    expect(el.textContent).toContain('Run-wide evidence · run_a41c07e2');
    expect(el.textContent).not.toContain('Event-scoped evidence');
  });

  it('classifies a defined mismatching Run response as a failed read, never not-found or unrelated evidence', async () => {
    vi.spyOn(TestBed.inject(ControlCenterDataSource), 'getRun').mockReturnValue(
      of(buildRunDetail('run_a41c07e2')),
    );
    await router.navigateByUrl('/runs/run_3c81f0a7');
    await settle();
    expect(el.textContent).toContain('Could not load this Run');
    expect(el.textContent).not.toContain('Run not found');
    expect(
      el.querySelector('cc-result-shell, cc-execution-timeline, cc-evidence-panel'),
    ).toBeNull();
  });
});
