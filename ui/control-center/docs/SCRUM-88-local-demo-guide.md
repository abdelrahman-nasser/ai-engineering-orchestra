# SCRUM 88 Guided Developer Alpha local demo

This five-minute walkthrough explains a fabricated Task through approval preview,
Run, Result and Journal evidence. Open **Guided developer demo** from Overview or
the sidebar. The existing route is `/application-v1-preview`; its detailed
Application v1 evidence panels remain below the guide.

All observations are synthetic. Option D remains active, S0 remains NO-GO and
operational integration remains deferred. No Core reader, provider invocation,
backend transport or execution/approval/cancellation/resume path is connected.
Moving between stops changes only the local presentation.

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

Open `http://localhost:4200/`, then choose **Open guided developer demo**.
Alternatively open `http://localhost:4200/application-v1-preview` directly.
This uses the installed dependencies; no installation is part of this guide.
The `--prebundle=false` flag avoids the existing Vite dependency-cache failure
seen in this workspace. Stop the server with Ctrl+C in its terminal.

## Repeatable five-stop demonstration

Keep **Interrupted lifecycle / recorded success** selected for the first pass.
Each stop can also be selected directly; the numbered controls are navigation,
not lifecycle transitions or a record of completed Workflow Stages.

1. **Task:** read the illustrative scope and exact selected Task, Run, operation
   and resource. The narrative is demo guidance, not rich Task definition data.
   Follow the evidence link to the existing dependency, scheduler and Run-history
   panel if needed. The selected scheduling subjects are advisory, not reservations
   or authority.
2. **Approval preview:** read the explicit nonauthorization notice and selected
   subject fields. This does not request or grant approval, create a Grant or
   consume authority. Approval count is unavailable, never zero. The exact Contract
   and Binding are in the existing lifecycle panel. Continue with **Next: Run**.
3. **Run:** compare the supplied interrupted state with its explanation. Expand
   the seven predefined state descriptions. They are an educational reference,
   not simulated state transitions. Failed-before-effect is limited to the
   operation's content effect; effect-ambiguous is terminal and blocks continuation
   and automatic replay. Human assessment is not an uncertainty override.
4. **Result:** observe the explicit null lifecycle-accepted Result identity and
   the separately recorded `succeeded` summary with zero bytes. No lifecycle
   promotion, Task completion or live Result reconstruction is inferred. Payload
   and historical content are unavailable. Follow the physical-identity evidence
   link if needed.
5. **Journal:** inspect coverage, stop reason and discrepancy. Open the detailed
   Journal panel for provenance, Entry/Admission/Grant metadata, physical identities
   and supplied reconciliation. No winner, repair or continuation eligibility is
   inferred. **Back to Task** restarts the guide without changing the scenario.

Use the numbered controls, **Previous stop** and **Next** to move through the
guide. Focus moves to the selected heading below the sticky header. Tab reaches
the evidence links and native disclosure; Enter activates them. Evidence links
focus the existing panel without leaving the current route. The scenario selector
can be changed at any stop and retains the current stop. Reload resets to Task
and the default scenario; no demo progress is persisted.

The **separate mock DAG / Nile workbench** link opens `/flow`, which reuses the
existing graph exploration controls. It uses separate mock models and does not
visualize the selected Application v1 observation or map Journal events into
Workflow Stages. Return through the sidebar's guided-demo link for a fresh guide.

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
`ui/control-center/.tmp/scrum-88-2026-10-20/`; do not include unrelated browser tabs,
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
Human acceptance and a separate commit decision remain required.
