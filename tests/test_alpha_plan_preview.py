"""Approval preview regressions over descriptive in-memory lifecycle snapshots.

No workspace provisioning, operational Store, provider request or Tool execution.
"""
from contextlib import redirect_stdout
from dataclasses import replace
from io import StringIO
import json
import unittest
from unittest import mock

from itru import developer_alpha as alpha, task_run_state as state
from itru.alpha_config import validate_work
from itru.cli import main


class AlphaPlanPreviewTests(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(workspace='synthetic-alpha', store_id='store::preview',
                        project_id='project::preview', max_concurrency=2)
        self.work = {'format_version': 1, 'tasks': [
            {'id': 'read-z', 'objective': '  Inspect "Z" exactly  ',
             'resource': 'MiXeD/e\u0301 input.txt', 'dependencies': []},
            {'id': 'read-A', 'objective': 'Inspect \u00e9 / \u6587\u4ef6',
             'resource': 'Docs/\u6587\u4ef6.txt', 'dependencies': []},
            {'id': 'blocked', 'objective': 'Wait for governance closure',
             'resource': 'later.txt', 'dependencies': ['read-A', 'read-z']}]}
        self.enroll()
        patch = mock.patch.object(alpha, 'read_json', return_value=self.work)
        patch.start()
        self.addCleanup(patch.stop)

    def enroll(self):
        self.tasks = {node.task_id: state.TaskSnapshot(
            node.task_id, node.definition_reference, 'planned', 1, 'enrolled')
            for node in validate_work(self.work).nodes}
        self.store = mock.Mock(spec=['get_task', 'close'])
        self.store.get_task.side_effect = self.tasks.get

    def succeeded(self):
        run = alpha.AgentExecutionRun('run::preview', alpha.AgentExecutionContract(
            'read-A', 'standard-change', 'implement', 'software-engineer',
            'actor::preview', 'runtime::preview', 'option::preview', 'environment::preview',
            'repository_file_read', 'Docs/\u6587\u4ef6.txt', 'deep'))
        ledger = alpha.AuthorizationDomainIdentity('domain::preview', 'ledger::preview', 1)
        observed = state.RunSnapshot(alpha.AgentOperationToolBinding(run, alpha.TOOL),
            ledger, 'succeeded', 4,
            ('ledger::preview', 'domain::preview', 'human', 'issuer::preview', 'grant::preview'))
        self.tasks['read-A'] = replace(self.tasks['read-A'], state='in_progress',
                                       revision=4, reason='succeeded', runs=(observed,))

    def test_selected_subjects_are_exact_and_in_selection_order(self):
        plan = alpha.make_plan(self.cfg, self.store)
        self.assertEqual(plan['selected'], ['read-A', 'read-z'])
        self.assertEqual(plan['selected_subjects'], [
            {'task_id': 'read-A', 'objective': 'Inspect \u00e9 / \u6587\u4ef6',
             'resource': 'Docs/\u6587\u4ef6.txt'},
            {'task_id': 'read-z', 'objective': '  Inspect "Z" exactly  ',
             'resource': 'MiXeD/e\u0301 input.txt'}])
        self.assertEqual(plan['tasks'][0]['dependencies']['state'], 'blocked')

    def test_maximum_length_subjects_survive_cli_json_without_truncation(self):
        task = dict(id='T' * 4096, objective='\u6587' * 4096,
                    resource='r' * 4096, dependencies=[])
        self.work['tasks'] = [task]
        self.enroll()
        output = StringIO()
        with mock.patch.object(alpha, 'load_config', return_value=self.cfg), \
                mock.patch.object(alpha, 'open_state', return_value=self.store), \
                mock.patch.object(alpha, 'plan_task', side_effect=AssertionError('provider invoked')), \
                mock.patch.object(alpha, 'AlphaExecution', side_effect=AssertionError('execution invoked')), \
                redirect_stdout(output):
            code = main(['alpha', 'plan', '--config', 'synthetic-alpha/alpha.json'])
        self.assertEqual(code, 0)
        plan = json.loads(output.getvalue())
        self.assertEqual(plan['selected_subjects'], [
            {'task_id': task['id'], 'objective': task['objective'], 'resource': task['resource']}])
        self.assertEqual(plan['status'], 'approval_required')

    def test_run_resume_and_complete_keep_existing_approval_digests(self):
        # Captured from make_plan before adding selected_subjects.
        cases = [('run', None, None,
                  'f3dc9c5a9a0979f4606fb6bd3e0eb721bcad3c0b7b09713319c50a785b5d4d5c'),
                 ('resume', 'read-A', None,
                  'c816a4b9051a58feefd74f7cb5f1e2ae3f5cde82a9dd873aa19fd8375f813e78'),
                 ('complete', 'read-A', 'human::governance-closure',
                  'e82c2ddcc156fe11122a217cd30ae2ce87ea3505bfa4d214ecd1c970a0daed1d')]
        for action, task_id, reference, expected in cases:
            if action != 'run':
                self.succeeded()
            with self.subTest(action=action):
                plan = alpha.make_plan(self.cfg, self.store, action, task_id, reference)
                self.assertEqual(plan['approval'], expected)
                alpha.require_approval(plan, expected)
                with self.assertRaisesRegex(ValueError, 'fresh exact Human approval required'):
                    alpha.require_approval(plan, None)
                if action != 'run':
                    self.assertEqual(plan['selected'], ['read-A'])
                    self.assertEqual(plan['selected_subjects'], [
                        {'task_id': 'read-A', 'objective': 'Inspect \u00e9 / \u6587\u4ef6',
                         'resource': 'Docs/\u6587\u4ef6.txt'}])

    def test_no_selection_has_empty_preview_and_no_approval(self):
        for key, task in self.tasks.items():
            self.tasks[key] = replace(task, state='blocked', revision=2, reason='manual')
        plan = alpha.make_plan(self.cfg, self.store)
        self.assertEqual(plan['status'], 'no_runnable_tasks')
        self.assertEqual(plan['selected'], [])
        self.assertEqual(plan['selected_subjects'], [])
        self.assertIsNone(plan['approval'])

    def test_config_work_and_lifecycle_changes_still_invalidate_approval(self):
        approval = alpha.make_plan(self.cfg, self.store)['approval']
        for change in ('config', 'work', 'lifecycle'):
            with self.subTest(change=change):
                if change == 'config':
                    self.cfg['max_concurrency'] = 1
                elif change == 'work':
                    self.cfg['max_concurrency'] = 2
                    self.work['tasks'][0]['objective'] += ' changed'
                    self.enroll()
                else:
                    self.work['tasks'][0]['objective'] = '  Inspect "Z" exactly  '
                    self.enroll()
                    self.succeeded()
                plan = alpha.make_plan(self.cfg, self.store)
                with self.assertRaisesRegex(ValueError, 'fresh exact Human approval required'):
                    alpha.require_approval(plan, approval)
