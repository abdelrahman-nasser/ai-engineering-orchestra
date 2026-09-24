# AI Engineering Orchestra — Terminology

Version: 0.1.0

This document defines the canonical terminology used by AI Engineering Orchestra.

All Orchestra documentation, configurations, workflows, adapters, and agents must use these terms consistently.

---

## Orchestra

The complete AI Engineering Orchestra framework.

The Orchestra defines how AI-assisted software engineering work is structured, delegated, validated, reviewed, and controlled.

It is independent of any specific AI provider, model, programming language, framework, or repository type.

---

## Provider

A system or platform forming an operational access boundary for inference or
external service access. For an Inference Option, the Provider is the boundary
through which its model is addressed. The Provider need not be the organization
that developed the model.

A Provider is not a Role or Actor and does not fulfil a Role. A Provider may
expose many models or supply many Agent Actors. A Human Actor has no Provider
requirement.

For example:

Claude != Architect

A Provider may supply an Agent Actor capable of fulfilling the Architect Role.

---

## Model

A Provider-addressable inference capability. A model identifier is meaningful
only within its Provider namespace; AIO v0.1 defines no global model namespace,
Model contract, catalog, family, version, tier, or capability registry.

Models may differ in:

- reasoning capability
- speed
- cost
- quota
- context size
- tool support
- agent capabilities

Projects should avoid directly depending on specific model names where possible.

---

## Inference Option

A Provider-neutral identity describing one caller/environment-accessible way to
address a model for inference.

The canonical Definition contains exactly opaque, case-sensitive `option_id`,
`provider_id`, and Provider-scoped `model_id`. `option_id` is unique only within
one supplied inventory. It remains the identity even when multiple options use
the same Provider/model pair.

An Inference Option does not describe an Agent Runtime Option, Agent Service,
tool or session ownership, credentials, endpoint, capabilities, availability,
selection, authorization, or invocation. The canonical contract is defined in:

`core/inference-option-specification.md`

---

## Inference Option Availability Observation

An immutable, Provider-neutral, ephemeral value describing the currently known
availability state of one Inference Option within one caller-supplied evaluation
snapshot.

The state is exactly `available`, `unavailable`, or `unknown`; unknown is not
unavailable. A missing observation normalizes to unknown. Availability does not
change option identity and does not establish capability fit, selection,
authorization, execution, quota, price, Execution Mode satisfaction, or Agent
Runtime Option availability. The canonical contract is defined in:

`core/inference-option-availability-specification.md`

---

## Agent Runtime Option

An opaque, caller/environment-supplied configured execution surface through
which an Agent execution can be run or delegated. It identifies the
execution/Agent-loop boundary for one evaluation context.

The canonical Definition contains exactly opaque, case-sensitive
`runtime_option_id`, unique within one supplied sequence. It contains no Actor,
Provider, model, implementation, framework, managed, capability, tool, state,
session, endpoint, credential, authorization, or invocation field.

A concrete implementation may own or delegate some combination of execution
lifecycle, environment, tools, state, sessions, scheduling, and inference
access. The definition does not claim that every Agent Runtime Option owns all
of them.

Agent Runtime Option is not Actor, executable Agent definition, execution
instance, Inference Option, Agent Service, authorization, or credentials. Human
Actors require no Agent Runtime Option. The Definition itself contains no Actor
mapping or Runtime-to-Inference compatibility relation. Separate relations may
reference its opaque identity. The canonical contract is defined in:

`core/agent-runtime-option-specification.md`

After the canonical term is established, **Runtime Option** is acceptable short
prose. It does not mean a Python runtime or .NET runtime.

---

## Agent Runtime Option Availability Observation

An immutable, ephemeral observation describing the currently known availability
state of one Agent Runtime Option within one caller-supplied evaluation
snapshot.

The state is exactly `available`, `unavailable`, or `unknown`; unknown is not
unavailable. A missing observation normalizes to unknown. Runtime availability
does not establish Actor applicability, Inference Option availability,
Runtime-to-Inference compatibility, selection, authorization, capacity,
Execution Mode satisfaction, or execution. The canonical contract is defined
in:

`core/agent-runtime-option-availability-specification.md`

---

## Runtime Operation Capability Observation

An immutable, caller/environment-supplied observation describing the currently
known technical-support state of one known Agent Runtime Option for one
Core-defined abstract operation within one caller-owned evaluation snapshot.

The value contains exactly `runtime_option_id`, `operation_id`, and `state`.
Its identity is the exact case-sensitive pair
`(runtime_option_id, operation_id)`; state is not identity. The state is exactly
`present`, `absent`, or `unknown`. Present is positive supplied technical-support
evidence, absent is positive supplied non-support evidence, and unknown means no
reliable determination. Absent is not unknown.

A missing observation for a known Runtime/Core-operation pair normalizes to
unknown. Explicit and synthesized unknown observations are semantically
indistinguishable in normalized output. Duplicate pairs, unknown Runtime
references, malformed operation IDs, and well-formed unsupported operation IDs
invalidate the complete snapshot without partial normalization.

