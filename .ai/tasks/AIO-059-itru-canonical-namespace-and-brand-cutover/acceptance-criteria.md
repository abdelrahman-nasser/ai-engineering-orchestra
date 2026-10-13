# AIO-059 Acceptance Criteria

## Phase 1: design and inventory

- [x] P1: Exactly the four requested Task artifacts and one canonical specification
  exist; Task YAML conforms to the current schema with truthful in-progress state.
- [x] P2: Baseline HEAD matches; bounded inventory records PRESENT/ABSENT for the
  two root files, categories A-J and every surface's cutover/preserve/compatibility
  disposition, with evidence and display/contract/durable distinctions.
- [x] P3: One target identity is locked: ITRU, `itru` package/distribution/CLI,
  `ITRU_`, `~/.itru`; no hypothetical config migration or source shim is proposed.
- [x] P4: Package/resource/import/wheel move strategy is coherent and unstaged;
  exact outside-inventory paths require subsequent implementation authorization.
- [x] P5: New native Tool ID is `tool::itru-native-repository-file-read::v1`;
  historical read is YES, new legacy binding is NO. Distinct exact new routes,
  preserved retired mappings, restart compatibility and new-work rejection are
  designed without same-route rebind or identity normalization.
- [x] P6: Frozen allowlist includes AIO-001 through AIO-058, AIO-059 cutover
  provenance, incidents/reviews/approvals, Git history, AIO-058 experiments,
  migration hashes, persisted Tool IDs and exact historical regression fixtures.
- [x] P7: v1 STORE_ID/application ID/schema URI/ownership-root exceptions are
  precise, justified, lifetime-bound to protocol compatibility and independently
  reviewable. No duplicate ownership authority or durable rewrite is proposed.
- [x] P8: AIO-059 is last legacy Task; first new ID is ITRU-060 after closure.
  Guard scope, exact patterns, creation-vs-reading rule, anchored allowlist,
  false-positive policy and validation integration are designed, not implemented.
- [x] P9: Bounded 2A-2D, 3A, 3B and final Human-controlled one-commit plan and
  offline/synthetic/safe validation sequence are specified.
- [x] P10: All four current migration bytes match the supplied digests and tracked
  production/tests/history remain unchanged; no forbidden path/catalog/network,
  staging, commit, push or implementation validation was used.
- [x] P11: Six fresh independent read-only perspectives each issue APPROVE:
  Architect, Compatibility/Durable Identity, Packaging/Python, Audit/History,
  Runtime Contract, Process/Validation. Zero blocker and zero high findings remain.
- [x] P12: Documentation consistency and independent-review gates pass for design;
  skips/failures are explicit and Human Phase-2 authorization remains pending.

## Future implementation and closure: not executed in Phase 1

- [x] C1: ITRU is the single living product/project brand with reviewed exact
  historical/protocol exceptions; new behavior emits no unintended legacy names.
- [x] C2: Only `itru/` is canonical; all current production/test/schema-validator
  imports, mocks, dynamic strings, source wrappers and resource loaders use it.
  Public symbol semantics and private module boundaries remain intact; clean
  `import itru` performs no operational I/O or discovery.
- [x] C3: Metadata Name is `itru`; only installed console `itru` targets
  `itru.cli:main`. Real offline editable and setuptools-wheel installs work from
  fresh environments, contain all expected schemas/Roles/four SQL resources,
  and contain no legacy runtime tree or duplicate distribution identity.
- [x] C4: Only `ITRU_VERIFY_DEPTH` controls current runtime. Absent/`"0"`
  permit entry, empty/nonzero values reject, and restoration is exact. The legacy
  variable is inactive, never an alias. No config subsystem or fictional home
  migration is introduced; future root stays `~/.itru`.
- [x] C5: Distinct new route uses only canonical native Tool ID/selector. Legacy
  history reconstructs exactly across restart and original historical retry
  returns unchanged Admission. Same old Run with new Tool fails; route rebind and
  missing historical mapping fail closed. No alias rewrites old identity.
- [x] C6: Forged new legacy-route work cannot create new authority/Binding/Admission
  or acquire/renew/enter/invoke dispatch. Original audit/reconciliation/revocation
  remain available. All trusted creation and execution entry paths are covered.
- [x] C7: v1 ledger metadata, payloads, schema URI graph, fingerprints, ownership
  registry/locks and immutable facts retain compatibility. No duplicated domain
  authority, fact rewrite, migration mutation or Git-history rewrite occurs.
- [x] C8: Migration 0001-0004 hashes match the specification in source and wheel;
  the explicitly authorized `.gitattributes` successor SQL-path rule preserves
  UTF-8/LF and all four digests in the eventual authorized Git index;
  versions 1-4 open/migrate under existing explicit authority and predecessor
  semantics using owned synthetic fixtures, never live historical ledgers.
- [x] C9: No AIO-060+ or other new legacy Task identities are introduced. ITRU-060
  is first after closure; generic historical Task/value reading remains valid.
- [x] C10: Namespace guard passes and its negative/positive fixtures prove precise
  historical exceptions cannot mask new legacy living content or import paths.
