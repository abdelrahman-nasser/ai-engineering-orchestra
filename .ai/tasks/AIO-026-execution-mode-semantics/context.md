# AIO-026 Context

## Current limitation

AIO already records Task `complexity`, `risk`, and `execution.mode`, but the
existing Execution Mode description is not precise enough for future
Provider/model option matching. It also conflicts with Workflow ownership by
suggesting that mode changes stage count, gates, approval, or model capability.

The dormant Model Tier values `fast`, `standard`, and `high` mix latency and
capability axes. They cannot support deterministic matching and have no active
schema or runtime behavior.

## Locked semantics

Complexity describes the work's inherent reasoning difficulty, engineering
depth, coordination, and decomposition demand. Risk describes the impact if
execution is wrong. They are independent descriptive facts; neither selects a
Workflow, Execution Mode, model, authority level, or approval policy.

Execution Mode is the Provider-neutral, Task-wide minimum required engineering
execution posture within an already selected Workflow. It covers cumulative
process depth, rigor, analysis and decomposition, evidence discipline, and
bounded self-direction. It is ordered exactly:

```text
lite < standard < deep < critical
```

A posture satisfies the same or any lower minimum. The order expresses process
depth only. It is neither an exact ceiling nor a Task classification.

Each description is a cumulative minimum obligation, not a ceiling. A lighter
mode does not require the additional obligations of higher modes, but never
prohibits extra rigor, analysis, decomposition, evidence, validation, or bounded
self-direction.

- `lite` is the smallest floor for well-bounded work: a coherent direct path,
  sufficient context and evidence, proportionate validation, decomposition
  needed for coherence, and narrowly bounded self-direction.
- `standard` includes `lite` plus explicit planning, disciplined execution,
  validation, self-checking, routine bounded self-direction, and explicit
  evidence for material claims.
- `deep` includes `standard` plus deliberate decomposition, trade-off and edge
  analysis, broader evidence, probing validation, and sustained bounded
  self-direction.
- `critical` includes `deep` plus the strongest scrutiny, assumption challenge,
  failure and safety analysis, traceability, corroboration, the strongest
  bounded self-direction, and conservative escalation of unresolved uncertainty.

Expected autonomy means bounded self-direction inside existing scope,
permissions, Policies, and Human controls. It never grants authority.

## Boundaries

All current Human and Agent responsibilities inherit the effective Task mode.
Stage-, Role-, and responsibility-specific overrides are unsupported, and mode
must not be inferred from Stage or Role identity or capabilities.

Workflow is governance choreography. Execution Mode changes the depth applied
inside that choreography; it does not select a Workflow, add, remove, or reorder
stages, change Roles, gates, or checkpoints, or establish their results.

Explicit Task values override Project defaults independently for Complexity,
Risk, and Execution Mode. No mapping among those values is implied.

Model Tier is deprecated. Its former mixed-axis values are withdrawn and
non-consumable until evidence-backed Provider/model inventory research defines
stable option-side dimensions in a future contract. AIO-026 adds no replacement
enum, mapping, routing, inventory, adapter, or invocation behavior.

## Workflow and Human control

The `architecture-change` Workflow governs AIO-026. The implementation remains
`in_progress` at the review-stage Human Control checkpoint. Independent Reviewer,
Architect, and explicit Human approval evidence must be recorded before closure.
