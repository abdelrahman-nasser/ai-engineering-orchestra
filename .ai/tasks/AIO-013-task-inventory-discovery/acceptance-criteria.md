# AIO-013 — Acceptance Criteria

## Discovery & Canonical Identity

- [x] `list_tasks.py` enumerates immediate subdirectories under `.ai/tasks/` and discovers all valid canonical tasks.
- [x] Task identity is taken exclusively from `task.yaml.id`. The directory name is never parsed, regex-matched, or assumed to be the Task ID.
- [x] If a directory is named arbitrarily (e.g. `arbitrary-dir`), the inventory correctly reports the canonical `id` declared inside `task.yaml`.
- [x] Discovered valid tasks are presented in strictly deterministic order sorted by canonical Task `id`. Diagnostic anomalies are sorted by directory name.

## Filtering & Presentation

- [x] Filtering by `--status completed` returns only tasks whose canonical `status` equals `completed`.
- [x] Filtering by `--status in_progress` returns only tasks whose canonical `status` equals `in_progress`.
- [x] Filtering by `--workflow standard-change` returns only tasks declaring `workflow: standard-change`. Historical tasks with omitted workflow bindings are excluded.
- [x] `--status` and `--workflow` filters can be combined conjunctively.
- [x] A task declaring a resolvable workflow displays the declared workflow ID and `Resolution: RESOLVED`.
- [x] A task without workflow binding displays `Workflow: -` and `Resolution: NOT DECLARED`.
- [x] A task declaring an unknown workflow ID displays the declared workflow ID, `Resolution: UNRESOLVED`, and appears in the inventory table without crashing.

## Anomaly Isolation & Robustness

- [x] An immediate child directory lacking `task.yaml` does not crash inventory; it is reported under diagnostics and omitted from the valid tasks table.
- [x] A directory with syntax-invalid `task.yaml` does not crash inventory; it is reported under diagnostics and omitted from the valid tasks table.
- [x] A directory failing `task.schema.json` validation does not crash inventory; it is reported under diagnostics and omitted from the valid tasks table.
- [x] One corrupt or invalid directory does not suppress the display of other valid tasks.
- [x] `list_tasks.py` reuses `scripts.inspect_task.inspect_task` directly in-process; it does not launch `inspect_task.py` as an external subprocess or scrape stdout.
- [x] Workflow resolution relies strictly on declared workflow ID via `scripts.workflow_catalog`, never coupling Workflow ID to filename.
- [x] Exit code semantics: returns `0` when all discovered directories are valid tasks; returns `1` when genuine repository anomalies (missing `task.yaml`, malformed YAML, or schema violations) are found.

## Governance & Integrity

- [x] Scope discipline: no CLI bloat (no `--quiet`, no JSON/CSV, no pagination, no mutation). No modifications to contracts or schemas.
- [x] Historical integrity: Tasks AIO-001 through AIO-012 remain completely unmodified.
- [x] Governed execution under `standard-change`, with Stage 4 executed by an independent `reviewer` subagent.
- [x] Quality gates `documentation_consistency` and `independent_review` satisfied with evidence.
- [x] Work stops at the Human Control checkpoint before closure; no auto-completion.
- [x] Human approval explicitly obtained, recorded in `review.md`, and closure authorized.
