# AI Engineering Orchestra

This repository uses AI Engineering Orchestra.

Current framework version: 0.1.0

---

## Start Here

When entering this repository for the first time or when the framework contract is unknown:

1. Read `.ai/project.yaml`.
2. Read `core/principles.md`.
3. Read `core/terminology.md`.
4. Read `core/precedence.md`.

This is repository bootstrap context and should not be repeatedly loaded for every routine Task when the Agent already understands the framework contract.

For normal Task execution:

1. Identify and read the current Task.
2. Read the Project Manifest if relevant configuration is not already known.
3. Load only the Project Rules relevant to the Task.
4. Load the applicable Workflow.
5. Load the assigned Role instructions.
6. Load relevant Stack Modules and architecture decisions only when needed.
7. Inspect relevant implementation files and tests.
8. Expand context only when necessary.
9. Complete all required Quality Gates before reporting completion.

---

## Sources of Truth

Use these locations as authoritative sources:

- Project configuration: `.ai/project.yaml`
- Core principles: `core/principles.md`
- Canonical terminology: `core/terminology.md`
- Precedence model: `core/precedence.md`
- Project lifecycle: `core/lifecycle.md`
- Context policy: `core/context-policy.md`
- Human control model: `core/human-control.md`
- Project Manifest specification: `core/project-manifest.md`
- Project Manifest template: `templates/project.yaml`
- Task specification: `core/task-specification.md`
- Task template: `templates/task/`
- Task schema: `schemas/task.schema.json`
- Role specification: `core/role-specification.md` — authoritative semantic contract for Roles; governs semantics if it conflicts with the Role schema.
- Role schema: `schemas/role.schema.json` — machine-readable structural validation of the Role contract; semantically subordinate to `core/role-specification.md`.
- Canonical Role instances: `roles/*.yaml` — framework-owned Role data; identity
  comes from each object's declared `id`.
- Role compatibility stubs: `roles/*.md` — non-authoritative historical-link and
  documentation paths; never runtime Role data.
- Actor specification: `core/actor-specification.md` — authoritative semantic contract for Actors and Actor-to-Role competency coverage; governs semantics if it conflicts with the Actor schema.
- Actor schema: `schemas/actor.schema.json` — machine-readable structural validation of the Actor contract; semantically subordinate to `core/actor-specification.md`.
- Actor Availability Observation specification: `core/actor-availability-specification.md` — authoritative semantic contract for ephemeral Actor availability observations and snapshot validation; governs semantics if it conflicts with the Actor Availability Observation schema.
- Actor Availability Observation schema: `schemas/actor-availability.schema.json` — machine-readable structural validation of the Actor Availability Observation contract; semantically subordinate to `core/actor-availability-specification.md`.
- Assignment specification: `core/assignment-specification.md` — authoritative semantic contract for immutable Actor responsibility bindings and Assignment validation; governs semantics if it conflicts with the Assignment schema.
- Assignment schema: `schemas/assignment.schema.json` — machine-readable structural validation of the Assignment contract; semantically subordinate to `core/assignment-specification.md`.
- Workflow specification: `core/workflow-specification.md` — authoritative semantic contract for Workflows; governs semantics if it conflicts with the Workflow schema.
- Workflow schema: `schemas/workflow.schema.json` — authoritative machine-readable structural validation of normalized Workflow objects; semantically subordinate to `core/workflow-specification.md`.
- Workflows: `workflows/` — canonical reusable Workflow definitions governed by `core/workflow-specification.md`.
- Quality Gates: `quality-gates/`
- Architecture decisions: `docs/adr/`
- Current Tasks: `.ai/tasks/`

---

## Core Rules

Agents must:

- understand the Task before changing files,
- respect Task scope,
- prefer minimum necessary change,
- avoid unrelated refactoring,
- use explicit Sources of Truth over assumptions,
- expand context only when necessary,
- report failed or skipped validation,
- respect Human approval requirements,
- avoid provider-specific assumptions in Orchestra Core.

---

## Review Rule

An Agent that implements a material change must not be the sole authority approving that change when the applicable Workflow requires independent review.

---

## Scope Rule

Discovering an unrelated issue does not authorize fixing it.

Unrelated findings should be reported separately unless the current Task explicitly includes them.

---

## Provider Independence

Claude, Codex, Antigravity, and future AI systems are Providers or execution environments.

They are not permanent architectural dependencies of Orchestra Core.

Provider-specific behavior belongs behind Provider Adapters.

---

## Current Development Stage

AI Engineering Orchestra is currently in v0.1.x Foundation.

The following are intentionally reserved for later versions:

- Brownfield deep analysis and safe refactoring automation — v0.2
- Command permission enforcement — v0.2
- Detailed Stack Modules — v0.3
- Full Provider Adapters — v0.4
- Model routing, quota handling, and escalation — v0.5
- CLI — v0.6
- Package distribution — v0.7

Do not implement future-version features unless the current Task explicitly changes the roadmap.

---

## Completion Rule

Before reporting a Task as complete, the Agent must be able to state:

1. what changed,
2. why it changed,
3. what validation was performed,
4. whether any required Quality Gate failed or was skipped,
5. whether Human approval is still required.
