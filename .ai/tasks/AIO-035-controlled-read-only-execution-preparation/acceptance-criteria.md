# AIO-035 Acceptance Criteria

Checklist count: 33.

- [x] A separate non-implementing Security Reviewer approves the no-I/O design,
  exact API, vocabularies, validation, scope, freshness, default-deny behavior,
  and exclusions before implementation and confirms no generic permission or
  authorization contract is required.
- [x] Exactly one provisional abstract operation is supported:
  `repository_file_read`.
- [x] The operation remains separate from every concrete tool, API, provider,
  adapter, and implementation identity.
- [x] The controlled requirement resource is one exact canonical
  repository-relative Markdown path: `workflows/README.md`.
- [x] Unsafe, malformed, alternate-root, broad, directory, and non-Markdown
  resource forms are rejected through lexical validation only.
- [x] The harness and controlled-action path never open, read, stat, hash,
  existence-check, or filesystem-resolve the target; explicitly required
  repository-wide validation remains external to that action path.
- [x] The full AIO-034 candidate result must be valid and coherent, and only a
  `satisfied` candidate may contribute to `potentially_executable`.
- [x] Requirement, capability, permission, and authorization remain separate
  facts and are not collapsed into a generic allowed flag.
- [x] Capability evidence is scoped exactly to candidate Runtime plus operation.
- [x] Permission evidence is scoped exactly to Runtime, environment, operation,
  and resource.
- [x] Authorization evidence is scoped exactly to all seven candidate identity
  parts plus environment, operation, and resource.
- [x] Unknown or missing evidence remains distinct from explicit negative
  evidence.
- [x] Stale permission remains distinct from current and can never support
  `potentially_executable`.
- [x] Any well-formed scope mismatch fails closed and never matches or becomes
  reusable authority.
- [x] Only exact, current, positive evidence in every required dimension may
  yield the `potentially_executable` diagnostic.
- [x] `potentially_executable` remains a dry-run diagnostic and never creates a
  request, contract, dispatch, or invocation.
- [x] Exact granted authorization plus exact current denied permission preserves
  `authorized_but_not_permitted` and remains blocked.
- [x] Exact current allowed permission plus exact missing authorization
  preserves `permitted_but_not_authorized` and remains unresolved.
- [x] A blocked candidate remains blocked regardless of downstream positives.
- [x] An unresolved candidate remains unresolved regardless of downstream
  positives.
- [x] Focused tests verify all twelve authorized investigation scenarios.
- [x] Invalid inputs remain atomic and separate from valid blocked or unresolved
  outcomes.
- [x] The harness performs no permission discovery, mutation, grant, or sandbox
  change.
- [x] The harness performs no Human approval, Task, chat, or commit-prose parsing.
- [x] No authorization identifier, token, store, lifecycle, replay, revocation,
  expiry, consumption, or session is introduced.
- [x] No Task schema or Project Manifest schema or field is added.
- [x] No Execution Contract or execution request is introduced.
- [x] No adapter or provider integration is introduced.
- [x] No dispatch, tool call, Agent execution, or other invocation is performed.
- [x] Static and dynamic evidence proves no persistence, network, subprocess,
  permission discovery, target I/O, or ambient-state dependency.
- [x] Caller inputs remain unmodified and immutable results, findings, and
  reasons are deterministic.
- [x] Focused tests, regressions, validators, package installation, docs, final
  Security review, independent review, boundary review, and both effective
  Quality Gates pass or are reported accurately with no unresolved material
  finding.
- [x] Explicit Human approval is recorded before Task closure, staging, or
  commit.

The Human accepted the unauthorized recursive review-tool read as disclosed for
continuation without retroactively authorizing it or waiving a Gate. A genuinely
separate bounded independent re-review then approved the reconciled evidence
with no material findings and the actual `independent_review` Gate passed
without waiver, completing criterion 32. At the pre-approval checkpoint,
criterion 33 remained pending. On 2026-09-20, the Human then gave explicit final
acceptance, authorized Task closure, and authorized exactly one local closure
commit on `main`. All **33/33** criteria are complete. The incident remains
recorded, was not retroactively authorized, and required no Gate waiver. The
production harness no-I/O criteria remain satisfied.
