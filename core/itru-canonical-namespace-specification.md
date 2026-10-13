# ITRU Canonical Namespace and Brand Cutover Specification

Version: 0.1.0. Phase 2A package/distribution and Phase 2B runtime identity
cutovers are implemented. Phase 2C authorizes the prospective guard and living
documentation only; final validation, closure reviews and Human approval remain
pending.

## Authority and boundary

This specification records the Human-requested cutover from baseline
`45c70d02fd5e905417945264b14db755c31149eb`. Phase-1 baseline inventory and
predecessor attribution remain historical evidence. The approved historical
Registration amendment and subsequent Human resume instruction govern the
implemented private compatibility boundary. The later resume instruction
supersedes the original inbound legacy-marker proposal: current runtime reads
only the canonical marker.

The `standard-change` Workflow applies. No phase approval grants authority for
network access, historical rewrites, staging, publication or Task closure.
Phase 2D and subsequent closure reviews require separate Human authorization.

## Single canonical living identity

| Surface | Canonical target |
| --- | --- |
| Product and repository/project brand | ITRU |
| Python import package | `itru` |
| Python distribution metadata Name | `itru` |
| Installed CLI | `itru` |
| Product environment prefix | `ITRU_` |
| Prospective user configuration root | `~/.itru` |
| Last newly created legacy Task | `AIO-059` |
| First subsequent Task after successful closure | `ITRU-060` |
| Subsequent new Task identities | `ITRU-061`, `ITRU-062`, ... |
| New native reader Tool identity | `tool::itru-native-repository-file-read::v1` |

The import/distribution change is a pre-release source compatibility break.
There is no evidence of a deployed source compatibility requirement in the
authorized inventory. No `engineering_orchestration` shim, alias in
`sys.modules`, duplicate tree, legacy installed console, or permanent dual
namespace is proposed. Arbitrary caller-owned IDs remain opaque; this branding
decision does not normalize Actor, Runtime, environment, Run, Grant, or domain
identifiers supplied by callers.

## Historical baseline inventory and classification

Inventory used exact-string/bounded-pattern `git grep` only within the six
authorized paths, then exact evidence reads. Both root files are PRESENT.
The following rules classify every matching occurrence by semantic role, not
by file alone. A living document or test can contain both current behavior and
historical provenance. The Task context records evidence locations.

| Category | Discovered surface | Disposition and kind |
| --- | --- | --- |
| A Product brand | README heading/body; Core titles; schema titles/descriptions; current code docstrings and CLI prose | CUT OVER display text to ITRU; PRESERVE dated predecessor attribution |
| B Code namespace | Python absolute imports, patch targets, subprocess snippets, package paths, resource-package strings | CUT OVER source identity to `itru`; retain private leaf names and public symbol behavior |
| C Distribution | `pyproject.toml` Name, description, scripts target, explicit packages, resource mapping/data keys; metadata and installation tests | CUT OVER to one `itru` distribution; no dependency/version/support-floor change |
| D CLI | Installed `aio` console and README commands; references to source `aio.py` and `scripts/` wrappers | CUT OVER installed console; source wrapper follow-up requires explicit paths authorized in Phase 2 |
| E Environment | `ENGINEERING_ORCHESTRATION_VERIFY_DEPTH` in runner, README, Core, tests | CUT OVER to `ITRU_VERIFY_DEPTH`; the later Human resume instruction makes the old marker inactive |
| F Configuration | No `~/.aio` or `~/.aeo` user-config implementation found; existing Windows Local AppData ownership registry has legacy brand | Public config migration NOT APPLICABLE; `~/.itru` reserved directly. Ownership registry COMPATIBILITY REQUIRED below |
| G Tool/runtime contracts | Native Tool ID, private constant/factory, closed selector, native implementation ID and coordinator comparisons | CUT OVER active new-work identity; retain historical route/selector facts only in the separate evidence view, never as active entries |
| H Serialized/durable | v1 schema URI IDs/refs, SQLite store/application identifiers, DDL, migration hashes, registry manifests, Run/Grant/Binding payloads | COMPATIBILITY REQUIRED; preserve exact v1 protocol constants and historical facts |
| I Test-only current references | All executable legacy package imports, mocks, metadata expectations, new reader fixtures and current smoke payload paths | CUT OVER coherently; exact historical protocol/regression fixtures remain explicitly allowlisted |
| J History | AIO Task citations, incident/review provenance, experiment module references, synthetic predecessor identities and ownership sentinels, SQL migration headers | PRESERVE immutable history or exact predecessor regression meaning; not permission for new legacy product behavior |

