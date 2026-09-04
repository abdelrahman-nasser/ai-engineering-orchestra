# AI Engineering Orchestra — Task Specification

Version: 0.1.0

This document defines the canonical Task contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

A Task is the canonical unit of scoped work managed through AI Engineering Orchestra.

A Task defines:

- what work is intended
- what work is in scope
- what work is explicitly out of scope
- Task-specific Risk and Complexity
- Execution Mode
- required Quality Gates
- Human control requirements
- dependencies
- acceptance criteria
- review and closure evidence

Tasks must remain auditable before, during, and after execution.

---

## 2. Default Task Location

The canonical default Project Task directory is:

`.ai/tasks/`

A Project may configure a different Task directory through:

`tasks.directory`

in the Project Manifest (`.ai/project.yaml`).

Each Task must have its own directory.

Recommended directory format:

```text
<TASK-ID>-<short-description>
```

Example:

```text
AIO-004-task-specification
```

A Task directory name is a repository organization convention.

The canonical Task identity remains the `id` declared in `task.yaml`.

---

## 3. Canonical Task Directory Layout

A standard v0.1 Task directory contains:

```text
<TASK-DIRECTORY>/
├── task.yaml
├── context.md
├── acceptance-criteria.md
└── review.md
```

All four files are required for a standard Orchestra-managed Task.

Additional Task-specific files may be included when necessary, but they must not redefine the responsibilities of these canonical files.

---

## 4. Canonical File Responsibilities

### `task.yaml`

`task.yaml` is the structured Source of Truth for Task identity, classification, scope, execution requirements, Quality Gates, Human control requirements, and Task status.

It should contain information that future tooling may need to parse deterministically.

### `context.md`

`context.md` contains explanatory background needed to understand the Task.

It may describe:

- motivation
- existing behavior
- architectural context
- constraints
- relevant history
- known limitations
- future compatibility considerations

`context.md` must not silently override structured requirements defined in `task.yaml`.

### `acceptance-criteria.md`

`acceptance-criteria.md` defines the observable conditions required for Task completion.

It is the canonical checklist used to determine whether the Task deliverables satisfy the agreed requirements.

### `review.md`

`review.md` records:

- review scope
- Quality Gate results
- independent-review findings
- final recommendation
- Human approval where required
- closure evidence

It must reflect the actual review state and must not claim approval that has not occurred.

---

## 5. Source of Truth Boundaries

Task files own Task-specific intent and execution requirements.

They do not own canonical definitions belonging to:

- the Project Manifest
- Orchestra Core Principles
- Policies
- Project Rules
- Workflows
- Roles
- Quality Gate definitions
- architecture decisions
- Stack Modules
- Provider Adapters

Task files may reference those Sources of Truth without duplicating their canonical content.

When Task files conflict with higher-precedence requirements, `core/precedence.md` applies.

---

## 6. Canonical `task.yaml` Fields

The v0.1 Task contract defines these top-level fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | Yes | Stable Task identifier |
| `title` | Yes | Human-readable Task title |
| `type` | Yes | Broad Task classification |
| `status` | Yes | Current Task lifecycle state |
| `version_target` | No | Intended Project or Orchestra version target |
| `complexity` | No | Task Complexity |
| `risk` | No | Task Risk |
| `execution` | No | Task execution configuration, including `execution.mode` |
| `objective` | Yes | Primary Task outcome |
| `scope` | Yes | Included and excluded work |
| `dependencies` | No | Tasks that must be satisfied first |
| `quality_gates` | No | Task-specific Quality Gate requirements |
| `human_control` | No | Task-specific Human approval requirements |

Unknown top-level fields are unsupported in the v0.1 Task contract unless a future specification explicitly introduces them.

---

## 7. `id`

`id` is the stable machine-readable identity of the Task.

Example:

```yaml
id: AIO-004
```

Requirements:

- required
- non-empty string
- unique within the Project
- should remain stable after Task creation

The Task directory name may include the Task ID, but directory naming does not replace `task.yaml` identity.

---

## 8. `title`

`title` is the human-readable Task name.

Example:

```yaml
title: Define Task Specification
```

Requirements:

- required
- non-empty string
- should describe the intended outcome rather than implementation detail alone

---

## 9. `type`

`type` describes the broad classification of the Task.

Example values may include:

- `foundation`
- `specification`
- `implementation`
- `maintenance`
- `refactoring`
- `migration`
- `review`
- `documentation`
- `investigation`

Requirements:

- required
- non-empty string

The value is intentionally extensible in v0.1.

