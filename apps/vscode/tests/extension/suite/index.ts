import assert from "node:assert/strict";
import { mkdir, mkdtemp, realpath, rm, symlink, unlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";

import * as vscode from "vscode";
import { CoreClientError } from "../../../src/coreClient/client";
import {
  CODEX_OBSERVER_SHA256,
  type CodexMonitorOptions,
  type CodexMonitorSnapshot,
  type CodexMonitorStopReason,
} from "../../../src/monitoring/codex";
import type { BridgeResponse, ProjectSnapshotResult } from "../../../src/coreClient/protocol";
import {
  ControlCenterController,
  type ControllerMonitorHandle,
} from "../../../src/views/controller";
import type { ControlCenterState } from "../../../src/views/model";
import { canonicalRootsMatch, type RootLifecycleIdentity } from "../../../src/views/selection";

const EXTENSION_ID = "aio-local-dev.aio-control-center-dev";

function deferred<T>(): {
  readonly promise: Promise<T>;
  readonly resolve: (value: T) => void;
} {
  let resolvePromise: ((value: T) => void) | undefined;
  const promise = new Promise<T>((resolve) => {
    resolvePromise = resolve;
  });
  return {
    promise,
    resolve: (value) => resolvePromise?.(value),
  };
}

function monitorSnapshot(listener: "stopped" | "listening"): CodexMonitorSnapshot {
  return {
    state: listener === "listening" ? "configured_no_observations" : "disconnected",
    listener,
    setup: listener === "listening" ? "unverified" : "not_configured",
    source: "codex.lifecycle-hooks/v1",
    rootFingerprint: "0".repeat(64),
    events: [],
    sessions: [],
  };
}

class DeferredControllerMonitor implements ControllerMonitorHandle {
  public readonly startEntered = deferred<void>();
  public readonly startRelease = deferred<void>();
  public listening = false;
  public stopped = false;
  public disposed = false;
  public stopReason: CodexMonitorStopReason | undefined;

  public async start(): Promise<CodexMonitorSnapshot> {
    this.startEntered.resolve();
    await this.startRelease.promise;
    if (!this.stopped && !this.disposed) {
      this.listening = true;
    }
    return monitorSnapshot(this.listening ? "listening" : "stopped");
  }

  public async stop(reason: CodexMonitorStopReason = "user"): Promise<CodexMonitorSnapshot> {
    this.stopReason = reason;
    this.stopped = true;
    this.listening = false;
    this.startRelease.resolve();
    return monitorSnapshot("stopped");
  }

  public async dispose(): Promise<void> {
    this.disposed = true;
    this.stopped = true;
    this.listening = false;
    this.startRelease.resolve();
  }

  public snapshot(): CodexMonitorSnapshot {
    return monitorSnapshot(this.listening ? "listening" : "stopped");
  }
}

interface ControllerPrivateAccess {
  selectedFolder: vscode.WorkspaceFolder | undefined;
  lastBoundCanonicalRoot: string | undefined;
  canonicalRoot: string | undefined;
  pythonPath: string | undefined;
  monitor: ControllerMonitorHandle | undefined;
  pendingMonitor: { readonly epoch: number; readonly monitor: ControllerMonitorHandle } | undefined;
  activeObservation: RootLifecycleIdentity | undefined;
  hookPlan: unknown;
  generation: number;
  observationEpoch: number;
  state: ControlCenterState;
  coreClient: {
    request(
      pythonPath: string,
      canonicalRoot: string,
      operation: "project_snapshot",
      payload: { status: string | null; workflow: string | null },
      generation: number,
    ): Promise<{
      requestId: string;
      generation: number;
      response: BridgeResponse<ProjectSnapshotResult>;
    }>;
  };
  changeProject(folder: vscode.WorkspaceFolder | undefined): Promise<void>;
  invalidateObservation(reason: "root-changed" | "interpreter-changed" | "error"): Promise<void>;
  hasManifestMarker(folder: vscode.WorkspaceFolder): Promise<boolean>;
  applyClientFailure(error: unknown): void;
}

function fakeContext(storageDirectory: string): vscode.ExtensionContext {
  const state = new Map<string, unknown>();
  return {
    extensionUri: vscode.Uri.file(path.resolve(__dirname, "../../..")),
    globalStorageUri: vscode.Uri.file(storageDirectory),
    globalState: {
      get: <T>(key: string, defaultValue?: T): T | undefined =>
        (state.has(key) ? state.get(key) : defaultValue) as T | undefined,
      update: async (key: string, value: unknown): Promise<void> => {
        state.set(key, value);
      },
      keys: () => [...state.keys()],
      setKeysForSync: () => undefined,
    },
  } as unknown as vscode.ExtensionContext;
}

function successfulProjectSnapshot(generation: number, projectId = "test-project"): {
  requestId: string;
  generation: number;
  response: BridgeResponse<ProjectSnapshotResult>;
} {
  return {
    requestId: "controller-root-refresh",
    generation,
    response: {
      protocol: "aio.ide/1",
      request_id: "controller-root-refresh",
      ok: true,
      meta: {
        package_version: "0.1.0",
        package_origin: "C:\\trusted-python\\site-packages\\engineering_orchestration",
      },
      result: {
        project: { state: "managed", id: projectId, name: `Test Project ${projectId}` },
        snapshot_at: "2026-09-19T00:00:00Z",
        tasks: [],
        anomalies: [],
        filters: { statuses: ["in_progress"], workflows: ["security-sensitive-change"] },
        validation: { status: "PASS", findings: [] },
      },
      diagnostics: [],
    },
  };
}

interface JunctionFixture {
  readonly directory: string;
  readonly targetA: string;
  readonly targetB: string;
  readonly link: string;
  readonly folder: vscode.WorkspaceFolder;
}

async function createJunctionFixture(prefix: string): Promise<JunctionFixture> {
  const directory = await mkdtemp(path.join(tmpdir(), prefix));
  const targetA = path.join(directory, "target-a");
  const targetB = path.join(directory, "target-b");
  const link = path.join(directory, "selected-project");
  for (const [target, id] of [[targetA, "project-a"], [targetB, "project-b"]] as const) {
    await mkdir(path.join(target, ".ai"), { recursive: true });
    await writeFile(path.join(target, ".ai", "project.yaml"), `project:\n  id: ${id}\n`, "utf8");
  }
  await symlink(targetA, link, "junction");
  return {
    directory,
    targetA,
    targetB,
    link,
    folder: {
      uri: vscode.Uri.file(link),
      name: "Junction project",
      index: 0,
    },
  };
}

async function retargetJunction(fixture: JunctionFixture, target: string): Promise<void> {
  await unlink(fixture.link);
  await symlink(target, fixture.link, "junction");
}

async function removeJunctionFixture(fixture: JunctionFixture): Promise<void> {
  await unlink(fixture.link).catch(() => undefined);
  await rm(fixture.directory, { recursive: true, force: true });
}

function junctionController(
  fixture: JunctionFixture,
  monitor: DeferredControllerMonitor,
  confirmObservation: () => Promise<string | undefined>,
): { readonly controller: ControlCenterController; readonly access: ControllerPrivateAccess } {
  const controller = new ControlCenterController(fakeContext(path.join(fixture.directory, "storage")), {
    confirmObservation,
    installObserver: async () => ({
      observerPath: path.join(fixture.directory, "codex_hook_observer.py"),
      sha256: CODEX_OBSERVER_SHA256,
    }),
    createMonitor: () => monitor,
  });
  const access = controller as unknown as ControllerPrivateAccess;
  access.selectedFolder = fixture.folder;
  access.pythonPath = process.env.AIO_TEST_PYTHON ?? process.execPath;
  return { controller, access };
}

async function startJunctionObservation(
  controller: ControlCenterController,
  monitor: DeferredControllerMonitor,
): Promise<void> {
  monitor.startRelease.resolve();
  await controller.startObserving();
  assert.equal(monitor.listening, true);
}

async function exerciseControllerObservationInterleavings(): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  assert.ok(folder);
  const storageDirectory = await mkdtemp(path.join(tmpdir(), "aio-controller-race-"));
  const pythonPath = process.env.AIO_TEST_PYTHON ?? process.execPath;
  const observerPath = path.join(storageDirectory, "codex_hook_observer.py");
  const configure = (controller: ControlCenterController): ControllerPrivateAccess => {
    const access = controller as unknown as ControllerPrivateAccess;
    access.selectedFolder = folder;
    access.canonicalRoot = folder.uri.fsPath;
    access.pythonPath = pythonPath;
    return access;
  };

  try {
    const confirmationEntered = deferred<void>();
    const confirmation = deferred<string | undefined>();
    let consentCreateCount = 0;
    const consentController = new ControlCenterController(fakeContext(storageDirectory), {
      confirmObservation: () => {
        confirmationEntered.resolve();
        return confirmation.promise;
      },
      createMonitor: (_options: CodexMonitorOptions) => {
        consentCreateCount += 1;
        return new DeferredControllerMonitor();
      },
    });
    configure(consentController);
    const consentStart = consentController.startObserving();
    await confirmationEntered.promise;
    await consentController.stopObserving("user");
    confirmation.resolve("Start observer");
    await consentStart;
    assert.equal(consentCreateCount, 0, "Stop during consent must prevent monitor creation.");
    consentController.dispose();

    const installEntered = deferred<void>();
    const installRelease = deferred<void>();
    let installCreateCount = 0;
    const installController = new ControlCenterController(fakeContext(storageDirectory), {
      confirmObservation: async () => "Start observer",
      installObserver: async () => {
        installEntered.resolve();
        await installRelease.promise;
        return { observerPath, sha256: CODEX_OBSERVER_SHA256 };
      },
      createMonitor: () => {
        installCreateCount += 1;
        return new DeferredControllerMonitor();
      },
    });
    const installAccess = configure(installController);
    const installStart = installController.startObserving();
    await installEntered.promise;
    const rootChange = installAccess.changeProject(undefined);
    installRelease.resolve();
    await Promise.all([installStart, rootChange]);
    assert.equal(installCreateCount, 0, "Root change during installation must prevent monitor creation.");
    assert.equal(installAccess.monitor, undefined);
    assert.equal(installAccess.pendingMonitor, undefined);
    installController.dispose();

    for (const action of ["stop", "root", "interpreter", "dispose"] as const) {
      const fakeMonitor = new DeferredControllerMonitor();
      const controller = new ControlCenterController(fakeContext(storageDirectory), {
        confirmObservation: async () => "Start observer",
        installObserver: async () => ({ observerPath, sha256: CODEX_OBSERVER_SHA256 }),
        createMonitor: () => fakeMonitor,
      });
      const access = configure(controller);
      const starting = controller.startObserving();
      await fakeMonitor.startEntered.promise;
      if (action === "stop") {
        await controller.stopObserving("user");
      } else if (action === "root") {
        await access.changeProject(undefined);
      } else if (action === "interpreter") {
        await access.invalidateObservation("interpreter-changed");
      } else {
        controller.dispose();
      }
      await starting;
      assert.equal(fakeMonitor.listening, false, `${action} must not leave a pending listener alive.`);
      assert.equal(fakeMonitor.stopped, true, `${action} must claim and stop the pending monitor.`);
      assert.equal(fakeMonitor.disposed, true, `${action} must dispose the pending monitor.`);
      assert.equal(access.monitor, undefined, `${action} must not promote a stale monitor.`);
      assert.equal(access.pendingMonitor, undefined, `${action} must clear pending ownership.`);
      controller.dispose();
    }
  } finally {
    await rm(storageDirectory, { recursive: true, force: true });
  }
}

