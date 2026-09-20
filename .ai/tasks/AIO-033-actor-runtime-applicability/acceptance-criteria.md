# AIO-033 Acceptance Criteria

Checklist count: 30.

- [x] A separate non-implementing Architect approves the canonical term,
  definition, public API, validation order, diagnostics, schema/runtime split,
  and authority boundaries before implementation.
- [x] The canonical term is Actor-to-Runtime Applicability Evidence and means
  only caller-supplied positive evidence that one known Agent Actor may use one
  known Agent Runtime Option within the supplied evaluation context.
- [x] The immutable evidence value contains exactly required `actor_id` and
  `runtime_option_id`, in that order, with no applicability ID or other field.
- [x] Both references remain nonempty, opaque, exact, and case-sensitive and are
  never parsed, normalized, trimmed, case-folded, or assigned format rules.
- [x] The structural schema accepts exactly the two required nonempty string
  fields, rejects additional properties, and makes no foreign-reference or
  Actor-kind claim.
- [x] The supplied Actor sequence is captured once, preserves the Actor
  contract, and rejects duplicate Actor IDs using the established diagnostic.
- [x] The supplied Runtime Option sequence is captured once and validated by
  `validate_agent_runtime_option_inventory` without weaker reimplementation.
- [x] Every applicability edge references one known Actor whose exact `kind` is
  `agent`; Actor kind grants no authority or preference.
- [x] A known Human Actor endpoint is rejected with the design-locked stable
  diagnostic without invalidating the Human Actor or changing the Human path.
- [x] Every duplicated exact `(actor_id, runtime_option_id)` edge is rejected
  once deterministically without deduplication or declaration-order precedence.
- [x] Every unknown Actor reference is rejected deterministically without
  synthesis, inference, silent dropping, or partial output.
- [x] Every unknown Runtime Option reference is rejected deterministically using
  the established Runtime reference diagnostic convention.
- [x] One-to-many, many-to-one, and mixed many-to-many applicability relations
  validate without selecting, preferring, ranking, or routing an endpoint.
- [x] Empty evidence is valid for every valid Actor/Runtime context and yields an
  empty normalized tuple.
- [x] A missing edge means only that no positive applicability evidence was
  supplied; it never means incompatible, unavailable, unauthorized, or unable
  to execute.
- [x] Valid evidence is canonically ordered by exact
  `(actor_id, runtime_option_id)` solely for deterministic representation.
- [x] Foundational and relation finding categories follow the locked order, with
  exact case-sensitive sorting inside each category and declaration-order
  independence.
- [x] Every invalid input produces an atomic result with `valid: false`,
  nonempty findings, and no normalized evidence.
- [x] All public values are frozen and result collections are tuples; all three
  caller sequences are captured once and are neither mutated nor reread.
- [x] Validation performs no filesystem, network, process, clock, environment,
  discovery, persistence, cache, registry, or global mutable-state work.
- [x] Actor fields, Actor-role competency semantics, and the Actor schema remain
  unchanged.
- [x] Agent Runtime Option fields, inventory validation, and Runtime Availability
  semantics remain unchanged.
- [x] Actor Availability, Actor Selection, and Assignment fields and behavior
  remain unchanged, including the Human Actor path.
- [x] Inference Option, Inference Availability, Runtime-to-Inference
  compatibility, and Pair Availability Assessment remain unchanged.
- [x] Applicability composes no Actor, Runtime, or pair availability state and
  adds no available, unavailable, or unknown state.
- [x] No Task/Role suitability, Complexity/Risk mapping, Execution Mode fit,
  runtime capability, tool, permission, credential, or Human authorization
  behavior is introduced.
- [x] No selection, ranking, routing, fallback, reservation, dispatch,
  Execution Contract, execution, adapter, or invocation behavior is introduced.
- [x] Source-checkout and installed-package tests prove the public API, schema
  resource, relation semantics, diagnostic atomicity, exact package payload,
  and absence of source fallback or a new dependency.
- [x] AGENTS, terminology, README, changelog, composed specifications, packaging,
  Task evidence, Architect review, independent review, and both effective
  Quality Gates describe one consistent implemented state.
- [x] Explicit Human architecture/schema and final acceptance approval is
  recorded before Task closure, staging, or commit.
