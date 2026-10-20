# SCRUM-87 acceptance criteria

- [x] Valid demo and compatible configurations receive bounded local diagnostics;
  missing/unreadable/invalid config, missing/incomplete provider, unsupported
  selection and absent credentials have actionable fixed codes.
- [x] Diagnostic output and Alpha error handling exclude input values, private
  environment values, endpoint/model/key names, HTTP bodies and raw exceptions.
- [x] Diagnostics perform no network, owner acquisition, provisioning, Run
  registration, work loading, storage mutation or Tool execution.
- [x] Known provider errors retain safe categories and recovery; unknown failures
  remain generic. Human approval rejection remains distinct and cannot be
  satisfied by provider setup. Cancellation/approval/digest semantics persist.
- [x] Deterministic positive, negative, redaction, response/error and recovery tests
  execute offline; exact verification results and limits are recorded.
- [x] First-run/manual/help and roadmap match the implemented command and clearly
  distinguish local validation from connectivity, authority and readiness.
- [x] Independent security and CLI usability reviews and documentation consistency
  are recorded; SCRUM-86 debt and all failed/skipped evidence remain explicit.
- [x] Human reviews the unstaged, uncommitted handoff before any commit or closure.

## Final Human acceptance — October 20, 2026

**Final Human acceptance: APPROVED — October 20, 2026.** The Human accepted
implementation commit `705c306c51278e6c218f316db7ab63244b58515c`, the Security and
CLI usability APPROVE verdicts, and the implementation documentation-consistency
and independent-review PASS results. The Human acceptance criterion is satisfied;
the seven previously checked implementation criteria retain their evidence.

The Human explicitly approved final Task closure and exactly one local closure-only
commit. The limitations listed in [review](review.md) are accepted as nonblocking
for SCRUM-87 Task closure only. SCRUM-86 retains broader Core verification debt;
no failed, skipped or unexecuted result becomes PASS and no mandatory Gate is
waived. Fresh closure-documentation checks and independent review are recorded
separately in [verification](verification.md).
