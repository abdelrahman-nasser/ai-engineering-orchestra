# Authorization-domain durable admission experiment

This directory is the private AIO-046 persistence experiment. It asks whether
one authoritative authorization-domain ledger can serialize exact Grant and
Run consumption, trusted decision time, and revocation into one durable,
immutable admission. It never dispatches or invokes a Tool.

The experiment is deliberately non-production, non-packaged, and
noncanonical. Its SQL is not a Core schema, its Python surface is not a stable
store API, and its JSON encoding is not a public wire format. Nothing here is
registered as package data or exported from the library. SQLite is a local
experimental vehicle (and might inform a future local Developer backend), not
a mandatory production backend; a future Team or Enterprise backend could be
PostgreSQL or an authoritative service while preserving backend-neutral
semantics.

## Trust, ownership, and freshness boundaries

The coordinator supplies out-of-band, payload-bound capabilities for a
synthetically trusted Grant and Tool Binding. Trust is bound to their exact
payloads and expected authorization domain; it is not a caller boolean or a
attested request field. The coordinator also retains and requires identity of
the exact envelope object it minted, so cloning that envelope while reusing its
visible token cannot rebind the Grant, Binding, revoker, or domain. This stub is
neither real issuer authentication
nor a real Tool resolver. Untrusted requests fail before ledger lookup so they
cannot use the historical-return path to disclose state.

One exact `authorization_domain_id` has one logical authoritative ledger and,
in this SQLite experiment, one harness-configured database path. Requests do
not choose that path. The database must be on a local filesystem in a
controlled temporary directory, never a network share, cloud-sync directory,
replicated copy, or repository source directory. Two independent database
files claiming one domain are an intentionally invalid split-ledger
counterexample; SQLite cannot itself prevent that deployment error.

Every genuinely new admission obtains new parent observations/evidence, builds
a new satisfied AIO-040 assessment, resolves the effective Task-wide Execution
Mode again, prepares the exact Contract again, and reconstructs the expected
Run using `grant.run.run_id`. It then requires exact value equality:

```text
grant.run == tool_binding.run == freshly reconstructed expected Run
```

Bare IDs or hashes never establish equality. A historical exact retry is the
one exception to fresh prerequisite collection: after the trust, intrinsic
validation, domain, metadata, decoding, index/payload-agreement, and exact
Grant-plus-Binding checks pass, it returns the already committed record without
reevaluating expiry or revocation and without sampling the clock. That record
is historical evidence, not fresh authority for dispatch.

## SQLite provisioning and connection contract

Provisioning and operational opening are separate fail-closed paths.
Provisioning selects `WAL` outside a transaction, installs `schema.sql` and one
`ledger_metadata` row atomically, and binds private schema version `1`, exact domain,
complete revocation history, and an initially null decision-time watermark.
Normal connections open that existing file read/write; they do not create,
initialize, migrate, repair, fail over, or fall back to memory. Missing,
duplicate, mismatched, unsupported, corrupt, or incomplete metadata is a
storage failure.

Every normal connection uses and verifies:

- `PRAGMA journal_mode = WAL`;
- `PRAGMA synchronous = FULL`;
- `PRAGMA busy_timeout = 5000` (a focused busy test may inject a shorter
  timeout);
- `PRAGMA foreign_keys = ON`;
- `PRAGMA locking_mode = NORMAL`;
- Python `sqlite3` with `isolation_level=None`; and
- explicit `BEGIN IMMEDIATE` for admission and first-time revocation writes.

`BEGIN IMMEDIATE`, rather than transaction opening alone, establishes the
authoritative writer order for competing Grant, Run, and revocation decisions.
A busy timeout produces a retryable storage failure; it never selects another
ledger or an in-memory fallback.

The guarded historical precheck uses one read transaction so its Grant-identity
and domain/Run lookups share one SQLite snapshot. The serialized write path
then repeats the classification before making any new decision.

The private DDL contains:

- singleton `ledger_metadata`, with immutable schema/domain/completeness
  identity and a paired nullable decision-time text/integer-key watermark;
- append-only `admissions`, keyed by
  `(authorization_domain_id, issuer_kind, issuer_id, grant_id)` and also unique
  by `(authorization_domain_id, run_id)`; and
- append-only `revocations` with the same Grant and domain/Run identities, the
  exact Grant/Run binding, and the original authenticated producer identity as
  revoker.

Revocations are unique by composite Grant identity, not by domain/Run alone:
multiple distinct Grants proposed for one Run may each need a tombstone even
though at most one can ever become an accepted admission. Their `run_id` is
still retained and checked against the exact stored Grant. If an admission
already owns the same composite Grant identity, a revocation must contain that
same complete Grant; identity rebound across the two tables is rejected.

Foreign keys tie every row to the singleton domain. `BINARY` text collation,
primary/unique constraints, and decoded exact-value checks preserve the
difference between “same ID, same value” and “same ID, different value.” SQL
triggers reject admission or revocation update/deletion, metadata deletion,
metadata identity/completeness change, watermark removal/regression, and a
text/key rebound. Pre-insert guards also reject reuse of singleton,
composite Grant, or domain/Run identities before conflict resolution. The
experiment uses plain `INSERT` and explicit reads; `REPLACE`, `INSERT OR
REPLACE`, and UPSERT/conflict-update semantics are forbidden because they could
erase or rewrite immutable history.

## Exact storage encoding

