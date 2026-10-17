# First-Run operator card: static verification and review

Date: October 17, 2026. Scope: the documentation-only P0 first-Run slice authorized
in the [Human decision](architecture/control-center/human-decisions.md#october-17-2026--evidence-archival-and-first-run-documentation-authorization).
No new Task ID, CLI/runtime behavior, configuration key or endpoint was created.

## Sequential prerequisite and changed paths

Phase A completed first in local commit
`f287678b9709a9b04ac62b990361c0dcfb4374de`. Before Phase B, all 31 committed
artifact blobs were rechecked against original SHA-256/byte counts, and the
Core worktree/index were clean. Evidence is preserved in the
[archive](architecture/control-center/evidence/README.md).

Phase B changes only:

- [docs/developer-alpha-first-run.md](developer-alpha-first-run.md): concise
  operator sequence for existing behavior, with preparation/execution boundaries,
  manual approval, expected status landmarks and conservative recovery guidance.
- [docs/developer-alpha.md](developer-alpha.md): discoverability link and explicit
  notice that the existing bundle predates the card; original manual retained.
- [README.md](../README.md): card/manual links and framework/package version
  clarification (`0.1.0` / `0.1.0a1`).
- [docs/developer-alpha-usability-roadmap.md](developer-alpha-usability-roadmap.md):
  dated disposition linking delivered documentation and the committed archive;
  original assessment retained and clearly identified as historical.
- This review record: source traceability, limitations and independent outcomes.

## Command and behavior source verification

Every product command in the card was checked against the parser and router,
then its implementation. No command shown in the card was executed.

| Card instruction | Authoritative source inspected | Verified contract |
| --- | --- | --- |
| Existing ZIP/receipt, hash inspection, `SHA256SUMS.json`, trusted handoff | [Builder](../scripts/build_developer_alpha.py), [release validator source](../scripts/validate_developer_alpha.py), [manual](developer-alpha.md#install-and-offline-integrity); local receipt and filenames inspected read-only | Builder's exact ZIP/receipt/payload names and hash relationship; no public acquisition channel or signature claimed. PowerShell `Get-FileHash -LiteralPath ... -Algorithm SHA256` only inspects the named archive. |
| `py -3.12 -m venv .venv`; explicit venv Python offline `pip install --no-index --no-deps --find-links wheelhouse --require-hashes -r requirements.lock` | Manual installation block; release validator installation argv | Exact existing offline installation procedure; no dependency download or installation performed for this task. |
| Explicit venv `itru.exe --version` and `alpha --help` | [CLI](../itru/cli.py), [version](../itru/__init__.py), [metadata](../pyproject.toml) | Existing options; version `itru 0.1.0a1`. These are expectations, not new output evidence. |
| `alpha init $workspace`; `Join-Path`/`Get-Content` for generated sample paths | [Alpha initialize/example_work](../itru/developer_alpha.py), [manual](developer-alpha.md#local-demo) | New exact path with existing plain ancestors; real provisioning and sequential setup, generated `alpha.json`, `example-work.json`, `repository/input.txt`; no atomic rollback assumed. Shell inspection is limited to the new nonsecret sample. |
| Optional provider configuration reference | [Closed config validation](../itru/alpha_config.py), [adapter](../itru/alpha_provider.py), [approved example](developer-alpha.md#configure-a-byo-provider) | Exact five-field provider shape; demo has no inference; compatible endpoint rules, environment-variable name, objective/resource disclosure, no file bytes; no fabricated provider setup or credential values. |
| `alpha load --config $cfg --work ...`; inspect `work.json` | CLI; Alpha `load_work`; [example](../examples/developer-alpha/work.json) | Exact flags and explicit work; immutable loaded definitions; three example Tasks, two prerequisites, `input.txt` only. |
| `alpha plan --config $cfg` | CLI; Alpha `make_plan`, `context`, `open_state`; [Store](../itru/sqlite_task_run_state.py) | Default run action; selected IDs and `approval`; subjects require cross-reading exact work. Owner acquisition/recovery is operational, without a provider/key connectivity check. |
| Manual `$approval` then `alpha run --config $cfg --approve $approval`; `$LASTEXITCODE` | CLI; Alpha `require_approval`, `execute` | Exact current approval binding; no automatic digest forwarding. Governed bounded read and configured provider work; exact success/attention statuses and Result/Journal fields. |
| `alpha history --config $cfg [--after $after]` | CLI; Alpha `history` | Integer cursor, maximum 100 records, `journal_more`/`journal_after`, recaptured high-water, owner/recovery boundary; no frozen traversal or reconstructed Results. |
| Separate completion/resume/stop references and error table | CLI exception handling; Alpha `command`/`make_plan`; [Task states](../itru/task_run_state.py) and Store recovery; manual recovery/completion sections | Exit codes 0/1/2/130; success leaves governance pending; separate completion attestation; no automatic retry; unsafe history cannot resume; busy owner cannot be seized; missing Results/uncertain effects remain unresolved. |

The card explicitly requires one command at a time and stopping on error; its
quoted approval placeholder cannot supply a valid digest without a deliberate
Human edit. The existing completion walkthrough is linked rather than scripted.
No aggregate `itru verify`, release builder, validator, authentication probe or
inference test is introduced into the first-run sequence.

## Package evidence and limitations

The existing ignored local ZIP was inspected read-only: 2,066,114 bytes; SHA-256
`e9363941bd8b30513ea9c92b4fd595159eb3c8560dfdff1dcdb0d70475389cdb`
matches the retained build receipt. Its dependency filenames include CPython
3.12 `win_amd64` wheels; the card scopes this bundle to Windows x64 CPython 3.12.
This is hash/source evidence, not a new installation, release validation,
signature or platform-support expansion. The trusted maintainer handoff remains
an operator prerequisite; no download URL is invented.

The old ZIP and receipt are untouched. The new card is not in that ZIP. The
checkout's authorized link addition to `docs/developer-alpha.md` changes that
one product fingerprint relative to the historical build receipt; the other
14 of 15 listed product files remain hash-identical. The historical receipt is
not claimed as fresh validation of this documentation revision. No bundle,
fingerprint receipt or package was rebuilt or refreshed.

No first-run, CLI, runtime, installation, inference/authentication, network,
build or product test execution occurred. Manifest schema validators and
network-capable Markdown lint/aggregate verification were not run under the
explicit static-only instruction. Existing test source was read as supporting
context; historical tests were not rerun or claimed as fresh PASS results.

## Static checks and independent outcomes

- Every scoped relative file-link target resolves. Linked manual sections exist;
  command/flag and expected-behavior checks are traced above.
- The original roadmap body and full manual body remain intact beneath their
  newly added current-status/discoverability notes.
- Exactly the five documentation paths listed above are staged; no unintended
  untracked paths or unstaged tracked differences remain.
- Both `git -c core.autocrlf=false diff --check` and its `--cached` form returned
  exit 0 with no whitespace diagnostics for Phase B. The preserved CRLF finding
  in Phase A is recorded in that archive's review; it is not part of this diff.
- The 31 evidence hashes/byte counts, protected-document hashes and separate UI
  baseline are rechecked at final closure. No evidence artifact is changed by
  this phase.

| Independent reviewer | Scope | Actual outcome and disposition |
| --- | --- | --- |
| `/root/integrity_review` | All five intended paths against parser/router, Alpha/config/provider/Task-state source and existing package evidence; commands, statuses, links and provenance | **APPROVE**. No invented flags, keys, endpoint or transcript; no missing file-link targets or unresolved accuracy findings. Independently confirmed the manual is the sole differing historical product fingerprint. |
| `/root/packaging_review` | Actual card, review record and existing-doc diffs against governance/safety source; all ten requested journey topics, approval, recovery and scope | **APPROVE**. Preparation/inspection/execution boundaries, credential safety, governance pending and uncertain-effect treatment are correct. No unresolved governance or safety findings. |

Both reviews were read-only and performed by separate Agent execution instances
from the implementer. Documentation consistency and independent review Quality
Gates pass within the authorized static scope. No skipped executable check is
reported as passed.

Final Human acceptance remains required. Stop after the authorized local Phase B
documentation commit and report; no further usability feature or reader work,
push, merge, tag, publication or release action follows.
