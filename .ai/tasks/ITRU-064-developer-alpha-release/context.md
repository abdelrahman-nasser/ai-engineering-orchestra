# ITRU-064 design lock

## Final Human release closure: COMPLETE

Human authorization in this conversation, recorded 2026-10-16:
APPROVE ITRU-064 FINAL HUMAN RELEASE CLOSURE ONLY.
H01 COMPLETE; G01 complete; acceptance 23/23; Task completed / CLOSED.
FQ-DC-1 documentation_consistency PASS, FQ-IR-1 independent_review PASS and
publication/artifact evidence readback PASS (3f5ec8) remain the retained basis.
The fresh 15/15 product-hash match, 122-test / 27-smoke history (zero skips),
clean install, Alpha smoke, two planning workers with SERIALIZED Tool execution,
5/5 specialist approvals and VERIFIED release artifacts remain current.
Unresolved B/H/M/L: 0/0/0/0. CLI-only Developer Alpha preserved; parked SCRUM-81
code used: NO. Only the same five existing Task evidence/status files change.
All frozen definitions, commands, read whitelists, criteria and historical
evidence below are retained verbatim; prior OPEN/pending statements describe
their earlier checkpoints and are superseded only by this closure record.
No validation, smoke, specialist review, final gate or artifact generation rerun;
no production, specification, test, config/provider, packaging or UI changes.
No staging, commit, amend, push, merge, rebase, reset, upload, publication or
post-Alpha work. No further authorization is needed for ITRU-064 closure.
Any further action requires a new explicitly scoped Human instruction.
STOP AT HUMAN CONTROL.

## Historical final-gate checkpoint (retained; superseded by closure above)

Current checkpoint: authorized locked final gates PASS. FQ-DC-1
documentation_consistency PASS, then FQ-IR-1 independent_review PASS.
G01 complete; acceptance 22/23; only H01 final Human release closure pending.
Task in_progress and OPEN; same-five-file publication readback PASS (3f5ec8).
Ready for final Human release closure YES; H01 requires separate authorization.
Current validation 122 tests / 27 smoke checks and 5/5 independent approvals
remain bound by the fresh exact 15-product hash match. Unresolved B/H/M/L 0/0/0/0.
Frozen definitions, commands, read whitelists and criteria below remain verbatim.
All NOT EXECUTED/future-authorization and 21/23 statements in the retained
pre-gate record below describe the earlier checkpoint or design-time procedure,
not the current gate outcome. This authorization covers locked gates only;
final Human release closure, Git actions and external publication remain absent.
Exact receipts and per-check evidence are in review.md/completion-report.md.
STOP AT HUMAN CONTROL.

## Historical pre-gate checkpoint and unchanged frozen lock

Current checkpoint: implementation and V1-V6 validation complete; all five fresh product
reviews APPROVE after SEC-M1 Medium remediation; specialist Task publication readback PASS. Current V1 22/V2 96/V3 4 passing tests
and V5 27/27 release smoke assertions; zero skips. Exact current fingerprints
and artifact hashes are retained in completion-report.md and generated receipts.
Acceptance 21/23, only G01/H01 pending. Ready for final gates YES, requiring
separate explicit Human authorization. Final gates frozen, NOT EXECUTED.
Task remains in_progress; Human closure pending. STOP AT HUMAN CONTROL.

Frozen before implementation, 2026-10-16. Baseline
905813a349b0a34248c9d719b27b05e88ca8cdc1 verified CLEAN; branch
itru-064-developer-alpha-release created. Human authorization is the supplied
SCRUM-21 request: design through evidence and fresh reviews, then Human stop.
No final gates or closure are authorized. Stop immediately on Blocker/High,
upstream semantic or migration change, material authority expansion, widening,
cross-branch transfer, parked code requirement, public publication, ambiguous
validation safety or any need to access workflows/README.md. Medium/Low within
this lock may be recorded, minimally fixed, revalidated and freshly reassessed.

## Frozen product decisions

1. Task directory: .ai/tasks/ITRU-064-developer-alpha-release/.
2. Exact write whitelist is below; no other tracked file edits.
3. Extend the existing flat itru package, retain its existing console entry point.
   Add alpha_config.py, alpha_provider.py, alpha_authority.py, developer_alpha.py
   and __main__.py. Package both unchanged SQL migration resource packages.
4. CLI: itru --version; itru alpha init DIRECTORY; alpha load, plan, run,
   resume, complete, stop and history, all with explicit --config; load takes
   --work; resume/complete/stop take --task; run/resume/complete take --approve.
   Existing tasks/inspect/verify retain behavior and are never invoked here.
