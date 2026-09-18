# AI Engineering Orchestra — Workflow Specification

Version: 0.1.0

> Authoritative semantic contract for Workflows in AI Engineering Orchestra.
> This specification governs Workflow semantics. If a future Workflow schema is introduced, this specification takes precedence.

---

## 1. Purpose

A **Workflow** is a reusable, provider-independent specification of the ordered governance stages required to complete a class of engineering work.

A Workflow defines the process choreography — establishing WHEN governance checkpoints occur, what Roles are required at each stage, and what Quality Gates must be satisfied. It does not execute work, instantiate actors, select providers, route messages, or manage runtime state.

The canonical Workflow directory is:

`workflows/`

The initial reusable Workflow definitions are maintained in that directory.

---

## 2. Architectural Boundary

AI Engineering Orchestra enforces a strict separation of concerns across framework contracts:

| Concern | Authoritative Source | Boundary |
| --- | --- | --- |
| **Workflow** | `core/workflow-specification.md`, `workflows/` | Ordered governance stages, Role references, Quality Gate references, and Human Control checkpoint locations. |
| **Task** | `core/task-specification.md`, `.ai/tasks/` | Scoped engineering work item, objective, acceptance criteria, Risk, Complexity, Execution Mode, and lifecycle status. |
| **Role** | `core/role-specification.md`, `roles/` | Declarative responsibility and abstract engineering competency contracts. |
| **Quality Gate** | `quality-gates/` | Named validation checkpoints with specific pass/fail criteria. |
| **Human Control** | `core/human-control.md` | Authority levels, approver identity, approval authority, protected actions, and escalation paths. |
| **Precedence** | `core/precedence.md` | Conflict resolution and non-weakening rules across authority layers. |
| **Assignment Contract** | `core/assignment-specification.md` | Immutable binding and validation of a caller-selected eligible Actor for one required Role responsibility. |
| **Execution Contract** | *Future specification* | Provision of runtime context, tools, and permissions to assigned actors. |
| **External Runtime** | *External execution layer* | Actor execution, graph execution, Agent lifecycle, state, routing, messaging, retries, and pause/resume mechanics. |

A Workflow specifies the governance choreography. It does not own Task work, Role capabilities, Quality Gate verification logic, Human approval authority, or runtime execution.

---

## 3. Canonical Workflow Contract

The v0.1 Workflow contract contains these top-level fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | Yes | Stable machine-readable Workflow identifier. |
| `name` | Yes | Human-readable Workflow display name. |
| `purpose` | Yes | Concise statement of the Workflow's governance intent. |
| `applicable_task_types` | No | Advisory Task categories for which the Workflow is commonly suitable. |
| `stages` | Yes | Ordered sequence of governance stages. |

### `id`

`id` is the stable machine-readable identity of the Workflow.

Requirements:

- MUST be unique across all Workflows in the project.
- MUST be stable — changing an ID is a breaking change.

Canonical AIO Workflow definitions use kebab-case identifiers by convention (e.g., `standard-change`, `architecture-change`). This convention is not a normative identifier grammar in v0.1.

Example:

```yaml
id: standard-change
```

### `name`

`name` is the human-readable display name of the Workflow.

Requirements:

- MUST be a non-empty string.
- Descriptive and recognizable.

Example:

```yaml
name: Standard Change
```

### `purpose`

`purpose` briefly explains the class of engineering work governed by the Workflow.

Requirements:

- MUST be a concise statement of why this Workflow exists.
- MUST describe a governance objective rather than runtime instructions.

Example:

```yaml
purpose: Govern standard engineering work through disciplined understanding, implementation, validation, and review.
```

### `applicable_task_types`

`applicable_task_types` lists Task categories for which the Workflow is commonly suitable.

Requirements:

- Optional list of string identifiers matching valid Task types (e.g., `implementation`, `architecture`).
- **Advisory only**: It SHALL NOT automatically select, trigger, assign, or authorize a Workflow.
- It does not restrict a Workflow from being used with other Task types when authorized by project configuration or Human direction.

Example:

```yaml
applicable_task_types:
  - implementation
  - bugfix
  - refactoring
```

### `stages`

`stages` defines the ordered sequence of governance stages that constitute the Workflow choreography.

Requirements:

- MUST be a non-empty list of Stage objects conforming to the Stage Contract.
- Order is significant and defines the sequential progression of governance stages.

---

