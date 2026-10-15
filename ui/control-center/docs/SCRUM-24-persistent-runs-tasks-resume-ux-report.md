# SCRUM-24 Completion Report: Persistent Runs, Tasks & Resume UX

- **Jira Task**: SCRUM-24: Persistent Runs and Tasks with Resume UX
- **Baseline Commit**: `484525e` (`feat: add Journal timeline and evidence explorer (SCRUM-23)`)
- **Branch**: `ui/persistent-runs-tasks-resume-ux`
- **Final Status**: COMPLETE — Contract-Safe Presentation & UX Phase
- **Commit Hash**: PENDING — final local commit hash recorded in Jira after commit
- **Push Status**: NOT PUSHED (Local commit only per task scope)
- **Merge Status**: NOT MERGED (Merge and PR deferred per task scope)
- **Human Approval**: Human authorization granted (`APPROVE SCRUM-24 FINAL UI CLOSURE AND REPORT PATH`)

---

## 1. Executive Summary

SCRUM-24 delivers the complete, contract-safe operator user experience for browsing persistent Task and Run history and inspecting continuation/resume affordances in the ITRU Control Center.

Because Core persistence and resume semantics are scheduled for **ITRU-062 / SCRUM-19** (which has not yet started), SCRUM-24 strictly adheres to a presentation-only boundary. All lifecycle states, run associations, temporal timestamps, and continuation affordance indicators are modeled strictly within UI-local read models and data sources. When ITRU-062 standardizes canonical persistence and resume contracts, the underlying adapters can be updated without requiring any structural redesign of the UI layer.

---

## 2. Architectural Boundaries & Precedence

### Task-History Read-Model Boundary
- **Zero Core persistence or lifecycle mutation**: Core defines declarative tasks (`.ai/tasks/*.yaml`), but defines no runtime database persistence, Task state machines, or execution indexes.
- **UI-local read-model inputs only**: All history, temporal, and continuation indicators are encapsulated in `TaskSummary`:
  - `runCount?: number`
  - `latestRunId?: string`
  - `latestRunState?: PresentationState`
  - `hasResult?: boolean`
  - `continuationAvailable?: boolean`
  - `lastActivityLabel?: string`
- **Data-source origin**: Computed dynamically within `MockControlCenterDataSource` from associated mock runs without inventing backend storage or API contracts.

### Run-History Read-Model Boundary
- **Zero canonical Run lifecycle states or persistence**: Core defines `AgentExecutionRun` (`run_id`, `AgentExecutionContract`) as in-memory declarative intent only.
- **Generic source-supplied presentation fields**: Added to `RunSummary` and `RunDetail` without inventing scheduler states:
  - `statusLabel?: string` (e.g., `"In progress"`, `"Finished"`, `"Interrupted (Runner Preempted)"`, `"Failed Before Effect"`)
  - `lastActivityLabel?: string` (e.g., `"Today · 13:45"`, `"Yesterday · 11:45"`)
  - `hasResult?: boolean`
  - `resultOutcome?: AgentExecutionResultOutcome`
  - `evidenceCount?: number`
  - `continuation?: RunContinuationPresentation`
- **Presentation-only classification**: Mapped strictly through `PresentationState` (`'not-started' | 'in-progress' | 'needs-attention' | 'finished' | 'unknown'`).

### Continuation & Resume Presentation Boundary
- **Strictly decoupled from Core**: Core has NO concept of resume eligibility, checkpoint tokens, recovery semantics, or resume capabilities.
- **Pure adapter layer**: `adaptContinuationReadModel` maps raw source-supplied `RunContinuationReadModel` to `RunContinuationPresentation`.
- **Explicit disclaimer banner**: Every continuation container displays:
  > *"Continuation availability supplied by current data source · Core defines no canonical continuation/resume contract yet (pending ITRU-062)"*
- **No fake backend mutation**: All continuation/resume action buttons are strictly disabled demo affordances (`[disabled]="true"`, `[attr.aria-disabled]="true"`).
- **Prohibition on `effect_ambiguous`**: If a Run ended in `effect_ambiguous`, continuation is unconditionally blocked, a prominent danger warning is displayed, and resume buttons are omitted.
- **Audit disclaimer**: Explicitly warns operators that presence of Journal entries or evidence does not constitute resume safety proofs.

---

## 3. Integration with Prior Milestones

### Result Integration (SCRUM-22)
- Reuses `ResultShell` (`cc-result-shell`) directly without duplicating result semantics.
- Result outcome badges (`success`, `failure_clean`, `failure_with_side_effects`, `effect_ambiguous`) and execution summaries are integrated into the Task Run History tree and Run Inspector.

### Journal & Evidence Integration (SCRUM-23)
- Directly embeds `ExecutionTimeline` (`cc-execution-timeline`) and `EvidencePanel` (`cc-evidence-panel`) in the Task detail Run Inspector pane.
- Evidence counts and verification badges are surfaced on history table rows and tree nodes.
- Preserves the critical safety invariant: presence of WAL entries or evidence does not prove resume safety.

