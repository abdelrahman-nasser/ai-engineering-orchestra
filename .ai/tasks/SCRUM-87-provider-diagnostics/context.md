# SCRUM-87 context

## Final closure authority — October 20, 2026

The Human explicitly approved final acceptance of SCRUM-87 and accepted
implementation checkpoint `705c306c51278e6c218f316db7ab63244b58515c`. The approved
local closure-only commit subject is
`docs(alpha): finalize SCRUM-87 provider diagnostics task closure`.

Only `task.yaml`, `acceptance-criteria.md`, `context.md`, `review.md` and
`verification.md` in this Task directory may change. Product code, tests, the
verification helper, shared architecture, guides and Lane B remain unchanged.
Jira Done, push, merge, PR, tag, release, deployment and publication are excluded.

The Human accepts the enumerated native, packaging and Core verification limits
as nonblocking for this Task closure only; [review](review.md) preserves their
actual statuses. SCRUM-86 continues to own broader Core verification debt. No
mandatory Quality Gate is waived or failed/skipped/unexecuted result relabelled.

This authority supersedes earlier no-closure restrictions only for the bounded
closure action. The historical implementation context below, the precommit
review/verification reports and the roadmap's October 20 implementation
disposition describe earlier handoff states. Their pending-commit/acceptance
wording is superseded by the accepted checkpoint and this decision; their product
facts, failures, receipts and limitations remain historical evidence unchanged.
The canonical Task lifecycle and current closure records are authoritative.

Fresh closure checks and independent Security/CLI review approved the five-file
closure records. Final Human acceptance and all eight criteria are satisfied;
the canonical lifecycle is `completed`. Final lifecycle/staged-content checks
must preserve the accepted checkpoint and exact closure-only scope.

## Historical implementation context (preserved)

Human authorization on October 20, 2026 permits implementation, deterministic
offline testing and independent review of
[SCRUM-87](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-87).
The Jira implementation authorization of October 19 supersedes planning-only
restrictions. Commit and final Task closure remain separately controlled.

Verified clean starting tree: `D:\Dev\ITRU\worktrees\itru-core-usability`, branch
`feature/developer-alpha-usability-p0`, HEAD
`90fa7137e49fb60309200b0292375ec84d757852`. No applicable rule requires a branch
switch; this dedicated Core lane is retained. Historical evidence paths remain
historical. No completed P0 Task record is edited.

Existing functionality includes the exact approval-subject preview, closed local
configuration, labelled demo, compatible chat adapter and cancellation before
Tool invocation on provider failure. The gaps are passive local diagnostics,
actionable failure categories and the raw exception text printed by Alpha CLI.

The bounded CLI decision is additive `alpha diagnose --config <alpha.json>`.
It reuses config/file-security validation and checks credential presence only.
It never opens a lifecycle owner, authority registry, ledger or Journal, loads
work, contacts a provider, registers a Run or executes a Tool. Existing commands
retain their owner/recovery and approval ordering.

Alpha CLI rejection JSON retains `status` and `reason`, adds fixed `code` and
`recovery`, and omits raw exception text. Provider-failure CLI rows add a fixed
`provider_diagnostic`; their outcome and lifecycle reference remain
`provider_failed_before_tool`. These are local Alpha presentation changes, not
new Provider APIs or canonical Core contracts. No digest inputs change.
Alpha argument-parser errors also use fixed rejection JSON without echoing
argument values; their exit status remains 2. Non-Alpha parsing stays unchanged.

The security-sensitive-change Workflow applies with Software Engineer
implementation and independent Reviewer/Security Reviewer executions. Required
Quality Gates are documentation consistency and independent review. Final Human
review remains required. Project Rules directory `.ai/rules/` is absent.

Known Core-wide debt remains owned by SCRUM-86: retained 24 failures, 275 errors,
five skips and nonexecuted full C109. No failure or skip becomes PASS or waived.
No live network, inference, release build or privileged hostile fixture is used.
