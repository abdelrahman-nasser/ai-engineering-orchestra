"""18 exact storage scenarios. Owned disposable local fixtures only.

Cooperative in-memory Fact membership tests storage mechanics; it makes no
original-producer claim. Only J27/J29 create fresh disposable v4 ledger fixtures
via existing reviewed helpers. Journal operations read that ledger without writes.
No subprocess, discovery, operational registry or hostile fixture is used.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import sqlite3
import stat
import tempfile
import threading
import unittest
from unittest import mock

from itru import agent_execution_journal as journal
from itru import sqlite_agent_execution_journal_store as storage
from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from tests.test_agent_execution_journal import _body, _storage_fact


def _cleanup_owned(temporary):
    root = Path(temporary.name)
    if (root.resolve() != root or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith('itru-061-journal-') or root.is_symlink()
            or getattr(root.lstat(), 'st_file_attributes', 0) & 0x400):
        raise AssertionError('Journal fixture cleanup containment failure')
    for parent, directories, files in os.walk(root, followlinks=False):
        for name in (*directories, *files):
            path = Path(parent) / name
            info = path.lstat()
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or getattr(info, 'st_file_attributes', 0) & 0x400
                    or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)):
                raise AssertionError('Journal fixture cleanup rejected foreign object')
    temporary.cleanup()


class _Clock:
    def __init__(self):
        self.value = datetime(2026, 10, 14, 0, 0, 3, tzinfo=timezone.utc)
        self.calls = 0
        self.error = None

    def __call__(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.value


def _different(index):
    body = _body()
    body['execution_entry']['identity'][3] += f'::{index}'
    body['admission']['grant']['grant_id'] += f'::{index}'
    body['admission']['grant']['run']['run_id'] += f'::{index}'
    body['admission']['tool_binding']['run']['run_id'] += f'::{index}'
    return body


class JournalStorageScenarios(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='itru-061-journal-', dir=Path(tempfile.gettempdir()).resolve())
        self.root = Path(self.temporary.name).resolve()
        self.assertEqual(self.root.parent, Path(tempfile.gettempdir()).resolve())
        self.addCleanup(_cleanup_owned, self.temporary)
        storage._security(self.root, directory=True, establish=True)
        self.identity = AuthorizationDomainIdentity('domain::journal-fixture', 'ledger::journal-fixture', 1)
        self.configuration = storage.SqliteExecutionJournalConfiguration(self.root / 'journal.sqlite3', self.root, 'journal::fixture', self.identity)
        storage.SqliteExecutionJournalStore.provision(self.configuration, metadata_authorized=True)
        self.clock = _Clock()
        self.store = storage.SqliteExecutionJournalStore(self.configuration, clock=self.clock)
        self.facts = (_storage_fact(_body()), _storage_fact(_body('result_observed')))
        self.key = journal._subject_key(_body())
        print(f'ITRU061_STORAGE_FIXTURE {self._testMethodName} parent={self.root} journal=journal::fixture', flush=True)

    def raw(self, sql, parameters=()):
        with closing(sqlite3.connect(self.configuration.database_path)) as connection, connection:
            connection.execute(sql, parameters)

    def historical_fixture(self, *, unknown_commit=False):
        # Lazy imports: these helpers are used only in the two exact ledger cases.
        from tests import test_jit_execution_attempt_authorization as predecessor
        from tests import test_durable_execution_entry_and_controlled_invocation as original
        rig = predecessor._Rig(self)
        self.assertEqual(rig.fixture.root.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(rig.fixture.root.name.startswith('aio-056-'))
        cap = rig.cap(self)
        if unknown_commit:
            def lost(point):
                if point == 'entry.after_commit_before_response':
                    raise OSError('synthetic lost acknowledgement')
            with mock.patch.object(rig.store, '_fault', side_effect=lost):
                result = original._enter(rig, cap)
            self.assertEqual(result.outcome, 'commit_unknown')
        else:
            result = original._enter(rig, cap)
            self.assertEqual(result.outcome, 'entered')
        config = replace(self.configuration, database_path=self.root / 'history.sqlite3',
            journal_id='journal::history', ledger_identity=rig.subject.ledger_identity)
        history_store = storage.SqliteExecutionJournalStore.provision(config, metadata_authorized=True)
        recorder = journal.ExecutionJournalRecorder(history_store, rig.store, metadata_authorized=True)
        key = (rig.subject.ledger_identity.ledger_instance_id, *rig.claim.identity)
        return rig, recorder, key

    def test_J17_atomic_ordered_batch(self):
        receipt = self.store.append(self.facts)
        self.assertEqual(receipt.outcome, 'appended')
        docs = [item.document for item in receipt.records]
        self.assertEqual([item['sequence'] for item in docs], [1, 2])
        self.assertEqual([item['event_kind'] for item in docs], ['entry_observed', 'result_observed'])
        self.assertEqual(docs[0]['recorded_at'], docs[1]['recorded_at'])
        self.assertEqual(self.clock.calls, 1)

    def test_J18_exact_retry_no_new_clock(self):
        first = self.store.append(self.facts)
        self.clock.error = AssertionError('duplicate cannot sample clock')
        second = self.store.append(self.facts)
        self.assertEqual(second.outcome, 'existing')
        self.assertEqual(first.records, second.records)
        self.assertEqual(self.clock.calls, 1)

    def test_J19_conflict_not_replacement(self):
        self.assertEqual(self.store.append(self.facts).outcome, 'appended')
        changed = _body('result_observed', count=1)
        self.assertEqual(self.store.append((_storage_fact(changed),)).outcome, 'conflict')
        changed = _body(); changed['ledger_identity']['domain_generation'] = 2
        self.assertEqual(self.store.append((_storage_fact(changed),)).outcome, 'integrity_failure')
        changed = _different(3)
        changed['admission']['grant']['run']['run_id'] = _body()['admission']['grant']['run']['run_id']
        changed['admission']['tool_binding']['run']['run_id'] = changed['admission']['grant']['run']['run_id']
        for part in ('grant', 'tool_binding'):
            changed['admission'][part]['run']['contract']['resource'] = 'fixtures/other.bin'
        self.assertEqual(self.store.append((_storage_fact(changed),)).outcome, 'conflict')
        self.assertEqual(len(self.store.lookup(self.key)), 2)

    def race(self, left, right):
        gate, results, errors = threading.Barrier(2), [], []
        def worker(facts):
            try:
                other = storage.SqliteExecutionJournalStore(self.configuration, clock=_Clock())
                gate.wait(timeout=10)
                results.append(other.append(facts).outcome)
            except BaseException as error:
                errors.append(type(error).__name__)
        workers = [threading.Thread(target=worker, args=(facts,)) for facts in (left, right)]
        for worker in workers: worker.start()
        for worker in workers: worker.join(timeout=20)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        return sorted(results)

    def test_J20_concurrent_exact_duplicate(self):
        self.assertEqual(self.race(self.facts, self.facts), ['appended', 'existing'])
        self.assertEqual(len(self.store.lookup(self.key)), 2)

    def test_J21_concurrent_conflict(self):
        second = (self.facts[0], _storage_fact(_body('result_observed', count=1)))
        self.assertEqual(self.race(self.facts, second), ['appended', 'conflict'])
        self.assertEqual(len(self.store.lookup(self.key)), 2)

    def test_J22_clock_and_overflow(self):
        self.assertEqual(self.store.append((self.facts[0],)).outcome, 'appended')
        self.assertEqual(self.store.append((_storage_fact(_different(1)),)).outcome, 'appended')
        self.clock.value -= timedelta(seconds=1)
        self.assertEqual(self.store.append((_storage_fact(_different(2)),)).outcome, 'clock_failure')
        self.clock.error = OSError('clock unavailable')
        self.assertEqual(self.store.append((_storage_fact(_different(3)),)).outcome, 'clock_failure')
        self.clock.error = None
        with mock.patch.object(journal, 'MAX_SEQUENCE', 2):
            self.assertEqual(self.store.append((_storage_fact(_different(4)),)).outcome, 'integrity_failure')
        self.assertEqual(len(self.store.page()[0]), 2)

    def test_J23_precommit_fatal_cut(self):
        class FatalCut(BaseException):
            pass
        def cut(point):
            if point == 'append.after_insert':
                raise FatalCut()
        with mock.patch.object(self.store, '_fault', side_effect=cut), self.assertRaises(FatalCut):
            self.store.append(self.facts)
        restarted = storage.SqliteExecutionJournalStore(self.configuration, clock=_Clock())
        self.assertEqual(restarted.lookup(self.key), ())
        self.assertEqual(restarted.append(self.facts).records[0].document['sequence'], 1)

    def test_J24_commit_unknown_retrieval(self):
        def lost(point):
            if point == 'append.after_commit_before_response':
                raise OSError('synthetic acknowledgement lost')
        with mock.patch.object(self.store, '_fault', side_effect=lost):
            receipt = self.store.append(self.facts)
        self.assertEqual(receipt.outcome, 'commit_unknown')
        self.assertEqual(len(receipt.records), 0)
        self.assertEqual(len(self.store.lookup(self.key)), 2)
        self.clock.error = AssertionError('no new recording')
        self.assertEqual(self.store.append(self.facts).outcome, 'existing')

    def test_J25_restart_descriptive_retrieval(self):
        receipt = self.store.append(self.facts)
        restarted = storage.SqliteExecutionJournalStore(self.configuration)
        self.assertEqual(restarted.lookup(self.key), receipt.records)
        with self.assertRaises(journal.JournalIntegrityError):
            restarted.lookup(('foreign', *self.key[1:]))
        for item in receipt.records:
            self.assertFalse(journal._trusted_fact(item))
            self.assertFalse(hasattr(item, 'invoke'))

    def test_J26_stable_pagination(self):
        self.store.append(self.facts)
        first, cursor = self.store.page(limit=1)
        self.store.append((_storage_fact(_different(1)),))
        second, done = self.store.page(cursor=cursor, limit=1)
        self.assertEqual([item.document['sequence'] for item in (*first, *second)], [1, 2])
        self.assertEqual(done.high_water, 2)
        self.assertEqual(self.store.page(cursor=done)[0], ())
        self.assertEqual(len(self.store.page()[0]), 3)

    def test_J27_history_only_reconciliation(self):
        rig, recorder, key = self.historical_fixture()
        from tests import test_dispatch_claim_lease_foundation as claims
        before = claims._snapshot(rig.store.configuration.database_path)
        report = recorder.reconcile(key, append_missing=True)
        self.assertEqual(report.state, 'unresolved_result')
        self.assertEqual(report.records[0].document['provenance'], 'authoritative_entry_history')
        self.assertEqual(report.records[0].document['result_summary'], None)
        self.assertEqual(recorder.reconcile(key, append_missing=True).records, report.records)
        self.assertEqual(claims._snapshot(rig.store.configuration.database_path), before)
        self.assertIsNone(rig.store._read_execution_journal_history((key[1], key[2], key[3], 'grant::absent')).subject_json)

    def test_J28_missing_result_is_unresolved(self):
        receipt = self.store.append((self.facts[0],))
        self.assertEqual(len(receipt.records), 1)
        self.assertIsNone(receipt.records[0].document['result_summary'])
        self.assertEqual(receipt.records[0].document['event_kind'], 'entry_observed')
        self.assertFalse(hasattr(receipt.records[0], 'outcome'))

    def test_J29_unknown_entry_commit(self):
        from itru.sqlite_agent_execution_dispatch_admission_store import SqliteAdmissionStoreIntegrityError
        rig, recorder, key = self.historical_fixture(unknown_commit=True)
        ledger_configuration = rig.store.configuration
        paths = (ledger_configuration.database_path, recorder._store.configuration.database_path)

        def snapshot():
            snapshots = []
            for path in paths:
                with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as connection:
                    connection.execute('PRAGMA query_only=ON')
                    connection.execute('BEGIN')
                    snapshots.append(tuple(connection.iterdump()))
            return tuple(snapshots)

        append = recorder._store.append
        for error_type, receipt_outcome, expected_state in (
                (journal.JournalIntegrityError, 'integrity_failure', 'integrity_failure'),
                (OSError, 'storage_unavailable', 'evidence_unavailable')):
            with self.subTest(append_failure=receipt_outcome):
                receipts = []

                def fail_before_insert(point):
                    if point == 'append.before_insert':
                        raise error_type()

                def capture_append(observations):
                    receipt = append(observations)
                    receipts.append(receipt)
                    return receipt

                before = snapshot()
                with (
                        mock.patch.object(recorder._store, 'append', side_effect=capture_append) as append_call,
                        mock.patch.object(recorder._store, '_fault', side_effect=fail_before_insert) as fault):
                    reconciliation = recorder.reconcile(key, append_missing=False)
                    self.assertEqual(reconciliation.state, 'unresolved_result')
                    self.assertEqual(reconciliation.records, ())
                    self.assertIsNone(reconciliation.receipt)
                    append_call.assert_not_called()
                    fault.assert_not_called()
                    self.assertEqual(receipts, [])
                    self.assertEqual(snapshot(), before)

                    reconciliation = recorder.reconcile(key, append_missing=True)
                    append_call.assert_called_once()
                    fault.assert_called_once_with('append.before_insert')
                    self.assertEqual(reconciliation.state, expected_state)
                    self.assertEqual(reconciliation.records, ())
                    self.assertEqual(len(receipts), 1)
                    self.assertIs(reconciliation.receipt, receipts[0])
                    self.assertEqual(reconciliation.receipt.outcome, receipt_outcome)
                    self.assertEqual(reconciliation.receipt.subject_identity, key)
                    self.assertEqual(reconciliation.receipt.event_kinds, ('entry_observed',))
                    self.assertEqual(reconciliation.receipt.records, ())
                    self.assertEqual(snapshot(), before)

        report = recorder.reconcile(key, append_missing=True)
        self.assertEqual(report.state, 'unresolved_result')
        self.assertEqual(len(report.records), 1)
        self.assertEqual(report.records[0].document['event_kind'], 'entry_observed')
        self.assertIsNone(report.records[0].document['result_summary'])
        self.assertEqual(snapshot()[0], before[0])
        absent = (*key[:-1], 'grant::absent')
        self.assertEqual(recorder.reconcile(absent).state, 'no_entry_evidence')
        with mock.patch.object(rig.store, '_read_execution_journal_history', side_effect=OSError('unavailable')):
            self.assertEqual(recorder.reconcile(key).state, 'evidence_unavailable')
        self.assertFalse(hasattr(report, 'resume'))

        missing = ledger_configuration.database_path.with_name('arch-m1-unavailable.sqlite3')
        self.assertTrue(missing.resolve().is_relative_to(rig.fixture.root))
        self.assertFalse(missing.exists())
        before = snapshot()
        with mock.patch.object(rig.store, 'configuration', replace(ledger_configuration, database_path=missing)):
            for append_missing in (False, True):
                with self.subTest(evidence='unavailable', append_missing=append_missing):
                    reconciliation = recorder.reconcile(key, append_missing=append_missing)
                    self.assertEqual(reconciliation.state, 'evidence_unavailable')
                    self.assertEqual(reconciliation.records, ())
                    self.assertIsNone(reconciliation.receipt)
                    self.assertFalse(missing.exists())
                    self.assertEqual(snapshot(), before)

        with closing(sqlite3.connect(ledger_configuration.database_path)) as connection, connection:
            connection.execute('CREATE TABLE arch_m1_corruption_marker (id INTEGER)')
        before = snapshot()
        with self.assertRaisesRegex(SqliteAdmissionStoreIntegrityError, 'sqlite_schema object/DDL fingerprint mismatch'):
            rig.store._read_execution_journal_history(key[1:])
        self.assertEqual(snapshot(), before)
        for append_missing in (False, True):
            with self.subTest(evidence='corrupted', append_missing=append_missing):
                reconciliation = recorder.reconcile(key, append_missing=append_missing)
                self.assertEqual(reconciliation.state, 'integrity_failure')
                self.assertEqual(reconciliation.records, ())
                self.assertIsNone(reconciliation.receipt)
                self.assertEqual(snapshot(), before)

    def test_J30_corruption_and_orphan(self):
        self.assertEqual(self.store.append((self.facts[1],)).outcome, 'integrity_failure')
        self.assertEqual(self.store.lookup(self.key), ())
        committed = self.store.append(self.facts)
        self.raw('DROP TRIGGER journal_entries_no_update')
        self.raw("UPDATE journal_entries SET record_json='{}' WHERE sequence=2")
        trigger = next(statement for statement in storage._schema_resource()[0]
                       if statement.startswith('CREATE TRIGGER journal_entries_no_update '))
        self.raw(trigger)
        with self.assertRaises(journal.JournalIntegrityError):
            self.store.lookup(self.key)
        self.assertEqual(self.store.append(self.facts).outcome, 'integrity_failure')
        self.raw('DROP TRIGGER journal_entries_no_update')
        self.raw('UPDATE journal_entries SET record_json=?,sequence=3 WHERE sequence=2', (committed.records[1].canonical_json,))
        self.raw(trigger)
        with self.assertRaises(journal.JournalIntegrityError):
            self.store.lookup(self.key)

    def test_J31_unknown_missing_partial_schema(self):
        missing = replace(self.configuration, database_path=self.root / 'missing.sqlite3')
        with self.assertRaises((OSError, ValueError)):
            storage.SqliteExecutionJournalStore(missing)
        self.assertFalse(missing.database_path.exists())
        self.raw('PRAGMA user_version=2')
        with self.assertRaises(storage.JournalIncompatibleSchema):
            storage.SqliteExecutionJournalStore(self.configuration)

    def test_J32_guards_and_coherent_copy_limit(self):
        self.store.append(self.facts)
        for sql in ("UPDATE journal_entries SET recorded_at=recorded_at", 'DELETE FROM journal_entries',
                    'INSERT OR REPLACE INTO journal_entries SELECT * FROM journal_entries WHERE sequence=1'):
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.raw(sql)
        # TEST ONLY privileged coherent-copy limit, not a production restore API.
        destination = self.root / 'descriptive-copy.sqlite3'
        with closing(sqlite3.connect(self.configuration.database_path)) as source, closing(sqlite3.connect(destination)) as copy:
            with source, copy:
                source.backup(copy)
        storage._security(destination, directory=False, establish=True)
        copied = storage.SqliteExecutionJournalStore(replace(self.configuration, database_path=destination))
        self.assertEqual(copied.lookup(self.key), self.store.lookup(self.key))

    def test_J33_history_not_current_authority(self):
        self.clock.value = datetime(2026, 10, 16, tzinfo=timezone.utc)  # Recorded Grant already expired now.
        self.assertEqual(self.store.append(self.facts).outcome, 'appended')
        historical = self.store.lookup(self.key)
        self.assertEqual(historical[1].document['result_summary']['outcome'], 'succeeded')
        self.assertFalse(hasattr(historical[1], 'grant_authority'))

    def test_J34_explicit_provisioning_only(self):
        with self.assertRaises(FileExistsError):
            storage.SqliteExecutionJournalStore.provision(self.configuration, metadata_authorized=True)
        other = replace(self.configuration, database_path=self.root / 'not-authorized.sqlite3')
        with self.assertRaises(journal.JournalIntegrityError):
            storage.SqliteExecutionJournalStore.provision(other)
        self.assertFalse(other.database_path.exists())
        partial = replace(self.configuration, database_path=self.root / 'partial.sqlite3')
        with mock.patch.object(storage, '_schema_resource', return_value=(['invalid SQL'], ())):
            with self.assertRaises(sqlite3.Error):
                storage.SqliteExecutionJournalStore.provision(partial, metadata_authorized=True)
        self.assertTrue(partial.database_path.exists())
        with self.assertRaises(storage.JournalIncompatibleSchema):
            storage.SqliteExecutionJournalStore(partial)
