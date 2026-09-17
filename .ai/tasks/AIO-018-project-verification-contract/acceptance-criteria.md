# AIO-018 Acceptance Criteria

- [x] The Manifest owns optional verification.checks; absence and empty checks are
  valid, while a present section requires checks and permits no unknown fields.
- [x] Only id, command, cwd, and timeout_seconds are accepted. IDs follow the
  canonical pattern and duplicate IDs fail semantic validation.
- [x] Commands require nonempty string arrays, nonblank executable, no NUL,
  literal later arguments including empty strings, and no scalar coercion.
- [x] Cwd defaults to the active root and rejects absolute, rooted, UNC,
  backslash, drive-relative, empty, and NUL representations. Relative traversal
  remains declarative; no existence or execution containment logic is introduced.
- [x] Timeout defaults to 600; positive integers only, excluding boolean, null,
  string, zero, and negative values. No timeout execution is implemented.
- [x] Specification defines ordering, full-set validation, future resolution,
  continuation/results/exit codes, recursion prohibition, environment inheritance,
  no glob expansion, and explicit command-versus-authority and Gate boundaries.
- [x] Structural validation, tasks, and inspect execute zero declared commands;
  tests cover valid and malformed data without launching future checks.
- [x] Updated canonical schema is available through normal and editable installs;
  old Manifests and template validate; no resource duplication is introduced.
- [x] Terminology and README truthfully describe contract-only availability.
  Current verify and all seven development checks remain unchanged; Orchestra's
  own Manifest contains no verification declarations.
- [x] Full unittest, Task, Workflow, Role, Manifest, preflight, packaging/install,
  markdownlint, and diff checks pass, with all failures or skips recorded.
- [x] Separate independent and security-focused reviewers evaluate actual changes,
  resolve material findings, and establish existing Gate outcomes without new Gates.
- [x] Exactly four Task artifacts and canonical Task registration exist. The
  pre-approval Human Control stop was honored with status in_progress and no commit.
- [x] Explicit Human approval dated 2026-09-17 is recorded in review.md; closure
  is authorized and Task status is completed. No AIO-019 or runner was created.
