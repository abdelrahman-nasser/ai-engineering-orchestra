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
- retirement enforced by active selection/resolution, with separate preserved history;
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
| Active registry snapshot | Resolve only eligible current routes with exact aliases and retirement policy |
| Permanent historical manifest | Preserve original route/Tool facts without active registration |
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

The permanent manifest preserves the exact original Binding identity across
restarts and upgrades. Active resolution applies only to eligible current routes;
retirement changes eligibility without rewriting the historical mapping. Missing
or rebound historical declarations fail closed. A new route must be distinct;
changing a Run ID alone never permits rebinding. Historical evidence retrieval
is separate from active Binding production.

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

Retirement preserves permanent historical facts and never rebinds a route.
Pre-Run selection and active Binding resolution of retired routes return
`tool_retired` without a selected route or new Binding. Legacy Tool declarations
are rejected by the active builder; an alias cannot reactivate them.

Authenticated exact historical lookup and original revocation use the separate
`_HistoricalExecutionEvidenceBoundary`, not the active resolver. The recorded
Binding remains unchanged, including its original Tool ID. Decoding it is not
active selection or authority. Intrinsic Binding validation remains capable of
reading old values. Claim/renewal/Entry/invocation reject legacy work.

## Restart and package-upgrade behavior

Trusted composition rebuilds the active view and separate complete permanent
historical manifest. Existing recorded Bindings are verified against historical
facts without producing new Bindings. Eligible current routes resolve through
the active view; historical evidence lookup uses the original durable record.

Compatible upgrades append distinct routes and Tool identities. Retirement can
remove active eligibility but never delete or reinterpret a historical fact.
Aliases affect eligible future selection only. Existing Run, route, scoped Tool
identity and implementation meaning remain permanent. Missing or rebound history
fails closed; no alternate registry, alias, network or identity normalization
supplies a replacement.

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
4. reject retired/legacy work and look up its eligible active route;
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

## Current native Tool identity

The current canonical native Tool ID is:

```text
tool::itru-native-repository-file-read::v1
```

Its closed implementation selector is:

```text
ITRU_NATIVE_REPOSITORY_FILE_READ_V1
```

It denotes the immutable v1 identity of an ITRU-owned native Python
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
belongs to active selection/resolution and dispatch policy, never evidence-only
historical lookup. `historical_mapping_missing` identifies a route trusted
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
same immutable snapshot + eligible active same Run -> same Binding
restart + complete permanent manifest + authenticated lookup -> original recorded Binding
append-only package upgrade + old Run -> old tool_id and same Binding
new route appended + new Run -> new tool_id without changing old Binding
retired registration + authenticated history lookup -> original recorded Binding
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
| 23 | Package retires old Tool | Authenticated historical boundary returns recorded Binding; active resolution rejects | No |
| 24 | Canonical route mapping changes | Rebind evidence; stop and remediate history | No |
| 25 | First `repository_file_read` Registration | Identity-only synthetic resolution | No |
| 26 | Same route, new `run_id`, attempted new Tool | Original identity or invalid configuration; no upgrade | No |
| 27 | Upgrade via distinct encoded route | New Run receives new Binding; old Binding unchanged | No |
| 28 | Retired historical exact retry/load | Original recorded Binding through the separate authenticated history boundary | No |
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

The foundation relies on trusted package composition and permanent historical
manifest/release review. It does not independently attest prior package history
or turn recorded data into current execution authority. Active resolution rejects
retired/legacy work; the separate authenticated historical boundary reads
existing evidence and revokes exact original authority without issuance.

Same-route replacement, public/cross-process registry values, persistent Tool
selection, live discovery or expanded adapter semantics still require a separate
Human-approved architecture change. The implemented cutover does not add these
capabilities or widen public signatures.

## Cutover compatibility

`AIO-059` preserves historical persisted
`tool::aeo-native-repository-file-read::v1` evidence exactly. This is a legacy
compatibility fact, absent from active registrations. Current native work uses
only `tool::itru-native-repository-file-read::v1` on a distinct configured route.
Active resolution rejects retired/legacy work; exact authenticated lookup and
original revocation use the separate historical evidence boundary and cannot
produce replacement authority. The permanent historical manifest remains
append-only and cannot rebind a route.

The [canonical cutover specification](itru-canonical-namespace-specification.md)
supersedes predecessor historical-resolution behavior described by this document.
