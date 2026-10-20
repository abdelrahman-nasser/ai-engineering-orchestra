# SCRUM-86 Phase 1 acceptance criteria

- [x] Verify clean expected baseline and dedicated branch without altering history.
- [x] Preserve an exact historical failure/error/skip/Markdown inventory with
  root-cause hypotheses, environment dependencies and risk classifications.
- [x] Reproduce the selected CLI-help assertion failure offline before changing it.
- [x] Ground the explicit corrected help expectations in approved contracts and
  implementation; preserve wrapper, no-project-discovery and exit assertions.
- [x] Pass the selected test and directly affected safe help/parser regressions
  after the minimal test-only change, with exact commands and before/after receipts.
- [x] Obtain independent test-integrity/security and contract/documentation review
  of the actual diff; resolve material findings without weakening assertions.
- [x] Record remaining debt, not-run limits, next safe phase and commit readiness;
  leave completed Tasks, production code, index and HEAD unchanged.
- [ ] Receive separate final Human acceptance before Task closure.

The seven checked criteria record the implementation handoff, including an empty
index and unchanged HEAD before the separately authorized checkpoint. The original
final criterion said "before any commit or Task closure". The October 20 Human
checkpoint decision (`#10746`) supersedes only its commit restriction, permitting
one conditional local checkpoint after verification. It does not satisfy final
Task acceptance or authorize closure; the final criterion remains unchecked.
