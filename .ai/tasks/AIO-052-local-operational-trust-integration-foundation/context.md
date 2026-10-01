# AIO-052 Context

## Phase 1 authorization and baseline

The Human authorized Task creation and design lock only. Phase 1 authorizes
exactly the four canonical Task artifacts in this directory. It does not
authorize implementation, tests, validators, Quality Gates, staging, a commit,
dispatch, Tool invocation, or repository resource access.

The bounded baseline was confirmed on 2026-10-01:

- branch: `main`;
- HEAD: `286d3033ff5f3baff3a8e4f5e1b5743de1f70421`;
- worktree and index: clean before AIO-052 creation;
- exact AIO-052 candidate path: absent;
- AIO-047, AIO-049, AIO-050, and AIO-051: completed; and
- AIO-052 Task identity: available.

The intended Phase 1 end state is `in_progress`, exactly four Task artifacts,
locked design, no implementation, no test or Quality Gate execution, a clean
index, and no commit.

## Process-safety disclosure

Initial read-only reconnaissance enumerated the Task catalog despite the
explicit AIO-052 prohibition. The enumeration did not modify files, execute a
validator or test, inspect the protected target, or affect the design evidence,
but it is a process-safety deviation and cannot be represented as compliant.
No further Task or Workflow catalog enumeration is permitted. Phase 1 readiness
must remain pending unless the Human explicitly decides how this execution is
to be treated; the deviation is not silently waived by the design reviews.

## Cancellation record

AIO-052 was cancelled by explicit Human authorization on 2026-10-01 because
PROCESS-052-1 made the existing acceptance contract permanently
unsatisfiable. The exact failed requirement remains:

> Every executed command is present in an approved Task-local Validation
> Safety Matrix and receives its required static preflight.

The prohibited Task-catalog enumeration occurred before implementation. The
incident did occur, is not retroactively authorized, is not waived, and must
remain permanently visible in AIO-052 history.

```text
PROCESS-052-1: UNRECOVERABLE UNDER CURRENT ACCEPTANCE CONTRACT
TASK REMAINS TRUTHFULLY COMPLETABLE: NO
RETROACTIVE AUTHORIZATION: NO
WAIVER: NO
PROTECTED TARGET ACCESSED: NO
IMPLEMENTATION PERFORMED: NO
```

The Phase 1 design remains here as historical reference only. It is not
acceptance, review, Quality Gate, Human approval, or replacement-Task
completion evidence. Any future replacement must perform fresh Phase 1 design
and review under separate authorization.

## Canonical term and responsibility

The canonical integration term is **Local Operational Trust Coordinator**.

It is the smallest useful same-process trusted composition root and thin
orchestrator that:

1. joins one live AIO-049 Owned Authorization Domain Session to the existing
   AIO-050, AIO-051, and AIO-047 components;
2. asks AIO-050 to produce one private issued-Grant presentation for one exact
   complete Run and already-authenticated synthetic authority;
3. passes only that presentation to the Owned Session's existing Admission
   operation;
4. returns the existing AIO-047 Admission-store result; and
5. stops before dispatch or invocation.

It does not decide entitlement, authenticate a principal or authority proof,
resolve a Tool itself, assess prerequisites, determine effective execution
mode, reconstruct a Run, consume a Grant, select decision time, or persist an
Admission. Those responsibilities stay with their predecessor components.

## Real production components and synthetic edges

| Boundary | Phase 2 treatment |
| --- | --- |
| AIO-049 administration, owner, live session, and operation lease | Real canonical implementation against a disposable domain and ledger |
| AIO-050 Producer and paired authentication port | Real canonical implementation |
| AIO-051 registry snapshot and resolver | Real canonical implementation with `tool::aeo-native-repository-file-read::v1` |
| AIO-047 coordinator and SQLite Admission Store | Real canonical implementation against the disposable authoritative ledger |
| Principal authentication source | Synthetic external edge |
| Exact Human approval or policy decision source | Synthetic external edge |
| Issuer-state and entitlement authorities | Synthetic deterministic external edges with real AIO-050 validation |
| Fresh prerequisite and effective-mode observations | Synthetic external sources that own bounded freshness and are consumed by existing AIO-047 ports |
| Original-issuer revocation authentication | Independently authenticated synthetic external edge used only to exercise real AIO-047 revocation |
| Clock and entropy | Deterministic/test-controlled only where predecessor contracts permit |
| Filesystem and database location | Disposable test-owned location |

