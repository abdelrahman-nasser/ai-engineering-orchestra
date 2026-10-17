# Application v1.0 synthetic integration preparation

This is standalone UI-only preparation on `ui/control-center-integration-prep`,
based on UI commit `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67`. The current Human
instruction authorizes this synthetic scope. It does not resume S5 or the blocked
S1–S8 operational integration. S0 remains closed at NO-GO.

## Reference evidence

Read-only technical source: `D:/Dev/ai-engineering-orchestra/docs/architecture/control-center/application-boundary-v2.md`,
approved v2 SHA-256 `c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062`.
The subsequent `human-decisions.md` establishes approval scope and later reader
deferral; candidate/pending labels inside the preserved design are historical.
Sections 6, 8–10, 12–14 supply the exact closed fields, enums and UI obligations.
The reconciliation addendum and current Core timestamp/resource contracts were
read statically; no Core code is imported, modified or executed.

Governance used: root `AGENTS.md`, `.ai/project.yaml`, bootstrap principles,
terminology and precedence, `standard-change.yaml`, canonical
`roles/software-engineer.yaml`, and independent-review/documentation-consistency
gates. `.ai/rules/` does not exist in this base. The current Human instruction is
the Task scope; no historical `.ai` Task/release artifacts are changed.

## Implemented surface

Open `/application-v1-preview` using the sidebar link. Every observation and
context is synthetic. The existing `MockControlCenterDataSource` binding remains
unchanged. Existing catalog, river, approval and rich Result demonstrations stay
separate; their data models and adapters are not used by this preview. On this
route the shell labels the synthetic source and shows approval count unavailable.
Primary navigation explicitly leads back to separate mock demonstrations.

Files under `src/app/application-v1/`:

- `contracts.ts`: UI-owned closed application `1.0` request and success/error models
  inferred from exact shape validators; complete nested Binding, Contract,
  Journal Entry/Admission/Grant and content-free summary fields.
- `validation.ts`: unknown-field/type/enum rejection, required nullable fields,
  duplicate-aware logical JSON decoding, canonical decimal strings, exact UTC
  calendar validation and BigInt microsecond keys. Grant fractions retain their
  original 0–6 digit spelling; other times require six digits. Only bounded
  integer tokens use JavaScript Number. Opaque text is never normalized.
- `decode.ts`: inert request decoding and whole-response decoding with no usable invalid prefix, exact
  source/inspection/Binding/ledger matching, supplied graph/history/coverage
  consistency checks and strict summary diagnostics/nullability. Selected and
  historical Run states require an accepted Result identity exactly for
  `succeeded`, `failed_before_effect` and `effect_ambiguous`; other Run states
  require explicit null. Historical identities retain their own ledger/domain.
  There is no
  scheduler, readiness, authority, eligibility or lifecycle-transition evaluation.
  Error prose from a future producer is never retained/displayed: the design
  has no literal server-message table, so the UI uses its own fixed public text.
- `presentation.ts`: bounded-to-one-current-observation display state with no
  persistence. Historical values survive only ordinary busy/unavailable/deadline
  refresh failures in the same still-entitled synthetic context. Denial/revocation
  and principal/policy/source-context changes clear prior subject references.
  Invalid pages yield no page data, while the independent lifecycle panel remains.
- `fixtures.ts`, `synthetic-preview.*`: fabricated scenarios for interrupted
  lifecycle plus recorded success, successful historical Run plus an unfinished
  Task, explicit registration latest, disconnected pending capacity consumer,
  missing Task observation, over-capacity decision, partial-empty/complete-empty Journal coverage,
  Entry-only evidence, multiple physical subjects/outcomes, stale reads, denial,
  incompatible/invalid/expired/exhausted/not-found/loading states.

Numeric edge fixtures deliberately exercise the projection's full integer
ranges. They are not claimed to be operational histories realizable under P07's
event/row/work limits. Delivery-context snapshots are captured explicitly;
responses from an earlier context are withheld even if the same named principal
is later selected again.

