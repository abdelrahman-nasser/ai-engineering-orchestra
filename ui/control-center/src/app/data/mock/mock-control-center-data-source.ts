import { Injectable, InjectionToken, inject } from '@angular/core';
import { Observable, delay, map, of } from 'rxjs';
import { ControlCenterDataSource } from '../control-center-data-source';
import {
  AgentSummary,
  ApprovalItem,
  OverviewPresentation,
  RunDetail,
  RunSummary,
  TaskDetail,
  TaskSummary,
} from '../models';
import {
  MOCK_AGENTS,
  MOCK_APPROVALS,
  MOCK_RUNS,
  MOCK_TASK_DETAILS,
  buildRunDetail,
} from './mock-data';

/** Simulated latency (ms) so loading states are exercised. Tests set this to 0. */
export const MOCK_LATENCY_MS = new InjectionToken<number>('MOCK_LATENCY_MS', {
  providedIn: 'root',
  factory: () => 160,
});

function toTaskSummary(task: TaskDetail): TaskSummary {
  const runs = MOCK_RUNS.filter((run) => run.contract.taskId === task.id);
  const latestRun = runs[runs.length - 1];
  const hasResult = runs.some((r) => r.hasResult);
  const continuationAvailable = Boolean(
    latestRun?.continuation?.isAvailable && latestRun?.resultOutcome !== 'effect_ambiguous',
  );
  return {
    id: task.id,
    title: task.title,
    type: task.type,
    status: task.status,
    risk: task.risk,
    complexity: task.complexity,
    executionMode: task.executionMode,
    workflowId: task.workflowId,
    approvalLevel: task.approvalLevel,
    updatedLabel: task.updatedLabel,
    runCount: runs.length,
    latestRunId: latestRun?.runId,
    latestRunState: latestRun?.presentationState,
    hasResult,
    continuationAvailable,
    lastActivityLabel: latestRun?.lastActivityLabel ?? task.updatedLabel,
  };
}

/**
 * In-memory, read-only {@link ControlCenterDataSource} backed by fabricated
 * data. It performs no I/O and implements no Core behavior.
 */
@Injectable()
export class MockControlCenterDataSource extends ControlCenterDataSource {
  readonly originLabel = 'Mock data';

  private readonly latencyMs = inject(MOCK_LATENCY_MS);

  private respond<T>(value: T): Observable<T> {
    const source = of(value);
    return this.latencyMs > 0 ? source.pipe(delay(this.latencyMs)) : source;
  }

  getOverview(): Observable<OverviewPresentation> {
    return this.respond<OverviewPresentation>({
      tasks: MOCK_TASK_DETAILS.map(toTaskSummary),
      runs: MOCK_RUNS,
      agents: MOCK_AGENTS,
      approvals: MOCK_APPROVALS,
    });
  }

  listRuns(): Observable<readonly RunSummary[]> {
    return this.respond(MOCK_RUNS);
  }

  getRun(runId: string): Observable<RunDetail | undefined> {
    return this.respond(buildRunDetail(runId));
  }

  listTasks(): Observable<readonly TaskSummary[]> {
    return this.respond(MOCK_TASK_DETAILS).pipe(map((tasks) => tasks.map(toTaskSummary)));
  }

  getTask(taskId: string): Observable<TaskDetail | undefined> {
    return this.respond(MOCK_TASK_DETAILS.find((task) => task.id === taskId));
  }

  listAgents(): Observable<readonly AgentSummary[]> {
    return this.respond(MOCK_AGENTS);
  }

  listApprovals(): Observable<readonly ApprovalItem[]> {
    return this.respond(MOCK_APPROVALS);
  }
}
