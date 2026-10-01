# AIO-051 Acceptance Criteria

Checked criteria record only the phase-scoped evidence that has actually
completed. They do not imply completion of any unchecked later review, Quality
Gate, final Human approval, Task closure, staging, or commit criterion.

<!-- markdownlint-disable MD029 -- Criterion IDs remain stable across sections. -->

## Identity, authorization, and governance

1. [x] AIO-051 is a new immutable Task identity titled Trusted Agent Operation Tool Registry and Resolver Foundation.
2. [x] The Task is `in_progress` and Phase 1 is the only authorized phase.
3. [x] Classification is implementation, high Complexity, critical Risk, `critical` Execution Mode, and `architecture-change` Workflow.
4. [x] Direct dependencies are exactly AIO-045 and AIO-047.
5. [x] AIO-036, AIO-037, AIO-038, AIO-041, AIO-042, AIO-043, and AIO-049 are semantic/program context rather than inflated direct dependencies.
6. [x] AIO-050 is an independent trust track, is not a dependency, remains `in_progress` with Phase 1 complete, and is not modified.
7. [x] AIO-049 remains completed and unmodified, AIO-048 remains cancelled, AIO-030 remains parked, and AIO-052 is not created.
8. [x] The AIO-051 Task directory contains exactly `task.yaml`, `context.md`, `acceptance-criteria.md`, and `review.md`.
9. [x] No runtime, test, schema, package, AIO-050, or other non-Task file is created or modified in Phase 1.
10. [x] No implementation, test, validator, package smoke, final Gate, staging, commit, push, merge, release, publication, discovery, real resolution, Admission, dispatch, or invocation occurs in Phase 1.

## Canonical contracts and responsibility boundaries

11. [x] The canonical track term is Trusted Agent Operation Tool Registry and Resolver.
12. [x] The canonical semantic record term is Agent Operation Tool Registration.
13. [x] A Registration denotes configured immutable identity and is not a live Tool, availability fact, invocation descriptor, Binding, or Admission.
14. [x] The existing AIO-045 Binding remains exactly `(run, tool_id)` in canonical order.
15. [x] No route, alias, adapter, revision, retirement, availability, credential, fingerprint, or metadata field is added to the Binding or schema.
16. [x] The existing AIO-047 resolver signature remains `resolve_tool_binding(grant) -> AgentOperationToolBinding | None`.
17. [x] The resolver receives the exact authenticated Grant, not a raw Run, alias, registry revision, selection token, candidate list, or caller Binding.
18. [x] AIO-051 private outcomes do not alter AIO-047 outcomes: `None`/exception becomes `untrusted_tool_binding`, and noncanonical/invalid/mismatched output becomes `invalid_input`.
19. [x] Registration, pre-Run route selection, Binding resolution, Admission, JIT availability, dispatch, and invocation remain separate responsibilities.
20. [x] Trust comes from composition-root construction/injection and exact resolver behavior, never a class shape, caller value, fingerprint, wrapper, or `trusted` flag.
21. [x] Python privacy is ordinary same-process encapsulation, not a claim against malicious code already executing in the trusted process.

## Registration and registry snapshot

