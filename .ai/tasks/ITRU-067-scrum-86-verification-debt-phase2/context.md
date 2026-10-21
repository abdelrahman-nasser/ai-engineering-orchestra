# ITRU-067 Phase 2 context

## Authority and identity

The Human's October 21, 2026 APPROVE IMPLEMENTATION AND TESTING instruction,
identified as SCRUM-86 approval comment #10767, authorizes this bounded Phase 2.
The instruction itself is the authority; no fresh Jira read or transition is
claimed. Staging, committing and final acceptance require separate Human approval.

Expected and observed baseline: branch `feature/core-verification-debt-phase1`,
HEAD `4775d649e13639504a8007e57890f80c699bb1be`, clean worktree at entry, in
`D:\Dev\ITRU\worktrees\itru-core-usability`.
Repository-wide identity inspection found no prior ITRU-067 Task or reservation.
ITRU-066 belongs to the completed SCRUM-89 UI Task; it is not reused. Detailed
search scope and receipts are retained in [identity evidence](evidence/identity.json).
The clean entry observation precedes Task creation; the later freeze snapshot
correctly includes this new untracked Task directory.

## Approved expectation boundary

Only `tests.test_packaging.PackagingTests.test_explicit_resource_allowlist` may
change outside this new Task directory. Preserve exact ordered equality and
`include-package-data == False`. Add the Journal migration package, its SQL
package-data key and the method-local event-schema expectation exactly as approved.

Grounding:

- [ITRU-064 frozen decision 3](../ITRU-064-developer-alpha-release/context.md)
  packages both unchanged SQL migration resource packages.
- [ITRU-062 accepted package evidence](../ITRU-062-persistent-task-run-state/context.md)
  includes `task-run-state-event.schema.json` as package data without adding a
  schema validator or remote resolution.
- [Phase 1 closure and inventory](../ITRU-065-scrum-86-verification-debt-phase1/phase1-report.md)
  retain the broader debt and recommend this static method as a separate slice.
- [Current metadata](../../../pyproject.toml) supplies implementation evidence;
  it does not define the independent expected values by itself.

The shared `PACKAGED_SCHEMAS` tuple stays unchanged. The event schema's package
membership does not establish support through `schema_resource`; extending that
lookup API is outside scope. No build, installation or wheel verification occurs.

## Execution and validation

The explicitly selected `standard-change` Workflow and `standard` Execution Mode
apply. The Software Engineer implements; independent reviewers assess test
integrity/security and contract/documentation evidence. Required Gates are
`documentation_consistency` and `independent_review`. Project Rules and overrides
directories are absent. No operational lifecycle Store enrollment is performed.

Verify import/setup safety before execution. Use the existing Python 3.12 with
`-I -B`, the exact checkout root and named methods only. Capture the selected
unchanged failure, then run exactly the four approved methods after correction.
The child runner must reject network, test subprocesses, SQLite connections and
native operational imports. Parent-controlled interpreter launch and read-only
Git commands are verification support, not tests creating subprocesses.

Task schema/reference checks, manual documentation comparison, local-reference
and whitespace checks and independent review establish scoped evidence. Broad
manifest Check declarations do not automatically bind all checks to this Task
under `core/project-manifest.md` section 33. Scoped mechanical Markdown lint is
NONMANDATORY / NOT RUN; documentation consistency still requires its own verdict.

## Preservation and Human checkpoints

Historical 24 failures, 275 errors, five skips, full C109 NOT RUN and 132 broader
Markdown findings remain unresolved historical evidence. Focused results are
separate receipts and do not replace these totals. All original failures and
errors remain failures and errors; no skip, xfail or success substitution is used.

Option D remains binding: S0 closed at NO-GO, reader admission deferred, S1-S8
unauthorized, Core CLI-only and Control Center mock-backed. Other Tasks and
historical receipts remain unchanged. Jira SCRUM-86 remains open.

Leave this Task `in_progress`, unstaged and uncommitted. STOP AT HUMAN CONTROL
for a separate checkpoint decision after implementation, validation and review.
Final Human acceptance and Task closure remain pending.
