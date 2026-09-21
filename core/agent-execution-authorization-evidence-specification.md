# AI Engineering Orchestra - Agent Execution Authorization Evidence Specification

Version: 0.1.0

This document defines the canonical Agent Execution Authorization Evidence
contract for AI Engineering Orchestra v0.1.

---

## 1. Purpose

**Agent Execution Authorization Evidence** is an immutable, caller-supplied,
evaluation-scoped value asserting that one identified Human or policy authority
granted or denied one exact assigned external-inference Agent action.

It answers only:

> What authorization assertion did the caller supply for this exact assigned
> Agent, Runtime Option, external Inference Option, environment, operation, and
> lexical resource subject?

The category is Evidence. It is not an Observation, Grant, Permission Decision,
or decision made by Core. Core validates a supplied assertion describing a
decision made elsewhere. It neither issues authority nor authenticates the
asserted authority or provenance.

The following separation is mandatory:

```text
Assignment responsibility
+ Agent candidate prerequisites
+ Operation Requirement
+ Runtime Operation Capability Observation
+ Environment Operation Permission Observation
!= Agent Execution Authorization Evidence
!= execution
```

Task approval, candidate satisfaction, Runtime capability, and environment
permission do not manufacture authorization evidence. Conversely, `granted`
evidence does not establish capability, permission, freshness, entitlement, or
safe executability.

---

## 2. Canonical Value and Exact Subject

The value contains exactly these fourteen fields, in this order:

| Field | Required | Purpose |
| --- | --- | --- |
| `task_id` | Yes | Exact Task identity from the bound Assignment |
| `workflow_id` | Yes | Exact Workflow identity from the bound Assignment |
| `stage_id` | Yes | Exact Workflow Stage identity from the bound Assignment |
| `role_id` | Yes | Exact Role identity from the bound Assignment |
| `actor_id` | Yes | Exact selected Actor identity from the bound Assignment |
| `runtime_option_id` | Yes | Exact known Agent Runtime Option reference |
| `option_id` | Yes | Exact known external Inference Option reference |
| `environment_id` | Yes | Opaque exact evaluation-environment identity |
| `operation_id` | Yes | Exact Core-defined abstract operation identity |
| `resource` | Yes | Exact lexical repository-relative resource |
| `authority_kind` | Yes | Caller-attested authority category |
| `authority_id` | Yes | Exact opaque caller-scoped authority identity |
| `provenance_reference` | Yes | Exact opaque caller-supplied provenance reference |
| `state` | Yes | Caller-attested authorization state |

```yaml
task_id: AIO-SYNTHETIC
workflow_id: architecture-change
stage_id: implement
role_id: software-engineer
actor_id: agent-engineer-1
runtime_option_id: primary-agent-runtime
option_id: primary-inference-option
environment_id: synthetic-evaluation-environment
operation_id: repository_file_read
resource: synthetic/input.txt
authority_kind: human
authority_id: human-reviewer-1
provenance_reference: approval-record-1
state: granted
```

The exact action subject is the first ten fields:

```text
(
  task_id,
  workflow_id,
  stage_id,
  role_id,
  actor_id,
  runtime_option_id,
  option_id,
  environment_id,
  operation_id,
  resource,
)
```

The first five fields reproduce one complete Assignment value. The next two
identify one external-inference Agent execution candidate. The final three
subject fields identify the exact environment-scoped abstract action.

Every subject part is exact and case-sensitive. Core does not trim, case-fold,
alias, resolve, normalize, or rewrite it. `authority_kind`, `authority_id`,
`provenance_reference`, and `state` describe evidence about the subject; they
are not subject identity.

There is no `authorization_id`, grant identity, Execution Run identity,
`execution_id`, or `run_id`.

### External-inference Agent boundary

Evidence must reference one exact valid Assignment whose selected Actor has
`kind: agent`. A matched Human Assignment is outside this contract. The
mandatory `option_id` binds one supplied external Inference Option. Runtime-owned
inference is not modeled.

The Runtime and Inference Option references do not prove applicability,
compatibility, availability, credentials, quota, or execution readiness.

### Operation and resource

`operation_id` uses the Core operation syntax and vocabulary shared by
Operation Requirement, Runtime Operation Capability Observation, and
Environment Operation Permission Observation. The current supported vocabulary
contains exactly:

```text
repository_file_read
```

The syntax is exact ASCII lower-snake-case:

```regex
^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$
```

`resource` uses the exact extension-neutral lexical repository-resource grammar
defined by Operation Requirement. Validation never resolves or accesses the
resource.