22. [x] The private frozen Registration has exactly runtime option, environment, operation, `tool_id`, and closed implementation-selector semantics.
23. [x] Registration has no separate ID/revision, digest, display metadata, config bag, alternate resource/root/glob, lifecycle state, endpoint, command, callable, live handle, availability, credential, or secret.
24. [x] The implementation selector is a closed package-owned non-callable token, never an import path, arbitrary callable, command, executable, endpoint, environment value, entry point, or discovery result.
25. [x] Registration, route, snapshot, selected route, resolved Registration, internal outcomes/results/retries, aliases, and audit values have no public serialized schema.
26. [x] The local registry is one deeply immutable process-local snapshot built atomically from explicit package-owned declarations and exact trusted route configuration.
27. [x] There is no JSON/YAML registry, database, writable registry, live reload, hot swap, external registry service, mutable global, or caller-retained mutable backing map.
28. [x] Snapshot construction validates every exact private value, route, Tool ID, selector, alias, retirement reference, duplicate, and contradiction before publication.
29. [x] Any malformed registration, unknown selector, duplicate route, duplicate/conflicting scoped Tool ID, alias collision/chain/cycle/shadow, or unknown policy target invalidates the whole snapshot.
30. [x] No first-wins, last-wins, precedence, deduplication, overwrite, partial snapshot, fallback snapshot, or best-effort construction exists.
31. [x] Construction failure publishes no resolver and prevents AIO-047 coordinator composition.
32. [x] Concurrent calls observe one immutable snapshot; rebuild after restart is atomic.
33. [x] A snapshot fingerprint is audit/integrity metadata only and is neither authority nor canonical identity.
34. [x] A current snapshot cannot prove that a prior package version was not rewritten; cross-version no-rebind is explicitly a release/supply-chain invariant.
35. [x] Full historical declarations and cross-version fixtures must be retained and reviewed append-only across releases.

## Route, Tool identity, and deterministic history

36. [x] The exact route key is `(runtime_option_id, environment_id, operation_id)` projected only from `grant.run.contract`.
37. [x] Route components and lookup are exact and case-sensitive with no normalization, wildcard, default, prefix, parent-environment, compatibility, operation-family, Provider/model ranking, or fallback.
38. [x] Exactly one permanent historical Registration is allowed per route, and even an equal duplicate invalidates the snapshot.
39. [x] The AIO-045 Tool-ID namespace remains `(runtime_option_id, environment_id, tool_id)`.
40. [x] Within that scope, one `tool_id` denotes one immutable implementation and security-relevant configuration revision forever.
41. [x] Adapter, protocol, endpoint-semantics, containment, operation behavior, or security-relevant configuration changes require a new `tool_id`.
42. [x] Documentation, display, Human alias, and nonsecurity presentation changes outside Registration do not by themselves require a new Tool ID.
43. [x] One exact route maps permanently to exactly one canonical `tool_id`; same-route replacement is forbidden forever.
44. [x] A different `run_id` alone cannot select a different Tool for an unchanged route.
45. [x] The formal append-only function proof establishes same-Run/same-Binding resolution across restart and compatible upgrade.
46. [x] Package compatibility requires every old route mapping to remain byte-for-byte semantically unchanged in the new manifest.
47. [x] Missing historical mapping fails closed and never remaps through another registry, network, checkout, source tree, alias, or fallback Tool.
48. [x] No persistent Run-to-Tool selection store is required under the permanent-route invariant.
49. [x] Same-route upgrade, resolver-enforced new-versus-history retirement, or unencoded post-Run alias selection triggers a stop for persistent-state or contract-change Human review.

## Alias, upgrade, and retirement

50. [x] An optional alias maps only to one complete already registered route and is used strictly before Run construction.
51. [x] Alias, selected-route proof, and alias spelling never enter Run, Grant, Binding, Admission, or a public schema.
52. [x] Alias chains, cycles, duplicate aliases, canonical-ID shadowing, unknown targets, and same-route Tool retargeting are prohibited.
53. [x] Alias retargeting affects only future Runs and must target a distinct complete route already encoded by the new Run.
54. [x] A selectable implementation upgrade appends a new `tool_id` on a new canonical route, normally a new Runtime Option or environment identity.
55. [x] Upgrade requires a new Run, Grant, Binding, and Admission and never mutates existing values.
56. [x] Retirement never deletes, rebinds, or mutates the historical Registration.
57. [x] A separate monotonic pre-Run retirement index rejects new route selection as `tool_retired`.
58. [x] The AIO-047 historical resolver remains total for retained retired registrations so guarded retry/load can reconstruct the original Binding.
59. [x] The unchanged AIO-047 port cannot itself distinguish new Admission from history and therefore does not claim port-level retired-Tool rejection.
60. [x] Canonical upstream composition must create new Runs only from active routes; AIO-051 alone cannot prove that a post-retirement old-route Run was not fabricated.
61. [x] Future dispatch performs a fresh retirement/JIT check and fails closed without Tool substitution.
62. [x] Historical Binding and Admission identity remain unchanged after retirement.

