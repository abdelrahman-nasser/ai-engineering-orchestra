"""Six genuine controlled Journal scenarios on owned synthetic native fixtures.

The exact ITRU-060 rig is reused without external/hostile paths or child tools.
Journal storage is confined to a protected child of that nonce-owned Temp parent.
Importing this module creates no fixture, database, registry or native root.
"""
from __future__ import annotations

from pathlib import Path
import os
import threading
import unittest
from unittest import mock
from uuid import uuid4

from itru import agent_execution_journal as journal
from itru import agent_execution_result as result
from itru import _execution_entry_and_controlled_invocation as entry
from itru import _native_repository_file_read as native
from itru import sqlite_agent_execution_journal_store as storage
from tests import test_controlled_execution_result as predecessor


class ControlledJournalScenarios(unittest.TestCase):
    def rig(self, data=predecessor.DATA):
        self.assertEqual(os.name, 'nt', 'genuine native fixture requires supported Windows host; no skip')
        rig = predecessor.ControlledResultScenarios.rig(self, data)
        directory = Path(rig.h._temporary_directory.name).resolve() / 'journal'
        self.assertTrue(directory.parent == rig.h.root.parent.resolve())
        directory.mkdir()
        storage._security(directory, directory=True, establish=True)
        configuration = storage.SqliteExecutionJournalConfiguration(directory / 'journal.sqlite3',
            directory, 'journal::itru-061::' + uuid4().hex, rig.subject.ledger_identity)
        store = storage.SqliteExecutionJournalStore.provision(configuration, metadata_authorized=True)
        recorder = journal.ExecutionJournalRecorder(store, rig.store, metadata_authorized=True)
        rig.coordinator = entry._ControlledInvocationCoordinator(rig.a, rig.root, journal=recorder)
        rig.journal_store, rig.journal_recorder = store, recorder
        print(f'ITRU061_NATIVE_JOURNAL {self._testMethodName} parent={directory.parent} journal={configuration.journal_id}', flush=True)
        return rig

    def documents(self, rig):
        return tuple(item.document for item in rig.journal_store.page()[0])

    def test_J35_success_and_journal_failure(self):
        rig = self.rig()
        outcome = rig.invoke(self)
        self.assertEqual(outcome.journal_receipt.outcome, 'appended')
        self.assertTrue(result._is_authoritative_result(outcome.result))
        self.assertEqual(outcome.result.payload.data, predecessor.DATA)
        docs = self.documents(rig)
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[1]['result_summary'], dict(outcome='succeeded', diagnostic_code=None, byte_count=len(predecessor.DATA)))
        self.assertNotIn(predecessor.DATA.decode('ascii'), outcome.journal_receipt.records[1].canonical_json)
        other = self.rig()
        with mock.patch.object(other.journal_store, 'append', side_effect=OSError('synthetic Journal unavailable')):
            preserved = other.invoke(self)
        self.assertEqual(preserved.result.outcome, 'succeeded')
        self.assertEqual(preserved.result.payload.data, predecessor.DATA)
        self.assertTrue(result._is_authoritative_result(preserved.result))
        self.assertEqual(preserved.journal_receipt.outcome, 'storage_unavailable')
        self.assertEqual(self.documents(other), ())

    def test_J36_original_failure_outcomes(self):
        for ambiguous in (False, True):
            with self.subTest(ambiguous=ambiguous):
                rig = self.rig(None if not ambiguous else predecessor.DATA)
                cap = rig.cap(self)
                if ambiguous:
                    with mock.patch.object(rig.root._native, 'read_data', side_effect=native._NativeFailure('read_failure')):
                        outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
                else:
                    outcome = rig.coordinator.invoke(cap, rig.principal, rig.decision)
                expected = 'effect_ambiguous' if ambiguous else 'failed_before_effect'
                self.assertEqual(outcome.result.outcome, expected)
                summary = self.documents(rig)[1]['result_summary']
                self.assertEqual(summary['outcome'], expected)
                self.assertEqual(summary['diagnostic_code'], 'read_failure' if ambiguous else 'resource_missing')
                self.assertIsNone(summary['byte_count'])
                with mock.patch.object(rig.root._native, 'open_component', side_effect=AssertionError('no replay')) as opens:
                    repeated = rig.coordinator.invoke(cap, rig.principal, rig.decision)
                opens.assert_not_called()
                self.assertIsNone(repeated.result)
                self.assertEqual(len(self.documents(rig)), 2)

    def test_J37_fatal_and_construction_missing_result(self):
        rig = self.rig()
        cap = rig.cap(self)
        with mock.patch.object(rig.root._native, 'read_data', side_effect=native._UnverifiedCompletion('synthetic fatal')):
            with self.assertRaises(native._UnverifiedCompletion):
                rig.coordinator.invoke(cap, rig.principal, rig.decision)
        self.assertEqual(cap._cell.state, 'CONSUMED')
        docs = self.documents(rig)
        self.assertEqual([item['event_kind'] for item in docs], ['entry_observed'])
        self.assertIsNone(docs[0]['result_summary'])
        other = self.rig()
        with mock.patch.object(result, '_map_invocation', side_effect=ValueError('synthetic private construction failure')):
            with self.assertRaises(result._ResultIntegrityError) as caught:
                other.invoke(self)
        self.assertIsNone(caught.exception.__context__)
        self.assertEqual([item['event_kind'] for item in self.documents(other)], ['entry_observed'])
        key = (other.subject.ledger_identity.ledger_instance_id, *other.claim.identity)
        self.assertEqual(other.journal_recorder.reconcile(key).state, 'unresolved_result')

    def test_J38_restart_never_restores_result_or_capability(self):
        rig = self.rig()
        outcome = rig.invoke(self)
        old_records = rig.journal_store.lookup(outcome.result.identity)
        rig.root.close(); rig.a.close(); rig.h.restart()
        reopened = storage.SqliteExecutionJournalStore(rig.journal_store.configuration)
        recorder = journal.ExecutionJournalRecorder(reopened, rig.h.coordinator._session._store, metadata_authorized=True)
        with mock.patch.object(rig.root._native, 'open_component', side_effect=AssertionError('no target access')) as opens:
            report = recorder.reconcile(outcome.result.identity)
        opens.assert_not_called()
        self.assertEqual(report.state, 'recorded_result')
        self.assertEqual(report.records, old_records)
        with self.assertRaises(TypeError):
            result.AgentExecutionResult(report.records[1].document)
        self.assertFalse(hasattr(report, 'invoke'))
        self.assertFalse(hasattr(report, 'capability'))

    def test_J39_scope_order_and_readonly_ledger(self):
        rig = self.rig()
        append = rig.journal_store.append
        history = rig.store._read_execution_journal_history
        calls = []
        def assert_outside():
            self.assertFalse(getattr(rig.a.guard.thread, 'read', False))
            self.assertFalse(getattr(rig.a.guard.thread, 'leaf', False))
            self.assertEqual(rig.session._thread_operations.get(threading.get_ident(), 0), 0)
        def append_outside(facts):
            assert_outside(); calls.append('append')
            return append(facts)
        def history_outside(identity):
            assert_outside(); calls.append('history')
            from tests import test_dispatch_claim_lease_foundation as claims
            before = claims._snapshot(rig.store.configuration.database_path)
            observed = history(identity)
            self.assertEqual(claims._snapshot(rig.store.configuration.database_path), before)
            return observed
        with mock.patch.object(rig.journal_store, 'append', side_effect=append_outside), \
                mock.patch.object(rig.store, '_read_execution_journal_history', side_effect=history_outside):
            outcome = rig.invoke(self)
        self.assertEqual(outcome.journal_receipt.outcome, 'appended')
        self.assertEqual(calls, ['history', 'append'])

    def test_J40_commit_unknown_and_history_gap(self):
        rig = self.rig()
        def lost(point):
            if point == 'append.after_commit_before_response':
                raise OSError('synthetic lost acknowledgement')
        with mock.patch.object(rig.journal_store, '_fault', side_effect=lost):
            outcome = rig.invoke(self)
        self.assertEqual(outcome.result.outcome, 'succeeded')
        self.assertTrue(result._is_authoritative_result(outcome.result))
        self.assertEqual(outcome.journal_receipt.outcome, 'commit_unknown')
        with mock.patch.object(rig.root._native, 'open_component', side_effect=AssertionError('no replay')) as opens:
            report = rig.journal_recorder.reconcile(outcome.result.identity)
        opens.assert_not_called()
        self.assertEqual(report.state, 'recorded_result')
        other = self.rig()
        with mock.patch.object(result, '_map_invocation', side_effect=ValueError('synthetic failure')), \
                mock.patch.object(other.journal_store, 'append', side_effect=OSError('synthetic gap')):
            with self.assertRaises(result._ResultIntegrityError):
                other.invoke(self)
        self.assertEqual(self.documents(other), ())
        key = (other.subject.ledger_identity.ledger_instance_id, *other.claim.identity)
        with mock.patch.object(other.root._native, 'open_component', side_effect=AssertionError('no recovery effect')) as opens:
            missing = other.journal_recorder.reconcile(key, append_missing=True)
        opens.assert_not_called()
        self.assertEqual(missing.state, 'unresolved_result')
        self.assertEqual(missing.records[0].document['provenance'], 'authoritative_entry_history')
        self.assertIsNone(missing.records[0].document['result_summary'])
