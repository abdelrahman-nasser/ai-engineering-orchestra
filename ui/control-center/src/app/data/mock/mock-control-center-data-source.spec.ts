import { TestBed } from '@angular/core/testing';
import { firstValueFrom } from 'rxjs';
import { ControlCenterDataSource } from '../control-center-data-source';
import { ApprovalLevel, AvailabilityState, Level, PresentationState, TaskStatus } from '../models';
import { testProviders } from '../../../testing/providers';

describe('MockControlCenterDataSource', () => {
  let source: ControlCenterDataSource;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: testProviders() });
    source = TestBed.inject(ControlCenterDataSource);
  });

  it('identifies itself as mock data', () => {
    expect(source.originLabel).toBe('Mock data');
  });

  it('lists tasks, runs, agents and approvals', async () => {
    expect((await firstValueFrom(source.listTasks())).length).toBeGreaterThan(0);
    expect((await firstValueFrom(source.listRuns())).length).toBeGreaterThan(0);
    expect((await firstValueFrom(source.listAgents())).length).toBeGreaterThan(0);
    expect((await firstValueFrom(source.listApprovals())).length).toBeGreaterThan(0);
  });

  it('returns undefined for unknown ids instead of throwing', async () => {
    expect(await firstValueFrom(source.getRun('run_missing'))).toBeUndefined();
    expect(await firstValueFrom(source.getTask('NOPE-1'))).toBeUndefined();
  });

  it('assembles run detail with timeline, evidence and sibling runs', async () => {
    const run = await firstValueFrom(source.getRun('run_f27a9c58'));
    expect(run).toBeDefined();
    expect(run!.timeline.length).toBeGreaterThan(0);
    expect(run!.evidence.length).toBeGreaterThan(0);
    expect(run!.taskRuns.every((sibling) => sibling.contract.taskId === run!.contract.taskId)).toBe(true);
    expect(run!.taskRuns.length).toBe(4);
  });

  it('is referentially consistent across collections', async () => {
    const tasks = await firstValueFrom(source.listTasks());
    const runs = await firstValueFrom(source.listRuns());
    const approvals = await firstValueFrom(source.listApprovals());
    const taskIds = new Set(tasks.map((task) => task.id));
    const runIds = runs.map((run) => run.runId);

    expect(new Set(runIds).size).toBe(runIds.length);
    expect(runs.every((run) => taskIds.has(run.contract.taskId))).toBe(true);
    expect(approvals.every((approval) => taskIds.has(approval.taskId))).toBe(true);
    expect(approvals.every((approval) => !approval.runId || runIds.includes(approval.runId))).toBe(true);
  });

  it('only uses existing Core vocabulary for Core-owned fields', async () => {
    const taskStatuses: TaskStatus[] = ['planned', 'in_progress', 'blocked', 'completed', 'cancelled'];
    const levels: Level[] = ['low', 'medium', 'high', 'critical'];
    const approvalLevels: ApprovalLevel[] = ['none', 'review', 'explicit', 'protected'];
    const availability: AvailabilityState[] = ['available', 'unavailable', 'unknown'];

    const tasks = await firstValueFrom(source.listTasks());
    const agents = await firstValueFrom(source.listAgents());
    expect(tasks.every((task) => taskStatuses.includes(task.status))).toBe(true);
    expect(tasks.every((task) => levels.includes(task.risk) && levels.includes(task.complexity))).toBe(true);
    expect(tasks.every((task) => approvalLevels.includes(task.approvalLevel))).toBe(true);
    expect(agents.every((agent) => availability.includes(agent.availability))).toBe(true);
  });

  it('keeps UI-local presentation states within the declared set', async () => {
    const allowed: PresentationState[] = ['not-started', 'in-progress', 'needs-attention', 'finished', 'unknown'];
    const runs = await firstValueFrom(source.listRuns());
    expect(runs.every((run) => allowed.includes(run.presentationState))).toBe(true);
  });

  it('never presents a Result for a run that has not finished', async () => {
    const runs = await firstValueFrom(source.listRuns());
    for (const summary of runs) {
      const detail = await firstValueFrom(source.getRun(summary.runId));
      if (summary.presentationState !== 'finished') {
        expect(detail!.result).toBeNull();
      }
    }
  });
});
