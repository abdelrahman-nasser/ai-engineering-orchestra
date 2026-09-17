# AIO-017 Review

## Implementation

The installed programmatic entry point is
engineering_orchestration.validation.validate_project. It returns a small result
with PASS/FAIL/ERROR and findings, separate from formatting. No CLI command was
added and verify retains its seven-check development battery unchanged.

engineering_orchestration.project owns upward root discovery and Manifest Task
path resolution. The CLI imports that shared implementation and passes the
resolved Task directory to the existing inventory/inspection capabilities.
Standalone inventory also uses the shared resolver. The canonical omitted-field
default is .ai/tasks/; an explicit path never silently falls back to it.

Schema error evaluation is shared with the Task, Manifest, and Workflow regression
harnesses and existing inspection/catalog code. Workflow-local Stage uniqueness
was extracted from the regression harness into the existing catalog module and
is reused by both. Fixture registries, exact negative-error checks, historical
Task coverage, templates, and schema self-tests remain in development harnesses.

The installed resource allowlist adds project-manifest.schema.json alongside the
existing Task and Workflow schemas. Canonical schema files are unchanged. Normal
installation uses importlib.resources without a checkout resource dependency.
The prior uninstalled source-wrapper compatibility path remains; it never searches
the target project for tool schemas. Role schema packaging is unnecessary because
portable Role project validation remains outside this slice.

## Validation Evidence

Environment: Windows, Python 3.12.10; validation date 2026-09-17.

| Command | Result |
| --- | --- |
| `python -B -m unittest discover -s tests -p "test_*.py" -v` | PASS: 144 tests, including 18 structural tests |
| `python -B schemas/tests/validate_task.py` | PASS: 34/34 cases, 7/7 Workflow references |
| `python -B schemas/tests/validate_workflow.py` | PASS: 42/42 checks |
| `python -B schemas/tests/validate_role.py` | PASS: 34/34 checks |
| `python -B schemas/tests/validate_project_manifest.py` | PASS: 12/12 cases |
| `python -B scripts/verify_repo.py` | PASS: 7/7 checks |
| `npx --yes markdownlint-cli2 "**/*.md"` | PASS: 81 Markdown files, 0 issues |
| `git diff --check` | PASS |
| `python -B aio.py tasks` | PASS: 17 Tasks, AIO-017 in_progress |
| `python -B aio.py inspect AIO-017` | PASS: VALID, RESOLVED, four artifacts |
| `python -B aio.py verify` | PASS: 7/7 checks |
| `python -B scripts/list_tasks.py --status in_progress` | PASS: AIO-017 |
| `python -B scripts/inspect_task.py .ai/tasks/AIO-017-installed-structural-validation --quiet` | PASS |
| `python -B tests/package_installation_smoke.py` | PASS: editable and normal installations |

Initial regression failures were corrected: the new fixture lacked required
Manifest fields; Windows short temporary paths differed from resolved paths in
I/O mocks; the CLI import assertion needed to permit the shared project module;
and Windows rooted `/absolute` needed explicit rejection. All subsequent checks
passed. The sandbox lacked Python discovery; approved outside-sandbox execution
used the existing Python 3.12.10 interpreter. No required check was skipped.

## Installed External Project Evidence

The reproducible smoke script created and removed this temporary tree:

```text
C:\Users\Abdelrahman\AppData\Local\Temp\aio017-07u5munx
  editable\
  normal\
  wheels\
  external project\
    .ai\project.yaml
    governance\tasks\unrelated-directory\task.yaml
    workflows\unrelated-filename.yaml
    src\nested\
```

Both installs passed external tasks and inspect LOCAL-123 from src/nested using
governance/tasks. The API passed valid data and returned FAIL for invalid Manifest,
invalid Task, duplicate Task ID, unresolved Workflow, duplicate Workflow ID, and
duplicate Stage ID. Mocked missing installed resources returned ERROR. Unit tests
add invalid YAML, missing metadata, denied I/O, validator failure, no fallback,
and Stage IDs repeated legitimately across different Workflows.

