"""Explicit local integration check; not collected by normal unittest discovery.

Creates and removes two temporary venvs. Requires Python 3.12+, package/build
dependency access, Git, and Node/npm for Manifest-driven repository verification.
Run: python -B tests/package_installation_smoke.py
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path, env: dict[str, str], expected: int = 0) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", shell=False)
    print(f"$ [{cwd}] {' '.join(command)}", flush=True)
    if result.returncode != expected:
        print(result.stdout + result.stderr, flush=True)
        raise AssertionError(f"Expected {expected}, got {result.returncode}")
    print(f"PASS exit={result.returncode}", flush=True)
    return result.stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source_digest() -> dict[str, str]:
    paths = [ROOT / "pyproject.toml", ROOT / "aio.py"]
    paths += list((ROOT / "engineering_orchestration").glob("*.py"))
    paths += list((ROOT / "schemas").glob("*.json"))
    paths += list((ROOT / "roles").glob("*.yaml"))
    return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def make_project(base: Path) -> Path:
    project = base / "external project"
    tasks = project / "governance/tasks/unrelated-directory"
    tasks.mkdir(parents=True)
    (project / ".ai").mkdir()
    manifest = {
        "schema_version": "0.1", "project": {"id": "external", "name": "External",
        "type": "application", "lifecycle": "greenfield"},
        "orchestra": {"version": "0.1.0"}, "complexity": {"default": "medium"},
        "risk": {"default": "low"}, "execution": {"default_mode": "standard"},
        "human_control": {}, "quality": {},
        "tasks": {"directory": "governance/tasks"},
        "verification": {"checks": [{"id": "tests",
            "command": [sys.executable, "-c",
                "from pathlib import Path; Path('verification-ran').touch()"],
            "timeout_seconds": 7}]},
    }
    (project / ".ai/project.yaml").write_text(json.dumps(manifest), encoding="utf-8")
    (tasks / "task.yaml").write_text(json.dumps({
        "id": "LOCAL-123", "title": "External Task", "type": "implementation",
        "status": "in_progress", "objective": "Exercise installed resources",
        "scope": {"include": ["Inspection"]}, "workflow": "external-flow",
    }), encoding="utf-8")
    for name in ("context.md", "acceptance-criteria.md", "review.md"):
        (tasks / name).write_text("# External fixture\n", encoding="utf-8")
    (project / "workflows").mkdir()
    (project / "workflows/unrelated-filename.yaml").write_text(json.dumps({
        "id": "external-flow", "name": "External", "purpose": "Local governance",
        "stages": [{"id": "external-stage", "purpose": "Local check",
                    "required_roles": ["software-engineer"],
                    "required_quality_gates": ["external_gate"]}],
    }), encoding="utf-8")
    (project / "roles").mkdir()
    (project / "roles/software-engineer.yaml").write_text(json.dumps({
        "id": "project-only-role", "name": "Project override",
        "purpose": "Must be ignored by the framework Role catalog.",
        "responsibilities": [], "required_capabilities": [],
    }), encoding="utf-8")
    (project / "src/nested").mkdir(parents=True)
    return project


def main() -> None:
    require(sys.version_info[:2] == (3, 12), "Validate the adopted baseline on Python 3.12")
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    env["PYTHONUTF8"] = "1"
    before = source_digest()
    print(f"Python: {sys.version}; PYTHONPATH/PYTHONHOME removed", flush=True)
    with tempfile.TemporaryDirectory(prefix="aio017-") as temporary:
        base = Path(temporary).resolve()
        require(not base.is_relative_to(ROOT), "Temporary environments must be outside checkout")
        project = make_project(base)
        for mode in ("editable", "normal"):
            environment = base / mode
            venv.EnvBuilder(with_pip=True).create(environment)
            executable_dir = environment / ("Scripts" if os.name == "nt" else "bin")
            python = executable_dir / ("python.exe" if os.name == "nt" else "python")
            aio = executable_dir / ("aio.exe" if os.name == "nt" else "aio")
            run_env = dict(env)
            run_env["PATH"] = str(executable_dir) + os.pathsep + run_env.get("PATH", "")
            if mode == "editable":
                run([str(python), "-m", "pip", "install", "-e", str(ROOT)], base, run_env)
            else:
                wheel_dir = base / "wheels"
                run([str(python), "-m", "pip", "wheel", "--no-deps", "--wheel-dir",
                     str(wheel_dir), str(ROOT)], base, run_env)
                wheel = next(wheel_dir.glob("ai_engineering_orchestra-*.whl"))
                with zipfile.ZipFile(wheel) as archive:
                    names = archive.namelist()
                    modules = {f"engineering_orchestration/{name}" for name in
                               ("__init__.py", "_responsibility.py", "actor_availability.py", "actor_coverage.py", "actor_selection.py", "assignment.py", "cli.py", "list_tasks.py", "inspect_task.py",
                                "verify_repo.py", "workflow_catalog.py", "role_catalog.py", "schema_resources.py",
                                "project.py", "validation.py", "project_verification.py")}
                    schemas = {f"engineering_orchestration/_schemas/{name}" for name in
                               ("actor-availability.schema.json", "actor.schema.json", "assignment.schema.json", "role.schema.json", "task.schema.json", "workflow.schema.json",
                                "project-manifest.schema.json")}
                    roles = {f"engineering_orchestration/_roles/{name}" for name in
                             ("architect.yaml", "documentation-specialist.yaml", "reviewer.yaml",
                              "security-reviewer.yaml", "software-engineer.yaml")}
                    payload = {name for name in names if ".dist-info/" not in name}
                    require(payload == modules | schemas | roles,
                            f"Unexpected wheel payload: {payload}")
                    for name in schemas:
                        require(archive.read(name) == (ROOT / "schemas" / Path(name).name).read_bytes(),
                                "Installed schema differs from canonical source")
                    for name in roles:
                        require(archive.read(name) == (ROOT / "roles" / Path(name).name).read_bytes(),
                                "Installed Role differs from canonical source")
                    print("WHEEL CONTENTS:\n" + "\n".join(names), flush=True)
                run([str(python), "-m", "pip", "install", str(wheel)], base, run_env)
            run([str(python), "-m", "pip", "check"], base, run_env)
            probe = """
