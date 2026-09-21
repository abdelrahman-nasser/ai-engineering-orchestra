# AI Engineering Orchestra - Agent Execution Candidate Prerequisite Assessment Specification

Status: Canonical for AIO-034

Version: 0.1.0

Scope: One caller-designated external-inference Agent candidate

---

## 1. Purpose

Agent Execution Candidate Prerequisite Assessment is a pure, immutable,
deterministic, in-memory assessment of whether one caller-designated
external-inference Agent candidate satisfies all currently modeled hard
prerequisites in one caller-owned evaluation context.

The assessment composes only:

```text
valid Assignment
+ current assigned-Actor availability
+ exact supplied Actor-to-Runtime applicability
+ exact Runtime-to-Inference pair availability
```

It reports one of three ordinary outcomes for valid Agent-domain input:
`satisfied`, `blocked`, or `unresolved`.

The assessment does not prove that a candidate is selected, permitted,
authorized, reserved, executable now, or guaranteed to succeed. It performs no
execution.

---

## 2. Candidate and Identity

The assessment subject is exactly:

```text
Assignment + runtime_option_id + option_id
```

Its flattened identity is:

```text
task_id
workflow_id
stage_id
role_id
actor_id
runtime_option_id
option_id
```

The Assignment is the immutable responsibility anchor. Its responsibility key
provides `task_id`, `workflow_id`, `stage_id`, and `role_id`; its `actor_id`
identifies the already assigned Actor. The two caller-designated endpoint IDs
complete the assessment identity.

There is no `candidate_id`, Candidate entity, Candidate inventory, persistent
record, or lifecycle. The word *candidate* names only the subject of this one
assessment.

Actor Selection is not an input. The assessment neither selects nor replaces
the Actor and does not mutate or extend Assignment.

---

## 3. Public API

The canonical implementation is:

```text
engineering_orchestration.agent_execution_candidate_prerequisite
```

It defines:

```python
class AgentExecutionCandidatePrerequisiteOutcome(StrEnum):
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class AgentExecutionCandidatePrerequisiteReason(StrEnum):
    ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED = (
        "all_currently_modeled_prerequisites_satisfied"
    )
    ACTOR_UNAVAILABLE = "actor_unavailable"
    ACTOR_AVAILABILITY_UNKNOWN = "actor_availability_unknown"
    ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED = (
        "actor_runtime_applicability_not_supplied"
    )
    RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED = (
        "runtime_inference_compatibility_not_supplied"
    )
    AGENT_RUNTIME_OPTION_UNAVAILABLE = "agent_runtime_option_unavailable"
    AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN = (
        "agent_runtime_option_availability_unknown"
    )
    INFERENCE_OPTION_UNAVAILABLE = "inference_option_unavailable"
    INFERENCE_OPTION_AVAILABILITY_UNKNOWN = (
        "inference_option_availability_unknown"
    )
```

The immutable finding is:

```python
@dataclass(frozen=True)
class AgentExecutionCandidatePrerequisiteFinding:
    code: str
    message: str
```

The immutable result is:

```python
@dataclass(frozen=True)
class AgentExecutionCandidatePrerequisiteResult:
    valid: bool
    findings: tuple[AgentExecutionCandidatePrerequisiteFinding, ...]
    responsibility_key: tuple[str, str, str, str] | None
    actor_id: str | None
    runtime_option_id: str | None
    option_id: str | None
    outcome: AgentExecutionCandidatePrerequisiteOutcome | None
    reasons: tuple[AgentExecutionCandidatePrerequisiteReason, ...]
```

`responsibility_key`, `actor_id`, `runtime_option_id`, and `option_id` expose the
seven flattened identifiers without storing redundant individual responsibility
fields.

The public function is:

```python
assess_agent_execution_candidate_prerequisites(
    assignment,
    runtime_option_id,
    option_id,
    task,
    workflow_catalog,
    role_catalog,
    actors,
    actor_availability_observations,
    actor_runtime_applicability_evidence,
    runtime_options,
    inference_options,
    runtime_inference_compatibility_evidence,
    runtime_availability_observations,
    inference_availability_observations,
)
```

The function accepts raw domain inputs. It does not accept detached validation
results or a detached pair-assessment result as proof of a shared context.

---

## 4. Caller-Owned Evaluation Context

The caller owns the truth, freshness, and coherent collection timing of every
input. Core does not discover or refresh external facts.

The function captures every supplied iterable exactly once as a tuple, in this
public parameter order:

1. Actors;
2. Actor Availability Observations;
3. Actor-to-Runtime Applicability Evidence;
4. Agent Runtime Options;
5. Inference Options;
6. Runtime-to-Inference Compatibility Evidence;
7. Agent Runtime Option Availability Observations; and
8. Inference Option Availability Observations.

The same captured Actor tuple is reused for Assignment, Actor Availability, and
applicability validation. The same captured Runtime tuple is reused for
applicability and pair assessment. The same captured Inference tuple,
compatibility evidence, and endpoint observations are reused for pair assessment
and exact endpoint resolution.

