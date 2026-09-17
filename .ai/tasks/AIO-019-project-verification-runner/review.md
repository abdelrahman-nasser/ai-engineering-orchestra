# AIO-019 Review

Status: Completed; explicitly Human-approved on 2026-09-17

## Implementation evidence

The programmatic planner and runner are implemented in
`engineering_orchestration/project_verification.py`. Frozen plans materialize all
cwd and timeout values before execution. Execution remains sequential, resolves
each executable at launch, revalidates project-root and cwd identity, uses
`shell=False`, inherited environment, and noninteractive stdin, and returns
bounded ephemeral PASS, FAIL, or ERROR evidence.

The current seven-check preflight, `aio verify`, and Orchestra Manifest remain
unchanged. No permanent CLI, Task or Workflow runtime, Agent or Provider behavior,
Quality Gate mapping, permission engine, sandbox, persistence, or AIO-020 exists.

## Validation evidence

- Python 3.12.10 on Windows: 57 focused planner/runner tests ran; 53 passed and 4
  were skipped for unavailable POSIX execution or Windows symlink privilege.
- Full unit discovery: 206 tests ran; 202 passed and the same 4 were skipped.
- Live Windows evidence passed for cwd defaults/containment/traversal/spaces,
  junction escape and launch-time retarget, filesystem-resolution loops, native,
  relative, absolute, external, `.cmd`, `.bat`, npm/npx PATHEXT, explicit
  PowerShell, literal arguments, inherited environment, stdin EOF, bounded and
  invalid output, PASS/FAIL/ERROR, continuation, timeout, and interruption.
- Windows directory symlink creation was denied by the host account, so contained,
  escape, and retarget symlink cases were skipped; live junction equivalents and
  shared resolved-path logic passed.
- Live Linux/POSIX evidence passed in a disposable Linux/amd64 Python 3.12.14
  container on Docker Desktop's WSL2 Linux kernel. The 57 focused tests ran with
  49 passing and 8 Windows-only skips, and a separate live probe passed 32
  assertions covering cwd containment, real inside and escaping symlinks, bare
  PATH, relative, and absolute executables, permission failure, literal native
  argv, explicit `bash -c`, PASS/FAIL/ERROR classification, continuation,
  inherited environment, stdin EOF, separate and bounded output, invalid bytes,
  timeout diagnostics, direct-child reaping, the surviving-descendant
  limitation, and SIGINT/KeyboardInterrupt propagation. This is Linux evidence,
  not validation of macOS or every POSIX platform.
- POSIX validation found no defect, so no source changes or follow-up security or
  independent review were required.
- Task validation: 36/36; declared Workflow references: 9/9; Workflow validation:
  42/42; Role validation: 34/34; Project Manifest validation: 66/66; structural
  integration tests: 23/23.
- Editable and normal-wheel installation smoke passed after final remediation.
  The installed runner and packaged schemas loaded from the intended locations;
  dependency checks, unchanged CLI/preflight behavior, external-project probes,
  uninstall, source-digest checks, and temporary cleanup passed.
- Live repository preflight: 7/7; Markdown lint: 0 issues; `git diff --check`:
  passed. No required validation failed or was waived.

## Security review

Outcome: PASS.

The separate `security-reviewer` initially required deterministic rejection of
Windows drive-relative and rooted-without-drive executable forms. The implementer
rejected those ambiguous forms as check-local ERRORs and added no-launch and
continuation tests. Final security outcome: PASS with no remaining findings.

Review scope included cwd traversal, symlink/junction containment, TOCTOU claims,
filesystem-resolution loops, PATH/PATHEXT and batch wrappers, argument and shell
semantics, inherited credentials/environment, stdin, sensitive diagnostics,
timeouts, surviving descendants, external executables, sandbox limitations,
invocation authority, Agent auto-execution exclusion, recursion, and Quality Gate
separation.

## Independent review

Outcome: APPROVE.

The separate `reviewer` initially required local handling of Python 3.12
filesystem-resolution loops and correction of stale packaged schema wording.
Those findings were remediated with continuation/fatal-boundary tests and updated
documentation. The reviewer then inspected the Windows executable-path remediation
and issued final outcome: APPROVE with no remaining findings.

The reviewer found the separate result model justified by the legacy preflight's
incompatible fixed-check fields, confirmed contract/planner/executor separation,
scope discipline, compatibility, test proportionality, package behavior, and
documentation truthfulness.

## Quality Gates

- `documentation_consistency`: pass
- `independent_review`: pass

Security review is recorded review scope under the governing Workflow and high
Task risk; it is not a new Quality Gate. Mechanical Check PASS is not Quality Gate
PASS. No required Gate failed, was skipped, or was waived.

## Observations

- Execution safety: containment constrains the initial cwd and detects obvious
  replacement; it is not sandboxing or proof against all path races.
- Platform coverage: Windows wrapper and junction behavior is proven live; Linux
  runtime, real symlink, signal, and direct-child behavior is also proven live.
- Planning sufficiency: the current four-field declaration supports complete
  sequential plans without speculative execution fields.
- Preflight reuse: shared validation findings and continuation concepts were
  reused; the fixed legacy result model remained unchanged where its semantics did
  not fit project checks.
- Dogfooding pressure: evidence supports a separately approved migration, but the
  current Orchestra Manifest and CLI were deliberately not migrated.
- Runtime pressure: no retries, DAG, scheduler, persistent logs, filtering, or
  process-tree supervisor was needed.
- Authority pressure: the callable API supplies mechanism only; caller or Agent
  authority must be established outside the runner.

The most concrete next product limitation is: The Project Verification Runner
exists programmatically, but `aio verify` still uses the legacy fixed Orchestra
preflight.

## Human approval and closure

Explicit Human approval was granted on 2026-09-17 for AIO-019 — Implement
Project Verification Runner. Closure was authorized after the implementation,
Windows live evidence, Linux/POSIX live evidence, security review outcome PASS,
independent review outcome APPROVE, and regression evidence were accepted.

No source changes were required after POSIX validation. The existing `aio verify`
command remains the legacy seven-check Orchestra preflight and was not migrated.
The runner's existence does not authorize Agent auto-execution. Project commands
continue to execute with caller privileges; no sandbox, filesystem or network
isolation, credential isolation, race freedom, descendant termination, or
process-tree guarantee is claimed. Mechanical Project Verification Check results
remain evidence only and do not establish Quality Gate PASS.

The Task is completed. No AIO-020 was created.
