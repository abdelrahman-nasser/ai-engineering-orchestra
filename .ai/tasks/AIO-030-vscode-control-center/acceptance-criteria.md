# AIO-030 Acceptance Criteria

## Task and design

- [x] AIO-030 has exactly the four canonical Task artifacts and remains
  `in_progress` at the final Human Control checkpoint.
- [x] `security-sensitive-change` governs the Task with effective gates
  `documentation_consistency` and `independent_review`.
- [x] A separate Architect reviews and approves the locked design before
  implementation, and separate Security Reviewer and Reviewer executions
  examine the complete change set afterward.
- [x] The design records the selected Codex source, wire contracts, ownership,
  trust and consent boundaries, identity, ordering, freshness, limits, cleanup,
  UI truth conditions, and unsupported cases.
- [x] The corrected Architect lock defines immutable observer installation,
  bounded multi-window registry resolution, mutual local authentication,
  renewable leases, closed bridge envelopes/errors/limits, opaque-ID handling,
  replay bounds, and exact state evidence before implementation starts.

## Core bridge and project boundary

- [x] A one-shot `aio.ide/1` JSON bridge exposes only `project_snapshot` and
  exact-ID `task_detail` operations with bounded structured responses.
- [x] The bridge reuses current project, inventory, Task inspection, Workflow,
  Role, effective metadata, and structural-validation behavior without parsing
  CLI tables or changing domain schemas/default semantics.
- [x] Managed, unmanaged, invalid, and error project states; Task inventory and
  anomalies; declared status/workflow filters; artifact health; provenance; and
  ordered declared Workflow/Role detail come from real project data.
- [x] Canonical selected-root containment blocks external configured Task paths,
  symlink/junction escapes, and out-of-scope navigation without rewriting the
  Manifest.
- [x] Bridge requests validate protocol, request ID, explicit root, operation,
  payload, output limits, and exact declared Task IDs, with structured missing
  Core/interpreter, timeout, invalid input/project, and unsupported-protocol
  behavior at the appropriate layer.
- [x] A trusted interpreter is launched by absolute path with argument arrays,
  `shell: false`, isolated imports, sanitized environment, timeout, bounded
  output, package-origin checks, and stale-response rejection.
- [x] Existing human CLI behavior remains compatible, and the wheel excludes
  extension/check-out artifacts while working from an installed Core outside
  the checkout.

## Control Center

- [x] `apps/vscode/` contains a reproducible TypeScript extension with a
  temporary development identity, lockfile, local build/test/package scripts,
  an AIO sidebar entry, and an explicitly opened Control Center.
- [x] The UI shows selected project, Core connection/version, last snapshot,
  Task inventory/detail/anomalies, existing filters, and ordered declared
  Workflow Stages and Roles labelled as definition rather than execution.
- [x] Valid Task YAML, complete four-artifact health, and Workflow resolution
  are visibly distinct, with truthful empty, loading, error, and stale states.
- [x] The extension supports exactly one selected local project per window and
  explicit multi-root choice, and rejects remote/WSL/container/web surfaces.
- [x] Restricted Mode command handlers prevent Python, project commands, hook
  setup, monitoring intake, and navigation while showing only safe explanatory
  state and static marker recognition.
- [x] Artifact opening resolves a host-owned identifier and rechecks containment;
  webview input cannot select executables, commands, hooks, or arbitrary paths.
- [ ] CSP, bundled resources, minimal local roots, safe text rendering, closed
  message validation, theme tokens, contrast, keyboard focus, narrow layout,
  and labels beyond color are verified.
  Static source checks and review cover the security controls and CSS
  declarations; runtime contrast, keyboard-focus behavior, and narrow-layout
  visual inspection remain pending. A guided-validation continuation prepared
  and installed the current package in an isolated profile. A later launch pass
  started the isolated VS Code process and renderer, but the single permitted
  post-launch computer-use inventory again exposed no native application
  surface; the owner-performed walkthrough is therefore still required.
