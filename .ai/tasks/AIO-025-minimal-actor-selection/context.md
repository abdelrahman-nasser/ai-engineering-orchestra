# AIO-025 Context

## Current limitation

AIO can resolve canonical Workflow and Role definitions, compare supplied Actor
competencies with a Role, normalize an ephemeral Actor availability snapshot,
and validate an externally constructed Assignment. It cannot yet combine those
facts into deterministic evidence about which Actor, if any, is selectable for
one responsibility.

AIO-025 adds only that missing hard-constraint decision. It does not add a
Selection Policy, ranking, Assignment creation, authorization, or execution.

## Design lock

The canonical term is **Actor Selection**: pure, deterministic,
Provider-neutral resolution of one valid Task/Workflow/Stage/Role
responsibility against a caller-supplied Actor set and availability snapshot,
using exact competency coverage and availability facts only.

One invocation evaluates exactly this existing responsibility identity:

```text
(task_id, workflow_id, stage_id, role_id)
```

`task_id` and `workflow_id` come from the supplied Task. No selection ID,
candidate-set ID, responsibility ID, Actor Catalog, or serialized request
contract is introduced.

## Outcome semantics

A valid evaluation produces exactly one of:

- `selected`: exactly one eligible Actor is available and no eligible Actor has
  unknown availability.
- `ambiguous`: two or more eligible Actors are available.
- `indeterminate`: zero or one eligible Actor is available and at least one
  eligible Actor has unknown availability.
- `no_candidate`: no eligible Actor is available and none has unknown
  availability.

The critical conservative rule is:

```text
one eligible available Actor + one eligible unknown Actor
-> indeterminate
```

Treating that case as selected would invent a preference for known availability
over unknown availability. By contrast, two confirmed available Actors already
prove ambiguity even when additional eligible Actors are unknown.

Invalid input is separate from this outcome taxonomy. Invalid availability or
responsibility context produces `valid: false` and no outcome or partial
candidate evidence. Corrupt catalogs remain infrastructure errors.

## Composition and boundaries

Selection reuses `evaluate_actor_role_coverage()` and the AIO-024 availability
validator. Missing observations therefore continue to normalize to `unknown`,
and malformed snapshots are not reinterpreted as `no_candidate`.

The implementation may extract only the smallest private responsibility
resolver shared with Assignment. It must preserve AIO-023 validation behavior
and must not construct a temporary Assignment as a selection mechanism.

Selection returns immutable decision evidence using Actor IDs. Evidence is
sorted case-sensitively only for deterministic output; ordering is not ranking
or tie-breaking. Human and Agent Actors use the same constraints.

`selected` means uniquely selectable only within the supplied Actor set and
supplied availability snapshot. The caller owns snapshot freshness. Selection
does not prove that an Actor is globally best, permanently available, assigned,
authorized, reserved, executing, or sufficient for a Quality Gate.

## Workflow and Human control

The `architecture-change` Workflow governs this Task. An architect locked the
contract before implementation, a software engineer implements it, and
genuinely separate reviewer and architect reviews must evaluate the completed
change. Work stops at the review-stage Human Control checkpoint with the Task
still `in_progress` until explicit Human approval is recorded. No commit or
AIO-026 is authorized.