async function exerciseCanonicalRootRefreshInvalidation(): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  assert.ok(folder);
  const storageDirectory = await mkdtemp(path.join(tmpdir(), "aio-controller-root-refresh-"));
  const pythonPath = process.env.AIO_TEST_PYTHON ?? process.execPath;
  let confirmationCount = 0;
  const controller = new ControlCenterController(fakeContext(storageDirectory), {
    confirmObservation: async () => {
      confirmationCount += 1;
      return undefined;
    },
  });
  const access = controller as unknown as ControllerPrivateAccess;
  const activeMonitor = new DeferredControllerMonitor();
  const pendingMonitor = new DeferredControllerMonitor();
  try {
    access.selectedFolder = folder;
    access.canonicalRoot = path.join(folder.uri.fsPath, "previous-junction-target");
    access.lastBoundCanonicalRoot = access.canonicalRoot;
    access.pythonPath = pythonPath;
    access.monitor = activeMonitor;
    access.pendingMonitor = { epoch: access.observationEpoch, monitor: pendingMonitor };
    access.activeObservation = {
      token: access.observationEpoch,
      projectKey: folder.uri.toString(),
      canonicalRoot: access.canonicalRoot,
      pythonPath,
    };
    access.hookPlan = { existingConsent: true };
    access.state.filters.status = "in_progress";
    access.state.filters.workflow = "security-sensitive-change";
    const previousObservationEpoch = access.observationEpoch;
    let markerChecks = 0;
    let coreCalls = 0;
    access.hasManifestMarker = async () => {
      markerChecks += 1;
      return true;
    };
    access.coreClient.request = async (_python, _root, _operation, _payload, generation) => {
      coreCalls += 1;
      assert.equal(activeMonitor.disposed, true, "The old active monitor must stop before a new snapshot is published.");
      assert.equal(pendingMonitor.disposed, true, "The pending monitor must stop before a new snapshot is published.");
      assert.equal(access.activeObservation, undefined);
      assert.equal(access.hookPlan, undefined);
      return successfulProjectSnapshot(generation);
    };

    await controller.refresh();

    assert.equal(markerChecks, 1, "Only the replacement root may be checked for a project marker.");
    assert.equal(coreCalls, 1, "Core must only inspect the newly resolved root after invalidation.");
    assert.equal(activeMonitor.stopReason, "root-changed");
    assert.equal(activeMonitor.stopped, true);
    assert.equal(activeMonitor.disposed, true);
    assert.equal(pendingMonitor.stopReason, "root-changed");
    assert.equal(pendingMonitor.stopped, true);
    assert.equal(pendingMonitor.disposed, true);
    assert.equal(access.monitor, undefined);
    assert.equal(access.pendingMonitor, undefined);
    assert.equal(access.activeObservation, undefined);
    assert.equal(access.hookPlan, undefined);
    assert.ok(access.observationEpoch > previousObservationEpoch, "The old consent lifecycle must be invalidated.");
    assert.equal(access.state.filters.status, null, "A root identity change must reset the status filter.");
    assert.equal(access.state.filters.workflow, null, "A root identity change must reset the workflow filter.");
    assert.equal(access.state.project.id, "test-project");
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", folder.uri.fsPath), true);

    await controller.startObserving();
    assert.equal(confirmationCount, 1, "Observation on the new root must request fresh consent.");
  } finally {
    controller.dispose();
    await rm(storageDirectory, { recursive: true, force: true });
  }
}

