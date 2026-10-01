# Agent Operation Tool Registry and Resolver Specification

## Status

This document is the authoritative semantic contract for the AIO-051 Trusted
Agent Operation Tool Registry and Resolver foundation in AI Engineering
Orchestra v0.1.x.

The registry, its registrations, its internal result values, and its audit
material are private process-local implementation contracts. They are not new
serialized Core values and have no public schema. The existing Agent Operation
Tool Binding specification and schema remain authoritative for the resolver's
canonical output. The existing AIO-047 resolver port remains authoritative for
the integration seam.

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, and **MAY** are
normative.

## Purpose

The Trusted Agent Operation Tool Registry and Resolver establishes one
explicit, trusted, deterministic mapping from an exact immutable
Runtime/environment/operation route to one immutable configured Tool identity.
It constructs the canonical Agent Operation Tool Binding for the exact Run in
an authenticated Agent Execution Authorization Grant.

It separates configured Tool identity from discovery, availability, adapter
construction, permission, Admission, dispatch, and invocation. In particular:

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

## Scope

This specification defines:

- the private frozen Agent Operation Tool Registration;
- one atomic, deeply immutable, process-local trusted registry snapshot;
- permanent exact route-to-Tool mapping;
- immutable scoped Tool identity and no-rebind rules;
- optional pre-Run aliases to complete canonical routes;
- new-route/new-Tool-ID upgrades;
- retirement as pre-Run selection policy while preserving history;
- deterministic restart and append-only package-upgrade resolution;
- exact Runtime, environment, and operation applicability;
- canonical Binding construction through the unchanged AIO-047 resolver port;
- closed private outcomes and retry dispositions;
- bounded nonsecret audit material; and
- the identity-only first native `repository_file_read` Tool declaration.

This specification does not define:

- a public registration, registry, route, alias, result, or audit schema;
- a writable registry, database, external service, or persistent selection
  store;
- dynamic discovery, ranking, fallback, or post-Run reselection;
- live Tool availability, health, credentials, endpoints, or commands;
- a callable Tool adapter or repository file reader;
- physical resource containment, file opening, or repository access;
- Grant authentication, consumption, revocation, or Admission persistence; or
- dispatch, invocation, Result, or execution lifecycle.

## Preserved canonical contracts

### Agent Operation Tool Binding

The AIO-045 `AgentOperationToolBinding` remains exactly:

```text
run
tool_id
```

No route, alias, registration, selector, revision, retirement, availability,
credential, fingerprint, or metadata field is added. Direct construction or
intrinsic validity does not establish trusted resolver provenance.

### AIO-047 resolver port

The resolver implements the unchanged integration seam:

```python
class AgentOperationToolBindingResolverPort(Protocol):
    def resolve_tool_binding(
        self,
        grant: AgentExecutionAuthorizationGrant,
    ) -> AgentOperationToolBinding | None: ...
```

The input is the exact authenticated Grant. It is not a raw Run, alias,
registry revision, selection token, Tool ID, candidate list, or caller-created
Binding. AIO-051 MUST NOT change the signature or add outcomes to AIO-047.

At that boundary, `None` or a resolver exception is handled by AIO-047 as
`untrusted_tool_binding`. A noncanonical, invalid, or Run-mismatched returned
value remains AIO-047 `invalid_input`.

### Responsibility split

| Boundary | Responsibility |
| --- | --- |
| Trusted composition root | Supply package-owned declarations, atomically build the snapshot, and inject the paired resolver |
| Pre-Run routing | Select one active complete route, optionally through an alias, before Run construction |
| Registry snapshot | Preserve permanent route and scoped Tool-ID mappings plus current alias and retirement policy |
| AIO-051 resolver | Reconstruct one exact Binding from the Grant's complete Run and permanent mapping |
| AIO-047 coordinator and Store | Validate the Binding, reconstruct the expected Run, classify history, consume authority, and create or return Admission |
| Future dispatcher and adapter | Recheck retirement and availability, enforce containment and permission, and invoke |

## Trust model

Registry trust derives only from trusted composition-root construction using
explicit package-owned declarations and exact trusted route configuration.
Resolver trust derives from injection of the resolver paired with that
successfully built snapshot.

None of the following proves provenance:

