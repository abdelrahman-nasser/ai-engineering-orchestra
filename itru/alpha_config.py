"""Closed local Alpha inputs. No credentials, catalog discovery or authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from itru._native_repository_file_read import _resource_components, _NativeFailure
from itru.sqlite_task_run_state import _plain, _security
from itru.task_dependency import TaskNode, TaskDependency, build_task_graph

CONFIG_KEYS = {'format_version', 'workspace', 'project_id', 'runtime_id',
    'environment_id', 'domain_id', 'ledger_id', 'journal_id', 'store_id',
    'max_concurrency', 'provider'}
PROVIDER_KEYS = {'kind', 'endpoint', 'model', 'key_env', 'timeout_seconds'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def text(value):
    if type(value) is not str or not value.strip() or len(value) > 4096 or any(ord(c) < 32 for c in value):
        raise ValueError('nonempty bounded text required')
    return value


def closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('unknown or missing input fields')


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


def read_json(path):
    path = Path(path).absolute()
    for parent in path.parents:
        _plain(parent, directory=True)
    _plain(path, directory=False)
    with path.open('rb') as stream:
        data = stream.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError('input exceeds 1 MiB')
    return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def load_config(path):
    path = Path(path).absolute()
    cfg = read_json(path)
    closed(cfg, CONFIG_KEYS)
    if type(cfg['format_version']) is not int or cfg['format_version'] != 1:
        raise ValueError('unsupported Alpha config version')
    for key in CONFIG_KEYS - {'format_version', 'max_concurrency', 'provider'}:
        text(cfg[key])
    if Path(cfg['workspace']) != path.parent or path.name != 'alpha.json':
        raise ValueError('config must be workspace/alpha.json with exact workspace identity')
    if type(cfg['max_concurrency']) is not int or cfg['max_concurrency'] not in (1, 2):
        raise ValueError('Alpha supports one or two agent workers')
    p = cfg['provider']
    closed(p, PROVIDER_KEYS)
    if p['kind'] not in ('demo', 'compatible'):
        raise ValueError('unsupported provider adapter')
    text(p['model'])
    if type(p['endpoint']) is not str or type(p['key_env']) is not str:
        raise ValueError('endpoint/key_env must be strings')
    if p['key_env'] and not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', p['key_env']):
        raise ValueError('key_env must name an environment variable')
    if type(p['timeout_seconds']) is not int or not 1 <= p['timeout_seconds'] <= 120:
        raise ValueError('provider timeout must be 1..120 seconds')
    if p['kind'] == 'compatible':
        from itru.alpha_provider import validate_endpoint
        validate_endpoint(p['endpoint'])
    _security(path.parent, directory=True)
    _security(path, directory=False)
    return cfg


def validate_work(work):
    closed(work, {'format_version', 'tasks'})
    if type(work['format_version']) is not int or work['format_version'] != 1:
        raise ValueError('unsupported work version')
    if type(work['tasks']) is not list or not 1 <= len(work['tasks']) <= 100:
        raise ValueError('work requires 1..100 explicit Tasks')
    nodes, edges = [], []
    for task in work['tasks']:
        closed(task, {'id', 'objective', 'resource', 'dependencies'})
        for key in ('id', 'objective', 'resource'):
            text(task[key])
        try:
            _resource_components(task['resource'])
        except _NativeFailure:
            raise ValueError('unsupported lexical repository resource') from None
        if type(task['dependencies']) is not list:
            raise ValueError('dependencies must be a list')
        for key in task['dependencies']:
            text(key)
        nodes.append(TaskNode(task['id'], 'sha256::' + digest(task)))
        edges.extend(TaskDependency(task['id'], key) for key in task['dependencies'])
    graph = build_task_graph(tuple(nodes), tuple(edges))
    return graph


def write_private(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(canonical(value) + '\n')
    _security(path, directory=False, establish=True)
