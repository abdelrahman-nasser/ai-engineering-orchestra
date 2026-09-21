# AIO-037 Context

## Authorization and verified baseline

On 2026-09-21, the Human explicitly authorized creation of AIO-037, a
pre-implementation Architect design lock, implementation, target-safe
validation, Architect final review, independent review, Quality Gate
evaluation, and preparation of the final Human Control checkpoint.

The initial implementation authorization did not include final Human
architecture/schema approval, final acceptance, Task closure, staging, commit,
push, merge, tag, release, publication, AIO-030 work, AIO-038, permission
changes, adapters, discovery, execution contracts, or real invocation. Final
approval, closure, and one local commit were authorized separately on
2026-09-21; all other exclusions remain in force.

The verified baseline was a clean `main` worktree and index at
`6a0527d5dfb950380dccf67d6870ea323a3778b0`, subject
`feat: add Operation Requirement foundation (AIO-036)`. AIO-036 was completed
with 37/37 acceptance criteria, AIO-037 was absent, and the parked local
`feature/aio-030-vscode-control-center` branch remained at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`.

## Motivation and contract boundary

AIO-036 established demand only:

```text
operation_id + resource -> caller-declared required action
```

It does not establish whether any Runtime can technically provide the abstract
operation. AIO-035 experimentally demonstrated that explicit capability
absence and unknown capability need distinct meanings. AIO-037 formalizes only
that stable layer as a separate observation contract.

The mandatory separation is:

```text
capability
!= requirement
!= availability
!= permission
!= authorization
!= execution
```

The canonical value contains exactly `runtime_option_id`, `operation_id`, and
`state`. Its exact identity is `(runtime_option_id, operation_id)`, and its
closed states are `present`, `absent`, and `unknown`. Missing observations for
known Runtime/Core-operation pairs normalize to `unknown`; explicit and
synthesized unknown values are semantically indistinguishable in normalized
output. This missing-value normalization is a new canonical AIO-037 decision.

Runtime Option remains opaque identity. Operation Requirement remains demand
against one resource. Runtime Availability remains operational availability.
Capability contains no resource, tool identity, environment, freshness,
permission, authorization, candidate result, or execution semantics.

## Operation vocabulary reuse

AIO-037 must introduce one package-internal Core operation-vocabulary source
of truth. Both Operation Requirement validation and Runtime Operation
Capability validation must consume it. The refactor must preserve AIO-036's
public types, validator signature, supported operation, findings, messages,
resource grammar, ordering, and atomicity exactly.

The current vocabulary remains exactly `repository_file_read`; no second
operation or generic registry is introduced.

## Protected-target incident boundary

The Post-AIO-036 investigation included one unauthorized broad-search read of
the protected target. The Human disposition is **ACCEPT DISCLOSED INCIDENT FOR
CONTINUATION**. The incident remains recorded, was not retroactively
authorized, and received no waiver. Its returned content must not be reused as
evidence.

AIO-037 must not open, read, search, list specifically, stat, hash, resolve,
inspect permissions for, or otherwise access the protected target. All
operation and capability examples are synthetic. Broad content traversal that
could include the target is prohibited; validation must use explicit safe
paths or target-safe mechanisms.

## AIO-037 validation-process incident

During AIO-037 on 2026-09-21, the Task schema validator was run twice as
requested by the authorization: once by the primary implementation path after
Task creation and once by the isolated schema-validation path after schema
registration. Its semantic phase calls `load_workflow_catalog()`. That
implementation enumerates every entry in `workflows/` and evaluates
`Path.is_file()` before filtering for YAML suffixes. Each execution therefore
likely listed and statted the protected target. Neither execution read or
returned the target's contents, and neither access supplied capability,
requirement, validation, or implementation evidence.

These two protected-target metadata accesses violated the explicit AIO-037
boundary. They are recorded without retroactive authorization, waiver, or
minimization. The Human disposition is **ACCEPT DISCLOSED INCIDENT FOR
CONTINUATION**: continuation was authorized, but the disposition granted no
final AIO-037 approval, satisfied no Quality Gate, and authorized no commit or
closure. Final Human approval was supplied separately on 2026-09-21; it does
not retroactively authorize or waive the incident. It authorizes Task closure
and exactly one local closure commit, but no push, publication, or further
protected-target access.

## Governance and classification

The Human explicitly selected `architecture-change`. Its
`applicable_task_types` values are advisory under the Workflow specification,
so binding an `implementation` Task is valid. The Workflow requires Architect
design and review, Software Engineer implementation, an independent Reviewer,
the `documentation_consistency` and `independent_review` Quality Gates, and a
review-stage Human Control checkpoint.

`complexity: high` reflects cross-contract vocabulary reuse, tri-state and
missing-value semantics, pair normalization, deterministic validation, schema
packaging, and installation proof. `risk: medium` reflects the chance that
incorrect capability evidence could mislead later composition, while this
contract itself grants no authority and performs no execution. `deep` mode is
explicitly selected for boundary analysis, negative-versus-unknown coverage,
package validation, and independent review; it grants no additional authority.

## Human Control status

The Architect design lock was approved before feature implementation. The
validation-process incident received Human disposition for continuation.
Implementation, target-safe validation, Architect final review, independent
review, and both effective Quality Gates are complete. Explicit Human
architecture/schema approval and final acceptance were received on 2026-09-21,
and the Task lifecycle status is `completed`.
