import * as vscode from "vscode";
import { ControlCenterController } from "./controller";
import { controlCenterHtml } from "./html";

export class ControlCenterSidebarProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "aioControlCenter.sidebar";

  public constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly controller: ControlCenterController,
  ) {}

  public resolveWebviewView(view: vscode.WebviewView): void {
    view.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.context.extensionUri, "webview")],
    };
    view.webview.html = controlCenterHtml(view.webview, this.context.extensionUri);
    const attached = this.controller.attach(view.webview);
    view.onDidDispose(() => attached.dispose());
  }
}

export function openControlCenterPanel(
  context: vscode.ExtensionContext,
  controller: ControlCenterController,
): vscode.WebviewPanel {
  const panel = vscode.window.createWebviewPanel(
    "aioControlCenter.panel",
    "AIO Control Center",
    vscode.ViewColumn.One,
    {
      enableScripts: true,
      retainContextWhenHidden: false,
      localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, "webview")],
    },
  );
  panel.webview.html = controlCenterHtml(panel.webview, context.extensionUri);
  const attached = controller.attach(panel.webview);
  panel.onDidDispose(() => attached.dispose());
  return panel;
}
