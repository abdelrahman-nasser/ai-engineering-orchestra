import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it } from 'vitest';
import { Flow } from './flow';
import { testProviders } from '../../../testing/providers';

describe('Flow feature page', () => {
  let fixture: ComponentFixture<Flow>;
  let component: Flow;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Flow],
      providers: [...testProviders(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Flow);
    component = fixture.componentInstance;
    fixture.detectChanges();
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
    fixture.detectChanges();

    const banner = el.querySelector('[data-testid="stale-banner"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Stale Presentation Snapshot');
  });

  it('loads empty graph scenario and renders empty state panel', async () => {
    const el = fixture.nativeElement as HTMLElement;
    const select = el.querySelector<HTMLSelectElement>('#scenario-dropdown')!;
    select.value = 'empty-graph';
    select.dispatchEvent(new Event('change'));
    fixture.detectChanges();

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
    expect(el.querySelector('cc-state-panel[kind="empty"]')?.textContent).toContain('No nodes match your filter criteria');
    expect(el.textContent).not.toContain('No nodes in this mock scenario');
  });

  it('opens detail inspector when a node is selected', () => {
    const el = fixture.nativeElement as HTMLElement;
    const firstNode = el.querySelector<SVGGElement>('svg g.node')!;
    firstNode.dispatchEvent(new MouseEvent('click'));
    fixture.detectChanges();

    const inspector = el.querySelector('cc-dag-node-inspector');
    expect(inspector).not.toBeNull();
    expect(inspector?.querySelector('.inspector-card')).not.toBeNull();
  });
});
