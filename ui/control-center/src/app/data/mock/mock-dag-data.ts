import {
  DagEdgeReadModel,
  DagGraphReadModel,
  DagNodeReadModel,
  DagScenarioInfo,
  SchedulerSummaryReadModel,
} from '../models';
import {
  DEPENDENCY_DISCLAIMER_NOTICE,
  SCHEDULER_DISCLAIMER_NOTICE,
} from '../dag-adapter';
import { MOCK_RESULT_READ_MODELS } from './mock-data';

function computeSchedulerSummary(nodes: readonly DagNodeReadModel[]): SchedulerSummaryReadModel {
  let queued = 0;
  let ready = 0;
  let active = 0;
  let blocked = 0;
  let completed = 0;
  let attention = 0;

  for (const node of nodes) {
    if (node.resultOutcome === 'effect_ambiguous' || node.schedulerState === 'attention') {
      attention++;
    } else {
      switch (node.schedulerState) {
        case 'queued':
          queued++;
          break;
        case 'ready-looking':
          ready++;
          break;
        case 'active-looking':
          active++;
          break;
        case 'blocked-looking':
          blocked++;
          break;
        case 'completed-looking':
          completed++;
          break;
      }
    }
  }

  return {
    queuedCount: queued,
    readyLookingCount: ready,
    activeLookingCount: active,
    blockedLookingCount: blocked,
    completedLookingCount: completed,
    attentionCount: attention,
    dataSourceNotice: SCHEDULER_DISCLAIMER_NOTICE,
  };
}

// ---------------------------------------------------------------------------
// 1. Fan-out & Fan-in (Default Workspace Scenario)
// ---------------------------------------------------------------------------
const FANOUT_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'fo-understand',
    label: 'Understand Scope',
    sublabel: 'DEMO-101 · Stage 1',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'understand',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['fo-plan'],
  },
  {
    id: 'fo-plan',
    label: 'Architecture Plan',
    sublabel: 'agent-atlas · architect',
    kind: 'stage',
    column: 1,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'design',
    actorId: 'agent-atlas',
    roleId: 'architect',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['fo-understand'],
    downstreamNodeIds: ['fo-fanout-point'],
  },
  {
    id: 'fo-fanout-point',
    label: 'Sub-Agent Dispatch',
    sublabel: '4 parallel tributaries',
    kind: 'stage',
    column: 2,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'implement',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['fo-plan'],
    downstreamNodeIds: ['fo-sub-api', 'fo-sub-db', 'fo-sub-sec', 'fo-sub-test'],
  },
  // Tributary 1: API Implementation (completed, has Result)
  {
    id: 'fo-sub-api',
    label: 'API Service Layer',
    sublabel: 'agent-forge · software-engineer',
    kind: 'subagent',
    column: 3,
    lane: -1.4,
    taskId: 'DEMO-101',
    runId: 'run_c19e83d6',
    workflowId: 'standard-change',
    stageId: 'implement',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::itru-native-repository-file-read::v1',
    isMainFlow: false,
    schedulerState: 'completed-looking',
    hasResult: true,
    resultOutcome: 'succeeded',
    linkedResult: MOCK_RESULT_READ_MODELS.get('run_c19e83d6'),
    hasEvidence: true,
    evidenceCount: 3,
    hasJournal: true,
    upstreamNodeIds: ['fo-fanout-point'],
    downstreamNodeIds: ['fo-join'],
  },
  // Tributary 2: DB Schema (active)
  {
    id: 'fo-sub-db',
    label: 'Database Migrations',
    sublabel: 'agent-forge · in progress',
    kind: 'subagent',
    column: 3,
    lane: -0.45,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'implement',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::database-migration-runner',
    isMainFlow: false,
    schedulerState: 'active-looking',
    hasEvidence: true,
    evidenceCount: 1,
    upstreamNodeIds: ['fo-fanout-point'],
    downstreamNodeIds: ['fo-join'],
  },
  // Tributary 3: Security Controls (active)
  {
    id: 'fo-sub-sec',
    label: 'Security Analysis',
    sublabel: 'agent-sentinel · security-reviewer',
    kind: 'subagent',
    column: 3,
    lane: 0.45,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'security-analysis',
    actorId: 'agent-sentinel',
    roleId: 'security-reviewer',
    toolId: 'tool::security-scanner',
    isMainFlow: false,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['fo-fanout-point'],
    downstreamNodeIds: ['fo-join'],
  },
  // Tributary 4: Test Suite (ready)
  {
    id: 'fo-sub-test',
    label: 'Test Suite Scaffold',
    sublabel: 'agent-lumen · queued',
    kind: 'subagent',
    column: 3,
    lane: 1.4,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'validate',
    actorId: 'agent-lumen',
    roleId: 'reviewer',
    isMainFlow: false,
    schedulerState: 'ready-looking',
    upstreamNodeIds: ['fo-fanout-point'],
    downstreamNodeIds: ['fo-join'],
  },
  // Convergence Join
  {
    id: 'fo-join',
    label: 'Confluence Join',
    sublabel: 'Wait for all 4 tributaries',
    kind: 'join',
    column: 4,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['fo-sub-api', 'fo-sub-db', 'fo-sub-sec', 'fo-sub-test'],
    downstreamNodeIds: ['fo-validate'],
  },
  // Validation
  {
    id: 'fo-validate',
    label: 'Integration Validation',
    sublabel: 'Regression test suite',
    kind: 'stage',
    column: 5,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'validate',
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['fo-join'],
    downstreamNodeIds: ['fo-outcome'],
  },
  // Outcome
  {
    id: 'fo-outcome',
    label: 'Final Review & Merge',
    sublabel: 'Human control checkpoint',
    kind: 'outcome',
    column: 6,
    lane: 0,
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'review',
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['fo-validate'],
    downstreamNodeIds: [],
  },
];

