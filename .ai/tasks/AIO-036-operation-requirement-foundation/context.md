# AIO-036 Context

## Initial authorization and verified baseline

On 2026-09-21, the Human explicitly authorized creation of AIO-036, Architect
design lock, implementation, validation, Architect final review, independent
review, Quality Gate evaluation, and preparation of the final Human Control
checkpoint. The authorization does not include final Human architecture/schema
approval, final acceptance, Task closure, staging, commit, push, merge, tag,
release, publication, AIO-030 work, or creation of AIO-037.

Before Task creation, safe Git metadata checks verified a clean worktree and
index on branch `main` at HEAD
`d089bd69e56e9b38d538955eb6e97d08a850884c`. AIO-035 was completed and AIO-036
was absent. No fetch, pull, reset, stash, discard, or branch switch occurred.

AIO-030 remains parked independently on
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. It is not a dependency and remains
untouched. AIO-036 depends only on completed AIO-035.

## Need and objective

The post-AIO-035 investigation identified Operation Requirement as the first
justified canonical action-layer contract. AIO-036 establishes only the value
that declares what abstract operation is needed against what exact lexical
repository-relative resource. It does not establish whether a Runtime can
perform the operation, whether an environment permits it, whether a Human or
policy authorizes it, or whether execution occurs.

The canonical definition is:

> An immutable, caller-supplied declaration that one Core-defined abstract
> operation is required against one exact lexical repository-relative resource
> within the caller-owned evaluation context.

The mandatory separation is:

```text
requirement
!= capability
!= permission
!= authorization
!= execution
```

## Protected-target and incident boundary

The AIO-035 review-process incident remains accepted as disclosed for
continuation, not retroactively authorized, and not waived. The protected target
is `workflows/README.md`. AIO-036 must not open, read, search, list specifically,
stat, hash, resolve, permission-inspect, or otherwise access that target. Tests
and examples use synthetic resource strings only. Broad validation that could
include the target must be replaced by focused target-safe checks and any
resulting scope limitation must be reported.

## Governance and classification

The Human selected `architecture-change`. Its `applicable_task_types` list is
advisory, so `type: implementation` is valid for the authorized creation and
integration of a new canonical Core contract. The Workflow requires Architect
design, Software Engineer implementation, and Reviewer plus Architect review.
Its review-stage Human checkpoint applies.

`complexity: high` reflects the new Core semantic authority, exact lexical
resource grammar, deterministic diagnostics, schema/runtime split, packaging,
and no-I/O evidence. `risk: medium` reflects the risk that incorrect scoping
could later mis-match capability, permission, or authorization evidence while
this contract itself remains pure and non-authorizing. `execution.mode: deep`
requires deliberate edge-case analysis, packaging proof, and independent
review; it grants no authority.

The effective Quality Gates are exactly `documentation_consistency` and
`independent_review`, required independently by both Project configuration and
the bound Workflow and repeated explicitly by this Task.

## Architect design boundary

The non-implementing Architect approved the design before implementation on
2026-09-21. The value contains exactly `operation_id` and `resource`; exact
case-sensitive identity is `(operation_id, resource)`. AIO-036 supports only
`repository_file_read`, with an explicitly extensible Core vocabulary and no
registry service. The resource is a lexical string only: no repository root is
accepted or inferred and no filesystem, path-resolution, link, environment,
network, process, clock, or persistence operation is permitted.

Any discovered need for Task schema fields, Assignment or candidate changes,
Runtime capability, environment permission, execution authorization, an
Execution Contract, target access, or a broader operation registry is a scope
conflict requiring the Task to stop rather than expand.

## Human Control and closure

On 2026-09-21, a direct Human follow-up explicitly approved the reviewed
Operation Requirement architecture and schema, granted final acceptance,
authorized Task closure, and authorized exactly one local closure commit on
`main`. All 37 acceptance criteria are complete and the Task status is
`completed`.

This closure authorization does not authorize push, merge, tag, release,
publication, AIO-030 work, AIO-037 creation, or any downstream capability,
permission, authorization, execution, adapter, or invocation work.
