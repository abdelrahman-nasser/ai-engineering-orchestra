# AIO-049 Context

## Phase 1 authorization and verified baseline

Direct Human instruction on 2026-09-23 authorizes Phase 1 only: create this new
Task, define fresh acceptance and design locks, establish the validation-safety
allowlist, obtain fresh Architect, Security, and Ownership/Storage design
reviews, and prepare the Human checkpoint. Runtime or test implementation,
archive-code consultation, implementation validation, Quality Gate execution,
staging, commit, and Phase 2 are not authorized.

The verified starting point is clean `main` at
`dc22ff35612369c6af1d68f6b16ade7c959f3503`. The index is clean. AIO-047 is
completed at 105/105 and is the sole direct canonical dependency. AIO-048 is a
cancelled historical predecessor only; it remains cancelled at 94/100 with a
formal independent outcome of `CHANGES REQUIRED` and an `independent_review`
Gate result of `FAIL` without waiver.

This is a new immutable Task identity. It does not reopen, continue, amend,
replace, complete, or cure AIO-048. AIO-048 is not a dependency. AIO-044,
AIO-030, and Full UI are not dependencies. AIO-043 and AIO-045 are semantic
context only through the AIO-047 boundary.

The external reference at
`D:\Dev\aio-048-cancelled-technical-reference`, whose recorded checksum is
`974796c8b8ded830f32a907162a6035e348c070642bd9de3d11f234f38d91a7e`, is
noncanonical. No implementation or test file from that archive may be opened
in Phase 1. Its checksum is identification metadata, not AIO-049 acceptance
evidence.

```text
engineering knowledge != acceptance evidence
similar architecture != inherited approval
identical implementation != inherited validation
```

## Phase 2 authorization and environment block

Direct Human instruction on 2026-09-23 accepted the Phase 1 design baseline
and authorized Phase 2 implementation plus fresh technical validation. The
Phase 2 baseline matched exactly: `main` remained at
`dc22ff35612369c6af1d68f6b16ade7c959f3503`, the index and tracked diff were
clean, and only the four untracked AIO-049 Task artifacts were present.

The authorization required bounded interpreter resolution before validation
and required Phase 2 to stop if no compatible interpreter exists. Both exact
authorized discovery commands were executed:

```powershell
py -0p
where.exe python
```

`py -0p` could not start because the launcher is absent, and `where.exe
python` returned no candidate path. Therefore no candidate version command
was available, no interpreter was selected, and Phase 2 is environment-blocked
before implementation. No alternate executable, WSL runtime, installation,
PATH change, or virtual environment was probed or used.

```text
PHASE 2 STATUS: BOUNDEDLY BLOCKED
BLOCKER: no compatible Python interpreter discoverable by the authorized commands
IMPLEMENTATION STARTED: NO
READY FOR PHASE 3: NO
```

## Environment-remediation authorization and result

Direct Human instruction on 2026-09-23 authorized one narrow remediation:
check `winget`, and only if available install official user-scope
`Python.Python.3.12`, verify one exact CPython 3.12 executable, update the
matrix, pass the exact Task/Workflow structural gate, and resume Phase 2.

The Phase 2 remediation baseline again matched exactly. The sole authorized
availability command was executed:

```powershell
winget --version
```

PowerShell returned `CommandNotFoundException`; Windows Package Manager is not
available in the execution environment. The authorization requires an
immediate stop in this case and prohibits every alternate installer, package
manager, download, bootstrap script, elevation, PATH workaround, or arbitrary
executable search. Consequently `Python.Python.3.12` was not installed, the
preimplementation structural gate was not reached, and Phase 2 remains blocked
before implementation.

```text
ENVIRONMENT REMEDIATION: BLOCKED — winget unavailable
PHASE 2 STATUS: BOUNDEDLY BLOCKED
IMPLEMENTATION STARTED: NO
READY FOR PHASE 3: NO
```

## Human-provided interpreter resolution and agent verification result

On 2026-09-24, the Human reported an existing CPython 3.12.10 installation at
the exact path below and authorized verification of that path only:

```text
C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe
```

The previous failed discovery and `winget` history remain accurate. No new
installation or discovery was authorized. The four exact verification commands
were attempted with the supplied absolute path: `--version`, the `sys`
diagnostic, `pip --version`, and the `sqlite3` version diagnostic. In this
agent's command-execution environment, every invocation returned PowerShell
`CommandNotFoundException` for that exact executable path. No Python process
started and no diagnostic code ran.

The mandatory preimplementation gate therefore failed before Task/Workflow
schema validation. In accordance with the instruction, there was no Python
rediscovery, App Execution Alias use, alternate interpreter, WSL access,
installation, schema execution, archive consultation, or implementation.

```text
HUMAN-PROVIDED PYTHON RESOLUTION: RECORDED
AGENT VERIFICATION: FAILED — exact executable unavailable in agent environment
PREIMPLEMENTATION STRUCTURAL GATE: FAIL
PHASE 2 RESUMED: NO
PHASE 2 STATUS: BOUNDEDLY BLOCKED
```

## Environment blocker resolution and fixed interpreter

