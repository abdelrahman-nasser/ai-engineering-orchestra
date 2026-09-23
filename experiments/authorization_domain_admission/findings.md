# AIO-046 Experiment Findings

Date: 2026-09-23
Status: synthetic non-production evidence; not a canonical Core contract

## Result

The experiment confirmed, within its trusted local harness, that one
file-backed SQLite ledger per authorization domain can serialize exact Grant
and Run consumption, same-ledger revocation, trusted decision time, and an
immutable admission aggregate into one atomic transaction. It did not dispatch
or invoke a Tool, and it does not establish production replay protection.

The exact focused command completed successfully:

```text
python -B -m unittest tests.test_authorization_domain_admission_experiment -v
Ran 27 tests in 5.583s
OK
```

The tests used SQLite `3.49.1` through Python's `sqlite3` module. All database
files were created below per-test system temporary directories, never in the
repository.

## Actual SQLite configuration

The provisioned database and every operational connection verified:

| Setting | Observed/required value |
| --- | --- |
| Journal mode | `WAL` |
| Synchronous | `FULL` (`2`) |
| Busy timeout | `5000` ms normally; `100` ms only in the focused busy test |
| Foreign keys | `ON` (`1`) |
| Locking mode | `NORMAL` |
| Python connection isolation | `None` (autocommit outside explicit transactions) |
| Write transaction | explicit `BEGIN IMMEDIATE` |
| Clock skew tolerance | zero |

Provisioning and operational opening are separate. Operational access uses an
existing-file read/write URI and neither creates a missing ledger nor falls
back to memory or another file.

## Evidence obtained

- A new single-process request stored the complete exact Grant, Tool Binding,
  nested Run and Contract, plus canonical authority-owned decision time.
- Admission and revocation rejected cloned trust envelopes whose visible token
  was reused with changed payload fields; rejection preceded ledger lookup,
  fresh collection, and clock sampling.
- Every new admission reconstructed AIO-040 prerequisites from new parent
  containers, prepared the expected Run through the AIO-042 API (which applies
  AIO-041 Contract preparation), reused the supplied Run ID, and required exact
  three-way Run equality.
- An exact historical retry returned the original durable record and decision
  time without recollecting prerequisites, resampling the clock, or reevaluating
  currentness/revocation.
- Deterministic conflicts were observed for changed Binding, rebound Grant
  identity, and a second Grant for the same domain/Run.
- Parsed-instant boundaries admitted at issuance and one microsecond before
  expiry, while rejecting one microsecond before issuance and exactly at
  expiry. Decision time was stored as canonical six-fractional-digit UTC text
  plus a matching integer microsecond key.
- Throwing, missing, naive, and nonzero-offset clocks failed closed. A sampled
  time behind the committed domain watermark was rejected without advancing
  it. Expired, not-yet-current, and revoked sampled decisions advanced the
  watermark atomically when their denial committed.
- Immutable exact-Grant revocation worked before and after admission.
  Revocation-first prevented admission; admission-first preserved the
  historical admission and added a later tombstone. A mutated Grant could not
  reuse an admitted composite identity across tables.
- Two spawned OS processes issuing the same request produced exactly one
  `newly_admitted` and one `existing_exact_admission`. Changed Bindings produced
  one admission and one `binding_conflict`; distinct Grants for one Run
  produced one admission and one `run_conflict`.
- A spawned writer holding `BEGIN IMMEDIATE` caused a short-timeout contender
  to return retryable `storage_busy`, with no alternate ledger, clock sample,
  admission, or watermark change.
- Raised faults and hard process exits before the transaction, after begin,
  after checks, and after insert/before commit left no admission and no
  watermark. A hard exit after commit/before response left one durable row;
  a genuinely fresh spawned process recovered it as the exact historical
  admission without fresh inputs or a clock sample.
- A normal successful spawned process was followed by a different fresh
  process that reopened the file and recovered the byte-equivalent aggregate.
