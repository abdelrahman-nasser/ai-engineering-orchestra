"""Owned local lifecycle fixtures, atomicity, process loss and resume conflicts.

Child probes execute only this exact module against their passed nonce-owned
fixture. No operational registry, repository catalog, target invocation or network.
"""
from __future__ import annotations

from contextlib import closing
import copy
from dataclasses import replace
import os
from pathlib import Path
import pickle
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

from itru import task_run_state as state
from itru import sqlite_task_run_state as storage
from tests.test_task_run_state import binding, LEDGER

ROOT = Path(__file__).resolve().parents[1]


def approve(request):
    return state.ContinuationApproval(request.session_nonce, request.request_nonce,
                                     'human', 'human::synthetic', 'approval::synthetic')


def _cleanup(temporary):
    root = Path(temporary.name)
    if (root.resolve() != root or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith('itru-062-state-')):
        raise AssertionError('fixture cleanup containment failure')
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(parent)/name
            info = path.lstat()
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or getattr(info, 'st_file_attributes', 0) & 0x400
                    or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)):
                raise AssertionError('foreign fixture cleanup object')
    temporary.cleanup()
    if root.exists():
        raise AssertionError('fixture residue')
    print(f'ITRU062_CLEAN {root}', flush=True)


class StateStorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='itru-062-state-', dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.temporary.name).resolve()
        self.directory = self.root/'lifecycle'
        self.addCleanup(_cleanup, self.temporary)
        self.store = storage.SqliteTaskRunStateStore.provision(self.directory, store_id='store::fixture',
            project_id='project::fixture', continuation_authorizer=approve)
        self.addCleanup(self.store.close)

    def reopen(self, **kwargs):
        self.store.close()
        self.store = storage.SqliteTaskRunStateStore(self.directory, store_id='store::fixture',
            project_id='project::fixture', **kwargs)
        self.addCleanup(self.store.close)
        return self.store

    def pending(self):
        task = self.store.enroll('ITRU-062', definition_reference='definition::fixture')
        return self.store.register_run(binding(), LEDGER, expected_revision=task.revision)

    def safe_checkpoint(self):
        task = self.pending()
        self.store.transition(task.task_id, expected_revision=task.revision, operation='stop', reference='safe-stop')
        return self.store.checkpoint(task.task_id)

    def test_01_task_identity_and_restart(self):
        self.store.enroll('ITRU-062', definition_reference='definition::fixture')
        before = self.store.get_task('ITRU-062')
        self.reopen()
        self.assertEqual(self.store.get_task('ITRU-062'), before)
        self.assertIsNone(self.store.get_task('missing'))

    def test_02_pending_recovery_no_automatic_resume(self):
        task = self.pending()
        self.reopen()
        recovered = self.store.get_task(task.task_id)
        self.assertEqual((recovered.state, recovered.runs[0].state), ('blocked', 'cancelled'))
        self.assertEqual(recovered.runs[0].binding, binding())
        self.assertEqual(recovered.runs[0].ledger_identity, LEDGER)
        checkpoint = self.store.checkpoint(task.task_id)
        with self.assertRaises(state.ContinuationDeniedError):
            self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='explicit next')

    def test_03_running_recovery_blocks_even_fresh_approval(self):
        task = self.pending()
        self.store.start_run(task.task_id, 'run::1', expected_revision=task.revision)
        self.reopen(continuation_authorizer=approve)
        current = self.store.get_task(task.task_id)
        self.assertEqual((current.state, current.runs[0].state), ('blocked', 'interrupted'))
        with self.assertRaises(state.StateConflictError):
            self.store.continue_task(self.store.checkpoint(task.task_id), binding('run::2'), LEDGER, reason='unsafe')
        self.assertIsNone(self.store.get_run('run::2'))

    def test_04_enrollment_and_registration_exact_retries(self):
        task = self.pending()
        self.assertEqual(self.store.enroll(task.task_id, definition_reference='definition::fixture'), task)
        self.assertEqual(self.store.register_run(binding(), LEDGER, expected_revision=1), task)
        with self.assertRaises(state.StateConflictError):
            self.store.enroll(task.task_id, definition_reference='different')
        with self.assertRaises(state.StateConflictError):
            self.store.register_run(binding('run::2'), LEDGER, expected_revision=task.revision)

    def test_05_illegal_transition_and_stale_revision(self):
        task = self.pending()
        for operation in ('block', 'complete'):
            with self.subTest(operation=operation), self.assertRaises(state.StateConflictError):
                self.store.transition(task.task_id, expected_revision=task.revision, operation=operation, reference='ref')
        with self.assertRaises(state.StateConflictError):
            self.store.start_run(task.task_id, 'run::1', expected_revision=1)
        self.assertEqual(self.store.get_task(task.task_id), task)

    def test_06_fresh_exact_authority_new_run_and_checkpoint(self):
        checkpoint = self.safe_checkpoint()
        calls = []
        self.store._authorizer = lambda request: calls.append(request) or approve(request)
        task = self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='human continuation')
        self.assertEqual((task.state, task.runs[-1].state), ('in_progress', 'pending'))
        self.assertEqual(calls[0].checkpoint, checkpoint)
        with self.assertRaises(state.StateConflictError):
            self.store.continue_task(checkpoint, binding('run::3'), LEDGER, reason='stale')
        self.assertEqual(len(calls), 1)
        self.assertIsNone(self.store.get_run('run::3'))

    def test_07_denied_malformed_exception_and_old_receipts(self):
        checkpoint = self.safe_checkpoint()
        old = approve(state.ContinuationRequest(checkpoint, 'old', 'old', binding('run::2'), LEDGER, 'old'))
        for adapter in (None, lambda request: None, lambda request: True, lambda request: old,
                        lambda request: (_ for _ in ()).throw(OSError('synthetic'))):
            self.store._authorizer = adapter
            with self.subTest(adapter=adapter), self.assertRaises(state.ContinuationDeniedError):
                self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='next')
            self.assertEqual(self.store.checkpoint('ITRU-062'), checkpoint)

    def test_08_conflicting_concurrent_continuations_one_winner(self):
        checkpoint = self.safe_checkpoint()
        barrier, winners, errors, calls = threading.Barrier(8), [], [], []
        self.store._authorizer = lambda request: calls.append(request) or approve(request)
        def attempt(index):
            try:
                barrier.wait(timeout=10)
                winners.append(self.store.continue_task(checkpoint, binding(f'run::{index+2}'), LEDGER, reason='next'))
            except state.StateConflictError:
                errors.append(index)
        threads = [threading.Thread(target=attempt, args=(index,), daemon=True) for index in range(8)]
        for thread in threads: thread.start()
        for thread in threads:
            thread.join(15); self.assertFalse(thread.is_alive())
        self.assertEqual((len(winners), len(errors), len(calls)), (1, 7, 1))
        self.assertEqual(len(self.store.get_task('ITRU-062').runs), 2)

    def test_09_rollback_after_authorization_and_insert(self):
        checkpoint = self.safe_checkpoint()
        def fault(point):
            if point == 'after_insert': raise OSError('synthetic write failure')
        with mock.patch.object(self.store, '_fault', side_effect=fault):
            with self.assertRaises(OSError):
                self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='next')
        self.assertEqual(self.store.checkpoint('ITRU-062'), checkpoint)
        self.assertIsNone(self.store.get_run('run::2'))

    def test_10_uncertain_acknowledgement_query_without_replay(self):
        def fault(point):
            if point == 'after_commit': raise OSError('lost acknowledgement')
        with mock.patch.object(self.store, '_fault', side_effect=fault):
            with self.assertRaises(storage.StateCommitUnknownError):
                self.store.enroll('ITRU-062', definition_reference='definition::fixture')
        self.assertEqual(self.store.get_task('ITRU-062').revision, 1)
        self.assertEqual(self.store.enroll('ITRU-062', definition_reference='definition::fixture').revision, 1)

    def test_11_real_process_loss_reconstructs_without_authority(self):
        self.store.close()
        child = subprocess.run([sys.executable, '-B', '-m', 'tests.test_sqlite_task_run_state',
            '--crash-probe', str(self.directory)], cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 29, child.stderr.decode(errors='replace'))
        self.reopen()
        task = self.store.get_task('ITRU-062')
        self.assertEqual((task.state, task.runs[0].state), ('blocked', 'interrupted'))
        self.assertIsNone(task.runs[0].result_identity)
        first = task
        self.reopen()
        self.assertEqual(self.store.get_task('ITRU-062'), first)

    def test_12_other_process_cannot_open_live_store(self):
        task = self.pending()
        child = subprocess.run([sys.executable, '-B', '-m', 'tests.test_sqlite_task_run_state',
            '--busy-probe', str(self.directory)], cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stderr.decode(errors='replace'))
        self.assertEqual(self.store.get_task(task.task_id), task)

    def test_13_closed_copied_and_serialized_sessions_rejected(self):
        for operation in (copy.copy, copy.deepcopy, pickle.dumps):
            with self.assertRaises(TypeError): operation(self.store)
        self.store.close()
        with self.assertRaises(state.StateConflictError): self.store.get_task('ITRU-062')

    def test_14_recursive_authority_cannot_close_or_mutate(self):
        checkpoint = self.safe_checkpoint()
        for operation in (self.store.close, lambda: self.store.get_task('ITRU-062')):
            def adapter(request):
                operation()
                return approve(request)
            self.store._authorizer = adapter
            with self.assertRaises(state.ContinuationDeniedError):
                self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='next')
        self.assertEqual(self.store.checkpoint('ITRU-062'), checkpoint)

    def test_15_corruption_schema_and_pinned_metadata_fail_closed(self):
        self.pending()
        with closing(sqlite3.connect(self.directory/'state.sqlite3')) as connection, connection:
            connection.execute('PRAGMA user_version=2')
        with self.assertRaises(state.StateIntegrityError): self.store.page()
        self.store.close()
        with self.assertRaises(state.StateIntegrityError):
            storage.SqliteTaskRunStateStore(self.directory, store_id='store::fixture', project_id='project::fixture')

    def test_16_semantically_corrupt_history_has_no_clean_prefix(self):
        self.pending()
        with closing(sqlite3.connect(self.directory/'state.sqlite3')) as connection, connection:
            payload = state.decode(connection.execute('SELECT payload FROM events WHERE sequence=2').fetchone()[0])
            payload['revision'] = 9
            connection.execute('DROP TRIGGER events_no_update')
            connection.execute('UPDATE events SET payload=? WHERE sequence=2', (state.encode(payload),))
            connection.execute(next(sql for name, _, sql in storage._DDL if name == 'events_no_update'))
        with self.assertRaises(state.StateIntegrityError): self.store.get_task('ITRU-062')
        with self.assertRaises(state.StateIntegrityError): self.store.enroll('other', definition_reference='ref')

    def test_17_missing_and_existing_provision_fail_without_recreation(self):
        with self.assertRaises(FileExistsError):
            storage.SqliteTaskRunStateStore.provision(self.directory, store_id='store::fixture', project_id='project::fixture')
        absent = self.root/'absent'
        with self.assertRaises(OSError):
            storage.SqliteTaskRunStateStore(absent, store_id='store::fixture', project_id='project::fixture')
        self.assertFalse(absent.exists())
        self.store.close()
        with self.assertRaises(state.StateIntegrityError):
            storage.SqliteTaskRunStateStore(self.directory, store_id='wrong', project_id='project::fixture')

    def test_18_queries_bounded_ordered_and_terminal_task(self):
        for task_id in ('z', 'A', 'a'):
            self.store.enroll(task_id, definition_reference='definition::'+task_id)
        first = self.store.page(limit=2)
        second = self.store.page(after=first[-1].task_id, limit=2)
        self.assertEqual([task.task_id for task in first+second], ['A', 'a', 'z'])
        for limit in (0, 101, True):
            with self.assertRaises(state.StateIntegrityError): self.store.page(limit=limit)
        task = self.store.get_task('a')
        closed = self.store.transition('a', expected_revision=task.revision, operation='cancel', reference='cancel')
        with self.assertRaises(state.StateConflictError):
            self.store.transition('a', expected_revision=closed.revision, operation='block', reference='reopen')

    def test_19_untrusted_results_never_success(self):
        task = self.pending()
        self.store.start_run(task.task_id, 'run::1', expected_revision=task.revision)
        for result in (None, {'outcome': 'succeeded'}, state.reconcile_run(self.store.get_run('run::1'), ())):
            with self.assertRaises(state.StateIntegrityError):
                self.store.record_result(result, expected_revision=3)
        self.assertEqual(self.store.get_run('run::1').state, 'running')

    def test_20_foreign_checkpoint_and_new_session_receipt_rejected(self):
        checkpoint = self.safe_checkpoint()
        for changed in (replace(checkpoint, store_id='other'), replace(checkpoint, project_id='other'),
                        replace(checkpoint, revision=True)):
            with self.assertRaises(state.StateConflictError):
                self.store.continue_task(changed, binding('run::2'), LEDGER, reason='next')
        receipt = []
        self.store._authorizer = lambda request: receipt.append(approve(request)) or None
        with self.assertRaises(state.ContinuationDeniedError):
            self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='next')
        self.reopen(continuation_authorizer=lambda request: receipt[0])
        with self.assertRaises(state.ContinuationDeniedError):
            self.store.continue_task(checkpoint, binding('run::2'), LEDGER, reason='next')


