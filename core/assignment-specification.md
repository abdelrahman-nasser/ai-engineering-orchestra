# AI Engineering Orchestra - Assignment Specification

Version: 0.1.0

This document defines the canonical Assignment contract for AI Engineering
Orchestra v0.1.

---

## 1. Purpose

An **Assignment** is an immutable, provider-neutral value binding one concrete
Actor identity to one Role required at one Stage of the Workflow explicitly
governing one Task.

Assignment records a responsibility choice made outside the Assignment contract,
whether directly by a caller or after considering Actor Selection evidence. It
answers **who has been selected for this responsibility?** It does not choose,
rank, recommend, authorize, execute, or persist an Actor.

```text
Assignment = responsibility binding
```

Assignment is not an execution session, permission grant, availability
reservation, Workflow state, approval, or Quality Gate result.

---

## 2. Architectural Boundary

The following concepts remain separate:

- **Role** declares a reusable responsibility and required competencies.
- **Actor** identifies a concrete Human or Agent candidate and its competencies.
- **Actor-Role competency coverage** establishes eligibility evidence.
- **Actor Availability Observation** supplies ephemeral availability evidence.
- **Actor Selection** resolves hard eligibility and availability constraints into
  decision evidence without creating an Assignment.
- **Assignment** records which eligible Actor was selected for one responsibility.
- **Execution Policy** may later define how assigned work should be performed.
- **Execution Session** is actual execution and is not defined by AIO-023.
- **Human Control** governs approval authority and protected decisions.
- **Quality Gates** evaluate governance conditions independently of Assignment.

```text
eligible != assigned
selected != assigned
assigned != authorized
Assignment valid != Quality Gate PASS
Assignment complete != Workflow complete
```

An Assignment never selects a substitute when its named Actor is incompatible.
A caller constructing an Assignment from a `selected` Actor Selection result must
still pass this contract's validation.

---

## 3. Canonical Assignment Contract

The v0.1 Assignment contract contains exactly five required fields:

| Field | Purpose |
| --- | --- |
| `task_id` | ID of the one Task to which the responsibility applies |
| `workflow_id` | ID of the Workflow explicitly governing the Task |
| `stage_id` | Workflow-scoped Stage containing the responsibility |
| `role_id` | Canonical Role required by that Stage |
| `actor_id` | Concrete Actor selected for the responsibility |

```yaml
task_id: AIO-023
workflow_id: architecture-change
stage_id: review
role_id: reviewer
actor_id: reviewer-agent-1
```

All values are nonempty strings. Referenced identifiers are intentionally not
enumerated by the structural schema; their existence is semantic context.

`workflow_id` intentionally repeats the Task's explicit `workflow` binding. It
makes the Assignment self-describing, preserves the Workflow scope needed to
resolve `stage_id`, and lets validation detect stale or mismatched bindings
instead of silently correcting them.

Assignment has no `assignment_id`. There is no persistence, lifecycle, audit
history, or execution link requiring a separate durable identifier.

---

## 4. Responsibility Identity

The unique responsibility-binding key is:

```text
(task_id, workflow_id, stage_id, role_id)
```

`actor_id` is the selected value and is not part of the key. More than one
Assignment for the same key is invalid, whether the repeated values name the
same Actor or different Actors. There is no last-assignment-wins behavior.

AIO-023 supports one Actor per responsibility key. Workflow `required_roles`
defines no multiplicity, headcount, panel, pair, or requirement-slot identity.
A single Actor may hold different responsibility keys when competency-compatible
and when no applicable separation rule prohibits it.

---

## 5. Individual Validation Context

Individual semantic validation consumes:

- one schema-valid normalized Task,
- one valid Workflow Catalog,
- the valid framework Role Catalog,
- a schema-valid caller-supplied Actor sequence, and
- one Assignment.

There is no Task catalog or Actor catalog. The caller supplies Actor values, and
their IDs must be unique across that supplied context. Duplicate Actor IDs are
ordinary invalid caller data reported as `duplicate_actor_id`; the validator
does not guess which value was intended.

Broken or corrupt Workflow or framework Role catalogs are infrastructure
failures and raise their existing catalog error. Catalog corruption is not
reinterpreted as an invalid Actor or Assignment.

---

## 6. Deterministic Validation Order

Validation short-circuits in this dependency-aware order:

1. Actor context IDs are unique.
2. `Assignment.task_id` equals the supplied Task `id`.
3. The Task explicitly declares `workflow`.
4. `Assignment.workflow_id` equals `Task.workflow`.
5. The Workflow resolves through the supplied Workflow Catalog.
6. The Stage resolves inside that Workflow.
7. The Role resolves through the framework Role Catalog.
8. The Stage lists that Role in `required_roles`.
9. The Actor resolves exactly once in the supplied Actor sequence.
10. Existing Actor-Role competency coverage reports `compatible: true`.

The validator never infers a Workflow from Task type, corrects an identifier, or
selects another Actor.