---

## 3. Authority, Provenance, and State

### Authority kind

`authority_kind` has exactly these values, in this order:

- `human`
- `policy`

These values classify a caller assertion. `human` does not prove that a Human
was authenticated, and `policy` does not identify or execute a policy engine.

### Authority identity and provenance

`authority_id` and `provenance_reference` are exact, opaque, nonempty,
case-sensitive strings. Their namespace, truth, currency, and integrity belong
to the caller or authority producer.

Core does not:

- authenticate the authority;
- determine entitlement or delegation;
- look up an authority or approval record;
- dereference or verify provenance;
- verify a signature; or
- parse Task, review, chat, commit, or approval prose.

Consequently:

```text
caller-attested evidence != authenticated authority
```

### State

`state` has exactly these values, in this order:

- `granted`
- `denied`

`granted` states only that the caller supplied positive evidence for the exact
subject. It is not a usable grant, execution permission, or sufficient
condition for future execution.

`denied` states only that the caller supplied an explicit negative
authorization assertion for the exact subject. It is not missing evidence,
environment permission denial, or a formal revocation record.

There is no serialized `unknown` state. Missing evidence is represented by the
absence of an exact subject match and means authorization is unproven. Missing
is not denied.

---

## 4. Input Capture and Foundational Validation

`validate_agent_execution_authorization_evidence` captures each caller iterable
exactly once, in this order:

1. Assignments;
2. Actors;
3. Agent Runtime Options;
4. Inference Options; and
5. authorization evidence.

Caller values remain unmodified.

Validation then applies these foundational checks in order:

1. canonical Assignment-set validation;
2. canonical Agent Runtime Option inventory validation;
3. canonical Inference Option inventory validation;
4. snapshot `environment_id` validation; and
5. exact evidence type and field validation.

An invalid parent result is converted to authorization findings without
changing its codes or messages and stops later validation. Assignment-set
`valid` is required. Assignment completeness and separation findings are not
authorization facts; one exact valid supplied Assignment may be authorized
without claiming complete Workflow assignment coverage.

### Snapshot environment

The snapshot `environment_id` must be an exact nonempty string. Otherwise the
result contains exactly:

```text
agent_execution_authorization_environment_id_invalid
```

with the fixed message:

```text
Agent Execution Authorization Evidence snapshot environment_id must be an exact nonempty string.
```

### Exact evidence values

The runtime API accepts only exact `AgentExecutionAuthorizationEvidence`
values. Any other supplied item produces, at most once:

```text
agent_execution_authorization_evidence_invalid_type
```

with the fixed message:

```text
Each supplied Agent Execution Authorization Evidence item must be an exact AgentExecutionAuthorizationEvidence value.
```

For exact evidence objects, the first eight identity/reference fields must be
exact nonempty strings. `operation_id` and `resource` must be exact strings and
continue to their canonical semantic validators. `authority_kind` and `state`
must be exact enum values. `authority_id` and `provenance_reference` must be
exact nonempty strings. Any malformed field produces, at most once:

```text
agent_execution_authorization_evidence_invalid
```

with the fixed message:

```text
A supplied Agent Execution Authorization Evidence value contains malformed subject, authority, provenance, or state fields.
```

The invalid-type finding precedes the malformed-value finding when both apply.
Either category stops relation validation and normalization.

---

## 5. Repeated Subjects and Conflict Classification

At most one evidence value may be supplied for each exact ten-part subject.
Every repeated subject is classified once using this decision precedence:

1. more than one distinct `state` is a state conflict only;
2. otherwise, more than one distinct
   `(authority_kind, authority_id, provenance_reference)` tuple is unsupported
   multi-authority evidence only; and
3. otherwise, repeated identical complete values are an exact duplicate only.

Thus a mixed-state subject remains a state conflict even if it also contains
different authorities or an identical repetition. The decision precedence is:

```text
state conflict > unsupported multi-authority > exact duplicate
```

### Exact duplicate

```text
duplicate_agent_execution_authorization_evidence
```

Message shape:

```text
Agent Execution Authorization Evidence subject (task_id={task_id!r}, workflow_id={workflow_id!r}, stage_id={stage_id!r}, role_id={role_id!r}, actor_id={actor_id!r}, runtime_option_id={runtime_option_id!r}, option_id={option_id!r}, environment_id={environment_id!r}, operation_id={operation_id!r}, resource={resource!r}) has more than one identical supplied evidence value.
```

### State conflict

```text
conflicting_agent_execution_authorization_evidence
```

