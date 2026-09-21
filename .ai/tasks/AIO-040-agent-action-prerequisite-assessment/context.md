# AIO-040 Context

## Authorization and baseline

On 2026-09-21, the Human explicitly authorized creation of AIO-040, a separate
Architect design lock, a separate Security design review before implementation,
implementation, target-safe validation, final Architect and Security reviews,
independent review, Quality Gate evaluation, and preparation of the Human
Control checkpoint.

On 2026-09-21, the Human subsequently granted final architecture approval,
final security-boundary approval, final acceptance, Task closure authority,
target-safe closure validation, explicit staging of only the reviewed AIO-040
paths, and exactly one local implementation-and-closure commit on `main`.

The final authorization does not include push, merge, tag, release,
publication, AIO-041, an Execution Contract, an Execution Run, real
authorization consumption, or real invocation. Human approval of AIO-040 is
Task-lifecycle approval only; it is not Agent Execution Authorization Evidence
and does not authorize a real Agent action. An AIO-040 `satisfied` result
likewise is not permission to execute.

The verified baseline is clean `main` at
`eaab47b6b253b25d0980c3415f438c36c0ff6923`, subject
`feat: add Agent Execution Authorization Evidence foundation (AIO-039)`.
AIO-039 is completed with 73/73 acceptance criteria and recorded Human
architecture, schema, security-boundary, and final approval. AIO-040 was absent
before Task creation.

AIO-030 remains parked on `feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not a dependency. The
separate Full Control Center/UI track is also outside this Task.

## Architectural purpose

The five direct prerequisites now exist independently:

1. AIO-034 assesses one exact external-inference Agent candidate.
2. AIO-036 declares one exact operation/resource requirement.
3. AIO-037 reports Runtime technical support for the operation.
4. AIO-038 reports environment permission for the exact action.
5. AIO-039 supplies caller-attested authorization evidence for the exact
   ten-part action subject.

No canonical Core layer currently composes those facts. AIO-040 adds only that
pure diagnostic composition. It sits above AIO-034 and does not recompute Actor
availability, Actor-to-Runtime applicability, Runtime-to-Inference
compatibility, or endpoint availability.

## Required semantic boundary

The canonical subject is exactly:

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
```

The ordinary outcomes are exactly `satisfied`, `blocked`, and `unresolved`,
with diagnostic precedence `blocked > unresolved > satisfied`. Invalid input
has findings and no ordinary outcome. All applicable reasons remain visible,
including uncertainty reasons beside a blocker.

`satisfied` means only that all currently modeled caller-supplied prerequisites
for the exact action are positive. It does not mean trusted authority was
authenticated, an Execution Contract or tool binding exists, execution is
authorized by Core, dispatch is permitted, invocation may occur, or execution
will succeed.

## Input and validation boundary

The assessment consumes one exact coherent AIO-034 result, validates one
Operation Requirement through the existing validator, and consumes exact
AIO-037, AIO-038, and AIO-039 validation-result containers. It accepts no raw
capability, permission, or authorization collections and does not reimplement
their validators.

Capability lookup uses normalized AIO-037 output. Permission and authorization
use private exact lookups over supplied-only normalized output. Missing exact
permission is unknown; missing exact authorization is unproven. Invalid or
conflicting parent evidence remains invalid and is never converted to a normal
blocked or unresolved assessment.

## Security and execution boundary

AIO-040 performs no filesystem, protected-resource, environment, network,
subprocess, clock, database, cache, authority, policy, permission, Provider,
Agent, or tool operation. Tests and examples use synthetic resources only.

The assessment is diagnostically default-deny: invalid, blocked, and unresolved
results cannot support future execution. A satisfied result remains only one
necessary modeled prerequisite input for separately authorized future design.

No schema or persistence is justified because the result is derived,
ephemeral, in-memory, and non-serialized, following AIO-032 and AIO-034.

## Governance

The bound `architecture-change` Workflow requires Architect design work,
Software Engineer implementation, Architect and independent Reviewer review,
the `documentation_consistency` and `independent_review` Quality Gates, and a
Human Control checkpoint. A separate Security Reviewer is additionally required
before and after implementation because a false positive could later be
misused near an execution boundary.

`complexity: high` reflects five-contract composition, exact identity joins,
container coherence, deterministic diagnostics, and invalid-versus-negative
separation. `risk: high` reflects the impact of a false `satisfied` result.
`execution.mode: deep` establishes the required engineering rigor and grants no
runtime authority.

## Validation boundary

Validation must be exact-path and target-safe. Broad Task validation, Workflow
catalog enumeration, repository-wide verification, broad Markdown traversal,
and package smoke without target-safe mode remain prohibited. The protected
target must not be opened, read, searched, listed, statted, hashed, resolved,
or used as a fixture.

All required reviews and Gates passed without waiver. The Human separately
granted final architecture approval, security-boundary approval, final
acceptance, and closure authority on 2026-09-21, so the Task is `completed`.