On 2026-09-24, after the failed exact-path attempt above, the Human granted
narrow Read+Execute access on the existing Python 3.12 installation directory
to the Codex sandbox identity. The earlier discovery, remediation, and access
failures remain part of the record and are not superseded.

```text
PHASE 2 INITIAL ATTEMPT: BOUNDEDLY BLOCKED — Python not discoverable
HOST PYTHON DISCOVERED BY HUMAN: CPython 3.12.10
INITIAL AGENT ACCESS: DENIED
ROOT CAUSE: Codex sandbox Windows identity lacked Read/Execute access to the Human's user-local Python installation
HUMAN REMEDIATION: Narrow Read+Execute ACL on C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312 for MATEBOOK6S\codexsandboxoffline
RESULT: Python executable from the Codex environment
HOST PYTHON REINSTALLED: NO
PATH MODIFIED: NO
ALTERNATE RUNTIME INTRODUCED: NO
```

The agent then executed only the four Human-authorized exact-path checks. The
selected interpreter is
`C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe`;
it reported CPython 3.12.10, pip 25.0.1, and SQLite 3.49.1, and
`sys.executable` matched the exact selected path.

```text
SELECTED INTERPRETER: C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe
VERSION: 3.12.10
IMPLEMENTATION: CPython
ACCESS MODEL: Existing Human-user installation with explicit sandbox Read+Execute access
PATH DEPENDENCY: NO
INSTALLATION PERFORMED FOR AIO-049: NO
```

The two previously approved exact single-document schema loaders were then
executed with that absolute interpreter. The exact AIO-049 Task and exact
`architecture-change` Workflow both passed their schemas. Together with the
three approved Phase 1 design locks and the unchanged protected-target and
command-safety boundary, every preimplementation condition passed and the
existing Phase 2 authorization resumed.

```text
TASK SCHEMA: PASS
WORKFLOW SCHEMA: PASS
ARCHITECT DESIGN LOCK: APPROVE
SECURITY DESIGN REVIEW: APPROVE
OWNERSHIP/STORAGE DESIGN REVIEW: APPROVE
VALIDATION SAFETY MATRIX: UPDATED
COMMAND OUTSIDE MATRIX: NO
PROTECTED TARGET ACCESSED: NO
CATEGORICAL AIO-049 NON-ACCESS CERTIFIABLE: YES
PREIMPLEMENTATION STRUCTURAL GATE: PASS
PHASE 2: RESUMED
```

## Objective and authority boundary

AIO-049 establishes current-user, same-host operational ownership of one exact
authorization domain and one exact pre-provisioned AIO-047 SQLite Admission
ledger. The bounded supported claim is exclusivity among conforming AEO
coordinators operating under the same Windows user SID and fixed registry
namespace. It is not machine-global exclusivity across unrelated Windows
accounts.

Ownership is a prerequisite for supported operational access; it is not any of
the authorities or outcomes below.

```text
domain ownership != Grant authentication
domain ownership != issuer entitlement
domain ownership != Tool trust
domain ownership != Admission
domain ownership != dispatch
domain ownership != invocation
```

No ownership flag, PID, registry file, lock-file pathname, SQLite field, or
serialized value is authority alone. Operational authority is the live
composite of:

1. a held domain-keyed Win32 share-zero lock handle in the fixed namespace;
2. a valid immutable external binding and valid monotonic state evidence;
3. a held no-delete-share pin to the exact verified ledger file;
4. exact domain, path, file, ledger-instance, generation, and state agreement;
5. a live process-local Owned Authorization Domain Session; and
6. an operation lease covering the complete supported coordinator operation.

If any component is missing, stale, corrupt, contradictory, unsupported, or
cannot be revalidated, authority is unproven and the operation fails closed.

## Canonical concept family

The Phase 1 canonical terms are:

- **Authorization Domain Ownership Authority**: the provider-neutral semantic
  boundary that acquires, validates, holds, and releases exclusive operational
  ownership for one exact authorization domain.
- **Local Authorization Domain Binding**: the immutable, private,
  adapter-owned durable record binding a domain and current user SID to one
  exact ledger identity and positive generation. Possessing or copying the
  record is not authority.
- **Owned Authorization Domain Session**: the live, process-local,
  nonserializable and noncopyable operational boundary that retains the OS
  handles and gates complete coordinator operations. This live session is the
  capability; AIO-049 defines no separate public serialized ownership
  capability.
- **Windows Local Authorization Domain Owner**: the sole v1 operational
  adapter implementing the provider-neutral ownership semantics for the
  supported Windows profile.

The provider-neutral specification must not import Win32 paths, handles, ACL
APIs, or SQLite implementation details. Linux and macOS adapters do not exist
in AIO-049. The private Windows registry format is not a public Core schema.

## Supported platform and storage profile

The only guaranteed v1 profile is:

```text
Windows current-user SID
+ OS Known Folder Local AppData
+ fixed AEO-owned registry namespace
+ local fixed NTFS volumes
+ one conforming local AEO coordinator owner per domain and SID
+ domain-keyed Win32 ownership lock
+ pre-provisioned AIO-047 SQLite WAL/FULL ledger
+ no network, cloud-synchronized, replicated, or automatically failed-over storage
```

