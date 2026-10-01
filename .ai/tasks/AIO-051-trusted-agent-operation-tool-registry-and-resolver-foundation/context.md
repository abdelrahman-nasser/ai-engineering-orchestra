# AIO-051 Context

## Phase 1 authorization and verified baseline

Direct Human instruction authorizes Phase 1 only: create AIO-051, lock its
registry, resolver, security, historical-resolution, integration, and
validation-safety design, and prepare the Human Phase 2 checkpoint. It does not
authorize implementation, runtime or test files, tests, validators, package
smoke, AIO-050 implementation, AIO-052 creation, real Tool resolution,
Admission, dispatch, invocation, repository access, or protected-target access.

The verified starting point is `main` at
`145ac55215f272ecf8b94de95af9fd34e201ae25`, with a clean index, no tracked
diff, and exactly the four untracked AIO-050 Phase 1 Task artifacts. AIO-050
remains `in_progress`, Phase 1 complete, and unmodified. AIO-049 remains
completed at 81/81, AIO-048 remains cancelled at 94/100, AIO-047 remains
completed at 105/105, AIO-045 remains completed at 70/70, and AIO-030 remains
parked. AIO-051 was absent.

AIO-051 is a new immutable Task identity. Its direct dependencies are exactly
AIO-045 and AIO-047. AIO-036, AIO-037, AIO-038, AIO-041, AIO-042, AIO-043,
and AIO-049 are semantic or program-sequencing context. AIO-050 is an
independent trust track and is not a dependency.

Exactly four AIO-051 Task artifacts are created in Phase 1:

```text
task.yaml
context.md
acceptance-criteria.md
review.md
```

No runtime, test, schema, package, AIO-050, or other non-Task file may be
created or modified. If one becomes necessary, work stops for Human review.

## Canonical terms and objective

The canonical track term is **Trusted Agent Operation Tool Registry and
Resolver**.

The canonical semantic record term is **Agent Operation Tool Registration**.
It denotes one configured immutable implementation identity and exact route.
It is not a live Tool, availability observation, invocation descriptor,
Binding, Admission, or dispatch capability.

The objective is:

> Establish an explicit trusted Agent Operation Tool Registry that maps an
> exact immutable Runtime/environment/operation route to one immutable
> configured Tool identity and deterministically constructs the canonical
> Agent Operation Tool Binding without discovery, fallback, live availability
> probing, dispatch, or invocation.

The following inequalities are mandatory:

```text
Registration exists != Tool currently available
Registration exists != adapter executable
alias != canonical route
alias != canonical tool_id
route selected != Run created
Run created != Binding resolved
Binding resolved != permission or authorization
Binding resolved != Admission
Admission != dispatch
dispatch != invocation success
historical identity resolvable != retired Tool dispatchable
registry fingerprint != registry authority or canonical identity
```

## Preserved canonical contracts

AIO-045 remains authoritative. `AgentOperationToolBinding` keeps exactly these
fields in this order:

```text
run
tool_id
```

No registration, route, alias, adapter, revision, retirement, availability,
credential, fingerprint, or metadata field is added. The Binding schema is
unchanged. A directly constructed Binding is never trusted merely because it
is intrinsically valid.

AIO-047 remains the Admission boundary. Its exact existing resolver seam is:

```python
class AgentOperationToolBindingResolverPort(Protocol):
    def resolve_tool_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentOperationToolBinding | None: ...
```

The port takes the exact authenticated Grant, not a raw Run, alias, registry
revision, selection token, candidate list, or caller Binding. Its signature is
unchanged. AIO-047 calls it before guarded historical lookup as well as before
new Admission work. `None` or a resolver exception becomes AIO-047
`untrusted_tool_binding`; a noncanonical/invalid/mismatched result becomes
`invalid_input`. AIO-051 private outcomes do not silently extend AIO-047's
public outcome contract.

## Responsibility split

| Boundary | Responsibility |
| --- | --- |
| Trusted AEO composition root | Supply package-owned declarations, atomically build the snapshot, and inject the paired resolver into AIO-047 |
| Pre-Run route/alias selection | Choose one currently selectable complete immutable route before Run construction |
| Trusted registry snapshot | Preserve permanent route and scoped Tool-ID mappings plus separate current alias/retirement policy indexes |
| AIO-051 resolver | Reconstruct one exact Binding from the authenticated Grant's complete Run and permanent historical mapping |
| AIO-047 coordinator/Store | Validate Binding, compare exact Runs, classify history, consume authority, and create/return Admission |
| Future dispatcher/adapter | Check retirement and JIT availability, resolve physical implementation, enforce containment/permission, and invoke |

Trust derives from configured composition-root invocation. A Python class,
constructor, dataclass shape, caller dictionary/file, caller-supplied
Registration, caller Binding, `trusted` flag, fingerprint, or serialized value
does not prove registry or resolver provenance. Python privacy protects against
accidental miscomposition, not hostile arbitrary code already running inside
the trusted process.

## Permanent route identity

The exact route key is:

```text
(
  grant.run.contract.runtime_option_id,
  grant.run.contract.environment_id,
  grant.run.contract.operation_id,
)
```

All components are exact and case-sensitive. There is no normalization,
case-folding, wildcard, default route, prefix match, parent-environment match,
compatible-Runtime inference, operation-family match, Provider/model ranking,
or fallback.

The central v1 invariant is:

> One exact route maps permanently to exactly one canonical `tool_id`.

The route-to-Tool function is append-only and never retargeted. Even replacing
one route with a new Tool for only future Runs is prohibited because the Run
contains no Tool selection, registry revision, route generation, or selection
time. A different `run_id` alone cannot distinguish old and new Tool choices.

## Historical-resolution proof and hard boundary

Let:

```text
R(run) = (runtime_option_id, environment_id, operation_id)
F      = append-only partial function from route to tool_id
B(run) = AgentOperationToolBinding(run=run, tool_id=F(R(run)))
```

Snapshot validity requires functional uniqueness. Package-upgrade
compatibility requires:

```text
F_new restricted to domain(F_old) == F_old
```

