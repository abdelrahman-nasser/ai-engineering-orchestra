# AI Engineering Orchestra - Agent Action Prerequisite Assessment Specification

Status: Canonical for AIO-040

Version: 0.1.0

Scope: One exact assigned external-inference Agent action

---

## 1. Purpose and Category

Agent Action Prerequisite Assessment is an immutable, pure, deterministic,
ephemeral, in-memory diagnostic assessment describing whether all currently
modeled prerequisite facts for one exact assigned external-inference Agent
action are positively satisfied, explicitly blocking, or unresolved within
one caller-owned evaluation snapshot.

The assessment composes only:

```text
one coherent AIO-034 candidate prerequisite result
+ one valid AIO-036 Operation Requirement
+ one coherent AIO-037 capability validation result
+ one coherent AIO-038 permission validation result
+ one coherent AIO-039 authorization validation result
+ one exact evaluation environment identifier
```

It is derived diagnostic evidence. It is not caller-supplied evidence, a
Permission Decision, Grant, execution authorization issued by Core, Execution
Contract, or Execution Run. It performs no enforcement or execution.

The following inequalities are mandatory:

```text
prerequisites satisfied
!= execution ready
!= Core authorization
!= authenticated authority
!= Execution Contract
!= tool binding
!= dispatchable
!= invocation allowed
!= execution success
```

---

## 2. Exact Action Subject

The assessment subject is exactly the existing AIO-039 action subject:

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

AIO-034 supplies the first seven subject parts through its responsibility key,
Actor, Runtime Option, and external Inference Option fields. AIO-040 adds only
the supplied environment identifier and the validated Operation Requirement's
operation and resource.

Every part is exact and case-sensitive. Core does not trim, case-fold, alias,
resolve, or rewrite it. There is no Assessment value, Environment entity,
`assessment_id`, `action_id`, `candidate_id`, `execution_id`, or `run_id`.

The subject remains external-inference-only. A nonempty exact `option_id` is
required by the coherent AIO-034 result. Runtime-owned or hidden inference is
outside this contract.

---

## 3. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_action_prerequisite
```

It defines:

```python
class AgentActionPrerequisiteOutcome(StrEnum):
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class AgentActionPrerequisiteReason(StrEnum):
    CANDIDATE_PREREQUISITES_BLOCKED = "candidate_prerequisites_blocked"
    CANDIDATE_PREREQUISITES_UNRESOLVED = "candidate_prerequisites_unresolved"
    RUNTIME_OPERATION_CAPABILITY_ABSENT = (
        "runtime_operation_capability_absent"
    )
    RUNTIME_OPERATION_CAPABILITY_UNKNOWN = (
        "runtime_operation_capability_unknown"
    )
    ENVIRONMENT_OPERATION_PERMISSION_DENIED = (
        "environment_operation_permission_denied"
    )
    ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN = (
        "environment_operation_permission_unknown"
    )
    AGENT_EXECUTION_AUTHORIZATION_DENIED = (
        "agent_execution_authorization_denied"
    )
    AGENT_EXECUTION_AUTHORIZATION_MISSING = (
        "agent_execution_authorization_missing"
    )
    ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED = (
        "all_currently_modeled_action_prerequisites_satisfied"
    )
```

The immutable finding and result are:

```python
@dataclass(frozen=True)
class AgentActionPrerequisiteFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentActionPrerequisiteResult:
    valid: bool
    findings: tuple[AgentActionPrerequisiteFinding, ...]
    responsibility_key: tuple[str, str, str, str] | None
    actor_id: str | None
    runtime_option_id: str | None
    option_id: str | None
    environment_id: str | None
    operation_id: str | None
    resource: str | None
    outcome: AgentActionPrerequisiteOutcome | None
    reasons: tuple[AgentActionPrerequisiteReason, ...]
