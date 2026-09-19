# AIO-030 Context

## Objective and baseline

AIO-030 changes the implementation priority from onboarding-only to a useful
dashboard plus one real, opt-in engine observation path. A developer should be
able to select one managed local project, inspect its actual Tasks and declared
Workflow, enable observation separately, and see allowlisted Codex lifecycle
metadata without AIO controlling Codex.

The implementation baseline is commit
`5cca2fc5010defa2d789fb08795602c1ca038f55`. Local `HEAD`, `main`, and the
existing `origin/main` tracking reference were aligned at that commit before
work began; no fetch was performed. The worktree was clean. AIO-029 was Human
approved on 2026-09-19 with 21/21 criteria recorded complete. AIO-030 did not
already exist, so this directory is the canonical new Task registration.

## Governing Workflow and supplemental reviews

The canonical `security-sensitive-change` Workflow governs this Task:

1. `understand`
2. `security-analysis` (`security-reviewer`)
3. `implement` (`software-engineer`)
4. `validate`
5. `review` (`reviewer`, `security-reviewer`, `independent_review`, Human
   Control checkpoint)

The Project adds `documentation_consistency`, making the effective gate set
exactly `documentation_consistency` and `independent_review`. No architecture
or security gate ID exists. A separate Architect design review and separate
Security Reviewer review are supplemental role evidence recorded here and in
`review.md`; they do not change Workflow choreography.

## Installed-surface investigation

The initial non-invasive inspection found:

- VS Code `1.138.0` on Windows x64.
- OpenAI Codex VS Code extension `26.908.40401`.
- Its bundled Codex CLI reports `codex-cli 0.154.0-alpha.6.2` and exposes the
  hook-trust option documented for lifecycle hooks.
- Node.js `24.20.0` and npm `11.19.0`.
- No supported Python interpreter was initially resolvable from `PATH`; an
  installed interpreter remains a user-selected Core-connection prerequisite.
- No installed Windows AppX package identified a separate Codex desktop app.
  Codex cloud account capability was not probed because it is not the selected
  local observation surface.

These are distinct surfaces. The implementation observes documented Codex
lifecycle command hooks used by a normal local Codex session. It does not
attach to the IDE extension's private App Server, start another App Server,
inspect desktop data, or treat cloud capability as local activity evidence.

Official release behavior is defined by the current OpenAI hooks documentation
at <https://learn.chatgpt.com/docs/hooks>. App Server documentation at
<https://developers.openai.com/codex/app-server/> describes a client/server
control protocol, but it does not establish a supported independent-observer
attachment to another client's private server, so AIO-030 does not use it.

## Design lock

### Supported source and event subset

The first source is `codex.lifecycle-hooks/v1`, implemented as a dependency-free
observer script bundled in the VSIX and copied to a content-addressed immutable
path under extension global storage. The user-level hook invokes it with the
absolute selected interpreter as
`python -I -B -S <observer> --registry <registry> --owner aio-control-center-dev/v1`.
The fixed, correctly quoted `command` and `commandWindows` values contain no
event interpolation. The allowlisted event categories are:

- `SessionStart`
- `SessionEnd`
- `SubagentStart`
- `SubagentStop`
- `PostToolUse`
- `PostCompact`
- `Stop`
- `Interrupt`

`UserPromptSubmit`, `PreToolUse`, and `PermissionRequest` are deliberately not
registered. Their prompt, tool-input, and control semantics are unnecessary for
the dashboard. A user-level registration means the observer transiently parses
bounded input from every local Codex session before rejecting roots that were
not explicitly opted in; this is disclosed before consent. It constructs a new
allowlisted record only after root matching and never forwards, logs, or
persists the raw payload.

Neutral output is locked per event contract. `SessionStart`, `SubagentStart`,
`SubagentStop`, `PostToolUse`, `PostCompact`, and `Stop` return `{}` with exit
zero and empty standard error. Advisory `SessionEnd` and `Interrupt` return zero
bytes on both output streams with exit zero. The observer never returns a
decision, continuation, approval, denial, replacement input, context, warning,
prompt, or tool result. Hooks use `async: true` where supported, an explicit
one-second hook timeout, and a shorter network deadline. `SessionEnd` remains
synchronous by Codex contract. Failures after observer startup still return the
neutral result; command-launch failures may be reported by Codex, so absolute
non-interference is not claimed. Observation is intentionally lossy.