Lowercase `aio-` temporary roots and `.aio055-owner`/`.aio056-owner` sentinels
are predecessor safety fixture identities, not user configuration roots.
The store's `.{destination.name}.aio047-` temporary backup prefix is current
display naming: change its namespace component to `itru047` together with any
paired safety checks; preserve backup/fencing semantics. Historical test file
names and `experiments.aio_058_windows_containment` import references are
provenance, not a second product package. Do not inspect experiment evidence.

## Python package and packaging design

Move the tracked `engineering_orchestration/` tree once to `itru/`. Use a
filesystem move for the unstaged implementation, then inspect Git rename
similarity; if a later Human authorization explicitly permits staging,
`git mv` is acceptable. `git mv` stages changes and is not permitted in Phase 1
or under a continuing no-stage boundary. No copied package tree may remain.

Rewrite absolute imports, dynamic import strings, mocks, subprocess programs,
and module identity assertions to `itru`. The bounded source inventory found no
`from .` relative imports; any later authorized relative imports retain their
leaf relationships. Preserve public classes, functions, error codes,
field names, exact-value validation, ordering, and private leading underscores.
`__init__.py` remains minimal; import must not provision ledgers, obtain locks,
discover projects, launch subprocesses, probe native roots, or access network.
Native adapters remain behind their existing private boundary.

Set project Name to `itru`, script table to `itru = "itru.cli:main"`, and explicit
packages to `itru`, `itru._schemas`, `itru._roles`, and
`itru._sqlite_admission_migrations`. Retain `_schemas -> schemas` and
`_roles -> roles` source mapping with the new keys; retain explicit schema,
Role YAML, and SQL data allowlists. Update resource loaders, missing-module
exception comparisons, and `MIGRATION_PACKAGE` to the corresponding `itru`
names. Do not turn resource errors into alternate-directory fallback.

Before the move, explicitly authorize the exact `.gitattributes` file for
Phase 2 and replace the old migration-path rule with
`itru/_sqlite_admission_migrations/*.sql text eol=lf`; preserve unrelated rules.
The existing path rule is evidenced by `tests/test_packaging.py:111-116`, not
by a Phase-1 read of `.gitattributes`. Verify all four moved resources remain
UTF-8/LF and byte-identical in working tree, eventual Git index, and wheel;
never normalize existing frozen SQL bytes as a repair. Missing or changed
digests stop the move for correction of the move/attributes procedure.

Wheel payload must contain only the canonical package and intended resources,
one `itru-0.1.0.dist-info` metadata tree, and one `itru` console entry. No
historical Tasks, experiments, checkout-only wrappers, compatibility package,
or duplicate runtime tree may be installed. Preserve offline schema reference
resolution, exact Role resource ownership, and all migration bytes.
Reinstall editable environments after metadata changes; use a fresh offline
wheel install for verification so stale installations cannot hide omissions.

## CLI, environment, and configuration

Keep CLI router behavior and caller-derived project root intact; console naming
belongs to metadata. No new CLI capabilities or user configuration subsystem
are introduced by this Task. The existing project `.ai/project.yaml` structure,
`orchestra` key, Task-directory layout, and contract field names remain unchanged.
The manifest's living `project.id`/`project.name` should become `itru`/`ITRU`
only after its exact Phase-2 modification is explicitly authorized.

The runner reads, emits and restores only `ITRU_VERIFY_DEPTH`. Absent and literal
`"0"` permit entry; empty `""`, `"1"` and every other string reject nested aggregate
verification. The legacy `ENGINEERING_ORCHESTRATION_VERIFY_DEPTH` is inactive and
is never an alias or a second active configuration prefix. Tests prove that
legacy values do not affect current runtime and that canonical restoration is
exact. This recursion check is neither execution authority nor a sandbox.
No other product environment/config migration was established by this inventory.
Standard OS variables such as PATH/PATHEXT are not product namespace candidates.

## Durable protocol exceptions

