# AIO-008 — Context

## Objective

AIO-008 defines the first canonical Workflow contract for AI Engineering Orchestra.

A Workflow defines a reusable, ordered sequence of governance stages for a class of engineering work. It establishes the process choreography required to complete work safely and systematically.

A Workflow describes WHEN governance checkpoints occur, what Roles are required, and what Quality Gates must be satisfied. It does not execute work, instantiate actors, select providers, route messages, or manage runtime state.

## Architectural Boundaries

The authoritative Workflow specification is defined in:

- `core/workflow-specification.md`

The initial canonical reusable Workflow definitions are maintained in:

- `workflows/`

The Workflow specification cleanly separates:

- **Workflow**: ordered governance stages, Role references, Quality Gate references, and Human Control checkpoint locations.
- **Task**: scoped work, objectives, acceptance criteria, Risk, Complexity, Execution Mode, and lifecycle status (`core/task-specification.md`).
- **Role**: responsibility and competency contracts (`core/role-specification.md`). Workflow stages reference Role IDs; they do not define Roles or assign actors.
- **Quality Gate**: validation checkpoints and pass/fail conditions (`quality-gates/`). Workflow stages reference Quality Gate IDs; they do not define gate logic.
- **Human Control**: authority levels, approver identity, protected actions, and approval semantics (`core/human-control.md`). Workflow defines WHEN a checkpoint occurs; Human Control defines WHAT approval is required.
- **Assignment Contract**: future mechanism for selecting eligible Human or Agent actors for required Roles.
- **Execution Contract**: future mechanism for supplying runtime context, tools, and permissions to assigned actors.
- **External Execution Runtime**: runtime graph execution, agent lifecycle, messaging, retries, state, and actual pause/resume mechanics.

## Invariants and Transition Model

In v0.1, Workflows use simple ordered stages only.

Progression through a Workflow requires completing prior required stages and satisfying their requirements:

1. Required Roles engaged (capability contract available),
2. Required Quality Gates passed,
3. Human Control checkpoints evaluated.

The v0.1 Workflow contract strictly excludes:

- condition expressions (including `applies_when`),
- branching,
- loops,
- runtime predicates,
- event-driven transitions,
- conditional edges,
- expression languages,
- graph execution engines,
- retries, backoff, or fault recovery,
- durable state or checkpoint persistence,
- agent messaging or conversation routing.

## Quality Gate Composition Semantics

Quality Gates compose additively across three Sources of Truth:

1. **Project configuration**: Project-wide gates defined in `.ai/project.yaml` via `quality.require_<gate_id>: true`.
2. **Workflow requirements**: Stage-specific gates defined in the governing Workflow via stage `required_quality_gates`.
3. **Task-specific requirements**: Task-specific gates declared in `task.yaml` via `quality_gates`.

The non-weakening invariant (SAF-04 / `core/precedence.md`) strictly applies:

> A lower-level configuration SHALL NOT silently weaken a mandatory Quality Gate requirement established by an applicable higher-authority contract.

The effective Quality Gate set for any stage is the union of all applicable Project gates, Workflow stage gates, and Task gates. No lower level may remove or waive a gate required by a higher level unless permitted by an explicit Human approval policy.

## Human Control Checkpoint Semantics

A Workflow stage declares a Human Control checkpoint via:

```yaml
human_control_checkpoint: true
```

A checkpoint identifies a process location where applicable Human Control requirements are evaluated.

**Normative invariant**: A Human-control checkpoint SHALL NOT independently grant, require, or define approval authority. At a checkpoint, applicable Human Control rules (from Core Principles, Human Control Model, Project Manifest, and Task configuration) are evaluated:

- If applicable rules require Human approval, progression pauses until valid approval is obtained.
- If applicable rules require no Human approval (e.g. routine low-risk work), the checkpoint does not independently block progression.

Workflow owns WHEN Human Control is evaluated; `core/human-control.md` owns whether approval is required, who may approve, approval scope, and protected actions.

## Re-evaluation of Generic `standard-change` Gate Floor

Quality Gates declared on a Workflow stage establish a mandatory minimum floor that no Task using that Workflow can remove.

In defining the generic reusable `standard-change` Workflow, we distinguish the strict governance used to develop the AI Engineering Orchestra repository itself (which mandates `documentation_consistency` and `independent_review` project-wide via `.ai/project.yaml`) from universal minimum requirements for ordinary software changes across any project:

- **`documentation_consistency`**: Omitted from generic `standard-change`. Many routine code changes (e.g. internal bug fixes, performance improvements) do not touch documentation or specification contracts. Mandating this gate universally in `standard-change` would force unnecessary ceremony onto every adopting project. Projects that need documentation consistency (such as this framework) mandate it via their Project Manifest.
- **`independent_review`**: Omitted from generic `standard-change` stage-level gates. Instead, `standard-change` specifies `required_roles: [reviewer]` and `human_control_checkpoint: true` at its review stage. This guarantees that an independent reviewer responsibility is structurally present in the governance choreography, while allowing Project Policy (e.g. `quality.require_independent_review: true`) or Task configuration to mandate the formal gate ID.
- **Specialized Workflows**: By contrast, `architecture-change` and `security-sensitive-change` justifiably mandate explicit Quality Gates (`documentation_consistency`, `independent_review`) directly in their stage contracts due to their structural impact and high inherent risk.

## Representation & Validation Boundaries

Markdown is the canonical documentation representation of Workflow definitions in v0.1. AIO-008 does not establish Markdown as the runtime, persistence, API, or future machine-readable Workflow serialization format.

Workflow JSON/YAML schema validation is intentionally deferred to a subsequent specification-to-schema task (AIO-009). Task schema (`schemas/task.schema.json`) remains unchanged.