Capability reports technical support for an operation class in principle. It
does not include a resource, tool identity, environment, freshness, permission,
authorization, availability, discovery, or execution semantics. It neither
changes Runtime Option identity nor creates an Operation Requirement. The
qualified term does not mean Role `required_capabilities`, Actor competency, or
Provider/model capability. The canonical contract is defined in:

`core/runtime-operation-capability-specification.md`

---

## Environment Operation Permission Observation

An immutable, caller/environment-supplied observation describing the currently
known effective environment-permission state for one known Agent Runtime Option
to perform one Core-defined abstract operation against one exact lexical
repository-relative resource in one opaque caller-identified environment,
within one caller-owned evaluation snapshot.

The value contains exactly `runtime_option_id`, `environment_id`,
`operation_id`, `resource`, and `state`, in that order. Its identity is the exact
case-sensitive four-part tuple
`(runtime_option_id, environment_id, operation_id, resource)`; state is not
identity. The state is exactly `allowed`, `denied`, or `unknown`. Denied is
positive supplied negative evidence and is not unknown.

The environment identifier is opaque caller-owned snapshot scope, not an
Environment entity or registry. A missing exact observation semantically means
unknown, never denied, but validation preserves and canonically orders only
supplied observations because the resource domain is open-ended. It synthesizes
no Cartesian permission snapshot. The value has no freshness field; the caller
owns snapshot currency, and Core cannot independently verify it.

Identical repeated identities and differing-state conflicts are mutually
exclusive invalid-input categories. Conflicting permission observations
invalidate the complete snapshot; no first-, last-, latest-, allowed-, deny-,
or stricter-wins resolution applies, and a conflict is not converted to denied,
unknown, a Permission Decision, or a Human approval question. Reconciliation is
owned by the caller/environment evidence producer.

Environment Operation Permission Observation is evidence only. `allowed` does
not establish a Permission Decision, Human or policy authorization, Runtime
availability, capability, enforcement, dispatchability, or execution. The
canonical contract is defined in:

`core/environment-operation-permission-specification.md`

---

## Agent Execution Authorization Evidence

An immutable, caller-supplied, evaluation-scoped evidence value asserting that
one identified Human or policy authority granted or denied one exact assigned
external-inference Agent action.

Its exact subject is the ten-part tuple of `task_id`, `workflow_id`, `stage_id`,
`role_id`, `actor_id`, `runtime_option_id`, `option_id`, `environment_id`,
`operation_id`, and lexical `resource`. The first five fields reproduce one
complete valid Assignment. `authority_kind`, `authority_id`,
`provenance_reference`, and `state` describe the supplied assertion and are not
subject identity. Authority kind is exactly `human` or `policy`; state is
exactly `granted` or `denied`.

The value is evidence only. The authority identity and provenance are opaque
and caller-attested; Core does not authenticate the authority, verify
entitlement, dereference provenance, or issue a grant. Missing exact-subject
evidence means authorization is unproven, not denied. Assignment, Task approval,
candidate-prerequisite satisfaction, capability, environment permission, and a
Permission Decision do not manufacture this evidence.

The contract has no authorization lifecycle, freshness, expiry, persistence,
consumption, replay protection, revocation, enforcement, dispatch, or execution
semantics. The canonical contract is defined in:

`core/agent-execution-authorization-evidence-specification.md`

---

## Agent Action Prerequisite Assessment

A pure, derived, immutable, deterministic, ephemeral, in-memory diagnostic
assessment of one exact assigned external-inference Agent action.

Its subject is the existing ten-part Agent Execution Authorization Evidence
subject: the complete Assignment identity, exact Runtime and external Inference
Option identifiers, exact opaque environment identifier, Core operation, and
lexical repository-relative resource. It introduces no assessment, action,
candidate, execution, or run identifier.

The assessment consumes one coherent Agent Execution Candidate Prerequisite
result, validates one Operation Requirement, and consumes coherent Runtime
Operation Capability, Environment Operation Permission, and Agent Execution
Authorization results. Exact positive evidence in every category produces
`satisfied`; any explicit candidate, capability, permission, or authorization
negative produces `blocked`; otherwise valid unknown or missing evidence
produces `unresolved`. Blockers dominate uncertainties, but all applicable
reasons remain visible in canonical order. Invalid input has findings and no
ordinary outcome.

`satisfied` means only that all currently modeled caller-supplied prerequisites
are positive. It is not execution readiness, authenticated authority, Core
authorization, an Execution Contract, tool binding, dispatchability,
invocation permission, or execution success. The assessment performs no I/O,
policy composition, enforcement, authorization consumption, dispatch, or
invocation. The canonical contract is defined in:

`core/agent-action-prerequisite-specification.md`

---

## Agent Execution Contract

An immutable, provider-neutral, tool-neutral, serializable declarative intent
value for one exact assigned external-inference Agent action and its explicitly
supplied, already-resolved effective Task-wide Execution Mode.

