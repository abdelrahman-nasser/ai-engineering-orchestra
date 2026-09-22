# AIO-044 Context

## Authorization and verified baseline

On 2026-09-22, the Human explicitly authorized AIO-044 Task creation,
Architect design lock, separate Security-boundary approval before
implementation, implementation, target-safe validation, final Architect and
Security reviews, fresh independent review, Quality Gate evaluation, and
preparation of the Human Control checkpoint.

The authorization stops at Human Control. It does not authorize final Human
architecture, schema, immutable-Tool-identity, trusted-resolver,
no-widening/security, or acceptance approval; Task closure; staging; commit;
push; merge; tag; release; publication; AIO-045; a real Tool binding; Grant
consumption; persistence; admission; dispatch; or invocation.

The verified baseline is clean `main` at
`f3e21e459addd7233c69182358eb4bf0a7bc7afe`. The worktree and index were clean,
AIO-043 was completed with 60/60 criteria and recorded Human approval, and
AIO-044 was absent before authorized creation.

AIO-030 remains parked on `feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. The independent Full Control
Center/UI track is outside this Task. The protected target must not be opened,
read, searched, listed, statted, hashed, resolved, permission-inspected, or
used as a fixture.

## Architectural purpose

AIO-036 defines abstract operation/resource demand. AIO-037 supplies abstract
Runtime operation support but no implementation identity. AIO-041 binds exact
action intent, AIO-042 binds it to one immutable Run occurrence, and AIO-043
binds positive time-bounded authority to the complete Run. None identifies the
exact configured implementation that a later admission boundary may permit to
dispatch.

AIO-044 introduces **Agent Operation Tool Binding**, an immutable,
serializable, provider-neutral, derived/selected, non-authoritative value that
binds one exact complete Agent Execution Run to one exact immutable configured
Tool implementation selected by an external configured runtime/tool resolver.
The architectural sequencing rule is documentation-only here:

```text
exact Tool Binding
-> must exist before future single-use Grant consumption
```

AIO-044 implements neither consumption nor admission.

## Architect design lock

Before implementation, a separate non-implementing Architect issued
`ARCHITECT DESIGN LOCK: APPROVE` on 2026-09-22.

The exact frozen value is:

```python
AgentOperationToolBinding(
    run: AgentExecutionRun,
    tool_id: str,
)
```

Full `(run, tool_id)` value equality applies. `run` is the complete exact
nested Run; bare `run_id` is insufficient. There is no `binding_id`, separate
revision field, preparation API, collection API, inventory, registry, or
package-root export.

Model A is locked: `tool_id` itself denotes one immutable/version-stable
configured implementation revision. It is exact, opaque, nonempty,
case-sensitive, and unnormalized. Consistent with adjacent opaque string
contracts, whitespace-containing and whitespace-only values are intrinsically
accepted, without establishing safe external allocation. A mutable alias is
not canonical unless its mapping can never be rebound. Core neither allocates
Tool IDs nor proves global uniqueness.

The external namespace is scoped by the exact Runtime Option and environment
inside the nested Run. The external resolver owns configured existence,
identity integrity, applicability, and selection. A future adapter owns
physical resolution, credentials, endpoints, native translation, containment,
and invocation.

Only `validate_agent_operation_tool_binding` is public from the direct module.
It validates exact top-level type, nested Run, then exact nonempty `tool_id`.
Nested Run findings retain their exact codes, messages, multiplicity, and
order. Invalid output is atomic and contains no binding.

## Security design lock

Before implementation, a separate Security Reviewer issued
`SECURITY DESIGN REVIEW: APPROVE` on 2026-09-22.

Tool Binding is not permission, authority, a Grant, Grant validity or
currentness, Grant consumption, replay protection, dispatch admission,
dispatch, invocation, or success. Direct construction, schema validity,
intrinsic validity, and serialization prove no Tool existence, trust,
availability, executability, resolver provenance, or operation conformance.

Representational non-widening is achieved by nesting the exact Run and adding
no alternate Task, Workflow, Stage, Role, Actor, Runtime, Inference,
environment, operation, resource, or Execution Mode field. Changing any such
value creates a different nested Run and binding. Actual Tool behavior and
physical containment remain external resolver/adapter trust obligations.

Runtime Operation Capability state `present` is not a concrete Tool Binding.
Core performs no discovery, probing, PATH inspection, MCP enumeration, network
lookup, Runtime/Provider call, ranking, fallback, or reselection.

The intended v1 relationship is one Run to zero or one effective selected
binding. AIO-044 is single-value only and cannot enforce global cardinality;
future durable admission must store exactly one binding and reject
substitution.

## Schema and packaging boundary

The closed Draft 2020-12 schema contains exactly `run` and `tool_id` in that
order. `run` references the packaged AIO-042 schema, which transitively
references AIO-041. The closed offline registry must include both references.
Missing, mismatched, and unregistered resources fail closed without network,
CWD, active-project, or arbitrary source-checkout fallback.

Source, editable installation, and normal-wheel installation must agree. The
direct module remains the public import boundary; the package root gains no
binding export.

## Classification and governance

The Human explicitly selected the `architecture-change` Workflow. Its
`applicable_task_types` labels are advisory under the canonical Workflow
specification and do not conflict with `type: implementation`.

`complexity: high` reflects the first concrete implementation identity,
complete Run nesting, external ownership, immutable identity requirements,
no-widening analysis, and nested package references. `risk: high` reflects the
impact of implementation substitution or scope widening while the contract
remains pure and non-authoritative. Explicit `execution.mode: deep` provides
the required engineering rigor without granting runtime authority.

The Workflow requires Architect, Software Engineer, and independent Reviewer
participation, `documentation_consistency`, `independent_review`, and a Human
Control checkpoint. This Task additionally requires separate Security design
and final review.

## Target-safe validation plan

Validation is limited to focused Tool Binding tests and schema fixtures,
explicit adjacent regressions, focused packaging tests, target-safe editable
and normal-wheel installation smoke, exact Task and explicitly bound Workflow
validation, explicit Python syntax checks, exact changed-document Markdown
lint, and `git diff --check`.

Broad Task validation, Workflow-catalog enumeration, repository-wide
verification, broad Markdown traversal, and non-target-safe package smoke are
prohibited and must be reported as intentionally skipped for protected-target
safety.

## Pre-cancellation Human Control stopping point

Before the remediation decision, AIO-044 remained `in_progress` at Human
Control. Human architecture, schema, immutable-Tool-identity,
trusted-resolver, no-widening/security, and final acceptance approval had not
been granted. The later Human incident disposition accepted the disclosed
deviation for continuation only and did not constitute any of those approvals.

## Audited cancellation

On 2026-09-23, after the bounded Security and independent closure reviews, the
Human explicitly authorized audited cancellation. The initial installation
smoke had omitted `--target-safe`, entered a prohibited broad checkout-
verification path, and reported 5,493 pre-existing Markdown findings across
263 vendored `node_modules` files. That invocation is not validation evidence.
The correct target-safe rerun passed, and no direct protected-target access was
observed, but categorical protected-target non-access cannot be certified.
Criterion 60 is therefore unsatisfied. Because a prohibited broad check did
execute, criterion 61 is also unsatisfied. Criterion 66 was never satisfied by
final Human implementation acceptance.

The technical implementation had passed Architect, Security, independent
technical, packaging, and focused validation review. This technical outcome
is historical reference only: it is not successful Task completion and does
not make the removed implementation canonical.

During cancellation preparation on 2026-09-23, invocations of the legacy Task
and Workflow validators with `--help` unexpectedly ignored that argument and
executed their broad built-in validation catalogs. This was a second
unauthorized process deviation from the remediation's exact-validation scope.
Those outputs are excluded from evidence and changed no repository file. No
direct protected-target access was observed, but categorical protected-target
non-access during remediation cannot be certified. This later event is
disclosed without retroactive authorization, waiver, or reclassification as
compliant.

```text
CANCELLATION TYPE:
audited governance cancellation

