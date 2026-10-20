# SCRUM-89 Task-to-evidence integrity implementation and QA

## Authority, baseline and canonical mapping

Canonical Task: [ITRU-066](../../../.ai/tasks/ITRU-066-scrum-89-evidence-integrity/task.yaml).
Jira: [SCRUM-89](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-89).
Requirements: accepted [SCRUM-82 audit comment 10755](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-82?focusedCommentId=10755)
and the Human-approved SCRUM-89 acceptance criteria. This is new work, separate
from completed SCRUM-82, SCRUM-84 and SCRUM-88.

Active worktree: `D:/Dev/ITRU/worktrees/itru-ui-integration`.
Branch: `ui/control-center-integration-prep`; starting clean HEAD:
`f301d3785914ec6ff7cfd7d93103e5297815f74d`. No branch mandate was found.
The Human resolved the initially missing canonical mapping by explicitly
supplying `ITRU-066` and `.ai/tasks/ITRU-066-scrum-89-evidence-integrity/`.
Before creation, hidden/ignored project-content and filename searches, local refs
and relevant all-ref documentation history found no ID allocation/reservation or
other Task reference. Dependency/build/cache and Git-internal files were excluded
from text search. No unseen remote allocation registry is claimed checked.

All four Task files were created from the prescribed templates, with schema,
exact ID/directory, completed namespace cutover, Workflow, gate and status checks
before UI implementation resumed. The general Task validator has a static
inventory; its baseline results alone would not validate this new Task. Explicit
new-file validation and an independent validation were performed instead. Status
remains `in_progress`; final Human acceptance is pending.

## Verified root causes and resulting behavior

| Finding | Before evidence and cause | Implemented correction |
| --- | --- | --- |
| Cross-Task identity | Chrome: DEMO-102 → `run_a41c07e2` → dependency DEMO-101 left the old Run inspector under the new Task. Local selection was accepted without current-Task membership checks. | Parameter changes reset selection; Task reads carry requested identity; Run summaries must match both supplied Task Run references and exact Run contract Task ID. Selected detail must match requested Run and current Task. Loading, missing, failed and defined-but-mismatching reads withhold unrelated evidence. |
| Event attribution | `run_3c81f0a7`, `Stage "implement" entered`: event inspector had zero evidence while adjacent panel labeled three Run-wide items as filtered event evidence. `hasEvidence` fallback returned the Run collection. | Any selected event uses only its supplied evidence array. Empty events show an explicit empty state. Run-wide evidence is separately labeled and explicitly selectable. Its persistent scope button retains focus when deselection removes the event inspector. |
| Route context | Flow applied only truthy query inputs, retaining selection after query removal. Task filter was component-local and reset on return. | URL owns Flow scenario/node and Task `taskFilter`. Absence, invalid subjects, direct navigation and Back/Forward reconcile state. Toolbar filters remain local to the active Flow instance. Task-local Run selection resets to a valid default on a new Task visit; it is not silently carried across subjects. |
| Keyboard semantics | Partial Task tree semantics and timeline `aria-selected` did not implement their declared widget patterns. Inspector Close removed the focused control; native-disabled guide endpoints could leave focus on BODY. | Task history is a native list with Run-selection buttons and separate Detail links. Timeline uses native pressed buttons. Explicit inspector Close restores a surviving trigger with `preventScroll`, with meaningful scoped fallbacks. Guide endpoints use guarded, focusable `aria-disabled` buttons. |
| Available width | Audit: 1280px with guide/inspector left approximately 176.9px DAG canvas. During this work Chrome also found Task columns approximately 196.9px/360px, with a selected timeline available width 114.7px but two 320px tracks. | Flow, Task/Run detail and timeline use local container queries. At 1280px with guide, Flow stacks at approximately 572.9px; Task timeline stacks at 490.7px and dedicated Run timeline at 522.7px. No global overflow override was added. |
| Context composition | Scope, actor assignments, approvals and review evidence required manual reconciliation across surfaces. | A compact read-only Task context uses existing rich mock models: included/excluded scope counts, exact Task assignment observations, matching Runs, Task-scoped approval records and selected-Run review references. Human acceptance is explicitly unavailable; successful Runs, approval records and review notes establish neither Task acceptance nor operational permission. |

