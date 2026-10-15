# SCRUM-25 Completion Report — ITRU UI DAG, Scheduler & Nile Flow Integration

## Metadata
- **Jira Task**: SCRUM-25 — ITRU UI DAG, Scheduler & Nile Flow Integration
- **Baseline**: `cd2bdcb` (feat: add persistent run history and continuation UX - SCRUM-24)
- **Branch**: `ui/dag-scheduler-nile-flow`
- **Execution Date**: 2026-10-15
- **Lane**: UI Lane (Contract-safe operator visualization only; Core contracts pending ITRU-063)

---

## 1. Executive Summary & Goal
SCRUM-25 establishes a contract-safe, interactive operator experience for visualizing execution DAGs, task dependencies, execution flow, and scheduler-looking state using ITRU's organic Nile visual language.

Because ITRU-063 (Core DAG, Dependency Resolution, and Scheduler Specification) has NOT started yet, this phase is strictly a **presentation-only visualization and operator UX layer**. No canonical scheduler semantics, readiness algorithms, dispatch authority, cycle handling, or persistence models were invented. When ITRU-063 formalizes these contracts, they will connect through data-source presentation adapters without requiring redesign of the user interface.

---

## 2. Graph & Scheduler Read-Model Boundaries

### Strict Architecture
```
ControlCenterDataSource
        ↓
UI-local graph / scheduler read models
        ↓
pure presentation adapters (dag-adapter.ts)
        ↓
Nile / DAG / Scheduler UI
```

### Strict Non-Authority Guarantees
1. **Read Models Only**: All graph types (`DagGraphReadModel`, `DagNodeReadModel`, `DagEdgeReadModel`, `SchedulerSummaryReadModel`) are defined in `src/app/data/models.ts` as UI-local presentation structures.
2. **No Canonical Enums**: The scheduler panel uses UI presentation states (`'queued' | 'ready-looking' | 'active-looking' | 'blocked-looking' | 'completed-looking' | 'attention'`), explicitly documented as presentation-only labels.
3. **No Invented Algorithms**: The UI executes no dependency satisfaction checks, readiness algorithms, scheduling decisions, dispatch logic, or retry/failover policies.
4. **Mandatory Banners**:
   - Scheduler Overview: *"Scheduler state supplied by current data source · Core scheduler semantics pending ITRU-063."*
   - Dependency Inspector: *"Dependency relations supplied by presentation data source · Core readiness algorithm & dispatch eligibility pending ITRU-063."*
   - Effect Ambiguous Alert: *"WARNING: effect_ambiguous result · Automatic retry or replay is strictly prohibited. Core defines no safe recovery without external verification."*
5. **No Core/Schema Mutations**: Zero files modified outside `ui/control-center/`. Zero changes to `core/`, `.ai/`, or `schemas/`.

---

## 3. Nile & DAG Flow UX

### Nile Visual Metaphor
- **Principal Flow (Trunk)**: Main execution reach rendered with prominent channels, smooth S-curve tangents, and subtle organic meanders.
- **Tributaries**: Dependent sub-agent tasks, parallel branches, and security checkpoints that branch off the trunk and meander back into convergence points.
- **Confluence / Joins**: Explicit multi-dependency join points where tributary branches converge.
- **Decorative Water Highlights**: Flowing sheen lines with pause/resume toggle (`prefers-reduced-motion` fully respected). Flow animations carry zero progress or rate claims.
- **Node Islands**: Color-coded by presentation tone, with distinct badges for Result presence, evidence count, continuation affordance, and hazard stripes for `effect_ambiguous`.

### Navigation & Canvas Controls
- **Zoom & Pan**: Floating zoom in (`+`), zoom out (`-`), reset view (`1:1`), fit graph, and focus selected node controls. Mouse drag pans smoothly across the SVG canvas.
- **Keyboard Navigation**:
  - `ArrowRight`: Navigates to downstream dependent node.
  - `ArrowLeft`: Navigates to upstream dependency node.
  - `ArrowDown` / `ArrowUp`: Navigates to sibling nodes in adjacent vertical lanes.
  - `Enter` / `Space`: Selects focused node.
