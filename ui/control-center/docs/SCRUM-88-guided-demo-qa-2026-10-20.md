# SCRUM 88 Guided Developer Alpha QA October 20 2026

## Conditional checkpoint verification and console investigation

The October 20 Human decision, SCRUM-88 approval comment **10744**, conditionally
authorizes exactly one local commit with message
`fix(ui): replace blocking tour with non-modal guided explorer`, after the console
investigation and final candidate checks. Parent HEAD is
`2ad250b0ff365df700f6ef696987f8d6d6379a5e`, branch
`ui/control-center-integration-prep`. The earlier approval/prohibition statements
below record their historical handoffs; this decision supersedes the prohibition
only for that local checkpoint. No push, merge, PR, tag, deployment, release,
publication or Jira closure is authorized. Option D and S0 NO-GO remain binding.

### Exact errors, source and timing

The preserved `console-final.json` records the following identical message for
both original errors:

```text
Error: A listener indicated an asynchronous response by returning true, but the message channel closed before a response was received
```

| Event | UTC timestamp | Reported URL |
| --- | --- | --- |
| Original 1 | 2026-10-20T11:59:09.495Z | `http://localhost:4200/application-v1-preview` |
| Original 2 | 2026-10-20T12:06:09.838Z | `http://localhost:4200/flow?node=fo-plan` |
| Additional retained observation | 2026-10-20T12:31:20.809Z | `http://localhost:4200/flow?scenario=stale-data` |

The supported console API returns level, message, timestamp and URL. None of
these entries includes a script filename, line, extension ID or stack. The URLs
are page-context observations, not proof that an application script originated
the rejection. The original call sites cannot be reconstructed from this receipt.
The additional observation preceded the isolated replay; its trigger is unknown.

Read-only access to `chrome://extensions/` was blocked by the browser URL policy.
No alternate browser surface, raw debugger connection, extension setting change
or workaround was attempted. The diagnostic limit is preserved in
`console-investigation-retained.json`; no unavailable stack has been invented.

### Grounded classification

