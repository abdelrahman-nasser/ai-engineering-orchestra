"""Pure bounded selection and descriptive handoff; never execution authority.

    Supply a coherent current snapshot from the owned ITRU-062 Store. The caller
    serializes evaluation and registration and freshly checks downstream authority.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from itru.assignment import Assignment
from itru.task_dependency import TaskGraph, _text, validate_task_graph
from itru import task_run_state as state

MAX_CONCURRENCY = 100
_MIN_RUN_DELTA = dict(pending=1, running=2, succeeded=3, failed_before_effect=3,
                      effect_ambiguous=3, interrupted=3, cancelled=2)


class SchedulingError(ValueError):
    """Invalid snapshot/subject; no partial scheduling decision is returned."""


@dataclass(frozen=True, slots=True)
class SchedulingSnapshot:
    store_id: str
    project_id: str
    tasks: tuple[state.TaskSnapshot, ...]


@dataclass(frozen=True, slots=True)
class DependencyEvaluation:
    task_id: str
    state: str
    unsatisfied_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskEvaluation:
    task_id: str
    state: str
    dependencies: DependencyEvaluation


@dataclass(frozen=True, slots=True)
class SchedulerDecision:
    graph: TaskGraph
    snapshot: SchedulingSnapshot
    max_concurrency: int
    state: str
    occupied_run_ids: tuple[str, ...]
    evaluations: tuple[TaskEvaluation, ...]
    selected_task_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AssignmentHandoff:
    assignment: Assignment
    checkpoint: state.Checkpoint
    decision: SchedulerDecision


def _positive(value):
    if type(value) is not int or not 1 <= value <= 9223372036854775807:
        raise SchedulingError('invalid revision')


def _task_revision_coherent(task):
    if not task.runs:
        return task.revision in {
            'planned': (1,), 'blocked': (2,), 'cancelled': (2, 3),
            'in_progress': (), 'completed': (),
        }[task.state]
    latest = task.runs[-1]
    delta = task.revision - latest.revision
    if task.state == 'in_progress':
        return delta == 0
    if task.state == 'completed':
        return delta == 1
    if task.state == 'blocked':
        return delta == (1 if latest.state == 'succeeded' else 0)
    if task.state == 'cancelled':
        return (delta == 1 or delta == 0 and latest.state in ('interrupted', 'cancelled')
                or delta == 2 and latest.state == 'succeeded')
    return False


def _snapshot(graph, snapshot):
    if type(snapshot) is not SchedulingSnapshot or type(snapshot.tasks) is not tuple:
        raise SchedulingError('exact SchedulingSnapshot and Task tuple required')
    _text(snapshot.store_id)
    _text(snapshot.project_id)
    nodes = {node.task_id: node for node in graph.nodes}
    if len(snapshot.tasks) > len(nodes):
        raise SchedulingError('extra or duplicate Task observation')
    tasks, run_ids, result_ids = {}, set(), set()
    for task in snapshot.tasks:
        if type(task) is not state.TaskSnapshot:
            raise SchedulingError('exact persisted TaskSnapshot required')
        _text(task.task_id)
        _text(task.definition_reference)
        _text(task.reason)
        _positive(task.revision)
        if task.task_id not in nodes or task.task_id in tasks:
            raise SchedulingError('extra or duplicate Task observation')
        if task.definition_reference != nodes[task.task_id].definition_reference:
            raise SchedulingError('persisted Task definition mismatch')
        if type(task.state) is not str or task.state not in state.TASK_STATES:
            raise SchedulingError('invalid persisted Task state')
        if type(task.runs) is not tuple or len(task.runs) > state.MAX_EVENTS:
            raise SchedulingError('invalid Run history')
        previous_revision = 1
        for index, run in enumerate(task.runs):
            if type(run) is not state.RunSnapshot:
                raise SchedulingError('exact persisted RunSnapshot required')
            state.subject_document(run.binding, run.ledger_identity)
            _positive(run.revision)
            if type(run.state) is not str or run.state not in state.RUN_STATES:
                raise SchedulingError('invalid persisted Run state')
            if (run.binding.run.contract.task_id != task.task_id
                    or run.run_id in run_ids
                    or run.revision < previous_revision + _MIN_RUN_DELTA[run.state]
                    or run.revision > task.revision):
                raise SchedulingError('Run identity, ownership or revision conflict')
            previous_revision = run.revision
            run_ids.add(run.run_id)
            if len(run_ids) > state.MAX_EVENTS:
                raise SchedulingError('Run snapshot limit')
            if index < len(task.runs) - 1 and run.state in state.UNFINISHED | state.UNSAFE:
                raise SchedulingError('Run history continues past unfinished/unsafe effect')
            if run.state in state.RESULT_OUTCOMES:
                identity = run.result_identity
                if type(identity) is not tuple or len(identity) != 5:
                    raise SchedulingError('missing original Result identity')
                for item in identity:
                    _text(item)
                if (identity[:2] != (run.ledger_identity.ledger_instance_id,
                                     run.ledger_identity.authorization_domain_id)
                        or identity[2] not in ('human', 'policy') or identity in result_ids):
                    raise SchedulingError('Result identity scope/collision')
                result_ids.add(identity)
            elif run.result_identity is not None:
                raise SchedulingError('unexpected Result identity')
        unfinished = any(run.state in state.UNFINISHED for run in task.runs)
        unsafe = any(run.state in state.UNSAFE for run in task.runs)
        if (not _task_revision_coherent(task)
                or task.state == 'planned' and task.runs
                or task.state == 'in_progress' and (not task.runs or task.runs[-1].state
                    not in ('pending', 'running', 'succeeded'))
                or task.state != 'in_progress' and unfinished
                or task.state == 'completed' and (unsafe or not task.runs
                    or task.runs[-1].state != 'succeeded')):
            raise SchedulingError('incoherent persisted Task/Run states')
        tasks[task.task_id] = task
    return replace(snapshot, tasks=tuple(tasks[key] for key in sorted(tasks)))


def evaluate_schedule(graph, snapshot, *, max_concurrency):
    """Select initial work only; no I/O, callbacks, reservation, continuation or Run.

    Missing Task observations suspend all new selection. Equal input sets yield
    equal complete decisions regardless of supplied node/edge/Task tuple order.
    Invalid input raises ValueError, with no usable partial decision.
    """
    graph = validate_task_graph(graph)
    if type(max_concurrency) is not int or not 1 <= max_concurrency <= MAX_CONCURRENCY:
        raise SchedulingError('max_concurrency must be an exact integer in 1..100')
    snapshot = _snapshot(graph, snapshot)
    tasks = {task.task_id: task for task in snapshot.tasks}
    waiting = {node.task_id: [] for node in graph.nodes}
    for edge in graph.dependencies:
        waiting[edge.task_id].append(edge.prerequisite_task_id)
    evaluations, ready = [], []
    for node in graph.nodes:
        unsatisfied = tuple(key for key in waiting[node.task_id]
                            if key not in tasks or tasks[key].state != 'completed')
        dependency_state = ('blocked' if any(key in tasks for key in unsatisfied)
                            else 'unresolved' if unsatisfied else 'ready')
        dependency = DependencyEvaluation(node.task_id, dependency_state, unsatisfied)
        task = tasks.get(node.task_id)
        if task is None:
            outcome = 'unresolved'
        elif any(run.state in state.UNSAFE for run in task.runs):
            outcome = 'unsafe'
        elif task.state in ('completed', 'cancelled'):
            outcome = 'terminal'
        elif any(run.state in state.UNFINISHED for run in task.runs):
            outcome = 'active'
        elif task.state != 'planned' or task.runs:
            outcome = 'manual'
        elif dependency_state != 'ready':
            outcome = dependency_state
        else:
            outcome = 'ready'
            ready.append(node.task_id)
        evaluations.append(TaskEvaluation(node.task_id, outcome, dependency))
    occupied = tuple(sorted(run.run_id for task in snapshot.tasks for run in task.runs
                            if run.state in state.UNFINISHED))
    outcome = ('incomplete_snapshot' if len(tasks) != len(graph.nodes)
               else 'over_capacity' if len(occupied) > max_concurrency else 'evaluated')
    selected = tuple(ready[:max(0, max_concurrency - len(occupied))]) if outcome == 'evaluated' else ()
    return SchedulerDecision(graph, snapshot, max_concurrency, outcome, occupied,
                             tuple(evaluations), selected)


def prepare_assignment_handoff(graph, snapshot, assignment, *, max_concurrency):
    """Re-evaluate and return descriptive intent for one externally chosen binding.

    This checks Assignment value shape, not contextual Role/Actor coverage. Use
    existing validate_assignment before fresh downstream preparation/authority.
    No persisted decision is accepted as a bearer credential or authorization.
    """
    if type(assignment) is not Assignment:
        raise SchedulingError('exact Assignment required')
    for field in ('task_id', 'workflow_id', 'stage_id', 'role_id', 'actor_id'):
        _text(getattr(assignment, field))
    decision = evaluate_schedule(graph, snapshot, max_concurrency=max_concurrency)
    if assignment.task_id not in decision.selected_task_ids:
        raise SchedulingError('Assignment Task is not selected in supplied snapshot')
    task = next(task for task in decision.snapshot.tasks if task.task_id == assignment.task_id)
    checkpoint = state.Checkpoint(snapshot.store_id, snapshot.project_id, task.task_id, task.revision)
    return AssignmentHandoff(assignment, checkpoint, decision)
