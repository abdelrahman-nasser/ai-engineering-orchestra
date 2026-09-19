import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { randomBytes, randomUUID } from "node:crypto";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { isAbsolute, join, resolve } from "node:path";
import test from "node:test";

import {
  CODEX_MONITOR_OWNER,
  CODEX_OBSERVER_SHA256,
  CodexMonitor,
} from "../../src/monitoring/codex";

interface ObserverResult {
  exitCode: number | null;
  stdout: Buffer;
  stderr: Buffer;
}

async function runObserver(
  pythonPath: string,
  registry: string,
  input: Buffer | string,
): Promise<ObserverResult> {
  const observer = resolve(process.cwd(), "observer", "codex_hook_observer.py");
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(
      pythonPath,
      [
        "-I",
        "-B",
        "-S",
        observer,
        "--registry",
        registry,
        "--owner",
        CODEX_MONITOR_OWNER,
        "--observer-sha256",
        CODEX_OBSERVER_SHA256,
      ],
      { shell: false, windowsHide: true, stdio: ["pipe", "pipe", "pipe"] },
    );
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.once("error", rejectRun);
    child.once("close", (exitCode) =>
      resolveRun({ exitCode, stdout: Buffer.concat(stdout), stderr: Buffer.concat(stderr) }),
    );
    child.stdin.end(input);
  });
}

async function runObserverWithReadFailure(pythonPath: string): Promise<ObserverResult> {
  const observer = resolve(process.cwd(), "observer", "codex_hook_observer.py");
  const program = [
    "import importlib.util, sys",
    "spec = importlib.util.spec_from_file_location('aio_observer_under_test', sys.argv[1])",
    "module = importlib.util.module_from_spec(spec)",
    "spec.loader.exec_module(module)",
    "class BrokenBuffer:",
    "    def read(self, _size=-1): raise OSError('injected read failure')",
    "class BrokenInput:",
    "    buffer = BrokenBuffer()",
    "sys.stdin = BrokenInput()",
    "raise SystemExit(module.main())",
  ].join("\n");
  return new Promise((resolveRun, rejectRun) => {
    const child = spawn(
      pythonPath,
      ["-I", "-B", "-S", "-c", program, observer],
      { shell: false, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] },
    );
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.once("error", rejectRun);
    child.once("close", (exitCode) =>
      resolveRun({ exitCode, stdout: Buffer.concat(stdout), stderr: Buffer.concat(stderr) }),
    );
  });
}

test("Python observer emits event-specific neutral output and forwards only allowlisted metadata", async (context) => {
  const pythonPath = process.env.AIO_TEST_PYTHON;
  if (process.platform !== "win32" || !pythonPath || !isAbsolute(pythonPath)) {
    context.skip("Set AIO_TEST_PYTHON to an approved absolute Windows Python path for observer execution.");
    return;
  }

  const directory = await mkdtemp(join(tmpdir(), "aio-observer-test-"));
  try {
    const root = join(directory, "project");
    const registry = join(directory, "registry");
    await mkdir(root);
    const monitor = new CodexMonitor({ registryDirectory: registry, canonicalRoot: root });
    assert.equal((await monitor.start()).state, "configured_no_observations");

    const postTool = await runObserver(
      pythonPath,
      registry,
      JSON.stringify({
        session_id: "session-observer",
        turn_id: "turn-observer",
        transcript_path: "private-transcript.jsonl",
        cwd: root,
        hook_event_name: "PostToolUse",
        permission_mode: "dontAsk",
        model: "reported-model",
        tool_name: "apply_patch",
        tool_use_id: "call-observer",
        tool_input: { command: "private command" },
        tool_response: "private response",
        prompt: "private prompt",
        environment: { SECRET: "private credential" },
      }),
    );
    assert.equal(postTool.exitCode, 0);
    assert.equal(postTool.stdout.toString("utf8"), "{}\n");
    assert.equal(postTool.stderr.length, 0);
    const event = monitor.snapshot().events[0];
    assert.equal(event?.eventType, "PostToolUse");
    assert.equal(event?.toolLabel, "apply_patch");
    assert.equal(event?.model, "reported-model");
    assert.deepEqual(Object.keys(event ?? {}).sort(), [
      "collectorInstance",
      "deliveryId",
      "eventType",
      "model",
      "receiptSequence",
      "receivedAt",
      "rootFingerprint",
      "sessionId",
      "source",
      "toolCallId",
      "toolLabel",
      "turnId",
    ]);

    const sessionEnd = await runObserver(
      pythonPath,
      registry,
      JSON.stringify({
        session_id: "session-observer",
        transcript_path: "private-transcript.jsonl",
        cwd: root,
        hook_event_name: "SessionEnd",
        reason: "other",
      }),
    );
    assert.equal(sessionEnd.exitCode, 0);
    assert.equal(sessionEnd.stdout.length, 0);
    assert.equal(sessionEnd.stderr.length, 0);
    assert.equal(monitor.snapshot().events.length, 2);

    const malformed = await runObserver(pythonPath, registry, "{not-json");
    assert.equal(malformed.exitCode, 0);
    assert.equal(malformed.stdout.toString("utf8"), "{}\n");
    assert.equal(malformed.stderr.length, 0);
    assert.equal(monitor.snapshot().events.length, 2);

    const endOfFile = await runObserver(pythonPath, registry, "");
    assert.equal(endOfFile.exitCode, 0);
    assert.equal(endOfFile.stdout.toString("utf8"), "{}\n");
    assert.equal(endOfFile.stderr.length, 0);

    const readFailure = await runObserverWithReadFailure(pythonPath);
    assert.equal(readFailure.exitCode, 0);
    assert.equal(readFailure.stdout.toString("utf8"), "{}\n");
    assert.equal(readFailure.stderr.length, 0);

    for (const invalidEventName of [[], {}, 17, true, null]) {
      const invalidType = await runObserver(
        pythonPath,
        registry,
        JSON.stringify({ hook_event_name: invalidEventName }),
      );
      assert.equal(invalidType.exitCode, 0);
      assert.equal(invalidType.stdout.toString("utf8"), "{}\n");
      assert.equal(invalidType.stderr.length, 0);
    }
    assert.equal(monitor.snapshot().events.length, 2);

    const oversized = await runObserver(pythonPath, registry, Buffer.alloc(64 * 1024 + 1, 0x61));
    assert.equal(oversized.exitCode, 0);
    assert.equal(oversized.stderr.length, 0);
    assert.doesNotMatch(oversized.stdout.toString("utf8"), /continue|decision|approve|deny/iu);
    assert.equal(monitor.snapshot().events.length, 2);
    await monitor.dispose();
  } finally {
    await rm(directory, { force: true, recursive: true });
  }
});