Both the registry and ledger volumes must be local, fixed, and reported as
NTFS. UNC paths, mapped/network drives, ReFS, removable media, cloud placeholder
or offline files, and known synchronized-storage profiles are rejected. The
adapter also rejects any profile it cannot establish as supported. AIO-049
does not claim that Windows can detect every third-party synchronization agent;
absence of such an agent is a deployment precondition, and known indicators
must fail closed.

ReFS is not supported merely because some individual file-identity APIs exist
there. Support would require separate evidence for the full SQLite, locking,
ACL, link, reparse, durability, and atomic-publication profile.

## Threat model

### In scope

- accidental duplicate or concurrently starting conforming coordinators under
  the same current-user SID;
- process crash and automatic kernel-handle release;
- stale, closed, copied, or reused session objects and ABA-style reuse;
- copied, moved, replaced, hard-linked, symlinked, junctioned, mounted, or
  otherwise reparse-aliased ledgers;
- stale, corrupt, truncated, partially published, mismatched, or copied
  external binding/state records;
- wrong domain, registry key, path, stable file identity, ledger instance,
  generation, activation state, or fencing state;
- crashes or ambiguous results at every activation and fencing publication
  boundary;
- partial fencing, owner death during fencing, and stale operations after
  fencing begins;
- accidental split authority through a caller-selected registry root or raw
  supported Store construction;
- unsupported local storage, ACL, integrity-label, or filesystem profiles; and
- bounded accidental corruption and configuration drift detectable by the
  locked integrity and identity checks.

### Out of scope

- a malicious Administrator, SYSTEM, kernel, filesystem driver, or firmware;
- arbitrary hostile code running as the same Windows SID or inside the trusted
  AEO process;
- a compromised trusted coordinator, administrative authority, Grant
  Producer, or Tool Resolver;
- privileged in-place rollback or coordinated rewrite of both registry and
  ledger;
- cross-SID or machine-global mutual exclusion, distributed ownership,
  cross-host consensus, automatic failover, or authority transfer; and
- protection from every undetectable third-party file synchronization agent.

The registry checksum detects corruption and torn or mixed records. It is not
a signature and does not authenticate bytes against a hostile same-SID or
privileged writer.

## Fixed registry and external binding

The Windows adapter obtains Local AppData from
`SHGetKnownFolderPath(FOLDERID_LocalAppData)` for the current process token. It
must not accept an environment-derived or caller-supplied registry root. The
fixed namespace is conceptually:

```text
<LocalAppData>\AI Engineering Orchestra\authorization-domain-ownership\v1\
  locks\<domain-key>.lock
  domains\<domain-key>\
    binding.v1.json
    active.v1.json
    fencing.v1.json
    fenced.v1.json
```

`domain-key` is lowercase SHA-256 over the exact UTF-8 bytes of the
`authorization_domain_id`; no Unicode normalization or path-derived identity
is used. Every record contains and revalidates the exact domain ID and digest,
so a collision or misplaced record fails closed.

The immutable binding contains at least:

- private registry format and record versions;
- record kind and canonical-encoding identifier;
- exact `authorization_domain_id` and domain-key digest;
- exact current-user SID;
- canonical final ledger path;
- nonzero `FILE_ID_INFO.VolumeSerialNumber`;
- nonzero 128-bit `FILE_ID_INFO.FileId`;
- required link count of one;
- exact AIO-047 `ledger_instance_id`;
- positive immutable `domain_generation`;
- initial external state `inactive`; and
- a SHA-256 digest over the canonical record payload.

The binding is create-once and never rebound in AIO-049. State is represented
by create-once, append-only, digest-linked canonical markers. Effective state
uses terminal dominance:

```text
binding only -> inactive
active marker -> active
fencing marker -> fencing
fenced marker -> fenced
```

Each marker binds the exact binding digest and predecessor evidence. Unknown
fields, duplicate JSON keys, noncanonical UTF-8/JSON, digest mismatch,
impossible marker combinations, unexpected residue, or ACL drift fails closed.
Operational acquire never repairs or deletes registry state.

Durable publication uses a same-directory uniquely named temporary file with
an explicit security descriptor, complete write, `FlushFileBuffers`, close,
an NTFS same-directory atomic no-replace rename, and post-publication reopen,
ACL, byte, digest, and state verification. State records are never overwritten.
An ambiguous publication is reconciled only by an explicit same-target
administrative operation: the exact final record is either present and valid,
or absent; corrupt/contradictory state is not guessed or repaired. No design
claim relies on an unsupported `ReplaceFileW` write-through flag.

### ACL and integrity-label model

The namespace root, domain directories, lock files, binding, markers, and
administrative temporaries use an explicit protected DACL owned by the current
user SID. The allowlist grants the current SID and trusted Windows maintenance
principals required by the platform (SYSTEM and local Administrators) the
documented access, grants no broad user/group write access, disables inherited
write grants, and applies a mandatory integrity label that prevents Low
integrity write-up (normally Medium/`NO_WRITE_UP`). Phase 2 must lock and test
the exact security descriptor rather than silently accepting an equivalent-
looking broad ACL.

The ledger directory, main database, and present WAL/SHM files must likewise
meet the supported current-user storage ACL profile so another unprivileged SID
cannot mutate authority state. Operational acquire validates; it does not
auto-repair ACLs. These controls do not protect against the explicitly
out-of-scope current SID, Administrator, or SYSTEM threats.