5. Versioned closed JSON configuration pins workspace/project/runtime/environment,
   authorization domain/ledger/Journal/Store identities, repository and provider
   settings. Secrets are named environment variables, never serialized. Closed
   work JSON explicitly supplies bounded task IDs, objectives, lexical resource
   and dependency IDs. Reject duplicates, unknown fields, invalid paths/cycles.
   No repository discovery. Definition references hash complete work intent.
6. BYO boundary: explicit OpenAI-compatible HTTP chat JSON text adapter with
   endpoint/model/key-env/timeout configuration; HTTPS or loopback HTTP only,
   bounded response, no redirects, tools or model-derived authority. Offline
   demo adapter clearly identifies itself as deterministic fixture/no inference.
   Model text is advisory. Each worker plans one exact approved read task.
7. Example has two independent reads and one dependent read. init creates a NEW
   private local workspace/repository; never changes ACLs on an existing repo.
   Developers place inputs there and explicitly load work. No general shell tool.
8. Release 0.1.0a1 wheel plus SHA-256 manifest and offline wheelhouse zip. Build
   twice with fixed SOURCE_DATE_EPOCH; wheel bytes must match. Bundle dependency
   wheels fetched once if absent; offline install uses --no-index and hashes.
9. Composition: CLI -> explicit work DAG -> fresh complete scheduler snapshot ->
   Assignment handoff -> new Task/Run binding -> authenticated local current-user
   exact approval -> unchanged Grant/admission -> claim/JIT -> native reader ->
   original canonical Result -> unchanged Journal recorder -> lifecycle Result
   observation. Running marker commits before Tool invocation. Failure/unknown
   never becomes success. Successful Run does not close Task governance.
10. One process owns lifecycle and authority. At most two agent workers perform
    provider planning; registration is serialized under the owner, capacity and
    dependency revisions are rechecked. Upstream authority guard serializes Tool
    entry. This is bounded local worker concurrency, not parallel Tool effects.
11. plan emits a digest bound to current config/work, exact selected subjects and
    current Task revisions. run/resume/complete require exact fresh --approve.
    Approval is local control-plane caller intent under current OS identity;
    config, model output and durable receipts never authenticate approval.
    No unattended policy grant path. No approval token is a restored capability.
12. Opening the unchanged lifecycle Store performs conservative recovery.
    Resume only eligible prior attempts through its fresh request-bound adapter,
    new unique Run, new authority and fresh checkpoint; interrupted/ambiguous
    remains blocked without override. Never replay old claims/capabilities.
13. UI: CLI-only Alpha. No HTTP backend/API or UI mocks; no UI edits. Active
    baseline 0485a5f remains untouched; parked 61e817c is not read/transferred.
14. Validation matrix V1-V6 below covers each required scenario.
15. Clean install: fresh venv without system site packages, installed wheel and
    dependencies only, execution outside checkout, real installed console help,
    version, and isolated full CLI smoke with separate child processes.
16. Offline validation: --no-index --no-deps --require-hashes installation from
    explicit wheelhouse; compare two wheel builds and all bundle hashes.
17. Smoke: init/load/plan/approval rejection/run/history/process restart/complete/
    DAG advancement/two workers/safe resume/unsafe refusal. Fixture HTTP server
    implements BYO protocol without credentials or outside network. Native
    failure and ambiguity are fault-injected only by tests, never a CLI switch.
18. Fresh specialists: architecture/composition, authority/security,
    persistence/recovery, packaging/provider, process/docs. Read-only, at most
    two concurrent reviewer Agents, actual code and evidence, severity/verdict
    and exact product fingerprints. No final gate evaluation. Independent
    reassessment required after relevant remediation.
19. Acceptance is the exact numbered checklist in acceptance-criteria.md.
20. Completion report: completion-report.md in this Task directory.
21-23. Final gate procedures, commands, read whitelist and PASS/FAIL are frozen
    below NOW, and must NOT run during this cycle.

## Exact implementation whitelist

- .ai/tasks/ITRU-064-developer-alpha-release/task.yaml
- .ai/tasks/ITRU-064-developer-alpha-release/context.md
- .ai/tasks/ITRU-064-developer-alpha-release/acceptance-criteria.md
- .ai/tasks/ITRU-064-developer-alpha-release/review.md
- .ai/tasks/ITRU-064-developer-alpha-release/completion-report.md
- pyproject.toml
- itru/__init__.py
- itru/__main__.py
- itru/cli.py
- itru/alpha_config.py
- itru/alpha_provider.py
- itru/alpha_authority.py
- itru/developer_alpha.py
- tests/test_developer_alpha.py
- tests/test_alpha_provider.py
- scripts/build_developer_alpha.py
- scripts/validate_developer_alpha.py
- docs/developer-alpha.md
- examples/developer-alpha/work.json
- examples/developer-alpha/input.txt