## 4. Canonical Stage Contract

A **Stage** represents a single governance checkpoint within a Workflow.

The v0.1 Stage contract contains these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | Yes | Stable machine-readable stage identifier. |
| `purpose` | Yes | Concise statement of the stage's governance intent. |
| `required_roles` | No | Canonical Role IDs whose competencies and responsibilities are required for this stage. |
| `required_quality_gates` | No | Canonical Quality Gate IDs that must pass before this stage completes. |
| `human_control_checkpoint` | No | Boolean indicating a process location where Human Control is evaluated. |

### `id`

`id` is the stable machine-readable identifier of the stage within the Workflow.

Requirements:

- MUST be unique within the Workflow's `stages` list.
- MUST be stable within the containing Workflow.

Canonical AIO Workflow definitions use kebab-case stage identifiers by convention (e.g., `understand`, `implement`, `validate`, `review`). This convention is not a normative identifier grammar in v0.1.

### `purpose`

`purpose` describes the specific governance objective of the stage.

Requirements:

- MUST be a non-empty concise statement of what this stage achieves.

### `required_roles`

`required_roles` lists the canonical Role IDs required by this stage.

Requirements:

- Optional list of stable Role IDs defined in `roles/`.
- **References only**: This is NOT actor assignment. It indicates that the governance stage requires the capability and responsibility contract represented by the referenced Role(s).
- Concrete responsibility binding belongs to the Assignment Contract. Automatic
  Actor selection remains outside both Workflow and Assignment.

Example:

```yaml
required_roles:
  - reviewer
```

### `required_quality_gates`

`required_quality_gates` lists the canonical Quality Gate IDs that must be satisfied before the stage may complete.

Requirements:

- Optional list of stable Quality Gate IDs defined in `quality-gates/`.
- **References only**: The Workflow does not define gate logic or evaluation methods; it declares that the named gate is a mandatory completion condition for this stage.

Example:

```yaml
required_quality_gates:
  - independent_review
```

### `human_control_checkpoint`

`human_control_checkpoint` declares whether this stage represents a process location where Human Control rules are evaluated.

Semantics:

- `human_control_checkpoint` is optional.
- If omitted, the Stage does not declare a Human Control checkpoint.
- If `true`, the Stage declares a process location at which applicable Human Control rules are evaluated.
- The checkpoint itself does not create approval authority: progression pauses if and only if applicable Human Control rules require approval; if they require no approval, the checkpoint does not independently block progression.
- See Section 9 for detailed semantics and boundaries.

Example:

```yaml
human_control_checkpoint: true
```

---

## 5. Normative Workflow Invariants

The following normative rules govern all Workflows in AI Engineering Orchestra:

1. **Declarative Choreography**: An AIO Workflow is declarative and SHALL NOT itself constitute an executable workflow graph.
2. **Class of Work**: A Workflow defines reusable governance/process stages for a class of engineering work.
3. **No Actor Coupling**: A Workflow SHALL NOT identify, instantiate, configure, or select an Agent or Human actor.
4. **No Provider Coupling**: A Workflow SHALL NOT identify or configure an AI Provider or model.
5. **No Tool or Permission Grants**: A Workflow SHALL NOT grant tools, capabilities, or runtime permissions.
6. **No Runtime Engine Semantics**: A Workflow SHALL NOT implement runtime scheduling, message routing, retries, state persistence, checkpoints, or conversation management.
7. **Role References Only**: A Workflow may reference canonical Role IDs without assigning an actor.
8. **Quality Gate References Only**: A Workflow may reference canonical Quality Gate IDs without defining gate logic.
9. **Human Control Checkpoint Boundary**: A Workflow Human-control checkpoint identifies WHEN Human control is evaluated, not WHAT authority exists. A Human-control checkpoint SHALL NOT independently grant, require, or define approval authority. At a checkpoint, applicable Human Control rules are evaluated. If those rules require approval, progression pauses until valid approval is obtained; if they require no approval, the checkpoint does not independently block progression.
10. **Selection Decoupled from Definition**: Workflow selection is separate from Workflow definition.
11. **Advisory Task Types**: `applicable_task_types`, if present, is advisory only and SHALL NOT automatically select or authorize a Workflow.
12. **External Runtime Responsibility**: Workflow execution remains the responsibility of a future execution/runtime integration layer.

---

## 6. Stage Progression and Transition Model

