# AIO-047 Acceptance Criteria

Checklist count: 105.

1. [x] A fresh Architect design lock approves the final design before implementation.
2. [x] A fresh Security design review approves the final design before implementation.
3. [x] A fresh Storage/Atomicity design review approves the final design before implementation.
4. [x] The canonical term is Agent Execution Dispatch Admission.
5. [x] The immutable, serializable, historical, positive authorization-consumption category is explicit.
6. [x] The canonical definition preserves the durable-by-authoritative-store provenance boundary.
7. [x] Admission contains exactly `grant`, `tool_binding`, and `decision_time` in that order.
8. [x] No Admission ID is introduced.
9. [x] No status, state, lifecycle, attempt, result, error, lease, claim, or metadata field is introduced.
10. [x] The complete Agent Execution Authorization Grant is nested.
11. [x] The complete Agent Operation Tool Binding is nested.
12. [x] `decision_time` is required and store-owned.
13. [x] Grant composite identity is the natural Admission identity.
14. [x] Authorization-domain/Run uniqueness is a separate durable constraint.
15. [x] Full representation equality is Grant, Tool Binding, and decision time.
16. [x] New Admission requires exact Grant/Binding/fresh expected Run equality.
17. [x] Fresh Run reconstruction reuses `grant.run.run_id`.
18. [x] Intrinsic validation checks exact value type.
19. [x] Intrinsic validation delegates complete Grant validation.
20. [x] Intrinsic validation delegates complete Tool Binding validation.
21. [x] Intrinsic validation checks exact Grant/Binding Run equality.
22. [x] Intrinsic validation checks decision-time syntax and calendar validity.
23. [x] Intrinsic validation checks static half-open currentness coherence using parsed instants.
24. [x] Intrinsic validation does not claim authentication, trust, revocation state, commit, or provenance.
25. [x] Direct construction and serialization remain explicitly non-authoritative.
26. [x] Authoritative provenance comes only from the configured store/service boundary.
27. [x] The Admission JSON Schema is a closed exact three-property Draft 2020-12 object.
28. [x] Schema references to Grant, Binding, Run, and Contract resolve only from packaged offline resources.
29. [x] Missing, mismatched, or unknown schema resources fail closed without network or source fallback.
30. [x] The coordinator/store responsibility split is canonical and explicit.
31. [x] The coordinator defines typed Grant-producer and Tool-resolver trust handoffs without trust booleans.
32. [x] New Admission recomputes AIO-040 from newly collected parent values.
33. [x] Caller-serialized `satisfied` prerequisite results are not treated as authoritative provenance.
34. [x] The coordinator freshly resolves Execution Mode and reconstructs Contract and Run.
35. [x] The store protocol is backend-neutral and contains no SQLite SQL in its semantic contract.
36. [x] The store owns authorization-domain binding and authoritative history classification.
37. [x] The store owns authoritative currentness for new Admission.
38. [x] The store owns revocation serialization.
39. [x] The store owns Grant and authorization-domain/Run uniqueness.
40. [x] Grant consumption and Admission insertion are one indivisible durable state change.
41. [x] Exact historical retry returns the original Admission after required trust and integrity checks.
42. [x] Historical retry does not resample time, reevaluate expiry/revocation, or recollect prerequisites.
43. [x] Currentness uses `issued_at <= decision_time < expires_at` over parsed instants.
44. [x] Decision time is canonical UTC and never request supplied.
45. [x] The clock is sampled once after conflicting operations enter authoritative serialization.
46. [x] Clock failure fails closed with no fallback.
47. [x] Clock regression fails closed with no clamp or substitution.
48. [x] Zero implicit clock skew is applied.
49. [x] Per-domain decision-time non-regression is canonical while watermark storage remains backend-private.
50. [x] Original-issuer v1 revocation is implemented as a store operation.
51. [x] Revocation uses an immutable durable internal tombstone retaining the complete Grant.
52. [x] Revocation identity uses the complete Grant composite identity, never bare `grant_id`.
53. [x] Revocation-first rejects new Admission.
54. [x] Admission-first preserves historical Admission and records later revocation.
55. [x] Post-Admission revocation never mutates the Admission.
56. [x] Typed positive, rejection, coordinator, and infrastructure/indeterminate result families are defined.
57. [x] Retry guidance distinguishes exact retry, temporal retry, remediation, and permanent rejection.
58. [x] Operational Admission/revocation commit-unknown requires exact retry against the same authoritative ledger; administrative ambiguity uses typed same-target reconciliation.
59. [x] No request-bound durable denial receipts are introduced.
60. [x] Successful Admissions, revocations, and temporal watermark state are the durable security records.
61. [x] The official local SQLite backend is canonical and packaged.
62. [x] The SQLite backend uses one dedicated security ledger per authorization-domain ownership context.
63. [x] Only trusted local filesystem placement is supported.
64. [x] Multi-process same-host use is supported and multi-machine use is explicitly unsupported.
65. [x] WAL, FULL synchronous behavior, foreign keys, normal locking, and explicit writer serialization are enforced.
66. [x] Busy timeout and retryable busy behavior are explicit.
67. [x] No memory, alternate-file, temporary-store, domain-switch, or recreation fallback exists.
68. [x] Provisioning/migration is separate from operational open.
69. [x] Normal Admission calls do not silently create or migrate authority state.
70. [x] The production schema is new and is not the AIO-046 experimental DDL promoted unchanged.
71. [x] Store/application identity, domain, schema version, ledger instance, activation, watermark, and revocation-completeness metadata are explicit.
72. [x] Migration resources are forward-only, explicit, ordered, and checksum validated.
73. [x] One migration owner and fail-closed dirty/partial migration behavior are enforced.
74. [x] Unsupported newer schemas fail closed and downgrade is unsupported.
75. [x] Malformed metadata and impossible migration history fail closed.
76. [x] Missing required tables, indexes, constraints, or triggers fail closed.
77. [x] Corrupt databases, foreign-key/integrity failures, and schema drift fail closed.
78. [x] Malformed payloads, nested decode failures, and identity/payload mismatch fail closed.
79. [x] Local ACL and integrity checks are not claimed as malicious-administrator tamper resistance.
80. [x] Active WAL backup requires a validated SQLite-consistent snapshot mechanism.
81. [x] Raw active main-file copy is unsupported.
82. [x] A snapshot created through the supported backup path is permanently fenced and has no same-domain restore/reactivation path.
83. [x] Local ledger identity and one-way activation/fencing state are represented and enforced.
84. [x] Local fencing is not claimed to prevent two manually copied ledgers from both activating.
85. [x] Cross-backend migration and PostgreSQL are not implemented or claimed.
86. [x] Exact request equality is complete Grant plus complete Tool Binding with no new idempotency key.
87. [x] Grant identity rebound, changed Binding, and second Grant/same Run produce deterministic conflicts.
88. [x] A backend-neutral conformance suite covers authoritative lookup, exact retry, conflicts, currentness, revocation, uniqueness, and failure behavior.
89. [x] Spawned-process same-request and conflicting-request contention is safe.
90. [x] Busy, unavailable, crash, response-loss, commit-unknown, and fresh-process restart behavior is validated.
91. [x] Provisioning, migration, checksum, newer-schema, dirty-state, corruption, payload, backup, and fencing behavior is validated.
92. [x] Only disposable synthetic temporary databases, Grants, Bindings, domains, and resources are used.
93. [x] No real Grant is consumed, real Tool resolved, real Admission created, dispatch performed, or Tool invoked.
94. [x] Permission, Runtime/Inference, and Tool-mapping TOCTOU limitations remain explicit.
95. [x] Admission may be a future dispatch-intent source but no delivery lifecycle is added.
96. [x] Authorization-consumption replay protection is not represented as invocation replay protection.
97. [x] Relevant AIO-040 through AIO-046 behavior remains preserved by focused regressions.
98. [x] Schema and migration resources work from source, editable installation, and normal wheel installation without external fallback.
99. [x] The protected target remains categorically untouched by AIO-047 operations.
100. [x] AIO-044 remains cancelled and untouched, AIO-030 remains parked, and Full UI remains untouched.
101. [x] Strict target-safe process rules are followed without broad or unknown-safety validation.
102. [x] Fresh Architect, Security, and storage/atomicity final reviews approve the actual final implementation.
103. [x] A fresh independent Reviewer approves the actual final implementation and evidence.
104. [x] `documentation_consistency` and `independent_review` pass without waiver.
105. [x] Explicit Human architecture, schema, provenance, security, storage, migration, claim-boundary, and final approval is recorded before closure.
