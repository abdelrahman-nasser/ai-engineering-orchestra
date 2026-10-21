# ITRU-067 Phase 2 implementation and verification report

## Outcome and Human boundary

The three approved static package/resource expectation corrections are implemented
inside `tests.test_packaging.PackagingTests.test_explicit_resource_allowlist`.
The original unchanged test FAILED as expected. Exactly four approved methods
then PASS, with zero errors, skips or prohibited-operation attempts.
Both independent implementation reviews APPROVE with no unresolved findings.
Required documentation_consistency and independent_review Gates PASS for this
bounded implementation handoff. The exact candidate is ready for Human review.

Task status remains `in_progress`. Changes are unstaged and uncommitted. STOP AT
HUMAN CONTROL for a separate checkpoint approval; no final acceptance, closure,
stage, commit, Jira transition or publication is authorized by this handoff.

## Authority, baseline and Task identity

Human decision: APPROVE IMPLEMENTATION AND TESTING, October 21, 2026, identifying
SCRUM-86 approval comment #10767. The direct instruction is recorded authority;
no fresh Jira query or external update is claimed.

Entry was clean at branch `feature/core-verification-debt-phase1`, HEAD
`4775d649e13639504a8007e57890f80c699bb1be`, in
`D:\Dev\ITRU\worktrees\itru-core-usability`. Branch/HEAD are unchanged and the
index remains empty. The later freeze includes the newly created Task directory
as untracked; that does not replace the earlier clean-entry observation.

[Identity evidence](evidence/identity.json) records root and independent searches:
six registered worktrees, 23 distinct local branch/remote/tag tips and supplemental
ignored `.ai` state/reservations. No prior ITRU-067 use was found. ITRU-066 was
verified as the completed SCRUM-89 Task in the UI integration worktree and remains
unchanged. The audit did not fetch remotes or claim global external uniqueness.

ITRU-067 has all four canonical records. Type is bugfix, complexity medium, risk
low, explicit Execution Mode standard and Workflow standard-change. It depends on
completed ITRU-065; both required Gates and all Project Human controls remain in
force. Jira tracking stays in context/review, not an unsupported task.yaml field.

## Root cause and exact implementation

The retained historical receipt and fresh before run fail on exact package-list
equality: approved metadata contains `itru._sqlite_journal_migrations`, but the old
test expected only four packages. Static inspection also identified two later
expectation omissions: the Journal SQL package-data key and lifecycle event schema.
Those later comparisons were not reached in the original failed invocation.

[ITRU-064 frozen decision 3](../ITRU-064-developer-alpha-release/context.md)
explicitly packages both unchanged SQL migration resource packages.
[ITRU-062 accepted package evidence](../ITRU-062-persistent-task-run-state/context.md)
explicitly includes `task-run-state-event.schema.json` as package data without a
new schema validator or remote resolution. Current pyproject metadata agrees.

Only the selected method changes:

1. Append `itru._sqlite_journal_migrations` to the ordered expected package list.
2. Add its explicit `["*.sql"]` package-data entry.
3. Use `["task-run-state-event.schema.json", *PACKAGED_SCHEMAS]` in the method-local
   schema package-data expectation.

Exhaustive equality, ordering and include-package-data false remain asserted.
Shared PACKAGED_SCHEMAS stays unchanged because packaged schema membership does
not establish runtime schema lookup support. Expectations remain independent
literals rather than being copied dynamically from the metadata under test.
No production code, metadata configuration, schema, migration or other test changes.
The raw bytes outside this method are identical to the frozen original source.

## Safety review and exact test receipts

Source inspection established that the four named methods read only metadata or
the existing 22 schema resources. PackagingTests has no setup hooks. Import-time
code is declarative; SQLite import is not a connection, and operational/native/
Provider paths are not invoked. Independent runner safety review approved the
actual guarded launch before either test command.

The runner uses an explicit module file and synthetic tests namespace to prevent
an installed tests package from taking precedence. It asserts checkout origins,
exact suite IDs, Python isolation and disabled bytecode. Before repository imports,
its audit hook rejects filesystem mutation/write opens, socket/DNS, subprocess/
shell/spawn, SQLite connections, native ctypes/registry operations and excluded
operational imports. Denied attempts force failure even if a test catches them.
The parent launches only the approved interpreter child and read-only Git commands.

