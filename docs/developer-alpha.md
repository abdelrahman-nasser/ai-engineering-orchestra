# ITRU Developer Alpha 0.1.0a1

This local Windows/Python 3.12 Alpha runs explicit read workflows using your
configured model. Its controlled Tool is the bounded native repository file
reader (maximum 64 KiB). Model plans are advisory text. Task governance completion
is a separate explicit Human action after a successful Run.

Use a fixed local NTFS volume and private current-user storage. Shared, network,
cloud-sync and distributed storage are unsupported. init creates a new private
workspace and repository; place only files you intend to inspect inside it.
The Alpha does not run shell commands, edit source files, or implement general
coding-agent loops. Existing Foundation inspection commands remain available.
One or two local agent workers plan approved Tasks; the existing authority guard
serializes controlled Tool execution. There are no distributed workers or
automatic retries, routing or failover.

## Install and offline integrity

Unzip itru-0.1.0a1-windows-py312-offline.zip. In that directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps --find-links wheelhouse --require-hashes -r requirements.lock
.\.venv\Scripts\itru.exe --version
.\.venv\Scripts\itru.exe alpha --help
```

requirements.lock pins and hashes every wheel, including dependencies. Verify
other bundle payload against SHA256SUMS.json. The retained build receipt binds
the bundle hash. The bundle targets Windows CPython 3.12; the application wheel
contains platform-independent Python, but controlled execution needs Windows.
No package publication or upload has occurred.

## Local demo

Use an absolute NEW directory. Activate the venv above to put itru on PATH.

```powershell
itru alpha init C:\Dev\itru-alpha-demo
$cfg = 'C:\Dev\itru-alpha-demo\alpha.json'
itru alpha load --config $cfg --work C:\Dev\itru-alpha-demo\example-work.json
itru alpha plan --config $cfg
```

init defaults to an explicitly labelled deterministic offline demo adapter,
which performs no model inference. Inspect plan JSON and the exact selected
resources/objectives in work.json. To approve these current subjects, copy the
approval digest from plan and invoke:

```powershell
itru alpha run --config $cfg --approve <digest-from-plan>
itru alpha history --config $cfg
```

read-a and read-b run with two advisory workers. Successful Runs leave both Tasks
in_progress. read-c remains dependency-blocked. After you have satisfied every
applicable Task governance/Quality Gate/review requirement, explicitly attest
that closure with a meaningful reference:

```powershell
itru alpha plan --config $cfg --action complete --task read-a --reference human-demo-closure-a
itru alpha complete --config $cfg --task read-a --reference human-demo-closure-a --approve <new-digest>
itru alpha plan --config $cfg --action complete --task read-b --reference human-demo-closure-b
itru alpha complete --config $cfg --task read-b --reference human-demo-closure-b --approve <new-digest>
itru alpha plan --config $cfg
itru alpha run --config $cfg --approve <new-digest>
itru alpha history --config $cfg
```

The Store checks lifecycle eligibility; it does not evaluate external governance
or prove the truth of your closure attestation. The CLI does not close repository
task.yaml files. Explicit loaded-work operational states are the Store's facts.

## Configure a BYO Provider

Edit only the provider object in private alpha.json before obtaining a new plan.
All fields are required; no extra fields or credential values are accepted:

```json
{"kind":"compatible","endpoint":"https://your-provider.example/v1/chat/completions","model":"your-model-id","key_env":"ITRU_MODEL_KEY","timeout_seconds":30}
```

Set ITRU_MODEL_KEY in your process environment. Use your Provider's actual
OpenAI-compatible chat endpoint and model identifier. HTTPS is required except
for explicit loopback HTTP development endpoints. Redirects and inherited HTTP
proxies are disabled. An empty key_env supports local credential-free models.
The adapter sends only objective/resource planning text, not file content. It
accepts bounded text responses; tool calls are rejected. Provider-specific
authentication/protocol differences require another adapter, not Core changes.
The local smoke uses a fixture HTTP server and no paid external inference.

alpha.json format_version is 1. It pins the exact absolute workspace and immutable
project/runtime/environment/domain/ledger/Journal/Store identities. Do not edit
these identity fields or relocate storage. max_concurrency is exactly 1 or 2.
The provider object is mutable between commands and invalidates old plan digests.
Configuration and work inputs are bounded to 1 MiB and reject duplicate keys.

## Explicit work, approval, restart and history

examples/developer-alpha/work.json shows the closed work format: format_version
and tasks; each Task has id, objective, resource and dependencies. IDs are exact
and case-sensitive, dependencies form a closed DAG, and resources use lexical
repository-relative paths. At most 100 Tasks may be explicitly loaded. A loaded
definition is immutable; use a new workspace for changed work. No Task or Workflow
catalog is discovered. The embedded Alpha workflow binds standard-change,
implement, software-engineer and its explicitly configured reader Actor.

The Human caller's --approve digest attests the exact current config, work,
subjects and lifecycle revisions. It is not a secret credential or saved
capability. Only the current OS user within this private local trust boundary
can supply control-plane intent. Model/config/Journals never supply approval.
No unattended policy-grant mode exists. Every invocation requires a new Run,
fresh authenticated proofs, admission, claim and JIT checks. Reusing an old
digest after state changes fails. Terminal evidence cannot dispatch work.

Each command opens and closes the process-owned Store. On restart, pending Runs
recover as cancelled and running Runs as interrupted. History preserves these
facts; a recorded Journal success cannot repair a missing original lifecycle
Result. Interrupted and effect_ambiguous Tasks cannot resume in this version.
Eligible succeeded, failed_before_effect or cancelled-before-start history can
continue only with explicit fresh approval:

```powershell
itru alpha plan --config $cfg --action resume --task read-a
itru alpha resume --config $cfg --task read-a --approve <new-digest>
```

There is no automatic restart/retry. `alpha stop --config $cfg --task <id>
--reference <reason>` conservatively stops an unfinished attempt when the Store
is available. A concurrent owner fails busy. To interrupt the active process,
use Ctrl+C and inspect history afterward. Commit uncertainty or missing Results
require inspection; never infer no effect or repeat automatically.

history returns explicit enrolled Tasks/Run snapshots and at most 100 Journal
records. Use `--after <journal_after>` to request subsequent records while
journal_more is true. Journal summaries exclude file content and cannot recreate
authoritative Results. Execution output reports canonical outcome, byte count,
physical Result identity and Journal receipt. A Journal failure is visible as
attention_required even if the original Tool Result succeeded; no success is
fabricated or reconstructed. Exit codes: 0 command success (including plans),
1 attention required after execution, 2 rejection/error, 130 interruption.

## Reproduce the local release

From the authorized repository checkout using Python 3.12:

```powershell
python -B scripts/build_developer_alpha.py --output .tmp/itru-064-release
python -B scripts/validate_developer_alpha.py --release .tmp/itru-064-release
```

The first build downloads pinned public dependency/build wheels once; later
build and install steps are offline. Two isolated builds use a fixed timestamp
and must produce identical application wheels. The validation creates a fresh
venv without system packages, verifies package RECORD/payload hashes, and runs
installed CLI subprocesses outside the checkout. Native fixtures redirect only
their authority registry to disposable private storage. Fault injection and
fixture registry redirection are validation-only and are not CLI features.

This Alpha has no UI/API integration. Active UI baseline 0485a5f is untouched;
parked SCRUM-81/i18n/RTL work is not required or transferred.