Message shape:

```text
Agent Execution Authorization Evidence subject (task_id={task_id!r}, workflow_id={workflow_id!r}, stage_id={stage_id!r}, role_id={role_id!r}, actor_id={actor_id!r}, runtime_option_id={runtime_option_id!r}, option_id={option_id!r}, environment_id={environment_id!r}, operation_id={operation_id!r}, resource={resource!r}) has conflicting supplied states.
```

### Unsupported multi-authority evidence

```text
unsupported_multi_authority_agent_execution_authorization_evidence
```

Message shape:

```text
Agent Execution Authorization Evidence subject (task_id={task_id!r}, workflow_id={workflow_id!r}, stage_id={stage_id!r}, role_id={role_id!r}, actor_id={actor_id!r}, runtime_option_id={runtime_option_id!r}, option_id={option_id!r}, environment_id={environment_id!r}, operation_id={operation_id!r}, resource={resource!r}) has same-state evidence with differing authority or provenance; multi-authority composition is not supported.
```

The `!r` substitutions render escaped exact Python representations. Output
categories are reported in the fixed order duplicate, state conflict, then
unsupported multi-authority, with exact subject sorting within each category.
This output order does not change the per-subject classification precedence.

Conflict resolution is absent from Core. There is no first-, last-, latest-,
grant-, deny-, stricter-, majority-, Human-, or policy-wins rule. Core does not
deduplicate or claim consensus. The caller or authority producer must reconcile
evidence externally and resupply one coherent value.

---

## 6. Relationship and Lexical Findings

After repeated subjects, validation reports the following categories in this
fixed order.

### Exact Assignment reference

The first five fields must match one complete supplied valid Assignment value.
Each distinct unmatched five-part value produces:

```text
agent_execution_authorization_assignment_not_found
```

with the fixed message shape:

```text
Assignment (task_id={task_id!r}, workflow_id={workflow_id!r}, stage_id={stage_id!r}, role_id={role_id!r}, actor_id={actor_id!r}) was not found in the supplied valid Assignment context.
```

Unmatched values are sorted as exact five-part tuples. An Assignment does not
itself create evidence for any operation.

### Human Assignment boundary

Evidence that matches a Human Assignment produces:

```text
agent_execution_authorization_not_applicable_to_human_actor
```

with the fixed message shape:

```text
Agent Execution Authorization Evidence does not apply to Human Actor {actor_id!r} for Assignment (task_id={task_id!r}, workflow_id={workflow_id!r}, stage_id={stage_id!r}, role_id={role_id!r}, actor_id={actor_id!r}).
```

Only evidence referencing a Human Assignment receives this finding. Unrelated
valid Human Assignments may remain in the supplied context.

### Runtime and Inference Option references

Each distinct unknown `runtime_option_id` produces the established:

```text
agent_runtime_option_not_found
```

Each distinct unknown `option_id` produces the established:

```text
inference_option_not_found
```

Distinct identifiers are sorted exactly within each category. The validator
does not infer applicability or compatibility.

### Environment scope

Each distinct evidence `environment_id` differing from the snapshot scope
produces:

```text
agent_execution_authorization_environment_mismatch
```

with the fixed message shape:

```text
Agent Execution Authorization Evidence environment_id {observed_environment_id!r} does not match snapshot environment_id {snapshot_environment_id!r}.
```

### Operation syntax and support

Each distinct malformed operation produces:

```text
operation_id_invalid_syntax
```

with the fixed message:

```text
Agent Execution Authorization Evidence operation_id must use ASCII lower_snake_case syntax.
```

Each distinct well-formed unsupported operation produces the established:

```text
operation_id_not_supported
```

Malformed operations precede unsupported operations. Values are exactly sorted
within each category.

### Resource grammar

Resource validation reuses the canonical lexical repository-resource helper
and its first-issue precedence:

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

The message shape is:

```text
Agent Execution Authorization Evidence resource {resource!r} {message_suffix}
```

Findings sort first by canonical resource-issue precedence and then by exact
resource. Validation is lexical only and performs no path resolution or access.

---

## 7. Determinism, Atomicity, and Canonical Output

After foundational validation, finding categories are ordered exactly as:

1. exact duplicate subjects;
2. state-conflict subjects;
3. unsupported multi-authority subjects;
4. unknown exact Assignment references;
5. matched Human Assignments;
6. unknown Runtime Option references;
7. unknown Inference Option references;
8. environment mismatches;
9. malformed operation identifiers;
10. well-formed unsupported operation identifiers; and
11. invalid resources in canonical resource-issue order.