## Resolver, applicability, and non-widening

63. [x] `TrustedAgentOperationToolBindingResolver` implements the unchanged AIO-047 port over the immutable trusted snapshot.
64. [x] It exact-type and intrinsically validates the Grant before route lookup.
65. [x] It constructs `AgentOperationToolBinding(run=grant.run, tool_id=registration.tool_id)` and requires exact input Run object identity plus complete equality.
66. [x] It never accepts caller Binding, Tool ID, alias, Registration, registry, route override, resource, trust flag, candidate list, or fallback choice.
67. [x] It returns an exact canonical Binding only for `resolved`; all private rejections collapse to `None` at the AIO-047 port.
68. [x] Runtime applicability requires exact equality with `grant.run.contract.runtime_option_id`.
69. [x] Environment applicability requires exact equality with `grant.run.contract.environment_id`.
70. [x] Operation applicability requires exact equality with `grant.run.contract.operation_id`; initial support is only `repository_file_read`.
71. [x] Resource remains owned by Operation Requirement/Contract/Run and is absent from route and Registration.
72. [x] Resolver does not inspect, normalize, resolve, replace, prefix, widen, open, or otherwise use the resource.
73. [x] Binding construction preserves the complete Run and cannot change Runtime, Inference Option, environment, operation, resource, Execution Mode, Actor, Role, Task, Workflow, or Stage.
74. [x] Physical containment, reparse handling, file kind, size, encoding, permission, TOCTOU, and opening remain future adapter/JIT responsibilities.
75. [x] Registration and Binding existence make no Tool availability, health, reachability, behavior, containment, permission, or executability claim.
76. [x] Live availability belongs to future dispatcher/adapter JIT checks and can never cause same-Run fallback.
77. [x] A private resolved Registration is process-local, nonauthoritative outside the resolver call, nonserialized, and does not mirror the Binding as a public value.

## First Tool, discovery, secrets, outcomes, and audit

78. [x] The first Tool ID is `tool::aeo-native-repository-file-read::v1` with closed selector `AEO_NATIVE_REPOSITORY_FILE_READ_V1`.
79. [x] Every first-Tool Registration still requires an exact Runtime Option, environment, and `repository_file_read` route; no wildcard is allowed.
80. [x] The first Tool is identity-only in AIO-051; no callable adapter or filesystem-read behavior is implemented.
81. [x] No shell, subprocess, PowerShell, `cmd`, PATH/CLI lookup, import entry point, MCP, Provider, marketplace, filesystem, network, or dynamic discovery exists.
82. [x] No password, token, key, credential, secret value/reference, endpoint, command, or environment dump enters Registration, registry, Binding, Admission, result, audit, diagnostic, or log.
83. [x] The closed private outcome taxonomy covers construction, selection, resolution, duplicate/rebind, applicability, retirement, history, selector, fingerprint, and integrity failures.
84. [x] `tool_retired` is pre-Run/JIT only; AIO-047 historical resolution does not emit it.
85. [x] No outcome claims `historical_tool_unavailable` without a prohibited availability probe; missing mapping is a distinct deterministic failure.
86. [x] Every private outcome has one exact retry disposition, and none permits selecting another Tool for the same Run.
87. [x] Future availability retry is outside the AIO-051 retry taxonomy.
88. [x] Audit material is a pure closed nonsecret value and no durable Journal sink is implemented.
89. [x] Audit never enumerates registry/alias catalogs or exposes full object repr, package paths, callables, selectors, stack traces, commands, endpoints, environment/configuration objects, resources, credentials, or secrets.
90. [x] No new public Tool Registration, registry, route, alias, resolved-registration, result/retry, audit, Binding, or Admission schema is added.
91. [x] The complete 32-scenario matrix is documented and dispatch is `NO` throughout.

