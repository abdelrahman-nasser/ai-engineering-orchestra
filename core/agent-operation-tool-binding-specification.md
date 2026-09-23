# AI Engineering Orchestra - Agent Operation Tool Binding Specification

Status: Canonical for AIO-045

Version: 0.1.0

Scope: Pure binding of one exact Agent Execution Run to one exact immutable
configured Tool implementation identity

---

## 1. Purpose and Category

An **Agent Operation Tool Binding** is an immutable, serializable,
provider-neutral value binding one exact complete Agent Execution Run to one
exact immutable configured Tool implementation identity supplied by an
external trusted resolver, without granting authority, widening the Run
Contract, performing discovery, consuming authorization, admitting dispatch,
or invoking the Tool.

Its concept category is:

```text
Immutable selected implementation-binding value
```

It is derived or selected in the limited sense that an external resolver
chooses the configured implementation and supplies the resulting value. Core
does not perform that selection. The value is not a decision, permission,
authority artifact, Grant, lifecycle state, admission, or invocation.

The following inequalities are mandatory:

```text
Tool Binding exists != Runtime capability present
Tool Binding exists != Tool existence proven by Core
Tool Binding exists != Tool availability proven by Core
Tool Binding exists != permission allowed
Tool Binding exists != Grant valid or current
Tool Binding exists != authorization consumed
Tool Binding exists != dispatch admitted
Tool Binding exists != invocation allowed or performed
```

Tool Binding must precede any future single-use authorization consumption.
Authority must not be spent until the consumer has one exact implementation
identity to admit, and a later dispatcher must not substitute another
implementation after admission. AIO-045 defines only the pure value needed for
that ordering. It consumes no authority and implements no admission.

---

## 2. Canonical Value and Exact Field Order

`AgentOperationToolBinding` contains exactly these fields, in this order:

| Field | Required | Meaning |
| --- | --- | --- |
| `run` | Yes | Exact complete nested `AgentExecutionRun` |
| `tool_id` | Yes | Exact immutable configured Tool implementation identity |

No field is inferred, normalized, flattened, generated, or silently added.
In particular, the value has no `binding_id`, separate `run_id`, Task,
Workflow, Stage, Role, Actor, Runtime Option, Inference Option, environment,
operation, resource, Execution Mode, adapter, Provider, model, endpoint,
command, payload, argument, credential, Grant, status, timestamp, result, or
metadata field.

Full dataclass equality over `(run, tool_id)` defines Tool Binding value
equality. There is no separate Tool Binding identity or `binding_id`. The
configured implementation identity is `tool_id`; the action and occurrence
identity are retained by the complete nested Run.

---

## 3. Complete Run Binding

`run` is the exact nested AIO-042 `AgentExecutionRun`, not a bare `run_id`,
hash, reference, or copied subset. It transitively binds:

- Run ID;
- Task, Workflow, and Stage;
- Role and Actor;
- Runtime Option and Inference Option;
- environment, operation, and exact lexical repository resource; and
- the already-resolved Task-wide Execution Mode.

A bare Run ID is insufficient because AIO-042 does not prove global Run-ID
uniqueness, and equal Run IDs can be rebound to differing Contracts in an
untrusted namespace. The complete immutable Run is necessary to compare the
entire intended action at a future admission boundary.

Intrinsic validation delegates the nested value directly to
`validate_agent_execution_run`. Every Run finding is converted to an
`AgentOperationToolBindingFinding` while preserving its exact code, message,
multiplicity, and order. AIO-045 does not duplicate Run or Contract validation.

---

## 4. Tool Identity and Immutable-Revision Model

`tool_id` is an exact, opaque, case-sensitive, nonempty string. Core does not
trim, normalize, case-fold, parse, prefix, resolve, allocate, generate, or
rewrite it. Consequently, every exact nonempty string, including a
whitespace-containing or whitespace-only string, satisfies the intrinsic
string rule. The external resolver remains responsible for supplying a useful
canonical identity.

AIO-045 locks **Model A**: `tool_id` itself denotes one immutable,
version-stable configured callable implementation revision. No separate
revision field is added. A conceptual value such as
`tool::synthetic-repository-reader::v1` may make revision stability visible,
but Core imposes no textual prefix or version grammar.