- Deterministic encoding round-tripped exactly, while noncanonical/duplicate
  JSON and deliberately corrupted stored payloads failed closed. SQL triggers
  rejected admission, revocation, and metadata update/deletion.
- Guarded tests prohibited access to the lexical resource
  `synthetic/input.txt`, network sockets, and subprocess entry points while the
  transaction still succeeded. The resource remained an inert string.
- Packaging inspection confirmed that `experiments/` is absent from the
  explicit setuptools package list and package-data configuration.

## Negative counterexamples

An in-memory SQLite table disappeared when its connection closed and a new
connection opened. It is therefore not sufficient for replay protection.

Two independently provisioned SQLite files carrying the same synthetic domain
both admitted the same exact Grant and Run. This intentionally demonstrated:

```text
split ledger != valid authorization-domain architecture
```

SQLite cannot prove that two configured paths do not alias, that a path is not
cloud-synchronized or junction-backed, or that no independent copy exists.
One-domain/one-ledger and local-filesystem placement therefore remain trusted
harness/deployment preconditions, not properties inferred from the request.

## Hypotheses

Confirmed within the experiment boundary:

- writer serialization plus same-ledger constraints yields one authoritative
  order for competing admission and revocation transactions;
- admission creation and experimental Grant consumption can be one indivisible
  durable state change;
- composite Grant identity and domain/Run uniqueness suppress duplicate
  authority consumption across local processes sharing one file;
- exact historical retry is sufficient to recover row-creating success after
  response loss without turning expiry into an unrecoverable outcome;
- a persisted monotonic decision-time watermark provides a fail-closed local
  response to authority-clock regression; and
- complete exact values can detect identity rebound that ID-only or hash-only
  storage would conceal.

Rejected or deliberately bounded:

- memory is not durable across process restart;
- separate database files cannot provide domain-wide uniqueness;
- transaction success does not prove dispatch, invocation, or operation
  success;
- local SQLite duplicate suppression is not production authorization replay
  protection and is not invocation replay protection; and
- a watermark-only denial can be safely reevaluated after ambiguous response
  loss, but the original denial commit cannot be proven or reconstructed.

## Outbox finding

The immutable admission retains enough exact intent to be a candidate source
record for a later dispatcher: Grant, Binding, Run, Contract, resource,
execution mode, and authoritative decision time are present. It is not a safe
outbox by itself. It lacks claim/lease state, delivery attempts,
acknowledgement, a downstream idempotency key, provider deduplication/status
lookup, timeout reconciliation, cancellation, and result/event semantics.

## Required work before AIO-047 or production use

- Define backend-neutral canonical semantics from this evidence; do not adopt
  the private SQL tables, JSON encoding, outcome strings, or Python API as-is.
- Add real issuer authentication and authorization, real immutable Tool
  resolution, and a production authority-clock boundary.
- Choose and enforce domain-to-ledger ownership in deployment, including path,
  replication, failover, backup/restore, and migration rules.
- Decide whether request-bound denial records are needed for stronger
  commit-ambiguity reconciliation.
- Define the production threat model for schema/index/trigger integrity. This
  experiment assumes exclusive trusted control of the database file and does
  not continuously attest DDL against an external manifest.
- Address permission, Runtime, Inference, and Tool-mapping TOCTOU separately.
- Design any dispatch/outbox lifecycle and invocation idempotency separately,
  with its own Human approval and failure experiments.
- Validate a production backend under its real crash, replication, isolation,
  and durability model.

## Remaining limitations

The evidence is bounded to synthetic trusted stubs, one local filesystem,
SQLite's reported commit behavior, and process-crash tests. It does not prove
power-loss survival on dishonest storage hardware, filesystem corruption
recovery, malicious local database tampering, distributed consensus,
production authentication, or external-state freshness after admission.

```text
PERMISSION TOCTOU SOLVED?: NO
RUNTIME/INFERENCE TOCTOU SOLVED?: NO
TOOL-MAPPING TRUST SOLVED?: NO
REAL DISPATCH?: NO
REAL INVOCATION?: NO
```