- a Python class or dataclass shape;
- direct construction;
- a caller dictionary, file, Registration, registry, alias, or Binding;
- a caller-supplied `trusted` flag;
- a fingerprint; or
- serialization and restoration.

Python privacy protects against accidental miscomposition. It does not defend
against malicious arbitrary code already executing inside the trusted process.

Construction MUST publish the complete snapshot and resolver together or
publish neither. A construction failure MUST prevent coordinator composition.

## Private implementation contracts

The following names are the locked process-local concepts:

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

Private result and evidence values MUST be frozen, deterministic, and
process-local. `_ResolvedAgentOperationToolRegistration` is only the exact
private lookup result of the trusted snapshot. It is not authoritative outside
the configured resolver call and does not mirror or replace the public Binding.

`TrustedAgentOperationToolBindingResolver` is a direct-module integration
class. Neither the resolver nor any private contract is a package-root export,
and none has a public serialized schema.

The registry module has no public export surface. The resolver module exports
only `TrustedAgentOperationToolBindingResolver`. Its constructor requires one
exact `_TrustedAgentOperationToolRegistrySnapshot`. Its rich private
`resolve(...)` result contains exactly `outcome`, `retry_disposition`,
`resolved_registration`, `binding`, and `audit`; the public integration method
remains only `resolve_tool_binding(grant)`.

## Agent Operation Tool Registration

The private frozen Registration has exactly these semantic fields:

```text
runtime_option_id
environment_id
operation_id
tool_id
implementation_selector
```

The first three fields form the exact canonical route. `tool_id` is the
canonical AIO-045 identity. `implementation_selector` is a closed,
package-owned, non-callable token that names the implementation family a future
adapter layer may open.

The selector MUST NOT be:

- an import or module path;
- an arbitrary callable, factory, class, or object handle;
- a command, executable, endpoint, or environment variable;
- an entry point, marketplace item, Provider, or discovery result;
- a credential or secret reference;
- an availability observation; or
- a generic configuration bag.

A Registration has no separate registration ID, implementation revision,
configuration digest, display name, metadata bag, resource, repository root,
glob, lifecycle field, or fingerprint field. The complete five-value tuple is
its private semantic identity. The Tool ID itself denotes the immutable
implementation and security-relevant configuration revision.

Every string identifier admitted into Registration identity, an exact route,
an alias, or snapshot fingerprint material MUST be an exact nonempty `str`
that is representable by strict UTF-8 encoding before fingerprint
construction. This includes `runtime_option_id`, `environment_id`,
`operation_id`, `tool_id`, the closed implementation-selector value, and alias
identifiers. Unpaired surrogate code points are invalid. Construction MUST
reject malformed identifiers without producing a snapshot or allowing
`UnicodeEncodeError` to escape. It MUST NOT replace, ignore, normalize, or use
`surrogatepass` to reinterpret malformed input.

## Exact route model

The canonical route is:

```text
(
  runtime_option_id,
  environment_id,
  operation_id,
)
```

For resolution, it is projected only from:

```text
(
  grant.run.contract.runtime_option_id,
  grant.run.contract.environment_id,
  grant.run.contract.operation_id,
)
```

All components and lookups are exact and case-sensitive. There is no
normalization, case-folding, wildcard, default, prefix match, parent-environment
match, compatible-Runtime inference, operation-family match, Provider/model
ranking, nearest match, or fallback.

One exact route maps permanently to exactly one canonical Tool ID.

## Tool identity and no-rebind semantics

The canonical Tool identity namespace remains:

```text
(runtime_option_id, environment_id, tool_id)
```

Within that scope, one Tool ID denotes exactly one implementation and
security-relevant configuration revision forever. A Registration adds exact
operation applicability; it does not alter the Binding namespace.

The following changes require a new Tool ID and, when selectable for future
Runs, a distinct complete route:

- adapter implementation;
- protocol or endpoint semantics;
- containment or permission-enforcement semantics;
- operation behavior;
- security-relevant configuration; or
- any other execution or trust-meaning change.

Documentation wording, display names, Human aliases, and nonsecurity
presentation metadata outside Registration do not by themselves require a new
Tool ID.

An existing route MUST NOT be rebound, even for future Runs. A different
`run_id` alone cannot distinguish another Tool choice because the Run has no
Tool selection, registry revision, route generation, or selection timestamp.