The code package and a serialized protocol identity are separate. Preserve:

- SQLite `STORE_ID = engineering_orchestration.agent_execution_dispatch_admission.sqlite`;
- `SQLITE_APPLICATION_ID = 0x41494F47`, schema version 4, table/column names,
  encoding, schema-manifest computation and expected DDL fingerprints;
- existing `https://ai-engineering-orchestra.dev/schemas/...` v1 `$id`/`$ref`
  values and matching offline registry constants;
- migration manifest resource names, ordered IDs, and SHA-256 values;
- caller-owned domain/ledger/generation IDs, binding paths, lock identities,
  persisted Run/Grant/Admission/Intent/Claim/Entry values and fingerprints.

These are reviewed compatibility exceptions for the existing v1 protocol,
including newly provisioned v1 ledgers and bundled v1 schemas. They are not
canonical product branding or a legacy import API. Renaming STORE_ID alone
would reject existing ledgers; changing only schema URIs breaks exact offline
reference resolution. No schema evolution or data rewrite is required here.
Any later removal needs a separate explicitly versioned protocol contract,
compatibility review and, for database evolution, a new migration.

The existing OS Local AppData suffix is exactly
`AI Engineering Orchestra/authorization-domain-ownership/v1`. Preserve it as
the single coordination location for the v1 ownership protocol, including
new v1 domains. Do not introduce a second ITRU ownership registry, discover or
merge legacy authorities, copy authority files, rename active ledgers, or
relocate domains to `~/.itru`. The frozen location is a durable interoperability
exception, not the public configuration root. Removing it requires a separate
Human-approved ownership-protocol transition proving that old and new processes
cannot acquire competing authority for the same domain. No such transition is
part of AIO-059. The reviewed exception lasts for v1 ownership compatibility.

## Registration terminology and current storage facts

**Historical Registration Record** is an immutable historical identity fact,
not a current runtime entry. **Active Tool Registration** is a declaration
eligible for current new-work selection. **Canonical Tool ID** denotes current
new-work identity; **Historical Tool ID** denotes exactly what an old record
actually contains. Never use an unqualified registration-coexistence claim.

Durable historical Registration coexistence is ALLOWED. Two active canonical
native-reader Tool identities are FORBIDDEN. Old and new eras' durable records
can coexist without exposing the old ID through the active registry.

The inspected v1 implementation has process-local Registration snapshots,
not a separate durable Registration table. SQLite stores exact Grants and
Bindings in Admission payloads/indexes and exact Grants in revocation rows.
An old Binding's recorded Tool ID is a durable historical Registration reference;
the matching trusted historical declaration preserves its original route and
selector meaning. Do not invent a persisted selector or standalone Registration
row where none exists. Any already-existing external historical Registration
record remains unchanged; this design introduces no new registry database,
serialized Registration contract, table, or migration.

## Separate active selection and permanent historical identity

All new native work uses `tool::itru-native-repository-file-read::v1`. Active
factory, constant and selector targets are
`_make_itru_native_repository_file_read_registration`,
`_ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID` and
`ITRU_NATIVE_REPOSITORY_FILE_READ_V1`. The AEO Tool ID and original selector
string remain exact historical evidence only; no active factory accepts them.

Trusted composition publishes two immutable, separately typed views:

1. A permanent historical identity manifest preserving every known original
   complete route/Tool/selector fact, including retired legacy mappings. It is
   input to evidence matching and no-rebind validation, not Tool selection.
2. An active snapshot whose native-reader indexes/aliases contain only ITRU
   Registrations. Legacy entries are absent from active enumeration, selection
   and `TrustedAgentOperationToolBindingResolver.resolve/resolve_tool_binding`.
   Those methods reject old routes rather than reconstructing a legacy Binding.

The private snapshot transition validator compares permanent manifests for
append-only identity preservation, separately from active-view membership.
Moving a legacy fact out of active indexes must not remove or reinterpret it
in that manifest. A Historical Registration Record is not an
`_AgentOperationToolRegistration` accepted by the active builder. Disjoint
types and construction capabilities prevent an evidence record from being
registered through an active factory. No legacy alias or fallback exists.