### Core bridge

The one-shot bridge is
`python -I -B -X utf8 -m engineering_orchestration.ide_bridge`. Each invocation
accepts one JSON value on standard input and emits one JSON value on standard
output. Protocol `aio.ide/1` allowlists exactly:

- `project_snapshot`: resolve and validate one explicit selected project and
  return project state, Core metadata, Task inventory, anomalies, filter
  values, artifact health, and snapshot time.
- `task_detail`: resolve one exact declared Task ID in that project and return
  effective metadata with provenance, safe artifact descriptors, and ordered
  declared Workflow Stages and canonical required Role metadata.

The request envelope is a closed object with exactly `protocol`, `request_id`,
`operation`, `project_root`, and `payload`. `protocol` must equal `aio.ide/1`;
`request_id` is 1-64 ASCII alphanumeric, dot, underscore, or hyphen characters;
`project_root` is an existing absolute local path of at most 4096 characters.
`project_snapshot` payload contains exactly nullable `status` and `workflow`
filters. `task_detail` payload contains exactly one nonempty `task_id` of at
most 256 Unicode scalar values. Unknown fields, duplicate JSON object keys,
multiple/trailing JSON values, non-finite numbers, and invalid types are
rejected.

`project_snapshot.result` is a closed object containing `project` (`state`,
declared `id`, declared `name`), UTC `snapshot_at`, `tasks`, `anomalies`,
`filters`, and `validation`. Each Task summary contains declared `id`, `title`,
`type`, `status`, nullable declared `workflow`, `workflow_resolution`,
`schema_status`, four-artifact health, and a host-only opaque Task resource ID.
Filters contain only values present in the unfiltered valid inventory.
Anomalies and validation findings contain bounded code/status, host-owned
resource ID, and message; they contain no navigable path for the webview.

`task_detail.result` is a closed object containing a Task summary, effective
`risk`, `complexity`, and `execution_mode` each paired with its existing
provenance, effective Quality Gates, effective Human Control, four artifact
descriptors, and nullable declared Workflow detail. An artifact descriptor has
an opaque host-owned ID, fixed label, `present`/`missing`/`blocked` state, and a
host-only validated relative path. Workflow detail contains declared ID, name,
`definition_not_execution: true`, and ordered Stages; each Stage contains ID,
purpose, checkpoint flag, required gate IDs, and canonical required Role
records with ID, name, purpose, and required capabilities. No runtime progress
field exists.

A success response is a closed object containing `protocol`, `request_id`,
`ok: true`, `meta`, `result`, and bounded `diagnostics`; an error response uses
the same protocol and request identity with `ok: false`, `meta`, `error`, and
`diagnostics`. `meta` contains Core package version and origin for extension-host
verification. `error` contains one code and bounded message. For malformed
framing without a valid identity, `request_id` is `null`; the response protocol
remains `aio.ide/1` even when the incoming version is unsupported.

The closed bridge error codes are `invalid_json`, `invalid_request`,
`unsupported_protocol`, `unmanaged_project`, `invalid_project`,
`out_of_scope_resource`, `task_not_found`, `task_id_ambiguous`,
`invalid_catalog`, `resource_limit`, and `internal_error`. Missing interpreter,
missing Core, incompatible Core, timeout, oversized stdout/stderr, process
failure, and malformed response are extension-host errors because no conforming
bridge response exists in those cases.

Normative limits are 64 KiB request input, 2 MiB response/stdout, 16 KiB
diagnostic stderr, a 10-second host process timeout, 1 MiB for each YAML input,
1,000 immediate Task directories, 256 Workflow files, 100 diagnostics, and 512
characters per diagnostic. Limit overflow returns `resource_limit`; inventory
is never silently partial. Package origin and filesystem paths remain in the
extension host and are not forwarded to the webview.

Handled requests, including structured errors, exit zero with exactly the JSON
response on stdout and empty stderr. An unexpected failure is converted to a
bounded `internal_error` response when possible; a nonzero exit is reserved for
failure before a response can be serialized. If a candidate success response
would exceed 2 MiB, it is replaced by a bounded `resource_limit` error.