- [x] C11: Relevant predecessor contract, registry/resolver, ownership/fencing,
  trust, outbox/lease, JIT, entry/invocation and AIO-058 native containment
  regressions pass with reviewed safe setup. Native bounds/order/ambiguity and
  cleanup semantics remain unchanged; unsafe/default catalog paths are not run.
- [x] C12: Targeted documentation/schema/whitespace checks and packaging evidence
  are offline, use no protected target or catalog enumeration, and report every
  skip/failure. Required missing evidence prevents closure.
- [x] C13: Fresh Phase-3A specialists and Phase-3B independent formal review
  approve final changes; all required gates pass and Human approval is recorded.
  Only subsequently authorized staging and one commit close AIO-059; no push
  or physical repository rename is required for code cutover.

## Human-authorized Phase 2B checkpoint ? 2026-10-12

The latest resume request supersedes C4's original prospective inbound legacy
marker rule: only `ITRU_VERIFY_DEPTH` is active; the old variable is ignored.
Previous phase design criteria are not a claim of overall Task closure.

- [x] B1: Only canonical ITRU native identity is active; old Registration facts
  remain outside active indexes and cannot produce current authority.
- [x] B2: Exact authenticated old lookup/revocation is supported across restart
  without producer/resolver/Binding creation, history rewriting or authority
  refresh; missing/rebound manifests and reused occurrences fail closed.
- [x] B3: Disjoint sealed capabilities, mandatory direct producer gate, exact
  original writer rechecks, revocation-only handling and existing live issuance
  lookup pass adversarial/fault/concurrency tests.
- [x] B4: Legacy outstanding Claim/Lease/Entry/invocation is denied; genuine
  canonical AIO-058 chain, continuation and native bounds still pass.
- [x] B5: CLI/source launcher/installed wheel use `itru`; installed `aio` is
  absent. Only `ITRU_VERIFY_DEPTH` controls the existing marker behavior.
- [x] B6: No config subsystem, durable rewrite, migration changes or public
  signature/result/export widening. Four SQL resources remain byte-identical.
- [x] B7: Final 240 exact focused tests, real offline setuptools 77.0.3 wheel,
  isolated installed imports/resources, AST/public-surface/whitespace checks
  and two fresh independent implementation approvals are recorded.
- [x] B8: Task remains in progress; Phase 2C/closure/Human approval are pending.
  No guard, Task-prefix rule, broad docs cleanup, network, catalog enumeration,
  staging or commit was performed.

## Human-authorized Phase 2C checkpoint: 2026-10-12

- [x] N1: Standard-library test guard validates only the explicit living Git
  manifest; no Task/Workflow catalog, experiments or protected target is read.
- [x] N2: Exact historical allowances bind path, token, semantic scope, line
  digest, count, constrained reason and removal condition; no broad exemption.
- [x] N3: Historical references preserve AIO-001 through AIO-059; new Task IDs
  require ITRU-060 or later, with explicit closure and matching directory for
  candidate creation. Generic historical Task/schema semantics are unchanged.
- [x] N4: README and inventoried living Core/schema/current test examples use
  ITRU identities while frozen durable and truthful historical facts remain.
- [x] N5: All 14 focused tests pass; exact AST/compile, documentary-only schema,
  migration hash, offline Markdown and whitespace checks pass.
- [x] N6: Fresh independent allowlist, living-documentation and Task-prefix
  reviews approve; blocker, high and remaining findings are zero.
- [x] N7: No runtime semantic change, packaged guard, network, history mutation,
  staging or commit occurred. Task remains in progress.
- [x] N8: Phase 2C implementation is complete; Phase 2D, final Quality Gates,
  Phase 3 review, Task closure and final Human approval remain pending.

## Human-authorized Phase 2D checkpoint: 2026-10-12

- [x] D1: Current source and fresh installed artifact use only the canonical
  package/distribution/console; old package, shim and console are absent.
- [x] D2: Real fresh offline setuptools 77.0.3 wheel build and disposable wheel
  install pass; separate offline editable install/import/resources also pass.
- [x] D3: Current Registration/resolution/Binding/invocation use the ITRU Tool;
  historical facts stay separate, exact and incapable of new authority rebound.
- [x] D4: Canonical-only ENV, historical lookup/revocation, safe AIO-058 chain and
  required predecessor selections pass in one current 386-test run.
- [x] D5: Namespace guard, exact 1,106 allowances and prospective Task policy pass;
  inventoried living documentation has no dual canonical identity.
- [x] D6: Source/wheel SQL bytes and frozen durable identities remain exact;
  124 Python AST/compile checks and 22 schema documentary checks pass.
- [x] D7: Locked offline exact Markdown, whitespace and modified-path scope checks
  pass. No network, protected access, history mutation or staging occurred.
- [x] D8: Phase 2 implementation/integrated validation is complete. Phase 3,
  final Quality Gates, Task closure and final Human approval remain pending.

## Final closure reconciliation: 2026-10-13

Human final approval is APPROVE, dated 2026-10-13. C8 staged-index migration
verification passes; C13 review/Gate/approval predicates and closure authorization
are satisfied. All 49 criteria are checked against recorded evidence, with zero
failure or not-applicable disposition. Closure takes effect with the one
authorized local closure commit. Prior phase statements above remain historical
checkpoints, and the accepted original 386-runner limitation is retained in review.
