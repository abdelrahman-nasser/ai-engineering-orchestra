# AIO-012 — Acceptance Criteria

## Canonical Representation & Migration

- [x] `workflows/standard-change.yaml` exists, is valid YAML, and matches approved AIO-008 semantics.
- [x] `workflows/architecture-change.yaml` exists, is valid YAML, and matches approved AIO-008 semantics.
- [x] `workflows/security-sensitive-change.yaml` exists, is valid YAML, and matches approved AIO-008 semantics.
- [x] Omitted optional fields (such as `human_control_checkpoint`) remain omitted and are not normalized to `false`.
- [x] `workflows/standard-change.md` is retained as a minimal non-authoritative compatibility stub pointing to the YAML file.
- [x] `workflows/architecture-change.md` is retained as a minimal non-authoritative compatibility stub pointing to the YAML file.
- [x] `workflows/security-sensitive-change.md` is retained as a minimal non-authoritative compatibility stub pointing to the YAML file.
- [x] Compatibility Markdown stubs contain NO duplicated stages, roles, quality gates, checkpoints, or contract details.
- [x] `schemas/workflow.schema.json` is unchanged and directly validates all three canonical YAML files.

## Documentation & Specification

- [x] `core/workflow-specification.md` is updated to reflect YAML serialization without renumbering sections or reopening semantics.
- [x] `workflows/README.md` documents the clear hierarchy: YAML = authoritative definitions, Markdown = compatibility stubs, README = directory documentation.

## Shared Workflow Catalog & Loader

- [x] Lightweight shared catalog component is created in `scripts/workflow_catalog.py`.
- [x] Catalog discovers and parses `*.yaml` files in the Workflow directory without assuming filename matches Workflow ID.
- [x] Catalog validates each definition against `schemas/workflow.schema.json`.
- [x] Catalog indexes definitions by their declared `id`.
- [x] Catalog detects and rejects duplicate declared Workflow IDs.
- [x] Catalog provides resolution by declared Workflow ID.
- [x] Catalog introduces no runtime execution, actor assignment, automatic selection, or stage state persistence.

## Tooling & Validation Integration

- [x] `schemas/tests/validate_workflow.py` is updated to validate canonical YAML definitions directly.
- [x] `extract_workflow_from_markdown()` and test-only Markdown extraction logic are retired.
- [x] `schemas/tests/validate_task.py` incorporates repository semantic reference validation for declared Task workflows.
- [x] `scripts/inspect_task.py` reports `Resolution: RESOLVED` (or `UNRESOLVED`), stage count, and human control checkpoint stages.
- [x] `scripts/inspect_task.py` programmatically calculates and displays the effective Quality Gate union (`Project ∪ Workflow ∪ Task`).
- [x] Historical Tasks AIO-001 through AIO-011 remain unmodified.

## Test Coverage & Quality

- [x] New unit tests in `tests/test_workflow_catalog.py` verify catalog loading, resolution by declared ID, filename independence, duplicate ID rejection, malformed YAML handling, non-dict root handling, and omission preservation.
- [x] `tests/test_inspect_task.py` tests updated resolution reporting and effective Quality Gate calculation.
- [x] `python -B -m unittest discover -s tests -p "test_*.py" -v` passes.
- [x] All schema validators (`validate_task.py`, `validate_workflow.py`, `validate_role.py`, `validate_project_manifest.py`) pass.
- [x] `npx --yes markdownlint-cli2 "**/*.md"` passes with 0 issues.
- [x] `git diff --check` passes with 0 whitespace errors.
- [x] Independent review is conducted and passes with zero findings.
- [x] Task execution halts at the Human approval boundary before completion.
- [x] Human approval explicitly obtained, recorded in `review.md`, and closure authorized.