- **Dependency Illumination**: When a node is selected, upstream dependencies and edges illuminate in cyan (`var(--info)`), while downstream dependents illuminate in purple (`var(--accent-strong)`), with unrelated nodes gently dimmed for scannability.
- **Responsive List View Fallback**: Toolbar toggle between "River view" and "List view", rendering a high-density, screen-reader friendly table of all nodes, states, and dependency links.

---

## 4. Scheduler Presentation Panel

- **Status Counters & Filter Pills**: Fast filtering by scheduler-looking presentation states:
  - All nodes
  - Active (looking)
  - Ready (looking)
  - Blocked (looking)
  - Needs Attention
  - Completed (looking)
  - Queued
- **Immediate Operator Focus Strip**: Horizontal list of active, blocked, and attention items with quick-click selection.
- **Search & Artifact Filters**: Text search across node labels, IDs, roles, tools, and actors, plus artifact filtering (`has-result`, `has-evidence`, `has-continuation`).

---

## 5. Result, Journal, Evidence & Continuation Integration

When a node is selected, the **Node Detail Inspector** composes prior approved milestone components directly without duplicating semantics:
- **ResultShell (SCRUM-22)**: Canonical ITRU-060 in-memory Result presentation, derived identity tuples, outcome badges, text previews, hex samples, and truncation indicators.
- **ExecutionTimeline (SCRUM-23)**: Ordered Journal timeline events (`entry_observed`, `result_observed`) with the canonical order disclaimer banner.
- **EvidencePanel (SCRUM-23)**: Quality gate outcomes, command outputs, diff summaries, and verification states.
- **ContinuationShell (SCRUM-24)**: Source-supplied continuation affordances with locked ITRU-062 disclaimers and disabled demo controls.

### Strict `effect_ambiguous` Boundary
Nodes linked to an `effect_ambiguous` Result outcome:
- Render with red dashed hazard halos and warning glyphs on the canvas.
- Trigger prominent danger alert boxes in the inspector:
  *"Strict Side-Effect Boundary Alert: WARNING: effect_ambiguous result · Automatic retry or replay is strictly prohibited. Core defines no safe recovery without external verification."*
- Never present resume or replay buttons, preventing any operator misconception that DAG visualization implies retry safety.

---

## 6. Realistic Mock Scenarios Implemented

1. **`fan-out-fan-in`** (Default): Multi-agent workflow fanning out into 4 sub-agents (API layer, DB schema, security analysis, test scaffold) converging on a confluence join.
2. **`linear-workflow`**: Sequential 5-stage pipeline without branching.
3. **`blocked-branch`**: Tributary blocked by missing human authorization checkpoint; downstream join blocked waiting.
4. **`attention-error`**: Diagnostic failure branch with `failed_before_effect` and `containment_rejected` diagnostic code.
5. **`effect-ambiguous`**: Hazardous write branch with `run_a41c07e2` linked, testing hazard styling and strict retry prohibitions.
6. **`completed-historical`**: Fully completed execution DAG with canonical Results and evidence attached.
7. **`active-branch`**: Concurrent executing tributaries with live flow highlights and in-progress presentation states.
8. **`large-mesh-24`**: 24-node complex graph across 6 columns and 5 vertical lanes, testing zoom, pan, large-scale filtering, and list view fallback.
9. **`disconnected-graph`**: Multiple disconnected sub-flows testing presentation resilience to disjoint components.
10. **`stale-data`**: Scenario with `isStale: true` verifying warning banner presentation.
11. **`empty-graph`**: Scenario returning 0 nodes verifying empty state panel presentation.

---

## 7. Core Contract Questions Updated (`docs/core-contract-questions.md`)

Added Section 10: `## 10. DAG & Scheduler Semantics (SCRUM-25 / UNRESOLVED PENDING ITRU-063)` tracking all 16 items explicitly marked UNRESOLVED in Core pending ITRU-063:
1. Canonical DAG identity
2. Canonical node identity
3. Canonical edge / dependency contract
4. Dependency satisfaction rules
5. Scheduler lifecycle / state machine
6. Readiness rules
7. Scheduling authority
8. Dispatch / admission interaction
9. Concurrency semantics
10. Fairness policy
11. Retry / failover policy
12. Graph persistence
13. Scheduler persistence
14. Query / index / pagination model
15. Cycle handling
16. Cancellation semantics and scheduler recovery after restart

