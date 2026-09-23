# AIO-048 Context

## Authorization and verified baseline

On 2026-09-23, the Human's initial instruction explicitly authorized AIO-048
Task creation, fresh Architect, Security, and Ownership/Storage design reviews,
implementation, target-safe validation, fresh final specialist and independent
reviews, Quality Gate evaluation, and preparation of the Human Control
checkpoint. That initial instruction did not authorize final approval, Task
closure, staging, commit, push, publication, AIO-049, operational authority
use, dispatch, invocation, or protected-target access.

The verified baseline is clean `main` at
`23a79bf4801c9daf592028ef64fc1fe543984470`. AIO-047 is the direct
dependency. AIO-043 and AIO-045 are semantic predecessors; AIO-041 and
AIO-042 are transitive execution-identity predecessors. AIO-044, AIO-030,
and Full Control Center/UI are not dependencies and remain outside scope.

## Classification and governance

AIO-048 is an `implementation` with high Complexity, critical Risk, and an
explicit `critical` minimum Execution Mode. It uses the
`architecture-change` Workflow because it makes AIO-047's same-domain
single-authority precondition enforceable among conforming trusted consumers
and introduces a new local security authority boundary. The Workflow's
task-type list is advisory
under the canonical Workflow specification and does not override the Human's
explicit authorization of this implementation Task.

The effective Quality Gates are `documentation_consistency` and
`independent_review`. Human architecture, security, ownership, registry,
locking, fencing, limitation, and final approval remains mandatory before
successful completion.

## Approved design locks

All three required pre-implementation reviews approve the locked design:

```text
ARCHITECT DESIGN LOCK: APPROVE
SECURITY DESIGN REVIEW: APPROVE
OWNERSHIP/STORAGE DESIGN REVIEW: APPROVE
```

The supported v1 profile is Windows current-user local ownership only. The
production registry root is derived internally from the Windows non-roaming
Local AppData Known Folder and a fixed AEO-owned suffix. A caller cannot
choose another production registry root. The lock namespace is keyed by a
cryptographic digest of the opaque domain ID and lives under that fixed root,
not beside the SQLite ledger. An exclusive share-zero `CreateFileW` handle is
the live interprocess lock; file presence, a PID, registry data, or a boolean
is never ownership.

One immutable, strict external binding fixes the exact domain, canonical
absolute local ledger path, immutable ledger instance ID, positive domain
generation, Windows `FILE_ID_INFO`, registry format, and initial inactive
state. Subsequent activation and fencing evidence is append-only. `fencing`
and `fenced` evidence dominates `active` evidence, so torn, duplicated, or
partially completed transitions cannot reactivate the domain. Registry
records are canonical, versioned, atomically created and durably flushed;
unknown, missing, duplicate, non-canonical, contradictory, or corrupt state
fails closed. The registry is private operational infrastructure, not a public
schema-backed value.

Activation and acquisition are separate. The ceremony is:

```text
provision ledger
-> register exact inactive binding
-> activate exact binding
-> acquire domain lock and revalidate binding plus ledger
-> issue one live owned session
```

Provisioning never activates or owns a domain. Acquisition obtains the domain
lock before binding or ledger validation, pins an open ledger file handle,
requires exact canonical-path and `FILE_ID_INFO` agreement, rejects hard-link
ambiguity, verifies ledger domain/instance/generation/active metadata and
integrity, and only then mints a process-local capability. Same-domain lock
contention returns immediately as a typed unavailable outcome; it never waits
forever or falls back.

The selected Store-integration model is an owned Store session. Raw
operational SQLite construction requires package-private owner authority and
is not a supported public bypass. The private singleton is a trusted-package
composition convention, not a secret or a barrier against arbitrary Python or
nonconforming peer processes under the same Windows identity. The owned
session exposes the four AIO-047 Store operations, context-manager and close
behavior, terminal fencing, and fenced backup. Every operational call verifies
the exact live session, independently retained raw-Store/handle/PID
association, held lock, domain, path, file identity, ledger instance,
generation, and non-fencing state. The full operation lease rejects recursive
Store/fence entry and defers reentrant session or owner close until the raw call
returns. There is no prior `check_owner()` boolean. Capability construction,
copying, pickling, serialization, cross-store use, wrong-domain use,
wrong-generation use, release, close, loss, and ABA reuse all fail closed.

Generic AIO-047 Store outcome values remain unchanged. Ownership loss maps to
the existing retry-after-remediation `storage_unavailable` outcome;
counterfeit authority or internal ownership incoherence maps to
`integrity_failure`. Local-owner administration uses its own typed ownership
outcome taxonomy and never collapses contention, binding rejection, and
infrastructure failure into booleans.