class StoreImportTests(unittest.TestCase):
    def test_21_import_without_unbundled_journal_migrations(self):
        code = '''
import importlib.abc
import sys
class MissingJournalMigrations(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == 'itru._sqlite_journal_migrations':
            raise ModuleNotFoundError('unbundled Journal migration package')
sys.meta_path.insert(0, MissingJournalMigrations())
import itru.sqlite_task_run_state
'''
        child = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT,
                               capture_output=True, timeout=30)
        self.assertEqual(child.returncode, 0, child.stderr.decode(errors='replace'))


def _probe(mode, directory):
    if (directory.name != 'lifecycle' or directory.parent.parent != Path(tempfile.gettempdir()).resolve()
            or not directory.parent.name.startswith('itru-062-state-') or directory.resolve() != directory):
        raise AssertionError('child fixture containment')
    try:
        store = storage.SqliteTaskRunStateStore(directory, store_id='store::fixture', project_id='project::fixture')
    except storage.StateStoreBusyError:
        if mode == '--busy-probe': return
        raise
    if mode != '--crash-probe':
        store.close()
        raise AssertionError('expected live owner rejection')
    task = store.enroll('ITRU-062', definition_reference='definition::fixture')
    task = store.register_run(binding(), LEDGER, expected_revision=task.revision)
    store.start_run(task.task_id, 'run::1', expected_revision=task.revision)
    os._exit(29)  # Real process loss: no cleanup, close, callback or implicit replay.


if __name__ == '__main__' and len(sys.argv) == 3 and sys.argv[1] in ('--crash-probe', '--busy-probe'):
    _probe(sys.argv[1], Path(sys.argv[2]))
