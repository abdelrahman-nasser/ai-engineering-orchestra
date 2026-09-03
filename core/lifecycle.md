# AI Engineering Orchestra — Project Lifecycle

Version: 0.1.0

This document defines the project lifecycle concepts used by AI Engineering Orchestra.

---

## 1. Purpose

The Orchestra must behave differently depending on whether it is working with:

- a new project,
- an established project,
- a project under active refactoring,
- or a project in maintenance mode.

The lifecycle model gives the Orchestra a consistent way to reason about project state.

---

## 2. Lifecycle Types

The initial lifecycle types are:

- greenfield
- brownfield
- modernization
- maintenance

---

## 3. Greenfield

A Greenfield Project is a new project where the architecture, codebase, workflows, and conventions are still being established.

Typical characteristics:

- little or no existing production behavior
- architecture can still change relatively cheaply
- project rules are being defined
- initial quality gates are being established

The Orchestra may be more proactive in architecture design during Greenfield work.

---

## 4. Brownfield

A Brownfield Project is an existing project with established code, behavior, dependencies, users, integrations, or production history.

Typical characteristics:

- existing behavior must be preserved
- undocumented conventions may exist
- technical debt may exist
- tests may be incomplete
- architecture may not match current best practices
- changes may have hidden side effects

The Orchestra must apply stronger caution before broad changes.

Full Brownfield onboarding, analysis, health reporting, and safe refactoring planning are introduced in Orchestra v0.2.

---

## 5. Modernization

A Modernization Project is an existing project undergoing deliberate architectural, platform, or technology improvement.

Examples:

- .NET Framework to modern .NET
- Angular legacy architecture to modern Angular
- monolith decomposition
- database modernization
- CI/CD introduction
- test coverage improvement

Modernization is not the same as uncontrolled refactoring.

Modernization work should be:

- phased
- measurable
- reversible where possible
- protected by tests
- aligned with an approved roadmap

---

## 6. Maintenance

A Maintenance Project is an established project primarily receiving:

- bug fixes
- small features
- operational improvements
- security updates
- dependency updates

The default expectation is stability rather than architectural change.

---

## 7. Lifecycle Does Not Replace Task Classification

Project lifecycle and Task classification are separate concepts.

Example:

Project lifecycle:

maintenance

Task:

critical authentication change

The Task may still require a deep or critical Workflow even though the project is in Maintenance mode.

---

## 8. Lifecycle Influences Default Behavior

Lifecycle may influence:

- default Risk assumptions
- required discovery depth
- refactoring tolerance
- documentation requirements
- review depth
- migration strategy
- rollback expectations

---

## 9. Brownfield Protection Rule

For Brownfield and Modernization Projects:

The Orchestra must prefer:

1. understanding current behavior,
2. protecting current behavior,
3. making small changes,
4. validating each phase,
5. avoiding unnecessary rewrites.

---

## 10. Architecture Change Sensitivity

Architecture changes are generally easier to approve in Greenfield Projects than in Brownfield or Maintenance Projects.

The Orchestra should therefore consider lifecycle when evaluating architectural change proposals.

---

## 11. Lifecycle Is Explicit

The Project Manifest should explicitly declare lifecycle.

Example:

```yaml
project:
  lifecycle: greenfield
