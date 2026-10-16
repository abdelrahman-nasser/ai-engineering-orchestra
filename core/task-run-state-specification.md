# Persistent Task and Run state and continuation

Version: 0.1.0. ITRU-062 owns this optional local lifecycle contract.
ITRU-060 Result and ITRU-061 Journal contracts remain unchanged.

## Identity and ownership

A Task keeps its declared task.yaml id, exact and case-sensitive within one
Project. Explicit enrollment pins an immutable definition reference. A dedicated
Store pins store_id/project_id, and each Run retains the unchanged complete
AgentExecutionRun, Tool Binding and AuthorizationDomainIdentity. Run IDs are
permanently unique within that Store. One Run is one semantic attempt, belongs
to exactly Contract.task_id, and can never be rebound or reopened.

For enrolled Tasks the Store owns operational lifecycle; task.yaml continues to
own intent, requirements and governance closure evidence. Its status is an
explicitly reconciled mirror, never an implicit override. This API does not edit
YAML, prove ID uniqueness outside the enrolled namespace, evaluate Quality Gates
or infer Human closure from execution. Enrollment references must be resolved
by the trusted caller without Task/Workflow catalog enumeration.

## Task and Run state machines

Task states are the existing planned, in_progress, blocked, completed, cancelled.
Enrollment creates planned. A first pending Run changes it to in_progress.
Blocking planned/in_progress requires a reference and no unfinished attempt.
An original failed_before_effect/effect_ambiguous Result blocks the Task;
original success leaves it in_progress, never automatically completed.
Continuation from eligible blocked/in_progress state creates a new pending Run
and changes the Task to in_progress. No other unblock API exists.

Explicit completion requires in_progress, at least one succeeded Run, no pending,
running, interrupted or effect_ambiguous Run, and a governance closure reference.
The trusted caller must first satisfy every applicable closure requirement;
the Store checks lifecycle conditions only. Explicit cancellation is possible
from any nonterminal Task state and retains every unresolved effect. Both
completed and cancelled are terminal, with no reopen API.

| From Run state | Legal successor | Boundary |
| --- | --- | --- |
| pending | running | Explicit durable start marker |
| pending | cancelled | Stop, Task cancellation or recovery |
| running | succeeded | Exact authoritative original Result |
| running | failed_before_effect | Exact authoritative original Result |
| running | effect_ambiguous | Exact authoritative original Result |
| running | interrupted | Stop, Task cancellation or recovery |
| Any terminal state | None | New work always needs a new Run ID |

The terminal Run states are succeeded, failed_before_effect, effect_ambiguous,
interrupted and cancelled. At most one unfinished Run exists per Task. A caller
must commit the running marker before invoking through upstream execution.
The marker records intent; it cannot invoke or confer authority. The Store
cannot police effects performed outside its trusted composition contract.

interrupted means no original Result was durably accepted for an attempt marked
started. It may have effected work. It is distinct from completed or known
failure-before-effect. blocked is a Task condition with a retained reason.
Stale describes mismatched revision/checkpoint evidence and returns a conflict;
it is not a durable lifecycle state.

## Resume and authority

A Checkpoint is exactly store_id, project_id, task_id and committed Task revision.
It is a version reference, not a saved continuation or capability. A continuation
requires the exact current Checkpoint and a new unique Run with a valid complete
subject for the same Task. Eligible prior attempts are succeeded,
failed_before_effect or cancelled-before-start; an eligible blocked Task may
have no prior Runs. Any unfinished, interrupted or effect_ambiguous attempt in
the Task prevents continuation. There is no uncertainty override in v1.

The Store calls an explicitly configured trusted continuation_authorizer inside
the serialized transaction. A fresh immutable request binds the Checkpoint,
new complete subject, reason, a random process-session nonce and request nonce.
The adapter must freshly authenticate Human/policy entitlement for that exact
request and return an exact request-bound ContinuationApproval. Missing adapter,
denial, exception, malformed reply, changed request or mismatched nonce fails
closed. No caller-supplied approval argument or deserialize-to-authorize API
exists. Core validates binding, not the truth of an external Human/policy system;
adapter authentication and freshness are explicit trusted-composition obligations.

The decision allows one lifecycle insertion only. Its persisted receipt grants
nothing. It never substitutes for fresh effective mode, prerequisites, ownership,
Grant production/authentication, admission, claim/JIT or invocation authority.
No old capability or live Result is restored on restart. A new session must
configure its own fresh adapter. No scheduler or automatic retry is implemented.

effect_ambiguous is terminal for that attempt and blocks continuation. Neither
that outcome, missing Result, interrupted state nor Journal evidence proves no
effect. No automatic replay or exactly-once execution claim is made.

## Result and Journal reconciliation