## Domain lock

The lock namespace is keyed only by the exact domain digest and is independent
of ledger location. A fixed namespace/bootstrap lock serializes safe initial
namespace creation; the per-domain lock serializes all later registration,
activation, acquisition, migration, backup, recovery, and fencing for that
domain.

The Windows primitive is a non-inheritable `CreateFileW` handle opened on the
domain lock file with share mode zero. The handle is retained for the whole
administrative critical section or Owned Session lifetime. A lock file that
merely exists, a stored PID, a process name, a registry record, or a caller
`is_owner`/`is_admin` boolean proves nothing. Process termination releases the
kernel handle; ordinary recovery then reacquires the same domain lock without
changing generation.

The share-zero rule applies to the domain lock file, not the SQLite ledger.
Applying share-zero to the database would prevent SQLite from opening it.

## Ledger path and stable file identity

Registration obtains the authoritative path and identity from an opened file
handle, not from caller lexical normalization alone. The canonical path is the
normalized extended Win32 final DOS path returned by
`GetFinalPathNameByHandleW`; comparisons use exact Windows path semantics and
never a caller alias.

Every component from the volume root through the ledger and registry target is
opened and inspected without following a reparse point. Any terminal or
ancestor reparse point is rejected, including symlinks, junctions, mount
points, and unknown reparse tags. The final ledger must be a regular file on a
local fixed NTFS volume.

The stable identity is the composite of:

- canonical final path, which detects a move or alternate name;
- nonzero volume serial plus nonzero 128-bit file ID, which detects same-path
  replacement and distinguishes a copied file;
- link count exactly one, which excludes a second hard-link pathname;
- exact ledger instance ID, which distinguishes provisioned ledgers even when
  bytes or metadata are copied;
- exact positive generation, which binds the authority epoch; and
- exact external and SQLite activation/fencing state.

An Owned Session retains a separate ledger pin handle opened for attribute
access with share-read and share-write but without share-delete. This permits
SQLite WAL/FULL access while preventing supported rename/delete/replacement
during the session. Identity, link count, path, state, and handle liveness are
revalidated before and after every complete supported coordinator operation.

Deterministic hard-link and reparse rejection must always pass. A real symlink
creation test may locally skip only for exact `WinError 1314`, but that skip is
not PASS evidence. Final AIO-049 acceptance requires a real Windows run with
the necessary privilege or Developer Mode where the symlink test executes and
passes. Any other skip reason fails.

## Generation semantics

`domain_generation` is a positive immutable property of the binding and exact
SQLite ledger. It is not a PID, process-start counter, owner-session sequence,
lock acquisition count, or restart counter. Ordinary close, crash, and
reacquisition retain the same generation. A future authority transfer would
require a strictly new generation, but transfer is not implemented or
authorized by AIO-049.

A future authenticated Grant Producer must ensure a Grant associated with an
old generation cannot be admitted under a newer generation. AIO-049 does not
add a caller-trusted generation field to the existing Grant contract and does
not implement the producer.

## Activation lifecycle

The supported lifecycle is explicit:

```text
provision ledger
-> register immutable inactive external binding
-> verify exact pristine binding and ledger
-> publish active marker
-> acquire live session
-> operate
-> publish fencing marker
-> fence SQLite ledger
-> publish fenced marker
```

AIO-047 provisioning currently writes SQLite `activation_state='active'`.
AIO-049 deliberately treats that as ledger-local readiness, not authorization-
domain activation. Registration creates an externally `inactive` binding;
supported operational acquisition is impossible until the explicit external
active marker exists and all identity checks pass. Operational open never
registers or activates automatically.

Registration requires a pre-provisioned, exact, clean, internally active, and
pristine ledger: matching domain, instance and generation; valid migration and
schema integrity; null decision watermark; and no Admission or revocation
history. An already used, fenced, dirty, copied, incompatible, or mismatched
ledger cannot be registered or activated.

Operational acquisition accepts the exact domain ID as its ownership selector.
It accepts no caller registry root, ledger path, ledger instance, generation,
state, PID, or ownership boolean. Those values are derived from and checked
against the fixed registry and exact ledger. Trusted coordinator dependencies
may be configured by trusted composition, but they are not ownership evidence.

## Owned Authorization Domain Session and AIO-047 integration

Only the Windows Local Authorization Domain Owner can create an Owned Session.
The session is process-local, nonserializable, noncopyable, not caller-
constructible, bound to one exact domain/binding/ledger/generation, and
irreversibly unusable after close, fence, or loss. It retains the domain lock
and ledger pin handles for its full lifetime. An in-memory session nonce or
epoch may defend accidental object reuse, but it is neither durable generation
nor standalone authority.

The session owns a lifecycle gate. A supported `admit`, authoritative `load`,
or `revoke` call holds one operation lease across the entire AIO-047
coordinator call, including trust checks, guarded-history classification,
fresh prerequisite reconstruction, and final Store operation. Close or fence
first prevents new leases and waits for the current complete operation to
quiesce. This prevents release/fence from interleaving between
`classify_guarded_history` and `admit_or_return_existing`.

