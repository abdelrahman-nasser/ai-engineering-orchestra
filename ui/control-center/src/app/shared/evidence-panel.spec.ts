import { ComponentFixture, TestBed } from '@angular/core/testing';
import { describe, expect, it } from 'vitest';
import { EvidenceItem } from '../data/models';
import { EvidencePanel } from './evidence-panel';

describe('EvidencePanel', () => {
  async function create(items: readonly EvidenceItem[]): Promise<{
    fixture: ComponentFixture<EvidencePanel>;
    el: HTMLElement;
  }> {
    await TestBed.configureTestingModule({
      imports: [EvidencePanel],
    }).compileComponents();

    const fixture = TestBed.createComponent(EvidencePanel);
    fixture.componentRef.setInput('items', items);
    fixture.detectChanges();
    return { fixture, el: fixture.nativeElement as HTMLElement };
  }

  it('renders tally and items when evidence records are provided', async () => {
    const items: EvidenceItem[] = [
      {
        id: 'ev-1',
        category: 'quality-gate',
        categoryLabel: 'Quality Gate',
        kind: 'quality-gate',
        title: 'unit-tests',
        summary: 'All unit tests passed',
        outcome: 'passed',
        outcomeLabel: 'Passed',
        outcomeTone: 'success',
        source: 'python unittest',
        isTruncated: false,
        isBinary: false,
        isUnavailable: false,
      },
      {
        id: 'ev-2',
        category: 'diagnostic',
        categoryLabel: 'Diagnostic Failure',
        kind: 'diagnostic',
        title: 'containment_check',
        summary: 'Path containment rejected',
        outcome: 'failed',
        outcomeLabel: 'Failed',
        outcomeTone: 'danger',
        source: 'containment_guard',
        isTruncated: false,
        isBinary: false,
        isUnavailable: false,
      },
    ];

    const { el } = await create(items);

    expect(el.querySelectorAll('details').length).toBe(2);
    expect(el.textContent).toContain('unit-tests');
    expect(el.textContent).toContain('containment_check');
    expect(el.textContent).toContain('1 passed');
    expect(el.textContent).toContain('1 failed');
  });

  it('renders unavailable evidence notice and badge', async () => {
    const items: EvidenceItem[] = [
      {
        id: 'ev-3',
        category: 'audit-trail',
        categoryLabel: 'Audit Trail',
        kind: 'audit-trail',
        title: 'audit_trace',
        summary: 'Audit trace capture',
        outcome: 'unverified',
        outcomeLabel: 'Unverified',
        outcomeTone: 'muted',
        source: 'audit_daemon',
        isTruncated: false,
        isBinary: false,
        isUnavailable: true,
        unavailableReason: 'Trace log expired past retention window.',
      },
    ];

    const { el } = await create(items);

    expect(el.textContent).toContain('Trace log expired past retention window.');
    expect(el.textContent).toContain('Unavailable');
    expect(el.textContent).toContain('1 unavailable');
  });

  it('renders bounded text preview with truncation banner', async () => {
    const items: EvidenceItem[] = [
      {
        id: 'ev-4',
        category: 'command-output',
        categoryLabel: 'Command Output',
        kind: 'command-output',
        title: 'build_log',
        summary: 'Full compiler log',
        outcome: 'passed',
        outcomeLabel: 'Passed',
        outcomeTone: 'success',
        source: 'make check',
        isTruncated: true,
        truncationNotice: 'Showing bounded preview of 10,000 bytes.',
        textPreview: 'Compiler output line 1\nCompiler output line 2',
        isBinary: false,
        isUnavailable: false,
      },
    ];

    const { el } = await create(items);

    expect(el.textContent).toContain('Showing bounded preview of 10,000 bytes.');
    expect(el.textContent).toContain('Compiler output line 1');
  });

  it('renders binary hex sample snippet', async () => {
    const items: EvidenceItem[] = [
      {
        id: 'ev-5',
        category: 'payload-sample',
        categoryLabel: 'Payload Sample',
        kind: 'payload-sample',
        title: 'binary_sample',
        summary: 'Raw ELF sample',
        outcome: 'passed',
        outcomeLabel: 'Passed',
        outcomeTone: 'success',
        source: 'posix_read',
        isTruncated: false,
        isBinary: true,
        binaryHexSample: '00000000  7f 45 4c 46 02 01 01 00',
        isUnavailable: false,
      },
    ];

    const { el } = await create(items);

    expect(el.textContent).toContain('Non-text representation (hex sample)');
    expect(el.textContent).toContain('7f 45 4c 46');
  });

  it('renders empty state when no items provided', async () => {
    const { el } = await create([]);

    expect(el.querySelectorAll('details').length).toBe(0);
    expect(el.textContent).toContain('No evidence has been presented');
  });
});