The resulting Grant, Tool Binding, and Admission are real canonical
production-path values. Their authority inputs and storage location are
synthetic or disposable. No production authority is used.

## Trusted construction and the one-time authentication latch

There is a real construction cycle in the completed components:

- `WindowsLocalAuthorizationDomainOwner` needs a Grant-authentication port
  before it can acquire and construct the session's AIO-047 coordinator; and
- AIO-050 can compose its paired authentication port only after the exact live
  Owned Session has been acquired.

AIO-052 resolves that cycle inside its trusted concrete composition root with a
private, process-local, install-once, fail-closed forwarding latch. The latch:

- is passed to AIO-049 before acquisition and returns `None` while unbound;
- can be bound exactly once, by the composition root, to the exact paired
  AIO-050 authentication port returned for the acquired session;
- atomically publishes either that one binding or terminal failure;
- refuses calls before binding, second binding, unbinding, replacement,
  fallback, and use after failed composition or teardown;
- forwards the original presentation unchanged and returns only the paired
  port's result; and
- never constructs, authenticates, caches, widens, or treats a Grant as
  trusted itself.

The session and Local Operational Trust Coordinator are not exposed until the
paired port is bound and every other dependency is coherent. Any acquisition,
Producer-composition, adapter-binding, or latch-binding failure closes the
Producer if created, closes the Owned Session if acquired, terminally disables
the latch, and publishes nothing. The latch is wiring, not another authority
engine or a public installation setter. No AIO-049, AIO-050, or AIO-047 public
contract changes.

Phase 2 must test pre-bind rejection, one-time exact binding, bind races,
rebind/substitution rejection, terminal failure, and cleanup. If implementation
shows that this can only be achieved by weakening a predecessor trust boundary
or changing a public predecessor contract, work stops for Human review.

The latch lifecycle is closed and monotonic:

```text
UNBOUND -> BOUND -> CLOSED
       \-> FAILED
```

`FAILED` and `CLOSED` are terminal. Binding validates the exact port object
returned by the AIO-050 composition for the same session; a foreign-session
port, look-alike, second bind, bind-after-close, or concurrent losing bind is
rejected. Authentication takes one atomic snapshot of the sealed target; an
unbound, failed, or closed snapshot returns `None`. No target can change after
publication.

## Exact orchestration order

Disposable administrative setup precedes the operational flow: the real
AIO-049 administration component provisions, registers, and activates one
disposable AIO-047 SQLite ledger for one disposable authorization domain.

Trusted composition then follows this order:

1. construct the AIO-051 native `repository_file_read` registration for one
   exact Runtime/environment/operation route;
2. atomically build the immutable registry snapshot and real resolver;
3. create the unbound fail-closed authentication latch and the real AIO-049
   owner with that latch, the real resolver, fresh-fact ports, mode resolver,
   clock, and an independently authenticated synthetic original-issuer
   revocation port;
4. acquire one live AIO-049 Owned Authorization Domain Session by exact domain
   ID;
5. compose one AIO-050 Producer/paired-port binding for that exact session;
6. bind the latch exactly once to the paired AIO-050 port and only then publish
   the Local Operational Trust Coordinator;
7. obtain one synthetic authenticated principal from the configured external
   identity adapter;
8. obtain either one exact positive Human approval or one exact policy decision
   for the same complete Run, never both and never by fallback;
9. call the real AIO-050 Producer with that Run, principal, and proof;
10. on `issued` or an exact same-request issuance retry, pass the returned
    private presentation unchanged to `owned_session.admit(...)`;
11. return the canonical AIO-047 result; and
12. stop, with no dispatch, invocation, or repository resource read.

Steps 9 and 10 use two distinct, sequential, fresh AIO-049 operation leases on
the same exact Owned Session. AIO-050 `produce(...)` acquires the first lease,
performs issuance, exits with the provider post-check, and only then publishes
and returns the private presentation. `owned_session.admit(...)` subsequently
acquires a second lease and revalidates ownership, identity, and generation for
the whole AIO-047 operation. AIO-052 adds no third or outer lease, does not nest
or share the two leases, and cannot make issuance plus Admission one atomic
transaction.

The inter-operation gap is an explicit security boundary. Close, fence,
ownership loss, identity drift, or generation mismatch after issuance but
before Admission makes the second lease fail closed before Grant
authentication or Store access. The presentation is not an Admission and does
not authorize same-Run reissuance. If the exact session remains live, recovery
may retry only the same presentation. If the session is closed, fenced, lost,
or the process restarts, recovery requires a new session, new Run, fresh
authority, and new Grant under AIO-050's rules.

