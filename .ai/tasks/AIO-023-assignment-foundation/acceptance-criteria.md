# AIO-023 Acceptance Criteria

- [x] The canonical Assignment contract contains exactly `task_id`,
  `workflow_id`, `stage_id`, `role_id`, and `actor_id`, with no Assignment ID,
  lifecycle, Provider, availability, authority, or execution fields.
- [x] The responsibility key is `(task_id, workflow_id, stage_id, role_id)`, and
  the immutable selected `actor_id` is excluded from identity.
- [x] Draft 2020-12 structural validation requires five nonempty strings and
  rejects additional properties through focused registered fixtures.
- [x] Pure individual validation resolves Task, Workflow, Stage, Role, and Actor
  context in deterministic dependency order and reuses Actor competency coverage.
- [x] Duplicate Actor IDs invalidate supplied context, while corrupt framework
  catalogs remain infrastructure errors rather than ordinary Assignment findings.
- [x] Sequence validation rejects all duplicate bindings and lets only valid,
  unique responsibility keys cover requirements.
- [x] Validity and completeness remain distinct; unassigned requirements are
  deterministic, stages without Roles add nothing, and duplicate Role references
  collapse to one current responsibility slot.
- [x] Valid unique implementer and Reviewer bindings with the same Actor produce
  separate identity-conflict evidence without changing validity, completeness,
  Workflow state, or Quality Gate state.
- [x] No extra separation rule, automatic Actor selection, persistence,
  availability, authority, execution, Stage state, CLI, or AIO-024 is introduced.
- [x] The Assignment schema and runtime module are package-safe, compose with the
  Role catalog and Actor coverage outside the checkout, and need no Assignment file.
- [x] Full required validation passes or every failure and skip is recorded.
- [x] Separate reviewer and final architect reviews approve the actual change and
  the `documentation_consistency` and `independent_review` Gates pass.
- [x] Explicit Human approval is recorded before Task closure or commit.
