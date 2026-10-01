# AIO-052 Acceptance Criteria

AIO-052 is complete only when every applicable criterion is supported by fresh,
Task-local evidence. Phase 1 checks design only; Phase 2 implementation and
Phase 3 review require separate Human authorization.

## Cancellation record

AIO-052 was cancelled on 2026-10-01 because PROCESS-052-1 made the acceptance
contract permanently unsatisfiable. The checklist is preserved unchanged as
historical evidence; cancellation does not complete, weaken, rewrite, or waive
any unmet criterion. No implementation was performed, and a future replacement
must produce fresh Phase 1 design and review evidence.

## Task and Phase 1 design

- [x] The Task ID is `AIO-052` and the exact candidate location was available.
- [x] Exactly `task.yaml`, `context.md`, `acceptance-criteria.md`, and
  `review.md` are the Phase 1 Task artifacts.
- [x] Status is `in_progress`; type is `implementation`; Workflow is
  `architecture-change`; Complexity is `high`; Risk and execution mode are
  `critical`.
- [x] Direct dependencies are exactly AIO-047, AIO-049, AIO-050, and AIO-051.
- [x] The canonical integration term and narrow responsibility are defined as
  Local Operational Trust Coordinator.
- [x] No new public schema, Integration Admission, Integration ID, or durable
  integration state is proposed.
- [x] The exact orchestration order preserves component ownership and stops
  before dispatch, invocation, or repository resource read.
- [x] Exact Run agreement, retry boundaries, restart limits, and audit
  correlation are explicitly defined.
- [x] The minimum Phase 2 artifacts and focused-change boundary are defined.
- [x] The 41-scenario failure/no-fallback matrix is defined.
- [x] The Validation Safety Matrix is defined and every Phase 1 execution entry
  remains `NOT RUN`.
- [x] The preimplementation experiment decision is `NO`.
- [ ] The Phase 1 process-safety deviation is resolved by explicit Human
  direction; it is not silently waived.
- [x] Fresh Architect design review approves the final four artifacts.
- [x] Fresh Security design review approves the final four artifacts.
- [x] Fresh Operational Trust/Integration design review approves the final
  four artifacts.
- [x] No unresolved blocker or high-severity design finding remains.
- [ ] Separate Human Phase 2 implementation authorization is recorded before
  implementation begins.

## Canonical composition

- [ ] Phase 2 uses a real live AIO-049 Owned Authorization Domain Session over
  a disposable real AIO-047 SQLite ledger.
- [ ] Phase 2 uses the real AIO-050 Producer and exact paired authentication
  port; no raw or fabricated Grant can enter Admission.
- [ ] Phase 2 uses the real AIO-051 immutable registry and resolver to produce
  the canonical Tool Binding.
- [ ] Phase 2 uses the existing AIO-047 coordinator and official local SQLite
  backend to create or return the authoritative Admission.
- [ ] The private authentication latch is unbound-fail-closed, install-once,
  exact-target, race-safe, non-authorizing, non-replaceable, and terminal on
  composition failure.
- [ ] The coordinator is published only after live ownership, Producer
  composition, exact port binding, and resolver construction all succeed.
- [ ] A composition failure closes every acquired capability and exposes no
  partially trusted coordinator.
- [ ] AIO-050 issuance and AIO-049 Admission use two sequential fresh leases on
  the same session; no third, nested, shared, or cross-operation atomic lease
  is introduced.
- [ ] Close, fence, loss, or identity/generation drift in the inter-operation
  gap prevents authentication and Store access and never permits same-Run
  reissuance.
- [ ] AIO-047 alone orders authentication, resolution, guarded history, fresh
  prerequisites/mode, exact reconstruction, and authoritative Store access.
- [ ] Operational Grant authentication is never invoked directly outside the
  exact Owned Session operation.
- [ ] AIO-050 failures return the exact unchanged production result; successful
  issuance returns the exact unchanged AIO-047 result; no integration outcome
  taxonomy or presentation-bearing success result exists.
- [ ] Coordinator close is terminal, idempotent, race-safe, rejects new work,
  drains in-flight outer calls, closes Producer/latch/session, attempts all
  cleanup after an error, and releases the ownership lock.

## Authority and ownership

- [ ] Both exact Human-approval and exact policy-allow happy paths are proven
  with synthetic authenticated authority.
- [ ] Policy deny, malformed or expired proof, foreign Producer/session/adapter
  epoch, issuer disablement, wrong Run, wrong domain, wrong generation, lost
  ownership, closed session, and fenced domain all fail closed.
