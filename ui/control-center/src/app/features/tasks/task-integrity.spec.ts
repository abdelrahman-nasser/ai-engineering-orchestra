import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Subject, of, throwError } from 'rxjs';
import { vi } from 'vitest';
import { testProviders } from '../../../testing/providers';
import { ControlCenterDataSource } from '../../data/control-center-data-source';
import { MOCK_TASK_DETAILS, buildRunDetail } from '../../data/mock/mock-data';
import { TaskDetail } from '../../data/models';
import { TaskDetailPage } from './task-detail';

describe('Task inspection identity', () => {
  let fixture: ComponentFixture<TaskDetailPage>;
  let source: ControlCenterDataSource;
  const task = (id: string) => MOCK_TASK_DETAILS.find((item) => item.id === id)!;
  const text = () => fixture.nativeElement.textContent.replace(/\s+/g, ' ');
  const inspector = () =>
    fixture.nativeElement.querySelector('[data-testid="run-inspection-card"]');
  async function settle() {
    await fixture.whenStable();
    await fixture.whenStable();
  }
  async function open(id = 'DEMO-102') {
    fixture = TestBed.createComponent(TaskDetailPage);
    fixture.componentRef.setInput('taskId', id);
    await settle();
  }
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TaskDetailPage],
      providers: testProviders(),
    }).compileComponents();
    source = TestBed.inject(ControlCenterDataSource);
  });

  it('reconciles DEMO-102 selection on parameter-only Task changes and returning', async () => {
    await open();
    fixture.componentInstance.selectRun('run_a41c07e2');
    await settle();
    expect(inspector().textContent).toContain('run_a41c07e2');
    fixture.componentRef.setInput('taskId', 'DEMO-101');
    fixture.detectChanges();
    expect(inspector()?.textContent ?? '').not.toContain('run_a41c07e2');
    await settle();
    expect(inspector().textContent).toContain('run_3c81f0a7');
    expect(inspector().textContent).toContain('Task DEMO-101');
    expect(text()).not.toContain('run_a41c07e2');
    fixture.componentRef.setInput('taskId', 'DEMO-102');
    await settle();
    expect(inspector().textContent).toContain('run_f27a9c58');
  });

  it('hides old identity while the newly requested Task is loading or missing', async () => {
    const pending = new Subject<TaskDetail | undefined>();
    const original = source.getTask.bind(source);
    vi.spyOn(source, 'getTask').mockImplementation((id) =>
      id === 'MISSING' ? pending : original(id),
    );
    await open();
    fixture.componentRef.setInput('taskId', 'MISSING');
    await settle();
    expect(inspector()).toBeNull();
    expect(text()).not.toContain('Rework authentication');
    expect(fixture.nativeElement.querySelector('[aria-busy="true"]')).not.toBeNull();
    pending.next(undefined);
    await settle();
    expect(text()).toContain('Task not found');
    expect(inspector()).toBeNull();
  });

  it('never renders old evidence after a failed or identity-mismatched Task read', async () => {
    const original = source.getTask.bind(source);
    vi.spyOn(source, 'getTask').mockImplementation((id) =>
      id === 'FAILED'
        ? throwError(() => new Error('unavailable'))
        : id === 'WRONG'
          ? of(task('DEMO-102'))
          : original(id),
    );
    await open();
    for (const id of ['FAILED', 'WRONG']) {
      fixture.componentRef.setInput('taskId', id);
      await settle();
      expect(text()).toContain('Could not load this Task');
      expect(inspector()).toBeNull();
      expect(fixture.nativeElement.querySelector('cc-task-context-summary')).toBeNull();
    }
  });

  it('validates both returned Run identity and Task contract before exposing evidence', async () => {
    vi.spyOn(source, 'getRun').mockReturnValue(of(buildRunDetail('run_3c81f0a7')));
    await open();
    expect(inspector()).toBeNull();
    expect(text()).toContain('Selected Run details unavailable');
    const correctIdWrongTask = {
      ...buildRunDetail('run_f27a9c58')!,
      contract: buildRunDetail('run_3c81f0a7')!.contract,
    };
    vi.mocked(source.getRun).mockReturnValue(of(correctIdWrongTask));
    fixture.componentInstance.selectRun('run_a41c07e2');
    await settle();
    fixture.componentInstance.selectRun('run_f27a9c58');
    await settle();
    expect(inspector()).toBeNull();
  });

  it('handles failed/missing selected Run reads honestly and rejects unrelated selection', async () => {
    vi.spyOn(source, 'getRun').mockImplementation((id) =>
      id === 'run_f27a9c58' ? throwError(() => new Error('failed')) : of(undefined),
    );
    await open();
    expect(text()).toContain('Selected Run unavailable');
    fixture.componentInstance.selectRun('run_3c81f0a7');
    await settle();
    expect(fixture.componentInstance.selectedRunId()).toBeNull();
    fixture.componentInstance.selectRun('run_a41c07e2');
    await settle();
    expect(text()).toContain('Selected Run details unavailable');
    expect(inspector()).toBeNull();
  });

  it('does not report zero Runs or fabricate context after a failed Run-list read', async () => {
    vi.spyOn(source, 'listRuns').mockReturnValue(throwError(() => new Error('failed')));
    await open();
    expect(text()).toContain('Associated Runs unavailable');
    expect(text()).toContain('Run records unavailable');
    expect(text()).not.toContain('No runs yet');
    expect(inspector()).toBeNull();
  });

  it('uses native list selection buttons with separate navigable Detail links', async () => {
    await open();
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[role="tree"], [role="treeitem"], [aria-selected]')).toBeNull();
    const select = el.querySelector<HTMLButtonElement>(
      '[data-testid="run-tree-item-run_a41c07e2"]',
    )!;
    expect(select.tagName).toBe('BUTTON');
    expect(select.querySelector('a')).toBeNull();
    select.click();
    await settle();
    expect(select.getAttribute('aria-pressed')).toBe('true');
    expect(select.closest('li')?.querySelector('a')?.getAttribute('href')).toBe(
      '/runs/run_a41c07e2',
    );
  });

  it('distinguishes missing Run observations from proof of an empty execution history', async () => {
    vi.spyOn(source, 'listRuns').mockReturnValue(of([]));
    await open();
    expect(text()).toContain('No matching Run records supplied');
    expect(text()).toContain('matching observations are unavailable');
    expect(text()).not.toContain('Nothing has been run');
    expect(inspector()).toBeNull();
  });

  it('scopes summary assignments/approvals to the Task and review notes to the selected Run', async () => {
    await open('DEMO-101');
    const summary = () =>
      fixture.nativeElement.querySelector('cc-task-context-summary').textContent;
    expect(summary()).toContain('DEMO-101');
    expect(summary()).not.toContain('agent-sentinel');
    expect(summary()).toContain('Reviewer note');
    expect(summary()).toContain('Not supplied by this mock data model');
    expect(summary()).toContain('successful Runs do not establish final Human acceptance');
    fixture.componentRef.setInput('taskId', 'DEMO-105');
    await settle();
    expect(summary()).toContain('No approval records supplied for this Task');
    expect(summary()).not.toContain('DEMO-101');
    expect(summary()).toContain('Review evidence unavailable');
  });

  it('reports unavailable context source reads rather than a fabricated zero', async () => {
    vi.spyOn(source, 'listAgents').mockReturnValue(throwError(() => new Error('failed')));
    vi.spyOn(source, 'listApprovals').mockReturnValue(throwError(() => new Error('failed')));
    await open();
    expect(text()).toContain('Assignment observations unavailable');
    expect(text()).toContain('Approval evidence unavailable');
    expect(text()).not.toContain('0 supplied approval records');
  });
});
