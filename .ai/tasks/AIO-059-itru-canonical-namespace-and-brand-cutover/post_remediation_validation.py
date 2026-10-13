"""Explicit AIO-059 delta validation; no test or repository discovery."""
from __future__ import annotations

import ast
import configparser
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = Path(__file__).with_name("post-remediation-validation.json")
WHEELHOUSE = Path(r"D:\Dev\.aio-tools\python-build-wheelhouse\setuptools\77.0.3")
SOURCE_FILES = tuple("itru/" + name for name in (
    "__init__.py", "_execution_entry_and_controlled_invocation.py",
    "_jit_execution_attempt_authorization.py", "_local_dispatch_claim_lease.py",
    "_native_repository_file_read.py", "_operation_vocabulary.py",
    "_read_only_execution_preparation.py", "_repository_resource.py", "_responsibility.py",
    "_sqlite_admission_migrations/__init__.py",
    "_sqlite_admission_migrations/0001_initial.sql",
    "_sqlite_admission_migrations/0002_dispatch_outbox.sql",
    "_sqlite_admission_migrations/0003_dispatch_claim_lease.sql",
    "_sqlite_admission_migrations/0004_execution_entry.sql",
    "actor_availability.py", "actor_coverage.py", "actor_runtime_applicability.py",
    "actor_selection.py", "agent_action_prerequisite.py",
    "agent_execution_authorization_evidence.py", "agent_execution_authorization_grant.py",
    "agent_execution_authorization_grant_producer.py", "agent_execution_candidate_prerequisite.py",
    "agent_execution_contract.py", "agent_execution_dispatch_admission.py",
    "agent_execution_dispatch_admission_store.py", "agent_execution_run.py",
    "agent_operation_tool_binding.py", "agent_operation_tool_registry.py",
    "agent_operation_tool_resolver.py", "agent_runtime_option.py",
    "agent_runtime_option_availability.py", "assignment.py", "authorization_domain_ownership.py",
    "cli.py", "environment_operation_permission.py", "execution_mode.py", "inference_option.py",
    "inference_option_availability.py", "inspect_task.py", "list_tasks.py",
    "local_operational_trust.py", "operation_requirement.py", "project.py",
    "project_verification.py", "role_catalog.py", "runtime_inference_compatibility.py",
    "runtime_inference_pair_availability.py", "runtime_operation_capability.py",
    "schema_resources.py", "sqlite_agent_execution_dispatch_admission_store.py",
    "validation.py", "verify_repo.py", "windows_local_authorization_domain_owner.py",
    "workflow_catalog.py",
))
ROLE_FILES = tuple(name + ".yaml" for name in (
    "architect", "documentation-specialist", "reviewer", "security-reviewer", "software-engineer",
))
CHANGED_PYTHON = (
    "tests/test_itru_namespace.py", "itru/agent_operation_tool_registry.py",
    "itru/local_operational_trust.py", "tests/test_local_operational_trust.py",
)
MIGRATIONS = {
    "0001_initial.sql": "6ef55742cc589de7e9ef5f319424a4c31c7aa94c8da429860b5781fef2add4ed",
    "0002_dispatch_outbox.sql": "eee70c9d3e31dca036e716fc8b0ad42c78c97bb07cc5c6e323eaa7290e0ba6db",
    "0003_dispatch_claim_lease.sql": "c9163740873586ab39ee760c292cdcdd07bf050ee06f37c29614c5e3a8144949",
    "0004_execution_entry.sql": "044dec78513447aaddb5544f6e56ce9667be6b370ec42c510ae1fdf3a954a2b1",
}
TEST_GROUPS = {
    "namespace": ("test_itru_namespace",),
    "pure_manifest": ("test_local_operational_trust.PermanentHistoricalManifestTests",),
    "registry_resolver_binding_grant": (
        "test_agent_operation_tool_registry", "test_agent_operation_tool_resolver",
        "test_agent_operation_tool_binding", "test_agent_execution_authorization_grant_producer",
    ),
    "historical_compatibility_authority_rebound": (
        "test_local_operational_trust.ItruHistoricalBoundaryTests",
    ),
    "affected_predecessors": (
        "test_local_operational_trust.LocalOperationalTrustContractTests",
        "test_local_operational_trust.LocalOperationalTrustWindowsTests",
        "test_local_operational_trust.LocalOperationalTrustScenarioMapTests",
    ),
}


def audit(event, args):
    if event.startswith("socket."):
        raise RuntimeError("network forbidden during delta validation")
    if event in ("open", "os.listdir", "os.scandir") and args and isinstance(args[0], (str, bytes)):
        path = Path(os.fsdecode(args[0])).resolve()
        if event == "open" and path in (REPORT_PATH, Path(__file__).resolve()):
            return  # exact current-Task evidence, never catalog enumeration
        for forbidden in (ROOT / ".ai" / "tasks", ROOT / "workflows", ROOT / "experiments"):
            if path == forbidden or forbidden in path.parents:
                raise RuntimeError(f"protected catalog/evidence access forbidden: {path}")