---

## 4. Preservation of Unresolved ITRU-062 Dependencies

All 13 Core dependencies remain strictly preserved as unresolved pending ITRU-062 / SCRUM-19:
1. Canonical Task identity & persistence contract
2. Canonical Run identity & persistence contract
3. Task & Run lifecycle state machines
4. Continuation & resume eligibility rules
5. Checkpoint & continuation identity
6. Restart recovery semantics
7. State reconstruction rules
8. Persistence schema & database technology
9. Task↔Run durability rules
10. Resume authority & authorization Grant requirements
11. Query API, indexing & pagination protocol
12. Concurrency & lease semantics
13. Interrupted, abandoned, & stale execution definitions

Locked architectural decisions from **ITRU-060** (Result outcomes & side-effect boundaries) and **ITRU-061 Phase 1** (Journal schema & WAL SQLite persistence) are strictly preserved without modification.

`ui/control-center/docs/core-contract-questions.md` has been updated with a dedicated Section 9 detailing these architectural requirements and mock assumptions.

---

## 5. UX & Presentation Implementation

### Task History UX (`TaskDetailPage`, `Tasks`)
- **Task Run History Tree**: Renders hierarchical run occurrences for any selected task:
  ```
  Task DEMO-110 (5 runs)
   ├─ run_h1_init (Finished)
   ├─ run_h2_design (Finished)
   ├─ run_h3_proto (Finished)
   ├─ run_h4_fail (Interrupted · Needs Attention)
   └─ run_h5_current (In progress · Continuation Available)
  ```
- **Prior Run selection**: Operators can interactively click or use keyboard navigation to select prior runs.
- **Integrated Run Inspector**: Selecting any run displays its continuation status, Result outcome, Journal timeline, and evidence explorer, along with a direct navigation button to `/runs/:runId`.
- **Tasks List enhancements**: Added history columns (`Runs`, `Latest Run`, `Status`, `Continuation`, `Last Activity`) and filter chips.

### Run History UX (`RunDetailPage`, `Runs`)
- **Runs List enhancements**: Columns for Stage & Workflow, Role & Actor, Result outcome, Evidence count, Continuation badge, and Last Activity. Filterable by `All`, `In progress`, `Needs attention`, `Finished`, `Has result`, `Has evidence`, and `Continuation available`.
- **Run Detail continuation shell**: Embedded above the Journal timeline, displaying source-supplied interruption notices, blocked reasons, and last known activity.

### Continuation UX (`ContinuationShell`)
Supports all 9 specified UX states:
1. **Continuation available**: Displays `Available` badge, proposed action label, reason, last activity, and disabled demo resume button.
2. **Continuation unavailable**: Displays `Unavailable` badge with explanation.
3. **Continuation blocked**: Displays `Blocked` badge with reason callout.
4. **Interrupted / requires attention**: Displays `Interrupted` badge with amber callout detailing interruption cause (e.g. runner preemption).
5. **Historical completed run**: Displays `Completed` badge with closure notice.
6. **Missing continuation information**: Displays honest empty notice: *"No continuation metadata supplied by current data source."*
7. **Stale observation**: Displays `Stale` badge with warning banner regarding snapshot expiration.
8. **Loading & error states**: Handled via standard `<cc-state-panel>`.
9. **Critical `effect_ambiguous` outcome**: Unconditionally renders danger callout prohibiting automated retry/replay/continuation to prevent duplicate side effects.

---

## 6. Mock Scenarios & Fixtures

Added realistic scenarios to `mock-data.ts`:
- **Completed historical Task with one Run**: `DEMO-109` (`run_h0_single`).
- **Task with multiple prior Runs**: `DEMO-110` (5 runs spanning init, design, proto, interrupted failure, and current active run).
- **Interrupted-looking Run with continuation availability**: `run_h4_fail` (runner preemption notice, proposed resume stage).
- **Continuation blocked with reason**: `run_b267df88` (stale lease / lease timeout blocked reason).
- **Run with Result + Journal evidence**: `run_5d70b2e8` (successful completion with 4 journal entries and 2 evidence items).
- **Effect ambiguous Run**: `run_a41c07e2` (critical outcome prohibiting retry).
- **No continuation information**: `run_34e02206` (honest missing metadata notice).
- **Stale/loading/error states**: Validated in component test fixtures and state panels.

---

## 7. Accessibility & Responsive Review

- **Tree Accessibility**: Follows WAI-ARIA Tree pattern (`role="tree"`, `role="treeitem"`, `aria-selected`, `tabindex="0"`, keyboard navigation with <kbd>Enter</kbd> and <kbd>Space</kbd>).
- **Semantic Callouts**: Interruption, warning, and danger alerts use `role="alert"` and `role="status"`.
- **Visible Focus**: Clear `:focus-visible` focus outlines across all interactive elements.
- **Color Contrast & Theming**: Full dark and light theme compliance with verified contrast ratios.
- **Responsive Layout**: Resilient flex and CSS grid containers with mobile scroll containment and responsive tree wrapping (tested at 1920x945 and mobile viewports).
- **Motion Reduction**: All transitions respect `@media (prefers-reduced-motion: reduce)`.