The UI displays supplied decisions unchanged. It does not recompute Core
readiness, select a winner in conflicting evidence, infer Task completion from
Run success, derive global recency, or map Journal events into Workflow stages.
`configuredRoute` is unavailable: Binding remains exactly `{run, tool_id}`;
runtime/environment/operation are ordinary Contract fields. Approvals are
unavailable, never zero. Continuation is always unassessed; Execute, Approve,
Cancel and Resume are disabled with no handlers or command paths.

Journal displays only the two canonical event kinds, metadata provenance,
recording/observation times, physical identities and recorded summaries. No
payload/text/hex previews, source-content hashes, digests, signature badges or
live Result reconstruction exist. Complete-empty coverage is scoped to that
Journal/high water; it proves no absence of invocation or effects elsewhere.

## Limits and handoff

This is not a real adapter, authenticated reader, operational store validator,
P07 resource-admission implementation, cursor engine or cross-page accumulator.
`PreviewContext` is a fabricated state-machine input, not an authentication
mechanism. No HTTP/IPC/SSE choice, service, runtime connection, retry/poll loop,
persistent/offline observation cache, export, or Core import is introduced.
The UI never establishes whole-Journal semantic validation or cryptographic
authenticity itself. The validation label explicitly describes a synthetic
producer assertion. Prior Entry linkage across pages, complete-snapshot
validation, comparison/discrepancy generation and cursor/principal binding
remain future Core/application responsibilities behind separately authorized
reader admission. These tests establish no operational safety or runtime PASS.

All source/documentation changes stay below `ui/control-center/`. The supplied
offline `node_modules` is used without installation. Build/cache outputs stay in
this worktree. No parked SCRUM-81 transfer or other-worktree write occurs.

## Validation and control

Validation performed on October 17, 2026 with Node `v24.20.0`, npm `11.19.0`,
the provided offline dependencies and Vitest `5.0.4`. All npm script invocations
used `NG_CLI_ANALYTICS=false` and `npm_config_offline=true`; final invocations
also disabled npm's update notifier. Commands below run from `ui/control-center`
except the Git checks, which run at the worktree root.

| Check | Exact command | Final result |
| --- | --- | --- |
| Application and spec types | `npm run typecheck` | Exit 0; both tsconfig targets pass. |
| Focused new and shell regression tests | `npm run test:ci -- --include 'src/app/application-v1/**/*.spec.ts' --include 'src/app/app.spec.ts'` | Exit 0; 4 files, 202 tests pass. |
| All existing and new UI tests | `npm run test:ci` | Exit 0; 22 files, 343 tests pass. |
| Production build | `npm run build` | Exit 0; initial bundle 363.14 kB; synthetic preview lazy chunk 44.53 kB; no budget warnings. |
| Tracked whitespace check | `git diff --check` | Exit 0; no findings. |

New files are also checked individually using
`git -c core.autocrlf=false --no-optional-locks diff --no-index --check -- /dev/null <new-file>`
without staging them: all 12 new files produced no whitespace findings. Git's
no-index exit 1 identifies new-file differences, not a whitespace finding; the
aggregate check returned exit 0. An initial invocation without the configuration
override also emitted the repository's LF-to-CRLF conversion advisory.
Output/build caches remain under this worktree's `ui/control-center/`.

Initial typecheck iterations found fixture-array and test-tuple inference errors;
these were corrected before the final passing checks. All requested npm checks
pass; inherited Markdown findings are recorded below.

Manual documentation consistency comparison checked README, the historical
question-record qualifier and this report against the implementation, approved
v2 and later Human decisions. No material contradiction was identified. Changed
source, templates, tests and documentation were self-reviewed. The independent
review disposition is recorded below.