A mutable alias, display name, capability name, operation ID, adapter ID,
Provider name, command, or endpoint is not a canonical `tool_id` unless the
resolver guarantees that the identity can never be rebound to another
configured implementation. If a native system exposes only a mutable alias,
the resolver must derive or allocate a stable opaque revision identity outside
Core before constructing this value.

Therefore:

```text
tool_id accepted by intrinsic validation
!= immutable identity guarantee proven by Core
!= configured Tool existence proven
```

The resolver's integrity and stable-identity guarantee are external
preconditions, not fields that can be self-attested inside the binding.

---

## 5. Namespace and Ownership

Core does not allocate Tool IDs and does not claim global Tool-ID uniqueness.
The external configured Runtime/Tool resolver owns:

- the Tool-ID namespace;
- configured Tool existence;
- immutable identity and revision stability;
- applicability to the exact Runtime Option and environment;
- semantic applicability to the exact operation and resource; and
- selection of one effective configured implementation for the Run.

The namespace is scoped by the exact
`binding.run.contract.runtime_option_id` and
`binding.run.contract.environment_id`. Equal lexical Tool IDs in differing
Runtime or environment contexts need not identify the same implementation.
Those scope values are not copied into the binding because the complete Run
already contains them.

The future adapter owns:

- physical resolution of the immutable Tool identity;
- credentials and secrets;
- endpoints and protocols;
- provider- or Runtime-native parameters and translation;
- physical containment and native permission enforcement; and
- actual invocation.

Neither resolver responsibilities nor adapter responsibilities become Core
facts merely because a directly constructed binding is intrinsically valid.

---

## 6. Capability, Resolution, and Discovery Boundary

AIO-037 Runtime Operation Capability is abstract support evidence. Even the
state `present` does not identify or select a configured Tool:

```text
Runtime Operation Capability = present
!= concrete Agent Operation Tool Binding exists
```

Core does not derive `tool_id` from capability evidence and does not implement
a preparation API that would pretend to resolve a Tool. The binding is supplied
after external resolver selection and is subject only to intrinsic validation.

Core performs no Tool inventory, filesystem or `PATH` inspection, binary scan,
MCP enumeration, Provider or Runtime query, network lookup, configuration
probe, availability probe, ranking, fallback, retry, or dynamic reselection.
If the selected Tool becomes unavailable, AIO-045 supplies no alternative.

---

## 7. Non-Widening Semantics

The binding carries the complete Run unchanged and has no alternate scope
field. It therefore cannot represent a second Runtime, Inference Option,
environment, operation, resource, Execution Mode, Actor, or Role alongside the
Run. Changing any such value requires constructing a different nested Run and
therefore a different complete Tool Binding value.

The following substitutions are prohibited:

```text
Runtime fallback or substitution
Inference Option or Provider/model substitution
environment fallback or substitution
operation substitution
resource replacement or widening
Execution Mode substitution
Actor or Role substitution
```

For example, a Run for `repository_file_read` on
`synthetic/input.txt` cannot gain `repository_write`, `shell_execute`, a
repository-root resource, `*`, or another resource through the binding. There
is deliberately no separate operation or resource field in which to express
that wider scope.

This is a structural non-widening guarantee, not Tool-behavior attestation.
Core does not inspect executable behavior and cannot prove that the
implementation named by `tool_id` actually implements only the Run operation
or honors its resource. The trusted resolver must select a semantically
applicable non-widening implementation, and the future adapter or native
enforcement boundary must contain actual execution. If that trust cannot be
established, the binding must not progress to authorization consumption or
admission.

Any future admission comparison must require exact complete equality:

```text
binding.run == grant.run == freshly prepared expected Run
```

No field-by-field fallback, projection, aliasing, or partial match is allowed.

---

## 8. Cardinality and Selection

The current Run represents one action. AIO-045 therefore defines one selected
effective Tool Binding per Run for future admission. It does not define
multi-Tool composition, alternatives, fallback order, weighted choice, or a
Tool Binding collection.

The single-value validator cannot observe other bindings and does not enforce
cross-value cardinality. If multiple candidate bindings are supplied outside
this API, a future authoritative admission boundary must reject ambiguity and
admit exactly one immutable binding. AIO-045 does not select a winner,
deduplicate values, or create an inventory.

