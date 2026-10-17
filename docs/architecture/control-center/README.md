# ITRU Core and Control Center architecture

This directory is the permanent, version-controlled source of truth for the
approved Core application boundary architecture and its Human approval record.
The architecture baseline is **ITRU Core Application Boundary Design v2**,
including **P01–P10**, approved on **October 17, 2026** for architecture and
subsequent implementation planning. The completed implementation plan is now
Human-approved. A separate October 17, 2026 instruction authorizes only S0
synthetic feasibility, subject to repository governance; later implementation
slices and operational integration remain unauthorized.

## Canonical documents

All paths below are relative to the Core repository root.

| Canonical path | Purpose and current status |
| --- | --- |
| `docs/architecture/control-center/README.md` | Index, provenance, document identities, and instructions for future sessions. |
| [docs/architecture/control-center/boundary-investigation.md](boundary-investigation.md) | Preserved static investigation and evidence base. Its historical observations and proposals are not implementation authorization. |
| [docs/architecture/control-center/reconciliation-addendum.md](reconciliation-addendum.md) | Preserved reconciliation corrections and constraints incorporated into v2. Its historical approval wording is unchanged. |
| [docs/architecture/control-center/application-boundary-v2.md](application-boundary-v2.md) | Exact approved v2 technical baseline, including P01–P10. Historical candidate and approval-pending labels remain verbatim; read the later Human decision alongside it. |
| [docs/architecture/control-center/human-decisions.md](human-decisions.md) | Separate record of the actual October 17, 2026 Human approval, its exact document identity, scope, and exclusions. |
| [docs/architecture/control-center/integration-implementation-plan.md](integration-implementation-plan.md) | Exact Human-approved S0–S8 planning baseline. Historical authorization and unresolved-H2 statements are preserved; the subsequent Human decision accepts H2 and authorizes S0 only, subject to governance. |

The **implementation plan is approved and archived**. This does not authorize
S1–S8, operational-store access, transport/authentication selection, or UI work.
Read the later decisions below alongside the preserved plan.

## Preserved original identities

The three technical documents were copied byte-for-byte from the originals
in `C:\Users\Abdelrahman\Downloads`. The investigation's extension changed
from `.txt` to `.md`; its contents, encoding, and line endings did not change.
The following SHA-256 values identify the original bytes and must also match
the corresponding repository files and Git blobs.

| Original filename | Canonical filename | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `ITRU_Core_UI_Boundary_Investigation.txt` | `boundary-investigation.md` | 50565 | `1f736d4c0158c6781627b3abd9b95979b4f1279c92d270773d163f7e9cc12596` |
| `ITRU_Core_Application_Boundary_Reconciliation_Addendum.md` | `reconciliation-addendum.md` | 3670 | `8d816aefda08b9542cb448eca467c3fde3d32bf081ec2cfb52caae4f7b380d94` |
| `ITRU_Core_Application_Boundary_Design_v2.md` | `application-boundary-v2.md` | 75711 | `c15ac0c1cf6838e48c32cb42931138ee167902cc2eb27207486a178c06785062` |

These hashes establish document byte identity against the supplied expected
values. They are not cryptographic signatures, runtime integrity evidence,
operational authorization, or Quality Gate results.

## Approved implementation-plan identity

The completed report was recovered from its original temporary location and
copied byte-for-byte, without reconstruction from conversation text:

`C:\Users\Abdelrahman\AppData\Local\Temp\itru-read-only-planning-2026-10-17\ITRU_Read_Only_Integration_Implementation_Plan.md`

| Identity | Value |
| --- | --- |
| Original title / filename | `ITRU_Read_Only_Integration_Implementation_Plan.md` |
| Canonical path | [docs/architecture/control-center/integration-implementation-plan.md](integration-implementation-plan.md) |
| SHA-256 | `93241792fa9a0313e9bee28c6542cbe9d5dd16a4f6599c0b6e0892340f48ee9d` |
| Human approval date | October 17, 2026 |

The exact archived plan is the planning baseline. Its historical statements
that implementation was unauthorized and H2 unresolved remain unchanged.
The subsequent Human instruction recorded in `human-decisions.md` accepts H2:
historical integrity/event replay may use `continuation_eligible` internally;
neither query may assess or expose current continuation eligibility. First-slice
eligibility remains `unassessed` and continuation controls remain disabled.