import json, sys
from pathlib import Path
import engineering_orchestration.cli as cli
import engineering_orchestration.actor_availability as actor_availability
import engineering_orchestration.actor_coverage as actor_coverage
import engineering_orchestration.actor_selection as actor_selection
import engineering_orchestration.assignment as assignment
import engineering_orchestration.project_verification as project_verification
import engineering_orchestration.role_catalog as role_catalog
from engineering_orchestration.workflow_catalog import load_workflow_catalog
from engineering_orchestration.schema_resources import schema_resource
catalog = role_catalog.load_role_catalog()
software_engineer = catalog.get('software-engineer')
actor = {'id': 'installed-agent', 'kind': 'agent',
         'competencies': list(software_engineer['required_capabilities'])}
human_actor = {'id': 'installed-human', 'kind': 'human',
               'competencies': list(software_engineer['required_capabilities'])}
coverage = actor_coverage.evaluate_actor_role_coverage(actor, software_engineer)
observations = [
    actor_availability.ActorAvailabilityObservation(
        'installed-agent', actor_availability.AvailabilityState.AVAILABLE),
    actor_availability.ActorAvailabilityObservation(
        'installed-human', actor_availability.AvailabilityState.UNAVAILABLE),
]
availability_result = actor_availability.validate_actor_availability(
    observations,
    [actor, human_actor])
