# AIO-019 Acceptance Criteria

- [x] A planning API loads and validates the active Manifest without depending on
  unrelated Task or Workflow structural findings.
- [x] Planning materializes declaration order, default cwd, and the 600-second
  default timeout in immutable plan structures before any command executes.
- [x] Every planned cwd exists, is a directory, and resolves to the project root
  or within it; traversal and resolved symlink or junction escapes are rejected.
- [x] Planning failure executes zero project commands, while executable
  availability is resolved per check only at execution time.
- [x] Bare executables follow inherited PATH and platform rules, relative
  executable paths resolve from the effective cwd, and absolute external
  executables are supported without runner-invocation-directory influence.
- [x] Windows PATHEXT lookup supports `.cmd` and `.bat` while the Python
  subprocess boundary remains `shell=False` and no command string is synthesized.
- [x] Each cwd and the project root are revalidated immediately before launch;
  check-local cwd errors can continue, while an unusable project root stops the
  remaining execution without fabricated results.
- [x] Execution is sequential, inherits the caller environment, supplies
  `subprocess.DEVNULL` as stdin, and does not add interactive or PTY behavior.
- [x] Stdout and stderr are captured separately as bytes; retained diagnostic
  excerpts are bounded, safely decoded, and explicitly marked when truncated.
- [x] PASS output is suppressed by formatting, while FAIL and ERROR diagnostics
  remain useful and bounded.
- [x] Exit zero is PASS; every completed nonzero return code is FAIL; missing
  executables, launch failures, invalid launch-time cwd, and timeouts are ERROR;
  no SKIP state exists.
- [x] Timeouts preserve partial diagnostics, record monotonic duration, return no
  child return code, and best-effort terminate and reap the direct child without
  claiming descendant termination.
- [x] KeyboardInterrupt stops immediately, best-effort terminates and reaps the
  active direct child, propagates to the caller, and does not become a check ERROR.
- [x] FAIL and safe check-local ERROR results do not suppress later independent
  checks; a valid empty plan returns successful empty mechanical execution.
- [x] Result types expose only useful ephemeral mechanical evidence and do not map
  checks to Quality Gates or mutate Task, Workflow, Stage, Agent, or Provider state.
- [x] Focused tests cover planning, containment, executable forms, literal
  arguments, status classification, continuation, IO bounds, timeout,
  interruption, and legacy-preflight compatibility.
- [x] Live Windows evidence covers the available cwd, executable, wrapper,
  argument, IO, result, continuation, and timeout cases, including a junction
  escape where the host permits it.
- [x] Live POSIX evidence is recorded when an authorized environment is available;
  otherwise the missing evidence and approval impact are reported without
  overclaiming.
- [x] The current `aio verify`, `DEFAULT_CHECKS`, `run_preflight`, and
  `scripts/verify_repo.py` behavior remain unchanged, and no permanent runner CLI
  or Orchestra verification declarations are added.
- [x] Required full repository validation and installed-package evidence pass, or
  every failure or skipped check is reported accurately.
- [x] Documentation consistency, separate security review, and independent review
  pass with all material findings resolved.
- [x] Human approval is recorded before the Task may leave `in_progress`.
