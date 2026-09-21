# AIO-041 Context

## Authorization and verified baseline

On 2026-09-21, the Human initially authorized AIO-041 Task creation,
Architect design lock, separate Security design approval before implementation,
implementation, target-safe validation, final Architect and Security reviews,
independent review, Quality Gate evaluation, and preparation of the Human
Control checkpoint.

That initial authorization stopped at Human Control. On 2026-09-21, direct
Human final approval then approved the architecture, schema, security boundary,
and final acceptance; authorized Task closure; and authorized explicit staging
of the reviewed AIO-041 paths plus exactly one local closure commit on `main`.
It did not authorize push, merge, tag, release, publication, AIO-042, an
Execution Run, authorization consumption, tool binding, dispatch, or real
Agent invocation.

The verified baseline is clean `main` at
`35aeb7b044cbdd8385184281c25703bd66fa2a09`. The worktree and index were clean,
AIO-040 was completed with 52/52 criteria and recorded Human approval, and
AIO-041 was absent before Task creation.

AIO-030 remains parked on `feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not an AIO-041 dependency.
The separate Full Control Center and UI track is outside this Task.

## Architectural purpose

AIO-040 provides a pure, diagnostic Agent Action Prerequisite Assessment for
one exact assigned external-inference Agent action. A `satisfied` assessment is
necessary modeled prerequisite evidence only; it is not an execution request,
authorization, durable readiness claim, tool binding, dispatch permission, or
invocation permission.

AIO-041 adds the next bounded Core layer: one immutable declarative intent value
that directly embeds the exact ten-part AIO-039/AIO-040 action subject and binds
the already-resolved effective Task-wide minimum Execution Mode. The eleven
fields, in order, are:

```text
task_id
workflow_id
stage_id
role_id
actor_id
runtime_option_id
option_id
environment_id
operation_id
resource
execution_mode
```

The first ten fields remain the action subject. `execution_mode` is required
contract context and is not added to that subject. Full eleven-field equality
defines contract value equality; it does not create instance or lifecycle
identity.

## Preparation, validation, and trust boundary

Canonical preparation accepts only one exact observably coherent AIO-040 result
whose value is `valid=true`, has no findings, has outcome `satisfied`, and has
only the canonical positive reason, plus one explicitly supplied effective mode
from `lite`, `standard`, `deep`, or `critical`. The caller owns Task/Project
default resolution. AIO-041 never infers mode from Complexity, Risk, Workflow,
Stage, Role, Actor, Runtime, or Inference Option.

Blocked, unresolved, invalid, incoherent, and wrong-type prerequisite results
cannot prepare a contract. Preparation checks observable AIO-040 invariants; it
does not rerun AIO-034 or AIO-037 through AIO-039 and cannot authenticate
assessor provenance or caller truth.

Intrinsic validation proves only exact value structure, nonempty identity
strings, the closed Execution Mode value, supported operation semantics, and
lexical resource validity. It does not prove that canonical preparation
occurred, that AIO-040 was genuinely run, that evidence remains fresh, that
authority is authentic, or that execution is permitted.

## Staleness and future boundary

The contract may be durable as intent, but it carries no durable readiness.
Future Run or dispatch work must freshly resolve the effective Task mode,
freshly collect current prerequisite evidence, produce a fresh exact AIO-040
assessment, freshly prepare the eleven-field value, and compare values where
appropriate. Equality is only a necessary condition. Separately designed,
authenticated, run-bound authority would still be required.

AIO-041 implements none of that future Run decision. Contract creation consumes
no authorization and stores no prerequisite state, authority, provenance,
freshness, timestamp, or lifecycle state.

## Security, protected-target, and no-execution boundary

The specification, preparation, validation, schema, and tests are pure and
declarative. They perform no filesystem, protected-resource, network,
subprocess, clock, randomness, database, cache, discovery, dispatch, or
invocation work. Resources used in tests and examples are synthetic lexical
strings only.

The protected target must not be opened, read, searched, listed, statted,
hashed, resolved, permission-inspected, or used as a fixture. Broad Task
validation, Workflow-catalog enumeration, repository-wide verification, broad
Markdown traversal, and package smoke without target-safe mode remain
intentionally excluded.

## Governance and classification

The explicit `architecture-change` Workflow binding is valid even though the
Task type is `implementation`; Workflow `applicable_task_types` is advisory and
does not select or prohibit a binding. The Workflow requires Architect design
and final review, independent Reviewer evaluation, the
`documentation_consistency` and `independent_review` Gates, and a Human Control
checkpoint. A separate Security Reviewer is additionally required before and
after implementation because a contract could otherwise be misread as
execution authority.

`complexity: high` reflects the first serializable intended-action contract,
eleven-field identity and posture semantics, AIO-040 coherence checking, the
preparation-versus-validation distinction, schema/package behavior, and
staleness boundary. `risk: high` reflects the impact of incorrectly treating a
contract as executable. `execution.mode: deep` is the explicitly chosen Task
minimum for rigorous design and validation; it is not inferred and grants no
authority.

The Task is `completed` after all implementation, validation, reviews, Gates,
and explicit Human approvals were recorded. Human approval of AIO-041 is
governance approval of the reviewed architecture and Task lifecycle; it is not
Agent execution authorization. An Agent Execution Contract remains distinct
from permission to execute.