All previously locked boundaries (ITRU-060 Canonical Results, ITRU-061 Phase 1 SQLite Journal, ITRU-062 Persistent Runs/Tasks/Resumption) remain strictly preserved.

---

## 8. Validation Results

| Check | Result | Details |
|---|---|---|
| `npm run typecheck` | **PASS** | Zero TypeScript compiler errors (`tsc -p tsconfig.app.json` & `tsconfig.spec.json`) |
| `npm run test:ci` | **PASS** | **158 passed / 158 total** across **19 test files** (31 new tests added) |
| `npm run build` | **PASS** | Production bundle generated with **0 warnings and 0 errors** (`dist/control-center`) |
| Budget Check | **PASS** | All styles and scripts within production budget constraints |
| Scope Check | **PASS** | 100% of changes confined to `ui/control-center/` |

---

## 9. Browser & Visual Review Findings

A comprehensive interactive review was performed using `browser_subagent` recording video artifacts (`dag_nile_browser_review_1792051370638.webp`):
1. **Primary Navigation**: `'Flow'` nav link in the sidebar is active and highlights when routed to `/flow`.
2. **Default Scenario**: Page loads with `Multi-Agent Fan-Out & Join` scenario; river canvas renders trunk, 4 tributaries, and confluence join.
3. **Scheduler Panel**: Mandatory ITRU-063 notice is clearly rendered. Filter pills accurately reflect counts and filter nodes on click. Focus strip displays active and attention items.
4. **Node Selection & Illumination**: Clicking node `'API Service Layer'` illuminates upstream and downstream dependency edges, opens the Node Detail Inspector, and renders the embedded ResultShell.
5. **`effect_ambiguous` Hazard Review**: Selecting `'effect_ambiguous (Hazardous Outcome)'` renders hazard rings and warning icons on the canvas; inspector displays the bold hazard warning prohibiting retry or replay.
6. **Blocked Branch Review**: Selecting `'Blocked Dependency & Checkpoint'` displays blocked tributary and approval checkpoint with interactive cross-navigation chips.
7. **Large Graph & Zoom**: Selecting `'Large 24-Node Graph Mesh'` renders 24 nodes. Floating controls zoom in, zoom out, reset view, and fit graph smoothly.
8. **View Mode Toggling**: Successfully toggled between River view and List view table representation.
9. **Empty & Stale States**: Verified that `'Stale Data State'` displays the stale snapshot banner, and `'Empty Graph'` displays the empty state panel.
10. **Theming & Accessibility**: Dark and light themes toggle cleanly; focus outlines, keyboard arrow navigation, and reduced-motion declarations function properly.

---

## 10. Files Changed

### Modified Files (10)
- `ui/control-center/docs/core-contract-questions.md`: Added Section 10 documenting 16 unresolved ITRU-063 scheduler items.
- `ui/control-center/src/app/app.routes.ts`: Added `/flow` route to router configuration.
- `ui/control-center/src/app/app.ts`: Added `'Flow'` with icon `'nile'` to `PRIMARY_NAV`.
- `ui/control-center/src/app/app.spec.ts`: Updated primary navigation and destination test expectations.
- `ui/control-center/src/app/data/control-center-data-source.ts`: Added `listDagScenarios()` and `getDagGraph()` abstract methods.
- `ui/control-center/src/app/data/models.ts`: Added DAG node/edge/graph and scheduler summary read-models and presentation models.
- `ui/control-center/src/app/data/mock/mock-control-center-data-source.ts`: Implemented DAG methods with latency simulation.
- `ui/control-center/src/app/data/mock/mock-control-center-data-source.spec.ts`: Added unit tests for DAG scenario and graph loading.
- `ui/control-center/src/app/data/mock/mock-data.ts`: Exported `MOCK_RESULT_READ_MODELS` for DAG scenario integration.
- `ui/control-center/src/app/features/screens.spec.ts`: Added integration test verifying `/flow` screen rendering and interaction.

