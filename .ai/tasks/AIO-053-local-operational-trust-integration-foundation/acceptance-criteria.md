# AIO-053 Acceptance Criteria

AIO-053 is complete only when every applicable criterion has fresh AIO-053
evidence. AIO-052 evidence is never inherited.

## Task and Phase 1 design

- [x] The exact AIO-053 candidate path was available at the authorized clean
  baseline.
- [x] Exactly `task.yaml`, `context.md`, `acceptance-criteria.md`, and
  `review.md` are the Phase 1 artifacts.
- [x] Status is `in_progress`; type is `implementation`; Workflow is
  `architecture-change`; Complexity is `high`; Risk and execution mode are
  `critical`.
- [x] Direct dependencies are exactly AIO-047, AIO-049, AIO-050, and AIO-051.
- [x] AIO-052 remains cancelled and contributes no acceptance, review, Gate,
  Human approval, or completion evidence.
- [x] The Local Operational Trust Coordinator has one narrow responsibility and
  duplicates no predecessor policy.
- [x] Exact orchestration, Run agreement, ownership gaps, retries, restart
  limits, lifecycle, and result families are defined.
- [x] No new public schema, Integration Admission, Integration ID, or durable
  integration state is proposed.
- [x] The 42-scenario matrix is defined.
- [x] The Validation Safety Matrix exists before Phase 2 validation.
- [x] The preimplementation experiment decision is `NO`.
- [x] Fresh AIO-053 Architect design review approves the final four artifacts.
- [x] Fresh AIO-053 Security design review approves the final four artifacts.
- [x] Fresh AIO-053 Operational Trust/Integration design review approves the
  final four artifacts.
- [x] No unresolved blocker or high-severity Phase 1 finding remains.
- [x] Separate Human Phase 2 authorization is recorded before implementation.

## Prospective command-safety contract

- [x] Human-authorized bootstrap/control commands are explicitly distinguished
  from validation and review commands.
- [x] The Human-authorized baseline commands, exact candidate check, historical
  reference reads, and Task/matrix creation actions are recorded as bootstrap
  controls rather than validation evidence.
- [x] After matrix creation, every validation or review command is either
  explicitly Human-authorized for its phase or present in the approved matrix
  and receives its required static preflight.
- [x] No Task or Workflow catalog enumeration, repository-wide verification,
  recursive repository search, broad test discovery, broad Markdown traversal,
  legacy validator `--help`, unknown-safety validator, bare smoke, or
  protected-target access occurs.
- [x] Every matrix amendment precedes the newly authorized command; no command
  is retroactively inserted to cure an execution.

## Canonical composition

- [x] Phase 2 uses a real live AIO-049 Owned Authorization Domain Session over
  a disposable real AIO-047 SQLite ledger.
- [x] Phase 2 uses the real AIO-050 Producer and paired authentication port.
- [x] Phase 2 uses the real AIO-051 immutable registry and resolver.
- [x] Phase 2 uses the existing AIO-047 coordinator and official local SQLite
  backend.
- [x] The private latch is unbound-fail-closed, exact-target, install-once,
  race-safe, non-authorizing, non-replaceable, and terminal on failure.
- [x] The coordinator is published only after ownership, Producer composition,
  resolver construction, and exact port binding all succeed.
- [x] Composition failure closes every acquired capability and exposes no
  partially trusted coordinator; paired-port, Producer, latch, and session
  cleanup are all attempted even when one close raises, with errors preserved.
- [x] Issuance and Admission use two sequential fresh leases on the same exact
  session; no third, nested, shared, or transaction-spanning lease exists.
- [x] Inter-lease close, fence, loss, or identity/generation drift prevents
  authentication and Store access and never permits same-Run reissuance.
- [x] AIO-047 alone owns authentication ordering, Binding resolution, guarded
  history, fresh reconstruction, exact equality, and Store access.
- [x] AIO-050 failure and AIO-047 Admission results remain unchanged; no
  integration outcome taxonomy or presentation-bearing success result exists.
- [x] Coordinator close is terminal, idempotent, race-safe, drains registered
  operations, attempts all cleanup, and releases AIO-049 ownership.

## Authority, Tool, and Run integrity

- [x] Exact Human-approval and policy-allow happy paths are both proven using
  synthetic authenticated authority.
- [x] Policy deny, malformed/expired proof, foreign Producer/session/adapter
  epoch, issuer disablement, wrong Run/domain/generation, ownership loss,
  close, and fencing all fail closed.
- [x] A well-formed, unexpired authority proof bound to a foreign principal,
  authority channel/kind, issuer, domain, or generation is rejected before
  presentation creation or issuance-state mutation.
- [x] No production principal, authority source, domain, or ledger is used.
- [x] The first route resolves only
  `tool::aeo-native-repository-file-read::v1` for the exact configured route.
- [x] Unknown route, retired pre-Run selection, Tool-ID rebind, Runtime,
  environment, operation, resource, and fallback failures close at their
  owning boundary.
