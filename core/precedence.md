# AI Engineering Orchestra — Precedence Model

Version: 0.1.0

This document defines how conflicting instructions, Rules, Policies, and configuration are resolved.

---

## 1. Purpose

AI Engineering Orchestra may receive instructions from multiple layers.

A deterministic precedence model is required so Agents do not guess which instruction should win.

---

## 2. General Precedence Order

The Orchestra resolves instructions using both authority and specificity.

Unless another protected rule explicitly applies, the following order is used from highest to lowest precedence:

1. Protected security, safety, and platform Policies
2. Orchestra Core Principles and protected Core Policies
3. Explicit Human instruction for the current Task
4. Task-specific Policies
5. Project Policies
6. Organization or user Policies
7. Task-specific Rules and acceptance criteria
8. Project Rules
9. Organization or user Rules
10. Stack Module Rules
11. Workflow Rules
12. Role instructions
13. Profile defaults
14. Orchestra Core configuration defaults
15. Provider defaults

Higher-precedence instructions override lower-precedence instructions when both are valid and applicable.

This hierarchy distinguishes between:

- protected Policies,
- Core Principles,
- ordinary Policies,
- Rules,
- and configuration defaults.

Orchestra Core Principles must not be interpreted as ordinary low-priority defaults.

Protected Policies cannot be weakened by lower-precedence configuration.

---

## 3. Human Instructions

Explicit Human instructions have high precedence for normal engineering decisions.

However, Human instructions remain subject to:

- platform safety restrictions,
- protected security and safety Policies,
- protected Orchestra Core Policies,
- legally required restrictions,
- explicitly defined approval procedures.

A Human instruction may authorize an exception only when the applicable Policy permits such an exception.

Example:

Human instruction:

"Push this branch."

Protected Policy:

"Git push requires explicit approval."

If the current Human instruction constitutes the required approval under that Policy, the action may proceed.

If the Policy requires an additional approval mechanism or prohibits the operation entirely, the instruction alone does not bypass that requirement.

The Orchestra must never pretend that a protected restriction has been bypassed when it has not.

---

## 4. Policies vs Rules

Policies govern authority, permissions, protections, and mandatory process requirements.

Rules govern engineering behavior within the boundaries established by applicable Policies.

At comparable scopes, a Policy has stronger authority than an ordinary Rule.

A Rule must not weaken an applicable higher-authority Policy.

Example:

Project Rule:

"Automatically push completed branches."

Organization Policy:

"Git push requires Human approval."

Result:

Git push still requires Human approval.

However, specificity still matters among instructions of the same authority class.

For example, a Task-specific Rule may refine a Project Rule when it does not violate an applicable Policy.

---

## 5. Protected Policies

Some Policies are marked as protected.

Protected Policies may include:

- security restrictions
- destructive-operation restrictions
- protected Git operations
- production deployment requirements
- credential handling
- database destruction
- infrastructure mutations

A protected Policy cannot be weakened by a lower layer.

---

## 6. Security Precedence

For security-sensitive permission decisions, the stricter decision wins.

Future Orchestra versions may use decisions such as:

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

Example:

Global Policy:

git push = always-ask

Project configuration:

git push = allow

Effective result:

git push = always-ask

This behavior is reserved for full implementation in Orchestra v0.2.

---

## 7. Specificity

When two instructions exist at the same precedence level, the more specific applicable instruction wins.

Example:

Project Rule:

"All tests must run before completion."

Task Rule:

"Run only the authentication test suite during intermediate implementation steps, then run the full required test suite before completion."

Both Rules can coexist because the Task Rule is more specific without violating the final Project requirement.

---

## 8. Explicit Configuration Beats Inference

An explicit Rule or configuration value must be preferred over an inferred convention.

Agents must not replace explicit configuration with assumptions based on:

- repository style
- framework defaults
- common industry practice
- personal preference
- Provider behavior

---

## 9. Source of Truth

If a Source of Truth is explicitly defined for a category of information, Agents must use that Source rather than duplicated or stale copies.

Example:

If `.ai/project.yaml` is the Source of Truth for Orchestra project configuration, a conflicting value in an old planning document must not silently override it.

---

## 10. Conflict Handling

If two applicable instructions conflict and precedence does not clearly resolve the conflict, the Agent must not guess.

The Agent should:

1. identify the conflicting instructions,
2. determine whether the conflict blocks the Task,
3. choose the safest reversible path when possible,
4. escalate for Human decision when required.

---

## 11. Provider-Specific Instructions

Provider-specific configuration exists to adapt Orchestra behavior to a Provider.

It must not redefine the core engineering contract.

Example:

A Provider Adapter may define how an independent Reviewer Agent is created.

It must not redefine:

"Independent review is not required."

when the applicable Workflow requires independent review.

---

## 12. Profiles

Profiles provide defaults.

They are intentionally low precedence.

A Profile may define:

- default Workflow
- default Risk
- default Complexity
- default Quality Gates

Project and Task configuration may override Profile defaults where permitted.

---

## 13. Task Scope

Task-specific instructions may narrow Project defaults but must not silently weaken protected Policies.

Example:

Project:

"Do not modify database schema without approval."

Task:

"Add a new customer field."

The Task does not automatically authorize a schema change unless the applicable approval requirement is satisfied.

---

## 14. Future Compatibility

Provider Adapters, command permission systems, Brownfield policies, routing engines, and Organization policies introduced in later Orchestra versions must follow this precedence model unless a future breaking specification explicitly changes it.
