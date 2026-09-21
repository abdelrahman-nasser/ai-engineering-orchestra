# AI Engineering Orchestra

AI Engineering Orchestra is a reusable, versioned, model-agnostic framework for organizing AI-assisted software engineering.

It provides a common structure for:

- AI Agent Roles
- engineering Workflows
- project Rules
- Quality Gates
- Risk and Complexity handling
- Human approval
- project context
- future Provider routing and security controls

The framework is designed to work independently of any specific AI Provider, model, programming language, framework, or application architecture.

---

## Current Version

```text
0.1.0
```

## Local CLI Installation

Python 3.12 or newer is required for the locally installable CLI. AIO-016
establishes this initial packaging baseline; it is not a historical support claim.
From this checkout, in a virtual environment:

```powershell
python -m pip install -e .
aio --help
aio tasks
aio inspect AIO-015
aio verify
aio verify --structure
```

For a normal installation, use `python -m pip install .` instead. The command is
available when the installing environment's `Scripts` (Windows) or `bin` directory
is on PATH, usually by activating the environment. Editable installations follow
source edits; metadata/console-name changes require reinstalling. Normal installs
must be reinstalled to receive source changes. Uninstall with
`python -m pip uninstall ai-engineering-orchestra`; the checkout remains intact.

Run commands from the managed project or a subdirectory. The nearest ancestor
containing `.ai/project.yaml` determines the active project, never the installed
package location. `tasks` and `inspect` resolve `tasks.directory` from the active
Manifest (default `.ai/tasks/`). Workflows remain in the target project's
`workflows/`; canonical schemas and Roles belong to the tool. An adopter's own
`roles/` directory is ignored because project Role extensions and overrides are
not part of the current contract.

`aio verify` validates the active project's supported AIO structure and then runs
its project-declared Verification Checks from `.ai/project.yaml` in declaration
order. Omitted or empty checks mean zero commands; AIO does not infer checks from
repository contents and has no Orchestra-specific fallback. Before execution the
CLI names the declaration source and ordered Check IDs. `aio verify --structure`
is the non-executing inspection path: it validates supported structure without
planning, resolving, or running declared commands.

Declared commands use the caller's filesystem access, network access,
credentials, environment, and process authority. AIO provides no sandbox,
filesystem or network isolation, credential isolation, purity, read-only
guarantee, harmlessness, or full descendant containment. Bounded failure output
is unsanitized and may enter terminal or CI logs. The inherited
`ENGINEERING_ORCHESTRATION_VERIFY_DEPTH` marker blocks ordinary nested aggregate
verification, but wrappers can remove it and arbitrary recursion cannot be
proven absent. Repository declarations and command availability do not authorize
an Agent to invoke verification or grant any execution authority. Mechanical
PASS is not Quality Gate satisfaction or Human approval.

This repository dogfoods the same portable path with seven Manifest declarations.
Git and Node/npm (`npx`) must already be available on PATH; they are not Python
dependencies and are not installed automatically. Verification must run from a
supported/activated development environment where PATH-selected `python` has the
repository's required dependencies.

Source commands (`python -B aio.py ...` and `python -B scripts/list_tasks.py`,
`scripts/inspect_task.py`, `scripts/verify_repo.py`) remain available. Normal console
launchers may write Python bytecode; suppressing installed `__pycache__` is not a
product requirement. Preflight Python subprocesses retain their explicit `-B`.

The local distribution name `ai-engineering-orchestra`, temporary console name
`aio`, technical namespace `engineering_orchestration`, product display name,
and historical `AIO-*` Task IDs are separate identities. Another console name can
target the same router without changing capabilities. The static distribution
version `0.1.0` identifies installed code; Manifest `orchestra.version` expresses
the managed project's framework expectation. No version synchronization is implied.

This is an explicitly authorized local-installability experiment. It does not
complete the future public distribution milestone. No PyPI publication, public
name reservation, release automation, or full CLI lifecycle is provided.

## Execution Mode Semantics

Task Execution Mode is a Provider-neutral, Task-wide minimum engineering posture
inside an already-selected Workflow. The normative process-depth order is:

```text
lite < standard < deep < critical
```

A higher posture satisfies a lower minimum. The order controls cumulative rigor,
analysis and decomposition, evidence discipline, validation depth, and bounded
self-direction only. It does not choose or restructure a Workflow, change Roles,
Quality Gates, or Human controls, grant authority, or map directly to a Provider,
model, runtime, or reasoning setting. Human and Agent responsibilities inherit
the same effective Task mode.

