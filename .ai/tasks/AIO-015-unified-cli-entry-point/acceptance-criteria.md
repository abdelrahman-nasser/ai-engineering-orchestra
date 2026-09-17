# AIO-015 — Acceptance Criteria

## AC-01: Brand-neutral CLI router

Status: complete

`scripts/cli.py` exists and provides argparse-based subcommand routing
for `tasks`, `inspect`, and `verify` without embedding permanent product branding
in domain logic.

## AC-02: Temporary branded entry point

Status: complete

`aio.py` exists at repository root as a thin wrapper that imports and calls
`scripts.cli.main()`. Contains no argument routing or business logic.

## AC-03: tasks subcommand

Status: complete

`python -B aio.py tasks` delegates to existing Task inventory functions,
producing identical output to `python -B scripts/list_tasks.py`.
Supports `--status` and `--workflow` filters.

## AC-04: inspect subcommand with Task ID lookup

Status: complete

`python -B aio.py inspect AIO-014` resolves the declared Task ID through
Task inventory discovery (not directory name construction) and delegates
to the existing inspection capability.

## AC-05: verify subcommand

Status: complete

`python -B aio.py verify` delegates to the existing repository preflight
capability, preserving PASS/FAIL/ERROR classification and exit semantics.

## AC-06: Project root from caller CWD

Status: complete

Project root is discovered by walking up from the caller's current working
directory to find `.ai/project.yaml`. The physical location of CLI source
files does not determine project identity. Manifest and Workflow data belong to
the discovered project, including when its Workflow directory is absent.

## AC-07: CWD-independent operation

Status: complete

All commands work correctly when invoked from a repository subdirectory
(e.g., `cd scripts && python -B ..\aio.py tasks`).

## AC-08: Unknown command handling

Status: complete

`python -B aio.py banana` produces an argparse usage error with no stack
trace and exits with code 2.

## AC-09: Unknown Task ID handling

Status: complete

`python -B aio.py inspect DOES-NOT-EXIST` prints a concise error to stderr
with no stack trace and exits with code 1.

## AC-10: No project marker handling

Status: complete

Running from a directory with no `.ai/project.yaml` in its ancestry prints
a concise diagnostic and exits with code 2.

## AC-11: Exit code preservation

Status: complete

Exit codes from underlying commands are propagated faithfully through
the CLI router.

## AC-12: No duplicated business logic

Status: complete

The CLI router does not reimplement Task parsing, Workflow resolution,
inventory filtering, or preflight checks.

## AC-13: No new third-party dependencies

Status: complete

Only Python standard library (`argparse`) is used for CLI routing.

## AC-14: Existing scripts retained

Status: complete

`scripts/list_tasks.py`, `scripts/inspect_task.py`, and `scripts/verify_repo.py`
remain available and functional as direct entry points.

## AC-15: CLI tests

Status: complete

`tests/test_cli.py` covers at minimum 20 specified test scenarios including
help output, delegation, Task ID resolution, error handling, CWD independence,
and rename safety.

## AC-16: Task registration

Status: complete

AIO-015 is registered in `schemas/tests/validate_task.py` canonical task list
and passes schema validation.

## AC-17: Rename safety

Status: complete

Product brand (`aio`) appears only in the entry script filename and help text.
Renaming the CLI command requires zero changes to domain logic or tests of
underlying capabilities.

## AC-18: Help UX

Status: complete

`--help` is supported at root level and for each subcommand, showing concise
command descriptions without internal architecture details.

## AC-19: Roadmap boundary

Status: complete

AIO-015 does not claim to complete the broader CLI lifecycle milestone.
The distinction is documented in context.md.

## AC-20: Independent review

Status: complete

An independent reviewer verifies all acceptance criteria before human checkpoint.
