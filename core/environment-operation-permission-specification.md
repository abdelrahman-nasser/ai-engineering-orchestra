# AI Engineering Orchestra - Environment Operation Permission Observation Specification

Version: 0.1.0

This document defines the canonical Environment Operation Permission
Observation contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

An **Environment Operation Permission Observation** is an immutable,
caller/environment-supplied observation describing the currently known
effective environment-permission state for one known Agent Runtime Option to
perform one Core-defined abstract operation against one exact lexical
repository-relative resource in one opaque caller-identified environment,
within one caller-owned evaluation snapshot.

It answers only:

> What is the currently known effective environment-permission state for this
> exact Runtime, environment, operation, and resource in the supplied snapshot?

Core validates supplied evidence. It does not independently discover or verify
native permission truth.

The following separation is mandatory:

```text
requirement
!= capability
!= permission observation
!= Permission Decision
!= Human or policy authorization
!= execution
```

An `allowed` observation does not authorize an operation, and Human or policy
authorization does not establish that the environment permits it. Runtime
availability is also independent from permission state.

---

## 2. Canonical Value and Identity

The observation contains exactly these fields, in this order:

| Field | Required | Purpose |
| --- | --- | --- |
| `runtime_option_id` | Yes | Exact reference to one known Agent Runtime Option |
| `environment_id` | Yes | Opaque exact identifier for the caller-owned snapshot environment |
| `operation_id` | Yes | Exact identifier of one Core-defined abstract operation |
| `resource` | Yes | Exact lexical repository-relative resource |
| `state` | Yes | Currently known effective environment-permission state |

```yaml
runtime_option_id: primary-agent-runtime
environment_id: synthetic-evaluation-environment
operation_id: repository_file_read
resource: synthetic/input.txt
state: allowed
```

Its exact identity is:

```text
(runtime_option_id, environment_id, operation_id, resource)
```

All four identity parts are exact and case-sensitive. Core does not trim,
case-fold, normalize, resolve, alias, or rewrite them. `state` is not part of
identity, and there is no `permission_id` or other synthetic identity.

### `runtime_option_id`

`runtime_option_id` is a required nonempty string referencing one Definition in
the supplied Agent Runtime Option inventory. It remains explicit because one
environment may contain multiple Runtime principals or execution surfaces, and
one Runtime may be evaluated in multiple environments. Permission evidence
must not leak across either scope.

### `environment_id`

`environment_id` is a required, nonempty, opaque, exact, case-sensitive string
owned by the caller within one evaluation context. It does not define an
Environment entity, type, topology, lifecycle, host, container, sandbox,
workspace, registry, persistence model, or discovery surface. Core does not
infer the Runtime from the environment identifier.

### `operation_id`

`operation_id` uses the Core operation syntax and vocabulary shared with
Operation Requirement and Runtime Operation Capability Observation through
`engineering_orchestration._operation_vocabulary`. The current supported
vocabulary contains exactly:

```text
repository_file_read
```

The syntax is exact ASCII lower-snake-case:

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

### `resource`

`resource` uses the exact extension-neutral lexical repository-resource grammar
defined by the Operation Requirement contract. It is forward-slash separated
and repository-relative. Validation never normalizes or accesses it.

### `state`

`state` is required and has exactly these values, in this order:

- `allowed`
- `denied`
- `unknown`

These are observation states. They are not the separate Permission Decision
values `allow`, `ask`, `always-ask`, and `deny`.

---

## 3. State Semantics

### `allowed`

Positive caller/environment-supplied evidence states that the current
environment permits the exact Runtime, operation, and resource action in the
supplied snapshot.

It does not establish a Permission Decision, Human or policy authorization,
Runtime availability, capability, dispatchability, execution, or success.

### `denied`

Positive caller/environment-supplied evidence states that the current
environment does not permit the exact Runtime, operation, and resource action
in the supplied snapshot.