workflow_catalog = load_workflow_catalog(Path.cwd().parents[1] / 'workflows')
selection_result = actor_selection.select_actor(
    {'id': 'LOCAL-123', 'workflow': 'external-flow'},
    'external-stage', 'software-engineer', workflow_catalog, catalog,
    [actor, human_actor], observations)
binding = assignment.Assignment('LOCAL-123', 'external-flow', 'external-stage',
                                'software-engineer', 'installed-agent')
assignment_result = assignment.validate_assignment_set(
    [binding], {'id': 'LOCAL-123', 'workflow': 'external-flow'},
    workflow_catalog, catalog, [actor])
role_source = role_catalog.find_default_roles_resource()
print(json.dumps({'module': cli.__file__,
    'availability_module': actor_availability.__file__,
    'actor_module': actor_coverage.__file__,
    'selection_module': actor_selection.__file__,
    'assignment_module': assignment.__file__,
    'runner_module': project_verification.__file__,
    'role_module': role_catalog.__file__, 'role_ids': catalog.role_ids,
    'role_valid': catalog.is_valid, 'coverage': coverage.compatible,
    'availability_valid': availability_result.valid,
    'availability_states': {observation.actor_id: observation.state for observation
                            in availability_result.normalized_observations},
    'availability_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('actor-availability', 'actor-availability.yaml', 'availability', 'availability.yaml')),
    'selection_valid': selection_result.valid,
    'selection_outcome': selection_result.outcome,
    'selected_actor_id': selection_result.selected_actor_id,
    'selection_evidence': {
        'eligible': selection_result.eligible_actor_ids,
        'available': selection_result.available_actor_ids,
        'unknown': selection_result.unknown_actor_ids},
    'selection_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('actor-selections', 'actor-selection.yaml', 'selections', 'selection.yaml')),
    'assignment_valid': assignment_result.valid,
    'assignment_complete': assignment_result.complete,
    'assignment_storage_absent': not (Path.cwd().parents[1] / '.ai/assignments').exists(),
    'roles': [str(role_source.joinpath(name)) for name in
    ('architect.yaml', 'documentation-specialist.yaml', 'reviewer.yaml',
     'security-reviewer.yaml', 'software-engineer.yaml')],
    'schemas': [str(schema_resource(n)) for n in
    ('actor-availability.schema.json', 'actor.schema.json', 'assignment.schema.json', 'role.schema.json', 'task.schema.json', 'workflow.schema.json',
     'project-manifest.schema.json')], 'sys_path': sys.path}))
