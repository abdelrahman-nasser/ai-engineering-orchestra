# Roles

This directory contains canonical framework-owned Role definitions used by AI
Engineering Orchestra.

The canonical Role contract is defined in:

`core/role-specification.md`

A Role is a reusable, provider-independent, declarative description of an engineering responsibility and its required abstract competencies. A Role is not directly executable and does not grant authority, permissions, approval authority, or actor eligibility.

## Authority Hierarchy

Role authority is ordered as follows:

1. `core/role-specification.md` — semantic authority
2. `schemas/role.schema.json` — structural authority
3. `roles/*.yaml` — canonical Role instances
4. `roles/*.md` — non-authoritative compatibility/documentation stubs
5. `schemas/tests/validate_role.py` — regression tooling only

Projects may reference these framework Role IDs. Project-defined Roles,
extensions, overrides, directories, and precedence rules are not supported.

## Initial v0.1 Roles

- [Architect](architect.yaml) (`architect`)
- [Documentation Specialist](documentation-specialist.yaml)
  (`documentation-specialist`)
- [Reviewer](reviewer.yaml) (`reviewer`)
- [Security Reviewer](security-reviewer.yaml) (`security-reviewer`)
- [Software Engineer](software-engineer.yaml) (`software-engineer`)

Role definitions use the canonical fields:

- `id`
- `name`
- `purpose`
- `responsibilities`
- `required_capabilities`
- optional `applicable_task_types`

Capability identifiers describe stable engineering competencies. They do not describe runtime tools, commands, provider features, or permissions.

Concrete responsibility bindings are defined by
`core/assignment-specification.md`. Actor selection, execution behavior,
Workflow sequencing, authority, approval, and broader separation-of-duties
policy remain outside the Role contract.

## Role Schema Validation

A machine-readable structural schema for normalized Role objects is available in:

`schemas/role.schema.json`

Repository-local validation reads the canonical YAML definitions directly through
`schemas/tests/validate_role.py`. Runtime code uses the packaged YAML resources
through `engineering_orchestration.role_catalog`; it does not inspect the active
project or parse Markdown.

Schema-valid does not imply semantically valid, useful, recommended, or
review-approved. The retained Markdown files are minimal historical-link stubs
and contain no duplicate Role contract data.
