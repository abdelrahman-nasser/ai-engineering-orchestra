# AIO-041 Acceptance Criteria

Checklist count: 49.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact security boundary before implementation.
- [x] The canonical term is Agent Execution Contract.
- [x] The contract is immutable declarative intent, not execution readiness.
- [x] Scope is Agent-only and external-inference-only.
- [x] The ten AIO-040 subject fields are embedded directly and in canonical order.
- [x] `execution_mode` is the only additional field.
- [x] Execution Mode remains outside the action subject and grants no authority.
- [x] Mode is exactly `lite | standard | deep | critical`.
- [x] Mode is not inferred from Complexity, Risk, Workflow, Stage, Role, Actor, Runtime, or Inference Option.
- [x] Runtime Option identity is bound exactly.
- [x] Inference Option identity is bound exactly.
- [x] Environment identity is bound exactly.
- [x] Operation and resource are bound exactly.
- [x] Operation and resource validation reuse AIO-036 semantics.
- [x] No generic payload is introduced.
- [x] No tool, adapter, Provider, model, credential, or endpoint field is introduced.
- [x] No contract ID, correlation reference, attempt ID, or idempotency key is introduced.
- [x] Repeated identical subject and mode preparations produce equal values.
- [x] Canonical preparation accepts one exact AIO-040 result and one explicit effective mode.
- [x] Exact observable AIO-040 result coherence is checked without recomputing parent assessments.
- [x] Only coherent valid and satisfied input with the canonical positive reason prepares a contract.
- [x] A blocked assessment produces no contract.
- [x] An unresolved assessment produces no contract.
- [x] Invalid, wrong-type, or incoherent input produces no contract.
- [x] Public constructibility and unauthenticated preparation provenance are explicit limitations.
- [x] Intrinsic validation does not prove canonical preparation.
- [x] No prerequisite outcome, reasons, state, or assessment reference is stored.
- [x] No authority or provenance is copied into the contract.
- [x] Contract existence establishes neither permission nor authorization.
- [x] Preparation consumes no authorization and mutates no input.
- [x] Future Run or dispatch work requires fresh prerequisite assessment and fresh effective-mode resolution.
- [x] A fresh AIO-040 result alone remains insufficient for actual invocation.
- [x] No lifecycle, Run, attempt, status, timestamp, or expiry field is introduced.
- [x] No dispatch or invocation behavior is introduced.
- [x] No result, error, cost, token, duration, or telemetry field is introduced.
- [x] No Permission Decision, policy composition, enforcement, or mutation is introduced.
- [x] Values and results are frozen, deterministic, and tuple-backed.
- [x] Preparation and validation perform no filesystem, network, subprocess, clock, randomness, database, cache, or discovery I/O.
- [x] Every invalid result is atomic with `contract=None`.
- [x] The closed eleven-field schema, structural fixtures, and semantic fixtures pass.
- [x] Serialization round-trip preserves equality without claiming preparation provenance.
- [x] AIO-026, AIO-036, and AIO-040 public behavior remains unchanged.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback.
- [x] All 28 scenarios plus forged-result, mode, subject-mutation, operation, resource, equality, and no-I/O cases pass.
- [x] The protected target, AIO-030, and Full Control Center or UI track remain untouched.
- [x] Architect, Security, and independent final reviews approve.
- [x] `documentation_consistency` and `independent_review` pass without waiver.
- [x] Explicit Human architecture, schema, security, and final acceptance is recorded before closure.

All 49 acceptance criteria are satisfied following explicit Human approval on
2026-09-21.
