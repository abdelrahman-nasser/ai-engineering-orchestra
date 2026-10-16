"""Pure scheduler evidence and isolated real lifecycle Store restart scenarios.

Synthetic reducer Result identities are descriptive specimens, never authoritative
Results. No target invocation, registry, network, or production authority fixture.
"""
from dataclasses import FrozenInstanceError, asdict, replace
from itertools import permutations
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from itru import task_dependency as dag, task_scheduler as scheduler, task_run_state as state
from itru.assignment import Assignment
from itru.agent_execution_contract import AgentExecutionContract
from itru.agent_execution_run import AgentExecutionRun
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from itru.sqlite_task_run_state import SqliteTaskRunStateStore

LEDGER = AuthorizationDomainIdentity('domain::synthetic', 'ledger::synthetic', 1)


def binding(task_id, run_id=None):
    contract = AgentExecutionContract(task_id, 'standard-change', 'implement',
        'software-engineer', 'actor::synthetic', 'runtime::synthetic', 'option::synthetic',
        'environment::synthetic', 'repository_file_read', 'fixtures/scheduler.bin', 'deep')
    return AgentOperationToolBinding(AgentExecutionRun(run_id or 'run::' + task_id, contract),
                                   'tool::itru-native-repository-file-read::v1')


def task(task_id, kind='planned'):
    """Construct coherent descriptive snapshots using the unchanged pure reducer."""
    tasks = {}
    def apply(operation, data):
        revision = 1 if not tasks else tasks[task_id].revision + 1
        state.apply_event(tasks, dict(format_version=1, sequence=revision,
            task_id=task_id, revision=revision, operation=operation, data=data))
    apply('enroll', dict(definition_reference='definition::' + task_id))
    if kind == 'planned':
        return tasks[task_id]
    if kind in ('blocked', 'cancelled_task'):
        apply('block' if kind == 'blocked' else 'cancel', dict(reference='manual'))
        return tasks[task_id]
    apply('register', dict(subject=state.subject_document(binding(task_id), LEDGER)))
    if kind == 'pending':
        return tasks[task_id]
    if kind == 'cancelled_run':
        apply('stop', dict(reference='before-start'))
        return tasks[task_id]
    apply('start', dict(run_id='run::' + task_id))
    if kind == 'running':
        return tasks[task_id]
    if kind == 'interrupted':
        apply('recover', {})
        return tasks[task_id]
    outcome = 'succeeded' if kind == 'completed' else kind
    apply('result', dict(run_id='run::' + task_id, outcome=outcome,
        result_identity=['ledger::synthetic', 'domain::synthetic', 'human', 'issuer', 'grant::' + task_id]))
    if kind == 'completed':
        apply('complete', dict(reference='synthetic-governance'))
    return tasks[task_id]


def graph(*ids, edges=()):
    return dag.build_task_graph(tuple(dag.TaskNode(key, 'definition::' + key) for key in ids),
                                tuple(dag.TaskDependency(*pair) for pair in edges))


def snapshot(*tasks):
    return scheduler.SchedulingSnapshot('store::synthetic', 'project::synthetic', tuple(tasks))


def evaluate(g, *tasks, limit=2):
    return scheduler.evaluate_schedule(g, snapshot(*tasks), max_concurrency=limit)