Generated output only: .tmp/itru-064-release/ (build staging, wheelhouse, venvs,
receipts, artifacts). Tests may create only nonce-owned itru-064-* OS temp roots
and inherited upstream aio-053-local-trust-* roots; verify absolute containment,
plain descendants and owned prefix before recursive cleanup; verify absence.
No cleanup of user workspaces or operational registry. Validation redirects the
unchanged Windows registry location only in test processes to owned fixtures.

## Exact read and specialist review whitelist

All implementation paths above; AGENTS.md; .ai/project.yaml;
core/principles.md; core/terminology.md; core/precedence.md;
core/context-policy.md; core/human-control.md; core/task-specification.md;
core/task-run-state-specification.md; core/task-scheduler-specification.md;
core/agent-execution-result-specification.md;
core/agent-execution-journal-specification.md;
core/assignment-specification.md;
workflows/standard-change.yaml; roles/architect.yaml; roles/software-engineer.yaml;
roles/reviewer.yaml; roles/security-reviewer.yaml;
quality-gates/documentation-consistency.md; quality-gates/independent-review.md;
schemas/task.schema.json;
itru/task_dependency.py; itru/task_scheduler.py; itru/task_run_state.py;
itru/sqlite_task_run_state.py; itru/agent_execution_result.py;
itru/agent_execution_journal.py; itru/sqlite_agent_execution_journal_store.py;
itru/_execution_entry_and_controlled_invocation.py;
itru/_native_repository_file_read.py; itru/_jit_execution_attempt_authorization.py;
itru/_local_dispatch_claim_lease.py; itru/local_operational_trust.py;
itru/windows_local_authorization_domain_owner.py;
itru/agent_execution_authorization_grant_producer.py;
itru/agent_execution_dispatch_admission_store.py;
itru/sqlite_agent_execution_dispatch_admission_store.py;
itru/agent_execution_candidate_prerequisite.py;
itru/agent_execution_authorization_evidence.py;
itru/runtime_operation_capability.py; itru/environment_operation_permission.py;
itru/agent_execution_contract.py; itru/agent_execution_run.py;
itru/agent_operation_tool_binding.py; itru/agent_operation_tool_registry.py;
itru/agent_operation_tool_resolver.py; itru/authorization_domain_ownership.py;
itru/assignment.py; itru/operation_requirement.py;
tests/test_task_dependency.py; tests/test_task_scheduler.py;
tests/test_task_run_state.py; tests/test_sqlite_task_run_state.py;
tests/test_agent_execution_result.py; tests/test_agent_execution_journal.py;
tests/test_controlled_execution_result.py; tests/test_controlled_execution_journal.py;
tests/test_controlled_task_run_state.py; tests/test_local_operational_trust.py;
tests/test_jit_execution_attempt_authorization.py;
tests/test_dispatch_claim_lease_foundation.py;
tests/test_agent_execution_authorization_grant_producer.py;
tests/test_agent_action_prerequisite.py;
tests/test_durable_execution_entry_and_controlled_invocation.py.

Packaging may copy known itru package modules, schema JSON, canonical Role YAML,
and the two SQL migration packages as opaque package payload, without catalog
enumeration or reading any Markdown. Runtime imports may load their exact Python
dependencies and schema/Role resources. No Task/Workflow discovery is invoked.
Baseline upstream preservation uses git diff --name-only against the baseline,
not further upstream document traversal. No linked-path context expansion.

## Frozen validation and audit

Python P is exactly
C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe.
Working directory is D:\Dev\ai-engineering-orchestra. Before any test execute,
statically inspect its exact entry points/imported fixture operations for owned
paths, no operational registry, no external target invocation, no network except
the nonce-owned loopback HTTP server, and safe cleanup. No unsafe fixture suite
or broad unittest discovery. Exact commands (P denotes the above literal path):

```powershell
& $P -B -m unittest tests.test_developer_alpha tests.test_alpha_provider -v
& $P -B -m unittest tests.test_task_dependency tests.test_task_scheduler tests.test_task_run_state tests.test_sqlite_task_run_state tests.test_agent_execution_result tests.test_agent_execution_journal -v
& $P -B -m unittest tests.test_controlled_task_run_state -v
& $P -B scripts/build_developer_alpha.py --output .tmp/itru-064-release
& $P -B scripts/validate_developer_alpha.py --release .tmp/itru-064-release
git diff --check
```

