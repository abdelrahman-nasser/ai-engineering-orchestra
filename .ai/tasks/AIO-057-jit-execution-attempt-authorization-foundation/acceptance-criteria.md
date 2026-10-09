# AIO-057 Acceptance Criteria

## Phase 1 checkpoint

- [x] Preserve verified main baseline b6566cdb8538e63307d1bae536fb56929a2b32c3 and the clean index before artifact creation.
- [x] Use only exact authorized predecessor evidence; no catalog enumeration, discovery, recursive search or protected-target access.
- [x] Compare both physical identity alternatives; keep the complete Run as semantic identity and select exact pinned-ledger Dispatch/claim_id/generation as physical-attempt identity.
- [x] Define the full Claim authorization subject and one Session-wide registry, one cell per physical key with complete subject conflict checks, and no independent same-subject consumption states.
- [x] Define exact preparation retry, aliases, publication, loss, abandonment, concurrent consumption and non-rearming terminal states.
- [x] Define exact private authority coordination, underlying state-partition ownership, all mutation participation, source failures and unsupported external-source behavior.
- [x] Preserve AIO-050 public issuance semantics; require an entry-purpose private decision and shared validation rather than issuance/presentation replay.
- [x] Preserve AIO-051 immutable snapshot and total historical resolver; define separate retirement rejection and terminal lifecycle configuration changes.
- [x] Define S/G/P/W/C acquisition order, COMMIT release exception and prohibition of inversion, nested public calls or mutation from read callbacks.
- [x] Define logical entry authorization time T conditional on successful future Entry COMMIT; later expiry or revocation does not retroactively cancel accepted entry.
- [x] Define mandatory future permanent Dispatch-unique Entry, original once-only effect continuation, reclaim exclusion and conservative crash/commit-unknown outcomes.
- [x] Define 96 explicit scenarios: 72 AIO-057 foundation obligations plus 24 deferred AIO-058 consumer obligations, without claiming future implementation or test results.
- [x] Define Task-local Validation Safety Matrix separately from authorized bootstrap/control commands.
- [x] All five fresh independent R2 design reviews APPROVE, with BLOCKER 0 and HIGH 0; record real reviewer provenance and historical rejected evidence.
- [x] Create exactly task.yaml, context.md, acceptance-criteria.md and review.md after convergence; no implementation, tests or migration.
- [x] Confirm the artifact footprint, exact text/count/whitespace evidence, unchanged HEAD and clean index.
- [x] State that Phase-1 review does not satisfy final documentation_consistency or independent_review Quality Gates.

## Later AIO-057 implementation and validation

Phase 2 and the exact path/validation supplements are now explicitly
authorized. Checked conditions below have Phase-2 implementation evidence in
review.md; they are not formal final Gate or Human acceptance verdicts.

- [x] Human explicitly authorizes the implementation scope and exact affected paths before production or test creation.
- [x] Exact Task and selected Workflow schema checks pass before implementation using matrix-approved direct loaders.
- [x] The one-registry/shared-cell factory and capability provenance checks enforce the locked subject, retry, concurrency and non-rearming semantics.
- [x] The private cooperative authority guard and AIO-050 entry-purpose validation extension enforce every registered mutable path without public API/schema or ordinary issuance changes.
- [x] The private owned Store scope supplies current audited Claim and parent facts and unchanged canonical time/watermark handling without leaking raw Store/connection access.
- [x] Preparation and diagnostic verification perform no entry/effect and never manufacture positive durable-entry authority from a v3 ledger.
- [x] All 72 foundation scenarios have fresh focused evidence, with every failed/skipped validation reported.
- [x] Focused predecessor, documentation and packaging checks are statically scoped and matrix-authorized before execution; required evidence, including one platform regression skip, is recorded.
- [x] No AIO-057 migration, persistent JIT authority, Claim/Renewal mutation, public widening, target IO, Tool invocation, transport, Result or command path is introduced.
- [x] Any required public predecessor redesign or durable entry inside AIO-057 stops as MATERIAL DESIGN CHANGE; none was required.

## Future consumer contract

E01-E24 are mandatory separately authorized AIO-058 acceptance obligations.
They are not implemented AIO-057 features, executed tests, inherited PASS
evidence, or skipped AIO-057 tests. AIO-058 may not effect a Tool until its
same-ledger Entry capability and controlled original continuation implement the
locked contract. AIO-057 does not claim AIO-058 readiness or exactly-once success.

## Final review and closure

- [x] Fresh post-implementation reviews and documentation_consistency/independent_review Quality Gates pass in their separately authorized phase.
- [x] Required Human architecture/final acceptance and explicit Task closure are recorded.
