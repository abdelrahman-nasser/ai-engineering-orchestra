import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Location } from '@angular/common';
import { provideLocationMocks } from '@angular/common/testing';
import { provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Subject, throwError } from 'rxjs';
import { describe, expect, it, vi } from 'vitest';
import { Flow } from './flow';
import { testProviders } from '../../../testing/providers';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { DagGraphReadModel } from '../../data/models';
import { getMockDagGraph } from '../../data/mock/mock-dag-data';

describe('Flow feature page', () => {
  let fixture: ComponentFixture<unknown>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Flow],
      providers: [
        ...testProviders(),
        provideRouter([{ path: 'flow', component: Flow }], withComponentInputBinding()),
        provideLocationMocks(),
      ],
    }).compileComponents();

    const harness = await RouterTestingHarness.create('/flow');
    fixture = harness.fixture;
    router = TestBed.inject(Router);
    await fixture.whenStable();
  });

  it('renders page header and scenario dropdown', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h1')?.textContent).toContain('Nile Flow & Scheduler');

    const select = el.querySelector<HTMLSelectElement>('#scenario-dropdown');
    expect(select).not.toBeNull();
    expect(select?.options.length).toBeGreaterThan(5);
  });

  it('renders scheduler panel and DAG flow visualizer on ready state', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('cc-scheduler-panel')).not.toBeNull();
    expect(el.querySelector('cc-dag-flow')).not.toBeNull();
    expect(el.querySelectorAll('svg g.node').length).toBeGreaterThan(5);
  });

  it('loads stale data scenario and surfaces stale snapshot warning banner', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const select = el.querySelector<HTMLSelectElement>('#scenario-dropdown')!;
    select.value = 'stale-data';
    select.dispatchEvent(new Event('change'));
    await fixture.whenStable();

    const banner = el.querySelector('[data-testid="stale-banner"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Stale Presentation Snapshot');
  });

  it('loads empty graph scenario and renders empty state panel', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const select = el.querySelector<HTMLSelectElement>('#scenario-dropdown')!;
    select.value = 'empty-graph';
    select.dispatchEvent(new Event('change'));
    await fixture.whenStable();

    const emptyPanel = el.querySelector('cc-state-panel[kind="empty"]');
    expect(emptyPanel).not.toBeNull();
    expect(emptyPanel?.textContent).toContain('No nodes in this mock scenario');
    expect(emptyPanel?.textContent).not.toContain('filter criteria');
  });

  it('filters nodes based on search query', () => {
    const el = fixture.nativeElement as HTMLElement;
    const searchInput = el.querySelector<HTMLInputElement>('.search-input')!;
    searchInput.value = 'API Service';
    searchInput.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const nodes = el.querySelectorAll('svg g.node');
    expect(nodes.length).toBe(1);
    expect(nodes[0].getAttribute('aria-label')).toContain('API Service Layer');
  });

  it('distinguishes an empty search from a supplied empty graph', () => {
    const el = fixture.nativeElement as HTMLElement;
    const search = el.querySelector<HTMLInputElement>('.search-input')!;
    search.value = 'SYNTHETIC-no-match';
    search.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    expect(el.querySelector('cc-state-panel[kind="empty"]')?.textContent).toContain(
      'No nodes match your filter criteria',
    );
    expect(el.textContent).not.toContain('No nodes in this mock scenario');
  });

  it('opens detail inspector when a node is selected', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const firstNode = el.querySelector<SVGGElement>('svg g.node')!;
    firstNode.dispatchEvent(new MouseEvent('click'));
    await fixture.whenStable();

    const inspector = el.querySelector('cc-dag-node-inspector');
    expect(inspector).not.toBeNull();
    expect(inspector?.querySelector('.inspector-card')).not.toBeNull();
  });

  it('uses direct query values and their absence as the selection source while retaining toolbar state', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const search = el.querySelector<HTMLInputElement>('.search-input')!;
    search.value = 'API';
    search.dispatchEvent(new Event('input'));
    await fixture.whenStable();

    await router.navigateByUrl('/flow?scenario=blocked-branch&node=fo-sub-api');
    await fixture.whenStable();
    expect(el.querySelector<HTMLSelectElement>('#scenario-dropdown')!.value).toBe('blocked-branch');
    expect(el.querySelector('.inspector-card')).toBeNull();
    expect(el.querySelector('.selection-notice')?.textContent).toContain('not supplied');
    expect(el.querySelector<HTMLInputElement>('.search-input')!.value).toBe('API');

    await router.navigateByUrl('/flow?node=fo-sub-api');
    await fixture.whenStable();
    expect(el.querySelector<HTMLSelectElement>('#scenario-dropdown')!.value).toBe('fan-out-fan-in');
    expect(el.querySelector('.inspector-card h3')?.textContent).toContain('API Service Layer');
    expect(el.querySelector<HTMLInputElement>('.search-input')!.value).toBe('API');

    await router.navigateByUrl('/flow');
    await fixture.whenStable();
    expect(el.querySelector('.inspector-card')).toBeNull();
    expect(el.querySelector('[aria-pressed="true"][data-node-id]')).toBeNull();
    expect(el.querySelector<HTMLInputElement>('.search-input')!.value).toBe('API');
  });

  it('reconciles node and scenario query removal and restoration through browser history', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const location = TestBed.inject(Location);
    router.setUpLocationChangeListener();
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    await router.navigateByUrl('/flow?scenario=blocked-branch');
    await fixture.whenStable();
    expect(el.querySelector('.inspector-card')).toBeNull();

    location.back();
    await vi.waitFor(async () => {
      await fixture.whenStable();
      expect(router.url).toBe('/flow?node=fo-plan');
      expect(el.querySelector<HTMLSelectElement>('#scenario-dropdown')!.value).toBe(
        'fan-out-fan-in',
      );
      expect(el.querySelector('.inspector-card h3')?.textContent).toContain('Architecture Plan');
    });
    location.forward();
    await vi.waitFor(async () => {
      await fixture.whenStable();
      expect(router.url).toBe('/flow?scenario=blocked-branch');
      expect(el.querySelector<HTMLSelectElement>('#scenario-dropdown')!.value).toBe(
        'blocked-branch',
      );
      expect(el.querySelector('.inspector-card')).toBeNull();
    });
  });

  it('shows honest missing states for invalid or empty scenario and node queries without a stale inspector', async () => {
    const el = fixture.nativeElement as HTMLElement;
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    expect(el.querySelector('.inspector-card')).not.toBeNull();
    for (const query of ['node=missing', 'node=']) {
      await router.navigateByUrl('/flow?' + query);
      await fixture.whenStable();
      expect(el.querySelector('.inspector-card')).toBeNull();
      expect(el.querySelector('.selection-notice')?.textContent).toContain('not supplied');
    }
    for (const query of ['scenario=missing&node=fo-plan', 'scenario=&node=fo-plan']) {
      await router.navigateByUrl('/flow?' + query);
      await fixture.whenStable();
      expect(el.querySelector('.inspector-card')).toBeNull();
      expect(el.querySelector('cc-state-panel[kind="not-found"]')?.textContent).toContain(
        'Mock scenario not found',
      );
      expect(el.querySelector('cc-dag-flow')).toBeNull();
    }
  });

  it('removes prior graph and inspector during delayed, failed and missing reads', async () => {
    const el = fixture.nativeElement as HTMLElement;
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    const pending = new Subject<DagGraphReadModel | undefined>();
    const getGraph = vi.spyOn(TestBed.inject(ControlCenterDataSource), 'getDagGraph');
    getGraph.mockReturnValueOnce(pending);
    await router.navigateByUrl('/flow?scenario=blocked-branch&node=fo-plan');
    await fixture.whenStable();
    expect(el.querySelector('cc-state-panel[kind="loading"]')).not.toBeNull();
    expect(el.querySelector('.inspector-card')).toBeNull();
    expect(el.querySelector('cc-dag-flow')).toBeNull();
    pending.next(getMockDagGraph('blocked-branch'));
    pending.complete();
    await fixture.whenStable();
    expect(el.querySelector('.selection-notice')).not.toBeNull();

    getGraph.mockReturnValueOnce(throwError(() => new Error('Synthetic read failure')));
    await router.navigateByUrl('/flow?scenario=attention-error&node=fo-plan');
    await fixture.whenStable();
    expect(el.querySelector('cc-state-panel[kind="error"]')).not.toBeNull();
    expect(el.querySelector('.inspector-card')).toBeNull();
    await router.navigateByUrl('/flow?scenario=missing&node=fo-plan');
    await fixture.whenStable();
    expect(el.querySelector('cc-state-panel[kind="not-found"]')).not.toBeNull();
    expect(el.querySelector('.inspector-card')).toBeNull();
  });

  it('explicit Close restores its surviving river or list trigger without scrolling, but query changes do not move focus', async () => {
    const el = fixture.nativeElement as HTMLElement;
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    const node = el.querySelector<SVGElement>('[data-node-id="fo-plan"]')!;
    const focus = vi.spyOn(node, 'focus');
    const close = el.querySelector<HTMLButtonElement>('[aria-label="Close inspector"]')!;
    close.focus();
    close.click();
    await fixture.whenStable();
    expect(router.url).toBe('/flow');
    expect(document.activeElement).toBe(node);
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });

    const list = Array.from(el.querySelectorAll<HTMLButtonElement>('.view-mode-group button'))[1];
    list.click();
    await fixture.whenStable();
    const listNode = el.querySelector<HTMLButtonElement>('.node-btn-cell[data-node-id="fo-plan"]')!;
    listNode.click();
    await fixture.whenStable();
    el.querySelector<HTMLButtonElement>('[aria-label="Close inspector"]')!.click();
    await fixture.whenStable();
    expect(document.activeElement).toBe(listNode);

    el.querySelector<HTMLInputElement>('.search-input')!.focus();
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    expect(document.activeElement).toBe(el.querySelector('.search-input'));
  });

  it('Close uses the scoped search fallback when a selected node is no longer in the filtered graph', async () => {
    const el = fixture.nativeElement as HTMLElement;
    await router.navigateByUrl('/flow?node=fo-plan');
    await fixture.whenStable();
    const search = el.querySelector<HTMLInputElement>('.search-input')!;
    search.value = 'API Service';
    search.dispatchEvent(new Event('input'));
    await fixture.whenStable();
    expect(el.querySelector('[data-node-id="fo-plan"]')).toBeNull();
    expect(el.querySelector('.inspector-card')).not.toBeNull();
    const focus = vi.spyOn(search, 'focus');
    el.querySelector<HTMLButtonElement>('[aria-label="Close inspector"]')!.click();
    await fixture.whenStable();
    expect(router.url).toBe('/flow');
    expect(document.activeElement).toBe(search);
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
    expect(search.value).toBe('API Service');
  });
});
