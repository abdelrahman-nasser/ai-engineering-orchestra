# SCRUM 88 Guided Explorer local demo

Open **Guide** in the top bar or **Open Guided Explorer** on Overview or the
synthetic evidence page. The optional, non-modal panel explains a fabricated Task
through approval preview, Run, Result and Journal evidence while you browse any
Control Center page. The detailed Application v1 evidence remains at
`/application-v1-preview`, labeled **Synthetic evidence workspace** in the sidebar.

All observations are synthetic. Option D remains active, S0 remains NO-GO and
operational integration remains deferred. No Core reader, provider invocation,
backend transport or execution/approval/cancellation/resume path is connected.
Previous, Next and direct step selection change the explanation only. They do not
navigate, focus another part of the application or scroll its content. This
supersedes the checkpoint's route-local five-stop guide.

## Start locally

Use the current worktree location. Historical reports retain their original
paths as evidence; those paths are not the active workspace.

```powershell
Set-Location 'D:\Dev\ITRU\worktrees\itru-ui-integration\ui\control-center'
$env:NG_CLI_ANALYTICS = 'false'
$env:npm_config_offline = 'true'
$env:npm_config_update_notifier = 'false'
npm start -- --host 127.0.0.1 --port 4200 --prebundle=false
```

Open `http://localhost:4200/`, then choose **Open Guided Explorer**.
Alternatively open `http://localhost:4200/application-v1-preview` directly.
This uses the installed dependencies; no installation is part of this guide.
The `--prebundle=false` flag avoids the existing Vite dependency-cache failure
seen in this workspace. Stop the server with Ctrl+C in its terminal.

## Repeatable five-stop demonstration

Keep **Interrupted lifecycle / recorded success** selected for the first pass.
Each stop can also be selected directly through **Explore step**. These five
explanations are not lifecycle transitions or canonical Workflow Stages.

1. **Task:** read the illustrative scope and exact selected Task, Run, operation
   and resource. The narrative is demo guidance, not rich Task definition data.
   Use **Locate Section** to inspect the existing lifecycle, dependency and
   scheduler panel if needed. Selected scheduling subjects are advisory, not reservations
   or authority.
2. **Approval preview:** read the explicit nonauthorization notice and selected
   subject fields. This does not request or grant approval, create a Grant or
   consume authority. Approval count is unavailable, never zero. The exact Contract
   and Binding are in the existing lifecycle panel. **Locate Section** opens the
   exact Contract disclosure. Continue with **Next** when ready.
3. **Run:** compare the supplied interrupted state with its explanation. Expand
   the seven predefined state descriptions. They are an educational reference,
   not simulated state transitions. Failed-before-effect is limited to the
   operation's content effect; effect-ambiguous is terminal and blocks continuation
   and automatic replay. Human assessment is not an uncertainty override.
4. **Result:** observe the explicit null lifecycle-accepted Result identity and
   the separately recorded `succeeded` summary with zero bytes. No lifecycle
   promotion, Task completion or live Result reconstruction is inferred. Payload
   and historical content are unavailable. Follow the physical-identity evidence
   with **Locate Section** if needed.
5. **Journal:** inspect coverage, stop reason and discrepancy. Open the detailed
   Journal panel using **Locate Section** for provenance, Entry/Admission/Grant metadata, physical identities
   and supplied reconciliation. No winner, repair or continuation eligibility is
   inferred. Select **Task** in **Explore step** to revisit the beginning.

Use **Previous**, **Next** or **Explore step** without losing your place in the
application. **Locate Section** is the separate explicit navigation action: it
opens the corresponding existing synthetic section, scrolling and focusing that
section. On another route, it first opens the synthetic evidence workspace. Missing
Contract/Run details fall back to lifecycle status; missing Result details fall
back to Journal status, with an explicit unavailable-section announcement. Locate
uses instant scrolling, including under reduced-motion preferences.

The desktop guide reserves a side column and has an independently scrollable
explanation. On mobile it becomes a bottom guide occupying at most 52% of the
layout viewport, capped at 460px. Matching bottom space lets the end of page
content scroll above it. **Minimize** reduces it to a compact 64px bar; **Expand**
or the top-bar **Guide** button restores it. **Exit** dismisses it and returns
focus to the top-bar opener. There is no guide backdrop, body scroll lock, inert
background, focus trap or wheel/touch cancellation.

Opening the guide explicitly focuses its named scroll region without scrolling
the application. Tab can leave the panel normally. All guide controls remain
native buttons/selects. Focus on a mobile application text editor minimizes the
guide without taking focus away; editable visual-viewport changes account for
keyboard occlusion. Safe-area insets are reserved. Real on-screen keyboard and
touch-device behavior still need device verification.

