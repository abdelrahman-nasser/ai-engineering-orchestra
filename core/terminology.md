# AI Engineering Orchestra — Terminology

Version: 0.1.0

This document defines the canonical terminology used by AI Engineering Orchestra.

All Orchestra documentation, configurations, workflows, adapters, and agents must use these terms consistently.

---

## Orchestra

The complete AI Engineering Orchestra framework.

The Orchestra defines how AI-assisted software engineering work is structured, delegated, validated, reviewed, and controlled.

It is independent of any specific AI provider, model, programming language, framework, or repository type.

---

## Provider

A system or platform forming an operational access boundary through which
models or Agent execution services may be supplied. For an Inference Option,
the Provider is the boundary through which its model is addressed. The
Provider need not be the organization that developed the model.

A Provider is not a Role or Actor and does not fulfil a Role. A Provider may
expose many models or supply many Agent Actors. A Human Actor has no Provider
requirement.

For example:

Claude != Architect

A Provider may supply an Agent Actor capable of fulfilling the Architect Role.

---

## Model

A Provider-addressable inference capability. A model identifier is meaningful
only within its Provider namespace; AIO v0.1 defines no global model namespace,
Model contract, catalog, family, version, tier, or capability registry.

Models may differ in:

- reasoning capability
- speed
- cost
- quota
- context size
- tool support
- agent capabilities

Projects should avoid directly depending on specific model names where possible.

---

## Inference Option

A Provider-neutral identity describing one caller/environment-accessible way to
address a model for inference.

The canonical Definition contains exactly opaque, case-sensitive `option_id`,
`provider_id`, and Provider-scoped `model_id`. `option_id` is unique only within
one supplied inventory. It remains the identity even when multiple options use
the same Provider/model pair.

An Inference Option does not describe a Runtime Option, Agent Service, tool or
session ownership, credentials, endpoint, capabilities, availability,
selection, authorization, or invocation. The canonical contract is defined in:

`core/inference-option-specification.md`

---

## Inference Option Availability Observation

An immutable, Provider-neutral, ephemeral value describing the currently known
availability state of one Inference Option within one caller-supplied evaluation
snapshot.

The state is exactly `available`, `unavailable`, or `unknown`; unknown is not
unavailable. A missing observation normalizes to unknown. Availability does not
change option identity and does not establish capability fit, selection,
authorization, execution, quota, price, Execution Mode satisfaction, or Runtime
Option availability. The canonical contract is defined in:

`core/inference-option-availability-specification.md`

---

## Runtime Option

A reserved boundary term for a future option describing where and how an Agent
loop executes and who owns tools, state, sessions, and lifecycle. No Runtime
Option contract, schema, inventory, or implementation exists in AIO v0.1.

Runtime Option is not Inference Option.

---

## Agent Service

A managed service that may own Agent sessions, tools, state, lifecycle,
scheduling, and model choice. Agent Service is distinct from bare model
inference and from Inference Option. No Agent Service contract or implementation
exists in AIO v0.1.

---

## Model Tier

**Deprecated.** Model Tier previously described the values `fast`, `standard`,
and `high` as one supposed capability or reasoning scale. Those values mix
latency and capability dimensions, so they are withdrawn and non-consumable.

Model Tier has no active semantics, schema, ordering, runtime behavior, or
routing behavior. It is not Execution Mode and is not a Provider reasoning
setting. AIO-028 adds only opaque Inference Option identity and separate
availability evidence; it establishes no replacement tier, capability scale,
requirement matching, reasoning mapping, or routing behavior. No replacement
enum is defined in v0.1.

---

## Agent

An AI participant that may be represented as an Actor with `kind: agent`.

Agent identity may be supplied as a candidate before assignment or execution.
Provider, model, runtime, reasoning configuration, availability, and execution
state are not part of the Actor contract.

When an Agent executes work, it may receive:

- a Task
- a Role
- relevant context
- applicable Rules
- applicable Policies
- available Capabilities

An Agent Actor does not receive execution authority merely by being an Agent.
A runtime execution remains separate from Actor identity.

A Role is reusable.

---

## Actor

A concrete, identifiable Human or Agent candidate capable of fulfilling a Role.

Actor identity is separate from availability, assignment, authority, permission,
approval, and execution. Actor answers **who**; Provider identifies a supplying
system or platform, and runtime describes **where or how** an Agent executes.

