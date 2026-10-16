"""Genuine controlled Alpha composition in new, private disposable Windows roots.

Only _local_appdata_path is redirected to an owned fixture registry. Native read
faults test original Result mapping; no reader/Result/authority replacement.
"""
from contextlib import closing
from dataclasses import replace
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest import mock

from itru import developer_alpha as alpha
from itru import alpha_config as config
from itru import _native_repository_file_read as native
from itru import windows_local_authorization_domain_owner as windows
from itru.cli import build_parser
from itru.task_run_state import StateConflictError


def cleanup_owned(temporary):
    root = Path(temporary.name)
    if (root.resolve() != root or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith('itru-064-')):
        raise AssertionError('Alpha fixture cleanup containment failure')
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            path = Path(parent)/name
            info = path.lstat()
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or getattr(info, 'st_file_attributes', 0) & 0x400
                    or stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
                raise AssertionError('foreign Alpha cleanup object')
    temporary.cleanup()
    if root.exists():
        raise AssertionError('Alpha fixture residue')
    print('ITRU064_CLEAN ' + str(root), flush=True)


class AlphaTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(os.name, 'nt', 'supported genuine Windows Alpha fixture required; no skip')
        temp = tempfile.TemporaryDirectory(prefix='itru-064-alpha-', dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(cleanup_owned, temp)
        self.root = Path(temp.name).resolve()
        registry = self.root/'appdata'
        registry.mkdir()
        alpha._security(registry, directory=True, establish=True)
        patch = mock.patch.object(windows, '_local_appdata_path', return_value=registry)
        patch.start()
        self.addCleanup(patch.stop)
        self.ws = self.root/'workspace'
        alpha.initialize(self.ws)
        self.cfg = config.load_config(self.ws/'alpha.json')

    def load(self, tasks=None):
        work = alpha.example_work()
        if tasks is not None:
            work['tasks'] = tasks
        path = self.root/'supplied.json'
        path.write_text(json.dumps(work), encoding='utf-8')
        alpha.load_work(self.cfg, path)

    def plan(self, action='run', task=None, reference=None):
        with closing(alpha.open_state(self.cfg)) as store:
            return alpha.make_plan(self.cfg, store, action, task, reference)

    def complete(self, task):
        reference = 'human-fixture::all-required-governance-satisfied'
        plan = self.plan('complete', task, reference)
        return alpha.command(build_parser().parse_args(['alpha', 'complete', '--config', str(self.ws/'alpha.json'),
            '--task', task, '--reference', reference, '--approve', plan['approval']]))

    def test_01_approval_no_effect_then_original_results(self):
        self.load()
        plan = self.plan()
        self.assertEqual(plan['selected'], ['read-a', 'read-b'])
        with self.assertRaises(ValueError):
            alpha.execute(self.cfg, None)
        with closing(alpha.open_state(self.cfg)) as store:
            self.assertFalse(store.get_task('read-a').runs)
        result = alpha.execute(self.cfg, plan['approval'])
        self.assertEqual(result['status'], 'runs_succeeded_governance_pending')
        self.assertEqual([r['outcome'] for r in result['results']], ['succeeded'] * 2)
        with closing(alpha.open_state(self.cfg)) as store:
            history = alpha.history(self.cfg, store)
        self.assertEqual(len(history['journal']), 4)
        self.assertFalse(history['journal_more'])
        self.assertNotIn('nonsecret example', json.dumps(history))
        self.assertEqual(history['selected'], [])
        self.assertEqual(history['tasks'][0]['state'], 'in_progress')

    def test_02_dag_governance_completion(self):
        self.load()
        alpha.execute(self.cfg, self.plan()['approval'])
        self.complete('read-a')
        self.assertEqual(self.plan()['selected'], [])
        self.complete('read-b')
        self.assertEqual(self.plan()['selected'], ['read-c'])
        output = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(output['results'][0]['task_id'], 'read-c')

    def test_03_stale_approval_and_fresh_resume(self):
        self.load([alpha.example_work()['tasks'][0]])
        approval = self.plan()['approval']
        alpha.execute(self.cfg, approval)
        with self.assertRaises(ValueError):
            alpha.execute(self.cfg, approval)
        before = self.plan('resume', 'read-a')
        result = alpha.execute(self.cfg, before['approval'], resume_task='read-a')
        self.assertEqual(result['results'][0]['outcome'], 'succeeded')
        with closing(alpha.open_state(self.cfg)) as store:
            runs = store.get_task('read-a').runs
        self.assertEqual(len(runs), 2)
        self.assertNotEqual(runs[0].run_id, runs[1].run_id)

    def test_04_failure_before_effect_resume(self):
        task = dict(alpha.example_work()['tasks'][0], resource='missing.txt')
        self.load([task])
        result = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(result['results'][0]['outcome'], 'failed_before_effect')
        (self.ws/'repository'/'missing.txt').write_bytes(b'repaired synthetic fixture')
        result = alpha.execute(self.cfg, self.plan('resume', 'read-a')['approval'], resume_task='read-a')
        self.assertEqual(result['results'][0]['outcome'], 'succeeded')

    def test_05_ambiguous_is_not_resumable(self):
        self.load([alpha.example_work()['tasks'][0]])
        with mock.patch.object(native._Native, 'read_data', side_effect=native._NativeFailure('read_failure')):
            result = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(result['results'][0]['outcome'], 'effect_ambiguous')
        with self.assertRaises(ValueError):
            self.plan('resume', 'read-a')

    def test_06_running_restart_interrupted_no_journal_success_repair(self):
        self.load([alpha.example_work()['tasks'][0]])
        with mock.patch.object(alpha.SqliteTaskRunStateStore, 'record_result', side_effect=OSError('synthetic lost observation')):
            with self.assertRaises(OSError):
                alpha.execute(self.cfg, self.plan()['approval'])
        with closing(alpha.open_state(self.cfg)) as store:
            history = alpha.history(self.cfg, store)
        self.assertEqual(history['tasks'][0]['runs'][0]['state'], 'interrupted')
        self.assertEqual(history['journal'][1]['result_summary']['outcome'], 'succeeded')
        with self.assertRaises(ValueError):
            self.plan('resume', 'read-a')

    def test_07_two_agent_workers(self):
        self.load()
        barrier = threading.Barrier(2)
        seen = set()
        def provider(cfg, task):
            seen.add(threading.get_ident())
            barrier.wait(timeout=10)
            return 'synthetic advisory only'
        with mock.patch.object(alpha, 'plan_task', side_effect=provider):
            result = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(len(seen), 2)
        self.assertEqual(result['tool_execution'], 'serialized')

    def test_08_provider_failure_cancels_before_tool(self):
        self.load([alpha.example_work()['tasks'][0]])
        with mock.patch.object(alpha, 'plan_task', side_effect=OSError('synthetic provider failure')):
            result = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(result['status'], 'attention_required')
        with closing(alpha.open_state(self.cfg)) as store:
            history = alpha.history(self.cfg, store)
        self.assertEqual(history['journal'], [])
        self.assertEqual(history['tasks'][0]['runs'][0]['state'], 'cancelled')
        self.assertTrue(self.plan('resume', 'read-a')['approval'])

    def test_09_definition_is_immutable(self):
        self.load()
        changed = alpha.example_work()
        changed['tasks'][0]['objective'] = 'changed'
        path = self.root/'changed.json'
        path.write_text(json.dumps(changed), encoding='utf-8')
        with self.assertRaises(ValueError):
            alpha.load_work(self.cfg, path)

    def test_10_closed_input_and_cycle_rejection(self):
        base = alpha.example_work()
        cases = [dict(base, unknown=True), dict(base, format_version=True)]
        traversal = alpha.example_work()
        traversal['tasks'][0]['resource'] = '../outside.txt'
        cases.append(traversal)
        cycle = alpha.example_work()
        cycle['tasks'][0]['dependencies'] = ['read-c']
        cases.append(cycle)
        duplicate = alpha.example_work()
        duplicate['tasks'].append(duplicate['tasks'][0])
        cases.append(duplicate)
        for bad in cases:
            with self.subTest(value=bad), self.assertRaises(ValueError):
                config.validate_work(bad)

    def test_11_changed_config_invalidates_plan(self):
        self.load()
        approval = self.plan()['approval']
        self.cfg['max_concurrency'] = 1
        with self.assertRaises(ValueError):
            alpha.execute(self.cfg, approval)

    def test_12_journal_failure_is_visible(self):
        self.load([alpha.example_work()['tasks'][0]])
        with mock.patch.object(alpha.SqliteExecutionJournalStore, 'append', side_effect=OSError('synthetic observer unavailable')):
            result = alpha.execute(self.cfg, self.plan()['approval'])
        self.assertEqual(result['status'], 'attention_required')
        self.assertEqual(result['results'][0]['outcome'], 'succeeded')
        self.assertEqual(result['results'][0]['journal'], 'storage_unavailable')

    def test_13_config_unknown_fields_and_duplicate_json(self):
        bad = dict(self.cfg, secret='never accepted')
        (self.ws/'alpha.json').write_text(json.dumps(bad), encoding='utf-8')
        with self.assertRaises(ValueError):
            config.load_config(self.ws/'alpha.json')
        path = self.root/'duplicate.json'
        path.write_text('{"x":1,"x":2}', encoding='utf-8')
        with self.assertRaises(ValueError):
            config.read_json(path)

    def test_14_ledger_identity_mismatch_before_registration(self):
        self.load([alpha.example_work()['tasks'][0]])
        self.cfg['ledger_id'] = 'ledger::different-from-owned-domain'
        approval = self.plan()['approval']
        with self.assertRaisesRegex(ValueError, 'ledger identity mismatch'):
            alpha.execute(self.cfg, approval)
        with closing(alpha.open_state(self.cfg)) as store:
            self.assertFalse(store.get_task('read-a').runs)
