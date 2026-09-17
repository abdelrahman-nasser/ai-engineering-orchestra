# AIO-013 — Context

## 1. Context Completion Rule Evidence

Per `core/context-policy.md` §22:

### 1. What am I changing?

Implementing a repository-local Task discovery and inventory utility in `scripts/list_tasks.py`,
supported by comprehensive unit tests in `tests/test_list_tasks.py`, and governed canonical
task artifacts in `.ai/tasks/AIO-013-task-inventory-discovery/`.

### 2. Why am I changing it?

Developers and orchestrators need a fast, deterministic, repository-level inventory command to answer:

- What Tasks exist?
- What is each Task's canonical ID?
- What is its status?
- What type is it?
- Which Workflow is declared?
- Does that Workflow resolve?

This feature provides repository visibility into existing Tasks and governance status (including
unresolved workflows or corrupted directories) by consuming existing contracts rather than inventing new ones.

### 3. What must remain unchanged?

- `schemas/task.schema.json`, `schemas/workflow.schema.json`, Role schema, Project Manifest schema.
- Human Control contracts in `core/human-control.md`.
- Historical Tasks AIO-001 through AIO-012.
- Workflow definitions in `workflows/`.
- No runtime execution engine, actor assignment, stage state tracking, or scheduler.
- No auto-selection of Workflows.

### 4. What Rules apply?

- `core/principles.md` (Source of Truth, Minimum Necessary Change, Explicit Context).
- `core/precedence.md` (Authoritative specifications govern).
- `core/context-policy.md` (§22 Context Completion Rule).
- `core/human-control.md` (Governed checkpoint requires explicit human approval before closure).
- `workflows/standard-change.yaml` (Stage mapping: understand -> implement -> validate -> review).
- `roles/software-engineer.md` and `roles/reviewer.md`.
- `quality-gates/documentation_consistency.md` and `quality-gates/independent_review.md`.

### 5. What proves the Task is complete?

- All 16 minimum test scenarios in `tests/test_list_tasks.py` pass cleanly.
- `scripts/list_tasks.py` runs on the live repository, deterministically displaying all valid tasks,
  showing historical tasks without bindings as `NOT DECLARED`, and resolving `standard-change` for AIO-011, AIO-012, and AIO-013.
- All schema validators (`validate_task.py`, `validate_workflow.py`, `validate_role.py`, `validate_project_manifest.py`) pass.
- Markdownlint and `git diff --check` pass with zero violations.
- An independent review subagent with role `reviewer` evaluates the changes and approves.
- Work stops at the Human Control checkpoint before task closure.

---

## 2. Design Decisions and Governance Boundaries

### Boundary 1 — Canonical Identity Source

Task identity is strictly derived from the `id` property inside `task.yaml`. A directory name under
`.ai/tasks/` conventionally resembles the ID, but directory name is NOT an identity contract.
Under no circumstances will `list_tasks.py` infer, parse, or regex-match a Task ID from a directory name.

### Boundary 2 — Discovery Semantics

`list_tasks.py` discovers immediate child directories under `.ai/tasks/` (or a configured tasks directory).
It does NOT recursively traverse subdirectories.
For each immediate child directory:

- If `task.yaml` exists: attempt to load and inspect it using existing inspection logic.
- If `task.yaml` is missing: handle it gracefully as a repository discovery anomaly/warning in diagnostics.
  Do NOT fabricate a Task ID or treat the directory as a valid Task.

### Boundary 3 — Reuse of Existing Inspection Logic

`list_tasks.py` directly imports and calls `inspect_task()` from `scripts.inspect_task`.
It SHALL NOT:

- Launch `inspect_task.py` as an external subprocess.
- Parse or scrape human-readable stdout.
- Duplicate YAML loading, schema validation, or Task metadata extraction.
- Create a second interpretation of Workflow resolution or Effective Quality Gates.

### Output Shape and Semantics

The primary output is a deterministic human-readable table:

```text
ID       Title   Type   Status   Workflow   Resolution
```

Workflow display semantics:

- Bound and resolved Workflow: `Workflow: <id>`, `Resolution: RESOLVED`
- No Workflow binding: `Workflow: -`, `Resolution: NOT DECLARED`
- Declared but unresolved Workflow: `Workflow: <declared_id>`, `Resolution: UNRESOLVED`

Unresolved Tasks are displayed in the table for visibility into governance issues.

### Structurally Invalid / Unreadable Tasks

If a directory lacks `task.yaml`, has malformed YAML, or fails schema validation, it cannot safely
provide trusted metadata. It is omitted from the valid Task table (no values are guessed) and
reported in a dedicated diagnostics section.

### Exit Code Semantics

- `0`: All discovered directories are valid readable Tasks, and the inventory table rendered successfully.
- `1`: One or more genuine repository anomalies or invalid/unreadable Task entries were found.

### Sorting

Tasks in the inventory table are deterministically sorted by their declared canonical Task `id`.
Anomalous directories in the diagnostics section are deterministically sorted by directory name.

### Filtering Semantics

- `--status <status>`: Filters by canonical `status` field in `task.yaml`.
- `--workflow <workflow_id>`: Filters strictly by declared `workflow` ID in `task.yaml`. Historical
  tasks without a declared workflow are excluded when filtering by `--workflow`.
- Filters can be combined conjunctively.
