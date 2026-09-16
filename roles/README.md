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
