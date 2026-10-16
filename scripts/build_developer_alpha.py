"""Build the locked Alpha wheel twice, then an offline, hash-pinned bundle.

Only explicit Python/schema/Role/SQL package payload is copied to isolated build
staging. No Task/Workflow catalogs or Markdown traversal. No sdist/publication.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = (
    'pyproject.toml', 'itru/__init__.py', 'itru/__main__.py', 'itru/cli.py',
    'itru/alpha_config.py', 'itru/alpha_provider.py', 'itru/alpha_authority.py',
    'itru/developer_alpha.py', 'tests/test_developer_alpha.py', 'tests/test_alpha_provider.py',
    'scripts/build_developer_alpha.py', 'scripts/validate_developer_alpha.py',
    'docs/developer-alpha.md', 'examples/developer-alpha/work.json', 'examples/developer-alpha/input.txt',
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    return {name: sha(ROOT/name) for name in PRODUCTS}


def run(args, **kwargs):
    print('BUILD_COMMAND ' + ' '.join(str(a) for a in args), flush=True)
    env = dict(kwargs.pop('env', os.environ), PIP_NO_CACHE_DIR='1', PIP_DISABLE_PIP_VERSION_CHECK='1')
    subprocess.run([str(a) for a in args], check=True, env=env, **kwargs)


def stage(destination):
    destination.mkdir()
    shutil.copyfile(ROOT/'pyproject.toml', destination/'pyproject.toml')
    # Opaque package payload only; never traverse repository catalogs/docs.
    selections = [('itru', '*.py'), ('schemas', '*.schema.json'), ('roles', '*.yaml'),
                  ('itru/_sqlite_admission_migrations', '*.sql'),
                  ('itru/_sqlite_journal_migrations', '*.sql')]
    for directory, pattern in selections:
        output = destination/directory
        output.mkdir(parents=True, exist_ok=True)
        for source in sorted((ROOT/directory).glob(pattern)):
            if source.is_symlink() or not source.is_file():
                raise ValueError('plain package payload required')
            shutil.copyfile(source, output/source.name)
        init = ROOT/directory/'__init__.py'
        if init.is_file() and not (output/'__init__.py').exists():
            shutil.copyfile(init, output/'__init__.py')


def build(output):
    expected = ROOT/'.tmp'/'itru-064-release'
    if output != expected or output.resolve() != output:
        raise ValueError('release output must be the exact locked directory')
    output.mkdir(parents=True, exist_ok=True)
    wheelhouse = output/'wheelhouse'
    wheelhouse.mkdir(exist_ok=True)
    pins = ['setuptools==80.9.0', 'wheel==0.45.1'] + [
        name + '==' + importlib.metadata.version(name)
        for name in ('PyYAML', 'jsonschema', 'referencing', 'attrs',
                     'jsonschema-specifications', 'rpds-py', 'typing_extensions')]
    pins_path = output/'dependency-pins.json'
    if not pins_path.exists():
        # Sole network-capable step. Downloads public Python wheels; no upload.
        run([sys.executable, '-m', 'pip', 'download', '--only-binary=:all:',
             '--dest', wheelhouse, *pins])
        pins_path.write_text(json.dumps(pins, indent=2) + '\n', encoding='utf-8')
    elif json.loads(pins_path.read_text()) != pins:
        raise ValueError('frozen dependency pins differ; do not silently refresh')
    nonce = uuid.uuid4().hex[:8]
    build_env = output/('build-env-' + nonce)
    venv.EnvBuilder(with_pip=True).create(build_env)
    python = build_env/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    run([python, '-m', 'pip', 'install', '--no-index', '--find-links', wheelhouse,
         'setuptools==80.9.0', 'wheel==0.45.1'])
    env = dict(os.environ, SOURCE_DATE_EPOCH='1767225600', PYTHONHASHSEED='0', PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    built = []
    for label in ('first', 'second'):
        directory = output/(label + '-' + nonce)
        stage(directory)
        dist = directory/'dist'
        run([python, '-m', 'pip', 'wheel', '--no-index', '--no-deps', '--no-build-isolation',
             '--wheel-dir', dist, directory], cwd=directory, env=env)
        wheels = list(dist.glob('itru-0.1.0a1-*.whl'))
        if len(wheels) != 1:
            raise ValueError('exactly one Alpha wheel required')
        built.append(wheels[0])
    if built[0].read_bytes() != built[1].read_bytes():
        raise ValueError('nonreproducible Alpha wheel')
    wheel = wheelhouse/built[0].name
    shutil.copyfile(built[0], wheel)
    locks = []
    for path in sorted(wheelhouse.glob('*.whl')):
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith('.dist-info/METADATA') and n.count('/') == 1]
            if len(names) != 1:
                raise ValueError('wheel metadata ambiguity')
            from email.parser import BytesParser
            metadata = BytesParser().parsebytes(archive.read(names[0]))
        locks.append(f"{metadata['Name']}=={metadata['Version']} --hash=sha256:{sha(path)}")
    requirements = output/'requirements.lock'
    requirements.write_text('\n'.join(locks) + '\n', encoding='utf-8')
    payload = {'wheelhouse/' + p.name: p for p in sorted(wheelhouse.glob('*.whl'))}
    payload['requirements.lock'] = requirements
    for name in ('docs/developer-alpha.md', 'examples/developer-alpha/work.json', 'examples/developer-alpha/input.txt'):
        payload[name] = ROOT/name
    hashes = {name: sha(path) for name, path in payload.items()}
    hash_path = output/'SHA256SUMS.json'
    hash_path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    payload['SHA256SUMS.json'] = hash_path
    bundle = output/'itru-0.1.0a1-windows-py312-offline.zip'
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(payload.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    receipt = dict(status='PASS', reproducible_wheel=True, wheel=str(wheel.relative_to(output)),
        wheel_sha256=sha(wheel), bundle=bundle.name, bundle_sha256=sha(bundle),
        product_sha256=manifest(), payload_sha256=hashes, dependency_pins=pins)
    (output/'build-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(receipt, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--gate-manifest', action='store_true')
    args = parser.parse_args()
    if args.gate_manifest:
        print(json.dumps(manifest(), indent=2, sort_keys=True))
    elif args.output:
        build(args.output.absolute())
    else:
        parser.error('--output or --gate-manifest required')
