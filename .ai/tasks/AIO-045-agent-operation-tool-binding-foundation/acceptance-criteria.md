# AIO-045 Acceptance Criteria

Checklist count: 70.

- [x] A fresh non-implementing Architect approves the exact AIO-045 design before implementation.
- [x] A separate Security Reviewer approves the exact AIO-045 trust boundary before implementation.
- [x] AIO-045 explicitly replaces cancelled AIO-044 without depending on it.
- [x] No AIO-044 acceptance, review, Gate, or test evidence is reused as AIO-045 evidence.
- [x] The canonical term is Agent Operation Tool Binding.
- [x] The Binding is an immutable, serializable, provider-neutral derived/selected value.
- [x] The Binding contains exactly `run` then `tool_id`.
- [x] `run` is one complete exact Agent Execution Run.
- [x] A bare `run_id` is insufficient to establish the exact Contract binding.
- [x] `tool_id` is required, exact, opaque, nonempty, case-sensitive, and unnormalized.
- [x] Core does not generate or allocate Tool IDs.
- [x] A Tool ID identifies one immutable configured implementation revision.
- [x] A mutable alias is insufficient unless permanent non-rebinding is guaranteed externally.
- [x] The external configured runtime/tool resolver owns the Tool-ID namespace.
- [x] The Tool namespace is scoped by the nested Run's exact Runtime and environment.
- [x] No `binding_id` or other instance/lifecycle identity is added.
- [x] No Run or Contract fields are flattened at Binding top level.
- [x] No alternate or duplicated operation, resource, or other action field is added.
- [x] No adapter, Provider, model, endpoint, command, payload, arguments, or credentials are added.
- [x] AIO-037 Runtime capability present is explicitly not a Tool Binding.
- [x] Core performs no Tool discovery, probing, resolution, inventory, ranking, fallback, or reselection.
- [x] The external trusted resolver boundary and its responsibilities are explicit.
- [x] The future adapter boundary and its responsibilities are explicit.
- [x] Exact `binding.run` equality prevents Binding-level widening of the Run.
- [x] Runtime substitution is unsupported.
- [x] Inference Option substitution is unsupported.
- [x] Environment substitution is unsupported.
- [x] Operation substitution is unsupported.
- [x] Resource widening is unsupported.
- [x] Execution Mode substitution is unsupported.
- [x] Actor and Role substitution are unsupported.
- [x] Tool Binding is not Permission or a Permission Decision.
- [x] Tool Binding is not authorization.
- [x] Tool Binding is not a Grant and contains no Grant field.
- [x] No Grant consumption or security-state mutation is introduced.
- [x] No currentness or revocation evaluation is introduced.
- [x] No replay-protection claim or mechanism is introduced.
- [x] No dispatch admission or readiness decision is introduced.
- [x] No dispatch, Tool invocation, Agent execution, result, event, error, or telemetry is introduced.
- [x] Direct construction does not prove Tool existence, resolver provenance, or operational trust.
- [x] Intrinsic validation is pure, deterministic, exact-type robust, and supplied-data-only.
- [x] Invalid validation is atomic with nonempty findings and no normalized Binding.
- [x] Binding, findings, and validation results are frozen immutable values.
- [x] Construction and validation use no clock.
- [x] Construction and validation use no randomness or generated identity.
- [x] No registry, persistence, database, cache, queue, store, history, outbox, or transaction is introduced.
- [x] The Draft 2020-12 schema is closed and has exactly two required properties.
- [x] The schema reuses the packaged canonical Run schema and its transitive Contract schema offline.
- [x] Missing, mismatched, unknown, or unregistered schema resources fail closed without network or source fallback.
- [x] Serialization round-trip preserves exact equality without proving Tool existence, resolver trust, authority, or admission.
- [x] Extra identity, security, adapter, execution, lifecycle, and result fields are rejected.
- [x] AIO-036, AIO-037, AIO-041, AIO-042, and AIO-043 public behavior remains unchanged.
- [x] Fresh AIO-045-focused tests pass.
- [x] Fresh exact adjacent regression tests pass with an actual AIO-045 evidence count.
- [x] Fresh package-content and installed-package tests pass.
- [x] Editable installation passes outside the checkout without source fallback.
- [x] A normal wheel installation passes outside the checkout without source fallback.
- [x] Exact target-safe AIO-045 Task validation passes without executing a broad legacy validator.
- [x] Exact target-safe `architecture-change` Workflow validation passes without catalog enumeration.
- [x] During AIO-045, every prohibited broad verification command is intentionally skipped.
- [x] During AIO-045, the protected target is not accessed by any authorized or observed command.
- [x] AIO-044 and all other historical Tasks remain unmodified.
- [x] AIO-030 remains untouched.
- [x] Full Control Center/UI and read-model tracks remain untouched.
- [x] A fresh Architect final review approves the implemented design and evidence.
- [x] A fresh Security final review approves the implemented trust boundary and evidence.
- [x] A genuinely independent Reviewer approves the AIO-045 worktree and evidence.
- [x] The `documentation_consistency` Gate passes without waiver.
- [x] The `independent_review` Gate passes without waiver.
- [x] Explicit Human architecture, schema, immutable-identity, resolver, no-widening, security, and final approval remains required before closure.

No criterion is satisfied merely by AIO-044 history or evidence. AIO-045 remains
independent of AIO-044 evidence. The Human explicitly approved criterion 70 on
2026-09-23 after all non-Human criteria and both Gates passed. All 70/70
criteria are complete, and AIO-045 is `completed`.
