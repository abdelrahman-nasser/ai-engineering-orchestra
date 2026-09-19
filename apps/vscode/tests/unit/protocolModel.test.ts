import assert from "node:assert/strict";
import test from "node:test";

import {
  IDE_PROTOCOL,
  parseBridgeResponse,
  type ProjectSnapshotResult,
  type TaskDetailResult,
  type TaskSummary,
} from "../../src/coreClient/protocol";
import {
  applySnapshot,
  applyTaskDetail,
  initialState,
  resetProjectScopeData,
  taskForUi,
} from "../../src/views/model";

const completeTask: TaskSummary = {
  resource_id: "task-opaque",
  id: "SYN-001",
  title: "Hostile <img src=x onerror=alert(1)>",
  type: "implementation",
  status: "in_progress",
  workflow: "standard-change",
  workflow_resolution: "RESOLVED",
  schema_status: "VALID",
  artifact_health: {
    task_yaml: true,
    context_md: true,
    acceptance_criteria_md: true,
    review_md: true,
  },
};

const emptySnapshot: ProjectSnapshotResult = {
  project: { state: "managed", id: "synthetic", name: "Synthetic fixture" },
  snapshot_at: "2026-09-19T00:00:00Z",
  tasks: [],
  anomalies: [],
  filters: { statuses: [], workflows: [] },
  validation: { status: "PASS", findings: [] },
};

const completeDetail: TaskDetailResult = {
  task: completeTask,
  effective: {
    risk: { value: "medium", source: "Task" },
    complexity: { value: null, source: "Project" },
    execution_mode: { value: "standard", source: "Task" },
    quality_gates: ["independent_review"],
    human_control: { final_review_required: { value: true, source: "Task" } },
  },
  artifacts: [{
    artifact_id: "artifact-opaque",
    label: "task.yaml",
    state: "present",
    relative_path: "governance/tasks/SYN-001/task.yaml",
  }],
  workflow: {
    id: "standard-change",
    name: "Standard Change",
    definition_not_execution: true,
    stages: [{
      id: "review",
      purpose: "Review the declared change.",
      human_control_checkpoint: true,
      required_quality_gates: ["independent_review"],
      required_roles: [{
        id: "reviewer",
        name: "Reviewer",
        purpose: "Review",
        required_capabilities: ["review"],
      }],
    }],
  },
};

test("bridge parser accepts only a closed versioned envelope", () => {
  const response = {
    protocol: IDE_PROTOCOL,
    request_id: "request-1",
    ok: true,
    meta: { package_version: "0.1.0", package_origin: "C:\\Core" },
    result: emptySnapshot,
    diagnostics: [],
  };
  assert.equal(parseBridgeResponse(JSON.stringify(response)).ok, true);
  assert.throws(
    () => parseBridgeResponse(JSON.stringify({ ...response, surprise: true })),
    /unexpected fields/u,
  );
  assert.throws(
    () => parseBridgeResponse(JSON.stringify({ ...response, protocol: "aio.ide/2" })),
    /incompatible envelope/u,
  );
  assert.throws(() => parseBridgeResponse("{} trailing"), /invalid JSON/u);
});

test("bridge parser preserves version metadata for the host compatibility check", () => {
  const success = {
    protocol: IDE_PROTOCOL,
    request_id: "request-1",
    ok: true,
    meta: { package_version: "0.2.0", package_origin: "C:\\Core" },
    result: emptySnapshot,
    diagnostics: [],
  };
  const failure = {
    protocol: IDE_PROTOCOL,
    request_id: "request-2",
    ok: false,
    meta: { package_version: "0.0.9", package_origin: "C:\\Core" },
    error: { code: "task_not_found", message: "Synthetic failure" },
    diagnostics: [],
  };
  for (const response of [success, failure]) {
    assert.equal(parseBridgeResponse(JSON.stringify(response)).meta.package_version, response.meta.package_version);
  }
});

test("bridge parser recursively enforces closed snapshot and Task-detail results", () => {
  const snapshotResponse = {
    protocol: IDE_PROTOCOL,
    request_id: "request-snapshot",
    ok: true,
    meta: { package_version: "0.1.0", package_origin: "C:\\Core" },
    result: {
      ...emptySnapshot,
      tasks: [completeTask],
      anomalies: [{ code: "fixture", message: "Synthetic", status: "FAIL" }],
      validation: {
        status: "PASS",
        findings: [{ status: "PASS", code: "fixture", message: "Synthetic" }],
      },
    },
    diagnostics: [],
  };
  assert.equal(parseBridgeResponse(JSON.stringify(snapshotResponse)).ok, true);

  const extraProjectField = structuredClone(snapshotResponse);
  (extraProjectField.result.project as Record<string, unknown>).unexpected = true;
  assert.throws(() => parseBridgeResponse(JSON.stringify(extraProjectField)), /incomplete/u);

  const arrayProjectState = structuredClone(snapshotResponse);
  (arrayProjectState.result.project as unknown as Record<string, unknown>).state = ["managed"];
  assert.throws(() => parseBridgeResponse(JSON.stringify(arrayProjectState)), /incomplete/u);

  const wrongArtifactHealthType = structuredClone(snapshotResponse);
  (wrongArtifactHealthType.result.tasks[0]?.artifact_health as unknown as Record<string, unknown>).review_md = "yes";
  assert.throws(() => parseBridgeResponse(JSON.stringify(wrongArtifactHealthType)), /incomplete/u);

  const detailResponse = {
    protocol: IDE_PROTOCOL,
    request_id: "request-detail",
    ok: true,
    meta: { package_version: "0.1.0", package_origin: "C:\\Core" },
    result: completeDetail,
    diagnostics: [],
  };
  assert.equal(parseBridgeResponse(JSON.stringify(detailResponse)).ok, true);

  const extraHumanControlField = structuredClone(detailResponse);
  const control = extraHumanControlField.result.effective.human_control.final_review_required;
  (control as unknown as Record<string, unknown>).unexpected = true;
  assert.throws(() => parseBridgeResponse(JSON.stringify(extraHumanControlField)), /incomplete/u);

  const invalidWorkflowLiteral = structuredClone(detailResponse);
  (invalidWorkflowLiteral.result.workflow as unknown as Record<string, unknown>).definition_not_execution = false;
  assert.throws(() => parseBridgeResponse(JSON.stringify(invalidWorkflowLiteral)), /incomplete/u);

  const extraRoleField = structuredClone(detailResponse);
  const role = extraRoleField.result.workflow?.stages[0]?.required_roles[0];
  (role as unknown as Record<string, unknown>).unexpected = true;
  assert.throws(() => parseBridgeResponse(JSON.stringify(extraRoleField)), /incomplete/u);

  const unknownErrorCode = {
    protocol: IDE_PROTOCOL,
    request_id: "request-error",
    ok: false,
    meta: { package_version: "0.1.0", package_origin: "C:\\Core" },
    error: { code: "invented_error", message: "Synthetic" },
    diagnostics: [],
  };
  assert.throws(() => parseBridgeResponse(JSON.stringify(unknownErrorCode)), /incomplete/u);
});