The bridge offers no verification runner, arbitrary callable, path reader,
command, Agent launch, or mutation operation. Existing CLI text output and
domain schemas remain unchanged.

The extension launches a user-selected trusted interpreter by absolute path,
with an argument array, `shell: false`, isolated imports, an extension-owned
working directory, a sanitized environment without `PYTHONPATH` or
`PYTHONHOME`, the limits above, and a timeout. Before importing the bridge, a
bounded isolated probe resolves the installed package without importing it;
an origin inside the selected project is rejected before project package code
can run. For structurally readable responses, the response origin is resolved
and compared again after execution before compatible-version and request-ID
classification. The host accepts exactly package version `0.1.0` for
`aio.ide/1`, recursively validates the closed operation-specific result, and
reports a version mismatch as an incompatible Core rather than a connected one.
The selected interpreter and its startup environment are still an explicit
user trust decision. Source/editable installs inside the observed checkout are
rejected by the product path and documented as a development limitation; tests
may call pure bridge functions directly. Request, project-selection, and Task
detail generations prevent late responses from replacing current state.

### Project boundary and selection

Exactly one existing local `file:` workspace-folder project is selected per VS
Code window. A multi-root workspace requires explicit folder selection; an
arbitrary folder outside the open workspace cannot be supplied. AIO-030 monitor
support is Windows local desktop only. Remote, WSL, container, web, UNC, and
mixed Windows/WSL path cases are affirmatively reported unsupported. A normal
local worktree is supported only when it is itself the selected workspace
folder and contains its own exact Manifest marker. Removed event CWDs, path
style mismatches, and paths that cannot be canonicalized are dropped before
retention.

The bridge performs an exact-root capture against only
`<selected-root>/.ai/project.yaml` and never walks upward. It canonicalizes and
containment-checks the Manifest, configured Task directory, every immediate
Task directory, all four canonical artifacts, `workflows/`, and every Workflow
YAML file, including symlink and junction targets. Bounded file-handle reads
verify regular-file identity, size, and post-open containment. One ephemeral
request-local snapshot receives only the captured Manifest, Task YAML,
canonical artifact-presence markers, and Workflow YAML; inventory, inspection,
Workflow resolution, and structural validation consume that immutable snapshot
instead of re-enumerating the selected project. Source-relative identities are
retained for safe artifact descriptors, and the snapshot is removed before the
one-shot process returns. Out-of-bound resources are reported; their contents
are not read or rewritten. Duplicate declared Task IDs are inventory anomalies;
`task_detail` returns `task_id_ambiguous` rather than choosing one.

In Restricted Mode, only the selected root label, explanatory UI, and narrowly
scoped `.ai/project.yaml` marker recognition are allowed. Python, project
commands, hook setup, listener startup, and event intake are rejected by the
command handlers. Workspace Trust is necessary but is not monitoring consent.

### Transport, consent, and setup

Monitoring starts only after a separate explicit user command. The extension
creates a per-window random collector identity and 256-bit secret, binds a
framed TCP listener to `127.0.0.1` on an ephemeral port, then atomically
publishes a versioned descriptor beneath extension global storage. The secret
never enters the webview or repository.

The static hook command points to a fixed registry directory. Each invocation
scans at most 128 entries, removes at most 32 owner-named expired descriptor
generations, and accepts at most 32 non-expired descriptor candidates. It
rejects malformed entries and fails closed if either bounded scan is partial,
so a later, more-specific root cannot be missed. Repeated hooks finish bounded
crash cleanup. From the complete candidate set it canonicalizes the event
`cwd`, selects the most-specific matching opted root, and fans out an event to
at most four live descriptors for an exactly equal root. Different roots and
windows retain separate collector identities, credentials, stores, and session
keys. Registry schema version, observer content hash, extension owner marker,
canonical root, loopback port, root fingerprint, collector identity, secret,
issuance time, and lease expiry are explicit descriptor fields.
An observer or interpreter upgrade requires regenerated setup instructions;
removal matches the owner marker plus exact observer hash/registry command and
removes only those AIO handlers.