Complete Grant and Tool Binding values are stored, not merely their IDs or
hashes. Their nested Runs and Contracts therefore remain reconstructable.
Private JSON encoding is compact, sorted-key, UTF-8 JSON produced with
`sort_keys=True`, separators `(',', ':')`, `ensure_ascii=False`, and
`allow_nan=False`. Decoding rejects duplicate keys, unknown/missing fields,
wrong types, non-finite numbers, invalid nested values, and lossy timestamps.
After reconstruction and intrinsic validation, re-encoding must exactly match
the stored text and indexed identity fields. Python object `repr` is never
storage identity. This deterministic encoding is experimental, not a frozen
production serialization.

## Decision time and transaction semantics

The authority-owned injected clock is a controlled trust stub. Request time,
caller time, fixture-creation time, and an arbitrary caller-supplied machine
clock are never accepted. After `BEGIN IMMEDIATE` succeeds and all relevant
state is rechecked, a new decision samples that clock exactly once. The value
must be an aware UTC instant. The store persists both its deterministic UTC
text and its exact integer microsecond ordering key; comparisons use parsed
instants/integer keys, never lexical timestamp order.

The new-admission currentness predicate has zero implicit skew:

```text
issued_at <= decision_time < expires_at
```

Clock failure, a naive/invalid value, or a value below the domain watermark
fails closed. Equality with the watermark is permitted. Every non-regressed
clock sample used for a new-request decision advances the watermark in the same
transaction, including `not-yet-current`, `expired`, and `revoked` denials.
Those denials return only after their watermark update commits. Successful
admission insertion and watermark advancement commit atomically. Failure before
commit leaves neither consumption nor admission.

The authoritative new-request sequence is:

1. enforce trusted capabilities, intrinsic values, expected domain, and full
   Grant/Binding Run equality;
2. check for a guarded historical exact retry or deterministic identity
   conflict;
3. collect fresh prerequisites and reconstruct the expected Run;
4. acquire writer serialization with `BEGIN IMMEDIATE`;
5. recheck metadata, existing Grant identity, domain/Run uniqueness, and exact
   values inside the transaction;
6. sample the authority clock once, enforce non-regression and currentness,
   and check the same-ledger revocation tombstone;
7. advance the watermark for every valid sample and, only for success, insert
   the immutable admission; then
8. return an outcome only after a known successful commit.

The admission row is the provisional consumption record. The Grant is never
mutated with `used`, `consumed`, or `revoked`, and no `consumption_id` or
`admission_id` is introduced.

## Revocation and race ordering

A revocation is an immutable private tombstone for the complete Grant identity
and exact Grant/Run value. Only the original synthetically authenticated
issuer/producer may create it; there is no domain-administrator or delegated
authority composition. Missing revocation means “not revoked” only while the
singleton metadata proves this domain's revocation ledger complete. Unknown,
incomplete, corrupt, or unavailable state fails closed.

A first revocation also uses `BEGIN IMMEDIATE`, rechecks identity, samples the
authority clock exactly once after serialization, rejects failure/regression,
and atomically inserts its tombstone while advancing the watermark. It returns
success only after commit. An exact existing tombstone is an idempotent
historical return and does not read or advance the clock; identity rebound is a
conflict.

Serialization, not caller timestamps, decides races. A revocation committed
first causes a later new admission to reject. An admission committed first
remains immutable historical evidence when a revocation commits later; this
experiment defines no cancellation of already admitted work.

## Retries, failures, and durability claim

The same exact Grant plus the same exact Binding returns the existing durable
admission with its original decision time. A reused Grant identity with a
changed Run, Contract, Tool, or Binding is a deterministic conflict. A second
Grant for the same domain/Run conflicts through the durable unique constraint.
No winner is overwritten, and no “latest” record is selected.

A `COMMIT` exception is always `commit-unknown`: the process must not report
the intended success or denial, and it closes/discards that connection. An
exact retry against the same authoritative ledger reconciles a row-creating
admission or revocation. A denial transaction stores only the domain watermark,
not a request-bound denial record, so its retry safely reevaluates current state
but cannot prove or recover the original denial commit. Response loss after a
known admission commit returns the stored outcome without a second consumption.
Unavailable, corrupt, or persistently locked storage fails closed.

WAL plus `FULL` supports this experiment's multi-process serialization,
rollback, process-crash, and fresh-process restart evidence on a conforming
local filesystem. It does not prove survival of power loss on dishonest
hardware/controllers, filesystem corruption, backup/restore mistakes, or
operator copying. Temporary tests must terminate their workers and remove all
database, WAL, shared-memory, and journal files.

The trusted harness also assumes exclusive control of the database file and
its schema. The store verifies version/domain/completeness metadata and every
addressed immutable payload, but it does not continuously attest trigger or
index definitions against an out-of-band schema manifest. Direct arbitrary SQL
or file tampering by another owner is outside the experiment's threat model.

## Claim boundary and remaining limitations

An immutable admission contains the complete intent needed to investigate a
future outbox source, but AIO-046 adds no dispatcher, claim/lease, delivery
attempt, acknowledgement, result, event, telemetry, timeout reconciliation, or
automatic recovery. Admission is not dispatch, invocation, or success.

```text
SQLite duplicate suppression != production authorization replay protection
authorization replay protection != invocation replay protection
PERMISSION TOCTOU SOLVED?: NO
RUNTIME/INFERENCE TOCTOU SOLVED?: NO
TOOL-MAPPING TRUST SOLVED?: NO
```

Real issuer authentication, a real immutable Tool resolver, an operational
authority, and a production backend remain external. Permission and
Runtime/Inference facts can change immediately after admission. Invocation
replay still needs downstream idempotency, delivery state, provider
deduplication or status lookup, and timeout reconciliation. Post-admission
revocation semantics would require a delivery lifecycle or just-in-time
reauthorization and are outside this experiment.
