"""Bounded Phase 1 evidence: static receipt inventory and explicit help-only tests.

No test discovery, operational stores, network, installation or native probes.
Run with installed Python 3.12 and -B. Outputs are retained under evidence/.
"""
from __future__ import annotations

import ast
import collections
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parent
EVIDENCE = TASK/'evidence'
SELECTED = 'tests.test_cli.TestActiveProjectIntegration.test_help_is_available_without_project_and_uses_wrapper_name'
REGRESSIONS = ['tests.test_cli.TestRootHelp', 'tests.test_cli.TestTasksHelp',
    'tests.test_cli.TestInspectHelp', 'tests.test_cli.TestVerifyHelp',
    'tests.test_cli.TestUnknownCommand']
BASE = 'e46aafd9790ced28a9ef6c1688c94bccdc4062b0'
BEFORE_TEST_SHA256 = '8e6f1cde9a5dae08cde9eb6c8a1da8eb75ce062f7b8fc4a89e5e603b7a0b8c84'
RUNTIME_SHA256 = '9ec6b857e4b6be267d23e349b700d8191e74a1a241f2225df26363bbb369db5e'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decoded(path):
    raw = path.read_bytes()
    return raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8-sig').replace('\r\n', '\n')


def save(name, value):
    (TASK/name).write_text(json.dumps(value, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')


def inventory():
    """Parse preserved text/AST only; never import collected test modules."""
    retained = ROOT/'.tmp/p0-final-verification/retained-failures.json'
    unit_log = ROOT/'.tmp/usability-p0-unit-tests.log'
    markdown_log = ROOT/'.tmp/usability-p0-markdown-lint.log'
    records = json.loads(retained.read_text(encoding='utf-8'))
    assert len(records) == 299
    categories = {
        'native-access': {'root_cause': 'Prior WinError 5 ancestor query-handle failure before native execution; predecessor assertions wrap the same prerequisite.', 'environment': 'Supported current-user Windows native access and security/authority prerequisites.', 'risk': 'high; security/native prerequisites', 'phase1': 'NOT RUN; no remediation authorized'},
        'journal-checkout-bytes': {'root_cause': 'Prior checkout CRLF bytes differ from canonical LF migration checksum; current/canonical/checkout-matched comparisons are retained.', 'environment': 'Exact SQL bytes, checkout conversion and supported storage setup.', 'risk': 'medium/high; integrity-sensitive resource boundary', 'phase1': 'NOT RUN; production/resource changes require separate approval'},
        'hostile-fixture': {'root_cause': 'Missing fixed external hostile fixture and authenticated owned-fixture prerequisites.', 'environment': 'Separately authorized hostile fixture, aliases, security profile and volume evidence.', 'risk': 'high; hazardous/security fixture', 'phase1': 'NOT RUN; do not fabricate or provision'},
        'retired-import': {'root_cause': 'Experiment imports retired engineering_orchestration namespace during discovery.', 'environment': 'Historical experiment/cutover disposition; not a missing package to install.', 'risk': 'medium; historical identity/experiment support', 'phase1': 'NOT RUN; separate category'},
        'containment-launch': {'root_cause': 'Prior broad launch omitted -I; containment guard required -I -B and exercised zero cases.', 'environment': 'Locked interpreter, isolation, native/privileged hostile prerequisites.', 'risk': 'high; containment/security probe', 'phase1': 'NOT RUN; no launch/probe authorized'},
        'migration-expectation': {'root_cause': 'Prior assertions expect schema/migrations v3 while approved implementation includes migration4/execution entry; includes historical O55 wrapper.', 'environment': 'SQLite schema and compatibility fixtures; some wrappers include native prerequisites.', 'risk': 'medium/high; security-adjacent schema/integrity checks', 'phase1': 'NOT RUN; no assertion changes'},
        'package-expectation': {'root_cause': 'Prior package lists omit approved Journal resources; other latent resource/schema expectations and C111 external wheel/setup prerequisites remain.', 'environment': 'Static metadata for one test; C111 additionally needs owned setup and authenticated external package evidence.', 'risk': 'low for static metadata; higher for C111 fixture/package boundary', 'phase1': 'NOT RUN; separate packaging category'},
        'cli-help-expectation': {'root_cause': 'Root-help literal predates approved alpha command; approved parser/documentation include alpha.', 'environment': 'CPython3.12, installed existing project dependencies, benign synthetic temp project only.', 'risk': 'low; nonsecurity help presentation', 'phase1': 'SELECTED for exact before/after help-only reproduction'},
        'namespace-manifest': {'root_cause': 'Prior explicit living-file namespace guard reports nine legacy occurrences in existing schemas/tests.', 'environment': 'Exact living-file inventory, historical allowances and identity contracts.', 'risk': 'medium; do not broaden namespace allowances to silence findings', 'phase1': 'NOT RUN; separate category'},
    }
    group_map = {'native-access (including assertion wrappers)': 'native-access',
        'Journal checksum/fixture initialization': 'journal-checkout-bytes',
        'missing external hostile fixture': 'hostile-fixture',
        'legacy Python import/discovery': 'retired-import',
        'containment matrix launch prerequisite': 'containment-launch'}
    events, source_classes = [], {}
    for index, record in enumerate(records, 1):
        match = re.search(r'\(([^()]*)\)', record['header'])
        raw_id = re.sub(r'\s+', '', match.group(1))
        test_id = 'tests.'+raw_id if raw_id.startswith('test_') else raw_id
        group = group_map.get(record['group'])
        if group is None:
            if '.test_C111_' in test_id or '.test_explicit_resource_allowlist' in test_id:
                group = 'package-expectation'
            elif '.test_help_is_available_without_project_and_uses_wrapper_name' in test_id:
                group = 'cli-help-expectation'
            elif '.test_full_explicit_living_manifest' in test_id:
                group = 'namespace-manifest'
            else:
                group = 'migration-expectation'
        source_check = 'discovery placeholder for failed module import'
        if raw_id.startswith('test_'):
            module, class_name, method = raw_id.split('.', 2)
            module_path = ROOT/'tests'/(module+'.py')
            if module not in source_classes:
                tree = ast.parse(module_path.read_text(encoding='utf-8'))
                source_classes[module] = {node.name: {item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))}
                    for node in tree.body if isinstance(node, ast.ClassDef)}
            assert class_name in source_classes[module], test_id
            source_check = ('AST class/method verified' if method in source_classes[module][class_name]
                else 'AST class verified; method generated by existing test-support source')
        events.append({'occurrence': index, 'test_id': test_id,
            'historical_result': record['header'].split(':', 1)[0],
            'category': group, 'subtest_suffix': record['header'][match.end():].strip(),
            'original_header': record['header'], 'identifier_source_check': source_check,
            'selected': test_id == SELECTED})
    summary = collections.Counter(event['historical_result'] for event in events)
    assert summary == {'ERROR': 275, 'FAIL': 24}, summary
    progress = decoded(unit_log).split('\n======================================================================', 1)[0]
    starts = [match.start() for match in re.finditer(r'^test_', progress, re.M)]+[len(progress)]
    skips = []
    for start, end in zip(starts, starts[1:]):
        block = progress[start:end]
        if '... skipped' not in block:
            continue
        match = re.search(r'\(([^()]*)\)', block)
        test_id = 'tests.'+re.sub(r'\s+', '', match.group(1))
        reason = ' '.join(block.split('... skipped', 1)[1].split())
        skips.append({'test_id': test_id, 'historical_result': 'SKIPPED', 'original_reason': reason,
            'root_cause': 'POSIX signal evidence unavailable on Windows' if 'POSIX' in reason else 'Windows symlink privilege unavailable (WinError1314)',
            'environment': 'POSIX host' if 'POSIX' in reason else 'Separately authorized Windows symlink/native security prerequisites',
            'risk': 'platform/native prerequisite; not authorized in Phase1', 'phase1': 'NOT RUN'})
    assert len(skips) == 5
    lint = decoded(markdown_log)
    matches = list(re.finditer(r'^(?:node\.exe : )?(.+?\.md):(\d+)(?::(\d+))?\s+error\b', lint, re.M))
    findings = []
    for index, match in enumerate(matches):
        block = lint[match.end():matches[index+1].start() if index+1 < len(matches) else len(lint)]
        rule = 'MD'+re.search(r'MD\s*(\d{3})', block).group(1)
        findings.append({'path': match.group(1), 'line': int(match.group(2)),
            'column': int(match.group(3)) if match.group(3) else None,
            'rule': rule, 'historical_result': 'FAILED', 'phase1': 'NOT RUN; unchanged'})
    assert len(findings) == 132 and len({f['path'] for f in findings}) == 17
    for group, data in categories.items():
        data['historical_events'] = dict(collections.Counter(e['historical_result'] for e in events if e['category'] == group))
    save('failure-inventory.json', {'schema': 'Phase1 report data, not a Core contract',
        'historical_summary': {'tests': 2103, 'failures': 24, 'errors': 275, 'skips': 5,
            'markdown_findings': 132, 'markdown_files': 17, 'full_C109_phase_validation': 'NOT RUN'},
        'sources': {str(p.relative_to(ROOT)).replace('\\', '/'): {'sha256': sha(p)} for p in (retained, unit_log, markdown_log)},
        'identifier_policy': 'Whitespace unwrapped only inside dotted test IDs; original headers/subtest suffixes and occurrence indices retained. No module imported or collected.',
        'categories': categories, 'failure_error_events': events, 'skip_events': skips,
        'markdown_findings': findings,
        'counting_limit': 'Events include subtests and predecessor wrappers, not unique root defects; historical counts are never rewritten by focused outcomes.'})
    print('Inventory retained:299failure/error events,5skipIDs,132Markdown findings in17files. No tests imported or executed.')