## Atomic snapshot construction

The local v1 registry is one validated, frozen, process-local snapshot. The
trusted composition root builds it from explicit package-owned Python
declarations and exact trusted policy indexes.

Before publication, construction MUST:

1. require exact private Registration, route, alias, and retirement value
   types;
2. intrinsically validate every route component, Tool ID, closed selector
   value, and alias identifier as an exact strict-UTF-8-encodable string;
3. validate every implementation selector against the closed selector set;
4. reject every duplicate exact route, including an equal duplicate;
5. reject every duplicate or contradictory scoped Tool identity;
6. validate every alias and retirement reference against a known complete
   route;
7. copy all caller-supplied values into fresh owned maps and immutable
   containers;
8. compute only optional audit fingerprint material; and
9. publish the complete snapshot and paired resolver together or neither.

Construction MUST NOT use first-wins, last-wins, declaration-order
precedence, deduplication, overwrite, partial publication, a fallback snapshot,
or best-effort mode.

The snapshot contains immutable indexes by exact route and exact scoped Tool
identity, a monotonic retirement set, an optional alias-to-route index, and an
optional registration-set fingerprint. It retains no caller-owned mutable
backing object. There is no mutable global registry. Concurrent resolver calls
observe the same immutable snapshot.

## Permanent historical mapping

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

Therefore the same complete Run resolves to the same Binding across repeated
resolution, process restart, and an append-only package upgrade. Adding a new
route cannot alter an old result. Retirement changes only current selection
policy and never changes `F`.

This proof fails if a route is rebound, an alias supplies a Tool after Run
creation, or an old Registration disappears. If same-route upgrade,
post-Run alias choice, or resolver-enforced distinction between new work and
history becomes required, implementation MUST stop for a Human architecture
decision between durable Run-to-Tool selection state and a Run/AIO-047
contract change. AIO-051 introduces neither.

## Cross-release preservation and fingerprint limits

A process snapshot can detect current duplicates and contradictions. It cannot
prove that an earlier package was not rewritten because it has no independently
trusted prior state.

Permanent no-rebind across releases is therefore also a release and
supply-chain invariant. Package declarations and cross-version fixtures MUST
retain every old route, scoped Tool ID, implementation meaning, and expected
Binding. Release review MUST reject deletion, reinterpretation, or mutation.

An optional fingerprint is integrity and audit material only unless a future
trusted deployment mechanism independently pins it. It is never authority,
provenance, a registry identity, or a substitute for the append-only review
invariant.

## Alias model

An optional alias is a private pre-Run routing convenience:

```text
alias -> (runtime_option_id, environment_id, operation_id)
```

It maps to one complete already registered route, never directly to a Tool on
an unchanged route. Alias lookup occurs outside the AIO-047 resolver. Alias
spelling and selected-route proof never enter the Run, Grant, Binding,
Admission, or a public schema. The new Run embeds the selected route through
its existing Contract fields.

Aliases are exact and case-sensitive. Empty aliases, duplicate aliases,
unknown targets, alias chains or cycles, canonical Tool-ID shadowing, and
canonical-route spelling substitution invalidate construction or selection.
There is no operational alias API exposed to an untrusted caller in v1.

Retargeting an alias affects only future pre-Run selection and MUST target a
different complete canonical route. It cannot mutate an existing Run.
Retargeting to a new Tool ID on the same route is a prohibited route rebind.

## Upgrade model

A selectable implementation upgrade MUST:

1. introduce a new Tool ID;
2. append a new exact route Registration;
3. retain every old Registration unchanged;
4. optionally move a pre-Run alias to the new complete route; and
5. create a new Run and complete downstream authority chain.

The normal sequence is:

```text
new route + new tool_id
-> new Run
-> new Grant
-> new Binding
-> new Admission
```

The distinct route must already be representable in the new Run, normally by
a new immutable Runtime Option or environment identity. No existing Binding or
Admission is upgraded or mutated.

## Retirement model

Retirement never deletes, changes, or rebinds a Registration. It marks the
route nonselectable in a separate monotonic current pre-Run policy index.

Pre-Run selection of a retired route returns `tool_retired` and no selected
route. An alias cannot make a retired route selectable for a new Run.
Reactivation requires a new architecture decision.