Task behavior must not be inferred solely from `type`.

Policies, Workflows, Risk, Complexity, and explicit Task requirements remain authoritative.

---

## 10. `status`

`status` represents the current Task lifecycle state.

Allowed v0.1 values:

- `planned`
- `in_progress`
- `blocked`
- `completed`
- `cancelled`

### `planned`

The Task exists but active implementation has not started.

### `in_progress`

Work on the Task is actively underway.

### `blocked`

Work cannot currently continue because a required dependency, decision, permission, resource, or external condition is unresolved.

A blocked Task should record the blocking reason in Task context or review evidence.

### `completed`

The Task has satisfied all applicable closure requirements.

A Task must not be marked `completed` merely because implementation work appears finished.

### `cancelled`

The Task will not be completed in its current form.

Cancellation should remain auditable, including the reason where material.

---

## 11. Status Transitions

Typical Task progression is:

```text
planned
  ↓
in_progress
  ↓
completed
```

A Task may transition to:

```text
blocked
```

and later return to:

```text
in_progress
```

A Task may transition to:

```text
cancelled
```

when execution is intentionally abandoned.

A completed or cancelled Task should not silently return to active execution.

Material reopening should be explicit and auditable.

---

## 12. `version_target`

`version_target` identifies the Project or Orchestra version the Task intends to contribute toward.

Example:

```yaml
version_target: "0.1.0"
```

This field is optional because not every Project uses semantic versioning.

When present:

- it must be a non-empty string
- its interpretation belongs to the Project's versioning model
- it must not be treated as the Task contract version

---

## 13. `complexity`

`complexity` describes the amount of reasoning, coordination, decomposition, or engineering depth expected for the Task.

Allowed values:

- `low`
- `medium`
- `high`
- `critical`

Example:

```yaml
complexity: high
```

This field is optional.

If omitted, the Task inherits the Project default from:

```text
complexity.default
```

in the Project Manifest (`.ai/project.yaml`).

Complexity remains independent from Risk.

---

## 14. `risk`

`risk` describes the potential impact of incorrect execution.

Allowed values:

- `low`
- `medium`
- `high`
- `critical`

Example:

```yaml
risk: medium
```

This field is optional.

If omitted, the Task inherits the Project default from:

```text
risk.default
```

in the Project Manifest (`.ai/project.yaml`).

Risk remains independent from Complexity.

A low-Complexity Task may still be high Risk.

---

## 15. `execution`

`execution` defines Task-specific execution configuration.

Example:

```yaml
execution:
  mode: standard
```

### `execution.mode`

Allowed values:

- `lite`
- `standard`
- `deep`
- `critical`

If `execution` or `execution.mode` is omitted, the Task inherits:

```text
execution.default_mode
```

from the Project Manifest (`.ai/project.yaml`).

A lower Task Execution Mode must not weaken:

- protected Policies
- required Quality Gates
- Human approval requirements
- other higher-precedence requirements

---

## 16. `objective`

`objective` defines the primary outcome the Task is intended to achieve.

Example:

```yaml
objective: >
  Define the canonical Task contract for AI Engineering Orchestra.
```

Requirements:

- required
- non-empty string
- outcome-oriented
- sufficiently specific to evaluate against acceptance criteria

The objective should describe what success means rather than prescribing unnecessary implementation detail.

---

## 17. `scope`

`scope` defines explicit Task boundaries.

Example:

```yaml
scope:
  include:
    - Task lifecycle
    - Task configuration
    - closure requirements

  exclude:
    - Task JSON Schema implementation
    - CLI task creation
```

### `scope.include`

Required.

It identifies work that belongs to the Task.

The list must contain at least one meaningful scope item.

### `scope.exclude`

Optional but strongly recommended when meaningful exclusions exist.

It identifies work that must not be introduced as part of the Task.

Explicit exclusions protect against accidental scope expansion.

An excluded feature must not be implemented merely because it may be useful later.

---

## 18. Scope Authority

Task scope is a boundary.

Agents must not silently expand scope.

When necessary work falls outside the declared scope, the Agent should:

1. identify the scope conflict
2. determine whether the additional work is required for correctness
3. request or obtain appropriate approval when required
4. update the Task scope when an authorized change is made
5. keep the change auditable

Scope changes remain subject to `core/precedence.md` and Human control requirements.

---

## 19. `dependencies`

`dependencies` identifies other Tasks whose outcomes are required before this Task can safely complete.

Example:

```yaml
dependencies:
  - AIO-002
  - AIO-003
```

This field is optional.