```

`responsibility_key` preserves AIO-034's representation while the remaining
fields expose the complete ten-part subject without duplicating the four
responsibility-key fields.

The exact public function is:

```python
assess_agent_action_prerequisites(
    candidate_result: AgentExecutionCandidatePrerequisiteResult,
    requirement: OperationRequirement,
    capability_result: RuntimeOperationCapabilityValidationResult,
    permission_result: EnvironmentOperationPermissionValidationResult,
    authorization_result: AgentExecutionAuthorizationValidationResult,
    *,
    environment_id: str,
) -> AgentActionPrerequisiteResult
```

The package root does not re-export these names. There is no redundant
`AgentActionPrerequisiteAssessment` value or public lookup helper.

---

## 4. Validated-Result Input Boundary

The public API accepts the AIO-034, AIO-037, AIO-038, and AIO-039 result
containers rather than their raw inputs. It does not accept raw capability,
permission, or authorization collections and does not recompute their
validators.

The one supplied Operation Requirement is different: AIO-040 validates it
internally with `validate_operation_requirement`. A malformed requirement is
invalid invocation input, not an uncertain prerequisite.

`environment_id` must be an exact nonempty opaque string. It binds the
permission and authorization lookups to one evaluation environment but does
not create an Environment entity or establish snapshot freshness.

Inputs are not mutated. The caller owns their truth, collection timing,
freshness, shared-context coherence, and continued currency.

### Publicly constructible result containers

Parent result dataclasses are frozen but publicly constructible. AIO-040 must
therefore check their exact observable canonical invariants rather than trust a
`valid` flag alone.

Every parent-result check requires:

- the exact result class, not a subclass;
- an exact `bool` validity flag;
- exact tuple containers;
- exact parent finding and payload value classes;
- nonempty exact-string finding codes and messages;
- a coherent invalid result with nonempty findings and an atomically empty
  payload; or
- a coherent valid result with no findings and a canonically shaped payload.

Malformed containers receive one AIO-040-owned incoherence finding. Their
contained findings are not trusted or copied. A coherent invalid parent's
finding codes, messages, and order are copied unchanged into AIO-040 findings.

Candidate valid-result coherence additionally requires an exact four-part
nonempty-string responsibility key; exact nonempty Actor, Runtime, and
Inference identifiers; exact AIO-034 outcome and reason enum members; unique
reasons in AIO-034 canonical order; and outcome/reason consistency. Blocked,
unresolved, and satisfied reason categories may not be combined incoherently.

Capability valid-result coherence additionally requires exact well-formed
observations, exact supported operation identifiers, exact capability states,
unique canonically sorted Runtime/operation identities, and complete supported
operation coverage for each Runtime represented by the normalized tuple.

Permission valid-result coherence additionally requires exact well-formed
observations, canonical operation/resource values, exact permission states,
unique canonically sorted four-part identities, and at most one represented
environment scope.

Authorization valid-result coherence additionally requires exact well-formed
evidence and enum values, canonical operation/resource values, nonempty
identity, authority, and provenance strings, unique canonically sorted
ten-part subjects, and at most one represented environment scope.

These checks establish observable structural and semantic output coherence.
They cannot prove that a value was actually returned by its validator,
reconstruct omitted inventories or catalogs, authenticate authority or
provenance, establish freshness, or prove that separately validated inputs
were observed simultaneously. Stronger provenance requires a different parent
API and is outside AIO-040. This limitation is one reason `satisfied` remains
non-authoritative.

---

## 5. Validation and Finding Order

Available diagnostics are aggregated in this fixed category order:

1. candidate result;
2. Operation Requirement;
3. environment identifier;
4. capability result;
5. permission result;
6. authorization result; and
7. cross-input coherence:
   1. missing required capability pair;
   2. permission environment mismatch;
   3. authorization environment mismatch.

A cross-input comparison runs only when every input required by that comparison
is coherently valid. Parent findings remain in their original order within
their category.

The fixed AIO-040 finding codes are:

```text
agent_action_prerequisite_candidate_result_invalid_type
agent_action_prerequisite_candidate_result_incoherent
agent_action_prerequisite_environment_id_invalid
agent_action_prerequisite_capability_result_invalid_type
agent_action_prerequisite_capability_result_incoherent
agent_action_prerequisite_permission_result_invalid_type
agent_action_prerequisite_permission_result_incoherent
agent_action_prerequisite_authorization_result_invalid_type
agent_action_prerequisite_authorization_result_incoherent
agent_action_prerequisite_capability_pair_missing
agent_action_prerequisite_permission_environment_mismatch
agent_action_prerequisite_authorization_environment_mismatch
```

The exact fixed type, coherence, and environment messages are:

```text
candidate_result must be an exact AgentExecutionCandidatePrerequisiteResult value.
candidate_result does not satisfy canonical AgentExecutionCandidatePrerequisiteResult invariants.
Agent Action Prerequisite Assessment environment_id must be an exact nonempty string.
capability_result must be an exact RuntimeOperationCapabilityValidationResult value.
capability_result does not satisfy canonical RuntimeOperationCapabilityValidationResult invariants.
permission_result must be an exact EnvironmentOperationPermissionValidationResult value.
permission_result does not satisfy canonical EnvironmentOperationPermissionValidationResult invariants.
authorization_result must be an exact AgentExecutionAuthorizationValidationResult value.
authorization_result does not satisfy canonical AgentExecutionAuthorizationValidationResult invariants.
```

Cross-input messages identify the exact required Runtime/operation pair or the
represented and assessment environment identifiers. Mixed environment scopes
make a parent payload incoherent. A nonempty coherent permission or
authorization result representing one different environment produces the
corresponding cross-input mismatch finding. An empty valid result carries no
represented environment, remains coherent, and contributes missing semantics
rather than claiming an environment match.

Any finding makes the complete AIO-040 result invalid. Findings never become
ordinary outcome reasons.

---

## 6. Exact Private Lookups

After validation, AIO-040 performs three private, exact, case-sensitive
lookups. It adds no lookup API to a parent module.

Capability identity:

```text
(candidate.runtime_option_id, requirement.operation_id)
```

The AIO-037 normalized output is complete for every represented Runtime and
supported operation. A missing required pair is therefore invalid
cross-context input, not synthesized `unknown`.

Permission identity:

```text
(
  candidate.runtime_option_id,
  environment_id,
  requirement.operation_id,
  requirement.resource,
)
```

A missing exact permission observation means semantically unknown. AIO-040
does not synthesize an observation.

Authorization identity:

```text
(
  *candidate.responsibility_key,
  candidate.actor_id,
  candidate.runtime_option_id,
  candidate.option_id,
  environment_id,
  requirement.operation_id,
  requirement.resource,
)
```

A missing exact evidence value means authorization is missing and unproven. It
is not denied or granted, and AIO-040 does not synthesize evidence.

---

## 7. Ordinary Outcomes

Ordinary outcomes exist only for coherent valid parent results, a valid
requirement and environment identifier, and coherent exact input scopes.

### `satisfied`

All four prerequisite categories are positive:

```text
candidate = satisfied
capability = present
permission = allowed
authorization = granted
```

It means only that all currently modeled caller-supplied prerequisites for the
exact action are positive.

### `blocked`

At least one explicit negative prerequisite exists. The blockers are exactly:

```text
candidate = blocked
capability = absent
permission = denied
authorization = denied
```

### `unresolved`

No blocker exists, but at least one required prerequisite is uncertain or
missing. The uncertainties are exactly:

```text
candidate = unresolved
capability = unknown
permission = unknown or missing
authorization = missing
```

Outcome precedence is:

```text
blocked > unresolved > satisfied
```

This is diagnostic aggregation, not Permission Decision precedence,
authorization conflict resolution, or a stricter-wins policy.

---

## 8. Reasons and Ordering

The exact reason vocabulary and declaration order is:

```text
candidate_prerequisites_blocked
candidate_prerequisites_unresolved
runtime_operation_capability_absent
runtime_operation_capability_unknown
environment_operation_permission_denied
environment_operation_permission_unknown
agent_execution_authorization_denied
agent_execution_authorization_missing
all_currently_modeled_action_prerequisites_satisfied
```

Ordinary output reason order is candidate, capability, permission, then
authorization. Each category contributes at most one reason. A blocker controls
the outcome but does not remove applicable uncertainty reasons. For example:

```text
capability = absent
permission = unknown
authorization = missing

