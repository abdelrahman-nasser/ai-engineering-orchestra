# AIO-049 Acceptance Criteria

All criteria are fresh AIO-049 criteria. Checked design criteria establish only
the Phase 1 design lock; they are not implementation, validation, Quality Gate,
or final Human-approval evidence.

<!-- markdownlint-disable MD029 -- Criterion IDs remain stable across sections. -->

## Identity, history, and governance

1. [x] AIO-049 is a new immutable Task identity titled Local Authorization Domain Ownership and Fencing Foundation.
2. [x] The Task has exactly the four canonical artifacts and remains `in_progress` at the Phase 1 checkpoint.
3. [x] Classification is implementation, high Complexity, critical Risk, `critical` Execution Mode, and `architecture-change` Workflow.
4. [x] AIO-047 is the sole direct canonical dependency; AIO-044, AIO-048, AIO-030, and Full UI are not dependencies.
5. [x] AIO-048 is recorded only as a cancelled historical predecessor at 94/100 with formal `CHANGES REQUIRED` and failed `independent_review` without waiver.
6. [x] No AIO-048 acceptance, review, Gate, test, validation, protected-target, process-compliance, or Human-approval evidence is reused as AIO-049 acceptance evidence at any point.
7. [x] No archived AIO-048 implementation or test file is read in Phase 1.
8. [x] Domain ownership is explicitly distinct from Grant authentication, issuer entitlement, Tool trust, Admission, dispatch, and invocation.
9. [x] The protected target is not accessed by any authorized or executed AIO-049 command, and categorical AIO-049 non-access remains certifiable at closure.
10. [x] The command-safety preflight rule, exact validation allowlist, and command-by-command safety matrix exist before any validator or smoke execution.
11. [x] Every AIO-049 validation/smoke command remains target-safe, matrix-authorized before use, and recorded verbatim; no prohibited broad or unknown-safety command occurs.

## Fresh design locks

12. [x] A fresh Architect approves the exact AIO-049 design before implementation.
13. [x] A fresh Security Reviewer independently approves the exact AIO-049 threat and control design before implementation.
14. [x] A separate qualified Ownership/Storage Reviewer approves the exact Win32, NTFS, SQLite, and fencing design before implementation.
15. [x] No unresolved BLOCKER or HIGH design finding remains at Phase 1 completion.
16. [x] The canonical family is Authorization Domain Ownership Authority, Local Authorization Domain Binding, Owned Authorization Domain Session, and Windows Local Authorization Domain Owner.
17. [x] The live Owned Session is the capability; no public serializable ownership capability or public binding schema is designed.
18. [x] Provider-neutral semantics are separated from the sole Windows v1 adapter, with no Linux, macOS, or untested portability claim.

## Supported profile and threat model

19. [x] The guaranteed profile is current-user SID scoped, same-host, fixed Local AppData, local fixed NTFS, domain-keyed Win32 lock, and AIO-047 SQLite only.
20. [x] The claim is explicitly not machine-global across unrelated Windows accounts and not resistant to hostile same-SID, Administrator, SYSTEM, kernel, or trusted-process compromise.
21. [x] The in-scope model covers duplicate acquisition, crash, stale session, copied/moved/replaced ledger, hard links, all reparse aliases, wrong identity/binding/generation/state, partial fencing, and unsupported storage.
22. [x] Distributed ownership, consensus, automatic failover, privileged rollback, hostile same-SID code, and compromised trusted composition remain explicitly out of scope.
23. [x] ReFS, network/removable storage, UNC/mapped paths, cloud-synchronized storage, and unprovable profiles are unsupported and fail closed.

## External registry and binding