This capture-and-reuse rule provides invocation-local coherence. It does not
assert that external facts were observed simultaneously. A `snapshot_id`,
fingerprint, timestamp, evaluation-context ID, or freshness expiry would label
data without proving its external simultaneity and is not part of this contract.

---

## 5. Validation Composition and Order

The assessment validates complete parent inputs in fixed dependency-aware order.
It never filters a parent relation or observation set to the target before
validation.

1. Validate Assignment with `validate_assignment`, the supplied Task, Workflow
   catalog, Role catalog, and captured Actor context.
2. Resolve the assigned Actor from the now-valid unique Actor context. Route a
   Human Assignment through the boundary in section 6.
3. Validate and normalize Actor availability with
   `validate_actor_availability` against the same Actor context.
4. Validate the complete Actor-to-Runtime relation with
   `validate_actor_runtime_applicability` against the same Actor and Runtime
   contexts.
5. Assess the complete Runtime-to-Inference relation with
   `assess_runtime_inference_pair_availability`, using the same Runtime and
   Inference inventories, compatibility evidence, and endpoint observations.
6. After all parents are valid, resolve the caller-designated Runtime and
   Inference IDs exactly and case-sensitively in their captured inventories.
7. Join the exact applicability and pair edges and derive reasons and outcome.

Each invalid phase short-circuits later validation. A malformed unrelated edge
or observation still invalidates its complete parent input under that parent's
existing atomic contract.

Framework catalog failures retain the exception behavior of Assignment
validation. They are not converted into ordinary consumer-data findings.

---

## 6. Human Assignment Boundary

A valid Assignment naming a Human Actor is outside this Agent-only assessment.
The function returns an atomic result with `valid: false`, no identity, no
outcome, no reasons, and exactly this boundary finding:

```text
agent_execution_candidate_not_applicable_to_human_actor
```

The message identifies the Human Actor and states that Agent Execution
Candidate Prerequisite Assessment does not apply to Human Assignments.

This result invalidates only the attempted assessment invocation. It does not
invalidate the Human Actor or Assignment, describe either as blocked, imply
missing Runtime or Inference configuration, or change the Human responsibility
path. Actor availability, applicability, and pair validation do not run after
this boundary is identified.

---

## 7. Explicit Endpoint Resolution

`runtime_option_id` and `option_id` are required, non-optional, explicit
references. Each must exist exactly and case-sensitively in its supplied
inventory.

An unknown Runtime produces:

```text
agent_runtime_option_not_found
```

An unknown Inference Option produces:

```text
inference_option_not_found
```

If both are unknown, the Runtime finding precedes the Inference finding. These
are invalid candidate inputs, not ordinary blocked or unresolved facts.

The assessment does not enumerate a Cartesian product, construct a candidate,
or select an endpoint. Multiple explicit candidates may be assessed through
separate calls, and more than one may independently be `satisfied`.

---

## 8. Exact Joins

All joins use exact, case-sensitive identifiers:

```text
assignment.actor_id == applicability.actor_id
runtime_option_id == applicability.runtime_option_id
runtime_option_id == pair.runtime_option_id
option_id == pair.option_id
```

The assessment does not join by Provider ID, model ID, Runtime vendor, Actor
name, string parsing, prefix, normalization, or inference.

Actor-to-Runtime applicability plus Runtime-to-Inference compatibility does not
create a canonical transitive Actor-to-Inference applicability relation.

---

## 9. Ordinary Outcomes

Ordinary outcomes exist only when every parent input is valid, both explicit
endpoints exist, and the assigned Actor is an Agent.

### `satisfied`

The assigned Actor is available, the exact Actor-to-Runtime applicability edge
is supplied, and the exact Runtime-to-Inference pair is established because
both endpoints are available.

`satisfied` means only that every hard prerequisite currently modeled by this
contract is positive. It does not mean selected, preferred, permitted,
authorized, reserved, tool-capable, executable now, executing, or guaranteed to
succeed.

### `blocked`

At least one currently modeled prerequisite contains explicit current negative
evidence: the assigned Actor, candidate Runtime, or candidate Inference Option
is unavailable.

Blocked candidate state does not invalidate or mutate Assignment.

### `unresolved`

No modeled prerequisite explicitly blocks the candidate, but at least one
required positive fact is absent or unknown. Examples include unknown Actor or
endpoint availability, a missing applicability edge, or a missing compatibility
edge.

---

## 10. Outcome Reasons and Precedence

Reasons explain a valid ordinary outcome. They are not validation findings.

Reason order is fixed:

1. assigned Actor availability;
2. missing exact Actor-to-Runtime applicability; and
3. Runtime-to-Inference compatibility or exact pair endpoint states, with
   Runtime before Inference.

The derivation is:

- assigned Actor unavailable: `actor_unavailable`;
- assigned Actor unknown: `actor_availability_unknown`;
- exact applicability edge absent:
  `actor_runtime_applicability_not_supplied`;
