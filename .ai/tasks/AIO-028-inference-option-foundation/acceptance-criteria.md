# AIO-028 Acceptance Criteria

- [x] The canonical specifications define Inference Option Definition and
  Inference Option Availability Observation as distinct Provider-neutral values.
- [x] The Definition contains exactly required nonempty `option_id`,
  `provider_id`, and `model_id`; the Availability Observation contains exactly
  required nonempty `option_id` and closed `state`.
- [x] Provider identity is an opaque operational access boundary, model identity
  is Provider-scoped, and neither Provider nor model has a closed Core enum.
- [x] `option_id` is unique only within one supplied inventory and is not parsed;
  duplicate Provider/model pairs remain valid when option IDs differ.
- [x] Structural validation rejects missing or empty fields, additional
  properties, Provider-specific configuration, credentials, and unsupported
  availability states through registered fixtures.
- [x] Immutable values and pure inventory validation return deterministic,
  atomic findings and canonicalized output without I/O, discovery, persistence,
  selection, authorization, or execution.
- [x] Availability states are exactly `available`, `unavailable`, and `unknown`,
  with `unknown` distinct from `unavailable`.
- [x] Missing observations normalize to explicit `unknown`; observations for
  unknown options are invalid and never synthesize definitions.
- [x] Identical and conflicting duplicate observations are invalid without
  declaration-order precedence, and invalid snapshots return no partial output.
- [x] Availability changes no Definition identity and never implies selection,
  authorization, execution, quota, price, Execution Mode fit, or runtime state.
- [x] No capability registry, model metadata, endpoints, credentials, Provider
  adapters, Runtime Options, Agent Services, SDKs, network calls, or option
  selection are introduced.
- [x] Actor, Assignment, Actor Selection, Execution Mode, Workflow, Role, Task,
  Project Manifest, and existing domain schemas retain their existing contracts.
- [x] Both modules and schemas are package-safe and work from editable and normal
  wheel installations outside the checkout without project inventory or network
  dependencies.
- [x] Current-state documentation, Source-of-Truth registration, changelog,
  package allowlists, and canonical Task validation agree with the implementation.
- [x] AIO-028 contains exactly its four canonical Task artifacts; historical
  Tasks remain unchanged, no AIO-029 exists, and closure changes only its
  approved lifecycle and review evidence.
- [x] Full required validation passes, or every failure and skip is recorded
  accurately in the review evidence.
- [x] Genuinely separate Reviewer and Architect reviews approve the actual
  complete worktree and both required Quality Gates pass.
- [x] Explicit Human approval is recorded before the Task is marked `completed`
  or the approved AIO-028 commit is created.