The value contains the exact ten-part Agent Action Prerequisite Assessment
subject, in canonical order, followed only by `execution_mode`. Mode is required
contract context outside the action subject and grants no authority. Equality
over all eleven fields is value equality, not contract-instance, attempt, Run,
correlation, or lifecycle identity.

Canonical preparation accepts only one observably coherent valid `satisfied`
AIO-040 result with the canonical singleton positive reason plus one explicit
mode from `lite`, `standard`, `deep`, or `critical`. Blocked, unresolved,
invalid, wrong-type, and incoherent prerequisite results produce no contract.
Preparation does not rerun prerequisite assessment, consume authorization, or
authenticate assessor provenance or caller truth. Public construction and
intrinsic validation likewise prove only value semantics, not that canonical
preparation occurred.

The contract is not authorization, permission, durable readiness, an Execution
Run, a tool or adapter binding, dispatch permission, or invocation permission.
It stores no prerequisite result, authority, provenance, freshness, payload,
status, timestamp, result, or telemetry and performs no resource I/O or
execution. Any future Run or dispatch work must freshly resolve the effective
Task mode, obtain a fresh exact prerequisite assessment, freshly prepare and
compare the value where appropriate, and separately obtain authenticated
run-bound authority. The canonical contract is defined in:

`core/agent-execution-contract-specification.md`

---

## Agent Execution Run

An immutable, provider-neutral, tool-neutral, serializable occurrence-identity
value for one concrete attempt involving one exact Agent Execution Contract.
It contains exactly a caller-supplied opaque `run_id` followed by the exact
nested immutable Contract.

Representation equality covers `(run_id, contract)` while logical occurrence
identity is `run_id`. Equal IDs and Contracts represent the same Run again;
equal IDs with different Contracts conflict in an authoritative namespace but
cannot be discovered by single-value validation; equal Contracts with different
IDs are distinct Runs. One Run equals one semantic attempt, so a semantic retry
uses a new Run ID and fresh preparation. No separate attempt identity exists.

Canonical preparation requires caller-supplied current prerequisite evidence,
an observably coherent valid `satisfied` AIO-040 result, a freshly resolved
effective Task-wide Execution Mode, fresh AIO-041 preparation, and exact
fresh/intended Contract equality. Core cannot authenticate temporal freshness,
provenance, Run-ID uniqueness, or caller truth.

The Run is not lifecycle state, authorization, authorization consumption,
replay protection, current permission, tool binding, dispatch, invocation, or
success. It has no status, timestamp, persistence, result, event, or telemetry
and performs no execution or resource I/O. The canonical contract is defined
in:

`core/agent-execution-run-specification.md`

---

## Agent Execution Authorization Grant

An immutable, serializable, positive authority artifact issued through an
external authenticated and integrity-protected authority-producer boundary,
bound to one exact nested Agent Execution Run and one exact authorization
domain, time-bounded, and intended for at most one future atomic consumption
toward dispatch admission.

The value contains exactly `grant_id`, `run`, `authorization_domain_id`,
`issuer_kind`, `issuer_id`, `provenance_reference`, `issued_at`, and
`expires_at`. Effective Grant identity is the exact tuple
`(authorization_domain_id, issuer_kind, issuer_id, grant_id)`. The issuer owns
Grant-ID allocation and namespace non-reuse; Core neither generates IDs nor
proves global uniqueness.

The complete nested Run, not `run_id` alone, is the authorized subject.
`authorization_domain_id` identifies the future acceptance and shared-ledger
domain and is not `environment_id`. `issuer_kind` is exactly `human` or
`policy`; `issuer_id` is distinct from AIO-039's caller-attested
`authority_id`; and provenance is audit-only.

The Grant is positive-only and has no state or reusable-use counter. Its fixed
single-use intent does not implement consumption. Pure validation checks exact
value semantics, canonical UTC timestamp syntax, `issued_at < expires_at`,
domain scope, collisions, and one-Grant-per-Run/domain cardinality using only
supplied data. It never reads a clock and cannot prove currentness.

Direct construction, structural or intrinsic validity, and serialization do
not authenticate an issuer or integrity-protect a payload. The Grant itself is
not AIO-039 evidence, Permission, a Permission Decision, consumption, replay
protection, revocation, persistence, dispatch admission, invocation, or
success. The canonical contract is defined in:

`core/agent-execution-authorization-grant-specification.md`

---

## Agent Operation Tool Binding

An immutable, serializable, provider-neutral selected-binding value that binds
one exact complete Agent Execution Run to one exact immutable configured Tool
implementation identity supplied by an external trusted resolver.

The value contains exactly `run` followed by `tool_id`. The complete nested Run,
not `run_id` alone, preserves the exact Contract binding. `tool_id` is an exact,
opaque, case-sensitive, nonempty identity in the namespace of the configured
runtime/tool resolver for the Run's exact Runtime Option and environment. Core
does not allocate Tool IDs or claim global uniqueness. The identifier must name
one immutable/version-stable configured implementation revision; a mutable
alias or display name is not a canonical Tool ID unless the resolver guarantees
that it can never be rebound.

