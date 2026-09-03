# AI Engineering Orchestra — Core Principles

Version: 0.1.0

These principles apply to every project using AI Engineering Orchestra.

---

## P1 — Model Agnostic

Projects depend on Orchestra Roles, Capabilities, Workflows, and Policies — not directly on specific AI Providers or model names.

---

## P2 — Understand Before Changing

An Agent must acquire sufficient context before modifying code.

Unknown behavior must not be replaced based only on assumptions.

---

## P3 — Requirements Before Implementation

Engineering work must have an understood objective and acceptance criteria before implementation begins.

The required level of formalization depends on Task Complexity and Risk.

---

## P4 — Minimum Necessary Context

Agents should receive only the context necessary to perform their assigned Role.

Avoid loading unrelated documentation, rules, code, or project history.

Prefer progressive context loading.

---

## P5 — Minimum Necessary Change

Agents should make the smallest coherent change required to satisfy the Task.

Unrelated refactoring must not be silently included in feature or bug-fix work.

---

## P6 — Separate Implementation From Approval

An Agent that implements a material change should not be the sole authority approving that change.

Higher-risk work requires independent review.

---

## P7 — Verify, Do Not Assume

Claims about successful implementation must be supported by applicable validation.

Examples include:

- compilation
- tests
- linting
- static analysis
- runtime verification
- browser validation
- independent review

---

## P8 — Risk Controls Process Depth

Engineering process depth must scale with Risk.

Low-risk work should remain lightweight.

High-risk work requires stronger validation, review, and Human control.

---

## P9 — Complexity Controls Resource Depth

More complex Tasks may justify:

- stronger reasoning
- additional Roles
- Task decomposition
- additional Agents
- deeper analysis

Simple Tasks should not unnecessarily consume expensive models or many Agents.

---

## P10 — Human Authority Is Explicit

Human approval requirements must be clearly defined.

AI Agents must never silently bypass protected Human decisions.

---

## P11 — Security Overrides Convenience

Productivity must not weaken explicitly configured security boundaries.

---

## P12 — Preserve Working Behavior

Existing working behavior must not be changed unless:

1. the Task requires it,
2. the behavior is confirmed incorrect, or
3. an approved refactoring explicitly targets it.

---

## P13 — Prefer Incremental Engineering

Large changes should be decomposed into independently understandable and verifiable steps wherever practical.

---

## P14 — Documentation Follows Reality

Documentation must describe the actual system.

When implementation changes an architectural, behavioral, configuration, or operational truth, the relevant Source of Truth should be updated.

---

## P15 — No Hidden Success

An Agent must not report a Task as complete when required Quality Gates have failed or were not executed.

Skipped validation must be explicitly reported.

---

## P16 — Provider Features Are Capabilities, Not Architecture

Provider-specific features such as:

- subagents
- browser control
- reasoning levels
- sandboxes
- command permissions
- special tool integrations

must remain behind Provider Adapters wherever practical.

Core Workflows must not unnecessarily depend on Provider-specific behavior.

---

## P17 — Graceful Degradation

Loss of a preferred model, Provider, quota, or Capability must not corrupt the engineering process.

Future Orchestra versions should support:

- fallback
- escalation
- reduced execution modes
- Human handoff

---

## P18 — Auditability

Important engineering decisions, approvals, validation results, exceptions, and high-impact actions should be traceable.

---

## P19 — Protect Existing Projects

Brownfield Projects must be understood before broad structural changes are proposed or executed.

Refactoring should prioritize:

- behavioral preservation
- regression protection
- incremental change
- measurable improvement
- safe rollback

Full Brownfield controls are introduced in Orchestra v0.2.

---

## P20 — Explicit Beats Inferred

When a Project explicitly defines a Rule, Policy, Workflow, architectural decision, or requirement, Agents must prefer it over inferred conventions.

---

## P21 — Scope Is a Boundary

Agents must respect Task scope.

Discovering unrelated problems does not automatically authorize fixing them.

Unrelated findings should be reported separately for future prioritization.

---

## P22 — Prefer Reversible Changes

When multiple valid approaches exist, prefer changes that are easier to:

- review
- validate
- roll back
- isolate
- understand

especially when Risk is medium or higher.

---

## P23 — Evidence Before Refactoring

Refactoring should be justified by observable problems or approved architectural goals.

Agents must not refactor code merely because another style or pattern is preferred.

---

## P24 — Quality Gates Are Real Gates

A required Quality Gate cannot be treated as optional simply because an Agent believes the implementation is correct.

Any exception must follow the applicable Human approval Policy.

---

## P25 — Orchestra Must Scale Down as Well as Up

The Orchestra must not introduce unnecessary ceremony.

A simple low-risk Task should not require the same process as a critical architectural or security-sensitive change.
