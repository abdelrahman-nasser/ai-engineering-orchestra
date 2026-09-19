import * as vscode from "vscode";

function attribute(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

export function controlCenterHtml(webview: vscode.Webview, extensionUri: vscode.Uri): string {
  const script = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, "webview", "main.js"));
  const style = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, "webview", "styles.css"));
  const csp = [
    "default-src 'none'",
    `style-src ${webview.cspSource}`,
    `script-src ${webview.cspSource}`,
    "img-src 'none'",
    "connect-src 'none'",
    "font-src 'none'",
  ].join("; ");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="${attribute(csp)}">
  <link rel="stylesheet" href="${attribute(style.toString())}">
  <title>AIO Control Center</title>
</head>
<body>
  <header class="hero">
    <div>
      <p class="eyebrow">Local development extension</p>
      <h1>AIO Control Center</h1>
      <p id="notice" class="notice" role="status" aria-live="polite"></p>
    </div>
    <div class="toolbar" role="group" aria-label="Control Center actions">
      <button type="button" data-action="selectProject">Select project</button>
      <button type="button" data-action="selectPython">Select Python</button>
      <button type="button" data-action="refresh">Refresh</button>
    </div>
  </header>

  <main>
    <section class="panel" aria-labelledby="project-heading">
      <h2 id="project-heading">Project</h2>
      <dl id="project-details" class="facts"></dl>
    </section>

    <section class="panel span-two" aria-labelledby="tasks-heading">
      <div class="panel-heading">
        <h2 id="tasks-heading">Tasks</h2>
        <div class="filters">
          <label>Status <select id="status-filter"></select></label>
          <label>Workflow <select id="workflow-filter"></select></label>
        </div>
      </div>
      <div id="task-anomalies" class="callout" hidden></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th scope="col">Task</th><th scope="col">Status</th><th scope="col">Workflow</th><th scope="col">Health</th></tr></thead>
          <tbody id="task-rows"></tbody>
        </table>
      </div>
      <div id="task-detail" class="detail"></div>
    </section>

    <section class="panel span-two" aria-labelledby="workflow-heading">
      <h2 id="workflow-heading">Declared Workflow</h2>
      <p id="workflow-label" class="muted">Select a Task to inspect its declared Workflow definition.</p>
      <ol id="workflow-stages" class="stages"></ol>
    </section>

    <section class="panel" aria-labelledby="codex-heading">
      <h2 id="codex-heading">Codex connection</h2>
      <dl id="codex-details" class="facts"></dl>
      <div class="toolbar vertical" role="group" aria-label="Codex observation actions">
        <button type="button" data-action="startObserving">Start observing</button>
        <button type="button" data-action="copyHookSetup">Copy hook setup</button>
        <button type="button" data-action="stopObserving">Stop observing</button>
      </div>
      <p class="muted">Installation, listener setup, and observed activity are separate facts. Silence does not prove idle or ended.</p>
    </section>

    <section class="panel" aria-labelledby="sessions-heading">
      <h2 id="sessions-heading">Observed sessions</h2>
      <ul id="session-list" class="list"></ul>
    </section>

    <section class="panel span-two" aria-labelledby="activity-heading">
      <h2 id="activity-heading">Activity</h2>
      <p class="muted">Allowlisted metadata only. No prompts, responses, tool arguments/results, source, diffs, or transcripts.</p>
      <ol id="event-list" class="timeline"></ol>
    </section>
  </main>
  <script src="${attribute(script.toString())}"></script>
</body>
</html>`;
}
