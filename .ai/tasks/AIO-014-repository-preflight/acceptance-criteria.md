# AIO-014 — Acceptance Criteria

## Mechanical Preflight Execution

- [x] `scripts/verify_repo.py` executes exactly the seven established mechanical verification checks:
  1. `Unit Tests`
  2. `Task Validation`
  3. `Workflow Validation`
  4. `Role Validation`
  5. `Project Manifest Validation`
  6. `Markdown Lint`
  7. `Git Diff Check`
- [x] Check execution order is strictly sequential and deterministic matching the defined list.
- [x] Checks run to completion: a failure or error in an earlier check does not abort remaining checks.
- [x] Subprocess execution uses argument arrays with `shell=False` and resolves executables via `shutil.which`.
- [x] Subprocesses execute with working directory set to the deterministically resolved repository root.
- [x] The utility succeeds and produces identical results regardless of the caller's working directory.

## Semantic Boundary & Governance

- [x] Preserves `Repository verification != Quality Gate satisfaction`.
- [x] Does NOT map mechanical checks to Quality Gate IDs.
- [x] Does NOT claim `documentation_consistency` or `independent_review` are satisfied.
- [x] Does NOT automate independent review or replace human reviewer evaluation.
- [x] Does NOT exhibit Task awareness: no `--task` flag, no task directory parsing, no loading of Task Quality Gates.
- [x] Does NOT implement a configurable runner framework (no YAML configuration, no plugin registry, no generic DSL).

## Exit Codes & Diagnostics

- [x] Exit code `0`: All seven checks pass cleanly.
- [x] Exit code `1`: Utility executes normally, but one or more checks return a non-zero exit code (`FAIL`).
- [x] Exit code `2`: Preflight infrastructure failure or check execution error (`ERROR`, such as missing executable or unresolved repo root).
- [x] `FAIL` is distinctly separated from `ERROR`.
- [x] Concise output for successful checks: `<Check Name>  PASS`.
- [x] Successful stdout/stderr is suppressed by default (no noisy test dumps).
- [x] Failed checks display check name, exit code, and captured stdout/stderr.
- [x] Errored checks display check name and the execution/launch error message.

## Unit Tests & Recursion Safety

- [x] Comprehensive unit test suite in `tests/test_verify_repo.py` covering all required scenarios:
  1. All seven checks pass -> exit `0`
  2. One check fails -> remaining checks execute
  3. Multiple checks fail -> complete summary produced
  4. Ordinary check failures -> overall exit `1`
  5. Executable launch failure -> status `ERROR`
  6. Infrastructure `ERROR` -> overall exit `2`
  7. Checks continue after one `ERROR` where safely possible
  8. Deterministic check order preserved
  9. Repository root used as subprocess `cwd`
  10. Stdout/stderr captured
  11. Successful subprocess output suppressed from normal summary
  12. Failed check diagnostics available
  13. `ERROR` diagnostics available
  14. Command execution uses argument lists / `shell=False`
  15. No Task loading / no `--task`
  16. No Quality Gate IDs or gate-result mapping
  17. Unit test recursion prevented (no unmocked recursive preflight execution)
  18. Caller working directory independence verified

## Repository Registration & Lifecycle

- [x] AIO-014 registered in `CANONICAL_TASKS` in `schemas/tests/validate_task.py`.
- [x] Canonical four-file structure created under `.ai/tasks/AIO-014-repository-preflight/`.
- [x] Governed under `standard-change` workflow.
- [x] Independent review executed by separate `reviewer` subagent.
- [x] Work stops at Human Control checkpoint (`status: in_progress`, no commit, no AIO-015).
- [x] Human approval explicitly obtained and recorded in `review.md`.
- [x] Task lifecycle closed as completed in `task.yaml` and `review.md`.