The unchanged AIO-047 port receives only the Grant and is called before both
guarded historical lookup and new Admission work. It cannot distinguish those
uses. The resolver therefore remains total for every retained registered route,
including retired routes, and reconstructs the original Binding. It MUST NOT
return `None` merely because the route is retired; otherwise exact historical
retry/load would become unreachable.

Trusted upstream composition MUST create new Runs only from active selected
routes. AIO-051 cannot prove that a caller did not fabricate a new post-
retirement Run because route-selection provenance is absent from the Run and
Grant.

A future dispatcher MUST perform a fresh retirement and just-in-time
availability check before invocation and fail closed without Tool substitution.
Historical Binding and Admission identity remain unchanged.

## Restart and package-upgrade behavior

On restart, trusted composition atomically rebuilds the snapshot from the full
package-owned historical manifest. Under the permanent-route invariant, the
same Run resolves to the same Binding.

A compatible upgrade may only:

- append a new route and new Tool identity;
- retire an old route while retaining its Registration; or
- add or retarget an alias to another registered complete route for future
  Runs.

It may not remove an old Registration, change an old route mapping, reuse an
old scoped Tool ID, reinterpret a selector, reactivate a retired route, or
retarget an existing Run. Missing history fails closed as
`historical_mapping_missing`; it MUST NOT consult a network, source checkout,
prior snapshot, alternate registry, alias, or fallback Tool.

## Pre-Run selection

Selection accepts only an exact canonical route or exact configured alias in
the trusted pre-Run boundary. A successful result preserves the complete
canonical route and Registration identity required for the caller to construct
a new Run. It does not create a Run, Grant, Binding, or Admission.

Selection MUST fail closed for malformed input, an unknown route or alias, a
retired route, an invalid snapshot, or contradictory state. It MUST NOT return
a fallback or infer a compatible route.

## Exact resolver algorithm

`TrustedAgentOperationToolBindingResolver` MUST perform these steps in order:

1. require the exact `AgentExecutionAuthorizationGrant` concrete type;
2. intrinsically validate the complete Grant;
3. read the route only from `grant.run.contract`;
4. perform one exact lookup in the immutable permanent historical route map;
5. fail closed on missing, contradictory, or integrity-invalid state;
6. construct
   `AgentOperationToolBinding(run=grant.run, tool_id=registration.tool_id)`;
7. intrinsically validate the new Binding;
8. require `binding.run is grant.run` and complete value equality; and
9. return that exact canonical Binding.

The resolver MUST NOT accept a caller Binding, Tool ID, alias, Registration,
registry, route override, resource, trust boolean, candidate list, or fallback
choice. It MUST NOT copy, normalize, flatten, rebuild, or project the Run.

A rich private `resolve(...)` operation MAY return the closed internal outcome,
retry disposition, optional resolved Registration, optional Binding, and audit
material. The AIO-047 `resolve_tool_binding(...)` method returns a Binding only
for `resolved`; every private rejection collapses to `None`.

## Exact applicability and resource preservation

Runtime applicability is exact equality with
`grant.run.contract.runtime_option_id`. Environment applicability is exact
equality with `grant.run.contract.environment_id`. Operation applicability is
exact equality with `grant.run.contract.operation_id`.

The initial supported operation is exactly `repository_file_read`. There is no
generic filesystem operation or operation substitution.

The exact lexical resource belongs only to the Operation Requirement,
Contract, and complete Run. It is absent from the route and Registration. The
resolver MUST NOT inspect, normalize, resolve, replace, prefix, widen, open, or
otherwise use it. Constructing the Binding with the identical Run object
preserves the resource and every other Contract field structurally.

Physical repository-root association, symlink/junction/reparse handling,
containment, file kind, size, encoding, time-of-check/time-of-use control,
permission, and opening belong to a future adapter and dispatch boundary.

## First Tool identity

The first canonical Tool ID is:

```text
tool::aeo-native-repository-file-read::v1
```

Its closed implementation selector is:

```text
AEO_NATIVE_REPOSITORY_FILE_READ_V1
```

It denotes the immutable v1 identity of an AEO-owned native Python
`repository_file_read` implementation family. Every production Registration
still requires an exact Runtime Option, environment, and
`repository_file_read` route. No wildcard is allowed.

