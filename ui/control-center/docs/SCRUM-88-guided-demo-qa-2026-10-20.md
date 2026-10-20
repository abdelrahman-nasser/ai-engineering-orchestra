# SCRUM 88 Guided Developer Alpha QA October 20 2026

## Scope and preflight

Human-authorized implementation and testing for
[SCRUM-88](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-88).
Recovered the Jira description and acceptance criteria through the read-only
connector. They match the current Human instruction. The old workspace path in
Jira and prior reports is historical; active work is in
`D:/Dev/ITRU/worktrees/itru-ui-integration`.

Starting branch: `ui/control-center-integration-prep`; clean index and worktree.
Starting and retained HEAD: `23e2f6ea06906d314ed782c172b6246f994c6748`.
Read the Project Manifest, Core principles/terminology/precedence, standard-change
Workflow, software-engineer/reviewer Roles and independent-review/documentation
consistency gates. `.ai/rules/` is absent. Current Human instruction and Jira supply
Task scope; historical `.ai/tasks` records are unchanged.

Application v1 preparation and October 19 browser QA were recovered and preserved.
This change adds first-time developer guidance rather than repeating their
implementation or a broad audit of unrelated screens. The current static Core
Run/Result specifications were consulted read-only for explanation accuracy.

## Implemented behavior

Overview and the sidebar now expose **Guided developer demo**, using the existing
`/application-v1-preview` route. An ordered five-stop guide sits above the existing
evidence panels: Task → Approval preview → Run → Result → Journal. It consumes the
same `PreviewSession`, preserving the existing scenario selector, detailed panels,
disclosure and operational-control boundary.

Task copy is explicitly illustrative; selected subjects come only from the current
inspection. Approval preview explains the exact subject without requesting or
granting authority. Run displays the supplied state and a separate seven-state
educational glossary. Result displays current-page recorded summaries separately
from lifecycle acceptance and preserves conflicting subjects. Journal retains
bounded partial/complete-empty claims, stale times and independent discrepancies.
Denied/not-found/loading states display no prior subject metadata. Scenario changes
retain the current stop; reload resets local guide state.

Native navigation controls expose one `aria-current="step"`, focus the selected
heading, and scroll it below the sticky header. Named evidence links focus existing
panels without base-href route loss. Layout uses existing design tokens in both
themes; long exact metadata wraps. The existing DAG/Nile workbench is linked with
explicit separate-model disclosure, without importing its adapters into this
preview or mapping Journal records to Workflow Stages.

Option D remains active: no operational Core connection, reader, transport, live
provider, credentials or execution/approval/cancellation/resume handler. Execute,
Approve, Cancel and Resume remain disabled. Contracts, validators, decoders,
presentation semantics, all 18 fixtures and the mock provider binding are unchanged.
No Core file, parked SCRUM-81 content or historical report was modified.

The [local demo guide](SCRUM-88-local-demo-guide.md) records exact start commands,
five-stop demonstration, all scenarios, keyboard use and safe local evidence capture.

## Validation receipts

Installed dependencies only; Node `v24.20.0`, npm `11.19.0`, Vitest `5.0.4`.
Npm commands set `NG_CLI_ANALYTICS=false`, `npm_config_offline=true` and
`npm_config_update_notifier=false`. Logs and browser observations are under
`ui/control-center/.tmp/scrum-88-2026-10-20/` and are ignored local evidence.