Therefore the same complete Run resolves to the same Binding across process
restart and append-only package upgrade. Adding a genuinely new route cannot
alter an old result. Retirement changes only a separate new-Run selectability
predicate and never changes `F`.

This proof fails immediately if an exact route is rebound, if an alias supplies
a Tool after Run creation, or if old registrations disappear. If a future
requirement needs same-route Tool upgrade, resolver-enforced new-versus-history
retirement, or alias selection not encoded by a distinct route in the Run,
A+B is insufficient. Work must stop for a Human architecture decision between
durable Run-to-Tool selection state and a Run/AIO-047 contract change. Neither
is introduced by AIO-051.

## Private Registration model

The minimum private frozen Registration has exactly these semantic fields:

```text
runtime_option_id
environment_id
operation_id
tool_id
implementation_selector
```

The first three fields form the route. `tool_id` is the AIO-045 canonical
identity. `implementation_selector` is a closed package-owned non-callable
token naming the implementation family that a future adapter layer may open.
It is not an import string, module path, arbitrary callable, object handle,
command, executable, endpoint, environment variable, entry point, credential,
secret reference, availability state, or configuration bag.

There is no separate registration ID, implementation revision, configuration
digest, display name, metadata bag, alternate resource, repository root,
glob, lifecycle state, or fingerprint field. The full Registration tuple is
its private semantic identity, while `tool_id` itself denotes the immutable
implementation and security-relevant configuration revision.

The private Python concepts are locked as:

```text
_AgentOperationToolRoute
_AgentOperationToolRegistration
_AgentOperationToolImplementationSelector
_TrustedAgentOperationToolRegistrySnapshot
_SelectedAgentOperationToolRoute
_ResolvedAgentOperationToolRegistration
_AgentOperationToolRegistryBuildResult
_AgentOperationToolRouteSelectionResult
_AgentOperationToolResolutionResult
_AgentOperationToolRegistryOutcome
_AgentOperationToolRegistryRetryDisposition
_AgentOperationToolRegistryAuditMaterial
TrustedAgentOperationToolBindingResolver
```

They are process-local implementation contracts, not public serialized Core
values. `_ResolvedAgentOperationToolRegistration` is an exact private lookup
result only; it is not authoritative outside the configured resolver call and
does not mirror or replace the Binding.

## Registry physical model and atomic construction

The local v1 registry is one validated, frozen, process-local snapshot. The
trusted AEO composition root assembles it from explicit package-owned Python
declarations and exact trusted route configuration. There is no JSON/YAML
registry, database, writable runtime registry, live reload, hot swap, external
registry service, filesystem scanning, entry-point loading, or network source.

Snapshot construction is all-or-nothing:

1. require exact private Registration and policy-index value types;
2. validate every exact route component and canonical `tool_id`;
3. validate every implementation selector against the closed package-owned
   selector set;
4. reject every duplicate exact route, including an equal duplicate;
5. reject every duplicate or contradictory scoped Tool identity;
6. validate aliases and retirement indexes against known complete routes;
7. build fresh owned maps and immutable containers with no caller-retained
   mutable backing object;
8. compute optional audit-only fingerprint material; and
9. publish the complete snapshot and resolver together or publish neither.

No first-wins, last-wins, declaration-order precedence, deduplication,
overwrite, partial snapshot, fallback snapshot, or best-effort mode exists.
Construction failure prevents resolver/coordinator composition.

The snapshot contains immutable indexes by exact route and by exact scoped
Tool identity, a monotonic current retirement set, an optional alias-to-route
index, and an optional registration-set fingerprint. No mutable global
registry exists. Concurrent resolver calls observe one immutable snapshot.

## Tool identity and no-rebind semantics

The canonical namespace remains the AIO-045 namespace:

```text
(runtime_option_id, environment_id, tool_id)
```

Within that scope, one `tool_id` denotes exactly one implementation and
security-relevant configuration revision forever. A Registration route adds
the operation applicability needed by this registry; it does not alter the
canonical Binding namespace.

The following require a new `tool_id` and, if selectable for future Runs, a
new complete canonical route:

- adapter implementation change;
- protocol or endpoint-semantics change;
- containment or permission-enforcement semantics change;
- operation behavior change;
- security-relevant configuration change; or
- any other change that could alter execution or trust meaning.

Documentation-only wording, display-name changes, Human alias changes, and
nonsecurity presentation metadata outside the Registration do not by
themselves require a new `tool_id`. Such values never participate in canonical
resolution.

A current process snapshot can detect only current-snapshot duplicates and
contradictions. It cannot prove that a malicious or accidental package upgrade
did not rewrite all prior declarations because it has no trusted prior state.
Permanent no-rebind across releases is therefore a supply-chain/release
invariant: package declarations and cross-version fixtures must retain every
old route, scoped Tool ID, implementation meaning, and expected Binding.
Release review must reject deletion or mutation. A fingerprint is integrity or
audit metadata only unless independently pinned by a future trusted deployment
mechanism; it is never authority or canonical identity.

## Alias model

Aliases are optional private pre-Run routing conveniences. An alias maps to
one exact complete route, not directly to a Tool on an unchanged route:

```text
alias -> (runtime_option_id, environment_id, operation_id)
```

The target route must already have one permanent Registration. Alias lookup is
outside the AIO-047 resolver. The alias and selected-route proof never enter
the Run, Grant, Binding, Admission, or any public schema. The new Run embeds
the selected route through its existing Contract fields.

Aliases are exact and case-sensitive. Empty aliases, duplicate aliases,
unknown targets, alias chains/cycles, canonical Tool-ID shadowing, and
canonical route spelling substitution invalidate the whole snapshot. There is
no operational alias API exposed to an untrusted caller in v1.

Retargeting an alias affects only future pre-Run selections and is valid only
when the new target is a different complete canonical route. It cannot mutate
an existing Run. Retargeting an alias to a new `tool_id` on the same route is a
forbidden route rebind.

## Upgrade model

An implementation upgrade creates a new `tool_id` and appends a new exact
route Registration. The distinct route must already be representable in the
new Run, normally through a new immutable `runtime_option_id` or
`environment_id`. The pre-Run router may then move an alias to that new route.