const FANOUT_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'fo-e1', from: 'fo-understand', to: 'fo-plan' },
  { id: 'fo-e2', from: 'fo-plan', to: 'fo-fanout-point' },
  { id: 'fo-e3', from: 'fo-fanout-point', to: 'fo-sub-api', isTributary: true, state: 'finished' },
  { id: 'fo-e4', from: 'fo-fanout-point', to: 'fo-sub-db', isTributary: true, state: 'in-progress' },
  { id: 'fo-e5', from: 'fo-fanout-point', to: 'fo-sub-sec', isTributary: true, state: 'in-progress' },
  { id: 'fo-e6', from: 'fo-fanout-point', to: 'fo-sub-test', isTributary: true, state: 'not-started' },
  { id: 'fo-e7', from: 'fo-sub-api', to: 'fo-join', isTributary: true, state: 'finished' },
  { id: 'fo-e8', from: 'fo-sub-db', to: 'fo-join', isTributary: true, state: 'in-progress' },
  { id: 'fo-e9', from: 'fo-sub-sec', to: 'fo-join', isTributary: true, state: 'in-progress' },
  { id: 'fo-e10', from: 'fo-sub-test', to: 'fo-join', isTributary: true, state: 'not-started' },
  { id: 'fo-e11', from: 'fo-join', to: 'fo-validate' },
  { id: 'fo-e12', from: 'fo-validate', to: 'fo-outcome' },
];

// ---------------------------------------------------------------------------
// 2. Linear Workflow
// ---------------------------------------------------------------------------
const LINEAR_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'lin-understand',
    label: '1. Understand Scope',
    sublabel: 'Requirements analysis',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-103',
    workflowId: 'standard-change',
    stageId: 'understand',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['lin-design'],
  },
  {
    id: 'lin-design',
    label: '2. Architecture Design',
    sublabel: 'Interface specifications',
    kind: 'stage',
    column: 1,
    lane: 0,
    taskId: 'DEMO-103',
    workflowId: 'standard-change',
    stageId: 'design',
    actorId: 'agent-atlas',
    roleId: 'architect',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['lin-understand'],
    downstreamNodeIds: ['lin-implement'],
  },
  {
    id: 'lin-implement',
    label: '3. Implementation',
    sublabel: 'Core logic updates',
    kind: 'stage',
    column: 2,
    lane: 0,
    taskId: 'DEMO-103',
    workflowId: 'standard-change',
    stageId: 'implement',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::file-editor',
    isMainFlow: true,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['lin-design'],
    downstreamNodeIds: ['lin-validate'],
  },
  {
    id: 'lin-validate',
    label: '4. Validation Suite',
    sublabel: 'Unit & integration tests',
    kind: 'stage',
    column: 3,
    lane: 0,
    taskId: 'DEMO-103',
    workflowId: 'standard-change',
    stageId: 'validate',
    actorId: 'agent-lumen',
    roleId: 'reviewer',
    isMainFlow: true,
    schedulerState: 'ready-looking',
    upstreamNodeIds: ['lin-implement'],
    downstreamNodeIds: ['lin-review'],
  },
  {
    id: 'lin-review',
    label: '5. Human Review Checkpoint',
    sublabel: 'Independent sign-off',
    kind: 'outcome',
    column: 4,
    lane: 0,
    taskId: 'DEMO-103',
    workflowId: 'standard-change',
    stageId: 'review',
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['lin-validate'],
    downstreamNodeIds: [],
  },
];

const LINEAR_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'lin-e1', from: 'lin-understand', to: 'lin-design' },
  { id: 'lin-e2', from: 'lin-design', to: 'lin-implement' },
  { id: 'lin-e3', from: 'lin-implement', to: 'lin-validate' },
  { id: 'lin-e4', from: 'lin-validate', to: 'lin-review' },
];