The permanent function over `(runtime_option_id, environment_id, operation_id)`
still maps each established route to its original Tool identity forever.
`R_old` cannot become an ITRU route. A new Run ID or process restart cannot
permit route rebinding. The trusted caller supplies a distinct complete
`R_new`, preferably an explicitly inventoried new Runtime Option ID, with all
existing prerequisite/applicability/compatibility evidence. No automatic ID
suffixing, environment broadening, changed persisted Run or selector inference.

Complete trusted historical declarations must be supplied/preserved across
restart; an ordinary caller's unverified manifest or fingerprint is not
provenance. Missing, omitted or contradictory history fails closed, never
rebinds to ITRU. This remains a trusted configuration/release invariant; an
in-memory snapshot cannot prove an earlier deployment was never rewritten.
No live deployment inventory is accessed in this amendment.

## One private historical evidence boundary

The exact planned semantic owner is
`itru.local_operational_trust._HistoricalExecutionEvidenceBoundary`.
Implementation stays in the already identified modules: private request/type
definitions in `agent_execution_dispatch_admission_store.py`, owned-session
integration in `windows_local_authorization_domain_owner.py`, and private exact
lookup/revocation leaves in `sqlite_agent_execution_dispatch_admission_store.py`.
These are transport/storage leaves, not independent legacy interpretation rules.
No additional runtime file was needed for this design investigation.

The boundary has no reference to a Grant producer, issuance minter, active Tool
resolver, admission/claim/entry/invocation function, or fallback registry. It
uses a session-bound historical read capability and a separate negative-only
revocation capability. The latter can only append the existing revocation
tombstone; it cannot produce or consume positive authority.

Private `_HistoricalLookupRequest`, `_HistoricalExecutionReference` and
`_HistoricalRevocationRequest` are nonconstructible by ordinary callers,
immutable, noncopyable, nonserializable, and tracked by exact identity in the
trusted composition. They bind exact intent, authenticated requester/issuer,
complete Run, domain/ledger/generation, owned session ticket, provenance and
the verified existing record's canonical payload/index identity. They are not
`IssuedAgentExecutionAuthorizationGrant`, active selection evidence, an
Admission request, or a continuation. No casting, widening unions or common
authentication port allows them to enter a positive authority path.

Current `load_authoritative_admission(run, authenticated_principal,
authority_proof)` retains its public signature and result shape. Its planned
flow is:

1. Independently validate the genuine current requester and supplied proof with
   the configured identity/approval/policy adapters. Preserve exact proof type
   and membership in composition-owned identity registries, principal/proof
   binding, complete subject, session/domain/generation, issuer/adapter epochs
   and current validity windows. Adapter Boolean results or matching epochs
   alone are insufficient substitutes for existing provenance checks.
   Trusted private history-access policy explicitly permits this exact read;
   a positive issuance approval is not automatically a read entitlement.
   Missing policy or proof fails closed. This uses read-only authentication
   predicates, never `produce`, issuance reservations, randomness or lifetime
   generation. Old Grant expiry is not evidence deletion or a freshness grant.
2. Under the original owned-session operation lease, mint an exact read request
   from the complete supplied Run plus authenticated issuer namespace and pinned
   domain. Query the existing indexed Run/issuer identity, then compare every
   nested stored Run field; never trust a matching Run ID alone. Obtain Grant ID
   and Binding only from verified stored data, not a caller-selected default.
3. Private store lookup uses a read transaction and existing schema, canonical
   decoding, duplicate-payload/index and ownership checks. Require an exact
   stored Admission for Admission inspection. A missing/conflicting record
   returns the existing appropriate failure/no-history result, not new issuance.
4. Mint an evidence-only reference to that verified existing occurrence and
   match recorded Tool identity against the permanent historical manifest.
   Surface the original Admission values and Tool ID unchanged through the
   existing result format. Rehydrating stored immutable values is decoding,
   not issuing a new Grant or selecting/minting a new-work Binding. No factory
   constructs a replacement from a historical declaration; no data is inserted.

Exact historical retry means this lookup of the original stored occurrence.
Legacy work is rejected by `admit`; it is never routed through new-admission
logic merely to return history. Both old and new eras' stored facts can use
the same private historical boundary without entering active resolution.
Canonical value validators must still accept exact old values for decoding;
intrinsic structural validity alone never supplies execution authority.

