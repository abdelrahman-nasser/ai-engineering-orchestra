# Independent Review Quality Gate

Version: 0.1.0

Gate ID:

`independent_review`

---

## Purpose

Verify that a material change is evaluated independently from the Agent that implemented it.

Independent review reduces confirmation bias and helps detect:

- incorrect assumptions,
- requirement gaps,
- architectural violations,
- regressions,
- inconsistent terminology,
- incomplete validation,
- unnecessary changes.

---

## Independence Requirement

The sole Reviewer must not be the same Agent execution instance that implemented the material change.

A different Agent, AI Provider, model, or Human may perform the review where permitted by the applicable Workflow and Policy.

Using a different Provider is not mandatory unless explicitly required.

---

## Minimum Review Context

The Reviewer should normally receive:

- Task objective,
- Task scope,
- acceptance criteria,
- applicable Rules and Policies,
- relevant architecture decisions,
- actual changed files or diff,
- available validation results.

The Reviewer should not rely solely on the Implementer's explanation.

---

## Pass Conditions

The gate passes when:

- an independent Reviewer evaluated the material change,
- required acceptance criteria were checked,
- material findings were resolved or explicitly accepted through the applicable approval process,
- the Reviewer issued an approval outcome.

---

## Fail Conditions

The gate fails when:

- no independent review occurred,
- the Reviewer lacked sufficient context,
- unresolved blocker or high-severity findings remain,
- required acceptance criteria failed,
- the implementation Agent was the sole Reviewer when independence was required.

---

## Review Outcomes

A review may produce:

- APPROVE
- APPROVE WITH MINOR CHANGES
- CHANGES REQUIRED

For this Quality Gate:

- `APPROVE` may satisfy the gate.
- `APPROVE WITH MINOR CHANGES` satisfies the gate only after required minor changes are completed or explicitly accepted.
- `CHANGES REQUIRED` does not satisfy the gate.

---

## Evidence

Review evidence should be recorded in the Task's review artifact when one exists.

Example:

`.ai/tasks/<task-id>/review.md`

---

## Result

Allowed results:

- pass
- fail
- not-applicable
- waived

A waived result requires an applicable Policy and required Human approval.

A skipped review must not be reported as passed.