// ---------------------------------------------------------------------------
// 3. Blocked Branch & Security Checkpoint
// ---------------------------------------------------------------------------
const BLOCKED_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'blk-init',
    label: 'Security Assessment',
    sublabel: 'DEMO-102 · Stage 1',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'understand',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['blk-branch-pt'],
  },
  {
    id: 'blk-branch-pt',
    label: 'Branch Point',
    sublabel: 'Split auditing paths',
    kind: 'stage',
    column: 1,
    lane: 0,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'security-analysis',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['blk-init'],
    downstreamNodeIds: ['blk-safe-path', 'blk-blocked-task'],
  },
  {
    id: 'blk-safe-path',
    label: 'Static Code Audit',
    sublabel: 'agent-sentinel · running',
    kind: 'subagent',
    column: 2,
    lane: -1,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    actorId: 'agent-sentinel',
    roleId: 'security-reviewer',
    toolId: 'tool::static-analyzer',
    isMainFlow: false,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['blk-branch-pt'],
    downstreamNodeIds: ['blk-join'],
  },
  {
    id: 'blk-blocked-task',
    label: 'Protected Credential Rotation',
    sublabel: 'BLOCKED · Missing Grant',
    kind: 'subagent',
    column: 2,
    lane: 1,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::credential-rotator',
    isMainFlow: false,
    schedulerState: 'blocked-looking',
    blockedByNodeIds: ['blk-checkpoint'],
    attentionReason: 'Missing Authorization Grant for elevated secret write access.',
    upstreamNodeIds: ['blk-branch-pt'],
    downstreamNodeIds: ['blk-join'],
  },
  {
    id: 'blk-checkpoint',
    label: 'Human Approval Checkpoint',
    sublabel: 'Protected Level: explicit sign-off',
    kind: 'checkpoint',
    column: 1.5,
    lane: 2.1,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    isMainFlow: false,
    schedulerState: 'attention',
    attentionReason: 'Human operator approval required before grant emission.',
    upstreamNodeIds: [],
    downstreamNodeIds: ['blk-blocked-task'],
  },
  {
    id: 'blk-join',
    label: 'Audit Convergence',
    sublabel: 'BLOCKED until tributary unblocks',
    kind: 'join',
    column: 3,
    lane: 0,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    isMainFlow: true,
    schedulerState: 'blocked-looking',
    blockedByNodeIds: ['blk-blocked-task'],
    attentionReason: 'Downstream blocked waiting on protected rotation branch.',
    upstreamNodeIds: ['blk-safe-path', 'blk-blocked-task'],
    downstreamNodeIds: ['blk-outcome'],
  },
  {
    id: 'blk-outcome',
    label: 'Release Gate Sign-off',
    sublabel: 'Final clearance',
    kind: 'outcome',
    column: 4,
    lane: 0,
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['blk-join'],
    downstreamNodeIds: [],
  },
];

const BLOCKED_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'blk-e1', from: 'blk-init', to: 'blk-branch-pt' },
  { id: 'blk-e2', from: 'blk-branch-pt', to: 'blk-safe-path', isTributary: true, state: 'in-progress' },
  { id: 'blk-e3', from: 'blk-branch-pt', to: 'blk-blocked-task', isTributary: true, state: 'needs-attention' },
  { id: 'blk-e4', from: 'blk-checkpoint', to: 'blk-blocked-task', isTributary: true, state: 'needs-attention' },
  { id: 'blk-e5', from: 'blk-safe-path', to: 'blk-join', isTributary: true, state: 'in-progress' },
  { id: 'blk-e6', from: 'blk-blocked-task', to: 'blk-join', isTributary: true, state: 'needs-attention' },
  { id: 'blk-e7', from: 'blk-join', to: 'blk-outcome' },
];

// ---------------------------------------------------------------------------
// 4. Attention / Diagnostic Error Branch
// ---------------------------------------------------------------------------
const ATTENTION_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'att-start',
    label: 'Initiate Workspace Scan',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-105',
    workflowId: 'standard-change',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['att-error-node', 'att-side-node'],
  },
  {
    id: 'att-error-node',
    label: 'Containment Route Check',
    sublabel: 'FAILED: containment_rejected',
    kind: 'subagent',
    column: 1,
    lane: -1,
    taskId: 'DEMO-105',
    runId: 'run_m3c4d5e6',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::itru-native-repository-file-read::v1',
    isMainFlow: false,
    schedulerState: 'attention',
    attentionReason: 'Containment violation: configured tool route exceeded sandboxed filesystem scope.',
    hasResult: true,
    resultOutcome: 'failed_before_effect',
    linkedResult: MOCK_RESULT_READ_MODELS.get('run_m3c4d5e6'),
    hasEvidence: true,
    evidenceCount: 2,
    hasJournal: true,
    upstreamNodeIds: ['att-start'],
    downstreamNodeIds: ['att-recover'],
  },
  {
    id: 'att-side-node',
    label: 'Telemetry Heartbeat',
    sublabel: 'Healthy background observer',
    kind: 'subagent',
    column: 1,
    lane: 1,
    taskId: 'DEMO-105',
    actorId: 'agent-atlas',
    roleId: 'architect',
    isMainFlow: false,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['att-start'],
    downstreamNodeIds: ['att-recover'],
  },
  {
    id: 'att-recover',
    label: 'Diagnostic Escalation',
    sublabel: 'Operator intervention required',
    kind: 'join',
    column: 2,
    lane: 0,
    taskId: 'DEMO-105',
    isMainFlow: true,
    schedulerState: 'attention',
    attentionReason: 'Upstream containment failure requires diagnostic review before continuing.',
    upstreamNodeIds: ['att-error-node', 'att-side-node'],
    downstreamNodeIds: [],
  },
];

const ATTENTION_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'att-e1', from: 'att-start', to: 'att-error-node', isTributary: true, state: 'needs-attention' },
  { id: 'att-e2', from: 'att-start', to: 'att-side-node', isTributary: true, state: 'finished' },
  { id: 'att-e3', from: 'att-error-node', to: 'att-recover', isTributary: true, state: 'needs-attention' },
  { id: 'att-e4', from: 'att-side-node', to: 'att-recover', isTributary: true, state: 'finished' },
];

