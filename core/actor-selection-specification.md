# AI Engineering Orchestra - Actor Selection Specification

Version: 0.1.0

This document defines the canonical Actor Selection contract for AI Engineering
Orchestra v0.1.

---

## 1. Purpose

**Actor Selection** is pure, deterministic, Provider-neutral resolution of one
valid Task/Workflow/Stage/Role responsibility against a caller-supplied Actor
set and availability snapshot, using exact competency coverage and availability
facts only.

Actor Selection produces decision evidence. It does not rank, assign, authorize,
reserve, or execute Actors.

```text
Actor competency eligibility
+
Actor Availability Observation
-> Actor Selection
```

---

## 2. Responsibility Granularity

One invocation evaluates exactly one responsibility:

```text
(task_id, workflow_id, stage_id, role_id)
```

The selector derives `task_id` and `workflow_id` from the supplied Task and
accepts `stage_id` and `role_id` directly. The existing four-part identity is
sufficient. Actor Selection defines no `selection_id`, `candidate_set_id`,
`responsibility_id`, public Responsibility request object, or Actor Catalog.

The responsibility must resolve through this chain:

```text
Task -> Workflow -> Stage -> required Role
```

Selection may reuse the smallest private resolution logic shared with Assignment.
It must not construct a temporary Assignment to validate this context.

---

## 3. Inputs

The pure selector consumes:

- one schema-valid normalized Task that explicitly declares its Workflow;
- one `stage_id`;
- one `role_id`;
- one valid loaded Workflow Catalog;
- the valid loaded framework Role Catalog;
- a caller-supplied sequence of schema-valid normalized Actors; and
- a caller-supplied sequence of Actor Availability Observations.

There is no Task catalog, Actor Catalog, registry, project Actor directory,
serialized Selection Request, or persisted candidate set. Catalog corruption is
an infrastructure failure and preserves the existing `WorkflowCatalogError` or
`RoleCatalogError` behavior.

Task Complexity, Risk, and Execution Mode are not selection inputs. They do not
differentiate current Actor identities.

---

## 4. Context Validity

Selection first reuses AIO-024 snapshot validation and normalization. This owns:

- duplicate Actor-ID rejection;
- duplicate observation rejection;
- unknown observation Actor rejection;
- deterministic availability finding order; and
- normalization of every missing observation to `unknown`.

The selector then validates responsibility context in dependency order:

1. the Task explicitly declares a nonempty Workflow;
2. the Workflow Catalog is valid;
3. the Task Workflow resolves;
4. the Stage resolves within that Workflow;
5. the Role Catalog is valid;
6. the Role resolves; and
7. the Stage lists the Role in `required_roles`.

Ordinary invalid context produces deterministic findings such as:

- `duplicate_actor_id`
- `duplicate_actor_availability`
- `actor_not_found`
- `task_workflow_missing`
- `workflow_not_found`
- `stage_not_found`
- `role_not_found`
- `role_not_required`

Invalid input is not a selection outcome. Catalog infrastructure failures are
not ordinary invalid-context findings.

---

## 5. Eligibility Composition

Selection evaluates each supplied Actor with the existing
`evaluate_actor_role_coverage()` semantics. An Actor is eligible if and only if
that evaluator reports compatible coverage for the resolved Role.

Matching remains exact and case-sensitive. Extra competencies do not hurt
eligibility, Actor kind does not affect it, and a Role with no semantically
approved required competencies is non-matchable under the existing coverage
contract.

Selection does not duplicate competency comparison and introduces no competency
strength, level, score, weight, alias, implication, or rank.

---

## 6. Availability Composition

Selection consumes the valid normalized snapshot returned by
`validate_actor_availability()`. Only eligible Actors participate in the outcome
calculation:

- eligible `available` Actors are confirmed current candidates;
- eligible `unavailable` Actors are excluded from current availability; and
- eligible `unknown` Actors remain unresolved candidates.

```text
unknown != unavailable
```

A missing observation is therefore `unknown`, not `unavailable`. Selection adds
no independent missing-observation, duplicate, or unknown-reference rule.

If snapshot validation fails, Selection is invalid and produces no outcome. It
must not transform malformed availability input into `no_candidate`.

---

## 7. Outcome Taxonomy

Actor Selection has exactly four valid outcomes:

- `selected`
- `ambiguous`
- `indeterminate`
- `no_candidate`

Invalid input is represented separately through `valid: false` and never by an
additional outcome such as `invalid`, `error`, or `failed`.

### `selected`

Exactly one eligible Actor is positively known as `available`, and zero other
eligible Actors have `unknown` availability.

```text
eligible available = 1
eligible unknown = 0
```

Other eligible Actors, if any, are positively `unavailable`.

### `ambiguous`

Two or more eligible Actors are positively known as `available`. Unknown
eligible Actors do not change this outcome because ambiguity is already proven,
but their IDs remain in the evidence.

### `indeterminate`

Current information is insufficient to establish either one uniquely selectable
Actor or that no selectable Actor exists. This outcome applies when there are
zero or one eligible available Actors and at least one eligible unknown Actor.

The mandatory conservative case is:

```text
one available + one unknown -> indeterminate
```

Returning `selected` would introduce an unauthorized preference of known
availability over unknown availability.

### `no_candidate`

Complete current hard-constraint evidence establishes that no Actor is
selectable. This requires zero eligible available Actors and zero eligible
unknown Actors.

The closed reasons distinguish an empty supplied Actor set, a nonempty set with
no eligible Actor, and a set whose eligible Actors are all unavailable.

---

## 8. Complete Decision Table

