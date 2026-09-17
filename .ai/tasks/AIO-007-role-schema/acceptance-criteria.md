# AIO-007 — Acceptance Criteria

AIO-007 is complete when all applicable criteria below are satisfied and Human approval is granted.

## Schema Contract

- [x] A canonical Role JSON Schema exists at `schemas/role.schema.json`.
- [x] The schema targets JSON Schema Draft 2020-12.
- [x] Root defines `type: object` and `additionalProperties: false`.
- [x] Required fields are enforced: `id`, `name`, `purpose`, `responsibilities`, `required_capabilities`.
- [x] Optional field `applicable_task_types` is permitted.
- [x] Unknown top-level fields are rejected.
- [x] `id` requires a non-empty string (`minLength: 1`).
- [x] `name` requires a non-empty string (`minLength: 1`).
- [x] `purpose` requires a non-empty string (`minLength: 1`).
- [x] `responsibilities` requires an array of non-empty strings.
- [x] `required_capabilities` requires an array of non-empty strings.
- [x] `applicable_task_types` requires an array of non-empty strings when present.
- [x] No unapproved constraints (`minItems`, `uniqueItems`, identifier regexes, vocabulary enums) are present in the schema.
- [x] No instance `schema_version`, extensions, provider, model, agent, human, prompt, tool, permission, authority, approval, assignment, workflow, execution, estimate, or task relationship fields are added.

## Markdown Projection and Extraction

- [x] Extractor is test-only, repository-local, and minimal.
- [x] Extractor does not establish Markdown as a public runtime serialization format.
- [x] Extractor parses the current canonical Markdown structure without inferring missing values or supplying defaults.
- [x] Extractor strictly fails on duplicate, ambiguous, or malformed sections.
- [x] Canonical Role definitions (`architect.md`, `software-engineer.md`, `reviewer.md`, `security-reviewer.md`, `documentation-specialist.md`) extract and validate successfully.
- [x] Extraction failure test cases verify visible failure for malformed, duplicate, or ambiguous Markdown.

## Fixtures and Validation Tooling

- [x] Repository-local validation tooling exists at `schemas/tests/validate_role.py`.
- [x] Role schema passes Draft 2020-12 meta-validation.
- [x] Valid fixture registry includes minimal, full, and structural edge cases.
- [x] Structural edge-case fixtures (`valid-structurally-empty-required-arrays.yaml`, `valid-structurally-empty-optional-array.yaml`, `valid-structurally-duplicate-items.yaml`) clearly document structural permissiveness only.
- [x] Invalid fixture registry includes exact expected failure keyword and path checks.
- [x] Fixture coverage check detects missing or unregistered fixtures.
- [x] Validator returns exit code 0 when all cases pass.
- [x] Validator returns nonzero exit code when a validation failure or mismatch occurs.

## Repository Integration

- [x] AIO-007 is registered in `CANONICAL_TASKS` in `schemas/tests/validate_task.py`.
- [x] Task validator passes (all canonical tasks and fixtures).
- [x] Project Manifest validator passes.
- [x] Existing Task and Project Manifest schema semantics remain untouched.
- [x] `git diff --check` passes cleanly.

## Quality Gates and Governance

- [x] `documentation_consistency` passes.
- [x] `independent_review` passes.
- [x] AIO-006 contract semantics remain unchanged.
- [x] No future-version or out-of-scope concepts are introduced.
- [x] Final Human approval is obtained before Task closure.
