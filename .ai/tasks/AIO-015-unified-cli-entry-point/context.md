# AIO-015 — Context

## 1. Context Completion Rule Evidence

Per `core/context-policy.md` §22:

### 1. What am I changing?

Creating a thin unified CLI entry point over the three proven Foundation utilities:

- `scripts/list_tasks.py` (AIO-013) — Task inventory and discovery
- `scripts/inspect_task.py` (AIO-010/011/012) — Task governance inspection
- `scripts/verify_repo.py` (AIO-014) — Repository mechanical verification

New files:

- `scripts/cli.py` — brand-neutral CLI router using argparse subcommands
- `aio.py` — temporary branded entry point (thin wrapper)
- `tests/test_cli.py` — comprehensive CLI tests

### 2. Why am I changing it?

The current developer experience requires fragmented commands exposing Python implementation details:

```powershell
python -B scripts/list_tasks.py
python -B scripts/inspect_task.py .ai/tasks/AIO-014-repository-preflight
python -B scripts/verify_repo.py
```

Problems:

- Long commands with boilerplate prefixes
- Requires knowledge of repository internals and file names
- Requires remembering separate Python script paths
- Requires physical directory paths instead of canonical Task IDs
- No unified help or command discovery
- Barrier to future IDE and automation integration

The unified CLI provides:

```powershell
python -B aio.py tasks
python -B aio.py inspect AIO-014
python -B aio.py verify
```

### 3. What must remain unchanged?

- Existing scripts (`list_tasks.py`, `inspect_task.py`, `verify_repo.py`) remain available and functional
- Task identity comes exclusively from `task.yaml.id`, never directory names
- Deterministic Task ordering and anomaly diagnostics
- Workflow resolution semantics
- Repository verification PASS/FAIL/ERROR classification
- Fundamental boundary: repository verification != Quality Gate satisfaction
- Exit code semantics of underlying commands
- No new third-party dependencies
- Historical Tasks AIO-001 through AIO-014 remain untouched
- Schemas remain unmodified

### 4. What Rules apply?

- `core/principles.md` (Minimum Necessary Change, Source of Truth)
- `core/precedence.md` (Authoritative specifications govern)
- `core/context-policy.md` (§22 Context Completion Rule)
- `core/human-control.md` (Governed checkpoint requires human approval)
- `workflows/standard-change.yaml` (understand → implement → validate → review)
- `roles/software-engineer.md` and `roles/reviewer.md`
- `quality-gates/documentation-consistency.md` and `quality-gates/independent-review.md`

### 5. What proves the Task is complete?

- All CLI tests pass in `tests/test_cli.py` covering 20 scenarios
- All existing tests continue to pass
- Schema validation, workflow validation, role validation, and project manifest validation pass
- Consolidated preflight runs cleanly
- Markdownlint passes
- Git diff check passes
- CLI exercises from repository root and subdirectory both succeed
- Independent review verifies no brand leakage, no duplicated logic, correct root discovery
- Work stops at Human Control checkpoint

---

## 2. Design Decisions

### Rename Safety

The architecture separates product branding from domain capabilities:

- `aio.py` is the sole location of product brand (temporary CLI name)
- `scripts/cli.py` is brand-neutral — it uses argparse and delegates to existing functions
- No domain behavior depends on the temporary command name; existing framework labels and historical Task IDs remain unchanged
- Help derives its command name from the invoked wrapper; a future rename requires updating the wrapper filename, invocation documentation, and wrapper integration tests

### Project Root Discovery

The unified CLI discovers the active project from the caller's current working directory:

```text
Path.cwd() → walk upward → find .ai/project.yaml → project root
```

This is intentionally different from the existing scripts which use `Path(__file__).parent.parent`.
The CWD-based approach is correct for a CLI that may eventually be globally installed.

The CLI explicitly passes the discovered project's `.ai/project.yaml` and `workflows/`
to inventory and inspection. An explicit missing Workflow directory remains missing;
it must not fall back to the tool checkout's catalog. The narrow reuse correction in
`inspect_task.py` preserves default behavior when no explicit directory is supplied.
Schemas remain tool-owned contract resources; active-project data does not become
an import search path. No project discovery scans beyond the CWD ancestor chain.

### Task ID Lookup

The `inspect` command resolves declared Task IDs through the existing inventory:

```text
declared Task ID → discover_tasks() → match TaskSummary.task_id → task_dir → inspect_task()
```

This reuses proven Task discovery without duplicating directory scanning or YAML parsing.
An unknown declared ID returns exit 1. Multiple matches also return exit 1 with an
ambiguity diagnostic; the router never chooses the first duplicate silently.

### Roadmap Distinction

AIO-015 implements a thin unified command router over already-proven Foundation utilities.
It does NOT claim to complete the broader CLI milestone reserved for a later lifecycle stage.
The distinction:

- AIO-015 = thin entry point wrapping 3 existing capabilities
- Future CLI milestone = broader product CLI capabilities that do not yet exist

No workflow execution, task mutation, planning, or agent commands are added.

`AGENTS.md` reserves "CLI — v0.6" and prohibits future-version features unless
the current Task explicitly changes the roadmap. The current Human instruction
expressly authorizes this limited utility-composition surface while retaining the
full CLI milestone for later. This Task records that narrow scope clarification;
it does not declare the milestone delivered or authorize broader CLI capabilities.

### Exit Semantics

- Help: exit 0, available without an active project.
- Invalid command/arguments, absent project marker, or execution error: exit 2.
- `tasks`: existing inventory output and filters; exit 1 on inventory anomalies,
  including anomalies outside filtered rows; otherwise exit 0.
- `inspect`: exact declared-ID lookup; exit 1 for missing or ambiguous identity,
  or an invalid inspection; exit 0 for a valid inspection.
- `verify`: underlying preflight exit 0 for all PASS, 1 for verification failures
  without errors, 2 for infrastructure/execution errors. Mechanical PASS does not
  satisfy Quality Gates or grant Human approval.

### Dependencies and Distribution

AIO-015 adds zero third-party dependencies and uses standard-library `argparse`.
Existing YAML/schema libraries and their pre-existing dependency-policy tension
are outside this Task. No packaging, installer, PATH setup, binary, completion,
or distribution metadata is added. The supported development invocation remains
`python -B aio.py ...`; from another project the caller must provide the wrapper's
path. `verify` still requires the active repository to provide the seven existing
check targets and prerequisites; this is not a general installed-project verifier.
