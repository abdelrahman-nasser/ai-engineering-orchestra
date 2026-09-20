# AIO-034 Context

## Authorization and verified baseline

On 2026-09-20, the Human authorized creation of AIO-034, a separate Architect
design lock, implementation, validation, package-installation evidence,
independent review, final Architect review, and preparation of the Human Control
checkpoint. That authorization did not include final Human approval, Task
closure, staging, commit, push, merge, tag, release, publication, AIO-030 work,
AIO-035, or any real Agent invocation.

On 2026-09-20, after the reviewed Human Control checkpoint was presented, the
Human explicitly approved the architecture and public contract, granted final
acceptance, authorized Task closure, and authorized one local
implementation-and-closure commit on `main`. Push, merge, tag, release,
publication, AIO-030 work, AIO-035, and real Agent invocation remain
unauthorized.

Before Task creation, the repository was verified on branch `main` at HEAD
`eeba4584a29c32a7dd14b0fcc1a1196824bc1b6f`, subject
`feat: add Actor-to-Runtime applicability evidence (AIO-033)`. The worktree and
index were clean, AIO-033 was completed with 30/30 acceptance criteria and
recorded Human approval, and AIO-034 was absent. No fetch, pull, remote query,
branch switch, reset, stash, discard, stage, or commit was performed.

AIO-030 remains parked on local branch
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. It is not a dependency. Its branch,
files, ignored extension dependencies, generated outputs, and local exclusions
remain outside AIO-034.

## Need and dependency boundary

AIO-033 completed the positive Actor-to-Runtime topology branch. Existing Core
can now separately prove a valid Assignment, normalize current Actor
availability, validate an exact positive Actor-to-Runtime edge, and assess an
exact positive external Runtime-to-Inference edge as established, blocked, or
unresolved. No current API composes those results for one explicit
Agent/Runtime/Inference candidate.

AIO-034 depends directly on AIO-033. The completed dependency chain supplies
the existing Assignment, Actor Availability, Runtime and Inference Option,
compatibility, applicability, and pair-assessment contracts. Actor Selection is
pre-binding evidence and is not an assessment input; Assignment remains the
responsibility anchor.

## Intended bounded capability

The authorized capability is a pure derived in-memory assessment of one
caller-designated external-inference Agent candidate:

```text
Assignment + runtime_option_id + option_id
```

The result may state only whether all currently modeled hard prerequisites are
`satisfied`, whether explicit current negative evidence makes the candidate
`blocked`, or whether missing or unknown positive evidence leaves it
`unresolved`. Invalid parent evidence remains a separate atomic validation
failure with no ordinary outcome.

The caller owns truth, freshness, and coherent collection timing. Core captures
each raw input sequence once, reuses the same captured contexts through existing
validators, joins only exact case-sensitive identifiers, and derives a
deterministic result. No snapshot ID, persistent Candidate, serialized schema,
Actor-to-Inference relation, Runtime-owned-inference representation, Execution
Contract, authorization, adapter, or invocation is introduced.

## Governance and classification

`complexity: high` reflects composition across responsibility, current Actor
availability, positive topology evidence, and pair availability while
preserving context coherence and invalid-input versus ordinary-outcome
semantics. `risk: medium` reflects that a false positive could mislead later
authorization planning while the utility remains pure, in-memory,
non-authorizing, and non-invoking. `execution.mode: deep` is explicitly selected
for exhaustive scenario, boundary, deterministic-order, atomicity, and package
validation; it is not inferred from Complexity or Risk and establishes no
runtime or model fit.

The explicitly bound `architecture-change` Workflow requires Architect design,
Software Engineer implementation, independent Reviewer and Architect review,
the `documentation_consistency` and `independent_review` Quality Gates, and a
review-stage Human Control checkpoint.

## Human Control status

On 2026-09-20, a separate non-implementing Architect approved the exact design
before feature implementation. The lock requires the raw-input API, flattened
Assignment/Runtime/Inference identity, immutable atomic result, three ordinary
outcomes, nine deterministic reason codes, Human non-applicability finding,
fixed capture and validation order, exact joins, and all documented exclusions.
No schema, persistent entity, additional relation, snapshot contract,
authorization contract, or Execution Contract was required.

Final Architect review approved the complete implementation and independently
re-approved the corrected multiple-pair scenario test. A separate Reviewer and
semantic-audit execution returned PASS after the Reviewer finding was resolved.
The effective `documentation_consistency` and `independent_review` Gates pass.

On 2026-09-20, the Human explicitly approved the architecture/public contract
and granted final implementation acceptance. All 32 acceptance criteria are
complete, no waiver or exception is required, and the Task is closed as
`completed`. One local implementation-and-closure commit on `main` is
authorized; push, merge, tag, release, and publication remain unauthorized.
