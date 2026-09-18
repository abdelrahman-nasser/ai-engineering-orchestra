# Workflows

This directory contains canonical Workflow definitions used by AI Engineering Orchestra.

The authoritative semantic Workflow contract is defined in:

`core/workflow-specification.md`

A Workflow is a reusable, provider-independent, declarative description of the ordered governance stages required to complete a class of engineering work. A Workflow defines WHEN governance checkpoints occur, what Roles are required, and what Quality Gates must be satisfied.

A Workflow is not directly executable and does not select actors, grant permissions, route messages, or manage runtime state.

## Initial v0.1 Workflows

- [Standard Change](standard-change.yaml) (`standard-change`) — Baseline 4-stage governance workflow for routine engineering work.
- [Architecture Change](architecture-change.yaml) (`architecture-change`) — 5-stage governance workflow for architectural decisions, structural framework evolution, or specification design.
- [Security-Sensitive Change](security-sensitive-change.yaml) (`security-sensitive-change`) — 5-stage governance workflow for work with security impact, access controls, or protected resources.

## Directory Structure and Authority Hierarchy

AI Engineering Orchestra enforces a strict hierarchy for Workflow definitions:

1. **Authoritative Canonical Definitions** (`workflows/*.yaml`):
   The canonical Source of Truth for Workflow instance definitions. All tooling, resolution, and validation must load from these YAML files.
2. **Historical-Link Compatibility Stubs** (`workflows/*.md`):
   Minimal non-authoritative stubs retained solely to preserve link targets in completed historical Task review records and documentation. These stubs contain no workflow contract data or stage definitions, must not be parsed by tooling, and must not be treated as Workflow definitions.
3. **Directory Catalog Documentation** (`workflows/README.md`):
   Human-facing directory overview, index, and usage documentation.

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

- **Role References**: Stages reference framework-owned canonical Role IDs from
  `roles/*.yaml`. Portable validation resolves those IDs through the packaged
  Role catalog. Resolution does not select or assign an Actor. The separate
  Assignment Contract records and validates a caller-selected Actor binding;
  automatic Actor selection remains outside the current framework.
- **Quality Gates**: Stages reference Quality Gate IDs from `quality-gates/`. Effective gates are the union of Project required gates, Workflow stage gates, and Task gates (non-weakening principle).
- **Human Control**: `human_control_checkpoint: true` identifies WHEN Human Control is evaluated. It does not independently require approval; execution pauses only if applicable Human Control rules require approval.
- **External Runtime**: Workflow execution, state, retries, and actor orchestration belong to an external runtime integration layer.

## Representation and Validation Status

Canonical Workflow definitions are serialized in YAML (`workflows/*.yaml`).

`schemas/workflow.schema.json` provides machine-readable structural validation of parsed Workflow objects using JSON Schema Draft 2020-12. The schema is semantically subordinate to `core/workflow-specification.md`; schema validity does not prove semantic or governance correctness.

Run `python -B schemas/tests/validate_workflow.py` from the repository root after installing `schemas/tests/requirements.txt`. This validator checks the Draft 2020-12 schema, registered structural fixtures, and canonical YAML workflow definitions. It separately validates repository semantic ID-uniqueness across definitions.