The call to `owned_session.admit(...)` owns the inner trust order under one
AIO-049 complete-operation lease. AIO-047, not AIO-052, then:

1. authenticates the presentation through the latch and exact paired AIO-050
   port;
2. resolves the exact Tool Binding through AIO-051;
3. classifies guarded authoritative history;
4. returns an exact historical Admission immediately when one already exists;
5. only when no Admission exists, collects fresh prerequisite parents and the
   effective execution mode;
6. performs the existing AIO-040 assessment and AIO-041 Contract preparation;
7. reconstructs the expected AIO-042 Run using the authenticated Run ID;
8. enforces exact Grant/Binding/expected-Run agreement; and
9. calls the real SQLite store to atomically consume the Grant or return exact
   history using the Store's decision time.

Operational authentication must never be called directly outside the Owned
Session gate. Tool resolution, fresh-fact collection, and expected-Run
reconstruction must not be duplicated or moved ahead of AIO-047's guarded
history logic.

## Result-family boundary

The coordinator introduces no outcome or retry taxonomy. Its operation has the
exact return type union:

```text
AgentExecutionAuthorizationGrantProductionResult
|
AgentExecutionDispatchAdmissionStoreResult
```

An AIO-050 non-issuance outcome returns the exact unchanged production result
and stops with no Admission call. `issued` and `existing_exact_issuance` remain
internal control outcomes: the coordinator passes their exact presentation to
`owned_session.admit(...)` and returns the exact unchanged AIO-047 Store result.
It does not translate one family into the other, synthesize an Admission
failure, add an integration result, or expose the presentation in a successful
return.

## Exact Run agreement

The path preserves complete canonical values and requires:

```text
Producer-approved Run == Grant.run
Resolver input Grant.run == Binding.run
Grant.run == Binding.run
freshly reconstructed expected Run == Grant.run == Binding.run
```

The AIO-051 resolver also constructs the Binding with the authenticated
Grant's exact Run object. AIO-047 remains the enforcement authority for the
final equality and Store request. There is no partial comparison, coercion,
normalization, fallback, alternate Tool selection, Runtime Option or Inference
Option substitution, or resource widening. The Run has no separate Provider
identity field, and AIO-052 invents no post-Run Provider override.

## Grant, Tool, ownership, and Admission paths

The Grant path is synthetic authenticated authority -> AIO-050 adapter-minted
private proof -> AIO-050 Producer -> private issued presentation -> owned
session -> paired AIO-050 authentication port -> canonical Grant. A raw or
directly constructed Grant, look-alike, copied value, foreign presentation, or
`trusted=true` flag cannot enter the path.

The Tool path is the package-owned AIO-051 registration -> immutable snapshot
-> real resolver -> canonical two-field Binding. The first route uses
`tool::aeo-native-repository-file-read::v1`; the registered identity has no
callable adapter, is never invoked, and does not read the repository.

AIO-051 retirement applies only to trusted pre-Run selection. The Local
Operational Trust Coordinator accepts an already-complete Run and cannot infer
whether its route was selected before or after retirement. Its Admission
resolver must therefore remain total for every retained historical route and
must not reinterpret retirement or reject exact historical reconstruction.
Retired-route rejection is proven separately at the real AIO-051 pre-Run
selection boundary before Run construction; it is predecessor-boundary
evidence, not Local Coordinator Admission behavior.

The ownership path is one actual live AIO-049 session from acquisition through
Producer composition and every Admission attempt. Wrong domain, wrong
generation, close, lost ownership, and fencing fail closed. No second ownership
abstraction is introduced.

The Admission path is only `owned_session.admit(presentation)`. Its existing
AIO-047 coordinator and official SQLite backend own authentication, Binding
resolution, history classification, fresh reconstruction, currentness,
revocation, expiry, decision time, atomic consumption, and exact retry. There
is no Integration Admission, Integration ID, or direct Store call.

The revoked-Grant scenario uses a separate synthetic original-issuer
reauthentication edge. It mints a private, nonserializable revocation
presentation bound to the exact original issuer, the original AIO-050 issued
presentation, live session, domain, generation, explicit revocation intent,
and fresh provenance. It does not contain, construct, or cache a raw canonical
Grant.