In AI Engineering Orchestra v0.1, Workflows use **simple ordered stages only**.

### Sequential Progression

Progression through a Workflow is strictly sequential:

```text
Stage 1 ──> Stage 2 ──> Stage 3 ──> ... ──> Stage N
```

A stage cannot be entered until the preceding stage has completed successfully. A stage is complete when:

1. The stage's purpose has been fulfilled,
2. All `required_roles` for the stage have been engaged by qualified actors,
3. All `required_quality_gates` for the stage have been evaluated and passed,
4. Any `human_control_checkpoint` at the stage has been evaluated against applicable Human Control policies and any required approval has been granted.

### Explicit Exclusion of Complex Transition Logic

The v0.1 Workflow contract strictly excludes:

- conditional expressions (including `applies_when`),
- runtime branching or conditional paths,
- loops or cyclic transitions,
- runtime predicates or boolean expressions,
- event-driven transitions,
- arbitrary graph edges or directed acyclic graph (DAG) routing,
- expression languages or template interpreters,
- fan-out/fan-in parallel execution,
- retries, backoff, or failure recovery paths,
- durable state or checkpoint persistence,
- agent messaging or conversation routing.

If a stage fails its requirements, progression stops. Recovery, replanning, or escalation is managed through Human Control and Task lifecycle states (`blocked`), not by Workflow transition machinery.

---

## 7. Workflow to Role Relationship

Workflow stages reference canonical Role IDs via `required_roles`.

### Semantic Meaning

Referencing a Role ID in a stage means:

> "This governance stage requires the capability and responsibility contract represented by the referenced Role."

It does NOT mean:

- "Assign this specific Human or Agent,"
- "Instantiate an Agent with this name,"
- "Send a prompt to this persona."

### Role Resolution Model

The relationship between Workflows, Roles, and execution flows through distinct architectural contracts:

```text
Workflow Stage
  └─ declares: required_roles: [reviewer]
        │
        ▼
Framework Role Catalog
  └─ resolves: reviewer -> required competencies
        │
        ▼
Actor-Role Competency Coverage
  └─ compares: supplied Actor -> eligibility evidence
        │
        ▼
Assignment Contract
  └─ validates and binds an externally selected eligible Human or Agent actor
        │
        ▼
Future Execution Contract
  └─ provides: runtime context, tools, and permissions to the selected actor
```

Workflows reference Roles directly. AI Engineering Orchestra does not introduce an intermediate "responsibility requirement" taxonomy between Workflow and Role.

Portable validation resolves `required_roles` against the framework-owned Role
catalog. An unresolved Role ID is semantic cross-resource failure, not a
Workflow schema rule. If the packaged Role catalog itself is unavailable or
corrupt, validation reports infrastructure error without per-reference cascades.
Role resolution and competency coverage alone do not create an Assignment. An
Assignment additionally records the caller-selected Actor against one concrete
Task/Workflow/Stage/Role responsibility key.

### Composition Rules

- A stage MAY require multiple Roles (e.g., `[reviewer, architect]`). All required Role contracts must be fulfilled for the stage to complete.
- A single actor MAY fulfill multiple Roles only when permitted by the applicable Human Control model, Project Rules, and separation-of-duties constraints (e.g., an actor implementing changes cannot serve as the independent reviewer for the same work).

---

## 8. Quality Gate Composition Semantics

Quality Gates are referenced by stable identifier from `quality-gates/`.

The effective Quality Gate requirements for any given engineering activity are composed additively across three authoritative sources:

```text
┌─────────────────────────────────────────────────────────┐
│ 1. Project Manifest (.ai/project.yaml)                  │
│    quality.require_<gate_id>: true                      │
│    (Establishes the project-wide minimum gate floor)     │
└───────────────────────────┬─────────────────────────────┘
                            │  +
┌───────────────────────────▼─────────────────────────────┐
│ 2. Governing Workflow (workflows/<workflow>.yaml)       │
│    stage.required_quality_gates: [<gate_id>]            │
│    (Establishes process-stage minimum gate floor)       │
└───────────────────────────┬─────────────────────────────┘
                            │  +
┌───────────────────────────▼─────────────────────────────┐
│ 3. Current Task (.ai/tasks/<task-id>/task.yaml)         │
│    quality_gates: [<gate_id>]                           │
│    (Adds task-specific gate requirements)               │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
           Effective Quality Gate Set (Union)
```

### Composition Invariant: Non-Weakening (SAF-04)