Both commands use this interpreter:
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`.
Version: CPython 3.12.10 x64, Windows-11-10.0.26300-SP0. Existing dependency versions:
PyYAML 6.0.3, jsonschema 4.26.0, referencing 0.37.0. No installation or network use.

From the workspace, the exact parent argv uses `-I -B` and
`.ai/tasks/ITRU-067-scrum-86-verification-debt-phase2/verify_phase2.py` followed by
`before` or `after`. Complete child argv/bootstrap, cwd, durations, source hashes,
module origins, outputs and exit codes are in [commands.jsonl](evidence/commands.jsonl).

All methods below belong to `tests.test_packaging.PackagingTests`:

| Phase | Exact method | Actual result |
| --- | --- | --- |
| Before | test_explicit_resource_allowlist | FAIL; one assertion failure, exit 1 |
| After | test_explicit_resource_allowlist | PASS |
| After | test_metadata_and_only_temporary_console | PASS |
| After | test_packaged_schema_content_matches_canonical_source | PASS |
| After | test_schema_lookup_does_not_consult_cwd | PASS |

The before child ran exactly one test with zero errors/skips. The after child ran
exactly four tests with zero failures/errors/skips and exit 0. Neither run recorded
a prohibited attempt, expected failure or unexpected success. No class collection,
broad discovery, fixture provisioning or unsafe setup occurred.

Raw output: [before.txt](evidence/before.txt) and [after.txt](evidence/after.txt).
Before SHA-256: `edee0fa80fe7d55f6246deac879ad99bc9d770d4dab78370c5c7c24d43c4abd0`.
After SHA-256: `a2b02455bae9d92f986fccee2d6880e229cc70eca061c56cdb13f36fc12eb629`.
Original test SHA-256:
`65d705841ea6ad3469f6dbbc18d8533190f56abcf63832aecd2f1624ef91a0b7`.
Corrected test SHA-256:
`e9d4ccb8580fff9a8c0fae6e9ac9960b3ae7d686e18884dad596a99f874049b4`.

The runner refuses baseline/source drift and never restores old source. Raw
before/after outputs are not overwritten. Timeout/launch exceptions retain output
and error receipts before stopping; that review correction preceded all tests,
so no timeout/launch error occurred. The expected failed before test remains FAILED.

## Scoped validation and independent review

[Baseline evidence](evidence/baseline.json) freezes original test bytes, relevant
metadata/import/contract inputs and all 1,164 other tracked file hashes. All those
tracked inputs and the selected historical ignored receipt hashes remain unchanged.
The ITRU-065 inventory still agrees with its original raw-log hashes.

`verify_phase2.py checks` PASS: current Task and governing Workflow schemas, used
Role schemas, canonical IDs/dependency/Role/Gate references, exact three-correction
byte comparison, protected historical/source hashes, raw test-receipt/source/runner
identities, branch/HEAD/empty index, exact path scope, local Markdown references,
nonreceipt whitespace and git diff --check. No tests execute in this check mode.
Input hashes and exact commands are in [governance checks](evidence/governance-checks.json).

Both independent reviewers inspected the actual implementation and evidence:

| Perspective | Independent execution | Verdict |
| --- | --- | --- |
| Test integrity/security | /root/journal_assessment | APPROVE; no residual findings |
| Contract/documentation | /root/assertion_namespace_assessment | APPROVE; documentation_consistency PASS; no findings |

They independently rehashed all 1,164 protected tracked inputs, seven historical
ignored receipts and candidate snapshot inputs with zero mismatches, and verified
the exact diff, raw test outcomes, runner/source bindings and Human boundaries.
`independent_review`: PASS. `documentation_consistency`: PASS using accepted-source
comparison, repository inspection, schema/reference checks and actual independent
review. These are scoped Gate verdicts, separate from mechanical Check outcomes.
[Review evidence](review.md) records the verdicts and resolved preliminary review
corrections. Final scoped checks and reviewer applicability reads cover the
editorial verdict/checklist/readiness updates without rerunning unchanged tests.

Scoped Markdown lint: NONMANDATORY / NOT RUN. AGENTS and standard-change require
applicable Gates but no linter invocation. The Manifest separately declares
repository Verification Checks; core/project-manifest.md section 33 explicitly
gives them no automatic Task/Stage/Gate binding. Configured Rules and overrides
directories are absent. The documentation-consistency Gate accepts manual
comparison, repository inspection, schema validation and independent review.
No lint PASS or mandatory Gate waiver is claimed.

## Exact changed paths and readiness

The only existing tracked file modified is `tests/test_packaging.py`, with four
added and two removed lines confined to the one method. Twelve new Task paths:

- `task.yaml`
- `context.md`
- `acceptance-criteria.md`
- `review.md`
- `phase2-report.md`
- `verify_phase2.py`
- `evidence/identity.json`
- `evidence/baseline.json`
- `evidence/commands.jsonl`
- `evidence/before.txt`
- `evidence/after.txt`
- `evidence/governance-checks.json`

All twelve are under `.ai/tasks/ITRU-067-scrum-86-verification-debt-phase2/`.
This is thirteen changed/new paths in total. Final scoped checks confirm this
exact scope after review. Git status is ` M tests/test_packaging.py` plus only
the new Task directory as untracked; the index is empty. No commit or other-lane
change is introduced. The candidate is READY for separate Human checkpoint
evaluation. A01-A09 are verified; H01/H02 remain unchecked. No staging or commit
authority is inferred from readiness or either independent verdict.

Historical Core debt stays open: 24 failures, 275 errors, five skips, full C109
NOT RUN, and 132 unresolved Markdown findings across 17 files. These are historical
aggregate results, not a freshly measured total. The selected test now has a
separate focused PASS; no historical event or count is rewritten as resolved.
No Journal/hostile-fixture/native-security/namespace/C111/Provider remediation,
wheel validation or operational Core reader work occurred.

Option D remains binding: S0 closed at NO-GO, reader admission deferred, S1-S8
unauthorized, Core CLI-only and Control Center mock-backed. SCRUM-86 remains open.
Human checkpoint approval and final acceptance remain pending; Task is not complete.