Under the AIO-049 operation lease already held by
`owned_session.revoke(...)`, the configured AIO-047 revocation-authentication
port validates the independent issuer proof and exact bindings, then forwards
the embedded issued presentation unchanged through the same sealed latch and
paired AIO-050 authentication port. Only that real AIO-050 port may recover
and return the canonical Grant; the revocation port returns that exact result
to AIO-047. Unbound, closed, foreign, malformed, stale, or failed proof and
authentication states return `None`. The issued presentation alone never
authorizes revocation, and the paired port is not called outside the owned
session gate.

A later `owned_session.admit(issued_presentation)` must be rejected by the real
AIO-047 authoritative Store. No direct Store mutation, fabricated or cached
Grant, direct out-of-gate authentication, or production revocation capability
is used or claimed.

## Retry model

AIO-052 adds no retry identifier or persistence.

- Before authoritative Admission, an in-process exact retry must reuse the
  identical complete Run, principal proof, authority proof, lifetime request,
  Producer/session, and private presentation according to AIO-050. A different
  proof, Grant, Tool, Run, Runtime Option, Inference Option, or session is not
  recovery.
- After an Admission may have committed, the same in-process presentation is
  passed again to the same Owned Session. AIO-047 re-authenticates, reproduces
  the same AIO-051 Binding, classifies history, and returns the historical exact
  Admission without collecting new prerequisite facts or writing a replacement.
- The canonical AIO-050 production outcome and AIO-047 store outcome distinguish
  pre-Admission issuance retry from post-Admission historical retry. AIO-052
  does not invent a second state machine.
- Ownership loss in the gap between the Producer lease and Admission lease is
  not retried with a replacement Grant. The already-issued presentation may be
  retried only while that exact session remains live; otherwise AIO-050's new-
  session/new-Run recovery rule applies.

## Coordinator lifecycle

The published coordinator has a terminal, idempotent `close()` boundary. An
internal lifecycle lock changes `LIVE -> CLOSING -> CLOSED`; entering
`CLOSING` rejects new operations. Close waits for already-registered outer
coordination calls to finish without holding a lock they need. It then closes
the AIO-050 Producer and paired port, terminally closes the latch, and closes
the AIO-049 session so its operation leases quiesce and the Windows ownership
lock and ledger pin are released. All cleanup steps are attempted even when
one raises; state remains terminal and no capability is republished. A repeated
close is safe, and every post-close operation fails closed.

Composition failure uses the same terminal cleanup discipline but ends the
latch in `FAILED`. Phase 2 must cover close-versus-operation, close after bind,
post-close calls, failure after bind, cleanup exceptions, and ownership lock
release. Lifecycle coordination adds no ownership authority and cannot bypass
AIO-049 session state.

## Restart model and hard recovery boundary

The predecessor contracts impose these exact limits:

1. **Restart before Grant issuance:** create a new Owned Session and Producer,
   authenticate fresh principal and authority proofs, and use a new Run. No old
   process-local proof or issuance state is authority.
2. **Restart after presentation but before Admission:** the old AIO-050
   presentation cannot be recovered or authenticated. Recovery requires a new
   session, new Run, fresh proofs, and a new Grant. The old Run is not silently
   reissued.
3. **Restart after authoritative Admission:** the AIO-047 SQLite record remains
   durable and authoritative and must never be replaced or contradicted. The
   old AIO-050 presentation is nevertheless unavailable, so the supported
   integrated public path cannot reload that historical Admission after
   restart. AIO-052 must not claim otherwise or add presentation persistence.
4. **Resolver reconstruction:** rebuilding the identical append-only AIO-051
   snapshot deterministically reproduces the historical Binding for the exact
   old Grant/Run. This proves Tool identity stability; it does not authenticate
   an old Grant or create a cross-restart Admission-recovery capability.

Same-process exact retry and AIO-047 ledger durability are supported. End-to-end
post-restart historical-Admission retrieval is not. If such retrieval is a
required outcome, it is a material new authority/persistence problem and this
Task must stop for Human architecture review.

## Audit correlation

Nonsecret correlation may use only existing identities: `task_id`, `run_id`,
Grant identity, `tool_id`, `authorization_domain_id`, domain generation, and
the existing Admission identity/composite. Audit material is explanatory only,
is not authority, and is not an Execution Journal. No speculative tracking ID
is introduced.

## Public-contract and persistence decisions

