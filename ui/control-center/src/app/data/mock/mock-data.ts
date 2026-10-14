import {
  AgentExecutionResultPresentation,
  AgentExecutionResultReadModel,
  AgentSummary,
  ApprovalItem,
  EvidenceItem,
  ExecutionMode,
  PresentationState,
  RunContractView,
  RunDetail,
  RunSummary,
  TaskDetail,
  TimelineEntry,
  WorkflowStageView,
} from '../models';
import { adaptResultReadModel } from '../result-adapter';

/**
 * MOCK DATA ONLY.
 *
 * Everything here is fabricated for UI review. Identifiers are prefixed
 * `DEMO-` / `run_` so they cannot be mistaken for real repository Tasks.
 * Workflow ids, Role ids, stage ids, status values, approval levels and
 * availability states reuse existing Core vocabulary; all other shapes are
 * UI-local assumptions (see docs/core-contract-questions.md).
 */

// ---------------------------------------------------------------------------
// Workflows (mirrors workflows/*.yaml stage structure, read-only copy)
// ---------------------------------------------------------------------------

const STANDARD_CHANGE: readonly WorkflowStageView[] = [
  {
    id: 'understand',
    purpose: 'Acquire necessary context, verify task scope, and understand requirements before implementation.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'implement',
    purpose: 'Execute scoped implementation changes according to task acceptance criteria.',
    requiredRoles: ['software-engineer'],
    humanControlCheckpoint: false,
  },
  {
    id: 'validate',
    purpose: 'Execute tests, builds, and automated verification to establish evidence of correctness.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'review',
    purpose: 'Evaluate changes against acceptance criteria and verify ready state for human evaluation.',
    requiredRoles: ['reviewer'],
    humanControlCheckpoint: true,
  },
];

const SECURITY_SENSITIVE_CHANGE: readonly WorkflowStageView[] = [
  {
    id: 'understand',
    purpose: 'Analyze security posture, identify potential threats, and understand existing security boundaries.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'security-analysis',
    purpose: 'Perform deep security analysis, evaluate control impact, and identify security risks.',
    requiredRoles: ['security-reviewer'],
    humanControlCheckpoint: false,
  },
  {
    id: 'implement',
    purpose: 'Execute security controls, remediate vulnerabilities, or apply defensive measures within scope.',
    requiredRoles: ['software-engineer'],
    humanControlCheckpoint: false,
  },
  {
    id: 'validate',
    purpose: 'Execute security testing, verify defensive assertions, and run regression suites.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'review',
    purpose: 'Conduct independent security review, verify control effectiveness, and evaluate Human Control requirements.',
    requiredRoles: ['reviewer', 'security-reviewer'],
    humanControlCheckpoint: true,
  },
];

const ARCHITECTURE_CHANGE: readonly WorkflowStageView[] = [
  {
    id: 'understand',
    purpose: 'Analyze current architecture, baseline dependencies, and understand problem context.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'design',
    purpose: 'Formulate architectural approach, evaluate design alternatives, and document architectural decisions.',
    requiredRoles: ['architect'],
    humanControlCheckpoint: false,
  },
  {
    id: 'implement',
    purpose: 'Execute structural changes or specification modifications aligned with the approved design.',
    requiredRoles: ['software-engineer'],
    humanControlCheckpoint: false,
  },
  {
    id: 'validate',
    purpose: 'Validate architectural consistency, run regression checks, and verify structural integrity.',
    requiredRoles: [],
    humanControlCheckpoint: false,
  },
  {
    id: 'review',
    purpose: 'Conduct independent evaluation of architecture changes, verify documentation consistency, and evaluate Human Control requirements.',
    requiredRoles: ['reviewer', 'architect'],
    humanControlCheckpoint: true,
  },
];

const WORKFLOWS: Readonly<Record<string, readonly WorkflowStageView[]>> = {
  'standard-change': STANDARD_CHANGE,
  'security-sensitive-change': SECURITY_SENSITIVE_CHANGE,
  'architecture-change': ARCHITECTURE_CHANGE,
};

// ---------------------------------------------------------------------------
// Runs
// ---------------------------------------------------------------------------

interface RunSeed {
  readonly runId: string;
  readonly taskId: string;
  readonly workflowId: string;
  readonly stageId: string;
  readonly roleId: string;
  readonly actorId: string;
  readonly runtimeOptionId: string;
  readonly optionId: string;
  readonly resource: string;
  readonly mode: ExecutionMode;
  readonly state: PresentationState;
  readonly startedLabel: string;
}