## Administration and storage policy

`LocalAuthorizationDomainOwner.for_current_user()` is the public production
factory. Public administration comprises exact register, activate, acquire,
migrate, and fence operations. Direct AIO-047 provisioning remains an offline
ledger operation and confers no ownership. Migration takes a transient
exclusive domain administration lock and operates only under its documented
quiescent policy. Operational read/write is possible only through an active
owned session. A supported backup is requested only through that live active
session and remains AIO-047's permanently fenced snapshot. Fencing may start
from a live owner or a recovery owner, but is always forward-only.

Fencing excludes operational use for the full call and persists external
`fencing` evidence before requesting the AIO-047 SQLite terminal fence. It then
appends external `fenced` evidence and retires the live capability. A created
but unpublished marker temp is retained as fail-closed ambiguity. Recovery
publishes and verifies the exact durable terminal marker before removing
validated residue, and establishes `fencing` before reconciling `fenced`
residue. A crash or I/O failure at any point therefore cannot expose `active`.
A later fence call may reconcile the same exact target forward, but no ordinary
API may remove markers, roll back state, or transition to `active`.

An ordinary process crash releases the Windows lock. Recovery may reacquire
only the same active external binding and exact ledger identity. It does not
bump domain generation. Domain generation is not a process-owner generation,
PID, caller-selected number, or capability token. A future explicit authority
transfer may advance it; AIO-048 supplies no transfer API. A future new
generation must reject older-generation Grants using trusted coordinator
context, without adding a caller-trusted generation field to the eight-field
Grant.

## Threat and claim boundary

The supported profile assumes the configured current-user AEO process, local
Windows filesystem and kernel locking, SQLite, and registry directory are
trusted and correctly administered. ACLs reduce accidental or peer-user
access but do not resist the local administrator, SYSTEM, arbitrary code in
the trusted process, raw-disk manipulation, malicious in-place overwrite, or
rollback by a privileged actor, or nonconforming same-identity code. Detectable
cloud-sync, UNC/network, remote, reparse-point, hard-link-ambiguous, and
unsupported filesystem profiles fail closed. Avoiding sync products that
cannot be identified from filesystem state is an operator prerequisite.

The allowed claim is:

> Same-host authorization-domain ownership is established for the configured
> Windows local profile when all supported lock, registry, path,
> file-identity, ledger-instance, generation, activation, and local
> threat-model assumptions hold.

This is not distributed ownership, malicious-administrator rollback
resistance, safe failover, Grant authentication, Tool trust, dispatch,
invocation, or full execution trust. Unavailable authority state never falls
back to memory, another file, a copied database, backup, alternate registry,
or backend.

## Validation boundary

Tests use only disposable temporary directories, synthetic domain IDs, and
synthetic AIO-047 values. Separate OS processes must cover concurrent
acquisition and crash release. Focused evidence must cover registry
corruption, exact mismatches, copy/move/replacement, aliases where safely
available, stale and counterfeit capabilities, release, ABA and callback
reentrancy, soft fence failure, crash-safe terminal-residue handoff, packaging,
and affected AIO-047 regression behavior.

No recursive repository search, broad validator, broad Markdown traversal,
unknown-safety smoke test, protected-target access, real Grant/Tool/Admission
action, dispatch, or invocation is authorized.

## Audited cancellation

Direct Human audited-cancellation authorization was recorded on 2026-09-23.
AIO-048 is `cancelled`, not `completed`; final implementation acceptance was
not approved and Task completion was not achieved. Retroactive authorization,
waiver, and failed-Gate override remain `NO`.

AIO-048 was cancelled because a prohibited non-target-safe package smoke
entered checkout-wide verification and broad Markdown traversal. This made
criteria 74-76 historically unsatisfied or non-certifiable, left the formal
independent outcome at `CHANGES REQUIRED`, and left the required
`independent_review` Gate at `FAIL` without waiver. The final acceptance count
remains 94/100. Human cancellation approval is not Human final acceptance, and
technical implementation quality is not governance completion eligibility.

The specialist-approved partial implementation was removed from the canonical
repository and preserved only as an external noncanonical technical reference
at `D:\Dev\aio-048-cancelled-technical-reference`. That reference is not a
Source of Truth, production implementation, release artifact, or acceptance
evidence. It must not be restored automatically. A future replacement may
consult it only under separate explicit authorization and inherits no approval,
review, Gate, test, or acceptance evidence.

If the technical objective still requires canonical successful completion,
the next separately authorized action is a replacement Task ID/sequencing and
clean-reimplementation investigation. No replacement Task or ID is created or
assigned by this cancellation.