The resolver owns configured Tool existence, namespace, immutable identity,
Runtime/environment applicability, and selection. A future adapter owns native
resolution, credentials, endpoints, protocol translation, parameters,
containment, and invocation. Core performs no Tool discovery or probing.
Runtime Operation Capability `present` reports only abstract support and does
not establish a concrete Tool Binding.

The binding cannot widen or replace any Run or Contract field. Direct
construction, intrinsic or schema validity, and serialization do not prove that
the Tool exists, is trusted, available, executable, or implements the intended
operation. The binding grants no permission or authority, consumes no Grant,
creates no dispatch admission, and performs no dispatch or invocation. The
canonical contract is defined in:

`core/agent-operation-tool-binding-specification.md`

---

## Agent Execution Dispatch Admission

An immutable, serializable, positive authorization-consumption record and
historical security fact for one exact complete Agent Execution Authorization
Grant and one exact trusted non-widening Agent Operation Tool Binding at one
authoritative decision time.

The value contains exactly `grant`, `tool_binding`, and `decision_time` in that
order. It has no Admission ID or lifecycle state. Its natural identity is the
Grant composite `(authorization_domain_id, issuer_kind, issuer_id, grant_id)`;
`(authorization_domain_id, run_id)` is a separate durable uniqueness
constraint. A new Admission requires exact complete
`grant.run == tool_binding.run == freshly reconstructed expected_run`
equality, reusing the existing Run ID.

Direct construction, deserialization, schema validity, and intrinsic validity
are descriptive only. Operational authority derives exclusively from creation
or retrieval through the configured authoritative authorization-domain store.
The store owns authoritative time, currentness, revocation ordering,
uniqueness, atomic Grant consumption plus Admission insertion, and exact
historical retry. The trusted coordinator owns Grant authentication, Tool
resolution, fresh AIO-040 composition, effective-mode resolution, and exact
Contract/Run reconstruction.

The official AIO-047 local realization is a dedicated, pinned, same-host
SQLite ledger on supported local storage. Its bounded duplicate-suppression
claim assumes one correctly owned active ledger and all declared Grant, Tool,
clock, filesystem, configuration, and domain-ownership trust preconditions.
It is not multi-machine consensus, malicious-local-administrator tamper
resistance, invocation replay protection, dispatch, invocation, or success.
The canonical value and store contracts are defined in:

`core/agent-execution-dispatch-admission-specification.md`

`core/agent-execution-dispatch-admission-store-specification.md`

---

## Authorization Domain Ownership Authority

A provider-neutral operational boundary that exclusively acquires, validates,
holds, and releases live ownership of one exact authorization domain and its
exact authoritative ledger identity. Ownership is a prerequisite for supported
local AIO-047 Store use; it is not Grant authentication, issuer entitlement,
Tool trust, Admission, dispatch, or invocation.

The AIO-049 v1 realization is deliberately limited to one conforming
coordinator under one current Windows user SID on one host, using a fixed
Local AppData registry, a domain-keyed OS lock, and a local fixed NTFS ledger.
The provider-neutral contract is defined in:

`core/authorization-domain-ownership-specification.md`

---

## Local Authorization Domain Binding

The immutable, private, adapter-owned durable record that binds one exact
authorization domain and current user identity to one canonical ledger path,
stable file identity, ledger instance, and positive generation. Append-only
activation and terminal-fencing evidence extends the binding without rebinding
it. A binding, marker, checksum, path, PID, or generation is descriptive
evidence and never a live bearer capability.

The Windows v1 binding format is private to its adapter and is not a public
Core schema.

---

## Owned Authorization Domain Session

The live, process-local, nonserializable and noncopyable capability returned by
a conforming Authorization Domain Ownership Authority. It retains the required
OS ownership and ledger-pin handles and holds one lifecycle lease across each
complete coordinator operation, including trust checks, fresh prerequisite
reconstruction, guarded history, and the final Store operation.

Closing, ownership loss, or the start of terminal fencing makes the session
irreversibly unusable. Reacquisition creates a distinct session; an old object
cannot be reanimated even when the same immutable domain generation is
reacquired after an ordinary process exit.

---

## Actor-to-Runtime Applicability Evidence

An immutable, caller-supplied positive evidence value stating that one known
Agent Actor may use one known Agent Runtime Option within the supplied
evaluation context.

The value contains exactly opaque, exact, case-sensitive `actor_id` and
`runtime_option_id`. Their pair is the identity in a caller-supplied
many-to-many relation. Duplicate pairs, unknown endpoint references, and known
Human Actor endpoints invalidate the complete relation; valid evidence is
canonically ordered by the exact pair.

An empty relation is valid. A missing edge means only that no positive
applicability evidence was supplied; it does not prove incompatibility,
unavailability, lack of authorization, or inability to execute. Applicability
does not alter the Human Actor path and grants no authority or preference.

