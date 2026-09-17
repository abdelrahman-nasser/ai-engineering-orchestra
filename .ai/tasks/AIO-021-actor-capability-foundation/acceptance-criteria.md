# AIO-021 Acceptance Criteria

- [x] `core/actor-specification.md` defines Actor as a concrete identifiable
  Human or Agent candidate and preserves every identity, authority, permission,
  Provider, runtime, availability, and Quality Gate boundary.
- [x] `schemas/actor.schema.json` authorizes exactly `id`, `kind`, and
  `competencies`, requires all three, permits only Human and Agent kinds, rejects
  empty or duplicate competency sets, and remains vocabulary-extensible.
- [x] Human and Agent Actors require no Provider, model, runtime, or reasoning
  data and use identical competency matching semantics.
- [x] The reusable evaluator computes exact case-sensitive set coverage,
  deterministically reports every missing competency, and permits extra Actor
  competencies.
- [x] A Role with empty `required_capabilities` produces a clear incompatible
  diagnostic rather than universal eligibility.
- [x] The result has no score, rank, recommendation, assignment, authority,
  availability, execution decision, independent-review decision, or Quality Gate
  result.
- [x] Canonical terminology and Role cross-references consistently distinguish
  Actor, Role, Agent, Provider, runtime, competency, and operational Capability.
- [x] No Actor catalog, `.ai/actors/`, canonical commercial Actor, CLI command,
  Assignment contract, Provider integration, or external dependency is added.
- [x] Focused Actor schema and evaluator tests cover all Human-specified cases
  and the standalone Actor schema validator passes.
- [x] Full unit, Task, Workflow, Role, Project Manifest, repository, packaging,
  Markdown, and Git diff validations pass or any failure or skip is recorded.
- [x] Separate reviewer and architect reviews approve the actual change and the
  existing `documentation_consistency` and `independent_review` Gates pass.
- [x] Human approval is recorded before the Task is marked `completed` or any
  commit is created.
