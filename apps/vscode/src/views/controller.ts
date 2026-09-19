import { mkdir, realpath, stat } from "node:fs/promises";
import path from "node:path";
import * as vscode from "vscode";
import { CoreClient, CoreClientError } from "../coreClient/client";
import {
  isProjectSnapshotResult,
  isTaskDetailResult,
  type ArtifactDescriptor,
  type ProjectSnapshotResult,
  type TaskDetailResult,
} from "../coreClient/protocol";
import { canonicalDirectory, canonicalRegularFile, isContained } from "../coreClient/scope";
import {
  CodexMonitor,
  createCodexHookSetup,
  formatCodexHookSetup,
  installObserverAsset,
  type CodexHookSetupPlan,
  type CodexMonitorOptions,
  type CodexMonitorSnapshot,
  type CodexMonitorStopReason,
  type InstalledObserverAsset,
} from "../monitoring/codex";
import { directActionAllowed, parseWebviewAction } from "./messages";
import {
  applySnapshot,
  applyTaskDetail,
  EMPTY_MONITORING,
  initialState,
  resetProjectScopeData,
  type ControlCenterState,
} from "./model";
import {
  boundOperationIsCurrent,
  canonicalRootsMatch,
  isUncWorkspaceRoot,
  responseIsCurrent,
  rootLifecycleIsCurrent,
  type BoundOperationIdentity,
  type RootLifecycleIdentity,
} from "./selection";

const PYTHON_STATE_KEY = "aioControlCenter.trustedPythonPath";

export function platformIsSupported(remoteName: string | undefined, uiKind: vscode.UIKind): boolean {
  return process.platform === "win32" && remoteName === undefined && uiKind === vscode.UIKind.Desktop;
}

interface ArtifactTarget {
  root: string;
  absolutePath: string;
}

type ObservationStopReason = "user" | "root-changed" | "interpreter-changed" | "dispose" | "error";

type RefreshRootResolution =
  | { readonly state: "current"; readonly root: string }
  | { readonly state: "stale" }
  | { readonly state: "error"; readonly error: unknown };

export interface ControllerMonitorHandle {
  start(): Promise<CodexMonitorSnapshot>;
  stop(reason?: CodexMonitorStopReason): Promise<CodexMonitorSnapshot>;
  dispose(): Promise<void>;
  snapshot(): CodexMonitorSnapshot;
}

export interface ControlCenterControllerDependencies {
  readonly confirmObservation: (detail: string) => Thenable<string | undefined>;
  readonly installObserver: (
    sourcePath: string,
    assetDirectory: string,
  ) => Promise<InstalledObserverAsset>;
  readonly createMonitor: (options: CodexMonitorOptions) => ControllerMonitorHandle;
}

function defaultControllerDependencies(): ControlCenterControllerDependencies {
  return {
    confirmObservation: (detail) => vscode.window.showInformationMessage(
      "Start AIO observation for this selected root? The user-level hook transiently parses bounded local Codex hook input, retains only IDs/event labels/model metadata, and discards prompts, responses, arguments, results, source, diffs, and transcript paths. Hook installation and Codex trust remain a separate manual step.",
      { modal: true, detail },
      "Start observer",
    ),
    installObserver: installObserverAsset,
    createMonitor: (options) => new CodexMonitor(options),
  };
}

export class ControlCenterController implements vscode.Disposable {
  private readonly views = new Set<vscode.Webview>();
  private readonly coreClient: CoreClient;
  private readonly artifactTargets = new Map<string, ArtifactTarget>();
  private readonly state: ControlCenterState = initialState();
  private selectedFolder: vscode.WorkspaceFolder | undefined;
  // This identity survives ordinary snapshot failures. `canonicalRoot` below
  // is intentionally transient and means only that the current snapshot is
  // eligible for Task inspection and observation.
  private lastBoundCanonicalRoot: string | undefined;
  private canonicalRoot: string | undefined;
  private pythonPath: string | undefined;
  private monitor: ControllerMonitorHandle | undefined;
  private pendingMonitor: { readonly epoch: number; readonly monitor: ControllerMonitorHandle } | undefined;
  private activeObservation: RootLifecycleIdentity | undefined;
  private hookPlan: CodexHookSetupPlan | undefined;
  private generation = 0;
  private detailGeneration = 0;
  private observationEpoch = 0;
  private disposed = false;
  private readonly freshnessTimer: NodeJS.Timeout;
  private readonly dependencies: ControlCenterControllerDependencies;

