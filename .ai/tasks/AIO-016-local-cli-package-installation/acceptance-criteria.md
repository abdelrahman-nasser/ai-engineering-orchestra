# AIO-016 Acceptance Criteria

- [x] Setuptools metadata installs `aio` into clean editable and normal environments.
- [x] Python >=3.12, static version, and existing runtime dependencies are declared.
- [x] One neutral implementation per capability; source wrappers remain functional.
- [x] Installed schema resources derive from canonical files without duplicate sources.
- [x] CWD selects the active project from root and subdirectory, never package location.
- [x] Installed help, tasks, inspection, and development preflight succeed in Orchestra.
- [x] External tasks/inspection use installed schemas and target-owned Workflows.
- [x] Normal installation proves no checkout import/resource leakage or PYTHONPATH aid.
- [x] Wheel contents exclude project state, tests, fixtures, and development evidence.
- [x] Temporary alias works without domain changes; no permanent rook entry point.
- [x] Uninstall removes the temporary installed command/package and preserves source.
- [x] Focused packaging tests and all existing regressions pass.
- [x] Documentation accurately limits verify and records the narrow roadmap exception.
- [x] Independent reviewer approves after inspecting actual changes and evidence.
- [x] Stop at the Human checkpoint before closure; explicit Human approval was
  subsequently recorded on 2026-09-17, authorizing completed status and the scoped
  AIO-016 commit. No AIO-017 or further implementation is authorized.
