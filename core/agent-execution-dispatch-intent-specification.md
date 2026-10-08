# AI Engineering Orchestra - Agent Execution Dispatch Intent Specification

Status: Canonical semantic contract for AIO-055

Version: 0.1.0

Scope: Immutable private dispatch-intent persistence in the authoritative
local SQLite Admission ledger; no dispatch or invocation

## 1. Meaning and boundary

An **Agent Execution Dispatch Intent** is the immutable same-ledger record
that one newly admitted action entered the dispatch-intent foundation. It is
logically separate from its authoritative Agent Execution Dispatch Admission,
while sharing the Admission's exact Grant-composite identity.

The supported production-path endpoint is:

```text
trusted pre-execution path
-> authoritative Admission and immutable Dispatch Intent committed atomically
-> STOP
```

Intent presence is historical persistence, not current dispatch eligibility,
an execution capability, permission, a Claim, a worker Lease, delivery,
invocation, a Result, or success. A later authorization/Claim contract must
establish its own current prerequisites. Later revocation preserves the
immutable Admission and Intent and grants no continuing authority.

This specification governs the AIO-055 local SQLite extension of AIO-047.
It does not change the backend-neutral Admission protocol or require a new
public serialized value, public schema, or package export.

## 2. Identity and immutable parent relationship

Logical identity is exactly the existing Admission Grant composite:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

Identifiers retain their canonical case-sensitive lexical representation.
There is no dispatch_id, intent_id, request retry ID, alternate Run ID, or
identity normalization. The existing Admission domain/Run unique constraint
remains separate from the Grant-composite identity.

The private table `agent_execution_dispatch_intents` contains only those four
nonempty TEXT COLLATE BINARY identity columns. Its composite primary key
permits at most one Intent. A restrictive composite foreign key references
the immutable `agent_execution_dispatch_admissions` parent.

The exact complete Grant, nested Run/Contract, trusted Binding and decision
time are inherited from that verified immutable parent. The Intent stores
no copied payload, Run key, Tool ID, timestamp, status, worker identity,
credential, transport descriptor, or mutable workflow state. Full canonical
parent decoding and index/payload verification remain mandatory before
authoritative classification or disclosure.

The configured domain, ledger instance, generation and supported AIO-049 file
pin establish ledger authority. A copied key or reconstructed private value
does not establish operational authority.

## 3. Complete immutable classification

Every committed Admission has exactly one of:

- one immutable Agent Execution Dispatch Intent; or
- one immutable legacy non-dispatchable marker.

The two sets are disjoint and their union is exactly the Admission set.
Neither overlap nor missing classification is a valid operational state.

The private `legacy_admission_markers` table contains the same composite key
plus migration_id fixed to 2. It has restrictive Admission and migration-history
foreign keys; the latter is deferred within explicit migration. Markers are
created only in the dirty supported v1-to-v2 administrative transition.
Historical v1 Admissions never receive Intents.

Both tables use strict immutable identity, duplicate/REPLACE rejection,
reciprocal overlap rejection, and unconditional UPDATE/DELETE rejection.
A marker is never converted to an Intent. Dispatching historical work later
requires a new authorized Run chain.

SQLite enforces at-most-one and referential/overlap constraints. The supported
Store additionally enforces completeness through full consistent-snapshot and
same-transaction precommit audits. It never commits a supported operation
with an unclassified Admission and never repairs missing classification.

## 4. Atomic authoritative transaction

AIO-047's Store remains the sole transaction owner. A new Admission follows
the existing owned coordinator and BEGIN IMMEDIATE writer path. After its
existing history, equality, revocation, clock and currentness checks, it
inserts the immutable Admission, inserts exactly one matching Intent, advances
the existing decision-time watermark, audits the complete final state, and
commits once.

Admission and Intent become durable together or neither becomes durable.
A second transaction that backfills an Intent after Admission commit is
prohibited. No coordinator, Producer, retry path, worker or external caller
owns a separate Intent write.

The temporary interval between the two INSERTs is uncommitted; no successful
result or authoritative historical disclosure may expose it.

## 5. Migration and exact retry

Explicit administration applies checksummed migration
`0002_dispatch_outbox.sql` after proving exact v1 source identity, schema,
history prefix, canonical payloads, integrity, foreign keys, state and
watermark. It preserves migration-1 bytes/history and all historical security
records, and atomically marks every prior Admission as legacy with zero
historical Intent backfill. Full destination verification precedes COMMIT.

Operational open never provisions, migrates or repairs. Unknown, old, dirty,
partial, checksum-mismatched, fingerprint-mismatched or corrupt state fails
closed.

An exact authenticated historical retry verifies the complete authoritative
Admission and its exact classification, returns its original value, and
creates nothing. It samples no clock, recollects no prerequisites, reevaluates
no historical expiry/revocation, and changes no watermark.

Commit-unknown reconciliation uses only the exact same configured pinned
ledger and complete original request. A committed pair is returned as
history; an intact no-pair state may enter the existing fresh Admission path.
Malformed half-state fails closed rather than being repaired. Migration
ambiguity similarly recognizes intact verified v1 or complete verified v2
only; it does not select another ledger or rerun blindly.

AIO-053's AIO-050 opaque presentation remains process-local. Durable Store
history does not manufacture integrated cross-restart authentication or
presentation recovery.

## 6. Private future seam and exclusions

Store-owned private classification/dereference returns only immutable verified
history within the owned boundary. It does not expose a mutable connection,
raw SQL authority, public enumerator, dispatchable boolean, or worker selector.

AIO-056 extends this internal seam with private controlled Intent selection,
append-only Claim/Renewal and generation fencing in schema v3. Its exact
semantics are governed by
`core/agent-execution-dispatch-claim-lease-specification.md`; the Intent value
and public Admission contract are unchanged. AIO-055 itself contains no Claim,
Lease, Renewal, reclaim, executor
identity, worker API, dispatch loop, queue consumer, transport, Tool probe,
credential resolution, resource read, Tool invocation, Result or external
effect.

AIO-055 implementation validation uses canonical production components with
synthetic authority edges and disposable local ledgers. It does not dispatch
actual user workloads. Final Quality Gates and Human acceptance remain
separate from Phase-2 implementation evidence.
