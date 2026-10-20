import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { describe, expect, it, vi } from 'vitest';
import { TimelineEntry } from '../data/models';
import { ExecutionTimeline } from './execution-timeline';

@Component({
  imports: [ExecutionTimeline],
  template: `
    <cc-execution-timeline
      [entries]="entries()"
      [(selectedId)]="selectedId"
      (entrySelect)="onEntrySelect($event)"
    />
  `,
})
class TestHost {
  readonly entries = signal<readonly TimelineEntry[]>([]);
  readonly selectedId = signal<string | null>(null);
  onEntrySelect: (entry: TimelineEntry | null) => void = () => undefined;
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
    expect(banner?.textContent).toContain('Mock display order only');
    expect(banner?.textContent).toContain('does not establish canonical Journal ordering');
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

    const secondEntry = el.querySelectorAll<HTMLButtonElement>('.entry-trigger')[1];
    secondEntry.focus();
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
    closeBtn?.focus();
    const focus = vi.spyOn(secondEntry, 'focus');
    closeBtn?.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.selectedId()).toBeNull();
    expect(el.querySelector('.timeline-detail-pane')).toBeNull();
    expect(document.activeElement).toBe(secondEntry);
    expect(focus).toHaveBeenCalledWith({ preventScroll: true });
  });

  it('exposes native toggle buttons within ordered list items', async () => {
    const { fixture, host, el } = await createHost(SAMPLE_ENTRIES);

    const firstEntry = el.querySelector<HTMLButtonElement>('ol.timeline li.entry > button')!;
    expect(firstEntry.type).toBe('button');
    expect(firstEntry.getAttribute('aria-pressed')).toBe('false');
    expect(el.querySelector('li[role="button"], [aria-selected]')).toBeNull();
    firstEntry.focus();
    firstEntry.click();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(host.selectedId()).toBe('tl-1');
    expect(document.activeElement).toBe(firstEntry);
    expect(firstEntry.getAttribute('aria-pressed')).toBe('true');
    expect(el.querySelector('.timeline-detail-pane')?.textContent).toContain(
      'Stage "implement" entered',
    );
    firstEntry.click();
    await fixture.whenStable();
    expect(host.selectedId()).toBeNull();
    expect(firstEntry.getAttribute('aria-pressed')).toBe('false');
    expect(document.activeElement).toBe(firstEntry);
  });

  it('returns to a visible event when filters hide the original trigger', async () => {
    const { fixture, el } = await createHost(SAMPLE_ENTRIES);
    el.querySelector<HTMLButtonElement>('.entry-trigger[data-entry-id="tl-1"]')!.click();
    await fixture.whenStable();
    el.querySelector<HTMLButtonElement>('.filter-attention')!.click();
    await fixture.whenStable();
    expect(el.querySelector('.entry-trigger[data-entry-id="tl-1"]')).toBeNull();
    const close = el.querySelector<HTMLButtonElement>('.close-btn')!;
    close.focus();
    close.click();
    await fixture.whenStable();
    expect(document.activeElement).toBe(el.querySelector('.entry-trigger[data-entry-id="tl-3"]'));
    expect(el.querySelector('.timeline-detail-pane')).toBeNull();
  });

  it('returns to the All filter when closing leaves no matching event', async () => {
    const { fixture, host, el } = await createHost(SAMPLE_ENTRIES);
    el.querySelector<HTMLButtonElement>('.entry-trigger[data-entry-id="tl-3"]')!.click();
    await fixture.whenStable();
    el.querySelector<HTMLButtonElement>('.filter-attention')!.click();
    await fixture.whenStable();
    host.onEntrySelect = (entry) => {
      if (entry === null) host.entries.set([SAMPLE_ENTRIES[0]]);
    };
    const close = el.querySelector<HTMLButtonElement>('.close-btn')!;
    close.focus();
    close.click();
    await fixture.whenStable();
    expect(el.querySelector('.entry-trigger')).toBeNull();
    expect(el.textContent).toContain('No matching timeline entries');
    expect(document.activeElement).toBe(el.querySelector('.filter-btn'));
    expect(document.activeElement?.textContent).toContain('All (1)');
  });

  it('returns to its named region if the parent removes entries while closing', async () => {
    const { fixture, host, el } = await createHost(SAMPLE_ENTRIES);
    el.querySelector<HTMLButtonElement>('.entry-trigger')!.click();
    await fixture.whenStable();
    host.onEntrySelect = (entry) => {
      if (entry === null) host.entries.set([]);
    };
    const close = el.querySelector<HTMLButtonElement>('.close-btn')!;
    close.focus();
    close.click();
    await fixture.whenStable();
    const region = el.querySelector<HTMLElement>('.timeline-wrapper')!;
    expect(region.getAttribute('aria-label')).toBe('Execution timeline');
    expect(region.tabIndex).toBe(-1);
    expect(document.activeElement).toBe(region);
    expect(el.querySelector('.timeline-detail-pane')).toBeNull();
  });

  it('renders empty state when entries are empty', async () => {
    const { el } = await createHost([]);

    expect(el.querySelectorAll('ol.timeline li.entry')).toHaveLength(0);
    expect(el.textContent).toContain('No timeline entries to show');
  });
});
