# AIO-055 Context and Production Design Lock

## Authorization and baseline

Phase 1 (Task creation and production design lock) is complete. The Human
explicitly authorized Phase 2 production implementation and focused validation
on 2026-10-07. The subsequent explicit offline tooling authorization
resolved P1/O55; the isolated local-wheelhouse build and full package-surface
inspection passed. Phase 2 is COMPLETE: 60 locked scenarios PASS, 0 FAIL,
0 SKIP. AIO-055 was completed on 2026-10-07. The Phase-2 completion record below
predates the separately authorized final Quality Gate phase.
The Human has now explicitly authorized final AIO-055 Quality Gate evaluation.
Fresh specialist and Formal Independent Reviews report APPROVE, with a
COMPLIANT fresh process assessment. Human final approval was explicitly
granted on 2026-10-07. Task closure was separately authorized and completed;
one local commit is authorized, with no push. AIO-056 is neither
created nor implemented. Fresh design is LOCKED: all five independent design review scopes APPROVE, with zero unresolved
blocker/high findings; evidence is recorded in review.md.

On 2026-10-07 the five requested baseline commands established:

| Check | Observed |
| --- | --- |
| Branch | `main` |
| HEAD | `14e8f16f6ac9d0cf10013068eee6da62861d0788` |
| Worktree, including all untracked files | Clean before Task creation |
| Unstaged diff stat | Empty |
| Cached diff stat | Empty |
| Exact candidate Task directory | Absent; AIO-055 AVAILABLE: YES |

Only the exact AIO-055 candidate was checked for availability. No Task catalog
was enumerated. The three-level classification is explicitly selected by the
Human: high Complexity, critical Risk, critical Execution Mode. The selected
`architecture-change` Workflow's Task-type hints are advisory, so its explicit
binding to an implementation Task is valid.

The direct dependency set is AIO-047 (authoritative ledger), AIO-049 (owned
administration and operations), AIO-053 (integrated trust path), and AIO-054
(experimental evidence). AIO-050 and AIO-051 are transitive through AIO-053;
their unchanged operational contracts still apply.

## Sources and evidence limits

Relevant authoritative sources were read at exact paths:

- `.ai/project.yaml`, Core principles, terminology, and precedence;
- `core/task-specification.md` and `schemas/task.schema.json`;
- `workflows/architecture-change.yaml` and its specification;
- `roles/architect.yaml`, `roles/software-engineer.yaml`,
  `roles/reviewer.yaml`, and `roles/security-reviewer.yaml`;
- documentation-consistency and independent-review Gate definitions;
- `core/agent-execution-dispatch-admission-store-specification.md`;
- `core/authorization-domain-ownership-specification.md`;
- `core/local-operational-trust-integration-specification.md`;
- the exact SQLite Store, migration manifest, unchanged
  `0001_initial.sql`, owned-session implementation, and integrated coordinator.

`.ai/rules/` contains no Project Rules. No Stack Module is needed for this
bounded Python/SQLite design.

AIO-054 remains completed at the baseline commit. Its Human-provided closure
record is 171/171; its experiment findings separately record 128 fresh locked
experiment scenarios. Neither count is fresh AIO-055 validation. The exact
`experiments/dispatch_outbox_claim_lease/README.md` and `findings.md` inform
atomicity, classification, retry, crash, response loss, and WAL/restart design.
Their experimental ownership surrogate is not canonical AIO-049 integration.
No experiment module is copied into or imported by production. No additional
preimplementation experiment is required; if a genuinely unproven production
seam emerges, stop for Human direction rather than executing an experiment.

## Objective and endpoint

Extend the authoritative AIO-047 authorization-domain SQLite ledger so every
newly committed dispatch-enabled Admission is atomically accompanied by
exactly one immutable Agent Execution Dispatch Intent, while safely
classifying pre-outbox historical Admissions as legacy non-dispatchable,
without introducing Claim/Lease, dispatch transport, Tool invocation, or
Result semantics.

The endpoint is:

```text
trusted pre-execution path
-> authoritative Admission
-> durable immutable Agent Execution Dispatch Intent
-> STOP
```

Intent existence is immutable dispatch-intent history. It does not establish
current eligibility, ongoing authority, dispatch, invocation, or success.

## Identity and minimum private durable representation

Logical Dispatch identity is the existing exact, case-sensitive Grant
composite:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

There is no separate public or private allocated dispatch ID. The existing
Admission `(authorization_domain_id, run_id)` unique index remains the
separate Run cardinality/integrity constraint.

Lock two private same-ledger tables:

| Table | Durable columns | Keys and relationship |
| --- | --- | --- |
| `agent_execution_dispatch_intents` | The four Grant-composite columns only | Composite primary key; exact composite FK to `agent_execution_dispatch_admissions`, ON UPDATE/DELETE RESTRICT |
| `legacy_admission_markers` | The same four keys plus `migration_id` fixed to 2 | Same primary key/FK; migration ID CHECK = 2 and deferred FK to `admission_schema_migrations.migration_id` with ON UPDATE/DELETE RESTRICT |

