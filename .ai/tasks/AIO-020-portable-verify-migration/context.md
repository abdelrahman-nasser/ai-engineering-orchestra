# AIO-020 Context

## Migration boundary

The public `aio verify` command currently runs an Orchestra-specific hardcoded
preflight. AIO-020 replaces that active battery with a thin composition of the
supported structural validator, the AIO-019 Project Verification planner, and
the Project Verification Runner. `.ai/project.yaml` becomes the only Source of
Truth for Orchestra's seven mechanical checks. Adopting projects receive the
same behavior without inferred checks or an Orchestra fallback.

Only `planning.is_ready` controls whether declared commands may execute. An
unrelated Task or Workflow structural failure therefore remains visible in the
aggregate result but does not suppress a usable verification plan. A malformed
or schema-invalid Manifest remains a structural FAIL, prevents planning and
execution, and is not reclassified as infrastructure ERROR for CLI convenience.

## Security and authority boundary

Default verification intentionally executes repository-controlled commands with
the caller's inherited filesystem access, network access, credentials,
environment, and process authority. AIO provides no sandbox, filesystem or
network isolation, credential isolation, purity, read-only guarantee,
harmlessness, or complete descendant containment. Bounded failure diagnostics
may still expose sensitive command output.

Full aggregate verification uses the brand-neutral inherited marker
`ENGINEERING_ORCHESTRATION_VERIFY_DEPTH` to reject nested execution. The marker
is restored after the runner returns. Wrappers can deliberately remove it, and
AIO cannot prove the absence of recursion through arbitrary external scripts.
Structural-only verification ignores the marker and neither plans nor executes
project commands.

The public mechanism does not authorize an Agent to invoke it. Manifest
declarations grant no command, filesystem, network, credential, or Agent
execution authority. Verification evidence does not satisfy a Quality Gate.

## Development environment

Orchestra's Manifest deliberately declares `python`, not `sys.executable` or an
interpolation token. Verification must run from a supported/activated
development environment where PATH-selected `python` has the repository's
required dependencies. This is an intentional migration difference from the
legacy preflight.

## Human control

The governing `security-sensitive-change` Workflow requires the canonical
stage order: understand, security-analysis, implement, validate, and review.
Separate security-reviewer and reviewer executions are required. Work stops at
the review-stage Human Control checkpoint with this Task still `in_progress`;
completion and commit are not authorized.