Actor-to-Runtime Applicability Evidence is not Actor or Runtime availability,
Actor Selection, Assignment, Task/Role fit, Execution Mode fit, tool or
permission evidence, configuration viability, selection, ranking,
authorization, or invocation. The canonical contract is defined in:

`core/actor-runtime-applicability-specification.md`

---

## Runtime-to-Inference Compatibility Evidence

An immutable, caller-supplied positive evidence value reporting that one Agent
Runtime Option supports invoking one externally selectable Inference Option
within the supplied evaluation context.

The value contains exactly opaque, exact, case-sensitive `runtime_option_id`
and `option_id`. Their pair is the edge identity in a caller-supplied
many-to-many relation. Duplicate pairs or unknown endpoint references invalidate
the complete relation; valid evidence is canonically ordered by the pair.

An empty relation is valid. A missing edge means only that no positive external
compatibility evidence was supplied; it does not prove incompatibility,
unavailability, or inability to execute. Runtime-owned inference remains
possible without an external edge.

Compatibility Evidence is not live integration verification, availability,
configuration viability, selection, authorization, or invocation. The
canonical contract is defined in:

`core/runtime-inference-compatibility-specification.md`

---

## Runtime-to-Inference Pair Availability Assessment

An immutable, pure, deterministic assessment of one explicitly supplied
positive external Runtime-to-Inference compatibility edge against the
normalized availability states of its exact endpoints within one caller-owned
evaluation context.

The closed outcomes are `established`, `blocked`, and `unresolved`.
`established` means only that the positive edge validated and both endpoints
normalized to available. Any unavailable endpoint makes the pair `blocked`;
otherwise, at least one unknown endpoint makes it `unresolved`.

Only supplied positive edges are assessed. No Cartesian product or synthetic
edge is created, and a Runtime Option without an external edge receives no
assessment. The result is not complete configuration viability, selection,
authorization, reservation, dispatch, execution, or invocation. The canonical
contract is defined in:

`core/runtime-inference-pair-availability-specification.md`

---

## Agent Execution Candidate Prerequisite Assessment

A pure, immutable, deterministic, in-memory assessment of whether one
caller-designated external-inference Agent candidate satisfies all currently
modeled hard prerequisites in one caller-owned evaluation context.

Its subject is exactly one valid Assignment plus one exact
`runtime_option_id` plus one exact `option_id`. The Assignment remains the
responsibility anchor; no `candidate_id`, Candidate entity, inventory,
persistence, lifecycle, selection, or reassignment is created.

The assessment reuses current assigned-Actor availability, exact positive
Actor-to-Runtime applicability, and exact Runtime-to-Inference pair
availability. Its ordinary outcomes are `satisfied`, `blocked`, and
`unresolved`. Missing positive evidence is unresolved, explicit current
unavailability is blocked, and invalid parent input has findings but no
ordinary outcome.

`satisfied` means only that every hard prerequisite currently modeled by this
contract is positive. It does not mean selected, permitted, authorized,
reserved, executable, executing, or guaranteed to succeed. Human Assignments
and Runtime-owned inference remain outside the Agent external-inference path.
The canonical contract is defined in:

`core/agent-execution-candidate-prerequisite-specification.md`

---

## Operation Requirement

An immutable, caller-supplied declaration that one Core-defined abstract
operation is required against one exact lexical repository-relative resource
within the caller-owned evaluation context.

The value contains exactly `operation_id` and `resource`. Its identity is the
exact case-sensitive pair `(operation_id, resource)`. AIO-036 supports exactly
the abstract `repository_file_read` operation; the vocabulary may expand only
through future explicit Core definitions. Resources use forward-slash lexical
segments, remain extension-neutral, and are never normalized or accessed by
validation.

Operation Requirement states need only:

```text
requirement
!= capability
!= permission
!= authorization
!= execution
```

Presence means the caller supplied the declaration in this evaluation context.
Absence means only that no requirement was supplied; it is not a negative
requirement or evidence of support, prohibition, permission, or authorization.
The canonical contract is defined in:

`core/operation-requirement-specification.md`

---

## Agent Service

An external managed implementation that may expose or realize one or more Agent
Runtime Options. A service may own or delegate Agent sessions, tools, state,
lifecycle, scheduling, and model choice, but Core does not infer those details
from the service boundary.

Agent Service is distinct from Agent Runtime Option, bare model inference, and
Inference Option. No Agent Service subtype, schema, or domain contract exists in
AIO v0.1.

---

## Model Tier

**Deprecated.** Model Tier previously described the values `fast`, `standard`,
and `high` as one supposed capability or reasoning scale. Those values mix
latency and capability dimensions, so they are withdrawn and non-consumable.

Model Tier has no active semantics, schema, ordering, runtime behavior, or
routing behavior. It is not Execution Mode and is not a Provider reasoning
setting. AIO-028 adds only opaque Inference Option identity and separate
availability evidence; it establishes no replacement tier, capability scale,
requirement matching, reasoning mapping, or routing behavior. No replacement
enum is defined in v0.1.

