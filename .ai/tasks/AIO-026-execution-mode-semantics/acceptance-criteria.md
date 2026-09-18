# AIO-026 Acceptance Criteria

- [x] Complexity is defined as descriptive inherent reasoning difficulty,
  engineering depth, coordination, and decomposition demand, without automatic
  mode, Workflow, model, authority, or approval mapping.
- [x] Risk remains the potential impact if execution is wrong and may drive
  stronger safeguards only through explicit Policies, without automatic mode or
  model mapping.
- [x] Execution Mode is defined as a Provider-neutral, Task-wide minimum
  engineering-execution posture rather than an exact ceiling or classification.
- [x] The canonical order is exactly `lite < standard < deep < critical`, with
  reflexive, monotonic minimum-satisfaction semantics and invalid-value
  rejection.
- [x] All four modes define cumulative minimum floors for process depth, bounded
  self-direction, analysis and decomposition, and evidence discipline; lighter
  modes never prohibit additional rigor.
- [x] All Human and Agent responsibilities inherit the effective Task mode;
  Stage, Role, and responsibility overrides and inference are unsupported.
- [x] Workflow remains orthogonal governance choreography: mode does not select
  it or change its stages, order, Roles, gates, or Human-control checkpoints.
- [x] Execution Mode grants no authority or permission, changes no Human approval
  requirement, and establishes no Quality Gate result.
- [x] Explicit Task Complexity, Risk, and mode independently override their
  matching Project defaults without automatic cross-field mapping.
- [x] Model Tier is deprecated; `fast`, `standard`, and `high` are withdrawn and
  non-consumable, with no active schema, runtime, routing, or replacement enum.
- [x] A minimal immutable order tuple and pure satisfaction helper implement only
  the normative mode relation and expose no Provider/model/reasoning inputs.
- [x] Executable schema, API-shape, and inspection tests cover the complete mode
  relation and all 15 semantic boundaries: independent Complexity, Risk, and
  Workflow values; no Stage/Role override; unchanged Workflow binding, stages,
  gates, and Human controls; no authority, competency, Availability, Selection,
  or Assignment effect; and no Model Tier schema/runtime/routing surface.
- [x] The unsupported-mode Task fixture is registered, AIO-026 is registered for
  canonical validation, and the packaged-module allowlist/import probe includes
  the new helper.
- [x] No existing schema, Workflow YAML, Role YAML, Actor, Availability,
  Selection, Assignment, permission, routing, or invocation contract changes.
- [x] All required focused, regression, schema, repository, installation,
  Markdown, and diff checks pass, or each failure and skip is recorded.
- [x] A genuinely separate Reviewer and non-implementing Architect approve the
  complete change, and both required Quality Gates pass.
- [x] Explicit Human approval is recorded before AIO-026 is marked `completed`
  or any commit is created.
