"""Offline clean-install and installed CLI smoke. No operational registry access.

All CLI children execute outside checkout with isolated Python. The sole native
registry-location override is process-local and points at our owned temp root.
Fault switches exist only in this validation script, never in the product CLI.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import venv
import zipfile

from build_developer_alpha import ROOT, manifest, sha

BOOTSTRAP = r'''
import sys
from pathlib import Path
from unittest import mock
from contextlib import ExitStack
from itru import windows_local_authorization_domain_owner as w
from itru.sqlite_task_run_state import _security, SqliteTaskRunStateStore
from itru import _native_repository_file_read as n
from itru.cli import main
registry=Path(sys.argv[1]); fault=sys.argv[2]
if not registry.exists():
 registry.mkdir(); _security(registry,directory=True,establish=True)
with ExitStack() as stack:
 stack.enter_context(mock.patch.object(w,'_local_appdata_path',return_value=registry))
 if fault=='ambiguous':
  stack.enter_context(mock.patch.object(n._Native,'read_data',side_effect=n._NativeFailure('read_failure')))
 elif fault=='lost-state':
  stack.enter_context(mock.patch.object(SqliteTaskRunStateStore,'record_result',side_effect=OSError('synthetic observation loss')))
 raise SystemExit(main(sys.argv[3:]))
'''


def cleanup(temporary):
    root = Path(temporary.name)
    if (root.resolve() != root or root.parent != Path(tempfile.gettempdir()).resolve()
            or not root.name.startswith('itru-064-release-')):
        raise AssertionError('release cleanup containment failure')
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            path = Path(parent)/name
            info = path.lstat()
            if (not path.resolve().is_relative_to(root) or path.is_symlink()
                    or getattr(info, 'st_file_attributes', 0) & 0x400
                    or stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
                raise AssertionError('foreign release fixture object')
    temporary.cleanup()
    if root.exists():
        raise AssertionError('release fixture residue')
    print('ITRU064_RELEASE_CLEAN ' + str(root), flush=True)


def validate(release):
    if release != ROOT/'.tmp'/'itru-064-release' or release.resolve() != release:
        raise ValueError('exact locked release directory required')
    receipts = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        receipts.append(name)
        print('SMOKE_PASS ' + name, flush=True)
    receipt = json.loads((release/'build-receipt.json').read_text())
    check('current-product-fingerprints', receipt['product_sha256'] == manifest())
    bundle = release/receipt['bundle']
    check('bundle-sha256', sha(bundle) == receipt['bundle_sha256'])
    with zipfile.ZipFile(bundle) as archive:
        hashes = json.loads(archive.read('SHA256SUMS.json'))
        check('bundle-exact-inventory', set(archive.namelist()) == set(hashes) | {'SHA256SUMS.json'})
        check('bundle-all-payload-hashes', all(hashlib.sha256(archive.read(name)).hexdigest() == value
                                             for name, value in hashes.items()))
    wheel = release/receipt['wheel']
    check('wheel-sha256', sha(wheel) == receipt['wheel_sha256'])
    with zipfile.ZipFile(wheel) as archive:
        check('both-migration-resource-packages', all(name in archive.namelist() for name in (
            'itru/_sqlite_journal_migrations/0001_initial.sql',
            'itru/_sqlite_admission_migrations/0004_execution_entry.sql')))
        record = next(name for name in archive.namelist() if name.endswith('.dist-info/RECORD'))
        valid = True
        for name, encoded, size in csv.reader(io.StringIO(archive.read(record).decode())):
            if not encoded:
                valid &= name == record
                continue
            data = archive.read(name)
            valid &= encoded == 'sha256=' + base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode()
            valid &= len(data) == int(size)
        check('wheel-RECORD-integrity', valid)
    temporary = tempfile.TemporaryDirectory(prefix='itru-064-release-', dir=Path(tempfile.gettempdir()).resolve())
    root = Path(temporary.name).resolve()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PIP_NO_CACHE_DIR='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
    env.pop('PYTHONPATH', None)
    clean_env = release/('clean-env-' + root.name.rsplit('-', 1)[-1])
    server = None
    try:
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(clean_env)
        python = clean_env/'Scripts'/'python.exe'
        install = subprocess.run([str(python), '-I', '-m', 'pip', 'install', '--no-index', '--no-deps',
            '--find-links', str(release/'wheelhouse'), '--require-hashes', '-r', str(release/'requirements.lock')],
            cwd=root, env=env, text=True, capture_output=True, timeout=120)
        (release/'clean-install.log').write_text(install.stdout + install.stderr, encoding='utf-8')
        check('clean-offline-hashed-install', install.returncode == 0)
        console = clean_env/'Scripts'/'itru.exe'
        version = subprocess.run([str(console), '--version'], cwd=root, env=env, text=True, capture_output=True, timeout=30)
        check('installed-console-version', version.returncode == 0 and version.stdout.strip() == 'itru 0.1.0a1')
        help_result = subprocess.run([str(console), 'alpha', '--help'], cwd=root, env=env, text=True, capture_output=True, timeout=30)
        check('installed-console-help', help_result.returncode == 0 and 'resume' in help_result.stdout)
        location = subprocess.check_output([str(python), '-I', '-c', 'import itru; print(itru.__file__)'], cwd=root, env=env, text=True)
        check('installed-package-outside-checkout', Path(location.strip()).is_relative_to(clean_env))
        logs = []
        def cli(*args, expect=0, fault='none'):
            result = subprocess.run([str(python), '-I', '-B', '-c', BOOTSTRAP,
                str(root/'appdata'), fault, 'alpha', *map(str, args)],
                cwd=root, env=env, text=True, capture_output=True, timeout=45)
            logs.append(dict(args=list(map(str, args)), returncode=result.returncode,
                             stdout=result.stdout, stderr=result.stderr))
            (release/'installed-cli-receipts.json').write_text(json.dumps(logs, indent=2), encoding='utf-8')
            if result.returncode != expect:
                raise AssertionError('installed CLI failed: ' + json.dumps(logs[-1]))
            return json.loads(result.stdout if expect in (0, 1) else result.stderr)
        ws = root/'workspace'
        initialized = cli('init', ws)
        cfg = Path(initialized['config'])
        p = json.loads(cfg.read_text())
        active, peak, calls = 0, 0, []
        mutex, barrier = threading.Lock(), threading.Barrier(2)
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                nonlocal active, peak
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                with mutex:
                    active += 1
                    peak = max(peak, active)
                    calls.append(body)
                    first_batch = len(calls) <= 2
                try:
                    if first_batch:
                        barrier.wait(timeout=15)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({'choices': [{'message': {'content': 'Fixture model advisory plan.'}}]}).encode())
                finally:
                    with mutex:
                        active -= 1
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        p['provider'] = dict(kind='compatible', endpoint=f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                             model='local-fixture-model', key_env='', timeout_seconds=30)
        cfg.write_text(json.dumps(p), encoding='utf-8')
        loaded = cli('load', '--config', cfg, '--work', ws/'example-work.json')
        check('configuration-and-explicit-work-load', len(loaded['tasks']) == 3)
        plan = cli('plan', '--config', cfg)
        check('dag-initial-selection', plan['selected'] == ['read-a', 'read-b'])
        check('human-approval-stop', cli('run', '--config', cfg, expect=2)['status'] == 'rejected')
        output = cli('run', '--config', cfg, '--approve', plan['approval'])
        check('controlled-original-results', [r['outcome'] for r in output['results']] == ['succeeded'] * 2)
        check('byo-adapter-and-two-agent-concurrency', peak == 2 and len(calls) == 2
              and all(c['model'] == 'local-fixture-model' and 'tools' not in c for c in calls))
        before = cli('history', '--config', cfg)
        again = cli('history', '--config', cfg)
        check('journal-task-run-process-restart', before == again and len(before['journal']) == 4
              and all(t['state'] != 'completed' for t in before['tasks']))
        check('stale-approval-rejected', cli('run', '--config', cfg, '--approve', plan['approval'], expect=2)['status'] == 'rejected')
        resume = cli('plan', '--config', cfg, '--action', 'resume', '--task', 'read-a')
        resumed = cli('resume', '--config', cfg, '--task', 'read-a', '--approve', resume['approval'])
        check('governed-fresh-run-resume', resumed['results'][0]['run_id'] != output['results'][0]['run_id']
              and resumed['results'][0]['outcome'] == 'succeeded')
        for task in ('read-a', 'read-b'):
            closure = cli('plan', '--config', cfg, '--action', 'complete', '--task', task, '--reference', 'synthetic-governance-closure')
            cli('complete', '--config', cfg, '--task', task, '--reference', 'synthetic-governance-closure', '--approve', closure['approval'])
        ready = cli('plan', '--config', cfg)
        check('dag-after-human-governance', ready['selected'] == ['read-c'])
        cli('run', '--config', cfg, '--approve', ready['approval'])
        # Independent fresh workspaces for each conservative failure boundary.
        for label, resource, fault, expected in (
            ('before', 'missing.txt', 'none', 'failed_before_effect'),
            ('ambiguous', 'input.txt', 'ambiguous', 'effect_ambiguous'),
            ('lost', 'input.txt', 'lost-state', 'interrupted')):
            other = root/label
            initialized = cli('init', other)
            other_cfg = Path(initialized['config'])
            work = {'format_version': 1, 'tasks': [{'id': label, 'objective': 'Synthetic boundary probe',
                                                  'resource': resource, 'dependencies': []}]}
            supplied = root/(label + '.json')
            supplied.write_text(json.dumps(work), encoding='utf-8')
            cli('load', '--config', other_cfg, '--work', supplied)
            planned = cli('plan', '--config', other_cfg)
            result = cli('run', '--config', other_cfg, '--approve', planned['approval'],
                         expect=2 if label == 'lost' else 1, fault=fault)
            history = cli('history', '--config', other_cfg)
            check(label + '-original-or-conservative-state', history['tasks'][0]['runs'][0]['state'] == expected)
            if label != 'before':
                check(label + '-resume-refused', cli('plan', '--config', other_cfg, '--action', 'resume', '--task', label, expect=2)['status'] == 'rejected')
            if label == 'lost':
                check('journal-success-never-repairs-lifecycle', history['journal'][1]['result_summary']['outcome'] == 'succeeded')
        with zipfile.ZipFile(bundle) as archive:
            example = json.loads(archive.read('examples/developer-alpha/work.json'))
        check('bundled-example-reproduces-init', example == json.loads((ws/'example-work.json').read_text()))
        result = dict(status='PASS', checks=len(receipts), passed=receipts, clean_install='PASS',
                      alpha_smoke='PASS', two_agent_concurrency='PASS',
                      build_bundle_sha256=receipt['bundle_sha256'], product_sha256=manifest())
        (release/'validation-receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print(json.dumps(result, sort_keys=True))
    finally:
        if server is not None:
            server.shutdown(); server.server_close(); worker.join(5)
        cleanup(temporary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', required=True, type=Path)
    validate(parser.parse_args().release.absolute())
