# AIO-050 Acceptance Criteria

Checked Phase 1 criteria establish the design and process-safety lock only.
They are not implementation, test, final-review, Quality Gate, or final Human-
approval evidence.

<!-- markdownlint-disable MD029 -- Criterion IDs remain stable across sections. -->

## Identity, authorization, and governance

1. [x] AIO-050 is a new immutable Task identity titled Authenticated Agent Execution Authorization Grant Producer Foundation.
2. [x] The Task is `in_progress` and Phase 1 is the only authorized phase.
3. [x] Classification is implementation, high Complexity, critical Risk, `critical` Execution Mode, and `architecture-change` Workflow.
4. [x] Direct dependencies are exactly AIO-043, AIO-047, and AIO-049.
5. [x] AIO-039 through AIO-042 and Human Control are semantic context rather than inflated direct dependencies.
6. [x] AIO-049 remains completed and unmodified, AIO-048 remains cancelled, AIO-030 remains parked, and AIO-051 is not created.
7. [x] The AIO-050 Task directory contains exactly `task.yaml`, `context.md`, `acceptance-criteria.md`, and `review.md`.
8. [x] No runtime, test, schema, package, or other non-Task file is created or modified in Phase 1.
9. [x] No implementation, test, validator, package smoke, final Gate, staging, commit, push, merge, release, or publication is performed in Phase 1.
10. [x] The protected target is not accessed by any authorized or executed AIO-050 command, and categorical non-access remains certifiable.

## Canonical contract and responsibility boundaries

11. [x] The canonical term is Agent Execution Authorization Grant Producer.
12. [x] The existing AIO-043 eight-field Grant and its schema remain unchanged.
13. [x] No signature, domain-generation, trusted, authenticated, state, or extension field is added to the Grant.
14. [x] Principal authentication, issuer entitlement, Grant construction, Grant-presentation authentication, currentness, revocation, consumption, Admission, dispatch, and invocation remain separate responsibilities.
15. [x] All mandatory trust inequalities are stated explicitly.
16. [x] AIO-039 evidence, Human Control, approval prose, policy text, provenance, and direct Grant construction cannot manufacture an authenticated Grant.
17. [x] AIO-047 remains the canonical currentness, revocation-ordering, consumption, and Admission boundary.
18. [x] The AIO-047 `authenticate_grant` port signature remains unchanged.
19. [x] AIO-049 ownership semantics and supported owned coordinator surfaces remain unchanged.
20. [x] AIO-051 Tool identity, resolution, availability, and invocation remain outside AIO-050.

## Principal, Human approval, policy, and entitlement

21. [x] The local profile uses a stable opaque installation-scoped Human principal ID whose protected SID binding and any persistence are owned by the trusted identity adapter, not the Producer or AIO-049.
22. [x] SID is identity evidence only, not entitlement and preferably not the public issuer ID.
23. [x] The AIO-049 ownership registry is explicitly not an identity registry.
24. [x] Caller principal IDs, SIDs, booleans, and look-alike proof objects establish no authentication.
25. [x] The locked `AuthenticatedIssuerPrincipal`, `AuthenticatedHumanApproval`, and `AuthenticatedPolicyDecision` types are configured-adapter outputs that are private, process-local, exact-adapter/epoch-bound, Producer/session-bound, nonserializable, and noncopyable where practical.
26. [x] Task-level Human Control is governance evidence and is distinct from operational action approval.
27. [x] The private Human approval proof binds the exact principal, complete Run, full domain identity/generation, exact session and Producer/adapter epoch, positive decision, validity interval, approval session, provenance, and any shorter lifetime.
28. [x] Any Run, principal, domain, generation, session, epoch, decision, validity, or approval-session mismatch rejects issuance.
29. [x] The private policy decision binds an authenticated policy principal, complete Run, full domain identity/generation, exact session and Producer/adapter epoch, allow/deny result, validity interval, policy revision, provenance, and any shorter lifetime.
30. [x] Policy denial is typed, Human and policy channels never fall back to each other, and no rule, language, database, delegation, quorum, or general policy engine is introduced.
31. [x] Exact entitlement is the conjunction of the complete Run, live ownership, full domain identity/generation, authenticated enabled issuer authority, immutable configured domain entitlement, and one exact positive Human or policy decision.
32. [x] No duplicate entitlement-scope object copies individual Run fields.
33. [x] Team/Enterprise identity mechanisms are documented only as future adapters.

## Ownership, generation, time, and Grant identity

