# AIO-031 Acceptance Criteria

Checklist count: 25.

- [x] A separate canonical Runtime-to-Inference Compatibility Evidence
  specification defines the approved positive-evidence semantics and limits.
- [x] The immutable evidence value contains exactly required
  `runtime_option_id` and `option_id`, in that order.
- [x] Both references remain nonempty, opaque, exact, case-sensitive, and are
  never parsed, normalized, trimmed, or replaced with Provider/model identity.
- [x] Agent Runtime Option and Inference Option Definitions and their identity
  and inventory-validation semantics remain unchanged.
- [x] Exact pair identity supports one-to-many and many-to-one evidence without
  a preferred, default, selected, or required-complete edge set.
- [x] Both foundational inventory validators execute before relation semantics;
  invalid endpoint findings are preserved deterministically without edge
  inspection or partial output.
- [x] Duplicate exact edges invalidate the complete relation without implicit
  deduplication or declaration-order precedence.
- [x] Unknown Runtime and Inference references are rejected using stable,
  deterministic diagnostics without synthesizing or dropping endpoints.
- [x] Empty evidence is valid for every valid empty/nonempty endpoint-inventory
  combination, while any edge to an absent endpoint remains invalid.
- [x] Missing edges mean only no supplied positive external evidence, and
  Runtime-owned inference remains possible without a synthetic or null edge.
- [x] Valid evidence is canonically ordered by exact
  `(runtime_option_id, option_id)` solely for deterministic representation.
- [x] Findings use the locked category and exact identifier ordering and are
  independent of declaration order.
- [x] Every invalid result is atomic and contains no partial normalized
  relation.
- [x] Validation does not mutate caller inputs or perform I/O, persistence,
  discovery, network, Provider, process, selection, authorization, or execution
  work.
- [x] The structural schema enforces exactly the two approved nonempty string
  fields and rejects missing, empty, wrong-type, and additional properties.
- [x] Structural tests remain distinct from semantic inventory/reference and
  relation tests; the schema makes no foreign-reference claim.
- [x] Compatibility remains independent from Actor, Runtime, and Inference
  availability and adds no availability composition, freshness, health,
  capacity, or quota behavior.
- [x] Actor identity and competency, Actor Selection, Assignment, Execution
  Mode, and capability semantics remain unchanged.
- [x] No configuration viability, ranking, routing, fallback, selection,
  authorization, reservation, Execution Contract, dispatch, or invocation is
  introduced.
- [x] No registry, graph service, database, cache, project inventory, Project
  Manifest storage, adapter, SDK integration, discovery, credential, endpoint,
  or network dependency is introduced.
- [x] The minimal public runtime API and canonical schema resource work from
  the source checkout without package-root re-export or source fallback claims.
- [x] Editable and normal-wheel installations outside the checkout expose the
  API and schema and verify valid, duplicate, unknown-reference, and empty
  relation behavior with the exact wheel allowlist.
- [x] README, terminology, changelog, AGENTS Sources of Truth, endpoint
  cross-references, package registration, tests, and AIO-031 evidence agree with
  the implemented current state.
- [x] All applicable focused, full-suite, schema, existing-contract,
  repository, packaging, installation, Markdown, and diff checks pass or every
  failure and skip is reported; a separate Reviewer and Architect evaluate the
  complete change and both effective Quality Gates pass.
- [x] Explicit Human architecture/schema and final acceptance approval is
  recorded before Task closure or any commit is created.