S0 may prepare isolated source/policy/budget definitions, synthetic fixtures,
tests and feasibility evidence within the separately authorized paths. It may
not modify existing production runtime/store/scheduler modules, database
schemas, UI source or canonical approved architecture. Operational data access,
audience grants, authentication/transport selection, S1–S8, downloads,
dependency installation, network/diagnostic probes and D6-E/B1 execution remain
excluded. No synthetic result establishes operational acceptance.

The authorization requires stopping if repository governance needs an assigned
Task ID or a different approved workflow before implementation; no Task ID may
be invented. S0 implementation changes must remain unstaged and uncommitted
until separate Human final review. A P07 safety property that cannot be
established requires a NO-GO recommendation, without relaxing the profile.

## Authority and document relationship

The investigation supplies the static evidence base. The addendum reconciles
that investigation with the earlier design direction. The complete v2
consolidates that evidence and defines the approved P01–P10 requirements.
Within its approved architecture scope, v2 supersedes the unavailable earlier
design; the investigation and addendum remain supporting evidence.

The originals describe their status when written. In particular, v2 still says
that it is a candidate, that P01–P10 are unapproved, and that Human approval is
pending. Those historical statements have deliberately not been rewritten.
The subsequent approval recorded in [human-decisions.md](human-decisions.md)
establishes the current architecture and planning authority of the exact v2
revision identified above. It does not convert proposed integration facilities
into implemented behavior or confer operational authority.

Historical local-file links, filenames, source observations, and review records
inside the originals are preserved provenance. Use this index for canonical
document locations; do not infer current repository state, current test results,
or fresh reviewer approval from those historical records. This documentation
consolidation does not amend existing Core semantic contracts, governance, or
the approved release scope.

## Repository baseline references

These are the Human-supplied architecture reference baselines, not a claim
about the current state of a future checkout.

| Reference | Location or branch | Commit |
| --- | --- | --- |
| Core approved release | `D:\Dev\ai-engineering-orchestra` | `e7af2c4c01645a05e6e78ccea7e845dafc455399` |
| Active UI baseline | `D:\Dev\itru-ui` | `0485a5fe84746252b3f8f3bcd4f0d9e85e2a7a67` |
| Parked SCRUM-81 | UI branch `ui/itru-062-contract-i18n-rtl` | `61e817c1f7a2c3987710a73366b516d792402520` |

The separate D6-E/B1 diagnostic foundation remains outside this documentation
task. No branch transfer, UI change, release rewrite, or diagnostic execution
is authorized here.

## Instructions for future Codex sessions

Before planning revisions or separately authorized integration work:

1. Read repository `AGENTS.md`, the current Task, and applicable governance.
2. Read this index and `human-decisions.md` to establish approval scope.
3. Verify the three preserved technical documents and the archived plan against
   the SHA-256 values above. A mismatch requires investigation and Human
   resolution; do not substitute a draft or reconstruct a missing document.
4. Read the complete `application-boundary-v2.md`, including P01–P10, alongside
   the complete investigation and reconciliation addendum. Use the recorded
   approval for current status while preserving historical document wording.
5. Verify current Core/UI baselines and preserve existing tracked and untracked
   work under the scope of the next separately authorized task.
6. Keep architecture approval distinct from implementation authorization.
   Planning may proceed only within the applicable Human instruction; code
   changes require separate authorization. Do not automatically begin planning
   as a consequence of this archive task.
7. Read the complete archived implementation plan and subsequent Human decisions.
   The current implementation scope is S0 only, subject to its governance
   prerequisites and explicit synthetic-only restrictions. Later slices require
   separate authorization.

The approved first slice contains exactly `InspectRun` and `ReadRunJournal`.
It remains read-only and content-free, with Core-authoritative lifecycle, DAG,
and scheduler observations. Source/dataset selection, metadata audience,
transport/authentication decisions, runtime validation, and operational-store
access require their own scoped authorization. Execution, approval,
cancellation, and continuation controls remain disabled.

**Human Control:** The October 17, 2026 instruction authorizes one local
documentation-only plan-archive commit, followed by a dedicated S0 branch and
S0 synthetic feasibility only if repository governance permits. Stop at any
required governance prerequisite; otherwise stop after S0 for Human review.
Do not stage or commit S0 implementation changes. No push, merge, tag, PR,
publication, external-system modification or automatic progression to S1–S8
is authorized.
