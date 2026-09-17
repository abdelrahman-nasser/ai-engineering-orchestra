# AIO-012 — Context

## Authority and Scope

Direct dependency: AIO-011, closed at commit `0d5cdce`.
The Human authorized proceeding with AIO-012 — Machine-Readable Workflow Representation and Resolution.

AIO-012 addresses the machine-readable representation and resolution gap exposed after AIO-011:
while a Task records its governing Workflow ID in machine-readable form, Workflow definitions previously
lived only in Markdown files (`workflows/*.md`) requiring a test-only regex extractor.
AIO-012 migrates canonical Workflow instances to YAML, establishes a shared catalog loader, and
enhances inspection and validation tooling without implementing a Workflow execution runtime.

## Core Architectural Decisions

1. **Canonical Workflow Data Moves to YAML**:
   Canonical Workflow definitions reside as YAML documents in `workflows/*.yaml`.
   `core/workflow-specification.md` remains the authoritative semantic contract.
   `schemas/workflow.schema.json` remains the structural validation schema.
   `workflows/README.md` remains directory-level human documentation.

2. **Critical Correction 1 — Workflow ID Must NOT Imply Filename**:
   Resolution does NOT use `path = workflows_dir / f"{workflow_id}.yaml"`.
   Filenames and Workflow IDs are distinct.
   Resolution enumerates all `*.yaml` files in the Workflow directory, safe-loads each, validates
   each against `schemas/workflow.schema.json`, reads the declared `id`, rejects duplicate declared IDs,
   indexes the definitions by their declared `id`, and resolves requested Workflows from this catalog.

3. **Critical Correction 2 — Preserve Historical Link Compatibility**:
   Historical Markdown paths (`workflows/standard-change.md`, `workflows/architecture-change.md`,
   `workflows/security-sensitive-change.md`) are NOT deleted.
   They are retained as minimal non-authoritative compatibility stubs pointing to the authoritative
   YAML files. The stubs contain no duplicated stages, roles, gates, or checkpoints to avoid dual sources of truth.

4. **Retire Test-Only Markdown Extractor**:
   `schemas/tests/validate_workflow.py` is updated to load canonical YAML definitions directly,
   retiring `extract_workflow_from_markdown()` and avoiding accidental promotion of Markdown to a production serialization DSL.

5. **Effective Quality Gate Union Automation**:
   With machine-readable Workflow definitions resolved, `scripts/inspect_task.py` programmatically calculates
   the three-way Quality Gate union (`Project ∪ Workflow ∪ Task`) under Principle SAF-04.

## Governing Workflow and Role Fulfillment

Governing Workflow: `standard-change` (explicitly declared on `task.yaml`).

Ordered Workflow stages:

1. `understand`
2. `implement`
3. `validate`
4. `review`

Role fulfillment:

- Stage 1 — `understand`: Verified context acquisition and satisfaction of Context Completion Rule.
- Stage 2 — `implement`: Required Role: `software-engineer`. Fulfilled by primary implementation actor.
- Stage 3 — `validate`: Executed by primary implementation actor across all repository test suites.
- Stage 4 — `review`: Required Role: `reviewer`. Executed by a genuinely separate independent reviewer subagent.
- Human Control: Evaluated at Stage 4 review checkpoint. Final review and approval are required before task completion.

## Quality Gate Determination

- Project required gates: `documentation_consistency`, `independent_review` (from `.ai/project.yaml`)
- Workflow stage required gates: None (`standard-change` defines no workflow floor)
- Task quality gates: `documentation_consistency`, `independent_review` (from `task.yaml`)
- Effective union: `documentation_consistency`, `independent_review`

## Context Completion Rule Evaluation

Before active implementation, the Context Completion Rule (`core/context-policy.md` §22) is satisfied:

1. **What am I changing?**
   - Authoring `workflows/standard-change.yaml`, `workflows/architecture-change.yaml`, `workflows/security-sensitive-change.yaml`.
   - Replacing contents of `workflows/*.md` with non-authoritative compatibility stubs.
   - Updating `workflows/README.md` and `core/workflow-specification.md`.
   - Implementing `scripts/workflow_catalog.py` (catalog indexing, validation, resolution by declared ID).
   - Updating `schemas/tests/validate_workflow.py` to directly validate canonical YAML and retire the Markdown extractor.
   - Updating `schemas/tests/validate_task.py` to semantically validate declared Workflow references.
   - Enhancing `scripts/inspect_task.py` to report resolved Workflow status, stage counts, human checkpoints, and effective Quality Gate unions.
   - Adding comprehensive unit tests in `tests/test_workflow_catalog.py` and updating `tests/test_inspect_task.py`.
   - Maintaining the canonical four-file Task structure in `.ai/tasks/AIO-012-workflow-representation-resolution/`.

2. **Why am I changing it?**
   To resolve the machine-readable Workflow representation limitation in an evidence-backed manner without introducing runtime execution or fragile Markdown parsing.

3. **What must remain unchanged?**
   - Workflow semantics and structural schema (`schemas/workflow.schema.json`).
   - Project Manifest schema and Task schema.
   - Core policies (`precedence.md`, `context-policy.md`, `human-control.md`, `principles.md`).
   - Historical Tasks AIO-001 through AIO-011.

4. **What Rules apply?**
   `AGENTS.md`, `workflows/standard-change.md`, `core/precedence.md`, `core/principles.md`,
   and user instructions with Critical Corrections 1 and 2.

5. **What proves the Task is complete?**
   - All unit tests pass.
   - All schema validators pass.
   - Markdownlint and git whitespace checks pass.
   - Direct inspection of AIO-012, AIO-011, and AIO-010 produces expected outputs.
   - Independent review passes with zero unresolved findings.
