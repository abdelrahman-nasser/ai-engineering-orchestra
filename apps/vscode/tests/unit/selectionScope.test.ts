import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";

import { isContained } from "../../src/coreClient/scope";
import {
  boundOperationIsCurrent,
  canonicalRootsMatch,
  isUncWorkspaceRoot,
  responseIsCurrent,
  rootLifecycleIsCurrent,
  type BoundOperationIdentity,
  type RootLifecycleIdentity,
} from "../../src/views/selection";

test("late Core responses cannot replace a new root selection", () => {
  assert.equal(responseIsCurrent(7, 7, "file:///project-a", "file:///project-a"), true);
  assert.equal(responseIsCurrent(6, 7, "file:///project-a", "file:///project-a"), false);
  assert.equal(responseIsCurrent(7, 7, "file:///project-a", "file:///project-b"), false);
});

test("containment rejects siblings, parents, and absolute escapes", () => {
  const root = path.resolve("C:\\work\\project");
  assert.equal(isContained(root, root), true);
  assert.equal(isContained(root, path.join(root, ".ai", "project.yaml")), true);
  assert.equal(isContained(root, path.resolve(root, "..", "other", "secret")), false);
  assert.equal(isContained(root, path.resolve("D:\\outside")), false);
});

test("canonical root identity normalizes separators without conflating distinct roots", () => {
  assert.equal(canonicalRootsMatch("C:\\work\\project\\", "C:\\work\\project", "win32"), true);
  assert.equal(canonicalRootsMatch("C:\\work\\project-a", "C:\\work\\project-b", "win32"), false);
  assert.equal(canonicalRootsMatch("C:\\work\\Project", "C:\\work\\project", "win32"), true);
  assert.equal(canonicalRootsMatch("/work/Project", "/work/project", "linux"), false);
});

test("UNC detection covers standard and namespaced shares without rejecting local device paths", () => {
  assert.equal(isUncWorkspaceRoot("\\\\server\\share\\project"), true);
  assert.equal(isUncWorkspaceRoot("//server/share/project"), true);
  assert.equal(isUncWorkspaceRoot("\\\\?\\UNC\\server\\share\\project"), true);
  assert.equal(isUncWorkspaceRoot("C:\\work\\project"), false);
  assert.equal(isUncWorkspaceRoot("\\\\?\\C:\\work\\project"), false);
  assert.equal(isUncWorkspaceRoot("\\single-component"), false);
});

test("monitor publication requires the same lifecycle, root, project, and interpreter", () => {
  const active: RootLifecycleIdentity = {
    token: 8,
    projectKey: "file:///project",
    canonicalRoot: "C:\\work\\project",
    pythonPath: "C:\\Python312\\python.exe",
  };
  assert.equal(rootLifecycleIsCurrent(active, { ...active }), true);
  assert.equal(rootLifecycleIsCurrent(active, { ...active, token: 9 }), false);
  assert.equal(rootLifecycleIsCurrent(active, { ...active, canonicalRoot: "C:\\work\\other" }), false);
  assert.equal(rootLifecycleIsCurrent(active, { ...active, projectKey: "file:///other" }), false);
  assert.equal(rootLifecycleIsCurrent(active, { ...active, pythonPath: "C:\\Python313\\python.exe" }), false);
});

test("awaited controller work cannot outlive its exact root and interpreter binding", async () => {
  let token = 4;
  let projectGeneration = 9;
  let projectKey = "file:///project-a";
  let canonicalRoot = "C:\\work\\project-a";
  let pythonPath = "C:\\Python312\\python.exe";
  const attempt: BoundOperationIdentity = {
    token,
    projectGeneration,
    projectKey,
    canonicalRoot,
    pythonPath,
  };
  let release: (() => void) | undefined;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const continuation = (async () => {
    await gate;
    return boundOperationIsCurrent(attempt, {
      token,
      projectGeneration,
      projectKey,
      canonicalRoot,
      pythonPath,
    });
  })();

  token += 1;
  projectGeneration += 1;
  projectKey = "file:///project-b";
  canonicalRoot = "C:\\work\\project-b";
  pythonPath = "C:\\Python313\\python.exe";
  release?.();
  assert.equal(await continuation, false);
});

test("a later Task-detail selection supersedes an older selection on the same project", () => {
  const older: BoundOperationIdentity = {
    token: 11,
    projectGeneration: 5,
    projectKey: "file:///project",
    canonicalRoot: "C:\\work\\project",
    pythonPath: "C:\\Python312\\python.exe",
  };
  assert.equal(boundOperationIsCurrent(older, { ...older, token: 12 }), false);
  assert.equal(boundOperationIsCurrent({ ...older, token: 12 }, { ...older, token: 12 }), true);
});