async function exerciseObservationPublicationBinding(): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  assert.ok(folder);
  const storageDirectory = await mkdtemp(path.join(tmpdir(), "aio-controller-publication-"));
  const pythonPath = process.env.AIO_TEST_PYTHON ?? process.execPath;
  const fakeMonitor = new DeferredControllerMonitor();
  let publish: ((snapshot: CodexMonitorSnapshot) => void) | undefined;
  const controller = new ControlCenterController(fakeContext(storageDirectory), {
    confirmObservation: async () => "Start observer",
    installObserver: async () => ({
      observerPath: path.join(storageDirectory, "codex_hook_observer.py"),
      sha256: CODEX_OBSERVER_SHA256,
    }),
    createMonitor: (options) => {
      publish = options.onDidChange;
      return fakeMonitor;
    },
  });
  const access = controller as unknown as ControllerPrivateAccess;
  try {
    const root = await realpath(folder.uri.fsPath);
    access.selectedFolder = folder;
    access.lastBoundCanonicalRoot = root;
    access.canonicalRoot = root;
    access.pythonPath = pythonPath;
    const starting = controller.startObserving();
    await fakeMonitor.startEntered.promise;
    fakeMonitor.startRelease.resolve();
    await starting;
    assert.ok(publish);

    const accepted: CodexMonitorSnapshot = {
      ...monitorSnapshot("listening"),
      state: "receiving",
    };
    publish(accepted);
    assert.equal(access.state.monitoring.state, "receiving");

    access.coreClient.request = async () => {
      throw new Error("intentional same-root Core failure");
    };
    await controller.refresh();
    assert.equal(access.canonicalRoot, undefined);
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", root), true);
    assert.equal(access.monitor, fakeMonitor);
    publish({ ...monitorSnapshot("listening"), state: "stale" });
    assert.equal(
      access.state.monitoring.state,
      "stale",
      "A same-root Core failure must not suppress the retained monitor's freshness updates.",
    );

    access.canonicalRoot = path.join(folder.uri.fsPath, "different-root");
    publish({ ...monitorSnapshot("listening"), state: "error", listener: "error", error: "wrong root" });
    assert.equal(access.state.monitoring.state, "stale", "A callback bound to another root must be ignored.");

    access.canonicalRoot = root;
    access.observationEpoch += 1;
    publish({ ...monitorSnapshot("listening"), state: "error", listener: "error", error: "late" });
    assert.equal(access.state.monitoring.state, "stale", "A callback from an old lifecycle must be ignored.");
  } finally {
    controller.dispose();
    await rm(storageDirectory, { recursive: true, force: true });
  }
}