- [x] No full project verification UI or terminal shortcut is added.

## Codex observation

- [x] The adapter uses only documented, explicitly enabled Codex lifecycle
  command hooks and never attaches to another client's private App Server.
- [x] Setup states exactly what is captured, destination, configuration change,
  trust review, enablement, and removal; implementation does not modify real
  user or project Codex configuration.
- [x] The installed observer applies bounded input and a fresh metadata allowlist
  before delivery, filters to the opted canonical root, and never persists or
  forwards the raw hook payload.
- [x] Prompt/response text, code/diffs, arguments/results, transcripts/paths,
  environment data, credentials, and headers are absent from retained events.
- [x] Neutral output is verified per registered event; failures and timeouts do
  not intentionally block, approve, deny, continue, prompt, or otherwise steer
  Codex.
- [x] Framed loopback intake binds only `127.0.0.1`, mutually authenticates a
  per-window secret over one connection, validates root/instance/lease/proofs,
  and enforces frame, identity, label, rate, replay, session, and timeline
  limits.
- [x] Secrets stay outside the webview/repository; descriptor and listener cleanup
  isolate windows and selected roots and do not affect Codex or other hooks.
- [x] Composite source/session/subagent identity, local receipt ordering,
  transport replay handling, legitimate repetition, restart isolation, weaker
  source-order guarantees, and no exactly-once claim are tested and documented.
- [x] Connection states distinguish not configured, configured/no observations,
  receiving, stale, disconnected, unsupported, and error; installation,
  connection, and activity remain different facts.
- [x] A session is never treated as an Actor, Task, Assignment, availability,
  approval, verification result, or governance state; turn completion never
  completes a Task.
- [x] Model is shown only when source-reported, reasoning is `not reported`, and
  no price, token, quota, rank, percentage, or fictional Agent data appears.
- [x] Synthetic/replayed fixtures are unmistakably labelled and excluded from
  live counts.

## Validation and packaging

- [x] Focused tests cover bridge requests/errors/bounds/scoping/provenance,
  malicious shadowing, external resources, and installed-Core behavior.
- [x] Focused extension tests cover rendering, selection changes, stale-response
  rejection, direct trust/consent enforcement, hostile text, forbidden actions,
  navigation, empty/error states, and no governance/engine-control paths.
- [x] Monitoring tests cover normalization, unsupported/malformed/oversized
  input, privacy, identity, repeats/reordering/replays, missing terminal events,
  disconnect/restart, limits/cleanup, neutral output, failure, idempotent setup
  and removal, unrelated configuration preservation, and unauthorized intake.
- [x] Existing Python tests, applicable schema validators, repository
  verification, Markdownlint, diff checks, extension type-check/build/unit
  tests, extension-host tests, and package-installation smoke tests pass or all
  failures/skips are accurately recorded.
- [x] A local development VSIX is built and inspected to exclude `.ai` evidence,
  secrets, sessions, home paths, Python checkout files, test/download/build
  caches, and unrelated documents while including required observer assets.
- [x] Wheel contents are inspected and exclude `apps/vscode` and extension build
  artifacts.
- [x] UI visual inspection and sanitized screenshots are recorded only if
  actually performed in an isolated Extension Development Host/profile.

## Live evidence and Human Control

- [ ] Authentic source-emitted events from an ordinary user-initiated Codex
  session reach the Control Center with correct project association, sensitive
  fields absent, truthful staleness, and observer-only disconnect behavior.
- [x] Live evidence is reported separately from synthetic fixtures with exact
  versions, categories, results, and any missing Human action or environment
  capability.
- [x] Separate Architect, Security Reviewer, and independent Reviewer outcomes
  have no unresolved blocking or high-severity findings.
  Final delta re-reviews approved the canonical-root, Core-compatibility,
  UNC-classification, Restricted Mode, and evidence-attribution remediations
  with zero remaining findings at any severity.
- [ ] Human approval is obtained before Task completion or any commit.