Flow stacks below 760px of available workspace. Task/Run detail stack below
1000px; selected timeline tracks stack below 680px. These are local layout
choices. The proposed 320 CSS px graph target is a usability starting point,
not a contract: at a 320px viewport, available graph width is approximately
276.9px after surrounding padding; it remains locally navigable without widening
the document. The existing list fallback remains available.

## Repeatable local inspection

Use installed dependencies only, from `ui/control-center`:

```powershell
$env:NG_CLI_ANALYTICS = 'false'
$env:npm_config_offline = 'true'
$env:npm_config_update_notifier = 'false'
npm start -- --host 127.0.0.1 --port 4200 --prebundle=false
```

1. Open `/tasks/DEMO-102`, inspect Task context, then select `run_a41c07e2`.
   Follow dependency DEMO-101. Its inspector must show `run_3c81f0a7` and DEMO-101
   context. Back/Forward must never attribute another Task's Run to it.
2. Open `/runs/run_3c81f0a7`; select `Stage "implement" entered`. The event has
   no supplied evidence. Choose **Show Run-wide evidence** to inspect the three
   separate records. Focus remains on that scope control.
3. On Tasks choose **Blocked**, open DEMO-103, then Back. The URL
   `/tasks?taskFilter=blocked`, pressed filter and one matching row are restored.
4. On `/flow`, select Understand Scope. Back removes `?node=fo-understand` and
   the inspector; Forward restores both. Unknown node/scenario queries must not
   leave stale content. Close returns focus to the surviving node, or a scoped
   search fallback if that node is no longer rendered/visible.
5. Open the guide and inspector together at approximately 1280×900. Inspect
   stacked graph/details; repeat with a selected timeline on Task and Run detail.
   Minimize, expand, Exit and re-enter the guide while navigating normally.
6. With keyboard focus on Next, advance Result → Journal; focus stays on Next.
   At the endpoint, activation is a no-op. Repeat Approval preview → Task with
   Previous. These actions change explanation only. **Locate Section** explicitly
   navigates/focuses the corresponding synthetic evidence section.

## Verification receipts

Local ignored receipts: `ui/control-center/.tmp/scrum-89-2026-10-20/`.
Previous QA artifacts and historical documents are preserved.

| Check | Final evidence / result |
| --- | --- |
| Canonical Task | Explicit Python 3.12 JSON Schema, four files, exact ID/directory, status, Workflow and required-gate checks PASS; independent scoped validation PASS. |
| Focused regressions | 82 tests / 7 files PASS, `focused-final.log`, final run 14:40 UTC. Task identity/read failures, missing observations, route history, event scoping, native selection, scope-button focus, inspector fallbacks and guide endpoints covered. |
| Complete UI suite | 391 tests / 25 files PASS, `full-ui-final.log`, 14:39 UTC. Includes unchanged Application v1 scenario/decoder tests. |
| Typecheck | Application and spec TypeScript checks PASS, `typecheck-final.log`. |
| Production build | PASS, `build-final.log`, 14:39 UTC; installed dependencies, local output only. Synthetic preview remains 17.78kB. |
| Scoped formatting | PASS, 24 changed source files; `formatting-final.log`. |
| Changed-document lint | PASS, zero issues in new QA report and three canonical Markdown files with root configuration; `markdown-changed.log`. |
| Exact inherited lint baseline | README plus `docs/core-contract-questions.md`: ten inherited findings, exit 1, unresolved and unwaived; `markdown-inherited.log`. This is not PASS. |
| Expanded historical-doc lint | README plus `docs/*.md`: 109 findings in five unchanged files, exit 1; `markdown-ui-docs-expanded.log`. Includes the ten baseline findings and existing SCRUM-24/25/26 report formatting findings. Outside this Task's repair scope; no waiver or fix claimed. |
| Whitespace / boundaries | PASS, exact 29-path inventory, scoped canonical validation, whitespace and sensitive-literal checks; raw SHA256/Git blobs in `candidate-validation.json`. Protected paths unchanged by exact inventory. Index empty and HEAD unchanged. |