async function exerciseUncRejectionBeforeInspection(): Promise<void> {
  const storageDirectory = await mkdtemp(path.join(tmpdir(), "aio-controller-unc-"));
  const controller = new ControlCenterController(fakeContext(storageDirectory));
  const access = controller as unknown as ControllerPrivateAccess;
  const fakeMonitor = new DeferredControllerMonitor();
  const uncFolder = {
    uri: vscode.Uri.file("\\\\server\\share\\project"),
    name: "UNC project",
    index: 0,
  } as vscode.WorkspaceFolder;
  let markerChecks = 0;
  let coreCalls = 0;
  try {
    access.selectedFolder = uncFolder;
    access.canonicalRoot = "C:\\previous-local-root";
    access.lastBoundCanonicalRoot = access.canonicalRoot;
    access.pythonPath = process.env.AIO_TEST_PYTHON ?? process.execPath;
    access.monitor = fakeMonitor;
    access.hasManifestMarker = async () => {
      markerChecks += 1;
      return true;
    };
    access.coreClient.request = async (_python, _root, _operation, _payload, generation) => {
      coreCalls += 1;
      return successfulProjectSnapshot(generation);
    };

    await controller.refresh();

    assert.equal(markerChecks, 0, "UNC rejection must happen before the project marker is read.");
    assert.equal(coreCalls, 0, "UNC rejection must happen before Core is invoked.");
    assert.equal(fakeMonitor.stopReason, "root-changed");
    assert.equal(fakeMonitor.stopped, true);
    assert.equal(fakeMonitor.disposed, true);
    assert.equal(access.state.platformSupported, false);
    assert.equal(access.state.project.state, "error");
    assert.equal(access.state.core.state, "incompatible");
    assert.equal(access.state.monitoring.state, "unsupported");
    assert.equal(access.canonicalRoot, undefined);
    assert.equal(access.lastBoundCanonicalRoot, undefined);
  } finally {
    controller.dispose();
    await rm(storageDirectory, { recursive: true, force: true });
  }
}

