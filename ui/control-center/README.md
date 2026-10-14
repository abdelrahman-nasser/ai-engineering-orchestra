# ITRU Control Center

ITRU Control Center is the operator-facing desktop web interface for AI Engineering Orchestra (`itru`).

This application provides visibility into Tasks, Agent Execution Runs, Workflow progression, Actor availability, Quality Gate evidence, and Human Approval checkpoints.

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
   - Where the UI requires presentation data that Core does not yet specify (e.g. Run lifecycle status, approval queueing, event timeline), these concepts are modeled strictly as **UI-local presentation models** in `src/app/data/models.ts`.
   - All unresolved Core dependencies are cataloged in [`docs/core-contract-questions.md`](./docs/core-contract-questions.md).

3. **Core Vocabulary Reuse**:
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
├── data/
│   ├── models.ts                 # UI-local presentation models & Core vocabulary
│   ├── control-center-data-source.ts # Abstract data-source contract & InjectionToken
│   └── mock/
│       ├── mock-data.ts          # Deterministic DEMO dataset
│       └── mock-control-center-data-source.ts # In-memory mock implementation
├── features/
│   ├── overview/                 # Overview dashboard: stat tiles, workspace river, attention
│   ├── runs/                     # Runs list & Run detail view
│   ├── tasks/                    # Tasks list & Task detail view
│   ├── agents/                   # Agents list with actor availability & competencies
│   ├── approvals/                # Read-only Human Approval checkpoint list
│   └── not-found/                # 404 fallback page
└── shared/
    ├── nile/                     # Nile organic branch execution river (SVG)
    ├── execution-timeline.ts     # Reusable vertical event timeline
    ├── result-shell.ts           # Provisional Result presentation card
    ├── evidence-panel.ts         # Collapsible Quality Gate & evidence inspector
    ├── status-badge.ts           # Unified status indicator badge
    ├── stat-tile.ts              # Metric summary tile
    ├── page-header.ts            # Standardized page title & breadcrumbs
    ├── state-panel.ts            # Loading, empty, and error feedback states
    └── theme.service.ts          # Dark / Light theme management (persisted in localStorage)
```

### Key Architectural Patterns

- **`ControlCenterDataSource`**:
  - The sole abstraction boundary between screens and data.
  - Returns `Observable<T>` streams to support future streaming or remote backends without altering feature components.
  - Implemented currently by `MockControlCenterDataSource`, injectable via the `ControlCenterDataSource` token.
  - In tests, simulated latency is removed via `MOCK_LATENCY_MS` set to `0`.

- **Nile Organic Branch Flow (`cc-nile-flow`)**:
  - Visualizes workflow execution as a river topology with smooth cubic bezier curves connecting stages, roles, and runs.
  - Features subtle animated flow dashed strokes indicating active pipelines (respects `prefers-reduced-motion` and includes an explicit UI toggle).
  - Represents **presentation topology only**: it visually diagrams stages and roles without declaring scheduler, concurrency, or dependency semantics.

- **Provisional Result Presentation Shell (`cc-result-shell`)**:
  - Renders run results with clear visual badges indicating provisional status until Core formalizes a Result contract.

- **Evidence Panel (`cc-evidence-panel`)**:
  - Displays validation evidence, Quality Gate results, and review notes.
  - Transparently highlights `skipped` and `unverified` gates, adhering to the principle that missing evidence means unproven—not denied.

- **Dark & Light Design System**:
  - Semantic CSS custom properties define color tokens, elevations, typography, and borders in `src/styles.css`.
  - Accessible contrast ratios across both modes.
  - Toggled via the shell header and persisted to `localStorage`.

---

## Mock-Data Policy

1. **Clear Labeling**:
   - All mock items use distinct identifiers prefixed with `DEMO-` (e.g., `DEMO-101`, `run_f27a9c58`) to prevent confusion with production or repository tasks.
   - The shell displays an explicit **"Mock data"** status pill in the header at all times.
2. **Deterministic & Realistic**:
   - Mock data reflects real Core workflows (`standard-change`, `security-sensitive-change`, `architecture-change`) and actual Role definitions (`software-engineer`, `security-reviewer`, `system-architect`).
   - Represents diverse lifecycle states (planned, in progress, blocked, completed, cancelled) and edge cases (unverified authorization, skipped gates).
3. **Non-Invasive**:
   - Mock datasets are confined to `src/app/data/mock/` and do not generate side-effects or touch external APIs.
