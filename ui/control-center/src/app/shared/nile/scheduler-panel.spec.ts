import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { SchedulerPanel } from './scheduler-panel';
import { SCHEDULER_DISCLAIMER_NOTICE } from '../../data/dag-adapter';
import { DagNodePresentation } from '../../data/models';

describe('SchedulerPanel', () => {
  let fixture: ComponentFixture<SchedulerPanel>;
  let component: SchedulerPanel;

  const mockSummary = {
    queuedCount: 2,
    readyLookingCount: 1,
    activeLookingCount: 3,
    blockedLookingCount: 1,
    completedLookingCount: 4,
    attentionCount: 1,
    dataSourceNotice: SCHEDULER_DISCLAIMER_NOTICE,
  };

  const mockNodes: DagNodePresentation[] = [
    {
      id: 'node-1',
      label: 'Worker Alpha',
      kind: 'subagent',
      column: 1,
      lane: 0,
      isMainFlow: true,
      schedulerState: 'active-looking',
      schedulerStateLabel: 'Active (looking)',
      schedulerTone: 'info',
      upstreamNodeIds: [],
      downstreamNodeIds: [],
      blockedByNodeIds: [],
      hasResult: false,
      isEffectAmbiguous: false,
      hasJournal: false,
      hasEvidence: false,
      evidenceCount: 0,
      hasContinuation: false,
      presentationState: 'in-progress',
    },
    {
      id: 'node-2',
      label: 'Worker Beta',
      kind: 'subagent',
      column: 1,
      lane: 1,
      isMainFlow: false,
      schedulerState: 'blocked-looking',
      schedulerStateLabel: 'Blocked (looking)',
      schedulerTone: 'warning',
      attentionReason: 'Missing checkpoint authorization',
      upstreamNodeIds: [],
      downstreamNodeIds: [],
      blockedByNodeIds: ['node-checkpoint'],
      hasResult: false,
      isEffectAmbiguous: false,
      hasJournal: false,
      hasEvidence: false,
      evidenceCount: 0,
      hasContinuation: false,
      presentationState: 'needs-attention',
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SchedulerPanel],
    }).compileComponents();

    fixture = TestBed.createComponent(SchedulerPanel);
    component = fixture.componentInstance;
    fixture.componentRef.setInput('summary', mockSummary);
    fixture.componentRef.setInput('nodes', mockNodes);
    fixture.detectChanges();
  });

  it('renders the mandatory ITRU-063 disclaimer banner', () => {
    const el: HTMLElement = fixture.nativeElement;
    const banner = el.querySelector('[data-testid="scheduler-disclaimer"]');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Scheduler state supplied by current data source');
    expect(banner?.textContent).toContain('Core scheduler semantics pending ITRU-063');
  });

  it('renders scheduler state filter pills with correct counts', () => {
    const el: HTMLElement = fixture.nativeElement;
    const pills = el.querySelectorAll('.stat-pill');
    expect(pills.length).toBe(7); // all, active, ready, blocked, attention, completed, queued

    const activePill = Array.from(pills).find((p) => p.textContent?.includes('Active (looking)'));
    expect(activePill?.textContent).toContain('3');
  });

  it('emits filterChange when a filter pill is clicked', () => {
    let emittedFilter = '';
    component.filterChange.subscribe((val) => (emittedFilter = val));

    const el: HTMLElement = fixture.nativeElement;
    const blockedPill = Array.from(el.querySelectorAll<HTMLButtonElement>('.stat-pill')).find((p) =>
      p.textContent?.includes('Blocked (looking)'),
    );
    blockedPill?.click();
    expect(emittedFilter).toBe('blocked-looking');
  });

  it('displays the immediate operator focus strip and emits nodeSelect', () => {
    let selectedNode: DagNodePresentation | null = null;
    component.nodeSelect.subscribe((val) => (selectedNode = val));

    const el: HTMLElement = fixture.nativeElement;
    const chips = el.querySelectorAll<HTMLButtonElement>('.queue-chip');
    expect(chips.length).toBe(2);

    chips[0].click();
    expect(selectedNode).not.toBeNull();
    expect((selectedNode as unknown as DagNodePresentation).id).toBe('node-1');
  });
});