test("observer cleans bounded expired saturation, selects the nested root, and rejects partial discovery", async (context) => {
  const pythonPath = process.env.AIO_TEST_PYTHON;
  if (process.platform !== "win32" || !pythonPath || !isAbsolute(pythonPath)) {
    context.skip("Set AIO_TEST_PYTHON to an approved absolute Windows Python path for observer execution.");
    return;
  }

  const directory = await mkdtemp(join(tmpdir(), "aio-observer-registry-test-"));
  const outerRoot = join(directory, "project");
  const innerRoot = join(outerRoot, "nested");
  const registry = join(directory, "registry");
  await mkdir(innerRoot, { recursive: true });
  const outer = new CodexMonitor({ registryDirectory: registry, canonicalRoot: outerRoot });
  const inner = new CodexMonitor({ registryDirectory: registry, canonicalRoot: innerRoot });
  try {
    assert.equal((await outer.start()).listener, "listening");
    assert.equal((await inner.start()).listener, "listening");
    const liveNames = (await readdir(registry)).filter((name) => name.endsWith(".json"));
    assert.equal(liveNames.length, 2);
    const template = JSON.parse(
      await readFile(join(registry, liveNames[0]!), "utf8"),
    ) as Record<string, unknown>;
    const expiredNames: string[] = [];
    for (let index = 0; index < 33; index += 1) {
      const collector = randomUUID();
      const generation = randomUUID();
      const name = `aio-codex-${collector}-${generation}.json`;
      expiredNames.push(name);
      await writeFile(
        join(registry, name),
        JSON.stringify({
          ...template,
          collector_instance: collector,
          secret: randomBytes(32).toString("base64url"),
          issued_at: new Date(Date.now() - 120_000).toISOString(),
          lease_expires_at: new Date(Date.now() - 60_000).toISOString(),
        }),
        { encoding: "utf8", flag: "wx", mode: 0o600 },
      );
    }

    const nested = await runObserver(
      pythonPath,
      registry,
      JSON.stringify({
        session_id: "nested-session",
        turn_id: "nested-turn",
        cwd: innerRoot,
        hook_event_name: "PostToolUse",
        tool_name: "apply_patch",
        tool_use_id: "nested-call",
      }),
    );
    assert.equal(nested.exitCode, 0);
    assert.equal(nested.stderr.length, 0);
    assert.equal(outer.snapshot().events.length, 0);
    assert.equal(inner.snapshot().events.length, 1);
    const namesAfterCleanup = new Set(await readdir(registry));
    assert.equal(expiredNames.filter((name) => namesAfterCleanup.has(name)).length, 1);

    for (let index = 0; index < 33; index += 1) {
      await writeFile(join(registry, `unowned-${index}.json`), "{}", { flag: "wx" });
    }
    const incomplete = await runObserver(
      pythonPath,
      registry,
      JSON.stringify({
        session_id: "must-not-route",
        cwd: innerRoot,
        hook_event_name: "SessionStart",
      }),
    );
    assert.equal(incomplete.exitCode, 0);
    assert.equal(incomplete.stderr.length, 0);
    assert.equal(outer.snapshot().events.length, 0);
    assert.equal(inner.snapshot().events.length, 1);
  } finally {
    await Promise.all([outer.dispose(), inner.dispose()]);
    await rm(directory, { force: true, recursive: true });
  }
});