Focused command: `npm run test:ci --` with seven `--include` arguments for
`features/tasks/task-integrity.spec.ts`, `features/inspection-navigation.spec.ts`,
`features/screens.spec.ts`, `features/flow/flow.spec.ts`,
`shared/nile/dag-flow.spec.ts`, `shared/execution-timeline.spec.ts` and
`application-v1/guided-explorer.spec.ts` under `src/app/`.
Full suite: `npm run test:ci`; typecheck: `npm run typecheck`; build: `npm run build`.
There is no configured UI ESLint/template-lint target; scoped formatting,
TypeScript, Angular compilation and document lint are the applicable checks.

Two sandboxed production-build attempts exited with Windows access-violation
status `-1073741819`. The same command passed outside the sandbox without code
changes. Exact process fault origin was not isolated; the failed attempts are
preserved in `build.log` and `build-retry.log`, not relabeled PASS. Initial focused
tests exposed harness assumptions: a zero-latency read could already render the
correct new Run; loading uses accessible skeletons; browser-history tests needed
the router location listener and asynchronous navigation settlement. Those tests
were corrected before the final runs. No decoder or assertion of identity
correctness was relaxed. Early transition tests emitted Angular collection
recreation warnings; final Chrome console capture is empty, a bounded observation.
The first cached Markdownlint attempts could not access the installed CLI inside
the sandbox and did not lint documents. Their logs are preserved separately;
rerunning the same cached tool outside the sandbox produced the actual scoped
and inherited results above. No dependency was installed.

## Actual Chrome coverage

The existing frontend-only preview was reused; no Core service, provider request
or engineering session was started. Actual CSS dimensions were read back because
Chrome had 90% zoom. Temporary viewport settings were reset and dark theme
restored. `browser-observations.json` contains timestamped DOM/layout/focus rows;
`scenario-matrix.json` contains all 18 selector/control observations.

| Actual viewport / theme | Observed coverage |
| --- | --- |
| 1280×900 dark | Task selection/dependency, Back/Forward, Task filter restoration, no-evidence event, timeline/DAG Close focus, Flow Back/Forward, guide-open DAG at 572.9px and Task selected timeline at 490.7px. |
| 1280×900 light | Dedicated Run with guide and selected timeline: 572.9px workspace, 522.7px timeline; persistent Run-wide scope control retains keyboard focus. |
| 390×844 light | All 18 scenarios selected; page/guide selectors agree; Execute/Approve/Cancel/Resume disabled throughout; document width 378px. Scroll action moved page from approximately 147.8px to 1085.6px with expanded guide. Long Task objective/context and Flow graph/inspector at 346.9px inspected. |
| 320×800 dark | Long synthetic metadata wraps; document width 308px. Guide Minimize/Expand/Exit/re-entry, opener focus and Flow graph/inspector stack at 276.9px observed. |
| 2133×1012 light | Task context and desktop side guide inspected; screenshot `desktop-task-context-light.jpg` captured. Default-width dark theme restored at end. |

The settled native-keyboard guide measurements are the acceptance evidence:
Result → Journal retained Next focus and page Y approximately 3156.7px;
Approval preview → Task retained Previous focus and Y approximately 3563.3px.
Route remained the current Task. Locate separately navigated to
`/application-v1-preview` and focused `lifecycle-evidence`.
Inspector Close observations confirm the surviving focus target; their broader
locator sequences are not paired before/after scroll measurements. Source and
regressions verify `preventScroll`, without claiming every document position is
invariant when inspector removal changes layout height.

Preliminary immediate DOM rows can precede Angular rendering; they are diagnostic,
not independent assertions of settled state. Locator actions can scroll a target
into view before activation and reject an `aria-disabled` control; current-focus
native Return was used to isolate endpoint behavior. A mobile locator click on
the fixed guide link did not navigate; keyboard activation did. These tool
limitations are not claimed as physical touch results. Selector mistakes and a
forward-with-no-history attempt were corrected and are not application failures.