async function exerciseDurableRootAfterFailedRefresh(): Promise<void> {
  const fixture = await createJunctionFixture("aio-controller-durable-root-");
  const monitor = new DeferredControllerMonitor();
  let confirmations = 0;
  const { controller, access } = junctionController(fixture, monitor, async () => {
    confirmations += 1;
    return confirmations === 1 ? "Start observer" : undefined;
  });
  const rootA = await realpath(fixture.targetA);
  const rootB = await realpath(fixture.targetB);
  let coreCalls = 0;
  access.coreClient.request = async (_python, root, _operation, _payload, generation) => {
    coreCalls += 1;
    if (coreCalls === 1) {
      assert.equal(canonicalRootsMatch(root, rootA), true);
      return successfulProjectSnapshot(generation, "project-a");
    }
    if (coreCalls === 2) {
      assert.equal(canonicalRootsMatch(root, rootA), true);
      throw new Error("intentional Core failure on root A");
    }
    assert.equal(coreCalls, 3);
    assert.equal(canonicalRootsMatch(root, rootB), true);
    assert.equal(monitor.disposed, true, "The A observer must stop before Core inspects B.");
    assert.equal(access.activeObservation, undefined);
    assert.equal(access.hookPlan, undefined);
    return successfulProjectSnapshot(generation, "project-b");
  };

  try {
    await controller.refresh();
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", rootA), true);
    await startJunctionObservation(controller, monitor);

    await controller.refresh();
    assert.equal(access.canonicalRoot, undefined);
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", rootA), true);
    assert.equal(access.monitor, monitor, "An ordinary Core failure must not silently replace root identity.");
    assert.equal(monitor.stopped, false);

    access.state.filters.status = "stale-status";
    access.state.filters.workflow = "stale-workflow";
    await retargetJunction(fixture, fixture.targetB);
    await controller.refresh();

    assert.equal(coreCalls, 3);
    assert.equal(monitor.stopReason, "root-changed");
    assert.equal(monitor.disposed, true);
    assert.equal(access.monitor, undefined);
    assert.equal(access.pendingMonitor, undefined);
    assert.equal(access.activeObservation, undefined);
    assert.equal(access.hookPlan, undefined);
    assert.equal(access.state.monitoring.listener, "stopped");
    assert.equal(access.state.filters.status, null);
    assert.equal(access.state.filters.workflow, null);
    assert.equal(access.state.project.id, "project-b");
    assert.equal(canonicalRootsMatch(access.canonicalRoot ?? "", rootB), true);
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", rootB), true);

    await controller.startObserving();
    assert.equal(confirmations, 2, "Root B must require consent independent of the old A observer.");
  } finally {
    controller.dispose();
    await removeJunctionFixture(fixture);
  }
}

