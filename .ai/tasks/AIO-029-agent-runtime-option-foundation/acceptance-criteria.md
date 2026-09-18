# AIO-029 Acceptance Criteria

- [x] The canonical specifications define Agent Runtime Option Definition and
  Agent Runtime Option Availability Observation as distinct values.
- [x] The Definition contains exactly required nonempty `runtime_option_id`; the
  Availability Observation contains exactly required nonempty
  `runtime_option_id` and closed `state`.
- [x] Agent Runtime Option is defined as an opaque caller/environment-supplied
  configured execution surface through which Agent execution can run or be
  delegated.
- [x] `runtime_option_id` is exact, opaque, case-sensitive, unique within one
  supplied sequence, and never parsed as Provider, model, process, session, or
  invocation identity.
- [x] Structural validation rejects missing or empty fields, additional
  properties, and Actor, Provider, model, tool, and credential fields through
  registered fixtures.
- [x] Immutable values and pure inventory validation return deterministic,
  atomic findings and canonicalized output without I/O, discovery, persistence,
  selection, authorization, or execution.
- [x] Availability states are exactly `available`, `unavailable`, and `unknown`,
  with `unknown` distinct from `unavailable`.
- [x] Missing observations normalize to explicit `unknown`; observations for
  unknown Runtime Options are invalid and never synthesize definitions.
- [x] Identical and conflicting duplicate observations are invalid without
  declaration-order precedence, and invalid snapshots return no partial output.
- [x] Runtime availability never implies Actor compatibility, Inference Option
  availability, Runtime-to-Inference compatibility, authorization, selection,
  capacity, Execution Mode satisfaction, or execution.
- [x] Agent Runtime Option remains distinct from Actor, executable Agent
  definition, execution instance, Inference Option, Agent Service,
  authorization, and credentials.
- [x] Human Actors require no Agent Runtime Option, and no Actor-to-Runtime or
  Actor-to-Inference relation is introduced.
- [x] A Runtime Option may expose zero externally selectable Inference Options;
  Runtime-to-Inference compatibility remains explicitly future work.
- [x] No runtime type, vendor, Provider, model, implementation, framework,
  managed, capability, tool, MCP, sandbox, state, session, capacity, endpoint,
  or credential field is introduced.
- [x] Actor, Inference Option, Assignment, Actor Selection, Execution Mode,
  Workflow, Role, Task, and Project Manifest contracts remain unchanged.
- [x] Both modules and schemas are package-safe and work from editable and normal
  wheel installations outside the checkout without project inventory, Agent
  framework, Provider SDK, or network dependencies.
- [x] Current-state documentation, Source-of-Truth registration, changelog,
  package allowlists, and canonical Task validation agree with implementation.
- [x] AIO-029 contains exactly its four canonical Task artifacts; historical
  Tasks remain unchanged and no AIO-030 exists.
- [x] Full required validation passes, or every failure and skip is recorded
  accurately in review evidence.
- [x] Genuinely separate Reviewer and Architect reviews evaluate the complete
  worktree and both required Quality Gates pass.
- [x] Explicit Human approval is recorded before the Task is marked `completed`
  or any AIO-029 commit is created.