class SchedulerTests(unittest.TestCase):
    def test_empty_domain(self):
        decision = evaluate(graph())
        self.assertEqual((decision.state, decision.selected_task_ids, decision.evaluations),
                         ('evaluated', (), ()))

    def test_lexical_selection_not_input_order(self):
        decision = evaluate(graph('z', 'a', 'A'), task('z'), task('a'), task('A'))
        self.assertEqual(decision.selected_task_ids, ('A', 'a'))
        self.assertEqual(tuple(item.task_id for item in decision.evaluations), ('A', 'a', 'z'))

    def test_all_snapshot_permutations_equal(self):
        g, tasks = graph('B', 'A', 'C'), (task('A'), task('B'), task('C'))
        expected = evaluate(g, *tasks)
        for supplied in permutations(tasks):
            self.assertEqual(evaluate(g, *supplied), expected)

    def test_task_completion_only_satisfies_dependencies(self):
        g = graph('A', 'B', edges=(('B', 'A'),))
        for kind in ('planned', 'pending', 'running', 'succeeded', 'failed_before_effect',
                     'effect_ambiguous', 'interrupted', 'cancelled_task', 'blocked'):
            with self.subTest(kind=kind):
                decision = evaluate(g, task('A', kind), task('B'))
                self.assertNotIn('B', decision.selected_task_ids)
                self.assertEqual(decision.evaluations[1].dependencies.unsatisfied_task_ids, ('A',))
        self.assertEqual(evaluate(g, task('A', 'completed'), task('B')).selected_task_ids, ('B',))

    def test_diamond_waits_for_both_prerequisites(self):
        g = graph('A', 'B', 'C', 'D', edges=(('B', 'A'), ('C', 'A'), ('D', 'B'), ('D', 'C')))
        decision = evaluate(g, task('A', 'completed'), task('B', 'completed'), task('C'), task('D'))
        self.assertEqual(decision.selected_task_ids, ('C',))
        self.assertEqual(decision.evaluations[-1].dependencies.unsatisfied_task_ids, ('C',))

    def test_missing_task_suspends_even_disconnected_ready_work(self):
        decision = evaluate(graph('A', 'B'), task('B'))
        self.assertEqual((decision.state, decision.selected_task_ids), ('incomplete_snapshot', ()))
        self.assertEqual(tuple(item.state for item in decision.evaluations), ('unresolved', 'ready'))

    def test_blocker_and_missing_dependency_evidence_preserved(self):
        g = graph('A', 'B', 'C', edges=(('C', 'B'), ('C', 'A')))
        decision = evaluate(g, task('A'), task('C'))
        self.assertEqual(decision.evaluations[-1].dependencies,
                         scheduler.DependencyEvaluation('C', 'blocked', ('A', 'B')))
        missing = evaluate(g, task('C'))
        self.assertEqual(missing.evaluations[-1].dependencies.state, 'unresolved')

    def test_pending_and_running_occupy_capacity(self):
        decision = evaluate(graph('A', 'B', 'C', 'D'), task('A', 'pending'),
                            task('B', 'running'), task('C'), task('D'), limit=3)
        self.assertEqual(decision.occupied_run_ids, ('run::A', 'run::B'))
        self.assertEqual(decision.selected_task_ids, ('C',))

    def test_saturation_and_over_capacity_are_explicit(self):
        g, tasks = graph('A', 'B', 'C'), (task('A', 'pending'), task('B', 'running'), task('C'))
        saturated, excess = evaluate(g, *tasks), evaluate(g, *tasks, limit=1)
        self.assertEqual((saturated.state, saturated.selected_task_ids), ('evaluated', ()))
        self.assertEqual((excess.state, excess.selected_task_ids), ('over_capacity', ()))
        self.assertEqual(excess.occupied_run_ids, saturated.occupied_run_ids)

    def test_limits_reject_bool_float_and_out_of_range(self):
        for limit in (True, False, 0, -1, 101, 1.0, '2', None):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                evaluate(graph(), limit=limit)
        self.assertEqual(evaluate(graph(), limit=100).max_concurrency, 100)

    def test_prior_work_never_automatically_continues(self):
        for kind, expected in (('effect_ambiguous', 'unsafe'), ('interrupted', 'unsafe'),
                               ('succeeded', 'manual'), ('failed_before_effect', 'manual'),
                               ('cancelled_run', 'manual'), ('blocked', 'manual'),
                               ('completed', 'terminal'), ('cancelled_task', 'terminal')):
            with self.subTest(kind=kind):
                decision = evaluate(graph('A'), task('A', kind))
                self.assertEqual((decision.selected_task_ids, decision.evaluations[0].state), ((), expected))

    def test_definition_extra_and_duplicate_observations_reject(self):
        g, a = graph('A'), task('A')
        for tasks in ((replace(a, definition_reference='other'),), (a, a), (task('B'),)):
            with self.subTest(tasks=tasks), self.assertRaises(ValueError):
                evaluate(g, *tasks)

    def test_malformed_snapshots_and_states_reject_atomically(self):
        a = task('A')
        for changed in (replace(a, state='future'), replace(a, revision=True),
                        replace(a, runs=[]), replace(a, state='completed'),
                        replace(a, state='in_progress'), replace(a, reason=''),
                        replace(a, revision=0), replace(a, revision=2), replace(a, task_id=[])):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                evaluate(graph('A'), changed)
        for supplied in (asdict(snapshot(a)), replace(snapshot(a), tasks=[a]),
                         replace(snapshot(a), store_id=''), replace(snapshot(a), project_id=True)):
            with self.subTest(supplied=supplied), self.assertRaises(ValueError):
                scheduler.evaluate_schedule(graph('A'), supplied, max_concurrency=1)

    def test_terminal_negative_cannot_fabricate_task_completion(self):
        succeeded = task('A', 'succeeded')
        for revision in (succeeded.revision, succeeded.revision + 2):
            with self.subTest(revision=revision), self.assertRaises(ValueError):
                evaluate(graph('A', 'B', edges=(('B', 'A'),)),
                         replace(succeeded, state='completed', revision=revision), task('B'))
        for kind in ('failed_before_effect', 'cancelled_run', 'effect_ambiguous', 'interrupted'):
            latest = task('A', kind).runs[0]
            latest = replace(latest, binding=binding('A', 'run::next'), revision=7)
            if latest.result_identity is not None:
                latest = replace(latest, result_identity=(*latest.result_identity[:4], 'grant::next'))
            for status in ('completed', 'in_progress'):
                changed = replace(succeeded, state=status, revision=8,
                                  runs=(succeeded.runs[0], latest))
                with self.subTest(kind=kind, status=status), self.assertRaises(ValueError):
                    evaluate(graph('A', 'B', edges=(('B', 'A'),)), changed, task('B'))

    def test_minimum_run_chronology_and_task_revision_relationships(self):
        for kind, minimum in (('pending', 2), ('running', 3), ('succeeded', 4),
                              ('failed_before_effect', 4), ('effect_ambiguous', 4),
                              ('interrupted', 4), ('cancelled_run', 3), ('completed', 4)):
            original = task('A', kind)
            evaluate(graph('A'), original)
            low = minimum - 1
            changed = replace(original, revision=low + (kind == 'completed'),
                              runs=(replace(original.runs[0], revision=low),))
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                evaluate(graph('A'), changed)
            with self.subTest(kind=kind, skipped_revision=True), self.assertRaises(ValueError):
                evaluate(graph('A'), replace(original, revision=original.revision + 2))
        for kind in ('blocked', 'cancelled_task'):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                evaluate(graph('A'), replace(task('A', kind), revision=4))

    def test_valid_block_and_cancellation_chronologies_remain_accepted(self):
        for kind in ('planned', 'blocked', 'pending', 'running', 'succeeded',
                     'failed_before_effect', 'effect_ambiguous', 'interrupted', 'cancelled_run'):
            original = task('A', kind)
            tasks = {'A': original}
            revision = original.revision + 1
            state.apply_event(tasks, dict(format_version=1, sequence=1, task_id='A',
                revision=revision, operation='cancel', data=dict(reference='explicit cancellation')))
            self.assertEqual(evaluate(graph('A'), tasks['A']).selected_task_ids, ())
        original = task('A', 'succeeded')
        tasks = {'A': original}
        for operation in ('block', 'cancel'):
            state.apply_event(tasks, dict(format_version=1, sequence=1, task_id='A',
                revision=tasks['A'].revision + 1, operation=operation, data=dict(reference='explicit')))
            self.assertEqual(evaluate(graph('A'), tasks['A']).selected_task_ids, ())

    def test_run_subject_revision_and_state_coherence_reject(self):
        a = task('A', 'running')
        run = a.runs[0]
        for changed in (replace(run, state='future'), replace(run, revision=True),
                        replace(run, revision=a.revision+1), replace(run, revision=1),
                        replace(run, binding=binding('B')), replace(run, result_identity=('x',)),
                        replace(run, binding=None)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                evaluate(graph('A'), replace(a, runs=(changed,)))
        with self.assertRaises(ValueError):
            evaluate(graph('A'), replace(a, state='blocked'))

    def test_original_result_identity_remains_descriptive_and_scoped(self):
        a = task('A', 'succeeded')
        for identity in (None, ('x',), ['ledger::synthetic', 'domain::synthetic', 'human', 'i', 'g'],
                         ('wrong-ledger', 'domain::synthetic', 'human', 'i', 'g')):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                evaluate(graph('A'), replace(a, runs=(replace(a.runs[0], result_identity=identity),)))
        self.assertEqual(evaluate(graph('A'), a).evaluations[0].state, 'manual')

    def test_handoff_exact_assignment_and_checkpoint(self):
        a, g = task('A'), graph('A')
        assignment = Assignment('A', 'standard-change', 'implement', 'software-engineer', 'actor::synthetic')
        handoff = scheduler.prepare_assignment_handoff(g, snapshot(a), assignment, max_concurrency=1)
        self.assertIs(handoff.assignment, assignment)
        self.assertEqual(handoff.checkpoint, state.Checkpoint('store::synthetic', 'project::synthetic', 'A', 1))
        self.assertEqual(handoff.decision, evaluate(g, a, limit=1))
        for value, field in ((handoff, 'assignment'), (handoff.checkpoint, 'revision'),
                             (handoff.decision, 'state'), (handoff.decision.evaluations[0], 'state'),
                             (handoff.decision.snapshot, 'tasks')):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, field, None)

    def test_handoff_rechecks_changed_snapshot_and_selection(self):
        assignment = Assignment('A', 'standard-change', 'implement', 'software-engineer', 'actor::synthetic')
        for supplied in (task('A', 'pending'), task('A', 'completed'), task('A', 'effect_ambiguous')):
            with self.subTest(state=supplied.state), self.assertRaises(ValueError):
                scheduler.prepare_assignment_handoff(graph('A'), snapshot(supplied), assignment, max_concurrency=1)
        for changed in (replace(assignment, task_id='other'), replace(assignment, actor_id=''), asdict(assignment)):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                scheduler.prepare_assignment_handoff(graph('A'), snapshot(task('A')), changed, max_concurrency=1)

    def test_repeated_decisions_reserve_nothing_and_never_invoke(self):
        g, supplied = graph('A'), snapshot(task('A'))
        with patch('builtins.open', side_effect=AssertionError('unexpected I/O')), \
                patch('socket.socket', side_effect=AssertionError('unexpected network')), \
                patch('subprocess.Popen', side_effect=AssertionError('unexpected execution')):
            first = scheduler.evaluate_schedule(g, supplied, max_concurrency=1)
            second = scheduler.evaluate_schedule(g, supplied, max_concurrency=1)
        self.assertEqual(first, second)
        self.assertEqual(supplied.tasks[0].runs, ())
        for name in ('invoke', 'grant', 'resume', 'retry', 'dispatch', 'capability'):
            self.assertFalse(hasattr(first, name))