async function exerciseOverlappingRefreshRetarget(): Promise<void> {
  const fixture = await createJunctionFixture("aio-controller-overlap-root-");
  const monitor = new DeferredControllerMonitor();
  const { controller, access } = junctionController(fixture, monitor, async () => "Start observer");
  const rootA = await realpath(fixture.targetA);
  const rootB = await realpath(fixture.targetB);
  const lateEntered = deferred<void>();
  const lateResponse = deferred<{
    requestId: string;
    generation: number;
    response: BridgeResponse<ProjectSnapshotResult>;
  }>();
  let lateGeneration = 0;
  let coreCalls = 0;
  access.coreClient.request = async (_python, root, _operation, _payload, generation) => {
    coreCalls += 1;
    if (coreCalls === 1) {
      return successfulProjectSnapshot(generation, "project-a");
    }
    if (coreCalls === 2) {
      assert.equal(canonicalRootsMatch(root, rootA), true);
      lateGeneration = generation;
      lateEntered.resolve();
      return lateResponse.promise;
    }
    assert.equal(coreCalls, 3);
    assert.equal(canonicalRootsMatch(root, rootB), true);
    assert.equal(monitor.disposed, true);
    return successfulProjectSnapshot(generation, "project-b");
  };

  try {
    await controller.refresh();
    await startJunctionObservation(controller, monitor);

    const refreshA = controller.refresh();
    await lateEntered.promise;
    await retargetJunction(fixture, fixture.targetB);
    const refreshB = controller.refresh();
    await refreshB;
    lateResponse.resolve(successfulProjectSnapshot(lateGeneration, "late-project-a"));
    await refreshA;

    assert.equal(coreCalls, 3);
    assert.equal(monitor.stopReason, "root-changed");
    assert.equal(monitor.disposed, true);
    assert.equal(access.state.project.id, "project-b");
    assert.equal(canonicalRootsMatch(access.canonicalRoot ?? "", rootB), true);
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", rootB), true);
  } finally {
    controller.dispose();
    lateResponse.resolve(successfulProjectSnapshot(access.generation, "cleanup"));
    await removeJunctionFixture(fixture);
  }
}

