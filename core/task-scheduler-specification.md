# Minimal Task DAG and scheduler

Version: 0.1.0. ITRU-063 owns this additive Developer Alpha contract.

## Explicit graph and dependency identity

TaskNode contains exactly task_id and definition_reference. Both are opaque,
nonempty, exact UTF-8 strings. Task identity is the unchanged Project-scoped Task
ID; the reference pins the definition already enrolled through ITRU-062.
TaskDependency contains exactly task_id and prerequisite_task_id; this ordered
pair is its identity. An edge (A, B) means A waits for B. There are no aliases,
case folding, edge IDs, priorities, weights or implicit Workflow-stage edges.

build_task_graph accepts exact tuples of nodes and edges, bounded to 1000 nodes
and 10000 edges. The graph is closed: every endpoint must be supplied. Duplicate
nodes, duplicate edges, self-edges, unknown endpoints and cycles reject the whole
graph with DependencyError. Empty graphs are valid. Returned TaskGraph contains
nodes sorted by task_id, edges by their exact pair, and topological_order from
Kahn traversal choosing the lexically smallest currently available Task. Traversal
is iterative. Directly constructed graphs are revalidated before use.
prerequisites returns sorted immediate IDs and rejects unknown Tasks.

The caller resolves only explicitly selected Task definitions and translates
their existing dependencies lists into these edges. Graph preparation does not
read task.yaml, discover Tasks, validate repository catalog uniqueness, change
Workflow order or infer dependency readiness from definition status.

## Persisted snapshot boundary

SchedulingSnapshot contains store_id, project_id and an exact tuple of unchanged
ITRU-062 TaskSnapshot values from one owned Store. This is one complete graph
scheduling domain. No extra or duplicate Task observation is accepted. Missing
Tasks stay unresolved and suppress ALL new selection because their occupancy is
unknown. Supplied Tasks must match each pinned definition_reference. The snapshot
normalizes Tasks by exact task_id; each Task retains its chronological Run tuple.

Evaluation checks exact value types, known states, positive bounded revisions,
Run subject ownership/identity, Result identity scope, duplicate Run/Result IDs,
revision order and observable lifecycle coherence. At most 10000 Runs are accepted.
Invalid input raises ValueError without partial decisions. These checks cannot
authenticate provenance, reconstruct omitted history, detect a coherent rollback
or establish freshness. Caller must obtain the verified current Store snapshot;
invented dataclasses, JSON or Journal evidence cannot prove operational facts.
Store queries remain authoritative for enrolled lifecycle; task.yaml remains
intent/governance evidence. No upstream storage format or behavior changes.

The local caller serializes snapshot collection, evaluation and registration
against every mutation in this graph domain. ITRU-062 pages are individually
transactional; collecting multiple pages without this exclusion is not a coherent
snapshot. Missing/uncertain collection must stop scheduling. Other domains and
workers are outside this local contract. A complete snapshot includes every Task
whose active Run consumes capacity in the domain, including disconnected nodes.

## Dependency evaluation and selection

Each Task receives DependencyEvaluation(task_id, state, unsatisfied_task_ids).
An immediate dependency is satisfied only by persisted Task state completed.
Run success alone, cancelled Tasks and Journal summaries do not satisfy it.
Unsatisfied IDs are sorted. State is blocked if any observed prerequisite is
not completed, otherwise unresolved if a prerequisite is missing, otherwise
ready. Negative and missing facts remain in the complete unsatisfied list.

TaskEvaluation contains task_id, state and that dependency evaluation. Its state
uses this precedence: missing observation unresolved; historical interrupted or
effect_ambiguous unsafe; completed/cancelled terminal; pending/running active;
other prior work or blocked/in_progress manual; unmet dependencies blocked or
unresolved; otherwise ready. Only planned Tasks without Run history can be ready.
Neither terminal attempts nor blocked Tasks automatically restart.

evaluate_schedule takes a graph, snapshot and explicit max_concurrency, an exact
integer in 1..100 (booleans rejected). Pending and running Runs occupy slots.
Occupied Run IDs are sorted. The decision state is incomplete_snapshot if any
Task is missing, else over_capacity if occupied exceeds the limit, else evaluated.
Only evaluated decisions select work. Select the first ready Task IDs in exact
lexical order, at most max_concurrency minus occupied count. At saturation select
nothing; above the bound select nothing without cancelling existing work.
Topological_order is graph evidence; selection tie breaking uses task_id.

SchedulerDecision contains exactly graph, normalized snapshot, max_concurrency,
state, occupied_run_ids, evaluations and selected_task_ids. All values are frozen
in-memory evidence. Equal input sets produce equal complete decisions independent
of tuple ordering. There is no clock, random value, callback, I/O, Tool/native
execution, state mutation, retry loop, persisted queue or decision serializer.

The bound governs proposed new work in one evaluation. A decision reserves no
slot and cannot enforce a system-wide bound against concurrent or stale callers.
Before registration the sole local coordinator must recheck all graph revisions,
dependency completion, snapshot completeness and capacity under its serialization
boundary, then use existing Store revision CAS. Repeated evaluation is descriptive
and idempotent; it is never a request to repeat an invocation.

## Assignment handoff and Human authority

prepare_assignment_handoff re-evaluates graph/snapshot and checks one exact,
externally chosen Assignment's five nonempty fields. Only a currently selected
Task produces AssignmentHandoff(assignment, checkpoint, decision). The Checkpoint
uses exact store_id/project_id/task_id/revision. Full decision evidence retains
dependency definitions and revisions. This API does not select an Actor, resolve
a Workflow, assess Role coverage or replace existing contextual validate_assignment.

The caller must validate the Assignment in its actual Task/Workflow/Role/Actor
context, then freshly resolve effective mode and prerequisites, prepare a new Run,
obtain live ownership and fresh exact authenticated Grant, and pass unchanged
admission, claim/JIT and controlled invocation boundaries. Commit the ITRU-062
running marker before invocation. A handoff creates no Run, capability, permission,
Grant, admission or execution authority. Human/policy approval is never inferred
from selection, persisted state, a checkpoint or Journal evidence.

Restart evaluation uses recovered persisted snapshots. Pending recovery becomes
cancelled-before-start and running recovery becomes interrupted under ITRU-062.
The scheduler returns manual or unsafe and initiates neither continuation nor
replay. effect_ambiguous stays terminal for its attempt and prevents continuation.
Explicit continuation of otherwise eligible work stays entirely in ITRU-062 and
still requires its fresh trusted authorizer plus fresh upstream execution authority.
Journal remains descriptive; it cannot manufacture an original Result or restore
a lost capability. No exactly-once invocation claim is made.

## Developer Alpha API boundary

Use build_task_graph, prerequisites, evaluate_schedule and
prepare_assignment_handoff directly with explicitly resolved values. Existing
Store get_task/get_run/checkpoint/page provide lifecycle queries; TaskEvaluation
and selected_task_ids provide the minimum scheduler queries. No new persistence,
schema, CLI, UI, routing, retry/failover policy, cost optimization, distributed
scheduler or remote worker is introduced. ITRU-060/061/062 remain unchanged.