  public constructor(
    private readonly context: vscode.ExtensionContext,
    dependencies: Partial<ControlCenterControllerDependencies> = {},
  ) {
    this.dependencies = { ...defaultControllerDependencies(), ...dependencies };
    this.coreClient = new CoreClient({ workingDirectory: context.globalStorageUri.fsPath });
    this.pythonPath = context.globalState.get<string>(PYTHON_STATE_KEY);
    this.state.trusted = vscode.workspace.isTrusted;
    this.state.platformSupported = platformIsSupported(vscode.env.remoteName, vscode.env.uiKind);
    this.freshnessTimer = setInterval(() => {
      const monitor = this.monitor;
      const binding = this.activeObservation;
      if (monitor && binding && this.observationPublicationIsCurrent(binding)) {
        this.state.monitoring = monitor.snapshot();
        this.broadcast();
      }
    }, 30_000);
  }

  public async initialize(): Promise<void> {
    await mkdir(this.context.globalStorageUri.fsPath, { recursive: true });
    const folders = vscode.workspace.workspaceFolders ?? [];
    if (folders.length === 1 && folders[0]?.uri.scheme === "file") {
      await this.changeProject(folders[0]);
      return;
    }
    this.state.project.message = folders.length > 1
      ? "Multiple workspace folders are open. Select exactly one managed project."
      : "Open a local filesystem workspace folder.";
    this.broadcast();
  }

  public attach(webview: vscode.Webview): vscode.Disposable {
    this.views.add(webview);
    const messages = webview.onDidReceiveMessage((message: unknown) => {
      void this.handleMessage(message);
    });
    void webview.postMessage({ type: "state", state: this.state });
    return new vscode.Disposable(() => {
      messages.dispose();
      this.views.delete(webview);
    });
  }

  public async handleMessage(message: unknown): Promise<void> {
    const action = parseWebviewAction(message);
    if (!action) {
      this.setNotice("Rejected an unsupported Control Center action.");
      return;
    }
    if (!directActionAllowed(action.type, vscode.workspace.isTrusted)) {
      this.setNotice("This action is disabled in Restricted Mode.");
      return;
    }
    switch (action.type) {
      case "ready":
        this.broadcast();
        return;
      case "refresh":
        await this.refresh();
        return;
      case "selectProject":
        await this.selectProject();
        return;
      case "selectPython":
        await this.selectPython();
        return;
      case "selectTask":
        await this.selectTask(action.taskId);
        return;
      case "setFilters":
        this.state.filters.status = action.status;
        this.state.filters.workflow = action.workflow;
        await this.refresh();
        return;
      case "openArtifact":
        await this.openArtifact(action.artifactId);
        return;
      case "startObserving":
        await this.startObserving();
        return;
      case "stopObserving":
        await this.stopObserving("user");
        return;
      case "copyHookSetup":
        await this.copyHookSetup();
    }
  }

  public async selectProject(): Promise<void> {
    if (!this.requireTrusted("Project selection")) {
      return;
    }
    const folders = (vscode.workspace.workspaceFolders ?? []).filter((folder) => folder.uri.scheme === "file");
    if (folders.length === 0) {
      this.setNotice("No local filesystem workspace folder is available.");
      return;
    }
    const items = folders.map((folder) => ({ label: folder.name, description: "Local workspace folder", folder }));
    const picked = await vscode.window.showQuickPick(items, {
      title: "Select one AIO project for this window",
      placeHolder: "Only the selected local workspace folder will be read",
    });
    if (picked) {
      await this.changeProject(picked.folder);
    }
  }

