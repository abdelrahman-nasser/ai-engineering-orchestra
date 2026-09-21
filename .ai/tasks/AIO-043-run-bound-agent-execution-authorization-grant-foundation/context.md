# AIO-043 Context

## Authorization and verified baseline

On 2026-09-22, the Human explicitly authorized AIO-043 Task creation,
Architect design lock, dedicated Security/trust-boundary design approval before
implementation, implementation, target-safe validation, final Architect and
Security reviews, fresh independent review, Quality Gate evaluation, and
preparation of the Human Control checkpoint.

That implementation authorization stopped at Human Control. On 2026-09-22, a
subsequent direct Human final approval authorized architecture, schema,
security/trust-boundary, issuer/domain-model, lifetime/time-model, and final
acceptance approval; Task closure; explicit staging of the reviewed AIO-043
paths; and exactly one local closure commit on `main`. It did not authorize
push, merge, tag, release, publication, AIO-044, real Grant issuance or
authentication, consumption, replay protection, persistence, tool binding,
dispatch admission, dispatch, or real invocation.

The verified baseline is clean `main` at
`b175bfc116b8ad1629dea42f08beca6ffd864f06`. The worktree and index were clean,
AIO-042 was completed with 56/56 criteria and recorded Human approval, and
AIO-043 was absent before authorized creation.

AIO-030 remains parked on `feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187` and is not an AIO-043 dependency.
The separate Full Control Center/UI track remains outside this Task.

## Architectural purpose

AIO-039 supplies caller-attested authorization evidence. AIO-040 composes
diagnostic prerequisites. AIO-041 declares exact action intent. AIO-042 binds
that intent to one immutable Run occurrence. None supplies an authenticated,
issuer-scoped, domain-bound, time-bounded positive authority artifact.

AIO-043 adds that next bounded Core value: **Agent Execution Authorization
Grant**, categorized as a positive authority artifact. It is issued through a
future external authenticated and integrity-protected authority-producer
boundary, uniquely identified within one issuer/domain namespace, bound to one
exact nested Run, and intended for at most one future atomic consumption toward
dispatch admission.

The Grant itself does not prove current prerequisites, authenticate its issuer,
consume authority, provide replay protection, admit dispatch, or invoke an
Agent.

## Exact value, identity, and Run binding

The Grant contains exactly these fields, in order:

```text
grant_id
run
authorization_domain_id
issuer_kind
issuer_id
provenance_reference
issued_at
expires_at
```

The exact complete nested `AgentExecutionRun` transitively binds the Run ID and
all Contract fields. A bare Run ID is insufficient. The effective Grant
identity is:

```text
(authorization_domain_id, issuer_kind, issuer_id, grant_id)
```

`grant_id`, `authorization_domain_id`, `issuer_id`, and
`provenance_reference` are exact, opaque, case-sensitive, nonempty strings.
The external producer allocates `grant_id` and owns non-reuse inside the
composite namespace. Core neither generates it nor proves global uniqueness.
`authorization_domain_id` identifies the future consumer/audience and shared
consumption-ledger domain; it is never inferred from `environment_id`.

`issuer_kind` is exactly `human` or `policy`. These issuer fields deliberately
do not alias AIO-039's caller-attested authority fields. Provenance is audit-only
and is neither identity nor authentication proof.

## Positive-only, time, and cardinality semantics

Grant existence is the positive artifact, so the value has no `state`,
`authenticated`, `verified`, consumed, reusable, revocation, or lifecycle
field. At-most-one-use is a fixed semantic invariant rather than a flag or
counter; AIO-043 does not enforce consumption.

Timestamps use the exact grammar
`YYYY-MM-DDTHH:MM:SS[.fraction]Z`: uppercase `T` and `Z`, Gregorian years
`0001` through `9999`, seconds `00` through `59`, and an optional one-to-six
ASCII-digit fractional part. Runtime validation checks calendar validity and
requires `issued_at < expires_at`. It never reads a clock, proves currentness,
adds skew tolerance, or evaluates revocation.

Within one supplied authorization-domain snapshot, one Grant binds exactly one
Run and one Run has zero or at most one accepted Grant. Exact duplicates,
rebound Grant identities, rebound Run IDs, multiple Grants for one exact Run,
and Human/policy composition fail closed. There is no first-, last-, latest-,
Human-, policy-, shorter-, or longer-expiry winner. New authority requires a new
Run and new Grant in v1.

## Validation, schema, and trust boundary

Intrinsic validation checks only exact value type, all eight fields, complete
nested Run validity, issuer kind, timestamp grammar/calendar validity, and
static time ordering. Domain-scoped collection validation captures its iterable
once, requires one explicit exact domain, validates every value, rejects all
collisions/cardinality violations atomically, and canonically orders valid
Grants by `(authorization_domain_id, issuer_kind, issuer_id, grant_id)`.

The closed Draft 2020-12 schema owns the exact eight-field JSON structure and
references the packaged Run schema. The explicit offline registry also includes
the transitive Contract schema. Missing or unknown references fail closed with
no network, current-working-directory, active-project, or external-checkout
fallback.

An intrinsically or structurally valid directly constructed Grant is not an
operationally trusted Grant. Operational trust requires an external producer to
authenticate and authorize the issuer, bind that identity to `issuer_id`, bind
the complete payload to the correct domain and Run, and integrity-protect all
eight fields. AIO-043 neither implements nor simulates that boundary.

## Purity and protected-target boundary

Validation is deterministic and supplied-data-only. It performs no filesystem
or protected-resource access, network, subprocess, system-clock, randomness,
database, cache, queue, store, tool discovery, authority-service call,
consumption, dispatch, or invocation. Tests and fixtures use only synthetic
lexical resources.

The protected target must not be opened, read, searched, listed, statted,
hashed, resolved, permission-inspected, or used as a fixture. Broad Task
validation, Workflow-catalog enumeration, repository-wide verification, broad
Markdown traversal, and non-target-safe package smoke remain excluded.

## Governance and classification

The explicit `architecture-change` Workflow is retained from AIO-041 and
AIO-042 precedent; its applicability labels are advisory. It requires Architect
design/final review, an independent Reviewer, `documentation_consistency`,
`independent_review`, and a Human Control checkpoint. The Task additionally
requires separate Security design/final review.

`complexity: high` reflects the first authority-bearing artifact, full Run
binding, scoped identities, time grammar, collection collision semantics, and
nested package references. `risk: critical` reflects the security impact of a
false-positive Grant interpretation. Explicit `execution.mode: critical`
requires maximum engineering rigor only and grants no runtime authority.

The Task is `completed`. Human architecture, schema, security/trust-boundary,
issuer/domain-model, lifetime/time-model, and final acceptance approvals were
recorded on 2026-09-22. This lifecycle approval does not issue or authenticate
a Grant, consume authorization, provide replay protection, or admit dispatch.