// ---------------------------------------------------------------------------
// 5. effect_ambiguous Node (Prominent Hazard, Strict No-Retry Boundary)
// ---------------------------------------------------------------------------
const AMBIGUOUS_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'amb-stage-1',
    label: 'Preparation & Lease Acquisition',
    sublabel: 'Completed safely before effect',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-106',
    workflowId: 'standard-change',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['amb-hazardous-node'],
  },
  {
    id: 'amb-hazardous-node',
    label: 'Hazardous File Write Attempt',
    sublabel: 'DANGER: effect_ambiguous Result',
    kind: 'run',
    column: 1,
    lane: 0,
    taskId: 'DEMO-106',
    runId: 'run_a41c07e2',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::itru-native-repository-file-read::v1',
    isMainFlow: true,
    schedulerState: 'attention',
    resultOutcome: 'effect_ambiguous',
    attentionReason:
      'Content access commenced or post-operation uncertainty encountered. Automatic retry or replay is STRICTLY PROHIBITED.',
    hasResult: true,
    linkedResult: MOCK_RESULT_READ_MODELS.get('run_a41c07e2'),
    hasEvidence: true,
    evidenceCount: 3,
    hasJournal: true,
    upstreamNodeIds: ['amb-stage-1'],
    downstreamNodeIds: ['amb-quarantine'],
  },
  {
    id: 'amb-quarantine',
    label: 'Manual Quarantine & State Verification',
    sublabel: 'Core defines NO safe recovery without manual external verification',
    kind: 'outcome',
    column: 2,
    lane: 0,
    taskId: 'DEMO-106',
    isMainFlow: true,
    schedulerState: 'attention',
    attentionReason: 'Manual ledger reconciliation mandatory before Task resumption.',
    upstreamNodeIds: ['amb-hazardous-node'],
    downstreamNodeIds: [],
  },
];

const AMBIGUOUS_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'amb-e1', from: 'amb-stage-1', to: 'amb-hazardous-node', state: 'needs-attention' },
  { id: 'amb-e2', from: 'amb-hazardous-node', to: 'amb-quarantine', state: 'needs-attention' },
];

// ---------------------------------------------------------------------------
// 6. Completed Historical Graph
// ---------------------------------------------------------------------------
const HISTORICAL_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'hist-1',
    label: '1. Discovery',
    sublabel: 'Finished 2h ago',
    kind: 'stage',
    column: 0,
    lane: 0,
    taskId: 'DEMO-104',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['hist-2'],
  },
  {
    id: 'hist-2',
    label: '2. Specification Draft',
    sublabel: 'Finished 1h 45m ago',
    kind: 'stage',
    column: 1,
    lane: 0,
    taskId: 'DEMO-104',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['hist-1'],
    downstreamNodeIds: ['hist-3a', 'hist-3b'],
  },
  {
    id: 'hist-3a',
    label: '3a. Implementation',
    sublabel: 'Validated Result · 784 bytes',
    kind: 'subagent',
    column: 2,
    lane: -1,
    taskId: 'DEMO-104',
    runId: 'run_c19e83d6',
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::itru-native-repository-file-read::v1',
    isMainFlow: false,
    schedulerState: 'completed-looking',
    hasResult: true,
    resultOutcome: 'succeeded',
    linkedResult: MOCK_RESULT_READ_MODELS.get('run_c19e83d6'),
    hasEvidence: true,
    evidenceCount: 3,
    hasJournal: true,
    upstreamNodeIds: ['hist-2'],
    downstreamNodeIds: ['hist-4'],
  },
  {
    id: 'hist-3b',
    label: '3b. Peer Validation',
    sublabel: 'Independent audit passed',
    kind: 'subagent',
    column: 2,
    lane: 1,
    taskId: 'DEMO-104',
    runId: 'run_b9d2e5f1',
    actorId: 'agent-sentinel',
    roleId: 'security-reviewer',
    toolId: 'tool::itru-native-repository-file-read::v1',
    isMainFlow: false,
    schedulerState: 'completed-looking',
    hasResult: true,
    resultOutcome: 'succeeded',
    linkedResult: MOCK_RESULT_READ_MODELS.get('run_b9d2e5f1'),
    hasEvidence: true,
    evidenceCount: 2,
    hasJournal: true,
    upstreamNodeIds: ['hist-2'],
    downstreamNodeIds: ['hist-4'],
  },
  {
    id: 'hist-4',
    label: '4. Confluence Verification',
    sublabel: 'All checks passed',
    kind: 'join',
    column: 3,
    lane: 0,
    taskId: 'DEMO-104',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['hist-3a', 'hist-3b'],
    downstreamNodeIds: ['hist-5'],
  },
  {
    id: 'hist-5',
    label: '5. Release Signed Off',
    sublabel: 'Archived historical execution',
    kind: 'outcome',
    column: 4,
    lane: 0,
    taskId: 'DEMO-104',
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: ['hist-4'],
    downstreamNodeIds: [],
  },
];

const HISTORICAL_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'hist-e1', from: 'hist-1', to: 'hist-2' },
  { id: 'hist-e2', from: 'hist-2', to: 'hist-3a', isTributary: true, state: 'finished' },
  { id: 'hist-e3', from: 'hist-2', to: 'hist-3b', isTributary: true, state: 'finished' },
  { id: 'hist-e4', from: 'hist-3a', to: 'hist-4', isTributary: true, state: 'finished' },
  { id: 'hist-e5', from: 'hist-3b', to: 'hist-4', isTributary: true, state: 'finished' },
  { id: 'hist-e6', from: 'hist-4', to: 'hist-5' },
];