const RUN_SEEDS: readonly RunSeed[] = [
  // DEMO-101 — standard-change, implementation underway
  {
    runId: 'run_3c81f0a7',
    taskId: 'DEMO-101',
    workflowId: 'standard-change',
    stageId: 'implement',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/diagnostics/error-reporter',
    mode: 'standard',
    state: 'in-progress',
    startedLabel: 'Today · 14:02',
  },
  // DEMO-102 — security-sensitive-change, review stage reached
  {
    runId: 'run_a41c07e2',
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'security-analysis',
    roleId: 'security-reviewer',
    actorId: 'agent-sentinel',
    runtimeOptionId: 'rt-hosted-agent',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/auth/token-refresh',
    mode: 'deep',
    state: 'finished',
    startedLabel: 'Yesterday · 16:40',
  },
  {
    runId: 'run_b9d2e5f1',
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'implement',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/auth/token-refresh',
    mode: 'deep',
    state: 'finished',
    startedLabel: 'Yesterday · 18:15',
  },
  {
    runId: 'run_e60d4b13',
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'review',
    roleId: 'reviewer',
    actorId: 'agent-lumen',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-beta-fast',
    resource: 'src/auth/token-refresh',
    mode: 'deep',
    state: 'in-progress',
    startedLabel: 'Today · 09:30',
  },
  {
    runId: 'run_f27a9c58',
    taskId: 'DEMO-102',
    workflowId: 'security-sensitive-change',
    stageId: 'review',
    roleId: 'security-reviewer',
    actorId: 'agent-sentinel',
    runtimeOptionId: 'rt-hosted-agent',
    optionId: 'opt-alpha-reasoning',
    resource: 'config/credentials-template',
    mode: 'deep',
    state: 'needs-attention',
    startedLabel: 'Today · 09:34',
  },
  // DEMO-103 — architecture-change, blocked on design checkpoint
  {
    runId: 'run_74be2d90',
    taskId: 'DEMO-103',
    workflowId: 'architecture-change',
    stageId: 'design',
    roleId: 'architect',
    actorId: 'agent-atlas',
    runtimeOptionId: 'rt-hosted-agent',
    optionId: 'opt-alpha-reasoning',
    resource: 'docs/architecture/module-boundaries',
    mode: 'deep',
    state: 'finished',
    startedLabel: 'Mon · 11:20',
  },
  {
    runId: 'run_08d5c6a4',
    taskId: 'DEMO-103',
    workflowId: 'architecture-change',
    stageId: 'implement',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-beta-fast',
    resource: 'src/modules/boundaries',
    mode: 'deep',
    state: 'needs-attention',
    startedLabel: 'Tue · 10:05',
  },
  // DEMO-104 — standard-change, completed
  {
    runId: 'run_c19e83d6',
    taskId: 'DEMO-104',
    workflowId: 'standard-change',
    stageId: 'implement',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-beta-fast',
    resource: 'docs/release/checklist',
    mode: 'lite',
    state: 'finished',
    startedLabel: 'Last week · Thu',
  },
  {
    runId: 'run_5d70b2e8',
    taskId: 'DEMO-104',
    workflowId: 'standard-change',
    stageId: 'review',
    roleId: 'reviewer',
    actorId: 'agent-lumen',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-beta-fast',
    resource: 'docs/release/checklist',
    mode: 'lite',
    state: 'finished',
    startedLabel: 'Last week · Fri',
  },
  // DEMO-107 — standard-change, failed validation evidence
  {
    runId: 'run_d82e11a9',
    taskId: 'DEMO-107',
    workflowId: 'standard-change',
    stageId: 'validate',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/io/streaming-frame-parser',
    mode: 'deep',
    state: 'needs-attention',
    startedLabel: 'Today · 11:15',
  },
  // DEMO-108 — standard-change, multi-agent branch with long labels and paths
  {
    runId: 'run_m1a2b3c4',
    taskId: 'DEMO-108',
    workflowId: 'standard-change',
    stageId: 'implement',
    roleId: 'software-engineer',
    actorId: 'agent-forge',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/cluster/partition-lease-fencing-coordinator',
    mode: 'critical',
    state: 'in-progress',
    startedLabel: 'Today · 13:45',
  },
  {
    runId: 'run_m2b3c4d5',
    taskId: 'DEMO-108',
    workflowId: 'standard-change',
    stageId: 'implement',
    roleId: 'reviewer',
    actorId: 'agent-lumen',
    runtimeOptionId: 'rt-local-cli',
    optionId: 'opt-beta-fast',
    resource: 'config/policies/distributed-partition-fencing-rules',
    mode: 'critical',
    state: 'in-progress',
    startedLabel: 'Today · 13:50',
  },
  {
    runId: 'run_m3c4d5e6',
    taskId: 'DEMO-108',
    workflowId: 'standard-change',
    stageId: 'implement',
    roleId: 'security-reviewer',
    actorId: 'agent-sentinel',
    runtimeOptionId: 'rt-hosted-agent',
    optionId: 'opt-alpha-reasoning',
    resource: 'src/cluster/epoch-attestation-verifier',
    mode: 'critical',
    state: 'finished',
    startedLabel: 'Today · 13:40',
  },
];