If a Task has no dependencies, either of the following is valid:

- omit the `dependencies` field
- use an empty list: `dependencies: []`

Requirements when present:

- must be a list
- every dependency entry must be a non-empty Task identifier
- duplicate dependency identifiers should not be used
- a Task must not depend on itself

An empty dependency list is valid and indicates that the Task has no dependencies.

A dependency does not automatically mean implementation must wait entirely.

However, a Task must not be marked completed when an unresolved dependency materially prevents its acceptance criteria from being satisfied.

Circular Task dependencies are invalid.

---

## 20. `quality_gates`

`quality_gates` defines Task-specific Quality Gate requirements.

Example:

```yaml
quality_gates:
  - documentation_consistency
  - independent_review
```

This field is optional.

Each value must correspond to a canonical Quality Gate identifier.

Task-specific Quality Gates are additive.

A Task cannot remove a Quality Gate required by:

- a higher-precedence Policy
- the Project Manifest
- an applicable Workflow
- another protected requirement

Duplicate Gate identifiers should not be used.

Quality Gate behavior and pass conditions remain defined in `quality-gates/`.

---

## 21. `human_control`

`human_control` defines Task-specific Human approval requirements.

Example:

```yaml
human_control:
  final_review_required: true
  breaking_contract_changes_require_approval: true
```

Supported v0.1 fields are:

- `final_review_required`
- `architecture_changes_require_approval`
- `breaking_schema_changes_require_approval`
- `breaking_contract_changes_require_approval`

Values must be boolean.

### Task-Level Human Control Semantics

A `true` value adds the corresponding Human approval requirement to the Task.

A `false` value removes only a requirement introduced by the Task itself.

It does not override a requirement imposed by:

- protected Policies
- higher-precedence Policies
- the Project Manifest
- applicable Workflows
- other authoritative requirements

Task-level Human control cannot grant permission to perform an otherwise protected action.

Detailed approval behavior remains defined in `core/human-control.md`.

---

## 22. Project Default Inheritance

Task configuration inherits Project defaults when Task-specific configuration is omitted and the Project Manifest defines a corresponding default.

Canonical v0.1 inheritance includes:

| Task Configuration | Project Manifest Default |
| --- | --- |
| `complexity` | `complexity.default` |
| `risk` | `risk.default` |
| `execution.mode` | `execution.default_mode` |

Quality Gates and Human control requirements are cumulative rather than simple replacement values.

Task configuration may become stricter than Project defaults.

It must not weaken protected or higher-precedence requirements.

---

## 23. Precedence

Task configuration operates within:

`core/precedence.md`

Task-specific Policies and Rules may have higher precedence than Project-level Rules where the precedence model permits.

However, Task configuration cannot weaken:

- protected security or safety Policies
- Orchestra Core Principles
- protected Core Policies
- applicable higher-precedence Policies

Explicit Human instructions remain subject to the same protected boundaries.

---

## 24. `context.md`

`context.md` exists to provide enough background for an Agent or Human to understand the Task without requiring unnecessary repository-wide context loading.

Useful content may include:

- why the Task exists
- relevant current behavior
- architectural constraints
- historical decisions
- related systems
- known limitations
- compatibility expectations

It should not duplicate large amounts of canonical documentation.

Context loading must follow `core/context-policy.md`.

---

## 25. `acceptance-criteria.md`

Acceptance criteria define observable Task completion requirements.

Canonical checklist syntax is:

```markdown
- [ ] Requirement not yet verified.
- [x] Requirement verified.
```

A criterion must not be marked `[x]` merely because implementation exists.

It should be marked complete only when supporting evidence is sufficient.

Acceptance criteria should cover:

- required deliverables
- architectural constraints
- compatibility requirements
- relevant Quality Gates
- required Human approval

Acceptance criteria must remain synchronized with material Task scope changes.

---

## 26. Acceptance Criteria and Evidence

Checking an acceptance criterion records that the criterion has been verified.

It does not replace:

- tests
- Quality Gate evidence
- independent review
- required Human approval

When a criterion cannot be satisfied, the Task must not be marked completed unless an applicable Policy explicitly permits an exception and the required Human approval is recorded.

---

## 27. `review.md`

`review.md` is the Task's persistent review and approval record.

Before review, it may contain:

```text
Status: Pending
```

During and after review it should record relevant information such as:

- review type
- review scope
- findings
- Quality Gate outcomes
- independent-review recommendation
- accepted non-blocking observations
- Human approval
- final closure state

Review evidence must reflect reality.