---

## 9. Public API

The canonical direct-import module is:

```text
engineering_orchestration.agent_operation_tool_binding
```

It defines these frozen public values:

```python
@dataclass(frozen=True)
class AgentOperationToolBinding:
    run: AgentExecutionRun
    tool_id: str


@dataclass(frozen=True)
class AgentOperationToolBindingFinding:
    code: str
    message: str


@dataclass(frozen=True)
class AgentOperationToolBindingValidationResult:
    valid: bool
    findings: tuple[AgentOperationToolBindingFinding, ...]
    binding: AgentOperationToolBinding | None
```

The only public function is:

```python
validate_agent_operation_tool_binding(
    binding: AgentOperationToolBinding,
) -> AgentOperationToolBindingValidationResult
```

There is no preparation, selection, resolution, collection, serialization,
lookup, registry, availability, currentness, fallback, admission, dispatch, or
invocation API. The package root does not re-export these names.

---

## 10. Intrinsic Validation

A wrong top-level concrete type stops validation with exactly:

```text
agent_operation_tool_binding_invalid_type
Agent Operation Tool Binding must be an exact AgentOperationToolBinding value.
```

For an exact binding, findings aggregate in declaration order:

1. exact nested Agent Execution Run intrinsic findings; and
2. exact nonempty `tool_id`.

An invalid Tool ID produces:

```text
agent_operation_tool_binding_tool_id_invalid
Agent Operation Tool Binding tool_id must be an exact nonempty string.
```

Nested Run findings retain their exact codes, messages, multiplicity, and
order. Validation performs no normalization and success preserves the exact
supplied binding object.

Intrinsic validation proves only:

- the exact concrete Tool Binding type;
- current intrinsic validity of the complete nested Run;
- the exact nonempty string shape of `tool_id`; and
- atomic value semantics.

It does not prove:

- external resolver provenance or trust;
- configured Tool existence, availability, or executability;
- immutable revision integrity outside the supplied lexical identity;
- semantic applicability to the operation or resource;
- native permission or containment;
- current prerequisites, authority, Grant validity, or Grant currentness;
- authorization consumption, replay protection, or admission; or
- dispatch, invocation, result, or success.

Direct construction is intentional. An intrinsically valid directly
constructed, copied, or deserialized value has no resolver provenance by
itself.

---

## 11. Atomicity, Immutability, and Purity

All three public values are frozen dataclasses and findings are tuples. Inputs,
the nested Run, and its Contract are not mutated.

A valid result is exactly:

```text
valid = true
findings = ()
binding = the exact validated AgentOperationToolBinding
```

An invalid result is exactly:

```text
valid = false
findings != ()
binding = null
```

There is no partial or normalized Tool Binding. Validation is a deterministic
pure function over the supplied value. It performs no filesystem or
protected-target access, network access, subprocess invocation, environment
inspection, Runtime or Provider probing, Tool discovery, schema loading,
clock access, randomness, UUID generation, persistence, database/cache/queue
access, policy evaluation, permission mutation, Grant authentication,
currentness or revocation evaluation, authorization consumption, admission,
dispatch, or invocation.

---

## 12. Structural Schema and Offline Resolution

The Draft 2020-12 structural schema is:

```text
schemas/agent-operation-tool-binding.schema.json
```

It is a closed object with exactly the two required properties in canonical
order: `run` and `tool_id`. `tool_id` is a string with `minLength: 1`. `run`
references the canonical AIO-042 schema identifier:

```text
https://ai-engineering-orchestra.dev/schemas/agent-execution-run.schema.json
```

The Run schema transitively references the canonical AIO-041 Contract schema.
Neither nested shape is duplicated. The packaged schema loader resolves both
Run and Contract from an explicit closed in-memory registry. It defines no
generic remote retriever. Missing, mismatched, or unregistered resources fail
closed without HTTP, HTTPS, network, CWD, active-project, or external
source-checkout fallback.

