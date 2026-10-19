# Application v1 browser QA and UI polish — October 19, 2026

## Scope, preflight and authority

Human instruction: **ITRU — LANE B: BROWSER QA & UI POLISH — PROCEED**.
Workspace: `D:/Dev/itru-ui-integration`; branch:
`ui/control-center-integration-prep`; unchanged HEAD:
`20f0abd8347bfbc054f926f0eb96308ed8092c36`.
The starting index and worktree were clean. The Result-identity guard and its
fourteen regressions were already committed and were preserved.

Governance: root `AGENTS.md`, known Project Manifest/bootstrap contract,
`standard-change.yaml`, software-engineer/reviewer Roles and independent-review /
documentation-consistency gates. The current Human instruction supplies Task
scope. `.ai/rules/` is absent; no historical Task artifacts were rewritten.

Approved Core architecture and later Human decisions were read only. Option D
remains active: S0 closed NO-GO; S1–S8 unauthorized. No real Core reader, database,
credentials, operational transport, execution/approval/cancellation/resume path,
dependency installation or parked SCRUM-81 transfer was introduced. Contracts,
decoders, validation and presentation-state semantics remain unchanged. The mock
provider binding remains unchanged. Added metadata is explicitly synthetic.

## Browser and viewport coverage

Actual Chrome browser automation used the installed Angular development server
at `http://localhost:4200`, started with `npm start -- --host 127.0.0.1 --port 4200`.
Existing dependencies were used offline. No operational Core command was run.

The browser had existing 90% zoom. Viewport overrides were adjusted and **actual
CSS dimensions were read back**, rather than inferred from screenshot pixels.
Temporary viewport overrides were reset after QA.

| Surface | Actual rendered coverage | Evidence and result |
| --- | --- | --- |
| `/application-v1-preview` | 1440×900 dark; 1024×767/768 dark/light; 390×844 dark/light; 320×800 light long-text check | Desktop columns, tablet rail/single column, mobile notice/stacking and exact metadata wrapping inspected. No page-wide horizontal overflow in the scenario checks. |
| All 18 synthetic scenarios | Live 390×844 light browser matrix and final 1440×900 dark matrix | Distinct loading, not-found, denied, incompatible, invalid, expired, exhausted, unavailable and stale states; partial-empty, complete-empty, Entry-only, success-with-unfinished-Task, over-capacity, missing graph observation, conflicting physical subjects and long metadata exercised. Four operational buttons stayed disabled throughout. |
| `/flow` | Desktop 1440×900 dark/light; tablet 1024×768 light; mobile 390×844 dark/light | Fan-out, 24-node mesh, effect-ambiguous, empty and stale scenarios inspected. River/list, keyboard selection, zoom, reset, fit, center and pointer pan exercised. |
| Existing Nile and Run detail | `/runs/run_a41c07e2`, mobile 390×844 dark | Ten workflow-river nodes rendered; decorative animation pause and keyboard Run selection worked. Unsafe Result warning, diagnostic prose, identity metadata and corrected mock continuation disclosure inspected. |
| Task history | `/tasks/DEMO-102`, 1440×900 dark | Workflow/history, evidence and classification layout inspected; mock continuation/Journal prose corrected. |
| Overview | 1440×900 light | Original workspace river, labels, source pill and shell inspected. |
| Primary route smoke coverage | `/`, `/runs`, `/tasks`, `/agents`, `/approvals`, 1440×900 dark | Actual rendered DOM checks: each route had one expected h1, mock provenance and no page-wide horizontal overflow. These smoke checks are not a visual review of every record on every list. |

## Verified defects and implemented fixes