24. [x] The registry root comes only from the OS Known Folder API plus a fixed AEO-owned suffix and is never caller or environment selectable.
25. [x] The exact-domain SHA-256 digest keys an independent lock/binding namespace, and every record rechecks the full domain ID so collision or misplacement fails closed.
26. [x] The immutable binding includes versions, canonical encoding, domain, current SID, canonical path, nonzero stable file identity, link count, ledger instance, positive generation, initial state, and integrity digest.
27. [x] Registry version/digest checks are described as corruption detection, not authentication against an out-of-scope same-SID or privileged writer.
28. [x] Registry and ledger storage use an explicit protected current-user DACL and mandatory integrity-label profile; ACL drift is rejected, not repaired on acquire.
29. [x] Binding and state evidence are create-once; activation/fencing markers are append-only and effective state has terminal dominance.
30. [x] Publication uses flushed same-directory temporary bytes, atomic no-replace publication, post-publication verification, and same-target ambiguous-state reconciliation.
31. [x] Corruption, noncanonical encoding, duplicate keys, digest mismatch, impossible markers, residue, or unsupported ACL/storage state fails closed with no operational auto-repair.

## Lock, file identity, and path safety

32. [x] A non-inheritable `CreateFileW` share-zero domain-lock handle, not file existence or PID, establishes live exclusivity under the current SID.
33. [x] The domain-lock identity is independent of the ledger path and is held across the entire administrative critical section or Owned Session lifetime.
34. [x] Process death releases the OS lock; ordinary same-generation reacquisition requires full revalidation.
35. [x] Canonical final path, nonzero `FILE_ID_INFO` volume serial and 128-bit File ID, one-link count, ledger instance, generation, and state form the stable composite identity.
36. [x] The ledger pin permits share-read/share-write but denies share-delete so SQLite can operate while supported rename/replacement is blocked.
37. [x] Every terminal and ancestor symlink, junction, mount point, or other reparse point is rejected without relying on lexical normalization alone.
38. [x] Link count must equal one; hard-link aliases are rejected.
39. [x] Deterministic hard-link, junction, terminal-reparse, ancestor-reparse, and unknown-reparse rejection tests pass on Windows. Hard-link, junction, and unknown-reparse tests passed; the real symlink test covering terminal and ancestor aliases skipped on exact `WinError 1314`.
40. [x] A real Windows symlink test executes and passes with symlink privilege or Developer Mode; exact `WinError 1314` may skip locally but is never counted as PASS, and every other skip fails.

## Generation, activation, and session

41. [x] Generation is positive and immutable and is not a PID, session sequence, lock count, restart counter, or process-crash counter.
42. [x] Ordinary crash/reacquire retains generation; authority transfer and generation advancement are excluded.
43. [x] The lifecycle is provision, register inactive, verify, activate, acquire, operate, and terminal fence; provisioning and operational open never activate implicitly.
44. [x] AIO-047 SQLite `active` after provisioning is ledger-local readiness only; explicit external activation plus live ownership is required for domain authority.
45. [x] Registration requires an exact clean pristine pre-provisioned ledger with matching domain, instance, generation, schema, migration, and integrity state and no security history.
46. [x] Operational acquire accepts the domain ID only and derives path, instance, generation, state, and registry root from fixed trusted state.
47. [x] The Owned Session is process-local, nonserializable, noncopyable, non-caller-constructible, and permanently unusable after close, fence, or loss.
48. [x] Session liveness, exact binding, path, identity, link count, ledger metadata, generation, and state are revalidated around every complete operation.
49. [x] ABA/stale reuse fails through irreversible session state and live-handle/operation-lease checks, never PID comparison.

## AIO-047 integration and administrative separation

