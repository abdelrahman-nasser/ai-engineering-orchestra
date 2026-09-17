# AIO-014 — Context

## 1. Context Completion Rule Evidence

Per `core/context-policy.md` §22:

### 1. What am I changing?

Implementing a repository-level preflight verification utility in `scripts/verify_repo.py`,
supported by comprehensive unit tests in `tests/test_verify_repo.py`, and governed canonical
task artifacts in `.ai/tasks/AIO-014-repository-preflight/`.

### 2. Why am I changing it?

During AIO-010 through AIO-013, running the repository's mechanical verification battery required
manually executing seven separate commands:

1. `python -B -m unittest discover -s tests -p test_*.py -v`
2. `python -B schemas/tests/validate_task.py`
3. `python -B schemas/tests/validate_workflow.py`
4. `python -B schemas/tests/validate_role.py`
5. `python -B schemas/tests/validate_project_manifest.py`
6. `npx --yes markdownlint-cli2 **/*.md`
7. `git diff --check`

This manual battery causes operational friction, invites accidental skipping of checks, and clutters
developer context with enormous successful output. A single preflight command (`python -B scripts/verify_repo.py`)
executes all 7 checks, reports failures or execution errors with diagnostics, and displays a concise PASS
summary for clean checks.

### 3. What must remain unchanged?

- Fundamental semantic boundary: Repository verification != Quality Gate satisfaction.
  - Markdown Lint PASS is supporting evidence; it is NOT `documentation_consistency = PASSED`.
  - Unit Tests PASS is supporting evidence; it does NOT satisfy `independent_review`.
- No Quality Gate runner, checker registry, or gate satisfaction engine.
- No mapping of checks to Quality Gate IDs.
- No Task awareness (no `--task`, no reading `review.md` or task quality gates).
- No configurable runner framework (no YAML config, no plugins, no dynamic shell commands).
- No schema changes (`task.schema.json`, `workflow.schema.json`, `role.schema.json`, `project.schema.json`).
- Historical Tasks AIO-001 through AIO-013 remain untouched.
- Human Control contracts in `core/human-control.md`.

### 4. What Rules apply?

- `core/principles.md` (Source of Truth, Minimum Necessary Change, Explicit Context).
- `core/precedence.md` (Authoritative specifications govern).
- `core/context-policy.md` (§22 Context Completion Rule).
- `core/human-control.md` (Governed checkpoint requires explicit human approval before closure).
- `workflows/standard-change.yaml` (Stage mapping: understand -> implement -> validate -> review).
- `roles/software-engineer.md` and `roles/reviewer.md`.
- `quality-gates/documentation_consistency.md` and `quality-gates/independent_review.md`.

### 5. What proves the Task is complete?

- All required unit test scenarios in `tests/test_verify_repo.py` pass cleanly without recursion.
- All individual verification tools continue to pass independently:
  - Unit tests
  - Task validation
  - Workflow validation
  - Role validation
  - Project Manifest validation
  - Markdownlint
  - Git diff check
- Consolidated preflight runs cleanly (`python -B scripts/verify_repo.py`), reporting all 7 checks PASS and exit 0.
- Independent review subagent with role `reviewer` evaluates implementation correctness and semantic boundary preservation.
- Work stops at the Human Control checkpoint before task closure.

---

## 2. Design Decisions and Governance Boundaries

### Semantic Boundary — Verification != Quality Gate Satisfaction

Mechanical verification checks provide empirical evidence about repository health, syntax validity,
schema compliance, and code correctness. They do NOT constitute semantic Quality Gate evaluations:

- `documentation_consistency` requires evaluating conceptual alignment between specifications, context,
  and implementation, which mechanical markdown linting cannot verify alone.
- `independent_review` strictly requires an independent reviewer evaluation and explicit review outcome.

The preflight utility outputs only mechanical check names and execution outcomes, never Quality Gate IDs
or claims of gate satisfaction.

### Exact Fixed Check Set

The battery consists of exactly seven sequentially executed checks:

1. `Unit Tests`: `python -B -m unittest discover -s tests -p test_*.py -v`
2. `Task Validation`: `python -B schemas/tests/validate_task.py`
3. `Workflow Validation`: `python -B schemas/tests/validate_workflow.py`
4. `Role Validation`: `python -B schemas/tests/validate_role.py`
5. `Project Manifest Validation`: `python -B schemas/tests/validate_project_manifest.py`
6. `Markdown Lint`: `npx --yes markdownlint-cli2 **/*.md`
7. `Git Diff Check`: `git diff --check`

### Repository Root Resolution & Working Directory Independence

`verify_repo.py` deterministically locates the repository root relative to its own file location
(`Path(__file__).resolve().parent.parent`) and verifies the presence of repository markers
(`.ai/project.yaml` or `.git`).
All subprocesses are executed with `cwd = repo_root`, guaranteeing identical deterministic results
regardless of the caller's working directory.

### Subprocess Safety & Platform Resolution

Commands are specified strictly as argument lists (`list[str]`) executed with `shell=False`.
Executable names are resolved using `shutil.which`, ensuring cross-platform support (such as resolving
`npx` to `npx.cmd` on Windows) without falling back to arbitrary shell execution strings.

### Execution Behavior & Fault Tolerance

The utility executes every check sequentially even if prior checks fail. This provides a complete
health snapshot rather than halting after the first error.

### Exit Code & Classification Semantics

Three mutually exclusive states are tracked per check:

- `PASS`: Subprocess completed with exit code 0.
- `FAIL`: Subprocess completed normally but returned a non-zero exit code (verification failure).
- `ERROR`: Subprocess could not be launched (missing executable, OS permission failure, runner exception).

Overall preflight exit codes:

- `0`: All 7 checks completed with `PASS`.
- `1`: Normal execution, but one or more checks reported `FAIL` (no `ERROR`).
- `2`: One or more checks encountered an `ERROR`, or the preflight utility itself suffered an infrastructure failure (e.g., repository root unresolved).

### Concise Output & Failure Diagnostics

- Successful checks print a single aligned status line: `<Check Name>  PASS`.
- Successful stdout/stderr is suppressed to preserve developer focus.
- Failed or errored checks print diagnostics showing check name, exit code, and captured stdout/stderr.
- No CLI flags like `--verbose` or `--quiet` are added.

### Unit Test Recursion Prevention

Because `python -B -m unittest discover` will discover `tests/test_verify_repo.py`, tests in
`test_verify_repo.py` must never invoke `verify_repo.py` in an unmocked subprocess running unittest discovery.
A narrow execution seam (`default_runner` parameter/mocking) is used to verify orchestration, exit codes,
and formatting without spawning recursive preflights. Live unmocked verification occurs during Stage 3.
