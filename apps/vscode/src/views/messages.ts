export type WebviewAction =
  | { type: "ready" }
  | { type: "refresh" }
  | { type: "selectProject" }
  | { type: "selectPython" }
  | { type: "selectTask"; taskId: string }
  | { type: "setFilters"; status: string | null; workflow: string | null }
  | { type: "openArtifact"; artifactId: string }
  | { type: "startObserving" }
  | { type: "stopObserving" }
  | { type: "copyHookSetup" };

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): boolean {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return actual.length === wanted.length && actual.every((key, index) => key === wanted[index]);
}

function boundedScalarText(value: unknown, maximum: number): value is string {
  if (typeof value !== "string" || value.length === 0 || value.includes("\0")) {
    return false;
  }
  const scalars = [...value];
  return scalars.length <= maximum
    && scalars.every((character) => {
      const codePoint = character.codePointAt(0)!;
      return codePoint < 0xd800 || codePoint > 0xdfff;
    });
}

function nullableFilter(value: unknown): value is string | null {
  return value === null || boundedScalarText(value, 256);
}

export function parseWebviewAction(value: unknown): WebviewAction | null {
  if (!isObject(value) || typeof value.type !== "string") {
    return null;
  }
  switch (value.type) {
    case "ready":
    case "refresh":
    case "selectProject":
    case "selectPython":
    case "startObserving":
    case "stopObserving":
    case "copyHookSetup":
      return exactKeys(value, ["type"]) ? value as WebviewAction : null;
    case "selectTask":
      return exactKeys(value, ["type", "taskId"])
        && boundedScalarText(value.taskId, 256)
        ? value as WebviewAction
        : null;
    case "setFilters":
      return exactKeys(value, ["type", "status", "workflow"])
        && nullableFilter(value.status)
        && nullableFilter(value.workflow)
        ? value as WebviewAction
        : null;
    case "openArtifact":
      return exactKeys(value, ["type", "artifactId"])
        && typeof value.artifactId === "string"
        && value.artifactId.length > 0
        && value.artifactId.length <= 256
        ? value as WebviewAction
        : null;
    default:
      return null;
  }
}

const TRUSTED_ACTIONS = new Set<WebviewAction["type"]>([
  "selectProject",
  "selectPython",
  "selectTask",
  "setFilters",
  "openArtifact",
  "startObserving",
  "copyHookSetup",
]);

export function actionRequiresTrust(action: WebviewAction["type"]): boolean {
  return TRUSTED_ACTIONS.has(action);
}

export function directActionAllowed(action: WebviewAction["type"], trusted: boolean): boolean {
  return !actionRequiresTrust(action) || trusted || action === "stopObserving";
}