---

## Agent

An AI participant that may be represented as an Actor with `kind: agent`.

Agent identity may be supplied as a candidate before assignment or execution.
Provider, model, runtime, reasoning configuration, availability, and execution
state are not part of the Actor contract.

An Agent Actor is logical identity, not an executable Agent definition. The
latter may include instructions, tools, memory, state configuration, model
policy, runtime binding, environment, sessions, permissions, and credentials;
AIO v0.1 defines no canonical Agent Definition contract.

When an Agent executes work, it may receive:

- a Task
- a Role
- relevant context
- applicable Rules
- applicable Policies
- available Capabilities

An Agent Actor does not receive execution authority merely by being an Agent.
A runtime execution remains separate from Actor identity.

A Role is reusable.

---

## Actor

A concrete, identifiable Human or Agent candidate capable of fulfilling a Role.

Actor identity is separate from availability, assignment, authority, permission,
approval, and execution. Actor answers **who**; Provider identifies an
operational access boundary, and Agent Runtime Option identifies the execution
surface through which an Agent may run or be delegated.

The canonical contract and matching semantics are defined in:

`core/actor-specification.md`

---

## Actor Competency

An exact, case-sensitive engineering competency identifier declared by an
Actor. Actor competencies use boolean set membership only; they have no levels,
weights, aliases, implications, or scores.

Actor competency is not runtime Capability, permission, authority, availability,
assignment, approval, or execution.

---

## Actor-Role Competency Coverage

Pure evidence that an Actor declares every engineering competency in a Role's
`required_capabilities` set.

Coverage does not select or assign an Actor and does not establish availability,
authority, permission, execution, Quality Gate PASS, or independent-review
satisfaction. A Role with no semantically approved required competencies is not
automatically matchable.

---

## Actor Availability Observation

An immutable, Provider-neutral, ephemeral value describing the currently known
availability state of one Actor within one caller-supplied evaluation snapshot.

The state is exactly `available`, `unavailable`, or `unknown`; unknown is not
unavailable. A missing observation normalizes to unknown. Availability does not
change Actor identity or competencies and does not establish eligibility,
Assignment, authority, permission, approval, or execution. The canonical
contract is defined in:

`core/actor-availability-specification.md`

---

## Actor Selection

Pure, deterministic, Provider-neutral resolution of one valid
Task/Workflow/Stage/Role responsibility against a caller-supplied Actor set and
availability snapshot, using exact competency coverage and availability facts
only.

Actor Selection produces decision evidence with exactly one of `selected`,
`ambiguous`, `indeterminate`, or `no_candidate` for valid input. It does not rank,
assign, authorize, reserve, or execute Actors. The canonical contract is defined
in:

`core/actor-selection-specification.md`

---

## Assignment

An immutable, Provider-neutral value binding one concrete Actor identity to one
Role required at one Stage of the Workflow explicitly governing one Task.

Assignment records an externally made responsibility choice. It does not select
or rank Actors, inspect availability, grant authority or permission, configure or
perform execution, establish Workflow state, or produce a Quality Gate result.

Agent Execution Authorization Evidence may refer to one complete Assignment as
part of an exact action subject, but an Assignment never creates that evidence.

The responsibility key is `(task_id, workflow_id, stage_id, role_id)`;
`actor_id` is the selected value. The canonical contract is defined in:

`core/assignment-specification.md`

---

## Role

A reusable engineering responsibility and its required competencies.

Examples:

- Orchestrator
- Architect
- Developer
- Tester
- Reviewer
- Security Reviewer
- Documentation Agent

Roles are Provider-independent.

---

## Capability

An action or class of work an Agent or Provider can perform.

Examples:

- repository-read
- repository-write
- shell-execution
- browser-testing
- code-review
- deep-reasoning
- visual-analysis
- subagent-spawning

Future routing decisions should primarily use Capabilities instead of hardcoded Provider names.

---

## Task

A Task is the canonical unit of scoped work managed through AI Engineering Orchestra.

Examples:

- implement a feature
- fix a bug
- refactor a service
- update documentation
- review a pull request
- investigate a technical problem
- define an architecture or specification

A Task defines Task-specific intent, scope, Risk, Complexity, Execution Mode, acceptance criteria, Quality Gate requirements, Human control requirements, dependencies, review evidence, and lifecycle status.

The canonical Task contract is defined in:

`core/task-specification.md`

The default Project Task location is:

`.ai/tasks/`

The canonical reusable Task example is available at:

`templates/task/`

A Task must operate within the precedence, context, Human control, Policy, Rule, Workflow, and Quality Gate requirements that apply to the Project.

A Task may reference an applicable Workflow, but Workflow definitions and behavior remain owned by `workflows/`.

---

## Workflow

A reusable sequence of engineering stages used to complete a class of Task.

