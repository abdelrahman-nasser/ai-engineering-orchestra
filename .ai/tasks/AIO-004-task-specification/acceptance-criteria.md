# AIO-004 — Acceptance Criteria

AIO-004 is complete when all applicable criteria below are satisfied.

## Task Contract

- [x] A canonical Task specification exists.
- [x] The canonical Task directory layout is defined.
- [x] `task.yaml` responsibility is defined.
- [x] `context.md` responsibility is defined.
- [x] `acceptance-criteria.md` responsibility is defined.
- [x] `review.md` responsibility is defined.
- [x] required Task files are identified.
- [x] optional Task files are identified.
- [x] unknown or unsupported Task configuration has defined handling rules.

## Task Configuration

- [x] Task identity is specified.
- [x] Task title is specified.
- [x] Task type is specified.
- [x] Task status lifecycle is specified.
- [x] version target behavior is specified.
- [x] objective behavior is specified.
- [x] scope include/exclude behavior is specified.
- [x] Complexity behavior is specified.
- [x] Risk behavior is specified.
- [x] Execution Mode behavior is specified.
- [x] Quality Gate requirements are specified.
- [x] Human control requirements are specified.
- [x] Task dependencies are specified.
- [x] Project default inheritance and Task overrides are specified.

## Lifecycle and Closure

- [x] allowed Task status values are defined.
- [x] transition expectations are defined.
- [x] acceptance criteria behavior is defined.
- [x] independent review behavior is defined.
- [x] Human approval behavior is defined.
- [x] closure requirements are explicitly defined.
- [x] completed Tasks remain auditable.

## Architecture

- [x] Task configuration cannot weaken protected Policies.
- [x] Task configuration follows `core/precedence.md`.
- [x] Task Human control follows `core/human-control.md`.
- [x] Task context behavior follows `core/context-policy.md`.
- [x] Quality Gate identifiers align with `quality-gates/`.
- [x] the contract remains Provider- and model-agnostic.
- [x] the contract remains stack-, language-, and framework-agnostic.
- [x] future-version functionality is not prematurely implemented.

## Example

- [x] A canonical reusable Task example exists.
- [x] the example conforms to the Task specification.
- [x] existing Orchestra Tasks either conform or documented migration requirements exist.

## Quality

- [x] `documentation_consistency` passes.
- [x] `independent_review` passes.
- [x] Final Human approval is obtained before Task closure.
