import { constants as fsConstants } from "node:fs";
import {
  chmod,
  link,
  lstat,
  mkdir,
  open,
  readFile,
  realpath,
  unlink,
} from "node:fs/promises";
import { isAbsolute, join, resolve } from "node:path";
import { randomUUID } from "node:crypto";

import {
  CODEX_MONITOR_OWNER,
  CODEX_OBSERVER_SHA256,
  CODEX_SOURCE_ID,
  CODEX_SUPPORTED_EVENTS,
} from "./constants";
import { sha256Hex } from "./protocol";
import type {
  CodexHookSetupPlan,
  CreateCodexHookSetupOptions,
  InstalledObserverAsset,
} from "./types";

const ASSET_FILENAME = "codex_hook_observer.py";

function requireSafeAbsolutePath(value: string, label: string): string {
  if (!isAbsolute(value) || value.includes("\0") || /[\r\n"%!]/u.test(value)) {
    throw new Error(
      `${label} must be an absolute path without command-expansion or control characters.`,
    );
  }
  return resolve(value);
}

function quoteWindowsArgument(value: string): string {
  // CommandLineToArgvW-compatible quoting. Paths containing quotes were
  // rejected above, but the full algorithm also handles trailing slashes.
  return `"${value.replace(/(\\*)"/gu, "$1$1\\\"").replace(/(\\+)$/u, "$1$1")}"`;
}

function exactHookHandler(command: string, commandWindows: string, event: string): Record<string, unknown> {
  const handler: Record<string, unknown> = {
    type: "command",
    command,
    commandWindows,
    timeout: 1,
  };
  if (event !== "SessionEnd") {
    handler.async = true;
  }
  return handler;
}

function createConfigFragment(command: string, commandWindows: string): Record<string, unknown> {
  const hooks: Record<string, unknown> = {};
  for (const event of CODEX_SUPPORTED_EVENTS) {
    hooks[event] = [{ hooks: [exactHookHandler(command, commandWindows, event)] }];
  }
  return { hooks };
}

export function createCodexHookSetup(options: CreateCodexHookSetupOptions): CodexHookSetupPlan {
  const pythonPath = requireSafeAbsolutePath(options.pythonPath, "Python path");
  const observerPath = requireSafeAbsolutePath(options.observerPath, "Observer path");
  const registryDirectory = requireSafeAbsolutePath(options.registryDirectory, "Registry directory");
  if (options.observerSha256 !== CODEX_OBSERVER_SHA256) {
    throw new Error("The installed observer does not match this extension build.");
  }

  const arguments_ = [
    pythonPath,
    "-I",
    "-B",
    "-S",
    observerPath,
    "--registry",
    registryDirectory,
    "--owner",
    CODEX_MONITOR_OWNER,
    "--observer-sha256",
    CODEX_OBSERVER_SHA256,
  ];
  const commandWindows = arguments_.map(quoteWindowsArgument).join(" ");
  // A command is required even when commandWindows is present. AIO-030 is
  // Windows-only, so both fixed values deliberately describe the same command.
  const command = commandWindows;

  return Object.freeze({
    owner: CODEX_MONITOR_OWNER,
    observerSha256: CODEX_OBSERVER_SHA256,
    source: CODEX_SOURCE_ID,
    command,
    commandWindows,
    configFragment: createConfigFragment(command, commandWindows),
    capturedMetadata: Object.freeze([
      "Codex lifecycle event category",
      "source-scoped session, turn, subagent, and tool-call identifiers when reported",
      "bounded tool and subagent labels when reported",
      "source-reported model when reported",
      "selected-root association and local receipt time",
    ]),
    excludedData: Object.freeze([
      "prompts and assistant responses",
      "source code and diffs",
      "tool arguments and results",
      "transcripts and transcript paths",
      "environment data, credentials, headers, and permission mode",
    ]),
    destination:
      "Authenticated 127.0.0.1 listener for the explicitly selected VS Code window; memory only.",
    trustNotice:
      "Copying this fragment does not enable or verify the hook. Codex must perform its own hash-bound hook trust review.",
    removalNotice:
      "Remove only handlers whose exact command and commandWindows values match this owner/hash-bound plan.",
  });
}

export function formatCodexHookSetup(plan: CodexHookSetupPlan): string {
  const captured = plan.capturedMetadata.map((item) => `- ${item}`).join("\n");
  const excluded = plan.excludedData.map((item) => `- ${item}`).join("\n");
  return [
    "AIO Codex lifecycle-hook observation (Windows, user-mediated)",
    "",
    "Captured metadata:",
    captured,
    "",
    "Never captured:",
    excluded,
    "",
    `Destination: ${plan.destination}`,
    "",
    "Setup:",
    "1. Review and merge the fragment below into your user-level Codex hooks configuration.",
    "2. Use Codex /hooks to review and trust the exact hash-bound command; AIO does not bypass that review.",
    "3. Return to the Control Center. Setup remains unverified until an authenticated event arrives.",
    "",
    JSON.stringify(plan.configFragment, null, 2),
    "",
    "Removal:",
    `1. ${plan.removalNotice}`,
    "2. Save the configuration and use Codex's normal hook review flow for the resulting configuration.",
    "3. Stop observation in AIO to remove its local descriptor and clear its in-memory timeline.",
    "",
    plan.trustNotice,
  ].join("\n");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function cloneFixture<T>(value: T): T {
  return structuredClone(value);
}

function isOwnedHandler(value: unknown, plan: CodexHookSetupPlan): boolean {
  return (
    isRecord(value) &&
    value.type === "command" &&
    value.command === plan.command &&
    value.commandWindows === plan.commandWindows
  );
}

/** Pure helper for disposable tests and previews. It never reads or writes Codex configuration. */
export function applyOwnedHookRegistrationFixture(
  config: unknown,
  plan: CodexHookSetupPlan,
): Record<string, unknown> {
  if (!isRecord(config)) {
    throw new Error("Fixture configuration must be an object.");
  }
  const result = cloneFixture(config);
  const existingHooks = result.hooks;
  if (existingHooks !== undefined && !isRecord(existingHooks)) {
    throw new Error("Fixture hooks must be an object when present.");
  }
  const hooks: Record<string, unknown> = existingHooks ?? {};
  result.hooks = hooks;
  const fragmentHooks = (plan.configFragment as { hooks: Record<string, unknown> }).hooks;

  for (const event of CODEX_SUPPORTED_EVENTS) {
    const existing = hooks[event];
    if (existing !== undefined && !Array.isArray(existing)) {
      throw new Error(`Fixture hook event ${event} must be an array.`);
    }
    const groups = (existing ?? []) as unknown[];
    const alreadyPresent = groups.some(
      (group) =>
        isRecord(group) &&
        Array.isArray(group.hooks) &&
        group.hooks.some((handler) => isOwnedHandler(handler, plan)),
    );
    if (!alreadyPresent) {
      const ownedGroups = fragmentHooks[event] as unknown[];
      groups.push(cloneFixture(ownedGroups[0]));
    }
    hooks[event] = groups;
  }
  return result;
}

/** Pure helper for disposable tests and previews. It removes only exact owned handlers. */
export function removeOwnedHookRegistrationFixture(
  config: unknown,
  plan: CodexHookSetupPlan,
): Record<string, unknown> {
  if (!isRecord(config)) {
    throw new Error("Fixture configuration must be an object.");
  }
  const result = cloneFixture(config);
  if (!isRecord(result.hooks)) {
    return result;
  }
  const hooks = result.hooks;
  for (const event of CODEX_SUPPORTED_EVENTS) {
    const existing = hooks[event];
    if (!Array.isArray(existing)) {
      continue;
    }
    const retainedGroups: unknown[] = [];
    for (const group of existing) {
      if (!isRecord(group) || !Array.isArray(group.hooks)) {
        retainedGroups.push(group);
        continue;
      }
      const retainedHandlers = group.hooks.filter((handler) => !isOwnedHandler(handler, plan));
      if (retainedHandlers.length > 0) {
        group.hooks = retainedHandlers;
        retainedGroups.push(group);
      } else if (Object.keys(group).some((key) => key !== "hooks")) {
        group.hooks = [];
        retainedGroups.push(group);
      }
    }
    if (retainedGroups.length > 0) {
      hooks[event] = retainedGroups;
    } else {
      delete hooks[event];
    }
  }
  return result;
}

async function requireRegularNonSymlink(pathValue: string): Promise<void> {
  const info = await lstat(pathValue);
  if (!info.isFile() || info.isSymbolicLink()) {
    throw new Error("Observer asset must be a regular non-symlink file.");
  }
}

async function requireDirectoryNonSymlink(pathValue: string): Promise<void> {
  const info = await lstat(pathValue);
  if (!info.isDirectory() || info.isSymbolicLink()) {
    throw new Error("Observer install location must be a regular non-symlink directory.");
  }
}

async function verifyInstalledTarget(target: string, expectedHash: string): Promise<void> {
  await requireRegularNonSymlink(target);
  const targetHash = sha256Hex(await readFile(target));
  if (targetHash !== expectedHash) {
    throw new Error("Existing content-addressed observer asset has unexpected bytes.");
  }
}

export async function installObserverAsset(
  sourcePath: string,
  installRoot: string,
): Promise<InstalledObserverAsset> {
  const absoluteSource = requireSafeAbsolutePath(sourcePath, "Observer source path");
  const absoluteInstallRoot = requireSafeAbsolutePath(installRoot, "Observer install root");
  await requireRegularNonSymlink(absoluteSource);
  const sourceBytes = await readFile(absoluteSource);
  const sha256 = sha256Hex(sourceBytes);
  if (sha256 !== CODEX_OBSERVER_SHA256) {
    throw new Error("Bundled observer hash does not match the extension build pin.");
  }

  await mkdir(absoluteInstallRoot, { recursive: true, mode: 0o700 });
  await requireDirectoryNonSymlink(absoluteInstallRoot);
  const canonicalInstallRoot = await realpath(absoluteInstallRoot);
  const assetRoot = join(canonicalInstallRoot, "codex-observer");
  const versionRoot = join(assetRoot, sha256);
  await mkdir(versionRoot, { recursive: true, mode: 0o700 });
  await requireDirectoryNonSymlink(assetRoot);
  await requireDirectoryNonSymlink(versionRoot);

  const target = join(versionRoot, ASSET_FILENAME);
  try {
    await verifyInstalledTarget(target, sha256);
    return { observerPath: target, sha256 };
  } catch (error) {
    const code = (error as NodeJS.ErrnoException).code;
    if (code !== "ENOENT") {
      throw error;
    }
  }

  const temporary = join(versionRoot, `.${ASSET_FILENAME}.${randomUUID()}.tmp`);
  const handle = await open(
    temporary,
    fsConstants.O_CREAT | fsConstants.O_EXCL | fsConstants.O_WRONLY,
    0o600,
  );
  try {
    await handle.writeFile(sourceBytes);
    await handle.sync();
  } finally {
    await handle.close();
  }
  await chmod(temporary, 0o400);
  try {
    // link() creates the final name atomically and never replaces an existing
    // immutable hash target. Both paths are on the same extension-owned volume.
    await link(temporary, target);
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code !== "EEXIST") {
      await unlink(temporary).catch(() => undefined);
      throw error;
    }
  }
  await unlink(temporary).catch(() => undefined);
  await verifyInstalledTarget(target, sha256);
  return { observerPath: target, sha256 };
}
