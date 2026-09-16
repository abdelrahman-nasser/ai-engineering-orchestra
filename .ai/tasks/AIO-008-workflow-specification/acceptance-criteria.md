# AIO-008 — Acceptance Criteria

AIO-008 may be closed only after all applicable criteria are verified and the required Human approval is recorded.

## Workflow Contract

- [x] A canonical Workflow specification exists at `core/workflow-specification.md`.
- [x] The top-level Workflow contract contains only `id`, `name`, `purpose`, optional `applicable_task_types`, and `stages`.
- [x] No `applies_when`, condition expressions, branching, loops, or expression languages exist in the Workflow contract.
- [x] `applicable_task_types` is advisory/descriptive only and does not automatically select or authorize a Workflow.
- [x] An AIO Workflow is defined as declarative governance choreography and SHALL NOT constitute an executable workflow graph.
- [x] A Workflow SHALL NOT identify, instantiate, configure, or select an Agent or Human actor.
- [x] A Workflow SHALL NOT identify or configure a Provider or model.
- [x] A Workflow SHALL NOT grant tools or runtime permissions.
- [x] A Workflow SHALL NOT implement runtime scheduling, routing, retries, state, checkpoints, or messaging.

## Stage Contract & Governance Invariants

- [x] The Stage contract contains only `id`, `purpose`, optional `required_roles`, optional `required_quality_gates`, and optional `human_control_checkpoint`.
- [x] Stages are simple ordered stages executed sequentially; no graph nodes, arbitrary edges, or branching.
- [x] Workflow stages may reference canonical Role IDs directly without assigning an actor.
- [x] Workflow stages may reference canonical Quality Gate IDs without defining gate logic.
- [x] `human_control_checkpoint: true` identifies WHEN Human Control is evaluated, not WHAT authority exists.
- [x] A Human-control checkpoint SHALL NOT independently grant, require, or define approval authority. Progression pauses only if applicable Human Control rules require approval; otherwise it does not block.
- [x] Quality Gate composition across Project configuration, Workflow requirements, and Task requirements is explicitly documented.
- [x] Non-weakening Quality Gate invariant (SAF-04) is enforced: lower-level configuration SHALL NOT silently weaken a mandatory Quality Gate established by an applicable higher-authority contract. Effective gates = Project gates ∪ Workflow stage gates ∪ Task gates.
- [x] Workflow and Task `execution.mode` are orthogonal in v0.1 without mode matrices or automatic mappings.
- [x] Workflow selection is explicitly documented as separate from Workflow definition.

## External-Runtime Delegation Boundary

- [x] The specification explicitly defines what AIO owns (governance stages, Role requirements, Quality Gate requirements, Human Control checkpoint locations).
- [x] The specification explicitly delegates execution runtime concerns (actor execution, graph execution, Agent lifecycle, state, routing, messaging, retries, tool execution, provider/model selection, actual pause/resume mechanics) to an external/future runtime.
- [x] Without an execution runtime, an AIO Workflow remains non-executable by itself.

## Initial Workflow Library

- [x] Reusable Workflow definitions exist in `workflows/` as Markdown documents.
- [x] `standard-change` is defined with 4 ordered stages (understand, implement, validate, review).
- [x] Generic `standard-change` gate floor is re-evaluated and minimally opinionated (`documentation_consistency` and `independent_review` omitted from generic stage floor; required reviewer Role and human control checkpoint retained).
- [x] `architecture-change` is defined with 5 ordered stages, engaging the `architect` Role in design and review stages, with required quality gates.
- [x] `security-sensitive-change` is defined with 5 ordered stages, engaging the `security-reviewer` Role in analysis and review stages, with required quality gates.
- [x] `documentation-change` is excluded as a separate workflow because it does not require a distinct governance stage structure.
- [x] Explicit documentation states that Markdown is the current canonical documentation representation, not the runtime/persistence serialization format.

## Maintenance, Quality, and Closure

- [x] `AGENTS.md` registers `core/workflow-specification.md` and `workflows/` as Sources of Truth.
- [x] No Workflow schema entry is added to `AGENTS.md` in AIO-008.
- [x] `schemas/tests/validate_task.py` registers `.ai/tasks/AIO-008-workflow-specification/task.yaml` in `CANONICAL_TASKS`.
- [x] `core/terminology.md` updates Workflow and Stage definitions to reference `core/workflow-specification.md`.
- [x] Existing validators (`validate_project_manifest.py`, `validate_task.py`, `validate_role.py`) pass without error.
- [x] `git diff --check` passes with no whitespace errors.
- [x] `documentation_consistency` Quality Gate passes.
- [x] `independent_review` Quality Gate passes.
- [x] Final Human approval is obtained before Task closure (approved by Human on 2026-09-17).