| ID | Reproduction / finding | Fix and verification |
| --- | --- | --- |
| UI-01 | Skip to content on the unsafe Run detail navigated to `/#main`, showing Overview and losing the current route. | Prevent default base-href navigation, focus/scroll the current main landmark and account for the sticky header. Final browser URL stayed `/application-v1-preview` with focus on `main`; regression protects route preservation. |
| UI-02 | Closed mobile navigation received Tab focus on the brand at x≈−290. Opening retained background focus; the aside claimed modal semantics without dialog behavior. | Closed drawer is inert; open drawer has dialog semantics and an explicit close button; background is inert. Initial focus, Tab/Shift+Tab containment, Escape/close/navigation restoration and breakpoint changes are handled. Final keyboard screenshot shows complete navigation and a visible focus ring. |
| UI-03 | Tablet footer was wider than its 72px rail: x≈−7.8, width≈86.4; long preview text spilled outside it. | Existing icon component plus labeled link; text hidden only in the compact rail and footer constrained. Final link bounds x≈21.1..49.8 stay inside the rail; accessible name is retained. |
| UI-04 | Global flex notice styling split the mobile synthetic boundary notice into cramped columns. | Preview-local block flow and paragraph spacing restore readable stacked disclosure. Existing design tokens are retained. |
| UI-05 | Browser accessibility tree exposed preview scheduler headings as generic cells; the overflow area was not a named keyboard stop and scenario changes lacked one concise persistent announcement. | Explicit column scopes, labeled focusable region and atomic status summary. DOM regressions verify semantics, state changes and no subject identifiers in the announcement. This is not a screen-reader speech certification. |
| UI-06 | DAG ArrowRight selected Architecture Plan while focus stayed on Understand Scope; ArrowRight on Zoom in changed graph selection. Plain table rows carried unsupported `aria-selected`. | Arrow traversal starts from the focused canvas node, moves focus and centers it; toolbar/list keys retain native behavior. Selection is exposed with `aria-pressed` on native list buttons. Final browser focus and selected node agree; list ArrowRight scrolls its local region. |
| UI-07 | Fit graph stopped at 50%: 24-node SVG width≈840px exceeded the ≈681px canvas and hid rightmost nodes. | Fit computes the required scale without that floor; zoom-out supports smaller views and zero-sized canvases are ignored. Final SVG width≈663px fits the same canvas at 39%. A narrow-canvas regression covers the former failure. |
| UI-08 | At mobile fit, overlaid zoom controls covered the graph's first-row nodes and labels. | Controls occupy their own row above the canvas. Final mobile controls end at y≈442 while the canvas starts at y≈454. All three hazardous-scenario nodes remain visible. |
| UI-09 | Mobile unsafe-node inspector widened the document to ≈586px at 390px and shifted it horizontally. | Shrinkable grid tracks/aside, bounded scenario selection and wrapped metadata. Final document scroll width≈378px at 390px; scrollX=0. Canvas pan remains local. |
| UI-10 | An originally empty graph told the user to fix filter criteria even with no filters. | Empty supplied graph and empty search results have separate messages and regressions. |
| UI-11 | Rendered workbench, Run and Task prose claimed Core had no scheduler/Journal/continuation semantics yet. | Static disclosure now says these are mock presentations with no operational Core connection and no established eligibility/canonical Journal ordering. State mapping, safety warnings, adapters' behavior and disabled actions are unchanged. |

The added `long-text` scenario is fabricated presentation stress coverage, not a
new runtime history. Exact whole-string replacements preserve all matching
references and pass the existing unchanged decoders. The initial fixture attempt
violated supplied ID ordering and was rejected as invalid; its Task ID suffix was
corrected before final checks. No decoder rule was relaxed. Long Run/Task/Grant
IDs and a long lexical resource remain exact in the rendered DOM and wrap with
CSS. Existing long diagnostic/safety prose was inspected on the unsafe Run.

## Accessibility and evidence findings

Keyboard checks covered skip navigation, drawer opening/containment/closing,
visible focus, breakpoint focus restoration, scenario selection, native details,
graph arrows, list selection and local horizontal table scrolling. In the mobile
list, ArrowRight moved local scrollLeft to ≈78.9px while document width stayed
within the viewport. The preview selector, table and operational controls retain
explicit accessible names. Run success remains separate from Task completion;
conflicting subjects/outcomes remain visible without choosing a winner.

Partial-empty and complete-empty Journal notices retain their different absence
claims. Denial clears prior subject metadata; stale evidence keeps its original
time. Approvals/routes/payload remain unavailable in the preview; continuation
remains unassessed. Decorative water animation controls do not perform Run resume.

No axe package was installed or downloaded. Checks used real rendered Chrome,
accessibility/DOM snapshots, keyboard actions and component regressions. No full
WCAG conformance, screen-reader speech, cross-browser or touch-device claim is
made. Fitted large graphs provide an overview; readable full labels remain
available through zoom, focus/inspector and the structured list.