---

## 8. Validation Tooling Rationale (`angular.json` / `vitest.config.mts`)

- **Change**: Created `ui/control-center/vitest.config.mts` setting `fileParallelism: false` and referenced it in `angular.json` (`projects['control-center'].architect.test.options.configFile: "vitest.config.mts"`).
- **Rationale**: When running the comprehensive Angular component test suite under Vitest on Windows, concurrent worker threads caused rapid V8 heap fragmentation and out-of-memory crashes (`heap limit allocation failed`). Disabling Vitest worker parallelism for tests serializes test file execution, maintaining a stable memory footprint (~300MB) and delivering deterministic execution of all 127 tests in ~3.5 seconds.

---

## 9. Verification & Quality Gates

### Typecheck
```
> control-center@0.0.0 typecheck
> tsc -p tsconfig.app.json --noEmit && tsc -p tsconfig.spec.json --noEmit
Exit code: 0 (PASSED)
```

### Test Suite
```
> control-center@0.0.0 test:ci
> ng test --watch=false

Using Vitest configuration file: D:\Dev\itru-ui\ui\control-center\vitest.config.mts

Test Files  14 passed (14)
Tests       127 passed (127)
Duration    3.56s
Exit code:  0 (ALL TESTS PASSED)
```

### Production Build
```
> control-center@0.0.0 build
> ng build

Initial total: 319.21 kB (Raw) / 83.76 kB (Transfer)
Application bundle generation complete. [2.196 seconds]
Output location: D:\Dev\itru-ui\ui\control-center\dist\control-center
Exit code: 0 (PASSED)
```

### Browser Visual Review
Verified on local dev server (`http://localhost:4200`):
- `/tasks`: Run counts, latest run links, result status, continuation badges, and history filter chips verified.
- `/tasks/DEMO-110`: 5-run tree rendered with connectors; selection of `run_h4_fail` correctly updated the Run Inspector with continuation notices, timeline, and evidence; navigation link to `/runs/run_h4_fail` verified.
- `/runs/run_a41c07e2`: Danger callout blocking continuation on `effect_ambiguous` verified.
- `/runs/run_3c81f0a7`: Continuation available state, disclaimer, and disabled resume button verified.
- `/runs`: Column layout and history filters verified.
- Light/dark themes and responsive viewports verified.

---

## 10. Findings & Issues Summary

- **Blocker**: 0
- **High**: 0
- **Medium**: 0

No contract violations or unintended dependencies were introduced.

---

## 11. Exact Scope of Files Changed (20 Files)

1. `ui/control-center/angular.json` (configured Vitest config file)
2. `ui/control-center/vitest.config.mts` (Vitest sequential test configuration)
3. `ui/control-center/docs/core-contract-questions.md` (Section 9 for SCRUM-24 / ITRU-062)
4. `ui/control-center/docs/SCRUM-24-persistent-runs-tasks-resume-ux-report.md` (this report)
5. `ui/control-center/src/app/data/models.ts` (continuation models, TaskSummary and RunSummary extensions)
6. `ui/control-center/src/app/shared/presentation.ts` (continuation presentation status descriptors)
7. `ui/control-center/src/app/data/continuation-adapter.ts` (pure continuation presentation adapter)
8. `ui/control-center/src/app/data/continuation-adapter.spec.ts` (unit tests for continuation adapter)
9. `ui/control-center/src/app/shared/continuation-shell.ts` (reusable continuation shell component)
10. `ui/control-center/src/app/shared/continuation-shell.css` (continuation shell styling tokens)
11. `ui/control-center/src/app/shared/continuation-shell.spec.ts` (unit tests for continuation shell)
12. `ui/control-center/src/app/data/mock/mock-data.ts` (DEMO-109, DEMO-110, realistic continuation scenarios)
13. `ui/control-center/src/app/data/mock/mock-control-center-data-source.ts` (computed Task history fields)
14. `ui/control-center/src/app/features/tasks/tasks.ts` (history columns and filter chips)
15. `ui/control-center/src/app/features/tasks/task-detail.ts` (Task Run History tree and Run Inspector)
16. `ui/control-center/src/app/features/tasks/task-detail.css` (tree and inspector styling)
17. `ui/control-center/src/app/features/runs/runs.ts` (history columns and filter chips)
18. `ui/control-center/src/app/features/runs/run-detail.ts` (embedded continuation shell)
19. `ui/control-center/src/app/shared/nile/nile-topology.spec.ts` (updated portfolio topology tests for DEMO-110)
20. `ui/control-center/src/app/features/screens.spec.ts` (updated screen counts, tree selection, and continuation tests)