The normal wheel contained nine Python modules and exactly three canonical schema
resources, byte-identical to source. Implementation and all resource paths resolved
inside normal/Lib/site-packages, with no checkout on sys.path. PYTHONPATH and
PYTHONHOME were removed. The external project had no .git, tests, schemas,
Orchestra fixtures, historical Tasks, or node_modules. Structural probes prohibited
subprocess.run and subprocess.Popen. Git/Node were used only by the separate
unchanged Orchestra development preflight, never by external structural validation.

Both console installations also passed help, tasks, inspect, and verify from the
Orchestra root and scripts directory. Pip dependency checks, console alias,
uninstall, source-content digest, exact wheel payload, and temporary cleanup passed.

## Review and Human Checkpoint

Independent Reviewer: separate Agent execution /root/independent_review.
Outcome: APPROVE after remediation; no unresolved material findings.

The Reviewer inspected the request, acceptance criteria, actual diff and new files,
Role and gate contracts, regression preservation, installed resource isolation,
identity/path behavior, and prohibited-scope boundaries. Review found stale
inventory help text and a missing-directory diagnostic that reported the default
instead of the configured path. Both were corrected and independently rechecked.
A direct-wrapper regression was added; the full 144-test suite passed afterward.
The installed smoke preceded this help/diagnostic-only correction; no resources
or portable validation logic changed afterward.

Quality Gate evaluation: independent_review PASS, based on that separate review;
documentation_consistency PASS, based on comparison with implemented behavior,
existing contracts, and verified remediation. These evaluations are distinct from
structural PASS. No required gate failed or was skipped at the checkpoint.

## Human Approval and Closure

Human approval date: 2026-09-17. The Human explicitly approved AIO-017 and
authorized recording approval, completing acceptance criteria, setting status to
completed, and committing the approved scope with the message
`feat: add installed structural validation (AIO-017)`.
Independent review outcome remains APPROVE; both required Quality Gates passed.

Approval covers the reviewed installed structural API, shared Manifest Task-path
resolver, canonical packaged resources, regression reuse, tests, and documentation.
Installed structural validation is portable: editable and normal installation,
external project, and custom Task-directory evidence passed without checkout
leakage or adopter development-tool requirements. Closure changes only Task
documentation and status, so the reviewed installation evidence remains valid.

Project-authored command execution was NOT introduced. aio verify remains
Orchestra-development-specific with all seven checks. Role Markdown extraction
remains test-only, not runtime serialization; no new Role representation contract,
runtime parser, migration, or discovery contract was introduced. Structural results
remain separate from Quality Gate evaluation and Task/Workflow execution.

All eight acceptance criteria were verified against implementation, recorded test
evidence, and independent review. The pre-approval stop was honored; this explicit
Human decision now authorizes closure. Task status is completed, with exactly four
canonical artifacts. No historical Task or schema semantics changed; no AIO-018
or project-verification command contract was created.

Closure pre-commit regression on 2026-09-17: all 144 tests (18 structural), Task
34/34 and references 7/7, Workflow 42/42, Role 34/34, Manifest 12/12, and live
preflight 7/7 passed. Markdown lint reported 0 issues and git diff --check passed.
No required validation or Quality Gate was waived, failed, or skipped at closure.
The requested post-commit regression and clean-tree checks are reported with the
final commit in the closure response.

## Observations

- Genericity: data-only validation works independently of target language and
  development tools. Generic verify is still absent.
- Validator reuse: schema error evaluation and Workflow uniqueness moved into
  installed code; regression orchestration remains development-only.
- Task path configuration: the existing Manifest contract now drives all three
  capabilities, while identity remains declared metadata.
- Package resources: installed ownership is proven without schema copies.
- Role representation: no pressure was resolved by inventing a runtime format;
  project Role validation is explicitly outside coverage.
- Quality Gate boundary: structural evidence does not establish documentation
  consistency, independent review, or Human approval.
- Command execution: none in the portable layer. A future project check contract
  requires separate trust, argument, cwd, timeout, and Windows design.
- Dogfooding: existing Orchestra commands and the seven development checks remain
  intact while the external project proves portable structural behavior.
- Runtime pressure: no lifecycle selection, stage state, actor assignment, or
  runtime orchestration is introduced.

The evidence supports considering project-declared mechanical checks as the next
product limitation. It does not authorize their implementation. The most concrete
remaining limitation is that aio verify still requires Orchestra's development
battery and cannot run an adopter project's own mechanical checks.