| Condition | Outcome | Reason |
| --- | --- | --- |
| Supplied Actor set is empty | `no_candidate` | `candidate_set_empty` |
| Supplied set is nonempty and eligible set is empty | `no_candidate` | `no_eligible_actor` |
| Eligible available is two or more | `ambiguous` | `multiple_available_actors` |
| Eligible unknown is one or more and available is zero or one | `indeterminate` | `availability_unknown` |
| Eligible available is one and unknown is zero | `selected` | `unique_available_actor` |
| Eligible set is nonempty and every eligible Actor is unavailable | `no_candidate` | `all_eligible_unavailable` |

The ambiguity rule precedes the unknown rule. Thus two available Actors plus an
unknown Actor is `ambiguous`, while one available Actor plus an unknown Actor is
`indeterminate`.

---

## 9. Result Contract

The canonical immutable in-memory result contains:

- `valid: bool`
- `responsibility_key: tuple[str, str, str, str] | None`
- `outcome: ActorSelectionOutcome | None`
- `reason: ActorSelectionReason | None`
- `selected_actor_id: str | None`
- `eligible_actor_ids: tuple[str, ...]`
- `available_actor_ids: tuple[str, ...]`
- `unknown_actor_ids: tuple[str, ...]`
- `findings: tuple[ActorSelectionFinding, ...]`

The outcome enum values are exactly the four values in Section 7. The closed
valid-outcome reason values are:

- `unique_available_actor`
- `multiple_available_actors`
- `availability_unknown`
- `candidate_set_empty`
- `no_eligible_actor`
- `all_eligible_unavailable`

For `selected`, `selected_actor_id` is the one available eligible Actor ID. It is
`None` for every other outcome.

Candidate evidence contains only Actor IDs:

- `eligible_actor_ids` contains every competency-compatible Actor;
- `available_actor_ids` contains eligible Actors whose normalized state is
  `available`; and
- `unknown_actor_ids` contains eligible Actors whose normalized state is
  `unknown`.

Eligible unavailable IDs are derivable from those sets and have no dedicated
field. The result never retains full Actor objects.

---

## 10. Invalid Results

An invalid result is atomic:

```text
valid = false
responsibility_key = None
outcome = None
reason = None
selected_actor_id = None
eligible_actor_ids = ()
available_actor_ids = ()
unknown_actor_ids = ()
findings != ()
```

Valid results contain no findings. Partial candidate evidence is not exposed
when the snapshot or responsibility context is invalid.

---

## 11. Determinism Without Preference

Eligible, available, and unknown Actor IDs are sorted in case-sensitive ascending
order. Sorting canonicalizes evidence only.

```text
ordering != preference != ranking
```

Selection never uses declaration order, lexical first-wins behavior, randomness,
Human preference, Agent preference, price, competency strength, or any other
tie-break. Repeated identical inputs produce equal results.

Human and Agent Actors use identical coverage, availability, and outcome rules.
Actor kind grants no preference, approval authority, or execution authority.

---

## 12. Candidate-Set and Snapshot Scope

`selected` means uniquely selected within the caller-supplied Actor candidate set
and caller-supplied Availability snapshot. It does not mean globally best, the
only capable Actor in an organization, or permanently available.

AIO-025 accepts the supplied AIO-024 snapshot semantics. The caller owns
freshness. Selection introduces no timestamp, clock, expiry, polling, recheck,
history, load, capacity, reservation, lease, or lock.

---

## 13. Assignment Boundary

```text
Selection = decision evidence
Assignment = responsibility binding
```

Selection returns only the selected Actor ID and evidence. It does not create an
Assignment, proposed Assignment, pending Assignment, or Assignment lifecycle
state.

A caller may subsequently construct an Assignment using the same responsibility
key and `selected_actor_id`. That Assignment must still pass AIO-023 validation.
Selection neither bypasses nor substitutes for Assignment validation.

Existing Assignments are not selector inputs. Reviewer/implementer identity
separation remains later Assignment-sequence evidence and does not become a
Selection Policy. A selected reviewer does not establish
`independent_review` satisfaction.

---

## 14. Authority, Reservation, Execution, and Quality Boundaries

```text
selected != assigned
selected != authorized
selected != reserved
selected != executing
selected != Quality Gate PASS
```

Selection grants no filesystem, shell, network, credential, permission, Human
Control, approval, or execution authority. It changes no project or runtime
responsibility state, reserves no availability, invokes no Actor, and evaluates
no Quality Gate.

Selection contains no Provider, model, runtime, reasoning, prompt, tool, cost,
quota, or execution-requirement field and performs no Provider lookup.

---

## 15. Runtime and Structural Authority

The pure runtime implementation is:

`engineering_orchestration.actor_selection`

It uses immutable values and pure functions with no I/O, network, clock,
randomness, persistence, or global mutable state.

Actor Selection is derived in-memory runtime evidence. AIO-025 defines no
serialized Selection Request or Decision contract and therefore adds no Actor
Selection schema. Existing Actor, Actor Availability Observation, Assignment,
Task, Workflow, Role, and Project Manifest schemas remain unchanged.

---

## 16. Exclusions

AIO-025 does not define or implement:

- Actor ranking, scoring, weights, competency strength, or tie-breaking
- Task Assessment or Complexity-, Risk-, or Execution Mode-based selection
- Selection Policy, Human override machinery, or recommendation policy
- Actor discovery, catalogs, registries, persistence, or selection history
- Assignment creation, proposed Assignments, reassignment, or allocation policy
- reviewer-separation policy or existing-Assignment inputs
- scheduling, reservations, locks, freshness, load, capacity, or polling
- Provider, model, runtime, reasoning, cost, quota, or Provider Adapter behavior
- Execution Requirements, Execution Policy, invocation, or authorization
- Quality Gate Result models, CLI commands, or AIO-026
