# AIO-005 — Acceptance Criteria

AIO-005 is complete when all applicable criteria below are satisfied.

## Schema

- [x] A canonical Task JSON Schema exists.
- [x] the schema targets JSON Schema Draft 2020-12.
- [x] required Task fields are enforced.
- [x] unknown top-level Task fields are rejected.
- [x] `id` is validated as a non-empty string.
- [x] `title` is validated as a non-empty string.
- [x] `type` is validated as a non-empty string.
- [x] allowed Task status values are enforced.
- [x] `version_target` is validated when present.
- [x] Complexity values are enforced.
- [x] Risk values are enforced.
- [x] `execution.mode` values are enforced.
- [x] scope structure is validated.
- [x] `scope.include` requires at least one meaningful item.
- [x] `scope.exclude` is validated when present.
- [x] dependencies are validated when present.
- [x] an empty dependency list is allowed.
- [x] duplicate dependency identifiers are rejected where supported.
- [x] Quality Gate identifiers are structurally validated.
- [x] supported Human control fields are validated.
- [x] unsupported nested Human control fields are rejected.

## Validation Boundaries

- [x] the schema does not attempt to enforce Task ID uniqueness across the repository.
- [x] the schema does not attempt to prove dependency existence.
- [x] the schema does not attempt to detect circular dependencies.
- [x] the schema does not pretend to validate Human approval truth.
- [x] the schema does not pretend to validate independent-review independence.
- [x] the schema does not treat JSON Schema validation as sufficient evidence for Task closure.

## Fixtures and Tests

- [x] representative valid fixtures exist.
- [x] representative invalid fixtures exist.
- [x] the canonical Task template validates successfully.
- [x] AIO-001 validates successfully.
- [x] AIO-002 validates successfully.
- [x] AIO-003 validates successfully.
- [x] AIO-004 validates successfully.
- [x] AIO-005 validates successfully.
- [x] invalid fixtures are rejected for their intended reasons.
- [x] the schema itself passes Draft 2020-12 meta-validation.
- [x] repository-local validation exits successfully when expected outcomes match.
- [x] repository-local validation fails when expected outcomes do not match.

## Architecture

- [x] `core/task-specification.md` remains the authoritative semantic contract.
- [x] Task schema validation remains separate from future CLI behavior.
- [x] no Provider-specific behavior is introduced.
- [x] no model-specific behavior is introduced.
- [x] no Stack Module behavior is introduced.
- [x] no orchestration or routing behavior is introduced.
- [x] no future-version functionality is prematurely implemented.

## Documentation

- [x] Task schema location is documented.
- [x] validation tooling location is documented.
- [x] schema limitations are documented.
- [x] canonical Sources of Truth remain consistent.

## Quality

- [x] `documentation_consistency` passes.
- [x] `independent_review` passes.
- [x] Final Human approval is obtained before Task closure.
