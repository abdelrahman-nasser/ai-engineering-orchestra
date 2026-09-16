# AIO-006 - Context

## Objective

AIO-006 defines the first canonical Role contract for AI Engineering Orchestra.

A Role must remain smaller than a runtime Agent, permission model, Workflow, or Human approval mechanism. It describes what engineering responsibility and abstract competency is required, not which actor performs the work or how the work is executed.

## Architectural Boundaries

The authoritative Role contract is defined in:

- `core/role-specification.md`

The Role contract deliberately does not change:

- `core/task-specification.md`
- `schemas/task.schema.json`
- Task-to-Role assignment behavior
- Agent runtime behavior
- Provider adapters
- Workflows
- Human Control
- Quality Gate definitions

Tasks continue to own work, scope, objectives, dependencies, acceptance criteria, and results. Workflows continue to own sequencing. Policies and Human Control continue to own authority, permissions, protected actions, and approval. Quality Gates continue to own pass/fail conditions.

## Capability Semantics

Role `required_capabilities` use stable abstract engineering competencies such as:

- `software-implementation`
- `source-code-analysis`
- `architecture-analysis`
- `requirements-analysis`
- `automated-testing`
- `security-analysis`
- `documentation-analysis`
- `evidence-evaluation`

Runtime tools, commands, provider features, and permissions are not Role capabilities.

## Future Relationship

A future Assignment Contract may connect multiple Task responsibility requirements to Roles and select Human or Agent actors. A future Execution Contract may define runtime context, tools, permissions, execution behavior, and evidence handling. AIO-006 intentionally does not choose or implement those structures.

AIO-005 is completed and remains untouched.

## Closure

AIO-006 is completed following explicit Human approval on 2026-09-16.
All acceptance criteria are checked. Review, validation, and approval evidence
is recorded in `review.md`. AIO-007 has not been created.