The existing AIO-047 raw SQLite Store constructor and administrative methods
are directly callable today. Phase 2 must structurally change the supported
composition so operational raw Store construction requires a package-internal
exact-identity access token minted only for a live Owned Session. The raw Store
remains an internal building block and is never returned by the supported API.
The session owns the coordinator and Store facade. This is an encapsulation
boundary for conforming callers, not a sandbox against hostile Python code in
the trusted process or hostile same-SID code.

All four backend-neutral Store operations retain their AIO-047 semantics:

```text
classify_guarded_history
admit_or_return_existing
load_authoritative_admission
revoke_or_return_existing
```

They are reachable operationally only inside a live operation lease. Ownership
failure maps to an existing fail-closed infrastructure/integrity outcome and
never changes Admission, retry, currentness, revocation, or conflict semantics.
The AIO-047 coordinator remains responsible for Grant/Binding trust, fresh
prerequisites, and exact Run reconstruction; ownership does not impersonate
those responsibilities.

## Administrative and operational separation

Operational authority is limited to Admission history classification,
admission, authoritative Admission loading, and revocation through the owned
coordinator surface. Provision, register, activate, migrate, back up, recover,
fence, close, and release are distinct administrative operations.

Every state-changing administrative operation serializes on the same domain
lock, but holding that lock is concurrency control, not administrative
authorization. Administrative calls use a separate trusted internal entrypoint
and operation-specific intent; there is no caller `is_admin` boolean. AIO-049
does not authenticate a Human or policy administrator and makes no entitlement
claim beyond the trusted-composition boundary.

Provisioning occurs under the domain lock before binding and creates no domain
authority. Migration occurs only under the domain lock with no live
operational session, on the same pinned file. It preserves path, instance, and
generation; dirty, incompatible, or commit-unknown migration state blocks
acquisition until explicit same-target reconciliation. Operational acquire
never migrates or repairs.

A supported backup uses AIO-047's SQLite-consistent backup path under the
administrative lock and produces a permanently fenced, unbound destination.
No backup is registered, restored, activated, or used as failover in AIO-049.

## Crash recovery and stale-session model

An ordinary process crash closes the domain-lock and ledger-pin handles and
lets SQLite perform its existing WAL recovery. A new coordinator under the
same SID may reacquire the same domain lock and must revalidate the exact fixed
binding, path, file identity, ledger instance, same generation, active state,
schema, migration history, and integrity before returning a new session. No
generation bump occurs.

For ABA:

```text
owner A closes or crashes
-> owner B acquires the same domain and obtains a distinct live session
-> any retained A object remains closed/stale and every operation fails closed
```

The rule relies on irreversible session state, live handle ownership, and the
operation lease, not PID equality. A closed session cannot reacquire or be
reanimated.

A ledger copied from path A to B fails because the registered canonical path
and stable file identity do not match. Replacement at the same path fails
because the file ID changes; replacement during a session is also denied by
the no-delete-share pin. Movement fails canonical-path comparison. Hard-link
aliasing fails the one-link rule. These claims apply to the supported threat
model and do not cover a privileged coordinated rewrite of registry and ledger.

## Terminal fencing and partial-state recovery

Fencing first quiesces complete coordinator operations while retaining the
domain lock and exact ledger pin. The only supported durable order is:

1. atomically publish and verify external state `fencing`;
2. call the idempotent AIO-047 SQLite fence on the exact pinned ledger under
   its existing WAL/FULL and `BEGIN IMMEDIATE` durability semantics; and
3. after confirmed or reconciled SQLite fencing, atomically publish and verify
   external state `fenced`.

`fencing` immediately dominates `active`; no new operational acquire or call
is permitted. A SQLite fence `commit_unknown` leaves external state at
`fencing`. Recovery reacquires the same domain lock, validates the same binding
and file identity, and may only repeat/reconcile the SQLite fence and publish
`fenced`. It never returns to `active`.

| Observed durable state | Required behavior |
| --- | --- |
| Registry `fencing`, SQLite `active` | Reject operations; idempotently complete SQLite fence, then publish `fenced`. |
| Registry `fencing`, SQLite `fenced` | Reject operations; verify exact identity, then publish `fenced`. |
| Registry `fenced`, SQLite `active` | Reject operations; treat as contradictory terminal residue and only complete SQLite fencing. |
| Registry `active`, SQLite `fenced` | Reject operations; publish forward fencing evidence and complete `fenced`; never reactivate SQLite. |
| Owner dies at any fence boundary | Kernel releases lock; next explicit recovery follows the same forward-only rules. |
| Stale session calls during/after fence | Lifecycle gate rejects before Store access. |
| Corrupt, ambiguous, or mismatched identity | Fail closed; no operational repair or alternate ledger. |

`fenced -> active` is unsupported. Deleting registry files, rebinding a domain,
restoring a copy, or incrementing generation is not recovery. Those require a
future transfer design and new authorization.

## No fallback and future boundary

There is no memory, alternate-database, alternate-registry, automatic-backup,
alternate-backend, recreation, or automatic-failover path. If authoritative
ownership cannot be proven, the only operational result is fail closed.

The local design preserves a future Team/Enterprise direction:

```text
central ownership service
+ linearizable ownership registry
+ lease
+ monotonic fencing token/generation
+ write-boundary fencing validation
+ PostgreSQL or service Admission backend
```