def cleanup(temporary):
    root = Path(temporary.name)
    if (root.resolve() != root or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith('itru-063-scheduler-')):
        raise AssertionError('fixture cleanup containment failure')
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(parent) / name
            info = path.lstat()
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or getattr(info, 'st_file_attributes', 0) & 0x400
                    or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)):
                raise AssertionError('foreign fixture cleanup object')
    temporary.cleanup()
    if root.exists():
        raise AssertionError('fixture residue')
    print('ITRU063_CLEAN', root, flush=True)


class SchedulerStorageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='itru-063-scheduler-',
                                                 dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(cleanup, temporary)
        self.directory = Path(temporary.name).resolve() / 'lifecycle'
        self.store = SqliteTaskRunStateStore.provision(self.directory,
            store_id='store::synthetic', project_id='project::synthetic')
        self.addCleanup(self.store.close)

    def reopen(self):
        self.store.close()
        self.store = SqliteTaskRunStateStore(self.directory,
            store_id='store::synthetic', project_id='project::synthetic')
        self.addCleanup(self.store.close)

    def test_restart_planned_preserves_exact_decision(self):
        self.store.enroll('A', definition_reference='definition::A')
        first = evaluate(graph('A'), self.store.get_task('A'), limit=1)
        self.reopen()
        self.assertEqual(evaluate(graph('A'), self.store.get_task('A'), limit=1), first)

    def test_pending_recovery_returns_manual_without_automatic_retry(self):
        a = self.store.enroll('A', definition_reference='definition::A')
        self.store.register_run(binding('A'), LEDGER, expected_revision=a.revision)
        self.assertEqual(evaluate(graph('A'), self.store.get_task('A')).occupied_run_ids, ('run::A',))
        self.reopen()
        a = self.store.get_task('A')
        decision = evaluate(graph('A'), a)
        self.assertEqual((a.runs[0].state, decision.evaluations[0].state, decision.selected_task_ids),
                         ('cancelled', 'manual', ()))
        with self.assertRaises(state.ContinuationDeniedError):
            self.store.continue_task(self.store.checkpoint('A'), binding('A', 'new-run'), LEDGER, reason='explicit')

    def test_running_recovery_stays_unsafe_and_repeated_restarts_stable(self):
        a = self.store.enroll('A', definition_reference='definition::A')
        a = self.store.register_run(binding('A'), LEDGER, expected_revision=a.revision)
        self.store.start_run('A', 'run::A', expected_revision=a.revision)
        self.reopen()
        a = self.store.get_task('A')
        first = evaluate(graph('A'), a)
        self.assertEqual((a.runs[0].state, first.evaluations[0].state), ('interrupted', 'unsafe'))
        self.assertEqual(first.selected_task_ids, ())
        self.reopen()
        self.assertEqual(evaluate(graph('A'), self.store.get_task('A')), first)

    def test_serialized_handoff_registration_reduces_next_capacity(self):
        for key in ('B', 'A'):
            self.store.enroll(key, definition_reference='definition::' + key)
        g = graph('A', 'B')
        assignment = Assignment('A', 'standard-change', 'implement', 'software-engineer', 'actor::synthetic')
        supplied = snapshot(*self.store.page())
        handoff = scheduler.prepare_assignment_handoff(g, supplied, assignment, max_concurrency=1)
        # Registration records lifecycle intent only; no authority or invocation.
        self.store.register_run(binding('A'), LEDGER, expected_revision=handoff.checkpoint.revision)
        decision = scheduler.evaluate_schedule(g, snapshot(*self.store.page()), max_concurrency=1)
        self.assertEqual((decision.occupied_run_ids, decision.selected_task_ids), (('run::A',), ()))
        with self.assertRaises(ValueError):
            scheduler.prepare_assignment_handoff(g, snapshot(*self.store.page()), assignment, max_concurrency=1)