In accordance with Core Principle SAF-04 and `core/precedence.md`:

> A lower-level configuration SHALL NOT silently weaken a mandatory Quality Gate requirement established by an applicable higher-authority contract.

1. **Project Configuration**: Gates required by the Project Manifest (`quality.require_*`) apply to all Tasks and all Workflows in the project. Neither a Workflow nor a Task can remove a Project-mandated gate.
2. **Workflow Requirements**: Gates required by a Workflow stage form a mandatory process floor for that stage. A Task executing under that Workflow inherits those stage gates and CANNOT remove or bypass them.
3. **Task Requirements**: A Task may add additional Quality Gates specific to its own risk or scope. It cannot weaken Workflow or Project gates.
4. **Effective Gate Set**: The effective Quality Gates for a stage are the **union** of applicable Project gates, Workflow stage gates, and Task gates.
5. **Exceptions**: A mandatory Quality Gate may be waived only when the applicable Policy explicitly permits an exception and the required Human approval is documented (per `core/human-control.md`).

Quality Gate definitions, pass/fail conditions, and verification criteria remain owned exclusively by `quality-gates/`.

---

## 9. Human Control Boundary

A Workflow stage indicates a Human Control evaluation point using:

```yaml
human_control_checkpoint: true
```

### Boundary of Responsibility

The division of responsibility between Workflow and Human Control is strict:

```text
Workflow owns:       WHEN execution evaluates Human Control.
Human Control owns:  WHAT approval is required,
                     WHO may approve,
                     WHAT authority that approval carries.
```

### Non-Blocking Evaluation Semantics

`human_control_checkpoint: true` does NOT itself create a new approval requirement or grant authority.

Normative semantic rule:

> A Human-control checkpoint SHALL NOT independently grant, require, or define approval authority. At a checkpoint, applicable Human Control rules are evaluated. If those rules require approval, progression pauses until valid approval is obtained; if they require no approval, the checkpoint does not independently block progression.

Specifically:

- **Evaluation**: When a Workflow stage declares `human_control_checkpoint: true`, the runtime inspects applicable Human Control rules (from `core/principles.md`, `core/human-control.md`, `.ai/project.yaml`, and the Task's `human_control` configuration).
- **Pausing**: If any applicable rule requires Human approval (e.g., architecture change, security-sensitive change, breaking contract change, or Task-level `final_review_required: true`), execution pauses at this checkpoint until explicit Human approval is recorded.
- **Continuing**: If no applicable rule requires Human approval for the current work, the checkpoint is satisfied immediately and does not independently block progression.
- **Workflow Does Not Prescribe Authority**: A Workflow stage SHALL NOT define approver identities, approval levels, escalation paths, or protected action categories. Those remain owned by `core/human-control.md`.

---

## 10. Execution Mode Relationship

Execution Mode (`core/task-specification.md`) and Workflow are **orthogonal** concepts in AI Engineering Orchestra v0.1:

- **Workflow**: Defines the sequence of governance stages, required Roles, and Quality Gates for a *class of engineering work* (e.g., standard change, architecture change).
- **Execution Mode**: Defines the *depth of engineering process and agent autonomy* applied to an individual Task (`lite`, `standard`, `deep`, `critical`).

In v0.1:

- Workflows do not define mode-specific stage counts.
- Workflows are not selected by Execution Mode.
- No mode-to-Workflow mapping matrix exists.
- Execution Mode does not alter the ordered stages of a Workflow.

The interaction between Execution Mode and Workflow stages (such as adjusting review depth or resource allocation) remains deferred to future runtime and routing specifications.

---

## 11. Workflow Selection Boundary

Workflow definition is strictly decoupled from Workflow selection:

- **Definition** (`workflows/`): Reusable specifications of governance stages.
- **Selection**: The decision of which Workflow applies to a specific Task.

In v0.1:

- A Task may explicitly declare its governing Workflow via `workflow: <workflow-id>` in `task.yaml`.
- The Project Manifest may configure a default Workflow via `workflows.default` in `.ai/project.yaml`.
- `applicable_task_types` on a Workflow is advisory only and does NOT automatically select or bind a Workflow.
- No automatic Workflow selection engine, rule-based selector, or dynamic routing exists in v0.1.

---

## 12. External-Runtime Boundary

AI Engineering Orchestra governance choreography is strictly separated from executable workflow orchestration:

```text
┌────────────────────────────────────────────────────────┐
│ AI Engineering Orchestra (AIO Governance Choreography) │
│                                                        │
│ - Required governance stages                           │
│ - Sequential stage order                               │
│ - Role capability requirements                         │
│ - Quality Gate requirements                            │
│ - Human Control checkpoint locations                   │
└───────────────────────────┬────────────────────────────┘
                            │ delegates to
                            ▼
┌────────────────────────────────────────────────────────┐
│ External / Future Execution Runtime                    │
│                                                        │
│ - Agent instantiation and execution                    │
│ - Graph execution and transition mechanics             │
│ - Agent lifecycle management                           │
│ - Runtime state and checkpoint persistence             │
│ - Message routing and agent conversations              │
│ - Retries, backoff, and error recovery                 │
│ - Tool execution and permission enforcement            │
│ - Provider and model routing                           │
│ - Actual HITL pause/resume mechanics                   │
└────────────────────────────────────────────────────────┘
```

**Normative Rule**: Without an external execution runtime, an AIO Workflow remains declarative documentation and is non-executable by itself.

---

## 13. Ownership and Precedence

Workflows operate within the authority hierarchy defined by `core/precedence.md`:

1. Human Override
2. Core Principles (`core/principles.md`)
3. Core Specifications (`core/*.md`)
4. Schemas (`schemas/`)
5. Project Manifest (`.ai/project.yaml`)
6. **Workflow Requirements** (`workflows/`) — *Level 6*
7. Task Configuration (`.ai/tasks/`)
8. Role Defaults (`roles/`)
9. Provider Defaults

Workflow rules cannot weaken requirements established by Core Principles, Core Specifications, Schemas, or the Project Manifest. Task-specific configuration cannot weaken requirements established by an applicable Workflow.

---

## 14. Initial Workflow Library

The initial canonical Workflow library defines three reusable Workflows:

1. **`standard-change`**: Baseline governance workflow for routine engineering work.
2. **`architecture-change`**: Specialized governance workflow for work involving architectural decisions or specification changes.
3. **`security-sensitive-change`**: Specialized governance workflow for work with security impact.

### Rationale for Three Workflows

These three Workflows are justified because they genuinely differ in governance stage structure, required Roles, and Quality Gate floors:

| Workflow | Stages | Specialized Roles | Mandatory Quality Gates |
| --- | --- | --- | --- |
| `standard-change` | 4 (understand, implement, validate, review) | `software-engineer`, `reviewer` | (None at workflow floor; delegated to project/task) |
| `architecture-change` | 5 (understand, design, implement, validate, review) | `architect`, `software-engineer`, `reviewer` | `documentation_consistency`, `independent_review` |
| `security-sensitive-change` | 5 (understand, security-analysis, implement, validate, review) | `security-reviewer`, `software-engineer`, `reviewer` | `independent_review` |

A separate `documentation-change` Workflow is intentionally excluded because documentation work follows the 4-stage structure of `standard-change` at lower risk/complexity, without requiring a distinct governance stage structure.

---

## 15. Representation and Validation Status in v0.1

### Canonical YAML Representation

Canonical Workflow instance definitions in `workflows/` are serialized as YAML documents (`workflows/*.yaml`).

- YAML is the authoritative machine-readable serialization format for Workflow instance definitions in AI Engineering Orchestra.
- Markdown is no longer the canonical per-Workflow data representation. Historical Markdown paths (`workflows/*.md`) are preserved solely as minimal non-authoritative compatibility stubs for historical links and task review records; they contain no workflow contract data and must not be parsed by tooling.
- Canonical Workflow representation is declarative process choreography data and SHALL NOT imply runtime execution, scheduling, or actor dispatch.

### Structural Schema Validation

`schemas/workflow.schema.json` provides machine-readable structural validation of parsed Workflow objects using JSON Schema Draft 2020-12.

- This specification (`core/workflow-specification.md`) remains the authoritative semantic Workflow contract.
- The schema is semantically subordinate to this specification.
- Schema validity establishes structural conformance only; it does not prove semantic correctness, meaningful governance, approval truth, or correct execution.
- Parsed YAML definitions are validated directly against `schemas/workflow.schema.json` without intermediate text extraction or custom Markdown parsing.
- Canonical Workflow-ID and per-Workflow Stage-ID uniqueness checks are separately labelled repository semantic validation, not JSON Schema validation.
