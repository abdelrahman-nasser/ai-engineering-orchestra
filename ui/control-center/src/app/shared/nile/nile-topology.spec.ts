import { MOCK_RUNS, MOCK_TASK_DETAILS, buildRunDetail } from '../../data/mock/mock-data';
import { buildPortfolioTopology, buildRunTopology, branchLanes } from './nile-topology';

describe('branchLanes', () => {
  it('is empty for zero, centered for one and symmetric for many', () => {
    expect(branchLanes(0)).toEqual([]);
    expect(branchLanes(1)).toEqual([0]);
    const two = branchLanes(2);
    expect(two[0]).toBeCloseTo(-two[1]);
    const three = branchLanes(3);
    expect(three[1]).toBeCloseTo(0);
    expect(three[0]).toBeCloseTo(-three[2]);
  });
});

describe('buildRunTopology', () => {
  const detail = buildRunDetail('run_f27a9c58')!;
  const topology = buildRunTopology(detail);

  it('has one trunk node per Workflow stage in Core order, then a provisional outcome', () => {
    const stages = topology.nodes.filter((node) => node.kind === 'stage');
    expect(stages.map((node) => node.label)).toEqual(detail.stages.map((stage) => stage.id));
    expect(stages.map((node) => node.column)).toEqual(stages.map((_, index) => index));
    const outcome = topology.nodes.filter((node) => node.kind === 'outcome');
    expect(outcome).toHaveLength(1);
    expect(outcome[0].sublabel).toBe('provisional');
  });

  it('draws one branch per Run of the same Task and no others', () => {
    const branches = topology.nodes.filter((node) => node.kind === 'run');
    expect(branches.map((node) => node.id).sort()).toEqual(detail.taskRuns.map((run) => run.runId).sort());
  });

  it('only creates edges between existing nodes and has unique node ids', () => {
    const ids = topology.nodes.map((node) => node.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const edge of topology.edges) {
      expect(ids).toContain(edge.from);
      expect(ids).toContain(edge.to);
    }
  });

  it('fans a Stage out to its Runs and rejoins at the next reach', () => {
    const reviewRuns = detail.taskRuns.filter((run) => run.contract.stageId === 'review');
    expect(reviewRuns.length).toBe(2);
    for (const run of reviewRuns) {
      expect(topology.edges).toContainEqual({ from: 'stage:review', to: run.runId });
      expect(topology.edges).toContainEqual({ from: run.runId, to: 'outcome' });
    }
    const lanes = reviewRuns.map((run) => topology.nodes.find((node) => node.id === run.runId)!.lane);
    expect(lanes[0]).not.toBe(lanes[1]);
  });

  it('links stages directly when no Run is bound, without implying progress', () => {
    expect(topology.edges).toContainEqual({ from: 'stage:understand', to: 'stage:security-analysis' });
    const understand = topology.nodes.find((node) => node.id === 'stage:understand')!;
    expect(understand.state).toBe('unknown');
  });

  it('derives stage state from its Runs, with attention dominating', () => {
    const review = topology.nodes.find((node) => node.id === 'stage:review')!;
    expect(review.state).toBe('needs-attention');
    const analysis = topology.nodes.find((node) => node.id === 'stage:security-analysis')!;
    expect(analysis.state).toBe('finished');
  });
});

describe('buildPortfolioTopology', () => {
  const tasks = MOCK_TASK_DETAILS;
  const topology = buildPortfolioTopology(tasks, MOCK_RUNS);

  it('includes only active Tasks that have Runs', () => {
    const taskNodes = topology.nodes.filter((node) => node.kind === 'task').map((node) => node.id);
    expect(taskNodes.sort()).toEqual(['DEMO-101', 'DEMO-102', 'DEMO-103', 'DEMO-107', 'DEMO-108', 'DEMO-110']);
  });

  it('merges every Run into one confluence', () => {
    const runs = topology.nodes.filter((node) => node.kind === 'run');
    expect(runs).toHaveLength(16);
    for (const run of runs) {
      expect(topology.edges).toContainEqual({ from: run.id, to: 'confluence' });
    }
  });

  it('gives every node a distinct position', () => {
    const keys = topology.nodes.map((node) => `${node.column}:${node.lane.toFixed(3)}`);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('renders a valid, empty-safe topology with no active Tasks', () => {
    const empty = buildPortfolioTopology([], []);
    expect(empty.nodes).toHaveLength(1);
    expect(empty.edges).toHaveLength(0);
  });
});
