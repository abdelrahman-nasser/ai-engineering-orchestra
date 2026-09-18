# AIO-025 Acceptance Criteria

- [x] The canonical Actor Selection specification defines pure deterministic
  hard-constraint resolution for exactly one Task/Workflow/Stage/Role
  responsibility and defines the caller-supplied candidate-set and snapshot
  scope.
- [x] The runtime API accepts a schema-valid Task with explicit Workflow,
  `stage_id`, `role_id`, valid Workflow and Role catalogs, schema-valid supplied
  Actors, and supplied Actor Availability Observations without introducing a
  public request contract or Actor Catalog.
- [x] The result is immutable, retains only Actor IDs as candidate evidence,
  separates validity from outcome, and exposes exactly `selected`, `ambiguous`,
  `indeterminate`, and `no_candidate` outcomes.
- [x] Invalid availability or responsibility context produces no selection
  outcome and no partial candidate evidence, while corrupt catalogs preserve
  their existing infrastructure-error semantics.
- [x] Selection reuses existing Actor-Role competency coverage and AIO-024
  availability validation and normalization without duplicating either
  contract.
- [x] Missing availability observations remain `unknown`, and one eligible
  available Actor plus one eligible unknown Actor returns `indeterminate` with
  no selected Actor.
- [x] Two or more eligible available Actors return `ambiguous`, including when
  another eligible Actor is unknown, and all unknown IDs remain visible as
  evidence.
- [x] Empty candidates, no eligible candidates, and all eligible unavailable
  candidates return `no_candidate` with the appropriate closed reason.
- [x] Eligible, available, and unknown Actor IDs are sorted by case-sensitive
  Actor ID solely for deterministic evidence; declaration order, lexical order,
  randomness, Actor kind, and hidden preference never select a winner.
- [x] Human-only, Agent-only, and mixed candidate sets use identical hard
  constraints and neither Actor kind receives preference or authority.
- [x] Selection does not use Task Complexity, Risk, Execution Mode, existing
  Assignments, reviewer-separation policy, Provider/model facts, Quality Gates,
  authorization, reservation, persistence, network access, or execution.
- [x] Selection creates no Assignment or proposed Assignment, and a caller-built
  final Assignment still requires and can pass AIO-023 validation independently.
- [x] Any shared private responsibility resolver preserves all existing AIO-023
  finding order, messages, exceptions, validity, completeness, and separation
  evidence.
- [x] No Selection schema or changes to existing Task, Workflow, Role, Actor,
  Assignment, Availability, or Project Manifest schemas are introduced.
- [x] The normal wheel includes the runtime implementation and proves outside
  the checkout that Role resolution, competency coverage, availability
  normalization, and Actor Selection work without project-local storage,
  Provider integration, or network dependency.
- [x] AIO-025 has exactly four canonical Task artifacts, is registered in
  canonical Task validation, and historical Task artifacts remain unchanged.
- [x] Current-state documentation consistently distinguishes Selection from
  Assignment, authorization, reservation, execution, and Quality Gate results.
- [x] All required focused, regression, schema, repository, installation,
  Markdown, and diff checks pass, or every failure and skip is recorded
  accurately in review evidence.
- [x] A genuinely separate Reviewer and non-implementing Architect approve the
  complete change, and `documentation_consistency` and `independent_review`
  pass.
- [x] Explicit Human approval is recorded before the Task is marked `completed`
  or any commit is created.
