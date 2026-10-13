# AIO-059 Context

## Final closure: 2026-10-13

Human final approval is APPROVE. C8 staged-index migration verification passes;
C13 and all 49 acceptance criteria are reconciled with no failures. Task status
is completed in the closure metadata, effective with the one authorized local
closure commit. No push, physical/remote rename, ITRU-060 or UI worktree is part
of closure. The full chronology and accepted missing original 386-runner note
remain in review.md. The original context below is retained as phase evidence.

## Retained pre-review context snapshot

AIO-059 remains the last legacy transition Task. Phase 1 design, Phase 2A
package/distribution and Phase 2B runtime identity work are complete and reviewed.
Phase 2C prospective namespace/Task-prefix enforcement and living documentation
are implemented, validated and independently approved. Human-authorized Phase 2D
integrated validation passes on the current finished tree. Phase 3, final Quality
Gates, Task closure and final Human approval remain pending. Baseline HEAD remains
`45c70d02fd5e905417945264b14db755c31149eb`; no stage/commit/network is authorized.

The baseline and prior design records below are historical phase evidence. The
later Human resume instruction supersedes the original inbound legacy-marker
proposal: only `ITRU_VERIFY_DEPTH` controls current runtime. No new home config
subsystem exists. Completed predecessor Tasks and experiments are not inspected
or modified.

## Context boundaries

Bootstrap used exact `.ai/project.yaml`, Core principles, terminology and
precedence reads. Task contract/schema/template, exact selected
`workflows/standard-change.yaml`, Architect/Reviewer/Software Engineer Role
definitions, and the two required Quality Gate definitions supplied governance
context. No Task or Workflow catalog was enumerated. The exact attempted
`roles/orchestrator.yaml` read returned ABSENT; no alternate was searched.
The named Workflow review checkpoint is retained. Human approval is pending.

Namespace inventory used bounded `git grep` within only `pyproject.toml`,
`README.md`, `core/`, `schemas/`, `engineering_orchestration/`, and `tests/`.
Both listed root files were PRESENT. Additional bounded patterns covered the
actual `aio` console, environment marker and resource-loading contracts.
No whole-repository recursive search or experiment read was used.

The initial exact-string sweep at baseline returned 1,981 matching lines in
365 matching tracked files: README 65, pyproject 8, Core 534, schemas 354,
production package 222, tests 798. These are occurrence counts, not a whole
repository file inventory. Supplemental bounded patterns established the actual
console, environment, resource and relative-import surfaces. Classification
rules in the specification cover every occurrence according to its semantic
use, including mixed living/provenance content within a single file.

## Evidence and decisions

| Evidence at baseline | Finding and design consequence |
| --- | --- |
| `pyproject.toml:6-24` | Existing distribution `ai-engineering-orchestra`, console `aio`, four explicit package identities and resource data maps must change coherently |
| `README.md:28-93` | Legacy installation commands/source wrapper, environment recursion marker and separate brand/contract discussion are living surfaces |
| `engineering_orchestration/__init__.py` | Minimal package entry; preserve minimal import-time behavior |
| `engineering_orchestration/schema_resources.py:105` and module constants | Private schema loader and old v1 URI registry need separate treatment: package changes, URI identities remain exact |
| `engineering_orchestration/role_catalog.py:70-78` | Change resource package `_roles` while preserving source-vs-installed ownership and strict missing-module handling |
| `engineering_orchestration/project_verification.py:49,668-698` | Actual legacy environment marker exists; canonical emission plus legacy inbound-only recursion protection is required |
| `engineering_orchestration/agent_operation_tool_registry.py:23-38,539-552,705-729` | Old Tool constant, factory, selector and append-only prior-map validation preclude same-route substitution |
| `core/agent-operation-tool-registry-and-resolver-specification.md:249-350,407-445` | Permanent route mapping, retired selection and history resolver semantics require distinct new route and explicit new-work checks |
| `engineering_orchestration/local_operational_trust.py:375-397` | Existing trusted composition rebuilds one native route; future cutover must include retained historical registrations, not forget them at restart |
| `engineering_orchestration/_execution_entry_and_controlled_invocation.py:168-175` and `_native_repository_file_read.py:23` | Native identity and selector checks must change together for new actions; no native safety refactor |
| `engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py:71-73,643-692,1397,1501-1508` | Durable STORE_ID/application ID/hash identities cannot follow package rename; resource package can |
| `engineering_orchestration/windows_local_authorization_domain_owner.py:70-86,586,817` | Existing Local AppData ownership root is not user config; moving it risks duplicate authority. Preserve v1 coordination location |
| `schemas/*.schema.json` and `schema_resources.py` | Existing legacy schema URI IDs are exact offline contract identities; display titles can change without changing IDs/refs |
| SQL migration resources and manifest | Four exact digests match the Human baseline; freeze bytes and resource names |
| `tests/test_packaging.py`, `tests/package_installation_smoke.py`, `schemas/tests/validate_*.py` | Imports, entry points, payload paths and expectations need coherent updates; default tools may enumerate prohibited catalogs |
| `tests/test_packaging.py:111-116` | Explicit old migration-path LF rule requires later exact `.gitattributes` authorization and successor rule; that external inventory path was not opened |
| `tests/test_atomic_durable_dispatch_outbox.py`, `test_dispatch_claim_lease_foundation.py`, `test_durable_execution_entry_and_controlled_invocation.py` | Historical temporary sentinels are safety fixtures; do not mechanically rename them or execute experiment imports |

