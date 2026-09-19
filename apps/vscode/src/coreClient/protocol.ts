export const IDE_PROTOCOL = "aio.ide/1" as const;
export const SUPPORTED_CORE_PACKAGE_VERSION = "0.1.0" as const;
export const BRIDGE_ERROR_CODES = [
  "invalid_json",
  "invalid_request",
  "unsupported_protocol",
  "unmanaged_project",
  "invalid_project",
  "out_of_scope_resource",
  "task_not_found",
  "task_id_ambiguous",
  "invalid_catalog",
  "resource_limit",
  "internal_error",
] as const;

export type BridgeErrorCode = typeof BRIDGE_ERROR_CODES[number];

export type BridgeOperation = "project_snapshot" | "task_detail";

export interface ProjectSnapshotPayload {
  status: string | null;
  workflow: string | null;
}

export interface TaskDetailPayload {
  task_id: string;
}

export interface BridgeRequest {
  protocol: typeof IDE_PROTOCOL;
  request_id: string;
  operation: BridgeOperation;
  project_root: string;
  payload: ProjectSnapshotPayload | TaskDetailPayload;
}

export interface BridgeMeta {
  package_version: string;
  package_origin: string;
}

export interface BridgeDiagnostic {
  code: string;
  message: string;
  status?: string;
  resource_id?: string;
}

export interface BridgeErrorBody {
  code: BridgeErrorCode;
  message: string;
}

export interface ArtifactHealth {
  task_yaml: boolean;
  context_md: boolean;
  acceptance_criteria_md: boolean;
  review_md: boolean;
}

export interface TaskSummary {
  id: string;
  title: string;
  type: string;
  status: string;
  workflow: string | null;
  workflow_resolution: string;
  schema_status: string;
  artifact_health: ArtifactHealth;
  resource_id: string;
}

export interface InventoryAnomaly {
  code: string;
  message: string;
  status?: string;
  resource_id?: string;
}

export interface ValidationFinding {
  status: string;
  code: string;
  message: string;
  resource_id?: string;
}

export interface ProjectSnapshotResult {
  project: {
    state: "managed" | "unmanaged" | "invalid" | "error";
    id: string | null;
    name: string | null;
  };
  snapshot_at: string;
  tasks: TaskSummary[];
  anomalies: InventoryAnomaly[];
  filters: {
    statuses: string[];
    workflows: string[];
  };
  validation: {
    status: string;
    findings: ValidationFinding[];
  };
}

export interface EffectiveValue {
  value: string | null;
  source: string;
}

export interface ArtifactDescriptor {
  artifact_id: string;
  label: string;
  state: "present" | "missing" | "blocked";
  relative_path?: string;
}

export interface WorkflowRole {
  id: string;
  name: string;
  purpose: string;
  required_capabilities: string[];
}

export interface WorkflowStage {
  id: string;
  purpose: string;
  human_control_checkpoint: boolean;
  required_quality_gates: string[];
  required_roles: WorkflowRole[];
}

export interface TaskDetailResult {
  task: TaskSummary;
  effective: {
    risk: EffectiveValue;
    complexity: EffectiveValue;
    execution_mode: EffectiveValue;
    quality_gates: string[];
    human_control: Record<string, { value: boolean; source: string }>;
  };
  artifacts: ArtifactDescriptor[];
  workflow: null | {
    id: string;
    name: string;
    definition_not_execution: true;
    stages: WorkflowStage[];
  };
}

export type BridgeResult = ProjectSnapshotResult | TaskDetailResult;

export interface BridgeSuccess<T extends BridgeResult = BridgeResult> {
  protocol: typeof IDE_PROTOCOL;
  request_id: string;
  ok: true;
  meta: BridgeMeta;
  result: T;
  diagnostics: BridgeDiagnostic[];
}

export interface BridgeFailure {
  protocol: typeof IDE_PROTOCOL;
  request_id: string | null;
  ok: false;
  meta: BridgeMeta;
  error: BridgeErrorBody;
  diagnostics: BridgeDiagnostic[];
}

export type BridgeResponse<T extends BridgeResult = BridgeResult> =
  | BridgeSuccess<T>
  | BridgeFailure;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function hasClosedKeys(
  value: Record<string, unknown>,
  required: readonly string[],
  optional: readonly string[] = [],
): boolean {
  const actual = Object.keys(value);
  const allowed = new Set([...required, ...optional]);
  return required.every((key) => Object.hasOwn(value, key))
    && actual.every((key) => allowed.has(key));
}