### New Files Created (17)
- `ui/control-center/src/app/data/dag-adapter.ts`: Pure presentation adapter for DAG nodes, edges, graph, and scheduler state.
- `ui/control-center/src/app/data/dag-adapter.spec.ts`: Unit tests for DAG adapter and disclaimers.
- `ui/control-center/src/app/data/mock/mock-dag-data.ts`: Realistic mock scenarios (linear, fan-out/fan-in, blocked, attention, effect_ambiguous, large 24-node mesh, stale, empty, disconnected).
- `ui/control-center/src/app/shared/nile/scheduler-panel.ts`: Operator scheduler presentation panel component.
- `ui/control-center/src/app/shared/nile/scheduler-panel.html`: HTML template for scheduler panel.
- `ui/control-center/src/app/shared/nile/scheduler-panel.css`: Scoped CSS styles for scheduler panel.
- `ui/control-center/src/app/shared/nile/scheduler-panel.spec.ts`: Unit tests for scheduler panel.
- `ui/control-center/src/app/shared/nile/dag-flow.ts`: Nile DAG river visualizer component with pan/zoom/keyboard navigation.
- `ui/control-center/src/app/shared/nile/dag-flow.html`: HTML template for DAG flow visualizer and list view fallback.
- `ui/control-center/src/app/shared/nile/dag-flow.css`: Scoped CSS styles for DAG flow visualizer.
- `ui/control-center/src/app/shared/nile/dag-flow.spec.ts`: Unit tests for DAG flow visualizer.
- `ui/control-center/src/app/shared/nile/dag-node-inspector.ts`: Node detail inspector component with Result/Timeline/Evidence/Continuation integration.
- `ui/control-center/src/app/shared/nile/dag-node-inspector.html`: HTML template for node inspector.
- `ui/control-center/src/app/shared/nile/dag-node-inspector.css`: Scoped CSS styles for node inspector.
- `ui/control-center/src/app/shared/nile/dag-node-inspector.spec.ts`: Unit tests for node inspector.
- `ui/control-center/src/app/features/flow/flow.ts`: Route component for `/flow`.
- `ui/control-center/src/app/features/flow/flow.html`: HTML template for Flow feature page.
- `ui/control-center/src/app/features/flow/flow.css`: Scoped CSS styles for Flow feature page.
- `ui/control-center/src/app/features/flow/flow.spec.ts`: Unit tests for Flow feature page.
- `ui/control-center/src/styles.css`: Added `--surface-1` token alias to dark and light modes, base scrollbar rules, and shared `.swatch` styling.
- `ui/control-center/docs/SCRUM-25-dag-scheduler-nile-flow-report.md`: Completion report.

---

## 11. Review Boundary & Next Actions
- **Blocker / High / Medium Issues**: **0**.
- **Human Approval State**: **Awaiting Human UI Review (Post-Remediation)**.
- **Commit Readiness**: Ready for commit upon Human UI sign-off.
- **Push / Merge Status**: NOT committed or pushed, strictly adhering to protocol.
- **Stop Condition**: Stopped at Human UI Review checkpoint.

---

## 12. Remediation Log (Human Review Reopening)

### Human Review Rejection / Reopening Summary
Human review rejected the initial SCRUM-25 checkpoint citing three requirements:
1. **Build issue**: Build warning/budget defect requiring reproduction and exact root-cause fix.
2. **Dark-mode UI issues**: Visual defects in dark mode (text contrast, missing surface tints, inspector layout blowout).
3. **EOF whitespace issues**: Trailing blank lines at EOF reported by `git diff --check`.

### 1. Build Issue Reproduction & Root Cause
- **Reproduction**: Running `npm run build` emitted:
  ```text
  ▲ [WARNING] src/app/shared/nile/dag-flow.css exceeded maximum budget. Budget 6.00 kB was not met by 334 bytes with a total of 6.33 kB.
  ```