Stable individual finding codes are:

- `duplicate_actor_id`
- `task_id_mismatch`
- `task_workflow_missing`
- `workflow_id_mismatch`
- `workflow_not_found`
- `stage_not_found`
- `role_not_found`
- `role_not_required`
- `actor_not_found`
- `actor_role_incompatible`

Incompatible results retain `ActorRoleCoverage`, including deterministic missing
competencies or the `role_required_capabilities_empty` diagnostic.

---

## 7. Assignment Sequence Validation

Sequence validation accepts ordinary in-memory Assignment values. It does not
define a serialized or persisted `AssignmentSet` domain object.

The result distinguishes:

```text
valid
= supplied bindings and input context satisfy Assignment invariants

complete
= every distinct Workflow Stage/Role requirement has one valid binding
```

A partial sequence can be valid and incomplete. `complete` is `None` when the
Task's governing Workflow requirement set cannot be determined honestly, such
as when the Task omits its Workflow or that Workflow cannot be resolved.

Only individually valid Assignments whose responsibility key occurs exactly
once cover a requirement. All values sharing a duplicate key cover nothing and
produce `duplicate_assignment_binding`.

Unassigned requirements use the same four-part key. They are ordered by Workflow
Stage declaration order and then Role declaration order. Stages without
`required_roles` add no requirements. Repeated Role IDs within one Stage collapse
to one responsibility because current Workflow semantics define no multiplicity.

---

## 8. Reviewer Separation Evidence

Sequence validation reports `reviewer_actor_matches_implementer` when the same
Actor ID appears in valid, unique `software-engineer` and `reviewer` bindings for
the same Task and Workflow.

```text
equal Actor IDs -> definite Actor-level identity conflict
unequal Actor IDs -> no Actor-level conflict detected
```

This finding is returned separately from generic validity and completeness. It
does not change either value and does not create a Quality Gate result. Unequal
IDs do not prove separate execution, actual review, resolved findings, approval,
or `independent_review` PASS.

AIO-023 defines no automatic Security Reviewer/implementer, Architect/Reviewer,
or all-reviewer uniqueness rule.

---

## 9. Result Contracts

`AssignmentValidationResult` contains only:

- `valid`
- immutable `findings`
- `coverage`, which is `ActorRoleCoverage` or `None`

`AssignmentSetValidationResult` contains only:

- `valid`
- `complete`, which is `bool` or `None`
- immutable `findings`
- immutable `unassigned_requirements`
- immutable `separation_findings`

Assignment semantics use valid/invalid and complete/incomplete terminology.
PASS, FAIL, and ERROR remain Verification Check, infrastructure-reporting, and
Quality Gate terminology.

---

## 10. Authority and Execution Boundaries

Assignment grants no filesystem, shell, network, credential, Provider, Human
approval, permission, or execution authority. Actor kind grants none of those
things either.

Assignment contains no Provider, model, runtime, reasoning, prompt, tools,
timeout, cost, quota, result, or runtime session ID. Availability is not
inspected. No Stage becomes current, active, complete, or otherwise stateful
because an Assignment references it.

Actor-to-Runtime Applicability Evidence is a separate positive relation defined
by `core/actor-runtime-applicability-specification.md`. A valid Assignment does
not prove Runtime applicability, an applicability edge does not create an
Assignment, and `runtime_option_id` is not an Assignment field.

Agent Execution Candidate Prerequisite Assessment may consume one valid
Assignment as its immutable responsibility anchor together with separate
current availability and topology evidence. That derived assessment neither
changes Assignment validity nor attaches Runtime or Inference fields to the
Assignment. Its separate contract is defined in
`core/agent-execution-candidate-prerequisite-specification.md`.

Agent Execution Authorization Evidence may reproduce one complete valid
Assignment as the first five fields of an exact action subject. That separate
caller-attested evidence does not change the Assignment or make responsibility
authorization-bearing. Conversely, Task approval, Assignment validity, or
Assignment completeness does not create authorization evidence. The evidence
contract is defined in
`core/agent-execution-authorization-evidence-specification.md`.

---

## 11. Lifecycle and Persistence Boundaries

Assignment has no proposed, accepted, active, completed, failed, or cancelled
status and no reassignment history. Changing `actor_id` creates a different
immutable value.

AIO-023 defines no `.ai/assignments/`, Task embedding, database, event log,
runtime state store, Actor inventory, Actor registry, or CLI command. Assignment
values are caller-supplied and in memory.

---

## 12. Structural and Runtime Authority

Authority is ordered as follows:

1. `core/assignment-specification.md` is the semantic authority.
2. `schemas/assignment.schema.json` is subordinate structural authority.
3. `engineering_orchestration.assignment` provides pure semantic validation.
4. `schemas/tests/validate_assignment.py` and fixtures are regression tooling.

The runtime module performs no I/O, discovery, persistence, Actor selection,
execution, or global-state mutation. Schema validity alone does not prove that
references resolve or that an Actor is compatible.
