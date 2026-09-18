# AIO-024 Acceptance Criteria

- [x] The canonical semantic specification defines Actor Availability
  Observation as a provider-neutral, ephemeral value separate from Actor
  identity, eligibility, Assignment, authority, permission, approval,
  reservation, and execution.
- [x] The serialized observation contains exactly nonempty `actor_id` and
  `state`, with `state` restricted to `available`, `unavailable`, and `unknown`.
- [x] The state meanings are explicit, and `unknown` remains distinct from
  `unavailable` in the schema, runtime representation, resolution, and tests.
- [x] Structural validation rejects missing or empty Actor IDs, missing or
  unsupported states, additional properties, and Provider, model, runtime, and
  authorization fields through focused registered fixtures.
- [x] An immutable observation representation and pure validation or resolution
  logic support Human and Agent Actors without I/O, network access, polling,
  persistence, or Provider dependencies.
- [x] Supplied Actor IDs must be unique, observations naming unknown Actors are
  rejected deterministically, and no observation creates Actor identity.
- [x] Duplicate observations for one Actor are rejected without declaration-order
  precedence or last-write-wins behavior, including identical and conflicting
  duplicates.
- [x] A known Actor without an observation resolves deterministically as
  availability-equivalent to `unknown` and is never interpreted as
  `unavailable`.
- [x] Actor identity and competencies, Actor-Role competency coverage, and
  Assignment validity remain independent of availability.
- [x] Available does not imply eligible, assigned, authorized, permitted, or
  executing, and Human or Agent availability grants no approval or execution
  authority.
- [x] No selection, ranking, recommendation, proposed Assignment, selection
  outcome, Actor catalog, availability persistence, reservation, scheduling,
  load, capacity, Provider polling, CLI, or AIO-025 is introduced.
- [x] The runtime module and schema are package-safe and work from a normal wheel
  outside the checkout without project-local availability files or network
  dependencies.
- [x] Existing Actor, Assignment, Task, Workflow, Role, and Project Manifest
  schemas remain unchanged, historical Tasks remain untouched, and AIO-024 has
  exactly its four canonical Task artifacts and canonical Task registration.
- [x] Full required validation passes, or every failure and skip is recorded
  accurately in the review evidence.
- [x] Genuinely separate reviewer and architect reviews approve the actual
  change, and `documentation_consistency` and `independent_review` pass.
- [x] Explicit Human approval is recorded before the Task is marked `completed`
  or any commit is created.