Before any event metadata is sent, the observer and listener complete a
nonce/HMAC-SHA-256 mutual challenge over the same TCP connection. The event is
then framed, authenticated, acknowledged, and the connection closed. The
listener accepts no command, file, path, URL, or proxy request. A descriptor is
published only after listen succeeds, has a 90-second lease atomically renewed
every 30 seconds, and is required to be a regular non-symlink file under the
extension-owned directory with owner-restricted permissions where the platform
supports them. This protects against accidental stale-port delivery; a hostile
process running as the same OS user remains outside the threat model and is an
explicit limitation.

The bundled observer is installed with the extension rather than sourced from
the observed project and does not rely on `node` from `PATH` or a private OpenAI
extension binary. A user-mediated setup command displays or copies the exact
user-level hook registration and removal instructions. AIO-030 does not edit
the real Codex configuration and never uses the hook-trust bypass. Codex's own
hash-bound `/hooks` review remains required. Setup/removal helpers operate only
on disposable test fixtures, preserve unrelated hooks and concurrent changes,
and remove only the AIO registration they own.

Consent and startup are bound to the exact selected folder, canonical root,
trusted interpreter, project generation, and observation epoch shown in the
modal. Stop, root/interpreter change, or disposal invalidates that epoch
synchronously and claims both active and not-yet-started monitors. The monitor
also serializes start/stop and descriptor renewal under its own lifecycle epoch,
so an obsolete publication cannot recreate a listener or descriptor after Stop
finishes. Stopping observation removes AIO's descriptor, closes the listener,
and destroys accepted sockets. It leaves Codex and other hooks running. No
spool or durable event database is used.

### Intake allowlist, identity, ordering, and retention

Retained fields are limited to source ID, transport instance ID, delivery ID,
engine session ID, optional turn/subagent/tool-call IDs, event type, local
receipt time, selected-root association, bounded tool label, and source-reported
model when present. Model or reasoning data absent from the source is displayed
as `not reported`; the chosen hook source does not report a reasoning setting.

Prompts, assistant text, source code, diffs, command/tool arguments, tool
results, transcript and transcript paths, environment data, credentials, and
headers are discarded at intake and never retained. `permission_mode` is also
discarded because it is unnecessary and could be misconstrued as AIO authority.

Opaque session, turn, subagent, tool-call, delivery, and collector identifiers
are never trimmed, case-folded, Unicode-normalized, or truncated. Required IDs
over 512 Unicode scalar values are rejected; optional overlong IDs cause the
event to be rejected rather than collision-prone shortening. Only display labels
such as tool, agent type, and model are shortened to 128 scalars with an
explicit ellipsis marker.

The composite session key is a structural tuple of source, collector instance,
selected-root SHA-256 fingerprint, complete engine session ID, and complete
root/subagent identity; it is never delimiter-concatenated and is not an AIO
Actor ID. One delivery UUID is generated before fan-out. The listener
deduplicates `(collector_instance, delivery_id)` with a 1,024-entry LRU before
assigning receipt sequence; replays after eviction can reappear. Legitimate
repeated source events receive distinct delivery IDs. Collector receipt
sequence defines display order because this source documents neither source
sequence nor source timestamp and asynchronous hooks may arrive out of order.
Background delivery delay also means a newly received event can describe older
source activity. Exactly-once delivery and source ordering are not claimed.

Hook input and each transport frame are bounded to 64 KiB, intake to 120
accepted attempts per minute per listener, the in-memory timeline to 200 events,
and displayed sessions to 20. The descriptor is removed and memory cleared on
stop, selected-root change, interpreter change, or window disposal. A crash can
leave an owner-protected descriptor only until its short lease expires; mutual
authentication prevents an unrelated process that later receives the port from
receiving event metadata. The same-user threat-model limitation still applies.

### UI truth conditions

Setup evidence, listener health, and observed activity are separate facts. The
UI distinguishes:

- Project: managed, unmanaged, invalid, or error.
- Core: unconfigured, connected/versioned, missing, incompatible, or error.
- Codex observation: not configured, configured with no observations,
  receiving observations, stale observation, disconnected, unsupported, or
  error. Setup copied or user-confirmed remains explicitly `unverified`; AIO
  does not infer Codex registration or trust.