Examples:

- feature Workflow
- bugfix Workflow
- refactor Workflow
- architecture-change Workflow

The canonical Workflow contract is defined in:

`core/workflow-specification.md`

The canonical reusable Workflow definitions are maintained in:

`workflows/`

---

## Stage

One step inside a Workflow.

Examples:

- Analyze
- Plan
- Implement
- Test
- Review
- Validate

The canonical Stage contract is defined in:

`core/workflow-specification.md`

---

## Quality Gate

A condition that must be satisfied before work may progress.

Examples:

- build passes
- tests pass
- lint passes
- independent review passes

A Quality Gate is not simply a recommendation.

---

## Project Verification Check

A declarative project-owned definition of a mechanical repository check that can
be executed programmatically by AIO to collect mechanical evidence.
**Verification Check** is the preferred short form when context is unambiguous.

The declaration is owned by `core/project-manifest.md`, under
`.ai/project.yaml` → `verification.checks`.

A Check is not a Quality Gate, Task, Workflow Stage, Agent execution, Assignment,
Execution Contract, or approval mechanism. Its ID is not a Quality Gate ID, and
Verification Check PASS is not Quality Gate PASS. Mechanical evidence does not
itself establish governance approval or confer execution authority.

The contract, programmatic runner, and public `aio verify` composition execute
these declarations when the Human caller explicitly invokes full verification.
This mechanism does not grant execution authority to Agents or establish Quality
Gate results.

---

## Policy

A rule governing Agent behavior.

Policies may define:

- required approvals
- prohibited behavior
- security boundaries
- Agent limits
- quality requirements

Policies are stronger than suggestions.

---

## Organization Policy

A Policy defined above an individual Project and intended to apply across multiple Projects or repositories.

Examples may include:

- security requirements
- deployment restrictions
- review requirements
- compliance requirements
- protected Git operations

Organization Policies may establish constraints that Project configuration cannot weaken.

---

## User Policy

A Policy defined by the individual Human operating the Orchestra and intended to apply across their Projects or environments.

Examples may include:

- personal security restrictions
- approval requirements
- Agent autonomy limits

User Policies must follow the Orchestra precedence model.

---

## Rule

An instruction relevant to a project, technology, domain, or Task.

Rules may originate from:

- Orchestra Core
- Stack Module
- organization
- project
- Task

---

## Organization Rule

A reusable engineering Rule defined above an individual Project.

Examples may include:

- naming conventions
- documentation standards
- coding conventions
- repository conventions

Organization Rules apply unless a higher-precedence Policy or a permitted more-specific Rule overrides them.

---

## User Rule

A reusable Rule defined by an individual Human for their engineering environment.

Examples may include:

- preferred documentation practices
- personal workflow conventions
- local development preferences

User Rules must not weaken applicable protected Policies.

---

## Profile

A reusable collection of default configuration.

Examples:

- minimal
- standard
- critical
- SaaS
- enterprise

A Project may inherit from a Profile and override permitted settings.

---

## Stack Module

Reusable guidance for a specific technology.

Examples:

- .NET
- Angular
- SQL Server
- PostgreSQL
- Docker
- Kubernetes

Stack Modules must not contain project-specific business Rules.

---

## Provider Adapter

The integration layer between AI Engineering Orchestra and a specific AI Provider.

Adapters translate Orchestra concepts into Provider-specific configuration where necessary.

Example:

```text
Orchestra Role
    ↓
Provider Adapter
    ↓
Provider-specific Agent configuration
```

---

## Project Manifest

The project's primary Orchestra configuration file.

Default location:

.ai/project.yaml

It defines Project-level Orchestra configuration and references the locations or defaults needed to govern Orchestra behavior for that Project.

The canonical Project Manifest contract is defined in `core/project-manifest.md`.

---

## Project Rule

A Rule that applies only to a specific project.

Examples:

- architecture conventions
- naming conventions
- repository restrictions
- business invariants
- deployment constraints

---

## Override

A project-specific modification of default Orchestra configuration where overrides are permitted.

Overrides may make Policies stricter.

Security-sensitive Policies may prohibit weakening through overrides.

---

## Orchestrator

The Role responsible for coordinating engineering work.

The Orchestrator may:

- analyze a Task
- classify complexity
- classify risk
- select Workflows
- assign Roles
- select required Capabilities
- coordinate Agents
- evaluate Quality Gates
- escalate work

The Orchestrator is not a specific AI Provider.

---

## Approval Level

A classification describing the degree of Human involvement required before work or an action may proceed.

Initial Approval Levels are:

- none
- review
- explicit
- protected

Their detailed behavior is defined in:

`core/human-control.md`

Approval Level is separate from Task risk and complexity.

---

## Permission Decision

A security decision describing whether an Agent operation may proceed.

Reserved initial Permission Decisions are:

- allow
- ask
- always-ask
- deny

Their security precedence is:

deny

>

always-ask

>

ask

>

allow

Permission Decision is defined conceptually in v0.1.

