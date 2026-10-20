"""Deterministic CLI diagnostics; no sockets, operational stores or inference.

File fixtures exercise the actual JSON reader and closed validation. ACL checks
are mocked here; these tests do not establish native storage/ACL readiness.
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from dataclasses import replace
from io import BytesIO, StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from itru import alpha_config as config, alpha_provider as provider
from itru import developer_alpha as alpha, task_run_state as state
from itru.alpha_diagnostics import AlphaDiagnosticError, exception_diagnostic
from itru.cli import main
from itru.sqlite_task_run_state import StateStoreBusyError, StateCommitUnknownError


SECRET = 'SCRUM87_PRIVATE_SENTINEL'
TASK = {'id': 'read-a', 'objective': 'Read synthetic input',
        'resource': 'input.txt', 'dependencies': []}


def compatible(**changes):
    return dict(dict(kind='compatible', endpoint='https://provider.invalid/v1/chat/completions',
                     model='synthetic-model', key_env='SCRUM87_TEST_KEY', timeout_seconds=30), **changes)


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='scrum87-diagnostics-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.path = self.root/'alpha.json'
        self.cfg = dict(format_version=1, workspace=str(self.root), max_concurrency=2,
                        **{key: 'synthetic::'+key for key in ('project_id', 'runtime_id',
                           'environment_id', 'domain_id', 'ledger_id', 'journal_id', 'store_id')},
                        provider=compatible())
        patch = mock.patch.object(config, '_security')
        self.security = patch.start()
        self.addCleanup(patch.stop)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        # Any regression into operational composition or networking fails the test.
        for target in ('socket.socket', 'socket.create_connection', 'itru.alpha_provider.build_opener',
                       'itru.developer_alpha.open_state', 'itru.developer_alpha.AlphaExecution',
                       'itru.developer_alpha.initialize', 'itru.developer_alpha.write_private',
                       'itru.developer_alpha.plan_task'):
            self.stack.enter_context(mock.patch(target, side_effect=AssertionError('forbidden operation')))
        self.stack.enter_context(mock.patch.dict('os.environ', {}, clear=True))

    def write(self):
        self.path.write_text(json.dumps(self.cfg), encoding='utf-8')

    def cli(self, *args):
        out, err = StringIO(), StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(['alpha', *args, '--config', str(self.path)])
        combined = out.getvalue()+err.getvalue()
        self.assertNotIn(SECRET, combined)
        self.assertNotIn(str(self.root), combined)
        return code, json.loads(out.getvalue() or err.getvalue()), out.getvalue(), err.getvalue()

    def rejected(self, expected):
        code, result, out, err = self.cli('diagnose')
        self.assertEqual(code, 2)
        self.assertEqual(result['status'], 'rejected')
        self.assertEqual(result['code'], expected)
        self.assertTrue(result['reason'])
        self.assertTrue(result['recovery'])
        self.assertEqual(out, '')
        self.assertTrue(err)
        return result

    def test_demo_is_offline_without_credential_lookup_or_writes(self):
        self.cfg['provider'] = dict(kind='demo', endpoint='', model='offline-demo',
                                    key_env='SCRUM87_TEST_KEY', timeout_seconds=30)
        self.write()
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with mock.patch.object(provider, 'os') as environment:
            environment.environ.get.side_effect = AssertionError('credential lookup')
            code, result, out, err = self.cli('diagnose')
        self.assertEqual((code, result['credential'], result['provider']), (0, 'not_required', 'demo'))
        self.assertEqual(result['network'], 'not_checked')
        self.assertEqual(result['authority'], 'not_checked')
        self.assertEqual(result['storage'], 'not_checked')
        self.assertEqual(result['execution_readiness'], 'not_checked')
        self.assertEqual(err, '')
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})
        self.security.assert_has_calls([mock.call(self.root, directory=True), mock.call(self.path, directory=False)])

    def test_valid_compatible_presence_is_not_verification(self):
        self.cfg['provider']['model'] = SECRET
        self.cfg['provider']['endpoint'] = 'https://provider.invalid/'+SECRET
        self.write()
        with mock.patch.dict('os.environ', {'SCRUM87_TEST_KEY': SECRET}):
            code, result, out, err = self.cli('diagnose')
        self.assertEqual(code, 0)
        self.assertEqual(result['credential'], 'present_not_verified')
        self.assertNotIn('SCRUM87_TEST_KEY', out)
        self.assertNotIn('provider.invalid', out)
        self.assertEqual(err, '')

    def test_intentionally_credential_free_compatible_is_supported(self):
        self.cfg['provider']['key_env'] = ''
        self.write()
        code, result, _, _ = self.cli('diagnose')
        self.assertEqual((code, result['credential']), (0, 'not_configured'))

    def test_missing_and_empty_credential_have_same_safe_recovery(self):
        self.write()
        for env in ({}, {'SCRUM87_TEST_KEY': ''}):
            with self.subTest(env=env), mock.patch.dict('os.environ', env, clear=True):
                result = self.rejected('provider_credential_missing')
                self.assertIn('privately', result['recovery'])

    def test_missing_file_and_unreadable_file(self):
        self.rejected('config_missing')
        self.write()
        with mock.patch.object(config, 'read_json', side_effect=PermissionError(SECRET)):
            self.rejected('config_unreadable')

    def test_invalid_json_duplicate_nonfinite_oversized_and_closed_config(self):
        for data in ('{"'+SECRET+'":', '{"provider":1,"provider":2}',
                     '{"provider":NaN}', 'x'*(1024*1024+1), '[]', json.dumps({**self.cfg, SECRET: SECRET})):
            with self.subTest(size=len(data)):
                self.path.write_text(data, encoding='utf-8')
                self.rejected('config_invalid')

    def test_missing_and_incomplete_provider(self):
        saved = self.cfg.pop('provider')
        self.write()
        self.rejected('provider_config_missing')
        for value in (None, {}, {k: v for k, v in saved.items() if k != 'endpoint'}):
            with self.subTest(provider=value):
                self.cfg['provider'] = value
                self.write()
                self.rejected('provider_config_missing')

    def test_unsupported_selection_is_not_echoed(self):
        for kind in (SECRET, [], None, 1):
            with self.subTest(kind=kind):
                self.cfg['provider'] = compatible(kind=kind)
                self.write()
                self.rejected('provider_unsupported')

    def test_invalid_provider_fields_are_sanitized(self):
        for changes in ({SECRET: SECRET}, {'endpoint': 'https://user:'+SECRET+'@provider.invalid'},
                        {'endpoint': 'http://provider.invalid'}, {'endpoint': ''},
                        {'model': ''}, {'model': SECRET+'\n'}, {'model': []},
                        {'key_env': SECRET+'='}, {'key_env': None},
                        {'timeout_seconds': True}, {'timeout_seconds': 0}, {'timeout_seconds': 121}):
            with self.subTest(changes=changes):
                self.cfg['provider'] = compatible(**changes)
                self.write()
                self.rejected('provider_config_invalid')

    def test_invalid_workspace_identity_and_version_are_not_echoed(self):
        for key, value in (('workspace', SECRET), ('format_version', 2), ('max_concurrency', True)):
            with self.subTest(key=key):
                old = self.cfg[key]
                self.cfg[key] = value
                self.write()
                self.rejected('config_invalid')
                self.cfg[key] = old

    def test_acl_failure_stays_rejected_without_repair(self):
        self.cfg['provider']['key_env'] = ''
        self.write()
        self.security.side_effect = OSError(SECRET)
        self.rejected('config_unreadable')

    def test_other_alpha_commands_use_same_config_errors(self):
        for action in ('plan', 'run', 'history'):
            with self.subTest(action=action):
                code, result, _, _ = self.cli(action)
                self.assertEqual((code, result['code']), (2, 'config_missing'))

    def test_cli_never_emits_raw_exception_or_mutated_diagnostic(self):
        for exc in (ValueError(SECRET), RuntimeError(SECRET), OSError(SECRET),
                    provider.ProviderError(SECRET), StateStoreBusyError(SECRET),
                    StateCommitUnknownError(SECRET)):
            with self.subTest(exception=type(exc).__name__), mock.patch.object(alpha, 'command', side_effect=exc):
                code, result, _, _ = self.cli('diagnose')
                self.assertEqual(code, 2)
                self.assertNotIn(SECRET, json.dumps(result))
        exc = AlphaDiagnosticError('config_invalid')
        exc.code = [SECRET]
        with mock.patch.object(alpha, 'command', side_effect=exc):
            self.rejected('alpha_operation_failed')

    def test_human_approval_failure_is_separate_from_provider_setup(self):
        plan = {'approval': 'a'*64}
        for supplied in (None, '', 'b'*64, '\u6587', b'a'*64):
            with self.subTest(supplied=supplied):
                with self.assertRaises(AlphaDiagnosticError) as caught:
                    alpha.require_approval(plan, supplied)
                self.assertEqual(exception_diagnostic(caught.exception)['code'], 'human_approval_required')
        alpha.require_approval(plan, 'a'*64)
        store = mock.Mock()
        with mock.patch.object(alpha, 'open_state', return_value=store), \
                mock.patch.object(alpha, 'make_plan', return_value=plan), \
                mock.patch.object(alpha, 'load_config', return_value=self.cfg):
            code, result, _, _ = self.cli('run')
        self.assertEqual((code, result['code']), (2, 'human_approval_required'))
        store.close.assert_called_once()

    def test_help_describes_offline_scope(self):
        output = StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as caught:
            main(['alpha', 'diagnose', '--help'])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn('no network, owner acquisition', ' '.join(output.getvalue().split()))

    def test_argument_errors_never_echo_private_values(self):
        for args in (['diagnose', '--config', SECRET, '--api-key', SECRET],
                     ['history', '--config', SECRET, '--after', SECRET],
                     ['plan', '--config', SECRET, '--action', SECRET], [SECRET],
                     ['diagnose']):
            out, err = StringIO(), StringIO()
            with self.subTest(args=args), redirect_stdout(out), redirect_stderr(err), \
                    self.assertRaises(SystemExit) as caught:
                main(['alpha', *args])
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(out.getvalue(), '')
            self.assertNotIn(SECRET, err.getvalue())
            self.assertEqual(json.loads(err.getvalue())['code'], 'alpha_arguments_invalid')


class OfflineProviderTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch('socket.socket', side_effect=AssertionError('network')))
        self.stack.enter_context(mock.patch.dict('os.environ', {'SCRUM87_TEST_KEY': SECRET}, clear=True))
        self.opener = self.stack.enter_context(mock.patch.object(provider, 'build_opener'))

    def response(self, value):
        self.opener.return_value.open.return_value = BytesIO(value)

    def test_valid_response_and_request_shape_without_network(self):
        self.response(json.dumps({'choices': [{'message': {'content': 'Synthetic advisory'}}]}).encode())
        self.assertEqual(provider.plan_task(compatible(), TASK), 'Synthetic advisory')
        request = self.opener.return_value.open.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(body['model'], 'synthetic-model')
        self.assertNotIn('tools', body)
        self.assertEqual(json.loads(body['messages'][1]['content']),
                         {'objective': TASK['objective'], 'resource': TASK['resource']})

    def test_missing_key_and_bad_config_never_build_transport(self):
        for cfg, code in ((compatible(key_env='SCRUM87_ABSENT'), 'provider_credential_missing'),
                          (compatible(kind=SECRET), 'provider_unsupported'),
                          (compatible(endpoint='http://provider.invalid'), 'provider_config_invalid')):
            with self.subTest(code=code), self.assertRaises(provider.ProviderError) as caught:
                provider.plan_task(cfg, TASK)
            self.assertEqual(caught.exception.code, code)
        self.opener.assert_not_called()

    def test_transport_errors_never_emit_private_detail_or_infer_auth_cause(self):
        self.opener.return_value.open.side_effect = OSError('401 token='+SECRET)
        with self.assertRaises(provider.ProviderError) as caught:
            provider.plan_task(compatible(), TASK)
        self.assertEqual(caught.exception.code, 'provider_request_failed')
        self.assertNotIn(SECRET, str(caught.exception))
        self.assertIn('unknown', str(caught.exception))

    def test_response_shapes_and_tool_calls_are_rejected(self):
        cases = [SECRET.encode(), b'x'*65537, b'{}', b'{"choices":[]}']
        for message in ({'content': SECRET, 'tool_calls': [{}]},
                        {'content': SECRET, 'function_call': {'name': SECRET}},
                        {'content': ''}, {'content': None}, {'content': 'x'*16385}):
            cases.append(json.dumps({'choices': [{'message': message}]}).encode())
        for raw in cases:
            with self.subTest(size=len(raw)):
                self.response(raw)
                with self.assertRaises(provider.ProviderError) as caught:
                    provider.plan_task(compatible(), TASK)
                self.assertEqual(caught.exception.code, 'provider_response_rejected')
                self.assertNotIn(SECRET, str(caught.exception))

    def test_redirect_and_unknown_provider_error_codes_are_fixed(self):
        with self.assertRaises(provider.ProviderError) as caught:
            provider._NoRedirect().redirect_request(None, None, None, None)
        self.assertEqual(caught.exception.code, 'provider_redirect_rejected')
        for code in (SECRET, ['secret'], 'human_approval_required'):
            exc = provider.ProviderError()
            exc.code = code
            result = provider.provider_diagnostic(exc)
            self.assertEqual(result['code'], 'provider_request_failed')
            self.assertNotIn(SECRET, json.dumps(result))

    def test_endpoint_rejects_controls_spaces_and_all_userinfo(self):
        for endpoint in ('\nhttps://provider.invalid', 'https://provider.invalid/\tfoo',
                         'https://provider.invalid/has space', 'https://@provider.invalid',
                         'https://:@provider.invalid', 'https://provider.invalid/?'+SECRET,
                         'https://provider.invalid/#'+SECRET, 'https://provider.invalid:bad'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                provider.validate_endpoint(endpoint)
        for endpoint in ('https://provider.invalid/v1', 'http://localhost/v1',
                         'http://127.0.0.1/v1', 'http://[::1]/v1'):
            provider.validate_endpoint(endpoint)


class ProviderFailureCompositionTests(unittest.TestCase):
    def test_provider_failure_cancels_before_tool_and_keeps_safe_category(self):
        for failure, code in ((provider.ProviderError('provider_credential_missing'), 'provider_credential_missing'),
                              (provider.ProviderError('provider_response_rejected'), 'provider_response_rejected'),
                              (RuntimeError(SECRET), 'provider_request_failed')):
            with self.subTest(code=code):
                cfg = dict(workspace='synthetic', store_id='store::test', project_id='project::test',
                           runtime_id='runtime::test', environment_id='environment::test',
                           max_concurrency=1, provider=compatible())
                graph = config.validate_work({'format_version': 1, 'tasks': [TASK]})
                task = state.TaskSnapshot(TASK['id'], graph.nodes[0].definition_reference, 'planned', 1, 'enrolled')
                store = mock.Mock()
                store.get_task.return_value = task
                store.register_run.return_value = replace(task, revision=2)
                with mock.patch.object(alpha, 'open_state', return_value=store), \
                        mock.patch.object(alpha, 'read_json', return_value={'format_version': 1, 'tasks': [TASK]}), \
                        mock.patch.object(alpha, 'AlphaExecution') as runtime, \
                        mock.patch.object(alpha, 'plan_task', side_effect=failure) as plan_task, \
                        mock.patch('socket.socket', side_effect=AssertionError('network')):
                    approval = alpha.make_plan(cfg, store)['approval']
                    result = alpha.execute(cfg, approval)
                self.assertEqual(result['status'], 'attention_required')
                row = result['results'][0]
                self.assertEqual(row['outcome'], 'provider_failed_before_tool')
                self.assertEqual(row['provider_diagnostic']['code'], code)
                self.assertNotIn(SECRET, json.dumps(result))
                store.transition.assert_called_once_with(TASK['id'], expected_revision=2,
                    operation='stop', reference='provider_failed_before_tool')
                store.start_run.assert_not_called()
                runtime.return_value.invoke.assert_not_called()
                runtime.return_value.close.assert_called_once()
                self.assertEqual(plan_task.call_count, 1)
