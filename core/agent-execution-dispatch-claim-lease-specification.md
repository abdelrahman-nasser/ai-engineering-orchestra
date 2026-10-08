# AI Engineering Orchestra - Dispatch Claim-Lease and Fencing Specification

Status: Canonical private local persistence contract for AIO-056

Version: 0.1.0

## 1. Meaning and identity

A Dispatch Claim is an immutable ownership attempt against one verified
production Dispatch Intent. Its logical dispatch identity remains exactly
`(authorization_domain_id, issuer_kind, issuer_id, grant_id)`. There is no
dispatch_id. Claims and Renewals are private local-ledger values; no public
Admission, Intent, schema, protocol or package export changes.

Claim, Lease and historical disclosure establish no Tool invocation authority.
Admission is not continuing authority; Intent is not authority. A later Task
owns final invocation/JIT authorization, delivery and Result handling.

## 2. Attempt and executor identity

The trusted caller supplies claim_id and renewal_id as exact 64-character
lowercase hexadecimal opaque tokens. IDs are ledger-wide unique within their
respective append-only histories. A committed ID cannot be rebound. A no-row
attempt consumes no ID and may be explicitly reevaluated later. Fresh reclaim
requires a new claim_id; retry never silently generates one.

The local adapter creates a fresh random 32-byte executor_instance_id for each
logical worker incarnation. Its nonserializable immutable capability binds the
exact genuine AIO-049 concrete owned session and current process. A copied ID,
Actor, Runtime, PID, machine or Grant identity is not that capability. Restart
or a new logical incarnation gets a new executor identity. Capability copying,
pickling, reconstruction and transfer across sessions/processes fail closed.

The private facade composes the session's existing Store. Its unchanged
`session.operation()` covers request creation, complete Store operation,
result validation and successful post-check before disclosure. Terminal
ownership loss prevents current evidence. This does not change AIO-049 APIs,
file pinning, operation-count quiescence or lifecycle semantics.

## 3. Time and generation

Trusted UTC wall time is sampled once per fresh timed transaction. The exact
datetime must be UTC-aware, with zero offset; naive, non-UTC, wrong-type,
throwing and overflow values fail closed. Canonical text is exactly
`YYYY-MM-DDTHH:MM:SS.ffffffZ`, 27 characters, with an integer microsecond key
from ordinal day 1. Keys range from 0 through 315537897599999999.

The shared durable Admission/revocation watermark never regresses. Equal
samples are permitted; rollback is rejected without clamping or fallback.
The watermark audits decision times, not future Lease expiry. Historical
queries and exact committed retries neither sample time nor advance it.

Lease duration D is fixed at 30000000 microseconds. Validity is half-open:
`acquired_at <= now < effective_lease_until`. Initial and renewed expiry are
the sampled decision time plus D, never the preceding expiry plus D.

Per-Intent generations begin at 1 and increase exactly by 1 on each reclaim.
Renewal sequences begin at 1 per Claim and increase exactly by 1. Both are
positive signed-64 integers, maximum 9223372036854775807. Exhaustion fails
closed without wrap, reservation, watermark change or candidate skipping.

## 4. Claim transaction and eligibility

The Store owns one BEGIN IMMEDIATE transaction. It validates the complete
schema/history and first reconciles a committed claim_id. Equal original
executor facts return original immutable history even after expiry,
supersession or revocation. Another executor gets a conflict without evidence.

Fresh selection considers only production Intents with fully decoded exact
Admission/Grant/Run/Binding parents and no same-ledger revocation. Legacy
Admissions cannot be claimed. Consumed Grant interval expiry is not reevaluated;
this is the locked ledger/revocation policy, not JIT execution authorization.

Candidates sort by Admission decision-time key, then the four identity fields
using BINARY ascending order. The first unclaimed or expired candidate wins.
There is no fairness promise. Empty sets and entirely revoked sets are untimed
negative outcomes. All-active sets sample time and may commit only a watermark
advance, without a durable denial receipt or consuming the attempt ID.

For an eligible candidate, the Store allocates 1 or highest generation plus 1,
appends Claim, advances watermark, audits the entire resulting snapshot, and
commits once. No Claim can commit separately from valid immutable parent
history. Complete prior Renewal history determines predecessor expiry.

