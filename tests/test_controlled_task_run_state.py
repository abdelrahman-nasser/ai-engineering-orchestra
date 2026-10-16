"""Original Result and Journal integration on existing disposable Windows rigs."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import os
import tempfile
import unittest
from unittest import mock

from itru import task_run_state as state
from itru import sqlite_task_run_state as storage
from itru import agent_execution_result as result
from itru import _native_repository_file_read as native
from itru.agent_operation_tool_binding import AgentOperationToolBinding
from tests import test_controlled_execution_result as original
from tests import test_controlled_execution_journal as journal_tests
from tests.test_sqlite_task_run_state import approve


class ControlledStateTests(unittest.TestCase):
    def setUp(self):
        roots, create = [], tempfile.mkdtemp
        def verify():
            for root in roots:
                self.assertFalse(root.exists(), f'fixture residue: {root}')
                print(f'ITRU062_NATIVE_CLEAN {root}', flush=True)
        def track(*args, **kwargs):
            root = Path(create(*args, **kwargs)).resolve()
            self.assertEqual(root.parent, Path(tempfile.gettempdir()).resolve())
            self.assertTrue(root.name.startswith('aio-053-local-trust-'))
            roots.append(root)
            return str(root)
        self.addCleanup(verify)
        patcher = mock.patch.object(tempfile, 'mkdtemp', side_effect=track)
        patcher.start(); self.addCleanup(patcher.stop)

    def attach(self, rig):
        self.assertEqual(os.name, 'nt', 'genuine supported native rig required; no skip')
        directory = Path(rig.h._temporary_directory.name).resolve()/'task-state'
        store = storage.SqliteTaskRunStateStore.provision(directory, store_id='store::native',
            project_id='project::native', continuation_authorizer=approve)
        self.addCleanup(store.close)
        task = store.enroll(rig.run.contract.task_id, definition_reference='definition::native')
        task = store.register_run(rig.binding_value, rig.subject.ledger_identity, expected_revision=task.revision)
        store.start_run(task.task_id, rig.run.run_id, expected_revision=task.revision)
        return store

    def reopen(self, store):
        store.close()
        reopened = storage.SqliteTaskRunStateStore(store.directory, store_id='store::native',
            project_id='project::native')
        self.addCleanup(reopened.close)
        return reopened

    def test_01_original_outcomes_and_durable_passive_state(self):
        for expected in ('succeeded', 'failed_before_effect', 'effect_ambiguous'):
            with self.subTest(expected=expected):
                rig = original.ControlledResultScenarios.rig(self, None if expected == 'failed_before_effect' else original.DATA)
                store = self.attach(rig)
                if expected == 'effect_ambiguous':
                    with mock.patch.object(rig.root._native, 'read_data', side_effect=native._NativeFailure('read_failure')):
                        outcome = rig.invoke(self)
                else:
                    outcome = rig.invoke(self)
                self.assertTrue(result._is_authoritative_result(outcome.result))
                task = store.record_result(outcome.result, expected_revision=3)
                self.assertEqual(task.runs[0].state, expected)
                self.assertEqual(task.state, 'in_progress' if expected == 'succeeded' else 'blocked')
                self.assertEqual(store.record_result(outcome.result, expected_revision=1), task)
                if expected == 'effect_ambiguous':
                    adapter = mock.Mock(side_effect=approve)
                    store._authorizer = adapter
                    with self.assertRaises(state.StateConflictError):
                        new_run = replace(rig.run, run_id=rig.run.run_id+'::next')
                        store.continue_task(store.checkpoint(task.task_id),
                            AgentOperationToolBinding(new_run, rig.binding_value.tool_id),
                            rig.subject.ledger_identity, reason='must fail')
                    adapter.assert_not_called()
                reopened = self.reopen(store)
                self.assertEqual(reopened.get_task(task.task_id), task)
                self.assertFalse(hasattr(reopened.get_run(rig.run.run_id), 'payload'))
                if expected == 'succeeded':
                    closed = reopened.transition(task.task_id, expected_revision=task.revision,
                        operation='complete', reference='governance::fixture-closure')
                    self.assertEqual(closed.state, 'completed')

    def test_02_exact_result_subject_required(self):
        rig = original.ControlledResultScenarios.rig(self)
        directory = Path(rig.h._temporary_directory.name).resolve()/'task-state'
        store = storage.SqliteTaskRunStateStore.provision(directory, store_id='store::native', project_id='project::native')
        self.addCleanup(store.close)
        task = store.enroll(rig.run.contract.task_id, definition_reference='definition::native')
        changed_run = replace(rig.run, contract=replace(rig.run.contract, resource='fixtures/other.bin'))
        task = store.register_run(AgentOperationToolBinding(changed_run, rig.binding_value.tool_id),
            rig.subject.ledger_identity, expected_revision=task.revision)
        store.start_run(task.task_id, rig.run.run_id, expected_revision=task.revision)
        outcome = rig.invoke(self)
        with self.assertRaises(state.StateConflictError): store.record_result(outcome.result, expected_revision=3)
        self.assertEqual(store.get_run(rig.run.run_id).state, 'running')

    def test_03_journal_success_cannot_repair_missing_state_result(self):
        rig = journal_tests.ControlledJournalScenarios.rig(self)
        store = self.attach(rig)
        cap = rig.cap(self)
        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        records = rig.journal_store.lookup(outcome.result.identity)
        reopened = self.reopen(store)  # Deliberately lose lifecycle observation before restart.
        run = reopened.get_run(rig.run.run_id)
        self.assertEqual(run.state, 'interrupted')
        diagnostic = state.reconcile_run(run, records)
        self.assertEqual((diagnostic.state, diagnostic.recorded_outcome), ('recorded_result', 'succeeded'))
        self.assertEqual(reopened.get_run(rig.run.run_id), run)
        with self.assertRaises(state.StateConflictError):
            reopened.record_result(outcome.result, expected_revision=reopened.get_task(rig.run.contract.task_id).revision)
        rig.a.close(); rig.h.close()
        with mock.patch.object(rig.root._native, 'open_component', side_effect=AssertionError('no replay')) as opens:
            repeated = rig.coordinator.invoke(cap, rig.principal, rig.decision)
        opens.assert_not_called()
        self.assertIsNone(repeated.result)

    def test_04_continuation_creates_no_execution_or_ledger_effect(self):
        rig = original.ControlledResultScenarios.rig(self)
        store = self.attach(rig)
        outcome = rig.invoke(self)
        task = store.record_result(outcome.result, expected_revision=3)
        before_count = original.original._count(rig)
        new_run = replace(rig.run, run_id=rig.run.run_id+'::next')
        with mock.patch.object(rig.root._native, 'open_component', side_effect=AssertionError('no replay')) as opens:
            continued = store.continue_task(store.checkpoint(task.task_id),
                AgentOperationToolBinding(new_run, rig.binding_value.tool_id),
                rig.subject.ledger_identity, reason='explicit synthetic approval')
        opens.assert_not_called()
        self.assertEqual(continued.runs[-1].state, 'pending')
        self.assertEqual(original.original._count(rig), before_count)
        self.assertFalse(hasattr(continued.runs[-1], 'invoke'))