def run_tests(mode):
    assert mode in ('before', 'after')
    if sha(ROOT/'itru/cli.py') != RUNTIME_SHA256:
        raise SystemExit('runtime source differs from the approved Phase 1 baseline; inspect before testing')
    if mode == 'before' and sha(ROOT/'tests/test_cli.py') != BEFORE_TEST_SHA256:
        raise SystemExit('before requires the recorded untouched baseline test source; no source is restored automatically')
    names = [SELECTED] if mode == 'before' else [SELECTED, *REGRESSIONS]
    bootstrap = f'''import sys, unittest
from pathlib import Path
from unittest import mock
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, {str(ROOT)!r})
import itru
assert Path(itru.__file__).resolve().is_relative_to(Path({str(ROOT)!r}).resolve())
print('IMPORT_ROOT', itru.__file__, 'isolated', sys.flags.isolated, 'bytecode_disabled', sys.flags.dont_write_bytecode)
with mock.patch('socket.socket', side_effect=AssertionError('network forbidden')), mock.patch('socket.create_connection', side_effect=AssertionError('network forbidden')), mock.patch('subprocess.Popen', side_effect=AssertionError('test child process forbidden')):
    suite = unittest.defaultTestLoader.loadTestsFromNames({names!r})
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
'''
    argv = [sys.executable, '-I', '-B', '-c', bootstrap]
    started = time.time()
    proc = subprocess.run(argv, cwd=ROOT, env=dict(os.environ,
        PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8'),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    filename = mode+'-'+str(time.time_ns())+'.txt'
    (EVIDENCE/filename).write_bytes(proc.stdout)
    receipt = {'phase': mode, 'argv': argv, 'cwd': str(ROOT), 'test_names': names,
        'exit_code': proc.returncode, 'seconds': round(time.time()-started, 3),
        'output': filename, 'output_sha256': hashlib.sha256(proc.stdout).hexdigest(),
        'test_source_sha256': sha(ROOT/'tests/test_cli.py'),
        'runtime_source_sha256': sha(ROOT/'itru/cli.py')}
    with (EVIDENCE/'commands.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt)+'\n')
    print(json.dumps(receipt, indent=2), flush=True)
    print(proc.stdout.decode('utf-8', errors='replace'), flush=True)
    return proc.returncode


def checks():
    """Validate only current Task metadata, retained receipts and the narrow diff."""
    import yaml
    from jsonschema import Draft202012Validator
    cfg = yaml.safe_load((TASK/'task.yaml').read_text(encoding='utf-8'))
    validator = Draft202012Validator(json.loads((ROOT/'schemas/task.schema.json').read_text()))
    assert not list(validator.iter_errors(cfg))
    assert cfg['id'] == 'ITRU-065' and cfg['status'] == 'in_progress'
    assert re.fullmatch(r'ITRU-[0-9]{3,}', cfg['id']) and TASK.name.startswith(cfg['id']+'-')
    workflow = yaml.safe_load((ROOT/'workflows'/(cfg['workflow']+'.yaml')).read_text())
    assert workflow['id'] == 'standard-change' and cfg['type'] in workflow['applicable_task_types']
    roles = {yaml.safe_load(path.read_text())['id'] for path in (ROOT/'roles').glob('*.yaml')}
    for stage in workflow['stages']:
        assert set(stage.get('required_roles', [])) <= roles
    assert cfg['quality_gates'] == ['documentation_consistency', 'independent_review']
    for gate in cfg['quality_gates']:
        assert (ROOT/'quality-gates'/(gate.replace('_', '-')+'.md')).is_file()
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()
    assert git('rev-parse', 'HEAD') == BASE
    assert git('branch', '--show-current') == 'feature/core-verification-debt-phase1'
    assert not git('diff', '--cached', '--name-only')
    assert git('diff', '--name-only').splitlines() == ['tests/test_cli.py']
    prefix = str(TASK.relative_to(ROOT)).replace('\\', '/')+'/'
    assert all(path.startswith(prefix) for path in git('ls-files', '--others', '--exclude-standard').splitlines())
    assert sha(ROOT/'itru/cli.py') == RUNTIME_SHA256
    data = json.loads((TASK/'failure-inventory.json').read_text())
    assert len(data['failure_error_events']) == 299 and len(data['skip_events']) == 5
    assert len(data['markdown_findings']) == 132
    assert collections.Counter(e['historical_result'] for e in data['failure_error_events']) == {'FAIL':24, 'ERROR':275}
    assert sum(e['selected'] for e in data['failure_error_events']) == 1
    for path, source in data['sources'].items():
        assert sha(ROOT/path) == source['sha256']
    commands = [json.loads(line) for line in (EVIDENCE/'commands.jsonl').read_text().splitlines()]
    assert [r['exit_code'] for r in commands] == [1,1,0]
    for receipt in commands:
        assert sha(EVIDENCE/receipt['output']) == receipt['output_sha256']
        assert receipt['runtime_source_sha256'] == RUNTIME_SHA256
    assert commands[-1]['test_source_sha256'] == sha(ROOT/'tests/test_cli.py')
    source = (ROOT/'tests/test_cli.py').read_text()
    tree = ast.parse(source)
    test = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'TestActiveProjectIntegration')
    method = next(n for n in test.body if isinstance(n, ast.FunctionDef) and n.name == SELECTED.rsplit('.',1)[1])
    method_source = ast.get_source_segment(source, method)
    for required in ('{tasks,inspect,verify,alpha}', 'itru.cli.find_project_root', 'rook.py',
                     'raised.exception.code, 0', 'self.assertIn(expected, out.getvalue())'):
        assert required in method_source
    patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}', r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
        r'\bgh[pousr]_[A-Za-z0-9]{30,}', r'Bearer [A-Za-z0-9_.-]{20,}']
    references = 0
    for path in TASK.glob('*.md'):
        value = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', value):
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
                continue
            target = target.split('#',1)[0]
            if target:
                assert (path.parent/target).resolve().exists(), target
                references += 1
    files = [path for path in TASK.rglob('*') if path.is_file() and path.name != 'governance-checks.json']
    for path in [*files, ROOT/'tests/test_cli.py']:
        value = path.read_bytes().decode('utf-8', errors='replace')
        assert not any(re.search(pattern, value) for pattern in patterns), 'Sensitive-data pattern in '+path.name
        if path.suffix != '.txt':  # Preserve original captured output bytes verbatim.
            assert value.endswith('\n'), 'Missing final newline: '+path.name
            assert all(line == line.rstrip(' \t') for line in value.splitlines()), 'Trailing whitespace: '+path.name
    whitespace = subprocess.run(['git','diff','--check'], cwd=ROOT, capture_output=True)
    assert whitespace.returncode == 0
    record = {'result':'PASS', 'checks':['current Task schema', 'canonical ITRU identity',
        'Workflow/Role/Gate references', 'HEAD/branch/index and exact test-only scope',
        'historical inventory/log hashes and child exits preserved', 'unchanged runtime',
        'explicit original assertions retained', 'local Markdown references', 'sensitive-data pattern scan',
        'scoped non-receipt text whitespace', 'git diff --check'],
        'local_markdown_references':references, 'markdown_lint':'NOT RUN in Phase1; documentation consistency assessed manually and independently',
        'command':[sys.executable, '-B', str(Path(__file__).resolve()), 'checks'],
        'cwd':str(ROOT), 'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'candidate_paths':sorted([prefix+'evidence/governance-checks.json',
            *[str(path.relative_to(ROOT)).replace('\\','/') for path in files], 'tests/test_cli.py']),
        'inputs_sha256':{str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in [*files, ROOT/'tests/test_cli.py']}}
    output = EVIDENCE/'governance-checks.json'
    previous = json.loads(output.read_text())['runs'] if output.exists() else []
    output.write_text(json.dumps({'runs':[*previous,record]},indent=2)+'\n',encoding='utf-8')
    print('PASS: current Task schema/identity/references, scope, preserved receipts, assertions, sensitive-data and whitespace checks. No tests executed.')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    EVIDENCE.mkdir(exist_ok=True)
    if sys.argv[1] == 'inventory':
        inventory()
    elif sys.argv[1] in ('before', 'after'):
        raise SystemExit(run_tests(sys.argv[1]))
    elif sys.argv[1] == 'checks':
        checks()
    elif sys.argv[1] == 'environment':
        import importlib.metadata
        save('evidence/environment.json', {'python': sys.executable, 'version': sys.version,
            'platform': platform.platform(), 'workspace': str(ROOT), 'baseline_head': BASE,
            'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
            'packages': {name: importlib.metadata.version(name) for name in ('PyYAML', 'jsonschema', 'referencing')},
            'network_or_installs': 'none in tests or diagnostics'})
        print('Environment receipt retained without private environment-variable values.')
    else:
        raise SystemExit('expected inventory, environment, before, after or checks')
