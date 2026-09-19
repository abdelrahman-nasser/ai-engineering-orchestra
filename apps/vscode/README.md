# AIO Control Center (Development)

This directory contains the local, experimental VS Code client for AI
Engineering Orchestra. The extension reads one explicitly selected managed
project through the installed Python Core and can observe a bounded subset of
local Codex lifecycle-hook metadata. It does not start, steer, approve, stop,
or otherwise control Codex.

The package identity `aio-control-center-dev` / `aio-local-dev` and version
`0.0.1` are temporary development values. They do not claim a registered
Marketplace publisher, a permanent product identity, or a chosen license. Do
not publish this package.

## Support boundary

- Local Windows desktop VS Code is the only supported host for this slice.
- The manifest compatibility floor is VS Code `^1.96.0`. AIO-030 development
  inspected VS Code `1.138.0` on Windows x64.
- The selected interpreter must be Python 3.12 or newer and contain a normal,
  non-editable installation of `ai-engineering-orchestra` `0.1.0` outside the
  selected project checkout.
- The observed source is `codex.lifecycle-hooks/v1`. The installed Codex
  metadata inspected for AIO-030 was IDE extension `26.908.40401` with bundled
  `codex-cli 0.154.0-alpha.6.2`; the hook payload itself does not identify
  whether the local event originated in the CLI or IDE surface.
- Remote SSH, WSL, Dev Containers, virtual workspaces, UNC roots, Codex desktop,
  and Codex cloud are not supported or claimed.
- Live monitoring remains unverified until a user explicitly installs and
  trusts the generated user hook, keeps the listener running, and produces an
  authentic lifecycle event from an ordinary Codex session in the selected
  root. Synthetic tests are not live evidence.