The normal chain is:

```text
new route + new tool_id
-> new Run
-> new Grant
-> new Binding
-> new Admission
```

Merely changing `run_id` while keeping the same route cannot select an upgrade.
No existing Binding or Admission is silently upgraded.

## Retirement model and port limitation

Retirement never deletes or mutates the immutable Registration. It marks the
route/Tool nonselectable in the separate current pre-Run policy index. The
pre-Run selection operation returns `tool_retired` and cannot create a new
selected route from it. An alias cannot target a retired route for a new Run.

The unchanged AIO-047 port cannot distinguish new Admission from historical
lookup because both calls provide only the Grant and occur before Store history
classification. Therefore its historical resolver remains total for every
retained registered route, including retired routes, and reconstructs the same
Binding. It must not return `None` merely because the registration is retired.
Otherwise authoritative exact retry/load would become unreachable.

This creates an explicit composition precondition: canonical upstream routing
must create new Runs only from active selected routes. AIO-051 alone cannot
prove that a post-retirement Run was not fabricated because no route-selection
provenance is present in Run or Grant. A future Local Operational Trust
Integration must preserve that precondition. If port-level rejection of every
new retired-Tool Admission is required while historical load remains possible,
the unchanged AIO-047 contract is insufficient and work stops for Human review.

Future dispatch performs a fresh retirement/JIT check and fails closed before
invocation of a retired implementation. It never substitutes another Tool.
Historical Binding and Admission bytes remain unchanged.

## Restart and package-upgrade semantics

On restart the snapshot is atomically rebuilt from the full trusted
package-owned historical manifest. Under the permanent-route invariant, the
same Run resolves to the same Binding.

An upgrade may only:

- append a new route and new Tool identity;
- retire an old route while retaining its Registration; or
- add or retarget an alias to another already registered complete route for
  future Runs.

It may not remove an old Registration, change an old route mapping, reuse an
old scoped `tool_id`, reinterpret an implementation selector, reactivate a
retired route without a new architecture decision, or retarget an existing
Run. Missing historical mapping fails closed as
`historical_mapping_missing`; there is no network, source-checkout, prior
snapshot, or alternate registry fallback.

No persistent Run-to-Tool selection store and no AIO-047 or Run contract
change are required under these exact constraints. A requirement outside them
triggers the historical-resolution blocker rule.

## Exact resolver algorithm and AIO-047 integration

`TrustedAgentOperationToolBindingResolver` implements only the unchanged
AIO-047 port at the integration boundary. Its exact behavior is:

1. require the exact `AgentExecutionAuthorizationGrant` concrete type;
2. intrinsically validate the complete Grant;
3. read the exact route only from `grant.run.contract`;
4. perform one exact lookup in the immutable permanent historical route map;
5. fail closed on missing, contradictory, or integrity-invalid state;
6. construct
   `AgentOperationToolBinding(run=grant.run, tool_id=registration.tool_id)`;
7. intrinsically validate the newly constructed Binding;
8. require `binding.run is grant.run` and complete value equality; and
9. return that exact canonical Binding.

The resolver never accepts a caller Binding, `tool_id`, alias, Registration,
registry, route override, resource, trust boolean, candidate list, or fallback
choice. It does not copy, normalize, flatten, rebuild, or project the Run.

A rich private `resolve(...)` operation may return the locked internal outcome,
retry disposition, optional resolved Registration/Binding, and closed audit
material. The AIO-047 `resolve_tool_binding(...)` method returns only the exact
Binding on `resolved`; every internal rejection collapses to `None`. Exceptions
are caught at the AIO-047 coordinator and likewise become
`untrusted_tool_binding`. AIO-051 does not claim that its private outcome enum
crosses the existing port.

Raw caller Bindings remain freely constructible AIO-045 values and are never
accepted as resolver output provenance. Trust is the configured port call plus
the resolver's own snapshot and exact construction, not a wrapper or field.

## Applicability and resource no-widening

Runtime applicability is exact equality with
`grant.run.contract.runtime_option_id`. Environment applicability is exact
equality with `grant.run.contract.environment_id`. Operation applicability is
exact equality with `grant.run.contract.operation_id`. The initial supported
operation is exactly `repository_file_read`; there is no generic filesystem
operation or substitution.

The exact lexical resource remains owned solely by the Operation Requirement,
Contract, and complete Run. It is not part of the route or Registration. The
resolver does not inspect, normalize, resolve, replace, prefix, widen, or open
it and cannot inject a repository root, wildcard, sibling, parent, or alternate
resource. Constructing the Binding with the exact same Run object preserves the
resource structurally.

Physical repository-root association, symlink/junction/reparse handling,
containment, file kind, size limits, encoding, TOCTOU control, permission, and
opening are future adapter/JIT responsibilities. AIO-051 performs no resource
access.

## Availability and secret boundary

Configured Tool identity is not live availability or executability. The
registry and resolver perform no process check, health check, filesystem probe,
PATH lookup, import discovery, Provider query, MCP call, network request, or
adapter construction. Future dispatch/adapter code owns JIT availability
immediately before invocation and must fail closed without fallback.

No passwords, tokens, keys, credentials, opaque secret references, endpoints,
commands, environment dumps, or authentication material enter a Registration,
snapshot, Binding, Admission, result, audit value, diagnostic, or log. Secret
broker design is deferred until a concrete Tool requires credentials.

## First Tool identity

The first canonical Tool identity is locked as:

```text
tool::aeo-native-repository-file-read::v1
```

It denotes the immutable v1 identity of a native AEO-owned Python
`repository_file_read` implementation family. Its closed private implementation
selector is:

```text
AEO_NATIVE_REPOSITORY_FILE_READ_V1
```

Every production Registration must still provide an exact
`runtime_option_id`, exact `environment_id`, and the exact operation
`repository_file_read`; no wildcard route is permitted. Phase 2 may implement
only the identity declaration, private selector, registry mechanics, and
Binding resolver. It does not implement or obtain a callable adapter.

