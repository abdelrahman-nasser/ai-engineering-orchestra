# AIO-016 Context

## Context Completion

1. Change: install the five existing capability modules under the technical,
   brand-neutral `engineering_orchestration` namespace. Add setuptools metadata,
   one `aio` console entry point, schema resources, and thin source compatibility
   wrappers. No capability is reimplemented.
2. Reason: remove checkout-path and `python -B aio.py` invocation friction.
3. Preserve: CWD ancestor discovery of `.ai/project.yaml`, command/exit semantics,
   target-owned Workflows, declared Task identity, the seven-check preflight,
   historical Tasks, schema semantics, and mechanical evidence != gate approval.
4. Rules: Core principles, precedence, context completion, Human control,
   `standard-change`, `software-engineer`, `reviewer`, documentation consistency,
   and independent review apply. The explicit Human instruction authorizes this
   package boundary and narrow roadmap exception, not completion or a commit.
5. Evidence: existing regressions plus clean editable and normal installations,
   source-independent imports/resources, root/subdirectory CLI exercises,
   an external project, artifact inspection, alias and uninstall experiments,
   and genuinely independent review. Stop at the Human review checkpoint.

## Scope and Roadmap Authorization

AIO-016 is an explicitly authorized narrow pull-forward of local installability,
console invocation, and package-boundary validation. It does not complete the
future public distribution, release automation, or general CLI distribution
milestones. No AIO-017, public publication, or commit is authorized.

## Ownership and Compatibility

The installed tool owns code plus `task.schema.json` and `workflow.schema.json`.
Canonical files in `schemas/` remain authoritative; setuptools maps that directory
into a private resource namespace with an explicit two-file allowlist. Runtime
access uses `importlib.resources`. Uninstalled source execution can use those same
canonical files via a narrowly identified source checkout; it never searches the
managed project's CWD for tool schemas.

The managed project owns `.ai/project.yaml`, `.ai/tasks/`, and `workflows/`.
The router passes discovered project paths explicitly. Tests, validators, fixtures,
Task evidence, Git state, and development documentation are not runtime package
resources. Existing source-relative standalone defaults remain compatibility
behavior; installed CLI discovery always starts from CWD.

`tasks` and `inspect` are partially generic and still assume conventional Task
and Workflow directories. `verify` remains Orchestra development tooling with
the established repository check targets, Git, and Node/npm (`npx`) prerequisites.
It is not a generic verification system. Its Python subprocesses use the tool's
interpreter, retain explicit `-B`, and use argument lists, `shell=False`, and the
active project CWD. No checks are skipped or generalized for installation.

## Metadata Decisions

- Distribution: `ai-engineering-orchestra`, a local metadata identity, with no
  public name reservation or availability claim.
- Console: temporary `aio`; namespace: technical `engineering_orchestration`.
- Display name and historical `AIO-*` Task IDs are separate identities.
- Existing runtime imports require `PyYAML>=6,<7` and `jsonschema>=4,<5`.
  Declaring them makes installation truthful; it adds no runtime capability.
- Setuptools is a build dependency, not a product runtime dependency.
- AIO-016 establishes Python >=3.12 as the first packaging support baseline;
  the repository did not historically guarantee it. Validate on Python 3.12.
- Static distribution version `0.1.0` identifies installed code. Manifest
  `orchestra.version` identifies the managed project's framework expectation.
  Equality does not make them one source, and no dynamic synchronization is added.
- Console launchers may write normal Python bytecode. Suppressing installed
  `__pycache__` is not a product requirement; no launcher hacks emulate `-B`.

## Exclusions

No public publishing, release CI/CD, package managers or native installers,
Docker distribution, automatic updates, completion, telemetry, licensing, cloud
accounts, GUI, generic verification, plugins/check configuration, new commands,
JSON output, Task mutation, Assignment, Gate Results, Agent/Workflow execution,
product rename, dynamic versioning, or broad domain redesign.