Every mode description is a cumulative minimum floor, not a ceiling: `standard`
includes `lite`, `deep` includes `standard`, and `critical` includes `deep`.
Selecting a lighter minimum never prohibits additional rigor; it means only that
the extra obligations of higher modes are not required.

The pure relation is available to runtime consumers without a policy or routing
engine:

```python
from engineering_orchestration.execution_mode import execution_mode_satisfies

assert execution_mode_satisfies("deep", "standard")
```

Complexity, Risk, and Execution Mode remain independent values with explicit
Task values taking precedence over their matching Project defaults. The former
Model Tier values (`fast`, `standard`, `high`) are deprecated and non-consumable;
Inference Option identity and availability add no replacement tier or routing
behavior. Canonical Execution Mode semantics are defined in
[`core/task-specification.md`](core/task-specification.md#15-execution).

## Inference Option Definition and Availability

An Inference Option is a caller/environment-supplied identity for one accessible
way to address a model through an operational Provider boundary. Its Definition
contains exactly `option_id`, `provider_id`, and Provider-scoped `model_id`:

```python
from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    validate_inference_option_inventory,
)

options = [
    InferenceOptionDefinition("primary", "provider-a", "model-x"),
    InferenceOptionDefinition("secondary", "provider-a", "model-x"),
]
inventory = validate_inference_option_inventory(options)
```

`option_id` is the unique identity within one supplied inventory. Two options
may use the same Provider/model pair. IDs remain opaque and case-sensitive; no
Provider or model enum, catalog, endpoint, credential, capability, or discovery
contract exists.

Availability is separate ephemeral evidence:

```python
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
    validate_inference_option_availability,
)

availability = validate_inference_option_availability(
    [
        InferenceOptionAvailabilityObservation(
            "primary", InferenceOptionAvailabilityState.AVAILABLE
        )
    ],
    options,
)
```

States are exactly `available`, `unavailable`, and `unknown`. Missing
observations normalize to unknown. Duplicate option IDs, duplicate observations,
and unknown-option references invalidate their complete input without partial
normalized output. Available does not mean selected, authorized, executable,
within quota, compatible with Execution Mode, or backed by an available runtime.

AIO-028 introduced no option selection, routing, Provider integration, network
access, persistence, Runtime Option modeling, authorization, or invocation. Its
semantic authorities are
[`core/inference-option-specification.md`](core/inference-option-specification.md)
and
[`core/inference-option-availability-specification.md`](core/inference-option-availability-specification.md).

## Agent Runtime Option Definition, Availability, and Capability

An Agent Runtime Option is an opaque, caller/environment-supplied configured
execution surface through which an Agent execution can run or be delegated. Its
Definition contains exactly `runtime_option_id`:

```python
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)

runtime_options = [
    AgentRuntimeOptionDefinition("primary-agent-runtime"),
    AgentRuntimeOptionDefinition("secondary-agent-runtime"),
]
runtime_inventory = validate_agent_runtime_option_inventory(runtime_options)
```

The ID is opaque, exact, case-sensitive, and unique within one supplied
sequence. It does not encode an Actor, Provider, model, implementation,
framework, Runtime Option type, process, session, or invocation.

Availability is separate ephemeral evidence:

```python
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
    validate_agent_runtime_option_availability,
)

runtime_availability = validate_agent_runtime_option_availability(
    [
        AgentRuntimeOptionAvailabilityObservation(
            "primary-agent-runtime",
            AgentRuntimeOptionAvailabilityState.AVAILABLE,
        )
    ],
    runtime_options,
)
```

States are exactly `available`, `unavailable`, and `unknown`. Missing
observations normalize to unknown. Duplicate Runtime Option IDs, duplicate
observations, and unknown references invalidate their complete input without
partial normalized output. Available does not mean Actor-applicable,
Inference-compatible, selected, authorized, capacity-ready, or executing.

Runtime Operation Capability Observation is separate caller/environment-supplied
technical-support evidence for one known Runtime Option and one Core-defined
abstract operation:

```python
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    validate_runtime_operation_capability,
)

runtime_capability = validate_runtime_operation_capability(
    [
        RuntimeOperationCapabilityObservation(
            "primary-agent-runtime",
            "repository_file_read",
            RuntimeOperationCapabilityState.PRESENT,
        )
    ],
    runtime_options,
)
```

The observation contains exactly `runtime_option_id`, `operation_id`, and
`state`; its exact pair identity excludes state. States are exactly `present`,
`absent`, and `unknown`. Every missing known Runtime/Core-operation pair
normalizes to unknown, never absent. Duplicate pairs, unknown Runtime
references, malformed operation IDs, and well-formed unsupported operations
invalidate the complete snapshot without partial normalized output.

Capability means technical support for the abstract operation in principle. It
contains no resource, tool identity, environment, timestamp, or freshness, and
does not establish requirement, availability, permission, authorization,
dispatchability, execution, or success. Core validates supplied observations;
it performs no capability discovery or Runtime probing.

Actor-to-Runtime Applicability Evidence is a separate caller-supplied positive
many-to-many relation between known Agent Actors and Runtime Options:

```python
from engineering_orchestration.actor_runtime_applicability import (
    ActorRuntimeApplicabilityEvidence,
    validate_actor_runtime_applicability,
)

actors = [
    {"id": "agent-engineer", "kind": "agent",
     "competencies": ["implementation"]},
]
applicability_evidence = [
    ActorRuntimeApplicabilityEvidence(
        "agent-engineer", "primary-agent-runtime"
    ),
]
applicability = validate_actor_runtime_applicability(
    applicability_evidence,
    actors,
    runtime_options,
)
```

Actor values are structurally validated by their existing schema; relation
validation rejects duplicate Actor IDs, duplicate exact edges, unknown
references, and known Human Actor endpoints atomically. Runtime inventory
validation is reused. Valid evidence is ordered by exact
`(actor_id, runtime_option_id)` only for deterministic representation. An empty
relation is valid, and a missing edge means only that no positive applicability
evidence was supplied. It is not proof of incompatibility, unavailability, lack
of authorization, or inability to execute.

Runtime-to-Inference Compatibility Evidence is a separate caller-supplied
positive many-to-many relation:

```python
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
    validate_runtime_inference_compatibility,
)

compatibility_evidence = [
    RuntimeInferenceCompatibilityEvidence("primary-agent-runtime", "primary"),
    RuntimeInferenceCompatibilityEvidence("primary-agent-runtime", "secondary"),
]
compatibility = validate_runtime_inference_compatibility(
    compatibility_evidence,
    runtime_options,
    options,
)
```

Both endpoint inventories are validated first. Duplicate exact edges and
unknown endpoint references invalidate the complete relation without partial
normalized evidence. Valid evidence is ordered by exact
`(runtime_option_id, option_id)` only for deterministic representation. An empty
relation is valid, and a missing edge means only that no positive external
compatibility evidence was supplied; it is not proof of incompatibility or
non-executability. A Runtime Option may still own or hide inference selection
and have no external edge.

Runtime-to-Inference Pair Availability Assessment composes that validated
positive relation with both normalized endpoint-availability snapshots:

```python
from engineering_orchestration.runtime_inference_pair_availability import (
    assess_runtime_inference_pair_availability,
)

pair_availability = assess_runtime_inference_pair_availability(
    compatibility_evidence,
    runtime_options,
    options,
    [
        AgentRuntimeOptionAvailabilityObservation(
            "primary-agent-runtime",
            AgentRuntimeOptionAvailabilityState.AVAILABLE,
        )
    ],
    [
        InferenceOptionAvailabilityObservation(
            "primary", InferenceOptionAvailabilityState.AVAILABLE
        )
    ],
)
print([(item.runtime_option_id, item.option_id, item.outcome)
       for item in pair_availability.assessments])
```

Each supplied edge receives exactly one outcome: `established` only when both
endpoints are available, `blocked` when either is unavailable, and `unresolved`
otherwise. Missing observations normalize to unknown. Invalid input produces
findings and no assessments; an empty valid relation still validates both
availability inputs and produces an empty assessment tuple. This derived result
does not add inferred edges or select, authorize, reserve, dispatch, or invoke a
configuration.

Agent Execution Candidate Prerequisite Assessment composes the existing
contracts for one explicit external-inference Agent candidate. Its identity is
one valid Assignment plus exact Runtime and Inference Option IDs:

```python
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    assess_agent_execution_candidate_prerequisites,
)

candidate = assess_agent_execution_candidate_prerequisites(
    assignment,
    "primary-agent-runtime",
    "primary",
    task,
    workflow_catalog,
    role_catalog,
    actors,
    actor_availability_observations,
    applicability_evidence,
    runtime_options,
    options,
    compatibility_evidence,
    runtime_availability_observations,
    inference_availability_observations,
)
print(candidate.outcome, candidate.reasons)
```

The ordinary outcomes are `satisfied`, `blocked`, and `unresolved`. Explicit
unavailability blocks; missing or unknown positive evidence is unresolved; all
currently modeled positive prerequisites are satisfied. Invalid parent input
instead returns findings with no outcome or partial identity. A Human
Assignment is outside this Agent-only path. `satisfied` is not selection,
permission, authorization, reservation, an Execution Contract, or execution.

AIO-035 adds a private, experimental dry-run preparation harness for exactly
one abstract operation: `repository_file_read` on one exact canonical
repository-relative Markdown path, `workflows/README.md`. It consumes the
existing candidate result
plus separate caller-supplied capability, environment-permission/freshness,
and Human- or policy-provided authorization evidence. Only exact, current,
positive evidence in every required dimension can produce the cautious
`potentially_executable` diagnostic; other valid combinations remain `blocked`
or `unresolved` with deterministic reasons.

The harness validates the resource lexically. It never opens, reads, stats,
hashes, or filesystem-resolves the target; discovers or changes permissions;
parses historical approval prose; creates an execution request or Execution
Contract; dispatches; or invokes anything. It is packaged only as the private
`engineering_orchestration._read_only_execution_preparation` module, with no
public package export, CLI, schema, adapter, or stable Core contract. This
evidence-consuming experiment is not the v0.2 permission-enforcement system.

The current high-level separation is:

```text
Actor
  = logical who

Agent Runtime Option
  = configured execution surface

Inference Option
  = configured inference access

Caller/environment
  -> caller-scoped Actor context
  -> caller-scoped Runtime Option inventory + availability
  -> caller-scoped Runtime operation capability observations
  -> caller-scoped environment operation permission observations
  -> caller-scoped Inference Option inventory + availability
  -> supplied positive Actor-to-Runtime applicability evidence
  -> supplied positive Runtime-to-Inference compatibility evidence

current independent evidence:
Actor-to-Runtime Applicability Evidence

compatibility evidence + endpoint availability
  -> Runtime-to-Inference Pair Availability Assessment

Assignment + Actor availability
  + Actor-to-Runtime applicability
  + Runtime-to-Inference pair availability
  -> Agent Execution Candidate Prerequisite Assessment
  -> satisfied | blocked | unresolved

current canonical action-layer declaration:
caller/planner
  -> Operation Requirement(operation_id, resource)
  -> declared need only; no capability, permission, authorization, or execution

current canonical Runtime technical-support evidence:
caller/environment
  -> Runtime Operation Capability Observation(runtime_option_id,
                                                operation_id, state)
  -> present | absent | unknown
  -> no resource, tool binding, availability, permission, authorization,
     or execution

current canonical environment-permission evidence:
caller/environment
  -> Environment Operation Permission Observation(runtime_option_id,
                                                    environment_id,
                                                    operation_id,
                                                    resource, state)
  -> allowed | denied | unknown
  -> exact supplied evidence only; no Permission Decision, Human/policy
     authorization, enforcement, or execution

current canonical exact-action authorization evidence:
caller/authority producer
  -> Agent Execution Authorization Evidence(Assignment subject,
                                             runtime_option_id, option_id,
                                             environment_id, operation_id,
                                             resource, authority, state)
  -> granted | denied
  -> caller-attested evidence only; no authenticated authority, lifecycle,
     enforcement, dispatch, or execution

current private experiment:
candidate prerequisite assessment
  + its existing provisional capability evidence
  + its existing provisional environment permission + freshness evidence
  + caller-supplied Human/policy authorization evidence
  -> read-only execution preparation dry run
  -> potentially_executable | blocked | unresolved
  -> no target I/O, permission discovery, request, dispatch, or invocation

future only, through separately designed contracts and adapters:
potentially_executable diagnostic
  -> Execution Contract
  -> invocation
```

Actor is not an executable Agent definition, Runtime Option, Inference Option,
or execution instance. Human Actors require no Runtime Option. A Runtime Option
may expose zero externally selectable Inference Options because inference may be
selected internally or hidden by an external Agent definition or managed Agent
Service. Absence of compatibility edges therefore does not prove that a
Runtime Option cannot execute. Absence of an Actor-to-Runtime edge likewise
means only that no positive applicability evidence was supplied.

AIO-029 introduces no Actor mapping, Runtime-to-Inference compatibility,
execution configuration, Agent Definition, Agent Service contract, Provider
adapter, selection, authorization, persistence, network access, or invocation.
The later AIO-033 relation references Actor and Runtime identities without
embedding a mapping in either endpoint Definition or changing the Human path.
The semantic authorities are
[`core/agent-runtime-option-specification.md`](core/agent-runtime-option-specification.md)
and
[`core/agent-runtime-option-availability-specification.md`](core/agent-runtime-option-availability-specification.md).
The separate Actor-to-Runtime relation authority is
[`core/actor-runtime-applicability-specification.md`](core/actor-runtime-applicability-specification.md).
The separate positive-relation authority is
[`core/runtime-inference-compatibility-specification.md`](core/runtime-inference-compatibility-specification.md).
The derived pair-availability authority is
[`core/runtime-inference-pair-availability-specification.md`](core/runtime-inference-pair-availability-specification.md).
The exact-candidate composition authority is
[`core/agent-execution-candidate-prerequisite-specification.md`](core/agent-execution-candidate-prerequisite-specification.md).
The Runtime-operation capability authority is
[`core/runtime-operation-capability-specification.md`](core/runtime-operation-capability-specification.md).
The environment-operation permission-observation authority is
[`core/environment-operation-permission-specification.md`](core/environment-operation-permission-specification.md).
The exact-action authorization-evidence authority is
[`core/agent-execution-authorization-evidence-specification.md`](core/agent-execution-authorization-evidence-specification.md).
AIO-035 deliberately adds no new Core specification: its provisional semantics
remain in the AIO-035 Task evidence, private implementation, and focused tests.
AIO-037 through AIO-039 do not retrofit that private experiment or compose
capability, permission, candidate, and authorization evidence into execution.

## Operation Requirement

Operation Requirement is the canonical, immutable caller-supplied declaration
that one Core-defined abstract operation is needed against one exact lexical
repository-relative resource in the caller-owned evaluation context. It
contains exactly `operation_id` and `resource`:

```python
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    validate_operation_requirement,
)

requirement = OperationRequirement(
    operation_id="repository_file_read",
    resource="synthetic/input.txt",
)
result = validate_operation_requirement(requirement)
```

Identity is exact case-sensitive `(operation_id, resource)`. AIO-036 supports
only `repository_file_read`; future operation identifiers require explicit Core
definitions. Operation Requirement and Runtime Operation Capability validation
consume one shared package-internal Core operation vocabulary. The operation
remains abstract and is not inferred from a tool or Provider.

The resource is validated as an extension-neutral lexical string with `/`
separators. Absolute, drive-qualified, UNC, URI, tilde-rooted, backslash,
control-character, empty-segment, dot-segment, parent-segment, trailing-slash,
and glob/meta forms are rejected. Validation does not normalize, resolve,
existence-check, open, read, stat, hash, list, or otherwise access the resource
or repository. Operation Requirement and Environment Operation Permission
Observation reuse one package-internal repository-resource validator without
changing AIO-036 codes, messages, precedence, public API, or atomicity.

Presence states need only; absence means only that no requirement was supplied
in that evaluation context. Operation Requirement proves no Runtime capability,
environment permission, Human or policy authorization, or execution:

```text
requirement != capability != permission != authorization != execution
```

The structural schema owns only the exact two required nonempty string fields.
The semantic authority and deterministic runtime behavior are defined in
[`core/operation-requirement-specification.md`](core/operation-requirement-specification.md).
The separate technical-support contract is defined in
[`core/runtime-operation-capability-specification.md`](core/runtime-operation-capability-specification.md).
The separate environment-permission evidence contract is defined in
[`core/environment-operation-permission-specification.md`](core/environment-operation-permission-specification.md).
The earlier AIO-035 preparation harness remains a private bounded experiment;
AIO-036 does not retrofit it, access its protected target, or canonicalize its
provisional capability, permission, or authorization evidence.

## Environment Operation Permission Observation

Environment Operation Permission Observation is immutable,
caller/environment-supplied evidence about whether one opaque environment
currently permits one known Runtime Option to perform one Core operation
against one exact lexical repository-relative resource:

```python
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    validate_environment_operation_permission,
)

permission_snapshot = validate_environment_operation_permission(
    [
        EnvironmentOperationPermissionObservation(
            runtime_option_id="primary-agent-runtime",
            environment_id="synthetic-evaluation-environment",
            operation_id="repository_file_read",
            resource="synthetic/input.txt",
            state=EnvironmentOperationPermissionState.ALLOWED,
        )
    ],
    runtime_options,
    "synthetic-evaluation-environment",
)
```

The observation contains exactly `runtime_option_id`, `environment_id`,
`operation_id`, `resource`, and `state`, in that order. Its exact case-sensitive
identity excludes state. States are exactly `allowed`, `denied`, and `unknown`;
they remain distinct from the Permission Decision vocabulary `allow`, `ask`,
`always-ask`, and `deny`.

The Runtime inventory, snapshot environment, operation vocabulary, and lexical
resource grammar are validated without discovery or I/O. An environment
mismatch, unknown Runtime, malformed or unsupported operation, or invalid
resource invalidates the complete snapshot. Valid output contains only supplied
observations sorted by exact Runtime, environment, operation, and resource
identity. A missing exact observation semantically means unknown, never denied,
but no open-ended Cartesian permission snapshot is synthesized.

Repeated exact identities are invalid. Identical-state repetitions produce a
duplicate finding; any repeated identity with differing states produces a
conflict finding. The categories are mutually exclusive and deterministic.
Conflicting permission observations are invalid evidence: there is no first-,
last-, latest-, allowed-, deny-, or stricter-wins rule, no declaration-order
precedence, and no conversion to unknown, denied, a Permission Decision, or a
Human approval question. The caller/environment evidence producer owns
reconciliation and must resupply one coherent observation.

`allowed` is only an environment fact. It does not establish Runtime capability
or availability, a Permission Decision, Human or policy authorization,
enforcement, dispatchability, execution, or success. The contract contains no
freshness field; snapshot currency is caller-owned, and stale or unreliable
evidence must be omitted or supplied as unknown. Core does not discover,
verify, poll, enforce, or mutate permissions and creates no Execution Contract
or invocation.

The schema owns only the exact five-field object shape, required nonempty
strings, the closed state enum, and rejection of extra properties. Semantic
validation, deterministic finding order, exact canonical ordering, and atomic
invalid results are defined by
[`core/environment-operation-permission-specification.md`](core/environment-operation-permission-specification.md).
The earlier AIO-035 preparation harness retains separate provisional evidence
and freshness semantics; AIO-038 does not retrofit or canonicalize it.

## Agent Execution Authorization Evidence

Agent Execution Authorization Evidence is an immutable, caller-supplied
assertion that one identified Human or policy authority granted or denied one
exact assigned external-inference Agent action:

```python
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
    validate_agent_execution_authorization_evidence,
)

evidence = AgentExecutionAuthorizationEvidence(
    task_id="AIO-SYNTHETIC",
    workflow_id="architecture-change",
    stage_id="implement",
    role_id="software-engineer",
    actor_id="agent-engineer-1",
    runtime_option_id="primary-agent-runtime",
    option_id="primary-inference-option",
    environment_id="synthetic-evaluation-environment",
    operation_id="repository_file_read",
    resource="synthetic/input.txt",
    authority_kind=AgentExecutionAuthorizationAuthorityKind.HUMAN,
    authority_id="human-reviewer-1",
    provenance_reference="approval-record-1",
    state=AgentExecutionAuthorizationState.GRANTED,
)

authorization_snapshot = validate_agent_execution_authorization_evidence(
    [evidence],
    assignments,
    task,
    workflow_catalog,
    role_catalog,
    actors,
    runtime_options,
    inference_options,
    "synthetic-evaluation-environment",
)
```

The first ten fields form the exact action subject; the remaining fields state
the caller-attested authority, opaque provenance, and `granted` or `denied`
assertion. Evidence applies only to an exact valid Agent Assignment and known
Runtime and external Inference Options in the supplied context. Repeated
subjects are rejected deterministically as a state conflict, unsupported
multi-authority assertion, or exact duplicate; Core chooses no winner.

The value is evidence, not authenticated authority or a usable grant. Core does
not verify identity, entitlement, provenance, freshness, expiry, or revocation.
Missing exact-subject evidence means authorization is unproven, not denied.
Task approval, Assignment, candidate satisfaction, capability, environment
permission, and Permission Decision do not create it. Validation performs no
target I/O and provides no lifecycle, persistence, replay protection,
enforcement, dispatch, or execution.

The closed fourteen-field schema owns structure only. Exact semantics,
deterministic findings, canonical supplied-only output, and atomic invalid
results are defined by
[`core/agent-execution-authorization-evidence-specification.md`](core/agent-execution-authorization-evidence-specification.md).

## Installed Structural Validation

The programmatic API reads the nearest active project's supported AIO structures:

```python
from engineering_orchestration.validation import validate_project

result = validate_project()  # CWD, then ancestors containing .ai/project.yaml
print(result.status)  # PASS, FAIL, or ERROR
for finding in result.findings:
    print(finding.status, finding.path, finding.message)
```

An optional `start=Path(...)` chooses the discovery starting directory. Validation
covers the Project Manifest, immediate Task child directories in the configured
Task path, declared Task ID uniqueness, Workflow YAMLs and ID uniqueness,
Workflow-local Stage ID uniqueness, declared Task-to-Workflow references, and
Workflow-to-framework-Role references.
Directory and file names do not define IDs. Missing required project structures
or invalid data produce FAIL; missing installed resources, I/O problems, and
internal failures produce ERROR. ERROR takes precedence over FAIL. PASS covers
only the supported structural rules, without establishing Quality Gate results.

The installed tool packages canonical Actor, Actor Availability Observation,
Actor-to-Runtime Applicability Evidence, Agent Runtime Option, Agent Runtime
Option Availability Observation, Runtime Operation Capability Observation,
Environment Operation Permission Observation, Agent Execution Authorization
Evidence, Assignment, Inference Option, Inference Option Availability
Observation, Runtime-to-Inference Compatibility Evidence, Role, Task, Workflow,
and Project Manifest schemas from their single sources in `schemas/`, plus the
five framework-owned canonical Role YAML instances from `roles/`.
Managed projects
need no schema regression scripts, fixtures, Orchestra Task history, Git,
Node/npm, or Python tests. Python and the declared tool dependencies run the
validator; the target project's own language is irrelevant. The API executes no
project commands and changes no files. No Actor catalog exists. No SKIP results
are emitted.

## Runtime Role Catalog

Canonical Role instances are machine-readable and package-owned:

```python
from engineering_orchestration.role_catalog import load_role_catalog

catalog = load_role_catalog()
role = catalog.get("software-engineer")
print(catalog.role_ids, role["required_capabilities"])
```

The catalog safe-loads and validates packaged `roles/*.yaml`, indexes by declared
Role `id` rather than filename, rejects duplicate IDs, and returns `None` for an
unknown lookup. It never searches CWD or a managed project's `roles/` directory.
The authority order is Role specification, Role schema, canonical Role YAML,
then non-authoritative Markdown compatibility stubs. The catalog does not select
or assign Actors, inspect availability, authorize execution, or evaluate Quality
Gates.

## Actor Competency Coverage

The framework defines a Provider-neutral Actor as a concrete Human or Agent
candidate with an ID, kind, and engineering competencies. The pure evaluator
compares already-normalized Actor competencies with Role requirements:

```python
from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.role_catalog import load_role_catalog

role = load_role_catalog().get("software-engineer")
coverage = evaluate_actor_role_coverage(actor, role)
print(coverage.compatible, coverage.missing_competencies)
```

Matching is exact and case-sensitive. A Role with empty required capabilities is
explicitly non-matchable. Coverage is evidence only: it does not rank, select,
assign, authorize, or execute an Actor; inspect availability; or produce a
Quality Gate result. The semantic contract is defined in
[`core/actor-specification.md`](core/actor-specification.md).

## Actor Availability Observation

Availability is a separate, ephemeral runtime observation over supplied Actors:

```python
from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
    validate_actor_availability,
)

observations = [
    ActorAvailabilityObservation("agent-engineer-1", AvailabilityState.AVAILABLE)
]
result = validate_actor_availability(observations, actors)
print(result.valid, result.normalized_observations)
```

Each observation contains only `actor_id` and `state`, where state is exactly
`available`, `unavailable`, or `unknown`. A known Actor without an observation
normalizes to unknown, never unavailable. Duplicate observations and unknown
Actor references invalidate the snapshot without producing partial normalized
output. Human and Agent Actors use identical semantics.

Availability does not change Actor identity or competency coverage, affect
Assignment validity, grant authority, or imply execution. The validator performs
no selection, persistence, Provider integration, polling, or network access. The
semantic contract is defined in
[`core/actor-availability-specification.md`](core/actor-availability-specification.md).

## Actor Selection

Actor Selection combines one resolved Task/Workflow/Stage/Role responsibility,
exact Actor competency coverage, and a caller-supplied availability snapshot:

```python
from engineering_orchestration.actor_selection import select_actor

result = select_actor(
    task,
    stage_id="implement",
    role_id="software-engineer",
    workflow_catalog=workflow_catalog,
    role_catalog=role_catalog,
    actors=actors,
    availability_observations=observations,
)
print(result.valid, result.outcome, result.selected_actor_id)
```

Valid outcomes are exactly `selected`, `ambiguous`, `indeterminate`, and
`no_candidate`. One eligible available Actor is selected only when no other
eligible Actor has unknown availability; available plus unknown is
`indeterminate`, while two available Actors are `ambiguous` even when another is
unknown. Actor-ID evidence is sorted for deterministic output, never preference
or ranking.

Selection is scoped to the supplied Actors and supplied snapshot. It creates no
Assignment and grants no authority, reservation, execution permission, or
Quality Gate result. A caller-built Assignment still requires AIO-023
validation. The semantic contract is
[`core/actor-selection-specification.md`](core/actor-selection-specification.md).

## Assignment Responsibility Bindings

An Assignment records one Actor selected outside the Assignment contract for one
required Task/Workflow/Stage/Role responsibility:

```python
from engineering_orchestration.assignment import (
    Assignment,
    validate_assignment_set,
)

binding = Assignment(
    task_id="AIO-023",
    workflow_id="architecture-change",
    stage_id="implement",
    role_id="software-engineer",
    actor_id="agent-engineer-1",
)
result = validate_assignment_set(
    [binding], task, workflow_catalog, role_catalog, actors
)
print(result.valid, result.complete, result.unassigned_requirements)
```

Validation checks exact Task and Workflow consistency, Stage and Role
requirements, unique supplied Actor identities, and existing competency coverage.
Sequence validation separately reports duplicate bindings, completeness,
unassigned requirements, and definite implementer/Reviewer Actor-ID conflicts.
It does not select Actors, inspect availability, persist values, grant authority,
execute work, manage Workflow state, or establish a Quality Gate result. The
semantic contract is
[`core/assignment-specification.md`](core/assignment-specification.md).

AIO-018 defines the optional Project Verification Check contract in
[`core/project-manifest.md`](core/project-manifest.md#33-verification--project-verification-checks),
at `.ai/project.yaml` → `verification.checks`. Declarations contain `id`, an
argument-array `command`, optional project-relative `cwd`, and optional positive
`timeout_seconds` (default `600`). Structural validation checks their shape and
ID uniqueness without executing them. Existing Manifests remain valid; omitted
checks mean zero declarations, with no automatic command discovery.

The contract has a programmatic planner, runner, and thin aggregate composition:

```python
from pathlib import Path
from engineering_orchestration.project_verification import (
    plan_project_checks,
    run_project_checks,
    verify_project,
)

planning = plan_project_checks(Path("/path/to/project"))
if planning.is_ready:
    evidence = run_project_checks(planning.plan)

aggregate = verify_project(Path("/path/to/project"))
```

Planning validates all declarations and resolved working directories before any
command runs. Execution is sequential, noninteractive, timeout-bounded, and
captures bounded stdout/stderr excerpts as PASS, FAIL, or ERROR evidence. Commands
use the caller's existing authority and inherited environment; declarations grant
no permission, promise no sandbox, and do not establish Quality Gate results.
Timeout or interruption cleanup covers the direct child only, not all descendants.
Only planning readiness gates project command execution, so unrelated Task or
Workflow structural findings remain reported without suppressing a valid plan.
Aggregate exit codes are 0 for PASS, 1 for FAIL without ERROR, 2 for any ERROR,
and 130 when the public CLI is interrupted by the user.