function isString(value: unknown): value is string {
  return typeof value === "string";
}

function isNullableString(value: unknown): value is string | null {
  return value === null || isString(value);
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(isString);
}

function isBridgeErrorCode(value: unknown): value is BridgeErrorCode {
  return typeof value === "string"
    && (BRIDGE_ERROR_CODES as readonly string[]).includes(value);
}

function isMeta(value: unknown): value is BridgeMeta {
  return isObject(value)
    && hasExactKeys(value, ["package_version", "package_origin"])
    && typeof value.package_version === "string"
    && typeof value.package_origin === "string";
}

function isDiagnostic(value: unknown): value is BridgeDiagnostic {
  if (!isObject(value)) {
    return false;
  }
  if (!hasClosedKeys(value, ["code", "message"], ["status", "resource_id"])) {
    return false;
  }
  return typeof value.code === "string"
    && typeof value.message === "string"
    && (value.status === undefined || typeof value.status === "string")
    && (value.resource_id === undefined || typeof value.resource_id === "string");
}

function isArtifactHealth(value: unknown): value is ArtifactHealth {
  return isObject(value)
    && hasExactKeys(value, ["task_yaml", "context_md", "acceptance_criteria_md", "review_md"])
    && typeof value.task_yaml === "boolean"
    && typeof value.context_md === "boolean"
    && typeof value.acceptance_criteria_md === "boolean"
    && typeof value.review_md === "boolean";
}

function isTaskSummary(value: unknown): value is TaskSummary {
  return isObject(value)
    && hasExactKeys(value, [
      "id",
      "title",
      "type",
      "status",
      "workflow",
      "workflow_resolution",
      "schema_status",
      "artifact_health",
      "resource_id",
    ])
    && isString(value.id)
    && isString(value.title)
    && isString(value.type)
    && isString(value.status)
    && isNullableString(value.workflow)
    && isString(value.workflow_resolution)
    && isString(value.schema_status)
    && isArtifactHealth(value.artifact_health)
    && isString(value.resource_id);
}

function isInventoryAnomaly(value: unknown): value is InventoryAnomaly {
  return isObject(value)
    && hasClosedKeys(value, ["code", "message"], ["status", "resource_id"])
    && isString(value.code)
    && isString(value.message)
    && (value.status === undefined || isString(value.status))
    && (value.resource_id === undefined || isString(value.resource_id));
}

function isValidationFinding(value: unknown): value is ValidationFinding {
  return isObject(value)
    && hasClosedKeys(value, ["status", "code", "message"], ["resource_id"])
    && isString(value.status)
    && isString(value.code)
    && isString(value.message)
    && (value.resource_id === undefined || isString(value.resource_id));
}

function isEffectiveValue(value: unknown): value is EffectiveValue {
  return isObject(value)
    && hasExactKeys(value, ["value", "source"])
    && isNullableString(value.value)
    && isString(value.source);
}

function isHumanControlValue(value: unknown): value is { value: boolean; source: string } {
  return isObject(value)
    && hasExactKeys(value, ["value", "source"])
    && typeof value.value === "boolean"
    && isString(value.source);
}

function isArtifactDescriptor(value: unknown): value is ArtifactDescriptor {
  return isObject(value)
    && hasClosedKeys(value, ["artifact_id", "label", "state"], ["relative_path"])
    && isString(value.artifact_id)
    && isString(value.label)
    && (value.state === "present" || value.state === "missing" || value.state === "blocked")
    && (value.relative_path === undefined || isString(value.relative_path));
}

function isWorkflowRole(value: unknown): value is WorkflowRole {
  return isObject(value)
    && hasExactKeys(value, ["id", "name", "purpose", "required_capabilities"])
    && isString(value.id)
    && isString(value.name)
    && isString(value.purpose)
    && isStringArray(value.required_capabilities);
}

function isWorkflowStage(value: unknown): value is WorkflowStage {
  return isObject(value)
    && hasExactKeys(value, [
      "id",
      "purpose",
      "human_control_checkpoint",
      "required_quality_gates",
      "required_roles",
    ])
    && isString(value.id)
    && isString(value.purpose)
    && typeof value.human_control_checkpoint === "boolean"
    && isStringArray(value.required_quality_gates)
    && Array.isArray(value.required_roles)
    && value.required_roles.every(isWorkflowRole);
}

