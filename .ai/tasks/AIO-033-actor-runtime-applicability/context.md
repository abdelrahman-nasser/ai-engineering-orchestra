# AIO-033 Context

## Authorization and verified baseline

On 2026-09-20, the Human authorized creation, Architect design lock,
implementation, validation, independent reviews, and preparation of the AIO-033
Human Control checkpoint. That initial authorization expressly withheld final Human
architecture/schema approval, final acceptance, Task closure, staging, commit,
push, merge, tag, release, publication, AIO-030 work, and AIO-034.

On 2026-09-20, after the complete reviewed implementation and validation
evidence were presented at that checkpoint, the Human explicitly approved the
architecture and schema, granted final acceptance, authorized Task closure, and
authorized one local closure commit on `main`. Push, merge, tag, release,
publication, AIO-030 work, and AIO-034 remain unauthorized.

Before Task creation, the repository was verified on branch `main` at HEAD
`5757066162440f12ef92b9748367810136dac238`, subject
`feat: add Runtime-to-Inference pair availability assessment (AIO-032)`. The
worktree and index were empty, AIO-032 was completed and closed, and no AIO-033
Task directory or tracked artifact existed. No fetch, pull, remote query, branch
switch, reset, stash, or discard was performed.

AIO-030 remains parked on local branch
`feature/aio-030-vscode-control-center` at
`5a4dae8ffcca8f986c0eb42755db9a958c57d187`. It is not a dependency, and its
branch, files, ignored dependencies, generated outputs, and local exclusions
remain outside AIO-033.

## Need and dependency boundary

AIO-032 can establish joint availability for each supplied positive external
Runtime-to-Inference edge, but its result deliberately has no Actor input and
does not prove Actor applicability. Actor Selection and Assignment establish a
logical Actor responsibility but contain no Runtime binding. Core therefore has
no validated positive evidence joining a selected or assigned Agent Actor to an
Agent Runtime Option.

AIO-033 depends directly on the completed AIO-032 baseline. Its endpoint
contracts were established by AIO-021 for Actor and AIO-029 for Agent Runtime
Option within the completed transitive chain. The new relation must remain
independent from pair availability and must not consume or change AIO-032.

## Architect design lock

Before feature implementation, a separate non-implementing Architect approved
the bounded design without scope expansion. The canonical term is
**Actor-to-Runtime Applicability Evidence**. The value contains exactly
`actor_id` and `runtime_option_id` and represents only caller-supplied positive
applicability evidence for one known Agent Actor and one known Agent Runtime
Option within one supplied evaluation context.

The locked public API is
`engineering_orchestration.actor_runtime_applicability`, with frozen evidence,
finding, and validation-result dataclasses and
`validate_actor_runtime_applicability(evidence, actors, runtime_options)`.
Inputs are captured once in Actor, Runtime, evidence order. Actor-context and
Runtime-inventory findings precede relation processing. Relation findings are
ordered as duplicate exact pairs, unknown Actor IDs, known Human Actor IDs, and
unknown Runtime Option IDs, with exact identifier sorting inside each category.
The new Human-endpoint code is
`actor_runtime_applicability_requires_agent_actor`; established Actor and
Runtime diagnostic codes and messages remain unchanged. Any finding produces no
normalized evidence; valid evidence is sorted by exact
`(actor_id, runtime_option_id)` only for canonical representation.

## Classification and governance

`complexity: high` reflects a new cross-domain semantic authority and schema,
Agent-only endpoint semantics, foreign-reference validation, deterministic
multi-category diagnostics, packaging, and independent architectural review.
`risk: medium` reflects that incorrect applicability evidence could mislead later
execution planning while the API remains pure, in-memory, non-authorizing, and
non-invoking. `execution.mode: deep` is explicitly selected for boundary
analysis, exhaustive relation validation, package proof, and independent review;
it is not inferred from Complexity or Risk.

The explicitly bound `architecture-change` Workflow requires Architect design,
Software Engineer implementation, and independent Reviewer plus Architect
review. The effective Quality Gates are `documentation_consistency` and
`independent_review`. Both Gates passed, and the review-stage Human Control
checkpoint was satisfied by explicit Human approval on 2026-09-20.

## Human Control status

Human architecture/schema approval and final acceptance were explicitly
granted on 2026-09-20. AIO-033 is `completed`, and one local implementation and
closure commit on `main` is authorized. Push, merge, tag, release, publication,
AIO-030 work, and AIO-034 remain unauthorized.