34. [x] The exact `AgentExecutionAuthorizationGrantProducer.produce(...)`/`close()` surface and private `_compose_agent_execution_authorization_grant_producer(...)` factory are locked; composition creates exactly one Producer/paired-port/registry per exact live Owned Session and rejects a second.
35. [x] AuthorizationDomainIdentity, SID, PID, ledger path, generation, and `is_owner` alone are insufficient authority.
36. [x] Issuance uses a fresh AIO-049 operation lease across proof checks, reservation, construction, registration, clean provider post-check, and clean lease exit before result publication.
37. [x] No presentation may escape before the issuance lease exits cleanly.
38. [x] The private presentation binds exact Producer instance, Owned Session instance, full domain identity, issuer-state epoch, and exact Grant.
39. [x] Close, loss, fencing, a new owner session, or a generation change prevents new issuance and makes outstanding presentations unusable because the supported outer Owned Session gate rejects before the port/Store.
40. [x] Historical Admissions remain immutable after ownership or issuer-state changes.
41. [x] `domain_generation` remains private context and is not added to the Grant.
42. [x] Grant IDs encode 256 OS-CSPRNG bits, giving 256-bit entropy and an approximately 128-bit birthday-collision security bound; UUIDv4 is not the locked format.
43. [x] Session-local collision detection permits bounded internal regeneration before publication and otherwise fails closed without rebind.
44. [x] Absolute mathematical Grant-ID non-reuse across restart is not claimed without durable allocation state.
45. [x] Under the issuance lease, the Producer samples one injected trusted UTC clock exactly once and uses that same instant for half-open principal/proof validity (`valid_from <= issued_at < valid_until`) and Grant `issued_at`, with no fallback.
46. [x] Domain issuance policy supplies explicit positive default and maximum lifetimes plus a policy revision.
47. [x] A proof validity window is an issuance window rather than an implicit Grant-expiry cap; a trusted proof may carry only a shorter positive Grant duration, and callers cannot independently supply duration, issuance time, or absolute expiry.
48. [x] Clock failure, naive/non-UTC time, conversion loss, overflow, zero/negative lifetime, and invalid ordering fail closed.
49. [x] AIO-047 independently owns admission-time currentness, clock non-regression, and revocation ordering.

## Presentation and AIO-047 integration

50. [x] The exact private term is Issued Agent Execution Authorization Grant and its locked Python type name is `IssuedAgentExecutionAuthorizationGrant`.
51. [x] The presentation is process-local, has no public constructor or secret token, is nonserializable/noncopyable, and is exact-object-, Producer/epoch-, session/identity-, issuer-state-, and eight-field-Grant-integrity-bound.
52. [x] The presentation has no public schema, signature field, trusted flag, or authenticated flag.
53. [x] The paired port rejects raw/direct Grants, look-alikes, serialized/copied presentations, foreign Producers, wrong session/domain/generation bindings, tampering, and disabled issuer epochs; the outer gate rejects stale-session use, while `produce(...)` rejects expired or foreign-adapter proofs at its single time sample.
54. [x] A valid exact live presentation returns the exact canonical Grant through the unchanged AIO-047 port.
55. [x] Port success, not wrapper spelling or fields, establishes Grant-presentation trust.
56. [x] The port is private to the exact session-owned coordinator and is invoked under AIO-049's already-held complete-operation lease; it neither observes a lease witness nor independently proves liveness, and standalone invocation is unsupported/non-operational.
57. [x] The presentation never enters AIO-047 Store requests or serialization.
58. [x] Authentication does not decide currentness, revocation, or consumption and permits repeated exact AIO-047 retry only while the same presentation and Producer/session epoch remain live.
59. [x] Local cryptographic Grant signatures are unnecessary under the locked same-process assumptions.
60. [x] Failure of any same-process assumption requires an architecture stop and Human review rather than silent widening.

## Concurrency, restart, disablement, and retry

61. [x] One atomic process-local registry scoped across the exact session serializes issuance by `(authorization_domain_id, run_id)` and retains the complete Run and normalized request; it is not bypassable by another Producer object.
62. [x] At most one new Grant and one presentation are published for one Run within the bounded Producer/session lifetime.
63. [x] An exact same-process retry returns the identical presentation as `existing_exact_issuance`; a different proof/lifetime is `run_already_issued`, a same-ID/different-Run rebound is `run_identity_conflict`, and neither returns a presentation.
64. [x] An unambiguous pre-publication failure releases its reservation, while ambiguity after reservation or any possible publication installs a non-evictable `run_issuance_conflict` tombstone and requires a new Run.
65. [x] Producer restart invalidates every outstanding presentation and process-local issuance record.
66. [x] New Run after restart is a trusted-composition rule and bounded limitation, not a cross-restart guarantee provable without durable issuance state.
67. [x] AIO-050 does not claim cross-restart authentication, exact retry, or authoritative load for an old ephemeral presentation.
68. [x] AIO-047 historical Admission remains immutable even when AIO-050 cannot reauthenticate the old presentation after restart.
69. [x] No Producer database or durable unconsumed Grant store is introduced.
70. [x] Issuer-state transitions and checks have explicit serialization: disable-first rejects; port-check-first may let that in-flight coordinator continue; later re-enable changes epoch and never revives an old presentation; historical Admission remains unchanged.
71. [x] Presentation replay before Admission is left to AIO-047's atomic consumption rather than a mutable one-shot wrapper flag.
72. [x] The exact four-field Production Result invariant and every closed outcome's aggregate retry disposition/presentation rule are locked; fresh-session paths replace principal and same-channel authority proofs, closed-Producer paths also require a new Run, and no boolean or generic retry exists.