// ---------------------------------------------------------------------------
// 7. Active Branch Scenario
// ---------------------------------------------------------------------------
const ACTIVE_NODES: readonly DagNodeReadModel[] = [
  {
    id: 'act-1',
    label: 'Workflow Kickoff',
    sublabel: 'Completed',
    kind: 'stage',
    column: 0,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['act-2', 'act-3'],
  },
  {
    id: 'act-2',
    label: 'Live Agent Stream A',
    sublabel: 'Generating code diffs',
    kind: 'subagent',
    column: 1,
    lane: -1,
    actorId: 'agent-forge',
    roleId: 'software-engineer',
    toolId: 'tool::file-writer',
    isMainFlow: false,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['act-1'],
    downstreamNodeIds: ['act-4'],
  },
  {
    id: 'act-3',
    label: 'Live Agent Stream B',
    sublabel: 'Running tests concurrently',
    kind: 'subagent',
    column: 1,
    lane: 1,
    actorId: 'agent-lumen',
    roleId: 'reviewer',
    toolId: 'tool::pytest-runner',
    isMainFlow: false,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['act-1'],
    downstreamNodeIds: ['act-4'],
  },
  {
    id: 'act-4',
    label: 'Results Aggregator',
    sublabel: 'Ready to receive inputs',
    kind: 'join',
    column: 2,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'ready-looking',
    upstreamNodeIds: ['act-2', 'act-3'],
    downstreamNodeIds: ['act-5'],
  },
  {
    id: 'act-5',
    label: 'Deploy Artifact',
    sublabel: 'Queued',
    kind: 'outcome',
    column: 3,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['act-4'],
    downstreamNodeIds: [],
  },
];

const ACTIVE_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'act-e1', from: 'act-1', to: 'act-2', isTributary: true, state: 'in-progress' },
  { id: 'act-e2', from: 'act-1', to: 'act-3', isTributary: true, state: 'in-progress' },
  { id: 'act-e3', from: 'act-2', to: 'act-4', isTributary: true, state: 'in-progress' },
  { id: 'act-e4', from: 'act-3', to: 'act-4', isTributary: true, state: 'in-progress' },
  { id: 'act-e5', from: 'act-4', to: 'act-5' },
];

