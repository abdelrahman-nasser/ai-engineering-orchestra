# AIO-030 Review

Status: In Progress - Review Gates Passed; Live/Visual/Human Evidence Pending

## Baseline

- Starting commit: `5cca2fc5010defa2d789fb08795602c1ca038f55`.
- Starting worktree: clean.
- Local tracking evidence: `main` and the existing `origin/main` reference were
  aligned; no remote fetch was performed.
- AIO-029 baseline: Human approved 2026-09-19, 21/21 criteria complete.
- AIO-030 identity was available and this directory contains exactly the four
  canonical artifacts.

## Workflow Evidence

- Governing Workflow: `security-sensitive-change`.
- Effective gates: `documentation_consistency`, `independent_review`.
- Supplemental required reviews: Architect design review before implementation,
  Security Reviewer review, and independent Reviewer review.
- Human Control: stop at the review-stage checkpoint with `status: in_progress`.

## Design Review

Initial verdict: CHANGES REQUIRED

A separate Architect reviewed the pre-implementation lock at the highest
available reasoning setting and found four blockers: undefined multi-window
observer rendezvous, incomplete bridge wire/limit definitions, unsafe stale-port
claims, and collision-prone identity truncation. High-severity findings also
required exact freshness evidence and narrower support/neutrality claims.

The lock was corrected before implementation to define:

- a content-addressed standalone observer, fixed user-level hook command,
  bounded descriptor registry, most-specific-root selection, and same-root
  fan-out;
- exact closed `aio.ide/1` envelopes, error codes, sizes/counts/timeouts,
  duplicate-key rejection, exact-root preflight, duplicate Task-ID behavior,
  and selection-generation rejection;
- short renewable descriptor leases plus same-connection mutual HMAC over
  framed loopback TCP and the explicit same-user threat-model limitation;
- non-normalized opaque IDs, collision-free structural session keys, bounded
  replay memory, five-minute monotonic freshness, state evidence, root-change
  cleanup, Windows-only support, and event-specific neutral output.

Corrected-design verdict: APPROVE

The separate Architect re-reviewed the complete corrected lock and reported no
remaining blocker, high-, or medium-severity findings. This approval covers the
design lock; implementation, validation, and the later reviews are recorded
below.

## Implementation Architecture Review

Initial implementation verdict: CHANGES REQUIRED (0 blocker, 1 high, 2 medium)

The separate Architect's final implementation pass found that a canonical
workspace-root retarget during refresh could leave the prior observer active;
the extension host accepted only shallow Core result/version evidence; and UNC
roots reached a generic failure rather than an explicit unsupported state.

The remediation now stops and clears active and pending monitors before a
replacement canonical root is inspected or published, binds callbacks and
timer publication to the exact root/project/interpreter/lifecycle, resets
project filters, and requires fresh consent. The host accepts only Core
`0.1.0`, recursively validates closed operation-specific results and error
codes, and maps version mismatches to `incompatible`. UNC roots are rejected
before marker or Core access with explicit unsupported/incompatible state.
Controller-level Extension Host regressions cover these boundaries.

A follow-up implementation pass found that the transient snapshot root could
erase the last identity after a failed or overlapping refresh. The final delta
keeps a durable last-bound identity, re-canonicalizes after marker and Core
awaits (including failure paths), and exercises real temporary-junction races
for failure then retarget, overlapping A/B refreshes, and a post-Core retarget.
Restricted Mode stops prior observation while remaining marker-only. A retained
same-root observer can still publish truthful freshness after snapshot failure;
wrong-root and stale-lifecycle callbacks remain rejected. Response origin is
also verified before compatible-version and request-identity classification.

Final implementation architecture verdict: APPROVE (0 blocker, 0 high, 0
medium)

The Architect's final delta review confirmed that durable canonical-root
identity survives failure and overlapping refreshes, post-await
re-canonicalization prevents publication for a retargeted workspace, and old
observers are torn down before the replacement root is inspected or published.
It also confirmed recursive protocol validation, response-origin precedence,
explicit UNC rejection, Restricted Mode fail-closed behavior, and truthful
same-root freshness retention.

## Implementation and Validation Evidence

The completed implementation adds the one-shot `aio.ide/1` bridge, the local
development extension under `apps/vscode/`, the content-addressed Codex hook
observer, authenticated loopback collector, bounded Control Center views, a
safe external-project fixture, package inspections, and focused tests. Existing
CLI operations and domain schemas were not changed.

Final local validation on Windows x64 used VS Code `1.138.0`, OpenAI Codex
extension `26.908.40401`, bundled `codex-cli 0.154.0-alpha.6.2`, Node
`24.20.0`, npm `11.19.0`, Python `3.12.10`, and Core `0.1.0`:

- Focused bridge and packaging tests: 44 run, 41 passed, with three Windows
  symlink-privilege skips. Post-preflight Manifest redirect, late-entry,
  file-growth, and immutable-snapshot regressions ran and passed.
- Complete Python suite: 554 run, 547 passed, with seven documented skips: six
  unavailable Windows directory-symlink cases and one POSIX-signal-only case.
- Task validator: 47/47 cases passed; all 19 declared Task Workflow references
  resolved, including AIO-030.
- Canonical repository verification: 7 PASS, 0 FAIL, 0 ERROR, covering the full
  unit suite, Task/Workflow/Role/Manifest validators, Markdownlint, and diff
  checking.
- Installation smoke: editable and normal-wheel environments passed; the
  installed bridge worked from a hostile CWD; uninstall cleanup passed. The
  inspected wheel contains Core, packaged Roles/schemas, and the bridge, but no
  `apps/vscode` or extension output.
- Extension type-check and build passed. Unit tests reported 43 passed and one
  expected Windows-run skip for the opposite unsupported-platform branch.
  Real observer subprocess cases covered malformed types, injected read
  failure, privacy, neutrality, expired-registry saturation, nested roots, and
  fail-closed overflow. Direct monitor tests covered start/stop/renew races;
  direct-action unit tests covered Restricted Mode command gating.
- The isolated real VS Code Extension Development Host exited zero. Its direct
  controller tests deferred consent, installation, and monitor startup and
  proved Stop, root/interpreter change, and disposal cannot promote a stale
  listener. They also proved durable canonical-root retarget cleanup across
  failure, overlap, and post-Core races; root/lifecycle callback binding;
  same-root freshness; fresh consent; incompatible-version state; and UNC
  short-circuiting before marker/Core access. The new Restricted Mode teardown
  path is source-reviewed rather than attributed to this trusted Extension Host
  run. The disposable profile/extension directories were removed.
- Development VSIX packaging and strict inspection passed. The initial package
  contained 24 entries and 54,842 archive bytes with SHA-256
  `774aadca6a6aa7f279c1f3944f566ae1187ff25afdb89ad184321fca224760e7`.
  It is superseded by the guided-validation package recorded below.
  The expected development-only warnings were missing repository metadata and
  license; neither was invented or authorized. The observer pin matches
  `a36e1b645d302c1ef80d76de0835e17465b051a51b8b662a01fa6f08ad6cbaf5`.
- Direct Markdownlint covered 129 first-party Markdown files with zero issues.
  `git diff --check` passed; Git emitted only existing Windows LF-to-CRLF
  conversion notices for four tracked files.

Visual inspection was attempted in an isolated profile. The available
computer-use service exposed no native application surface, so no visual or
accessibility inspection and no screenshot are claimed. Static source checks
and review confirmed CSP construction, local resource roots, text-node
rendering, closed messages, theme-token/focus declarations, and a narrow-width
media rule; they did not execute DOM rendering, keyboard traversal, contrast
measurement, or a narrow-layout visual check. Those runtime accessibility
aspects remain pending.

## Guided Local Validation Preparation

On 2026-09-19, a continuation rechecked the unchanged baseline HEAD and the
complete uncommitted AIO-030 worktree without fetching, resetting, switching,
stashing, or overwriting source. The existing package predated the current
packaged README by 39 seconds, so it was rebuilt from the current worktree
rather than using evidence for the earlier archive. The build passed and strict
inspection confirmed 24 entries, 54,916 archive bytes, and SHA-256
`74f9731108e4b9db947a8176808a1f0149675b78f7011d0775eec81ba9405e65`.
All 22 workspace-mapped payload files byte-match the current source, and no
package input is newer than the resulting VSIX. The expected development-only
missing-repository and missing-license warnings remain unchanged.

A temporary validation area was prepared at
`%TEMP%\aio030-guided-validation-20260919-1815` without changing global
`PATH` or global packages. Standard PEP 517 build isolation downloaded the
declared build backend because the trusted base Python did not expose
`setuptools.build_meta`; runtime dependency installation then used cached
packages. The local Core wheel was built from this exact worktree with these
properties:

- file: `ai_engineering_orchestra-0.1.0-py3-none-any.whl`;
- size: 65,309 bytes; 43 archive entries;
- SHA-256:
  `24fc940467e679071bb5131dbf7a8a3727ebae6b78135dee5e3fc227ed9505e2`;
- embedded `engineering_orchestration/ide_bridge.py` SHA-256:
  `176c525962127a9455f2efc065cd6f0325f6a171c6c3e99400784ad8882d7fbf`,
  equal to the worktree bridge;
- no VS Code or Control Center artifact in the wheel.