The canonical contract and matching semantics are defined in:

`core/actor-specification.md`

---

## Actor Competency

An exact, case-sensitive engineering competency identifier declared by an
Actor. Actor competencies use boolean set membership only; they have no levels,
weights, aliases, implications, or scores.

Actor competency is not runtime Capability, permission, authority, availability,
assignment, approval, or execution.

---

## Actor-Role Competency Coverage

Pure evidence that an Actor declares every engineering competency in a Role's
`required_capabilities` set.

Coverage does not select or assign an Actor and does not establish availability,
authority, permission, execution, Quality Gate PASS, or independent-review
satisfaction. A Role with no semantically approved required competencies is not
automatically matchable.

---

## Actor Availability Observation

An immutable, Provider-neutral, ephemeral value describing the currently known
availability state of one Actor within one caller-supplied evaluation snapshot.

The state is exactly `available`, `unavailable`, or `unknown`; unknown is not
unavailable. A missing observation normalizes to unknown. Availability does not
change Actor identity or competencies and does not establish eligibility,
Assignment, authority, permission, approval, or execution. The canonical
contract is defined in:

`core/actor-availability-specification.md`

---

## Actor Selection

Pure, deterministic, Provider-neutral resolution of one valid
Task/Workflow/Stage/Role responsibility against a caller-supplied Actor set and
availability snapshot, using exact competency coverage and availability facts
only.

Actor Selection produces decision evidence with exactly one of `selected`,
`ambiguous`, `indeterminate`, or `no_candidate` for valid input. It does not rank,
assign, authorize, reserve, or execute Actors. The canonical contract is defined
in:

`core/actor-selection-specification.md`

---

## Assignment

An immutable, Provider-neutral value binding one concrete Actor identity to one
Role required at one Stage of the Workflow explicitly governing one Task.

Assignment records an externally made responsibility choice. It does not select
or rank Actors, inspect availability, grant authority or permission, configure or
perform execution, establish Workflow state, or produce a Quality Gate result.

The responsibility key is `(task_id, workflow_id, stage_id, role_id)`;
`actor_id` is the selected value. The canonical contract is defined in:

`core/assignment-specification.md`

---

## Role

A reusable engineering responsibility and its required competencies.

Examples:

- Orchestrator
- Architect
- Developer
- Tester
- Reviewer
- Security Reviewer
- Documentation Agent

Roles are Provider-independent.

---

## Capability

An action or class of work an Agent or Provider can perform.

Examples:

- repository-read
- repository-write
- shell-execution
- browser-testing
- code-review
- deep-reasoning
- visual-analysis
- subagent-spawning

Future routing decisions should primarily use Capabilities instead of hardcoded Provider names.

---

## Task

A Task is the canonical unit of scoped work managed through AI Engineering Orchestra.

Examples:

- implement a feature
- fix a bug
- refactor a service
- update documentation
- review a pull request
- investigate a technical problem
- define an architecture or specification

A Task defines Task-specific intent, scope, Risk, Complexity, Execution Mode, acceptance criteria, Quality Gate requirements, Human control requirements, dependencies, review evidence, and lifecycle status.

The canonical Task contract is defined in:

`core/task-specification.md`

The default Project Task location is:

`.ai/tasks/`

The canonical reusable Task example is available at:

`templates/task/`

A Task must operate within the precedence, context, Human control, Policy, Rule, Workflow, and Quality Gate requirements that apply to the Project.

A Task may reference an applicable Workflow, but Workflow definitions and behavior remain owned by `workflows/`.

---

## Workflow

A reusable sequence of engineering stages used to complete a class of Task.

Examples:

- feature Workflow
- bugfix Workflow
- refactor Workflow
- architecture-change Workflow

The canonical Workflow contract is defined in:

`core/workflow-specification.md`

The canonical reusable Workflow definitions are maintained in:

`workflows/`

---

## Stage

One step inside a Workflow.

Examples:

- Analyze
- Plan
- Implement
- Test
- Review
- Validate

The canonical Stage contract is defined in:

`core/workflow-specification.md`

---

## Quality Gate

A condition that must be satisfied before work may progress.

Examples:

- build passes
- tests pass
- lint passes
- independent review passes

A Quality Gate is not simply a recommendation.

---

## Project Verification Check

A declarative project-owned definition of a mechanical repository check that can
be executed programmatically by AIO to collect mechanical evidence.
**Verification Check** is the preferred short form when context is unambiguous.