The predecessor shared `_produce` lookup/revocation path was removed in
Phase 2B. The implemented historical paths never call the producer. Its
process-local `existing_exact_issuance` outcome cannot prove durable history;
calling `produce` and hoping for that outcome remains forbidden for history.

## Exact historical revocation is negative authority only

`revoke(run, authenticated_principal, authority_proof, original_issuer_proof,
provenance_reference)` keeps its public signature and result shape. It locates
the already-existing exact authority through the historical boundary, then
independently authenticates the original issuer's current revoke intent against
that exact stored Grant, owned domain and provenance. Read permission alone
does not confer revoke permission. No fresh Grant, lifetime, Grant ID, approval
conversion or Binding resolution is performed.

The sealed revocation request refers to the exact existing authority. Inside
one `BEGIN IMMEDIATE` transaction, re-read and compare the original record,
Run, issuer namespace and Grant composite key/payload before writing. Existing
exact tombstone returns `existing_exact_revocation`; a conflict fails closed.
Otherwise append the existing-schema tombstone and perform its required
monotonic decision-watermark metadata update, only after the original issuer,
ownership, trusted-clock/watermark and integrity checks. This existing negative
operation's coordination-metadata update is not a rewrite of historical
Registration/Grant/Binding facts. No other positive authority state is created.
Preserve existing
writer serialization, commit-unknown handling and original-record bytes.
The reference is not independently sufficient if its session, adapter epoch,
generation or payload identity changed before the transaction.

A legacy authority absent from durable Admission/revocation history is NOT
created just so it can be revoked. A revocation-only row proves its recorded
Grant/tombstone; it does not prove a Binding or Tool ID that was never stored.
Return the existing tombstone idempotently; do not invent a Registration field.
An admitted historical legacy Grant may receive its first exact tombstone.
Any already-existing, genuinely authenticated current-era unadmitted issuance
can retain original revocation behavior through a private lookup-only reference
to its existing live issuance record, without calling `produce`. That live
reference is not durable legacy evidence and cannot be fabricated after restart.

Revocation is therefore a negative, non-expansive operation, not a read-only
database transaction: one legitimate existing revocation row may be appended.
No historical payload is updated/deleted, no old work becomes runnable, and
no branding migration or replacement authority is introduced. Fenced/inactive
stores remain unavailable under their existing contract; history access does
not reactivate, provision, repair or select another ledger.

## New-work gate and no-rebound argument

Private `_ActiveCanonicalToolRouteEvidence` is minted only from the trusted
active view for an exact complete new Run/domain. The trusted producer state
and admission/dispatch composition require the corresponding gate; absence of
that gate fails closed, including direct calls to `Producer.produce` outside
the coordinator facade. Its binding-producing leaf accepts active evidence
only. The producer's public signature need not gain a new argument: the gate
is mandatory private composition state, with no historical capability input.

Grant production is allowed only for a Run whose eligible active mapping is
ITRU. A Grant has no Tool field; this rule does not add one. Before positive
issuance side effects, check the exact issuer/domain/Run ID against existing
issuance and authoritative history for reuse/conflict. The check yields only
eligibility or rejection, never converts an old stored Grant into a new one.
Changing nested runtime identity while reusing an old occurrence ID must not
mint replacement authority. Genuinely new work requires a distinct Run,
active route and fresh exact authority, not a relabeled historical occurrence.

The historical boundary cannot supply the active capability or an issued
presentation. New-work authentication ports, producer entry, Binding resolver,
admission requests and controlled invocation reject historical capability
types before positive side effects. Extracting the old Run from displayed
evidence also fails the active-route/occurrence gate; normalizing its Tool
string never supplies genuine active evidence or new exact authority.

Thus neither historical lookup -> producer -> new authority nor historical
AEO record -> normalized ITRU entry -> new authority is a valid capability
path. This is a design invariant to prove with implementation tests, not a
claim of authority supplied by historical evidence. A caller can propose
an independently approved genuinely new action; historical evidence itself
cannot authorize it.

All trusted claim/renewal/entry/invocation paths require active eligibility;
legacy outstanding work stays non-executable. Keep S/G/P/W/C ordering,
ownership/fencing, JIT checks, durable Entry and original continuation,
native containment, read bounds and private outcome semantics intact.
Policy rejection adds no new continuation/Entry representation or alternate
execution path. New fingerprints may differ; recorded old hashes remain old.