Permission Decision is distinct from Environment Operation Permission
Observation. The latter uses `allowed`, `denied`, and `unknown` only as supplied
environment facts; none is a Permission Decision or authorization result.

Permission Decision is also distinct from Agent Execution Authorization
Evidence. Core does not map `allow`, `ask`, `always-ask`, or `deny` to the
evidence states `granted` or `denied`; any authority producer remains outside
the AIO-039 evidence-validation contract.

Full command permission enforcement is planned for Orchestra v0.2.

---

## Human

The ultimate authority over the Orchestra.

Human approval may be required for operations such as:

- production deployment
- critical changes
- security exceptions
- destructive database migrations
- protected Git operations
- architecture exceptions

The Orchestra must never design a Workflow where AI authority silently exceeds explicitly defined Human authority.

---

## Complexity

A descriptive property of what the work inherently demands: expected reasoning
difficulty, engineering depth, coordination, decomposition, and problem
complexity.

Initial levels:

- low
- medium
- high
- critical

Complexity is independent from Risk and Execution Mode. It is not a model tier,
Provider reasoning setting, authorization level, approval policy, or Workflow
selector. No Complexity value automatically determines any of those concepts.

---

## Risk

The potential impact if Task execution is wrong.

Initial levels:

- low
- medium
- high
- critical

A Task may have low Complexity but critical Risk. Risk may cause stronger
validation, review, Human oversight, or safety controls only when an applicable
Policy or other authoritative rule says so. Risk does not automatically select
an Execution Mode, Workflow, model, or Provider option.

---

## Execution Mode

A Provider-neutral, Task-wide minimum required engineering-execution posture
within the already selected Workflow. It governs cumulative process depth,
rigor, analysis and decomposition, evidence discipline, and bounded
self-direction. It is neither an exact ceiling nor a Task classification.

The modes have this normative process-depth order:

```text
lite < standard < deep < critical
```

A mode satisfies its own minimum and every lower minimum; it does not satisfy a
higher minimum. The order describes process depth only, not authority, approval,
cost, latency, model strength, or outcome quality.

Each description is a cumulative minimum obligation, not a maximum. A lighter
mode does not require the additional obligations named by higher modes, but it
never prohibits extra rigor, analysis, decomposition, evidence, validation, or
bounded self-direction.

- `lite`: the smallest floor for well-bounded work, requiring a coherent direct
  path, sufficient relevant context and evidence, proportionate validation, and
  the decomposition needed for coherence. Expected bounded self-direction is
  narrow.
- `standard`: includes `lite` plus explicit planning, disciplined execution,
  validation, self-checking, routine bounded self-direction, and explicit
  evidence for material claims.
- `deep`: `standard` plus deliberate decomposition, trade-off and edge-case
  analysis, broader evidence gathering, probing validation, and sustained
  bounded self-direction.
- `critical`: `deep` plus the strongest scrutiny, assumption challenge, failure
  and safety analysis, traceability, corroboration, the strongest bounded
  self-direction, and conservative escalation of unresolved uncertainty.

Expected autonomy means bounded self-direction within already established
scope, authority, permissions, Policies, and Human controls. Execution Mode
applies to both Human and Agent Actors and never grants authority.

All responsibilities inherit the effective Task mode. Stage-, Role-, and
responsibility-specific overrides are unsupported in v0.1, and mode is not
inferred from Stage or Role identity, name, or capabilities.

Workflow and Execution Mode are orthogonal. Mode changes only the depth applied
inside existing choreography. It does not:

- select a Workflow;
- add, remove, or reorder Workflow Stages;
- change required Roles, Quality Gates, or Human-control checkpoints;
- establish a Quality Gate result or satisfy Human approval;
- grant permission or authorization; or
- map to a Provider, model, runtime, or Provider reasoning control.

Complexity, Risk, Workflow, Stage, and Role do not automatically determine
Execution Mode. An explicit Task value takes precedence over the Project default.

---

## Greenfield Project

A new project where architecture and implementation are being created from the beginning.

---

## Brownfield Project

An existing project with established behavior, architecture, code, dependencies, and technical debt.

Full Brownfield onboarding and analysis is planned for Orchestra v0.2.

---

## Modernization Project

An existing Project undergoing deliberate architectural, platform, technology, or engineering improvement.

Examples may include:

- framework upgrades
- platform migrations
- architectural restructuring
- CI/CD introduction
- test coverage improvement
- monolith decomposition
- dependency modernization

Modernization must be planned and incremental.

It is not authorization for uncontrolled refactoring or broad rewrites.

---

## Maintenance Project

An established Project primarily focused on preserving stability while receiving ongoing changes.

Typical work may include:

- bug fixes
- small features
- dependency updates
- operational improvements
- security updates
- support changes

Maintenance does not prohibit architectural improvement, but stability is the default expectation.

---

## Source of Truth

The authoritative location for a specific category of information.

Agents must prefer Sources of Truth over assumptions or duplicated documentation.
