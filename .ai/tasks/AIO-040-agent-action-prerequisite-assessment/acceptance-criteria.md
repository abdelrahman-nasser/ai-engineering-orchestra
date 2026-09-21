# AIO-040 Acceptance Criteria

Checklist count: 52.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact security boundary before implementation.
- [x] The canonical term is Agent Action Prerequisite Assessment.
- [x] The definition states pure, immutable, deterministic, ephemeral, and in-memory behavior.
- [x] The concept is a derived assessment, not caller-supplied evidence, a Grant, Decision, or Execution Contract.
- [x] Identity is the exact ordered ten-part AIO-039 action subject.
- [x] No synthetic assessment, action, candidate, execution, or run identifier or Environment entity is introduced.
- [x] Only Agent Assignments with exact external Inference Options are applicable.
- [x] Human Assignment produces a boundary finding and no ordinary outcome.
- [x] Runtime-owned inference remains excluded.
- [x] The exact coherent AIO-034 candidate result is consumed without recomputing its prerequisite logic.
- [x] Exactly one Operation Requirement is assessed per call with the canonical validator.
- [x] Capability input is an exact AIO-037 validation result.
- [x] Permission input is an exact AIO-038 validation result.
- [x] Authorization input is an exact AIO-039 validation result.
- [x] One exact nonempty environment identifier binds the action context.
- [x] Raw capability, permission, and authorization collections are absent from the public API.
- [x] Exact parent result types and coherence invariants are checked deterministically.
- [x] Any invalid parent produces an atomic invalid result with no identity, outcome, or reasons.
- [x] Parent findings retain their codes, messages, and deterministic source order.
- [x] Capability lookup uses the exact Runtime and operation identity.
- [x] A missing required normalized capability pair is invalid cross-context input.
- [x] Permission lookup uses the exact Runtime, environment, operation, and resource identity.
- [x] Missing exact permission is semantically unknown.
- [x] Authorization lookup uses the exact ten-part action subject.
- [x] Missing exact authorization is missing and unproven, not denied.
- [x] Ordinary outcomes are exactly `satisfied`, `blocked`, and `unresolved`.
- [x] Candidate blocked, capability absent, permission denied, or authorization denied makes the outcome blocked.
- [x] A blocker dominates every uncertainty while all applicable reasons remain present.
- [x] Candidate unresolved, capability unknown, permission unknown, or authorization missing makes the outcome unresolved when no blocker exists.
- [x] Only all-positive valid exact prerequisites produce satisfied.
- [x] Invalid input never becomes blocked or unresolved.
- [x] All applicable reasons are returned.
- [x] The exact nine-code reason taxonomy is implemented.
- [x] Reason order is candidate, capability, permission, then authorization.
- [x] Satisfied has only `all_currently_modeled_action_prerequisites_satisfied`.
- [x] Invalid capability data remains invalid and is not reinterpreted by AIO-040.
- [x] Permission duplicates or conflicts remain invalid and are never resolved by stricter-wins.
- [x] Authorization duplicates, conflicts, or unsupported multi-authority evidence remain invalid.
- [x] No Permission Decision, policy composition, or Task-approval-to-authorization mapping occurs.
- [x] `granted` authority evidence remains caller-attested and unauthenticated.
- [x] Satisfied explicitly does not imply execution readiness, Core authorization, dispatchability, invocation, or success.
- [x] Values and results are frozen, tuple-backed, deterministic, and do not mutate inputs.
- [x] The implementation performs no I/O, discovery, enforcement, dispatch, or invocation.
- [x] No schema, persistence, package-root export, or new dependency is introduced.
- [x] AIO-034 and AIO-036 through AIO-039 public behavior remain unchanged.
- [x] Source, editable-install, and normal-wheel behavior agree without source fallback.
- [x] No Execution Contract, Execution Run, tool binding, authorization consumption, replay protection, revocation, or lifecycle is added.
- [x] All 26 scenarios, blocker/uncertainty combinations, reason retention, determinism, atomicity, exact lookup, and no-I/O tests pass.
- [x] Protected-target access, AIO-030, AIO-041, VS Code, and Full UI work remain excluded and untouched.
- [x] Architect, Security, and fresh independent final reviews pass and both required Quality Gates pass without waiver.
- [x] Explicit Human architecture/security/final acceptance is recorded before closure.

Criteria 1 and 2 must be completed before implementation begins. Criterion 52
was completed by direct Human final approval on 2026-09-21 after all required
reviews and Quality Gates passed without waiver.