  public async selectPython(): Promise<void> {
    if (!this.requireTrusted("Interpreter selection")) {
      return;
    }
    const dialogOptions: vscode.OpenDialogOptions = {
      title: "Select a trusted installed Python interpreter containing AIO Core",
      canSelectMany: false,
      canSelectFiles: true,
      canSelectFolders: false,
      openLabel: "Use this interpreter",
    };
    if (process.platform === "win32") {
      dialogOptions.filters = { "Python executable": ["exe"] };
    }
    const selection = await vscode.window.showOpenDialog(dialogOptions);
    const selected = selection?.[0];
    if (!selected || selected.scheme !== "file") {
      return;
    }
    const invalidation = this.invalidateObservation("interpreter-changed");
    const selectionGeneration = this.generation;
    try {
      const [canonical] = await Promise.all([
        canonicalRegularFile(selected.fsPath),
        invalidation,
      ]);
      if (selectionGeneration !== this.generation || this.disposed) {
        return;
      }
      this.pythonPath = canonical;
      await this.context.globalState.update(PYTHON_STATE_KEY, canonical);
      if (selectionGeneration !== this.generation || this.disposed) {
        return;
      }
      await this.refresh();
    } catch (error) {
      if (selectionGeneration === this.generation && !this.disposed) {
        this.setNotice(error instanceof Error ? error.message : String(error));
      }
    }
  }

  public async refresh(): Promise<void> {
    const lastBoundCanonicalRoot = this.lastBoundCanonicalRoot;
    const currentGeneration = ++this.generation;
    ++this.detailGeneration;
    // A root becomes eligible for Task inspection or observation only after a
    // current, structurally valid Core snapshot succeeds.
    this.canonicalRoot = undefined;
    this.state.trusted = vscode.workspace.isTrusted;
    this.state.platformSupported = platformIsSupported(vscode.env.remoteName, vscode.env.uiKind);
    this.state.busy = true;
    this.state.notice = "";
    this.broadcast();

    const folder = this.selectedFolder;
    if (!folder) {
      this.lastBoundCanonicalRoot = undefined;
      this.state.project.state = "none";
      this.state.project.message = "Select one local workspace folder.";
      this.finishBusy();
      return;
    }
    this.state.project.workspaceLabel = folder.name;
    const projectKey = folder.uri.toString();
    if (isUncWorkspaceRoot(folder.uri.fsPath)) {
      this.lastBoundCanonicalRoot = undefined;
      const invalidation = this.invalidateObservation("root-changed");
      const invalidatedGeneration = this.generation;
      this.clearProjectData();
      this.state.platformSupported = false;
      this.state.project.state = "error";
      this.state.project.message = "UNC workspace roots are unsupported; no project marker or Core data was read.";
      this.state.core = {
        state: "incompatible",
        version: "",
        message: "Use a local Windows filesystem workspace. UNC roots are outside AIO-030 scope.",
      };
      this.state.monitoring = { ...EMPTY_MONITORING, state: "unsupported" };
      this.broadcast();
      await invalidation;
      if (
        !this.disposed &&
        responseIsCurrent(
          invalidatedGeneration,
          this.generation,
          projectKey,
          this.selectedFolder?.uri.toString() ?? "",
        )
      ) {
        this.state.monitoring = { ...EMPTY_MONITORING, state: "unsupported" };
        this.finishBusy();
      }
      return;
    }
    let candidateRoot: string | undefined;
    if (vscode.workspace.isTrusted && this.state.platformSupported) {
      const resolution = await this.resolveRefreshRoot(folder, currentGeneration, projectKey);
      if (resolution.state === "stale") {
        return;
      }
      if (resolution.state === "error") {
        await this.failRefreshRootResolution(folder, currentGeneration, projectKey, resolution.error);
        return;
      }
      candidateRoot = resolution.root;
      if (
        lastBoundCanonicalRoot !== undefined &&
        !canonicalRootsMatch(lastBoundCanonicalRoot, candidateRoot)
      ) {
        await this.changeProject(folder);
        return;
      }
    }
    const marker = await this.hasManifestMarker(folder);
    if (!responseIsCurrent(
      currentGeneration,
      this.generation,
      folder.uri.toString(),
      this.selectedFolder?.uri.toString() ?? "",
    )) {
      return;
    }
    if (!vscode.workspace.isTrusted) {
      const invalidation = this.invalidateObservation("error");
      const invalidatedGeneration = this.generation;
      this.clearProjectData();
      this.state.project.state = marker ? "managed" : "unmanaged";
      this.state.project.message = marker
        ? "A static AIO marker is present. Trust this workspace to connect Core."
        : "No .ai/project.yaml marker exists at the selected root.";
      this.state.core = { state: "restricted", version: "", message: "Python and monitoring are disabled in Restricted Mode." };
      this.broadcast();
      await invalidation;
      if (
        !this.disposed &&
        responseIsCurrent(
          invalidatedGeneration,
          this.generation,
          projectKey,
          this.selectedFolder?.uri.toString() ?? "",
        )
      ) {
        this.finishBusy();
      }
      return;
    }
    if (
      candidateRoot !== undefined &&
      !await this.revalidateRefreshRoot(folder, candidateRoot, currentGeneration, projectKey)
    ) {
      return;
    }
    if (!marker) {
      this.clearProjectData();
      this.state.project.state = "unmanaged";
      this.state.project.message = "No .ai/project.yaml marker exists at the selected root.";
      this.finishBusy();
      return;
    }
    if (!this.state.platformSupported) {
      this.clearProjectData();
      this.state.project.state = "managed";
      this.state.project.message = "AIO-030 supports Windows local desktop filesystem workspaces only.";
      this.state.core = { state: "incompatible", version: "", message: "Remote, WSL, container, web, and UNC cases are unsupported." };
      this.finishBusy();
      return;
    }
    if (!this.pythonPath) {
      this.clearProjectData();
      this.state.project.state = "managed";
      this.state.project.message = "Static AIO marker found; Core has not been connected.";
      this.state.core = { state: "unconfigured", version: "", message: "Select a trusted installed Python/Core environment." };
      this.finishBusy();
      return;
    }

    let inspectedRoot = candidateRoot;
    try {
      inspectedRoot ??= await canonicalDirectory(folder.uri.fsPath);
      if (!responseIsCurrent(
        currentGeneration,
        this.generation,
        folder.uri.toString(),
        this.selectedFolder?.uri.toString() ?? "",
      )) {
        return;
      }
      const call = await this.coreClient.request<ProjectSnapshotResult>(
        this.pythonPath,
        inspectedRoot,
        "project_snapshot",
        { status: this.state.filters.status, workflow: this.state.filters.workflow },
        currentGeneration,
      );
      if (!responseIsCurrent(
        call.generation,
        this.generation,
        folder.uri.toString(),
        this.selectedFolder?.uri.toString() ?? "",
      )) {
        return;
      }
      if (!await this.revalidateRefreshRoot(folder, inspectedRoot, currentGeneration, projectKey)) {
        return;
      }
      if (!call.response.ok) {
        this.applyBridgeFailure(call.response.error.code, call.response.error.message);
        return;
      }
      if (!isProjectSnapshotResult(call.response.result)) {
        throw new CoreClientError("malformed_response", "Core bridge returned the wrong operation result.");
      }
      this.lastBoundCanonicalRoot = inspectedRoot;
      this.canonicalRoot = inspectedRoot;
      applySnapshot(this.state, call.response.result, call.response.meta.package_version);
      this.state.selectedTask = null;
      this.state.workflow = null;
      this.artifactTargets.clear();
    } catch (error) {
      if (currentGeneration !== this.generation) {
        return;
      }
      if (
        inspectedRoot !== undefined &&
        !await this.revalidateRefreshRoot(folder, inspectedRoot, currentGeneration, projectKey)
      ) {
        return;
      }
      if (currentGeneration !== this.generation) {
        return;
      }
      this.applyClientFailure(error);
    } finally {
      if (currentGeneration === this.generation) {
        this.finishBusy();
      }
    }
  }