## Amendment decision register

| Question | Locked prospective answer |
| --- | --- |
| Retain historical AEO Registration facts? | YES, exact historical values and references; no invented durable Registration table |
| Are legacy facts active Registrations? | NO; separate historical type/view, absent from active indexes |
| Can legacy facts mint new Grants or Bindings? | NO; decoding a stored value does not grant new-work eligibility |
| Can legacy identity be selected for new work? | NO; only canonical ITRU active mapping |
| Read historical evidence? | YES, exact authenticated existing-record lookup only |
| Revoke exact existing historical authority? | YES, original-issuer-authenticated negative operation; never issue missing authority |
| Historical lookup owner? | `_HistoricalExecutionEvidenceBoundary` in `itru/local_operational_trust.py` |
| What excludes Grant production? | Disjoint capabilities/requests/ports, no producer dependency, mandatory active gate and occurrence-conflict checks |
| Durable rewrite or new migration? | NO; existing schema/bytes and identities unchanged |
| Public API effect? | YES, intentional behavioral restriction: active resolver rejects legacy routes; lookup/revocation stop issuing. No new public methods, signature/return-shape/exports or serialized-field changes required |

These requirements supersede the original same-snapshot historical Binding
resolver design. They preserve the permanent identity relation in the separate
historical view, while changing where historical evidence can be obtained.
CLI `itru` and environment `ITRU_` are implemented; `~/.itru` remains reserved
without a home configuration subsystem. The subsequent Human resume instruction
made the original legacy recursion marker inactive. The amendment itself was
design-only; its separately authorized Phase-2B implementation is now complete.

## Frozen historical allowlist

The following is an explicit preservation policy, not a claim to have inspected
forbidden history paths or live databases:

| Frozen class | Preservation rule |
| --- | --- |
| Completed `.ai/tasks/AIO-001...AIO-058` and their historical citations | Never rename or edit; declared IDs stay exact |
| AIO-059 Task and specification cutover evidence | Keep last legacy ID and truthful old/new comparison; freeze closure evidence after approval |
| Historical experiments, especially AIO-058 | No reads or edits in this phase; preserve bytes and recorded paths |
| Prior reviews/incidents, Human approvals, Git commits/messages | Preserve exact identity; no Git history rewrite |
| Migration resources 0001-0004 | Move as resources later without any byte change; digests below |
| Persisted legacy Tool IDs and other ledger facts | Read/reconcile verbatim; never normalize into ITRU |
| Quoted historical package/brand names in living docs | Preserve only precisely anchored provenance, with explicit historical annotation |
| Predecessor regression fixtures and safety sentinels | Preserve exact semantics; new current-product expectations use ITRU |
| v1 schema/store/ownership protocol constants | Exact scoped compatibility exceptions above; not a blanket legacy-code exemption |

| Immutable resource | SHA-256 |
| --- | --- |
| `0001_initial.sql` | `6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed` |
| `0002_dispatch_outbox.sql` | `eee70c9d3e31dca036e716fc8b0ad42c78c97bb07cc5c6e323eaa7290e0ba6db` |
| `0003_dispatch_claim_lease.sql` | `c9163740873586ab39ee760c292cdcdd07bf050ee06f37c29614c5e3a8144949` |
| `0004_execution_entry.sql` | `044dec78513447aaddb5544f6e56ce9667be6b370ec42c510ae1fdf3a954a2b1` |

## Prospective namespace guard design

Implement only in authorized Phase 2C: proposed `tests/test_itru_namespace.py`
with a standard-library pure checker shared by its explicit-file tests. Do not
add import-time runtime scanning, command permission enforcement, or catalog
discovery. Validation is a repository check, not an authorization mechanism.

The guard examines explicit living files in `itru/`, `pyproject.toml`, README,
Core, schemas and `tests/`, plus separately supplied new/changed Task artifacts. Use
an explicit Git-tracked path manifest filtered to these roots; do not walk
the repository or open protected paths. A change-based check must be paired
with a full allowlisted living-file check so an unchanged old import cannot
escape. Source wrappers/manifest and other living paths outside Phase-1
inventory require explicit Phase-2 path authorization before inclusion.