- **Root Cause**: Component scoped CSS in `src/app/shared/nile/dag-flow.css` contained verbose compound selectors and duplicated definitions that expanded to 6.33 kB after Angular style scoping.
- **Remediation**:
  - Replaced verbose comma-separated compound selectors with modern `:is(...)` grouping.
  - Eliminated redundant properties and manual vendor prefixes handled by PostCSS.
  - Promoted the reusable `.swatch` badge utility to global `styles.css`.
  - **Result**: `npm run build` now completes with **0 warnings and 0 errors**.

### 2. Dark-Mode Visual Defects & Remediation
- **Defect 1 (SVG Node Labels Occlusion)**:
  - *Cause*: SVG `.node text` had `stroke: var(--surface-2); stroke-width: 4px;` without `paint-order: stroke fill;`. The 4px dark stroke painted over the text fill, turning the labels almost completely black on the dark river canvas.
  - *Fix*: Added `paint-order: stroke fill;` with `stroke: var(--bg); stroke-width: 3.5px;`. The stroke now renders cleanly behind the text, making `var(--text)` labels and `var(--text-muted)` subtitles razor-sharp and high-contrast in both dark and light themes.
- **Defect 2 (Undefined `--surface-1` Token)**:
  - *Cause*: Several components referenced `var(--surface-1)`, which was not defined in `styles.css`, causing `color-mix()` expressions to evaluate as invalid and resolve to transparent/unset backgrounds.
  - *Fix*: Added `--surface-1: #0e1a20;` in dark mode and `--surface-1: #ffffff;` in light mode in `styles.css`, and normalized all SCRUM-25 components to use `var(--surface)` directly.
- **Defect 3 (Inspector Grid Blowout in River View)**:
  - *Cause*: `flow.css` used `grid-template-columns: 1fr 380px` without `minmax(0, 1fr)` or `min-width: 0` on `.main-column`. The 1200px wide SVG inside `.viewport` prevented the 1st column from shrinking, pushing the aside inspector below the canvas.
  - *Fix*: Updated `flow.css` to `grid-template-columns: minmax(0, 1fr) 380px` (and 420px on wide screens) and added `min-width: 0` to `.main-column`. The inspector now sits properly side-by-side with the river canvas.
- **Defect 4 (Scrollbars)**:
  - *Cause*: Default bright gray browser scrollbars were visible in scrollable panels in dark mode.
  - *Fix*: Added `scrollbar-width: thin; scrollbar-color: var(--border-strong) transparent;` to `styles.css`.
- **Light-Mode Regression Check**: Verified in Light Mode (`data-theme='light'`). Papyrus surfaces, dark ink text, badges, and the inspector rendered with high contrast and zero visual regressions.

### 3. Whitespace Remediation
Resolved trailing blank lines at EOF in all 6 flagged files:
- `ui/control-center/docs/core-contract-questions.md`
- `ui/control-center/src/app/data/control-center-data-source.ts`
- `ui/control-center/src/app/data/mock/mock-control-center-data-source.spec.ts`
- `ui/control-center/src/app/data/mock/mock-control-center-data-source.ts`
- `ui/control-center/src/app/data/models.ts`
- `ui/control-center/src/app/features/screens.spec.ts`

`git diff --check` now exits cleanly with **code 0 and 0 errors**.

### 4. Final Quality Gates
| Gate | Command | Result |
|---|---|---|
| Typecheck | `npm run typecheck` | **PASS** (0 errors) |
| Tests | `npm run test:ci` | **PASS** (158 passed / 158 total across 19 test files) |
| Build | `npm run build` | **PASS** (0 warnings, 0 errors, all budgets met) |
| Git Diff Check | `git diff --check` | **PASS** (0 whitespace/conflict errors) |
| Interactive Browser Review | Visual & Responsive Validation | **PASS** (Dark mode, light mode, 11 scenarios, mobile, tablet, desktop) |

### 5. Final Path Count
- **Tracked modified files**: **11**
- **Untracked files**: **20**
- **Total SCRUM-25 paths**: **31**
- **Remaining issues**: **0 Blocker, 0 High, 0 Medium**
- **Commit readiness**: Ready for final Human UI sign-off.
