import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";

const extensionRoot = path.resolve(__dirname, "../../..");

test("webview rendering uses text nodes and exposes no command or path primitive", async () => {
  const script = await readFile(path.join(extensionRoot, "webview", "main.js"), "utf8");
  assert.match(script, /textContent/u);
  assert.match(script, /replaceChildren/u);
  assert.doesNotMatch(script, /innerHTML|outerHTML|insertAdjacentHTML|eval\s*\(|new Function/u);
  assert.doesNotMatch(script, /executeCommand|createTerminal|child_process|require\s*\(/u);
  assert.doesNotMatch(script, /price|quota|token count|reasoning effort|percentage|rank/u);
  assert.match(script, /identity\.sessionId/u);
  assert.match(script, /platformRequired = new Set\(\["startObserving", "copyHookSetup"\]\)/u);
});

test("webview CSP and resource roots remain closed", async () => {
  const htmlSource = await readFile(path.join(extensionRoot, "src", "views", "html.ts"), "utf8");
  const sidebarSource = await readFile(path.join(extensionRoot, "src", "views", "sidebar.ts"), "utf8");
  assert.match(htmlSource, /default-src 'none'/u);
  assert.match(htmlSource, /connect-src 'none'/u);
  assert.match(htmlSource, /img-src 'none'/u);
  assert.doesNotMatch(htmlSource, /unsafe-inline|unsafe-eval|https?:\/\//u);
  assert.match(sidebarSource, /localResourceRoots: \[vscode\.Uri\.joinPath\([^\]]+"webview"\)\]/u);
  assert.match(sidebarSource, /enableScripts: true/u);
});

test("host and webview contain no governance or engine control actions", async () => {
  const files = [
    path.join(extensionRoot, "src", "views", "messages.ts"),
    path.join(extensionRoot, "src", "extension.ts"),
    path.join(extensionRoot, "webview", "main.js"),
  ];
  const source = (await Promise.all(files.map((file) => readFile(file, "utf8")))).join("\n");
  assert.doesNotMatch(source, /approveTask|completeTask|createAssignment|startCodex|resumeCodex|steerCodex|stopCodex/u);
  assert.doesNotMatch(source, /aio verify|full verification|terminal shortcut/iu);
});
