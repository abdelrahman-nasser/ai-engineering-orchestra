# ITRU-066 — Acceptance Criteria

## Identity and evidence

- [x] DEMO-102 → `run_a41c07e2` → DEMO-101 never associates the old Run with the new Task.
- [x] Task/Run selection is reconciled for parameter changes, loading, missing or failed reads, direct routes and browser history; regression tests prove exact current-subject consistency.
- [x] Selecting the `Stage "implement" entered` event of `run_3c81f0a7` shows an honest empty event-evidence state, separately from explicitly Run-wide evidence.
- [x] No evidence relationship, authority, completion or Human acceptance is fabricated or inferred.

## Navigation, interaction and context

- [x] Flow node/scenario query removal and restoration synchronize selection across Back/Forward and direct navigation.
- [x] Task filter → detail → Back restores the filter through explicit route/state ownership.
- [x] Closing DAG/timeline inspectors restores focus to a surviving meaningful trigger without forced viewport scrolling.
- [x] Guided Explorer Previous/Next boundaries retain logical focus and change explanations only; Locate remains the explicit navigation action.
- [x] Selection uses supported native interactions or complete accessible widget semantics.
- [x] DAG reflows using available container width with guide and inspector open; desktop and narrow widths are observed against the initial 320 CSS px usability target.
- [x] A compact read-only Task summary presents supplied scope, actor/role context, associated Runs, approval/review references and explicitly unavailable Human acceptance evidence.

## Preservation and verification

- [x] All 18 Application v1 meanings, approved contracts/decoders, non-modal guide behavior and disabled operational controls are preserved.
- [x] Option D/S0 NO-GO is preserved; no Core edits, operational transport/providers/actions or SCRUM-81 import occurs.
- [x] Focused regressions, complete UI suite, typecheck, production build and applicable scoped formatting/document lint are recorded accurately.
- [x] Chrome desktop/mobile-width and light/dark observations, before/after evidence and actual limitations are recorded in a durable implementation/QA report.
- [x] Ten inherited Markdownlint findings remain non-green unless independently corrected and verified within authorized scope.
- [x] `documentation_consistency` passes against actual final behavior and authoritative sources.
- [x] Independent UX/accessibility and contract/evidence-integrity reviews approve the final candidate, resolving material findings.
- [ ] Final Human acceptance is recorded before Task closure; work remains unstaged and uncommitted at this handoff.