function isWorkflowDetail(value: unknown): value is NonNullable<TaskDetailResult["workflow"]> {
  return isObject(value)
    && hasExactKeys(value, ["id", "name", "definition_not_execution", "stages"])
    && isString(value.id)
    && isString(value.name)
    && value.definition_not_execution === true
    && Array.isArray(value.stages)
    && value.stages.every(isWorkflowStage);
}

export function parseBridgeResponse(text: string): BridgeResponse {
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("Core bridge returned invalid JSON.");
  }
  if (!isObject(value) || value.protocol !== IDE_PROTOCOL || typeof value.ok !== "boolean") {
    throw new Error("Core bridge returned an incompatible envelope.");
  }
  if (!isMeta(value.meta) || !Array.isArray(value.diagnostics) || !value.diagnostics.every(isDiagnostic)) {
    throw new Error("Core bridge returned invalid metadata or diagnostics.");
  }
  if (value.ok) {
    if (!hasExactKeys(value, ["protocol", "request_id", "ok", "meta", "result", "diagnostics"])) {
      throw new Error("Core bridge success envelope contained unexpected fields.");
    }
    if (
      typeof value.request_id !== "string"
      || (!isProjectSnapshotResult(value.result) && !isTaskDetailResult(value.result))
    ) {
      throw new Error("Core bridge success envelope was incomplete.");
    }
    return value as unknown as BridgeSuccess;
  }
  if (!hasExactKeys(value, ["protocol", "request_id", "ok", "meta", "error", "diagnostics"])) {
    throw new Error("Core bridge error envelope contained unexpected fields.");
  }
  if ((value.request_id !== null && typeof value.request_id !== "string") || !isObject(value.error)
      || !hasExactKeys(value.error, ["code", "message"])
      || !isBridgeErrorCode(value.error.code) || typeof value.error.message !== "string") {
    throw new Error("Core bridge error envelope was incomplete.");
  }
  return value as unknown as BridgeFailure;
}

export function isProjectSnapshotResult(value: unknown): value is ProjectSnapshotResult {
  if (!isObject(value)
      || !hasExactKeys(value, ["project", "snapshot_at", "tasks", "anomalies", "filters", "validation"])
      || !isObject(value.project)
      || !hasExactKeys(value.project, ["state", "id", "name"])
      || (
        value.project.state !== "managed"
        && value.project.state !== "unmanaged"
        && value.project.state !== "invalid"
        && value.project.state !== "error"
      )
      || !isNullableString(value.project.id)
      || !isNullableString(value.project.name)
      || !isString(value.snapshot_at)
      || !Array.isArray(value.tasks)
      || !value.tasks.every(isTaskSummary)
      || !Array.isArray(value.anomalies)
      || !value.anomalies.every(isInventoryAnomaly)
      || !isObject(value.filters)
      || !hasExactKeys(value.filters, ["statuses", "workflows"])
      || !isStringArray(value.filters.statuses)
      || !isStringArray(value.filters.workflows)
      || !isObject(value.validation)
      || !hasExactKeys(value.validation, ["status", "findings"])
      || !isString(value.validation.status)
      || !Array.isArray(value.validation.findings)
      || !value.validation.findings.every(isValidationFinding)) {
    return false;
  }
  return true;
}

export function isTaskDetailResult(value: unknown): value is TaskDetailResult {
  if (!isObject(value)
      || !hasExactKeys(value, ["task", "effective", "artifacts", "workflow"])
      || !isTaskSummary(value.task)
      || !isObject(value.effective)
      || !hasExactKeys(value.effective, [
        "risk",
        "complexity",
        "execution_mode",
        "quality_gates",
        "human_control",
      ])
      || !isEffectiveValue(value.effective.risk)
      || !isEffectiveValue(value.effective.complexity)
      || !isEffectiveValue(value.effective.execution_mode)
      || !isStringArray(value.effective.quality_gates)
      || !isObject(value.effective.human_control)
      || !Object.values(value.effective.human_control).every(isHumanControlValue)
      || !Array.isArray(value.artifacts)
      || !value.artifacts.every(isArtifactDescriptor)
      || (value.workflow !== null && !isWorkflowDetail(value.workflow))) {
    return false;
  }
  return true;
}
