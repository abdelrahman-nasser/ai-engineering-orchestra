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

A system or platform capable of supplying AI agents or models.

Examples may include:

- Claude
- Codex
- Antigravity
- future AI providers

A Provider is not a Role or Actor and does not fulfil a Role. A Provider may
supply many Agent Actors. A Human Actor has no Provider requirement.

For example:

Claude != Architect

A Provider may supply an Agent Actor capable of fulfilling the Architect Role.

---

## Model

A specific AI model available through a Provider.

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

## Model Tier

An abstract capability or reasoning level.

Initial tiers:

- fast
- standard
- high

Provider Adapters may map tiers to actual Provider models.

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

An estimate of how difficult a Task is to understand and implement.

Initial levels:

- low
- medium
- high
- critical

Complexity is independent from Risk.

---

## Risk

The potential impact if a Task is implemented incorrectly.

Initial levels:

- low
- medium
- high
- critical

A Task may have low Complexity but critical Risk.

---

## Execution Mode

The depth of engineering process applied to a Task.

Initial modes:

- lite
- standard
- deep
- critical

Execution Mode influences:

- number of Stages
- review depth
- model capability
- Quality Gates
- Human approval

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
