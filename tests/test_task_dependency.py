"""Explicit pure DAG scenarios; no catalog discovery or fixture I/O."""
from dataclasses import FrozenInstanceError, replace
from itertools import permutations
import unittest

from itru import task_dependency as dag


def node(task_id):
    return dag.TaskNode(task_id, 'definition::' + task_id)


class DependencyTests(unittest.TestCase):
    def test_empty_and_singleton(self):
        self.assertEqual(dag.build_task_graph(()), dag.TaskGraph((), (), ()))
        self.assertEqual(dag.build_task_graph((node('A'),)).topological_order, ('A',))

    def test_dependency_identity_and_exact_case(self):
        edge = dag.TaskDependency('a', 'A')
        graph = dag.build_task_graph((node('a'), node('A')), (edge,))
        self.assertEqual(edge.key, ('a', 'A'))
        self.assertEqual(graph.topological_order, ('A', 'a'))
        self.assertEqual(dag.prerequisites(graph, 'a'), ('A',))

    def test_diamond_and_disconnected_order(self):
        nodes = tuple(node(key) for key in ('D', 'B', 'C', 'A', '0'))
        edges = tuple(dag.TaskDependency(*pair) for pair in
                      (('D', 'B'), ('D', 'C'), ('B', 'A'), ('C', 'A')))
        graph = dag.build_task_graph(nodes, edges)
        self.assertEqual(graph.topological_order, ('0', 'A', 'B', 'C', 'D'))
        self.assertEqual(dag.prerequisites(graph, 'D'), ('B', 'C'))

    def test_permutation_invariance(self):
        nodes = (node('z'), node('A'), node('a'))
        edges = (dag.TaskDependency('z', 'A'), dag.TaskDependency('z', 'a'))
        expected = dag.build_task_graph(nodes, edges)
        for supplied in permutations(nodes):
            for dependencies in permutations(edges):
                self.assertEqual(dag.build_task_graph(supplied, dependencies), expected)

    def test_duplicate_nodes_even_if_equal(self):
        for other in (node('A'), dag.TaskNode('A', 'different')):
            with self.subTest(other=other), self.assertRaises(dag.DependencyError):
                dag.build_task_graph((node('A'), other))

    def test_duplicate_edges(self):
        edge = dag.TaskDependency('B', 'A')
        with self.assertRaises(dag.DependencyError):
            dag.build_task_graph((node('A'), node('B')), (edge, edge))

    def test_unknown_and_self_endpoints(self):
        for edge in (dag.TaskDependency('B', 'A'), dag.TaskDependency('A', 'B'),
                     dag.TaskDependency('A', 'A')):
            with self.subTest(edge=edge), self.assertRaises(dag.DependencyError):
                dag.build_task_graph((node('A'),), (edge,))

    def test_cycle_rejects_whole_graph_including_clean_component(self):
        nodes = tuple(node(key) for key in ('clean', 'A', 'B', 'C'))
        edges = tuple(dag.TaskDependency(*pair) for pair in
                      (('B', 'A'), ('C', 'B'), ('A', 'C')))
        with self.assertRaises(dag.DependencyError):
            dag.build_task_graph(nodes, edges)

    def test_invalid_types_and_text(self):
        for nodes, edges in (([], ()), ((node('A'),), []), (({'task_id': 'A'},), ()),
                             ((dag.TaskNode('', 'ref'),), ()),
                             ((dag.TaskNode('A', '\ud800'),), ()),
                             ((node('A'),), (('A', 'A'),))):
            with self.subTest(nodes=repr(nodes)), self.assertRaises(dag.DependencyError):
                dag.build_task_graph(nodes, edges)

    def test_limits_and_iterative_deep_chain(self):
        nodes = tuple(node(str(index).zfill(4)) for index in range(dag.MAX_TASKS))
        edges = tuple(dag.TaskDependency(nodes[index].task_id, nodes[index-1].task_id)
                      for index in range(1, len(nodes)))
        self.assertEqual(len(dag.build_task_graph(nodes, edges).topological_order), dag.MAX_TASKS)
        with self.assertRaises(dag.DependencyError):
            dag.build_task_graph(nodes + (node('extra'),))
        with self.assertRaises(dag.DependencyError):
            dag.build_task_graph((), (dag.TaskDependency('A', 'B'),) * (dag.MAX_DEPENDENCIES + 1))

    def test_direct_graph_forgery_and_unknown_query(self):
        graph = dag.build_task_graph((node('A'), node('B')))
        for changed in (replace(graph, topological_order=('B', 'A')),
                        replace(graph, nodes=tuple(reversed(graph.nodes))), {}):
            with self.subTest(changed=changed), self.assertRaises(dag.DependencyError):
                dag.validate_task_graph(changed)
        with self.assertRaises(dag.DependencyError):
            dag.prerequisites(graph, 'unknown')

    def test_values_are_immutable(self):
        graph = dag.build_task_graph((node('A'), node('B')), (dag.TaskDependency('B', 'A'),))
        for value, field in ((graph, 'nodes'), (graph.nodes[0], 'task_id'),
                             (graph.dependencies[0], 'task_id')):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, field, 'changed')