That future model is not implemented. Local process-lifetime handles are not
misrepresented as distributed leases or fencing tokens.

Program sequencing remains:

```text
AIO-049 ownership foundation
        -> Authenticated Grant Producer
        -> Trusted Tool Registry / Resolver
        -> Local Operational Trust Integration
        -> Dispatch Delivery / Outbox / Claim-Lease
        -> Invocation Idempotency / Result
        -> first Human-approved controlled invocation
```

The Grant Producer and Tool Resolver remain blocked as a program-sequencing
recommendation until AIO-049 completes; afterward they may proceed in parallel.
No later Task IDs are allocated here.

## Validation-safety policy

Before any validator, smoke, packaging, lint, test-discovery, or verification
command is executed, its exact executable, arguments, scope, and target safety
must be established from already approved syntax or static inspection of the
exact source revision.

```text
unknown command -> do not execute
unknown validator -> do not execute
legacy validator --help discovery -> prohibited
command absent from this matrix -> not authorized
```

An absent command may be added only after static safety review, matrix
amendment, and explicit Human authorization. Every executed validation or
smoke command must be recorded verbatim in `review.md`.

### Validation Safety Matrix

| Validation | Exact allowed scope | Safety basis | Phase | Authorized? | Executed? |
| --- | --- | --- | --- | --- | --- |
| AIO-049 Task schema (`V1`) | Exact AIO-049 `task.yaml` plus exact Task schema only | Direct loader command below; legacy source inspection proves the legacy validator is catalog-wide | Phase 1/2 | Yes, exact command only | PASS after fixed-interpreter verification; earlier unavailable attempt remains recorded |
| `architecture-change` Workflow schema (`V2`) | Exact workflow YAML plus exact Workflow schema only | Direct loader command below; legacy source inspection proves the legacy validator is catalog-wide | Phase 1/2 | Yes, exact command only | PASS after fixed-interpreter verification; earlier skip remains recorded |
| Ownership tests (`T1`) | Two exact proposed AIO-049 test modules | Explicit unittest module names; both final sources statically reviewed | Phase 2 | Yes, exact command only | OK: 30 run, one exact `WinError 1314` symlink skip; criterion 40 remains open |
| Standalone real Windows symlink/reparse test | One exact unittest node: `tests.test_windows_local_authorization_domain_owner.WindowsLocalAuthorizationDomainOwnerWin32Tests.test_terminal_and_ancestor_reparse_points_are_rejected` | Exact Python 3.12 interpreter; disposable synthetic test state; no protected-target traversal; no repository-wide discovery | Phase 2 | Yes, exact command only; direct Human validation-matrix amendment dated 2026-09-24 | Fresh Human-controlled elevated Windows PowerShell evidence: 1/1 PASS in 0.014s; no `WinError 1314`; AC39/AC40 complete |
| AIO-047 regressions (`T2`) | Three exact AIO-047 modules | Explicit unittest module names; exact modules and imported conformance helper re-reviewed | Phase 2 | Yes, exact command only | PASS: 75/75 |
| Packaging unit test (`T3`) | Exact `tests.test_packaging` module | Explicit module; source statically re-reviewed | Phase 2 | Yes, exact command only | PASS: 27/27 |
| AST parsing (`A1`) | Explicit anticipated changed Python files only | `ast.parse`; no discovery or glob; actual paths match the locked list | Phase 2 | Yes, exact command only | PASS: 11/11 |
| Markdown (`M1`) | Explicit anticipated changed Markdown files only | Explicit arguments; no discovery or glob; actual paths match the locked list | Phase 2 | Yes, exact command only | PASS: 0 issues in 5 files after formatting fixes |
| Editable and wheel smoke (`S1`) | Exact `package_installation_smoke.py --target-safe` | Target-safe branch skips checkout Task/Workflow/full verification; entire exact script revision must be re-read before use | Phase 2 | Yes, exact command only after final static re-review | PASS; first restricted-network attempt was terminated without a verdict, then the exact command passed with package-index access |
| Git metadata (`G1`-`G7`) | Status, exact HEAD/branch, changed-path diff, stat, cached stat, and diff check | Bounded Git metadata/diff over the current change | All phases | Yes | As recorded in `review.md` |
| Repository-wide verification | Prohibited | Broad scope and protected-target risk | None | No | No |
| Legacy Task validator | Prohibited | Static inspection: hard-coded Task catalog plus Workflow catalog resolution | None | No | No |
| Legacy Workflow validator | Prohibited | Static inspection: all canonical Workflows, fixtures, and Role catalog | None | No | No |
| Legacy validator `--help` | Prohibited | Discovery execution is explicitly forbidden | None | No | No |
| Bare package smoke | Prohibited | Enters checkout Task/Workflow/full verification branch | None | No | No |
| Bare/broad unittest or pytest discovery | Prohibited | Unbounded test discovery | None | No | No |
| Broad Markdown traversal | Prohibited | Unknown-file traversal | None | No | No |
| Recursive repository search | Prohibited | Unknown-file traversal | None | No | No |
| Unknown command | Prohibited | Not statically reviewed | None | No | No |
| Python interpreter discovery | `py -0p`; `where.exe python`; exact returned candidate `--version` only | Explicit Phase 2 Human authorization; touches no repository content | Phase 2 | Yes | Yes; no candidate found |
| Environment remediation | `winget --version`; exact user-scope `Python.Python.3.12` install only if available | Explicit Human remediation authorization; environment-only | Phase 2 remediation | Yes | Availability check failed; install not executed |
| Human-supplied interpreter verification | Exact `C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe` with `--version`, `sys` diagnostic, `pip --version`, and `sqlite3` diagnostic only | Direct Human resolution instruction; no discovery | Phase 2 resume | Yes | All four failed to start: path unavailable to agent environment |
| Resolved fixed-interpreter verification | Exact `C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe` with `--version`, `sys` diagnostic, `pip --version`, and `sqlite3` diagnostic only | Direct Human resumption instruction after narrow Read+Execute ACL remediation; no discovery, PATH dependency, or installation | Phase 2 resume | Yes | PASS: CPython 3.12.10, exact `sys.executable`, pip 25.0.1, SQLite 3.49.1 |