function toContract(seed: RunSeed): RunContractView {
  return {
    taskId: seed.taskId,
    workflowId: seed.workflowId,
    stageId: seed.stageId,
    roleId: seed.roleId,
    actorId: seed.actorId,
    runtimeOptionId: seed.runtimeOptionId,
    optionId: seed.optionId,
    environmentId: 'env-workspace',
    operationId: 'repository_file_read',
    resource: seed.resource,
    executionMode: seed.mode,
  };
}

export const MOCK_RUNS: readonly RunSummary[] = RUN_SEEDS.map((seed) => ({
  runId: seed.runId,
  contract: toContract(seed),
  presentationState: seed.state,
  startedLabel: seed.startedLabel,
}));

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

export const MOCK_TASK_DETAILS: readonly TaskDetail[] = [
  {
    id: 'DEMO-101',
    title: 'Introduce structured error reporting',
    type: 'implementation',
    status: 'in_progress',
    risk: 'medium',
    complexity: 'medium',
    executionMode: 'standard',
    workflowId: 'standard-change',
    approvalLevel: 'review',
    updatedLabel: 'Today · 14:02',
    objective:
      'Replace ad-hoc error strings with a single structured error report shape consumed by diagnostics output.',
    scopeIncluded: ['Error report type and factory', 'Diagnostics output formatting', 'Unit tests for the new shape'],
    scopeExcluded: ['Transport or persistence of error reports', 'Localization of messages'],
    dependencies: [],
    qualityGates: ['unit-tests', 'independent_review'],
    runIds: ['run_3c81f0a7'],
    stages: STANDARD_CHANGE,
  },
  {
    id: 'DEMO-102',
    title: 'Rework authentication token refresh',
    type: 'implementation',
    status: 'in_progress',
    risk: 'high',
    complexity: 'high',
    executionMode: 'deep',
    workflowId: 'security-sensitive-change',
    approvalLevel: 'explicit',
    updatedLabel: 'Today · 09:34',
    objective:
      'Harden the token refresh path so expired credentials are rejected deterministically and never logged.',
    scopeIncluded: ['Refresh decision logic', 'Credential redaction in diagnostics', 'Regression suite for expiry edge cases'],
    scopeExcluded: ['Identity provider configuration', 'Session storage migration'],
    dependencies: ['DEMO-101'],
    qualityGates: ['unit-tests', 'independent_review'],
    runIds: ['run_a41c07e2', 'run_b9d2e5f1', 'run_e60d4b13', 'run_f27a9c58'],
    stages: SECURITY_SENSITIVE_CHANGE,
  },
  {
    id: 'DEMO-103',
    title: 'Restructure module boundaries',
    type: 'architecture',
    status: 'blocked',
    risk: 'high',
    complexity: 'high',
    executionMode: 'deep',
    workflowId: 'architecture-change',
    approvalLevel: 'explicit',
    updatedLabel: 'Tue · 10:05',
    objective: 'Define and apply explicit dependency boundaries between application modules.',
    scopeIncluded: ['Boundary design document', 'Module entry-point restructuring'],
    scopeExcluded: ['Public API renames', 'Build tooling changes'],
    dependencies: [],
    qualityGates: ['documentation_consistency', 'independent_review'],
    runIds: ['run_74be2d90', 'run_08d5c6a4'],
    stages: ARCHITECTURE_CHANGE,
    blockedReason:
      'Design outcome requires explicit Human approval before implementation may continue.',
  },
  {
    id: 'DEMO-104',
    title: 'Document release checklist',
    type: 'documentation',
    status: 'completed',
    risk: 'low',
    complexity: 'low',
    executionMode: 'lite',
    workflowId: 'standard-change',
    approvalLevel: 'review',
    updatedLabel: 'Last week · Fri',
    objective: 'Capture the release steps in one reviewed checklist document.',
    scopeIncluded: ['Release checklist document'],
    scopeExcluded: ['Automation of the release process'],
    dependencies: [],
    qualityGates: ['documentation_consistency'],
    runIds: ['run_c19e83d6', 'run_5d70b2e8'],
    stages: STANDARD_CHANGE,
  },
  {
    id: 'DEMO-105',
    title: 'Migrate configuration loader',
    type: 'migration',
    status: 'planned',
    risk: 'medium',
    complexity: 'medium',
    executionMode: 'standard',
    workflowId: 'standard-change',
    approvalLevel: 'review',
    updatedLabel: 'Mon · 08:00',
    objective: 'Move configuration loading to the new typed loader without behavior change.',
    scopeIncluded: ['Loader replacement', 'Compatibility tests'],
    scopeExcluded: ['New configuration keys'],
    dependencies: ['DEMO-103'],
    qualityGates: ['unit-tests'],
    runIds: [],
    stages: STANDARD_CHANGE,
  },
  {
    id: 'DEMO-106',
    title: 'Prototype alternative export format',
    type: 'investigation',
    status: 'cancelled',
    risk: 'low',
    complexity: 'low',
    executionMode: 'lite',
    workflowId: 'standard-change',
    approvalLevel: 'none',
    updatedLabel: 'Last month',
    objective: 'Explore whether a compact export format is worth supporting.',
    scopeIncluded: ['Throwaway prototype'],
    scopeExcluded: ['Production integration'],
    dependencies: [],
    qualityGates: [],
    runIds: [],
    stages: STANDARD_CHANGE,
  },
  {
    id: 'DEMO-107',
    title: 'Harden buffer boundary validation in streaming frame parser',
    type: 'implementation',
    status: 'in_progress',
    risk: 'high',
    complexity: 'high',
    executionMode: 'deep',
    workflowId: 'standard-change',
    approvalLevel: 'explicit',
    updatedLabel: 'Today · 11:20',
    objective:
      'Enforce strict bounds checking during streaming frame deserialization to trap malformed frames before buffer allocation.',
    scopeIncluded: ['Frame length validation', 'Streaming boundary assertions', 'Fuzz regression suite'],
    scopeExcluded: ['Transport buffer reallocation'],
    dependencies: ['DEMO-101'],
    qualityGates: ['unit-tests', 'independent_review'],
    runIds: ['run_d82e11a9'],
    stages: STANDARD_CHANGE,
  },
  {
    id: 'DEMO-108',
    title:
      'Implement distributed partition lease fencing and epoch attestation validation across isolated cluster nodes',
    type: 'architecture',
    status: 'in_progress',
    risk: 'critical',
    complexity: 'critical',
    executionMode: 'critical',
    workflowId: 'standard-change',
    approvalLevel: 'protected',
    updatedLabel: 'Today · 13:50',
    objective:
      'Guarantee that partitioned nodes in a multi-region deployment cannot acquire or extend execution leases once epoch fencing has committed, validating mutual exclusion across divergent network partitions.',
    scopeIncluded: [
      'Epoch fencing contract assertions',
      'Cluster partition simulation harness',
      'Attestation token verification',
      'Telemetry audit trail',
    ],
    scopeExcluded: ['Physical hardware watchdog integration', 'Legacy consensus migration'],
    dependencies: ['DEMO-102', 'DEMO-103'],
    qualityGates: ['unit-tests', 'documentation_consistency', 'independent_review'],
    runIds: ['run_m1a2b3c4', 'run_m2b3c4d5', 'run_m3c4d5e6'],
    stages: STANDARD_CHANGE,
  },
];