test("Task YAML validity and four-artifact completeness remain distinct", () => {
  assert.deepEqual(taskForUi(completeTask), {
    id: "SYN-001",
    title: completeTask.title,
    type: "implementation",
    status: "in_progress",
    workflow: "standard-change",
    workflowResolution: "RESOLVED",
    schemaStatus: "VALID",
    artifactHealth: "complete",
  });
  const incomplete: TaskSummary = {
    ...completeTask,
    artifact_health: { ...completeTask.artifact_health, review_md: false },
  };
  assert.equal(taskForUi(incomplete).schemaStatus, "VALID");
  assert.equal(taskForUi(incomplete).artifactHealth, "incomplete");
});

test("snapshot and declared Workflow are mapped without runtime-progress claims", () => {
  const snapshot: ProjectSnapshotResult = {
    project: { state: "managed", id: "synthetic", name: "Synthetic fixture" },
    snapshot_at: "2026-09-19T00:00:00Z",
    tasks: [completeTask],
    anomalies: [{ code: "fixture", message: "Synthetic only" }],
    filters: { statuses: ["in_progress"], workflows: ["standard-change"] },
    validation: { status: "PASS", findings: [] },
  };
  const detail: TaskDetailResult = {
    task: completeTask,
    effective: {
      risk: { value: "medium", source: "Task" },
      complexity: { value: "medium", source: "Task" },
      execution_mode: { value: "standard", source: "Task" },
      quality_gates: ["independent_review"],
      human_control: { final_review_required: { value: true, source: "Task" } },
    },
    artifacts: [{ artifact_id: "artifact-opaque", label: "task.yaml", state: "present", relative_path: "governance/tasks/SYN-001/task.yaml" }],
    workflow: {
      id: "standard-change",
      name: "Standard Change",
      definition_not_execution: true,
      stages: [{
        id: "review",
        purpose: "Review the declared change.",
        human_control_checkpoint: true,
        required_quality_gates: ["independent_review"],
        required_roles: [{ id: "reviewer", name: "Reviewer", purpose: "Review", required_capabilities: ["review"] }],
      }],
    },
  };
  const state = initialState();
  applySnapshot(state, snapshot, "0.1.0");
  const artifacts = applyTaskDetail(state, detail);
  assert.equal(state.core.version, "0.1.0");
  assert.equal(state.tasks[0]?.title, completeTask.title);
  assert.equal(state.workflow?.label, "Workflow definition — not current execution progress");
  assert.equal(state.workflow?.stages[0]?.checkpoint, true);
  assert.deepEqual(artifacts.map((item) => item.id), ["artifact-opaque"]);
  assert.equal("progress" in (state.workflow ?? {}), false);
});

test("project-scope reset removes stale identity, Core, filters, and Task detail", () => {
  const state = initialState();
  state.project.id = "project-a";
  state.project.name = "Project A";
  state.core = { state: "connected", version: "0.1.0", message: "Connected" };
  state.snapshotAt = "2026-09-19T00:00:00Z";
  state.filters = {
    status: "in_progress",
    workflow: "standard-change",
    statuses: ["in_progress"],
    workflows: ["standard-change"],
  };
  state.tasks = [{
    id: "AIO-001",
    title: "Old Task",
    type: "implementation",
    status: "in_progress",
    workflow: "standard-change",
    workflowResolution: "RESOLVED",
    schemaStatus: "VALID",
    artifactHealth: "complete",
  }];
  state.selectedTask = {
    id: "AIO-001",
    title: "Old Task",
    status: "in_progress",
    risk: "medium (Task)",
    complexity: "medium (Task)",
    executionMode: "standard (Task)",
    qualityGates: ["independent_review"],
    artifacts: [],
  };
  state.workflow = { id: "standard-change", name: "Standard", label: "Workflow definition \u2014 not current execution progress", stages: [] };
  state.anomalies = ["old finding"];

  resetProjectScopeData(state);

  assert.equal(state.project.id, "");
  assert.equal(state.project.name, "");
  assert.equal(state.core.state, "unconfigured");
  assert.equal(state.core.version, "");
  assert.deepEqual(state.filters, { status: null, workflow: null, statuses: [], workflows: [] });
  assert.deepEqual(state.tasks, []);
  assert.equal(state.selectedTask, null);
  assert.equal(state.workflow, null);
  assert.deepEqual(state.anomalies, []);
});
