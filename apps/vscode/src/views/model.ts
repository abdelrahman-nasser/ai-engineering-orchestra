import type {
  ArtifactDescriptor,
  ProjectSnapshotResult,
  TaskDetailResult,
  TaskSummary,
} from "../coreClient/protocol";
import type { CodexMonitorSnapshot } from "../monitoring/codex";

export interface UiArtifact {
  id: string;
  label: string;
  state: ArtifactDescriptor["state"];
}

export interface UiTask {
  id: string;
  title: string;
  type: string;
  status: string;
  workflow: string;
  workflowResolution: string;
  schemaStatus: string;
  artifactHealth: "complete" | "incomplete";
}

export interface UiWorkflowStage {
  id: string;
  purpose: string;
  checkpoint: boolean;
  gates: string[];
  roles: Array<{
    id: string;
    name: string;
    purpose: string;
    capabilities: string[];
  }>;
}

export interface ControlCenterState {
  trusted: boolean;
  platformSupported: boolean;
  project: {
    state: "none" | "managed" | "unmanaged" | "invalid" | "error";
    workspaceLabel: string;
    id: string;
    name: string;
    message: string;
  };
  core: {
    state: "unconfigured" | "connected" | "restricted" | "missing" | "incompatible" | "error";
    version: string;
    message: string;
  };
  snapshotAt: string;
  filters: {
    status: string | null;
    workflow: string | null;
    statuses: string[];
    workflows: string[];
  };
  tasks: UiTask[];
  selectedTask: null | {
    id: string;
    title: string;
    status: string;
    risk: string;
    complexity: string;
    executionMode: string;
    qualityGates: string[];
    artifacts: UiArtifact[];
  };
  workflow: null | {
    id: string;
    name: string;
    label: "Workflow definition — not current execution progress";
    stages: UiWorkflowStage[];
  };
  anomalies: string[];
  monitoring: CodexMonitorSnapshot;
  busy: boolean;
  notice: string;
}

export const EMPTY_MONITORING: CodexMonitorSnapshot = {
  state: "not_configured",
  listener: "stopped",
  setup: "not_configured",
  source: "codex.lifecycle-hooks/v1",
  rootFingerprint: "",
  events: [],
  sessions: [],
};

export function initialState(): ControlCenterState {
  return {
    trusted: false,
    platformSupported: false,
    project: {
      state: "none",
      workspaceLabel: "No project selected",
      id: "",
      name: "",
      message: "Open a local folder or select one workspace folder.",
    },
    core: {
      state: "unconfigured",
      version: "",
      message: "Select a trusted installed Python/Core environment.",
    },
    snapshotAt: "",
    filters: { status: null, workflow: null, statuses: [], workflows: [] },
    tasks: [],
    selectedTask: null,
    workflow: null,
    anomalies: [],
    monitoring: EMPTY_MONITORING,
    busy: false,
    notice: "",
  };
}

export function resetProjectScopeData(state: ControlCenterState): void {
  state.project.id = "";
  state.project.name = "";
  state.core = {
    state: "unconfigured",
    version: "",
    message: "Select a trusted installed Python/Core environment.",
  };
  state.snapshotAt = "";
  state.filters = { status: null, workflow: null, statuses: [], workflows: [] };
  state.tasks = [];
  state.selectedTask = null;
  state.workflow = null;
  state.anomalies = [];
}

function artifactComplete(task: TaskSummary): boolean {
  return Object.values(task.artifact_health).every(Boolean);
}

export function taskForUi(task: TaskSummary): UiTask {
  return {
    id: task.id,
    title: task.title,
    type: task.type,
    status: task.status,
    workflow: task.workflow ?? "Not declared",
    workflowResolution: task.workflow_resolution,
    schemaStatus: task.schema_status,
    artifactHealth: artifactComplete(task) ? "complete" : "incomplete",
  };
}

export function applySnapshot(state: ControlCenterState, snapshot: ProjectSnapshotResult, coreVersion: string): void {
  state.project.state = snapshot.project.state === "error" ? "error" : snapshot.project.state;
  state.project.id = snapshot.project.id ?? "";
  state.project.name = snapshot.project.name ?? "";
  state.project.message = snapshot.validation.status === "PASS"
    ? "Structural snapshot loaded from the selected project."
    : `Structural findings: ${snapshot.validation.status}.`;
  state.core = { state: "connected", version: coreVersion, message: "Installed Core protocol connected." };
  state.snapshotAt = snapshot.snapshot_at;
  state.tasks = snapshot.tasks.map(taskForUi);
  state.filters.statuses = [...snapshot.filters.statuses];
  state.filters.workflows = [...snapshot.filters.workflows];
  state.anomalies = [
    ...snapshot.anomalies.map((item) => `${item.code}: ${item.message}`),
    ...snapshot.validation.findings.map((item) => `${item.status}: ${item.message}`),
  ];
}

export function applyTaskDetail(state: ControlCenterState, detail: TaskDetailResult): UiArtifact[] {
  const artifacts = detail.artifacts.map((artifact) => ({
    id: artifact.artifact_id,
    label: artifact.label,
    state: artifact.state,
  }));
  state.selectedTask = {
    id: detail.task.id,
    title: detail.task.title,
    status: detail.task.status,
    risk: `${detail.effective.risk.value ?? "not reported"} (${detail.effective.risk.source})`,
    complexity: `${detail.effective.complexity.value ?? "not reported"} (${detail.effective.complexity.source})`,
    executionMode: `${detail.effective.execution_mode.value ?? "not reported"} (${detail.effective.execution_mode.source})`,
    qualityGates: [...detail.effective.quality_gates],
    artifacts,
  };
  state.workflow = detail.workflow === null ? null : {
    id: detail.workflow.id,
    name: detail.workflow.name,
    label: "Workflow definition — not current execution progress",
    stages: detail.workflow.stages.map((stage) => ({
      id: stage.id,
      purpose: stage.purpose,
      checkpoint: stage.human_control_checkpoint,
      gates: [...stage.required_quality_gates],
      roles: stage.required_roles.map((role) => ({
        id: role.id,
        name: role.name,
        purpose: role.purpose,
        capabilities: [...role.required_capabilities],
      })),
    })),
  };
  return artifacts;
}