### Exact Phase 1 commands

`V1` — exact AIO-049 Task structural validation:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/task.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'.ai/tasks/AIO-049-local-authorization-domain-ownership-and-fencing-foundation/task.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact AIO-049 task schema')"
```

`V2` — exact `architecture-change` Workflow structural validation:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import json,pathlib,yaml; from jsonschema import Draft202012Validator as V; s=json.loads(pathlib.Path(r'schemas/workflow.schema.json').read_text(encoding='utf-8')); V.check_schema(s); d=yaml.safe_load(pathlib.Path(r'workflows/architecture-change.yaml').read_text(encoding='utf-8')); e=sorted(V(s).iter_errors(d), key=lambda x:list(x.absolute_path)); assert not e, '\n'.join(f'{list(x.absolute_path)}: {x.message}' for x in e); print('PASS exact architecture-change workflow schema')"
```

The two commands load only their two named files. They do not enumerate a Task,
Workflow, Role, Markdown, or repository catalog and do not perform semantic
catalog resolution.

### Exact planned Phase 2 commands

These commands are locked for planning but are not authorized until separate
Human Phase 2 authorization and the stated static source review.

`T1` — proposed exact ownership modules:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_authorization_domain_ownership tests.test_windows_local_authorization_domain_owner -v
```

`T2` — exact affected AIO-047 regressions:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_agent_execution_dispatch_admission tests.test_agent_execution_dispatch_admission_store_conformance tests.test_sqlite_agent_execution_dispatch_admission_store -v
```

`T3` — exact packaging module:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest tests.test_packaging -v
```

`A1` — exact anticipated Python paths, with no discovery:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B -c "import ast,pathlib; p=[pathlib.Path(x) for x in ('engineering_orchestration/authorization_domain_ownership.py','engineering_orchestration/windows_local_authorization_domain_owner.py','engineering_orchestration/agent_execution_dispatch_admission_store.py','engineering_orchestration/sqlite_agent_execution_dispatch_admission_store.py','engineering_orchestration/__init__.py','tests/test_authorization_domain_ownership.py','tests/test_windows_local_authorization_domain_owner.py','tests/test_agent_execution_dispatch_admission_store_conformance.py','tests/test_sqlite_agent_execution_dispatch_admission_store.py','tests/test_packaging.py','tests/package_installation_smoke.py')]; [ast.parse(x.read_text(encoding='utf-8'), filename=str(x)) for x in p]; print(f'PASS AST {len(p)}/{len(p)}')"
```

`M1` — exact anticipated changed Markdown paths, with no glob or discovery:

```powershell
npx --yes markdownlint-cli2 core/authorization-domain-ownership-specification.md core/terminology.md .ai/tasks/AIO-049-local-authorization-domain-ownership-and-fencing-foundation/context.md .ai/tasks/AIO-049-local-authorization-domain-ownership-and-fencing-foundation/acceptance-criteria.md .ai/tasks/AIO-049-local-authorization-domain-ownership-and-fencing-foundation/review.md
```

`S1` — exact target-safe editable and normal-wheel smoke:

```powershell
& 'C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe' -B tests/package_installation_smoke.py --target-safe
```

`python -B tests/package_installation_smoke.py` without `--target-safe` is
prohibited. Before `S1`, the whole exact script revision must be re-read and
confirmed to keep target-safe execution out of checkout Task/Workflow catalog
enumeration and full repository verification. If actual Phase 2 paths differ
from the explicit lists above, execution pauses for static review, matrix
amendment, and explicit Human authorization.

## Protected-target and process boundary

Throughout AIO-049, no authorized or executed command may open, read, search,
grep, recursively enumerate, specifically list, stat, hash, or resolve the
protected target. Its identity must not be investigated. Categorical AIO-049
non-access must remain certifiable at closure.

No non-target-safe smoke, broad Task validation, Task catalog enumeration,
Workflow catalog enumeration, repository-wide verification, recursive
repository search, broad Markdown traversal, unknown-safety validator, legacy
validator `--help`, or command absent from the approved matrix is permitted.
These are fresh prospective AIO-049 requirements and do not alter AIO-048's
historical record.

## Phase 2 implementation and technical checkpoint