## Architecture tradeoffs

Clean package cutover is preferred because the bounded evidence establishes no
real source shim requirement. Durable compatibility remains mandatory, including
v1 protocol constants in new v1 ledgers: these are narrow exceptions to the
living-brand rule, not dual canonical packages. New Tool identity requires a
distinct explicit route, not merely a new Run. Caller-owned identities are not
automatically rewritten. A historical resolver may represent the old binding;
trusted composition must prevent it becoming newly consumable/executable work.

The public configuration root is prospective `~/.itru`; no old home config was
found. Do not create migration code for it. Preserve the existing Windows v1
authority registry for its protocol lifetime, separately from user config.

Source wrapper and guidance paths are referenced by inspected README/tests but
outside this phase's inventory. The implementation plan identifies exact paths
that require a later scope authorization; it does not claim a complete global
namespace inventory. Do not execute broad lint, aggregate verification, Task
validators or full tests merely because the manifest declares them.

The Packaging review identified the missing `.gitattributes` transition detail.
The draft was revised to require exact later authorization, a canonical SQL-path
LF rule, and four-resource byte/hash verification including the eventual index.
No SQL bytes or attributes file were edited in Phase 1.

The Runtime review corrected marker semantics: both inbound keys independently
permit only absent or literal `"0"`; empty and other values reject entry.
Prospective validation now includes exact values and mixed-key combinations.
This design correction preserves baseline behavior and changes no runner code.

## Validation limitation observed during design

An exact read found `tests/test_packaging.py` still asserts one migration while
the current migration manifest contains four. It was not executed or changed.
The later packaging validation must explicitly reconcile current four-resource
expectations within its authorized cutover test scope; no baseline test PASS is
claimed here. This does not authorize unrelated regression repairs.

## Human control

Phase 1 is design-ready only after six independent APPROVE outcomes, zero
blocker/high findings, targeted artifact validation and documentation consistency.
Next step is explicit Human Phase-2 authorization. AIO-059 remains in progress
until implementation, fresh reviews, all closure gates and Human approval.
No stage, commit, push, physical-directory rename or repository rename occurs now.

## Phase-2B historical identity design amendment

The Human amendment permits durable historical Registration coexistence while
forbidding two active canonical Tool identities. The canonical specification's
amended registration/evidence sections supersede the original same-snapshot
historical resolver plan. Historical data remains exact; legacy entries leave
active indexes and cannot produce new authority. Existing persisted Bindings
reference Tool identity; the inspected registry is process-local, with no
standalone durable Registration table. No new persistence model is invented.

The planned private `_HistoricalExecutionEvidenceBoundary` in
`itru/local_operational_trust.py` owns authenticated exact existing-record lookup
and negative-only original revocation. Private store/session leaves carry
disjoint historical request/reference types. They never call `_produce`, the
active resolver or a new Binding factory; decoding recorded values is not
granting new-work authority. A mandatory active canonical route/occurrence gate
also applies to direct producer entry, not only the coordinator facade.

Historical revocation must locate the existing exact authority and authenticate
the original issuer, then recheck it inside writer serialization before an
existing-schema tombstone append. Absence/conflict cannot trigger issuance.
Revocation-only rows do not invent a missing recorded Tool/Binding. Current live
unadmitted issuance can be referenced without minting a replacement; missing
legacy durable authority is not synthesized. Public signatures/results/exports
need not widen, but active resolution and history methods intentionally change
behavior. This source contract effect is explicit, not claimed to be no change.

Only the canonical specification and current Task context/review may change in
this amendment. Runtime/test/migration files remain at the Phase-2A state.
Four fresh independent design reviews are required before recommending renewed
Phase-2B implementation authorization. The existing blocked Task status is not
changed by this three-document amendment; its pending implementation checkpoint
will be explained in the review record. No Phase-2B runtime work resumes here.

All four fresh amendment reviewers approved the revised design. Authority review
required preservation of proof-registry identity/subject binding and validity
checks; Durable review required the normal revocation decision-watermark update.
Both existing obligations are now explicit in the specification. No public
surface widening, new durable table, migration or historical rewrite is needed.
The design blocker is resolved; renewed runtime implementation authorization
remains pending, so the existing blocked lifecycle field is left unchanged.
