# AIO-005 — Context

## Objective

AIO-004 established the canonical v0.1 Task contract in:

`core/task-specification.md`

AIO-005 must add machine-readable structural validation for that contract.

## Existing Pattern

AIO-003 established the validation pattern for the Project Manifest through:

- `schemas/project-manifest.schema.json`
- `schemas/tests/requirements.txt`
- `schemas/tests/validate_project_manifest.py`
- valid fixtures
- invalid fixtures

AIO-005 should follow the same repository-local validation philosophy where appropriate without creating CLI behavior.

## Required Contract Source

The authoritative semantic contract remains:

`core/task-specification.md`

The JSON Schema must validate structural conformance to that specification.

The schema must not replace the specification as the semantic Source of Truth.

## Canonical Task Structure

A standard v0.1 Task directory contains:

- `task.yaml`
- `context.md`
- `acceptance-criteria.md`
- `review.md`

AIO-005 primarily validates the structured `task.yaml` contract.

Validation of Markdown semantics or actual approval truth must not be falsely represented as fully enforceable through JSON Schema alone.

## Existing Tasks

The following current Orchestra Tasks should conform to the schema:

- AIO-001
- AIO-002
- AIO-003
- AIO-004
- AIO-005

The reusable Task template must also conform:

`templates/task/task.yaml`

## Architecture Constraints

The schema and test tooling must remain:

- Provider-agnostic
- model-agnostic
- programming-language-agnostic
- framework-agnostic
- repository-hosting-agnostic

The implementation must not introduce:

- routing
- orchestration
- Provider behavior
- Stack Module behavior
- CLI semantics
- command-permission behavior

## Validation Boundaries

The schema may validate structural properties such as:

- required fields
- enumerations
- scalar and collection types
- minimum lengths
- object shape
- unknown top-level fields
- nested supported fields
- dependency item shape
- duplicate dependency identifiers where JSON Schema can express it

The schema must not pretend to validate semantic facts that require repository state or historical evidence, including:

- Task ID uniqueness across the Project
- dependency existence
- circular dependency detection
- whether acceptance criteria are actually satisfied
- whether Human approval really occurred
- whether independent review was actually independent
- whether a Task should legitimately be completed

Those concerns remain governed by specification, review, and later tooling.

## Deliverables

AIO-005 should produce:

- one canonical Task JSON Schema
- valid Task fixtures
- invalid Task fixtures
- repository-local Task schema validation tooling
- validation of the canonical Task template
- validation of existing Orchestra Tasks

CLI behavior remains reserved for later work.

## Verification and Closure

Project Manifest validation passed 12/12 cases and Task Schema validation passed
16/16 cases. The in-memory mismatch test demonstrated exit code 1, followed by
normal validation passing with exit code 0. Evidence is recorded in `review.md`.

The first independent review returned CHANGES REQUIRED. Remediation was completed,
and follow-up independent review passed with final recommendation
READY FOR HUMAN APPROVAL. Documentation consistency passed.

The Human subsequently explicitly approved AIO-005: "I approve AIO-005."
All acceptance criteria and configured review and approval requirements are
satisfied. AIO-005 is completed.
