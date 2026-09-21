# AIO-043 Acceptance Criteria

Checklist count: 60.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact trust boundary before implementation.
- [x] The canonical term is Agent Execution Authorization Grant.
- [x] The Grant is a positive authority artifact, not evidence, Permission, a Permission Decision, a token, or lifecycle state.
- [x] The Grant contains exactly the eight locked fields in canonical order.
- [x] The complete exact nested Agent Execution Run is required and intrinsically validated.
- [x] A bare Run ID is insufficient and no Run or Contract fields are flattened.
- [x] `grant_id` is required, opaque, exact, case-sensitive, and nonempty.
- [x] The effective Grant identity is exactly domain plus issuer kind plus issuer ID plus Grant ID.
- [x] The external authenticated producer allocates Grant IDs; Core does not generate them.
- [x] Grant-ID acceptance makes no global uniqueness claim.
- [x] `authorization_domain_id` is required and is distinct from `environment_id`.
- [x] `issuer_kind` is exactly `human` or `policy`.
- [x] `issuer_id` is required, exact, opaque, case-sensitive, and nonempty.
- [x] Direct construction, runtime validity, and schema validity do not authenticate an issuer.
- [x] Operational trust explicitly requires an external authenticated and integrity-protected producer boundary.
- [x] `provenance_reference` is required and remains audit-only, not identity or authentication proof.
- [x] The Grant is positive-only and has no `state` field.
- [x] At-most-one-use is fixed semantic intent with no reusable flag or use counter.
- [x] One Grant binds exactly one Run.
- [x] One Run has zero or at most one accepted Grant per supplied authorization domain in v1.
- [x] Multi-authority composition is unsupported and fails closed.
- [x] Replacement or reissue for the same Run/domain is unsupported.
- [x] `issued_at` is required and uses the locked canonical UTC grammar.
- [x] `expires_at` is required and uses the locked canonical UTC grammar.
- [x] Runtime validation enforces valid Gregorian timestamps and `issued_at < expires_at`.
- [x] Validation uses no wall clock and makes no currentness claim.
- [x] No clock-skew or revocation model is introduced.
- [x] Core neither issues nor authenticates a Grant.
- [x] No signature, key, cryptographic, bearer-token, introspection, or network-authority implementation is introduced.
- [x] Intrinsic validation is pure, deterministic, exact-type robust, and atomic.
- [x] Exact duplicate Grants invalidate the whole collection.
- [x] A reused composite Grant identity with any differing field is an identity-binding conflict.
- [x] A reused Run ID with a different Contract is a Run identity-binding conflict.
- [x] Multiple distinct Grant identities for one exact Run/domain invalidate the collection.
- [x] Human and policy Grants for one exact Run/domain are rejected as unsupported multi-authority.
- [x] No conflict chooses first, last, latest, Human, policy, shorter expiry, or longer expiry.
- [x] Valid collections are canonically ordered by domain, issuer kind, issuer ID, and Grant ID.
- [x] Invalid collection results contain findings and no normalized Grants.
- [x] Collection inputs are captured once and never mutated.
- [x] The closed Draft 2020-12 schema contains exactly eight required properties.
- [x] The schema references the canonical Run schema and resolves Run plus Contract resources offline.
- [x] Unknown, missing, or mismatched schema references fail closed without network or CWD fallback.
- [x] Serialization round-trip preserves exact equality without proving authentication, currentness, or consumption.
- [x] No registry, persistence, database, cache, queue, store, ledger, or transaction is added.
- [x] No consumption, replay-protection, or revocation claim or API is added.
- [x] No Tool Binding or adapter, Provider, endpoint, credential, command, parameter, or payload binding is added.
- [x] No dispatch admission, dispatch, invocation, result, error, event, or telemetry is added.
- [x] AIO-039, AIO-040, AIO-041, and AIO-042 public behavior remains unchanged.
- [x] Required scenario, collision, domain, timestamp, serialization, and purity coverage passes.
- [x] Source, editable-install, and normal-wheel behavior agrees without source fallback.
- [x] The protected target, AIO-030, Full Control Center/UI, and historical Task evidence remain untouched.
- [x] Target-safe Task/Workflow, Python syntax, changed-document Markdown, and Git diff checks pass as applicable.
- [x] The Architect final review approves the implementation and evidence.
- [x] The Security final review approves the implementation and evidence.
- [x] A fresh independent Reviewer approves the implementation and evidence.
- [x] `documentation_consistency` passes without waiver.
- [x] `independent_review` passes without waiver.
- [x] No required Quality Gate fails or is skipped; prohibited broad checks are explicitly reported as intentionally skipped.
- [x] Explicit Human architecture, schema, security, trust, lifetime, and final acceptance is recorded before closure.

All 60 criteria are satisfied. The required Human Control approval is recorded,
and the Task is completed.
