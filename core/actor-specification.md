# AI Engineering Orchestra - Actor Specification

Version: 0.1.0

This document defines the canonical Actor contract for AI Engineering Orchestra
v0.1.

---

## 1. Purpose

An Actor is a concrete, identifiable Human or Agent candidate capable of
fulfilling a Role.

An Actor answers **who** may be considered. It does not state that the candidate
is available, assigned, authorized, permitted, approved, or executing.

```text
Actor identity
!= availability
!= assignment
!= authority
!= permission
!= approval
!= execution
```

---

## 2. Architectural Boundaries

The following concepts remain separate:

- **Role**: reusable responsibility and required competencies.
- **Actor**: concrete potential fulfiller.
- **Agent**: the AI kind of Actor.
- **Human**: the Human kind of Actor.
- **Provider**: a system or platform that may supply models or Agent Actors.
- **Runtime**: where and how an Agent executes.

A Provider is not the fulfiller of a Role. A Provider may supply many Agent
Actors, while a Human Actor has no Provider requirement. Runtime and Provider
details do not form part of Actor identity.

An Actor does not declare `roles`. Actor-to-Role compatibility is derived from
competency coverage.

---

## 3. Canonical Actor Contract

The v0.1 Actor contract contains exactly these fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `id` | Yes | Stable Actor identity within the supplied Actor set or assignment context |
| `kind` | Yes | Actor category: `human` or `agent` |
| `competencies` | Yes | Engineering competencies declared by the Actor |

No other field is part of the contract.

```yaml
id: agent-engineer-1
kind: agent
competencies:
  - software-implementation
  - source-code-analysis
  - automated-testing
  - evidence-evaluation
```

### `id`

`id` is required, nonempty, opaque, and stable within the supplied Actor set or
assignment context. Actor IDs must be unique within that set or context.

The identifier does not encode a Provider, model, runtime, or capability claim.
The single-Actor schema cannot establish cross-document uniqueness; callers that
supply an Actor set remain responsible for that semantic invariant.

### `kind`

`kind` is required and has exactly two values:

- `human`
- `agent`

The value classifies the Actor. It does not grant authority.

```text
kind: human != Human approval authority
kind: agent != execution authority
```

### `competencies`

`competencies` is a required, nonempty set represented as an array of unique,
nonempty, case-sensitive strings.

Each value is an exact engineering competency identifier used for Role
matching. A competency is boolean membership only. AIO-021 defines no levels,
weights, aliases, implications, fuzzy matching, or scores.

The initial matching vocabulary comes from the current canonical Roles:

- `architecture-analysis`
- `requirements-analysis`
- `source-code-analysis`
- `evidence-evaluation`
- `documentation-analysis`
- `security-analysis`
- `risk-analysis`
- `software-implementation`
- `automated-testing`

The Actor schema deliberately does not enumerate this list. Unknown or
misspelled competencies remain ordinary declared strings and simply fail to
cover a different required Role competency.

Although the Role contract retains the historical field name
`required_capabilities`, its values are engineering competencies. Actor uses the
more precise field name `competencies` so operational abilities such as shell or
tool execution are not confused with Role matching.

---

## 4. Actor-Role Competency Coverage

Actor-role competency coverage is a pure comparison over an already-normalized
Actor and Role:

```text
missing =
    set(Role.required_capabilities)
    -
    set(Actor.competencies)
```

Coverage succeeds if and only if the Role has at least one semantically approved
required competency and `missing` is empty.

Matching is exact and case-sensitive. Extra Actor competencies do not prevent
coverage. Actor kind does not alter the comparison. Missing competencies are
reported in deterministic case-sensitive sort order.

A Role whose `required_capabilities` is empty is not automatically matchable.
The evaluator returns an incompatible result with the diagnostic
`role_required_capabilities_empty` and no missing competencies. This preserves
the distinction between an absent semantic requirement and universal
eligibility without changing the current Role schema.

The reusable evaluator is:

`engineering_orchestration.actor_coverage.evaluate_actor_role_coverage`

It consumes already-normalized data. It does not discover Role files, parse Role
Markdown, scan repositories, load Actor catalogs, consult Providers, or inspect
availability.

The result contains only:

- `actor_id`
- `role_id`
- `compatible`
- `missing_competencies`
- `diagnostic`

It contains no score, rank, recommendation, assignment, authority, availability,
execution decision, or Quality Gate result.

---

## 5. Human and Agent Symmetry

Human and Agent Actors use the same contract and coverage rule.

```yaml
id: human-engineer-1
kind: human
competencies:
  - software-implementation
  - source-code-analysis
  - automated-testing
  - evidence-evaluation
```

```yaml
id: ai-engineer-1
kind: agent
competencies:
  - software-implementation
  - source-code-analysis
  - automated-testing
  - evidence-evaluation
```

Neither example needs Provider, model, runtime, or reasoning configuration.

---

## 6. Authority, Permission, and Quality Boundaries

Competency coverage means only that the Actor declares every competency required
by the Role.

```text
Actor competency-compatible != assigned
Actor competency-compatible != available
Actor competency-compatible != authorized
Actor competency-compatible != permitted
Actor competency-compatible != executing
Actor competency-compatible != Quality Gate PASS
Actor competency-compatible != independent review satisfied
```

Competency is not permission. For example, an Actor declaring
`software-implementation` does not thereby receive filesystem, shell, network,
credential, or execution permission.

Human Control remains the authority for Human approval requirements. Actor kind
does not infer approval authority. Likewise, Agent kind does not infer execution
authority.

Actor identity makes later separation checks possible. In particular, equal
implementer and reviewer Actor IDs cannot satisfy independent-review separation.
Unequal IDs alone do not establish that the Quality Gate passed. AIO-021 does not
evaluate Quality Gates or reviewer independence.

---

## 7. Ownership and Persistence

The Actor contract is framework-owned. Actual Actor inventories are expected to
be primarily environment-owned, organization-owned, user-owned, or supplied by a
runtime.

Projects define Role requirements. They should not commit volatile Provider
availability, quotas, credentials, or personal data as canonical Actor data.
AIO-021 defines no `.ai/actors/` directory, Actor catalog, Actor profile, or Actor
instance contract.

Future selection may consider both competency compatibility and runtime
availability. Availability remains runtime state and is not part of Actor
identity.

---

## 8. Exclusions

The Actor contract does not define or contain:

- Role assignments or Assignment persistence
- availability, status, cost, or quota
- authority, permissions, approval state, tools, or credentials
- Provider, model, runtime, reasoning, or execution policy
- competency levels, aliases, hierarchy, scoring, or ranking
- Actor catalogs, profiles, or canonical Actor instances
- Task complexity assessment
- Quality Gate or review results
- Agent invocation or CLI commands

A capability registry is not justified by the current small, consistent
vocabulary. Aliases, hierarchy, extension governance, or overlapping
project-defined terms may provide evidence for one later.

---

## 9. Structural Authority

The machine-readable structural schema is:

`schemas/actor.schema.json`

This specification is the semantic authority. The schema is subordinate when a
structurally valid value still violates a semantic boundary described here.
