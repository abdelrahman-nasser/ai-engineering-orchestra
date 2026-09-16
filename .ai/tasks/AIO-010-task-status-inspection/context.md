# AIO-010 — Context

## Authority and Scope

Direct dependency: AIO-009, closed at `d94943fcfcbffc58a69a473b64c8d37446554dc9`.
The Human approved the vertical-slice architecture with four explicit corrections and
authorized proceeding with AIO-010 — Implement Task Status Inspection Utility.

AIO-010 is the first real governed vertical slice. It is an implementation Task,
not a new foundation specification. No new foundation contracts or schemas are
created. Frozen Core semantic contracts, canonical Role semantics, canonical
Workflow semantics, Human Control semantics, Quality Gate definitions, Precedence,
and JSON schemas remain untouched.

## Governing Workflow

Explicit Human/orchestrator selection: `standard-change`.

> This is explicit Human/orchestrator Workflow selection for the first vertical slice. It is not machine-readable Task→Workflow binding and does not modify the Task schema.

Ordered Workflow stages:
1. `understand`
2. `implement`
3. `validate`
4. `review`

## Temporary Role Fulfilment and Stage Actors

No Assignment Contract artifacts are created. Operational mapping is recorded
directly here in `context.md` and evaluated in `review.md`.

In accordance with Correction 1, the distinction between the Actor performing
a Stage and the Role required by the Workflow is preserved:

- **Stage 1 — `understand`**:
  No `required_roles` are declared by `workflows/standard-change.md`.
  The primary implementation actor executes context acquisition and verifies
  satisfaction of the Context Completion Rule.
- **Stage 2 — `implement`**:
  Required Role: `software-engineer`.
  Fulfilled by the primary implementation actor.
- **Stage 3 — `validate`**:
  No `required_roles` are declared by `workflows/standard-change.md`.
  The primary implementation actor executes deterministic verification commands.
- **Stage 4 — `review`**:
  Required Role: `reviewer`.
  Fulfilled by a separate independent review execution with clean review context.
  Human Control checkpoint: `true`.
- **Human Control**:
  Human Project Owner. Final review and approval are required before Task completion.

## Quality Gate Determination

In accordance with Correction 2:
**Role requirement != Quality Gate requirement.**

The requirement for the `reviewer` Role in Stage 4 does not automatically invoke
the `independent_review` Quality Gate; they are distinct governance contracts.

For AIO-010, the effective Quality Gate set is computed strictly from authoritative sources:
- Project required gates: `documentation_consistency`, `independent_review` (from `.ai/project.yaml`)
- Workflow stage required gates: None (the `standard-change` Workflow declares no mandatory gate floor)
- Task quality gates: `documentation_consistency`, `independent_review` (from `task.yaml`)

Effective union:
- `documentation_consistency`
- `independent_review`

## Evidence Terminology

In accordance with Correction 3, AIO does not claim to provide "tamper-evident evidence."
Evidence is described using truthful, accurate terminology:
- auditable evidence,
- version-controlled evidence,
- recorded verification evidence.

No hashes, cryptographic signing, attestations, or new evidence schemas are introduced.

## Known Workflow-Selection Integration Gap

In accordance with Correction 4, `scripts/inspect_task.py` SHALL NOT machine-parse
the `## Governing Workflow` section from `context.md` as a machine-readable Workflow binding.
Doing so would accidentally establish a new machine contract outside the approved Task schema.
The utility must make this limitation visible and report:
`Workflow: NOT MACHINE-RESOLVED`.
The gate requirements deterministically computable from Task and Project Manifest
are labelled `Machine-readable gate requirements` rather than claiming a full
effective gate union while Workflow contribution remains unresolvable.

## Context Completion Rule Evaluation

Before transitioning from `planned` to `in_progress` and beginning source implementation,
the Context Completion Rule (`core/context-policy.md` §22) must be satisfied:

1. **What am I changing?**
   Adding `scripts/inspect_task.py` and `tests/test_inspect_task.py`.
   Registering AIO-010 in `schemas/tests/validate_task.py`.
   Maintaining the four canonical AIO-010 Task artifacts in `.ai/tasks/AIO-010-task-status-inspection/`.

2. **Why am I changing it?**
   To provide a repository-local, read-only Python utility that inspects and reports
   Task governance status using existing approved contracts, serving as the first
   governed vertical slice under `workflows/standard-change.md`.

3. **What must remain unchanged?**
   All foundation schemas (`task.schema.json`, `workflow.schema.json`, `role.schema.json`,
   `project-manifest.schema.json`), all frozen Core specifications (`principles.md`,
   `terminology.md`, `precedence.md`, `lifecycle.md`, `context-policy.md`, `human-control.md`,
   `project-manifest.md`, `task-specification.md`, `role-specification.md`, `workflow-specification.md`),
   canonical Role definitions, canonical Workflow definitions, and existing Tasks AIO-001 through AIO-009.

4. **What Rules apply?**
   AGENTS.md, `workflows/standard-change.md`, `core/precedence.md`, `core/context-policy.md`,
   `core/human-control.md`, `core/task-specification.md`, and the user's four corrections.

5. **What proves the Task is complete?**
   - Unit tests pass with comprehensive coverage.
   - All repository schema validators pass (`validate_task.py`, `validate_workflow.py`, `validate_role.py`, `validate_project_manifest.py`).
   - `git diff --check` passes with no whitespace errors.
   - `inspect_task.py` correctly reports status, artifacts, schemas, gates, human control, and workflow limitation.
   - Independent review is conducted by a separate reviewer with clean context and passes.
   - Quality Gates `documentation_consistency` and `independent_review` pass.
   - Human approval is obtained before final closure.