- New public integration schema: **NO**.
- New Grant, Tool Binding, Admission, or Run schema: **NO**.
- New Integration Admission or Integration ID: **NO**.
- Producer/presentation persistence: **NO**.
- Integration persistence: **NO**.
- AIO-047 contract change: **NO**.
- AIO-049 contract change: **NO**.
- AIO-050 contract change: **NO**.
- AIO-051 contract change: **NO**.

The private authentication latch is a composition detail in the AIO-052 module,
not a serializable contract. A material need to change any predecessor contract
or add a public schema requires an immediate stop and Human review.

## Expected Phase 2 artifacts

The minimal anticipated new files are:

```text
core/local-operational-trust-integration-specification.md
engineering_orchestration/local_operational_trust.py
tests/test_local_operational_trust.py
```

Only focused terminology, package/export, exact predecessor regression, or
test-support changes proven necessary by the locked design may accompany them.
No predecessor behavior change is pre-authorized by this list.

## Phase 2 scenario matrix

Every rejection is fail-closed. Every row must prove dispatch `NO`, invocation
`NO`, and repository resource read `NO`. Disposable SQLite and ownership-
metadata I/O is allowed and must not be mislabeled as repository Tool resource
access.

Rows owned by a predecessor boundary, including retired pre-Run selection and
an intentionally contradictory resolver-port result, are proven through exact
focused predecessor regression evidence. They must not replace a real trust
component in the central integrated path or add an impossible input to the
Local Coordinator API. In particular, the production AIO-051 resolver always
constructs `Binding.run` from the authenticated `Grant.run`; the mismatch row
proves AIO-047's defense in depth without claiming that canonical AIO-051 emits
such a value.

| # | Scenario | Required result |
| ---: | --- | --- |
| 1 | Happy-path exact Human approval | One real authoritative disposable Admission |
| 2 | Happy-path exact policy `allow` | One real authoritative disposable Admission |
| 3 | Policy `deny` | AIO-050 denial; no Grant presentation or Admission |
| 4 | Malformed authority proof | AIO-050 rejection |
| 5 | Run changed after approval | Exact subject mismatch; rejection |
| 6 | Direct or fabricated canonical Grant | AIO-050 authentication rejects it |
| 7 | Tampered issued presentation or Grant record | AIO-050 authentication rejects it |
| 8 | Wrong authorization domain | Fail before Store admission |
| 9 | Ownership lost | AIO-049 fail-closed result |
| 10 | Domain fenced or session closed | Operation rejected before authentication |
| 11 | Wrong domain generation | Producer or ownership rejection |
| 12 | Unknown Tool route | AIO-051 returns no Binding; AIO-047 rejects |
| 13 | Retired Tool route at AIO-051 pre-Run selection | Real pre-Run selector rejects before Run construction; Admission resolver remains historically total |
| 14 | Tool-ID rebind attempt | Registry construction fails atomically |
| 15 | Wrong Runtime | Exact route/Run checks reject |
| 16 | Wrong environment | Exact route/Run checks reject |
| 17 | Wrong operation | Exact route/Run checks reject |
| 18 | Resource widening attempt | Fresh reconstruction or exact Run agreement rejects |
| 19 | Grant/Binding Run mismatch | AIO-047 rejects exact mismatch |
| 20 | Expected Run mismatch | AIO-047 rejects exact mismatch |
| 21 | Fresh-source value missing, unavailable, invalid, unsatisfied, or Run-mismatched | AIO-047 rejects before Store admission; source owns bounded freshness provenance |
| 22 | Invalid or insufficient execution mode | Contract reconstruction rejects |
| 23 | Separately authenticated original-issuer revocation | Under real `session.revoke(...)`, proof validation forwards the embedded issued presentation through the sealed AIO-050 path; Store records revocation and later Admission rejects |
| 24 | Expired Grant | AIO-047 currentness rejects |
| 25 | Same-process exact Admission retry | Same historical Admission; no new facts or write |
| 26 | Restart after Admission | Durable record remains authoritative; old presentation cannot reload it |
| 27 | Registry reconstruction after restart | Exact historical Binding reproduced |
| 28 | Ledger corruption or incompatible schema | Official Store fails closed |
| 29 | Attempted Tool fallback | Rejected; no alternate Tool selected |
| 30 | `runtime_option_id` or `option_id` substitution after Run creation | Rejected; no separate Provider field or post-Run override is invented |
| 31 | Authentication-latch call before bind | Returns no Grant |
| 32 | Authentication-latch second bind or target substitution | Terminal fail-closed rejection |
| 33 | Composition or adapter bind failure | Nothing published; session and Producer closed |
| 34 | Exact pre-Admission in-process retry | Same AIO-050 presentation; no replacement Grant |
| 35 | Repository Tool identity reaches Admission | Binding only; no callable behavior or file open |
| 36 | Ownership close/fence/loss between issuance and Admission leases | Second lease fails before authentication or Store access; no reissue |
| 37 | Coordinator close races an in-flight operation | In-flight call quiesces; no new call enters; terminal cleanup releases ownership |
| 38 | Operation after coordinator close | Fail closed with no Producer, session, resolver, or Store call |
| 39 | Expired/foreign principal or authority proof and foreign adapter/session epoch | AIO-050 rejects before issuance |
| 40 | Issuer disablement or epoch change after issuance but before Admission | Paired AIO-050 port rejects under the second owned lease |
| 41 | Fabricated/tampered value enters through `session.admit(...)` | Owned operation reaches real paired authentication and fails; port is never called directly by the test |

