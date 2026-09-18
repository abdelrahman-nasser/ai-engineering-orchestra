# AIO-029 Context

## Current limitation

AIO can represent logical Human and Agent Actors, select and assign Actors for
Workflow responsibilities, and validate caller-supplied Inference Option
identity and availability. It cannot yet represent the distinct configured
execution surface through which an Agent execution can run or be delegated.

The approved post-AIO-028 topology investigation established that these are
separate concepts:

```text
Actor
!= executable Agent definition
!= Agent Runtime Option
!= Inference Option
!= execution instance
```

It also found no justification for a direct Actor-to-Runtime or
Actor-to-Inference relation. AIO-029 therefore adds Runtime Option identity and
availability only.

## Design lock

The canonical term is **Agent Runtime Option**. **Runtime Option** is acceptable
short prose only after that term has been established. The Definition is:

> An Agent Runtime Option is an opaque, caller/environment-supplied configured
> execution surface through which an Agent execution can be run or delegated.

The Definition contains exactly:

```yaml
runtime_option_id: primary-agent-runtime
```

`runtime_option_id` is required, nonempty, opaque, exact, case-sensitive, and
unique within one caller-supplied sequence. It does not encode a Provider,
model, framework, runtime type, implementation, owner, capability, credential,
endpoint, process, session, or invocation.

Availability is a distinct immutable, ephemeral observation:

```yaml
runtime_option_id: primary-agent-runtime
state: available
```

The states are exactly `available`, `unavailable`, and `unknown`; unknown is not
unavailable. A known Runtime Option without an observation normalizes to
`unknown`. Unknown references and identical or conflicting duplicate
observations invalidate the complete snapshot without partial normalized
output. Duplicate Runtime Option IDs invalidate the foundational inventory.
Deterministic sorting is canonicalization only and never preference.

## Architectural boundaries

An Actor remains logical identity with exactly `id`, `kind`, and
`competencies`; it is not an executable Agent definition. An Agent Runtime
Option identifies an execution/Agent-loop boundary, not an Actor, execution
instance, session, invocation, Inference Option, Agent Service, authorization,
or credential.

A concrete Runtime Option may own or delegate some combination of execution-loop
lifecycle, environment, tools, state, sessions, scheduling, and inference
access. The Core contract does not claim that every option owns all of them and
does not expose those concerns as fields.

A Provider is an operational access boundary for inference or external service
access. An Agent Runtime Option is the execution surface running or delegating
an Agent loop. One external product may participate in both concepts without
collapsing their Core identities.

An Agent Service is only a descriptive external managed implementation that may
expose or realize one or more Agent Runtime Options. AIO-029 creates no Agent
Service subtype or schema.

A Runtime Option may expose zero externally selectable Inference Options because
inference may be selected internally, bound in external Agent configuration, or
hidden behind a managed service. Runtime-to-Inference compatibility remains
future work; absence of compatibility edges must not imply inability to execute.

The caller may supply only the Runtime and Inference Option candidates
applicable to the Agent Actor or execution context being evaluated. Core does
not yet validate why that scope is correct and defines no global Actor topology.
Human Actors require no Agent Runtime Option.

## Ownership and persistence

The framework owns contracts and validation. The environment owns actual
configured Agent execution surfaces. The caller supplies definitions and
observations for one evaluation context. A future adapter may translate native
runtime facts, but AIO-029 implements no adapter or discovery.

Definitions and observations remain in memory. There is no project runtime
catalog, Project Manifest section, cache, history, network access, or credential
storage.

## Workflow and Human control

The `architecture-change` Workflow governs this implementation Task. Complexity
is `high` because the work introduces two semantic authorities, two schemas,
cross-value validation, packaging, and architecture boundaries. Risk is
`medium` because the foundation shapes future execution work but remains
additive, pure, non-authorizing, network-free, and non-invoking. `deep` is
explicitly selected for boundary analysis, edge-case coverage, packaging proof,
and independent review.

An Architect locked the design before implementation. Software Engineer
workstreams implemented it, and genuinely separate Reviewer and Architect
executions inspected the complete worktree. During the review stage, work
stopped at the Human Control checkpoint with the Task `in_progress` and no
commit authorized. On 2026-09-19, the Human explicitly approved AIO-029 closure
and its single approved commit. That approval did not authorize AIO-030, a
push, or any compatibility, selection, authorization, or invocation work.