The selected step and synthetic scenario survive minimize, exit/re-entry and
route changes in the same page session. The native selectors show those retained
values. Reload resets to Task/default and closes the guide; nothing is persisted.
The page's **Synthetic scenario** and panel's **Guide scenario** share the same
synthetic observation. Denial clears subject references in every view.

The **separate mock DAG / Nile workbench** link opens `/flow`, which reuses the
existing graph exploration controls. It uses separate mock models and does not
visualize the selected Application v1 observation or map Journal events into
Workflow Stages. The guide remains available while exploring that workbench;
its synthetic subject stays independent of the workbench's mock nodes.

## Scenario exploration

All 18 existing IDs and fixture meanings are preserved. The guide adds a short
observation prompt for each; it does not add fixtures or reinterpret outcomes.

| Selector choice | What to demonstrate |
| --- | --- |
| Interrupted lifecycle / recorded success | Separate lifecycle acceptance and recorded Result evidence. |
| Empty partial Journal page | An empty page does not establish absence, agreement or uniqueness; traversal is incomplete. |
| Successful Run / Task still in progress | Run success is separate from Task completion; latest means registration order. |
| Core over-capacity decision | Supplied capacity decision and disconnected pending consumer; no UI scheduling. |
| Complete traversal / no matching evidence | Absence is bounded to this Journal, subject and high water; invocation/effects may still exist. |
| Entry only | Entry does not establish completion or effect outcome. |
| Conflicting physical subjects | Both summaries and all four records remain separate; no winner. |
| Missing graph observation | Missing evidence is unresolved, not a negative observation. |
| Unavailable Journal | Independent lifecycle remains; no Journal records displayed. |
| Stale after busy refresh | Historical evidence and original times survive under continuing entitlement. |
| Entitlement revoked | Both observations and previously displayed subject references clear at every stop. |
| Incompatible source | No usable Journal data. |
| Invalid projection | No usable Journal prefix; independent lifecycle remains. |
| Expired inspection | Expired inspection context yields no Journal records; absence remains unproven. |
| Read budget exhausted | Read failure does not establish absence or continuation eligibility. |
| Run not found | No lifecycle subject is displayed. |
| Loading | No observation yet; loading is not a Run state. |
| Long synthetic identities and resource | Exact identities and lexical resource wrap, without normalization or truncation. |

For a compact second pass, stay on Result while choosing **Conflicting physical
subjects**, **Entry only**, **Stale after busy refresh** and **Entitlement revoked**.
Then choose Journal and compare **Empty partial Journal page** with **Complete
traversal / no matching evidence**. Revisit Run with **Successful Run / Task still
in progress**.

## Evidence capture and limitations

Capture only the localhost synthetic UI. Verify the synthetic source label,
scenario, theme, actual CSS viewport dimensions and selected stop in each receipt.
Keep screenshots and JSON observations locally under the ignored directory
`ui/control-center/.tmp/scrum-88-explorer-2026-10-20/`; the earlier checkpoint's
`scrum-88-2026-10-20/` receipts remain preserved. Do not include unrelated browser tabs,
credentials, real operational metadata or generated output in a proposed commit.
Reset temporary viewport overrides after QA. Public hosting, distribution or
uploading evidence requires separate authorization.

The demo has no connected execution or real authorization. Lifecycle examples do
not provide retry/resume eligibility. Journal traversal is a predefined snapshot,
not interactive pagination. The guide does not add rich Task metadata, a payload
viewer, configured routes or approval queue. These remain unavailable according
to the unchanged Application v1 contracts.

See the [October 20 QA report](SCRUM-88-guided-demo-qa-2026-10-20.md) for checks,
browser evidence, capture limitations, inherited lint findings and review verdicts.
The conditional local-checkpoint decision (approval comment 10744) and console
investigation are recorded there. Human product acceptance and SCRUM-88 closure
remain on hold; the checkpoint grants no publication or operational authority.

## Root cause and before versus after

The verified defect in checkpoint `2ad250b` was unconditional focus and
`scrollIntoView` on every explanation change, plus a guide destroyed when leaving
the preview route, with no minimize/exit. That forced navigation posture is
replaced by independent explanation controls and an explicit Locate action.
A literal website-wide overflow lock was not reproduced: body/document overflow
were visible and no guide modal or cancelling wheel/touch handler was present.
The QA report preserves the distinction and the browser input limitations rather
than attributing the report to a speculative global CSS rule.
