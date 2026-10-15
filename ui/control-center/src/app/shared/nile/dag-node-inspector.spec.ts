import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { describe, expect, it } from 'vitest';
import { DagNodeInspector } from './dag-node-inspector';
import { DagGraphPresentation, DagNodePresentation } from '../../data/models';
import { EFFECT_AMBIGUOUS_DAG_WARNING } from '../../data/dag-adapter';
import { adaptResultReadModel } from '../../data/result-adapter';
import { MOCK_RESULT_READ_MODELS } from '../../data/mock/mock-data';


describe('DagNodeInspector', () => {
  let fixture: ComponentFixture<DagNodeInspector>;
  let component: DagNodeInspector;

  const mockParentNode: DagNodePresentation = {
    id: 'n-parent',
    label: 'Parent Node',
    kind: 'stage',
    column: 0,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'completed-looking',
    schedulerStateLabel: 'Completed (looking)',
    schedulerTone: 'success',
    upstreamNodeIds: [],
    downstreamNodeIds: ['n-child'],
    blockedByNodeIds: [],
    hasResult: false,
    isEffectAmbiguous: false,
    hasJournal: false,
    hasEvidence: false,
    evidenceCount: 0,
    hasContinuation: false,
    presentationState: 'finished',
  };

  const mockAmbiguousNode: DagNodePresentation = {
    id: 'n-child',
    label: 'Ambiguous Child Node',
    sublabel: 'Hazardous execution',
    kind: 'run',
    column: 1,
    lane: 0,
    taskId: 'DEMO-101',
    runId: 'run_ambig_01',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    stageId: 'implement',
    toolId: 'tool::native-write',
    isMainFlow: true,
    schedulerState: 'attention',
    schedulerStateLabel: 'Needs Attention',
    schedulerTone: 'danger',
    resultOutcome: 'effect_ambiguous',
    isEffectAmbiguous: true,
    upstreamNodeIds: ['n-parent'],
    downstreamNodeIds: ['n-downstream'],
    blockedByNodeIds: ['n-blocker'],
    hasResult: true,
    linkedResult: adaptResultReadModel(MOCK_RESULT_READ_MODELS.get('run_a41c07e2')) ?? undefined,
    hasJournal: false,
    hasEvidence: false,
    evidenceCount: 0,
    hasContinuation: false,
    presentationState: 'needs-attention',
  };

  const mockGraph: DagGraphPresentation = {
    id: 'test-graph',
    name: 'Test',
    scenario: 'test',
    description: 'desc',
    updatedLabel: 'now',
    isStale: false,
    nodes: [mockParentNode, mockAmbiguousNode],
    edges: [],
    schedulerSummary: {
      queuedCount: 0,
      readyLookingCount: 0,
      activeLookingCount: 0,
      blockedLookingCount: 0,
      completedLookingCount: 1,
      attentionCount: 1,
      dataSourceNotice: 'notice',
    },
    nodeMap: new Map([
      ['n-parent', mockParentNode],
      ['n-child', mockAmbiguousNode],
    ]),
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DagNodeInspector],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(DagNodeInspector);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('graph', mockGraph);
  });

  it('renders placeholder when no node is selected', () => {
    fixture.componentRef.setInput('node', null);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('.empty-inspector')).not.toBeNull();
    expect(el.querySelector('.inspector-card')).toBeNull();
  });

  it('renders node details and prominent effect_ambiguous warning', () => {
    fixture.componentRef.setInput('node', mockAmbiguousNode);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('h3')?.textContent).toContain('Ambiguous Child Node');

    const warningBox = el.querySelector('[data-testid="effect-ambiguous-warning"]');
    expect(warningBox).not.toBeNull();
    expect(warningBox?.textContent).toContain('Automatic retry or replay is strictly prohibited');
  });

  it('renders dependency relationships and emits nodeSelect when clicking dependency chip', () => {
    fixture.componentRef.setInput('node', mockAmbiguousNode);
    fixture.detectChanges();

    let selected: DagNodePresentation | null = null;
    component.nodeSelect.subscribe((val) => (selected = val));

    const el: HTMLElement = fixture.nativeElement;
    const parentChip = Array.from(el.querySelectorAll<HTMLButtonElement>('.dep-btn-chip')).find((c) =>
      c.textContent?.includes('Parent Node'),
    );
    expect(parentChip).toBeDefined();

    parentChip?.click();
    expect(selected).not.toBeNull();
    expect((selected as unknown as DagNodePresentation).id).toBe('n-parent');
  });

  it('renders embedded ResultShell when linkedResult is present', () => {
    fixture.componentRef.setInput('node', mockAmbiguousNode);
    fixture.detectChanges();

    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('cc-result-shell')).not.toBeNull();
  });

  it('emits close when close button is clicked', () => {
    fixture.componentRef.setInput('node', mockAmbiguousNode);
    fixture.detectChanges();

    let closed = false;
    component.close.subscribe(() => (closed = true));

    const el: HTMLElement = fixture.nativeElement;
    const closeBtn = el.querySelector<HTMLButtonElement>('.close-btn');
    closeBtn?.click();

    expect(closed).toBe(true);
  });
});
