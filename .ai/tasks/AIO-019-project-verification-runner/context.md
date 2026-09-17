# AIO-019 Context

## Security boundary

AIO-018 defined the Project Verification Check declaration contract. AIO-019
implements its first programmatic execution path, so repository-controlled
commands can run with the invoking caller's effective authority. The governing
`security-sensitive-change` Workflow requires separate `software-engineer`,
`security-reviewer`, and independent `reviewer` executions before the Human
Control checkpoint.

The runner owns mechanical evidence only. It is not Task or Workflow execution,
does not invoke Agents or Providers, and does not evaluate or update Quality
Gates. Availability of the API does not grant future Agents authority to call it.
The existing seven-check `aio verify` preflight remains the active CLI behavior.

## Runtime truth

Planning validates the Manifest narrowly and resolves every effective working
directory before any project command runs. Resolved cwd containment limits only
the initial working directory; it is not filesystem confinement and cannot
eliminate path races. Commands inherit the caller environment and may use its
credentials, access the network, write accessible files, modify caches, or spawn
descendants. Verification Checks must not deliberately invoke the aggregate AIO
verifier recursively.

Execution uses literal argument arrays with the outer Python subprocess call set
to `shell=False`. A project may explicitly select a shell executable. On Windows,
resolved `.cmd` and `.bat` wrappers may still be processed by the command
interpreter, so native-executable argument guarantees do not extend unchanged to
batch wrappers. A timeout terminates and reaps the directly launched child on a
best-effort basis; descendants may survive.

The current fixed preflight uses `sys.executable`. A future declaration containing
`python` instead uses inherited PATH and is not guaranteed to select the same
interpreter. AIO-019 deliberately adds no substitution token for that migration
limitation.

## Closure boundary

Implementation, validation, security review, and independent review reached the
Workflow's Human Control checkpoint. Explicit Human approval was granted on
2026-09-17 and the Task is completed. No AIO-020 was created or authorized by
this closure.