"""
            evidence = json.loads(run([str(python), "-B", "-c", probe], project / "src/nested", run_env))
            print(f"{mode.upper()} IMPORT/RESOURCE EVIDENCE: {json.dumps(evidence)}", flush=True)
            if mode == "normal":
                require(Path(evidence["module"]).resolve().is_relative_to(environment),
                        "Normal install imports leaked to source")
                require(Path(evidence["runner_module"]).resolve().is_relative_to(environment),
                        "Normal runner import leaked to source")
                require(Path(evidence["availability_module"]).resolve().is_relative_to(environment),
                        "Normal Actor Availability validator import leaked to source")
                require(Path(evidence["actor_module"]).resolve().is_relative_to(environment),
                        "Normal Actor evaluator import leaked to source")
                require(Path(evidence["selection_module"]).resolve().is_relative_to(environment),
                        "Normal Actor Selection import leaked to source")
                require(Path(evidence["assignment_module"]).resolve().is_relative_to(environment),
                        "Normal Assignment validator import leaked to source")
                require(Path(evidence["role_module"]).resolve().is_relative_to(environment),
                        "Normal Role catalog import leaked to source")
                for path in evidence["schemas"]:
                    require(Path(path).resolve().is_relative_to(environment), "Resource leaked to source")
                for path in evidence["roles"]:
                    require(Path(path).resolve().is_relative_to(environment),
                            "Role resource leaked to source")
                require(all(not Path(p).resolve().is_relative_to(ROOT) for p in evidence["sys_path"] if p),
                        "Checkout unexpectedly present on sys.path")
            require(evidence["role_valid"], "Installed Role catalog is invalid")
            require(evidence["role_ids"] == ["architect", "documentation-specialist", "reviewer",
                                             "security-reviewer", "software-engineer"],
                    "Installed Role IDs differ from canonical catalog")
            require(evidence["coverage"], "Installed Role-to-Actor coverage failed")
            require(evidence["availability_valid"],
                    "Installed Actor Availability validation failed")
            require(evidence["availability_states"] == {
                        "installed-agent": "available", "installed-human": "unavailable"},
                    "Installed Human and Agent availability states differ from observations")
            require(evidence["availability_storage_absent"],
                    "Actor Availability validation unexpectedly required project storage")
            require(evidence["selection_valid"]
                    and evidence["selection_outcome"] == "selected"
                    and evidence["selected_actor_id"] == "installed-agent",
                    "Installed Actor Selection failed")
            require(evidence["selection_evidence"] == {
                        "eligible": ["installed-agent", "installed-human"],
                        "available": ["installed-agent"], "unknown": []},
                    "Installed Actor Selection evidence is incorrect")
            require(evidence["selection_storage_absent"],
                    "Actor Selection unexpectedly required project storage")
            require(evidence["assignment_valid"] and evidence["assignment_complete"],
                    "Installed Assignment validation failed")
            require(evidence["assignment_storage_absent"],
                    "Assignment validation unexpectedly required project storage")
            for cwd in (ROOT, ROOT / "scripts"):
                for args, marker in [(["--help"], "{tasks,inspect,verify}"),
                                     (["tasks"], "AIO-016"),
                                     (["inspect", "AIO-015"], "Schema: VALID")]:
                    output = run([str(aio), *args], cwd, run_env)
                    require(marker in output, f"Missing expected output: {marker}")
            output = run([str(aio), "verify", "--structure"], ROOT / "scripts", run_env)
            require("Supported AIO Structure" in output, "Installed structure mode failed")
            output = run([str(aio), "verify"], ROOT, run_env)
            require("Verification passed." in output and "unit-tests" in output,
                    "Installed Orchestra verification did not use Manifest checks")
            for args in (["tasks"], ["inspect", "LOCAL-123"]):
                output = run([str(aio), *args], project / "src/nested", run_env)
                require("LOCAL-123" in output and "AIO-015" not in output, "Wrong active project")
                if args[0] == "inspect":
                    require("external_gate" in output and "Resolution: RESOLVED" in output,
                            "Target Workflow was not used")
            structural_probe = """
import json
from pathlib import Path
from unittest.mock import patch
from engineering_orchestration.validation import validate_project
root = Path.cwd().parents[1]
assert not any((root / name).exists() for name in ('.git', 'tests', 'schemas', 'node_modules'))
task = root / 'governance/tasks/unrelated-directory/task.yaml'
flow = root / 'workflows/unrelated-filename.yaml'
manifest = root / '.ai/project.yaml'
def check(expected):
    with patch('subprocess.run', side_effect=AssertionError('No project commands')), \
         patch('subprocess.Popen', side_effect=AssertionError('No project commands')):
        result = validate_project()
    assert result.status == expected, result
check('PASS')
saved_manifest = manifest.read_text()
try:
    data = json.loads(saved_manifest)
    data.pop('verification')
    manifest.write_text(json.dumps(data))
    check('PASS')
    data = json.loads(saved_manifest)
    data['verification']['checks'][0]['timeout_seconds'] = True
    manifest.write_text(json.dumps(data))
    check('FAIL')
    data = json.loads(saved_manifest)
    data['verification']['checks'].append(dict(data['verification']['checks'][0], command=['different']))
    manifest.write_text(json.dumps(data))
    check('FAIL')
finally:
    manifest.write_text(saved_manifest)
