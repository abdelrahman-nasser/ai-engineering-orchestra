# AIO-017 Acceptance Criteria

- [x] Installed API validates Manifest and Task schemas, required Task identity,
  duplicate declared Task IDs, Workflow schemas and IDs, Workflow-local Stage IDs,
  and declared Task-to-Workflow references using the existing catalog.
- [x] Inventory, inspect, and structural validation share configured Task paths;
  custom paths never fall back to .ai/tasks. Root discovery walks upward from CWD.
- [x] Invalid YAML, schemas, identities, and references produce FAIL. Missing tool
  resources, I/O failures, and internal failures produce ERROR without a traceback.
- [x] Normal installation validates an independent temporary external project without
  source imports, PYTHONPATH, development fixtures, Task history, Git, or Node.
- [x] Canonical schemas remain single-source resources. Regression fixture, template,
  historical, and schema self-test coverage is preserved.
- [x] No Role runtime parser, command runner, lifecycle/stage execution, gate mapping,
  JSON output, state mutation, new CLI command, or generic verify is introduced.
- [x] Existing seven-check preflight and compatibility wrappers pass; full regressions,
  installation smoke, Markdown lint, and diff checks pass with evidence recorded.
- [x] Independent review and documentation consistency are evaluated explicitly;
  the required pre-approval checkpoint was honored. Explicit Human approval on
  2026-09-17 authorizes completed status and the closure commit.