// ---------------------------------------------------------------------------
// Agents (Actors)
// ---------------------------------------------------------------------------

export const MOCK_AGENTS: readonly AgentSummary[] = [
  {
    actorId: 'agent-forge',
    name: 'Forge',
    kind: 'agent',
    roleIds: ['software-engineer'],
    availability: 'available',
    runtimeOptionIds: ['rt-local-cli', 'rt-hosted-agent'],
    assignments: [
      { taskId: 'DEMO-101', stageId: 'implement', roleId: 'software-engineer' },
      { taskId: 'DEMO-102', stageId: 'implement', roleId: 'software-engineer' },
      { taskId: 'DEMO-103', stageId: 'implement', roleId: 'software-engineer' },
      { taskId: 'DEMO-107', stageId: 'validate', roleId: 'software-engineer' },
      { taskId: 'DEMO-108', stageId: 'implement', roleId: 'software-engineer' },
    ],
  },
  {
    actorId: 'agent-atlas',
    name: 'Atlas',
    kind: 'agent',
    roleIds: ['architect'],
    availability: 'available',
    runtimeOptionIds: ['rt-hosted-agent'],
    assignments: [{ taskId: 'DEMO-103', stageId: 'design', roleId: 'architect' }],
  },
  {
    actorId: 'agent-lumen',
    name: 'Lumen',
    kind: 'agent',
    roleIds: ['reviewer', 'documentation-specialist'],
    availability: 'available',
    runtimeOptionIds: ['rt-local-cli'],
    assignments: [
      { taskId: 'DEMO-102', stageId: 'review', roleId: 'reviewer' },
      { taskId: 'DEMO-108', stageId: 'implement', roleId: 'reviewer' },
    ],
  },
  {
    actorId: 'agent-sentinel',
    name: 'Sentinel',
    kind: 'agent',
    roleIds: ['security-reviewer'],
    availability: 'unknown',
    runtimeOptionIds: ['rt-hosted-agent'],
    assignments: [
      { taskId: 'DEMO-102', stageId: 'security-analysis', roleId: 'security-reviewer' },
      { taskId: 'DEMO-102', stageId: 'review', roleId: 'security-reviewer' },
      { taskId: 'DEMO-108', stageId: 'implement', roleId: 'security-reviewer' },
    ],
  },
  {
    actorId: 'agent-quill',
    name: 'Quill',
    kind: 'agent',
    roleIds: ['documentation-specialist'],
    availability: 'unavailable',
    runtimeOptionIds: ['rt-local-cli'],
    assignments: [],
  },
  {
    actorId: 'human-maya',
    name: 'Maya',
    kind: 'human',
    roleIds: ['architect', 'reviewer', 'security-reviewer'],
    availability: 'available',
    runtimeOptionIds: [],
    assignments: [],
  },
  {
    actorId: 'human-omar',
    name: 'Omar',
    kind: 'human',
    roleIds: ['reviewer'],
    availability: 'unknown',
    runtimeOptionIds: [],
    assignments: [],
  },
];