Schema validation owns the two-field JSON structure, required properties,
closed-object boundary, nonempty JSON string rule, and nested structural shape.
Runtime validation owns exact Python types, nested Run intrinsic semantics,
deterministic findings, immutability, and atomicity. Neither layer owns actual
Tool configuration or trust.

---

## 13. Serialization

Standard mapping and JSON serialization can round-trip:

```text
Tool Binding
-> mapping or JSON
-> structural schema validation
-> deserialization
-> runtime validation
-> equal Tool Binding
```

Round-trip equality preserves only the exact two-field value:

```text
round-trip success != Tool existence proven
round-trip success != Tool trust proven
round-trip success != immutable resolver state proven
round-trip success != permission or authorization
round-trip success != admission or invocation
```

Serialization creates no persistence, registry, cache, database, queue,
history, or authoritative record.

---

## 14. Grant and Future Admission Boundary

The AIO-043 Grant is not included in the Tool Binding, and the Grant does not
bind a Tool directly. The two independent values meet only at a future,
separately authorized admission boundary.

A future consumer must obtain and validate an exact Tool Binding before
attempting single-use Grant consumption. That consumer must then require exact
Run equality, fresh prerequisite evidence, authentic and current authority,
and its own durable atomic consumption/admission semantics. AIO-045 supplies
none of those stateful mechanisms.

The following remain distinct:

```text
binding validated != Grant authenticated
Grant authenticated != Grant current
binding.run == grant.run != Grant consumed
Grant consumed != dispatch occurred
dispatch admitted != invocation occurred
invocation occurred != operation succeeded
```

Tool Binding failure must occur before authority is spent. A valid Tool Binding
still cannot cause consumption or admission by itself.

---

## 15. Scenario Boundary

The required scenario coverage establishes, without Tool discovery or
invocation:

1. one exact valid Run and nonempty Tool ID form an intrinsically valid value;
2. a wrong top-level type fails atomically;
3. nested Run findings pass through unchanged before the Tool-ID category;
4. an empty or non-string Tool ID fails, while case and whitespace are not
   normalized;
5. two Tool IDs differing only by case remain different bindings;
6. every Run ID or Contract field mutation creates a different binding value;
7. there is no alternate field through which Runtime, Inference Option,
   environment, operation, resource, Execution Mode, Actor, or Role can be
   substituted;
8. schema extras such as adapter, Provider, command, credential, Grant,
   admission, or result fields are rejected;
9. Runtime capability `present` remains insufficient to construct a concrete
   binding inside Core;
10. mutable aliases remain noncanonical unless the resolver guarantees stable
    immutable identity;
11. direct construction and serialization prove no Tool existence or trust;
12. source, editable-install, and wheel schema resolution remain offline; and
13. binding existence implies no permission, consumption, admission,
    invocation, or success.

All examples and fixtures use synthetic lexical identities and resources. No
test or example requires a real configured Tool or protected-target access.

---

## 16. Explicit Exclusions and Preservation

AIO-045 contains no:

- Tool inventory, discovery, filesystem probing, Runtime probing, MCP or
  Provider enumeration, ranking, fallback, or dynamic reselection;
- Tool existence, availability, currentness, health, or executability claim;
- global Tool-ID registry, binding registry, persistence, database, cache,
  queue, store, history, or transaction;
- adapter, Provider, model, endpoint, command, payload, argument, parameter,
  credential, secret, or native protocol field;
- permission, authority, Grant, Grant authentication, currentness, revocation,
  consumption, replay protection, or mutable security state;
- dispatch admission, admission token, outbox, dispatch, execution, invocation,
  result, error, event, usage, cost, or telemetry;
- lifecycle, cancellation, retry, status, timestamp, clock, randomness, or
  generated identity;
- multi-Tool composition, collection validation, alternative selection, or
  Tool behavior attestation;
- new Core operation, AIO-030, Full Control Center/UI, or protected-target
  behavior.

AIO-045 does not modify AIO-036 Operation Requirement, AIO-037 Runtime
Operation Capability, AIO-040 prerequisite assessment, AIO-041 Contract,
AIO-042 Run, or AIO-043 Grant semantics. It layers one pure immutable configured
implementation identity over the exact complete Run. Any stateful trust,
consumption, admission, execution, lifecycle, result, or telemetry capability
requires separate explicit authorization.