  public async selectTask(taskId: string): Promise<void> {
    const projectKey = this.selectedFolder?.uri.toString();
    if (
      !this.requireTrusted("Task inspection") ||
      !this.pythonPath ||
      !this.canonicalRoot ||
      !projectKey
    ) {
      return;
    }
    const attempt: BoundOperationIdentity = {
      token: ++this.detailGeneration,
      projectGeneration: this.generation,
      projectKey,
      canonicalRoot: this.canonicalRoot,
      pythonPath: this.pythonPath,
    };
    this.state.busy = true;
    this.broadcast();
    try {
      const call = await this.coreClient.request<TaskDetailResult>(
        attempt.pythonPath,
        attempt.canonicalRoot,
        "task_detail",
        { task_id: taskId },
        attempt.projectGeneration,
      );
      if (!this.taskDetailIsCurrent(attempt) || call.generation !== attempt.projectGeneration) {
        return;
      }
      if (!call.response.ok) {
        if (this.taskDetailIsCurrent(attempt)) {
          this.setNotice(`${call.response.error.code}: ${call.response.error.message}`);
        }
        return;
      }
      if (!isTaskDetailResult(call.response.result)) {
        throw new CoreClientError("malformed_response", "Core bridge returned the wrong Task detail result.");
      }
      const artifactTargets = await this.buildArtifactMap(
        call.response.result.artifacts,
        attempt.canonicalRoot,
      );
      if (!this.taskDetailIsCurrent(attempt)) {
        return;
      }
      applyTaskDetail(this.state, call.response.result);
      this.artifactTargets.clear();
      for (const [artifactId, target] of artifactTargets) {
        this.artifactTargets.set(artifactId, target);
      }
    } catch (error) {
      if (this.taskDetailIsCurrent(attempt)) {
        this.setNotice(error instanceof Error ? error.message : String(error));
      }
    } finally {
      if (this.taskDetailIsCurrent(attempt)) {
        this.finishBusy();
      }
    }
  }

