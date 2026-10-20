# SCRUM-86 Phase 1 context

The implementation authority and handoff below are historical. The final section
records the later conditional checkpoint authority; final Task acceptance remains
pending.

The October 20, 2026 Human instruction and read-only
[SCRUM-86 Jira requirements](https://abdelrahmann-hegab.atlassian.net/browse/SCRUM-86)
authorize one low-risk offline remediation category, focused testing and review.
They prohibit production/runtime/security-contract changes, native/containment
probes, network/provider calls, installations, stage/commit and final closure.
The Jira read was required preflight; no network is used by tests or diagnostics.

Verified clean baseline: `D:\Dev\ITRU\worktrees\itru-core-usability`, HEAD
`e46aafd9790ced28a9ef6c1688c94bccdc4062b0`, initially on
`feature/developer-alpha-usability-p0`. The explicitly authorized dedicated
`feature/core-verification-debt-phase1` branch was created from that clean HEAD.
No reset, overwrite or additional worktree was used. SCRUM-87 remains completed.

This canonical Task has ID `ITRU-065`, the next unused canonical numeric ID
required by the Project cutover Task creation policy. It tracks only the bounded
Phase 1 handoff under parent Jira SCRUM-86 and does not complete the parent debt.
The initial untracked draft directory used the Jira label; it was moved within
this worktree to the canonical ID before handoff. No existing Task was renamed.
The standard-change Workflow applies. Implementation uses the Software Engineer
role; separate test-integrity/security and contract/documentation reviewers
evaluate the actual diff and evidence. Both required Quality Gates remain in
force. Project Rules directory `.ai/rules/` is absent.

## Selected category and authoritative expected behavior

Only `tests.test_cli.TestActiveProjectIntegration.test_help_is_available_without_project_and_uses_wrapper_name`
is remediated. Its root-help expectation predates the approved `alpha` command.
The explicit command list, wrapper-name check, zero exit status and prohibition
on project discovery must remain asserted, without deriving expected text from
the parser under test.

Grounding read before any assertion change:

- Completed ITRU-064's `context.md`, frozen product decisions 3-4, explicitly
  approves the Alpha CLI alongside unchanged Foundation commands.
- ITRU-064 acceptance A01/A16 and `docs/developer-alpha.md` document the console
  and `itru alpha --help` journey.
- Completed SCRUM-87's accepted implementation adds offline `alpha diagnose`.
- `itru/cli.py` independently implements the explicit root command list and
  help-only Alpha/diagnose parsers. Help exits during parsing before dispatch.
- AIO-015 acceptance AC-17/AC-18 requires rename safety and root/subcommand help
  (AC-02 specifies the thin wrapper); it does not freeze the root inventory before
  later approved work.

Historical migration/package/namespace assertions are separate categories.
In particular C111's name hides owned storage setup and external wheel evidence;
it is not admitted as a static packaging check. No such test is executed here.

## Evidence preservation

The retained 2,103-test broad result remains FAILED: 24 failures, 275 errors and
five skips. `failure-inventory.json` enumerates the exact historical events,
skip IDs and Markdown findings without importing test modules or running probes.
Historical path spellings in receipts remain historical. New active commands use
only the relocated workspace. Full C109 remains NOT RUN for this phase.

The original logs, comparison exports and completed Task records are read-only.
Fresh Phase 1 receipts are kept in this Task's `evidence/` directory, separately
from historical receipts. No failure is converted to skip, xfail or PASS by fiat.

## Conditional local checkpoint authority - October 20, 2026

The Human's ITRU-065 / SCRUM-86 checkpoint instruction, identifying Jira
authorization comment `#10746`, conditionally authorizes exactly one local commit:
`test(alpha): correct stale CLI help expectation`. This supersedes the earlier
stage/commit prohibition only for the same 15-file reviewed candidate and necessary
checkpoint evidence updates. The expected parent is
`e46aafd9790ced28a9ef6c1688c94bccdc4062b0` on
`feature/core-verification-debt-phase1` in the relocated worktree.

The original scope exclusion was "Stage, commit, push, merge, PR, tag, release,
deployment and publication". Only staging the exact candidate and one local
checkpoint commit are now permitted. No final acceptance, Task closure, further
remediation, second commit, publication or Jira state change is authorized.
ITRU-065 remains `in_progress`; SCRUM-86 remains open. The final Human acceptance
criterion stays unchecked.

Scoped Markdown lint is nonmandatory for this bounded checkpoint; its result
remains NOT RUN. The governing justification and independent confirmation are
recorded in the checkpoint sections of `phase1-report.md` and `review.md`.