The posture is subprocess-less and shell-free: no PowerShell, `cmd`, shell,
PATH lookup, CLI discovery, MCP, Provider SDK call, importlib entry-point
discovery, marketplace, filesystem read, or protected-target operation.

## Closed outcome and retry taxonomy

The private closed semantic outcome vocabulary spans atomic construction,
pre-Run selection, and Binding resolution:

```text
resolved
registry_invalid
registry_unavailable
registration_invalid
unknown_route
unknown_tool
duplicate_route
duplicate_tool_id
tool_id_rebind
alias_invalid
alias_target_unknown
runtime_mismatch
environment_mismatch
operation_mismatch
resource_widening
tool_retired
historical_mapping_missing
adapter_kind_unknown
fingerprint_mismatch
integrity_failure
```

Operation-specific result types permit only coherent subsets. In particular,
`tool_retired` belongs to pre-Run selection and future JIT policy, never the
AIO-047 historical resolver; `historical_mapping_missing` belongs to resolution
of a route that trusted composition expected to retain; and no availability
outcome is synthesized without a forbidden probe.

The retry dispositions and mandatory meanings are:

| Disposition | Meaning |
| --- | --- |
| `no_retry_needed` | Exact route/Binding resolved successfully |
| `new_run_required` | Select a different active canonical route and construct a new Run plus the complete downstream authority chain |
| `registry_remediation_required` | Repair current snapshot construction/integrity before composing a resolver |
| `package_or_configuration_remediation_required` | Correct trusted package declarations or exact route/selector configuration; never fall back |
| `historical_mapping_remediation_required` | Restore the exact original declaration/meaning under controlled release remediation; never remap the old Run |
| `do_not_retry_same_run` | The same Run cannot validly progress |

The exact mapping is:

| Outcome | Retry disposition |
| --- | --- |
| `resolved` | `no_retry_needed` |
| `registry_invalid` | `registry_remediation_required` |
| `registry_unavailable` | `registry_remediation_required` |
| `registration_invalid` | `package_or_configuration_remediation_required` |
| `unknown_route` | `new_run_required` |
| `unknown_tool` | `package_or_configuration_remediation_required` |
| `duplicate_route` | `package_or_configuration_remediation_required` |
| `duplicate_tool_id` | `package_or_configuration_remediation_required` |
| `tool_id_rebind` | `historical_mapping_remediation_required` |
| `alias_invalid` | `package_or_configuration_remediation_required` |
| `alias_target_unknown` | `package_or_configuration_remediation_required` |
| `runtime_mismatch` | `new_run_required` |
| `environment_mismatch` | `new_run_required` |
| `operation_mismatch` | `new_run_required` |
| `resource_widening` | `do_not_retry_same_run` |
| `tool_retired` | `new_run_required` |
| `historical_mapping_missing` | `historical_mapping_remediation_required` |
| `adapter_kind_unknown` | `package_or_configuration_remediation_required` |
| `fingerprint_mismatch` | `historical_mapping_remediation_required` |
| `integrity_failure` | `registry_remediation_required` |

Future availability retry belongs to dispatcher/adapter policy and is not an
AIO-051 retry disposition. No outcome authorizes selecting another Tool for
the same Run.

## Audit and disclosure boundary

Private results may contain one pure nonsecret closed audit value with, when
available:

- outcome and retry disposition;
- exact input Run ID;
- the one requested route;
- canonical `tool_id` only on exact resolved/known-subject paths;
- fixed resolver implementation identity; and
- audit-only snapshot fingerprint.

Audit is not authority, a registry listing, a public schema, or a durable
Journal sink. It must not contain full object `repr`, complete registry or alias
catalogs, other known routes, package paths, callables, selectors, stack traces,
commands, endpoints, environment values, configuration objects, resources,
credentials, or secrets. Internal errors collapse to closed outcomes rather
than free-form exception disclosure.

## Public/private contract boundary

No new public serialized schema is introduced for Tool Registration, route,
registry snapshot, alias, selected route, resolved Registration, internal
result, retry disposition, or audit material. The AIO-045 Binding schema and
AIO-047 Admission schema remain unchanged. Any public/cross-process consumer
would require a new explicit Human architecture review.

## Scenario matrix

`Conditional` means the trusted Binding may proceed to AIO-047, whose Grant,
history, prerequisite, currentness, revocation, and Store rules remain
independent. Dispatch is `NO` in every scenario.

