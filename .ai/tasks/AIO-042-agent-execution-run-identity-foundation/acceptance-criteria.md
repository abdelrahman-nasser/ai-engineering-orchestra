# AIO-042 Acceptance Criteria

Checklist count: 56.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact security boundary before implementation.
- [x] The canonical term is Agent Execution Run.
- [x] The Run is immutable occurrence identity, not lifecycle, readiness, or execution state.
- [x] The Run contains exactly `run_id` then `contract`.
- [x] `run_id` is an exact, opaque, case-sensitive, nonempty string.
- [x] The caller or execution coordinator owns Run-ID allocation and operational non-reuse.
- [x] Core performs no Run-ID generation, UUID generation, hashing, timestamp derivation, or randomness.
- [x] Run-ID validation proves neither global uniqueness nor authenticity.
- [x] `contract` is the exact nested and intrinsically validated `AgentExecutionContract` value.
- [x] The AIO-041 Agent Execution Contract remains unchanged.
- [x] The Run has no flattened Contract fields, Contract ID, or Contract hash.
- [x] One Run represents one concrete attempt.
- [x] No `attempt_id`, retry count, retry lineage, or previous-Run field is introduced.
- [x] Equal Contracts may bind distinct Run IDs and thereby form distinct Runs.
- [x] Equal Run ID and Contract values mean the same Run represented again.
- [x] Equal Run IDs with different Contracts are documented as an identity-binding conflict that one-value validation cannot globally detect.
- [x] Representation equality is `(run_id, contract)` while logical occurrence identity is `run_id`.
- [x] Canonical preparation accepts an intended Contract, fresh AIO-040 result, effective mode, and caller-supplied Run ID.
- [x] Freshness is caller-owned current parent evidence and is not inferred from repeated composition over cached results.
- [x] Only an observably coherent valid and `satisfied` AIO-040 result can prepare a Run.
- [x] The effective Task-wide Execution Mode is freshly supplied and never inferred or substituted.
- [x] Canonical preparation reuses `prepare_agent_execution_contract` rather than reimplementing AIO-040 or AIO-041.
- [x] Exact equality between the freshly prepared and intended Contract is required.
- [x] A blocked prerequisite result produces no Run.
- [x] An unresolved prerequisite result produces no Run.
- [x] Invalid, wrong-type, or incoherent inputs produce no Run.
- [x] Any fresh/intended Contract mismatch produces no Run.
- [x] Direct construction and intrinsic validation do not prove canonical preparation, provenance, freshness, or operational uniqueness.
- [x] Caller-attested AIO-039 `granted` remains unauthenticated and non-authoritative.
- [x] Run creation consumes no authorization and mutates no permission or authorization state.
- [x] No replay, revocation, expiry, grant, token, authorization-ID, or consumption claim is introduced.
- [x] TOCTOU remains explicitly unsolved and owned by a future dispatch-admission layer.
- [x] No lifecycle, status, transition, mutable record, state snapshot, or event sourcing is introduced.
- [x] No timestamp, clock, expiry, duration, or temporal-order field is introduced.
- [x] No persistence, Run registry, database, cache, queue, repository, or history store is introduced.
- [x] No cancellation, failure, retry mechanism, or retry lineage is introduced.
- [x] No tool, adapter, Provider, model, endpoint, credential, payload, or command binding is introduced.
- [x] No result, error, output, event, token, cost, duration, usage, or telemetry field is introduced.
- [x] Values and results are frozen, deterministic, tuple-backed, and atomically return `run=None` on failure.
- [x] Validation and preparation perform no filesystem, network, subprocess, clock, randomness, database, cache, discovery, dispatch, or invocation I/O.
- [x] The Draft 2020-12 Run schema is closed and contains exactly required `run_id` and `contract` properties.
- [x] The nested Contract schema is reused by packaged offline `$ref`, not duplicated.
- [x] Schema resolution performs no network retrieval, CWD lookup, or external source-checkout fallback.
- [x] Serialization round-trip preserves exact Run value equality without proving preparation provenance.
- [x] All 36 required scenarios explicitly preserve no-lifecycle, no-dispatch, and no-invocation boundaries.
- [x] Run-ID tests cover opaque, case-sensitive, whitespace-containing, UUID-looking, empty, wrong-type, repeated, and distinct values without normalization.
- [x] Fresh Contract mismatch tests cover all eleven Contract fields.
- [x] Human Assignment and Runtime-owned inference remain outside the Agent external-inference Run preparation boundary.
- [x] Static and dynamic guards prove no I/O, clock, randomness, schema network fetch, dispatch, or invocation.
- [x] AIO-040 and AIO-041 public behavior remains unchanged.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback.
- [x] The protected target, AIO-030, and Full Control Center or UI track remain untouched.
- [x] Architect, Security, and fresh independent final reviews approve the implementation and evidence.
- [x] `documentation_consistency` and `independent_review` pass without waiver.
- [x] Explicit Human architecture, schema, security-boundary, and final acceptance is recorded before Task closure.

All 56 acceptance criteria are satisfied following direct Human architecture,
schema, security-boundary, final acceptance, closure, and local-commit approval
on 2026-09-21.