  public async startObserving(): Promise<void> {
    const projectKey = this.selectedFolder?.uri.toString();
    if (
      !this.requireTrusted("Monitoring") ||
      !this.requireSupported() ||
      !this.pythonPath ||
      !this.canonicalRoot ||
      !projectKey
    ) {
      if (!this.pythonPath) this.setNotice("Select a trusted installed Python interpreter first.");
      if (!this.canonicalRoot) this.setNotice("Load a managed project snapshot first.");
      return;
    }
    const attempt: BoundOperationIdentity = {
      token: ++this.observationEpoch,
      projectGeneration: this.generation,
      projectKey,
      canonicalRoot: this.canonicalRoot,
      pythonPath: this.pythonPath,
    };
    const choice = await this.dependencies.confirmObservation(
      `Selected root: ${attempt.canonicalRoot}\nTrusted interpreter: ${attempt.pythonPath}\nEvents go only to a mutually authenticated loopback listener and remain in memory. Stopping AIO does not stop Codex.`,
    );
    if (choice !== "Start observer" || !this.observationIsCurrent(attempt)) {
      return;
    }
    let partialMonitor: ControllerMonitorHandle | undefined;
    try {
      await this.stopCurrentMonitor("root-changed", attempt.token);
      if (!this.observationIsCurrent(attempt)) {
        return;
      }
      const base = path.join(this.context.globalStorageUri.fsPath, "codex-observer");
      const registryDirectory = path.join(base, "registry-v1");
      const installed = await this.dependencies.installObserver(
        vscode.Uri.joinPath(this.context.extensionUri, "observer", "codex_hook_observer.py").fsPath,
        path.join(base, "assets"),
      );
      if (!this.observationIsCurrent(attempt)) {
        return;
      }
      const publication: RootLifecycleIdentity = {
        token: attempt.token,
        projectKey: attempt.projectKey,
        canonicalRoot: attempt.canonicalRoot,
        pythonPath: attempt.pythonPath,
      };
      const monitor = this.dependencies.createMonitor({
        registryDirectory,
        canonicalRoot: attempt.canonicalRoot,
        onDidChange: (snapshot) => {
          if (
            this.monitor === monitor &&
            this.activeObservation === publication &&
            this.observationPublicationIsCurrent(publication)
          ) {
            this.state.monitoring = snapshot;
            this.broadcast();
          }
        },
      });
      partialMonitor = monitor;
      this.pendingMonitor = { epoch: attempt.token, monitor };
      const started = await monitor.start();
      if (this.pendingMonitor?.monitor === monitor) {
        this.pendingMonitor = undefined;
      }
      if (!this.observationIsCurrent(attempt)) {
        await monitor.dispose();
        return;
      }
      if (started.listener !== "listening") {
        await monitor.dispose();
        partialMonitor = undefined;
        if (!this.observationIsCurrent(attempt)) {
          return;
        }
        throw new Error(started.error ?? `Observer listener is ${started.state}.`);
      }
      const hookPlan = createCodexHookSetup({
        pythonPath: attempt.pythonPath,
        observerPath: installed.observerPath,
        observerSha256: installed.sha256,
        registryDirectory,
      });
      if (!this.observationIsCurrent(attempt)) {
        await monitor.dispose();
        return;
      }
      this.monitor = monitor;
      this.activeObservation = publication;
      partialMonitor = undefined;
      this.hookPlan = hookPlan;
      this.state.monitoring = started;
      this.setNotice("Observer listener started. Copy the exact hook setup, merge it manually, then review and trust it in Codex with /hooks.");
    } catch (error) {
      if (partialMonitor && this.pendingMonitor?.monitor === partialMonitor) {
        this.pendingMonitor = undefined;
      }
      await partialMonitor?.dispose().catch(() => undefined);
      if (!this.observationIsCurrent(attempt)) {
        return;
      }
      this.monitor = undefined;
      this.hookPlan = undefined;
      this.state.monitoring = { ...EMPTY_MONITORING, state: "error", listener: "error", error: error instanceof Error ? error.message : String(error) };
      this.setNotice(this.state.monitoring.error ?? "Unable to start observer.");
    }
  }