// ---------------------------------------------------------------------------
// 8. Large 24-Node Mesh Scenario
// ---------------------------------------------------------------------------
function buildLargeMeshScenario(): {
  nodes: readonly DagNodeReadModel[];
  edges: readonly DagEdgeReadModel[];
} {
  const nodes: DagNodeReadModel[] = [];
  const edges: DagEdgeReadModel[] = [];

  // Column 0: Root inputs (3 nodes)
  for (let i = 0; i < 3; i++) {
    const id = `mesh-c0-${i}`;
    nodes.push({
      id,
      label: `Init Source ${i + 1}`,
      sublabel: `Input packet ${i + 1}`,
      kind: 'stage',
      column: 0,
      lane: (i - 1) * 1.5,
      isMainFlow: i === 1,
      schedulerState: 'completed-looking',
      upstreamNodeIds: [],
      downstreamNodeIds: [`mesh-c1-0`, `mesh-c1-1`, `mesh-c1-2`, `mesh-c1-3`].slice(i, i + 2),
    });
  }

  // Column 1: Parser & Analysis tier (4 nodes)
  for (let i = 0; i < 4; i++) {
    const id = `mesh-c1-${i}`;
    const state = i === 3 ? 'ready-looking' : 'completed-looking';
    nodes.push({
      id,
      label: `Analyzer ${i + 1}`,
      sublabel: `actor-${['atlas', 'forge', 'sentinel', 'lumen'][i]}`,
      kind: 'subagent',
      column: 1,
      lane: (i - 1.5) * 1.2,
      actorId: `agent-${['atlas', 'forge', 'sentinel', 'lumen'][i]}`,
      roleId: i % 2 === 0 ? 'architect' : 'software-engineer',
      toolId: `tool::parser-${i + 1}`,
      isMainFlow: false,
      schedulerState: state,
      upstreamNodeIds: [`mesh-c0-${Math.min(i, 2)}`],
      downstreamNodeIds: [`mesh-c2-0`, `mesh-c2-1`, `mesh-c2-2`, `mesh-c2-3`].slice(
        Math.max(0, i - 1),
        i + 1,
      ),
    });
    edges.push({
      id: `mesh-e-c0-c1-${i}`,
      from: `mesh-c0-${Math.min(i, 2)}`,
      to: id,
      isTributary: true,
      state: state === 'completed-looking' ? 'finished' : 'not-started',
    });
  }

  // Column 2: Intermediate Join & Transformation (5 nodes)
  for (let i = 0; i < 5; i++) {
    const id = `mesh-c2-${i}`;
    const state =
      i === 0 ? 'completed-looking' : i === 1 || i === 2 ? 'active-looking' : 'ready-looking';
    nodes.push({
      id,
      label: `Transform Reach ${i + 1}`,
      sublabel: `lane ${i - 2}`,
      kind: i === 2 ? 'join' : 'subagent',
      column: 2,
      lane: (i - 2) * 1.1,
      isMainFlow: i === 2,
      schedulerState: state,
      upstreamNodeIds: [`mesh-c1-${Math.min(i, 3)}`],
      downstreamNodeIds: [`mesh-c3-${Math.min(i, 3)}`],
    });
    edges.push({
      id: `mesh-e-c1-c2-${i}`,
      from: `mesh-c1-${Math.min(i, 3)}`,
      to: id,
      isTributary: i !== 2,
      state: state === 'completed-looking' ? 'finished' : state === 'active-looking' ? 'in-progress' : 'not-started',
    });
  }

  // Column 3: Processing & Auditing tier (5 nodes, including one blocked and one attention)
  for (let i = 0; i < 5; i++) {
    const id = `mesh-c3-${i}`;
    let state: DagNodeReadModel['schedulerState'] = 'queued';
    let attentionReason: string | undefined;
    let blockedByNodeIds: string[] | undefined;

    if (i === 0) {
      state = 'completed-looking';
    } else if (i === 1) {
      state = 'active-looking';
    } else if (i === 2) {
      state = 'blocked-looking';
      blockedByNodeIds = [`mesh-c2-${i}`];
      attentionReason = 'Awaiting upstream transform consensus.';
    } else if (i === 3) {
      state = 'attention';
      attentionReason = 'Tool latency threshold exceeded.';
    } else {
      state = 'ready-looking';
    }

    nodes.push({
      id,
      label: `Processor Node ${i + 1}`,
      sublabel: `cluster-worker-0${i + 1}`,
      kind: i === 3 ? 'checkpoint' : 'subagent',
      column: 3,
      lane: (i - 2) * 1.2,
      actorId: `agent-${['forge', 'atlas', 'sentinel', 'lumen', 'forge'][i]}`,
      roleId: 'software-engineer',
      toolId: `tool::exec-engine-v${i + 1}`,
      isMainFlow: false,
      schedulerState: state,
      attentionReason,
      blockedByNodeIds,
      upstreamNodeIds: [`mesh-c2-${i}`],
      downstreamNodeIds: [`mesh-c4-${Math.min(i, 3)}`],
    });
    edges.push({
      id: `mesh-e-c2-c3-${i}`,
      from: `mesh-c2-${i}`,
      to: id,
      isTributary: true,
      state: state === 'completed-looking' ? 'finished' : state === 'active-looking' ? 'in-progress' : state === 'attention' || state === 'blocked-looking' ? 'needs-attention' : 'not-started',
    });
  }

  // Column 4: Verification & Confluence (4 nodes)
  for (let i = 0; i < 4; i++) {
    const id = `mesh-c4-${i}`;
    const state = i === 0 ? 'completed-looking' : 'queued';
    nodes.push({
      id,
      label: `Verifier ${i + 1}`,
      sublabel: `Quality gate check`,
      kind: i === 1 ? 'join' : 'stage',
      column: 4,
      lane: (i - 1.5) * 1.3,
      isMainFlow: i === 1,
      schedulerState: state,
      upstreamNodeIds: [`mesh-c3-${i}`],
      downstreamNodeIds: [`mesh-c5-${Math.min(i, 2)}`],
    });
    edges.push({
      id: `mesh-e-c3-c4-${i}`,
      from: `mesh-c3-${i}`,
      to: id,
      isTributary: i !== 1,
      state: state === 'completed-looking' ? 'finished' : 'not-started',
    });
  }

  // Column 5: Terminal Confluence (3 nodes: 2 joins + final outcome)
  nodes.push({
    id: `mesh-c5-0`,
    label: 'Stage Audit Confluence',
    sublabel: 'Gather upstream outputs',
    kind: 'join',
    column: 5,
    lane: -1,
    isMainFlow: false,
    schedulerState: 'queued',
    upstreamNodeIds: ['mesh-c4-0', 'mesh-c4-1'],
    downstreamNodeIds: ['mesh-final-outcome'],
  });
  edges.push(
    { id: 'mesh-e-c4-c5-0', from: 'mesh-c4-0', to: 'mesh-c5-0', isTributary: true },
    { id: 'mesh-e-c4-c5-1', from: 'mesh-c4-1', to: 'mesh-c5-0', isTributary: true },
  );

  nodes.push({
    id: `mesh-c5-1`,
    label: 'Policy Gate Check',
    sublabel: 'Awaiting human authorization',
    kind: 'checkpoint',
    column: 5,
    lane: 1,
    isMainFlow: false,
    schedulerState: 'queued',
    upstreamNodeIds: ['mesh-c4-2', 'mesh-c4-3'],
    downstreamNodeIds: ['mesh-final-outcome'],
  });
  edges.push(
    { id: 'mesh-e-c4-c5-2', from: 'mesh-c4-2', to: 'mesh-c5-1', isTributary: true },
    { id: 'mesh-e-c4-c5-3', from: 'mesh-c4-3', to: 'mesh-c5-1', isTributary: true },
  );

  nodes.push({
    id: 'mesh-final-outcome',
    label: 'Workspace Execution Confluence',
    sublabel: 'Terminal Release State',
    kind: 'outcome',
    column: 6,
    lane: 0,
    isMainFlow: true,
    schedulerState: 'queued',
    upstreamNodeIds: ['mesh-c5-0', 'mesh-c5-1'],
    downstreamNodeIds: [],
  });
  edges.push(
    { id: 'mesh-e-c5-final-0', from: 'mesh-c5-0', to: 'mesh-final-outcome' },
    { id: 'mesh-e-c5-final-1', from: 'mesh-c5-1', to: 'mesh-final-outcome' },
  );

  return { nodes, edges };
}

const LARGE_MESH = buildLargeMeshScenario();

