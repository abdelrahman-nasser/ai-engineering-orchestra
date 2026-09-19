import * as vscode from "vscode";
import { ControlCenterController } from "./views/controller";
import { ControlCenterSidebarProvider, openControlCenterPanel } from "./views/sidebar";

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  const controller = new ControlCenterController(context);
  context.subscriptions.push(
    controller,
    vscode.window.registerWebviewViewProvider(
      ControlCenterSidebarProvider.viewType,
      new ControlCenterSidebarProvider(context, controller),
    ),
    vscode.commands.registerCommand("aioControlCenter.open", () => openControlCenterPanel(context, controller)),
    vscode.commands.registerCommand("aioControlCenter.refresh", () => controller.handleMessage({ type: "refresh" })),
    vscode.commands.registerCommand("aioControlCenter.selectProject", () => controller.handleMessage({ type: "selectProject" })),
    vscode.commands.registerCommand("aioControlCenter.selectPython", () => controller.handleMessage({ type: "selectPython" })),
    vscode.commands.registerCommand("aioControlCenter.startObserving", () => controller.handleMessage({ type: "startObserving" })),
    vscode.commands.registerCommand("aioControlCenter.stopObserving", () => controller.handleMessage({ type: "stopObserving" })),
    vscode.commands.registerCommand("aioControlCenter.copyHookSetup", () => controller.handleMessage({ type: "copyHookSetup" })),
    vscode.workspace.onDidChangeWorkspaceFolders(() => controller.onWorkspaceFoldersChanged()),
    vscode.workspace.onDidGrantWorkspaceTrust(() => controller.onTrustGranted()),
  );
  await controller.initialize();
}

export function deactivate(): void {
  // VS Code disposes the subscriptions registered during activation.
}