Independent reviewer `ui_preflight_review` issued **CHANGES REQUIRED**, as relayed
by the coordinator's session follow-up. The remaining concrete finding was that
`decodeInspectRun` accepted contradictory Run-state/accepted-identity pairs when
the selected lifecycle and matching history agreed with each other.

Remediation adds one descriptive consistency guard to the selected lifecycle and
every history entry. A nonnull accepted identity is required exactly for
`succeeded`, `failed_before_effect` and `effect_ambiguous`; `pending`, `running`,
`interrupted` and `cancelled` require null. Fourteen regressions cover the wrong
combination for each state in the selected lifecycle (with matching target
history) and in a separate historical entry. The existing positive regression
for a historical identity with its own ledger/domain still passes; history is
not rebound to the selected Run's ledger. Read-only evidence was checked in
Core `task_scheduler._snapshot` and `core/task-run-state-specification.md`.
No readiness, scheduler, lifecycle-transition or authority computation is added.

The repaired context-token A→B→A and fragment-route regressions remain green in
the focused and full suites above. That earlier follow-up changed only `decode.ts`,
`decode.spec.ts` and this report; no broader review finding was taken into scope.
On October 17, 2026, independent Reviewer `ui_preflight_review` issued
**APPROVE** for the scoped product diff and updated audit evidence. All material
findings are resolved. Independent review: **PASS**. Documentation consistency:
**PASS**. No operational acceptance or waiver of inherited lint is implied.
Final **Human review remains required**. This scoped implementation is ready for
review, not a fully approved Task completion or operational admission.

Repository-wide Markdownlint was not run for this UI-only scope. The coordinator
used an already-cached `markdownlint-cli2` directly, without installation or
network access, on the three changed documentation files. The new preparation
report passes; README and the historical questions record have ten inherited
findings (nine MD032 and one MD040). Exact HEAD copies in ignored scratch space
produce the same ten findings, with only line offsets changed. These are
unwaived baseline failures, not a mechanical clean-lint PASS or authorization
for unrelated cleanup. Core tests/schema validators and operational acceptance
were not run for this UI-only scope. Browser layout QA was not performed;
Angular DOM tests and the production template build passed.

All changes remain unstaged and uncommitted. No push, merge or publication is
performed. Stop at Human control after coordinator review handoff.

## Final Lane B verification and commit candidate — October 17, 2026

### Worktree and preserved evidence

- Worktree: `D:/Dev/itru-ui-integration`.
- Branch: `ui/control-center-integration-prep`.
- HEAD/base: `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67`
  (`feat: polish Developer Alpha Control Center integration (SCRUM-26)`).
- Original UI worktree: `D:/Dev/itru-ui`, still on
  `ui/developer-alpha-integration-qa-polish` at the same baseline. No tracked
  changes; its sole untracked file remains
  `ui/control-center/docs/ITRU-064-ui-runtime-integration-readiness.md`.
  Preserved SHA-256:
  `21478d4423c9e4761971507f95cafa0fb7ef9e848790d447b512bfdffb3c3be3`.
- Parked SCRUM-81: `ui/itru-062-contract-i18n-rtl`, unchanged at
  `61e817c1f7a2c3987710a73366b516d792402520`; no transfer performed.
- Approved v2 reference hash was rechecked against the value above. Core's
  architecture directory remains read-only and has no pending changes.

### Contract and semantic findings

The final contract review found **C-01: missing closed request models** (medium).
The original response-only preparation did not meet the explicit request-shape
acceptance criterion. The scoped repair adds inert `InspectRunRequest` and
`ReadRunJournalRequest` models and separate decoders. They accept exactly
`application_version`, `source_id`, `source_revision` and the operation's subject
field (`run_id` or `inspection_ref`). Only Journal requests permit optional
`limit` and `cursor`. A supplied limit must be an exact integer in `1..100`;
absence remains absence, preserving the producer's default of 50. Explicit
null/undefined optionals, unknown keys/versions, malformed text, duplicate JSON
keys and unsafe numeric tokens are rejected. Opaque text is preserved.
No operation discriminator, dispatcher, request client or transport was added.
Forty-three request regressions cover this repair.

