# AIO-046 Context

## Authorization and verified baseline

On 2026-09-23, the Human explicitly authorized creation and execution of this
synthetic experiment, including Task creation, design locks, implementation,
fault and concurrency validation, specialist and independent reviews, Quality
Gate evaluation, and preparation of the Human Control checkpoint.

On 2026-09-23, the Human separately approved the final experiment design,
security boundary, storage/atomicity model, trusted-time/currentness model,
revocation model, SQLite experiment limitations, and final findings. That
approval authorized criterion 69, Task completion, explicit staging of the ten
reviewed AIO-046 paths, and exactly one local closure commit on `main`.

The verified baseline is clean `main` at
`b7f30c52747c93faedccd0c1987902a45c9e5211`. The worktree and index were clean,
and AIO-046 was absent before creation. AIO-045 is completed at 70/70. AIO-044
remains cancelled at 63/66 and is neither a dependency nor a source of AIO-046
evidence. AIO-030 remains parked independently at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`.

The preceding investigation incident is historical context only. Its recursive
discovery output is not AIO-046 evidence, and the AIO-046 command history starts
independently. No recursive repository search, broad Task validation, Workflow
catalog enumeration, repository-wide verification, broad Markdown traversal,
unknown-safety validator, or non-target-safe smoke is authorized.

## Final Human approval and closure

Approval date: 2026-09-23.

Approval source: direct Human final approval, experiment closure, and
local-commit authorization.

```text
HUMAN EXPERIMENT ARCHITECTURE APPROVAL:
APPROVED

HUMAN SECURITY-BOUNDARY APPROVAL:
APPROVED

HUMAN STORAGE/ATOMICITY APPROVAL:
APPROVED

HUMAN TRUSTED-TIME/CURRENTNESS MODEL APPROVAL:
APPROVED

HUMAN REVOCATION MODEL APPROVAL:
APPROVED

HUMAN SQLITE EXPERIMENT LIMITATIONS APPROVAL:
APPROVED