The declaration is owned by `core/project-manifest.md`, under
`.ai/project.yaml` → `verification.checks`.

A Check is not a Quality Gate, Task, Workflow Stage, Agent execution, Assignment,
Execution Contract, or approval mechanism. Its ID is not a Quality Gate ID, and
Verification Check PASS is not Quality Gate PASS. Mechanical evidence does not
itself establish governance approval or confer execution authority.

The contract, programmatic runner, and public `aio verify` composition execute
these declarations when the Human caller explicitly invokes full verification.
This mechanism does not grant execution authority to Agents or establish Quality
Gate results.

---

## Policy

A rule governing Agent behavior.

Policies may define:

- required approvals
- prohibited behavior
- security boundaries
- Agent limits
- quality requirements

Policies are stronger than suggestions.

---

## Organization Policy

A Policy defined above an individual Project and intended to apply across multiple Projects or repositories.

Examples may include:

- security requirements
- deployment restrictions
- review requirements
- compliance requirements
- protected Git operations

Organization Policies may establish constraints that Project configuration cannot weaken.

---

## User Policy

A Policy defined by the individual Human operating the Orchestra and intended to apply across their Projects or environments.

Examples may include:

- personal security restrictions
- approval requirements
- Agent autonomy limits

User Policies must follow the Orchestra precedence model.

---

## Rule

An instruction relevant to a project, technology, domain, or Task.

Rules may originate from:

- Orchestra Core
- Stack Module
- organization
- project
- Task

---

## Organization Rule

A reusable engineering Rule defined above an individual Project.

Examples may include:

- naming conventions
- documentation standards
- coding conventions
- repository conventions

Organization Rules apply unless a higher-precedence Policy or a permitted more-specific Rule overrides them.

---

## User Rule

A reusable Rule defined by an individual Human for their engineering environment.

Examples may include:

- preferred documentation practices
- personal workflow conventions
- local development preferences

User Rules must not weaken applicable protected Policies.

---

## Profile

A reusable collection of default configuration.

Examples:

- minimal
- standard
- critical
- SaaS
- enterprise

A Project may inherit from a Profile and override permitted settings.

---

## Stack Module

Reusable guidance for a specific technology.

Examples:

- .NET
- Angular
- SQL Server
- PostgreSQL
- Docker
- Kubernetes

Stack Modules must not contain project-specific business Rules.

---

## Provider Adapter

The integration layer between AI Engineering Orchestra and a specific AI Provider.

Adapters translate Orchestra concepts into Provider-specific configuration where necessary.

Example:

Orchestra Role

    ↓

Provider Adapter

    ↓

Provider-specific Agent configuration

---

## Project Manifest

The project's primary Orchestra configuration file.

Default location:

.ai/project.yaml

It defines Project-level Orchestra configuration and references the locations or defaults needed to govern Orchestra behavior for that Project.

The canonical Project Manifest contract is defined in `core/project-manifest.md`.

---

## Project Rule

A Rule that applies only to a specific project.

Examples:

- architecture conventions
- naming conventions
- repository restrictions
- business invariants
- deployment constraints

---

## Override

A project-specific modification of default Orchestra configuration where overrides are permitted.

Overrides may make Policies stricter.

Security-sensitive Policies may prohibit weakening through overrides.

---

## Orchestrator

The Role responsible for coordinating engineering work.

The Orchestrator may:

- analyze a Task
- classify complexity
- classify risk
- select Workflows
- assign Roles
- select required Capabilities
- coordinate Agents
- evaluate Quality Gates
- escalate work

The Orchestrator is not a specific AI Provider.

---

## Approval Level

A classification describing the degree of Human involvement required before work or an action may proceed.

Initial Approval Levels are:

- none
- review
- explicit
- protected

Their detailed behavior is defined in:

`core/human-control.md`

Approval Level is separate from Task risk and complexity.

---

## Permission Decision

A security decision describing whether an Agent operation may proceed.

Reserved initial Permission Decisions are:

- allow
- ask
- always-ask
- deny

Their security precedence is:

deny

>

always-ask

>

ask

>

allow

Permission Decision is defined conceptually in v0.1.

Full command permission enforcement is planned for Orchestra v0.2.

---

## Human

The ultimate authority over the Orchestra.

Human approval may be required for operations such as:

