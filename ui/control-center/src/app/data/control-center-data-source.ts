import { Observable } from 'rxjs';
import {
  AgentSummary,
  ApprovalItem,
  DagGraphReadModel,
  DagScenarioInfo,
  OverviewPresentation,
  RunDetail,
  RunSummary,
  TaskDetail,
  TaskSummary,
} from './models';

/**
 * The single boundary between Control Center screens and any data origin.
 *
 * Screens depend ONLY on this abstract class (it doubles as the DI token).
 * Today the sole implementation is {@link MockControlCenterDataSource}.
 *
 * This is deliberately read-only and transport-agnostic. It defines no REST,
 * WebSocket, polling, push, write, or command contract. A real implementation
 * must wait for explicit Core contracts (see docs/core-contract-questions.md).
 *
 * `undefined` from a single-item lookup means "not found in this source".
 */
export abstract class ControlCenterDataSource {
  /** Human-readable origin label shown in the shell, e.g. "Mock data". */
  abstract readonly originLabel: string;

  abstract getOverview(): Observable<OverviewPresentation>;

  abstract listRuns(): Observable<readonly RunSummary[]>;
  abstract getRun(runId: string): Observable<RunDetail | undefined>;

  abstract listTasks(): Observable<readonly TaskSummary[]>;
  abstract getTask(taskId: string): Observable<TaskDetail | undefined>;

  abstract listAgents(): Observable<readonly AgentSummary[]>;

  abstract listApprovals(): Observable<readonly ApprovalItem[]>;

  abstract listDagScenarios(): Observable<readonly DagScenarioInfo[]>;
  abstract getDagGraph(scenarioId?: string): Observable<DagGraphReadModel | undefined>;
}
