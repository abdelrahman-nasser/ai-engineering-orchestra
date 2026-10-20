"""Reproduce scoped offline checks and retain exact command/log receipts.

Run with installed Python 3.12 and -B. Outputs go to a fresh OS temp directory.
This never invokes full verify, network fixture tests or a release build.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(tempfile.mkdtemp(prefix='scrum87-verification-'))


def run(label, argv):
    started = time.time()
    result = subprocess.run(argv, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                            PYTHONIOENCODING='utf-8'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = OUT/(label+'.log')
    log.write_bytes(result.stdout)
    receipt = dict(label=label, argv=argv, cwd=str(ROOT), exit_code=result.returncode,
                   seconds=round(time.time()-started, 3), log=str(log),
                   output_sha256=hashlib.sha256(result.stdout).hexdigest())
    with (OUT/'commands.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(receipt)+'\n')
    print(json.dumps(receipt), flush=True)
    print(result.stdout.decode('utf-8', errors='replace')[-1500:], flush=True)
    return result.returncode


if __name__ == '__main__':
    mode = sys.argv[1]
    results = []
    print('EVIDENCE_DIRECTORY', OUT, flush=True)
    if mode == 'focused':
        results.append(run('focused-final', [sys.executable, '-B', '-m', 'unittest',
            'tests.test_alpha_diagnostics', 'tests.test_alpha_plan_preview', '-v']))
        results.append(run('pure-regressions', [sys.executable, '-B', '-m', 'unittest',
            'tests.test_task_scheduler.SchedulerTests', 'tests.test_task_run_state',
            'tests.test_agent_execution_journal',
            'tests.test_alpha_provider.ProviderTests.test_01_demo_is_labelled',
            'tests.test_alpha_provider.ProviderTests.test_06_missing_key_no_network',
            'tests.test_alpha_provider.ProviderTests.test_07_endpoint_policy', '-v']))
    elif mode == 'schemas':
        for name in ('task', 'workflow', 'role', 'project_manifest'):
            results.append(run(name+'-validator', [sys.executable, '-B', 'schemas/tests/validate_'+name+'.py']))
        results.append(run('current-task-schema', [sys.executable, '-B', '-c',
            "import json,yaml; from pathlib import Path; from jsonschema import Draft202012Validator; "
            "v=Draft202012Validator(json.loads(Path('schemas/task.schema.json').read_text())); "
            "errors=list(v.iter_errors(yaml.safe_load(Path('.ai/tasks/SCRUM-87-provider-diagnostics/task.yaml').read_text()))); "
            "print(errors); raise SystemExit(bool(errors))"]))
        results.append(run('structure', [sys.executable, '-B', '-m', 'itru', 'verify', '--structure']))
    elif mode == 'diff':
        results.append(run('diff-check', ['git', 'diff', '--check']))
        results.append(run('git-status', ['git', 'status', '--short']))
        results.append(run('head', ['git', 'rev-parse', 'HEAD']))
    elif mode == 'lint':
        results.append(run('markdown-scoped', ['C:/Program Files/nodejs/npx.cmd', '--offline', '--no-install',
            'markdownlint-cli2', 'docs/developer-alpha.md', 'docs/developer-alpha-first-run.md',
            'docs/developer-alpha-usability-roadmap.md', '.ai/tasks/SCRUM-87-provider-diagnostics/*.md']))
    elif mode == 'lint-cache':
        results.append(run('markdown-scoped-cached', ['C:/Program Files/nodejs/node.exe',
            'C:/Users/Abdelrahman/AppData/Local/npm-cache/_npx/3158f213c58abe1a/node_modules/markdownlint-cli2/markdownlint-cli2-bin.mjs',
            'docs/developer-alpha.md', 'docs/developer-alpha-first-run.md',
            'docs/developer-alpha-usability-roadmap.md', '.ai/tasks/SCRUM-87-provider-diagnostics/*.md']))
    else:
        raise SystemExit('expected focused, schemas, diff, lint or lint-cache')
    raise SystemExit(int(any(results)))
