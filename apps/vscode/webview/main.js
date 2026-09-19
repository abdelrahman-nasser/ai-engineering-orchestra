(() => {
  "use strict";

  const vscode = acquireVsCodeApi();
  let state;

  const byId = (id) => document.getElementById(id);
  const text = (value) => value === null || value === undefined || value === "" ? "—" : String(value);

  function clear(node) {
    node.replaceChildren();
  }

  function element(tag, value, className) {
    const node = document.createElement(tag);
    if (value !== undefined) {
      node.textContent = text(value);
    }
    if (className) {
      node.className = className;
    }
    return node;
  }

  function factList(target, facts) {
    clear(target);
    for (const [label, value] of facts) {
      target.append(element("dt", label));
      target.append(element("dd", value));
    }
  }

  function populateSelect(select, values, selected, allLabel) {
    clear(select);
    const all = document.createElement("option");
    all.value = "";
    all.textContent = allLabel;
    select.append(all);
    for (const value of values) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      option.selected = value === selected;
      select.append(option);
    }
    select.value = selected ?? "";
  }

  function renderProject(current) {
    factList(byId("project-details"), [
      ["Workspace", current.project.workspaceLabel],
      ["State", current.project.state],
      ["Project", current.project.name || current.project.id || "not reported"],
      ["Core", `${current.core.state}${current.core.version ? ` · ${current.core.version}` : ""}`],
      ["Snapshot", current.snapshotAt || "not available"],
      ["Workspace Trust", current.trusted ? "Trusted" : "Restricted Mode"],
      ["Detail", current.project.message || current.core.message],
    ]);
  }

  function renderTasks(current) {
    populateSelect(byId("status-filter"), current.filters.statuses, current.filters.status, "All statuses");
    populateSelect(byId("workflow-filter"), current.filters.workflows, current.filters.workflow, "All workflows");
    const rows = byId("task-rows");
    clear(rows);
    if (current.tasks.length === 0) {
      const row = document.createElement("tr");
      const cell = element("td", current.busy ? "Loading Tasks…" : "No Tasks match this view.", "empty");
      cell.colSpan = 4;
      row.append(cell);
      rows.append(row);
    }
    for (const task of current.tasks) {
      const row = document.createElement("tr");
      const taskCell = document.createElement("td");
      const button = element("button", `${task.id} · ${task.title}`, "link-button");
      button.type = "button";
      button.addEventListener("click", () => vscode.postMessage({ type: "selectTask", taskId: task.id }));
      taskCell.append(button, element("span", task.type, "subtle"));
      row.append(
        taskCell,
        element("td", task.status),
        element("td", `${task.workflow} · ${task.workflowResolution}`),
        element("td", `YAML ${task.schemaStatus}; artifacts ${task.artifactHealth}`),
      );
      rows.append(row);
    }
    const anomaly = byId("task-anomalies");
    anomaly.hidden = current.anomalies.length === 0;
    anomaly.textContent = current.anomalies.join(" · ");

    const detail = byId("task-detail");
    clear(detail);
    if (!current.selectedTask) {
      detail.append(element("p", "Select a Task for effective metadata and artifacts.", "muted"));
      return;
    }
    detail.append(element("h3", `${current.selectedTask.id} — ${current.selectedTask.title}`));
    const facts = document.createElement("dl");
    facts.className = "facts compact";
    factList(facts, [
      ["Declared status", current.selectedTask.status],
      ["Risk", current.selectedTask.risk],
      ["Complexity", current.selectedTask.complexity],
      ["Execution Mode", current.selectedTask.executionMode],
      ["Effective gates", current.selectedTask.qualityGates.join(", ") || "none"],
    ]);
    detail.append(facts);
    const artifactList = element("ul", undefined, "artifacts");
    for (const artifact of current.selectedTask.artifacts) {
      const item = document.createElement("li");
      const open = element("button", `${artifact.label} · ${artifact.state}`, "link-button");
      open.type = "button";
      open.disabled = artifact.state !== "present";
      open.addEventListener("click", () => vscode.postMessage({ type: "openArtifact", artifactId: artifact.id }));
      item.append(open);
      artifactList.append(item);
    }
    detail.append(artifactList);
  }

  function renderWorkflow(current) {
    const label = byId("workflow-label");
    const stages = byId("workflow-stages");
    clear(stages);
    if (!current.workflow) {
      label.textContent = current.selectedTask
        ? "This Task has no resolved declared Workflow."
        : "Select a Task to inspect its declared Workflow definition.";
      return;
    }
    label.textContent = `${current.workflow.name} (${current.workflow.id}) · ${current.workflow.label}`;
    current.workflow.stages.forEach((stage, index) => {
      const item = document.createElement("li");
      item.append(element("h3", `${index + 1}. ${stage.id}`), element("p", stage.purpose));
      const meta = [];
      if (stage.checkpoint) meta.push("Human Control checkpoint");
      if (stage.gates.length) meta.push(`Gates: ${stage.gates.join(", ")}`);
      item.append(element("p", meta.join(" · ") || "No Stage-level gate or checkpoint", "subtle"));
      if (stage.roles.length) {
        const roleList = document.createElement("ul");
        for (const role of stage.roles) {
          roleList.append(element("li", `${role.name} (${role.id}) — ${role.purpose}`));
        }
        item.append(roleList);
      }
      stages.append(item);
    });
  }

  function renderMonitoring(current) {
    const monitor = current.monitoring;
    factList(byId("codex-details"), [
      ["Source", "Local Codex lifecycle hooks"],
      ["Observation", monitor.state],
      ["Listener", monitor.listener],
      ["Setup", monitor.setup === "unverified" ? "User-enabled listener; hook setup/trust unverified" : monitor.setup],
      ["Last observation", monitor.lastReceivedAt || "No observations"],
      ["Model", monitor.events[0]?.model || "not reported"],
      ["Reasoning", "not reported"],
      ["Error", monitor.error || "none"],
    ]);

    const sessions = byId("session-list");
    clear(sessions);
    if (monitor.sessions.length === 0) {
      sessions.append(element("li", "No observed sessions. No event means unknown, not idle."));
    }
    for (const session of monitor.sessions) {
      const scope = session.identity.scope.kind === "subagent"
        ? `subagent ${session.identity.scope.subagentId}`
        : "root session";
      sessions.append(element(
        "li",
        `${session.identity.sessionId || "unreported session"} · ${scope} · ${session.lastEventType || "event not reported"} · ${session.lastReceivedAt || "time not reported"}`,
      ));
    }

    const events = byId("event-list");
    clear(events);
    if (monitor.events.length === 0) {
      events.append(element("li", "No allowlisted activity received."));
    }
    for (const event of [...monitor.events].reverse()) {
      const labels = [
        event.eventType,
        event.toolLabel,
        event.agentType,
        event.model ? `model ${event.model}` : "model not reported",
        event.receivedAt,
      ].filter(Boolean);
      events.append(element("li", labels.join(" · ")));
    }
  }

  function render(current) {
    state = current;
    byId("notice").textContent = current.notice || (current.busy ? "Loading current project data…" : "");
    document.body.dataset.trusted = String(current.trusted);
    renderProject(current);
    renderTasks(current);
    renderWorkflow(current);
    renderMonitoring(current);
    const trustRequired = new Set(["selectProject", "selectPython", "startObserving", "copyHookSetup"]);
    const platformRequired = new Set(["startObserving", "copyHookSetup"]);
    document.querySelectorAll("button[data-action]").forEach((button) => {
      const action = button.dataset.action;
      button.disabled = (trustRequired.has(action) && !current.trusted)
        || (platformRequired.has(action) && !current.platformSupported);
    });
  }

  document.querySelectorAll("button[data-action]").forEach((button) => {
    button.addEventListener("click", () => vscode.postMessage({ type: button.dataset.action }));
  });
  byId("status-filter").addEventListener("change", () => vscode.postMessage({
    type: "setFilters",
    status: byId("status-filter").value || null,
    workflow: byId("workflow-filter").value || null,
  }));
  byId("workflow-filter").addEventListener("change", () => vscode.postMessage({
    type: "setFilters",
    status: byId("status-filter").value || null,
    workflow: byId("workflow-filter").value || null,
  }));
  window.addEventListener("message", (event) => {
    if (event.data && event.data.type === "state") {
      render(event.data.state);
    }
  });
  vscode.postMessage({ type: "ready" });
})();
