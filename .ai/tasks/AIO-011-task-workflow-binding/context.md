# AIO-011 — Context

## Authority and Scope

Direct dependency: AIO-010, closed at `ecdbd2d`.
The Human approved the Task→Workflow binding design with three explicit corrections and
authorized proceeding with AIO-011 — Add Machine-Readable Task Workflow Binding.

AIO-011 is a narrow, evidence-backed integration improvement discovered during AIO-010
vertical-slice execution. It is an implementation Task (`type: implementation`), NOT a
new foundation abstraction.

## Core Objective and Conceptual Distinctions

AIO-011 introduces the optional machine-readable Task field:
```yaml
workflow: standard-change
```

Semantic meaning:
> `workflow` records the stable identifier of the Workflow explicitly selected to govern this Task.

This is BINDING only. It SHALL NOT:
- automatically select a Workflow,
- infer from Task type, risk, or complexity,
- execute Workflow stages,
- configure a runtime,
- assign actors,
- create stage state,
- alter the referenced Workflow.

The canonical distinctions preserved in AIO are:
- **Selection**: Deciding which Workflow applies (conducted explicitly by Human/orchestrator).
- **Binding**: Recording that decision on the Task (`workflow` field on `task.yaml`).
- **Resolution**: Loading and verifying the referenced Workflow definition.
- **Execution**: Traversing its stages at runtime.

AIO-011 primarily solves **Binding**. It provides identity visibility without deep resolution
or runtime execution.

## First Canonical Task with Machine-Readable Workflow Binding

AIO-011 itself uses the newly introduced field:
```yaml
workflow: standard-change
```
This is the first canonical Task in AI Engineering Orchestra using machine-readable
Workflow binding.

Historical Tasks AIO-001 through AIO-010 remain untouched and without a `workflow` field,
serving as authentic evidence of the framework's evolution. Because `workflow` is optional,
all historical Tasks remain structurally valid under the updated schema.

## Governing Workflow and Role Fulfillment

Governing Workflow: `standard-change` (explicitly declared on `task.yaml`).

Ordered Workflow stages:
1. `understand`
2. `implement`
3. `validate`
4. `review`

Role fulfillment and stage execution:
- **Stage 1 — `understand`**:
  No `required_roles` declared by `workflows/standard-change.md`.
  Primary implementation actor verifies context acquisition and satisfies Context Completion Rule.
- **Stage 2 — `implement`**:
  Required Role: `software-engineer`.
  Fulfilled by primary implementation actor.
- **Stage 3 — `validate`**:
  No `required_roles` declared by `workflows/standard-change.md`.
  Primary implementation actor executes deterministic verification commands.
- **Stage 4 — `review`**:
  Required Role: `reviewer`.
  Fulfilled by a separate independent review execution with clean review context.
  Human Control checkpoint: `true`.
- **Human Control**:
  Human Project Owner. Final review and approval are required before Task completion.

## Quality Gate Determination

**Role requirement != Quality Gate requirement.**
- Project required gates: `documentation_consistency`, `independent_review` (from `.ai/project.yaml`)
- Workflow stage required gates: None (the `standard-change` Workflow declares no mandatory gate floor)
- Task quality gates: `documentation_consistency`, `independent_review` (from `task.yaml`)

Effective union:
- `documentation_consistency`
- `independent_review`

## Evidence Terminology

In accordance with established framework policy, evidence is described using truthful, accurate terminology:
- auditable evidence,
- version-controlled evidence,
- recorded verification evidence.

No claims of cryptographic "tamper-evident evidence" are made.

## Three User Corrections Incorporated

1. **Correction 1 — Do NOT renumber Task Specification sections**:
   Semantics for `workflow` are added cleanly to `core/task-specification.md` without renumbering subsequent sections, preserving existing internal and external documentation references.
2. **Correction 2 — Do NOT modify existing `valid-full.yaml` unless genuinely necessary**:
   Existing Task test fixtures (`valid-minimal.yaml`, `valid-full.yaml`, etc.) remain completely untouched. Positive coverage is provided by dedicated new fixtures `valid-workflow-standard.yaml` and `valid-workflow-custom.yaml`, directly proving optional backward compatibility.
3. **Correction 3 — Explicit semantic reference verification in review evidence**:
   Review evidence will explicitly inspect canonical Workflow definitions, verify that `standard-change` is the declared `id` of the governing Workflow (authoritative ID, not filename assumption), and document this check in `review.md`. No production Markdown parser is introduced into `inspect_task.py`.

## Context Completion Rule Evaluation

Before transitioning from `planned` to `in_progress` and beginning source implementation,
the Context Completion Rule (`core/context-policy.md` §22) is satisfied:

1. **What am I changing?**
   - Updating `core/task-specification.md` to add `workflow` field semantics without section renumbering.
   - Updating `schemas/task.schema.json` to add optional `workflow` string property with `minLength: 1`.
   - Adding dedicated valid and invalid Task schema test fixtures in `schemas/tests/task/`.
   - Updating `schemas/tests/validate_task.py` to register new fixtures and register AIO-011.
   - Enhancing `scripts/inspect_task.py` to read `task.yaml.workflow` and report `TASK-DECLARED` vs `NOT DECLARED` with truthful v0.1 limitation notice.
   - Updating `tests/test_inspect_task.py` with comprehensive test coverage.
   - Maintaining the four canonical Task artifacts in `.ai/tasks/AIO-011-task-workflow-binding/`.

2. **Why am I changing it?**
   To provide machine-readable Task→Workflow binding visibility on Tasks, addressing the integration gap discovered during AIO-010 while respecting the foundation freeze and keeping resolution and execution decoupled.

3. **What must remain unchanged?**
   - Workflow semantics and Workflow schema (`schemas/workflow.schema.json`).
   - Project Manifest semantics and schema (`schemas/project-manifest.schema.json`).
   - Role specifications and schemas.
   - Core policies (`precedence.md`, `context-policy.md`, `human-control.md`, `principles.md`, `terminology.md`).
   - Historical Tasks AIO-001 through AIO-010.
   - Existing Task fixtures (`valid-full.yaml`, `valid-minimal.yaml`, etc.).

4. **What Rules apply?**
   AGENTS.md, `workflows/standard-change.md`, `core/precedence.md`, `core/context-policy.md`,
   `core/human-control.md`, `core/task-specification.md`, and user instructions with corrections 1, 2, 3.

5. **What proves the Task is complete?**
   - Unit tests pass with comprehensive coverage.
   - All repository schema validators pass (`validate_task.py`, `validate_workflow.py`, `validate_role.py`, `validate_project_manifest.py`).
   - `git diff --check` passes with 0 whitespace errors.
   - `inspect_task.py` correctly reports status, artifacts, schemas, gates, human control, and workflow binding.
   - Historical Tasks remain valid without modification.
   - Manual semantic reference verification of AIO-011 workflow binding against canonical workflow definition is recorded in `review.md`.
   - Independent review is conducted by a separate reviewer with clean context and passes.
   - Quality Gates `documentation_consistency` and `independent_review` pass.
   - Human approval is obtained before final closure.
