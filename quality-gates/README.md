# Quality Gates

This directory contains canonical Quality Gate definitions used by AI Engineering Orchestra.

A Quality Gate is a condition that must be satisfied before work may progress or be reported as complete when that gate is required.

## v0.1 Quality Gates

Currently defined:

- `documentation_consistency` → `documentation-consistency.md`
- `independent_review` → `independent-review.md`

Additional Quality Gates such as build, tests, lint, security, performance, and deployment validation may be introduced in later Tasks or Orchestra versions.

A required Quality Gate must not be treated as passed unless its defined pass conditions are satisfied.