Reject exact `AI Engineering Orchestra`, `ai-engineering-orchestra`,
`engineering_orchestration`, `ENGINEERING_ORCHESTRATION_`, `tool::aeo-`,
`tool::aio-`, `.aio` config references, word-bounded `AEO`, `AIO`, `aeo`, `aio`,
and prefix tokens `AEO_`, `AIO_`, `aeo-`, `aio-` in living content unless an
exact exception matches. Scan file paths and Python AST imports as well as
content; aliases and dynamic strings are not escape routes.

For new Task creation, inspect supplied `task.yaml` and directory name;
reject every new `AIO-*` candidate, including the existing transition ID,
numeric 060+, zero-padded variants and synthetic legacy IDs. The original
`AIO-059` bootstrap remains an existing Task, never a new creation exception. Require this project's new sequence to start at `ITRU-060` after
AIO-059 closure; accept existing historical AIO IDs when reading old Tasks or
opaque contract values. Do not change the generic Task-schema `id` field to
reject legitimate histories or other adopters' ID schemes. Reject new Task
creation before the prerequisite cutover closure; no automatic closure logic.

Use a reviewed allowlist declared in the checker: exact path plus exact token
and semantic anchor/occurrence count, kind, justification, and expiration or
protocol-lifetime removal condition. Frozen history directories are exclusion
classes that are never scanned; in living files allow only exact quoted
provenance, named regression fixtures, and compatibility constants. No whole
test/Core/schema-file exemption or token-wide exception. Reject stale unused
allowlist entries and changed anchors/counts. A false positive requires a
reviewed narrow entry; no skip flag or silently expanded baseline. Include
positive/negative tests proving new legacy imports, Tool factories, Task IDs
and copied historical literals in living factories fail, while old records,
migrations, v1 schema refs and exact historical fixtures pass.

## Implementation sequence and authorized paths

These phases are planned, not authorized by Phase 1:

1. **2A:** lock exact modification allowlist, including `.gitattributes`;
   stop before outside-scope edits. Update only its SQL path rule before moving
   resources. Move tree once, rewrite production imports/resource loaders, packaging keys,
   and test imports/mocks/subprocess snippets as one coherent unpublished batch.
   Do not run tests between those steps or retain mixed canonical namespaces.
   Include exact `aio.py`, successor `itru.py`, and `scripts/` wrapper paths
   only on explicit Human Phase-2 authorization; they were referenced but not
   inspected in Phase 1. Remove legacy branded source launcher rather than
   offer two canonical commands; retain neutral wrappers only if reviewed.
2. **2B:** implement the reviewed historical evidence/capability separation
   before enabling the active Tool cutover. Update factory/selector/native checks
   and mandatory new-work gate, retain separate permanent history facts,
   set recursion marker policy, and keep
   v1 durable exceptions. No config subsystem/CLI expansion. Existing-route
   deployments need exact caller configuration before transition.
3. **2C:** update current-product expectations and living documentation; add
   guard and compatibility regressions. Authorize exact `.ai/project.yaml`,
   `AGENTS.md`, relevant templates/guidance/validation files before modifying
   them; Phase-1 restricted inventory is not a claim that these contain no
   other living references. No catalog or protected-target discovery.
4. **2D:** validate imports, guard, offline editable/wheel packaging, four
   migration digests and durable compatibility, then required predecessor
   regressions with an explicitly safe fixture plan. Never invoke aggregate
   checkout verification that traverses forbidden catalogs/targets.
5. **3A:** fresh six-perspective implementation specialist reviews.
6. **3B:** formal independent review of the final exact diff/evidence.
7. **Final:** required Quality Gates, recorded Human approval and explicit Git
   authorization, then one commit. Keep AIO-059 open (`in_progress`, or `blocked`
   while a required decision/implementation checkpoint remains unresolved).

If phase boundaries require temporary unpublished test expectation changes,
do not publish, stage, or declare cutover complete until all phases cohere.
Rollback is reversal of the uncommitted code/docs changes with Human-owned
work preserved, not a database rollback or history rewrite.

Physical checkout stays `D:\Dev\ai-engineering-orchestra`. An external Human
may later choose an ITRU-oriented repository slug and update local directory
and remote URLs through a separate action; neither repository ownership nor
filesystem rename is a dependency of code cutover. No public name reservation
or release availability is claimed.