It is an observed negative environment fact, not Runtime unavailability,
missing evidence, a policy decision, lack of Human approval, or a failed
invocation.

### `unknown`

No reliable current determination is available in the supplied snapshot.

Unknown is not denied. Stale, unreliable, or indeterminately current native
evidence must be omitted or supplied as unknown; it must not be represented as
allowed. Core cannot independently verify freshness.

---

## 4. Snapshot Inputs and Foundational Validation

`validate_environment_operation_permission` consumes a caller-supplied Runtime
Option inventory, a caller-supplied observation iterable, and one exact
`environment_id` that scopes the snapshot. The Runtime inventory is captured
once before the observations are captured once. Caller inputs remain
unmodified.

### Runtime Option inventory

The captured Runtime Option sequence is validated through
`validate_agent_runtime_option_inventory`. Existing inventory diagnostics,
ordering, duplicate handling, and atomicity are preserved. An invalid Runtime
inventory invalidates the permission snapshot and yields no normalized
observations. No later snapshot or observation validation occurs.

### Snapshot environment

The snapshot `environment_id` must be an exact nonempty string. An invalid value
produces exactly:

```text
environment_operation_permission_environment_id_invalid
```

with the fixed message:

```text
Environment Operation Permission snapshot environment_id must be an exact nonempty string.
```

This foundational finding stops observation validation and normalization.

### Exact observation values

The runtime API accepts only exact
`EnvironmentOperationPermissionObservation` values. Any other supplied value
produces, at most once:

```text
environment_operation_permission_observation_invalid_type
```

with the fixed message:

```text
Each supplied Environment Operation Permission Observation must be an exact EnvironmentOperationPermissionObservation value.
```

For exact observation objects, `runtime_option_id` and `environment_id` must be
exact nonempty strings; `operation_id` and `resource` must be exact strings;
and `state` must be an exact `EnvironmentOperationPermissionState` value. A
malformed field or state produces, at most once:

```text
environment_operation_permission_observation_invalid
```

with the fixed message:

```text
A supplied Environment Operation Permission Observation contains malformed fields or state.
```

An empty exact-string `operation_id` proceeds to operation syntax validation,
and an empty exact-string `resource` proceeds to canonical resource validation.
Type and malformed-value findings are emitted in the order above and stop
relation validation and normalization.

---

## 5. Repeated Identities and Conflicting Evidence

At most one observation may be supplied for each exact
`(runtime_option_id, environment_id, operation_id, resource)` identity.

### Identical duplicates

A repeated identity whose supplied observations all have the same state is an
invalid identical duplicate. Each such identity produces one:

```text
duplicate_environment_operation_permission
```

with the fixed message shape:

```text
Environment Operation Permission Observation identity (runtime_option_id={runtime_option_id!r}, environment_id={environment_id!r}, operation_id={operation_id!r}, resource={resource!r}) has more than one supplied observation with the same state.
```

Each `!r` substitution renders the escaped exact Python representation of its
corresponding identity value.

### Conflicting observations

A repeated identity containing more than one state is invalid conflicting
evidence. This includes `allowed + denied`, `allowed + unknown`, `denied +
unknown`, every reversed declaration order, and larger mixed-state groups. Each
such identity produces one:

```text
conflicting_environment_operation_permission
```

with the fixed message shape:

```text
Environment Operation Permission Observation identity (runtime_option_id={runtime_option_id!r}, environment_id={environment_id!r}, operation_id={operation_id!r}, resource={resource!r}) has conflicting supplied states.
```

Identical duplicate and conflict findings are mutually exclusive for one
identity. A mixed-state group is a conflict only, even if one state is repeated.
Identical duplicates are reported before conflicts; identities within each
category are sorted by the exact four-part identity.

Conflicting permission observations are invalid evidence. A conflict
invalidates the complete snapshot and is never converted to denied, unknown, a
Permission Decision, or a Human approval question. There is no first-wins,
last-wins, latest-wins, allowed-wins, deny-wins, stricter-wins, deduplication,
or declaration-order precedence.