Declaration order creates no preference, authority, recency, or policy
strength. Values within each category follow the exact sorting rules above.

Any finding invalidates the complete snapshot:

```text
valid: false
findings: nonempty tuple
normalized_evidence: ()
```

No invalid result contains partial normalized evidence. No value is corrected,
deduplicated, rewritten, reconciled, or mutated.

A valid result contains only the exact supplied evidence objects, ordered by
the exact ten-part subject:

```text
valid: true
findings: ()
normalized_evidence: canonically ordered supplied tuple
```

No missing value and no Assignment x Runtime x Inference x environment x
operation x resource Cartesian product is synthesized. An empty evidence
iterable produces a valid empty normalized tuple after foundational context
validation.

The API intentionally provides no lookup helper. Agent Action Prerequisite
Assessment privately compares one exact subject with the normalized supplied
values. Failure to find that subject means missing or unproven authorization,
not denial. Its separate derived contract is defined in
`core/agent-action-prerequisite-specification.md`.

---

## 8. Structural and Semantic Authority

The machine-readable structural schema is:

`schemas/agent-execution-authorization-evidence.schema.json`

It is a Draft 2020-12 closed-object schema with exactly fourteen required
properties, nonempty string fields, `authority_kind` enum `human | policy`,
`state` enum `granted | denied`, and no additional properties.

The schema owns structure only. It does not validate Assignment, Actor kind,
Runtime or Inference inventory references, environment scope, operation syntax
or support, lexical resource grammar, repeated subjects, finding order,
atomicity, or absence semantics. This specification is the semantic authority,
and the pure runtime validator owns those semantic rules.

---

## 9. Ownership, Currency, and Lifecycle Boundary

Ownership remains:

```text
Framework/Core
-> closed vocabularies, structural and semantic validation, deterministic
   findings, canonical ordering, and atomic result behavior

Caller or authority producer
-> decision truth, authority identity, authentication, entitlement,
   provenance integrity, evidence currency, and conflict reconciliation
```

The value contains no timestamp, issued-at, expiry, freshness, duration,
authorization ID, Execution Run identity, consumption state, reuse policy, or
revocation record. Validation performs no clock access.

Core cannot detect stale evidence. The caller must not supply a stale grant as
current. A later snapshot may omit old evidence or contain one coherent
`denied` value, but that denial is not a formal revocation record.

Repeated validation performs no consumption and provides no replay protection.
Before any future contract claims single-use authorization, consumption,
replay safety, or per-run revocation, a separately authorized design must bind
authenticated authority to an Execution Run identity and define durable state.

---

## 10. No-I/O and No-Execution Boundary

Validation is pure, supplied-data-only, and lexical. It never:

- opens, reads, writes, stats, hashes, lists, resolves, or existence-checks a
  resource or protected target;
- discovers or probes Actors, Runtime Options, Inference Options, tools,
  credentials, environments, sandboxes, ACLs, capabilities, or permissions;
- consults a filesystem, repository root, current working directory, network,
  subprocess, clock, cache, database, policy service, authority service, or
  persistent store;
- parses Task, review, chat, commit, architecture-approval, or other prose;
- authenticates an authority, checks entitlement, verifies a signature, or
  dereferences provenance;
- issues authority, mutates permission or authorization state, or enforces a
  decision; or
- creates an Execution Contract or Execution Run, binds a concrete tool,
  dispatches, executes, or invokes anything.

---

## 11. Adjacent Contract Boundaries

### Assignment and candidate prerequisites

Assignment records responsibility. It grants no authority for arbitrary action.
Agent Execution Candidate Prerequisite Assessment states whether one designated
external-inference Agent candidate satisfies the prerequisites currently
modeled by AIO-034. Its `satisfied` outcome does not mean authorized. AIO-039
changes neither contract and adds no authorization field to either.

### Requirement, capability, and permission

Operation Requirement states demand. Runtime Operation Capability Observation
states technical support in principle. Environment Operation Permission
Observation states an environment-scoped permission fact. None creates
authorization evidence, and authorization evidence changes none of them.

These are coherent independent facts:

```text
permission allowed + authorization missing
permission denied + authorization granted
permission allowed + authorization denied
capability present + authorization missing
```

Agent Action Prerequisite Assessment provides a non-executing diagnostic
composition over coherent parent results. It treats explicit denial as
blocking and missing evidence as unresolved, while `satisfied` remains
non-authoritative. AIO-039 itself performs no such composition, and neither
contract creates an execution boundary.

