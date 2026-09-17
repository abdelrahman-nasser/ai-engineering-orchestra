# AIO-016 Review

## Scope

The Human explicitly authorized a narrow local-installability experiment,
console command, and package-boundary validation. This does not complete public
distribution, release automation, or the future general distribution milestone.
`verify` remains Orchestra-development-specific. No public publishing is included.

## Implementation

The five capabilities moved mechanically into `engineering_orchestration`.
Legacy `scripts` modules delegate and preserve module identity for existing
imports; `aio.py` calls the packaged router. No second capability implementation
exists. Preflight's seven commands, exit classification, and runner are unchanged.

Setuptools explicitly packages the implementation and maps canonical `schemas/`
to `engineering_orchestration._schemas`, allowing only the two required JSON
files. No schema source was copied or semantically modified. Installed resource
lookup uses `importlib.resources`; uninstalled source wrappers use their own
checkout's canonical resources, never a CWD schema fallback. Schema access accepts
resource Traversables rather than requiring filesystem-only Paths.

Static metadata declares distribution `ai-engineering-orchestra` version `0.1.0`,
console `aio`, and technical namespace `engineering_orchestration`. The package
version and managed-project `orchestra.version` have different meanings. Python
>=3.12 is a new AIO-016 baseline, tested on 3.12.10, not a historical guarantee.
Existing runtime dependencies are `PyYAML>=6,<7` and `jsonschema>=4,<5`;
`setuptools>=77.0.3` is build-only. No runtime capability was added.

## Validation

Validation date: 2026-09-17. Environment: Windows, Python 3.12.10.

| Exact source command | Result |
| --- | --- |
| `python -B -m unittest discover -s tests -p "test_*.py" -v` | PASS: 126 tests; 10 focused packaging tests |
| `python -B schemas/tests/validate_task.py` | PASS: 33/33 cases; 6/6 Workflow references |
| `python -B schemas/tests/validate_workflow.py` | PASS: 42/42 checks |
| `python -B schemas/tests/validate_role.py` | PASS: 34/34 checks |
| `python -B schemas/tests/validate_project_manifest.py` | PASS: 12/12 cases |
| `python -B scripts/verify_repo.py` | PASS: 7/7 mechanical checks |
| `npx --yes markdownlint-cli2 "**/*.md"` | PASS: 78 Markdown files; 0 issues |
| `git diff --check` | PASS |
| `python -B aio.py tasks` | PASS: 16 Tasks; AIO-016 in_progress |
| `python -B aio.py inspect AIO-015` | PASS: VALID; Workflow RESOLVED |
| `python -B aio.py verify` | PASS: 7/7 checks |
| `python -B tests/package_installation_smoke.py` | PASS: two clean venvs, wheel, external fixture, alias, uninstall, cleanup |

The first regression run found a removed legacy `REPO_ROOT` import used by the
inventory tests. Retaining the constant (without import-path mutation) resolved
it; all 126 tests then passed. Python discovery for new shell commands failed
inside the sandbox. Approved execution outside the sandbox supplied Python 3.12.10
and access needed to install build/runtime dependencies. No unresolved failed
validation remains. There was no change to the seven-check battery to obtain PASS.

## Isolated Installation Evidence

The reproducible integration entry point is
`python -B tests/package_installation_smoke.py`. It is intentionally not collected
by ordinary unit-test discovery, so installed preflight cannot recurse into pip
installation. It creates clean venvs without system site packages and removes
`PYTHONPATH` and `PYTHONHOME` from subprocess environments.

For the recorded run, use these exact path substitutions:

```text
R = D:\Dev\ai-engineering-orchestra
T = C:\Users\Abdelrahman\AppData\Local\Temp\aio016-jjb4z90o
E = T\editable\Scripts
N = T\normal\Scripts
X = T\external project
```

The script executed the following commands with substituted absolute paths:

```text
E\python.exe -m pip install -e R
E\python.exe -m pip check
N\python.exe -m pip wheel --no-deps --wheel-dir T\wheels R
N\python.exe -m pip install T\wheels\ai_engineering_orchestra-0.1.0-py3-none-any.whl
N\python.exe -m pip check
```

Both `E\aio.exe` and `N\aio.exe` passed all four invocations below from **each**
of `R` and `R\scripts`, including the complete development preflight:

```text
aio.exe --help
aio.exe tasks
aio.exe inspect AIO-015
aio.exe verify
```

Each command exited 0; both root/subdirectory `verify` runs in both environments
reported 7/7 checks passed. Direct executable paths avoid any dependence on a
previous global `aio` command or environment activation.

Both environments passed `aio.exe tasks` and `aio.exe inspect LOCAL-123` from
`X\src\nested`. The target has no tool schemas. Inspection resolved its own
`external-flow` Workflow from an unrelated filename and reported `external_gate`.
Missing project marker returned 2; missing declared Task ID returned 1.
External `verify` was intentionally not applicable and was not run: the fixture
does not have the development battery. No verifier checks were skipped or made
configurable to manufacture generic success.

The integration script's Python import/resource probe recorded:

```text
Editable module: R\engineering_orchestration\cli.py
Editable schemas: R\schemas\{task,workflow}.schema.json
Normal module: T\normal\Lib\site-packages\engineering_orchestration\cli.py
Normal schemas: T\normal\Lib\site-packages\engineering_orchestration\_schemas\{task,workflow}.schema.json
```

The normal probe ran from the external project's nested directory. Its `sys.path`
contained CWD, Python stdlib locations, and the normal venv, with no source checkout.
Assertions verified both schema paths and the implementation path were inside
that venv. Thus normal installation did not borrow source imports or resources.

## Artifact, Alias, and Uninstall Evidence

Wheel payload was exactly:

```text
engineering_orchestration/__init__.py
engineering_orchestration/cli.py
engineering_orchestration/inspect_task.py
engineering_orchestration/list_tasks.py
engineering_orchestration/schema_resources.py
engineering_orchestration/verify_repo.py
engineering_orchestration/workflow_catalog.py
engineering_orchestration/_schemas/task.schema.json
engineering_orchestration/_schemas/workflow.schema.json
ai_engineering_orchestra-0.1.0.dist-info/METADATA
ai_engineering_orchestra-0.1.0.dist-info/WHEEL
ai_engineering_orchestra-0.1.0.dist-info/entry_points.txt
ai_engineering_orchestra-0.1.0.dist-info/top_level.txt
ai_engineering_orchestra-0.1.0.dist-info/RECORD
```

The script compared both wheel schemas byte-for-byte against canonical sources.
There were no Tasks, tests, schema validators, fixtures, Git metadata, or unrelated
documentation. No sdist was generated. Nothing was uploaded or published.

For each installation, an in-memory `EntryPoint(name='rook', ...)` built from
installed `aio` metadata loaded the identical `main` callable. Calling that
function with `sys.argv = ['rook', '--help']` exited 0 with `rook` usage text.
No permanent `rook` entry point or deprecation behavior was introduced.

Both `E\python.exe -m pip uninstall -y ai-engineering-orchestra` and the matching
`N` command passed. Each removed `aio.exe` and package discoverability outside the
source tree. Before/after source hashes were identical. The temporary directory,
both venvs, wheel, and fixture were removed successfully. No permanent installation
was left on the developer machine.

## Scope Integrity and Observations

- Historical Tasks AIO-001 through AIO-015 are unchanged. The Task directory has
  exactly four artifacts and only AIO-016 was added to canonical validation.
- Packaging friction was limited to mechanical imports, compatibility delegates,
  resource types, and explicit package selection. No domain redesign was needed.
- Fresh environments received existing dependencies solely through package metadata;
  no undeclared runtime dependency was found.
- Mapping canonical schemas to a private resource namespace worked for both editable
  and normal installations without a second source copy or generation tooling.