A review document must not state `Approved` while required material findings remain unresolved.

---

## 28. Independent Review

When `independent_review` is required, behavior must follow:

`quality-gates/independent-review.md`

The sole reviewer must not be the same Agent execution instance that implemented the material change.

A different Provider is not mandatory unless another applicable requirement says otherwise.

An independent review does not replace required Human approval.

---

## 29. Human Approval

When final Human approval is required, the Task must remain active until that approval is explicitly obtained.

Approval should be recorded in `review.md`.

The applicable acceptance criterion should be checked only after approval has actually occurred.

Human approval does not retroactively convert a failed Quality Gate into a pass unless the Quality Gate definition explicitly permits an approved waiver.

---

## 30. Task Closure

A Task may be marked `completed` only when all applicable closure requirements are satisfied.

At minimum:

1. required deliverables exist
2. applicable acceptance criteria are satisfied
3. required validation has passed
4. required Quality Gates have passed or have an explicitly permitted approved disposition
5. required independent review is complete
6. required Human approval has been obtained
7. material review findings are resolved or explicitly accepted where permitted
8. Task documentation reflects the final state

Only then should:

```yaml
status: completed
```

be recorded.

Implementation completion alone is not Task completion.

---

## 31. Cancellation

A cancelled Task does not need to satisfy normal completion criteria.

However, cancellation should record:

- that the Task was cancelled
- why it was cancelled when material
- any partial work that remains
- whether follow-up work is required

Cancellation must not be used to disguise a failed Task as successful.

---

## 32. Blocked Tasks

A blocked Task remains incomplete.

The blocking condition should be recorded clearly enough that another Agent or Human can understand what prevents progress.

When the blocker is resolved, the Task may return to `in_progress`.

A blocked status does not waive Quality Gates, acceptance criteria, or approval requirements.

---

## 33. Completed Task Auditability

Completed Tasks must remain available as historical evidence unless an applicable repository retention policy says otherwise.

A completed Task should make it possible to determine:

- what was requested
- what scope applied
- what acceptance criteria were used
- what Quality Gates were required
- what review occurred
- what Human approval occurred
- whether the Task completed successfully

Task history must not be silently rewritten to conceal failed reviews or material scope changes.

---

## 34. Unsupported Task Configuration

For the v0.1 Task contract:

- unknown top-level `task.yaml` fields are unsupported
- Agents must not invent semantics for unknown fields
- unsupported configuration should be reported during review
- future tooling may reject unsupported configuration

Future Task contract versions may introduce additional fields through explicit specification changes.

---

## 35. Provider Independence

The Task contract must not require a specific Provider or model.

A Task should remain valid whether work is executed by:

- Claude
- Codex
- Antigravity
- another compatible Provider
- a Human

Provider selection and model routing belong to later Orchestra capabilities.

---

## 36. Stack Independence

The Task contract does not require a specific:

- programming language
- application framework
- database
- infrastructure platform
- deployment system

Stack-specific behavior belongs to applicable Stack Modules and Project Rules.

---

## 37. Repository Independence

Task semantics must not depend on a specific source-control provider or hosting platform.

A Task may exist in repositories hosted through systems such as GitHub, GitLab, Azure DevOps, or another compatible source-control environment without changing the Core Task contract.

---

## 38. Forward Compatibility

Future Orchestra versions may introduce:

- Task JSON Schema validation
- CLI Task creation
- automated decomposition
- automated Agent assignment
- routing metadata
- Stack Module references
- Provider Adapter references
- Brownfield-specific Task metadata

AIO-004 does not implement these capabilities.

Future additions must not silently change the meaning of existing v0.1 fields.

---

## 39. Canonical Ownership

The Task specification defines the Task contract.

It does not define:

- Project Manifest semantics
- Quality Gate pass conditions
- Workflow behavior
- Role behavior
- Provider behavior
- Stack Module behavior
- command-permission enforcement
- orchestration-engine behavior

Those remain in their respective Sources of Truth.

---

## 40. Canonical Conformance Rule

A v0.1 Task conforms to this specification when:

1. all four canonical Task files exist
2. `task.yaml` contains all required fields
3. structured values use allowed types and enumerations
4. Task scope is explicit
5. unsupported Task configuration is absent
6. acceptance criteria represent the Task requirements accurately
7. Task-specific Quality Gates and Human control requirements do not weaken higher-precedence requirements
8. context remains explanatory rather than conflicting with structured Task requirements
9. review evidence accurately reflects the current Task state
10. Task lifecycle status matches the actual lifecycle state
