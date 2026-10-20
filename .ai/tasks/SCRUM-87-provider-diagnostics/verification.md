# SCRUM-87 implementation and verification

## Handoff state

October 20, 2026. Implementation/testing authorized; final Human acceptance,
staging, commit and Task closure are not authorized. Task remains `in_progress`.
Workspace: `D:\Dev\ITRU\worktrees\itru-core-usability`. Branch:
`feature/developer-alpha-usability-p0`. Starting HEAD:
`90fa7137e49fb60309200b0292375ec84d757852`; starting Git status was clean.
No branch reset/switch or existing-change overwrite occurred.

## Implemented behavior

`alpha diagnose --config` reuses the closed configuration/file checks and tests
only configured credential presence. It prints fixed kind/presence/limit facts,
never configuration or environment values. It returns before work loading,
owner acquisition, recovery, authority/storage composition or provider/Tool
invocation. Valid demo, valid compatible setup, intentional empty `key_env`,
missing/empty credentials and invalid inputs have deterministic handling.

Alpha invocation and operation errors use fixed codes/reasons/recovery. Unknown
exceptions and arbitrary ProviderError text cannot be rendered. Known busy-owner
and uncertain-commit exceptions retain safe recovery categories. Missing/stale/
malformed Human approval is distinct from provider setup and remote failure.
Non-ASCII/wrong-type approvals remain rejected with the Human-approval category.
Non-Alpha argument parsing is unchanged.

Provider-worker failures retain their existing cancellation and
`provider_failed_before_tool` outcome/reference, adding only fixed CLI
`provider_diagnostic`. Request failure does not speculate about remote causes;
malformed/oversized/tool-call responses and redirects have separate recovery.
Endpoint validation rejects whitespace/control characters and all embedded
userinfo. No canonical Task/Run/Result/Journal contract, digest input, selection,
authority sequence, automatic retry or approval semantics changes.

The manual gives reproducible before/after examples. First-run guidance preserves
the existing offline-bundle sequence and identifies diagnostics as an optional
current-checkout feature; the existing ZIP was not rebuilt. The roadmap's current
disposition distinguishes implemented provider diagnostics from future work
preflight and broader CLI/Provider milestones.

## Changed-file inventory

Product:

- `itru/alpha_config.py`
- `itru/alpha_diagnostics.py` (new)
- `itru/alpha_provider.py`
- `itru/cli.py`
- `itru/developer_alpha.py`

Tests and guides:

- `tests/test_alpha_diagnostics.py` (new)
- `docs/developer-alpha.md`
- `docs/developer-alpha-first-run.md`
- `docs/developer-alpha-usability-roadmap.md`

New Task records under `.ai/tasks/SCRUM-87-provider-diagnostics/`:

- `task.yaml`
- `context.md`
- `acceptance-criteria.md`
- `review.md`
- `verification.md`
- `verify_offline.py`

Completed P0 Task records, Core contracts/schemas, release artifacts, UI and
SCRUM-86 remediation files are unchanged.

## Exact commands and results

Interpreter: `C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`
(CPython 3.12). Each reproduction uses this interpreter with `-B` and
`.ai/tasks/SCRUM-87-provider-diagnostics/verify_offline.py <mode>` from the workspace
above. The helper retains exact argv/cwd/exit/duration/output SHA-256 in
`commands.jsonl` beside raw process-byte logs in a fresh OS temporary directory.
It propagates failure status and does not install dependencies or execute full
Manifest commands. `lint-cache` uses the existing local cache path from prior
evidence; it needs read access to that path and performs no network access.

| Mode / check | Final result | Exit |
| --- | --- | ---: |
| focused: new diagnostics and existing P0 approval previews | 28 tests PASS: 23 new + 5 existing; zero skips | 0 |
| focused: scheduler, Run-state, Journal contract, existing offline provider tests | 50 tests PASS; zero skips | 0 |
| schemas: Task fixtures and declared Workflow references | 54/54 cases; 26/26 references PASS | 0 |
| schemas: Workflow / Role / Manifest validators | 43/43; 28/28; 66/66 PASS | 0 |
| schemas: current SCRUM-87 Task schema | No errors | 0 |
| schemas: `python -B -m itru verify --structure` | PASS; project commands not executed | 0 |
| lint-cache: changed guides and current Task Markdown | PASS; seven files, zero issues | 0 |
| diff: `git diff --check` | PASS; final Git inspection confirms no staged files and unchanged HEAD | 0 |

