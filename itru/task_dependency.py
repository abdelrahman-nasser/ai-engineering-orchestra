"""Closed, deterministic Task dependency DAGs over explicitly supplied identities."""
from __future__ import annotations

from dataclasses import dataclass
from heapq import heapify, heappop, heappush

MAX_TASKS = 1000
MAX_DEPENDENCIES = 10000


class DependencyError(ValueError):
    """Invalid complete graph; no partial graph is usable."""


def _text(value):
    if type(value) is not str or not value:
        raise DependencyError('expected exact nonempty text')
    try:
        value.encode('utf-8', 'strict')
    except UnicodeError:
        raise DependencyError('invalid text') from None
    return value


@dataclass(frozen=True, slots=True)
class TaskNode:
    task_id: str
    definition_reference: str


@dataclass(frozen=True, slots=True)
class TaskDependency:
    task_id: str
    prerequisite_task_id: str

    @property
    def key(self):
        return self.task_id, self.prerequisite_task_id


@dataclass(frozen=True, slots=True)
class TaskGraph:
    nodes: tuple[TaskNode, ...]
    dependencies: tuple[TaskDependency, ...]
    topological_order: tuple[str, ...]


def build_task_graph(nodes, dependencies=()):
    """Normalize a bounded closed DAG, rejecting the entire input on any defect.

    Edge (A, B) means A waits for B. No catalog or repository is consulted.
    """
    if (type(nodes) is not tuple or type(dependencies) is not tuple
            or len(nodes) > MAX_TASKS or len(dependencies) > MAX_DEPENDENCIES):
        raise DependencyError('bounded tuples required')
    by_id = {}
    for node in nodes:
        if type(node) is not TaskNode:
            raise DependencyError('exact TaskNode required')
        _text(node.task_id)
        _text(node.definition_reference)
        if node.task_id in by_id:
            raise DependencyError('duplicate Task identity')
        by_id[node.task_id] = node
    edges, waiting = set(), {key: set() for key in by_id}
    dependents = {key: set() for key in by_id}
    for edge in dependencies:
        if type(edge) is not TaskDependency:
            raise DependencyError('exact TaskDependency required')
        _text(edge.task_id)
        _text(edge.prerequisite_task_id)
        if edge.task_id not in by_id or edge.prerequisite_task_id not in by_id:
            raise DependencyError('unknown dependency endpoint')
        if edge.task_id == edge.prerequisite_task_id:
            raise DependencyError('self dependency')
        if edge.key in edges:
            raise DependencyError('duplicate dependency identity')
        edges.add(edge.key)
        waiting[edge.task_id].add(edge.prerequisite_task_id)
        dependents[edge.prerequisite_task_id].add(edge.task_id)
    ready = [key for key, prerequisites in waiting.items() if not prerequisites]
    heapify(ready)
    order = []
    while ready:
        current = heappop(ready)
        order.append(current)
        for dependent in sorted(dependents[current]):
            waiting[dependent].remove(current)
            if not waiting[dependent]:
                heappush(ready, dependent)
    if len(order) != len(nodes):
        raise DependencyError('cyclic dependency graph')
    return TaskGraph(tuple(by_id[key] for key in sorted(by_id)),
                     tuple(TaskDependency(*key) for key in sorted(edges)), tuple(order))


def validate_task_graph(graph):
    """Recheck public values, including the derived canonical traversal."""
    if type(graph) is not TaskGraph:
        raise DependencyError('exact TaskGraph required')
    canonical = build_task_graph(graph.nodes, graph.dependencies)
    if canonical != graph:
        raise DependencyError('noncanonical TaskGraph')
    return canonical


def prerequisites(graph, task_id):
    """Return exact sorted immediate prerequisite IDs; unknown Task is an error."""
    graph = validate_task_graph(graph)
    _text(task_id)
    if task_id not in {node.task_id for node in graph.nodes}:
        raise DependencyError('unknown Task')
    return tuple(edge.prerequisite_task_id for edge in graph.dependencies
                 if edge.task_id == task_id)