V1=first command; V2=second; V3=third; V4=build; V5=release validation;
V6=diff check plus offline Draft202012Validator validation of this exact
task.yaml against schemas/task.schema.json, via yaml.safe_load and json.loads.
Set P literally once; no shell aliases or alternate test discovery. Capture
full outputs as retained receipts under the generated output directory. Build
dependency download is allowed only from Python package index, no upload; all
subsequent build/install/validation is offline. Build performs no target Tool.
PASS requires exit 0, zero failing/error/skipped tests, supported genuine Windows
native fixtures, clean-install and every smoke assertion, equal wheel bytes and
all SHA-256 matches. Any failure is recorded; repeat only affected validation
after remedy. Missing evidence is never PASS. These are implementation validation,
not final Quality Gates.

## Frozen FINAL QUALITY GATES: NOT EXECUTED

Both require later explicit Human authorization. No tests/build/install/new
reviews are included. The exact gate reads are bounded by this file's literal
inventories. Future gate operator uses P above for the hash command:

FQ-DC-1 command: `P -B scripts/build_developer_alpha.py --gate-manifest`
This read-only command prints SHA-256 for the 15 product paths (implementation
whitelist minus five Task files); it never builds/downloads/writes. Then read
exactly the 20 whitelist files and quality-gates/documentation-consistency.md
using `Get-Content -LiteralPath <each exact path> -Encoding utf8`.
No link traversal. DC01 hashes equal final validation/review manifest; DC02
CLI/config/provider/version/examples match code/artifact and documented limits;
DC03 authority/Result/Journal/state/DAG/resume/concurrency match unchanged upstream
boundaries; DC04 V1-V6 and install/reproducibility/smoke receipts are complete;
DC05 all five fresh approvals and finding dispositions bind current products;
DC06 acceptance and evidence agree, with only G01/H01 pending; DC07 no UI transfer,
upstream changes, staging/commit/publication or premature governance completion.
PASS iff all seven checks and commands pass with no material contradiction;
otherwise FAIL and stop without repair/expansion. Record each check separately.

FQ-IR-1 only after DC PASS: read exactly the five Task files and
quality-gates/independent-review.md with the same Get-Content command. IR01 five
distinct independent reviewers differ from implementer and inspect real files;
IR02 scope/acceptance and successful evidence covered on exact final fingerprints;
IR03 every finding disposition and required independent reassessment retained,
no unresolved Blocker/High or required unremedied changes; IR04 five explicit
APPROVE outcomes; IR05 DC PASS, Task in_progress, H01 pending. PASS iff all hold;
otherwise FAIL and stop. No self-approval substitution.

After later authorized gate PASS, update only five Task files, mark G01, reread
those exact five files; contradiction invalidates relevant gate. H01/closure
require separate Human decision. No Git mutation/publication in final gates.

## Literal final-gate command expansion (pre-review clarification)

PROC-M3: the design-time command shorthand is expanded here into literal runnable
PowerShell. This adds no read, check, action or authorization to the already
frozen procedures; their seven/five PASS/FAIL checks remain exact. No command
below has been executed. Fresh process/docs reassessment is required.

FQ-DC-1 literal commands, in order:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B scripts/build_developer_alpha.py --gate-manifest
$itru064DcFiles = @(
  '.ai/tasks/ITRU-064-developer-alpha-release/task.yaml',
  '.ai/tasks/ITRU-064-developer-alpha-release/context.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/acceptance-criteria.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/review.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/completion-report.md',
  'pyproject.toml',
  'itru/__init__.py',
  'itru/__main__.py',
  'itru/cli.py',
  'itru/alpha_config.py',
  'itru/alpha_provider.py',
  'itru/alpha_authority.py',
  'itru/developer_alpha.py',
  'tests/test_developer_alpha.py',
  'tests/test_alpha_provider.py',
  'scripts/build_developer_alpha.py',
  'scripts/validate_developer_alpha.py',
  'docs/developer-alpha.md',
  'examples/developer-alpha/work.json',
  'examples/developer-alpha/input.txt',
  'quality-gates/documentation-consistency.md'
)
foreach ($itru064File in $itru064DcFiles) {
  Get-Content -LiteralPath $itru064File -Encoding utf8 -ErrorAction Stop
}
```

FQ-IR-1 literal command, only after FQ-DC-1 PASS:

```powershell
$itru064IrFiles = @(
  '.ai/tasks/ITRU-064-developer-alpha-release/task.yaml',
  '.ai/tasks/ITRU-064-developer-alpha-release/context.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/acceptance-criteria.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/review.md',
  '.ai/tasks/ITRU-064-developer-alpha-release/completion-report.md',
  'quality-gates/independent-review.md'
)
foreach ($itru064File in $itru064IrFiles) {
  Get-Content -LiteralPath $itru064File -Encoding utf8 -ErrorAction Stop
}
```

Publication readback uses that exact IR command with its gate-definition path
omitted, after later authorized updates of only the same five Task files.
