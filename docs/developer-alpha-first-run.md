# Developer Alpha first-Run operator card

For ITRU **0.1.0a1** (framework **0.1.0**). This is a source-verified procedure,
not a newly executed walkthrough. Use it only with Human authorization for the
local workspace and actions. The documentation task did not execute these commands.
Run one command at a time and stop on an error before continuing. Use only the
new demo workspace and nonsecret sample below.

## 1. Prerequisites and existing package

Use **Windows x64 CPython 3.12**, PowerShell, and private current-user storage on
a fixed local NTFS volume. Shared, network and cloud-sync storage are unsupported;
workspace ancestors must be existing plain directories without reparse/symlink
aliases. Package metadata's Python `>=3.12` is not a broader Alpha support claim.

Obtain `itru-0.1.0a1-windows-py312-offline.zip` and its trusted build receipt/hash
from your maintainer. This checkout's existing copy is
`.tmp/itru-064-release/itru-0.1.0a1-windows-py312-offline.zip`; its receipt is
`.tmp/itru-064-release/build-receipt.json`. No public download URL is provided.
Without a trusted bundle/handoff, acquisition remains unresolved: stop there.
Do not build a release as a first-run setup step.

**Inspection:** in the ZIP's containing directory, compare this hash with the
independently trusted receipt before extracting to a new private directory:

```powershell
Get-FileHash -LiteralPath '.\itru-0.1.0a1-windows-py312-offline.zip' -Algorithm SHA256
```

Hash equality establishes integrity, not an authenticated signature. Check
extracted payload hashes against `SHA256SUMS.json`; stop on any mismatch. The
existing ZIP contains the older full guide, not this card; keep this card locally.

## 2. Install and inspect (no governed read yet)