// ---------------------------------------------------------------------------
// Approvals
// ---------------------------------------------------------------------------

export const MOCK_APPROVALS: readonly ApprovalItem[] = [
  {
    id: 'apr-1001',
    taskId: 'DEMO-102',
    runId: 'run_f27a9c58',
    stageId: 'review',
    level: 'explicit',
    action: 'repository_file_read of config/credentials-template via rt-hosted-agent and opt-alpha-reasoning',
    state: 'awaiting',
    requestedLabel: 'Today · 09:34',
  },
  {
    id: 'apr-1002',
    taskId: 'DEMO-103',
    stageId: 'design',
    level: 'explicit',
    action: 'Approve the boundary design before the implement stage may proceed',
    state: 'awaiting',
    requestedLabel: 'Tue · 10:05',
  },
  {
    id: 'apr-1003',
    taskId: 'DEMO-101',
    runId: 'run_3c81f0a7',
    stageId: 'implement',
    level: 'review',
    action: 'repository_file_read of src/diagnostics/error-reporter via rt-local-cli and opt-alpha-reasoning',
    state: 'granted',
    authorityId: 'human-maya',
    requestedLabel: 'Today · 14:00',
  },
  {
    id: 'apr-1004',
    taskId: 'DEMO-104',
    runId: 'run_5d70b2e8',
    stageId: 'review',
    level: 'review',
    action: 'repository_file_read of docs/release/checklist via rt-local-cli and opt-beta-fast',
    state: 'granted',
    authorityId: 'policy-docs-default',
    requestedLabel: 'Last week · Fri',
  },
  {
    id: 'apr-1005',
    taskId: 'DEMO-102',
    runId: 'run_a41c07e2',
    stageId: 'security-analysis',
    level: 'protected',
    action: 'repository_file_read of config/production-secrets via rt-hosted-agent and opt-alpha-reasoning',
    state: 'denied',
    authorityId: 'human-maya',
    requestedLabel: 'Yesterday · 16:42',
  },
  {
    id: 'apr-1006',
    taskId: 'DEMO-108',
    runId: 'run_m1a2b3c4',
    stageId: 'implement',
    level: 'protected',
    action:
      'repository_file_read of config/policies/distributed-partition-fencing-rules via rt-local-cli and opt-alpha-reasoning',
    state: 'awaiting',
    requestedLabel: 'Today · 13:45',
  },
];

// ---------------------------------------------------------------------------
// Per-run presentation content (timeline / evidence / result)
// ---------------------------------------------------------------------------

