# ITRU Control Center architecture Human decisions

## October 17, 2026 — v2 architecture approval

**Decision:** APPROVED

**Approval date:** October 17, 2026

**Approval statement:**

> approve ITRU Core Application Boundary Design v2, including P01–P10, for architecture and subsequent implementation planning

**Approval scope:** Architecture baseline and subsequent implementation planning,
including P01–P10 in full, for the exact complete v2 document identified below.

| Document identity | Value |
| --- | --- |
| Title | ITRU Core Application Boundary Design v2 |
| Original filename | `ITRU_Core_Application_Boundary_Design_v2.md` |
| Original document date | 17 October 2026 |
| Revision | v2; exact revision is fixed by the SHA-256 of the preserved original bytes |
| Canonical repository path | [docs/architecture/control-center/application-boundary-v2.md](application-boundary-v2.md) |
| SHA-256 | `c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062` |

Within this approved scope, the complete v2 supersedes the unavailable earlier
architecture design. It does not replace existing Core governance or semantic
contracts, authorize production implementation, or establish runtime acceptance.

**Not authorized by this architecture approval:**

- Production implementation or source modifications outside the separately
  authorized documentation consolidation task.
- Runtime execution, operational-store access, source/dataset selection, or
  metadata-access grants.
- Transport/authentication selection or operational UI commands.
- Activation of execution, approval, cancellation, or continuation controls.

At the time of this architecture approval, the implementation plan remained
**pending**. The separate plan approval and S0-only authorization below supersede
that planning status without broadening this original architecture decision.

## Provenance and historical status

This record transcribes the actual Human decision explicitly supplied in the
permanent documentation consolidation instruction and reaffirmed in the resume
instruction identifying the exact v2 file and expected SHA-256. Those instructions
state that the approval of P01–P10 was given on October 17, 2026.

No separate `ITRU_Core_Application_Boundary_Design_v2_Human_Approval.md` file was
found in the permitted source locations during consolidation. The explicit Human
instruction is the source for this record. No signature, precise approval time,
additional decision, independent approval, or formal Quality Gate result is
inferred or fabricated.

The technical originals are preserved byte-for-byte. Their candidate,
`UNAPPROVED`, and approval-pending statements describe their historical status
when authored. This separate subsequent decision establishes the current approved
architecture scope without rewriting that historical evidence. Historical review
records inside the originals are not fresh approvals of executable integration.

## Documentation consolidation authorization and stop

The separate Human consolidation instruction authorizes inspection, preservation,
organization, verification, independent review, and one local documentation-only
commit of `docs/architecture/control-center/`, subject to its baseline, integrity,
scope, and governance checks. The resume instruction continues that authorization
after the missing v2 document becomes available and its expected hash is verified.

That task authorization is distinct from the October 17 architecture decision.
It does not authorize product implementation, UI changes, runtime execution,
transport selection, pushes, merges, tags, PRs, or publication. No new Task ID or
implementation-plan document is created by this archive.

**STOP AT HUMAN CONTROL** after the authorized local documentation commit and
report the final commit hash and canonical document paths. Any further planning
or implementation requires a subsequent scoped Human instruction.

## October 17, 2026 — implementation-plan approval, H2 and S0-only authorization

**Source:** The explicit Human instruction titled
`ITRU — APPROVE PLAN, ARCHIVE & EXECUTE S0`, dated October 17, 2026.

**Plan decision:** APPROVED as the planning baseline.

| Approved plan identity | Value |
| --- | --- |
| Title / original filename | `ITRU_Read_Only_Integration_Implementation_Plan.md` |
| Canonical path | [docs/architecture/control-center/integration-implementation-plan.md](integration-implementation-plan.md) |
| Exact SHA-256 | `93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d` |
| Architecture retained unchanged | Approved v2 and P01–P10, SHA-256 `c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062` |

**H2 clarification: ACCEPTED.** The Human instruction states:

> Existing historical lifecycle integrity and event-replay validation may continue using `continuation_eligible` internally. However, `InspectRun` and `ReadRunJournal` must not assess or expose current continuation eligibility. First-slice eligibility remains `unassessed`, and every continuation control remains disabled.

