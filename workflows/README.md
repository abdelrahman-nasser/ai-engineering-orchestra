# Workflows

This directory contains canonical Workflow definitions used by AI Engineering Orchestra.

The authoritative semantic Workflow contract is defined in:

`core/workflow-specification.md`

A Workflow is a reusable, provider-independent, declarative description of the ordered governance stages required to complete a class of engineering work. A Workflow defines WHEN governance checkpoints occur, what Roles are required, and what Quality Gates must be satisfied.

A Workflow is not directly executable and does not select actors, grant permissions, route messages, or manage runtime state.

## Initial v0.1 Workflows

- [Standard Change](standard-change.md) (`standard-change`) — Baseline 4-stage governance workflow for routine engineering work.
- [Architecture Change](architecture-change.md) (`architecture-change`) — 5-stage governance workflow for architectural decisions, structural framework evolution, or specification design.
- [Security-Sensitive Change](security-sensitive-change.md) (`security-sensitive-change`) — 5-stage governance workflow for work with security impact, access controls, or protected resources.

## Canonical Contract Structure

Workflow definitions use the canonical fields:

- `id`: Stable machine-readable Workflow identifier
- `name`: Human-readable display name
- `purpose`: Concise statement of governance intent
- optional `applicable_task_types`: Advisory Task categories
- `stages`: Ordered list of governance stages

Each Stage defines:

- `id`: Stable machine-readable stage identifier
- `purpose`: Concise statement of stage governance objective
- optional `required_roles`: Canonical Role IDs required for the stage (references only)
- optional `required_quality_gates`: Canonical Quality Gate IDs required for the stage (references only)
- optional `human_control_checkpoint`: Optional boolean indicating a process location where Human Control is evaluated (if omitted, the Stage does not declare a checkpoint)

Canonical AIO Workflow definitions use kebab-case identifiers by convention. This convention is not a normative identifier grammar in v0.1.

## Governance and Runtime Boundaries

- **Role References**: Stages reference canonical Role IDs from `roles/` to specify required responsibilities/capabilities. Actor selection is deferred to a future Assignment Contract.
- **Quality Gates**: Stages reference Quality Gate IDs from `quality-gates/`. Effective gates are the union of Project required gates, Workflow stage gates, and Task gates (non-weakening principle).
- **Human Control**: `human_control_checkpoint: true` identifies WHEN Human Control is evaluated. It does not independently require approval; execution pauses only if applicable Human Control rules require approval.
- **External Runtime**: Workflow execution, state, retries, and actor orchestration belong to an external runtime integration layer.

## Markdown Representation Notice

> Markdown is the current canonical documentation representation of Workflow definitions. AIO-008 does not establish Markdown as the runtime, persistence, API, or future machine-readable Workflow serialization format.

AIO-009 provides `schemas/workflow.schema.json` for normalized Workflow objects. The schema is semantically subordinate to `core/workflow-specification.md`; schema validity does not prove semantic or governance correctness.

Run `python -B schemas/tests/validate_workflow.py` from the repository root after installing `schemas/tests/requirements.txt`. This repository-local test tool validates the schema, registered fixtures, and strict in-memory projections of the three canonical Markdown definitions. The extractor preserves Stage order and omission, adds no defaults, and is not a public parser or runtime serializer.

The validator separately reports repository semantic ID-uniqueness checks across inspected definitions. Role and Quality Gate references remain open strings in the schema; their canonical existence was manually verified in the AIO-009 review record. Fixtures named `valid-structurally-*` demonstrate structural permissiveness, not recommended Workflow design.

AIO-009 does not add machine-readable Task-to-Workflow or Project-default Workflow selection. The current Task and Project Manifest schemas do not accept `workflow` and `workflows.default`, respectively. Explicit Human/orchestrator selection remains available for the first vertical slice; automatic resolution is not provided.