Both use STRICT, WITHOUT ROWID and the existing TEXT COLLATE BINARY identity
representation. All identity columns are NOT NULL/nonempty; issuer kind is
restricted to the canonical human/policy vocabulary. Do not normalize, case
fold, trim, or allocate identity.

A keys-only Intent anchors the exact existing immutable Admission, whose
canonical payload already contains the complete Grant, nested Run/Contract,
trusted Binding, and authoritative decision time. The FK plus verified
parent immutability establishes the payload relationship. There is no
independent Intent JSON, duplicated Admission/Run payload, copied Tool ID,
status, timestamp, worker field, or repeated Run key. Exact Run integrity is
inherited through the parent's unique domain/Run constraint and full
canonical index/payload verification. A private frozen reference/classification
returned within the Store may include the verified Admission in memory;
it is not a public serialized value or package export.

The ledger's singleton domain FK, unchanged ledger_instance_id/generation,
and configured ownership/file pin establish exact domain/ledger relationship;
a key copied to another ledger establishes no authority.

PUBLIC ADMISSION SCHEMA CHANGE: NO. Admission remains exactly `grant`,
`tool_binding`, and `decision_time`. PUBLIC DISPATCH INTENT VALUE NEEDED: NO.
PUBLIC JSON SCHEMA NEEDED: NO.

## Constraints, immutability, and complete classification

The migration adds exact primary/FK constraints, reciprocal BEFORE INSERT
anti-overlap guards, BEFORE INSERT duplicate guards (including attempted
REPLACE), and unconditional UPDATE/DELETE rejection for both new tables.
A marker can be inserted only in the trusted dirty v1-to-v2 migration window;
ordinary v2 operations cannot mark a new Admission as legacy. Intent insertion
requires active, clean v2 operational state. No caller may choose a
dispatch-enabled flag or classification.

For every durable Admission exactly one classification must exist:

```text
Intent XOR legacy non-dispatchable marker
```

SQLite constraints provide at-most-one, referential integrity, and no overlap.
They cannot supply a deferred cross-table completeness assertion for this
additive design. The supported Store therefore MUST run a full same-transaction
classification/payload audit after mutation and before each successful commit,
including migration, and at every operational open/history/read/mutation
verification boundary. The temporary new Admission without its Intent is
uncommitted and is never disclosed as success. No supported mutation path may
commit an unclassified Admission.

The audit proves:

- Intent keys and marker keys are disjoint;
- their union equals all Admission keys, with no missing classification;
- neither set has an orphan or duplicate;
- each Intent dereferences exactly one canonically valid immutable Admission;
- indexed Grant composite, domain/Run identity, nested Grant/Binding Run,
  canonical JSON, decision-time text/key, and metadata all agree;
- marker provenance is the exact migration-2 history entry; and
- schema DDL fingerprint, checksums, migration history, active/clean state,
  ledger identity, revocation completeness, and watermark are valid.

This is the supported owned Store boundary, not a guarantee against arbitrary
SQL writers, a malicious local administrator, or disabled constraints.
Operational code never fills a missing row or repairs a mismatch. Any missing,
overlapping, orphaned, duplicated, malformed, or mismatched state fails closed.

## Exact AIO-047 transaction seam

The unchanged baseline
`engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py`
owns `SqliteAgentExecutionDispatchAdmissionStore.admit_or_return_existing()`.
Its baseline transaction starts at line 1713; Admission insertion completes
at line 1816; the existing `after_insert_before_commit` cut is at line 1817,
watermark advancement at line 1818, and commit at line 1820. These line
references identify baseline evidence, not guaranteed future line numbers.

Add Intent insertion directly after the Admission INSERT and before watermark
advancement/COMMIT in that same existing connection and transaction. Preserve
the old fault cut, add precise post-Admission/pre-Intent and post-Intent cuts,
and audit final classification before attempting commit.

```text
BEGIN IMMEDIATE
-> authoritative schema/identity/payload/classification verification
-> existing history/conflict classification
-> complete request/expected Run equality recheck
-> existing revocation ordering and trusted clock/currentness checks
-> insert immutable Admission
-> insert one exact keys-only immutable Dispatch Intent
-> advance existing sampled-now watermark
-> final complete v2 invariant verification
-> COMMIT
```

Prerequisite collection/reconstruction stays in the existing trusted
coordinator before the Store call. The Store retains the serialized
three-way Run recheck; it does not add a second prerequisite producer or
duplicate Admission logic outside the Store.