The new tests exercise the actual bounded JSON reader/closed config validator
using synthetic files, forbidden socket/operational-entry guards, mock HTTP
opener responses, secret sentinels, CLI stdout/stderr/exit behavior, provider
category propagation, cancellation before Tool invocation and no automatic
retry. Config ACL checks are mocked; these are not native ACL readiness tests.
Existing unchanged preview tests prove exact digest compatibility and stale
approval rejection across config/work/lifecycle changes.

Retained receipt directories (under
`C:\Users\ABDELR~1\AppData\Local\Temp\`):

- `scrum87-verification-mdsxb5yb`: final 28-test focused run and 50 regressions.
- `scrum87-verification-52ey3fou`: earlier 28-test focused run and 50 regressions.
- `scrum87-verification-vo4_lkdw`: earlier 27-test focused run and 50 regressions,
  before the additional argument-parser regression; both PASS.
- `scrum87-verification-i2grgiyw`: all schema and structure checks.
- `scrum87-verification-6vbr7woj`: failed offline npx lookup, retained unchanged.
- `scrum87-verification-ofo96t09`: failed restricted cached-linter launch.
- `scrum87-verification-boke48gu`: successful cached lint of the first six Markdown
  files.
- `scrum87-verification-2t952tag`: successful cached lint including all seven final
  guide/Task Markdown files.
- `scrum87-verification-0gxp6n8w`: final diff/status/HEAD receipts (all exit 0).

These directories are evidence outputs, not active worktrees. Historical P0
paths remain unchanged in their historical records.

## Failed attempts and checks not performed

The first combined unittest invocation ran 27 tests and exited 1 with eight
failure events. Six subtest failures came from changing the original approval
message's initial letter to uppercase; restoring the exact original text fixes
compatibility without changing P0 tests. Two new-test failures were harness
issues: mocking the shared `os.environ.get` intercepted argparse/gettext locale
lookup, and a help substring assertion crossed a line wrap. The tests now mock
only the provider's environment reference and normalize help whitespace. The
original failed output is retained in the tool transcript, not a separate raw
log file; this paragraph is its explicit summary, not a claim of raw-log retention.
The CLI reviewer also independently observed those two harness failures before
their correction. Those invocations remain FAILED historical results.

The attempted `.tmp/scrum87-verification` creation was denied by its filesystem
permissions. No permissions were altered. Evidence therefore uses fresh allowed
OS temporary directories. Offline npx initially failed with `ENOTCACHED`; direct
cached lint initially failed module access in the restricted process. Both failed
logs/receipts remain retained. The same pre-existing cached linter then ran with
approved cache read access: no dependency download or installation occurred.

Full Core discovery, full C109, native controlled Alpha integration, loopback
HTTP tests, clean installation and release validation were NOT RUN. Broad
discovery would execute network/native fixtures outside these deterministic
checks and repeat known prerequisites. These omissions are not PASS. No real
provider request, loopback request, paid inference, operational demo walkthrough,
privileged fixture preparation, release build, publication or UI integration ran.

Known SCRUM-86 debt remains open: retained Core-wide **24 failures, 275 errors,
five skips**, nonexecuted full C109, and previously retained broad Markdown lint
failure. No debt result is reclassified or waived. Scoped success is not full
Core health, native readiness or packaged-release certification.

## Independent review and Human Control

Independent `security_review` and `cli_review` executions inspected the actual
changed files, requirements and evidence without editing implementation files.
Both approved the scoped implementation; CLI review also assessed documentation
consistency as PASS. They independently ran the then-current 22 diagnostics and
five unchanged preview tests. Security review additionally guarded preview tests
against sockets. Their final parser/audit delta review is recorded in `review.md`.
Both reviewers also inspected this audit and the verification helper and verified
recorded test/schema log hashes and exits. Security checked ten receipt/log pairs;
CLI checked eight final focused/schema pairs. Restricted cache-log access was
unavailable to those reviewers; their independent documentation-consistency
review does not claim direct inspection of the cached-lint receipt. The final
cached lint was run by the implementation execution with approved read access.
The first-run executable ambiguity and provider-code/userinfo robustness findings
were resolved before approval. No material finding remains. The independent
review and documentation-consistency gates PASS for SCRUM-87's bounded scope.

The feature is ready for final Human review of a possible local commit. All scoped
checks/reviews are recorded; no required scoped Quality Gate failed or was skipped.
The expressly not-run broad/native/network checks and SCRUM-86 debt retain the
limits above. No commit authority or Task closure is inferred.
**STOP AT HUMAN CONTROL: no staging, committing, push, merge, PR or release.**