// ---------------------------------------------------------------------------
// 9. Disconnected Graph (Testing disconnected presentation data)
// ---------------------------------------------------------------------------
const DISCONNECTED_NODES: readonly DagNodeReadModel[] = [
  // Island cluster A
  {
    id: 'disc-a1',
    label: 'Island Alpha - Step 1',
    kind: 'stage',
    column: 0,
    lane: -1.2,
    isMainFlow: false,
    schedulerState: 'completed-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['disc-a2'],
  },
  {
    id: 'disc-a2',
    label: 'Island Alpha - Step 2',
    kind: 'stage',
    column: 1,
    lane: -1.2,
    isMainFlow: false,
    schedulerState: 'active-looking',
    upstreamNodeIds: ['disc-a1'],
    downstreamNodeIds: [],
  },
  // Island cluster B (completely disconnected from Alpha)
  {
    id: 'disc-b1',
    label: 'Island Beta - Step 1',
    kind: 'stage',
    column: 0,
    lane: 1.2,
    isMainFlow: false,
    schedulerState: 'ready-looking',
    upstreamNodeIds: [],
    downstreamNodeIds: ['disc-b2'],
  },
  {
    id: 'disc-b2',
    label: 'Island Beta - Step 2',
    kind: 'stage',
    column: 1,
    lane: 1.2,
    isMainFlow: false,
    schedulerState: 'queued',
    upstreamNodeIds: ['disc-b1'],
    downstreamNodeIds: [],
  },
];

const DISCONNECTED_EDGES: readonly DagEdgeReadModel[] = [
  { id: 'disc-e-a', from: 'disc-a1', to: 'disc-a2', isTributary: true, state: 'in-progress' },
  { id: 'disc-e-b', from: 'disc-b1', to: 'disc-b2', isTributary: true, state: 'not-started' },
];

// ---------------------------------------------------------------------------
// All Scenarios Catalog
// ---------------------------------------------------------------------------
export const MOCK_DAG_SCENARIOS: readonly DagScenarioInfo[] = [
  {
    id: 'fan-out-fan-in',
    name: 'Multi-Agent Fan-Out & Join',
    description: 'Principal execution trunk fanning out into 4 sub-agent tributaries, converging at a join.',
    nodeCount: FANOUT_NODES.length,
    edgeCount: FANOUT_EDGES.length,
  },
  {
    id: 'linear-workflow',
    name: 'Linear Sequential Pipeline',
    description: 'Direct sequential multi-stage workflow with no branching or concurrency.',
    nodeCount: LINEAR_NODES.length,
    edgeCount: LINEAR_EDGES.length,
  },
  {
    id: 'blocked-branch',
    name: 'Blocked Dependency & Checkpoint',
    description: 'Tributary blocked by missing authorization checkpoint; downstream join blocked waiting.',
    nodeCount: BLOCKED_NODES.length,
    edgeCount: BLOCKED_EDGES.length,
  },
  {
    id: 'attention-error',
    name: 'Diagnostic Error & Containment Fault',
    description: 'Tributary branch with diagnostic failure (failed_before_effect / containment_rejected).',
    nodeCount: ATTENTION_NODES.length,
    edgeCount: ATTENTION_EDGES.length,
  },
  {
    id: 'effect-ambiguous',
    name: 'effect_ambiguous (Hazardous Outcome)',
    description: 'Node linked to effect_ambiguous Result outcome with strict no-retry warnings.',
    nodeCount: AMBIGUOUS_NODES.length,
    edgeCount: AMBIGUOUS_EDGES.length,
  },
  {
    id: 'completed-historical',
    name: 'Completed Historical Path',
    description: 'Fully completed execution DAG with canonical results, timelines, and evidence attached.',
    nodeCount: HISTORICAL_NODES.length,
    edgeCount: HISTORICAL_EDGES.length,
  },
  {
    id: 'active-branch',
    name: 'Active Concurrent Branches',
    description: 'Active executing tributaries with animated flow highlights and in-progress states.',
    nodeCount: ACTIVE_NODES.length,
    edgeCount: ACTIVE_EDGES.length,
  },
  {
    id: 'large-mesh-24',
    name: 'Large 24-Node Graph Mesh',
    description: 'Complex multi-tier graph testing zoom, pan, large-scale readability, and filtering.',
    nodeCount: LARGE_MESH.nodes.length,
    edgeCount: LARGE_MESH.edges.length,
  },
  {
    id: 'disconnected-graph',
    name: 'Disconnected Sub-Flows',
    description: 'Separate isolated sub-graphs verifying presentation handling of disconnected data.',
    nodeCount: DISCONNECTED_NODES.length,
    edgeCount: DISCONNECTED_EDGES.length,
  },
  {
    id: 'stale-data',
    name: 'Stale Data State',
    description: 'Scenario with source isStale flag set to test stale data banner presentation.',
    nodeCount: FANOUT_NODES.length,
    edgeCount: FANOUT_EDGES.length,
  },
  {
    id: 'empty-graph',
    name: 'Empty Graph',
    description: 'Scenario returning 0 nodes to test the empty state presentation panel.',
    nodeCount: 0,
    edgeCount: 0,
  },
];

