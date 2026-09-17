# AIO-018 Context

## Stage 1 — understand

The Human approved the Project Verification Contract investigation after AIO-017
at `8e61feacd55d6fab852a6c8f5fe262630b835792`. This Task defines what a declaration
means, without implementing its execution. The governing Workflow is
`standard-change`; implementation uses `software-engineer`, followed by validation,
independent `reviewer`, and separate `security-reviewer` executions.

The Project Manifest specification owns optional `verification.checks` in
`.ai/project.yaml`; the existing Manifest schema owns structural conformance.
Verification Checks produce future mechanical evidence, not Quality Gate results.
They do not represent Tasks, Stages, Agents, Assignments, or Execution Contracts.

The four-field contract uses unique canonical `id`, literal argument-array
`command`, optional project-relative `cwd`, and optional positive integer
`timeout_seconds`. Cwd defaults to the active project root; timeout defaults to
600 seconds. Boolean timeout is invalid. Unknown fields are rejected. Missing
verification and empty checks are valid; no discovery is inferred.

Future execution specifies shell=False, no AIO expansion or interpolation, caller
environment inheritance, and no sandbox claim. Repository commands do not grant
authority. Bare executables use PATH, relative executables use effective cwd,
absolute executables are allowed, and no interpreter is inferred. Availability,
cwd existence, symlink/junction resolution, containment, and timeouts belong to a
future runner, never structural validation.

Future results distinguish completed zero/nonzero exit codes (PASS/FAIL) from
unevaluable completion (ERROR). A child exit code 2 is FAIL. Future aggregate codes
are 0/1/2 with ERROR dominating FAIL, and no SKIP. Declaration order is preserved,
the full set must validate before execution, and initial future execution should
continue sequentially after individual failures and safe local errors. Deliberate
recursive `aio verify` declarations are prohibited by the specification.

## Context Completion Rule

What changes: the Manifest contract, its schema and data-only uniqueness check,
template, terminology, tests, installed-schema proof, and these four artifacts.
Why: establish a reviewable contract before introducing repository-controlled code
execution. What stays unchanged: current seven-check `aio verify`, CLI flags,
Quality Gates, Task/Workflow/Role contracts, Orchestra's own Manifest, and package
resource architecture. Applicable Rules: repository AGENTS.md, Core principles,
precedence, context policy, standard-change, software-engineer, and existing Gates.
No Project Rules are present; no Stack Module is needed for this provider-neutral
data contract. Proof: contract cases, non-execution assertions, full regressions,
normal/editable install smoke, documentation consistency, and independent reviews.

The migration split is explicit: the contract exists after AIO-018, but AIO cannot
execute declared checks. Older valid Manifests remain valid with the updated
schema; older closed schemas are not promised to accept the new section.

The initial Human instruction required a stop after Stage 4 with status in_progress
and no commit. That checkpoint was honored. On 2026-09-17, the Human explicitly
approved closure and the scoped commit; approval is recorded in review.md.
No AIO-019, walkthrough, implementation plan, or fifth Task artifact is authorized.
