# AI Engineering Orchestra

AI Engineering Orchestra is a reusable, versioned, model-agnostic framework for organizing AI-assisted software engineering.

It provides a common structure for:

- AI Agent Roles
- engineering Workflows
- project Rules
- Quality Gates
- Risk and Complexity handling
- Human approval
- project context
- future Provider routing and security controls

The framework is designed to work independently of any specific AI Provider, model, programming language, framework, or application architecture.

---

## Current Version

```text
0.1.0
```

## Local CLI Installation

Python 3.12 or newer is required for the locally installable CLI. AIO-016
establishes this initial packaging baseline; it is not a historical support claim.
From this checkout, in a virtual environment:

```powershell
python -m pip install -e .
aio --help
aio tasks
aio inspect AIO-015
aio verify
aio verify --structure
```

For a normal installation, use `python -m pip install .` instead. The command is
available when the installing environment's `Scripts` (Windows) or `bin` directory
is on PATH, usually by activating the environment. Editable installations follow
source edits; metadata/console-name changes require reinstalling. Normal installs
must be reinstalled to receive source changes. Uninstall with
`python -m pip uninstall ai-engineering-orchestra`; the checkout remains intact.

Run commands from the managed project or a subdirectory. The nearest ancestor
containing `.ai/project.yaml` determines the active project, never the installed
package location. `tasks` and `inspect` resolve `tasks.directory` from the active
Manifest (default `.ai/tasks/`). Workflows remain in the target project's
`workflows/`; canonical schemas and Roles belong to the tool. An adopter's own
`roles/` directory is ignored because project Role extensions and overrides are
not part of the current contract.

`aio verify` validates the active project's supported AIO structure and then runs
its project-declared Verification Checks from `.ai/project.yaml` in declaration
order. Omitted or empty checks mean zero commands; AIO does not infer checks from
repository contents and has no Orchestra-specific fallback. Before execution the
CLI names the declaration source and ordered Check IDs. `aio verify --structure`
is the non-executing inspection path: it validates supported structure without
planning, resolving, or running declared commands.

Declared commands use the caller's filesystem access, network access,
credentials, environment, and process authority. AIO provides no sandbox,
filesystem or network isolation, credential isolation, purity, read-only
guarantee, harmlessness, or full descendant containment. Bounded failure output
is unsanitized and may enter terminal or CI logs. The inherited
`ENGINEERING_ORCHESTRATION_VERIFY_DEPTH` marker blocks ordinary nested aggregate
verification, but wrappers can remove it and arbitrary recursion cannot be
proven absent. Repository declarations and command availability do not authorize
an Agent to invoke verification or grant any execution authority. Mechanical
PASS is not Quality Gate satisfaction or Human approval.

This repository dogfoods the same portable path with seven Manifest declarations.
Git and Node/npm (`npx`) must already be available on PATH; they are not Python
dependencies and are not installed automatically. Verification must run from a
supported/activated development environment where PATH-selected `python` has the
repository's required dependencies.

Source commands (`python -B aio.py ...` and `python -B scripts/list_tasks.py`,
`scripts/inspect_task.py`, `scripts/verify_repo.py`) remain available. Normal console
launchers may write Python bytecode; suppressing installed `__pycache__` is not a
product requirement. Preflight Python subprocesses retain their explicit `-B`.

The local distribution name `ai-engineering-orchestra`, temporary console name
`aio`, technical namespace `engineering_orchestration`, product display name,
and historical `AIO-*` Task IDs are separate identities. Another console name can
target the same router without changing capabilities. The static distribution
version `0.1.0` identifies installed code; Manifest `orchestra.version` expresses
the managed project's framework expectation. No version synchronization is implied.

This is an explicitly authorized local-installability experiment. It does not
complete the future public distribution milestone. No PyPI publication, public
name reservation, release automation, or full CLI lifecycle is provided.

## Installed Structural Validation

The programmatic API reads the nearest active project's supported AIO structures:

```python
from engineering_orchestration.validation import validate_project

result = validate_project()  # CWD, then ancestors containing .ai/project.yaml
print(result.status)  # PASS, FAIL, or ERROR
for finding in result.findings:
    print(finding.status, finding.path, finding.message)
```

An optional `start=Path(...)` chooses the discovery starting directory. Validation
covers the Project Manifest, immediate Task child directories in the configured
Task path, declared Task ID uniqueness, Workflow YAMLs and ID uniqueness,
Workflow-local Stage ID uniqueness, declared Task-to-Workflow references, and
Workflow-to-framework-Role references.
Directory and file names do not define IDs. Missing required project structures
or invalid data produce FAIL; missing installed resources, I/O problems, and
internal failures produce ERROR. ERROR takes precedence over FAIL. PASS covers
only the supported structural rules, without establishing Quality Gate results.

The installed tool packages canonical Actor, Actor Availability Observation,
Assignment, Role, Task, Workflow, and Project Manifest schemas from their single
sources in `schemas/`, plus the five framework-owned canonical Role YAML
instances from `roles/`. Managed projects
need no schema regression scripts, fixtures, Orchestra Task history, Git,
Node/npm, or Python tests. Python and the declared tool dependencies run the
validator; the target project's own language is irrelevant. The API executes no
project commands and changes no files. No Actor catalog exists. No SKIP results
are emitted.

