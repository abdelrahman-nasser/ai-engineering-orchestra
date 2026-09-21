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
- Agent Runtime Option specification: `core/agent-runtime-option-specification.md` — authoritative semantic contract for caller-supplied Agent Runtime Option identity and inventory validation; governs semantics if it conflicts with the Agent Runtime Option schema.
- Agent Runtime Option schema: `schemas/agent-runtime-option.schema.json` — machine-readable structural validation of the Agent Runtime Option Definition contract; semantically subordinate to `core/agent-runtime-option-specification.md`.
- Actor-to-Runtime Applicability specification: `core/actor-runtime-applicability-specification.md` — authoritative semantic contract for caller-supplied positive Actor-to-Runtime Applicability Evidence and relation validation; governs semantics if it conflicts with the Actor-to-Runtime Applicability schema.
- Actor-to-Runtime Applicability schema: `schemas/actor-runtime-applicability.schema.json` — machine-readable structural validation of one Actor-to-Runtime Applicability Evidence value; semantically subordinate to `core/actor-runtime-applicability-specification.md`.
- Agent Runtime Option Availability specification: `core/agent-runtime-option-availability-specification.md` — authoritative semantic contract for ephemeral Agent Runtime Option availability observations and snapshot validation; governs semantics if it conflicts with the Agent Runtime Option Availability schema.
- Agent Runtime Option Availability schema: `schemas/agent-runtime-option-availability.schema.json` — machine-readable structural validation of the Agent Runtime Option Availability Observation contract; semantically subordinate to `core/agent-runtime-option-availability-specification.md`.
- Inference Option specification: `core/inference-option-specification.md` — authoritative semantic contract for caller-supplied Inference Option identity and inventory validation; governs semantics if it conflicts with the Inference Option schema.
- Inference Option schema: `schemas/inference-option.schema.json` — machine-readable structural validation of the Inference Option Definition contract; semantically subordinate to `core/inference-option-specification.md`.
- Inference Option Availability specification: `core/inference-option-availability-specification.md` — authoritative semantic contract for ephemeral Inference Option availability observations and snapshot validation; governs semantics if it conflicts with the Inference Option Availability schema.
- Inference Option Availability schema: `schemas/inference-option-availability.schema.json` — machine-readable structural validation of the Inference Option Availability Observation contract; semantically subordinate to `core/inference-option-availability-specification.md`.
- Runtime-to-Inference Compatibility specification: `core/runtime-inference-compatibility-specification.md` — authoritative semantic contract for caller-supplied positive Runtime-to-Inference Compatibility Evidence and relation validation; governs semantics if it conflicts with the Runtime-to-Inference Compatibility schema.
- Runtime-to-Inference Compatibility schema: `schemas/runtime-inference-compatibility.schema.json` — machine-readable structural validation of one Runtime-to-Inference Compatibility Evidence value; semantically subordinate to `core/runtime-inference-compatibility-specification.md`.
- Runtime-to-Inference Pair Availability Assessment specification: `core/runtime-inference-pair-availability-specification.md` — authoritative semantic contract for pure deterministic per-edge availability composition; Pair Availability Assessment is derived in-memory evidence and has no serialized schema in AIO-032.
- Agent Execution Candidate Prerequisite Assessment specification: `core/agent-execution-candidate-prerequisite-specification.md` — authoritative semantic contract for pure deterministic composition of one explicit Assignment, Runtime Option, and Inference Option candidate; the assessment is derived in-memory evidence and has no serialized schema in AIO-034.
- Operation Requirement specification: `core/operation-requirement-specification.md` — authoritative semantic contract for an immutable caller-supplied abstract-operation requirement against one exact lexical repository-relative resource; governs semantics if it conflicts with the Operation Requirement schema.
- Operation Requirement schema: `schemas/operation-requirement.schema.json` — machine-readable structural validation of the Operation Requirement contract; semantically subordinate to `core/operation-requirement-specification.md`.
- Runtime Operation Capability Observation specification: `core/runtime-operation-capability-specification.md` — authoritative semantic contract for caller/environment-supplied tri-state technical-support observations over known Runtime Option and Core-operation pairs; governs semantics if it conflicts with the Runtime Operation Capability Observation schema.
- Runtime Operation Capability Observation schema: `schemas/runtime-operation-capability.schema.json` — machine-readable structural validation of one Runtime Operation Capability Observation; semantically subordinate to `core/runtime-operation-capability-specification.md`.
- Environment Operation Permission Observation specification: `core/environment-operation-permission-specification.md` — authoritative semantic contract for caller/environment-supplied Runtime-, environment-, operation-, and resource-scoped tri-state permission observations and deterministic snapshot validation; governs semantics if it conflicts with the Environment Operation Permission Observation schema.
- Environment Operation Permission Observation schema: `schemas/environment-operation-permission.schema.json` — machine-readable structural validation of one Environment Operation Permission Observation; semantically subordinate to `core/environment-operation-permission-specification.md`.
- Agent Execution Authorization Evidence specification: `core/agent-execution-authorization-evidence-specification.md` — authoritative semantic contract for caller-supplied Human/policy authorization assertions about one exact assigned external-inference Agent action; governs semantics if it conflicts with the Agent Execution Authorization Evidence schema.
- Agent Execution Authorization Evidence schema: `schemas/agent-execution-authorization-evidence.schema.json` — machine-readable structural validation of one Agent Execution Authorization Evidence value; semantically subordinate to `core/agent-execution-authorization-evidence-specification.md`.
- Agent Action Prerequisite Assessment specification: `core/agent-action-prerequisite-specification.md` — authoritative semantic contract for pure deterministic composition of one coherent candidate result, Operation Requirement, Runtime capability result, environment permission result, and execution authorization result for one exact assigned external-inference Agent action; the assessment is derived in-memory evidence and has no serialized schema in AIO-040.
- Actor Selection specification: `core/actor-selection-specification.md` — authoritative semantic contract for pure deterministic Actor candidate resolution; Actor Selection is derived in-memory evidence and has no serialized schema in AIO-025.
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
