import { realpath, stat } from "node:fs/promises";
import path from "node:path";

export function isContained(root: string, candidate: string): boolean {
  const normalizedRoot = path.resolve(root);
  const normalizedCandidate = path.resolve(candidate);
  const relative = path.relative(normalizedRoot, normalizedCandidate);
  return relative === "" || (!relative.startsWith(`..${path.sep}`) && relative !== ".." && !path.isAbsolute(relative));
}

export async function canonicalRegularFile(candidate: string): Promise<string> {
  if (!path.isAbsolute(candidate)) {
    throw new Error("The selected interpreter must be an absolute path.");
  }
  const resolved = await realpath(candidate);
  const info = await stat(resolved);
  if (!info.isFile()) {
    throw new Error("The selected interpreter is not a regular file.");
  }
  return resolved;
}

export async function canonicalDirectory(candidate: string): Promise<string> {
  if (!path.isAbsolute(candidate)) {
    throw new Error("The selected project root must be an absolute path.");
  }
  const resolved = await realpath(candidate);
  const info = await stat(resolved);
  if (!info.isDirectory()) {
    throw new Error("The selected project root is not a directory.");
  }
  if (process.platform === "win32" && resolved.startsWith("\\\\")) {
    throw new Error("UNC workspaces are not supported by this development extension.");
  }
  return resolved;
}

export async function assertPackageOriginOutsideProject(packageOrigin: string, projectRoot: string): Promise<string> {
  if (!path.isAbsolute(packageOrigin)) {
    throw new Error("Core package origin was not absolute.");
  }
  if (!path.isAbsolute(projectRoot)) {
    throw new Error("Selected project root was not absolute.");
  }
  const resolvedProjectRoot = await realpath(projectRoot);
  const resolvedOrigin = await realpath(packageOrigin);
  if (isContained(resolvedProjectRoot, resolvedOrigin)) {
    throw new Error(
      "Core resolved inside the selected project. Use a normal wheel installation in a trusted Python environment.",
    );
  }
  return resolvedOrigin;
}