- production deployment
- critical changes
- security exceptions
- destructive database migrations
- protected Git operations
- architecture exceptions

The Orchestra must never design a Workflow where AI authority silently exceeds explicitly defined Human authority.

---

## Complexity

A descriptive property of what the work inherently demands: expected reasoning
difficulty, engineering depth, coordination, decomposition, and problem
complexity.

Initial levels:

- low
- medium
- high
- critical

Complexity is independent from Risk and Execution Mode. It is not a model tier,
Provider reasoning setting, authorization level, approval policy, or Workflow
selector. No Complexity value automatically determines any of those concepts.

---

## Risk

The potential impact if Task execution is wrong.

Initial levels:

- low
- medium
- high
- critical

A Task may have low Complexity but critical Risk. Risk may cause stronger
validation, review, Human oversight, or safety controls only when an applicable
Policy or other authoritative rule says so. Risk does not automatically select
an Execution Mode, Workflow, model, or Provider option.

---

## Execution Mode

A Provider-neutral, Task-wide minimum required engineering-execution posture
within the already selected Workflow. It governs cumulative process depth,
rigor, analysis and decomposition, evidence discipline, and bounded
self-direction. It is neither an exact ceiling nor a Task classification.

The modes have this normative process-depth order:

    lite < standard < deep < critical

A mode satisfies its own minimum and every lower minimum; it does not satisfy a
higher minimum. The order describes process depth only, not authority, approval,
cost, latency, model strength, or outcome quality.

Each description is a cumulative minimum obligation, not a maximum. A lighter
mode does not require the additional obligations named by higher modes, but it
never prohibits extra rigor, analysis, decomposition, evidence, validation, or
bounded self-direction.

- `lite`: the smallest floor for well-bounded work, requiring a coherent direct
  path, sufficient relevant context and evidence, proportionate validation, and
  the decomposition needed for coherence. Expected bounded self-direction is
  narrow.
- `standard`: includes `lite` plus explicit planning, disciplined execution,
  validation, self-checking, routine bounded self-direction, and explicit
  evidence for material claims.
- `deep`: `standard` plus deliberate decomposition, trade-off and edge-case
  analysis, broader evidence gathering, probing validation, and sustained
  bounded self-direction.
- `critical`: `deep` plus the strongest scrutiny, assumption challenge, failure
  and safety analysis, traceability, corroboration, the strongest bounded
  self-direction, and conservative escalation of unresolved uncertainty.

Expected autonomy means bounded self-direction within already established
scope, authority, permissions, Policies, and Human controls. Execution Mode
applies to both Human and Agent Actors and never grants authority.

All responsibilities inherit the effective Task mode. Stage-, Role-, and
responsibility-specific overrides are unsupported in v0.1, and mode is not
inferred from Stage or Role identity, name, or capabilities.

Workflow and Execution Mode are orthogonal. Mode changes only the depth applied
inside existing choreography. It does not:

- select a Workflow;
- add, remove, or reorder Workflow Stages;
- change required Roles, Quality Gates, or Human-control checkpoints;
- establish a Quality Gate result or satisfy Human approval;
- grant permission or authorization; or
- map to a Provider, model, runtime, or Provider reasoning control.

Complexity, Risk, Workflow, Stage, and Role do not automatically determine
Execution Mode. An explicit Task value takes precedence over the Project default.

---

## Greenfield Project

A new project where architecture and implementation are being created from the beginning.

---

## Brownfield Project

An existing project with established behavior, architecture, code, dependencies, and technical debt.

Full Brownfield onboarding and analysis is planned for Orchestra v0.2.

---

## Modernization Project

An existing Project undergoing deliberate architectural, platform, technology, or engineering improvement.

Examples may include:

- framework upgrades
- platform migrations
- architectural restructuring
- CI/CD introduction
- test coverage improvement
- monolith decomposition
- dependency modernization

Modernization must be planned and incremental.

It is not authorization for uncontrolled refactoring or broad rewrites.

---

## Maintenance Project

An established Project primarily focused on preserving stability while receiving ongoing changes.

Typical work may include:

- bug fixes
- small features
- dependency updates
- operational improvements
- security updates
- support changes

Maintenance does not prohibit architectural improvement, but stability is the default expectation.

---

## Source of Truth

The authoritative location for a specific category of information.

Agents must prefer Sources of Truth over assumptions or duplicated documentation.