- exact compatibility edge absent:
  `runtime_inference_compatibility_not_supplied`;
- exact Runtime endpoint unavailable:
  `agent_runtime_option_unavailable`;
- exact Runtime endpoint unknown:
  `agent_runtime_option_availability_unknown`;
- exact Inference endpoint unavailable: `inference_option_unavailable`; and
- exact Inference endpoint unknown:
  `inference_option_availability_unknown`.

Outcome precedence is:

```text
any unavailable reason
-> blocked

otherwise, any unknown or missing-positive-evidence reason
-> unresolved

otherwise
-> satisfied
```

All applicable negative and unresolved reasons remain present even when a
blocking reason determines the outcome. A satisfied result contains exactly:

```text
all_currently_modeled_prerequisites_satisfied
```

---

## 11. Missing Evidence Semantics

Absence is not negative evidence.

A missing exact Actor-to-Runtime edge means only that no positive applicability
evidence was supplied. It contributes `unresolved` and never means incompatible,
unavailable, prohibited, or blocked.

A missing exact Runtime-to-Inference edge produces no pair assessment for that
edge. It contributes `unresolved` and never causes a pair to be synthesized.

A missing Actor Availability Observation continues to normalize to `unknown`
through the existing Actor Availability contract. Missing Runtime or Inference
availability observations on a supplied compatibility edge likewise retain the
pair assessor's existing normalized unknown semantics.

---

## 12. Result Atomicity

An invalid result has:

```text
valid = false
findings != ()
responsibility_key = None
actor_id = None
runtime_option_id = None
option_id = None
outcome = None
reasons = ()
```

A valid result has:

```text
valid = true
findings = ()
all identity fields populated
outcome in {satisfied, blocked, unresolved}
reasons != ()
```

Parent findings retain their existing codes, messages, and deterministic order.
The top-level finding type copies them without changing their meaning. Invalid
input never becomes an ordinary outcome, and no partial candidate identity or
evidence is published.

---

## 13. External-Inference Boundary

The assessment requires one known `option_id` and therefore covers only the
existing external-inference path.

Runtime-owned or hidden inference is outside this API. The absence of an
external pair does not establish that a Runtime-owned path is blocked or
non-executable. The assessment does not introduce `None`, an empty or wildcard
option, a synthetic Inference Option, a Runtime-only outcome, or an inference
ownership discriminator.

---

## 14. Authority and Execution Boundaries

The following inequalities are mandatory:

```text
satisfied
!= selected
!= permitted
!= authorized
!= reserved
!= executable
!= executing
```

Human Control, platform and sandbox permissions, credentials, policy, tool
access, runtime capabilities, context windows, quota, cost, and execution
authorization remain separate facts.

Agent Execution Authorization Evidence is a separate caller-attested assertion
about one exact assigned external-inference Agent action. A `satisfied`
assessment neither creates nor implies `granted` evidence, and supplied
authorization evidence does not satisfy missing candidate prerequisites. Its
contract is defined in
`core/agent-execution-authorization-evidence-specification.md`.

Agent Action Prerequisite Assessment may consume one exact coherent AIO-034
result as its candidate layer without recomputing Actor availability,
applicability, compatibility, or endpoint availability. Its action-level
diagnostic composition is defined in
`core/agent-action-prerequisite-specification.md` and does not change AIO-034
outcomes or authority boundaries.

Execution Mode is Task/process governance depth. It is not an assessment input
and creates no Runtime support, model-strength, reasoning-tier, permission, or
authority inference.

The assessment does not define an Execution Contract, adapter request,
reservation, dispatch, invocation, execution session, or result.

---

## 15. Purity, Persistence, and Structural Authority

The implementation is a pure function over supplied in-memory values. It
performs no filesystem access, network access, subprocess invocation, clock
read, polling, discovery, registry or cache mutation, persistence, or global
mutable-state work. It does not mutate caller inputs.

The assessment is derived evidence, not a serialized entity or request
contract. AIO-034 therefore introduces no JSON Schema, schema fixture, schema
resource, Project Manifest field, storage location, or new package dependency.

This specification is the authoritative semantic contract. The Python module
is the runtime contract. No serialized structural contract exists.

---

## 16. Exclusions

AIO-034 does not add:

- Actor Selection input or candidate discovery;
- Assignment mutation, reassignment, replacement, or refresh;
- Candidate identity, inventory, persistence, or lifecycle beyond the seven
  existing exact identifiers;
- Actor-to-Inference applicability or transitive entitlement;
- Runtime-owned or hidden-inference representation;
- Execution Mode, model-strength, or reasoning-tier fit;
- tool, MCP, filesystem, shell, network, capability, or context-window fit;
- permissions, credentials, Human approval state, policy satisfaction, or
  execution authorization;
- selection, ranking, scoring, preference, routing, fallback, or a winner;
- reservation, Execution Contract, adapter, dispatch, execution, or invocation;
  or
- a schema, CLI behavior, persistent store, external discovery, or new
  dependency.

Any such capability requires separately authorized future design work.