### Permission Decision and Human Control

Permission Decision retains its separate values:

```text
allow
ask
always-ask
deny
```

They are not mapped to `granted` or `denied` inside AIO-039. A future authority
producer may create authorization evidence under separately specified rules.

A Human Control checkpoint and Task Human approval remain governance evidence:

```text
Human Control checkpoint != authorization granted
Task Human approval != execution authorization
```

Human Control may later produce action-specific authorization evidence through
a separately authorized and authenticated boundary. AIO-039 never infers it.

### Earlier private experiment

The AIO-035 private read-only execution-preparation harness retains its own
provisional authorization assertion and freshness modeling. AIO-039 neither
retrofits that harness nor converts its private values into this canonical
contract.

---

## 12. Runtime and Package API

Immutable values and pure deterministic validation are defined in:

`engineering_orchestration.agent_execution_authorization_evidence`

The submodule exposes:

- `AgentExecutionAuthorizationAuthorityKind`
- `AgentExecutionAuthorizationState`
- `AgentExecutionAuthorizationEvidence`
- `AgentExecutionAuthorizationFinding`
- `AgentExecutionAuthorizationValidationResult`
- `validate_agent_execution_authorization_evidence(...)`

The exact public shapes are:

```python
class AgentExecutionAuthorizationAuthorityKind(StrEnum):
    HUMAN = "human"
    POLICY = "policy"


class AgentExecutionAuthorizationState(StrEnum):
    GRANTED = "granted"
    DENIED = "denied"


AgentExecutionAuthorizationEvidence(
    task_id: str,
    workflow_id: str,
    stage_id: str,
    role_id: str,
    actor_id: str,
    runtime_option_id: str,
    option_id: str,
    environment_id: str,
    operation_id: str,
    resource: str,
    authority_kind: AgentExecutionAuthorizationAuthorityKind,
    authority_id: str,
    provenance_reference: str,
    state: AgentExecutionAuthorizationState,
)

AgentExecutionAuthorizationFinding(
    code: str,
    message: str,
)

AgentExecutionAuthorizationValidationResult(
    valid: bool,
    findings: tuple[AgentExecutionAuthorizationFinding, ...],
    normalized_evidence: tuple[AgentExecutionAuthorizationEvidence, ...],
)

validate_agent_execution_authorization_evidence(
    evidence: Iterable[AgentExecutionAuthorizationEvidence],
    assignments: Iterable[Assignment],
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    actors: Iterable[Mapping[str, object]],
    runtime_options: Iterable[AgentRuntimeOptionDefinition],
    inference_options: Iterable[InferenceOptionDefinition],
    environment_id: str,
) -> AgentExecutionAuthorizationValidationResult
```

Values and result containers are frozen and tuple-backed. The package root does
not re-export these names. The runtime module and structural schema are packaged
without a new external dependency.

---

## 13. Exclusions

The first contract contains no:

- authenticated authority, authority issuance, authority registry, entitlement
  lookup, delegation, signature verification, or provenance dereferencing;
- `authorization_id`, Execution Run or execution identity, timestamp,
  issued-at, expiry, clock, freshness, duration, or temporal precedence;
- persistent grant, registry, consumption, single-use or reusable-grant claim,
  replay protection, revocation event, or revocation lifecycle;
- multi-authority composition, consensus, conflict winner, automatic Human
  escalation, or reconciliation policy;
- synthetic missing evidence, serialized unknown, Cartesian evidence, or
  inferred authorization from Assignment, Task approval, candidate
  prerequisites, capability, permission, or Permission Decision;
- filesystem, repository, protected-target, ACL, sandbox, Runtime, inference,
  resource, permission, policy, or authority discovery;
- permission or authorization mutation, enforcement, concrete tool binding,
  adapter, Provider integration, CLI, or Project Manifest field; or
- Execution Contract, Execution Run, request, session, dispatch, execution, or
  invocation.

Every future authentication, authorization-production, run-binding,
consumption, revocation, composition, enforcement, or execution contract
requires separate explicit authorization and must preserve this evidence-only
meaning.

AIO-043 supplies one separately authorized contract without changing this
evidence value: Agent Execution Authorization Grant is a positive, time-bounded,
issuer/domain-scoped artifact bound to one exact nested Agent Execution Run and
intended for at most one future atomic consumption. Its `issuer_kind` and
`issuer_id` do not alias this contract's caller-attested `authority_kind` and
`authority_id`, and this contract's `granted` state does not create a Grant.
See `core/agent-execution-authorization-grant-specification.md`.