The implementation follows the current official
[Codex hooks documentation](https://learn.chatgpt.com/docs/hooks), including
user-level `hooks.json` discovery and hash-bound review through `/hooks`. It
does not attach to another extension's private process or start a
[Codex App Server](https://developers.openai.com/codex/app-server/).

## Build prerequisites

Use local project dependencies; no global npm package is required.

- Windows desktop
- VS Code compatible with `^1.96.0`
- Node.js and npm (the AIO-030 development environment used Node `24.20.0` and
  npm `11.19.0`)
- Python 3.12 or newer

From the repository root, create a normal Core installation in a virtual
environment outside the checkout. `pip install .` builds and installs a wheel;
do not use `pip install -e .` for the interpreter selected in the extension.

```powershell
$RepositoryRoot = (Get-Location).Path
$CoreEnvironment = Join-Path $env:LOCALAPPDATA "AIO-Control-Center\core-0.1.0"
py -3.12 -m venv $CoreEnvironment
$CorePython = Join-Path $CoreEnvironment "Scripts\python.exe"
& $CorePython -m pip install --upgrade pip
& $CorePython -m pip install $RepositoryRoot
& $CorePython -I -B -X utf8 -c "import importlib.metadata as m; print(m.version('ai-engineering-orchestra'))"
```

The final command must print `0.1.0`. Before importing the bridge, the extension
uses isolated Python startup to locate the installed Core package without
importing it, then rejects an origin inside the selected project. It checks the
reported origin again after the bridge exits. The selected interpreter and its
startup environment remain an explicit user trust decision; editable installs
are unsuitable for this boundary.

Install the locked JavaScript dependencies and run the focused commands:

```powershell
Set-Location (Join-Path $RepositoryRoot "apps\vscode")
npm ci
npm run typecheck
npm run build
npm run test:unit
npm run test:extension
npm run package:vsix
npm run inspect:vsix
```

`test:extension` uses the executable named by `AIO_TEST_VSCODE_EXECUTABLE` when
set; otherwise `@vscode/test-electron` resolves its default stable VS Code test
runtime and may download it into `.vscode-test/`. `package:vsix` creates the
local development archive in `dist/`; `inspect:vsix` checks a strict content
allowlist, required runtime assets, path leakage, common credential signatures,
and the observer's build-pinned SHA-256. None of these commands publishes or
installs the VSIX.

## Isolated Extension Development Host

Keep development data and extensions separate from the everyday VS Code
profile. From `apps/vscode/`:

```powershell
$ExtensionRoot = (Get-Location).Path
$ProfileRoot = Join-Path $env:TEMP "aio-control-center-vscode-profile"
$ExtensionsRoot = Join-Path $env:TEMP "aio-control-center-vscode-extensions"
$ManagedProject = "D:\path\to\a-managed-project"
code --user-data-dir $ProfileRoot --extensions-dir $ExtensionsRoot --extensionDevelopmentPath $ExtensionRoot $ManagedProject
```

Alternatively, install the built VSIX only into those disposable directories:

```powershell
$Vsix = Join-Path $ExtensionRoot "dist\aio-control-center-dev-0.0.1.vsix"
code --user-data-dir $ProfileRoot --extensions-dir $ExtensionsRoot --install-extension $Vsix
code --user-data-dir $ProfileRoot --extensions-dir $ExtensionsRoot $ManagedProject
```

Close every VS Code window using the disposable profile before deleting those
temporary directories. Do not install this development VSIX into the everyday
profile without a separate, explicit decision.

## Local dashboard walkthrough

1. Trust the Extension Development Host workspace only after reviewing it.
2. Run **AIO: Open Control Center** from the Command Palette or open the AIO
   Activity Bar container. The extension never forces the panel open.
3. Choose **Select project** and select the local folder that contains
   `.ai/project.yaml`. In a multi-root window this selection is explicit.
4. Choose **Select Python** and select the absolute `python.exe` stored in
   `$CorePython` above.
5. Refresh. The Project, Tasks, and Declared Workflow panels now come from the
   one-shot `aio.ide/1` bridge operations `project_snapshot` and `task_detail`.
   The Workflow panel is a definition, not current execution progress.
6. Inspect valid Task YAML separately from four-artifact completeness, inventory
   anomalies, empty filters, and managed/invalid/error states. Artifact links
   are host-owned identifiers; webview messages never supply arbitrary paths.

Restricted Mode shows only an explanatory shell and static project-marker
recognition. Selecting Python, launching Core, starting observation, copying
hook setup, and artifact navigation are enforced as unavailable by the
extension host until the workspace is trusted.

## Enable Codex observation manually

Workspace Trust does not consent to monitoring. Enabling the observer is a
second, explicit action, and the extension does not edit real Codex
configuration.

1. In a trusted local desktop window, select the project and installed Core
   interpreter as described above.
2. Choose **Start observing** and approve the confirmation. This starts an
   authenticated loopback listener for this window, writes a short-lived
   descriptor in extension global storage, and installs a content-addressed
   copy of the bundled observer there. It does not configure Codex.
3. Choose **Copy hook setup**. Review the displayed capture/exclusion notice and
   the exact generated commands. The copied text contains a JSON `hooks`
   fragment bound to the selected interpreter, installed observer path,
   registry path, owner, and observer SHA-256.
4. Manually open the user-level Codex file
   `%USERPROFILE%\.codex\hooks.json`. Extract the JSON fragment from the copied
   instructions (do not paste the surrounding explanation). If the file does
   not exist, create it as that JSON object. If it already exists, merge each
   copied event group into the corresponding `hooks` array without deleting,
   replacing, or reordering unrelated handlers. Do not paste a second top-level
   `hooks` key.
5. Use only one representation at this user layer. If user hooks are already
   inline in `%USERPROFILE%\.codex\config.toml`, merge an equivalent definition
   there instead of also creating `hooks.json`; Codex otherwise merges both and
   warns. Do not place this integration in the observed repository.
6. In the normal Codex session, run `/hooks`. Inspect the user source, exact
   absolute command, event list, one-second timeout, and hash. Explicitly trust
   it through Codex's normal review. Never use a trust-bypass flag.
7. Keep **Start observing** active and use a user-initiated ordinary Codex
   session whose working directory is the selected root or a descendant. AIO
   reports **Receiving observations** only after an authenticated source event
   arrives. Registration alone is **Configured, no observations**; no event is
   unknown, not idle. Five minutes of silence after receipt is **Stale**, not a
   claim that Codex stopped.

The allowlisted event categories are `SessionStart`, `SessionEnd`,
`SubagentStart`, `SubagentStop`, `PostToolUse`, `PostCompact`, `Stop`, and
`Interrupt`. A turn stopping is not a Task completing, a session ID is not an
AIO Actor ID, and root association does not create an Assignment.

### Disable or remove only this integration

To pause intake without changing Codex, choose **Stop observing**. The extension
removes its live descriptor, closes its listener, and clears its in-memory
timeline; it does not stop the Codex session. The content-addressed observer
copy can remain in extension global storage and is inert without a matching
live descriptor.

To disable a trusted handler while retaining its definition, use `/hooks` and
disable only the AIO handlers shown by the exact copied command. To remove the
integration permanently:

1. Choose **Copy hook setup** while the matching observer is active and retain
   the exact `command` and `commandWindows` values.
2. In `%USERPROFILE%\.codex\hooks.json` (or the one user-level representation
   chosen above), remove only handler objects whose `command` and
   `commandWindows` both exactly match those values. Preserve every unrelated
   hook and any concurrent edits. Delete an event group only if it becomes
   empty.
3. Save the file and use `/hooks` again to review the resulting configuration.
4. Choose **Stop observing** in every AIO window that was enabled.

Setting `[features] hooks = false` in Codex disables all hooks, including other
integrations, so it is not the removal procedure for AIO.

## Data and transport contract

The observer constructs a fresh record rather than forwarding the hook payload.
It may retain only:

- source and collector instance;
- random delivery ID and source session ID;
- optional source-reported turn, subagent, and tool-call IDs;
- event category;
- bounded tool label, subagent type, and model when supplied;
- selected-root fingerprint/association; and
- local receipt time and receipt sequence.

Reasoning settings and source timestamps are not supplied by this source and
are not inferred. Missing model data is displayed as **not reported**.

The observer discards prompts, assistant text, source code, diffs, tool
arguments/results, transcript contents and paths, command text, environment
dumps, credentials, request headers, and permission data. The incoming `cwd`
is used only to canonicalize and match an explicitly opted-in root; it is not
forwarded as event data. Raw payloads are never logged or persisted.

Delivery uses length-framed TCP bound to `127.0.0.1` with mutual HMAC proof on
the same connection. The random credential stays in an extension-owned
short-lived descriptor outside the webview and repository. Limits include a
64-KiB hook input/frame, 120 connection attempts per minute, 128 registry
entries scanned, at most 32 non-expired descriptor candidates and 32 bounded
expired-generation removals per hook, fail-closed overflow, fan-out to at most
four collectors for the same most-specific root, a 90-second descriptor lease
renewed every 30 seconds, 1,024 replay IDs,
200 in-memory events, and 20 displayed sessions. The same logged-in OS user is
the local trust boundary; protection from a malicious same-user process is out
of scope.

Session identity is composite: source, collector instance, selected-root
fingerprint, source session ID, and root/subagent scope. Local receipt sequence
is authoritative for display order. Delivery can be missing, repeated, or
reordered; the UI does not claim exactly-once delivery or infer termination
from silence.

The command observer has a one-second hook timeout and a 600-ms total network
budget. It is asynchronous where the event supports background hooks;
`SessionEnd` remains synchronous because Codex requires it. It emits only the
event-specific neutral result (`{}` plus a newline, or no output for
`SessionEnd`/`Interrupt`), always exits successfully, suppresses diagnostics,
and treats collection failure as lossy observation rather than an engine
decision. Stopping AIO affects only the observer connection.

No raw event spool, analytics database, telemetry service, remote font, CDN,
or cloud backend is used. State is bounded in memory and cleared when
observation stops, the selected root/interpreter changes, or the extension is
disposed.

The consented root and interpreter are captured with a lifecycle generation.
Stop, root/interpreter change, and disposal synchronously invalidate pending
startup and claim both pending and active listeners. Descriptor publication and
renewal use a second monitor lifecycle generation, preventing obsolete async
work from republishing after cleanup.

## Security notes

- The webview uses bundled local assets, a source-restricted Content
  Security Policy, theme tokens, and text-only rendering for external values.
- Webview actions are a closed set. Process launch, interpreter selection, hook
  guidance, project selection, and contained artifact resolution remain in the
  extension host.
- Core requests use argument arrays with no shell, isolated Python mode,
  bounded standard streams, a timeout, and an extension-owned working
  directory. A non-importing package-origin probe runs before the bridge;
  response origin is checked again before compatible-version and request-ID
  classification. Protocol, exact supported Core version `0.1.0`, recursively
  closed result shape, exact project root, and stale generations are also
  enforced at the host boundary. Version mismatches are shown as incompatible,
  not as a connected Core.
- The bridge is read-only. It exposes only project snapshot and Task detail;
  bounded, containment-checked inputs are copied into one ephemeral
  request-local snapshot before current readers run. There is no arbitrary
  function call, verification runner, project command, Agent launch,
  governance mutation, or session-control operation.
- The observer is installed from the VSIX into extension global storage and
  checked against a build-pinned SHA-256. It is never sourced from the selected
  project.
- Refresh keeps a durable last-bound canonical identity across ordinary snapshot
  failures and rechecks the selected folder after marker and Core awaits. If a
  junction or directory target changed, the old listener and pending startup
  are stopped, project-scoped state is cleared, and monitoring requires fresh
  consent before the replacement root can publish state.

## Known limitations

- The mandatory authentic live-event check is pending user hook installation,
  `/hooks` trust, and an ordinary user-initiated Codex lifecycle event.
- Hook events do not identify CLI versus IDE origin, provide a global sequence,
  or prove engine liveness between events.
- Same-user hostile-process resistance and remote filesystem identity are not
  provided.
- The extension does not run full project verification. Continue to use the
  existing reviewed CLI workflow separately when authorized.
- This development package has no publication, update, migration, or stable
  compatibility commitment.