| Check | Command or scope | Result |
| --- | --- | --- |
| Focused UI/contract regressions | `npm run test:ci -- --include src/app/application-v1/synthetic-preview.spec.ts --include src/app/app.spec.ts --include src/app/application-v1/presentation.spec.ts --include src/app/application-v1/decode.spec.ts` | Exit 0; 4 files, 215 tests passed. |
| Full UI suite | `npm run test:ci` | Exit 0; 22 files, 360 tests passed; no failed/skipped tests. |
| Typecheck | `npm run typecheck` | Exit 0; application and spec targets pass. |
| Production build | `npm run build` | Exit 0; initial 365.86 kB, synthetic preview 66.56 kB; no budget warnings. |
| New component formatting | Installed Prettier, three new component files | Exit 0; all three match Prettier formatting. |
| Changed-document Markdownlint | Two SCRUM-88 reports only | Exit 0; zero findings. |
| Inherited Markdownlint | Unchanged README and core-contract-questions | Exit 1; nine MD032 and one MD040 findings remain unresolved. This is not PASS or waived. |
| Whitespace and boundary inventory | `git diff --check`, `git diff --cached --check`, new-file whitespace check, index/HEAD and changed paths | Exit 0; all 14 proposed files confined to the UI. Index empty; HEAD unchanged. |
| Browser console | Captured warning/error entries after final walkthrough | Empty captured list; `final-browser-receipt.json`. |

The seven added tests exercise five-stop navigation/focus, overview discovery,
route-preserving evidence navigation, exact nonauthorizing approval subject,
all-18 scenario prompts, denial clearing at each stop, seven-state explanations,
independent/conflicting/missing Result summaries, stale times, invalid data and
bounded Journal coverage. The original all-18 disabled-controls regression remains,
now scoped to the Operational controls section so guide navigation can be enabled.

The initial focused run reported 37 passing tests but one unhandled jsdom
`scrollIntoView` error and exited 1. The method is now optional, matching the existing
shell's approach; the later successful receipt supersedes that failed run. The
initial sandboxed production build crashed with exit `-1073741819`; the permitted
outside-sandbox rerun succeeded. Neither failed attempt was counted as PASS.
Server startup initially failed with a Vite cache EPERM; prebundling was disabled
and permitted local-only execution outside the sandbox supplied the working server.

Final focus behavior deliberately scrolls the heading to the top of the content
area, rather than leaving it near the bottom after a step change. Final tests,
typecheck and production build include that refinement. Final logs are
`focused-final.log` (215 tests), `full-final.log` (360 tests),
`typecheck-final.log` and `build-final.log`. Scoped Markdownlint uses the existing
cached `markdownlint-cli2` 0.23.3 / `markdownlint` 0.41.1; no checker was installed.
Initial sandboxed formatting writes returned EPERM; permitted formatting then
completed and the scoped check passed.

There is no configured JavaScript/TypeScript/template lint script or Angular lint
target in this project. Scoped formatting, typecheck, Angular compilation and
Markdownlint are the applicable configured checks. Core tests/schema validators,
repository-wide lint, real operational acceptance, new dependency installation,
cross-browser and screen-reader speech certification were not performed for this
UI-only Task.

## Browser coverage and artifacts

Actual Chrome automation used the localhost Angular server. Existing Chrome zoom
was 90%; actual CSS dimensions were read back after integer viewport overrides.
Keyboard and DOM measurements are recorded as observations, not inferred from
screenshot dimensions. Temporary viewport overrides are reset after QA.

| Coverage | Evidence and observation |
| --- | --- |
| Desktop light and dark | 1867×1057 native viewport, plus 1440×900 dark layout measurements. Five-stop guidance, source disclosure, selected subject and focus inspected in rendered Chrome; `desktop-light-task.jpg` and `final-desktop-dark-approval.jpg` saved locally. |
| Tablet 1024×768 light and dark | Five navigation controls remain readable, the guide body stacks, the rail is retained and document width stays within viewport. `tablet-light-full.jpg` records a full-page capture; `tablet-dark-result.json` records dark layout. |
| Mobile 390×844 light, all 18 scenarios | `scenarios-mobile-light.json` records exact observation states, records, disabled actions and document width. Every entry has width 390 with no page-wide overflow. |
| Narrow mobile 320×800 dark | `narrow-dark-long-approval.json` records exact long subjects/resource. `final-long-mobile-dark.json` verifies all five long-content stops, heading top ≈80px and no overflow. Earlier Enter checks are in `keyboard-mobile-dark-steps.json`. |
| Mobile keyboard | Step activation, Next, native lifecycle disclosure, Tab to evidence link and visible focus checked. `final-mobile-focus.json` records all five headings at ≈80px below the ≈64px sticky bar with focus, one current-step control and no overflow; both evidence links retain route and receive focus. |
| Existing evidence reuse | Lifecycle and Journal evidence destinations retain the current route and receive focus; separate `/flow` destination remains explicitly mock. |
| Overview discovery | Actual Overview link opens the existing preview at default Task/scenario; `final-browser-receipt.json`. |