## Validation receipts

Environment: Node `v24.20.0`, npm `11.19.0`, Vitest `5.0.4`; installed dependencies.
Each npm invocation set `NG_CLI_ANALYTICS=false`, `npm_config_offline=true` and
`npm_config_update_notifier=false`; logs are local under
`ui/control-center/.tmp/browser-qa-2026-10-19/`. Each command's actual
`$LASTEXITCODE` was printed and returned by its PowerShell wrapper.

| Final check | Exact command / scope | Result |
| --- | --- | --- |
| Types | `npm run typecheck` | Exit 0; application and spec targets pass. |
| Focused regressions | `npm run test:ci` with the nine exact `--include` arguments below | Exit 0; 9 files, 92 tests pass. |
| Full UI suite | `npm run test:ci` | Exit 0; 22 files, 353 tests pass; no failed or skipped tests. |
| Production build | `npm run build` | Exit 0; initial 365.84 kB, preview chunk 45.79 kB; no budget warnings. |
| Browser console | Captured warning/error entries after final source reload, from `2026-10-19T13:17:30Z` | No entries in the captured final window. |
| Whitespace | `git diff --check` and `git diff --cached --check` | Exit 0; Git emitted LF→CRLF working-copy advisories, not whitespace findings. New report checked separately without staging. |
| Scoped Markdownlint | Two changed reports with installed cached CLI | Exit 0; 2 files, zero issues. |
| Inherited Markdownlint comparison | Unchanged README and historical contract-question record | Exit 1; exactly nine MD032 and one MD040 findings, zero newly introduced findings. The prior accepted baseline exception is not a mechanical PASS. |

Focused command, from `ui/control-center`:

```powershell
npm run test:ci -- --include 'src/app/app.spec.ts' --include 'src/app/application-v1/synthetic-preview.spec.ts' --include 'src/app/shared/nile/dag-flow.spec.ts' --include 'src/app/shared/nile/scheduler-panel.spec.ts' --include 'src/app/features/flow/flow.spec.ts' --include 'src/app/features/screens.spec.ts' --include 'src/app/data/dag-adapter.spec.ts' --include 'src/app/shared/continuation-shell.spec.ts' --include 'src/app/shared/execution-timeline.spec.ts'
```

Final logs: `typecheck-final.log`, `focused-final-candidate.log`, `full-final.log`
and `build-final.log`; documentation receipts:
`markdown-changed-final.log`, `markdown-inherited-final.log`. Cached checker:
`markdownlint-cli2 0.23.3` / `markdownlint 0.41.1`, invoked from the worktree root:

```powershell
node 'C:\Users\Abdelrahman\AppData\Local\npm-cache\_npx\3158f213c58abe1a\node_modules\markdownlint-cli2\markdownlint-cli2-bin.mjs' 'ui/control-center/docs/application-v1-preparation.md' 'ui/control-center/docs/application-v1-browser-qa-2026-10-19.md'
node 'C:\Users\Abdelrahman\AppData\Local\npm-cache\_npx\3158f213c58abe1a\node_modules\markdownlint-cli2\markdownlint-cli2-bin.mjs' 'ui/control-center/README.md' 'ui/control-center/docs/core-contract-questions.md'
```

The two baseline documents are byte-unchanged relative to HEAD. Initial sandboxed
lookup could not read the existing cached checker; scoped permitted access enabled
the offline checks above. That failed lookup was not counted as a lint result.
No checker was installed or downloaded.

The new report was also checked using
`git diff --no-index --check -- /dev/null ui/control-center/docs/application-v1-browser-qa-2026-10-19.md`:
exit 1 denotes the new-file difference; it emitted no whitespace finding. No
staging was used for this check.

Earlier logs are intermediate evidence: initial focused
focus assertions failed because jsdom did not apply mobile media visibility;
tests now explicitly model visible mobile buttons and independently verify actual
browser behavior. A later focused run caught a remaining old disclaimer assertion;
it was updated before the final 92/353 passing runs. No failure was counted as PASS.