Phase 2 implemented the approved local ownership foundation without consulting
the AIO-048 archive and without touching a real ownership registry or domain.
The implementation consists of:

- a provider-neutral ownership identity, authority, operation-lease, live
  session, and typed fail-closed error contract;
- the canonical provider-neutral ownership specification and terminology;
- a Windows-only current-SID Local AppData adapter with a fixed domain-keyed
  registry, share-zero domain lock, canonical append-only records, protected
  ACL and integrity-label validation, complete reparse rejection, NTFS file
  identity, a live no-share-delete ledger pin, explicit activation, and
  forward-only terminal fencing;
- private, exact identity-bound, single-claim operational and administrative
  Store access so supported raw SQLite Store construction cannot bypass the
  owner; and
- focused provider-neutral, Win32, AIO-047 regression, and packaging evidence.

The final Windows pin requests read-data, attribute, and security-descriptor
access while sharing read and write but not delete. This keeps SQLite WAL/FULL
operation compatible and makes rename/replacement participate in Windows share
checking. Component inspection uses zero-access, non-following handles so every
absolute component is still opened and inspected while inaccessible parent ACLs
fail closed in production. Win32-retained DACL/SACL `AI` provenance bits are
accepted only through four finite exact descriptor variants; owner, protected
DACL, ACEs, rights, and mandatory label remain exact.

Fresh final-revision validation produced:

- `V1`: exact AIO-049 Task schema PASS;
- `V2`: exact `architecture-change` Workflow schema PASS;
- `A1`: 11/11 changed Python files parsed;
- `T1`: 30 tests completed with `OK (skipped=1)`; all 29 executed tests passed;
- `T2`: 75/75 AIO-047 value, conformance, and SQLite regression tests passed;
- `T3`: 27/27 packaging unit tests passed;
- `M1`: all five exact changed Markdown files passed targeted lint; and
- `S1`: the statically re-reviewed target-safe editable and normal-wheel smoke
  passed, including exact installed ownership exports and source-leak checks.

The prior Codex-sandbox symlink creation attempt returned exact `WinError 1314`
and was not counted as PASS. Fresh Human-controlled elevated Windows
PowerShell evidence subsequently executed the exact standalone real-symlink
node and passed (`1 test`, `0.014s`, no `WinError 1314`). Real
junction-ancestor, unknown-tag terminal reparse, hard-link, identity,
copy/move/replacement, duplicate-process, hard-exit, close-race, stale/lost
session, ACL drift, and every partial-fence boundary test executed and passed.
Acceptance criteria 39 and 40 are complete.

```text
PHASE 2 IMPLEMENTATION: COMPLETE
PHASE 2 TECHNICAL VALIDATION: COMPLETE
REAL SYMLINK RESULT: HUMAN ELEVATED PASS — 1 test in 0.014s; no WinError 1314
ARCHIVE FILES READ: NO
REAL OWNERSHIP REGISTRY OR DOMAIN TOUCHED: NO
PROTECTED TARGET ACCESSED: NO
PHASE 3 REVIEWS OR QUALITY GATES RUN: SPECIALIST AND INDEPENDENT REVIEWS COMPLETE; GATES PENDING
READY FOR PHASE 3 FINAL REVIEW AUTHORIZATION: YES
TASK STATUS: in_progress
TASK CLOSED: NO

PHASE 3 SPECIALIST REVIEWS: ALL APPROVED
FORMAL INDEPENDENT REVIEW: APPROVE / COMPLIANT
DOCUMENTATION_CONSISTENCY: PASS WITHOUT WAIVER
INDEPENDENT_REVIEW GATE: PASS WITHOUT WAIVER
READY FOR HUMAN FINAL APPROVAL: YES
HUMAN FINAL APPROVAL: PENDING

FINAL HUMAN APPROVAL: APPROVED
APPROVAL DATE: 2026-09-24
APPROVAL SOURCE: Direct Human final approval at AIO-049 Human Control
TASK-COMPLETION CRITERION: PENDING

## Final closure authorization

Task closure was authorized directly by the Human on 2026-09-24 after final
Human acceptance, all reviews, both Quality Gates, and 80/81 acceptance
criteria were complete. The final Task-completion criterion is now complete;
the canonical Task status is `completed`. Closure source: Direct Human
Task-closure and local-commit authorization. No implementation or validation
scope changed.
COMMIT CREATED: NO
```

## Archive consultation recommendation and Human checkpoint

If all three Phase 1 design reviews approve, Phase 2 may be allowed to inspect
individually named archive files only after a separate explicit Human Phase 2
authorization names them. The archive may then supply noncanonical engineering
reference only. It may not be bulk restored, mirrored, patch-applied, or used
as evidence. Any identical implementation introduced for AIO-049 becomes new
AIO-049 code and requires fully fresh tests, reviews, Gates, and Human approval.

At the Phase 1 stopping point, before the later authorization recorded above:

```text
AIO-049 status: in_progress
Human Phase 2 implementation authorization: PENDING
Task closed: NO
Commit created: NO
```

At the current Phase 2 checkpoint, archive consultation was not needed or
performed. Phase 2 implementation authorization has been consumed, the Task
remains `in_progress`, the real-symlink evidence gap remains open, and no
Phase 3 activity or commit has occurred.
