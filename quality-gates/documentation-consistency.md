# Documentation Consistency Quality Gate

Version: 0.1.0

Gate ID:

`documentation_consistency`

---

## Purpose

Verify that documentation affected by a Task remains consistent with the actual repository state and with other authoritative Sources of Truth.

---

## Applies When

This Quality Gate is required when a Task:

- creates or modifies framework documentation,
- changes terminology,
- changes configuration contracts,
- changes architectural or behavioral rules,
- changes documented Sources of Truth.

---

## Pass Conditions

The gate passes when all applicable checks are satisfied:

- terminology is used consistently,
- documentation does not materially contradict other authoritative Sources of Truth,
- documented file paths and identifiers are valid,
- implemented behavior is not falsely documented as future work,
- future work is not falsely documented as already implemented,
- version references are consistent where applicable,
- changes to one Source of Truth are reflected in dependent documentation when required.

---

## Fail Conditions

The gate fails when any material contradiction, stale authoritative statement, or incorrect implementation status remains unresolved.

---

## Not Applicable

The gate may be marked not applicable when the Task does not affect documentation or documented system behavior.

The reason should be recorded.

---

## Evidence

Evidence may include:

- manual comparison,
- independent review,
- schema validation,
- repository inspection,
- automated documentation checks introduced in future versions.

---

## Result

Allowed results:

- pass
- fail
- not-applicable
- waived

A waived result requires an applicable Policy and required Human approval.

A skipped check must not be reported as passed.