The wheel was installed normally, not editably, into
`%TEMP%\aio030-guided-validation-20260919-1815\core-env` with Python
`3.12.10`. Package and bridge origins resolve under that environment's
`Lib\site-packages`; installed metadata records the exact wheel file URL and
wheel digest without editable `dir_info`. Core reports version `0.1.0`. A
deliberately incomplete first request was rejected as `invalid_request`, then
an exact `aio.ide/1` `project_snapshot` request with the required `status` and
`workflow` fields succeeded against the real managed repository and returned
29 current Tasks.

The rebuilt VSIX was installed through the discovered VS Code `1.138.0` CLI
into the new disposable directories
`%TEMP%\aio030-guided-validation-20260919-1815\vscode-profile` and
`%TEMP%\aio030-guided-validation-20260919-1815\vscode-extensions`.
The isolated extension inventory contains only
`aio-local-dev.aio-control-center-dev@0.0.1`; it does not contain Codex and no
authentication or everyday-profile data was copied. The documented live route
therefore uses an explicitly opted-in ordinary external Codex session whose
working directory is the same selected root.

The available computer-use inventory again returned no native application
surface. During that preparation step no VS Code window was launched for
unattended interaction, no runtime visual/accessibility scenario was claimed,
and no screenshot was captured. The packaged profile was ready for the later
launch pass recorded below. The coding agent did not open or modify real Codex
configuration, trust a hook, submit a prompt, or observe an authentic source
event. Official Codex hook documentation was rechecked and still requires
exact-definition review and hash-bound trust for an unmanaged hook.
Consequently both runtime criteria remain pending and the acceptance count
remains 40/43.

### Packaged UI Launch Pass

A subsequent authorized first visual-validation pass reverified, without
rebuilding, the current VSIX SHA-256
`74f9731108e4b9db947a8176808a1f0149675b78f7011d0775eec81ba9405e65`
and Core-wheel SHA-256
`24fc940467e679071bb5131dbf7a8a3727ebae6b78135dee5e3fc227ed9505e2`.
All prepared paths existed, and the isolated extension inventory still
contained only `aio-local-dev.aio-control-center-dev@0.0.1`.

The exact documented VS Code CLI launch using the prepared `--user-data-dir`,
`--extensions-dir`, and managed-project arguments returned exit code zero. A
read-only process check found the isolated parent and eight child processes,
including a renderer, all bound to that disposable profile. This proves the
prepared process launch, not visibility or dashboard state. No everyday VS Code
window was targeted, changed, or closed, and the test process was left running
for the owner.

The single post-launch computer-use inventory exposed no native applications
and therefore supplied no VS Code window, screenshot, or accessibility tree.
Workspace Trust was not observed or acted on; the Control Center was not
observed open; project/Python selection and Refresh were not performed; and no
dashboard, Task/detail/Workflow, navigation, theme, narrow-layout, keyboard,
focus, or trap check is claimed. Observation was not started, Codex
configuration was not accessed or modified, and no engine action occurred.
The visual/accessibility criterion remains pending and the count stays 40/43.

## Security Review

Initial verdict: CHANGES REQUIRED (0 blocker, 2 high, 1 medium)

The separate Security Reviewer reproduced a post-preflight project-boundary
escape and observation start/stop lifecycle races, and found malformed observer
event types could escape neutral failure handling. Remediation now captures one
bounded immutable project snapshot through verified handles; binds controller
consent/start and monitor publication to cancellable lifecycle generations;
owns pending monitors during Stop; and guards the observer's complete input
path. Adversarial regressions cover each issue.

Final verdict: APPROVE (0 blocker, 0 high, 0 medium, 0 low)

The Security Reviewer independently reran the 44-test focused Python slice and
the 32-test compiled extension slice, probed Windows junction escape and
post-capture retarget behavior, and reinspected all 24 VSIX entries. The review
confirmed the prior findings resolved and the security/privacy boundary sound
under the documented trusted-interpreter and same-OS-user assumptions. It does
not claim authentic Codex delivery, runtime accessibility, or Task completion.

Final-delta Security verdict: APPROVE (0 blocker, 0 high, 0 medium, 0 low)

The Security Reviewer independently reran the 44-test focused Python slice,
the final 44-test extension slice, the isolated Extension Host suite, and the
strict 24-entry VSIX inspection. The review confirmed the final root-identity,
protocol-origin, version-compatibility, UNC, and observation-lifecycle changes
preserve the documented security boundary. Authentic Codex delivery, runtime
visual/accessibility validation, and Human approval remain pending.

## Independent Review

Initial verdict: CHANGES REQUIRED (0 blocker, 1 high, 3 medium, 1 low)