Run from the extracted bundle directory. Keep this working directory for every
block below, and use a new `.venv`; activation is unnecessary.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps --find-links wheelhouse --require-hashes -r requirements.lock
.\.venv\Scripts\itru.exe --version
.\.venv\Scripts\itru.exe alpha --help
```

`requirements.lock` pins/hashes all wheels. Expected version: `itru 0.1.0a1`.
These are environment preparation and inspection commands; they do not run a
Task or test provider connectivity.

## 3. Prepare a new workspace and choose the provider

Choose an unused absolute path beneath an **existing**, approved local parent;
the example assumes `C:\Dev` already exists on supported storage. `init`
provisions real current-user authority registration, ledger, lifecycle Store
and Journal, plus a new repository and nonsecret input. It does not import an
existing project. **Preparation writes state even in demo mode.**

```powershell
$workspace = 'C:\Dev\itru-alpha-demo'
$cfg = Join-Path $workspace 'alpha.json'
.\.venv\Scripts\itru.exe alpha init $workspace
Get-Content -LiteralPath (Join-Path $workspace 'repository\input.txt')
Get-Content -LiteralPath (Join-Path $workspace 'example-work.json')
```

On success, `init` reports `initialized` and creates `alpha.json` and
`example-work.json`. Keep its generated workspace/identity fields and storage
locations unchanged. The generated provider object is sufficient for this run:

```json
{"kind":"demo","endpoint":"","model":"offline-demo","key_env":"","timeout_seconds":30}
```

The labelled offline demo performs **no inference** and needs no credentials.
For optional BYO inference instead, first follow the full guide's
[approved provider-object example](developer-alpha.md#configure-a-byo-provider).
Edit only `provider` in private `alpha.json`, using your actual compatible chat
endpoint/model and the **name** of a privately supplied process environment
variable. Never put a credential value in JSON, a pasted command or output.
HTTPS is required except explicit loopback HTTP; redirects/proxies are disabled.
BYO sends the objective and resource path, not file bytes: use nonsecret subjects.
`plan` neither calls the provider nor checks credential presence. Provider edits
invalidate earlier digests; obtain a new plan afterward.

**Current-checkout option:** when using a CLI from the authorized current
checkout, `itru alpha diagnose --config $cfg` provides a passive local check.
This is an optional aside, outside the installed-bundle command sequence above.
The existing offline ZIP predates `diagnose`; its executable cannot run this
command. Do not rebuild the bundle as a recovery step.
`configuration_valid` (exit 0) means only that local config validation passed
and any configured credential is present. Demo needs no credential or inference.
No provider request, work loading, owner acquisition, startup recovery, Run
registration or Tool invocation occurs. Diagnostics print no input values or
credential names/values. They do not establish connectivity, credential validity,
Human authorization, storage health or execution readiness. Stop on exit 2 and
follow its fixed `code`/`recovery`; keep generated workspace/identity fields intact.

## 4. Load explicit work and inspect the proposed plan

The generated `example-work.json` explicitly defines `read-a`, `read-b` and
`read-c`, each reading only `input.txt`; `read-c` depends on both others.
This is local Alpha work, separate from repository `task.yaml` inventory.
`load` writes immutable `work.json` and enrolls these Tasks; it initiates no Tool
read. Review the generated example before loading it.

```powershell
.\.venv\Scripts\itru.exe alpha load --config $cfg --work (Join-Path $workspace 'example-work.json')
Get-Content -LiteralPath (Join-Path $workspace 'work.json')
.\.venv\Scripts\itru.exe alpha plan --config $cfg
```

On a clean demo, the plan should report `approval_required`, selected IDs
`read-a`/`read-b`, two workers and serialized Tool execution. `read-c` is blocked
pending prerequisite governance closure. The JSON `approval` field binds the
current config, complete work, action, selected subjects and lifecycle snapshot.
Inspect local `alpha.json` and every `selected_subjects` entry's exact `task_id`,
`objective` and `resource`. The current checkout displays complete loaded strings
in `selected` order; it does not normalize or truncate them. If your terminal
clips long JSON, inspect the complete output before approving. **The existing
offline ZIP predates this preview:** if `selected_subjects` is absent, join every
selected ID to its exact objective and resource in `work.json`.

**Operational boundary:** `load`, `plan` and `history` open the lifecycle owner;
startup recovery can cancel pending Runs or mark running Runs interrupted.
`plan`/`history` are not passive preflight or recovery-free Control Center reads.
Stop for inspection if an unexpected existing history appears.

## 5. Human approval and governed execution

Only after reviewing the current subjects and deciding to authorize this exact
read, manually replace the quoted placeholder with the plan's current `approval`
value. Do not pipe plan output into execution or reuse approval after changes.
Any config, work or lifecycle change requires a fresh plan and Human review.
The preview leaves the approval subject, digest and explicit approval unchanged.

**This block initiates governed execution**, including BYO inference if configured:

```powershell
$approval = 'PASTE_THE_REVIEWED_CURRENT_APPROVAL_VALUE_HERE'
.\.venv\Scripts\itru.exe alpha run --config $cfg --approve $approval
$LASTEXITCODE
```

The Tool performs a bounded local repository-file read (maximum 64 KiB); advisory
model text has no Tool authority. Conditional success status:
`runs_succeeded_governance_pending`. Inspect each `results` entry's `outcome`,
`result_identity`, `byte_count`, `task_state` and `journal` receipt. These are
source-defined expectations, not a claimed successful transcript.

## 6. Inspect history; keep governance and recovery explicit

```powershell
.\.venv\Scripts\itru.exe alpha history --config $cfg
```

History reports Tasks, Runs and at most 100 Journal records. If `journal_more`
is true, manually copy its numeric `journal_after` for the next page:

```powershell
$after = 0 # Replace with the last response's journal_after value.
.\.venv\Scripts\itru.exe alpha history --config $cfg --after $after
```

Each invocation recaptures the high-water; this is not a frozen cross-command
traversal. Successful `read-a`/`read-b` Runs leave Tasks **`in_progress`** and
`read-c` blocked. Perform actual applicable governance/Quality Gates/review before
using the [separate Human completion walkthrough](developer-alpha.md#local-demo).
Completion requires its own exact plan, meaningful reference and fresh approval;
Run success alone does not complete Tasks or update repository Task files.

| Situation | Safe next step |
| --- | --- |
| Exit 0 | Command succeeded; still inspect its status and per-Run facts. |
| Exit 1 (`attention_required`) | Inspect every Result and Journal receipt. Journal failure can coexist with a successful original Tool Result. |
| Exit 2 (`rejected`/error), partial init/load or stale approval | Stop and inspect the reason/local state. Failed setup may leave resources; do not rerun init over the path, delete/relocate storage or assume rollback. Replan only after Human inspection resolves the cause. |
| Exit 130 / Ctrl+C, missing original Result or commit uncertainty | Treat effects as unresolved; inspect history deliberately. No automatic retry. Journal success cannot reconstruct or repair a missing lifecycle Result. |
| Busy owner | Do not seize ownership. `stop` cannot acquire another process's owner; coordinate with its Human operator. |
| `provider_credential_missing` / `provider_config_missing` / `provider_config_invalid` / `provider_unsupported` | Correct only the private provider setup using the manual, then rerun `diagnose`. Never paste credentials into JSON/output or switch adapters automatically. Config edits invalidate earlier approvals. |
| `provider_failed_before_tool` with `provider_diagnostic` | The provider worker failed before Tool invocation and the pending Run is cancelled. Inspect history deliberately; only eligible continuation may use a fresh resume plan and explicit Human approval. No automatic retry. |
| `human_approval_required` | Review a new exact plan and let the Human explicitly approve its digest. Provider credentials or passing diagnostics do not satisfy approval. |
| Interrupted or `effect_ambiguous` history | Cannot resume in this Alpha. Stop for Human inspection; do not replay, repair or infer no effect. |

Only Core-eligible history may continue with a separately reviewed fresh resume
plan/approval. Prior success alone is insufficient; dependency/capacity and the
whole Task history also matter. See
[restart, stop and continuation details](developer-alpha.md#explicit-work-approval-restart-and-history)
before any such action. A generic failure or missing Result never proves no effect.

For full work/config limits, recovery and provider details use the
[Alpha manual](developer-alpha.md). Remaining usability proposals are in the
[roadmap](developer-alpha-usability-roadmap.md), whose current disposition
distinguishes implemented slices from remaining proposals.
Static command/source verification and review are recorded
[separately](developer-alpha-first-run-review.md).
