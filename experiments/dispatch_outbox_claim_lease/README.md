# AIO-054 Dispatch Outbox and Claim-Lease Experiment

This directory is a private, disposable, noncanonical experiment. It tests
transaction and claim/lease hypotheses for AIO-054. It is not production code,
is not part of the package surface, and defines no public schema or Core
contract.

Successful results do not establish canonical AIO-049 integration or authorize
dispatch, Tool invocation, repository-resource access, credentials, Result
handling, or external side effects.

## Experiment boundary

The experiment models:

- one-transaction Admission and immutable Dispatch Intent creation;
- legacy Admission classification without pending-work backfill;
- immutable Intents, append-only Claims, and append-only Lease Renewals;
- exact committed-history retry and explicit no-row reevaluation;
- Lease expiry, reclaim, monotonic generation fencing, and Renewal ordering;
- trusted UTC, half-open expiry, and a non-regressing decision-time watermark;
- same-ledger revocation ordering;
- crash, response-loss, restart, corruption, and local SQLite contention; and
- an in-process lifecycle surrogate around complete coordinator operations.

It stops before transport or invocation.

## Evidence lanes

Two evidence lanes remain deliberately separate:

1. Spawned local processes exercise raw SQLite writer contention, crash, busy,
   and restart mechanics against disposable ledgers.
2. An in-process lifecycle surrogate exercises operation entry, concurrent
   guards, post-Store revalidation, loss, terminal fencing, and quiescence.

The lifecycle surrogate is not the production AIO-049 owner. The canonical
owner rejects this private extended schema, so real owner/Store integration is
deferred to a separately authorized production-design Task. Results from the
two lanes must not be composed into a multiprocess operational-worker claim.

## Files

- `schema.sql` records the private current schema as review evidence.
- `store.py` contains the self-contained SQLite experiment Store and embedded
  runtime schema.
- `worker_harness.py` contains the process-local Executor capability,
  lifecycle surrogate, coordinator, and raw storage probes.
- `findings.md` records Phase 2 evidence and hypothesis classifications.
- `tests/test_dispatch_outbox_claim_lease_experiment.py` contains exactly 128
  separately discoverable locked-scenario tests.

Production modules do not import any experiment module. Experiment runtime
code imports no production module.

## Locked profile

The supported storage profile is:

- Windows, current user, same host, and a fixed local NTFS disposable ledger;
- SQLite 3.37.0 or newer;
- WAL journal mode, `synchronous=FULL`, foreign keys enabled, normal locking;
- autocommit outside explicit transactions and `BEGIN IMMEDIATE` writers;
- exact `busy_timeout=2000` configuration; and
- fixed Store-owned Lease duration of 30,000,000 microseconds.

The held-writer test treats 2000 milliseconds as configuration, not an exact
elapsed-time oracle. Its diagnostic observation window is 0.5 through 15.0
seconds.

Administrative migration quiescence is an external, unconfirmed precondition.
In WAL mode, `BEGIN EXCLUSIVE` serializes writers but does not prove reader or
multiprocess quiescence.

## Authorized execution

Phase 2 uses the exact bounded command recorded in the AIO-054 Validation
Safety Matrix:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' `
  -E -s -B -m unittest `
  tests.test_dispatch_outbox_claim_lease_experiment -v
```

The command must run from the repository root only after static inspection of
the complete experiment, test, import, subprocess, network, and target closure.
It performs no test discovery.

Markdown validation uses only the pinned offline
`markdownlint-cli2@0.23.3` executable, `--no-globs`, and the exact paths listed
in the Validation Safety Matrix.

## Interpreting results

A passing scenario supports only the bounded hypothesis it names. It does not
establish production suitability, canonical ownership integration,
exactly-once invocation, or exactly-once external effects. Production
recommendations and remaining blockers are recorded independently in
`findings.md`.