**C-02: README source-label and dataset-location wording** (minor) is corrected
to distinguish existing mock screens from the isolated synthetic preview.
Both findings are resolved within this lane. No additional product files or
operational behavior were introduced by final verification.

Review confirmed the closed success/error fields, canonical lifecycle and
scheduler enums, eleven-field Contract, complete Binding and ledger identities,
five-part physical Result identity, exact integer/timestamp representation,
inspection reference matching, high-water/cursor/coverage fields and required
nullable values. Prior accepted-identity/state contradictions, historical-ledger
preservation, A→B→A delivery invalidation and fragment-route handling remain
covered and resolved.

The UI keeps Run success separate from Task completion, uses explicit
registration-order latest evidence, preserves disconnected scheduler capacity
consumers and supplied selection, and separates Task dependencies from Workflow
stages. Journal summaries remain content-free with their recorded provenance;
partial, complete-empty, conflict, stale, denied, unavailable, incompatible,
invalid and expired states retain their distinct meaning. Unknown approvals,
rich metadata, Stage/Actor/live activity, configured routes and historical
payloads remain unavailable. Continuation is always unassessed and every
operational control remains disabled, with no keyboard or indirect command path.

Option D remains active: operational reader admission is **DEFERRED**. There is
no real Core/runtime/store connection, source enumeration, HTTP/REST/SSE/
WebSocket/IPC integration, authentication mechanism, generic execution endpoint,
autonomous scheduling, approval submission, continuation or cancellation command.
The mock provider binding and dependency manifests/lockfile are unchanged.
S5 and all other blocked operational slices remain inactive.

### Fresh validation receipts and limitations

The validation table above now reflects the final repaired candidate. The earlier
159-focused/300-full counts were reproduced before remediation; final counts
are 202-focused/343-full. Commands ran separately against existing dependencies.
All four npm checks returned exit 0 without warnings or skipped tests. No
dependency installation, download or upgrade occurred.

Local raw output is retained under ignored `ui/control-center/.tmp/`:
`final-review-typecheck.log`, `final-review-focused.log`,
`final-review-full.log`, and `final-review-build.log`. Each npm invocation used
`Tee-Object`, captured `$LASTEXITCODE`, printed `EXIT_CODE`, and returned that
code. These local receipts are excluded from the commit.

Tracked `git diff --check` and `git diff --cached --check` pass (exit 0). The twelve new
files were individually checked with the no-index command above: zero findings,
aggregate exit 0. No generated build/cache/log artifact appears in the proposed
Git inventory; the index is empty.

The actual cached checker was invoked offline with this command from the root:

```powershell
node 'C:\Users\Abdelrahman\AppData\Local\npm-cache\_npx\3158f213c58abe1a\node_modules\markdownlint-cli2\markdownlint-cli2-bin.mjs' 'ui/control-center/README.md' 'ui/control-center/docs/core-contract-questions.md' 'ui/control-center/docs/application-v1-preparation.md'
```

`markdownlint-cli2 0.23.3` / `markdownlint 0.41.1`: **exit 1, ten issues in two
files**. Nine MD032 findings remain in the historical question record and one
MD040 remains in README. The preparation report passes. Exact HEAD copies of
the two documents were written with Node's byte-preserving Git subprocess
output and checked with the same CLI: exit 1, the same ten rules/contexts, with
line offsets only. Logs: `final-review-markdown.log` and
`final-review-markdown-baseline.log`. No new documentation lint finding exists.
These baseline failures remain unwaived and require Human disposition before
treating the candidate as cleanly accepted. No unrelated formatting cleanup
was performed.

