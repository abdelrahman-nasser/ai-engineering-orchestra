# AIO-047 Context

## Authorization and verified baseline

On 2026-09-23, the Human initially authorized AIO-047 Task creation, fresh
Architect, Security, and storage/atomicity design locks, implementation,
target-safe validation, fresh final reviews, Quality Gate evaluation, and
preparation of the Human Control checkpoint. After that evidence passed, the
Human explicitly approved the architecture, Admission schema, authoritative
provenance, store protocol, SQLite backend, migration/integrity model,
trusted-time/currentness model, revocation model, bounded replay-protection
claim, security/storage boundaries, and final acceptance. The final
authorization completes criterion 105, closes the Task, and permits explicit
staging of the reviewed paths and exactly one local implementation-and-closure
commit on `main`. It does not authorize push, publication, real authority use,
dispatch, or invocation.

The verified baseline is clean `main` at
`9986827eee23e7f80a41769872036acbc37765a4`, whose subject is
`experiment: validate durable admission transaction semantics (AIO-046)`.
AIO-046 is completed at 69/69, AIO-045 is completed at 70/70, AIO-044 remains
cancelled at 63/66, and AIO-047 was absent before this Task was created.
AIO-030 remains parked independently at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. The worktree and index were clean.

## Classification and governance

AIO-047 is an `implementation` with high Complexity, critical Risk, and an
explicit `critical` minimum Execution Mode. It uses the `architecture-change`
Workflow because it creates the first canonical stateful authority-consumption
layer and a supported persistence backend. The Workflow requires Architect and
Software Engineer participation, final Architect and independent review,
`documentation_consistency`, `independent_review`, and a Human Control
checkpoint. A Security Reviewer and a non-implementing Architect or Reviewer
with explicit storage/atomicity responsibility are additionally required.

Implementation may start only after all three fresh design reviews approve:

```text
ARCHITECT DESIGN LOCK: APPROVE
SECURITY DESIGN REVIEW: APPROVE
STORAGE/ATOMICITY DESIGN REVIEW: APPROVE
```

## AIO-046 evidence boundary

AIO-046 is engineering evidence, not production implementation. It established
that one trusted local SQLite file using explicit writer serialization can
atomically combine exact Grant and Binding values, Grant/domain-Run uniqueness,
trusted decision time, revocation ordering, and exact historical retry. Its
private schema, encoding, trust stubs, Python API, and result strings are not
canonical and must not be copied unchanged.

```text
AIO-046 experiment PASS != AIO-047 production implementation PASS
```

## Approved canonical design locks

The canonical term is **Agent Execution Dispatch Admission**. The value is an
immutable serializable positive authorization-consumption admission record and
historical security fact whose operational authority and durability derive only
from creation or retrieval through the configured authoritative store.

The approved definition is:

> An Agent Execution Dispatch Admission is an immutable serializable record
> which, when created or retrieved through the authoritative authorization-
> domain admission store, establishes that one operationally trusted Agent
> Execution Authorization Grant was current and had no earlier authoritative
> revocation in the applicable serial order, and was atomically consumed for
> one exact Agent Execution Run and one exact trusted non-widening Agent
> Operation Tool Binding.

The value contains exactly, in order:

```text
grant
tool_binding
decision_time
```

It has no Admission ID, status, state, attempt, lifecycle, delivery, result,
error, lease, or metadata field. Natural identity is the Grant composite
identity. `(authorization_domain_id, run_id)` is a separate uniqueness key.
Full value equality is `(grant, tool_binding, decision_time)`.

For a new Admission:

```text
grant.run == tool_binding.run == freshly reconstructed expected Run
```

Fresh reconstruction reuses `grant.run.run_id`. The trusted coordinator owns
authenticated Grant and trusted Binding handoff, fresh parent collection,
AIO-040 composition, effective-mode resolution, and AIO-041/AIO-042
reconstruction. The store owns domain binding, authoritative time,
currentness, revocation serialization, uniqueness, atomic consumption plus
Admission insertion, exact retry, and failure classification. No caller trust
boolean is accepted.

Intrinsic validation proves only exact value type, nested intrinsic validity,
Grant/Binding Run equality, decision-time syntax, and static half-open interval
coherence. It does not prove issuer authentication, resolver trust,
authoritative time, non-revocation, persistence, or store provenance. Direct
construction remains descriptive only. A future dispatcher must load an
Admission from the authoritative store rather than trusting arbitrary bytes.

## Store and retry semantics

The approved backend-neutral protocol is
`AgentExecutionDispatchAdmissionStore`. Its core semantics include guarded
authoritative lookup, `admit_or_return_existing`, and
`revoke_or_return_existing`. Exact retry is the same complete Grant plus the
same complete Tool Binding. No request idempotency key or Admission ID is
introduced.

