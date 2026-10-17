# ITRU Control Center

ITRU Control Center is the operator-facing desktop web interface for AI Engineering Orchestra (`itru`).

This application provides visibility into Tasks, Agent Execution Runs, Workflow progression, Actor availability, Quality Gate evidence, and Human Approval checkpoints.

The application remains **mock-backed**. Existing screens are mock demonstrations;
their rich fields, payload previews and historical contract assumptions are not
real-source behavior. A separate **synthetic application v1.0 preview** is available
at `/application-v1-preview` (also linked in the sidebar). It uses isolated, closed
response decoders for the future `InspectRun` and `ReadRunJournal` reads and has
no operational connection. See [integration preparation](docs/application-v1-preparation.md)
for scope, evidence, validation and remaining review requirements.

---

## Getting Started

### Prerequisites

- Node.js >= 20.x
- npm >= 10.x

### Commands

From the `ui/control-center` directory:

```bash
# Start local development server (http://localhost:4200)
npm start

# Run type checking (tsconfig.app.json and tsconfig.spec.json)
npm run typecheck

# Run unit tests (Vitest)
npm test

# Run unit tests once in CI mode (no watch)
npm run test:ci

# Build production bundle
npm run build
```

---

## Core / UI Ownership Boundary

The UI lane operates under a **strict boundary contract**:

1. **Strict Core Isolation**:
   - The UI code lives entirely inside `ui/control-center/`.
   - The UI **MUST NOT** modify or import from `itru/`, `core/`, `schemas/`, `.ai/`, `migrations/`, or Core tests.
   - Core specifications (`core/*.md`) and schemas (`schemas/*.json`) remain the sole authoritative definitions for domain entities.

2. **No Invented Core Contracts**:
   - The UI **MUST NOT** invent REST endpoints, WebSocket protocols, scheduler semantics, lifecycle state transitions, Result schemas, or Journal contracts.
   - The original mock screens use **UI-local presentation models** in `src/app/data/models.ts`. Their required rich fields do not become application v1.0 fields.
   - Historical prototype questions are preserved in [`docs/core-contract-questions.md`](./docs/core-contract-questions.md); current preparation follows the approved v2 contract described below.

3. **Historical mock prototype references (not current integration contracts)**:
   - **ALREADY LOCKED**:
     - **ITRU-060 Result Semantics** (`core/agent-execution-result-specification.md`): Three terminal outcomes (`succeeded`, `failed_before_effect`, `effect_ambiguous`), derived 5-part identity tuple `(ledger_instance_id, domain_id, issuer_kind, issuer_id, grant_id)`, bounded content payload, closed diagnostic error table, permanent Execution Entry consumption.
     - **ITRU-061 Phase-1 Journal Semantics**: Sequential event progression, proof linkage, integrity assertions, non-synthetic timestamps.
   - Current Core already owns Task/Run lifecycle, continuation safety, Task DAG
     validation and advisory scheduler decisions. Older mock comments/questions
     about absent contracts describe prototype assumptions, not current Core.
   - The approved application boundary v2 defines content-free projections for
     exactly two semantic reads; it does not authorize operational reader admission.
     S0 is closed at NO-GO and S1–S8 remain unauthorized. This standalone synthetic
     preparation does not resume that implementation plan or select a transport.

4. **Core Vocabulary Reuse**:
   - Where Core has already established canonical terminology, the UI mirrors those values faithfully:
     - Task statuses (`planned`, `in_progress`, `blocked`, `completed`, `cancelled`)
     - Risk and complexity levels (`low`, `medium`, `high`, `critical`)
     - Human approval levels (`none`, `review`, `explicit`, `protected`)
     - Execution modes (`lite`, `standard`, `deep`, `critical`)
     - Actor kinds (`human`, `agent`)
     - Availability states (`available`, `unavailable`, `unknown`)

---

## Architecture

The application is built with **Angular 22** using TypeScript 6, Zoneless change detection, and standalone components.

```
ui/control-center/src/app/
├── app.ts / app.html / app.css   # Application shell with primary nav & header
├── app.routes.ts                 # Declarative lazy route configuration
├── app.config.ts                 # Application DI providers (router, data source)
├── application-v1/               # Isolated closed projections and synthetic preview
├── data/
│   ├── models.ts                 # UI-local presentation models & Core vocabulary
│   ├── control-center-data-source.ts # Abstract data-source contract & InjectionToken
│   ├── result-adapter.ts         # ITRU-060 Result presentation adapter
│   ├── timeline-adapter.ts       # Timeline & Evidence presentation adapter
│   ├── continuation-adapter.ts   # Continuation & Resume presentation adapter
│   ├── dag-adapter.ts            # DAG graph & Scheduler presentation adapter
│   └── mock/
│       ├── mock-data.ts          # Deterministic DEMO dataset
│       ├── mock-dag-data.ts      # Multi-scenario DAG & scheduler graph datasets
│       └── mock-control-center-data-source.ts # In-memory mock implementation
├── features/
│   ├── overview/                 # Overview dashboard: stat tiles, river, attention items
│   ├── runs/                     # Runs list & Run detail view
│   ├── tasks/                    # Tasks list & Task detail view with Run History tree
│   ├── agents/                   # Agents list with actor availability & competencies
│   ├── approvals/                # Read-only Human Approval checkpoint list
│   ├── flow/                     # Nile Flow & DAG Scheduler workbench
│   └── not-found/                # 404 fallback page
└── shared/
    ├── nile/                     # Nile organic branch execution river (SVG) & DAG components
    │   ├── nile-flow.ts          # Core portfolio & run river component
    │   ├── dag-flow.ts           # Interactive DAG dependency river & list view
    │   ├── dag-node-inspector.ts # Inspector drawer for node details & linked artifacts
    │   └── scheduler-panel.ts    # Operator scheduler overview & focus queue
    ├── execution-timeline.ts     # Reusable vertical event timeline with selection
    ├── result-shell.ts           # Canonical ITRU-060 Result presentation card
    ├── continuation-shell.ts     # Continuation affordances & effect-boundary warning
    ├── evidence-panel.ts         # Collapsible Quality Gate & evidence inspector
    ├── status-badge.ts           # Unified status indicator badge
    ├── stat-tile.ts              # Metric summary tile
    ├── page-header.ts            # Standardized page title & breadcrumbs
    ├── state-panel.ts            # Loading, empty, and error feedback states
    └── theme.service.ts          # Dark / Light theme management (persisted in localStorage)
```

