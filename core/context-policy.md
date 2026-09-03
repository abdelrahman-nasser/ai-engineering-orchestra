# AI Engineering Orchestra — Context Policy

Version: 0.1.0

This document defines how Agents should acquire, load, and use project context.

---

## 1. Purpose

AI Agents perform better when they receive the information relevant to their current responsibility without being overloaded by unrelated context.

The Orchestra therefore uses progressive context loading.

The goal is to provide:

- enough context to work correctly,
- enough context to understand dependencies,
- but not unnecessary information.

---

## 2. Core Rule

Load the minimum sufficient context required to safely perform the current Task and Role.

Agents should expand context only when the current information is insufficient.

---

## 3. Progressive Context Loading

Repository bootstrap is separate from normal Task context loading.

An Agent entering a repository for the first time may need to read the minimum framework and project entry instructions required to understand how context should be loaded.

Once that contract is understood, normal Task execution should begin with the Current Task and progressively load only relevant context.

Context should generally be loaded in layers.

Recommended order:

1. Current Task
2. Project Manifest
3. Relevant Project Rules
4. Applicable Workflow
5. Assigned Role instructions
6. Relevant Stack Modules
7. Relevant architecture decisions
8. Relevant implementation files
9. Related tests
10. Additional repository context when required

Agents should not automatically load every available document.

---

## 4. Task Context Comes First

The current Task defines the immediate objective.

An Agent should understand:

- objective
- scope
- acceptance criteria
- Risk
- Complexity
- expected outputs

before exploring unrelated parts of the repository.

---

## 5. Project Manifest

The Project Manifest provides high-level project configuration.

Default location:

.ai/project.yaml

Agents should use it to determine information such as:

- project type
- lifecycle
- default Workflow
- stack
- Risk defaults
- Quality Gate requirements
- Human approval requirements

---

## 6. Project Rules

Agents should load only Project Rules relevant to the current work.

Example:

An Angular UI change may require:

- frontend architecture Rules
- Angular Rules
- UI Rules
- testing Rules

It should not automatically require:

- database migration Rules
- infrastructure Rules
- unrelated backend Rules

unless the Task affects those areas.

---

## 7. Role Context

An Agent should receive instructions for its assigned Role.

Examples:

Developer Agent:

- implementation responsibilities
- scope restrictions
- validation responsibilities

Reviewer Agent:

- review responsibilities
- independence requirements
- reporting format

Role context should not unnecessarily include instructions intended only for other Roles.

---

## 8. Stack Context

Relevant Stack Modules should be loaded only when applicable.

Example:

Task affects:

- Angular frontend
- CSS

Load:

- Angular Stack Module
- relevant frontend Rules

Do not automatically load:

- .NET Stack Module
- SQL Server Stack Module
- Kubernetes Stack Module

unless required by the Task.

---

## 9. Architecture Context

Architecture Decisions should be loaded when the Task affects architecture or depends on an existing architectural constraint.

Approved Architecture Decision Records are authoritative Sources of Truth for the decisions they describe.

Agents must not silently violate an applicable ADR.

---

## 10. Repository Exploration

Agents may inspect additional repository files when necessary to understand:

- dependencies
- existing patterns
- call paths
- data flows
- integration points
- test coverage
- implementation behavior

Repository exploration should be purposeful.

Avoid broad exploration without a Task-related reason.

---

## 11. Brownfield Context

Brownfield Projects may require deeper initial discovery because existing behavior and conventions may not be documented.

However, discovery should remain primarily read-only until sufficient understanding has been established.

Full Brownfield onboarding policy is introduced in Orchestra v0.2.

---

## 12. Context Expansion

An Agent should expand its context when:

- required information is missing,
- implementation behavior is unclear,
- an unexpected dependency is discovered,
- an architectural constraint is encountered,
- tests reveal broader impact,
- a conflict exists between Sources of Truth.

Context expansion must remain relevant to the Task.

---

## 13. Context Boundaries

Agents must not treat access to information as authorization to modify it.

Example:

A frontend Agent may inspect backend API code to understand a contract.

That does not automatically authorize the Agent to modify the backend.

Task scope still applies.

---

## 14. Source of Truth Priority

When multiple documents contain similar information, Agents must prefer the explicitly defined Source of Truth.

Examples:

Project configuration:

.ai/project.yaml

Architecture decisions:

docs/adr/

Current Task requirements:

.ai/tasks/<task-id>/

Duplicated or historical documents must not silently override authoritative Sources of Truth.

---

## 15. Stale Context

Agents must be cautious with:

- old planning documents
- completed Task files
- outdated architecture diagrams
- stale comments
- obsolete README sections
- historical implementation notes

When stale information conflicts with current implementation or an authoritative Source of Truth, the conflict should be reported.

---

## 16. Context Isolation Between Agents

Different Agents may require different context for the same Task.

Example:

Architect Agent receives:

- requirements
- architecture
- relevant dependencies
- project constraints

Developer Agent receives:

- approved design
- implementation scope
- relevant source files
- tests
- coding Rules

Reviewer Agent receives:

- Task requirements
- relevant Rules
- implementation diff
- validation results

This reduces duplicated reasoning and confirmation bias.

---

## 17. Independent Review Context

A Reviewer should receive enough context to independently evaluate the implementation.

The Reviewer should not rely solely on the Implementer's explanation.

At minimum, review context should normally include:

- Task objective
- acceptance criteria
- applicable Rules
- relevant architecture decisions
- actual changes or diff
- validation results

---

## 18. Sensitive Context

Credentials, secrets, tokens, private keys, and unnecessary sensitive data should not be loaded into Agent context.

Future security Policies may define stronger controls.

---

## 19. Context Is Not Memory

Agents must not assume that information from previous sessions remains available or correct.

Important project knowledge must live in defined Sources of Truth.

The repository should not depend on a specific Agent remembering previous conversations.

---

## 20. Context Efficiency

The Orchestra should minimize repeated loading of large information sets when smaller references are sufficient.

Future versions may introduce:

- context indexes
- repository maps
- generated summaries
- dependency maps
- semantic retrieval
- Agent-specific context packs

These mechanisms must preserve the Source of Truth model.

---

## 21. Explicit Context Requests

An Agent may request additional context when necessary.

However, if the information can be discovered safely from the repository or project Sources of Truth, the Agent should prefer discovery over unnecessary Human interruption.

---

## 22. Context Completion Rule

Before implementation begins, the Agent must have enough context to answer:

1. What am I changing?
2. Why am I changing it?
3. What must remain unchanged?
4. What Rules apply?
5. What proves the Task is complete?

If these cannot be answered, additional context is required.
