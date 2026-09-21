# AIO-039 Context

## Authorization and verified baseline

On 2026-09-21, the Human initially authorized creation and implementation of
AIO-039 through Architect design lock, separate Security design approval,
implementation, target-safe validation, final specialist reviews, independent
review, Gate evaluation, and preparation of the final Human Control checkpoint.

That initial authorization did not include final Human architecture, schema,
or security approval; final acceptance; Task closure; staging; commit; push;
merge; tag; release; publication; AIO-040; authority issuance; permission
mutation; dispatch; or real invocation.

After the recorded review-process incident, explicit Human incident
disposition, and bounded follow-up Security approval, the Human supplied direct
final approval on 2026-09-21. That subsequent authorization approves the
reviewed architecture, schema, and security boundary; grants final acceptance;
closes the Task; and permits exactly one local implementation-and-closure
commit on `main`. It does not retroactively authorize or waive the incident and
does not authorize protected-target access, AIO-040, authority issuance,
execution, invocation, push, merge, tag, release, or publication.

The verified baseline is a clean `main` at
`7c295b570443a762a3202fec56d362d33a34ae8e`, subject
`feat: add Environment Operation Permission Observation foundation (AIO-038)`.
AIO-038 is completed with 55/55 criteria and recorded Human approval. AIO-039
was absent. AIO-030 remains parked at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not a dependency.

## Need and dependency boundary

The canonical execution facts remain distinct:

```text
Assignment responsibility
+ Agent candidate prerequisites
+ Operation Requirement
+ Runtime Operation Capability Observation
+ Environment Operation Permission Observation
!= Agent Execution Authorization Evidence
!= execution
```

AIO-035 privately demonstrated a no-I/O preparation composition with an exact
authorization assertion. AIO-036 through AIO-038 subsequently canonicalized
operation demand, Runtime technical support, and environment permission. The
remaining bounded Core layer is caller-attested authorization evidence for the
exact assigned external-inference Agent action.

## Canonical design boundary

The canonical term is **Agent Execution Authorization Evidence**. It is
Evidence, not an Observation, Grant, or Decision. Core validates a supplied
assertion describing an authorization decision made elsewhere; it does not
make that decision or issue authority.

The exact fields, in order, are:

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
authority_kind
authority_id
provenance_reference
state
```

The exact subject is the first ten fields. The first five reproduce the
complete Assignment value. Runtime and Inference Option identify the bounded
external-inference execution candidate; environment, operation, and resource
identify the exact action. `authority_kind`, `authority_id`,
`provenance_reference`, and `state` describe evidence about that subject and
are not subject identity.

Authority kind is exactly `human` or `policy`. Authority identity and
provenance are exact, opaque caller assertions. Core does not authenticate an
authority, verify entitlement, dereference provenance, or inspect approval
records. Mandatory boundaries are:

```text
caller-attested evidence != authenticated authority
Task approval != execution authorization
permission allowed != execution authorization
```

States are exactly `granted` and `denied`. Missing evidence is absence of an
exact subject match, not a serialized state. There is no authorization ID,
timestamp, expiry, clock, persistent grant, consumption, single-use or
reusable-grant claim, replay protection, or revocation lifecycle.

Repeated exact subjects are invalid and are classified deterministically as:

1. exact duplicate;
2. state conflict; or
3. unsupported multi-authority evidence.

Core performs no conflict resolution. The caller or authority producer must
reconcile evidence externally and resupply one coherent item.

## Governance and classification

`complexity: high` reflects the complete multi-contract subject, source and
provenance boundary, repeated-subject taxonomy, deterministic validation,
schema/package integration, and preservation of adjacent contracts.

`risk: high` reflects the harm of treating a false `granted` assertion as
authenticated authority near a future execution boundary. The contract remains
non-executing, so the Task does not claim critical operational authority.

`execution.mode: deep` is an explicit process-depth requirement for security
analysis, exhaustive mismatch testing, package evidence, and independent
review. It grants no authority or permission.

The governing Workflow is `architecture-change`. Effective Gates are
`documentation_consistency` and `independent_review`. A separate Security
Reviewer design approval is required before implementation, followed by
Architect and Security final reviews and a fresh independent review.

## Validation plan

Validation is target-safe and limited to exact paths and synthetic resources:

- focused AIO-039 unit and fixture tests;
- AIO-023, AIO-034, and AIO-036 through AIO-038 regressions;
- package-resource and source-package tests;
- editable-install and normal-wheel smoke tests;
- exact Task and `architecture-change` validation;
- explicitly named changed-Python syntax checks;
- explicitly named changed-document Markdown lint; and
- `git diff --check`.

Known unsafe broad Task validation, broad Workflow-catalog enumeration,
repository-wide verification, and broad Markdown traversal remain skipped.

## Protected-target and execution boundary

The protected target must not be opened, read, searched, listed specifically,
statted, hashed, resolved, or permission-inspected. Tests use synthetic
resources only.

The implementation performs no filesystem, ACL, sandbox, network, provider,
subprocess, clock, database, cache, Human UI, approval-record, policy-service,
authority-lookup, signature, issuance, mutation, dispatch, or invocation I/O.

## Human Control status

On 2026-09-21, direct Human final approval, closure, and local-commit
authorization approved the AIO-039 architecture, schema, and security boundary
and granted final acceptance. All 73 acceptance criteria are complete and the
Task status is `completed`.

This Task approval is lifecycle approval for the reviewed AIO-039 foundation;
it is not Agent Execution Authorization Evidence for a real action and creates
no authority, permission, dispatch, execution, or invocation.
