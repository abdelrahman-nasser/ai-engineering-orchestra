# AIO-045 Context

## Authorization and verified baseline

On 2026-09-23, the Human initially authorized creation and implementation of
AIO-045, fresh Architect and Security design locks before implementation,
target-safe validation, fresh final specialist and independent reviews, Gate
evaluation, and preparation of the Human Control checkpoint.

After all non-Human criteria and both Gates passed, the Human directly approved
the architecture, schema, immutable Tool-identity model, trusted resolver
boundary, no-widening model, security boundary, and final acceptance. The Human
also authorized Task closure, explicit staging of only reviewed AIO-045 paths,
and exactly one local implementation-and-closure commit on `main`.

The final authorization does not permit push, merge, tag, release, publication,
AIO-046 creation, real Tool discovery, probing, resolution, or binding, Grant
consumption, currentness or revocation, replay protection, persistence,
dispatch admission, dispatch, invocation, adapter/Provider integration,
credentials, results/events/telemetry work, AIO-030, Full Control Center/UI
work, or protected-target access.

```text
HUMAN ARCHITECTURE APPROVAL:
APPROVED

HUMAN SCHEMA APPROVAL:
APPROVED

HUMAN IMMUTABLE TOOL-IDENTITY MODEL APPROVAL:
APPROVED

HUMAN TRUSTED RESOLVER-BOUNDARY APPROVAL:
APPROVED

HUMAN NO-WIDENING MODEL APPROVAL:
APPROVED

HUMAN SECURITY-BOUNDARY APPROVAL:
APPROVED

FINAL ACCEPTANCE:
APPROVED

APPROVAL DATE:
2026-09-23

APPROVAL SOURCE:
Direct Human final approval, closure, and local-commit authorization
```

The verified baseline is clean `main` at
`157d2cbaa6af121b6dccf88bfefa76435a86e97c`. The worktree and index were clean,
and AIO-045 was absent before its authorized creation. The baseline commit is
the recorded cancellation of AIO-044. AIO-030 remains parked independently on
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not in scope.

## Replacement and evidence boundary

```text
REPLACES:
AIO-044

AIO-044 STATUS:
cancelled

AIO-044 TECHNICAL DESIGN:
may be consulted as prior engineering input

AIO-044 ACCEPTANCE EVIDENCE REUSED:
NO

AIO-044 REVIEW/GATE EVIDENCE REUSED:
NO

DEPENDENCY ON AIO-044:
NO
```

AIO-044 remains a cancelled historical Task at 63/66. Its implementation was
technically approved but was not successfully completed or committed as
canonical product code; criteria 60 and 61 remained unsatisfied. AIO-045 does
not waive, retroactively authorize, amend, or depend on that history.

The external cancelled AIO-044 technical reference may be consulted only as
prior engineering input. Any reused source text or code becomes new AIO-045
work and must receive fresh implementation, validation, review, Gate, and Human
Control evidence.

```text
ENGINEERING INPUT:
cancelled AIO-044 technical reference

CANONICAL EVIDENCE:
AIO-045 only
```

## Architectural purpose and approved design

AIO-036 defines an abstract Operation Requirement. AIO-037 records abstract
Runtime technical support. AIO-041 binds complete declarative action intent,
AIO-042 supplies immutable Run occurrence identity, and AIO-043 supplies a
separate positive authorization artifact. None identifies the exact configured
Tool implementation selected for one Run.

The approved canonical term is **Agent Operation Tool Binding**. It is an
immutable, serializable, provider-neutral, derived/selected binding value. It
is not Permission, authorization, a Grant, a decision, lifecycle state,
admission, or invocation.

The approved canonical definition is:

> An immutable, serializable, provider-neutral value binding one exact complete
> Agent Execution Run to one exact immutable configured Tool implementation
> identity supplied by an external trusted resolver, without granting authority,
> widening the Run Contract, performing discovery, consuming authorization,
> admitting dispatch, or invoking the Tool.

The approved value contains exactly these fields, in order:

```text
run
tool_id
```

`run` is the complete exact `AgentExecutionRun`; a bare `run_id` cannot prove
the Contract binding. No Run or Contract field is flattened or duplicated.
Full immutable value equality is `(run, tool_id)`, so no Binding ID is needed.