The separate Reviewer confirmed the observation race and found stale Task
detail publication, stale project identity/filter state, incomplete registry
selection under expired-file saturation, and inaccurate VS Code runtime wording.
Those findings are remediated with independent detail/observation generations,
atomic state publication, project-scope reset, bounded cleanup plus fail-closed
registry overflow, direct interleaving tests, and corrected documentation. The
interpreter now also performs a non-importing package-origin preflight before
bridge execution.

Final verdict: APPROVE (0 blocker, 0 high, 0 medium, 0 low)

The independent Reviewer reran the focused Python and compiled extension
suites, isolated Extension Development Host, all eight event-specific neutral
failure paths, type-check, diff check, and VSIX inspection. Additional direct
controller probes confirmed Task ordering, atomic artifact publication, stale
marker rejection, project-scope clearing, and Restricted Mode enforcement.
The approval explicitly leaves authentic Codex delivery and runtime visual
accessibility pending and does not authorize a commit.

Final-delta independent verdict: APPROVE (0 blocker, 0 high, 0 medium, 0 low)

The independent Reviewer reran the final 44-test extension slice, isolated
Extension Host regressions, type-check, diff check, and strict VSIX inspection.
A separate direct-controller Restricted Mode probe confirmed marker-only
access, zero Core calls, prior-observer stop/disposal, and cleared canonical
state; that probe is not attributed to the trusted Extension Host run. The
review confirmed the final evidence attribution and both effective gates.

## Quality Gates

- `documentation_consistency`: PASS.
- `independent_review`: PASS.

## Live Monitoring Evidence

Status: NOT VERIFIED - MANDATORY CRITERION PENDING

Synthetic observer/transport events and a real isolated VS Code host validated
the implemented path, but they are not authentic Codex lifecycle evidence. No
real Codex configuration was changed, no hook was trusted with `/hooks`, and no
billed/model-backed turn was launched. The guided continuation has prepared a
normal isolated Core, installed the current VSIX in a disposable profile, and
launched that isolated process. The remaining owner actions are locating or
surfacing a window for that already-launched process, handling Workspace Trust,
opening the Control Center,
selecting the prepared interpreter, performing the visual/accessibility
walkthrough, starting observation, manually merging and trusting the generated
hook in the chosen user-level representation, initiating an ordinary external
Codex action in the selected root, checking live/stale/stop behavior, and
removing only the matching handlers. Until source-emitted events prove
association, privacy, staleness, and observer-only disconnect, this criterion
and full readiness remain pending.

An independent guided-evidence audit approved this continuation with zero
blocker, high-, medium-, or low-severity findings. It independently verified
the current VSIX and wheel identities and contents, normal non-editable install
provenance, installed bridge equality and protocol result, isolated extension
inventory, generic-path redaction, unchanged 40/43 count, and continued
`in_progress` status. It reconfirmed `documentation_consistency` and
`independent_review` as PASS; prior architecture and security approvals remain
retained because no implementation source changed.

## CLI-First Preservation Decision - 2026-09-19

On 2026-09-19, the owner chose CLI-first development and deferred further VS
Code feature development and manual/live validation. AIO-030 is preserved, not
discarded, on `feature/aio-030-vscode-control-center` in
`D:\Dev\ai-engineering-orchestra`. It remains `in_progress` at 40/43; runtime
visual/accessibility evidence, authentic Codex delivery, and Human product
approval remain pending. The prior review and Quality Gate evidence above is
retained with its original scope and does not establish the missing evidence.

One scoped local preservation checkpoint of the unfinished change set is
authorized. This action-specific exception to the earlier no-commit boundary
does not approve the implementation, waive a criterion, authorize another
commit, or authorize push, merge, publication, release, or Task completion.
CLI-first work is separated into `D:\Dev\ai-engineering-orchestra-cli` on
`feature/cli-developer-preview` at the accepted baseline
`5cca2fc5010defa2d789fb08795602c1ca038f55`; AIO-030 remains reserved for the
deferred extension.

The pause inspection found that `apps/vscode/tsconfig.json` still uses
`"module": "commonjs"` with legacy `"moduleResolution": "node"`. The
later-requested TypeScript module-resolution remediation was not performed, and
no post-remediation validation exists. Resumption must inspect then-current
branch evidence and local test-resource availability, address the unresolved
configuration deliberately, and rerun affected TypeScript, build, test, and
package validation before relying on it.

## Human Control

- Acceptance criteria: 40/43 complete. Runtime visual/accessibility evidence,
  authentic Codex event delivery, and Human approval remain pending.
- Human product approval: PENDING
- Task status: `in_progress`
- Preservation-only local checkpoint authorization: GRANTED on 2026-09-19 for
  one scoped AIO-030 checkpoint commit on
  `feature/aio-030-vscode-control-center`. This is not implementation approval
  and does not satisfy the pending Human-approval criterion.
- Additional commit, push, merge, publication, Marketplace, license, and
  AIO-031 authorization: NOT GRANTED
