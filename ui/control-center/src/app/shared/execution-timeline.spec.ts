import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { TimelineEntry } from '../data/models';
import { ExecutionTimeline } from './execution-timeline';

@Component({
  imports: [ExecutionTimeline],
  template: `
    <cc-execution-timeline
      [entries]="entries()"
      [(selectedId)]="selectedId"
    />
  `,
})
class TestHost {
  readonly entries = signal<readonly TimelineEntry[]>([]);
  readonly selectedId = signal<string | null>(null);
}

describe('ExecutionTimeline', () => {
  async function createHost(initialEntries: readonly TimelineEntry[] = []) {
    await TestBed.configureTestingModule({ imports: [TestHost] }).compileComponents();
    const fixture = TestBed.createComponent(TestHost);
    fixture.componentInstance.entries.set(initialEntries);
    fixture.detectChanges();
    await fixture.whenStable();
    return {
      fixture,
      host: fixture.componentInstance,
      el: fixture.nativeElement as HTMLElement,
    };
  }

  const SAMPLE_ENTRIES: readonly TimelineEntry[] = [
    {
      id: 'tl-1',
      atLabel: 'Today · 14:00',
      kind: 'stage',
      title: 'Stage "implement" entered',
      detail: 'software-engineer assigned to agent-forge',
      state: 'finished',
      stateLabel: 'Finished',
      stateTone: 'success',
      stageId: 'implement',
      actorId: 'agent-forge',
      hasResult: false,
      result: null,
      evidenceCount: 0,
      hasEvidence: false,
      hasUnavailableEvidence: false,
      evidence: [],
    },
    {
      id: 'tl-2',
      atLabel: 'Today · 14:02',
      kind: 'tool',
      title: 'agent-forge executed repository_file_read',
      detail: 'Read direct POSIX file target',
      state: 'finished',
      stateLabel: 'Finished',
      stateTone: 'success',
      actorId: 'agent-forge',
      toolId: 'tool::itru-native-repository-file-read::v1',
      executionEntryRef: 'clm_1b2c3d4e',
      runIdRef: 'run_3c81f0a7',
      hasResult: true,
      result: {
        outcome: 'succeeded',
        outcomeLabel: 'Succeeded',
        outcomeTone: 'success',
        semanticEffect: {
          headline: 'Operation completed successfully',
          description: 'Safe immutable payload captured.',
        },
        identity: {
          derivedIdentityFormatted: '(ledg_1, auth_dom, human, maya, grnt_01)',
          ledgerInstanceId: 'ledg_1',
          domainId: 'auth_dom',
          issuer: 'human:maya',
          grantId: 'grnt_01',
          claimId: 'clm_1b2c3d4e',
          executorInstanceId: 'exec_node_01',
          leaseGeneration: 1,
          entryTimeLabel: 'Today · 14:02',
          timeKey: 1728984120,
          toolIdentity: 'tool::itru-native-repository-file-read::v1',
          configuredRoute: 'native::posix_read_direct',
        },
        payload: {
          byteCount: 120,
          formattedByteCount: '120 bytes',
          isText: true,
          textPreview: 'const hello = true;',
          isTruncated: false,
        },
        diagnostic: null,
      },
      evidenceCount: 1,
      hasEvidence: true,
      hasUnavailableEvidence: false,
      evidence: [
        {
          id: 'ev-tool-1',
          category: 'diagnostic',
          categoryLabel: 'Diagnostic Failure',
          kind: 'diagnostic',
          title: 'pre_flight_check',
          summary: 'Path verification passed',
          outcome: 'passed',
          outcomeLabel: 'Passed',
          outcomeTone: 'success',
          source: 'containment_guard',
          isTruncated: false,
          isBinary: false,
          isUnavailable: false,
        },
      ],
    },
    {
      id: 'tl-3',
      atLabel: 'Today · 14:05',
      kind: 'quality-gate',
      title: 'Validation failed',
      detail: 'unit-tests reported 1 failure',
      state: 'needs-attention',
      stateLabel: 'Needs attention',
      stateTone: 'warning',
      actorId: 'agent-sentinel',
      hasResult: false,
      result: null,
      evidenceCount: 1,
      hasEvidence: true,
      hasUnavailableEvidence: true,
      evidence: [
        {
          id: 'ev-gate-1',
          category: 'audit-trail',
          categoryLabel: 'Audit Trail',
          kind: 'audit-trail',
          title: 'audit_trace',
          summary: 'Worker trace',
          outcome: 'unverified',
          outcomeLabel: 'Unverified',
          outcomeTone: 'muted',
          source: 'audit_daemon',
          isTruncated: false,
          isBinary: false,
          isUnavailable: true,
          unavailableReason: 'Trace log expired.',
        },
      ],
    },
  ];

  it('renders honest disclaimer banner about data source order', async () => {
    const { el } = await createHost(SAMPLE_ENTRIES);

    const banner = el.querySelector('.timeline-disclaimer');
    expect(banner?.textContent).toContain('Display order supplied by current data source');
    expect(banner?.textContent).toContain('Core defines no canonical Journal ordering yet');
  });

  it('renders all entries when filter is all', async () => {
    const { el } = await createHost(SAMPLE_ENTRIES);

    const items = el.querySelectorAll('ol.timeline li.entry');
    expect(items).toHaveLength(3);
    expect(el.textContent).toContain('Stage "implement" entered');
    expect(el.textContent).toContain('agent-forge executed repository_file_read');
    expect(el.textContent).toContain('Validation failed');
  });

  it('filters entries with Result when With Result filter clicked', async () => {
    const { fixture, el } = await createHost(SAMPLE_ENTRIES);

    const resultFilterBtn = el.querySelector<HTMLButtonElement>('.filter-btn:nth-child(2)');
    expect(resultFilterBtn?.textContent).toContain('With Result (1)');
    resultFilterBtn?.click();
    fixture.detectChanges();
    await fixture.whenStable();

    const items = el.querySelectorAll('ol.timeline li.entry');
    expect(items).toHaveLength(1);
    expect(el.textContent).toContain('agent-forge executed repository_file_read');
  });

  it('filters entries needing attention when Attention filter clicked', async () => {
    const { fixture, el } = await createHost(SAMPLE_ENTRIES);

    const attentionBtn = el.querySelector<HTMLButtonElement>('.filter-attention');
    expect(attentionBtn?.textContent).toContain('Attention (1)');
    attentionBtn?.click();
    fixture.detectChanges();
    await fixture.whenStable();

    const items = el.querySelectorAll('ol.timeline li.entry');
    expect(items).toHaveLength(1);
    expect(el.textContent).toContain('Validation failed');
  });

  it('opens detail inspector when entry is clicked', async () => {
    const { fixture, host, el } = await createHost(SAMPLE_ENTRIES);

    expect(el.querySelector('.timeline-detail-pane')).toBeNull();

    const secondEntry = el.querySelectorAll<HTMLElement>('ol.timeline li.entry')[1];
    secondEntry.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.selectedId()).toBe('tl-2');
    const pane = el.querySelector('.timeline-detail-pane');
    expect(pane).not.toBeNull();
    expect(pane?.textContent).toContain('agent-forge executed repository_file_read');
    expect(pane?.textContent).toContain('clm_1b2c3d4e');
    expect(pane?.textContent).toContain('tool::itru-native-repository-file-read::v1');
    expect(pane?.textContent).toContain('Linked Result');
    expect(pane?.textContent).toContain('Operation completed successfully');
    expect(pane?.textContent).toContain('Associated Evidence (1)');

    // Click close button to deselect
    const closeBtn = pane?.querySelector<HTMLButtonElement>('.close-btn');
    closeBtn?.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.selectedId()).toBeNull();
    expect(el.querySelector('.timeline-detail-pane')).toBeNull();
  });

  it('supports keyboard selection with Enter key', async () => {
    const { fixture, host, el } = await createHost(SAMPLE_ENTRIES);

    const firstEntry = el.querySelectorAll<HTMLElement>('ol.timeline li.entry')[0];
    firstEntry.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.selectedId()).toBe('tl-1');
    expect(el.querySelector('.timeline-detail-pane')?.textContent).toContain('Stage "implement" entered');
  });

  it('renders empty state when entries are empty', async () => {
    const { el } = await createHost([]);

    expect(el.querySelectorAll('ol.timeline li.entry')).toHaveLength(0);
    expect(el.textContent).toContain('No timeline entries to show');
  });
});
