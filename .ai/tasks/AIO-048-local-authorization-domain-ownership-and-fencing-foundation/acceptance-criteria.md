# AIO-048 Acceptance Criteria

Checklist count: 100. Current progress: 94/100.

Cancellation audit: AIO-048 was cancelled by direct Human authorization on
2026-09-23 under the cancellation semantics in
`core/task-specification.md` section 31. Cancellation does not complete
acceptance criteria. Criteria 74, 75, 76, 89, 91, and 100 remain truthfully
unchecked: categorical protected-target non-access is not certifiable; broad
repository/Markdown traversal and non-target-safe checkout-wide validation
occurred; the formal independent outcome remains `CHANGES REQUIRED`; the
`independent_review` Gate remains `FAIL` without waiver; and final Human
implementation acceptance was not approved.

1. [x] A fresh Architect design lock approves the final design before implementation.
2. [x] A fresh Security design review approves the final design before implementation.
3. [x] A fresh Ownership/Storage design review approves the final design before implementation.
4. [x] Canonical ownership terminology and the four-concept ownership family are implemented consistently.
5. [x] Authentication, entitlement, Grant integrity, Tool trust, and domain ownership remain separate.
6. [x] No caller `trusted`, `authenticated`, `verified`, `active`, or `is_owner` value creates authority.
7. [x] Exactly one authoritative external binding exists for each registered local authorization domain.
8. [x] The binding includes the exact opaque authorization-domain ID.
9. [x] The binding includes one canonical absolute local ledger path.
10. [x] The binding includes the immutable ledger-instance ID.
11. [x] The binding includes an exact positive domain generation.
12. [x] The binding has explicit inactive, active, fencing, and fenced state semantics.
13. [x] Windows stable file identity is bound and verified through `FILE_ID_INFO`.
14. [x] The binding registry is external to the Admission database.
15. [x] Registry records are deterministic, canonical, strict, and versioned.
16. [x] Registry creation and state transition evidence are atomic, durable, and fail closed.
17. [x] Malformed, non-canonical, contradictory, duplicate, unknown-version, or corrupt registry state fails closed.
18. [x] The production registry root is internally pinned to the fixed current-user Windows Known Folder location.
19. [x] Provisioning alone creates neither a domain binding nor operational ownership.
20. [x] Registration and activation are explicit separate operations.
21. [x] Operational acquisition never silently activates, relocates, creates, repairs, migrates, or adopts a ledger.
22. [x] A Windows OS-backed exclusive lock keyed by authorization domain is required.
23. [x] The OS lock namespace is independent of ledger and copied-ledger locations.
24. [x] At most one live local owner exists for one authorization domain.
25. [x] A concurrent second same-domain owner receives a typed unavailable/contention outcome without unbounded waiting.
26. [x] The Ownership Capability represents a currently live owner session, not stored data.
27. [x] The Ownership Capability cannot be serialized, pickled, copied, or reconstructed from JSON.
28. [x] Supported public callers cannot directly construct or counterfeit an Ownership Capability; arbitrary same-identity Python code remains outside the v1 threat model.
29. [x] A capability is exact to domain, canonical ledger identity, ledger instance, generation, and owner session.
30. [x] A released, closed, or invalidated capability is unusable.
31. [x] A wrong-domain capability is unusable.
32. [x] A wrong-generation capability is unusable.
33. [x] All four operational AIO-047 Store calls require a live owned session.
34. [x] No check-then-use ownership boolean is accepted.
35. [x] Process death releases OS ownership through kernel handle closure.
36. [x] A replacement process can recover ownership only for the exact same active binding and ledger.
37. [x] Ordinary same-binding crash recovery does not advance domain generation.
38. [x] A PID is never an ownership identity or authority source.
39. [x] Domain generation is exact, positive, durable, and not caller authority.
40. [x] Ledger-instance identity remains immutable from provisioning.
41. [x] Canonical-path mismatch fails closed.
42. [x] Ledger-instance mismatch fails closed.
43. [x] Domain-generation mismatch fails closed.
44. [x] Windows file-identity mismatch or unavailable required identity fails closed.
45. [x] A copied active database at another identity is rejected for same-domain ownership.
46. [x] A moved or alternate-path ledger is rejected and no adoption API exists.
47. [x] Symlink, junction, reparse-point, and path-alias bypasses are rejected for the supported Windows profile.
48. [x] UNC, network, remote, detectable cloud-sync writable, and unsupported filesystem profiles are rejected; undetectable sync avoidance is an operator prerequisite.
49. [x] A stale backup, restore, or substituted ledger cannot silently acquire supported authority.
50. [x] Privileged in-place tamper and administrator rollback limitations are explicit and not overclaimed.
51. [x] Ledger unavailability never triggers automatic failover.
52. [x] No memory-store fallback exists.
53. [x] No alternate-file, copied-ledger, backup, registry, or backend fallback exists.
54. [x] Fencing is explicit, terminal, and forward-only.
55. [x] Fenced or fencing external state can never transition back to active.
56. [x] A fenced SQLite ledger can never reopen operationally through the supported owner path.
57. [x] Every external-registry/SQLite partial-fence order and injected failure leaves the supported path fail closed.
58. [x] Every capability issued before fencing is rejected after fencing starts.
59. [x] The future old-generation Grant rule is documented without changing the eight-field Grant schema.
60. [x] All AIO-047 Admission equality, uniqueness, and authority-provenance semantics remain unchanged.
61. [x] AIO-047 exact historical retry and response-loss recovery remain unchanged.
62. [x] AIO-047 original-issuer revocation identity and serialization semantics remain unchanged.
63. [x] AIO-047 authoritative currentness and clock-watermark semantics remain unchanged.
64. [x] AIO-047 migration, integrity, WAL, FULL-synchronous, and corruption behavior remain unchanged.
65. [x] No Grant Producer, issuer entitlement, signature, or Human-authentication implementation is added.
66. [x] No Tool registry, Tool alias, descriptor, secret broker, or real Tool Resolver is added.
67. [x] No OIDC, Keycloak, or other identity-provider integration is added.
68. [x] No PostgreSQL, distributed ownership, central ownership service, or lease is implemented or claimed.
69. [x] No local-to-Enterprise or same-domain cross-backend migration is implemented or claimed.
70. [x] No dispatch, outbox, delivery, Tool call, Runtime call, Provider call, or invocation is performed.
71. [x] No real authorization domain is registered, activated, acquired, migrated, backed up, or fenced.
72. [x] Every test uses disposable synthetic domains, temporary ledgers, and temporary private test registry roots.
73. [x] No real Grant, Tool Binding, Admission, revocation, or operational authority action occurs.
74. [ ] The protected target remains categorically untouched.
75. [ ] No recursive repository search, Task catalog enumeration, or broad Markdown traversal is used.
76. [ ] No broad, unknown-safety, repository-wide, or non-target-safe validation is run.
77. [x] Fresh separate-process ownership contention tests pass.
78. [x] Fresh hard-exit, lock-release, exact-ledger recovery, and no-generation-bump tests pass.
79. [x] Fresh copied, moved, replaced, and stale-ledger tests pass.
80. [x] Fresh domain, path, instance, generation, state, registry, and file-identity mismatch tests pass.
81. [x] Fresh terminal fencing, partial-failure, crash-window, and reconciliation tests pass.
82. [x] Fresh capability construction, copy, serialization, cross-store, wrong-scope, and counterfeit tests pass.
83. [x] Fresh released-capability, stale-session, fence invalidation, and ABA tests pass.
84. [x] Focused affected AIO-047 regressions pass without semantic weakening.
85. [x] Source, editable-install, and normal-wheel package behavior passes where applicable.
86. [x] A fresh Architect final review approves the actual final implementation and evidence.
87. [x] A fresh Security final review approves the actual final implementation and evidence.
88. [x] A fresh Ownership/Storage final review approves the actual final implementation and evidence.
89. [ ] A fresh independent Reviewer approves the actual final implementation and evidence.
90. [x] `documentation_consistency` passes without waiver.
91. [ ] `independent_review` passes without waiver.
92. [x] Immutable strict binding plus append-only state evidence prevents registry replacement or state rollback through supported APIs.
93. [x] Fencing and fenced markers dominate active evidence under every accepted registry parse.
94. [x] The pinned ledger is a regular local file with exactly one hard link when registered, activated, acquired, and used.
95. [x] Domain locking precedes security-sensitive binding and ledger reads during activate, acquire, migrate, recovery-fence, and other ownership-changing operations.
96. [x] Raw operational SQLite Store construction is gated by package-private trusted-composition authority and is not a supported public bypass, without claiming resistance to arbitrary same-identity Python code.
97. [x] Provision, migration, operational access, backup, and fence each enforce the separately locked administration policy.
98. [x] Ownership loss maps to existing `storage_unavailable`, while counterfeit or incoherent internal authority maps to `integrity_failure`, without changing generic Store outcomes.
99. [x] The Task directory contains exactly the four canonical artifacts and no public Ownership Capability or Binding JSON Schema exists.
100. [ ] Explicit Human architecture, security, ownership, registry, locking, fencing, limitations, and final approval is recorded before closure.