Reconciliation belongs to the caller/environment evidence producer. It must
reconcile native facts outside Core and resupply one observation that accurately
represents the intended snapshot. AIO-038 never determines which conflicting
fact is authoritative.

---

## 6. Relationship Findings

After repeated identities, validation reports the following categories in this
fixed order.

### Unknown Runtime references

An observation whose `runtime_option_id` is absent from the validated inventory
produces one finding per distinct unknown Runtime Option ID:

```text
agent_runtime_option_not_found
```

with the established fixed message shape:

```text
Agent Runtime Option '<runtime_option_id>' was not found in the supplied inventory.
```

Distinct IDs are sorted exactly and case-sensitively.

### Environment scope mismatches

An observation whose `environment_id` differs exactly from the snapshot scope
produces one finding per distinct observed environment ID:

```text
environment_operation_permission_environment_mismatch
```

with the fixed message shape:

```text
Environment Operation Permission Observation environment_id {observed_environment_id!r} does not match snapshot environment_id {snapshot_environment_id!r}.
```

The representations are escaped exact Python representations. Distinct observed
environment IDs are sorted exactly and case-sensitively. A mismatch is invalid
input, not denied, unknown, or an automatically added environment.

### Operation syntax and support

Each distinct malformed operation ID produces:

```text
operation_id_invalid_syntax
```

with the fixed message:

```text
Environment Operation Permission Observation operation_id must use ASCII lower_snake_case syntax.
```

Each distinct well-formed unsupported operation ID produces:

```text
operation_id_not_supported
```

with the established fixed message shape:

```text
Operation ID '<operation_id>' is not supported by Core.
```

Malformed identifiers are not support-checked. IDs are exactly sorted within
each category. Unsupported operations are invalid input, not permission denial.

### Resource grammar

Resource validation reuses one package-internal helper shared with Operation
Requirement. The helper returns the first applicable canonical issue in this
fixed precedence:

```text
resource_empty
resource_control_character
resource_unc_path
resource_absolute_path
resource_drive_qualified_path
resource_uri_scheme
resource_leading_tilde
resource_backslash
resource_trailing_slash
resource_empty_segment
resource_dot_segment
resource_parent_segment
resource_glob_meta
```

Each distinct invalid resource produces one finding with that canonical code
and the fixed message shape:

```text
Environment Operation Permission Observation resource {resource!r} {message_suffix}
```

`!r` supplies the escaped exact Python representation. The exact code-to-suffix
mapping is:

| Code | `message_suffix` |
| --- | --- |
| `resource_empty` | `must not be empty.` |
| `resource_control_character` | `must not contain control characters.` |
| `resource_unc_path` | `must not use a UNC path.` |
| `resource_absolute_path` | `must be repository-relative.` |
| `resource_drive_qualified_path` | `must not be drive-qualified.` |
| `resource_uri_scheme` | `must not use a URI scheme.` |
| `resource_leading_tilde` | `must not start with a tilde.` |
| `resource_backslash` | `must use forward-slash separators.` |
| `resource_trailing_slash` | `must not end with a slash.` |
| `resource_empty_segment` | `must not contain an empty segment.` |
| `resource_dot_segment` | `must not contain a dot segment.` |
| `resource_parent_segment` | `must not contain a parent segment.` |
| `resource_glob_meta` | `must not contain glob meta characters.` |

Resource findings are ordered first by the thirteen-code precedence above and
then by exact resource. The shared helper changes none of the public AIO-036
Operation Requirement codes, messages, precedence, behavior, or atomicity.

---

## 7. Deterministic Order and Atomicity

Runtime validation uses this exact order:

1. capture the Runtime Option inventory once;
2. capture the supplied observations once;
3. validate the complete Runtime Option inventory;
4. validate the snapshot `environment_id`;
5. validate exact observation value types, fields, and states;
6. report identical duplicate identities;
7. report conflicting identities;
8. report unknown Runtime Option references;
9. report observed-environment mismatches;
10. report malformed operation identifiers;
11. report well-formed unsupported operation identifiers;
12. report invalid resources in canonical resource-issue order; and
13. when there are no findings, sort the supplied observations by exact
    `(runtime_option_id, environment_id, operation_id, resource)`.

Finding categories follow this order. Values within a category use the exact
sorting rules stated above. Declaration order creates no preference,
precedence, recency, authority, or policy strength.

Any finding invalidates the complete snapshot:

```text
valid: false
findings: nonempty tuple
normalized_observations: ()
```

No invalid result contains partial normalized observations. No supplied object
is corrected, deduplicated, normalized, or mutated.

---

## 8. Missing Observations and Canonical Output

A valid result preserves only the supplied observations, sorted by their exact
four-part identity:

```text
valid: true
findings: ()
normalized_observations: canonically ordered supplied tuple
```

The observations themselves are not rewritten. Ordering is deterministic
representation only; it establishes no preference, recency, authority, policy
result, or execution order.

A missing exact observation semantically means unknown, never denied. AIO-038
adds no lookup API. Because the resource domain is open-ended, snapshot
validation does not synthesize any Runtime x environment x operation x resource
Cartesian product. Missing-to-unknown applies only when a future separately
designed exact lookup or composition assesses one exact subject.

An empty valid observation iterable produces an empty normalized tuple after
the Runtime inventory and snapshot environment are still validated.

---

## 9. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/environment-operation-permission.schema.json`

It validates one object with exactly the five required fields, nonempty string
identity/reference fields, a closed `allowed`/`denied`/`unknown` state enum, an
object root, and no additional properties.

The schema does not validate Runtime inventory references, snapshot environment
scope, operation syntax or support, lexical resource grammar, duplicates,
conflicts, ordering, missing semantics, or result atomicity. This specification
is the semantic authority, and the pure runtime validator owns those semantic
rules.

---

## 10. Ownership, Currency, and No-I/O Boundary

Ownership remains:

```text
Framework/Core
-> operation vocabulary, state meanings, validation, canonical ordering,
   and lexical repository-resource grammar

Environment/caller
-> observation truth, opaque environment identity, snapshot currency,
   snapshot coherence, and conflict reconciliation
```

The observation contains no timestamp, freshness, expiry, source, provenance,
reason, policy, authorization, metadata, or extension field. Its currentness is
a caller-owned evaluation-snapshot obligation. Core cannot determine whether a
caller supplied stale evidence.

Validation is pure and lexical. It never:

- opens, reads, writes, stats, hashes, resolves, lists, or existence-checks a
  resource;
- discovers, polls, probes, or verifies Runtime, environment, sandbox, ACL,
  tool, credential, or permission state;
- consults a filesystem, repository root, current working directory, network,
  subprocess, clock, cache, database, or persistent store;
- evaluates permission policy or Human Control evidence;
- mutates permissions or environment state; or
- creates an execution request or Execution Contract, dispatches, executes, or
  invokes anything.

---

## 11. Adjacent Contract Boundaries

Operation Requirement states caller-declared need. Runtime Operation Capability
Observation states technical support for an operation class in principle.
Agent Runtime Option Availability Observation states whether a Runtime is
currently available. Environment Operation Permission Observation supplies an
environment-scoped fact for one exact resource. None implies another.

These combinations are coherent:

```text
capability present + permission denied
permission allowed + Runtime unavailable
permission allowed + authorization evidence missing
authorization evidence granted + permission denied
```

None authorizes execution. AIO-038 changes no AIO-036 Operation Requirement,
AIO-037 Runtime Operation Capability Observation, Agent Runtime Option
Availability Observation, Permission Decision, or Human Control semantics.

Agent Execution Authorization Evidence is a separate caller-attested assertion
for one exact assigned external-inference Agent action. `allowed` does not
create `granted` evidence, `denied` permission does not create `denied`
authorization evidence, and either evidence category may be missing while the
other is present. The authorization-evidence contract is defined in
`core/agent-execution-authorization-evidence-specification.md`.