Development-only interruptions included an initial server-start connection
refusal, transient Angular HMR class/template mismatch during sequential edits,
and intermittent screenshot CDP timeouts. Reloading the completed candidate and
fresh capture resolved verification. Some intermediate screenshot captures include
transition/capture artifacts; only `final-*` images below identify the final
candidate. Viewport overrides were reset at the end.

Core tests/schema validators, operational acceptance, repository-wide lint and
real reader resource/integrity tests were not run for this UI-only task.

## Browser artifacts

Local artifacts are ignored and preserved, not proposed for staging. Browser
observations are in `observations.json`, `scenarios-mobile-light.json`,
`scenarios-desktop-final.json`, `primary-routes.json` and
`final-browser-logs.json` in the evidence directory above. Actual capture
dimensions/themes are recorded rather than inferred from filenames.

Final screenshots:

- `final-preview-desktop-dark.jpg`
- `final-preview-mobile-light.jpg`
- `final-flow-desktop-dark.jpg`
- `final-flow-tablet-light.jpg`
- `final-flow-mobile-light.jpg`
- `final-run-mobile-dark.jpg`
- `final-task-desktop-dark.jpg`
- `final-overview-desktop-light.jpg`

The settled keyboard drawer is also shown in
`after-mobile-drawer-keyboard.jpg`. Earlier `before-*` and `after-*` files are
intermediate or defect-reproduction receipts, not blanket final QA approvals.
Screenshots are direct browser captures; no generated illustration is used as
evidence.

## Exact proposed change inventory

All paths below are relative to `ui/control-center/`. Twenty-seven source/test
files and two documentation files; no generated artifact belongs in the commit.

```text
docs/application-v1-preparation.md
docs/application-v1-browser-qa-2026-10-19.md
src/app/app.css
src/app/app.html
src/app/app.spec.ts
src/app/app.ts
src/app/application-v1/fixtures.ts
src/app/application-v1/synthetic-preview.css
src/app/application-v1/synthetic-preview.html
src/app/application-v1/synthetic-preview.spec.ts
src/app/application-v1/synthetic-preview.ts
src/app/data/continuation-adapter.ts
src/app/data/dag-adapter.spec.ts
src/app/data/dag-adapter.ts
src/app/features/flow/flow.css
src/app/features/flow/flow.html
src/app/features/flow/flow.spec.ts
src/app/features/runs/run-detail.ts
src/app/features/screens.spec.ts
src/app/features/tasks/task-detail.ts
src/app/shared/continuation-shell.spec.ts
src/app/shared/continuation-shell.ts
src/app/shared/execution-timeline.spec.ts
src/app/shared/execution-timeline.ts
src/app/shared/nile/dag-flow.css
src/app/shared/nile/dag-flow.html
src/app/shared/nile/dag-flow.spec.ts
src/app/shared/nile/dag-flow.ts
src/app/shared/nile/scheduler-panel.spec.ts
```

## Independent review and Human handoff

| Independent Agent | Review scope | Verdict |
| --- | --- | --- |
| `/root/application_audit` | UI/UX/accessibility; complete final diff, regressions, scenario matrix, final browser screenshots and report | APPROVE; no material findings remain. |
| `/root/boundary_status` | Contract/governance and documentation consistency; complete final diff, approved boundary, mock isolation, final receipts and report | APPROVE; no material findings remain. |

Neither reviewer implemented these changes. The coordinator implemented the
fixes. Review raised a closed-toggle breakpoint focus issue, which was fixed and
covered, and requested replacement of intermediate screenshots, now supplied.
Both reviewers requested corroboration of the later keyboard-scroll measurement;
a fresh browser check saved `mobile-list-keyboard-scroll-final` in
`observations.json` (78.8889px), and both reviewers confirmed resolution.
Independent review: **PASS**. Documentation consistency: **PASS** within this
UI-only scope. These verdicts do not turn the inherited lint exit 1 into PASS.

The candidate is ready for Human acceptance review, with scoped checks and
independent reviews completed and the inherited lint exception explicitly retained.
Human final acceptance and separate commit approval remain required. All changes
are unstaged and uncommitted; no push, merge, PR, deployment or publication was
performed. The local development server remains available for Human inspection.
**STOP AT HUMAN CONTROL before committing.**