### Key Architectural Patterns

- **`ControlCenterDataSource`**:
  - The abstraction boundary for the existing mock demonstration screens.
  - Returns `Observable<T>` streams to support future streaming or remote backends without altering feature components.
  - Implemented currently by `MockControlCenterDataSource`, injectable via the `ControlCenterDataSource` token.
  - In tests, simulated latency is removed via `MOCK_LATENCY_MS` set to `0`.

- **`application-v1/` synthetic preparation**:
  - Separate closed models, decoders, presentation state and fixtures; never
    routed through the existing mock adapters or their incompatible fields.
  - Preserves exact numeric strings, timestamp text, identities, canonical
    lifecycle/scheduler values and independent Journal coverage/comparison.
  - No payload previews, authority badges or operational action paths. Approval
    counts and configured routes are unavailable; continuation stays unassessed.

- **Interactive Nile Flow & DAG Scheduler Workbench (`cc-dag-flow`, `cc-dag-node-inspector`, `cc-scheduler-panel`)**:
  - Visualizes multi-agent execution graphs, fan-out/fan-in tributaries, dependencies, and join points.
  - Features interactive zoom/pan controls, centered node selection, upstream/downstream highlighting, and structured list view fallback.
  - Embedded node inspector reveals Task links, Run links, roles, actors, tool routes, and integrated Result, Timeline, Evidence, and Continuation cards.
  - Operator scheduler panel highlights queued, ready-looking, active-looking, blocked-looking, and attention nodes.

- **Canonical ITRU-060 Result Presentation Shell (`cc-result-shell`)**:
  - Aligned with canonical ITRU-060 in-memory Result semantics (`core/agent-execution-result-specification.md`).
  - Distinct visual presentation for all three terminal outcomes:
    - `succeeded`: bounded content payload preview (explicitly marked UTF-8 text vs raw binary preview, with truncation indicators for bounded samples).
    - `failed_before_effect`: positive proof that no content-data request was issued; displays canonical diagnostic code from closed ITRU-060 table; permanent Execution Entry consumption note.
    - `effect_ambiguous`: prominent high-visibility warning communicating that content-data access commenced or post-read cleanup uncertainty was encountered; strictly warns against automatic retry or replay.
  - Full evidence provenance display: derived 5-part Result identity tuple `(ledger_instance_id, domain_id, issuer_kind, issuer_id, grant_id)`, Execution Entry metadata, and Tool binding route.
  - Honest empty state when no Result has been published for an in-progress or uncompleted attempt (reflecting that absence is missing evidence, not implicit success/failure).

- **Continuation & Resume Presentation Shell (`cc-continuation-shell`)**:
  - Surfaces data-source-supplied continuation affordances (`available`, `blocked`, `interrupted`, `completed`, `stale`, `missing`).
  - Enforces strict prohibition of automated retry or replay whenever the Result outcome is `effect_ambiguous`.
  - Disclaims that display of journal entries or evidence does not prove continuation safety.

- **Execution Timeline (`cc-execution-timeline`) & Evidence Explorer (`cc-evidence-panel`)**:
  - Chronological event timeline supporting event selection and drill-down into linked results and evidence.
  - Comprehensive evidence inspector supporting Quality Gate checks, diagnostic outputs, diffs, and audit assertions.
  - Transparently highlights `skipped` and `unverified` gates, adhering to the principle that missing evidence means unproven—not denied.

- **Dark & Light Design System**:
  - Semantic CSS custom properties define color tokens, elevations, typography, and borders in `src/styles.css`.
  - Accessible contrast ratios across both modes.
  - Toggled via the shell header and persisted to `localStorage`.

---

## Mock-Data Policy

1. **Clear Labeling**:
   - All mock items use distinct identifiers prefixed with `DEMO-` (e.g., `DEMO-101`, `run_f27a9c58`) to prevent confusion with production or repository tasks.
   - Existing mock screens display a **"Mock data"** header pill; the separate
     application preview displays **"Synthetic application v1.0"**.
2. **Deterministic & Realistic**:
   - Mock data reflects real Core workflows (`standard-change`, `security-sensitive-change`, `architecture-change`) and actual Role definitions (`software-engineer`, `security-reviewer`, `system-architect`).
   - Represents diverse lifecycle states (planned, in progress, blocked, completed, cancelled) and edge cases (unverified authorization, skipped gates).
3. **Non-Invasive**:
   - Original mock datasets stay in `src/app/data/mock/`; isolated application
     fixtures stay in `src/app/application-v1/fixtures.ts`. Neither touches external APIs.