| # | Scenario | Registration trusted? | Route valid? | Tool identity trusted? | Binding allowed? | AIO-047 path | Dispatch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Known exact active route | Yes | Yes | Yes | Exact Binding | Conditional | No |
| 2 | Unknown route | No mapping | No | No | No | Stop: resolver returns `None` | No |
| 3 | Alias resolves before Run | Yes | Exact complete active route | Yes | Only after new Run embeds route | Conditional later | No |
| 4 | Alias retargeted to distinct route | New target trusted | New future route only | New canonical ID | Existing Run unchanged; new Run may bind | Conditional for new chain | No |
| 5 | Canonical `tool_id` rebound attempt | Contradictory | No valid snapshot | No | No | Coordinator not composed | No |
| 6 | Tool upgraded on distinct route | Old and new records trusted | Both permanent routes valid | Distinct IDs | Each Run gets its own exact Binding | Conditional | No |
| 7 | Retired route requested by pre-Run selector | Historical record retained | Nonselectable for new Run | Historical ID preserved | No new selected route | Stop/new Run route | No |
| 8 | Wrong Runtime | Registration may exist elsewhere | No exact route match | No | No | Stop | No |
| 9 | Wrong environment | Registration may exist elsewhere | No exact route match | No | No | Stop | No |
| 10 | Wrong operation | Registration may exist elsewhere | No exact route match | No | No | Stop | No |
| 11 | Resource widening attempt | Route may match | Run contradiction | No widened identity | No | Stop | No |
| 12 | Registry construction corrupted | No snapshot | No | No | No | Coordinator not composed | No |
| 13 | Registry unavailable | No snapshot | No | No | No | Coordinator not composed | No |
| 14 | Future secret unavailable | Identity unaffected | Yes | Yes as identity only | Binding may resolve | Conditional; secret not checked here | No |
| 15 | Tool physically unavailable | Identity unaffected | Yes | Yes as identity only | Binding resolves; no fallback | Conditional; availability deferred | No |
| 16 | Resolver restart with identical manifest | Yes | Same | Same | Same Binding | Conditional | No |
| 17 | Duplicate scoped `tool_id` | Invalid snapshot | Ambiguous/contradictory | No | No | Coordinator not composed | No |
| 18 | Duplicate route, even equal | Invalid snapshot | Ambiguous | No | No | Coordinator not composed | No |
| 19 | Fallback Tool requested | Original mapping only | No alternate allowed | No substitute trusted | No substitute Binding | Stop/new Run route | No |
| 20 | Tool changes after Admission | Historical registration unchanged | Original route permanent | Original ID only | Existing Binding unchanged | Historical Admission unchanged | No |
| 21 | Historical mapping missing after upgrade | Package invariant broken | Route cannot resolve | No | No | Stop before Store disclosure | No |
| 22 | Package appends a new Tool on new route | Yes | Old and new routes unique | Both immutable | Route-specific Bindings | Conditional | No |
| 23 | Package retires old Tool | Registration retained | Historical route remains resolvable | Old identity preserved | Historical resolver returns old Binding | Exact history may continue | No |
| 24 | Canonical route mapping changes accidentally | Rebind | Invalid release/snapshot evidence | No | No | Stop/remediate history | No |
| 25 | First `repository_file_read` Registration | Identity declaration only | Exact configured route required | `tool::aeo-native-repository-file-read::v1` | Synthetic resolution only in later tests | No real Admission | No |
| 26 | Same route, new `run_id`, attempted new Tool | Forbidden rebind | Same permanent route | Original ID only | Original Binding identity or reject configuration | No upgrade | No |
| 27 | Upgrade via distinct encoded route | Both registrations retained | New Run carries new route | New ID | New Binding | Conditional | No |
| 28 | Retired historical exact retry/load | Yes | Permanent historical route | Old ID | Same old Binding | Guarded history/load reachable | No |
| 29 | Resolver returns `None` or raises | No trusted result | Unresolved | No | No | AIO-047 `untrusted_tool_binding` | No |
| 30 | Resolver returns wrong/invalid type | No | Invalid | No | No | AIO-047 `invalid_input` | No |
| 31 | Resolver returns Binding with different Run | No | Contradiction | No | No | AIO-047 `invalid_input` | No |
| 32 | Caller supplies Binding/registry/alias | Caller value untrusted | Not consulted | No provenance | No | Stop | No |

## Required later historical-resolution evidence

Phase 2 tests must prove, with synthetic identities only:

```text
same immutable snapshot + same Run -> same Binding
restart + rebuilt identical historical manifest + same Run -> same Binding
append-only package upgrade + old Run -> old tool_id and same Binding
new route appended + new Run -> new tool_id without changing old Binding
retired registration + historical Run -> same historical Binding
retired route + pre-Run selection -> tool_retired and no selected route
missing historical mapping -> fail closed, no remap
same-route replacement attempt -> invalid snapshot/release evidence
```

Tests must also prove `binding.run is grant.run`, complete equality, and no
resource, Runtime, environment, operation, or Execution Mode alteration.

## Expected Phase 2 artifacts

Phase 1 proposes but does not create:

```text
core/agent-operation-tool-registry-and-resolver-specification.md
engineering_orchestration/agent_operation_tool_registry.py
engineering_orchestration/agent_operation_tool_resolver.py
tests/test_agent_operation_tool_registry.py
tests/test_agent_operation_tool_resolver.py
```

Focused changes may be required in `core/terminology.md`, exact AIO-045
integration regressions, exact AIO-047 resolver/coordinator regressions, and
package/import metadata. No other path is implicitly authorized. A callable
repository reader is not an expected AIO-051 file.

## Validation-safety policy

Before any validator, test, smoke, packaging, lint, static audit, or
verification command is executed, its exact executable, arguments, scope, and
protected-target safety must be established from approved syntax or static
inspection of the exact source revision.

```text
unknown command -> do not execute
unknown validator -> do not execute
legacy validator --help discovery -> prohibited
command absent from this matrix -> not authorized
```

An absent or changed command requires static review, a matrix amendment, and
explicit Human authorization. Phase 1 executes none of the Python, validator,
test, Markdown, package, or static-audit commands below.

### Validation Safety Matrix

| ID | Validation | Exact prospective scope | Safety basis | Phase 1 status |
| --- | --- | --- | --- | --- |
| V1 | AIO-051 Task schema | Exact AIO-051 `task.yaml` and Task schema only | Direct two-file loader; no catalog traversal | Locked; not executed |
| V2 | `architecture-change` Workflow schema | Exact Workflow YAML and Workflow schema only | Direct two-file loader; no Workflow/Role catalog traversal | Locked; not executed |
| T1 | Registry tests | `tests.test_agent_operation_tool_registry` only | Exact unittest module after complete static review | Planned; not authorized |
| T2 | Resolver tests | `tests.test_agent_operation_tool_resolver` only | Exact unittest module after complete static review | Planned; not authorized |
| T3 | AIO-045 regression | `tests.test_agent_operation_tool_binding` only | Exact existing module, statically re-reviewed first | Planned; not authorized |
| T4 | AIO-047 integration regression | `tests.test_agent_execution_dispatch_admission_store_conformance` only | Exact existing module, statically re-reviewed first | PASS after Human-authorized Phase 2 correction; 20 tests |
| A1 | AST parsing | Explicit final changed Python paths only | `ast.parse`; no glob or discovery | Planned; paths locked after Phase 2 scope confirmation |
| N1 | Static no-shell/discovery audit | Exact new registry/resolver modules only | Explicit file paths and closed prohibited-call patterns | Planned; not authorized |
| M1 | Markdown | Exact AIO-051 Task files, new specification, and `core/terminology.md` only if changed | Explicit paths; no glob or broad traversal | Planned; not authorized |
| S1 | Package smoke | Exact `tests/package_installation_smoke.py --target-safe` only | Entire exact script revision must be re-read first | Planned; not authorized |
| G1-G7 | Git metadata/diff | Exact branch, HEAD, status, name-status, stat, diff check, cached stat | Bounded repository metadata and current diff | Authorized as explicitly requested |
| P1 | Python verification | Exact fixed interpreter path with approved version diagnostics only | Environment-only, no discovery | Phase 2 must freshly authorize and execute |
| X1 | Legacy Task validator | Prohibited | Catalog-wide behavior | Not authorized |
| X2 | Legacy Workflow validator | Prohibited | Workflow/Role catalog behavior | Not authorized |
| X3 | Legacy validator `--help` | Prohibited | Discovery execution forbidden | Not authorized |
| X4 | Repository-wide verification | Prohibited | Broad scope and protected-target risk | Not authorized |
| X5 | Bare unittest/pytest discovery | Prohibited | Unbounded test discovery | Not authorized |
| X6 | Recursive repository search | Prohibited | Unknown-file traversal | Not authorized |
| X7 | Broad Markdown traversal | Prohibited | Unknown-file traversal | Not authorized |
| X8 | Bare package smoke | Prohibited | Non-target-safe checkout behavior | Not authorized |
| X9 | Tool/MCP/PATH/Provider discovery | Prohibited | Operational discovery outside Task scope | Not authorized |
| X10 | Unknown command | Prohibited | No static safety basis | Not authorized |