An initial module-only checker invocation exited 0 without running lint and is
not counted as validation. A Python baseline-copy helper was unavailable; Node
completed and byte-verified that preparation. Initial read-only Git inspection
of the original worktree required a command-local `safe.directory` override;
no global configuration was changed.

Repository-wide Markdownlint, Core tests/schema validators, operational tests
and browser visual QA were not run in this UI-only lane. The Angular DOM tests
and production template build passed; no operational safety, reader admission,
cryptographic integrity or runtime acceptance result is claimed.

### Independent final review

| Independent reviewer | Actual review scope | Final disposition |
| --- | --- | --- |
| `/root/contract_semantic_review` | Actual source, fixtures, tests, shell/docs diff; approved v2 and later Human decisions; prior findings; closed requests and final repaired candidate. | APPROVE; C-01 and C-02 resolved; no material finding remains. |
| `/root/safety_governance_review` | Actual source/diff and repaired request validators; Option D, disabled controls, synthetic provenance, retention/revocation/context tokens, provider isolation and documentation. | APPROVE; no material findings. |

The reviewers are distinct Agent execution instances and neither implemented
these changes. The coordinating Agent implemented the scoped C-01/C-02 repair.
Both reviewers inspected the final audit text and refreshed raw validation
receipts. Independent review: **PASS**. Documentation consistency: **PASS**.
These results do not waive the inherited lint failures. Human acceptance is a
separate required checkpoint. A final file-hash inventory and boundary checks
are retained locally in ignored `.tmp/final-review-manifest.json`.

### Exact proposed local commit scope

Eighteen files total: six tracked modifications and twelve new files. The list
below is an explicit future staging candidate; nothing has been staged.

```text
ui/control-center/README.md
ui/control-center/docs/core-contract-questions.md
ui/control-center/docs/application-v1-preparation.md
ui/control-center/src/app/app.html
ui/control-center/src/app/app.routes.ts
ui/control-center/src/app/app.spec.ts
ui/control-center/src/app/app.ts
ui/control-center/src/app/application-v1/contracts.ts
ui/control-center/src/app/application-v1/decode.spec.ts
ui/control-center/src/app/application-v1/decode.ts
ui/control-center/src/app/application-v1/fixtures.ts
ui/control-center/src/app/application-v1/presentation.spec.ts
ui/control-center/src/app/application-v1/presentation.ts
ui/control-center/src/app/application-v1/synthetic-preview.css
ui/control-center/src/app/application-v1/synthetic-preview.html
ui/control-center/src/app/application-v1/synthetic-preview.spec.ts
ui/control-center/src/app/application-v1/synthetic-preview.ts
ui/control-center/src/app/application-v1/validation.ts
```

Exclude `.tmp/`, `.angular/`, `dist/`, `node_modules/`, every generated receipt,
all Core/other-worktree files, the original untracked readiness report, and
parked SCRUM-81 work. None belongs in this commit.

Proposed commit message and recommended later PR title:

```text
feat(ui): prepare Control Center application v1 read models
```

Recommended later PR description:

> Prepare closed, lossless UI-owned application v1.0 request/response models and
> an isolated synthetic inspection/Journal preview. Preserve canonical Task/Run
> states, supplied scheduler evidence, content-free summaries, explicit coverage
> and unavailable-data states; keep operational controls disabled and the existing
> mock provider unchanged. Operational reader admission remains deferred.
>
> Validation: typecheck, 202 focused tests, all 343 UI tests and production build
> pass. Independent contract/semantic and safety/governance review completed.
> Changed-document lint retains ten verified baseline findings; the new report
> passes. No browser visual or operational validation was performed.

Lane B is prepared for **Human acceptance review**, with the inherited lint
disposition explicitly outstanding. It is not a fully accepted Task or operational
admission. Separate Human approval is still required before staging or committing.
No commit, push, merge, PR publication or original-UI modification is performed.
**STOP AT HUMAN CONTROL.**