Chromium's own [extension-message port source change](https://chromium.googlesource.com/chromium/src/+/988c43b97b00934e8df90c9949681e73434e70bb%5E!/)
defines this exact message as `kClosedWhileResponsePendingError` and selects it
when an extension channel closes with an asynchronous reply pending. Its current
[SendMessageDisconnect browser test](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/chrome/browser/extensions/api/messaging/messaging_apitest.cc)
asserts the same error after an extension listener returns true and closes before
responding. [Chrome's messaging contract](https://developer.chrome.com/docs/extensions/develop/concepts/messaging#responses)
explains the corresponding asynchronous response channel.

Both original entries are therefore classified as **Chromium extension-message
channel disconnects**, with the responsible extension/tool and original call path
unresolved. Attribution to the external browser/extension environment is a
grounded inference, not identification of a particular extension or proof that
the automation extension caused them. The source/production-asset audit found no
application use of extension messaging APIs or this error string. The unchanged
Angular global-error listener can relay an external rejection; it does not prove
where that rejection began. No new Guide producer or material UX/safety failure
was identified. Prior October 19 and original October 20 browser receipts were
empty; they do not establish that this error pre-existed in the application.

### Reproducibility and conditional decision

`console-reproduction.json` contains **45 timestamped observations**, from
12:33:13.919Z to 12:34:33.119Z, in a fresh isolated Chrome tab. All captured console
arrays are empty. Coverage includes unopened guide on preview and Flow; Open,
Previous/Next, direct selection of all five explanations, every Locate target,
cross-route Locate, Minimize, expansion, Exit, re-entry, all 18 scenarios, closed
guide navigation/full reload, and a static favicon document/reload with no ITRU
scripts. The original error did not reproduce in either application or static
controls. This is bounded negative evidence, not proof of a universally clean
console or a reproduced external culprit. Locator ambiguity during replay was a
tool selection error, resolved by the unique top-bar accessible label; it was
not an application console exception.

Independent classification review confirms adequate investigation for the Human's
conditional checkpoint: no material new regression, unsafe behavior or plausible
application-source producer was found. Specific external sender identity remains
uncertain. The UX/accessibility and contract/governance approvals remain applicable;
final editorial and staged checks are recorded in the local checkpoint receipts.
No product behavior or error handling was changed to hide the messages.

All 15 implementation/test files retain the reviewed hashes. Only these two
already-approved documentation paths are updated with investigation/authorization
evidence. The 220 focused tests, 365 full tests, typecheck, production build and
scoped formatting receipts remain applicable. Document lint and final scope,
hash, whitespace, sensitive-data and governance checks are rerun for this
checkpoint. `checkpoint-candidate-receipt.json` records the final candidate;
`checkpoint-post-commit.json` records the actual commit result, parent, exact
17 paths and clean tracked/index state after a successful commit. The original
`handoff-receipt.json`, browser evidence and independent reviews remain preserved.

The ten inherited Markdownlint findings remain exit 1, unresolved and unwaived.
Incomplete screenshots, physical input/device, screen-reader speech, full WCAG
and cross-browser limits remain exactly as reported below. SCRUM-88 stays open;
Human product acceptance/closure remains on hold. Stop at Human Control after
the single verified local commit.

## Guided Explorer investigation before implementation

The Human-authorized non-modal redesign starts from clean checkpoint
`2ad250b0ff365df700f6ef696987f8d6d6379a5e` on
`ui/control-center-integration-prep`. The checkpoint and its original evidence
below are preserved. SCRUM-88 closure remains on hold; no new commit is authorized.

Before code changes, source inspection and actual Chrome reproduction verified
that every numbered/Previous/Next action invokes `GuidedJourney.go()`, which
unconditionally focuses `#guided-step-title` and calls
`scrollIntoView({block: 'start'})`. A Previous action moved the document from
approximately 154px to 628px and transferred focus to the heading. Explanatory
navigation therefore takes control of the application's scroll and focus.
The guide is also mounted inside the routed preview: opening `/flow` destroys
it, and there is no Minimize or Exit control or independently scrollable guide.

A literal global overflow lock was not reproduced in this checkout. Computed
body and document overflow were `visible`, the document was the scroll element,
and no modal, inert background or pointer-intercepting layer was present during
desktop guide use. The guide's `overflow: hidden` clips its own rounded card;
its measured scroll height equaled its client height, with scrollTop zero.
There are no guide wheel/touch handlers or focus-trap handlers. The existing
mobile navigation drawer alone uses a scrim, modal semantics, background inertness
and a Tab loop. Keyboard entry into the demo closed that drawer and removed its
modal/scrim state correctly. The reported website-wide scroll lock therefore
remains unconfirmed; it must not be attributed to a speculative global CSS rule.

Browser input attempts did not reliably produce default wheel/PageDown movement
in the baseline automation session. Those no-change attempts are retained as
observations, not evidence that physical input works or proof of an application
event cancellation. Before-state receipts are in the separate ignored directory
`ui/control-center/.tmp/scrum-88-explorer-2026-10-20/`. The verified forced-focus/
scroll mechanism and route-local guide lifetime will be removed by the redesign;
post-change scrolling is reported separately below.

## Current non-modal Guided Explorer candidate

The guide now lives once in the application shell, outside the routed evidence
page. A root-provided, in-memory presentation service shares the same unchanged
synthetic fixture session with that page. It retains the selected explanation and
scenario across routes, minimize and exit/re-entry. Reload closes and resets the guide.
There is no persistence, operational data source or backend transport.

Desktop reserves a 360px side column; minimizing reduces it to 76px. The sticky
panel has an independently scrollable named region. At widths up to 900px it is
a non-modal bottom panel, bounded to 52dvh/460px, with matching page bottom space.
Its 64px minimized bar also has matching reserve. Safe-area and editable visual
viewport occlusion are accounted for. Application text editing minimizes the
mobile guide without stealing input focus; pinch zoom without editing is not
mistaken for keyboard opening. Viewport listeners are removed on shell teardown.

Previous/Next/direct selection update explanation state only. They do not call
focus, scroll or router APIs. Only explicit Open/Expand focuses the guide, using
preventScroll; Minimize and Exit restore a surviving control. Locate Section is
the separate explicit action that navigates to the existing synthetic evidence
workspace and scrolls/focuses the appropriate section. It opens Contract details
when applicable and announces an honest observation-status fallback for unavailable
details. Locate uses instant scrolling; there are no guide motion transitions.
There is no guide backdrop, dialog, focus trap, global overflow mutation, inert
background, wheel/touch cancellation or gesture restriction. The existing mobile
primary-navigation dialog remains independent and closes correctly on navigation.

The five explanations preserve the checkpoint's Run/Result/Journal/approval
semantics. All 18 fixtures, contracts, decoders, validators and presentation
semantics remain unchanged, as does the mock provider binding. Page origin and
approval counts stay route-specific; the guide's subject remains explicitly
synthetic on separate mock pages. Option D and S0 NO-GO remain binding. No Core,
parked SCRUM-81 code, credentials, live providers or operational controls changed.

### Verified defects and corrections

| Finding | Before and after |
| --- | --- |
| Explanation navigation took control | Old go() forced heading focus/scroll; new go() changes explanation only. Direct visible-button Chrome activation keeps document y 0→0 on desktop and mobile. |
| Route-local, undismissable guide | Old guide was destroyed on /flow; new shell guide persists with direct selection, Previous, Next, Locate, Minimize and Exit. |
| Re-entry selectors disagreed with retained model during development | A remounted native select applied value before its options existed, showing the first option while Result/conflict/two summaries remained correctly retained. Explicit option.selected bindings now keep native selectors, model and content consistent in both guide and preview. A new DOM-value regression first failed (expected 3/received 0), then passed with the fix. |

The native-selector defect was caught in actual browser review, not explained
away as a reload. Before/after receipts are preserved as
`selector-regression-before-fix.log`, `selector-regression-after-fix.log`,
`reentry-isolated.json` (intermediate mismatch) and `reentry-final.json` (resolved).
The earlier `mobile-lifecycle-locate.json` re-entry native values are likewise
intermediate, not a retention PASS.

### Current validation receipts

All current receipts are in
`ui/control-center/.tmp/scrum-88-explorer-2026-10-20/`. Earlier checkpoint receipts
in `scrum-88-2026-10-20/` remain preserved. Installed dependencies only, with the
same offline npm/analytics settings as the checkpoint.

Markdownlint runs from the repository root using its unchanged
`.markdownlint.json` (MD013 disabled, MD024 limited to siblings). A final attempt
from the UI directory omitted that root configuration and reported default
line-length findings; both unconfigured-attempt logs are preserved separately.
The configured final runs below supersede those attempts without changing or
waiving the existing lint policy.

| Check | Final result |
| --- | --- |
| Focused guide/shell/preview/session/decoder tests | Exit 0; 5 files, 220 tests passed (`focused-final.log`). |
| Complete UI suite | Exit 0; 23 files, 365 tests passed, none failed/skipped (`full-final.log`). |
| Application and spec typecheck | Exit 0 (`typecheck-final.log`). |
| Production build | Exit 0; initial 419.38 kB, preview 17.78 kB; no budget warnings (`build-final.log`). Guide code is now shell-shared. |
| Scoped formatting | Exit 0; installed Prettier, 5 Explorer implementation/test files (`formatting-final.log`); independently confirmed. |
| Two changed documents | Exit 0; Markdownlint, zero findings (`markdown-new-final.log`); independently confirmed. |
| Inherited Markdownlint | Exit 1; nine MD032 and one MD040 remain unresolved in the unchanged README and core-contract-questions; not PASS or waived (`markdown-inherited-final.log`); independently confirmed. |
| Whitespace and boundary inventory | Exit 0; tracked/index whitespace checks and new-file whitespace inspection. Exactly 17 proposed UI paths, empty index; contract/fixture/provider/Core/history boundaries unchanged (`handoff-receipt.json`). |

The 12 Explorer regressions cover explanation-only navigation, no guide event
cancellation or global style mutation before/during/after, independent named
scroll region, re-entry DOM values, cross-route subject/state retention, direct
Locate and missing-target fallbacks, all 18 shared choices, denial clearing,
independent Result summaries, bounded Journal coverage, long copy, mobile editing,
editable visual-viewport handling/zoom distinction and listener teardown. Original
observation/disabled-action regressions remain. Native selector, focus and event
assertions are behavior tests; synthetic uncancelled wheel/touch/key events do
not certify physical scrolling. No new dependency, Core test or repository-wide
lint run was required for this UI-only change.

### Current browser evidence

Chrome inspection used the existing localhost server. Actual CSS dimensions are
recorded after 90%-zoom viewport overrides, not inferred from screenshot sizes.
The first tab's debugger detached during QA; a fresh local-only tab recovered
inspection. The final candidate was rechecked after the selector correction.

| Surface and viewport | Evidence and outcome |
| --- | --- |
| Desktop 2133×950 dark | `candidate-desktop-dark.jpg`: side panel reserves space, labels its independent synthetic subject and has its own scrollbar. Native accessibility-targeted guide scroll 0→253px while document stayed ≈32px (`candidate-input-attempts.json`). |
| Desktop 1440×900 dark | Main right ≈1045px, guide left ≈1057px, a 12px gap, no horizontal overflow. Direct Next changes Approval preview→Run with document y 0→0 and focus on Next (`direct-next-desktop.json`). |
| Mobile 390×844 dark | `final-mobile-dark-expanded.jpg`: bottom panel, visible Minimize/Exit/Previous/Next/Locate and topbar controls. Guide height ≈439px, matching bottom reserve ≈463px. All 18 scenario states/records/summaries preserved, all four operational actions disabled, document 378px≤390px (`mobile-dark-scenarios-final.json`). Direct Next keeps y 0→0. |
| Mobile 320×480 light | `mobile-small-light-layout.json`: panel 222..472px, 132px independently scrollable body, 273.6px bottom reserve; header/footer/topbar controls stay inside viewport. Screenshot capture timed out; this check is rendered DOM/layout evidence. |
| Mobile 320×800 light, long metadata | `mobile-long-light-final.json`: all five explanations keep document 308px≤320px; guide body 298px with longer content scrolling within it. |
| Tablet 1024×767 light | `tablet-light-final.json`: main right ≈629px, guide left ≈641px, side panel 360px and 12px gap, no horizontal overflow. Screenshot capture timed out. |
| Dismiss/re-entry | `reentry-final.json`: native step 3/scenario conflict, heading Result and two summaries identical before and after. Exit leaves body/html overflow visible and focuses opener. Minimized bar 64px plus 88px reserve. |
| Free route navigation and editing | `mobile-route-editing-final.json`: Journal/long-text retained on /flow with Mock data origin, no modal/inert content; filter editing retains input focus and minimizes guide. |
| Separate Locate | `dag-and-cross-route-locate-final.json`: from /flow, explicit Locate returns to synthetic Journal, retaining long-text/step 4 and focusing journal-evidence. Same-route Locate opens Contract details; missing-target behavior is covered by focused regressions. |
| Nested DAG interaction | `dag-keyboard-final.json`: Fit graph and ArrowRight move focus and selection together from fo-understand to fo-plan on the existing 10-node mock graph, with Journal/long-text guide retained and no horizontal overflow. |
| Restored desktop 2133×1012 dark | `final-desktop-dark-explorer.jpg`: final candidate with viewport override reset, original dark theme restored, document width 2122px and body overflow visible. |

`desktop-navigation-final.json` records an intermediate locator-click page move
from 0→407px. The automation centers sticky-footer controls before locator input;
this was separated from application behavior using direct visible coordinates
(`direct-next-desktop.json` and the mobile direct-click receipt), which keep page
position unchanged. The intermediate move is not reported as an explanation-only
PASS. Locate explicitly moves and focuses the target above the mobile panel
(Journal target ≈80px, panel starts ≈397px).

`console-final.json` preserves two generic asynchronous-listener/message-channel
errors observed during the browser session. They provide no application stack or
reliable source attribution; no corresponding application failure was observed.
This is not a zero-console-error certification.

Coordinate wheel/PageDown attempts in the baseline were not reliable proof of
native document input, and a document-scrollbar drag was rejected as outside the
tab content surface. The report therefore makes no blanket physical wheel/touch
device claim. Actual guide scrolling, document movement via explicit Locate,
native focus/graph keyboard behavior, no event cancellation and unchanged global
overflow are separately evidenced. Real touch/OS-keyboard, screen-reader speech,
full WCAG and cross-browser certification remain unperformed. The original global
scroll-lock report is not falsely claimed reproduced; the verified forced-focus/
scroll defect and restrictive guide lifetime are removed.

### Exact redesign files and review state

All 17 proposed paths are relative to `ui/control-center/`; ignored QA artifacts
remain outside the proposed change:

```text
docs/SCRUM-88-local-demo-guide.md
docs/SCRUM-88-guided-demo-qa-2026-10-20.md
src/app/app.css
src/app/app.html
src/app/app.routes.ts
src/app/app.spec.ts
src/app/app.ts
src/app/application-v1/guided-explorer-state.ts
src/app/application-v1/guided-explorer.spec.ts
src/app/application-v1/guided-journey.css
src/app/application-v1/guided-journey.html
src/app/application-v1/guided-journey.ts
src/app/application-v1/synthetic-preview.css
src/app/application-v1/synthetic-preview.html
src/app/application-v1/synthetic-preview.spec.ts
src/app/application-v1/synthetic-preview.ts
src/app/features/overview/overview.ts
```

| Independent review | Verdict and scope |
| --- | --- |
| UX and accessibility (`/root/ux_review`) | APPROVE; no material findings. Reviewed source, focused behavior coverage, desktop/mobile evidence, all 18 scenarios, direct Next without page movement, nested scrolling, DAG keyboard navigation and resolved selector re-entry. Physical device, speech, WCAG and cross-browser limits remain explicit. |
| Contract, governance and documentation (`/root/contract_review`) | APPROVE; no material findings across all 17 paths. Confirmed unchanged contracts/fixtures/provider/Core boundaries, final tests/build/typecheck, independent formatting/docs checks, exact ten inherited lint findings, unchanged HEAD and empty index. |

Both reviewers remained read-only and approved final editorial receipt updates.
No source changed after the final test run and reviewed candidate. The ignored
`independent-reviews-final.md` preserves both verdicts; `handoff-receipt.json`
records the final path inventory, SHA-256 file hashes and mechanical checks.

The scoped implementation is ready for Human UX acceptance and a separate commit
decision. This is not an all-green repository lint or device/accessibility
certification: the ten inherited findings and reported browser/input limits
remain unresolved. HEAD stays `2ad250b0ff365df700f6ef696987f8d6d6379a5e`; changes
remain unstaged and uncommitted. SCRUM-88 closure stays on hold for Human UX acceptance.
No staging, commit, push, merge, PR, deployment, release or publication is
authorized by this redesign handoff. **STOP AT HUMAN CONTROL before committing.**

## Preserved checkpoint implementation and review

The remaining sections record the accepted five-stop checkpoint before the
non-modal redesign; their unstaged/approval statements describe that handoff.

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
