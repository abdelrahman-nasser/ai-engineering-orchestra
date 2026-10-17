# Developer Alpha usability roadmap

## Current documentation disposition — October 17, 2026

The separately authorized [first-Run operator card](developer-alpha-first-run.md)
now documents the existing Alpha journey; it adds no CLI/runtime features.
The 31 feasibility artifacts are preserved in the
[quarantined evidence archive](architecture/control-center/evidence/README.md),
committed as `f287678b9709a9b04ac62b990361c0dcfb4374de` after independent review.
The [later Human authorization](architecture/control-center/human-decisions.md#october-17-2026--evidence-archival-and-first-run-documentation-authorization)
covers only that archive and this documentation slice. S0 remains closed at NO-GO.

Under a subsequent scoped Human authorization, the current checkout now adds
`selected_subjects` to the existing approval plan: exact Task ID, objective and
resource in selection order, without changing the approval subject or digest.
See the [Alpha guide](developer-alpha.md#explicit-work-approval-restart-and-history).
The existing offline ZIP predates this preview. Remaining proposed slices still
require separate authorization.

All remaining assessment text below is retained from the prior roadmap. Its
untracked-evidence and proposed-first-card statements describe that earlier
checkpoint and are superseded by this dated documentation disposition, as is
the assessment's missing-subject-display statement and preview proposal.

## Original assessment and proposals (historical checkpoint)

Date: October 17, 2026.
Status: assessment and proposed roadmap; implementation is not authorized.

The Human accepted **Option D - DEFER READER ADMISSION**. S0 is closed at NO-GO;
S1-S8, A/B redesign and transport selection are deferred. Core remains CLI-only
and Control Center remains mock-backed. The approved architecture and P07 limits
are unchanged. See the [Human decision](architecture/control-center/human-decisions.md).

Prioritize a developer's first successful governed local read Run using the
existing offline demo, followed by an explicitly configured BYO Provider. Improve
the current Alpha before considering new execution capabilities or integration.

## Assessment basis and limits

Source baseline: `19a321fc0876e73b9f83109f2a58528c9d54e331`, branch
`feature/control-center-s0-feasibility`. This is a static source, documentation,
configuration and test inspection. No installation, CLI command, provider call,
operational-store access, build or test was executed for this assessment. Test
names below describe existing coverage, not fresh PASS results. No user timing
or usability study was performed; friction priorities are engineering judgments.

Authoritative entry points:

- [Current Alpha guide](developer-alpha.md) and [Foundation README](../README.md).
- [CLI parser/router](../itru/cli.py), [Alpha composition](../itru/developer_alpha.py),
  [input validation](../itru/alpha_config.py), [provider adapter](../itru/alpha_provider.py)
  and [local authority composition](../itru/alpha_authority.py).
- [Work example](../examples/developer-alpha/work.json), [package metadata](../pyproject.toml)
  and [installed version](../itru/__init__.py).
- [Alpha tests](../tests/test_developer_alpha.py), [provider tests](../tests/test_alpha_provider.py),
  [CLI tests](../tests/test_cli.py), [packaging tests](../tests/test_packaging.py),
  [installation smoke source](../tests/package_installation_smoke.py),
  [bundle builder](../scripts/build_developer_alpha.py) and
  [release validator](../scripts/validate_developer_alpha.py).

## Verified capabilities and developer journey

| Stage | Existing behavior supported by source | Friction or missing convenience |
| --- | --- | --- |
| Installation/prerequisites | Local editable/normal installation and an offline hash-locked bundle already exist. Package requires Python >=3.12; controlled Alpha targets Windows CPython 3.12 on fixed private local NTFS. | README mixes the Foundation installation narrative with Alpha discovery and still describes installed code as 0.1.0; actual package/console version is 0.1.0a1. Package metadata alone is not a tested-platform matrix. |
| First-run setup | `alpha init <new-directory>` creates a new private workspace, repository/input, ledger, lifecycle Store, Journal, generated `alpha.json` and example work. Demo mode is explicitly labelled and performs no inference. | Guide requires venv activation after using explicit executables during install. No existing-repository import is provided. Setup performs real provisioning; it can leave partial resources if later steps fail. |
| BYO Provider | Closed provider object supports `demo` or compatible chat HTTP adapter, exact model/endpoint/env-key name and bounded timeout. HTTPS or explicit loopback HTTP; redirects/proxies disabled. Only objective/resource planning text is sent, without file content. | Credential presence is checked during provider work after Run registration. `alpha plan` does not invoke the provider. Execution collapses provider exceptions into `provider_failed_before_tool`, losing actionable distinctions. |
| Tasks/dependencies | Closed work JSON contains 1..100 explicit Tasks with exact IDs, objective, lexical repository-relative resource and dependencies; closed DAG validation rejects cycles/unknown endpoints/duplicates. Loaded definitions are immutable. | This work is distinct from repository `task.yaml` inventory. Changes require a new workspace; no editor/import/automatic catalog discovery. `load` writes work before per-Task enrollment, so atomic setup is not promised. |
| Planning/scheduler | `alpha plan` returns selected IDs, exact approval digest, Task/dependency evaluations, worker count and serialized Tool disclosure. Complete configured domain feeds Core scheduling. | JSON is detailed; developers must cross-read `work.json` for selected objectives/resources because the plan response does not display those subjects. No human-oriented explanation view exists. |
| Approval/execution | `alpha run --approve` checks the exact current config/work/snapshot digest. One or two advisory provider workers feed a serialized bounded native repository-file-read Tool, maximum 64 KiB. Fresh original Results are required. | Approval is intentionally manual. Success means a governed read Run, not file editing, shell execution or a general coding agent. Config/state changes invalidate old digests. |
| Results/history | Execution returns outcome, Result identity, byte count, advisory text, Task state and Journal receipt. `alpha history --after` returns Task/Run snapshots and at most 100 Journal records, with `journal_more`/`journal_after`. | Raw history is verbose. Journal high-water is recaptured across commands; this is not the deferred frozen application traversal or proof of passive reader admission. |
| Governance/continuation | Successful Runs leave Tasks `in_progress`. Separate planned/approved `complete --task --reference` attests actual Human governance closure. Fresh approved `resume` creates a new Run only for eligible history. | Run success versus Task completion needs stronger onboarding emphasis. Interrupted/effect-ambiguous history cannot resume. No command proves external Quality Gates or edits repository Task files. |
| Errors/troubleshooting | Alpha reports JSON rejection reasons on stderr; exit codes are 0 command success, 1 execution attention, 2 rejection/error and 130 interruption. `stop` takes Task/reference without `--approve`; concurrent ownership fails busy. | No structured troubleshooting map or static preflight command. `stop` cannot acquire another process's owner. Ctrl+C requires later inspection; generic errors must not invite automatic retry, repair or false no-effect conclusions. |
| Packaging/distribution | Builder creates two equal application wheels in its controlled build environment, locked wheelhouse, requirements hashes, payload manifest and local ZIP; validator contains clean-install/outside-checkout and loopback-provider checks. | Initial dependency download is network-capable and pins installed dependency versions; cross-host reproducibility is not established by two local builds. No public publication/support channel is supplied. Trusted bundle handoff needs clearer guidance. |

`alpha plan` and `alpha history` open the operational lifecycle owner and may
perform startup recovery. They are existing CLI operations, **not** recovery-free
Control Center read ports. Do not run them as a supposedly passive preflight.

The supported journey already exists:

`install -> init -> load -> inspect plan -> Human approval -> run -> history`

Dependency progress then requires actual governance closure, a fresh completion
plan/approval for each prerequisite, and a new plan before the dependent Run.
The CLI does not evaluate the truth of the Human's closure attestation.

## Prioritized, independently deliverable slices

S = small documentation/example change; M = bounded CLI behavior and focused
tests; L = multiple interacting contracts. Estimates are relative, not calendar
promises. Each slice below is a **proposal requiring separate Human scope and
validation authorization**. These names are not assigned Task IDs.

### P0 - Offline first-Run operator card (recommended first slice)

**Scope:** Add a short entry section to the existing Alpha guide and a discoverable
README link/version clarification. Reuse the existing guide and generated demo;
do not build an onboarding command or duplicate the full manual.

**Acceptance:** Explain framework 0.1.0 versus Alpha/package 0.1.0a1; identify
Windows/Python/private NTFS and trusted bundle prerequisites; use one explicit
venv executable convention throughout; show current init/load/plan/run/history
syntax and expected status/exit-code landmarks. Require the Human to inspect
selected Tasks, exact objectives/resources and current plan before copying the
digest. Mark demo as no inference, Run success as governance pending, and
plan/history as operational owner opens. Link the existing separate completion
walkthrough. Do not script automatic approval, completion, retry or cleanup.

**Dependencies/complexity:** Existing guide/parser/example; S. Documentation and
source review first. Any later executable walkthrough needs a separately
authorized disposable Windows fixture; this roadmap grants no such execution.

### P0 - Exact approval-subject preview

**Scope:** Propose a bounded plan view of selected objectives/resources alongside
existing exact approval subjects, reducing manual joins against `work.json`.

**Acceptance:** Preserve the approval binding and explicit Human action; display
exact resources/objectives without normalization or truncation presented as exact.
Handle oversized display explicitly. Show which config/work/lifecycle change
requires a fresh plan. No model output or preview becomes authority.

**Dependencies/complexity:** First-Run terminology; explicit CLI output/compatibility
decision; M. Future docs/examples and focused plan/approval tests must cover stale
digest, changed config/work/state, dependency blocking and no automatic dispatch.

### P0 - Actionable, sanitized provider failures

**Scope:** Preserve safe error categories through Alpha execution instead of only
`provider_failed_before_tool`; document supported adapter boundaries.

**Acceptance:** Distinguish missing environment variable, rejected configuration,
rejected response and request failure with bounded fixed codes/next steps. Never
expose key values, HTTP bodies, private exception text or claim a specific remote
cause that is unknown. Preserve cancellation-before-Tool behavior, explicit fresh
resume approval, no automatic retry/failover and existing Result authority.

**Dependencies/complexity:** Provider error contract and CLI compatibility review;
M. Update provider/config guidance and add focused missing-key, malformed-response,
redirect, tool-call, oversized-response and sanitized-error propagation tests using
owned loopback fixtures only under future authorization.

### P1 - Static configuration/work preflight

**Scope:** Design a clearly separate local input check before owner acquisition or
Run registration, reusing closed config/work validators and required-key presence.
The command name and output contract are not selected here.

**Acceptance:** No provider request, credential value output, provisioning,
recovery, registry mutation or Tool execution. Clearly state that syntactic input
validity/key presence does not prove provider connectivity, authority, storage
health or execution readiness. Do not relabel existing plan/history as passive.

**Dependencies/complexity:** Sanitized diagnostics and explicit command scope; M.
Future negative tests should use forbidden-operation guards and verify no owner,
network or Run creation; examples use only synthetic configuration.

### P1 - Setup and recovery troubleshooting

**Scope:** Document phase boundaries and actionable diagnostics for partial init,
partial load, immutable definitions, busy owner, interruption and commit uncertainty.
Automatic repair, rollback, deletion, relocation and retries remain out of scope.

**Acceptance:** Distinguish a new empty path from a partially created workspace;
do not advise rerunning init over it. Explain when to stop for Human inspection.
Provide the existing eligible-resume versus prohibited interrupted/ambiguous
decision table, Journal-success/lifecycle-interruption distinction and stop versus
Ctrl+C behavior. Never infer no effect from a missing Result or failed command.

**Dependencies/complexity:** First-Run guide plus source failure inventory; S for
docs, M for any later fixed diagnostic-code changes. Future tests inject setup/load
phase failures and confirm no hidden repair or changed commit/authority semantics.

### P1 - Planning and history presentation

**Scope:** First add an annotated JSON example and troubleshooting map; separately
consider an optional human view over unchanged Core facts/canonical JSON.

**Acceptance:** Explain dependency/capacity/unsafe/manual outcomes, governance
pending, original Result versus Journal attention, and existing `--after` paging.
Do not imply a frozen high-water across commands, recovery-free reads, cross-store
atomicity, current liveness or reconstructed authoritative Results. Preserve exact
identity access and stdout/stderr/exit-code compatibility.

**Dependencies/complexity:** Approval preview and diagnostic vocabulary; S example,
M optional presentation. Future tests cover blocked/missing domain, pagination,
Journal failure and lifecycle/Journal disagreement without changing Core policy.

### P1 - Local bundle handoff and validation alignment

**Scope:** Document existing trusted local bundle acquisition/verification,
consumer offline install versus maintainer build, and supported runtime. Do not
create a public download URL, publish a release or replace packaging.

**Acceptance:** Explain requirements.lock, SHA256SUMS and retained receipt identity;
hash equality is integrity evidence, not an authenticated signature. Disclose the
initial download and environment-derived dependency pins. Future builds must use
a separately authorized clean source inventory: builder staging copies `itru/*.py`,
so preserved untracked S0 modules must not accidentally ship. Do not delete them.

Review literal `{tasks,inspect,verify}` expectations in CLI/installation-smoke
source against the parser's additional `alpha` command. This is a source-observed
alignment concern, not a newly executed failure. Preserve historical release/Task
closure and obtain separate scope before changing tests or rebuilding.

**Dependencies/complexity:** Version/prerequisite guide; S documentation, M scoped
validation/test alignment. Only future authorized clean-venv/outside-checkout,
package-payload and loopback smoke execution can establish new installation evidence.

### P2 - Custom work examples and measured usability feedback

**Scope:** Add concise examples for one Task, a dependency pair, safe failed-before-
effect continuation and immutable-definition changes; then collect Human feedback
on the approved local journey. Improve help/navigation where evidence shows need.

**Acceptance:** Match the generated demo/work schema and lexical resource rules;
keep examples content-free and nonsecret. State that BYO planning sees objective
and resource, not file bytes. Separate fixture feedback from actual provider use;
never collect secrets or operational payloads. No existing-repository import,
multi-provider routing, auto-editing or general coding-agent loop is implied.

**Dependencies/complexity:** P0 terminology and P1 diagnostics; S-M. Future fixture
checks can compare examples with `validate_work` and test intended negative cases;
no tests or user-data collection are authorized by this document.

## Existing test evidence to preserve and extend

Alpha test source covers approval-before-effect, DAG governance completion, stale
approval/fresh resume, failed-before-effect continuation, ambiguous/interrupted
refusal, two advisory workers, provider failure before Tool, immutable work,
closed inputs/cycles, config changes, Journal failure and ledger mismatch.
Provider tests cover labelled demo, loopback wire shape, tool-call/redirect/size
rejection, missing key without network, endpoint policy and sanitized malformed
responses. Installation/release sources cover packaged payloads, offline install
and installed CLI behavior. They were inspected, not rerun here.

Future tests should verify changed user-visible contracts and authority boundaries,
not mirror formatting code. Do not run aggregate verification casually: `itru verify`
executes Manifest-declared commands with caller permissions, including potentially
network-capable tooling. `verify --structure` is the existing non-executing check
path, not an Alpha workspace/provider/authority readiness assessment.

## Human Control and evidence disposition

The current authorization records Option D and prepares this roadmap only. The
recommended first authorization is the **documentation-only offline first-Run
operator card**, with exact files and static review scope. Accepting this roadmap
does not authorize any later slice, test fixture, model call or release build.

Before each slice, Human approves its scope, commands/data if any, compatibility
and validation; independent review precedes final Human acceptance. Provider
access, native execution, operational workspaces and package handoff each retain
their existing authorization boundaries. No Task IDs are assigned here.

The general CLI, public distribution, full Provider Adapters and routing milestones
remain reserved by repository governance. Existing local Alpha capabilities do
not complete those broader milestones. No A/B redesign, transport/authentication,
Control Center connection, UI change or S1-S8 work follows from this roadmap.

All 31 S0/S0-R/S0-C artifacts remain untracked, unstaged and byte-preserved. A
separate Human archival decision should choose an explicit evidence inventory and
destination, preserve failed receipts and executed source hashes, and distinguish
experimental prototypes from product modules. No evidence is archived or committed
under the present documentation commit.

**STOP AT HUMAN CONTROL. Do not implement this roadmap automatically.**