for path in (manifest, task):
    saved = path.read_text()
    try:
        path.write_text('[]')
        check('FAIL')
    finally:
        path.write_text(saved)
duplicate = task.parent.parent / 'different-directory'
duplicate.mkdir()
try:
    (duplicate / 'task.yaml').write_text(task.read_text())
    check('FAIL')
finally:
    (duplicate / 'task.yaml').unlink()
    duplicate.rmdir()
saved = task.read_text()
try:
    data = json.loads(saved)
    data['workflow'] = 'unknown'
    task.write_text(json.dumps(data))
    check('FAIL')
finally:
    task.write_text(saved)
duplicate = flow.with_name('duplicate.yaml')
try:
    duplicate.write_text(flow.read_text())
    check('FAIL')
finally:
    duplicate.unlink()
saved = flow.read_text()
try:
    data = json.loads(saved)
    data['stages'].append(data['stages'][0])
    flow.write_text(json.dumps(data))
    check('FAIL')
finally:
    flow.write_text(saved)
saved = flow.read_text()
try:
    data = json.loads(saved)
    data['stages'][0]['required_roles'] = ['nonexistent-role']
    flow.write_text(json.dumps(data))
    check('FAIL')
finally:
    flow.write_text(saved)
with patch('engineering_orchestration.schema_resources.schema_resource', return_value=None):
    check('ERROR')
check('PASS')
print('PASS: installed structural validation, custom paths, invalid data, identities, references, framework Roles, resources')
"""
            print(run([str(python), "-B", "-c", structural_probe], project / "src/nested", run_env), flush=True)
            run([str(aio), "tasks"], base, run_env, expected=2)
            run([str(aio), "inspect", "MISSING"], project, run_env, expected=1)

            marker = project / "verification-ran"
            marker.unlink(missing_ok=True)
            output = run([str(aio), "verify"], project / "src/nested", run_env)
            require(marker.exists(), "Installed verifier did not execute adopter declaration")
            require("tests" in output and "Verification passed." in output,
                    "Installed adopter verification output incomplete")
            saved_manifest = (project / ".ai/project.yaml").read_text(encoding="utf-8")
            try:
                data = json.loads(saved_manifest)
                data["verification"]["checks"] = []
                (project / ".ai/project.yaml").write_text(json.dumps(data), encoding="utf-8")
                marker.unlink(missing_ok=True)
                output = run([str(aio), "verify"], project, run_env)
                require("0 project checks configured" in output,
                        "Installed zero-check project did not remain empty")
                require(not marker.exists(), "Zero-check verification executed a command")
            finally:
                (project / ".ai/project.yaml").write_text(saved_manifest, encoding="utf-8")
            alias = """
import sys
from importlib.metadata import EntryPoint, distribution
entry = next(e for e in distribution('ai-engineering-orchestra').entry_points if e.name == 'aio')
assert EntryPoint(name='rook', value=entry.value, group='console_scripts').load() is entry.load()
sys.argv = ['rook', '--help']
entry.load()()
"""
            output = run([str(python), "-B", "-c", alias], base, run_env)
            require("rook" in output, "Alias help did not reflect caller name")
            run([str(python), "-m", "pip", "uninstall", "-y", "ai-engineering-orchestra"], base, run_env)
            require(not aio.exists(), "Uninstall left executable behind")
            run([str(python), "-B", "-c",
                 "import importlib.util; assert importlib.util.find_spec('engineering_orchestration') is None"],
                base, run_env)
            require(before == source_digest(), "Install/uninstall modified authoritative sources")
            print(f"{mode.upper()}: commands, external project, alias and uninstall PASS", flush=True)
        print("External and zero-check installed verification PASS.", flush=True)
    require(not base.exists(), "Temporary environments were not cleaned")
    print("PASS: both temporary venvs and fixtures removed; no sdist generated", flush=True)


if __name__ == "__main__":
    main()