## Phase 1 process safety and reviews

92. [x] The command-safety preflight rule and Task-local Validation Safety Matrix exist before any Phase 2 validation.
93. [x] Exact prospective Task-schema, Workflow-schema, registry/resolver tests, AIO-045/AIO-047 regressions, AST, no-shell audit, Markdown, package-smoke, Git, and interpreter categories are recorded.
94. [x] Legacy validators, validator `--help`, broad Task/Workflow validation, catalog enumeration, repository-wide verification, recursive search, broad Markdown, broad test discovery, bare smoke, discovery commands, and unknown commands are prohibited.
95. [x] The fixed Python path is recorded only as an environment fact and must be freshly verified in Phase 2.
96. [x] No symlink, Developer Mode, elevation, or real filesystem-containment evidence is required.
97. [x] The protected-target non-access criterion is explicit, and registering a Tool identity performs no read.
98. [x] Fresh Architect Phase 1 design review approves the exact final artifacts with no blocker or high finding.
99. [x] Fresh Security Phase 1 design review approves the exact final artifacts with no blocker or high finding.
100. [x] Fresh Resolver/Integration Phase 1 review approves the exact final artifacts with no blocker or high finding.
101. [x] Phase 1 has zero unresolved blocker and zero unresolved high-severity finding, and historical resolution is locked.
102. [x] The Phase 1 design lock is complete and the Human checkpoint is prepared.

## Later Phase 2 implementation and technical evidence

103. [x] Separate explicit Human authorization permits AIO-051 Phase 2 only after AIO-050 implementation closes and AIO-051 is freshly rebaselined.
104. [x] The canonical registry/resolver specification is implemented consistently with the permanent-route design.
105. [x] The exact private Registration, snapshot, selection, resolver, outcomes, retries, and audit contracts are implemented without public schemas.
106. [x] The native repository-read Tool identity and selector are registered without implementing a callable adapter.
107. [x] The existing AIO-045 Binding shape/schema and AIO-047 resolver signature/outcomes remain unchanged.
108. [x] Exact registry tests pass for construction, deep immutability, duplicates, aliases, upgrades, retirement, append-only history, fingerprint limits, secrets, and no discovery.
109. [x] Exact resolver tests pass for Grant validation, exact route lookup, Run object preservation, historical reconstruction, port collapse, no widening, and no fallback.
110. [x] Restart and append-only package-upgrade tests prove same historical Run produces the same Binding, while missing/rebound history fails closed.
111. [x] Exact focused AIO-045 and AIO-047 regression evidence passes without real resolution, Admission, dispatch, or invocation.
112. [x] Exact AST, explicit-file no-shell audit, and explicit-path Markdown checks pass.
113. [x] Target-safe package/import evidence passes if packaging changes require it and after complete static preflight.
114. [x] Every Phase 2 command was matrix-authorized before execution and recorded verbatim; protected-target non-access remains certifiable.

## Later Phase 3 review, Gates, and Human control

115. [x] A fresh final Architect review approves the implemented permanent-route and registry design.
116. [x] A fresh final Security review approves the implemented trust, no-rebind, no-widening, no-discovery, and secret boundaries.
117. [x] A fresh final Resolver/Integration review approves AIO-045/AIO-047 compatibility and historical behavior.
118. [x] A fresh independent Reviewer approves the complete current snapshot.
119. [x] The `documentation_consistency` Quality Gate passes or has an explicitly permitted recorded exception.
120. [x] The `independent_review` Quality Gate passes or has an explicitly permitted recorded exception.
121. [x] Final Human architecture, security, history, schema, trust-boundary, and acceptance approval is recorded.
122. [x] Human Task-closure and local-commit authorization is recorded separately before status change, staging, or commit.