FINAL ACCEPTANCE:
APPROVED
```

The approval completed all 69 acceptance criteria and the Task lifecycle. It
does not widen the experiment boundary:

```text
Human approval of AIO-046 != production replay protection
Human approval of AIO-046 != production SQLite architecture
Human approval of AIO-046 != real Grant consumption
Human approval of AIO-046 != dispatch authorization
```

## Classification and Workflow

AIO-046 is an `investigation` with high Complexity, critical Risk, and an
explicit `critical` minimum Execution Mode. It uses the `architecture-change`
Workflow because it investigates the first stateful security boundary before a
canonical design is frozen. The Workflow's `applicable_task_types` list is
advisory, so the explicit Human/orchestrator binding is valid.

The Workflow requires Architect participation during design and final review,
Software Engineer participation for the experiment, `documentation_consistency`
and `independent_review`, and a Human Control checkpoint. A Security Reviewer is
additionally required by this Task. The repository defines no storage-specific
Role; storage/atomicity review is an explicit specialty responsibility performed
by a non-implementing Architect or Reviewer.

## Experiment status and canonical boundary

This is a non-production, synthetic persistence experiment. Its evidence may
inform AIO-047, but nothing introduced here automatically becomes a Core
contract:

```text
SQLite schema != canonical Core schema
experimental store != production admission store
experiment success != production replay protection
experiment admission != real dispatch admission
synthetic consumption != operational Grant consumption
```

The experiment creates no public JSON Schema, schema-resource registration,
package-root export, package-data change, or stable public
`AuthorizationAdmissionStore` API. Code remains private under
`experiments/authorization_domain_admission/` and is not shipped.

## Objective and security property under test

The experiment tests whether one logical authoritative ledger for one exact
`authorization_domain_id` can combine:

```text
trusted synthetic Grant input
+ trusted synthetic Tool Binding input
+ fresh prerequisite equality
+ trusted experimental decision time
+ same-ledger revocation
+ composite Grant and domain/Run uniqueness
-> one serialized SQLite transaction
-> one immutable durable admission record
```

No successful admission performs dispatch, invokes a Tool, reads the lexical
resource, or records execution success.

## Exact dependency semantics

The complete equality requirement is:

```text
grant.run == tool_binding.run == freshly reconstructed expected Run
```

The fresh Run must be prepared through AIO-040, AIO-041, and AIO-042 and must
reuse `grant.run.run_id`. A new Run ID would denote another semantic attempt.
Bare Run-ID equality is never sufficient. A fresh prerequisite source must
create new parent observations/evidence and a new AIO-040 assessment for every
new admission; rerunning AIO-040 over cached parent containers is not fresh.
The effective Task-wide Execution Mode is also resolved anew.

The Grant natural identity is:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

The second durable uniqueness key is:

```text
(authorization_domain_id, run_id)
```

Complete Grant, Tool Binding, Run, and Contract values remain stored and are
compared as decoded frozen values. IDs and hashes alone never establish exact
semantic identity.

## Implemented private transaction model

The proposed `admit_or_return_existing` sequence is:

1. Require out-of-band coordinator-minted trusted synthetic Grant and
   Tool-Binding capabilities bound to the exact payload and expected domain.
   Trust is never a request boolean or self-attested field, and failure occurs
   before any ledger lookup or historical-data disclosure. The synthetic
   coordinator requires identity of the exact envelope object it registered;
   copying a visible token into a changed envelope cannot rebind trust.
2. Intrinsically validate both complete values and require exact Grant/Binding
   Run equality plus the expected authorization domain.
3. Perform a read-only historical lookup. An exact committed admission returns
   immediately; an identity rebound or changed Binding conflicts immediately.
4. For a genuinely new request, collect new parent observations/evidence,
   produce a fresh AIO-040 assessment, freshly resolve the effective mode, and
   prepare the expected Run with the existing `grant.run.run_id`.
5. Require exact three-way Run equality, then acquire writer serialization with
   `BEGIN IMMEDIATE` on the one trusted-configured authoritative domain ledger.
6. Recheck the immutable singleton schema/domain/completeness metadata,
   existing admission identity, and domain/Run uniqueness inside the
   transaction.
7. An exact record committed by a concurrent worker is returned as historical
   existing state. Any changed value returns a deterministic conflict.
8. Sample the injected authority-owned clock exactly once and only after writer
   serialization. Reject clock failure, invalid/naive time, or regression and
   apply zero implicit skew.
9. Compare parsed instants using
   `issued_at <= decision_time < expires_at`; never compare timestamp strings.
10. Check the same-ledger immutable revocation tombstone.
11. For every non-regressed sampled new-request decision, advance the temporal
    watermark in the same transaction. This includes `not-yet-current`,
    `expired`, and `revoked` denials, which are returned only after the
    watermark commit succeeds.
12. For success, insert the complete immutable admission in that transaction,
    commit, and return success only after a known successful commit.

The read-only shortcut is a retry-recovery optimization, not an alternate
ledger. It may return only after trusted-boundary and intrinsic checks, expected
domain equality, metadata/completeness verification, safe decoding and
intrinsic validation of stored values, index/payload agreement, and exact full
Grant-plus-Binding equality. Every new admission still has exactly one
state-changing transaction. The in-transaction recheck is authoritative under
concurrency. The shortcut retrieves a historical outcome only; it is not
current authority or permission for a new dispatch. It does not require current
Grant freshness, current revocation, a new clock read, or a new prerequisite
collection.

Possible private experimental outcomes distinguish newly admitted, exact
existing admission, invalid input, not-yet-current, expired, revoked, domain
mismatch, Grant identity conflict, Run conflict, Binding conflict, clock
failure/regression, storage busy/unavailable, commit-unknown, and other storage
failure. A `COMMIT` exception is always indeterminate, never definite success
or rejection. An exact retry against the same ledger reconciles a row-creating
admission or revocation; a watermark-only denial can only be safely reevaluated
and cannot prove whether the earlier denial transaction committed. These names
are provisional and are not a public enum or API commitment.

## Implemented private SQLite design

The design candidate uses one local file-backed SQLite database per
authorization domain. A trusted harness owns the exact domain-to-database-path
mapping; admission and revocation requests cannot choose a path. SQLite cannot
globally prove that no copied or second file claims the same domain, so that
mapping is an explicit deployment precondition. Independent files for one
domain are an intentionally invalid negative counterexample.

Controlled one-time provisioning is separate from operational use. Provisioning
selects WAL outside a transaction, then atomically installs private DDL and one
singleton metadata row binding exact schema version, domain ID, revocation
completeness, and a nullable time watermark. Operational connections use
read/write-existing mode and never auto-create, initialize, repair, fail over,
or fall back to memory. Missing, duplicate, mismatched, unsupported, corrupt,
or incomplete metadata fails closed.

Verified settings:

- journal mode: `WAL`;
- synchronous level: `FULL`;
- busy timeout: 5000 ms per normal connection, with a documented shorter test
  override for the busy scenario;
- transaction mode: explicit `BEGIN IMMEDIATE` for conflicting writes;
- isolation: Python `sqlite3` autocommit mode with explicit transactions;
- foreign keys enabled and normal rather than exclusive locking;
- local filesystem only, excluding network shares, cloud-sync paths, and
  replicated copies.

Private SQL tables hold admissions and immutable revocation tombstones tied to
the singleton domain metadata. Admissions use composite Grant identity as the
primary key and domain/Run as a second unique key. Revocations retain the
complete Grant and original synthetically authenticated issuer identity. SQL
triggers reject admission/revocation update or deletion and prevent metadata
identity/completeness changes or watermark regression. `INSERT OR REPLACE` and
conflict updates are prohibited.

Stored Grant and Binding JSON use deterministic compact, sorted-key UTF-8
encoding with fixed options, explicit reconstruction, intrinsic validation,
index/payload agreement, and exact semantic round-trip. Duplicate JSON keys,
missing/extra fields, wrong types, invalid nested values, noncanonical bytes,
NaN, Infinity, and lossy timestamp conversion fail closed. IDs and hashes are
never equality authority. The encoding is experimental and noncanonical.

SQLite is only a local experiment vehicle and a possible future local Developer
backend. A future Team/Enterprise implementation could use PostgreSQL or an
authoritative service. Canonical semantics must remain backend-neutral.

## Trusted time and revocation model

The authority-owned clock is an injected controlled test stub, never a request
timestamp, fixture-creation timestamp, or arbitrary caller field. It must yield
an aware UTC instant. Failure is fail-closed. The locked regression rule is
that a newly sampled domain decision time may equal but must never precede the
persisted last authoritative ledger decision time. The experiment stores both
the deterministic UTC representation and an exact integer microsecond ordering
key, avoiding lexical ordering or precision loss. The watermark advances for
every committed sampled new-request decision and for a new revocation, not only
for successful admissions. Exact historical retries do not sample or advance
time.

Revocation is a private immutable ledger tombstone over the complete Grant,
including its composite identity and complete Run binding. An out-of-band
coordinator capability binds the original synthetically authenticated
issuer/producer and exact domain; no request trust flag, administrator, or
delegated-authority composition exists. Exact tombstone retries are idempotent;
identity rebound conflicts. A missing tombstone means not revoked only when the
database metadata proves the domain revocation ledger complete; unknown or
corrupt state fails closed.

A first-time revocation uses the same `BEGIN IMMEDIATE` serialization, samples
the authority clock exactly once after acquiring the writer lock, rejects clock
failure or regression, and atomically inserts the tombstone plus advances the
watermark. Revocation success is returned only after a known successful commit.
An exact historical tombstone retry does not sample or advance time.

Writer serialization determines race order. If revocation commits first, a new
admission rejects. If admission commits first, later revocation does not erase
or mutate the historical admission. Caller timestamps do not select a winner.

## Atomicity, recovery, and counterexamples

Injected worker faults cover hard termination before the transaction, after
`BEGIN IMMEDIATE`, after checks, after insertion but before commit, and after
commit but before a response. Pre-commit termination must leave no admission.
Post-commit admission response loss must be recoverable by an exact retry from
a genuinely fresh process. Any exception around `COMMIT` is `commit-unknown`.
A fresh exact retry reconciles row-creating admission/revocation commits; for a
watermark-only denial it safely reevaluates current state without claiming to
recover the original denial. The experiment also covers restart durability,
unavailable and busy databases,
two-process exact and conflicting requests, in-memory loss on restart, and
split-database double admission. `WAL` plus `FULL` supports process-crash and
restart evidence only; it does not prove power-loss durability on dishonest
hardware or filesystems.

Admission creation is provisional consumption. The Grant is never mutated with
`used`, `consumed`, or `revoked`. There is no consumption ID or admission ID.

## Explicit limitations

The immutable admission may contain enough information to become a future
outbox source, but AIO-046 adds no dispatcher, lease, delivery attempt,
acknowledgement, reconciliation, or automatic recovery. Consequently:

```text
SQLite duplicate suppression != production authorization replay protection
authorization replay protection != invocation replay protection
PERMISSION TOCTOU SOLVED?: NO
RUNTIME/INFERENCE TOCTOU SOLVED?: NO
TOOL-MAPPING TRUST SOLVED?: NO
```

Post-admission revocation does not cancel queued work because no queued-work
lifecycle exists. A future short-lived non-revocable read-only profile may be
investigated separately, but it is not a general production architecture.

## Safety boundary

All resources are synthetic lexical values. SQLite databases exist only in
controlled temporary directories outside repository source paths. The
experiment uses no network, provider, cloud database, operational authority,
real Tool, external dispatch, or protected-target access. Tests must clean all
processes and temporary SQLite/WAL/journal files.