export function getMockDagGraph(scenarioId: string = 'fan-out-fan-in'): DagGraphReadModel | undefined {
  switch (scenarioId) {
    case 'fan-out-fan-in':
      return {
        id: 'dag-fan-out-fan-in',
        name: 'Multi-Agent Fan-Out & Join',
        scenario: 'fan-out-fan-in',
        description: 'Principal execution trunk fanning out into 4 sub-agent tributaries, converging at a join.',
        updatedLabel: 'Just now',
        isStale: false,
        nodes: FANOUT_NODES,
        edges: FANOUT_EDGES,
        schedulerSummary: computeSchedulerSummary(FANOUT_NODES),
      };

    case 'linear-workflow':
      return {
        id: 'dag-linear-workflow',
        name: 'Linear Sequential Pipeline',
        scenario: 'linear-workflow',
        description: 'Direct sequential multi-stage workflow with no branching or concurrency.',
        updatedLabel: '2m ago',
        isStale: false,
        nodes: LINEAR_NODES,
        edges: LINEAR_EDGES,
        schedulerSummary: computeSchedulerSummary(LINEAR_NODES),
      };

    case 'blocked-branch':
      return {
        id: 'dag-blocked-branch',
        name: 'Blocked Dependency & Checkpoint',
        scenario: 'blocked-branch',
        description: 'Tributary blocked by missing authorization checkpoint; downstream join blocked waiting.',
        updatedLabel: '4m ago',
        isStale: false,
        nodes: BLOCKED_NODES,
        edges: BLOCKED_EDGES,
        schedulerSummary: computeSchedulerSummary(BLOCKED_NODES),
      };

    case 'attention-error':
      return {
        id: 'dag-attention-error',
        name: 'Diagnostic Error & Containment Fault',
        scenario: 'attention-error',
        description: 'Tributary branch with diagnostic failure (failed_before_effect / containment_rejected).',
        updatedLabel: '1m ago',
        isStale: false,
        nodes: ATTENTION_NODES,
        edges: ATTENTION_EDGES,
        schedulerSummary: computeSchedulerSummary(ATTENTION_NODES),
      };

    case 'effect-ambiguous':
      return {
        id: 'dag-effect-ambiguous',
        name: 'effect_ambiguous (Hazardous Outcome)',
        scenario: 'effect-ambiguous',
        description: 'Node linked to effect_ambiguous Result outcome with strict no-retry warnings.',
        updatedLabel: '3m ago',
        isStale: false,
        nodes: AMBIGUOUS_NODES,
        edges: AMBIGUOUS_EDGES,
        schedulerSummary: computeSchedulerSummary(AMBIGUOUS_NODES),
      };

    case 'completed-historical':
      return {
        id: 'dag-completed-historical',
        name: 'Completed Historical Path',
        scenario: 'completed-historical',
        description: 'Fully completed execution DAG with canonical results, timelines, and evidence attached.',
        updatedLabel: '1h ago',
        isStale: false,
        nodes: HISTORICAL_NODES,
        edges: HISTORICAL_EDGES,
        schedulerSummary: computeSchedulerSummary(HISTORICAL_NODES),
      };

    case 'active-branch':
      return {
        id: 'dag-active-branch',
        name: 'Active Concurrent Branches',
        scenario: 'active-branch',
        description: 'Active executing tributaries with animated flow highlights and in-progress states.',
        updatedLabel: 'Streaming · 5s ago',
        isStale: false,
        nodes: ACTIVE_NODES,
        edges: ACTIVE_EDGES,
        schedulerSummary: computeSchedulerSummary(ACTIVE_NODES),
      };

    case 'large-mesh-24':
      return {
        id: 'dag-large-mesh-24',
        name: 'Large 24-Node Graph Mesh',
        scenario: 'large-mesh-24',
        description: 'Complex multi-tier graph testing zoom, pan, large-scale readability, and filtering.',
        updatedLabel: 'Just now',
        isStale: false,
        nodes: LARGE_MESH.nodes,
        edges: LARGE_MESH.edges,
        schedulerSummary: computeSchedulerSummary(LARGE_MESH.nodes),
      };

    case 'disconnected-graph':
      return {
        id: 'dag-disconnected-graph',
        name: 'Disconnected Sub-Flows',
        scenario: 'disconnected-graph',
        description: 'Separate isolated sub-graphs verifying presentation handling of disconnected data.',
        updatedLabel: '10m ago',
        isStale: false,
        nodes: DISCONNECTED_NODES,
        edges: DISCONNECTED_EDGES,
        schedulerSummary: computeSchedulerSummary(DISCONNECTED_NODES),
      };

    case 'stale-data':
      return {
        id: 'dag-stale-data',
        name: 'Stale Data State',
        scenario: 'stale-data',
        description: 'Scenario with source isStale flag set to test stale data banner presentation.',
        updatedLabel: '45m ago (stale)',
        isStale: true,
        nodes: FANOUT_NODES,
        edges: FANOUT_EDGES,
        schedulerSummary: computeSchedulerSummary(FANOUT_NODES),
      };

    case 'empty-graph':
      return {
        id: 'dag-empty-graph',
        name: 'Empty Graph',
        scenario: 'empty-graph',
        description: 'Scenario returning 0 nodes to test the empty state presentation panel.',
        updatedLabel: 'Never updated',
        isStale: false,
        nodes: [],
        edges: [],
        schedulerSummary: {
          queuedCount: 0,
          readyLookingCount: 0,
          activeLookingCount: 0,
          blockedLookingCount: 0,
          completedLookingCount: 0,
          attentionCount: 0,
          dataSourceNotice: SCHEDULER_DISCLAIMER_NOTICE,
        },
      };

    default:
      return undefined;
  }
}