## Implementation validation design

All following checks are prospective; none is executed in Phase 1:

- AST/string/path checks prove zero legacy canonical imports in living code
  and tests, with `import itru` from checkout and a fresh installed wheel.
- Validate `Name: itru`, exact `itru.cli:main` console, resource-package contents,
  no duplicate package/dist-info tree, and editable reinstall behavior.
- Build an actual setuptools wheel offline using installed build dependencies
  (`pip wheel --no-index --no-deps --no-build-isolation` with explicit owned
  output); install with `--no-index --no-deps` into a fresh owned environment.
  No dependency download, `npx --yes`, public index lookup, or fabricated wheel
  substitutes for production build evidence. Missing local dependencies are
  reported as blocked validation, never fetched automatically.
- Verify the authorized `.gitattributes` successor rule and UTF-8/LF bytes;
  hash all four SQL resources before/after move, inside the wheel, and in the
  eventual explicitly authorized Git index. Open
  synthetic v1-v4 predecessor ledgers through canonical imports using genuine
  bounded ownership setup; metadata, DDL, migration history and payload remain
  exact. No live ledger or experiment data is used.
- Preserve exact authenticated old Admission lookup across restart with original
  payloads/Tool ID, without Grant production or active Binding resolution.
  Exercise permanent-manifest no-rebind/missing-history failure, rejection of
  legacy records by the active builder/resolver, and ITRU-only new selection.
- Prove both historical capability types and extracted old Run identities fail
  producer/admission/dispatch entry before positive side effects. Spy on Grant
  IDs, lifetime/issuance state, RNG, active resolver and SQL writes: historical
  reads perform none; exact original revocation writes only its allowed tombstone
  and the required monotonic decision-watermark metadata update.
  Test absent/forged/expired-session/wrong-generation/conflicting records,
  revocation-only history, current live unadmitted issuance, issuer mismatch,
  concurrent revocation and commit-unknown exact retry without replacement grants.
- Verify forged new work on an old route cannot issue new authority/consume
  grants/claim/renew/enter/invoke. Old outstanding work remains non-executable;
  exact reconciliation and original revocation still work.
- Verify v1 STORE_ID/application ID/schema refs/ownership-root compatibility,
  no duplicate authority namespace, same-domain fencing and owner invariants.
- Exercise canonical marker emission/restoration and rejection of empty/nonzero
  canonical values. Prove the legacy variable does not control current runtime
  for either absent or zero canonical input. Confirm no user config migration.
- Guard PASS, no new AIO-060+ (including alternate numeric spellings), and
  frozen historical allowlist enforced without opening history catalogs.
- Preserve predecessor contract/value, registry/resolver, trust/ownership,
  outbox/claim/lease, JIT, controlled invocation, and native containment behavior
  (AIO-047 through AIO-058), including authority order, ambiguity, cleanup and
  native work bounds. Review test setup before execution: several existing
  tests import historical experiments or traverse source wrappers/catalogs.
  Use explicitly authorized synthetic fixtures and individual tests; record
  unsafe/unavailable tests as skipped, never silently claim full-suite PASS.
- Run targeted documentation/schema/whitespace checks and fresh reviews.
  Record every gate failure/skip. No network or protected target access. A
  required regression that cannot be exercised safely keeps closure incomplete
  until a Human-approved safe validation plan supplies equivalent evidence.

## Implemented prospective validation policy

`tests/test_itru_namespace.py` owns the standard-library validation guard. It
reads an explicit Git path manifest restricted to the declared living roots and
exact root files, including unstaged canonical source files. It never traverses
Task/Workflow catalogs or experiment evidence. Its immutable allowance records
bind exact file, exact legacy value, semantic scope, exact line digest and
occurrence count to a constrained reason and removal condition. Deleted, stale
or changed exceptions fail; exceptions are not regular expressions or globs.

The pure `new_task_id` predicate accepts canonical numeric IDs starting at
`ITRU-060`. `historical_task_id` accepts only the exact prior legacy sequence
through `AIO-059`. Candidate creation additionally requires explicit completed
cutover status and a present matching supplied directory name; it performs no Task
discovery or automatic closure. A historical reference is not creation authority.
Generic Task schema/opaque-value validation is unchanged.