- [ ] The Producer, proof minters, issued presentation, paired authentication
  port, and exact session remain process-local and nonserializable as defined by
  AIO-050.
- [ ] No production principal, production authority source, production domain,
  or production ledger is used.
- [ ] No second ownership abstraction or authority engine is introduced.

## Tool and Run integrity

- [ ] The first route resolves only
  `tool::aeo-native-repository-file-read::v1` for the exact configured
  Runtime/environment/`repository_file_read` route.
- [ ] Unknown Admission routes, retired pre-Run selection, Tool-ID rebind,
  wrong Runtime, wrong environment, wrong operation, resource widening, and
  fallback all fail closed at their owning boundary.
- [ ] Retired-route rejection is proven only at AIO-051 pre-Run selection;
  Local Coordinator Admission remains total for retained historical routes.
- [ ] Caller-supplied Binding, Tool ID, alias, route override, or alternate Tool
  never becomes trusted.
- [ ] Producer-approved Run equals `Grant.run`; `Grant.run` equals
  `Binding.run`; and the freshly reconstructed expected Run equals both.
- [ ] Substitution of canonical `runtime_option_id` or `option_id` after Run
  creation is rejected; no nonexistent Provider field is claimed.
- [ ] Registry reconstruction under the unchanged append-only manifest
  reproduces the exact historical Binding.

## Admission, retry, and restart

- [ ] One synthetic Human happy path and one policy happy path each produce one
  real canonical Grant, Binding, and authoritative disposable Admission.
- [ ] Missing, unavailable, invalid, unsatisfied, or Run-mismatched fresh-source
  results, invalid execution mode, revoked Grant, expired Grant, ledger
  corruption, and incompatible schema fail closed; the source owns bounded
  freshness provenance.
- [ ] Revocation uses a distinct independently authenticated synthetic original-
  issuer presentation bound to the original issued presentation and real
  `session.revoke(...)`; under that owned lease its port forwards the issued
  presentation through the sealed AIO-050 authentication path, never caches or
  fabricates a Grant, never authenticates out of gate, and never directly seeds
  the Store.
- [ ] Same-process pre-Admission exact retry reuses the identical AIO-050
  presentation and never issues a replacement Grant.
- [ ] Same-process post-Admission exact retry returns AIO-047 historical
  Admission and does not collect fresh prerequisites or write a replacement.
- [ ] Restart before issuance requires a new session, new Run, and fresh
  authority flow.
- [ ] Restart after ephemeral presentation but before Admission rejects the old
  presentation and requires a new session, new Run, fresh proofs, and new
  Grant.
- [ ] Restart after Admission preserves the durable AIO-047 record as
  authoritative while explicitly rejecting any unsupported claim that the old
  AIO-050 presentation or integrated retrieval path survives.
- [ ] No persistence is added to mask a predecessor restart boundary.
- [ ] No new Admission contract, Admission identity, or Integration ID exists.

## Negative operational proof

- [ ] Every success and failure scenario proves `DISPATCH: NO`.
- [ ] Every success and failure scenario proves `INVOCATION: NO`.
- [ ] Every success and failure scenario proves `REPOSITORY RESOURCE READ: NO`
  while allowing disposable SQLite and ownership-metadata I/O.
- [ ] The identity-only native repository Tool has no callable behavior in the
  integration module or fixture.
- [ ] The protected target is never opened, read, searched, enumerated,
  specifically listed, statted, hashed, resolved, permission-inspected, or used
  as a fixture.
- [ ] Categorical AIO-052 protected-target non-access remains certifiable.

## Validation and review

- [ ] Every executed command is present in an approved Task-local Validation
  Safety Matrix and receives its required static preflight.
- [ ] No legacy validator `--help`, Task/Workflow catalog validation,
  repository-wide verification, recursive repository search, broad test
  discovery, broad Markdown traversal, or bare package smoke is used.
- [ ] Exact AIO-052 implementation tests pass.
- [ ] Exact affected AIO-047, AIO-049, AIO-050, and AIO-051 regression modules
  pass.
- [ ] Exact changed Python paths parse and exact changed Markdown paths lint.
- [ ] Target-safe package evidence passes if and only if the package surface
  changes.
- [ ] Fresh post-implementation Architect, Security, Operational
  Trust/Integration, and independent reviews approve the final snapshot.
- [ ] `documentation_consistency` passes without waiver.
- [ ] `independent_review` passes without waiver.
- [ ] Required final Human approval is recorded before Task closure.
- [ ] No required Quality Gate failed or was skipped at closure.
- [ ] The index is reconciled only under later explicit authorization, and no
  push, merge, tag, release, or publication occurs.
