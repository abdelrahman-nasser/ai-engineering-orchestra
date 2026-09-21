# AIO-042 Context

## Authorization and verified baseline

On 2026-09-21, the Human explicitly authorized AIO-042 Task creation,
Architect design lock, separate Security design approval before implementation,
implementation, target-safe validation, final Architect and Security reviews,
fresh independent review, Quality Gate evaluation, and preparation of the
Human Control checkpoint.

That implementation authorization stopped at Human Control. On 2026-09-21, the
Human then explicitly approved the architecture, schema, security boundary, and
final acceptance and authorized Task closure, explicit staging of only the
reviewed AIO-042 paths, and exactly one local closure commit on `main`.

The final approval does not authorize push, merge, tag, release, publication,
AIO-043, lifecycle, authorization consumption, replay protection, tool binding,
dispatch, invocation, persistence, AIO-030, Full Control Center/UI work, or
protected-target access.

The verified baseline is clean `main` at
`5b1fcfe14f0302096fc72e561d8c7b4cfe9bc6cd`. The worktree and index were clean,
AIO-041 was completed with 49/49 criteria and recorded Human approval, and
AIO-042 was absent before authorized creation.

AIO-030 remains parked on `feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not an AIO-042 dependency.
The separate Full Control Center and UI track is outside this Task.

## Architectural purpose

AIO-041 defines immutable declarative intent. Full eleven-field Contract value
equality is deliberately not occurrence identity. AIO-042 adds the next bounded
Core layer: one immutable Agent Execution Run occurrence identity binding one
caller-supplied opaque `run_id` to one exact nested Agent Execution Contract.

The Run contains exactly these fields, in order:

```text
run_id
contract
```

One Run denotes one concrete attempt. A semantic retry uses a new `run_id`; a
transport retry representing the same occurrence retains the same `run_id`.
Run lifecycle is a separate future foundation.

## Canonical preparation boundary

Canonical preparation requires an intrinsically valid intended Contract, a
fresh caller-supplied AIO-040 result that is observably coherent, valid, and
`satisfied`, a freshly resolved effective Task-wide Execution Mode, fresh
AIO-041 Contract preparation, and exact fresh/intended Contract equality.

Freshness means that the caller supplied new or current parent observations and
evidence. Calling AIO-040 again over cached parent results does not establish
freshness, and AIO-042 cannot authenticate temporal truth.

Blocked, unresolved, invalid, incoherent, wrong-type, or mismatched input
produces no Run. Direct construction and intrinsic validation prove only value
semantics; they do not prove canonical preparation, freshness, operational
Run-ID uniqueness, authority, or readiness.

## Identity, collision, and security boundary

The caller or execution coordinator owns Run-ID allocation and non-reuse within
its operational namespace. Core validates an exact, case-sensitive, nonempty
opaque string. It does not generate an ID, require UUID syntax, normalize the
value, use randomness, or prove global uniqueness or authenticity.

Full `(run_id, contract)` equality is representation equality. `run_id` is the
logical occurrence identity. Equal ID and Contract values represent the same
Run again. Equal IDs with different Contracts are an identity-binding conflict
in an authoritative namespace, but a single-value validator cannot discover an
unseen external collision. Equal Contracts with different IDs are distinct
Runs.

Run existence is not authorization, authorization consumption, replay
protection, current permission, tool binding, dispatch, invocation, or success.
AIO-039 remains caller-attested evidence. AIO-042 does not reinterpret its
`provenance_reference` as a grant, authorization, or token identity.

Fresh facts may change immediately after preparation, so TOCTOU remains
unsolved. A future separately authorized dispatch-admission layer must own a
just-in-time check or trusted bounded preflight plus atomic authorization
consumption and dispatch admission. AIO-042 implements none of that work.

## Schema and package boundary

The Run has a closed two-field Draft 2020-12 schema. Its nested `contract`
property references the packaged AIO-041 Contract schema instead of duplicating
the eleven Contract properties. Schema resolution is local and offline from
source, editable installation, and normal wheel installation. No canonical
HTTPS schema identifier may cause network retrieval, and resolution must not
depend on the current working directory or an external source checkout.

## Purity and protected-target boundary

Run preparation and validation are deterministic, supplied-data-only functions.
They perform no filesystem, protected-resource, network, subprocess, clock,
randomness, database, cache, discovery, tool, Provider, dispatch, or invocation
I/O. Tests and fixtures use synthetic lexical resources only.

The protected target must not be opened, read, searched, listed, statted,
hashed, resolved, permission-inspected, or used as a fixture. Broad Task
validation, Workflow-catalog enumeration, repository-wide verification, broad
Markdown traversal, and non-target-safe package smoke remain excluded.

## Governance and classification

The explicit `architecture-change` Workflow is retained from the validated
AIO-041 precedent. Its applicable Task types are advisory. The Workflow requires
Architect design and final review, independent Reviewer evaluation,
`documentation_consistency` and `independent_review`, and a Human Control
checkpoint. A separate Security Reviewer is additionally required before and
after implementation because Run identity could otherwise be misread as
authority or execution state.

`complexity: high` reflects the first execution-occurrence identity, fresh
preparation chain, exact Contract comparison, collision semantics, nested
cross-schema packaging, and identity/lifecycle separation. `risk: high`
reflects the harm of treating Run existence as authority or execution.
`execution.mode: deep` is the explicit engineering-process minimum and grants no
runtime authority.

The Task is `completed` with all 56 acceptance criteria satisfied following
explicit Human architecture, schema, security-boundary, and final acceptance
approval on 2026-09-21. This governance approval does not authorize an execution
occurrence, consume authorization, add replay protection, permit dispatch, or
permit Agent invocation.