async function exercisePostCoreRetargetRevalidation(): Promise<void> {
  const fixture = await createJunctionFixture("aio-controller-post-core-root-");
  const monitor = new DeferredControllerMonitor();
  const { controller, access } = junctionController(fixture, monitor, async () => "Start observer");
  const rootA = await realpath(fixture.targetA);
  const rootB = await realpath(fixture.targetB);
  const coreEntered = deferred<void>();
  const coreRelease = deferred<{
    requestId: string;
    generation: number;
    response: BridgeResponse<ProjectSnapshotResult>;
  }>();
  let pausedGeneration = 0;
  let coreCalls = 0;
  access.coreClient.request = async (_python, root, _operation, _payload, generation) => {
    coreCalls += 1;
    if (coreCalls === 1) {
      return successfulProjectSnapshot(generation, "project-a");
    }
    if (coreCalls === 2) {
      assert.equal(canonicalRootsMatch(root, rootA), true);
      pausedGeneration = generation;
      coreEntered.resolve();
      return coreRelease.promise;
    }
    assert.equal(coreCalls, 3);
    assert.equal(canonicalRootsMatch(root, rootB), true);
    assert.equal(monitor.disposed, true, "The A observer must stop before publishing B.");
    return successfulProjectSnapshot(generation, "project-b");
  };

  try {
    await controller.refresh();
    await startJunctionObservation(controller, monitor);

    const refreshing = controller.refresh();
    await coreEntered.promise;
    await retargetJunction(fixture, fixture.targetB);
    coreRelease.resolve(successfulProjectSnapshot(pausedGeneration, "stale-project-a"));
    await refreshing;

    assert.equal(coreCalls, 3, "A post-Core root mismatch must trigger a clean B refresh.");
    assert.equal(monitor.stopReason, "root-changed");
    assert.equal(monitor.disposed, true);
    assert.equal(access.state.project.id, "project-b");
    assert.equal(canonicalRootsMatch(access.canonicalRoot ?? "", rootB), true);
    assert.equal(canonicalRootsMatch(access.lastBoundCanonicalRoot ?? "", rootB), true);
  } finally {
    controller.dispose();
    coreRelease.resolve(successfulProjectSnapshot(access.generation, "cleanup"));
    await removeJunctionFixture(fixture);
  }
}

function exerciseIncompatibleCoreState(): void {
  const controller = new ControlCenterController(fakeContext(path.join(tmpdir(), "aio-controller-version")));
  const access = controller as unknown as ControllerPrivateAccess;
  try {
    access.applyClientFailure(new CoreClientError(
      "incompatible_core",
      "Core package version 0.2.0 is incompatible; this extension supports exactly 0.1.0.",
    ));
    assert.equal(access.state.project.state, "error");
    assert.equal(access.state.core.state, "incompatible");
    assert.match(access.state.core.message, /^incompatible_core:/u);
  } finally {
    controller.dispose();
  }
}

export async function run(): Promise<void> {
  const extension = vscode.extensions.getExtension(EXTENSION_ID);
  assert.ok(extension, `Expected development extension ${EXTENSION_ID}.`);
  await extension.activate();
  assert.equal(extension.isActive, true);

  const commands = new Set(await vscode.commands.getCommands(true));
  const expected = [
    "aioControlCenter.open",
    "aioControlCenter.refresh",
    "aioControlCenter.selectProject",
    "aioControlCenter.selectPython",
    "aioControlCenter.startObserving",
    "aioControlCenter.stopObserving",
    "aioControlCenter.copyHookSetup",
  ];
  for (const command of expected) {
    assert.equal(commands.has(command), true, `Missing command ${command}.`);
  }
  assert.equal(commands.has("aioControlCenter.verify"), false);
  assert.equal(commands.has("aioControlCenter.startCodex"), false);
  assert.equal(commands.has("aioControlCenter.approve"), false);

  assert.equal(vscode.workspace.workspaceFolders?.length, 1);
  assert.equal(vscode.workspace.workspaceFolders?.[0]?.uri.scheme, "file");
  await vscode.commands.executeCommand("aioControlCenter.refresh");
  await vscode.commands.executeCommand("aioControlCenter.stopObserving");
  await exerciseControllerObservationInterleavings();
  await exerciseCanonicalRootRefreshInvalidation();
  await exerciseObservationPublicationBinding();
  await exerciseUncRejectionBeforeInspection();
  await exerciseDurableRootAfterFailedRefresh();
  await exerciseOverlappingRefreshRetarget();
  await exercisePostCoreRetargetRevalidation();
  exerciseIncompatibleCoreState();
}