  public async stopObserving(reason: ObservationStopReason = "user"): Promise<void> {
    const epoch = ++this.observationEpoch;
    await this.stopCurrentMonitor(reason, epoch);
  }

  public async copyHookSetup(): Promise<void> {
    if (!this.requireTrusted("Hook setup") || !this.requireSupported()) {
      return;
    }
    if (!this.hookPlan) {
      this.setNotice("Start the observer first so the exact installed helper and registry paths can be shown.");
      return;
    }
    await vscode.env.clipboard.writeText(formatCodexHookSetup(this.hookPlan));
    this.setNotice("Copied exact setup and removal instructions. AIO did not modify Codex configuration; review the hook in Codex with /hooks.");
  }

  public onWorkspaceFoldersChanged(): void {
    const selected = this.selectedFolder;
    if (selected && !(vscode.workspace.workspaceFolders ?? []).some((folder) => folder.uri.toString() === selected.uri.toString())) {
      void this.changeProject(undefined);
    }
  }

  public onTrustGranted(): void {
    this.state.trusted = true;
    void this.refresh();
  }

  public dispose(): void {
    this.disposed = true;
    this.lastBoundCanonicalRoot = undefined;
    this.canonicalRoot = undefined;
    clearInterval(this.freshnessTimer);
    this.generation += 1;
    this.detailGeneration += 1;
    const epoch = ++this.observationEpoch;
    void this.stopCurrentMonitor("dispose", epoch);
    this.views.clear();
  }

  private async changeProject(folder: vscode.WorkspaceFolder | undefined): Promise<void> {
    const invalidation = this.invalidateObservation("root-changed");
    const selectionGeneration = this.generation;
    this.selectedFolder = folder;
    this.lastBoundCanonicalRoot = undefined;
    this.canonicalRoot = undefined;
    this.artifactTargets.clear();
    this.clearProjectData();
    this.state.project.workspaceLabel = folder?.name ?? "No project selected";
    this.state.project.state = "none";
    this.state.project.message = folder
      ? "Checking the selected workspace folder for an AIO project marker."
      : "Select one local workspace folder.";
    this.broadcast();
    await invalidation;
    if (
      this.disposed ||
      selectionGeneration !== this.generation ||
      (folder?.uri.toString() ?? "") !== (this.selectedFolder?.uri.toString() ?? "")
    ) {
      return;
    }
    await this.refresh();
  }

  private async invalidateObservation(reason: "root-changed" | "interpreter-changed" | "error"): Promise<void> {
    this.generation += 1;
    this.detailGeneration += 1;
    const epoch = ++this.observationEpoch;
    await this.stopCurrentMonitor(reason, epoch);
  }

  private async resolveRefreshRoot(
    folder: vscode.WorkspaceFolder,
    generation: number,
    projectKey: string,
  ): Promise<RefreshRootResolution> {
    try {
      const root = await canonicalDirectory(folder.uri.fsPath);
      if (!responseIsCurrent(
        generation,
        this.generation,
        projectKey,
        this.selectedFolder?.uri.toString() ?? "",
      )) {
        return { state: "stale" };
      }
      return { state: "current", root };
    } catch (error) {
      if (!responseIsCurrent(
        generation,
        this.generation,
        projectKey,
        this.selectedFolder?.uri.toString() ?? "",
      )) {
        return { state: "stale" };
      }
      return { state: "error", error };
    }
  }