An exact committed Admission may be returned after trust, intrinsic, domain,
decoding, and exact-value checks without recollecting prerequisites, sampling
time, or reevaluating expiry or revocation. This historical recovery path is
not fresh dispatch authority.

For a genuinely new request, the store samples an authority-owned UTC clock
after writer serialization, applies zero implicit skew, and requires:

```text
grant.issued_at <= decision_time < grant.expires_at
```

New domain decision time may not precede the prior committed decision in the
same active domain generation. SQLite uses a persisted watermark as a private
backend mechanism. Clock failure or regression fails closed without caller-time
fallback or clamping.

Original-issuer revocation uses the complete Grant composite identity, retains
the complete Grant in an immutable tombstone, and shares the Admission serial
order. Revocation-first rejects a new Admission; Admission-first preserves the
historical Admission and records later revocation. Post-Admission revocation
does not mutate Admission or decide queued-delivery behavior.

## SQLite persistence boundary

The supported v1 backend is one dedicated security admission SQLite database
per authorization-domain ownership context on a trusted local filesystem. It
supports multiple local processes using the same file and does not support
multi-machine use, network shares, cloud-sync folders, replicated writable
copies, copy-as-failover, or memory/alternate-file fallback.

The required profile is WAL, `synchronous=FULL`, foreign keys enabled, normal
locking, an explicit busy timeout, and explicit writer serialization.
Operational open uses an existing configured store and never silently creates,
repairs, migrates, or substitutes authority state.

The production schema is new and packaged separately from the experiment. It
contains explicit application/store identity, authorization domain, schema and
migration history, immutable migration checksum, ledger instance identity,
activation/fencing state, decision-time watermark, and revocation-completeness
metadata. Migrations are forward-only, explicit, checksum-validated, and
single-owner. Newer, dirty, partial, corrupt, or incompatible stores fail
closed; downgrade and silent repair are unsupported.

The local ledger may be marked irreversibly fenced/read-only, but copied local
metadata cannot globally prevent two copies from claiming authority. Active
WAL backup must use a SQLite-consistent backup mechanism. A snapshot created
through the supported backup path is permanently fenced and has no same-domain
restore/reactivation path. Raw active-file copying is unsupported and a
manually substituted stale active copy remains outside database-local
detection. Cross-backend ownership transfer and PostgreSQL are future work.

Local ACLs, schema checks, and payload integrity checks detect accidental
corruption and drift but do not resist a malicious local administrator who
controls the file and process. That requires an external trust boundary.

## Claim and non-execution boundary

The allowed bounded claim is:

> The supported local SQLite admission backend provides durable atomic
> at-most-once Grant and Run consumption, duplicate suppression, and exact-
> retry recovery within one correctly owned local authorization domain when
> every consumer uses the same active authoritative ledger and the declared
> Grant, Tool, clock, filesystem, and ownership trust preconditions hold.

No unqualified end-to-end authorization replay-protection claim is permitted
until operational Grant authentication, resolver trust, and domain ownership
are integrated. Authorization-consumption replay protection is not invocation
replay protection.

```text
Admission != dispatch
Admission != invocation
Admission != success
Admission != continuing permission or availability
```

Tests use synthetic values and disposable temporary databases only. They do no
resource I/O, Tool call, Provider call, Runtime call, dispatch, or invocation.

## Validation plan

Fresh AIO-047 evidence covers the three-field value and schema; offline nested
references; deterministic intrinsic validation; reusable backend-neutral
protocol conformance exercised against SQLite; exact retry and conflicts;
currentness and clock failure/regression; revocation and both race orders;
spawned-process contention and hard exits; busy/unavailable storage; faults
before and after transactional boundaries; response loss and fresh-process
restart; provisioning, migration, checksum, schema drift, corruption, and
malformed payload behavior; backup/fencing limitations; packaging and
installation; and focused AIO-040 through AIO-046 regressions.

No broad Task validation, Workflow catalog enumeration, repository-wide
verification, recursive search, broad Markdown traversal, unknown-safety
validator, or non-target-safe smoke is authorized.

## Human Control

Human Control is satisfied by direct Human final approval on 2026-09-23. The
approval explicitly covers architecture, the Admission schema, authoritative
provenance, the backend-neutral store protocol, the SQLite local backend,
schema-version/migration/integrity behavior, trusted time/currentness,
revocation ordering, the bounded authorization-consumption replay-protection
claim, security and storage/atomicity boundaries, and final acceptance.

The Task is `completed` at 105/105. This approval authorizes the reviewed local
closure commit only. It is not operational Grant issuance, real Grant
consumption, dispatch authorization, or invocation authorization.
