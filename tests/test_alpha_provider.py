"""Owned loopback HTTP protocol fixtures; no external Provider or credentials."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
from unittest import mock

from itru.alpha_provider import ProviderError, plan_task, validate_endpoint

TASK = {'id': 'one', 'objective': 'Read synthetic input', 'resource': 'input.txt', 'dependencies': []}


class ProviderTests(unittest.TestCase):
    def server(self, response, status=200):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(status)
                if status == 302:
                    self.send_header('Location', 'http://127.0.0.1:1/never')
                self.end_headers()
                self.wfile.write(response)
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), worker.join(5)))
        return dict(kind='compatible', endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                    model='fixture-model', key_env='', timeout_seconds=5), calls

    def test_01_demo_is_labelled(self):
        self.assertIn('no model inference', plan_task({'kind': 'demo'}, TASK))

    def test_02_byo_wire_smoke(self):
        cfg, calls = self.server(json.dumps({'choices': [{'message': {'content': 'Inspect the approved file.'}}]}).encode())
        self.assertEqual(plan_task(cfg, TASK), 'Inspect the approved file.')
        self.assertEqual(calls[0]['model'], 'fixture-model')
        self.assertNotIn('tools', calls[0])
        self.assertNotIn('api_key', str(calls))

    def test_03_reject_tool_calls(self):
        cfg, _ = self.server(json.dumps({'choices': [{'message': {'content': 'x', 'tool_calls': [{}]}}]}).encode())
        with self.assertRaises(ProviderError):
            plan_task(cfg, TASK)

    def test_04_reject_redirect(self):
        cfg, calls = self.server(b'', 302)
        with self.assertRaises(ProviderError):
            plan_task(cfg, TASK)
        self.assertEqual(len(calls), 1)

    def test_05_response_bound(self):
        cfg, _ = self.server(b'x' * 65537)
        with self.assertRaises(ProviderError):
            plan_task(cfg, TASK)

    def test_06_missing_key_no_network(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ProviderError):
                plan_task(dict(kind='compatible', endpoint='http://127.0.0.1:1/', model='fixture',
                    key_env='ITRU064_SYNTHETIC_MISSING', timeout_seconds=1), TASK)

    def test_07_endpoint_policy(self):
        for value in ('http://example.com/', 'file:///input.txt', 'https://user:secret@example.com/',
                      'https://example.com/?secret=x', 'https://example.com/#secret'):
            with self.subTest(endpoint=value), self.assertRaises(ValueError):
                validate_endpoint(value)

    def test_08_malformed_response_sanitized(self):
        cfg, _ = self.server(b'fixture private diagnostic')
        with self.assertRaises(ProviderError) as caught:
            plan_task(cfg, TASK)
        self.assertNotIn('private', str(caught.exception))
