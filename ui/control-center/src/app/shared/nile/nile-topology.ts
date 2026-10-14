import {
  NileEdge,
  NileNode,
  NileTopology,
  PresentationState,
  RunDetail,
  RunSummary,
  TaskStatus,
  TaskSummary,
} from '../../data/models';

/**
 * Pure builders that turn UI-local presentation data into a {@link NileTopology}.
 *
 * These describe WHAT IS DRAWN CONNECTED TO WHAT and nothing more. They do not
 * model scheduling, concurrency, ordering between branches, dependencies,
 * progress rate or dispatch. Core's Workflow stage order is sequential, so the
 * trunk follows stage order; branches are the Runs bound to a stage.
 */

/** Symmetric lane offsets around the trunk for `count` branches. */
export function branchLanes(count: number): number[] {
  const spacing = 1.15;
  return Array.from({ length: count }, (_, index) => (index - (count - 1) / 2) * spacing);
}

function stageState(runs: readonly RunSummary[]): PresentationState {
  if (runs.length === 0) {
    // Without any Run there is no observation. Do not imply progress or completion.
    return 'unknown';
  }
  if (runs.some((run) => run.presentationState === 'needs-attention')) {
    return 'needs-attention';
  }
  if (runs.some((run) => run.presentationState === 'in-progress')) {
    return 'in-progress';
  }
  if (runs.every((run) => run.presentationState === 'finished')) {
    return 'finished';
  }
  return 'not-started';
}

/** Workflow stages as the trunk, with each stage's Runs fanning out and rejoining. */
export function buildRunTopology(detail: RunDetail): NileTopology {
  const nodes: NileNode[] = [];
  const edges: NileEdge[] = [];
  const stageCount = detail.stages.length;
  const outcomeId = 'outcome';

  detail.stages.forEach((stage, index) => {
    const stageRuns = detail.taskRuns.filter((run) => run.contract.stageId === stage.id);
    const stageNodeId = `stage:${stage.id}`;
    const nextId = index + 1 < stageCount ? `stage:${detail.stages[index + 1].id}` : outcomeId;

    nodes.push({
      id: stageNodeId,
      label: stage.id,
      sublabel: stage.humanControlCheckpoint ? 'Human checkpoint' : undefined,
      kind: 'stage',
      column: index,
      lane: 0,
      state: stageState(stageRuns),
      labelSide: 'below',
    });

    if (stageRuns.length === 0) {
      edges.push({ from: stageNodeId, to: nextId });
      return;
    }

    const lanes = branchLanes(stageRuns.length);
    stageRuns.forEach((run, runIndex) => {
      nodes.push({
        id: run.runId,
        label: run.contract.roleId,
        sublabel: run.contract.actorId,
        kind: 'run',
        column: index + 0.5,
        lane: lanes[runIndex],
        state: run.presentationState,
        labelSide: lanes[runIndex] > 0 ? 'below' : 'above',
      });
      edges.push({ from: stageNodeId, to: run.runId }, { from: run.runId, to: nextId });
    });
  });

  nodes.push({
    id: outcomeId,
    label: 'Result',
    sublabel: 'provisional',
    kind: 'outcome',
    column: stageCount,
    lane: 0,
    state: 'unknown',
    labelSide: 'right',
  });

  return { nodes, edges };
}

function taskState(status: TaskStatus): PresentationState {
  switch (status) {
    case 'in_progress':
      return 'in-progress';
    case 'blocked':
      return 'needs-attention';
    case 'completed':
      return 'finished';
    case 'planned':
      return 'not-started';
    case 'cancelled':
      return 'unknown';
  }
}

/** Active Tasks and their Runs flowing into one workspace confluence. */
export function buildPortfolioTopology(
  tasks: readonly TaskSummary[],
  runs: readonly RunSummary[],
): NileTopology {
  const active = tasks
    .filter((task) => task.status === 'in_progress' || task.status === 'blocked')
    .map((task) => ({ task, runs: runs.filter((run) => run.contract.taskId === task.id) }))
    .filter((entry) => entry.runs.length > 0);

  const totalRuns = active.reduce((sum, entry) => sum + entry.runs.length, 0);
  const nodes: NileNode[] = [];
  const edges: NileEdge[] = [];
  const confluenceId = 'confluence';
  let slot = 0;

  for (const entry of active) {
    const lanes = entry.runs.map(() => slot++ - (totalRuns - 1) / 2);
    const taskLane = lanes.reduce((sum, lane) => sum + lane, 0) / lanes.length;

    nodes.push({
      id: entry.task.id,
      label: entry.task.id,
      sublabel: entry.task.title,
      kind: 'task',
      column: 0,
      lane: taskLane,
      state: taskState(entry.task.status),
      labelSide: 'left',
    });

    entry.runs.forEach((run, index) => {
      nodes.push({
        id: run.runId,
        label: run.contract.stageId,
        sublabel: run.contract.actorId,
        kind: 'run',
        column: 1,
        lane: lanes[index],
        state: run.presentationState,
        labelSide: 'above',
      });
      edges.push({ from: entry.task.id, to: run.runId }, { from: run.runId, to: confluenceId });
    });
  }

  nodes.push({
    id: confluenceId,
    label: 'Workspace',
    sublabel: `${active.length} active Task${active.length === 1 ? '' : 's'}`,
    kind: 'confluence',
    column: 2,
    lane: 0,
    state: 'unknown',
    labelSide: 'right',
  });

  return { nodes, edges };
}