Mobile screenshot capture timed out. The earlier before-state screenshot attempt
also timed out; before-state DOM reproduction and source evidence were recorded.
The successful desktop image is visual evidence only for its captured viewport.
`console.json` contains no captured warnings/errors in the fresh verification tab;
this does not prove universal console cleanliness or identify the responsible
sender of the historical SCRUM-88/SCRUM-82 extension-message-signature errors.
Their precise origin remains unresolved in the preserved earlier reports.

## Independent review and remaining limitations

Contract/evidence-integrity review by `/root/contract_review`: **APPROVE**.
Requested repairs to Run mismatch classification, absent-history
wording and scope-button focus are resolved. UX/accessibility review by
`/root/ux_review`: **APPROVE**, after inspecting source, tests, final receipts,
browser observations, the desktop image and Task/report records. Both are
separate Agent instances from all implementers. `independent_review` and
`documentation_consistency` **PASS**; no material findings remain. Final decisions
are recorded in the canonical
[review record](../../../.ai/tasks/ITRU-066-scrum-89-evidence-integrity/review.md).

Unperformed: physical touch/device/virtual-keyboard testing, screen-reader speech,
full WCAG certification, comprehensive contrast audit and cross-browser testing.
Not every scenario/theme/viewport combination was exercised. Missing source
observations remain unavailable, not negative evidence. The ten inherited
Markdownlint findings remain non-green. Unrelated recency copy, touch panning
and dense-table polish remain separate.

Option D and S0 NO-GO remain binding. No Core, models/contracts/decoders, mock
scenario fixtures, provider binding, operational transport/action, parked
SCRUM-81 import or completed Task record was changed. The 29-file candidate is
ready for Human review and a separately authorized local checkpoint. No
staging/commit is authorized; final
Human acceptance, Git checkpoint and Task/Jira closure remain separate decisions.

## Exact changed paths

Paths are relative to the repository root. The ignored QA receipts are not part
of this 29-file candidate.

```text
.ai/tasks/ITRU-066-scrum-89-evidence-integrity/task.yaml
.ai/tasks/ITRU-066-scrum-89-evidence-integrity/context.md
.ai/tasks/ITRU-066-scrum-89-evidence-integrity/acceptance-criteria.md
.ai/tasks/ITRU-066-scrum-89-evidence-integrity/review.md
ui/control-center/docs/SCRUM-89-task-evidence-integrity-qa-2026-10-20.md
ui/control-center/src/app/application-v1/guided-explorer.spec.ts
ui/control-center/src/app/application-v1/guided-journey.css
ui/control-center/src/app/application-v1/guided-journey.html
ui/control-center/src/app/application-v1/guided-journey.ts
ui/control-center/src/app/features/flow/flow.css
ui/control-center/src/app/features/flow/flow.html
ui/control-center/src/app/features/flow/flow.spec.ts
ui/control-center/src/app/features/flow/flow.ts
ui/control-center/src/app/features/inspection-navigation.spec.ts
ui/control-center/src/app/features/runs/run-detail.css
ui/control-center/src/app/features/runs/run-detail.ts
ui/control-center/src/app/features/screens.spec.ts
ui/control-center/src/app/features/tasks/task-context-summary.css
ui/control-center/src/app/features/tasks/task-context-summary.ts
ui/control-center/src/app/features/tasks/task-detail.css
ui/control-center/src/app/features/tasks/task-detail.ts
ui/control-center/src/app/features/tasks/task-integrity.spec.ts
ui/control-center/src/app/features/tasks/tasks.ts
ui/control-center/src/app/shared/execution-timeline.css
ui/control-center/src/app/shared/execution-timeline.spec.ts
ui/control-center/src/app/shared/execution-timeline.ts
ui/control-center/src/app/shared/nile/dag-flow.html
ui/control-center/src/app/shared/nile/dag-flow.spec.ts
ui/control-center/src/app/shared/nile/dag-flow.ts
```