record_result requires the unchanged original-production membership check and
exact complete Binding and ledger identity of the running Run. It stores only
outcome and physical Result identity, never content, diagnostic transport, Result
object, callable or serialized proof. One physical Result cannot bind two Runs.
Reconstruction of accepted lifecycle history does not reconstruct an authoritative
Result. Losing the live Result before its state transaction commits leaves an
interrupted attempt after recovery even if Journal has a success summary.

reconcile_run is a pure diagnostic over a RunSnapshot and an exact tuple of
validated JournalRecords. It compares full Binding/ledger and cross-record
Admission/Entry identity, order, event uniqueness and accepted outcome. Its closed
states are missing, entry_only, recorded_result, conflict and inconsistent.
It preserves the lifecycle state separately from any recorded outcome. It never
updates lifecycle, creates a Result, opens storage or supplies continuation
authority. Filtered subsets need not have contiguous Journal sequences but must
retain increasing order, one Journal and one coherent complete subject. A Result
summary without its Entry is inconsistent, not proof of success.
Entry or Result evidence for a pending or cancelled-before-start Run conflicts
with its absent durable start marker; the diagnostic preserves both facts.

## Persistence and recovery

The Developer Alpha realization is a separate dedicated local SQLite v1 Store.
Small bounded histories and one process owner favor SQLite atomic transactions
and constraints over custom file replacement. DELETE journaling avoids persistent
WAL sidecars; synchronous=FULL and BEGIN IMMEDIATE protect each aggregate update.
The Journal and authorization ledger are never opened or migrated by this Store.
The Store owns its private filesystem checks and delegates Windows access-profile
validation to the existing ownership adapter; it has no Journal storage import.

Explicit provision creates a new private directory, immutable metadata and
append-only events. Open requires existing complete storage, exact identities,
known application/schema version and exact DDL/fingerprint. It never creates,
migrates, restores or repairs storage. The supported profile is trusted private
same-host local storage, fixed local volume on Windows, current-user filesystem
profile, no links/reparse/hard-linked files, SQLite >= 3.37. Remote, shared/cloud
sync and distributed storage are unsupported. POSIX callers must ensure the
configured filesystem is local. Privileged coherent substitution/rollback is
outside the model; no cryptographic tamper/rollback detection is claimed.

An exclusive OS lock on the provisioned owner file is held until session close
or process loss. A second conforming owner fails busy. Each operation verifies
pinned directory/file identities, security profile, metadata, DDL, SQLite
quick_check, canonical JSON, sequence/revision continuity and every historical
transition. Invalid history fails as a whole; no usable prefix or skipped row.
Operational open validates first, then atomically recovers all unfinished Tasks:
pending Runs become cancelled, running Runs interrupted, affected Tasks blocked.
An explicit stop applies the same conservative conversion to one Task.
Recovery is idempotent when repeated; terminal outcomes are retained unchanged.

An in-process mutex and SQLite transaction serialize updates. Task-wide revision
CAS covers every owned Run; one conflicting continuation loses before authority
consultation/insertion. Callbacks cannot recursively mutate/read/close the Store.
Closed, copied, serialized and foreign-process sessions are unusable. The adapter
performs no execution and must avoid waiting on other Store operations.

Exact enrollment and initial-registration repeats return current descriptive
state only if immutable identity matches. Reobservation of the same authoritative
original Result is idempotent. Other transitions and continuation are strict CAS;
an old request cannot reopen/start/reexecute a Run. Commit uncertainty raises
StateCommitUnknownError: query state, do not automatically repeat. Failed
transactions roll back the entire event, including continuation insertion.

Event JSON is canonical, duplicate-key-free, closed, versioned and bounded to
1 MiB; the complete Store is bounded to 10,000 events. Exhaustion fails without
deletion or partial history. No compaction, retention, export/import, migration
or same-identity restore interface exists. Events have contiguous global sequence
and per-Task revision. The structural contract is
schemas/task-run-state-event.schema.json; the semantic reducer is authoritative
for cross-record identity, transitions and ownership. Schema validity alone
authenticates nothing. SQL schema/fingerprint are fixed implementation resources.

## Queries and future scheduler boundary

get_task/get_run return immutable exact-ID snapshots or None. checkpoint returns
the exact committed version. page returns bounded deterministic case-sensitive
keyset pages of enrolled Tasks, or one Task's Runs, with limits 1-100. A page is
current at its own transaction; later pages can observe later commits. It is not
a frozen multi-page export. Queries validate the whole Store and never enumerate
repository catalogs. They expose facts only: no ready queue, dependency/DAG
traversal, ordering policy, scheduler choice, budgets, routing or dispatch.
ITRU-063 may consume these boundaries under its own future contract.