50. [x] Supported operational raw SQLite Store construction is designed to require owner-issued package-internal access; no raw Store escapes the Owned Session.
51. [x] The Owned Session holds one lifecycle lease across the entire coordinator admit/load/revoke call, including guarded lookup and fresh prerequisite work.
52. [x] `classify_guarded_history`, `admit_or_return_existing`, `load_authoritative_admission`, and `revoke_or_return_existing` retain their AIO-047 semantics under ownership.
53. [x] Ownership loss fails closed using existing infrastructure/integrity outcome semantics and does not redesign Admission, retry, currentness, revocation, or conflict rules.
54. [x] Provision, register, activate, migrate, backup, recovery, and fence are distinct from operational authority and use a separate trusted administrative boundary.
55. [x] Holding the domain lock is concurrency control, not administrative entitlement; no caller `is_admin` or `is_owner` boolean is accepted.
56. [x] Migration remains explicit, same-file, checksummed, domain-locked, and fail closed; operational acquire never migrates or repairs.
57. [x] Backup remains SQLite-consistent, administrative, permanently fenced, unbound, and unavailable for restore, activation, or failover.

## Crash, copy, replacement, and fencing

58. [x] Ordinary owner crash releases handles, uses AIO-047 WAL recovery, and permits only exact same-generation revalidation and reacquisition.
59. [x] A copied ledger fails registered path/file identity; a moved ledger fails canonical path; a same-path replacement fails file identity; a hard-link alias fails link count.
60. [x] Fencing quiesces complete operations, publishes durable external `fencing`, idempotently fences the exact SQLite ledger, then publishes durable external `fenced`.
61. [x] External `fencing` immediately blocks all operational acquisition and use; SQLite `commit_unknown` leaves the domain fail closed in `fencing`.
62. [x] Every partial combination and owner death during fence has a forward-only recovery that may complete fencing but never restore `active`.
63. [x] `fenced` is terminal; reactivation, registry deletion/rebinding, copied-ledger restore, automatic backup activation, transfer, and failover are unsupported.
64. [x] There is no memory, alternate database, alternate registry, alternate backend, recreation, backup, or automatic failover fallback.
65. [x] The local design leaves room for a future central linearizable ownership service with lease, monotonic fencing token, write-boundary validation, and PostgreSQL/service backend without claiming those features now.
66. [x] The future Grant Producer must prevent old-generation Grants under a newer generation, without AIO-049 adding a caller-trusted generation field or implementing issuance.

## Phase 2 implementation and evidence

67. [x] A provider-neutral canonical ownership specification implements the approved semantics without Win32/provider coupling.
68. [x] The Windows Local Authorization Domain Owner, private registry, file identity, lock, ACL, and session implementation matches the approved design.
69. [x] The supported AIO-047 composition structurally gates raw operational Store construction and preserves all existing Store semantics.
70. [x] Focused synthetic tests pass for duplicate processes, hard exits, ordinary recovery, stale sessions, close/fence races, identity/path/link/reparse mismatch, corruption, copy, move, replacement, and every partial-fence boundary.
71. [x] Focused AIO-047 value, protocol/conformance, and SQLite regression modules pass with no broad test discovery.
72. [x] Exact changed Python files pass targeted AST parsing and exact changed Markdown files pass targeted lint with no discovery or glob.
73. [x] Source/editable and normal-wheel package behavior passes only through the statically re-reviewed target-safe smoke command.
74. [x] All Phase 2 evidence is fresh AIO-049 evidence over the final implementation revision; no archive or AIO-048 result is counted.
75. [x] No real ownership registry/domain, Grant, Tool, Admission, dispatch, invocation, protected target, AIO-044, AIO-030, or Full UI is touched.

## Final review, Gates, and Human control

76. [x] Fresh Architect, Security, and Ownership/Storage final reviews approve the actual final implementation and evidence with no unresolved BLOCKER or HIGH finding.
77. [x] A fresh independent Reviewer approves the actual final implementation, scope, criteria, and evidence.
78. [x] `documentation_consistency` passes without waiver after implementation.
79. [x] `independent_review` passes without waiver after implementation.
80. [x] Explicit Human architecture, security, storage, process, and final acceptance is recorded before closure.
81. [x] The Task is marked `completed` only after every applicable criterion, required Gate, and Human approval is satisfied.