function buildTimeline(seed: RunSeed): TimelineEntry[] {
  const base = (suffix: string) => `${seed.runId}-${suffix}`;
  const entries: TimelineEntry[] = [
    {
      id: base('t1'),
      atLabel: seed.startedLabel,
      kind: 'stage',
      title: `Stage "${seed.stageId}" entered`,
      detail: `${seed.roleId} responsibility bound to ${seed.actorId}.`,
      state: 'finished',
      stageId: seed.stageId,
      actorId: seed.actorId,
    },
    {
      id: base('t2'),
      atLabel: seed.startedLabel,
      kind: 'approval',
      title: 'Authorization evidence recorded',
      detail: `Exact action: repository_file_read of ${seed.resource}.`,
      state: seed.state === 'needs-attention' ? 'needs-attention' : 'finished',
      actorId: seed.actorId,
    },
  ];

  if (seed.runId === 'run_d82e11a9') {
    entries.push({
      id: base('t3'),
      atLabel: seed.startedLabel,
      kind: 'quality-gate',
      title: 'Validation failed',
      detail: 'unit-tests reported 1 failure; guard page offset exception not trapped.',
      state: 'needs-attention',
      stageId: seed.stageId,
    });
    return entries;
  }

  if (seed.state === 'needs-attention') {
    entries.push({
      id: base('t3'),
      atLabel: 'Awaiting',
      kind: 'approval',
      title: 'Waiting on explicit Human approval',
      detail: 'No grant evidence has been supplied for this exact action, so authorization is unproven.',
      state: 'needs-attention',
    });
    return entries;
  }

  entries.push({
    id: base('t3'),
    atLabel: seed.startedLabel,
    kind: 'agent',
    title: `${seed.actorId} working`,
    detail: 'Reading the resource and preparing findings.',
    state: seed.state === 'in-progress' ? 'in-progress' : 'finished',
    actorId: seed.actorId,
  });

  if (seed.state === 'finished') {
    entries.push(
      {
        id: base('t4'),
        atLabel: seed.startedLabel,
        kind: 'quality-gate',
        title: 'Validation reported',
        detail: 'unit-tests passed; documentation consistency not applicable.',
        state: 'finished',
      },
      {
        id: base('t5'),
        atLabel: seed.startedLabel,
        kind: 'note',
        title: 'Work reported complete',
        detail: 'Result is presented provisionally; Human review is still required.',
        state: 'finished',
        actorId: seed.actorId,
      },
    );
  }
  return entries;
}

function buildEvidence(seed: RunSeed): EvidenceItem[] {
  const id = (suffix: string) => `${seed.runId}-${suffix}`;

  if (seed.runId === 'run_d82e11a9') {
    return [
      {
        id: id('e1'),
        kind: 'command-output',
        title: 'unit-tests',
        summary: '1 test failed out of 14 during buffer boundary assertion checks.',
        outcome: 'failed',
        source: 'python -B -m unittest discover -s tests -p "test_frame_parser.py"',
        lines: [
          'test_frame_header_valid ... ok',
          'test_zero_length_frame ... ok',
          'FAIL: test_frame_overflow_boundary (test_frame_parser.TestFrameParser)',
          'Traceback (most recent call last):',
          '  File "tests/test_frame_parser.py", line 42, in test_frame_overflow_boundary',
          '    self.assertRaises(GuardPageException, parse_frame, payload)',
          'AssertionError: GuardPageException not raised when buffer offset exceeded 4096 bytes',
          '----------------------------------------',
          'Ran 14 tests in 0.112s — FAILED (failures=1)',
        ],
      },
      {
        id: id('e2'),
        kind: 'quality-gate',
        title: 'documentation_consistency',
        summary: 'Skipped pending resolution of failing validation test.',
        outcome: 'skipped',
        source: 'quality-gates/documentation-consistency',
      },
      {
        id: id('e3'),
        kind: 'review-note',
        title: 'Reviewer note',
        summary: 'Independent review cannot proceed while validation has failing checks.',
        outcome: 'unverified',
        source: 'agent-sentinel',
      },
    ];
  }

  if (seed.state === 'needs-attention') {
    return [
      {
        id: id('e1'),
        kind: 'authorization',
        title: 'Authorization evidence',
        summary:
          'No granted or denied evidence supplied for this exact action. Authorization is unproven, not denied.',
        outcome: 'unverified',
        source: `${seed.actorId} · ${seed.runtimeOptionId}`,
      },
      {
        id: id('e2'),
        kind: 'quality-gate',
        title: 'documentation_consistency',
        summary: 'Gate could not be evaluated yet because the stage is waiting on approval.',
        outcome: 'skipped',
        source: 'quality-gates/documentation-consistency',
      },
    ];
  }

  const pending = seed.state === 'in-progress';
  return [
    {
      id: id('e1'),
      kind: 'command-output',
      title: 'unit-tests',
      summary: pending ? 'Not yet executed for this run.' : 'All discovered tests passed.',
      outcome: pending ? 'unverified' : 'passed',
      source: 'python -B -m unittest discover -s tests',
      lines: pending
        ? undefined
        : [
            'test_error_report_shape ... ok',
            'test_redaction_never_logs_token ... ok',
            'test_expiry_edge_cases ... ok',
            '----------------------------------------',
            'Ran 3 tests in 0.041s — OK',
          ],
    },
    {
      id: id('e2'),
      kind: 'diff-summary',
      title: 'Change summary',
      summary: pending ? 'Partial changes reported so far.' : 'Changes confined to the declared scope.',
      outcome: pending ? 'unverified' : 'passed',
      source: seed.resource,
      lines: ['M  ' + seed.resource + '/index', 'A  ' + seed.resource + '/index.spec', '2 files changed'],
    },
    {
      id: id('e3'),
      kind: 'review-note',
      title: 'Reviewer note',
      summary: pending
        ? 'No review has been recorded yet.'
        : 'Implementer is not the sole approving authority; independent review requested.',
      outcome: pending ? 'unverified' : 'passed',
      source: seed.actorId,
    },
  ];
}

