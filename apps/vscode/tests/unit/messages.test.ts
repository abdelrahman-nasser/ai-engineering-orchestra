import assert from "node:assert/strict";
import test from "node:test";

import {
  actionRequiresTrust,
  directActionAllowed,
  parseWebviewAction,
} from "../../src/views/messages";

test("webview actions form a closed union", () => {
  assert.deepEqual(parseWebviewAction({ type: "refresh" }), { type: "refresh" });
  assert.deepEqual(
    parseWebviewAction({ type: "setFilters", status: "in_progress", workflow: null }),
    { type: "setFilters", status: "in_progress", workflow: null },
  );
  assert.equal(parseWebviewAction({ type: "refresh", command: "terminal" }), null);
  assert.equal(parseWebviewAction({ type: "executeCommand", command: "aio verify" }), null);
  assert.equal(parseWebviewAction({ type: "selectPython", path: "C:\\hostile.exe" }), null);
  assert.equal(parseWebviewAction({ type: "openArtifact", artifactId: "" }), null);
  assert.equal(parseWebviewAction({ type: "setFilters", status: "x".repeat(257), workflow: null }), null);
  assert.equal(parseWebviewAction({ type: "setFilters", status: "bad\0value", workflow: null }), null);
  assert.equal(parseWebviewAction({ type: "selectTask", taskId: "\ud800" }), null);
});

test("opaque identifiers are bounded without normalizing their content", () => {
  const opaque = "Session-Ä-".repeat(20);
  assert.equal(parseWebviewAction({ type: "selectTask", taskId: opaque })?.type, "selectTask");
  assert.equal(parseWebviewAction({ type: "selectTask", taskId: "x".repeat(257) }), null);
  assert.equal(parseWebviewAction({ type: "openArtifact", artifactId: "x".repeat(257) }), null);
});

test("restricted mode rejects every privileged direct action", () => {
  const privileged = [
    "selectProject",
    "selectPython",
    "selectTask",
    "setFilters",
    "openArtifact",
    "startObserving",
    "copyHookSetup",
  ] as const;
  for (const action of privileged) {
    assert.equal(actionRequiresTrust(action), true, action);
    assert.equal(directActionAllowed(action, false), false, action);
    assert.equal(directActionAllowed(action, true), true, action);
  }
  assert.equal(directActionAllowed("stopObserving", false), true);
  assert.equal(directActionAllowed("refresh", false), true);
});