TECHNICAL FAILURE:
NO

SECURITY DESIGN FAILURE:
NO

PROCESS FAILURE:
YES

ROOT CAUSE:
unauthorized/non-target-safe broad verification path entered during installation smoke

UNSATISFIED ACCEPTANCE CRITERIA:
60
61

SUCCESSFUL COMPLETION POSSIBLE UNDER CURRENT TASK:
NO

REPLACEMENT REQUIRED FOR SUCCESSFUL DELIVERY:
YES

HUMAN CANCELLATION AUTHORIZATION:
RECORDED 2026-09-23

HUMAN FINAL ACCEPTANCE:
NOT GRANTED

RETROACTIVE AUTHORIZATION:
NO

WAIVER:
NO
```

The 63/66 checklist result is preserved. The 35-file technical candidate was
archived outside the repository at
`D:\Dev\aio-044-cancelled-technical-reference` and then removed from `main`.
Its ZIP SHA-256 is
`8682d4fc500a9a2b70b9e944bb3b1a92bb5adba3a7e487542671f28249fea45f`.
The bundle is non-authoritative recovery/reference material only and includes
no protected target. It cannot serve as acceptance evidence for a replacement
Task.

A clean replacement is required for successful delivery. Creating AIO-045 is
not authorized by this cancellation, and any future replacement must obtain
its own design lock, implementation review, Security review, tests, package
evidence, Quality Gates, and Human Control decision.
