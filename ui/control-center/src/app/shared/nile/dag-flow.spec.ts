import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { DagFlow } from './dag-flow';
import { DagGraphPresentation, DagNodePresentation } from '../../data/models';
import { SCHEDULER_DISCLAIMER_NOTICE } from '../../data/dag-adapter';

describe('DagFlow', () => {
  let fixture: ComponentFixture<DagFlow>;
  let component: DagFlow;

  const mockNode1: DagNodePresentation = {
    id: 'n1',
    label: 'Stage Alpha',
    kind: 'stage',
    column: 0,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'completed-looking',
    schedulerStateLabel: 'Completed (looking)',
    schedulerTone: 'success',
    upstreamNodeIds: [],
    downstreamNodeIds: ['n2'],
    blockedByNodeIds: [],
    hasResult: true,
    isEffectAmbiguous: false,
    hasJournal: false,
    hasEvidence: false,
    evidenceCount: 0,
    hasContinuation: false,
    presentationState: 'finished',
  };

  const mockNode2: DagNodePresentation = {
    id: 'n2',
    label: 'Stage Beta',
    kind: 'run',
    column: 1,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'attention',
    schedulerStateLabel: 'Needs Attention',
    schedulerTone: 'danger',
    resultOutcome: 'effect_ambiguous',
    isEffectAmbiguous: true,
    upstreamNodeIds: ['n1'],
    downstreamNodeIds: ['n3'],
    blockedByNodeIds: [],
    hasResult: true,
    hasJournal: true,
    hasEvidence: true,
    evidenceCount: 2,
    hasContinuation: false,
    presentationState: 'needs-attention',
  };

  const mockNode3: DagNodePresentation = {
    id: 'n3',
    label: 'Stage Gamma',
    kind: 'outcome',
    column: 2,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'queued',
    schedulerStateLabel: 'Queued',
    schedulerTone: 'muted',
    upstreamNodeIds: ['n2'],
    downstreamNodeIds: [],
    blockedByNodeIds: [],
    hasResult: false,
    isEffectAmbiguous: false,
    hasJournal: false,
    hasEvidence: false,
    evidenceCount: 0,
    hasContinuation: false,
    presentationState: 'not-started',
  };

  const mockGraph: DagGraphPresentation = {
    id: 'test-graph',
    name: 'Test Flow Graph',
    scenario: 'test',
    description: 'A test flow',
    updatedLabel: 'Just now',
    isStale: false,
    nodes: [mockNode1, mockNode2, mockNode3],
    edges: [
      { id: 'e1', from: 'n1', to: 'n2', isTributary: false, weight: 'main', state: 'finished' },
      { id: 'e2', from: 'n2', to: 'n3', isTributary: false, weight: 'main', state: 'needs-attention' },
    ],
    schedulerSummary: {
      queuedCount: 1,
      readyLookingCount: 0,
      activeLookingCount: 0,
      blockedLookingCount: 0,
      completedLookingCount: 1,
      attentionCount: 1,
      dataSourceNotice: SCHEDULER_DISCLAIMER_NOTICE,
    },
    nodeMap: new Map([
      ['n1', mockNode1],
      ['n2', mockNode2],
      ['n3', mockNode3],
    ]),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DagFlow],
    }).compileComponents();

    fixture = TestBed.createComponent(DagFlow);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('graph', mockGraph);
    fixture.detectChanges();
  });

  it('renders svg canvas with nodes and curved channel edges', () => {
    const el: HTMLElement = fixture.nativeElement;
    const svg = el.querySelector('svg.river-svg');
    expect(svg).not.toBeNull();

    const nodes = el.querySelectorAll('svg g.node');
    expect(nodes.length).toBe(3);

    const edges = el.querySelectorAll('svg g.edge');
    expect(edges.length).toBe(2);
  });

  it('renders effect_ambiguous node with hazard class and badge', () => {
    const el: HTMLElement = fixture.nativeElement;
    const ambiguousNode = el.querySelector('svg g.node.effect-ambiguous');
    expect(ambiguousNode).not.toBeNull();
    expect(ambiguousNode?.querySelector('.hazard-ring')).not.toBeNull();
    expect(ambiguousNode?.querySelector('.badge-hazard')).not.toBeNull();
  });

  it('emits nodeSelect when a node is clicked', () => {
    let picked: DagNodePresentation | null = null;
    component.nodeSelect.subscribe((val) => (picked = val));

    const el: HTMLElement = fixture.nativeElement;
    const firstNode = el.querySelector<SVGGElement>('svg g.node');
    firstNode?.dispatchEvent(new MouseEvent('click'));

    expect(picked).not.toBeNull();
    expect((picked as unknown as DagNodePresentation).id).toBe('n1');
  });

  it('illuminates upstream and downstream dependency paths when a node is selected', () => {
    fixture.componentRef.setInput('selectedNodeId', 'n2');
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const upstreamNode = el.querySelector('svg g.node.upstream-highlight');
    expect(upstreamNode).not.toBeNull();

    const downstreamNode = el.querySelector('svg g.node.downstream-highlight');
    expect(downstreamNode).not.toBeNull();

    const upstreamEdge = el.querySelector('svg g.edge.upstream-path');
    expect(upstreamEdge).not.toBeNull();

    const downstreamEdge = el.querySelector('svg g.edge.downstream-path');
    expect(downstreamEdge).not.toBeNull();
  });

  it('adjusts zoom level when zoom controls are invoked', () => {
    const el: HTMLElement = fixture.nativeElement;
    const zoomInBtn = Array.from(el.querySelectorAll<HTMLButtonElement>('.floating-controls button')).find((b) =>
      b.getAttribute('aria-label') === 'Zoom in',
    );
    zoomInBtn?.click();
    fixture.detectChanges();

    const zoomLabel = el.querySelector('.floating-controls .zoom-level');
    expect(zoomLabel?.textContent).toBe('115%');
  });

  it('fits the whole graph in a narrow canvas below the former 50% limit', () => {
    const el = fixture.nativeElement as HTMLElement;
    const viewport = el.querySelector<HTMLElement>('.viewport')!;
    expect(viewport.querySelector('[aria-label="Canvas zoom and pan controls"]')).toBeNull();
    Object.defineProperty(viewport, 'clientWidth', { value: 320 });
    Object.defineProperty(viewport, 'clientHeight', { value: 480 });
    el.querySelector<HTMLButtonElement>('[aria-label="Fit graph"]')!.click();
    fixture.detectChanges();
    const svg = el.querySelector<SVGElement>('.river-svg')!;
    expect(parseFloat(svg.style.width)).toBeLessThanOrEqual(320);
    expect(parseFloat(svg.style.height)).toBeLessThanOrEqual(480);
    expect(parseInt(el.querySelector('.zoom-level')!.textContent!)).toBeLessThan(50);
  });

  it('switches to list view table representation', () => {
    fixture.componentRef.setInput('viewMode', 'list');
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    const table = el.querySelector('table.list-table');
    expect(table).not.toBeNull();

    const rows = el.querySelectorAll('table.list-table tbody tr');
    expect(rows.length).toBe(3);
  });

  it('navigates from the focused river node and moves focus with selection', () => {
    fixture.componentRef.setInput('selectedNodeId', 'n3');
    fixture.detectChanges();
    let picked: string | undefined;
    component.nodeSelect.subscribe((node) => { picked = node.id; });
    const nodes = fixture.nativeElement.querySelectorAll('g.node') as NodeListOf<SVGElement>;
    nodes[0].focus();
    const event = new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true });
    nodes[0].dispatchEvent(event);
    expect(picked).toBe('n2');
    expect(document.activeElement).toBe(nodes[1]);
    expect(event.defaultPrevented).toBe(true);
  });

  it('leaves toolbar and list arrow keys alone and exposes selection on native list buttons', () => {
    fixture.componentRef.setInput('selectedNodeId', 'n1');
    fixture.detectChanges();
    let selections = 0;
    component.nodeSelect.subscribe(() => selections++);
    const el = fixture.nativeElement as HTMLElement;
    const zoom = el.querySelector('[aria-label="Zoom in"]')!;
    const toolbarKey = new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true, cancelable: true });
    zoom.dispatchEvent(toolbarKey);
    expect(selections).toBe(0);
    expect(toolbarKey.defaultPrevented).toBe(false);
    fixture.componentRef.setInput('viewMode', 'list');
    fixture.detectChanges();
    const button = el.querySelector<HTMLButtonElement>('.node-btn-cell')!;
    expect(button.getAttribute('aria-pressed')).toBe('true');
    expect(el.querySelector('tr[aria-selected]')).toBeNull();
    expect(el.querySelector<HTMLElement>('.list-view-container')!.tabIndex).toBe(0);
    button.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowRight', bubbles: true }));
    expect(selections).toBe(0);
    button.click();
    expect(selections).toBe(1);
  });
});
