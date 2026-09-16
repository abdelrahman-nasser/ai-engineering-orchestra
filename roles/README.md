# Roles

This directory contains canonical Role definitions used by AI Engineering Orchestra.

The canonical Role contract is defined in:

`core/role-specification.md`

A Role is a reusable, provider-independent, declarative description of an engineering responsibility and its required abstract competencies. A Role is not directly executable and does not grant authority, permissions, approval authority, or actor eligibility.

## Initial v0.1 Roles

- [Architect](architect.md)
- [Software Engineer](software-engineer.md)
- [Reviewer](reviewer.md)
- [Security Reviewer](security-reviewer.md)
- [Documentation Specialist](documentation-specialist.md)

Role definitions use the canonical fields:

- `id`
- `name`
- `purpose`
- `responsibilities`
- `required_capabilities`
- optional `applicable_task_types`

Capability identifiers describe stable engineering competencies. They do not describe runtime tools, commands, provider features, or permissions.

Task assignment, actor selection, execution behavior, Workflow sequencing, authority, approval, and separation of duties remain owned by other Orchestra contracts and policies.

## Role Schema Validation

A machine-readable structural schema for normalized Role objects is available in:

`schemas/role.schema.json`

Repository-local validation tests validate normalized in-memory projections of the Markdown definitions in this directory via `schemas/tests/validate_role.py`.

Schema-valid does not imply semantically valid, useful, recommended, or review-approved. The existing canonical Role definitions remain Markdown; Markdown is not established as the runtime Role serialization format.
