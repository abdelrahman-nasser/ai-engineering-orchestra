# AIO-044 Acceptance Criteria

Checklist count: 66. Complete at cancellation: 63. Unmet at cancellation: 3.

- [x] A separate non-implementing Architect approves the exact design before implementation.
- [x] A separate Security Reviewer approves the exact security boundary before implementation.
- [x] The canonical term and definition are Agent Operation Tool Binding.
- [x] The binding is immutable, serializable, derived/selected, provider-neutral, and non-authoritative—not a decision, Grant, permission, lifecycle state, or invocation.
- [x] The value contains exactly `run` and `tool_id`, in that order.
- [x] `run` is the complete exact nested Agent Execution Run and is intrinsically validated.
- [x] A bare Run ID is insufficient, and no Run or Contract field is flattened.
- [x] Full `(run, tool_id)` equality defines value equality; no `binding_id` exists.
- [x] `tool_id` is required, exact, opaque, nonempty, case-sensitive, and unnormalized.
- [x] Core neither allocates Tool IDs nor claims their global uniqueness.
- [x] `tool_id` denotes one immutable/version-stable configured implementation revision.
- [x] A mutable alias or display name alone is insufficient as canonical identity.
- [x] No separate revision field is added because the locked `tool_id` itself identifies the immutable revision.
- [x] The external resolver owns the Tool namespace, scoped by the exact Runtime Option and environment bound through the Run.
- [x] The resolver owns configured existence, identity integrity, applicability, and selection.
- [x] A future adapter owns physical resolution, credentials, endpoints, protocol/native translation, containment, and invocation.
- [x] Runtime Operation Capability `present` is not a concrete Tool Binding.
- [x] V1 represents one selected effective binding per Run and adds no collection, inventory, or multi-tool composition.
- [x] Core performs no discovery, probing, enumeration, ranking, fallback, or dynamic reselection.
- [x] Exact Run binding and absence of alternate scope fields prevent silent Contract widening.
- [x] Runtime substitution is impossible without creating a different nested Run.
- [x] Inference Option substitution is impossible without creating a different nested Run.
- [x] Environment substitution is impossible without creating a different nested Run.
- [x] Operation substitution is impossible without creating a different nested Run.
- [x] Resource widening is impossible without creating a different nested Run.
- [x] Execution Mode substitution is impossible without creating a different nested Run.
- [x] Task, Workflow, Stage, Role, and Actor substitution likewise require a different nested Run.
- [x] Actual Tool behavior remains an external trusted-resolver/adapter precondition and is not proven by Core.
- [x] Binding existence grants no permission or authority, consumes no Grant, admits no dispatch, and allows no invocation.
- [x] No Grant field is included; future admission must compare complete `binding.run`, `grant.run`, and fresh expected Run equality.
- [x] Direct construction, schema validity, runtime validity, and serialization prove no Tool existence, trust, availability, executability, or semantic operation match.
- [x] The direct module exposes only the frozen binding, finding, validation-result types, and intrinsic validator; no fake preparation/resolution API or package-root re-export is added.
- [x] Intrinsic validation proves only exact binding type, valid nested Run, exact nonempty Tool ID, and immutable value semantics.
- [x] Wrong types and invalid fields produce an atomic invalid result with findings and no binding.
- [x] Values/results are frozen, and validation mutates neither nested values nor caller input.
- [x] Validation is pure and deterministic and uses no filesystem, network, subprocess, environment discovery, clock, or randomness.
- [x] No registry, persistence, database, cache, queue, store, ledger, or transaction is added.
- [x] No Grant authentication, currentness, revocation, consumption, or replay protection is added or claimed.
- [x] No admission, dispatch, invocation, Run lifecycle, result, error, event, or telemetry is added.
- [x] The Draft 2020-12 schema is closed and contains exactly the two required properties.
- [x] The schema references the canonical packaged Run schema and resolves its transitive Contract reference offline.
- [x] Missing, mismatched, or unregistered schema resources fail closed without network, CWD, or source-checkout fallback.
- [x] Schema and runtime responsibilities remain explicitly separated; neither proves Tool existence.
- [x] Serialization round-trip preserves exact equality only and proves neither Tool existence nor authority.
- [x] Structural schema fixtures cover the valid shape, required fields, types, closure, and nested Run reference.
- [x] Semantic fixtures cover intrinsic Run/Tool-ID semantics without external Tool checks.
- [x] Execution/security extra fields—including adapter, Provider, endpoint, command, payload, credential, Grant, consumption, admission, and result fields—are rejected.
- [x] Tests individually mutate all eleven Contract fields plus `run_id` and prove exact binding inequality/no substitution.
- [x] Tool-ID tests cover valid opaque values, empty/wrong types, case sensitivity, whitespace under locked nonempty semantics, and immutable-version identity documentation.
- [x] Security tests cover Runtime, Inference, environment, operation, resource, Execution Mode, actor, and role substitution attempts.
- [x] Static and dynamic guards cover no I/O, discovery, clock, randomness, persistence, Grant consumption, dispatch, or invocation.
- [x] Focused tests cover valid/invalid results, atomicity, determinism, nonmutation, immutability, and serialization.
- [x] AIO-036 behavior remains unchanged.
- [x] AIO-037 behavior remains unchanged.
- [x] AIO-041 behavior remains unchanged.
- [x] AIO-042 behavior remains unchanged.
- [x] AIO-043 behavior remains unchanged.
- [x] Source, editable-install, and normal-wheel behavior agree.
- [x] Wheel contents, external-project import, installed offline nested-schema resolution, and absence of source fallback are verified.
- [ ] Exactly four AIO-044 Task artifacts exist; protected target, AIO-030, Full UI, historical Tasks, credentials, generated files, and vendor files remain untouched.
- [ ] Exact Task/Workflow validation, Python syntax, exact changed-document Markdown lint, and `git diff --check` pass; prohibited broad checks are reported only as intentionally skipped.
- [x] Architect final review approves the final implementation and evidence.
- [x] Security final review approves immutable identity, resolver trust, non-widening, non-discovery, non-authority, and non-execution boundaries.
- [x] A fresh independent Reviewer approves after inspecting actual changes and validation evidence.
- [x] `documentation_consistency` and `independent_review` both pass without waiver; no required Gate fails or is skipped.
- [ ] Explicit Human architecture, schema, immutable-tool-identity, trusted-resolver, no-widening/security, and final acceptance approval is recorded before closure.

At audited cancellation, criteria 60 and 61 remain unchecked and unsatisfied
because the accidental legacy broad-smoke path prevents categorical
protected-target non-access and makes the all-broad-checks-skipped assertion
false. Criterion 66 remains unchecked and unmet because Human cancellation
authorization is not final implementation acceptance. Cancellation does not
satisfy, waive, or reclassify any of these criteria, so the historical result
remains 63/66.