  private async revalidateRefreshRoot(
    folder: vscode.WorkspaceFolder,
    candidateRoot: string,
    generation: number,
    projectKey: string,
  ): Promise<boolean> {
    const resolution = await this.resolveRefreshRoot(folder, generation, projectKey);
    if (resolution.state === "stale") {
      return false;
    }
    if (resolution.state === "error") {
      await this.failRefreshRootResolution(folder, generation, projectKey, resolution.error);
      return false;
    }
    if (!canonicalRootsMatch(candidateRoot, resolution.root)) {
      await this.changeProject(folder);
      return false;
    }
    return true;
  }

  private async failRefreshRootResolution(
    folder: vscode.WorkspaceFolder,
    generation: number,
    projectKey: string,
    error: unknown,
  ): Promise<void> {
    if (!responseIsCurrent(
      generation,
      this.generation,
      projectKey,
      this.selectedFolder?.uri.toString() ?? "",
    )) {
      return;
    }
    const invalidation = this.invalidateObservation("root-changed");
    const invalidatedGeneration = this.generation;
    this.clearProjectData();
    this.broadcast();
    await invalidation;
    if (
      !this.disposed &&
      responseIsCurrent(
        invalidatedGeneration,
        this.generation,
        folder.uri.toString(),
        this.selectedFolder?.uri.toString() ?? "",
      )
    ) {
      this.applyClientFailure(error);
      this.finishBusy();
    }
  }

  private async buildArtifactMap(
    artifacts: ArtifactDescriptor[],
    root: string,
  ): Promise<Map<string, ArtifactTarget>> {
    const targets = new Map<string, ArtifactTarget>();
    for (const artifact of artifacts) {
      if (artifact.state !== "present" || !artifact.relative_path) {
        continue;
      }
      const candidate = path.resolve(root, artifact.relative_path);
      let resolved: string;
      try {
        resolved = await realpath(candidate);
        const info = await stat(resolved);
        if (!info.isFile() || !isContained(root, resolved)) {
          continue;
        }
      } catch {
        continue;
      }
      targets.set(artifact.artifact_id, { root, absolutePath: resolved });
    }
    return targets;
  }

  private async openArtifact(artifactId: string): Promise<void> {
    if (!this.requireTrusted("Artifact navigation")) {
      return;
    }
    const target = this.artifactTargets.get(artifactId);
    if (!target) {
      this.setNotice("The artifact is missing, blocked, stale, or unknown to the extension host.");
      return;
    }
    try {
      const root = await realpath(target.root);
      const candidate = await realpath(target.absolutePath);
      const info = await stat(candidate);
      if (!info.isFile() || !isContained(root, candidate)) {
        throw new Error("Artifact containment changed; navigation was blocked.");
      }
      const document = await vscode.workspace.openTextDocument(vscode.Uri.file(candidate));
      await vscode.window.showTextDocument(document, { preview: true });
    } catch (error) {
      this.setNotice(error instanceof Error ? error.message : String(error));
    }
  }

  private async hasManifestMarker(folder: vscode.WorkspaceFolder): Promise<boolean> {
    try {
      const info = await vscode.workspace.fs.stat(vscode.Uri.joinPath(folder.uri, ".ai", "project.yaml"));
      return (info.type & vscode.FileType.File) !== 0;
    } catch {
      return false;
    }
  }

  private applyBridgeFailure(code: string, message: string): void {
    this.clearProjectData();
    if (code === "unmanaged_project") {
      this.state.project.state = "unmanaged";
    } else if (["invalid_project", "out_of_scope_resource", "invalid_catalog"].includes(code)) {
      this.state.project.state = "invalid";
    } else {
      this.state.project.state = "error";
    }
    this.state.project.message = `${code}: ${message}`;
    this.state.core = { state: "connected", version: "", message: "Core returned a structured project error." };
  }

  private applyClientFailure(error: unknown): void {
    this.clearProjectData();
    this.state.project.state = "error";
    if (error instanceof CoreClientError) {
      const incompatible = error.code === "unsafe_package_origin" || error.code === "incompatible_core";
      this.state.core = {
        state: error.code === "missing_core" ? "missing" : incompatible ? "incompatible" : "error",
        version: "",
        message: `${error.code}: ${error.message}`,
      };
      this.state.project.message = "Core connection did not produce a trusted snapshot.";
    } else {
      this.state.core = { state: "error", version: "", message: error instanceof Error ? error.message : String(error) };
      this.state.project.message = "Unexpected Core connection error.";
    }
  }

  private clearProjectData(): void {
    this.detailGeneration += 1;
    this.canonicalRoot = undefined;
    resetProjectScopeData(this.state);
    this.artifactTargets.clear();
  }

