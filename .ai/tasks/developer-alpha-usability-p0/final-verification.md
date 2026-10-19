# P0 approval preview final verification

## Final closure disposition — October 19, 2026

The Human explicitly approves final P0 Task closure, accepting the reviewed
implementation, focused verification, independent reviews and preserved
checkpoint `c2fef2e3c25415e75672d75b70e633f0f85a4caa`. The 24 broader failures,
275 errors, five skips, inherited Markdown findings and **full C109 not executed**
are nonblocking non-P0 debt for final closure of this Task only. Their results
and limitations remain unchanged; no mandatory Quality Gate is waived and no
full-Core PASS is claimed. SCRUM-86 remains open and is not modified.

The Human authorizes only necessary Task closure/audit updates and one local
commit: `docs(alpha): finalize P0 approval-preview task closure`. The exact
decision is recorded in [the final closure audit](review.md#final-human-closure-decision--october-19-2026).
Closure-only schema/documentation checks and independent review passed;
canonical Task status is `completed`. Actual outcomes are recorded in that audit.
No implementation, test, guide, architecture, UI or Lane B change is included.

The earlier sections below remain historical evidence. The new final Human
decision supersedes their checkpoint-only/pending-closure restrictions for this
Task's final closure, without changing any failed/skipped receipt or limit.

## Current Human checkpoint disposition — October 17, 2026

The Human has now accepted the nine documented pre-existing baseline-failure
classifications and explicitly authorized exactly one scoped local checkpoint
commit: `feat(alpha): show exact selected subjects in approval plans`.
The authorized branch is `feature/developer-alpha-usability-p0`, with expected
parent `2323c2726061785ff29e1bdfc65ccf90b7d057b2`. The exact ten-file scope and
Human decision are recorded in [the current audit](review.md#human-checkpoint-authorization--october-17-2026).

For this checkpoint only, the retained 24 failures, 275 errors, five skips and
inherited Markdown findings are documented nonblocking baseline/environment
issues, subject to the verification limits below. No failed/skipped check is
converted to PASS and no required Quality Gate is waived. Required scoped
documentation-consistency and independent-review evidence must remain valid.
Task status remains `in_progress`; final Task acceptance and closure remain
pending. This approval does not authorize any additional commit or publication.

The later final baseline comparison corroborated all nine assertion
classifications. Seven original direct test pairs remain valid. Original
C109/O55 helper-branch runtime evidence and static outer enumeration support
that subcase; **full C109 was not executed**. The unchanged namespace assertion
uses each tree's explicit verified inventory and produces the same nine
diagnostics. Complete newer receipts and reviewer conclusions remain in
`C:\Users\Abdelrahman\AppData\Local\Temp\itru-p0-final-baseline-r8b0a71s`.

The sections below preserve the earlier verification snapshot unchanged.
Their pending-authorization/no-commit statements were true at that checkpoint;
the Human decision above supersedes them solely for this one local commit.
The original failed/skipped receipts and classification evidence are preserved.

## Historical verification snapshot

Date: October 17, 2026. Authorization: the Human's Lane A final-verification
request. Scope: investigation, regression verification and scoped correction.
Task remains `in_progress`; final Human acceptance and failed-verification
disposition remain pending. No product correction was necessary.

## 1. Git state and preservation

Worktree: `D:\Dev\itru-core-usability`.
Branch: `feature/developer-alpha-usability-p0`.
HEAD and exact branch-creation base:
`2323c2726061785ff29e1bdfc65ccf90b7d057b2`
(`docs: add Developer Alpha first-run operator card`). The branch reflog records
creation directly from that commit on October 17, 2026 at 17:46:24 +03:00.
The original Core worktree is `D:\Dev\ai-engineering-orchestra`, on
`feature/control-center-s0-feasibility` at the same commit.

Changed tracked files:

- `itru/developer_alpha.py`: three additive preview lines.
- `docs/developer-alpha.md`: preview and compatibility explanation.
- `docs/developer-alpha-first-run.md`: exact subject inspection.
- `docs/developer-alpha-usability-roadmap.md`: dated implementation disposition.

Untracked files intended for review:

- `tests/test_alpha_plan_preview.py`.
- `.ai/tasks/developer-alpha-usability-p0/task.yaml`.
- `.ai/tasks/developer-alpha-usability-p0/context.md`.
- `.ai/tasks/developer-alpha-usability-p0/acceptance-criteria.md`.
- `.ai/tasks/developer-alpha-usability-p0/review.md`.
- `.ai/tasks/developer-alpha-usability-p0/final-verification.md` (this report).

There are no staged changes. All nine initially changed/untracked files were byte-hashed
before verification and remained identical through testing. This session then
added this report and appended the final checkpoint to `review.md`; it did not
alter the existing product, tests, acceptance checklist, or other audit text.
No branch switch, reset, staging, commit, push, merge or publication occurred.
The original Core checkout, reader architecture, archived feasibility evidence
and Control Center were not modified.

## 2. Approval-preview assessment

`make_plan` still constructs the same approval subject from config, complete
work, normalized lifecycle snapshot, action, selected IDs and reference. Its
digest expression, selection, validation and authorization paths are unchanged.
The additive dictionary joins each selected exact ID to its already validated
work definition, then emits only `task_id`, `objective` and `resource` in
`selected` order. It does not normalize, truncate, sort anew or call a provider.

Focused tests establish exact case, leading/trailing whitespace, quotes,
combining Unicode, non-Latin paths, 4096-character strings through CLI JSON,
lexical selection order, dependency blocking, empty selection, unchanged
run/resume/complete digests and rejection of missing/stale approval. Config,
work and lifecycle changes continue to invalidate the digest.

Additional in-memory probes compare all pre-existing response fields against
the exact base for run, resume, completion, all-blocked and unavailable-snapshot
plans. Every field matches after removing the new display array. Six additional
CLI/authorization probes cover selected, blocked, unavailable, invalid-work and
unknown-Task output, plus execution refusal without approval. Provider and
execution constructors are forbidden guards; synthetic environment credential,
key-env name, endpoint and model sentinels are absent from output. These checks
use descriptive snapshots and mocked owner opens; no operational workspace,
inference, Grant, admission or Tool invocation occurs.

The preview carries no authority. Explicit exact Human approval remains required
before execution, and unchanged execution code re-evaluates the plan. Empty,
blocked and incomplete-snapshot plans expose `[]` and no digest; invalid work
and unknown resume Tasks produce the existing rejected JSON/exit 2. The three
guides accurately disclose the older ZIP, input bounds and terminal clipping.
Backward compatibility is additive at the plan JSON field level; no pre-existing
field, digest or execution behavior changed in the examined cases.

## 3. Retained broad-suite classification

The original receipts were inspected before any new test execution. Original
unit discovery reported **2,103 tests, 24 failures, 275 errors, 5 skips** in
148.642 seconds. Counts below are reported failure/error events, including
subtests and nested regression wrappers, not counts of unique root defects.

| Root cause | Errors | Failures | Skips |
| --- | ---: | ---: | ---: |
| Native ancestor access, including predecessor wrappers | 251 | 14 | 0 |
| Journal resource checksum / setup cascade | 18 | 0 | 0 |
| Missing fixed external hostile fixture | 5 | 0 | 0 |
| Retired Python namespace import during discovery | 1 | 0 | 0 |
| Containment matrix launch prerequisite | 0 | 1 | 0 |
| Migration, packaging, help and namespace assertions | 0 | 9 | 0 |
| Platform / symlink prerequisites | 0 | 0 | 5 |
| **Total** | **275** | **24** | **5** |

The complete 299 failure/error headers and tracebacks are preserved in
`.tmp/p0-final-verification/retained-failures.json`. Original logs remain at
`.tmp/usability-p0-unit-tests.log`, `.tmp/usability-p0-alpha-tests.log` and
`.tmp/usability-p0-markdown-lint.log`; their hashes are recorded in
`source-comparison.json` in the final-verification evidence directory.

### Native access: 251 errors and 14 cascading assertion failures

Representative tests: `AtomicDurableDispatchOutboxTests.test_O19...`,
`ControlledResultScenarios.test_R01_success`, and all 14 existing `AlphaTests`.
First relevant trace: `_WindowsHarness` / `alpha.initialize` -> administration
`provision` -> `_lock_registry` -> `_create_registry_namespace` ->
`_reject_reparse_components` -> `_open_file`, line 848:
`PermissionError: [WinError 5] CreateFileW failed for 'Abdelrahman'`.

Shared prerequisite is query-handle access to the current-user ancestor while
checking the registry namespace. This is an environment access failure before
the tested invocation or P0 preview. Read-only native prerequisite probes fail
with the same exception in current and canonical baseline processes. All
underlying native implementation and existing test sources are unchanged.

Fourteen failures wrap predecessor errors: C018/C019/C038; eight C109 native
subcases; C110; L01/L04. They are not fourteen separate assertion defects.
Their shared dependency was reproduced; each wrapper was not rerun separately.
Remediation requires a separately approved supported native-access test context;
do not weaken ancestor checks or bypass the sandbox to claim these tests passed.

### Journal checksum: 18 errors, plus 14 errors in the separate Alpha rerun

Representative: `JournalStorageScenarios.test_J17_atomic_ordered_batch`.
Trace: storage test `setUp` -> `SqliteExecutionJournalStore.provision` ->
`_schema_resource`, line 58 -> `JournalIncompatibleSchema`.
The separate retained Alpha rerun reaches the same checksum guard from
`AlphaTests.setUp` -> `alpha.initialize`, line 70. No preview is reached.
Those separate 14 errors are not added to the 275-error broad-suite total.

The Journal SQL has 48 CRLF line endings in this checkout. Its SHA-256 is
`9fde52c6178a76ee152a736426f6eac32497b992a989ba4d3de98ff0fd0cd8d7`.
The Git blob is LF and hashes to the configured checksum
`844086bcc871212809478af7f213a9b61e891bef4120aa7d4045ab02ad98fb10`.
`core.autocrlf=true`; `.gitattributes` pins admission SQL to LF but has no
equivalent Journal rule. The loader verifies exact bytes before SQL setup.

Current read-only resource loading fails; canonical LF baseline loading passes.
In the isolated baseline only, supplying `git cat-file --filters` bytes that
exactly match this checkout reproduces the checksum failure. Canonical bytes
were restored and the whole export reverified afterward. This demonstrates a
checkout-byte prerequisite, not a defect in the canonical baseline SQL.
Journal code/resources/checksums and test expectations were not changed.
Any durable checkout/packaging correction requires separate scope.

### Missing hostile fixture: 5 errors

Representatives: `ProductionScenarios.test_I07` through `test_I11`.
Trace: `run_scenario` -> `group_I` -> `_validate_hostile_fixture` ->
`_plain_fixture` -> `Path.lstat` -> `FileNotFoundError [WinError 2]` for
`C:\Users\Abdelrahman\AppData\Local\Temp\aio-058-containment-8d832fd4da624cfeacb54a6a1466a1ca`.

The tests require this exact separately provisioned hostile fixture and its
authenticated contract, aliases/security profile and owned-volume evidence.
Both current and base read-only validators reproduce the missing-root error.
No changed P0 code is involved. Do not fabricate the fixture or run its privileged
preparation under this verification; it needs its own approved environment.

### Import/discovery: 1 error

Representative: unittest `_FailedTest.test_authorization_domain_admission_experiment`.
Trace: test import -> `experiments.authorization_domain_admission.sqlite_store`,
line 17 -> `ModuleNotFoundError: No module named 'engineering_orchestration'`.
Current and base imports reproduce this exact retired namespace dependency.
The experiment and test are unchanged. This is not evidence that a missing
third-party dependency should be installed; no dependency installation occurred.
Experiment discovery/namespace disposition belongs to a separate Task.

### Containment matrix launch: 1 failure, zero containment cases exercised

Representative: `AIO058WindowsContainmentExperiment.test_locked_matrix`.
The source requires the fixed Python 3.12 interpreter with **both `-I -B`**.
The original manifest discovery uses `python -B`; its isolated flag is false.
The first internal exception is the `RuntimeError('-I -B required')` guard;
the test catches it and finally asserts `COMPLETE SUCCESS`, line 614.
The retained summary reports environment-stage RuntimeError, 0/56 static cases,
0/3600 races, no roots created and no native data requests.

Deliberate no-`-I` narrow launch comparisons reproduce the same failed assertion
and zero exercises on current and base without provisioning anything. The
matrix's actual containment/security properties remain unverified here.
A correctly launched, separately approved fixture run would still need all its
native, privilege and hostile-storage prerequisites. No P0 code is involved.

### Actual assertions: 9 failures from four expectation families

Seven direct tests reproduce the same assertion failures on current and base:

- O55 expects three admission migrations; production has migration four.
- C001 expects schema version 3; actual is 4.
- C004 expects migration IDs `[1, 2, 3]`; actual includes 4.
- C082 expects the v3 schema fingerprint; the fixture has v4's fingerprint.
- C111 and `PackagingTests.test_explicit_resource_allowlist` omit the existing
  Journal package from their expected package list.
- `TestActiveProjectIntegration.test_help_is_available_without_project_and_uses_wrapper_name`
  expects `{tasks,inspect,verify}`; current/base help includes `alpha`.

Their full first assertion traces are in `current-assertions.log` and
`baseline-assertions.log`. The eighth failure, C109's O55 subcase, wraps that
same migration assertion; its wrapper was inspected rather than rerun wholesale.

The ninth, `NamespaceGuardTests.test_full_explicit_living_manifest`, reports
nine unauthorized legacy occurrences in two schemas and four existing test
modules. Current `living_files` and the explicit baseline living-file inventory
produce the identical nine diagnostics in `current-namespace.log` and
`baseline-namespace.log`. The archive has no Git metadata, so the baseline check
calls the unchanged checker with the verified exported file inventory; it does
not accidentally enumerate the parent worktree's Git files.

These are real failed repository assertions, not environmental exceptions.
Comparative runtime evidence locates their underlying inconsistencies on the
exact base. No changed P0 code is involved. Determining whether each expectation,
allowance or implementation should change is separate work; none was edited.

### Platform restrictions: 5 skips

Four skips require unavailable Windows symlink privilege (`WinError 1314`):
three project-verification symlink scenarios and the Windows owner terminal/
ancestor reparse scenario. The fifth requires POSIX negative-signal return
evidence on this Windows host. Test sources/conditions match the baseline.
These privileged/platform scenarios were not rerun; exact baseline skip
reproduction remains unverified. They are skipped evidence, never PASS.
Remediation needs appropriately authorized Windows symlink or POSIX test hosts.

### Other environment observations

Installed PyYAML, jsonschema and referencing import successfully. The bare
`python` command is absent from this shell's PATH; explicit installed Python
was used. Cached npm files require read access outside the restricted shell;
offline lint used approved access to the existing cache. No installation,
network request, real inference or unapproved operational execution occurred.

The retained repository-wide Markdown lint reported 132 issues in 17 unchanged
files. It remains failed evidence; no full lint rerun or unrelated repair was
attempted. All baseline-tracked sources except the four listed product/guide
files match the base after checkout newline normalization.

## 4. Baseline isolation and attribution limits

Only Git reads supplied the baseline; no existing worktree was modified and no
development branch or linked worktree was created. The final export is
`.tmp/p0-final-verification/baseline-canonical-qxwnu639` and has no `.git`.
All 1,136 exported files were verified against their exact Git blob IDs.
Each normal comparison process uses `-I -B` and asserts that `itru.__file__`
is beneath the selected root. Installed dependencies are shared; no venv or
dependency installation was needed. The deliberate matrix launch comparison
omits `-I` only to reproduce its launch guard, before fixture/native activity.

An initial `git archive` inherited autocrlf conversion. Byte verification exposed
that distinction; its receipt remains `baseline-checkout-export.json`. The
canonical export uses `git -c core.autocrlf=false archive --format=zip <base>`
and verifies every blob. This prevents incorrectly calling CRLF a canonical
baseline defect. The isolated exports are disposable ignored diagnostics, not
new development checkouts or permanent branches; no cleanup of other files ran.

No full baseline suite was run. Attribution is based on unchanged-source
comparison and the stated representative runtime checks, not a claim that all
275 errors/24 failures independently reproduced or that a full baseline passes.
Unexercised native/security paths, individual wrappers and platform skips retain
their stated limits. None of the observed roots implicates the P0 preview.

## 5. Commands, versions and scoped results

Working directory for current checks: `D:\Dev\itru-core-usability`.
Baseline comparisons use the isolated export as their working directory.
Python executable:
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`.
Version: CPython 3.12.10 x64; SQLite 3.49.1. Installed dependencies: PyYAML 6.0.3,
jsonschema 4.26.0, referencing 0.37.0. Git 2.56.0.windows.2; Node v24.20.0;
cached markdownlint-cli2 0.23.3 / markdownlint 0.41.1.

Reproducible orchestration commands were invoked with that explicit Python and
`-B .tmp/p0-final-verification/run_verification.py <mode>`.
The exact expanded child argv, working directory, exit code, output filename,
duration and output SHA-256 are in `commands-latest.json`; invocation history
is in `commands.jsonl`. Raw logs sit beside those receipts. Earlier logging
decoded console output; receipts distinguish its process-byte hash from the
saved text hash where applicable. Original retained logs were not altered.
Repeated diagnostic labels overwrote earlier output files; those superseded
history entries retain command/exit/duration/process-hash metadata only, not
their original output. `command-history-index.json` explicitly identifies them
and the authoritative final run for each label. `evidence-file-hashes.json`
indexes the retained files. The failed suite/schema/probe attempts are disclosed
without presenting superseded receipts as independently retained transcripts.

| Mode/check | Actual result | Exit |
| --- | --- | ---: |
| `focused`: `tests.test_alpha_plan_preview` | 5/5 pass | 0 |
| `focused`: selected pure regressions | 49/49 pass | 0 |
| `preview-probes`: current and base | Five plans identical; six current negative probes pass | 0 each |
| `focused`: Task fixture validator | 54/54; 26/26 Workflow references | 0 |
| `focused`: Workflow fixture validator | 43/43 | 0 |
| `focused`: Role fixture validator | 28/28 | 0 |
| `focused`: Manifest fixture validator | 66/66 | 0 |
| `task-schema`: current Task schema | No errors | 0 |
| `lint`: three guides and current audit Markdown | Zero issues | 0 |
| `git diff --check` | Clean | 0 |
| `baseline`: seven assertion tests | 7 failures on each tree | 1 each |
| `additional`: namespace checker | Same nine diagnostics on each tree | 1 each |
| `baseline`: native, missing-fixture, retired-import probes | Same first exception on each tree | 1 each |
| `additional`: no-isolation matrix launch | Same prerequisite failure; no cases exercised | 1 each |
| Journal resource current / canonical base / checkout-matched base | Fail / pass / fail | 1 / 0 / 1 |

The 49 selected regressions are `test_task_scheduler.SchedulerTests` (21),
`test_task_run_state` (10), `test_agent_execution_journal` (16), and two provider
validation tests (missing key without network, endpoint policy). No provider
HTTP/loopback request tests ran. Reviewers independently reran the five preview
tests with explicit Python `-B -m unittest` and exit 0.

An initial current-Task schema helper supplied a schema name where the existing
API requires a validator; the corrected helper passes. An initial extra CLI
probe retained an old mocked Store after resetting its fixture; correcting the
probe's mock resolves that assertion. These were evidence-harness errors, not
product corrections. Their failed invocations remain in receipt history.

The full suite was not rerun: doing so would repeat demonstrated access/setup
failures and separately governed hostile/native prerequisites without exercising
the blocked behavior. The retained broad result remains **FAILED**, and the
five skips remain **SKIPPED**. Focused success is not full Core success.

## 6. Independent review and Quality Gates

Independent `core_correctness` and `governance_security` Agents inspected the
actual diff, untracked tests, retained failures, final comparison evidence and
this audit. Neither implemented the material P0 change or edited its files.
Both issued **APPROVE for the scoped P0 change and final audit**, with no material
findings. The Core reviewer identified two minor audit wording/receipt issues;
the report now says no staged changes and explicitly indexes superseded output
receipts with separate persisted-output hashes. Both are resolved. The security
reviewer's documentation-consistency outcome is **PASS within the scoped change**.
Their final outcomes are also recorded in `review.md`.

Required broad verification is not green. No failed or skipped required check
is declared PASS or waived. Documentation consistency and independent review
must be interpreted within their expressly recorded scope; neither grants an
exception for the failed broader checks or completes the pending acceptance
criterion. Task-wide independent-review gate clearance is not asserted while
that required acceptance disposition remains open. No Human exception or
acceptance has been inferred.

## 7. Outstanding work and Human Control

The P0 product diff has no identified regression or required scoped correction.
Native access, checkout bytes, hostile fixture and platform prerequisites explain
the environment groups. The retired experiment import and migration/package/
help/namespace inconsistencies are reproduced baseline code/test issues.
The broad suite remains unsuitable as passing acceptance evidence, and genuine
native/security behavior behind blocked setup has not been revalidated here.

The feature is ready for Human evaluation of a local commit, but **not cleared
for commit**: the failed-verification acceptance item still needs an explicit
applicable disposition, followed by final Human approval. A general approval is
not an implicit waiver of failed gates. Otherwise, separate authorized baseline
remediation/environment work and the required validation remain necessary.

Recommended commit message if subsequently authorized:
`feat(alpha): show exact selected subjects in approval plans`.

**STOP AT HUMAN CONTROL.** No stage, commit, push, merge, publish, operational
approval or execution follows from this verification report.