The exact proposed structural commands are recorded for later authorization.

`V1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/task.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'.ai/tasks/AIO-051-trusted-agent-operation-tool-registry-and-resolver-foundation/task.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact AIO-051 task schema')"
```

`V2`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/workflow.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'workflows/architecture-change.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact architecture-change workflow schema')"
```

The current environment fact is
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`,
previously observed as CPython 3.12.10 and executable through a Human-granted
Read+Execute ACL. Phase 2 must freshly verify it. This is environment
configuration, not product architecture.

AIO-051 has no symlink or elevation requirement. If registry/resolver work
needs real filesystem containment, symlink evidence, or privileged access,
scope has leaked into the callable adapter and work stops.

## Protected-target boundary

During AIO-051, the protected target must not be opened, read, searched,
grepped, recursively enumerated, specifically listed, statted, hashed,
resolved, permission-inspected, or used as a fixture. Its identity must not be
investigated. Registering the abstract `repository_file_read` identity performs
no repository read. Categorical AIO-051 non-access must remain certifiable.

No broad Task validation, Task catalog enumeration, Workflow catalog
enumeration, repository-wide verification, recursive repository search, broad
Markdown traversal, unknown-safety validator, bare package smoke, Tool/MCP/
PATH/Provider discovery, legacy validator `--help`, or command absent from the
approved matrix is permitted.

## Phase boundaries and Human checkpoint

Phase 1 ends only when the exact four Task artifacts are present and fresh
Architect, Security, and Resolver/Integration reviews approve the same final
design with zero unresolved blocker or high-severity finding and explicitly
accept the permanent-route historical-resolution proof and retirement split.

Phase 1 does not run final `documentation_consistency` or
`independent_review` Gates. Those require fresh post-implementation evidence.

If Phase 1 locks, both AIO-050 and AIO-051 trust tracks have completed Phase 1.
The next separately authorized action is AIO-050 Phase 2 implementation and
validation. AIO-051 Phase 2 intentionally waits for AIO-050 closure and a fresh
rebaseline.

The program sequence is:

```text
AIO-050 Phase 1 locked
-> AIO-051 Phase 1 lock
-> Human checkpoint
-> AIO-050 Phase 2 implementation, validation, closure, and commit
-> rebaseline AIO-051
-> separate AIO-051 Phase 2 authorization
```

AIO-052 and any Local Operational Trust Integration Task are not created or
allocated here.

## Phase 2 T4 validation-matrix correction

The initial Phase 2 attempt stopped before implementation or validation when
the locked T4 target, `tests.test_agent_execution_dispatch_admission_store`,
was found not to exist at the AIO-051 rebaseline. No substitute module was run.

The Human then explicitly authorized this single matrix correction:

```text
old: tests.test_agent_execution_dispatch_admission_store
new: tests.test_agent_execution_dispatch_admission_store_conformance
```

The new target is the existing focused AIO-047 Admission Store conformance
regression module intended by T4. The correction changes no architecture,
Phase 1 design, implementation scope, AIO-047 contract, Tool Binding,
Admission, AIO-050 artifact, or protected-target rule. Every other validation
matrix entry and prohibition remains unchanged. T4 must pass before the
already authorized AIO-051 Phase 2 work resumes.

After complete static inspection of the corrected exact module, T4 passed all
20 tests. The validation blocker is cleared, and the previously authorized
AIO-051 Phase 2 implementation and technical validation resumes from this
checkpoint. No other module was substituted or run.

## Phase 2 implementation and technical-validation checkpoint

### Authorization and implementation

The Human-authorized Phase 2 resumed only after corrected T4 passed. AIO-050
was already completed at 112/112 on baseline HEAD
`7969eadc0dac35ac13dae80d0ab90f1e5e2b19cc`. AIO-051 remains `in_progress`.
Phase 3, final reviews, Quality Gates, final Human approval, closure, staging,
and commit remain unauthorized.

Phase 2 added the canonical registry/resolver specification, the private
registry implementation, the trusted resolver, and exact focused registry and
resolver tests. Terminology and target-safe package evidence were updated only
as required. No AIO-045, AIO-047, AIO-050, schema, Grant, Run, Admission, or
AIO-049 implementation changed.

The registry atomically validates explicit package-owned declarations and
publishes one deeply immutable process-local snapshot. Registration remains a
private five-field value over exact Runtime Option, environment, operation,
canonical `tool_id`, and closed non-callable implementation selector. There is
no writable registry, database, dynamic discovery, live reload, availability
probe, generic configuration bag, endpoint, command, credential, or secret.

The permanent exact route function remains:

```text
(runtime_option_id, environment_id, operation_id) -> canonical tool_id
```

