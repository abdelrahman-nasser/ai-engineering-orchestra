# Review and validation

The sections preceding the Human checkpoint record below are historical
verification snapshots. Their no-commit/pending-authorization statements describe
those earlier checkpoints and are superseded only for the explicitly authorized
single local commit.

## Scope and status

The scoped production change adds `selected_subjects` in `make_plan`.
Three Developer Alpha guides and one focused test module are affected.
The coordinator added this new Task directory after independent review identified
the missing current audit records. Task status remains `in_progress`.

On October 17, 2026, independent Reviewer `core_preflight_review` issued
**APPROVE** for the complete scoped product diff and these new audit records,
with no unresolved findings. Documentation consistency: **PASS**. Independent
review: **PASS**. The Reviewer reran all five focused tests, validated the new
Task schema/artifacts and compared baseline/current plans for all three actions;
every pre-existing field matched. Human acceptance remains pending.

## Validation evidence

- Five new preview tests pass, including fixed pre-change run/resume/complete
  digests and exact maximum-length strings through CLI JSON.
- Task, Workflow, Role and Manifest fixture validators pass.
- The three changed guides pass cached offline Markdown lint.
- Product `git diff --check` passes.
- Full unit discovery: 2,103 tests; 24 failures, 275 errors and 5 skips.
- Existing Alpha tests rerun outside the sandbox: 14 setup errors due to
  `JournalIncompatibleSchema`; the implementation session traced a Journal SQL
  checksum mismatch to checkout CRLF bytes before the preview is reached.
- Repository-wide cached Markdown lint: 132 issues in 17 unchanged files.

Diagnostics are retained under the worktree's ignored `.tmp/` directory.
Broader verification is **not green**. Those failures and skips are neither
waived nor repaired by this Task. No commit, publication or operational approval
has been performed. Stop at Human control.

## Final verification checkpoint — October 17, 2026

The Human authorized investigation, scoped regression verification and correction
only, with no commit. The [final verification report](final-verification.md)
records exact Git/base evidence, all 299 broad failure/error events and five
skips, isolated baseline comparisons, focused results and attribution limits.

No product correction was needed; the three-line implementation and all existing
product/tests/guides remain byte-preserved from the start of this verification.
Five preview tests and 49 selected pure regressions pass, as do the four fixture
validators, the current Task schema and changed Markdown checks. Additional
in-memory comparisons preserve every prior field across five plan cases.

Seven direct assertion tests and the namespace diagnostics reproduce on the
exact base. Native access, missing hostile fixture and retired experiment import
also reproduce at their shared prerequisites. Canonical LF Journal SQL passes;
the isolated baseline reproduces the checkout's checksum failure only with its
matching CRLF bytes. The containment matrix remains unexercised beyond its
launch prerequisite. No full baseline or full current suite was rerun.

The earlier approval above remains historical scoped implementation review.
Final independent `core_correctness` and `governance_security` reviews both
issued **APPROVE for the scoped P0 change and final audit**, with no material
findings. Both inspected the actual diff and final evidence; both independently
reran all five focused tests successfully. The Core reviewer identified minor
audit wording and receipt-retention ambiguities, now corrected and explicitly
indexed. Documentation consistency is **PASS within this scoped change**.
Task-wide independent-review gate clearance is not asserted while the required
broader-disposition acceptance item remains unresolved.
Broader unit verification remains **FAILED**, platform scenarios **SKIPPED**;
no waiver or Human acceptance is inferred. The unresolved broader-disposition
and final-Human-approval acceptance boxes remain unchecked. Task status remains
`in_progress`; no staging, commit or publication has occurred.

## Human checkpoint authorization — October 17, 2026

Human decision: **APPROVE — PROCEED with exactly one local checkpoint commit**.
Worktree: `D:\Dev\itru-core-usability`.
Branch: `feature/developer-alpha-usability-p0`.
Expected parent: `2323c2726061785ff29e1bdfc65ccf90b7d057b2`.
Approved message: `feat(alpha): show exact selected subjects in approval plans`.