The archived plan's historical H2 blocker and implementation-unauthorized labels
are deliberately not rewritten. This later decision resolves H2 only within
the scope above. It does not weaken historical validation or authorize a current
eligibility assessment.

**Phase A authorization:** Copy the verified original plan byte-for-byte; update
only this decision record and the index; verify preserved/staged bytes and obtain
independent documentation/governance review where available. Create one local
documentation-only commit:

`docs: archive approved Control Center integration plan`

**Phase B authorization: S0 ONLY, subject to repository governance.** After the
documentation commit, create `feature/control-center-s0-feasibility` from that
commit if governance permits. Do not invent a Task ID. If an assigned Task ID or
different approved workflow is required before implementation, stop and report.

S0 may create isolated source/policy/budget definitions, synthetic fixtures,
tests and feasibility evidence in these proposed allowed locations:

- `itru/control_center_read_source.py`
- `itru/control_center_read_budget.py`
- `tests/test_control_center_feasibility.py`
- `tests/fixtures/control_center/`
- `docs/architecture/control-center/s0-feasibility-report.md`

Any additional product file or integration hook requires separate authorization.
Existing production runtime/store/scheduler modules, database schemas, UI source,
and the canonical approved architecture must not be changed.

Scoped synthetic tests may use existing installed tools and standard libraries.
Record exact commands, tool versions, exit codes, measurements and limitations.
Synthetic databases/artifacts must stay in explicitly controlled test locations,
without reuse or deletion of existing user data. No operational owner/database,
production Alpha execution, credentials, downloads, dependency installation,
network probes, Codex diagnostics, D6-E/B1 execution, actual dataset registration,
metadata-access grant, or authentication/transport selection is authorized.

S0 must cover the complete mutation/shutdown inventory; recovery-free reading;
one-second capture/safe cleanup; Journal semantic validation; memory/byte/row/
cumulative accounting; SQLite WAL/SHM and DELETE sidecars; cancellation/writer
priority; source/policy/budget compatibility; and unsupported capabilities and
unresolved prerequisites. Preserve P07 in full. If a mandatory P07 safety
property cannot be established, report **NO-GO**, not a bypass or relaxed limit.

Obtain distinct Core-concurrency and Journal/resource-security reviews where
available, reporting actual independence and findings. Synthetic tests are not
operational acceptance; no simulated approval or fabricated runtime PASS is
implied by this authorization.

**Final control:** Report the documentation commit, actual S0 branch/status,
exact changed paths, tests/measurements, independent reviews and GO/NO-GO
recommendation. Do not stage or commit S0 changes before separate Human final
review. Do not proceed to S1, S2, S3 or UI development. No push, merge, tag,
publication or external-system modification is authorized.

**STOP AT HUMAN CONTROL.**

## October 17, 2026 — Phase A preserved-formatting disposition

**Source:** Explicit Human instruction titled `ITRU — HUMAN CONTROL DISPOSITION`.

**Decision:** ACCEPT the five preserved formatting findings for Phase A, limited
to `docs/architecture/control-center/integration-implementation-plan.md`:

- Four intentional Markdown hard breaks at lines 3–6.
- One preserved final blank line at line 439.

The whole-staged command
`git -c core.autocrlf=false --no-optional-locks diff --cached --check` returned
**exit code 2**. The command did not PASS. The five findings above have an
explicit Human-accepted disposition; no unrelated finding is accepted or hidden.
The approved plan must remain byte-for-byte identical, with SHA-256
`93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d`.

Before committing, verify that there are no additional formatting findings or
unauthorized staged changes. The Human authorizes the previously specified
documentation-only local commit and requires verification of its committed
blob hash, scope and Git state. This disposition concerns the known mechanical
formatting findings; it does not convert the command's exit code into a PASS
or waive any other validation or Quality Gate.

After successful Phase A closure, continue the previously authorized S0 work
only. Synthetic feasibility, prerequisite definitions, scoped validation and
independent review remain the complete S0 scope. Operational data access,
transport selection, UI changes and progression to S1–S8 remain prohibited.
S0 implementation changes must remain unstaged and uncommitted until separate
Human final review. Stop and report any new blocking finding, scope deviation
or governance conflict.

**STOP AT HUMAN CONTROL** after Phase A and S0.
