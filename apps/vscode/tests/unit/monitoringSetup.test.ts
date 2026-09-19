import assert from "node:assert/strict";
import { access, mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

import {
  CODEX_MONITOR_OWNER,
  CODEX_OBSERVER_SHA256,
  CODEX_SUPPORTED_EVENTS,
  applyOwnedHookRegistrationFixture,
  createCodexHookSetup,
  formatCodexHookSetup,
  installObserverAsset,
  removeOwnedHookRegistrationFixture,
} from "../../src/monitoring/codex";

async function withTempDirectory(run: (directory: string) => Promise<void>): Promise<void> {
  const directory = await mkdtemp(join(tmpdir(), "aio-monitor-setup-"));
  try {
    await run(directory);
  } finally {
    await rm(directory, { force: true, recursive: true });
  }
}

test("observer installation is content-addressed, pinned, and idempotent", async () => {
  await withTempDirectory(async (directory) => {
    const source = resolve(process.cwd(), "observer", "codex_hook_observer.py");
    await access(source);
    const first = await installObserverAsset(source, join(directory, "assets"));
    const second = await installObserverAsset(source, join(directory, "assets"));
    assert.deepEqual(second, first);
    assert.equal(first.sha256, CODEX_OBSERVER_SHA256);
    assert.match(first.observerPath, new RegExp(CODEX_OBSERVER_SHA256, "u"));
    assert.equal(await readFile(first.observerPath, "utf8"), await readFile(source, "utf8"));
    assert.equal((await stat(first.observerPath)).isFile(), true);
  });
});

test("setup is fixed, explicit, idempotent, and removal preserves unrelated hooks", async () => {
  await withTempDirectory(async (directory) => {
    const source = resolve(process.cwd(), "observer", "codex_hook_observer.py");
    const installed = await installObserverAsset(source, join(directory, "assets"));
    const plan = createCodexHookSetup({
      pythonPath: resolve(directory, "Python With Spaces", "python.exe"),
      observerPath: installed.observerPath,
      observerSha256: installed.sha256,
      registryDirectory: resolve(directory, "registry with spaces"),
    });
    assert.equal(plan.owner, CODEX_MONITOR_OWNER);
    assert.equal(plan.observerSha256, CODEX_OBSERVER_SHA256);
    assert.match(plan.commandWindows, /--owner/u);
    assert.match(plan.commandWindows, new RegExp(CODEX_OBSERVER_SHA256, "u"));
    assert.doesNotMatch(plan.commandWindows, /\$\{|%\w+%/u);
    assert.deepEqual(Object.keys((plan.configFragment as { hooks: object }).hooks), [
      ...CODEX_SUPPORTED_EVENTS,
    ]);

    const unrelated = {
      description: "keep me",
      hooks: {
        PostToolUse: [
          {
            matcher: "Bash",
            hooks: [{ type: "command", command: "other-tool", timeout: 7 }],
          },
        ],
        UserPromptSubmit: [{ hooks: [{ type: "command", command: "another-tool" }] }],
      },
      futureSetting: { enabled: true },
    };
    const applied = applyOwnedHookRegistrationFixture(unrelated, plan);
    const appliedAgain = applyOwnedHookRegistrationFixture(applied, plan);
    assert.deepEqual(appliedAgain, applied);
    assert.deepEqual(unrelated.hooks.PostToolUse[0]?.hooks[0], {
      type: "command",
      command: "other-tool",
      timeout: 7,
    });
    const removed = removeOwnedHookRegistrationFixture(applied, plan);
    assert.deepEqual(removed, unrelated);

    const instructions = formatCodexHookSetup(plan);
    assert.match(instructions, /Captured metadata:/u);
    assert.match(instructions, /Never captured:/u);
    assert.match(instructions, /Codex \/hooks/u);
    assert.match(instructions, /Removal:/u);
    assert.match(instructions, /does not enable or verify/u);
  });
});

test("removal requires the exact owned command and preserves concurrent edits", async () => {
  await withTempDirectory(async (directory) => {
    const installed = await installObserverAsset(
      resolve(process.cwd(), "observer", "codex_hook_observer.py"),
      join(directory, "assets"),
    );
    const plan = createCodexHookSetup({
      pythonPath: resolve(directory, "python.exe"),
      observerPath: installed.observerPath,
      observerSha256: installed.sha256,
      registryDirectory: resolve(directory, "registry"),
    });
    const applied = applyOwnedHookRegistrationFixture({}, plan);
    const hooks = (applied.hooks as Record<string, Array<{ hooks: Array<Record<string, unknown>> }>>);
    hooks.SessionStart![0]!.hooks[0]!.commandWindows = `${plan.commandWindows} --changed`;
    const removed = removeOwnedHookRegistrationFixture(applied, plan);
    const remaining = (removed.hooks as Record<string, unknown[]>).SessionStart;
    assert.equal(remaining?.length, 1);
  });
});
