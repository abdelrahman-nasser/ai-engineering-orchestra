# AIO-020 Acceptance Criteria

- [x] `aio verify` composes supported structural validation, Project
  Verification planning, and Project Verification execution without an
  Orchestra-specific fallback or inferred checks.
- [x] Planning readiness alone gates project command execution; unrelated Task
  or Workflow structural failures do not block a valid plan, while invalid
  Manifest data and planning errors execute no project commands.
- [x] Aggregate results map PASS to 0, FAIL without ERROR to 1, any ERROR to 2,
  and user interruption to 130; a child return code of 2 remains Check FAIL.
- [x] Omitted and empty verification declarations execute zero commands, report
  `0 project checks configured`, and derive the result from structure alone.
- [x] `.ai/project.yaml` declares the seven existing Orchestra checks in the
  required order using the unchanged four-field Verification Check contract.
- [x] No active `DEFAULT_CHECKS` registry or hidden fallback remains, and
  `run_preflight` is at most a thin compatibility delegate to the unified path.
- [x] Installed `aio verify`, source `python -B aio.py verify`, and
  `python -B scripts/verify_repo.py` use the same Manifest-owned semantics.
- [x] `aio verify --structure` performs supported structural validation only,
  without planning, executable resolution, runner invocation, command
  execution, or recursion-marker mutation.
- [x] CLI help and pre-execution output disclose project-controlled execution,
  caller authority, `.ai/project.yaml` as the source, and ordered Check IDs
  without implying sandboxing or echoing full command arguments by default.
- [x] PASS output is concise; FAIL and ERROR output includes bounded stdout and
  stderr excerpts, Check ID, duration, return code where applicable, and runner
  error where applicable without Quality Gate success language.
- [x] A brand-neutral inherited recursion marker rejects nested full aggregate
  verification with exit 2, is restored in `finally`, and does not restrict
  structural-only mode.
- [x] Tests cover the required composition, gating, exit, diagnostics,
  transparency, recursion, adopter, compatibility, contract, and authority
  cases, replacing obsolete no-migration assertions with migrated behavior.
- [x] Live Windows and Linux/POSIX evidence covers the required migration cases,
  with PATH-selected Python identity/version recorded and no macOS claim unless
  performed.
- [x] Legacy-to-Manifest migration evidence proves all seven protections and
  their order are retained while only one active declaration source ships.
- [x] Required repository, installed-package, documentation-consistency,
  security-review, and independent-review evidence passes or every failure,
  skip, and approval consequence is reported accurately.
- [x] Agent auto-execution remains unauthorized, explicit Human approval is
  recorded, the Task is `completed`, and closure creates no AIO-021.