def test_ids(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id()


def main():
    sys.addaudithook(audit)
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tests"))
    evidence = Path(tempfile.mkdtemp(prefix="itru-aio059-post-remediation-"))
    report = {"status": "RUNNING", "evidence_directory": str(evidence), "commands": [],
              "test_groups": {}, "original_386_runner_reconstructed": False}
    env = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1",
               PIP_NO_INPUT="1", PYTHONDONTWRITEBYTECODE="1")

    def run(label, command, cwd):
        command = list(map(str, command))
        completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
        log = evidence / (label + ".log")
        log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
        report["commands"].append({"label": label, "argv": command, "cwd": str(cwd),
                                   "exit_code": completed.returncode, "log": str(log)})
        if completed.returncode:
            raise RuntimeError(f"{label} failed: {completed.stdout}{completed.stderr}")
        print(label + ": PASS", flush=True)
        return completed.stdout

    try:
        for label, names in TEST_GROUPS.items():
            loader = unittest.TestLoader()
            suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in names)
            ids = tuple(test_ids(suite))
            with (evidence / (label + ".log")).open("w", encoding="utf-8") as log:
                result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
            report["test_groups"][label] = {"selectors": names, "test_ids": ids,
                "total": result.testsRun, "fail": len(result.failures), "error": len(result.errors),
                "skip": len(result.skipped)}
            if not result.wasSuccessful() or result.skipped:
                raise RuntimeError(f"{label} failed; inspect exact log in {evidence}")
            print(f"{label}: {result.testsRun} PASS", flush=True)

        import test_itru_namespace as guard
        assert len(guard._ALLOWLIST) == 1106
        report["allowlist_records"] = len(guard._ALLOWLIST)
        for name in CHANGED_PYTHON:
            source = (ROOT / name).read_text(encoding="utf-8")
            compile(ast.parse(source, filename=name), name, "exec")
        report["changed_python_ast_compile"] = list(CHANGED_PYTHON)

        # This is the same bounded production manifest mechanism as the guard,
        # restricted to the already-known package paths; no test-file enumeration.
        listed = run("exact-production-manifest", (
            "git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "itru/",
        ), ROOT)
        assert set(listed.split("\0")) - {""} == set(SOURCE_FILES), "unexpected production package path"
        configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        assert configuration["project"]["name"] == "itru"
        assert configuration["project"]["scripts"] == {"itru": "itru.cli:main"}
        schema_names = configuration["tool"]["setuptools"]["package-data"]["itru._schemas"]
        assert len(schema_names) == 22
        snapshot = evidence / "source-snapshot"
        snapshot.mkdir()
        payload = {}
        copies = {name: name for name in SOURCE_FILES}
        copies.update({"schemas/" + name: "schemas/" + name for name in schema_names})
        copies.update({"roles/" + name: "roles/" + name for name in ROLE_FILES})
        for name, destination in copies.items():
            data = (ROOT / name).read_bytes()
            target = snapshot / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            wheel_name = destination.replace("schemas/", "itru/_schemas/", 1) if destination.startswith("schemas/") else (
                destination.replace("roles/", "itru/_roles/", 1) if destination.startswith("roles/") else destination)
            payload[wheel_name] = data
        (snapshot / "pyproject.toml").write_bytes((ROOT / "pyproject.toml").read_bytes())
        assert len(payload) == 82
        report["source_files"] = list(copies)
        report["migration_hashes"] = {}
        for name, digest in MIGRATIONS.items():
            data = payload["itru/_sqlite_admission_migrations/" + name]
            actual = hashlib.sha256(data).hexdigest()
            assert actual == digest and b"\r" not in data, name
            report["migration_hashes"][name] = actual

        build_environment = evidence / "build-env"
        venv.EnvBuilder(with_pip=True).create(build_environment)
        build_python = build_environment / "Scripts" / "python.exe"
        report["build_environment"] = str(build_environment)
        report["wheelhouse"] = str(WHEELHOUSE)
        run("install-pinned-backend", (build_python, "-B", "-m", "pip", "install",
            "--no-index", "--no-deps", "--no-cache-dir", "--disable-pip-version-check",
            "--find-links", WHEELHOUSE, "setuptools==77.0.3"), evidence)
        version = run("verify-pinned-backend", (build_python, "-I", "-B", "-c",
            "from importlib.metadata import version; v=version('setuptools'); assert v=='77.0.3'; print(v)"), evidence).strip()
        report["setuptools_version"] = version
        dist = evidence / "dist"
        run("offline-current-source-wheel", (build_python, "-B", "-m", "pip", "wheel",
            "--no-index", "--no-deps", "--no-build-isolation", "--no-cache-dir",
            "--disable-pip-version-check", "--wheel-dir", dist, snapshot), evidence)
        wheel = dist / "itru-0.1.0-py3-none-any.whl"
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
            assert {name.split("/", 1)[0] for name in names} == {"itru", "itru-0.1.0.dist-info"}
            assert {name for name in names if name.startswith("itru/")} == set(payload)
            assert all(archive.read(name) == data for name, data in payload.items())
            metadata = BytesParser().parsebytes(archive.read("itru-0.1.0.dist-info/METADATA"))
            assert metadata["Name"] == "itru"
            entries = configparser.ConfigParser()
            entries.read_string(archive.read("itru-0.1.0.dist-info/entry_points.txt").decode("utf-8"))
            assert dict(entries["console_scripts"]) == {"itru": "itru.cli:main"}
        report["wheel"] = str(wheel)
        report["wheel_sha256"] = hashlib.sha256(wheel.read_bytes()).hexdigest()
        report["wheel_package_files"] = len(payload)
        report["wheel_migrations_byte_identical"] = True

        installed_environment = evidence / "installed-env"
        # As in Phase 2D, only existing third-party dependencies are shared.
        # ITRU itself must resolve entirely inside this fresh environment.
        venv.EnvBuilder(with_pip=True, system_site_packages=True).create(installed_environment)
        installed_python = installed_environment / "Scripts" / "python.exe"
        run("install-fresh-wheel", (installed_python, "-B", "-m", "pip", "install",
            "--no-index", "--no-deps", "--force-reinstall", "--no-cache-dir",
            "--disable-pip-version-check", wheel), evidence)
        hashes = {name: hashlib.sha256(data).hexdigest() for name, data in payload.items()}
        probe_input = evidence / "installed-probe-input.json"
        probe_input.write_text(json.dumps(hashes, sort_keys=True), encoding="utf-8")
        probe = '''
import hashlib, importlib, importlib.metadata, importlib.util, json, pathlib, sys
def deny_network(event, args):
    if event.startswith('socket.'):
        raise RuntimeError('network forbidden')
sys.addaudithook(deny_network)
environment = pathlib.Path(sys.prefix).resolve()
hashes = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
modules = ('itru', 'itru.cli', 'itru.schema_resources', 'itru.role_catalog',
           'itru.agent_operation_tool_registry', 'itru.agent_operation_tool_resolver',
           'itru.local_operational_trust', 'itru.sqlite_agent_execution_dispatch_admission_store',
           'itru._native_repository_file_read')
for name in modules:
    module = importlib.import_module(name)
    assert pathlib.Path(module.__file__).resolve().is_relative_to(environment), name
assert importlib.util.find_spec('engineering_orchestration') is None
package = pathlib.Path(importlib.import_module('itru').__file__).resolve().parent
for name, digest in hashes.items():
    assert hashlib.sha256((package.parent / name).read_bytes()).hexdigest() == digest, name
distribution = importlib.metadata.distribution('itru')
assert pathlib.Path(distribution.locate_file('')).resolve().is_relative_to(environment)
assert {(e.name,e.value) for e in distribution.entry_points if e.group=='console_scripts'} == {('itru','itru.cli:main')}
assert (environment / 'Scripts' / 'itru.exe').is_file()
assert not (environment / 'Scripts' / 'aio.exe').exists()
from itru import agent_operation_tool_registry as registry
registration = registry._make_itru_native_repository_file_read_registration('runtime::wheel-validation', 'environment::wheel-validation')
snapshot = registry._build_trusted_agent_operation_tool_registry_snapshot((registration,)).snapshot
assert snapshot is not None
assert {item.tool_id for item in snapshot._registrations} == {'tool::itru-native-repository-file-read::v1'}
from itru.schema_resources import load_validator
for name in ('agent-execution-run.schema.json', 'agent-operation-tool-binding.schema.json', 'role.schema.json'):
    validator = load_validator(name)
    validator.check_schema(validator.schema)
print(json.dumps({'import_path': str(package), 'resources': len(hashes), 'canonical_tool': registration.tool_id}))
'''
        installed_output = run("verify-isolated-installed-wheel", (installed_python, "-I", "-B", "-c", probe, probe_input), evidence)
        report["installed_probe"] = json.loads(installed_output)
        report["installed_environment"] = str(installed_environment)

        for name, destination in copies.items():
            assert (ROOT / name).read_bytes() == (snapshot / destination).read_bytes(), "source changed during build"
        run("git-diff-check", ("git", "diff", "--check"), ROOT)
        staged = run("git-staged-manifest", ("git", "diff", "--cached", "--name-status"), ROOT)
        assert not staged.strip(), "unexpected staged changes"
        report["total_tests"] = sum(group["total"] for group in report["test_groups"].values())
        report["status"] = "PASS"
        print(f"POST-REMEDIATION DELTA: {report['total_tests']} tests PASS; build/install/static PASS", flush=True)
    except BaseException as error:
        report["status"] = "FAILED"
        report["failure"] = repr(error)
        raise
    finally:
        REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("REPORT: " + str(REPORT_PATH), flush=True)


if __name__ == "__main__":
    main()
