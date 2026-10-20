# ITRU-066 — Context

## Identity and authority

Canonical Task: `ITRU-066`; Jira: [SCRUM-89](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-89).
Title: Task-to-Evidence Integrity & Inspection UX.

The Human approved SCRUM-89 implementation, testing, durable documentation and
independent UX/accessibility and contract/evidence-integrity reviews on October
20, 2026. The subsequent conditional governance decision explicitly supplied
this ID and directory and authorized the four canonical Task files after a
collision check. No canonical identity was selected by the Agent.

Pre-creation searches of repository content (including hidden and ignored
project evidence, excluding Git internals, dependency/build/cache directories),
filenames, local Git refs and relevant all-ref documentation history found no
allocation, reservation or other Task reference to `ITRU-066`. This is local
repository evidence, not a claim about an unseen remote allocation registry.

The accepted [SCRUM-82 audit, comment 10755](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-82?focusedCommentId=10755)
and SCRUM-89 acceptance requirements govern this new work. Completed SCRUM-82,
SCRUM-84 and SCRUM-88 records remain historical and unchanged.

## Baseline and observed defects

Worktree: `D:/Dev/ITRU/worktrees/itru-ui-integration`.
Branch: `ui/control-center-integration-prep`; clean starting HEAD:
`f301d3785914ec6ff7cfd7d93103e5297815f74d`.
No applicable separate-branch mandate was found.

Chrome reproduced Task DEMO-102 selecting `run_a41c07e2`, then navigating to
dependency DEMO-101 while the old Run inspector falsely claimed DEMO-101 context.
Run `run_3c81f0a7`, event `Stage "implement" entered`, exposed zero supplied event
evidence but displayed three Run-wide records under a filtered-event label.
The audit also identified stale Flow query selection, lost Task filter context,
inspector/guide boundary focus loss, incomplete selection semantics and DAG
compression with the guide and inspector open.

## Boundaries and evidence

Option D and S0 NO-GO remain binding. All changes are UI-only and mock-backed;
no Core reader, transport, live provider or operational action is authorized.
All 18 Application v1 scenario meanings, contracts, decoders and disabled
operational controls must remain intact. The Task context summary composes the
existing rich mock models, separately from Application v1 synthetic observations.
Successful Runs establish neither Task completion nor Human acceptance.

The 320 CSS px DAG target is an initial usability threshold to investigate, not
a new architectural contract. Inherited ten Markdownlint findings remain failed
and unwaived. Physical-device, screen-reader speech, full WCAG and cross-browser
certification require explicit evidence and must not be inferred from DOM tests.

## Human control

Status is `in_progress`. Implementation validation and both independent reviews
are complete; `independent_review` and `documentation_consistency` pass as
recorded in `review.md`. Final Human acceptance remains pending. Leave all work
unstaged and uncommitted. No
Git checkpoint, Jira closure, release or publication is authorized.
