# ITRU-067 Phase 2 context

The implementation-authority and handoff sections below are historical. The final
acceptance section records later Human authority for ITRU-067 only and supersedes
their pending-checkpoint, pending-acceptance and uncommitted-state descriptions.

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

## Final Human acceptance and closure authority - October 21, 2026

Final Human decision: **APPROVE - October 21, 2026**, SCRUM-86 authorization
comment #10778. The attached direct Human instruction is approval evidence;
no fresh Jira query or transition is claimed. Accepted implementation commit:
`4db4785916ce721c6769bb43ac9dcfd0519af861`, parent
`4775d649e13639504a8007e57890f80c699bb1be`, on the expected branch.

Earlier Human checkpoint authorization #10770 permitted exactly that one local
implementation commit. The exact 13-file checkpoint, matching reviewed blobs,
retained one-test FAIL/four-test PASS and clean entry were verified before
closure edits. H01 is now reconciled; the original handoff records remain history.

The new decision grants exactly one conditional closure-only local commit:
`docs(alpha): finalize ITRU-067 phase 2 verification task closure`.
Only task.yaml, acceptance-criteria.md, context.md, review.md, the closure addendum
in phase2-report.md, and new evidence/closure-checks.json may change.

Final acceptance is granted. Fresh closure validation passed, and both independent
actual-change reviews APPROVE without findings. Closure documentation_consistency
and independent_review PASS. H02 is satisfied; Task status is `completed` with
all 11/11 criteria checked. Final candidate checks and independent applicability
confirmation bind these completed records before the conditional closure commit.
The fresh [closure receipt](evidence/closure-checks.json) records actual mechanical
checks, input identities and review dispositions, without adding a Core schema.
Additional snapshots and staged/post-commit evidence stay ignored under
`.ai/local/itru-067-closure/`.

Existing implementation reviews and Gates remain applicable to unchanged code
and receipts. Separate closure-specific documentation_consistency and
independent_review verdicts PASS for these new records. No tests are
rerun, no old helper mode is replayed and no implementation receipt is rewritten.
Scoped Markdownlint remains NONMANDATORY / NOT RUN under the recorded Check/Gate
determination, with no waiver or full-Core green claim.

SCRUM-86 remains OPEN for historical 24 failures, 275 errors, five skips, full C109
NOT RUN and 132 broader Markdown findings. No built-wheel correctness, Journal
runtime health, native security or operational reader verification is established.
Option D/S0 NO-GO remains binding. No Phase 3, other-lane work, Jira transition,
push, merge, PR, tag, release, deployment or publication is authorized.
STOP AT HUMAN CONTROL after the single verified local closure commit.