Aliases select a complete active route only before Run creation. Upgrades
append a distinct route and new Tool ID. Retirement blocks new pre-Run
selection but retains the immutable historical Registration. The optional
prior-snapshot compatibility check rejects deletion, route rebind, Tool-ID
reinterpretation, and retirement rollback. Under this append-only invariant,
restart and compatible package upgrade reproduce the same historical Binding
without a persistent Run-to-Tool store or AIO-047 contract change.

`TrustedAgentOperationToolBindingResolver` exact-type and intrinsically
validates the Grant, derives the route only from the finalized Run, looks up
the permanent historical map without alias or retirement policy, constructs
the existing `AgentOperationToolBinding(run=grant.run, tool_id=...)`, validates
it, and requires both complete equality and exact nested Run object identity.
Its unchanged AIO-047 port returns only the exact Binding on success and
collapses private rejection to `None`. It performs no fallback, resource
inspection or widening, availability probing, persistence, Admission,
dispatch, or invocation.

The first identity is
`tool::aeo-native-repository-file-read::v1` with selector
`AEO_NATIVE_REPOSITORY_FILE_READ_V1`. It is an identity-only declaration; no
callable repository reader, shell, subprocess, filesystem read, containment,
permission enforcement, or protected-target operation was implemented.

### Phase 2 validation evidence

All runtime tests are synthetic or in-memory. No real Tool was resolved, no
Grant was issued, no Admission was created, and no dispatch or invocation
occurred.

| Matrix ID | Result |
| --- | --- |
| P1 | PASS; exact interpreter reported Python 3.12.10 |
| V1 | PASS; exact AIO-051 Task schema |
| V2 | PASS; exact `architecture-change` Workflow schema |
| T1 | PASS; 20 exact registry tests |
| T2 | PASS; 11 exact resolver tests |
| T3 | PASS; 29 exact AIO-045 regressions |
| T4 | PASS; 20 corrected exact AIO-047 conformance regressions |
| A1 | PASS; five exact changed Python paths parsed with `ast.parse` |
| N1 | PASS; exact registry/resolver no-shell and no-discovery AST audit |
| M1 | PASS; five exact Markdown paths, zero issues |
| S1 | PASS; target-safe editable and wheel payload/import/location smoke |

The first N1 invocation used an overbroad generic call-name pattern that
flagged the resolver's own `resolve()` method. No source defect was present.
The corrected audit retained the exact two-file scope and all prohibited
external import/call checks while removing only that semantically invalid
generic name; it then passed.

The first M1 invocation also passed the Task YAML artifact to the Markdown
linter. The linter reported YAML structure as Markdown heading/list issues;
none of the five Markdown files had an issue. The corrected bounded M1
invocation retained the matrix's exact Markdown scope—three Task Markdown
artifacts, the new specification, and `core/terminology.md`—and passed with
zero issues. The Task YAML remained covered separately by V1.

The first sandboxed S1 attempt emitted only the interpreter line and stalled
for more than ten minutes, so it was terminated. The identical approved
target-safe command was rerun outside the restricted sandbox and reached the
editable install, where the expanded monolithic `python -c` import probe hit
Windows `WinError 206`. The smoke source was changed only to write that same
probe into the existing external temporary directory, execute the short script
path, and delete it in `finally`. A1 was rerun and passed; the final exact S1
rerun passed both editable and wheel modes. No bare smoke was used.

### Exact Phase 2 commands

`P1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B --version
```

