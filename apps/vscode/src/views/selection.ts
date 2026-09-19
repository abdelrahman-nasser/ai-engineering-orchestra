import path from "node:path";

export function responseIsCurrent(
  responseGeneration: number,
  currentGeneration: number,
  responseProjectKey: string,
  currentProjectKey: string,
): boolean {
  return responseGeneration === currentGeneration && responseProjectKey === currentProjectKey;
}

export function canonicalRootsMatch(
  left: string,
  right: string,
  platform: NodeJS.Platform = process.platform,
): boolean {
  const pathApi = platform === "win32" ? path.win32 : path.posix;
  return pathApi.relative(left, right) === "" && pathApi.relative(right, left) === "";
}

export function isUncWorkspaceRoot(candidate: string): boolean {
  const normalized = candidate.replaceAll("/", "\\");
  if (/^\\\\[?.]\\UNC\\/iu.test(normalized)) {
    return true;
  }
  if (!normalized.startsWith("\\\\") || normalized.startsWith("\\\\?\\") || normalized.startsWith("\\\\.\\")) {
    return false;
  }
  return normalized.slice(2).split("\\").filter(Boolean).length >= 2;
}

export interface BoundOperationIdentity {
  readonly token: number;
  readonly projectGeneration: number;
  readonly projectKey: string;
  readonly canonicalRoot: string;
  readonly pythonPath: string;
}

export interface RootLifecycleIdentity {
  readonly token: number;
  readonly projectKey: string;
  readonly canonicalRoot: string;
  readonly pythonPath: string;
}

export function rootLifecycleIsCurrent(
  operation: RootLifecycleIdentity,
  current: RootLifecycleIdentity,
): boolean {
  return (
    operation.token === current.token &&
    operation.projectKey === current.projectKey &&
    canonicalRootsMatch(operation.canonicalRoot, current.canonicalRoot) &&
    operation.pythonPath === current.pythonPath
  );
}

export function boundOperationIsCurrent(
  operation: BoundOperationIdentity,
  current: BoundOperationIdentity,
): boolean {
  return (
    operation.token === current.token &&
    operation.projectGeneration === current.projectGeneration &&
    operation.projectKey === current.projectKey &&
    operation.canonicalRoot === current.canonicalRoot &&
    operation.pythonPath === current.pythonPath
  );
}
