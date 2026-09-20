# AIO-034 Acceptance Criteria

Checklist count: 32.

- [x] A separate non-implementing Architect approves the canonical term,
  definition, public API, candidate identity, result fields, exact outcomes,
  reason codes, validation order, atomicity, coherence strategy, Human handling,
  external-inference boundary, and exclusions before implementation.
- [x] The canonical term is Agent Execution Candidate Prerequisite Assessment
  and its definition is limited to currently modeled hard prerequisites for one
  caller-designated external-inference Agent candidate.
- [x] Candidate identity is exactly one Assignment plus `runtime_option_id` plus
  `option_id`, flattening to the seven exact responsibility, Actor, Runtime, and
  Inference identifiers without a `candidate_id`.
- [x] Assignment remains the immutable responsibility anchor; Actor Selection is
  not an input and no reassignment, replacement, refresh, or Assignment field
  change is introduced.
- [x] Every caller-supplied sequence is captured exactly once as a tuple, reused
  through all composed validators, never mutated, and never re-enumerated.
- [x] The existing Assignment validator is reused without weaker duplicate
  validation, and an invalid Assignment produces an atomic invalid result with
  findings and no ordinary outcome.
- [x] A valid Assignment naming a Human Actor is routed outside the Agent path
  through the design-locked non-applicable handling without blocking or
  invalidating the Human Actor or Assignment.
- [x] Current Actor Availability validation is reused against the same Actor
  context; missing observations retain existing normalized `unknown` semantics.
- [x] An assigned Agent observed `unavailable` blocks the candidate without
  invalidating or mutating the Assignment.
- [x] An assigned Agent with `unknown` availability, including a missing
  observation, yields an unresolved candidate when no explicit blocker exists.
- [x] `validate_actor_runtime_applicability` is reused against the same captured
  Actor and Runtime contexts, and the complete supplied relation is validated.
- [x] Absence of the exact assigned-Actor-to-candidate-Runtime edge is valid
  missing positive evidence and contributes `unresolved`, never incompatibility
  or `blocked`.
- [x] The existing Runtime-to-Inference Pair Availability assessor is invoked
  internally with the same captured Runtime and Inference inventories,
  compatibility evidence, and endpoint observations; detached results are not
  accepted as sufficient context evidence.
- [x] The caller must supply exact existing Runtime and Inference endpoint IDs;
  the assessment never enumerates, constructs, selects, or infers candidates.
- [x] Invalid parent evidence from Assignment, Actor Availability,
  applicability, compatibility, inventories, or endpoint availability produces
  `valid: false`, deterministic findings, `outcome: None`, and no partial
  candidate evidence.
- [x] A valid exact pair with outcome `blocked` contributes the candidate
  outcome `blocked`.
- [x] A valid exact pair with outcome `unresolved` contributes the candidate
  outcome `unresolved` when no explicit blocker exists.
- [x] Actor available plus the exact applicability edge plus the exact
  established pair produces `satisfied` and the locked positive reason code.
- [x] Missing Runtime-to-Inference positive evidence yields no exact pair
  assessment and contributes `unresolved`; no missing positive fact becomes
  `blocked`.
- [x] The assessment creates no Actor-to-Inference relation or canonical
  transitive applicability claim.
- [x] Runtime-owned or hidden inference remains outside the assessment without
  null, wildcard, fake, or synthesized Inference Options and without a blocked
  classification.
- [x] Execution Mode remains Task/process depth and is not an assessment input
  or Runtime, model-strength, or reasoning-tier fit rule.
- [x] No filesystem, shell, network, MCP/tool, context-window, permission,
  credential, Human approval, policy, or execution-authorization semantics are
  introduced.
- [x] No selection, ranking, scoring, preference, routing, fallback, winner,
  reservation, dispatch, Execution Contract, adapter, execution, or invocation
  behavior is introduced.
- [x] The implementation performs no filesystem, network, subprocess, clock,
  polling, discovery, persistence, cache, registry, or global mutable-state work
  and introduces no schema or new dependency.
- [x] Outcome reason codes and invalid-input findings are immutable, separate,
  deterministic, and ordered according to the Architect design lock.
- [x] Input declaration order does not affect valid outcomes, reasons, or
  findings; caller inputs remain unmodified and one-shot iterables are consumed
  once.
- [x] Focused tests cover all twelve mandatory scenarios plus exact IDs, unknown
  candidate endpoints, every invalid parent category, frozen values, atomicity,
  deterministic order, nonmutation, purity, and absence of automatic candidate
  enumeration.
- [x] Source-checkout, editable-install, and normal-wheel tests prove equivalent
  public behavior, module import outside the checkout, existing resource
  resolution, no new schema, no source fallback, no new dependency, and no
  generated or vendor payload.
- [x] AGENTS, terminology, README, changelog, composed specifications, Task
  evidence, implementation, tests, and package evidence describe one consistent
  implemented state.
- [x] A non-implementing Architect reviews the complete change, a genuinely
  separate Reviewer evaluates the diff and evidence, all required validation
  passes or is reported accurately, and both effective Quality Gates pass with
  no unresolved material finding.
- [x] Explicit Human architecture/public-contract approval and final acceptance
  are recorded before Task closure, staging, or commit.