-> outcome = blocked
-> reasons = (
     runtime_operation_capability_absent,
     environment_operation_permission_unknown,
     agent_execution_authorization_missing,
   )
```

When no negative or uncertain reason exists, the result is satisfied and its
reasons contain only:

```text
all_currently_modeled_action_prerequisites_satisfied
```

---

## 9. Atomic Result Behavior

An invalid result is exactly:

```text
valid = false
findings != ()
responsibility_key = None
actor_id = None
runtime_option_id = None
option_id = None
environment_id = None
operation_id = None
resource = None
outcome = None
reasons = ()
```

Invalid input is neither blocked nor unresolved. No partial action identity or
ordinary reason survives invalid invocation.

A valid result is exactly:

```text
valid = true
findings = ()
all ten subject parts represented
outcome in {satisfied, blocked, unresolved}
reasons != ()
```

All values and result containers are frozen and tuple-backed. Repeated calls
over the same values return equal results.

---

## 10. Human and External-Inference Boundaries

A canonical AIO-034 Human-boundary result is a coherent invalid parent result.
AIO-040 copies its existing finding unchanged, including:

```text
agent_execution_candidate_not_applicable_to_human_actor
```

It returns no action identity, outcome, or reasons. This describes only the
Agent-only assessment boundary; it does not invalidate Human execution or the
Human responsibility path.

AIO-040 intentionally does not receive raw Actor context and cannot rediscover
Actor kind. It relies on AIO-034's canonical boundary. Likewise, AIO-034's
required exact external `option_id` preserves the external-inference boundary.
AIO-040 does not add a nullable, empty, wildcard, or Runtime-owned inference
path.

---

## 11. Authorization and Security Boundary

AIO-039 `granted` remains a caller-attested, unauthenticated assertion. AIO-040
does not authenticate `authority_id`, verify or dereference
`provenance_reference`, infer evidence from Task approval or Human Control, or
issue authority.

The assessment is diagnostically default-deny for any possible future consumer:

```text
blocked -> cannot support future execution
unresolved -> cannot support future execution
invalid -> cannot support future execution
satisfied -> necessary modeled prerequisite evidence only
```

AIO-040 itself consumes no authorization and enforces nothing. A future
execution consumer would require separately authorized authenticated,
run-bound, freshness-aware authority and must not treat this assessment as a
grant.

Permission Decision values such as `allow`, `ask`, `always-ask`, and `deny` are
not inputs. There is no policy evaluation, conflict winner, or Task-approval-
to-authorization mapping.

---

## 12. Purity, Packaging, and Structural Authority

The implementation is a pure function over supplied in-memory values. It does
not access a filesystem or resource, inspect a protected target, discover the
environment, read a clock, use a network or subprocess, query a database or
cache, contact an authority or policy service, mutate permission or
authorization state, bind a tool, dispatch, or invoke anything.

The assessment is derived, ephemeral, in-memory evidence. AIO-040 adds no JSON
Schema, schema fixture, schema resource, Project Manifest field, serialized
request, persistence, registry, or external dependency.

Source checkout, editable installation, and normal wheel installation expose
the same direct submodule API without source fallback. The package root remains
unchanged.

This specification is the semantic authority. The Python module is the runtime
contract. No serialized structural contract exists.

---

## 13. Adjacent Contract Preservation

AIO-040 sits above and does not modify the meaning or public API of:

- AIO-034 Agent Execution Candidate Prerequisite Assessment;
- AIO-036 Operation Requirement;
- AIO-037 Runtime Operation Capability Observation;
- AIO-038 Environment Operation Permission Observation; or
- AIO-039 Agent Execution Authorization Evidence.

In particular, it does not recompute Actor availability, Actor-to-Runtime
applicability, Runtime-to-Inference compatibility, Runtime availability, or
Inference availability. Invalid capability, permission, and authorization
results remain invalid; AIO-040 does not reinterpret conflicts or malformed
snapshots as blocked, denied, missing, or unknown.

---

## 14. Exclusions

AIO-040 adds no:

- schema, persistence, stored assessment, registry, or lifecycle;
- synthetic assessment, action, candidate, execution, or run identity;
- Runtime-owned inference representation;
- Permission Decision evaluation or policy composition;
- authenticated authority, authority issuance, entitlement, signature
  verification, provenance dereferencing, or Task-approval inference;
- authorization consumption, nonce, used flag, replay protection, revocation,
  expiry, freshness, or clock behavior;
- permission or authorization mutation, enforcement, ACL or sandbox mutation,
  process interception, or command blocking;
- concrete tool binding, Provider or Runtime adapter, CLI, Execution Contract,
  Execution Run, request payload, dispatch, execution, invocation, result
  capture, or telemetry;
- protected-target, VS Code, Control Center, dashboard, frontend, or Full UI
  behavior; or
- AIO-030 or AIO-041 work.

Any future trusted authorization, execution, run-binding, consumption,
revocation, enforcement, or invocation contract requires separate explicit
authorization.