- Legacy source-location defaults remain for standalone compatibility; installed
  CLI project discovery remains CWD-based. No launcher hacks reproduce `-B`.
- Console aliasing needed no domain change. Product naming remains an edge concern.
- `tasks` and `inspect` remain partially generic; conventional directories are
  still assumed. `verify` remains tied to Orchestra development targets and the
  tool interpreter. The most concrete next product limitation is verification
  portability to adopting projects, not another installation channel.

## Independent Review

Reviewer: separate Agent execution `/root/aio016_review`, acting as `reviewer`.
Outcome: **APPROVE**, 2026-09-17.

The reviewer read the authorized request and applicable governance, inspected the
actual old/new module differences, metadata, wrappers, schema mapping, focused
tests, installation harness, and final recorded evidence. The review confirmed
the preflight implementation's behavior remained unchanged, resources and runtime
dependencies were correct, source-independent installation assertions were
meaningful, historical Tasks and schemas were unchanged, and no public release,
generic-verification, or roadmap-completion claim was introduced.

The only finding was stale CLI docstrings referring to future installation and
old implementation locations. Those were corrected; the reviewer inspected the
correction and final evidence before approving. This docstring-only correction
does not change the installed behavior validated by the smoke experiment.

The reviewer independently ran `git diff --check` and checked historical/schema
integrity. Installation results were evaluated through the actual integration
harness and recorded evidence, not represented as a second independent install.

Required Quality Gates:

- `documentation_consistency`: PASS, after final documentation review and lint.
- `independent_review`: PASS, separate reviewer APPROVE with no unresolved findings.

No required Quality Gate failed or was skipped. Mechanical validation supports
these judgments but does not itself grant gate satisfaction or Human approval.

## Human Control

Human approval date: **2026-09-17**.
Independent review outcome: **APPROVE**.
Closure authorization: **APPROVED** by explicit Human instruction.
Final Task status: **completed**.

Approval covers the reviewed local package installation, setuptools metadata,
neutral package boundary, temporary `aio` console command, canonical schema
resource mapping, compatibility delegates, dependency and Python support metadata,
tests, documentation, and isolated installation evidence. The Human authorized
recording closure and committing only the approved AIO-016 change set as
`feat: add local CLI package installation (AIO-016)`.

Editable and normal installations were validated in separate clean temporary
environments. Outside-source-tree imports/resources, external project Task
inventory and inspection, aliasing, and uninstall passed. This evidence remains
valid: closure changes only Task lifecycle/approval documentation, not package
metadata, layout, resources, dependencies, or console behavior.

The package/managed-project boundary is preserved: CWD ancestry selects the
active project; installed package location does not. Tool schemas remain derived
from one canonical source, while target Workflows and Tasks remain project-owned.
The five identities (distribution, console, import namespace, display name, and
historical Task prefix) remain separate and no permanent rename is performed.

Public distribution was **not authorized**. Generic verification was **not
claimed**: `verify` remains Orchestra development tooling. No publishing, release
automation, permanent machine installation, AIO-017, or generic verification work
is included in this closure.

## Closure Validation

After recording approval and completed status on 2026-09-17, the full requested
source regression battery was rerun: 126 tests (including 10 packaging tests),
Task validation 33/33 plus 6/6 Workflow references, Workflow validation 42/42,
Role validation 34/34, and Project Manifest validation 12/12 all passed.
`python -B scripts/verify_repo.py` and `python -B aio.py verify` both passed 7/7
checks. Source `tasks` and `inspect AIO-015` succeeded; inventory now reports
AIO-016 completed. Markdownlint found 0 issues across 78 files and
`git diff --check` passed. The four-artifact Task boundary is unchanged.

The earlier isolated editable, normal, outside-source-tree, external-project,
and uninstall evidence remains applicable; no package-affecting closure change
required repeating those experiments. Post-commit regression results are reported
with the final commit rather than creating a self-referential follow-up commit.
