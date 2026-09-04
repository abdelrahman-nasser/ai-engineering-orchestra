# AIO-004 — Context

## Objective

AI Engineering Orchestra already uses Task directories to govern its own development.

AIO-004 must turn that self-hosted convention into a canonical, reusable Task specification.

The specification must define how a unit of Orchestra-managed work is represented, constrained, reviewed, and closed.

## Existing Task Structure

Current Orchestra Tasks use a directory such as:

`.ai/tasks/AIO-004-task-specification/`

with files including:

- `task.yaml`
- `context.md`
- `acceptance-criteria.md`
- `review.md`

These files are working examples, but AIO-004 must formally define their responsibilities and boundaries.

## Why This Matters

Tasks are the operational unit through which Orchestra applies:

- scope
- Risk
- Complexity
- Execution Mode
- context loading
- Quality Gates
- Human approval
- independent review
- auditability

Future orchestration, CLI tooling, routing, and automation will depend on a stable Task contract.

## Architectural Constraints

The Task contract must remain:

- Provider-agnostic
- model-agnostic
- programming-language-agnostic
- framework-agnostic
- repository-friendly
- human-readable
- auditable
- compatible with progressive context loading

Task configuration must not silently weaken Project Policies, protected Core Policies, or Human control requirements.

## Source of Truth Boundaries

The Task must own Task-specific intent and execution requirements.

It must not duplicate canonical content owned by:

- the Project Manifest
- Core Policies
- Project Rules
- Workflow definitions
- Role definitions
- Quality Gate definitions
- architecture decisions

## Future Compatibility

The Task specification should leave clean extension points for future:

- Task schema validation
- CLI task creation
- automatic decomposition
- agent assignment
- routing
- Provider Adapters
- Stack Modules
- Brownfield workflows

Those capabilities must not be implemented by AIO-004.

## Deliverable

AIO-004 should produce:

- one canonical Task specification
- one canonical reusable Task example

Machine-readable Task schema validation will be handled by a later Task.