## Runtime Role Catalog

Canonical Role instances are machine-readable and package-owned:

```python
from engineering_orchestration.role_catalog import load_role_catalog

catalog = load_role_catalog()
role = catalog.get("software-engineer")
print(catalog.role_ids, role["required_capabilities"])
```

The catalog safe-loads and validates packaged `roles/*.yaml`, indexes by declared
Role `id` rather than filename, rejects duplicate IDs, and returns `None` for an
unknown lookup. It never searches CWD or a managed project's `roles/` directory.
The authority order is Role specification, Role schema, canonical Role YAML,
then non-authoritative Markdown compatibility stubs. The catalog does not select
or assign Actors, inspect availability, authorize execution, or evaluate Quality
Gates.

## Actor Competency Coverage

The framework defines a Provider-neutral Actor as a concrete Human or Agent
candidate with an ID, kind, and engineering competencies. The pure evaluator
compares already-normalized Actor competencies with Role requirements:

```python
from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.role_catalog import load_role_catalog

role = load_role_catalog().get("software-engineer")
coverage = evaluate_actor_role_coverage(actor, role)
print(coverage.compatible, coverage.missing_competencies)
```

Matching is exact and case-sensitive. A Role with empty required capabilities is
explicitly non-matchable. Coverage is evidence only: it does not rank, select,
assign, authorize, or execute an Actor; inspect availability; or produce a
Quality Gate result. The semantic contract is defined in
[`core/actor-specification.md`](core/actor-specification.md).

## Actor Availability Observation

Availability is a separate, ephemeral runtime observation over supplied Actors:

```python
from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
    validate_actor_availability,
)

observations = [
    ActorAvailabilityObservation("agent-engineer-1", AvailabilityState.AVAILABLE)
]
result = validate_actor_availability(observations, actors)
print(result.valid, result.normalized_observations)
```

Each observation contains only `actor_id` and `state`, where state is exactly
`available`, `unavailable`, or `unknown`. A known Actor without an observation
normalizes to unknown, never unavailable. Duplicate observations and unknown
Actor references invalidate the snapshot without producing partial normalized
output. Human and Agent Actors use identical semantics.

Availability does not change Actor identity or competency coverage, affect
Assignment validity, grant authority, or imply execution. The validator performs
no selection, persistence, Provider integration, polling, or network access. The
semantic contract is defined in
[`core/actor-availability-specification.md`](core/actor-availability-specification.md).

## Assignment Responsibility Bindings

An Assignment records one externally selected Actor for one required
Task/Workflow/Stage/Role responsibility:

```python
from engineering_orchestration.assignment import (
    Assignment,
    validate_assignment_set,
)

binding = Assignment(
    task_id="AIO-023",
    workflow_id="architecture-change",
    stage_id="implement",
    role_id="software-engineer",
    actor_id="agent-engineer-1",
)
result = validate_assignment_set(
    [binding], task, workflow_catalog, role_catalog, actors
)
print(result.valid, result.complete, result.unassigned_requirements)
```

Validation checks exact Task and Workflow consistency, Stage and Role
requirements, unique supplied Actor identities, and existing competency coverage.
Sequence validation separately reports duplicate bindings, completeness,
unassigned requirements, and definite implementer/Reviewer Actor-ID conflicts.
It does not select Actors, inspect availability, persist values, grant authority,
execute work, manage Workflow state, or establish a Quality Gate result. The
semantic contract is
[`core/assignment-specification.md`](core/assignment-specification.md).

AIO-018 defines the optional Project Verification Check contract in
[`core/project-manifest.md`](core/project-manifest.md#33-verification--project-verification-checks),
at `.ai/project.yaml` → `verification.checks`. Declarations contain `id`, an
argument-array `command`, optional project-relative `cwd`, and optional positive
`timeout_seconds` (default `600`). Structural validation checks their shape and
ID uniqueness without executing them. Existing Manifests remain valid; omitted
checks mean zero declarations, with no automatic command discovery.

The contract has a programmatic planner, runner, and thin aggregate composition:

```python
from pathlib import Path
from engineering_orchestration.project_verification import (
    plan_project_checks,
    run_project_checks,
    verify_project,
)

planning = plan_project_checks(Path("/path/to/project"))
if planning.is_ready:
    evidence = run_project_checks(planning.plan)

aggregate = verify_project(Path("/path/to/project"))
```

Planning validates all declarations and resolved working directories before any
command runs. Execution is sequential, noninteractive, timeout-bounded, and
captures bounded stdout/stderr excerpts as PASS, FAIL, or ERROR evidence. Commands
use the caller's existing authority and inherited environment; declarations grant
no permission, promise no sandbox, and do not establish Quality Gate results.
Timeout or interruption cleanup covers the direct child only, not all descendants.
Only planning readiness gates project command execution, so unrelated Task or
Workflow structural findings remain reported without suppressing a valid plan.
Aggregate exit codes are 0 for PASS, 1 for FAIL without ERROR, 2 for any ERROR,
and 130 when the public CLI is interrupted by the user.