AIO-051 provides identity, registration, selection, and Binding resolution
only. It does not provide, locate, construct, or invoke a callable repository
reader.

## Discovery, availability, and secret boundaries

Registry and resolver behavior MUST remain shell-free and discovery-free. It
MUST NOT perform or expose:

- PowerShell, `cmd`, a shell, subprocess, or command execution;
- PATH or CLI lookup;
- import entry-point or marketplace discovery;
- MCP, Provider SDK, filesystem, or network discovery;
- process, health, availability, or reachability probes; or
- adapter construction or invocation.

Configured identity is not current availability or executability. A future
dispatcher/adapter owns just-in-time availability immediately before
invocation and MUST fail closed without same-Run fallback.

Passwords, tokens, keys, credentials, secret values or references, endpoints,
commands, environment dumps, and authentication material MUST NOT enter a
Registration, snapshot, Binding, Admission, result, audit value, diagnostic,
or log. The first Tool requires no credential broker.

## Closed outcome taxonomy

The private closed outcome vocabulary is:

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

Operation-specific result types use only coherent subsets. `tool_retired`
belongs to pre-Run selection and future dispatch policy, never historical
resolution. `historical_mapping_missing` identifies a route trusted
composition was required to retain. No availability outcome may be fabricated
without a prohibited availability probe.

## Retry dispositions

The closed retry vocabulary is:

| Disposition | Meaning |
| --- | --- |
| `no_retry_needed` | Exact route and Binding resolved |
| `new_run_required` | Select another active canonical route and construct a new Run and authority chain |
| `registry_remediation_required` | Repair snapshot construction or integrity before composing a resolver |
| `package_or_configuration_remediation_required` | Correct trusted declarations or exact route/selector configuration without fallback |
| `historical_mapping_remediation_required` | Restore the exact original declaration and meaning; never remap the old Run |
| `do_not_retry_same_run` | The same Run cannot validly progress |

The exact outcome mapping is:

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

Future availability retry belongs to dispatcher/adapter policy. No outcome or
retry disposition permits another Tool for the same Run.

## Audit and disclosure boundary

A private result MAY carry one frozen nonsecret audit value containing, when
available:

- outcome and retry disposition;
- the exact input Run ID;
- the one requested route;
- the canonical Tool ID only on an exact resolved or known-subject path;
- a fixed resolver implementation identity; and
- an audit-only snapshot fingerprint.

Audit is not authority, provenance, a public schema, or a durable Journal sink.
It MUST NOT expose:

- full object representations;
- complete registry or alias catalogs;
- unrelated known routes;
- package paths, callables, or implementation selectors;
- stack traces or free-form internal exceptions;
- commands, endpoints, environment values, or configuration objects;
- resources; or
- credentials or secrets.

Internal errors collapse to closed outcomes.

## Required historical-resolution evidence

Synthetic tests MUST prove:

```text
same immutable snapshot + same Run -> same Binding
restart + rebuilt identical historical manifest + same Run -> same Binding
append-only package upgrade + old Run -> old tool_id and same Binding
new route appended + new Run -> new tool_id without changing old Binding
retired registration + historical Run -> same historical Binding
retired route + pre-Run selection -> tool_retired and no selected route
missing historical mapping -> fail closed, no remap
same-route replacement attempt -> invalid snapshot or release evidence
```

Tests MUST also prove `binding.run is grant.run`, complete equality, and no
resource, Runtime, environment, operation, or Execution Mode alteration.

## Scenario disposition matrix

`Conditional` means a trusted Binding may proceed to AIO-047, whose Grant,
history, prerequisite, currentness, revocation, and Store rules remain
independent. Dispatch is **No** in every scenario.