## Audit, revocation, schemas, and exclusions

73. [x] Producer audit material is a pure structured result built before publication, is nonsecret and non-authoritative, and has no sink side effect or issued-but-audit-failed ambiguity.
74. [x] Audit material covers outcome, issuer, domain identity/generation, Run correlation, Grant identity, provenance, times, and lifetime-policy revision when available.
75. [x] Passwords, tokens, private keys, bearer material, approval-session secrets, and adapter secrets never enter Grants, presentations, audit, diagnostics, Task artifacts, or logs.
76. [x] AIO-050 implements no durable Execution Journal; future Journal work owns persistence.
77. [x] Original-issuer revocation authentication is a distinct future seam requiring fresh original-principal authentication, live ownership, exact Grant/domain, intent, and provenance; AIO-050 does not make the AIO-047 revocation path operational.
78. [x] A presentation alone cannot authorize revocation, and AIO-050 Phase 2 does not implement general revocation authority.
79. [x] No new public Producer, presentation, principal, approval, policy-decision, audit, or retry schema is introduced.
80. [x] The explicit exclusions cover Tool work, dispatch, invocation, UI, PostgreSQL, remote handoff, signatures, key management, identity federation, policy engine, persistent issuance, and Admission redesign.

## Phase 1 process safety and design reviews

81. [x] The command-safety preflight rule and Task-local Validation Safety Matrix exist before any Phase 2 validation.
82. [x] Exact prospective Task-schema, Workflow-schema, test, AST, Markdown, package-smoke, Git, and interpreter categories are recorded.
83. [x] Legacy validators, validator `--help`, broad Task/Workflow validation, repository-wide verification, recursive search, broad Markdown traversal, bare smoke, broad test discovery, and unknown commands are prohibited.
84. [x] The exact fixed Python path is recorded only as an environment fact and must be freshly verified in Phase 2.
85. [x] No symlink privilege, Developer Mode, or elevation requirement is inherited from AIO-049.
86. [x] The matrix covers all 20 mandatory scenarios plus concurrency, sequential retry, Run-ID rebound, duplicate Producer, close, foreign/expired proof, disablement linearization, ID-source exhaustion, and audit-construction invariants; dispatch is `NO` throughout.
87. [x] Fresh Architect Phase 1 design review approves the exact final artifacts with no blocker or high finding.
88. [x] Fresh Security Phase 1 design review approves the exact final artifacts with no blocker or high finding.
89. [x] Fresh Ownership/Integration Phase 1 design review approves the exact final artifacts with no blocker or high finding.
90. [x] Phase 1 has zero unresolved blocker and zero unresolved high-severity finding.
91. [x] The Phase 1 design lock is complete and the Human Phase 2 checkpoint is prepared.

## Later Phase 2 implementation and technical evidence

92. [x] Separate explicit Human authorization permits Phase 2 after AIO-051 Phase 1 is also locked.
93. [x] The canonical Producer specification is implemented consistently with the locked design.
94. [x] The Producer module implements the exact approved API, typed outcomes, retry dispositions, private proofs, presentation, issuance guard, audit material, and AIO-047 port.
95. [x] Any optional Windows local issuer-identity adapter receives separate scope confirmation and implements only the approved bounded identity model; no optional adapter was authorized or created in Phase 2.
96. [x] The existing Grant schema, AIO-047 port signature, and AIO-049 authority semantics remain unchanged.
97. [x] Exact Producer tests pass for authentication, entitlement, proof binding, ID, time, lifetime, concurrency, restart, disablement, fencing, integrity, audit, and retry behavior.
98. [x] Exact AIO-043 regression evidence passes.
99. [x] Exact focused AIO-047 integration regression evidence passes without real Admission or dispatch.
100. [x] Exact focused AIO-049 ownership regression evidence passes.
101. [x] Exact AST and explicit-path Markdown checks pass.
102. [x] Statically reviewed target-safe package/import evidence passes if package changes require it.
103. [x] No real Human or policy authentication, Grant issuance, Grant consumption, Admission, Tool resolution, dispatch, invocation, or protected-target access occurs in validation.
104. [x] Every Phase 2 command was matrix-authorized before execution and recorded verbatim.

## Later Phase 3 review, Gates, and Human control

105. [x] A fresh final Architect review approves the implemented design.
106. [x] A fresh final Security review approves the implemented trust boundary.
107. [x] A fresh final Ownership/Integration review approves live-session and AIO-047 composition.
108. [x] A fresh independent Reviewer approves the complete current snapshot.
109. [x] The `documentation_consistency` Quality Gate passes or has an explicitly permitted recorded exception.
110. [x] The `independent_review` Quality Gate passes or has an explicitly permitted recorded exception.
111. [x] Final Human architecture, security, schema, trust-boundary, and acceptance approval is recorded.
112. [x] Human Task-closure and local-commit authorization is recorded separately before status change, staging, or commit.