`tool_id` is an exact, opaque, nonempty, case-sensitive, unnormalized string.
With no Tool-ID grammar, whitespace-containing and whitespace-only nonempty
strings are intrinsically valid; Core does not trim or invent a readable or
version grammar. Semantically, the ID must identify one immutable configured
implementation revision. A mutable alias is insufficient unless its resolver
guarantees permanent non-rebinding. Core neither creates nor resolves the ID,
proves global uniqueness, nor adds a separate revision field. The external
configured runtime/tool resolver owns the ID and namespace. The effective
external mapping namespace is scoped by the nested Run's exact
`runtime_option_id`, `environment_id`, and `tool_id`.

## Resolver, adapter, and no-widening boundaries

The external trusted resolver owns configured Tool existence, the Tool-ID
namespace, permanent immutable-identity mapping, Runtime/environment
applicability, and semantic selection. Core does not call that resolver and
cannot prove its integrity.

A future adapter owns physical implementation lookup, credentials, endpoint,
protocol/native translation, containment, native parameters, and invocation.
AIO-045 implements no adapter.

A valid Binding preserves exact Run equality and supplies no alternate action
field. It cannot substitute Runtime, Inference Option, environment, operation,
resource, Execution Mode, Actor, Role, Task, Workflow, or Stage. It adds no
fallback or reselection. Because Core does not inspect a real implementation,
assurance that selected Tool behavior does not widen the Run remains an
external resolver/implementation trust-boundary obligation.

Runtime capability and Tool Binding remain distinct:

```text
AIO-037 capability present
!= Tool Binding
```

Grant and Tool Binding also remain separate. A future admission layer must
compare complete values so `binding.run == grant.run == fresh expected Run`;
AIO-045 neither performs that comparison operationally nor admits dispatch.

## Approved API, validation, schema, and serialization

The approved direct-module public types are:

```text
AgentOperationToolBinding
AgentOperationToolBindingFinding
AgentOperationToolBindingValidationResult
```

The sole approved public function is:

```python
validate_agent_operation_tool_binding(binding)
```

No preparation or resolver API exists. Intrinsic validation proves only
the exact Binding type, valid complete nested Run, exact nonempty Tool ID, and
immutable value structure. It does not prove resolver provenance, Tool
existence, availability, executability, external mapping immutability,
behavioral containment, authority, permission, Grant currentness, or admission.
Invalid results are atomic: `valid` is false, findings are nonempty, and
`binding` is `None`.

The approved closed Draft 2020-12 schema has exactly required `run` and
`tool_id` properties and references the canonical packaged Run schema, whose
Contract reference must also resolve through the explicit offline registry.
Missing, mismatched, unknown, or unregistered resources fail closed without
network, current-working-directory, active-checkout, or source fallback.

Serialization round-trip must preserve exact equality. It does not prove Tool
existence, resolver trust, authority, or admission.

## Purity, validation safety, and protected-target boundary

Construction and validation are deterministic and supplied-data-only. They
perform no filesystem access, network, subprocess, clock, randomness,
database/cache/store access, Tool discovery, Runtime or Provider probing,
dispatch, or invocation. Tests and fixtures use synthetic Tool IDs and lexical
resources only.

During AIO-045, every prohibited broad verification command is intentionally
skipped. During AIO-045, the protected target is not accessed by any authorized
or observed command. These process criteria may be marked complete only while
both statements remain supportable.

The legacy Task and Workflow validators were inspected statically before use.
Both traverse catalogs and have no exact-target mode, so they are prohibited
for AIO-045 and will not be executed. Exact-file structural and semantic checks
will be used instead. Validator `--help` probing is prohibited.

## Governance and classification

The explicit `architecture-change` Workflow governs this new Core concept and
schema. Its applicability labels are advisory; its design, implementation,
validation, review, `documentation_consistency`, `independent_review`, and
Human Control requirements apply.

`complexity: high` reflects exact nested Run binding, immutable external Tool
identity semantics, offline schema closure, no-widening coverage, and fresh
cross-role review. `risk: high` reflects the security and authority confusion
that an incorrect Tool binding could create while stopping short of real
credentials, persistence, consumption, admission, or execution. Explicit
`execution.mode: deep` requires probing evidence and sustained bounded rigor;
it grants no additional authority.

Any expansion into persistence, credentials, Grant consumption, admission, or
real execution requires an immediate stop and classification reconsideration,
likely to critical.