## Validation-safety policy

No Phase 1 validator, test, smoke, lint, or Quality Gate is authorized. Before
each future command, the exact target source must be statically inspected. An
absent, changed, broader, or unknown command requires stop and Human
authorization before execution.

### Validation Safety Matrix

| ID | Exact future scope | Safety condition | Phase 1 status |
| --- | --- | --- | --- |
| V1 | Exact AIO-052 `task.yaml` against exact Task schema using a direct loader | No legacy validator and no Task catalog traversal | NOT RUN |
| V2 | Exact `architecture-change.yaml` against exact Workflow schema using a direct loader | No Workflow catalog traversal | NOT RUN |
| T1 | `tests.test_local_operational_trust` only | Entire exact module statically reviewed first | NOT RUN |
| T2 | Exact AIO-047 conformance and SQLite modules named in the Phase 2 amendment | Static preflight and no discovery | NOT RUN |
| T3 | Exact AIO-049 ownership modules named in the Phase 2 amendment | Static preflight; disposable domain only | NOT RUN |
| T4 | Exact AIO-050 Producer module | Static preflight; synthetic authority only | NOT RUN |
| T5 | Exact AIO-051 registry and resolver modules | Static preflight; identity only, no callable Tool | NOT RUN |
| A1 | Explicit anticipated changed Python paths only | `ast.parse`, no discovery or glob | NOT RUN |
| M1 | Explicit AIO-052 and exact changed specification Markdown paths only | No glob or broad traversal | NOT RUN |
| S1 | Exact target-safe package smoke only if package surface changes | Entire exact script revision re-read; `--target-safe` mandatory | NOT RUN |
| G1 | Bounded Git branch, HEAD, status, explicit-path diff, stat, cached stat, and diff check | No history or catalog discovery | Baseline metadata only; Gate NOT RUN |

Prohibited throughout AIO-052: legacy validator `--help`, catalog-wide Task or
Workflow validation, broad discovery, broad unit-test discovery,
repository-wide verification, recursive repository search, broad Markdown
globs, bare package smoke, and any command absent from an approved matrix.

## Protected-target boundary

The protected target must not be opened, read, searched, grepped, recursively
enumerated, specifically listed, statted, hashed, resolved,
permission-inspected, or used as a fixture. Its identity must not be
investigated. Registering and binding the abstract `repository_file_read`
identity performs no repository read. Categorical AIO-052 protected-target
non-access remains certifiable at this checkpoint.

## Preimplementation experiment decision

**PREIMPLEMENTATION EXPERIMENT REQUIRED: NO.**

The completed predecessor implementations and their exact interfaces provide
enough evidence for the design. The one-time latch is a locked composition
mechanism, not an exploratory mutation. If its fail-closed properties cannot be
implemented directly under the existing contracts, work stops rather than
experimenting or weakening a trust boundary.

## Phase boundaries

Phase 1 may end only after the exact four artifacts describe one identical
design, fresh Architect, Security, and Operational Trust/Integration reviews
approve it with no unresolved blocker or high finding, the process-safety state
is truthfully resolved, and the Human reaches the Phase 2 checkpoint.

Phase 2 requires separate explicit Human authorization. Phase 3 final reviews,
the two Quality Gates, final Human approval, closure, staging, and a commit are
separate later decisions.

Cancellation supersedes those prospective phase boundaries. No Phase 2 or
Phase 3 work is authorized for this cancelled Task.