Only the positive new-Admission branch inserts an Intent. Existing temporal
and revocation-denial branches retain their AIO-047 watermark rules and
insert no Admission/Intent. Equal watermark time remains allowed; regression
or clock failure remains rejected. Migration and exact historical retry do
not sample time or change the watermark.

## Historical migration and administration

MIGRATION FILE:
`engineering_orchestration/_sqlite_admission_migrations/0002_dispatch_outbox.sql`.

Keep `0001_initial.sql` byte-for-byte unchanged and preserve migration 1's
SHA-256:

```text
6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed
```

The source v1 DDL fingerprint remains:

```text
de080810b1d644dacf53e6bf79cbbd01343344904397a91c6dd483bd48dfad46
```

The migration manifest adds only ordered migration 2 and its immutable SHA-256
of canonical UTF-8/LF bytes. Lock a version-indexed allowlist of exact source
and destination DDL fingerprints and prefix manifest IDs. Derive each manifest
ID with the existing newline-joined migration-id/resource-name/checksum
algorithm, over the exact prefix for that version. Numeric version alone is
insufficient. At design lock the v2 values were intentionally not invented. Fresh
Phase-2 computations from the stable actual production bytes are recorded in
review.md; they are separate from the blocked packaged-archive check.

AIO-047 `migrate()` already owns explicit BEGIN EXCLUSIVE administration.
At the Phase-1 baseline its old-version branch did not fully verify a
version-specific source prefix and the operational verifier expected the latest
full manifest. AIO-055 now implements admin-only version-aware source
verification while retaining current-only operational verification.

Migration order is locked:

1. Enter existing trusted AIO-049 administrative composition with separately
   established administrative entitlement and exact supported domain/file pin.
   Quiesce conforming operations; the OS domain lock serializes administration.
   BEGIN EXCLUSIVE under WAL alone does not prove reader/process quiescence.
2. Verify exact configured ledger/domain/instance/generation, active/clean v1,
   application_id/user_version agreement, preserved v1 DDL fingerprint,
   exact migration-1 history prefix and manifest ID, integrity/FK checks,
   complete canonical Admission/revocation payloads and watermark.
3. Acquire BEGIN EXCLUSIVE; repeat the complete source verification under that
   serialization boundary before any dirty mutation.
4. Set migration_state dirty inside the transaction; execute only allowlisted
   checksummed migration-2 statements; create tables/guards and insert one
   immutable legacy marker per existing v1 Admission, with migration_id 2.
   The migration-history FK is deferred until the same transaction records 2.
   Create ZERO historical Intents.
5. Audit complete destination classification and exact v2 DDL before publication.
   Append the exact migration-2 history record without changing migration 1;
   set metadata version/manifest and PRAGMA user_version to 2; mark clean.
   Preserve activation, ledger identity/generation, Admissions, revocations,
   canonical payloads, and watermark.
6. Before COMMIT, verify exact complete v2 DDL fingerprint/history/metadata
   and the full XOR/union/payload invariant in the same transaction.
7. Commit once; retain same-file pin/ownership post-verification.

Fresh current-v2 provisioning retains the existing provision() API and its
single transaction: apply exact 0001 plus 0002, initialize complete v2
metadata/history, create zero legacy rows or Intents on the empty ledger, and
run the full v2 audit before COMMIT and supported reopen. No new provisioning
API or implicit operational provisioning is added.

Empty and nonempty valid v1 ledgers are migratable under these conditions.
Existing Admissions become permanently non-dispatchable markers, including
Admissions later revoked. No historical work becomes an Intent. A later
attempt requires a newly authorized Run chain.

Source corruption, partial migration, unknown newer schema, unsupported old
schema, checksum/fingerprint/prefix mismatch, dirty state, or insufficient
ownership/entitlement fails closed before mutation. A valid current v2
migration retry is `already_current` after complete verification. No
operational open repairs, provisions, or migrates.

Crash before migration commit leaves intact v1 history, metadata, payloads,
and schema. Commit ambiguity is reconciled only against the exact same
configured pinned file: intact validated v1 permits explicit migration retry;
complete validated v2 permits already-current; mixed/dirty/corrupt state fails
closed. No alternate path, replacement database, restore, or guessing.

The fallback (refuse nonempty-v1 migration) is reserved only for a fresh
Storage review that cannot prove marker safety. It is not the selected design.

## Retry, ambiguity, and ownership compatibility

History is disclosed only after existing authenticated Grant, expected-domain,
trusted Binding, and exact complete Run checks. Full v2 classification and
immutable-parent verification precede every historical return.

An existing exact new Admission must have exactly its Intent and no marker.
An existing exact legacy Admission must have exactly its marker and no Intent.
Both return the unchanged historical Admission/decision time, create nothing,
collect no fresh prerequisites, sample no clock, re-evaluate no expiry or
revocation, and advance no watermark. Preserve existing Grant-identity,
Binding, and domain/Run conflict precedence and typed retry outcomes.