  private currentBoundIdentity(token: number): BoundOperationIdentity {
    return {
      token,
      projectGeneration: this.generation,
      projectKey: this.selectedFolder?.uri.toString() ?? "",
      canonicalRoot: this.canonicalRoot ?? "",
      pythonPath: this.pythonPath ?? "",
    };
  }

  private taskDetailIsCurrent(attempt: BoundOperationIdentity): boolean {
    return (
      !this.disposed &&
      vscode.workspace.isTrusted &&
      boundOperationIsCurrent(attempt, this.currentBoundIdentity(this.detailGeneration))
    );
  }

  private observationIsCurrent(attempt: BoundOperationIdentity): boolean {
    return (
      !this.disposed &&
      vscode.workspace.isTrusted &&
      platformIsSupported(vscode.env.remoteName, vscode.env.uiKind) &&
      boundOperationIsCurrent(attempt, this.currentBoundIdentity(this.observationEpoch))
    );
  }

  private observationPublicationIsCurrent(binding: RootLifecycleIdentity): boolean {
    return (
      !this.disposed &&
      vscode.workspace.isTrusted &&
      platformIsSupported(vscode.env.remoteName, vscode.env.uiKind) &&
      rootLifecycleIsCurrent(binding, {
        token: this.observationEpoch,
        projectKey: this.selectedFolder?.uri.toString() ?? "",
        canonicalRoot: this.canonicalRoot ?? this.lastBoundCanonicalRoot ?? "",
        pythonPath: this.pythonPath ?? "",
      })
    );
  }

  private async stopCurrentMonitor(reason: ObservationStopReason, epoch: number): Promise<void> {
    const activeMonitor = this.monitor;
    const pendingMonitor = this.pendingMonitor?.monitor;
    this.monitor = undefined;
    this.pendingMonitor = undefined;
    this.activeObservation = undefined;
    this.hookPlan = undefined;
    const monitors = [...new Set([activeMonitor, pendingMonitor].filter(
      (monitor): monitor is ControllerMonitorHandle => monitor !== undefined,
    ))];
    if (monitors.length === 0) {
      if (!this.disposed && epoch === this.observationEpoch) {
        this.state.monitoring = reason === "user"
          ? { ...EMPTY_MONITORING, state: "disconnected" }
          : EMPTY_MONITORING;
        this.broadcast();
      }
      return;
    }

    let stopped: CodexMonitorSnapshot = EMPTY_MONITORING;
    let stopError: unknown;
    for (const monitor of monitors) {
      try {
        stopped = await monitor.stop(reason);
      } catch (error) {
        stopError ??= error;
      }
      try {
        await monitor.dispose();
      } catch (error) {
        stopError ??= error;
      }
    }
    if (this.disposed || epoch !== this.observationEpoch) {
      return;
    }
    if (stopError !== undefined) {
      this.state.monitoring = {
        ...EMPTY_MONITORING,
        state: "error",
        listener: "error",
        error: "The local observation listener could not be fully stopped; its short descriptor lease remains the fallback.",
      };
      this.broadcast();
      return;
    }
    this.state.monitoring = reason === "user" ? stopped : EMPTY_MONITORING;
    this.broadcast();
  }

  private requireTrusted(label: string): boolean {
    if (!vscode.workspace.isTrusted) {
      this.setNotice(`${label} is disabled in Restricted Mode.`);
      return false;
    }
    return true;
  }

  private requireSupported(): boolean {
    if (
      !platformIsSupported(vscode.env.remoteName, vscode.env.uiKind) ||
      (this.selectedFolder !== undefined && isUncWorkspaceRoot(this.selectedFolder.uri.fsPath))
    ) {
      this.state.monitoring = { ...EMPTY_MONITORING, state: "unsupported" };
      this.setNotice("Monitoring supports Windows local desktop filesystem workspaces only.");
      return false;
    }
    return true;
  }

  private finishBusy(): void {
    this.state.busy = false;
    this.broadcast();
  }

  private setNotice(message: string): void {
    this.state.notice = message;
    this.broadcast();
  }

  private broadcast(): void {
    if (this.disposed) {
      return;
    }
    for (const view of this.views) {
      void view.postMessage({ type: "state", state: this.state });
    }
  }
}
