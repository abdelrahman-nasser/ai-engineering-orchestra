# AIO-032 Acceptance Criteria

Checklist count: 26.

- [x] A separate Architect design lock approves the bounded canonical term,
  definition, public API, validation composition, result shape, no-schema
  decision, and authority boundaries before implementation.
- [x] The canonical term is Runtime-to-Inference Pair Availability Assessment,
  with established meaning only validated positive compatibility plus two
  normalized available endpoint states in the supplied context.
- [x] The public function accepts exactly the five approved existing typed input
  sequences in the locked order and accepts no Actor, Task, Assignment, policy,
  snapshot-ID, or prevalidated-result input.
- [x] Each caller input sequence is captured exactly once as a tuple, and the
  same captured Runtime and Inference inventories are reused throughout.
- [x] Compatibility validation runs first; invalid compatibility findings retain
  their exact codes, messages, and order and short-circuit availability calls.
- [x] After valid compatibility, both availability validators run against the
  captured inventories even when Runtime availability is invalid.
- [x] Availability findings retain exact codes, messages, and internal order,
  with Runtime findings before Inference findings.
- [x] Every invalid input produces an atomic result with `valid: false`, nonempty
  findings, and no assessments; invalid input never becomes an ordinary outcome.
- [x] The per-edge assessment stores exactly the two endpoint IDs and two typed
  endpoint availability states, while `outcome` is computed and read-only.
- [x] The closed computed outcomes are exactly `established`, `blocked`, and
  `unresolved`, and malformed direct state construction cannot silently become
  an ordinary outcome.
- [x] All nine Runtime/Inference availability combinations implement the locked
  truth table, including both unavailable-plus-unknown orientations.
- [x] Missing and explicit `unknown` observations normalize equivalently for both
  endpoint types and never become unavailable or malformed solely by absence.
- [x] Only normalized supplied positive edges are assessed; no Cartesian product,
  Provider/model inference, totality requirement, or missing-edge incompatibility
  is introduced.
- [x] Valid one-to-many, many-to-one, and mixed-outcome relations produce one
  deterministic assessment per supplied edge without selecting a winner.
- [x] Empty compatibility evidence still validates both availability snapshots
  and yields a valid empty assessment tuple only when every input is valid.
- [x] A Runtime without an external compatibility edge receives no assessment and
  is not classified as blocked, unavailable, internally inferred, or unable to execute.
- [x] Pair identity, exact case-sensitive references, pair ordering, finding
  ordering, and declaration-order independence remain deterministic.
- [x] All public values are frozen and tuple-backed; validation neither mutates
  caller inputs nor rereads one-shot caller sequences.
- [x] The assessment implementation performs no file, network, process, clock,
  polling, discovery, persistence, cache, registry, reservation, or global-state work.
- [x] No Actor coupling, Task suitability, capability or Execution Mode matching,
  selection, ranking, routing, fallback, authorization, execution, adapter, or
  invocation behavior is added.
- [x] No assessment schema, schema fixture, schema resource, serialized request,
  Project Manifest field, CLI command, package-root re-export, or dependency is added,
  and all existing domain schemas and standalone APIs remain unchanged.
- [x] Source-checkout and installed-package tests prove the public API, truth-table
  behavior, diagnostic atomicity, exact package payload, existing schema resources,
  and absence of source fallback or a new schema resource.
- [x] AGENTS, terminology, README, changelog, composed specifications, packaging
  coverage, Task registration, and all four AIO-032 artifacts describe one
  consistent implemented state.
- [x] A non-implementing Architect reviews the complete change against the design
  lock and finds no unresolved material issue.
- [x] A genuinely separate Reviewer evaluates the complete diff, acceptance
  criteria, validation evidence, and limitations; both effective Quality Gates pass.
- [x] Explicit Human architecture and final acceptance approval is recorded before
  Task closure, staging, or commit.