`receiving observations` requires an accepted authenticated source event for
the current listener and selected canonical root. Listener registration or hook
configuration alone is not a live connection. `stale` means only that five
minutes elapsed on the extension host's monotonic clock since the last accepted
event; rejected, replayed, and rate-limited attempts do not refresh it. It is
not an idle or ended engine claim. `disconnected` means only that AIO's listener
stopped or failed, never Codex silence. `unsupported` requires affirmative
platform/version evidence. No event means unknown/no observations. A turn
ending does not mean a session or AIO Task ended.

Changing the selected root resets project identity, Core, filters, and Task
detail. Changing either the root or interpreter removes the prior descriptor,
closes the listener, destroys sockets, clears retained events and replay state,
rotates credentials, increments the project/detail/observation generations,
invalidates in-flight Core work, and requires fresh monitoring consent.
Refresh also compares the newly resolved canonical root with a durable prior
bound identity that survives ordinary snapshot failure, then re-canonicalizes
after marker and Core awaits. A junction or directory retarget is handled as a
root change before the replacement snapshot can publish; stale callbacks remain
bound to their original root and observation lifecycle. A retained same-root
observer may continue publishing connection/freshness state after a Core
snapshot error, while new Task access and new observation starts stay blocked
until a current valid snapshot restores the transient eligible root.

The source is labelled **local Codex lifecycle hooks** because hook payloads do
not identify whether CLI or IDE emitted them. A live test may separately record
the initiating surface, but the adapter does not infer it. The selected Task is
display context only. Observed sessions never create an
Actor, Assignment, availability record, approval, verification result, Task
progress, or Task completion. Synthetic test fixtures are labelled synthetic
and are never included in live UI counts.

### Webview and accessibility

The webview uses bundled HTML/CSS/JavaScript, VS Code theme tokens, a restrictive
Content Security Policy, minimal local resource roots, text-node rendering for
untrusted values, keyboard-operable native controls, visible focus, and labels
plus text in addition to color. Incoming messages use a closed action union.
The host owns project selection, interpreter selection, hook guidance, process
launching, listener lifecycle, and artifact maps; the webview supplies no paths
or executables and has no Node privileges.

## Live-validation boundary

Synthetic and extension-host validation can prove normalization, security,
rendering, transport, and lifecycle behavior. Full live acceptance additionally
requires the Human to install the development VSIX into an isolated profile,
select an installed Core interpreter, approve the exact hook registration in a
disposable Codex profile, and initiate an ordinary Codex session. This Task does
not make those real configuration changes or launch a billed/model-backed turn.
Until authentic events are observed, live monitoring remains explicitly
unverified and full AIO-030 readiness remains pending at Human Control.

## CLI-first preservation pause (2026-09-19)

On 2026-09-19, the owner chose CLI-first development and deferred further VS
Code feature development and manual/live validation. AIO-030 is preserved, not
discarded, and remains `in_progress` with 40/43 criteria complete. Runtime
visual/accessibility evidence, authentic Codex delivery, and final Human product
approval remain pending.

The owner authorized one scoped local preservation checkpoint on
`feature/aio-030-vscode-control-center` in
`D:\Dev\ai-engineering-orchestra`. This action-specific exception permits the
unfinished change set to be saved locally; it does not approve the
implementation, satisfy or waive pending criteria, or authorize another
commit, push, merge, publication, release, or Task completion.

CLI-first work is separated into the linked working folder
`D:\Dev\ai-engineering-orchestra-cli` on
`feature/cli-developer-preview`, starting from the accepted baseline
`5cca2fc5010defa2d789fb08795602c1ca038f55`. AIO-030 remains reserved for the
deferred extension across both branches.

Inspection at the pause found that `apps/vscode/tsconfig.json` still declares
`"module": "commonjs"` with legacy `"moduleResolution": "node"`. The
later-requested TypeScript module-resolution remediation was not performed, and
no post-remediation validation exists. Earlier type-check and build evidence is
retained only for the configuration under which it ran. Resumption requires
checking the preservation branch's then-current evidence, confirming whether
prior ignored local test resources remain available, addressing the unresolved
configuration deliberately, and revalidating the affected TypeScript, build,
test, and package artifacts before relying on them.