Admission commit_unknown uses the same complete Grant/Binding and same pinned
ledger. Complete durable pair yields historical success; no pair allows the
existing fresh preparation/currentness path; any malformed half fails closed.
No retry manufactures an Intent for a committed Admission.

AIO-049's unchanged Owned Session operation lease spans trust checks,
reconstruction, guarded history, Store mutation, and post-validation.
It is an ownership lifecycle guard, not a dispatch worker Lease. Migration
uses the existing administrative access capability and same-file pin;
the OS lock is serialization, not proof of Human/policy entitlement.

If ownership is lost around or after a durable commit, do not report live
authority or pretend rollback undid a committed pair. Follow existing
fail-closed outcomes; recover only through an authorized exact same-ledger
history path. Terminal fencing permits only supported non-authoritative
audit; never reanimate the old session or silently select a replacement ledger.

AIO-053 same-live-session exact retry remains unchanged. Its AIO-050 opaque
presentation is process-local and cannot be reconstructed after process
restart. Store/WAL/process-restart durability tests do not establish integrated
cross-restart presentation recovery. Store-level exact retry after restart
requires an independently available conforming original authentication path;
the current integrated Producer offers none. A new integrated session follows
the existing new-Run/fresh-authority/new-Grant rules. No presentation
serialization, persisted proof, or new Producer retry contract is introduced.

## Minimal Phase-2 file plan

These paths were locked during Phase 1 and are now authorized for Phase 2.
The plan is preserved; no Claim/Lease or architecture expansion is authorized.

| Path | Minimum intended change |
| --- | --- |
| `core/agent-execution-dispatch-intent-specification.md` | New canonical semantic concept; private representation and no execution authority |
| `core/agent-execution-dispatch-admission-store-specification.md` | Extend local SQLite transaction, classification, migration, corruption, retry and ownership requirements |
| `core/terminology.md` | Add Agent Execution Dispatch Intent and legacy-classification meaning |
| `core/local-operational-trust-integration-specification.md` | Narrow endpoint/persistence consistency update; preserve process-local presentation limits |
| `engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py` | Same-transaction Intent insertion, keys-only private classification/dereference, full audit, version-aware admin migration and fingerprint/prefix checks |
| `engineering_orchestration/_sqlite_admission_migrations/0002_dispatch_outbox.sql` | Additive immutable Intent/legacy tables, constraints/guards and marker-only backfill |
| `engineering_orchestration/_sqlite_admission_migrations/__init__.py` | Append migration 2 checksum; retain exact migration 1 |
| `engineering_orchestration/local_operational_trust.py` | Narrow existing module docstring persistence/endpoint consistency only |
| `tests/test_atomic_durable_dispatch_outbox.py` | Fresh locked production scenario evidence |
| `tests/test_sqlite_agent_execution_dispatch_admission_store.py` | Exact existing schema/migration/transaction compatibility expectations |
| `tests/test_windows_local_authorization_domain_owner.py` | Existing owned migration/operation integration evidence using isolated fixtures |
| `tests/test_local_operational_trust.py` | Integrated endpoint and same-session retry/negative-boundary evidence |

No public coordinator protocol/outcome change is needed in
`agent_execution_dispatch_admission_store.py`. No ownership contract or
adapter control-flow/API change is required in AIO-049. No AIO-053 API or
control-flow change is required. AIO-047 Store and transaction changes are
required. No pyproject change is needed: its explicit migration package already
includes `*.sql`; verify packaged 0001/0002 resources prospectively.

## Future AIO-056 internal seam and exclusions

Leave Store-owned private immutable classification/dereference helpers
covering Intent versus legacy history. They return verified immutable
references/Admission data inside the owned boundary and never expose a
connection, mutable SQL handle, public enumerator, dispatchable boolean, worker
override, or capability token.

AIO-056 may later extend that authority-internal seam to select eligible
Intents and perform Claim transactions after its own fresh authorization,
currentness, revocation, and worker rules. AIO-055 implements no enumeration
policy, Claim operation, worker race, Lease, Renewal, reclaim, fencing
generation, or executor identity.

There is no transport, consumer, operational worker process, availability
probe, credential resolution, repository resource reader, Tool invocation,
Result attachment, or external side effect. SQLite process/crash probes in
future audited tests are disposable storage probes, never dispatch workers.

## Review and validation references

The fresh production scenario matrix is in `acceptance-criteria.md`.
The fresh Validation Safety Matrix and Phase-1/Phase-2 evidence are in
`review.md`. P1/O55 package acceptance passes after the authorized offline
bootstrap. The exact predecessor regression run separately records one existing
Windows symlink-privilege skip. The authorized final Quality Gate disposition
is recorded in review.md; Phase-2 completion does not close the Task.