The Human explicitly superseded the prior no-commit restriction for this
checkpoint only. The authorization covers the reviewed implementation, focused
tests, three guides, current Task audit/verification records and minimal updates
needed to record this decision. The exact ten-path candidate inventory is:

- `itru/developer_alpha.py`
- `tests/test_alpha_plan_preview.py`
- `docs/developer-alpha.md`
- `docs/developer-alpha-first-run.md`
- `docs/developer-alpha-usability-roadmap.md`
- `.ai/tasks/developer-alpha-usability-p0/task.yaml`
- `.ai/tasks/developer-alpha-usability-p0/context.md`
- `.ai/tasks/developer-alpha-usability-p0/acceptance-criteria.md`
- `.ai/tasks/developer-alpha-usability-p0/review.md`
- `.ai/tasks/developer-alpha-usability-p0/final-verification.md`

The Human accepts the nine documented `pre_existing_baseline_failure`
classifications. The final baseline comparison independently verified a fresh
1,136-blob canonical export, matched environments and retained seven original
direct test pairs. It additionally reproduced the original C109/O55 helper
branch and the unchanged namespace assertion with each tree's explicit inventory.
Full C109 was **not** run; original enumeration/membership was verified statically.
Both independent reviewers approved all nine classifications and their limits.
The complete newer evidence remains outside the worktree at
`C:\Users\Abdelrahman\AppData\Local\Temp\itru-p0-final-baseline-r8b0a71s`,
including `failure-matrix.json`, full retained tracebacks, unique command logs,
Git/source proofs, independent review records and `final-report.txt`.

For this checkpoint only, the Human accepts the retained **24 Core failures,
275 errors, five skips and inherited repository Markdown findings** as
documented nonblocking baseline/environment issues, subject to those limits.
No failed/skipped check is PASS, resolved or waived. All original receipts,
classifications and unexercised native/security limitations remain preserved.
The repository-wide lint result remains 132 issues in 17 unchanged files.

The effective required gates remain `documentation_consistency` and
`independent_review`; prior scoped PASS/APPROVE evidence is retained. The
checkpoint's audit changes require final independent staged-diff review and
documentation checks before committing. No Task-wide gate clearance, full Core
success or final acceptance is inferred from this authorization.

Manifest Verification Checks are mechanical evidence rather than automatic
Quality Gates (`core/project-manifest.md`, section 33). The Task's closure rules
remain in force (`core/task-specification.md`, sections 25–30). The scoped local
checkpoint is separately Human-approved; **Task status remains `in_progress`**,
with broader-disposition and final Task-acceptance criteria open for closure.

No additional commit, push, merge, PR, tag, release, publication, operational
Alpha/inference execution, UI repository change, deferred Core/UI reader work or
automatic Task completion is authorized. Stop at Human control after the one
local checkpoint. Its actual SHA, parent, inventory and final Git status must
be verified after creation; this section records authorization before commit.

## Final staged checkpoint review

Independent `core_correctness` and `governance_security` reviewers inspected the
entire staged ten-file diff and the actual checkpoint verification receipts.
Both issued **APPROVE**, with no material findings. For this checkpoint scope,
`documentation_consistency` is **PASS** and `independent_review` is **PASS**.
Neither result grants Task closure or converts broader failed/skipped checks
into passing evidence.

The checkpoint rerun passed all five focused preview tests, the current Task
schema (`in_progress`), offline Markdown lint for all seven scoped Markdown
files and staged whitespace checks. Reviewers independently verified all ten
staged content hashes and the six initial command-output receipt pairs.
The implementation, focused test and three guides are byte-identical to the
previously reviewed versions; all 44 prior verification artifacts remain intact.
The earlier 49 selected regressions and four fixture validators remain retained
valid evidence, rather than newly rerun results. The full Core suite and full
C109 were not rerun. Sensitive-data inspection found no provider credentials
or added execution authority.

Checkpoint receipts and staged fingerprints are retained separately under
`.tmp/p0-checkpoint-commit/`, with unique output filenames. The final approval
entry is an audit-only addition; the reviewers check that delta before commit.
The Human authorization above remains limited to exactly one local checkpoint.