Mobile scenario matrix: interrupted-success ready/ready with 2 records;
partial-empty ready/partial with 0; success-task-active and over-capacity ready/ready
with 2; complete-empty ready/complete-empty with 0; entry-only ready/ready with 1;
conflict ready/ready with 4; incomplete ready/ready with 2; unavailable
ready/unavailable with 0; stale ready/stale with 2; denied denied/denied with 0;
incompatible, invalid, expired and exhausted retain lifecycle ready with their
distinct Journal states and 0 records; not-found has not-found/unavailable with 0;
loading has loading/loading with 0; long-text ready/ready with 2. All four
operational controls stayed disabled throughout.

Viewport screenshot capture repeatedly timed out at the browser CDP boundary.
Desktop captures after resetting the override and a tablet full-page capture
succeeded. Mobile visual screenshots could not be obtained in those attempts;
mobile claims are limited to real rendered DOM/layout, keyboard and accessibility
semantics observations, not a complete mobile pixel review. No screenshots were
generated or edited to fill this gap. No axe package was installed and no full
WCAG, assistive-technology, real touch-device or cross-browser claim is made.
The selected fixtures still show interrupted/succeeded Run lifecycles;
effect-ambiguous also appears as a conflicting recorded Result outcome. Other
lifecycle states are covered by educational reference and deterministic tests,
not seven selected-lifecycle browser scenarios or simulated transitions.

## Exact proposed changed files

Paths are relative to `ui/control-center/`. Generated build/cache artifacts,
screenshots and logs remain ignored local evidence, outside the proposed change.

```text
docs/SCRUM-88-local-demo-guide.md
docs/SCRUM-88-guided-demo-qa-2026-10-20.md
src/app/app.html
src/app/app.routes.ts
src/app/app.spec.ts
src/app/application-v1/guided-journey.css
src/app/application-v1/guided-journey.html
src/app/application-v1/guided-journey.ts
src/app/application-v1/synthetic-preview.css
src/app/application-v1/synthetic-preview.html
src/app/application-v1/synthetic-preview.spec.ts
src/app/application-v1/synthetic-preview.ts
src/app/features/overview/overview.css
src/app/features/overview/overview.ts
```

## Independent review and Human Control

| Independent reviewer | Scope | Verdict |
| --- | --- | --- |
| `/root/ux_review` | Actual source/tests, both documents, desktop/tablet images, all 18 mobile scenarios, long content and final focus receipts | APPROVE; no material UX/accessibility findings. Explicit mobile pixel/screen-reader/cross-browser limits retained. |
| `/root/contract_review` | All 14 files, unchanged contract/fixture/data-source/history guards, final receipts, both docs, desktop image and browser JSON; independent Markdownlint rerun | APPROVE; no material contract, governance or documentation findings. |

Neither reviewer implemented changes. Independent review: **PASS**.
Documentation consistency: **PASS** within this UI-only scope. Neither verdict
turns the inherited Markdownlint exit 1 into PASS or certifies the unperformed
mobile pixel/screen-reader/cross-browser checks.

Commit-readiness assessment: ready for Human acceptance and commit review with
the ten inherited lint findings and mobile screenshot limitation explicitly
retained. No implementation blocker remains within the authorized synthetic scope;
this is not unconditional acceptance or authorization to commit.

The candidate is unstaged and uncommitted. Human acceptance and separate explicit
commit approval remain required. The inherited lint exit 1 remains unresolved;
no Task closure, commit, push, merge, cherry-pick, PR, tag, release, deployment or
publication is authorized by this handoff. **STOP AT HUMAN CONTROL before committing.**