const MOCK_RESULT_READ_MODELS = new Map<string, AgentExecutionResultReadModel>([
  [
    'run_c19e83d6',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_c19e_83d6_001',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_9a8b7c6d',
        executorInstanceId: 'exec_node_worker_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Last week · Thu 15:30',
        timeKey: 1728564600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 784,
        isText: true,
        isTruncated: false,
        previewByteCount: 784,
        textPreview: `# Release Checklist — Foundation Verification

1. [x] Pre-flight authentication & credential checks passed
2. [x] Architectural boundaries confirmed in core-precedence.md
3. [x] Dependency license and integrity audit completed
4. [x] Quality gates evaluated:
   - unit-tests: PASS (73 passed)
   - documentation-consistency: PASS
   - independent-review: PENDING
5. [x] Clean worktree verification completed`,
      },
      diagnostic: null,
    },
  ],
  [
    'run_5d70b2e8',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'policy',
        issuerId: 'policy-docs-default',
        grantId: 'grnt_5d70_b2e8_002',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_4d3e2f1a',
        executorInstanceId: 'exec_node_worker_02',
        leaseGeneration: 1,
        entryTimeLabel: 'Last week · Fri 16:45',
        timeKey: 1728655500,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 34816,
        isText: true,
        isTruncated: true,
        previewByteCount: 1024,
        textPreview: `# Comprehensive System Verification Audit Log
Generated by: agent-lumen
Target: docs/release/checklist
Execution Run: run_5d70b2e8
Audit Timestamp: 2026-10-09T16:45:00Z

[0001] AUDIT_START: Initiating repository tree scan
[0002] CHECKPOINT_01: Validating file mode permissions: 0644 (OK)
[0003] CHECKPOINT_02: Inspecting UTF-8 byte order mark: None present (OK)
[0004] CHECKPOINT_03: Line endings normalized: LF only, no CRLF (OK)
[0005] SCAN_ENTRY: Evaluating section headers against canonical markdown spec
[0006] SCAN_ENTRY: Header depth hierarchy: 1 -> 2 -> 3 (Consecutive, OK)
[0007] LINK_VALIDATION: Resolving relative file anchors:
       - core/principles.md -> FOUND (resolved at rev 55e8001)
       - core/terminology.md -> FOUND (resolved at rev 55e8001)
       - core/precedence.md -> FOUND (resolved at rev 55e8001)
[0008] CROSS_REF_CHECK: Reviewing referenced identifiers:
       - SCRUM-17: Foundation implementation (CLOSED)
       - SCRUM-80: UX Hardening (CLOSED)
       - ITRU-060: Result Specification (CLOSED)
[0009] VERIFICATION_MATRIX:
       - Gate unit-tests: 73 passed, 0 failed
       - Static type check: PASS (no emitted errors)
       - Accessibility review: WCAG 2.1 AA compliant`,
      },
      diagnostic: null,
    },
  ],
  [
    'run_74be2d90',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_74be_2d90_003',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_1b2c3d4e',
        executorInstanceId: 'exec_node_worker_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Mon · 11:20',
        timeKey: 1728897600,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 4096,
        isText: false,
        isTruncated: false,
        previewByteCount: 4096,
        bytesSampleHex: `00000000  7f 45 4c 46 02 01 01 00  00 00 00 00 00 00 00 00  |.ELF............|
00000010  03 00 3e 00 01 00 00 00  a0 1a 00 00 00 00 00 00  |..>.............|
00000020  40 00 00 00 00 00 00 00  18 3c 00 00 00 00 00 00  |@........<......|
00000030  00 00 00 00 40 00 38 00  0b 00 40 00 1f 00 1e 00  |....@.8...@.....|
00000040  06 00 00 00 04 00 00 00  40 00 00 00 00 00 00 00  |........@.......|
00000050  40 00 00 00 00 00 00 00  40 00 00 00 00 00 00 00  |@.......@.......|
00000060  68 02 00 00 00 00 00 00  68 02 00 00 00 00 00 00  |h.......h.......|
00000070  08 00 00 00 00 00 00 00  03 00 00 00 04 00 00 00  |................|`,
      },
      diagnostic: null,
    },
  ],
  [
    'run_m3c4d5e6',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'policy',
        issuerId: 'policy-test-runner',
        grantId: 'grnt_m3c4_d5e6_004',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_6f7e8d9c',
        executorInstanceId: 'exec_node_worker_03',
        leaseGeneration: 1,
        entryTimeLabel: 'Today · 13:40',
        timeKey: 1728983700,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'failed_before_effect',
      payload: null,
      diagnostic: {
        code: 'containment_rejected',
      },
    },
  ],
  [
    'run_a41c07e2',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_a41c_07e2_005',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_3a4b5c6d',
        executorInstanceId: 'exec_node_worker_02',
        leaseGeneration: 1,
        entryTimeLabel: 'Yesterday · 16:40',
        timeKey: 1728916800,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'effect_ambiguous',
      payload: null,
      diagnostic: {
        code: 'effect_ambiguous',
      },
    },
  ],
  [
    'run_b9d2e5f1',
    {
      derivedIdentity: {
        ledgerInstanceId: 'ledg_inst_482a9f10',
        authorizationDomainId: 'auth_dom_orchestra_core',
        issuerKind: 'human',
        issuerId: 'maya',
        grantId: 'grnt_b9d2_e5f1_006',
      },
      ledgerIdentity: {
        domainId: 'auth_dom_orchestra_core',
        ledgerInstanceId: 'ledg_inst_482a9f10',
        domainGeneration: 1,
      },
      executionEntry: {
        claimId: 'clm_7c8d9e0f',
        executorInstanceId: 'exec_node_worker_01',
        leaseGeneration: 1,
        entryTimeLabel: 'Yesterday · 18:15',
        timeKey: 1728922500,
      },
      toolBinding: {
        toolIdentity: 'tool::itru-native-repository-file-read::v1',
        configuredRoute: 'native::posix_read_direct',
      },
      outcome: 'succeeded',
      payload: {
        byteCount: 1240,
        isText: true,
        isTruncated: false,
        previewByteCount: 1240,
        textPreview: `export interface TokenRefreshConfig {
  readonly endpoint: string;
  readonly timeoutMs: number;
  readonly maxRetries: number;
}

export function validateRefreshToken(token: string): boolean {
  if (!token || token.length < 32) {
    return false;
  }
  return token.startsWith('itru_rt_');
}`,
      },
      diagnostic: null,
    },
  ],
]);

function buildResult(seed: RunSeed): AgentExecutionResultPresentation | null {
  if (seed.state !== 'finished') {
    return null;
  }
  const readModel = MOCK_RESULT_READ_MODELS.get(seed.runId);
  return adaptResultReadModel(readModel);
}

const SEED_BY_ID = new Map(RUN_SEEDS.map((seed) => [seed.runId, seed] as const));

/** Assembles the full {@link RunDetail} for a mock Run, or `undefined` when unknown. */
export function buildRunDetail(runId: string): RunDetail | undefined {
  const seed = SEED_BY_ID.get(runId);
  const summary = MOCK_RUNS.find((run) => run.runId === runId);
  if (!seed || !summary) {
    return undefined;
  }
  const task = MOCK_TASK_DETAILS.find((candidate) => candidate.id === seed.taskId);
  return {
    ...summary,
    taskTitle: task?.title ?? seed.taskId,
    stages: WORKFLOWS[seed.workflowId] ?? [],
    taskRuns: MOCK_RUNS.filter((run) => run.contract.taskId === seed.taskId),
    timeline: buildTimeline(seed),
    evidence: buildEvidence(seed),
    result: buildResult(seed),
  };
}
