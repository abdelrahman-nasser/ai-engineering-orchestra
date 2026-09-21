# AIO-038 Context

## Authorization and verified baseline

On 2026-09-21, the Human explicitly authorized creation of AIO-038, a
pre-implementation Architect design lock, a separate pre-implementation
Security Reviewer boundary approval, implementation, target-safe validation,
Architect and Security final reviews, independent review, Quality Gate
evaluation, and preparation of the final Human Control checkpoint.

That initial authorization did not include final Human
architecture/schema/security approval, final acceptance, Task closure, staging,
commit, push, merge, tag, release, publication, AIO-039, AIO-030 work,
protected-target access, permission mutation, an Execution Contract, dispatch,
or real invocation.

Safe Git metadata verified a clean worktree and index on `main` at
`de07e73e739e8c5c20da004ade6e9e2f923b051e`, subject
`feat: add Runtime Operation Capability Observation foundation (AIO-037)`.
AIO-037 was completed with 35/35 acceptance criteria, and AIO-038 was absent.
No fetch, pull, reset, restore, stash, discard, or branch switch occurred.

AIO-030 remains parked independently on
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. It is not a dependency and must
remain untouched. AIO-038 depends directly on completed AIO-037.

## Need and objective

AIO-036 established caller-declared operation/resource need, and AIO-037
established Runtime technical-support evidence. Neither contract describes
whether one environment currently permits one known Runtime to perform the
exact operation against the exact resource. The Human-authorized Post-AIO-037
investigation therefore selected Environment Operation Permission Observation
as the next canonical Core contract.

The canonical definition locked by the Architect is:

> An immutable, caller/environment-supplied observation describing the
> currently known effective environment-permission state for one known Agent
> Runtime Option to perform one Core-defined abstract operation against one
> exact lexical repository-relative resource in one opaque caller-identified
> environment, within one caller-owned evaluation snapshot.

Core validates supplied evidence. It does not independently discover or verify
native permission truth.

The mandatory separations are:

```text
requirement != capability != permission observation
permission allowed != Human or policy authorization granted
Runtime availability != permission state
conflicting evidence != denied != unknown != Permission Decision
permission observation != enforcement != execution
```

## Canonical design boundary

The observation contains exactly `runtime_option_id`, `environment_id`,
`operation_id`, `resource`, and `state`, in that order. Its exact case-sensitive
identity is `(runtime_option_id, environment_id, operation_id, resource)`;
state is not identity. States are exactly `allowed`, `denied`, and `unknown`.
The separate Permission Decision vocabulary remains `allow`, `ask`,
`always-ask`, and `deny`.

`environment_id` is an opaque caller-owned snapshot scope, not an Environment
entity, registry, lifecycle, topology, host, container, sandbox, or discovery
surface. `runtime_option_id` remains explicit so evidence cannot leak across
different Runtime principals or execution surfaces within one environment.

There is no freshness field. The caller owns snapshot currency and must omit
stale or unreliable evidence or supply `unknown`. Core cannot independently
verify freshness. A missing exact permission observation semantically means
unknown, never denied, but validation preserves and sorts only supplied
observations because the resource domain is open-ended. No Cartesian
permission snapshot is synthesized.

Runtime inventory validation is reused unchanged. Operation syntax and support
reuse the AIO-037 package-internal vocabulary. The AIO-036 repository-resource
grammar is extracted into one private helper used by both Operation Requirement
and Environment Operation Permission validation, while preserving all AIO-036
public behavior exactly.

Repeated exact identities with one state are invalid identical duplicates.
Repeated exact identities with differing states are invalid conflicts. The two
categories are mutually exclusive, deterministic, and identity-sorted. Any
conflict invalidates the complete snapshot; there is no first-, last-, latest-,
deny-, allowed-, or stricter-wins behavior and no conversion to unknown,
denied, a Permission Decision, or a Human approval question. Reconciliation
belongs to the caller/environment evidence producer.

## Protected-target boundary

The protected target remains `workflows/README.md`. AIO-038 must not open,
read, search, list specifically, stat, hash, resolve, inspect permissions for,
or otherwise access it. Broad Workflow-catalog enumeration and repository-wide
content traversal that may inspect it are prohibited. All new resources,
fixtures, examples, package probes, and tests use synthetic lexical values.

AIO-037 records that the full Task validator's Workflow-reference phase
enumerates the Workflow directory and may stat the protected target. AIO-038
therefore uses direct Task structural validation, exact safe-path resolution of
`workflows/architecture-change.yaml`, focused validators, explicitly named
Markdown files, and target-safe installation smoke. Unsafe broad checks remain
skipped and must be reported as skipped rather than passed.

## Governance and classification

The Human selected `architecture-change`. Task `type` is extensible and the
Workflow's `applicable_task_types` list is advisory, so `type: implementation`
is valid. The Workflow requires Architect design, Software Engineer
implementation, validation, and Reviewer plus Architect review. Its review
stage contains the Human Control checkpoint.

`complexity: high` reflects a canonical security-relevant evidence contract,
four-part scope, exact cross-contract reuse, conflict taxonomy, deterministic
validation, and schema/package integration. `risk: high` reflects the danger
that a false `allowed` interpretation or silent conflict resolution could later
be mistaken for execution authority. `execution.mode: deep` requires deliberate
boundary analysis, edge-case testing, installation proof, and independent
review; it grants no authority.

The effective Quality Gates are exactly `documentation_consistency` and
`independent_review`, required by Project configuration and the bound Workflow
and repeated explicitly by this Task.

## Review and Human Control status

The non-implementing Architect issued `APPROVE` for the complete design lock on
2026-09-21. A separate non-implementing Security Reviewer then issued
`APPROVE` before implementation for the permission/decision/authorization,
scope, state, duplicate/conflict, no-discovery, no-enforcement, and
protected-target boundaries. The Reviewer found no material security finding
or blocker and confirmed that implementation may proceed under the locked
design.

Implementation and target-safe validation are complete. The Architect's final
technical review issued `APPROVE` with no implementation blocker, and the
Security final boundary review issued `APPROVE` with no finding or blocker.
The Architect's exact-file synchronization recheck passed the
`documentation_consistency` Quality Gate. A fresh non-implementing Reviewer
then issued `APPROVE` with no material finding and passed the
`independent_review` Quality Gate. AIO-038 reached the Human Control checkpoint
with 54/55 criteria complete.

On 2026-09-21, the Human supplied explicit final architecture, schema, and
security-boundary approval and final acceptance through direct Human final
approval, closure, and local-commit authorization. The approval covers the
reviewed canonical term and definition, five-field model, identity, state and
missing-evidence semantics, conflict semantics, schema, resource-validation
and operation-vocabulary reuse, permission/decision/authorization separation,
and the no-discovery, no-enforcement, and no-execution boundaries.

This Task approval is not execution authorization for any resource or action.
It authorizes AIO-038 lifecycle closure and exactly one local closure commit on
`main`; it does not authorize protected-target access, AIO-030 work, AIO-039,
push, merge, tag, release, publication, permission mutation, dispatch, or real
invocation. AIO-038 is completed with 55/55 criteria.