Agent Action Prerequisite Assessment may privately look up one exact
Runtime/environment/operation/resource identity from a coherent AIO-038
result. Missing exact permission remains unknown, and an invalid permission
result remains invalid rather than becoming denied or blocked. The separate
derived contract is defined in
`core/agent-action-prerequisite-specification.md`.

The separate Permission Decision vocabulary remains exactly:

```text
allow
ask
always-ask
deny
```

Those are policy/authority decisions, not observation states. AIO-038 performs
no Permission Decision composition or stricter-wins resolution.

The earlier private read-only execution preparation experiment retains its own
provisional, harness-specific evidence types and freshness modeling. It is not
retrofitted into this canonical contract, and AIO-038 does not consume or
canonicalize that experiment's permission or authorization evidence.

---

## 12. Runtime and Package API

Immutable values and pure deterministic snapshot validation are defined in:

`engineering_orchestration.environment_operation_permission`

The submodule exposes:

- `EnvironmentOperationPermissionState`
- `EnvironmentOperationPermissionObservation`
- `EnvironmentOperationPermissionFinding`
- `EnvironmentOperationPermissionValidationResult`
- `validate_environment_operation_permission(observations, runtime_options,
  environment_id)`

The exact value and function shapes are:

```python
EnvironmentOperationPermissionObservation(
    runtime_option_id: str,
    environment_id: str,
    operation_id: str,
    resource: str,
    state: EnvironmentOperationPermissionState,
)

EnvironmentOperationPermissionFinding(
    code: str,
    message: str,
)

EnvironmentOperationPermissionValidationResult(
    valid: bool,
    findings: tuple[EnvironmentOperationPermissionFinding, ...],
    normalized_observations: tuple[
        EnvironmentOperationPermissionObservation, ...
    ],
)

validate_environment_operation_permission(
    observations: Iterable[EnvironmentOperationPermissionObservation],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
    environment_id: str,
) -> EnvironmentOperationPermissionValidationResult
```

Runtime values and result containers are frozen and tuple-backed. The package
root does not re-export these names. The structural schema and runtime module
are packaged resources/code; no new external dependency is introduced.

The shared private helpers are:

- `engineering_orchestration._operation_vocabulary` for operation syntax and
  support; and
- `engineering_orchestration._repository_resource` for the canonical first
  lexical repository-resource issue.

The latter exposes the frozen internal value
`RepositoryResourceValidationIssue(code, message_suffix)` and
`validate_repository_resource(resource)`, which returns the first issue or
`None`.

Neither helper is a public registry, permission engine, or discovery surface.

---

## 13. Exclusions

The first contract contains no:

- permission ID, Actor, Task, Workflow, Stage, Role, Inference Option, Provider,
  model, tool, timestamp, freshness, expiry, source, provenance, reason, policy,
  authorization, metadata, or extension field;
- Environment Definition, type, topology, host, container, sandbox, workspace,
  registry, lifecycle, persistence, or discovery contract;
- Runtime capability or availability field, Operation Requirement, Permission
  Decision, Human/policy authorization result, approval parsing, or authority
  inference;
- conflict-resolution policy, first/last/latest/allowed/deny/stricter winner,
  automatic Human escalation, or cross-environment merge;
- synthetic missing observation, unbounded resource enumeration, or Cartesian
  permission snapshot;
- filesystem or environment inspection, ACL query, sandbox query, Runtime
  probing, polling, network access, subprocess, clock, cache, or database;
- permission enforcement or mutation, concrete tool binding, adapter, Provider
  integration, CLI, or Project Manifest field; or
- Execution Contract, request, dispatch, session, execution, or invocation.

Future Permission Decision, authorization production, lookup, composition,
enforcement, or execution-layer contracts require separately authorized design.
They must preserve this observation contract's exact evidence-only meaning.
