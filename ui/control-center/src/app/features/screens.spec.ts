import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { App } from '../app';
import { testProviders } from '../../testing/providers';

/** Mock rendering checks for every screen, driven through the real router. */
describe('Screens (mock rendering)', () => {
  let settle: () => Promise<void> = async () => undefined;

  async function open(url: string): Promise<HTMLElement> {
    await TestBed.configureTestingModule({ imports: [App], providers: testProviders() }).compileComponents();
    const fixture = TestBed.createComponent(App);
    settle = async () => {
      await fixture.whenStable();
    };
    await TestBed.inject(Router).navigateByUrl(url);
    await settle();
    await settle();
    return fixture.nativeElement as HTMLElement;
  }

  const text = (el: Element | null) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

  it('Overview shows figures, the workspace river and attention items', async () => {
    const el = await open('/');
    expect(el.querySelectorAll('cc-stat-tile')).toHaveLength(4);
    expect(el.querySelectorAll('cc-nile-flow g.node').length).toBeGreaterThan(5);
    expect(text(el.querySelector('.attention'))).toContain('run_f27a9c58');
    expect(el.querySelector('cc-nile-flow .footnote')).not.toBeNull();
  });

  it('Overview river opens a run when a run island is activated', async () => {
    const el = await open('/');
    const run = el.querySelector<SVGGElement>('cc-nile-flow g.node[data-kind="run"]')!;
    run.dispatchEvent(new Event('click'));
    await settle();
    await settle();
    expect(TestBed.inject(Router).url).toMatch(/^\/runs\/run_/);
  });

  it('Runs lists every run and filters by visual state and continuation affordances', async () => {
    const el = await open('/runs');
    expect(el.querySelectorAll('table[aria-label="Runs"] tbody tr')).toHaveLength(19);

    el.querySelector<HTMLButtonElement>('[data-testid="run-filter-needs-attention"]')!.click();
    await settle();
    expect(el.querySelectorAll('table[aria-label="Runs"] tbody tr')).toHaveLength(4);
    expect(el.querySelector('[data-testid="run-filter-needs-attention"]')?.getAttribute('aria-pressed')).toBe('true');

    el.querySelector<HTMLButtonElement>('[data-testid="run-filter-continuation-available"]')!.click();
    await settle();
    expect(el.querySelectorAll('table[aria-label="Runs"] tbody tr').length).toBeGreaterThan(0);
  });

  it('Run detail composes river, timeline, result shell with canonical Result semantics, identity and evidence', async () => {
    const el = await open('/runs/run_a41c07e2');
    expect(el.querySelectorAll('cc-nile-flow g.node').length).toBeGreaterThan(8);
    expect(el.querySelector('cc-nile-flow g.node.selected')?.getAttribute('aria-label')).toContain('security-reviewer');
    expect(el.querySelectorAll('cc-execution-timeline li.entry').length).toBeGreaterThan(2);
    expect(text(el.querySelector('cc-result-shell'))).toContain('Canonical ITRU-060 in-memory evidence');
    expect(text(el.querySelector('cc-result-shell'))).toContain('Effect Ambiguous');
    expect(text(el.querySelector('cc-result-shell'))).toContain('Uncertain effect boundary');
    expect(text(el.querySelector('cc-result-shell'))).toContain('Do NOT automatically retry or replay');
    expect(text(el.querySelector('dl[aria-label="Run identity"]'))).toContain('repository_file_read');
    expect(el.querySelectorAll('cc-evidence-panel details').length).toBeGreaterThan(0);
  });

  it('Run detail surfaces succeeded outcome with bounded payload preview', async () => {
    const el = await open('/runs/run_c19e83d6');
    const shell = el.querySelector('cc-result-shell')!;
    expect(text(shell)).toContain('Succeeded');
    expect(text(shell)).toContain('Operation completed successfully');
    expect(text(shell)).toContain('784 bytes');
    expect(text(shell)).toContain('Release Checklist');
  });

  it('Run detail surfaces failed_before_effect with diagnostic code and permanent entry consumption', async () => {
    const el = await open('/runs/run_m3c4d5e6');
    const shell = el.querySelector('cc-result-shell')!;
    expect(text(shell)).toContain('Failed Before Effect');
    expect(text(shell)).toContain('containment_rejected');
    expect(text(shell)).toContain('Execution Entry is permanently consumed');
  });

  it('Run detail shows an honest empty Result for an unfinished run', async () => {
    const el = await open('/runs/run_e60d4b13');
    expect(text(el.querySelector('cc-result-shell'))).toContain('No Result published yet');
    expect(text(el.querySelector('cc-result-shell'))).toContain('absence is missing evidence');
  });

  it('Evidence surfaces skipped and unverified outcomes, opening skipped items', async () => {
    const el = await open('/runs/run_f27a9c58');
    const panel = el.querySelector('cc-evidence-panel')!;
    expect(text(panel.querySelector('.tally'))).toContain('1 skipped');
    expect(text(panel.querySelector('.tally'))).toContain('1 unverified');
    expect(panel.querySelectorAll('details[open]')).toHaveLength(1);
    expect(text(panel)).toContain('Authorization is unproven, not denied');
  });

  it('Evidence surfaces failed validation checks prominently', async () => {
    const el = await open('/runs/run_d82e11a9');
    const panel = el.querySelector('cc-evidence-panel')!;
    expect(text(panel.querySelector('.tally'))).toContain('1 failed');
    expect(text(panel.querySelector('.tally'))).toContain('1 skipped');
    expect(panel.querySelectorAll('details[open]')).toHaveLength(2);
    expect(text(panel)).toContain('FAIL: test_frame_overflow_boundary');
  });

  it('Run detail reports not found for an unknown run', async () => {
    const el = await open('/runs/run_unknown');
    expect(text(el.querySelector('cc-state-panel'))).toContain('Run not found');
  });

  it('Run detail allows selecting timeline items to inspect event details, result, and filtered evidence', async () => {
    const el = await open('/runs/run_3c81f0a7');
    const entries = el.querySelectorAll<HTMLElement>('cc-execution-timeline li.entry');
    expect(entries.length).toBeGreaterThan(1);

    // Select the tool execution entry
    const toolEntry = Array.from(entries).find((e) => text(e).includes('executed repository_file_read'));
    expect(toolEntry).toBeDefined();
    toolEntry!.click();
    await settle();

    // Verify timeline inspector opened
    const inspector = el.querySelector('.timeline-detail-pane');
    expect(inspector).not.toBeNull();
    expect(text(inspector)).toContain('agent-forge executed repository_file_read');
    expect(text(inspector)).toContain('Supplied Metadata & Provenance');

    // Verify Evidence Explorer updated header
    expect(text(el)).toContain('Filtered to event');
  });

  it('Run detail surfaces unavailable evidence in the Evidence Explorer', async () => {
    const el = await open('/runs/run_a41c07e2');
    const panel = el.querySelector('cc-evidence-panel')!;
    expect(text(panel)).toContain('unavailable');
    expect(text(panel)).toContain('Trace telemetry stream buffer was interrupted');
  });

  it('Tasks lists tasks with Core statuses and filters them', async () => {
    const el = await open('/tasks');
    expect(el.querySelectorAll('table[aria-label="Tasks"] tbody tr')).toHaveLength(10);
    const badges = Array.from(el.querySelectorAll('table tbody cc-status-badge')).map((b) => text(b));
    expect(badges).toEqual(expect.arrayContaining(['Planned', 'In progress', 'Blocked', 'Completed', 'Cancelled']));

    el.querySelector<HTMLButtonElement>('[data-testid="task-filter-blocked"]')!.click();
    await settle();
    expect(el.querySelectorAll('table[aria-label="Tasks"] tbody tr')).toHaveLength(1);

    el.querySelector<HTMLButtonElement>('[data-testid="task-filter-continuation-available"]')!.click();
    await settle();
    expect(el.querySelectorAll('table[aria-label="Tasks"] tbody tr').length).toBeGreaterThan(0);
  });

  it('Task detail shows workflow stages, runs tree, scope and a blocked reason', async () => {
    const el = await open('/tasks/DEMO-103');
    expect(el.querySelectorAll('ol.stages > li')).toHaveLength(5);
    expect(text(el.querySelector('.notice'))).toContain('explicit Human approval');
    expect(el.querySelectorAll('.run-tree .tree-item')).toHaveLength(2);
    expect(text(el.querySelector('.stages'))).toContain('Human checkpoint');
  });

  it('Task detail renders multi-agent branch and long objective without overflowing', async () => {
    const el = await open('/tasks/DEMO-108');
    expect(el.querySelectorAll('.run-tree .tree-item')).toHaveLength(3);
    expect(text(el.querySelector('h1'))).toContain('Implement distributed partition lease fencing');
    expect(text(el.querySelector('.lede'))).toContain('divergent network partitions');
  });

  it('Task detail allows selecting a run from the history tree to inspect its continuation, result and evidence', async () => {
    const el = await open('/tasks/DEMO-110');
    expect(el.querySelectorAll('.run-tree .tree-item')).toHaveLength(5);

    // Initial inspection card displays a run
    const inspection = el.querySelector('[data-testid="run-inspection-card"]')!;
    expect(inspection).not.toBeNull();
    expect(text(inspection)).toContain('run_h5_current');

    // Click on run_h4_fail in the tree
    const runH4Item = el.querySelector<HTMLElement>('[data-testid="run-tree-item-run_h4_fail"]')!;
    expect(runH4Item).not.toBeNull();
    runH4Item.click();
    await settle();
    await settle();

    // Verify inspection card switched to run_h4_fail with interrupted continuation notice
    const updatedInspection = el.querySelector('[data-testid="run-inspection-card"]')!;
    expect(text(updatedInspection)).toContain('run_h4_fail');
    expect(text(updatedInspection)).toContain('Continuation availability supplied by current data source');
    expect(text(updatedInspection)).toContain('Runner VM preempted');
  });

  it('Run detail strictly prohibits retry/replay on effect_ambiguous run', async () => {
    const el = await open('/runs/run_a41c07e2');
    const contShell = el.querySelector('cc-continuation-shell')!;
    expect(contShell).not.toBeNull();
    expect(text(contShell)).toContain('CRITICAL EFFECT UNCERTAINTY');
    expect(text(contShell)).toContain('strictly prohibit automated retry, replay, or continuation');
    // Ensure no resume/retry button is rendered for effect_ambiguous
    const resumeButton = contShell.querySelector('[data-testid="continuation-resume-button"]');
    expect(resumeButton).toBeNull();
  });

  it('Task detail reports not found for an unknown task', async () => {
    const el = await open('/tasks/NOPE-9');
    expect(text(el.querySelector('cc-state-panel'))).toContain('Task not found');
  });

  it('Agents shows actors with availability and filters by kind', async () => {
    const el = await open('/agents');
    expect(el.querySelectorAll('article.actor')).toHaveLength(7);
    expect(text(el.querySelector('main'))).toContain('Unknown');

    el.querySelector<HTMLButtonElement>('[data-testid="agent-filter-human"]')!.click();
    await settle();
    expect(el.querySelectorAll('article.actor')).toHaveLength(2);
  });

  it('Approvals is read-only, grouped, and never treats missing evidence as denial', async () => {
    const el = await open('/approvals');
    expect(text(el.querySelector('.notice'))).toContain('Read-only');
    expect(text(el.querySelector('.notice'))).toContain('not denied');
    expect(el.querySelectorAll('li.item[data-state="awaiting"]')).toHaveLength(3);
    expect(el.querySelectorAll('li.item[data-state="granted"]')).toHaveLength(2);
    expect(el.querySelectorAll('li.item[data-state="denied"]')).toHaveLength(1);
    expect(el.querySelectorAll('main button')).toHaveLength(0);
  });
});