`T1` through `T4`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_operation_tool_registry -v
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_operation_tool_resolver -v
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_operation_tool_binding -v
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_dispatch_admission_store_conformance -v
```

`A1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import ast,pathlib; paths=(r'engineering_orchestration/agent_operation_tool_registry.py',r'engineering_orchestration/agent_operation_tool_resolver.py',r'tests/test_agent_operation_tool_registry.py',r'tests/test_agent_operation_tool_resolver.py',r'tests/package_installation_smoke.py'); [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'), filename=p) for p in paths]; print('PASS exact AIO-051 changed-path AST parse')"
```

The successful `N1` command used the same fixed interpreter, parsed only
`engineering_orchestration/agent_operation_tool_registry.py` and
`engineering_orchestration/agent_operation_tool_resolver.py`, rejected the
closed prohibited import roots `glob`, `importlib`, `os`, `pathlib`, `pkgutil`,
`shutil`, `socket`, `sqlite3`, `subprocess`, and `urllib`, and rejected the
closed external-operation call names `open`, `read_text`, `read_bytes`,
`write_text`, `write_bytes`, `stat`, `listdir`, `scandir`, `getenv`, `system`,
`Popen`, `create_connection`, `urlopen`, `discover`, `probe`, `rank`,
`fallback`, `persist`, `consume`, `revoke`, `admit`, `dispatch`, `execute`, and
`invoke`. The initial false-positive invocation differed only by also including
the generic name `resolve` in that call-name set.

`S1`:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B tests/package_installation_smoke.py --target-safe
```

`M1`:

```powershell
npx --yes markdownlint-cli2 '.ai/tasks/AIO-051-trusted-agent-operation-tool-registry-and-resolver-foundation/context.md' '.ai/tasks/AIO-051-trusted-agent-operation-tool-registry-and-resolver-foundation/acceptance-criteria.md' '.ai/tasks/AIO-051-trusted-agent-operation-tool-registry-and-resolver-foundation/review.md' 'core/agent-operation-tool-registry-and-resolver-specification.md' 'core/terminology.md'
```

`V1` and `V2` were executed verbatim from the locked matrix above. Baseline
and final `G1` through `G7` use only the recorded bounded Git commands.

### Phase and safety status

- AIO-051 Phase 1: **COMPLETE**
- AIO-051 Phase 2: **COMPLETE**
- AIO-051 Phase 3: **NOT AUTHORIZED**
- Acceptance: **114/122**
- Task status: `in_progress`
- Material architecture change required: **NO**
- Unresolved blocker: 0
- Unresolved high finding: 0
- AIO-050 modified: **NO**
- Protected target accessed: **NO**
- Categorical AIO-051 protected-target non-access certifiable: **YES**
- Staging or commit: **NO**

Legacy validator help, unknown-safety validation, broad Task or Workflow
validation, catalog enumeration, repository-wide verification, recursive
repository search, broad Markdown traversal, bare smoke, and commands outside
the matrix were not used. AIO-051 remains stopped before Phase 3.

## Phase 3 final-review attempt and mandatory stop

The Human-authorized Phase 3 attempt reached specialist review and stopped on
the Security Final Review finding below. The prior Phase 2 checkpoint remains
historical evidence.

- Architect Final Review: **NOT COMPLETED**; interrupted at mandatory stop
- Security Final Review: **CHANGES REQUIRED**
- Resolver/Integration Final Review: **APPROVE**
- Formal Independent Review: **NOT RUN**
- `documentation_consistency`: **NOT RUN**
- `independent_review`: **NOT RUN**

The Security Final Review recorded:

- Finding: **SEC-051-1**
- Severity: **LOW**
- Review disposition: **CHANGES REQUIRED**
- Finding at review time: registration identifiers could contain unpaired
  Unicode surrogates, allowing strict UTF-8 snapshot fingerprint construction
  to raise `UnicodeEncodeError` instead of returning a closed rejection with
  no snapshot.

The Security verdict and finding are permanent historical review evidence.
No Phase 3 acceptance criterion was completed. Acceptance remained **114/122**,
and the Task remained `in_progress`.

## SEC-051-1 bounded Phase 2 remediation

The Human returned AIO-051 to Phase 2 solely to remediate `SEC-051-1`. This
authorization did not change the Tool Binding, exact-route model, Tool-ID
semantics, historical-resolution proof, persistence model, public schemas,
AIO-047, or AIO-050.

The root cause was that identifier validation accepted an exact nonempty
string without first proving strict UTF-8 encodability. Snapshot fingerprinting
later performed strict UTF-8 encoding, so an unpaired surrogate could escape
as `UnicodeEncodeError`.

One centralized strict UTF-8 identifier-validation rule now runs before
fingerprint construction for every string identifier admitted into canonical
registration identity, routing, registry validation, or fingerprint material.
Malformed identifiers are rejected through the existing closed
`registration_invalid` build outcome. No replacement, ignoring,
`surrogatepass`, or normalization is used, and no snapshot is published for
invalid input. A defensive fingerprint boundary also converts any unexpected
`UnicodeEncodeError` into the same closed rejection.

Focused evidence confirms:

- valid ASCII identifiers: accepted
- valid non-ASCII Unicode identifiers: accepted unchanged
- unpaired high surrogates: rejected
- unpaired low surrogates: rejected
- malformed `tool_id`: rejected
- malformed canonical route/identity fields: rejected
- malformed aliases: rejected
- escaping `UnicodeEncodeError`: none
- snapshot produced for invalid input: no
- normal fingerprint determinism: preserved
- restart and historical resolution: preserved
- registry tests: **PASS, 23/23**
- resolver tests: **PASS, 11/11**
- historical-resolution regression: **PASS**

Remediation-stop disposition:

- `SEC-051-1`: **REMEDIATED**
- Phase 2: **COMPLETE INCLUDING REMEDIATION**
- Phase 3: **FRESH RESTART REQUIRED**
- Acceptance: **114/122**
- Task status: `in_progress`
- Material design change required: **NO**
- Unresolved blocker/high/medium: 0
- Unresolved low from `SEC-051-1`: 0
- AIO-050 modified: **NO**
- Protected target accessed: **NO**
- Staging or commit: **NO**

## Fresh Phase 3 after SEC-051-1 remediation

The Human authorized a complete fresh Phase 3 review of the post-remediation
snapshot. The historical Security **CHANGES REQUIRED** verdict and
`SEC-051-1` finding above remain unchanged; the results below are separate
fresh reviews of the remediated implementation.

Fresh specialist results:

- Architect Final Review: **APPROVE**
- `SEC-051-1` architectural status: **CLOSED**
- Security Final Review: **APPROVE**
- `SEC-051-1` security status: **CLOSED**
- Resolver/Integration Final Review: **APPROVE**
- `SEC-051-1` integration impact: **NONE**
- Each specialist review: blocker 0, high 0, medium 0, low 0
- Specialist convergence: **YES**

The fresh reviews confirmed the exact two-field Binding, permanent exact route,
immutable Tool identity, no rebind or fallback, pre-Run-only aliases,
append-only upgrades, history-preserving retirement, identical complete Run
and resource preservation, repeat/restart/package-upgrade determinism, and no
persistent Run-to-Tool store or AIO-047 change. They also confirmed that strict
UTF-8 validation precedes fingerprint construction, preserves valid Unicode
unchanged, rejects malformed surrogate-bearing canonical identifiers and
aliases without a snapshot, and permits no escaping `UnicodeEncodeError` or
silent sanitization.

Fresh Formal Independent Review:

- `SEC-051-1` independent status: **CLOSED**
- Independent Technical Assessment: **APPROVE**
- Independent Security Assessment: **APPROVE**
- Independent Process Assessment: **COMPLIANT**
- Formal Independent Review: **APPROVE**
- Blocker 0, high 0, medium 0, low 0

Quality Gates:

- `independent_review`: **PASS WITHOUT WAIVER**
- `documentation_consistency`: **PASS WITHOUT WAIVER**
- All required Quality Gates passed: **YES**

Current checkpoint:

- Phase 1: **COMPLETE**
- Phase 2: **COMPLETE INCLUDING SEC-051-1 REMEDIATION**
- Phase 3: **COMPLETE**
- Acceptance: **122/122**
- Pending criteria: **NONE**
- Task status: `completed`
- Human final approval: **APPROVED**
- Final Human acceptance: **APPROVED**
- Human approval date: **2026-10-01**
- Human closure and one-local-commit authorization: **APPROVED**
- Closure date: **2026-10-01**
- Task closed: **YES**
- Push, merge, tag, release, or publication: **NOT AUTHORIZED**
- AIO-050 modified: **NO**
- Protected target accessed: **NO**