| # | Scenario | Required disposition | Dispatch |
| --- | --- | --- | --- |
| 1 | Known exact active route | Exact Binding; AIO-047 conditional | No |
| 2 | Unknown route | `None`; stop | No |
| 3 | Alias resolves before Run | Complete active route; only a later new Run may bind | No |
| 4 | Alias retargeted to distinct route | Existing Run unchanged; future new Run may bind | No |
| 5 | Canonical Tool ID rebound | Invalid snapshot; coordinator not composed | No |
| 6 | Tool upgraded on distinct route | Each route-specific Run receives its own exact Binding | No |
| 7 | Retired route selected pre-Run | `tool_retired`; no selected route | No |
| 8 | Wrong Runtime | No exact mapping; stop | No |
| 9 | Wrong environment | No exact mapping; stop | No |
| 10 | Wrong operation | No exact mapping; stop | No |
| 11 | Resource widening attempt | Reject contradiction | No |
| 12 | Registry construction corrupted | No snapshot or coordinator | No |
| 13 | Registry unavailable | No snapshot or coordinator | No |
| 14 | Future secret unavailable | Identity unaffected; no secret check here | No |
| 15 | Tool physically unavailable | Identity may resolve; no fallback or probe | No |
| 16 | Resolver restart with identical manifest | Same Binding | No |
| 17 | Duplicate scoped Tool ID | Invalid snapshot | No |
| 18 | Duplicate route, including equal duplicate | Invalid snapshot | No |
| 19 | Fallback Tool requested | No substitute Binding | No |
| 20 | Tool changes after Admission | Existing Binding and Admission unchanged | No |
| 21 | Historical mapping missing after upgrade | Stop before Store disclosure | No |
| 22 | Package appends new Tool on new route | Old and new route-specific Bindings preserved | No |
| 23 | Package retires old Tool | Historical resolver returns original Binding | No |
| 24 | Canonical route mapping changes | Rebind evidence; stop and remediate history | No |
| 25 | First `repository_file_read` Registration | Identity-only synthetic resolution | No |
| 26 | Same route, new `run_id`, attempted new Tool | Original identity or invalid configuration; no upgrade | No |
| 27 | Upgrade via distinct encoded route | New Run receives new Binding; old Binding unchanged | No |
| 28 | Retired historical exact retry/load | Same original Binding; guarded history remains reachable | No |
| 29 | Resolver returns `None` or raises | AIO-047 `untrusted_tool_binding` | No |
| 30 | Resolver returns wrong or invalid type | AIO-047 `invalid_input` | No |
| 31 | Resolver returns Binding with different Run | AIO-047 `invalid_input` | No |
| 32 | Caller supplies Binding, registry, or alias | Caller value rejected as provenance | No |

## Security invariants

An implementation conforms only if all of the following remain true:

- trusted composition is the only registry and resolver provenance;
- construction is atomic and fail-closed;
- every published index is deeply immutable and independently owned;
- exact route matching cannot normalize, infer, rank, or fall back;
- one route maps permanently to one Tool ID;
- one scoped Tool ID keeps one implementation meaning forever;
- an alias is pre-Run and never enters a canonical value;
- retirement never deletes historical identity;
- the resolver preserves the exact Run object and cannot widen resource scope;
- caller Bindings and registries do not establish trust;
- fingerprints are audit-only;
- no discovery, availability probe, secret resolution, or persistence occurs;
- no callable adapter, resource access, Admission, dispatch, or invocation is
  implemented; and
- all internal failures collapse to closed nonsecret results.

## Failure and recovery rules

Malformed or contradictory construction input invalidates the complete
snapshot. Missing historical data never remaps an old Run. An invalid resolver
input or lookup never returns a partial Binding. Recovery follows only the
closed retry disposition associated with the outcome.

No remediation may introduce first-wins behavior, same-Run substitution,
same-route replacement, alternate-registry lookup, dynamic discovery, or
silent contract widening.

## Provider independence

Runtime Option and environment identities are opaque canonical values. The
registry and resolver contain no permanent assumption about Codex, Claude,
Antigravity, an MCP server, a Provider SDK, a model, or a marketplace. Future
provider-specific integration belongs behind a separately reviewed adapter
boundary.

## Foundation limitations

This foundation relies on trusted package composition and append-only release
review. It does not independently attest prior package history, authenticate
arbitrary in-process callers, persist Run-to-Tool choices, distinguish new
Admission work from historical lookup at the AIO-047 port, or enforce future
dispatch retirement.

A requirement for same-route replacement, resolver-level new-versus-history
retirement enforcement, public/cross-process registry values, persistent
selection, callable adapters, live discovery, availability, credentials,
physical containment, dispatch, or invocation requires a separate Human-
approved architecture change.