- [x] Historical resolution remains total for retained routes and does not
  reinterpret retirement.
- [x] Caller Binding, Tool ID, alias, route override, raw Grant, or trust flag
  never becomes authority.
- [x] Producer-approved Run equals `Grant.run`, `Binding.run`, and the freshly
  reconstructed expected Run without coercion or partial equality.
- [x] `runtime_option_id` or `option_id` substitution is rejected; no Provider
  field or post-Run override is invented.

## Admission, retry, and restart

- [x] Each Human and policy happy path creates one real canonical Grant,
  Binding, and authoritative disposable Admission.
- [x] Missing, unavailable, invalid, unsatisfied, or Run-mismatched fresh facts,
  invalid mode, revoked/expired Grant, and corrupt/mismatched ledger fail closed.
- [x] Revocation uses independent original-issuer proof plus the opaque issued
  presentation under real `session.revoke(...)`; only the sealed AIO-050 path
  recovers the Grant, with no cache, fabrication, or direct Store seed.
- [x] Pre-Admission exact retry reuses the identical process-local presentation
  and never issues a replacement.
- [x] Post-Admission exact retry returns AIO-047 historical Admission before
  fresh-fact collection or another write.
- [x] Restart before Admission requires a new session, Run, proofs, and Grant;
  the old presentation is unavailable.
- [x] Restart after Admission preserves durable authority without claiming that
  the old presentation or integrated historical retrieval survives.
- [x] Identical AIO-051 reconstruction reproduces the historical Binding.
- [x] No new persistence masks a predecessor restart boundary.

## Negative operational proof

- [x] Every success and failure proves `DISPATCH: NO`.
- [x] Every success and failure proves `INVOCATION: NO`.
- [x] Every success and failure proves `REPOSITORY RESOURCE READ: NO` while
  allowing disposable SQLite and ownership-metadata I/O.
- [x] The identity-only native Tool has no callable behavior in integration or
  fixtures.
- [x] The protected target is never opened, read, searched, enumerated,
  specifically listed, statted, hashed, resolved, permission-inspected, or used
  as a fixture.
- [x] Categorical AIO-053 protected-target non-access remains certifiable.

## Validation and closure

- [x] Exact AIO-053 Task and architecture-change Workflow direct schema checks
  pass only after their exact commands are added and preflighted.
- [x] Exact integration and focused AIO-047/AIO-049/AIO-050/AIO-051 regression
  modules pass.
- [x] Exact approved changed Python paths parse and exact changed Markdown paths
  lint.
- [x] Every focused test, package test, and smoke preflight bounds the complete
  runtime-reachable local code, configuration, and fixture closure, including
  initializers, transitive or dynamic imports, subprocesses, network behavior,
  and protected-target behavior; `--target-safe` alone is insufficient.
- [x] Markdown lint uses only the Human-designated external fixed executable at
  exact version `0.23.3` after exact configuration, ignore, plugin, and path
  resolution; validation performs no implicit package acquisition or network
  access.
- [x] Packaging and target-safe smoke pass if the package surface changes.
- [x] Fresh post-implementation specialist and independent reviews approve the
  final AIO-053 snapshot.
- [x] `documentation_consistency` passes without waiver.
- [x] `independent_review` passes without waiver.
- [x] Required final Human approval is recorded before completion.
- [x] No required Quality Gate failed or was skipped at closure.
- [x] No push, merge, tag, release, or publication occurs.

## Current Phase 3 evidence state

Phase 2 implementation and technical validation are complete. The
Human-designated `markdownlint-cli2@0.23.3` bootstrap remained outside the
repository and was used directly offline. The rejected P1, S1, and M1 entries
remain recorded as superseded before execution; their bounded replacements all
passed.

The 42 locked scenarios, exact map integrity, focused AIO-047/AIO-049/AIO-050/
AIO-051 regressions, exact AST, direct Task and Workflow schemas, packaging,
Markdown, and target-safe editable/wheel smoke all pass. One AIO-049 regression
is skipped only because Windows symlink privilege is unavailable; the sibling
real-junction and unknown-reparse-tag checks pass. Fresh post-remediation
Architect, Security, Operational Trust/Integration, and Formal Independent
reviews approve with ARCH-053-1 closed and no unresolved findings. Both
required Quality Gates pass without waiver. Final Human approval is recorded
as approved on 2026-10-02.

## Final closure

On 2026-10-02, the Human authorized final closure and exactly one bounded local
implementation-and-closure commit. The recorded required Quality Gates remain
`PASS WITHOUT WAIVER`: `documentation_consistency` and `independent_review`.
No required Quality Gate failed, and no required Quality Gate was skipped.
The final closure criterion is satisfied, acceptance is 70 of 70, and AIO-053
status is `completed`. No push, merge, tag, release, publication, Dispatch,
Tool invocation, or repository resource read is authorized or performed by
closure.