## 5. Renewal, reclaim and queries

Fresh Renewal requires exact identity, claim_id, executor capability and
generation for the highest Claim, with an active nonrevoked parent. Missing,
mismatched, superseded or revoked tuples reject before sampling time. Expired
Claims cannot be revived. Live Renewal computes now plus D; only a strict
extension appends the next sequence. Expired/nonextending timed negatives may
advance watermark but consume no renewal_id or sequence.

Exact committed renewal_id retry first checks every bound field. It returns
the original history without time, watermark or a second extension. Conflicting
reuse fails closed. Reclaim appends a new Claim at the complete effective
expiry or later; it preserves every predecessor row and fences older
generations from fresh Renewal/current assessment.

History query accepts claim_id alone inside the genuine same-ledger owned
facade. It returns the exact Claim and ordered Renewals without requiring the
lost executor capability or previously unknown selected tuple. History is
explicitly history-only and never restores authority. Current query requires
the exact capability/tuple/generation and serialized fresh time, highest-row,
revocation and watermark assessment; it is point-in-time evidence.

## 6. Durable v3 representation and auditing

Migration `0003_dispatch_claim_lease.sql` adds STRICT WITHOUT ROWID append-only
`agent_execution_dispatch_claims` and `agent_execution_dispatch_renewals`.
Claims reference the Intent composite; Renewals reference the exact Claim,
dispatch composite, executor and generation. Restrictive foreign keys,
unique generation/sequence keys and unconditional update/delete/duplicate/
REPLACE guards protect immutable history. Insert guards enforce active clean
v3 state, current parent/revocation, contiguous allocation, ordering and expiry.
0003 replaces only the Intent active-clean-version insert guard with v3.

Every open/read/write/precommit audits the complete authoritative snapshot,
including unrelated candidates and old chains. It rejects orphan/mismatched
parents, missing/overlapping classification, gaps, duplicate/regressing
generations/sequences, overlapping ownership, Renewal after supersession or
expiry, incorrect D/arithmetic, noncanonical text/key/token values, decisions
after revocation, watermark inconsistency and schema/history drift. No repair
or selective corruption skipping is permitted.

## 7. Migration and recovery

0001 and 0002 remain byte-exact. Explicit same-pin trusted AIO-049
administration proves quiescence and exact source before BEGIN EXCLUSIVE,
then repeats verification. v2 classification XOR is audited even though v3
is current. v2-to-v3 preserves Admissions, revocations, Intents, legacy markers
and watermark exactly, with empty new histories. v1-to-v3 applies 0002's
legacy-only classification then 0003 in the same administrative transaction.
No Claim backfill occurs. Operational open never auto-migrates.

Migration uses allowlisted checksums, version-specific manifests/fingerprints,
contiguous history and complete clean destination verification. Precommit
crashes preserve the original source. Postcommit ambiguity recognizes verified
v3 already_current; intact verified old source permits explicit retry. WAL
writer serialization alone does not prove administrative quiescence.

Claim/Renewal/reclaim commit_unknown reconciles only the same pinned ledger
and original attempt ID. A committed row returns exact history; intact no-row
state may reevaluate current prerequisites. Corrupt or mixed history fails
closed. Never switch ledgers, synthesize rows, replace IDs or restore a lost
executor. Post-check loss can coexist with committed history and discloses no
current ownership evidence.

## 8. Supported guarantee and exclusions

Under the declared local storage, ownership, clock and trusted-caller
preconditions, this foundation provides crash-durable immutable Claim/Renewal
history, deterministic serialized acquisition, contiguous generation fencing
and same-ledger reconciliation. Canonical logical workers share one genuine
process-owned session; raw multiprocess probes demonstrate storage mechanics
only. No multi-machine ownership or malicious-admin tamper resistance is
claimed.

No executor launch, worker loop, command/resource execution, Tool invocation,
network transport, Result, DAG/multi-agent scheduling or exactly-once invocation
is implemented. Storage test subprocesses are disposable mechanics probes.
Phase-2 validation is separate from final independent review, Quality Gates
and Human acceptance.
