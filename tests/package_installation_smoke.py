"""Explicit local integration check; not collected by normal unittest discovery.

Creates and removes two temporary venvs. Requires Python 3.12+, package/build
dependency access, Git, and Node/npm for Manifest-driven repository verification.
Run: python -B tests/package_installation_smoke.py
Use ``--target-safe`` to skip checkout CLI probes that enumerate the repository
Workflow catalog when an external protected-target boundary requires focused
checks instead. Installed behavior is still exercised against synthetic data.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
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
    target_safe = "--target-safe" in sys.argv[1:]
    unknown_arguments = set(sys.argv[1:]) - {"--target-safe"}
    require(not unknown_arguments, f"Unknown arguments: {sorted(unknown_arguments)}")
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
        package_source = base / "package-source"
        package_source.mkdir()
        shutil.copy2(ROOT / "pyproject.toml", package_source / "pyproject.toml")
        shutil.copy2(ROOT / "aio.py", package_source / "aio.py")
        for relative, pattern in (
            ("engineering_orchestration", "*.py"),
            ("schemas", "*.json"),
            ("roles", "*.yaml"),
        ):
            destination = package_source / relative
            destination.mkdir()
            for source in (ROOT / relative).glob(pattern):
                shutil.copy2(source, destination / source.name)
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
                     str(wheel_dir), str(package_source)], base, run_env)
                wheel = next(wheel_dir.glob("ai_engineering_orchestra-*.whl"))
                with zipfile.ZipFile(wheel) as archive:
                    names = archive.namelist()
                    modules = {f"engineering_orchestration/{name}" for name in
                               ("__init__.py", "_operation_vocabulary.py", "_read_only_execution_preparation.py", "_repository_resource.py", "_responsibility.py", "actor_availability.py", "actor_coverage.py", "actor_runtime_applicability.py", "actor_selection.py", "agent_action_prerequisite.py", "agent_execution_authorization_evidence.py", "agent_execution_candidate_prerequisite.py", "agent_execution_contract.py", "agent_runtime_option.py", "agent_runtime_option_availability.py", "assignment.py", "cli.py", "list_tasks.py", "inspect_task.py",
                                "environment_operation_permission.py",
                                "execution_mode.py", "inference_option.py",
                                "inference_option_availability.py",
                                "operation_requirement.py",
                                "runtime_operation_capability.py",
                                "runtime_inference_compatibility.py",
                                "runtime_inference_pair_availability.py",
                                "verify_repo.py", "workflow_catalog.py", "role_catalog.py", "schema_resources.py",
                                "project.py", "validation.py", "project_verification.py")}
                    schemas = {f"engineering_orchestration/_schemas/{name}" for name in
                               ("actor-availability.schema.json", "actor-runtime-applicability.schema.json", "actor.schema.json",
                                "agent-execution-authorization-evidence.schema.json",
                                "agent-execution-contract.schema.json",
                                "agent-runtime-option.schema.json", "agent-runtime-option-availability.schema.json",
                                "assignment.schema.json",
                                "environment-operation-permission.schema.json",
                                "inference-option.schema.json", "inference-option-availability.schema.json",
                                "operation-requirement.schema.json",
                                "runtime-operation-capability.schema.json",
                                "runtime-inference-compatibility.schema.json",
                                "role.schema.json", "task.schema.json", "workflow.schema.json",
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
import json, os, socket, subprocess, sys, time, urllib.request
from pathlib import Path
from unittest.mock import patch
import engineering_orchestration.cli as cli
import engineering_orchestration.actor_availability as actor_availability
import engineering_orchestration.actor_coverage as actor_coverage
import engineering_orchestration.actor_runtime_applicability as actor_runtime_applicability
import engineering_orchestration.actor_selection as actor_selection
import engineering_orchestration.agent_execution_candidate_prerequisite as agent_execution_candidate_prerequisite
import engineering_orchestration.agent_runtime_option as agent_runtime_option
import engineering_orchestration.agent_runtime_option_availability as agent_runtime_option_availability
import engineering_orchestration.assignment as assignment
import engineering_orchestration.execution_mode as execution_mode
import engineering_orchestration.inference_option as inference_option
import engineering_orchestration.inference_option_availability as inference_option_availability
import engineering_orchestration.operation_requirement as operation_requirement
import engineering_orchestration.runtime_operation_capability as runtime_operation_capability
import engineering_orchestration.project_verification as project_verification
import engineering_orchestration.role_catalog as role_catalog
import engineering_orchestration.runtime_inference_compatibility as runtime_inference_compatibility
import engineering_orchestration.runtime_inference_pair_availability as runtime_inference_pair_availability
import engineering_orchestration._operation_vocabulary as operation_vocabulary
import engineering_orchestration._read_only_execution_preparation as read_only_execution_preparation
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
runtime_options = [
    agent_runtime_option.AgentRuntimeOptionDefinition('installed-runtime-primary'),
    agent_runtime_option.AgentRuntimeOptionDefinition('installed-runtime-secondary'),
]
runtime_inventory_result = (
    agent_runtime_option.validate_agent_runtime_option_inventory(runtime_options))
applicability_values = [
    actor_runtime_applicability.ActorRuntimeApplicabilityEvidence(
        'installed-agent', 'installed-runtime-secondary'),
    actor_runtime_applicability.ActorRuntimeApplicabilityEvidence(
        'installed-agent', 'installed-runtime-primary'),
]
applicability_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        applicability_values, [actor, human_actor], runtime_options))
applicability_duplicate_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        [applicability_values[0], applicability_values[0]],
        [actor, human_actor], runtime_options))
applicability_human_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        [actor_runtime_applicability.ActorRuntimeApplicabilityEvidence(
            'installed-human', 'installed-runtime-primary')],
        [actor, human_actor], runtime_options))
applicability_unknown_actor_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        [actor_runtime_applicability.ActorRuntimeApplicabilityEvidence(
            'missing-agent', 'installed-runtime-primary')],
        [actor, human_actor], runtime_options))
applicability_unknown_runtime_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        [actor_runtime_applicability.ActorRuntimeApplicabilityEvidence(
            'installed-agent', 'missing-runtime')],
        [actor, human_actor], runtime_options))
applicability_empty_result = (
    actor_runtime_applicability.validate_actor_runtime_applicability(
        [], [actor, human_actor], runtime_options))
runtime_availability_result = (
    agent_runtime_option_availability.validate_agent_runtime_option_availability(
        [agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
            'installed-runtime-primary',
            agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.AVAILABLE)],
        runtime_options))
inference_options = [
    inference_option.InferenceOptionDefinition(
        'installed-primary', 'provider-a', 'model-x'),
    inference_option.InferenceOptionDefinition(
        'installed-secondary', 'provider-a', 'model-x'),
]
inference_inventory_result = inference_option.validate_inference_option_inventory(
    inference_options)
inference_availability_result = (
    inference_option_availability.validate_inference_option_availability(
        [inference_option_availability.InferenceOptionAvailabilityObservation(
            'installed-primary',
            inference_option_availability.InferenceOptionAvailabilityState.AVAILABLE)],
        inference_options))
compatibility_values = [
    runtime_inference_compatibility.RuntimeInferenceCompatibilityEvidence(
        'installed-runtime-secondary', 'installed-primary'),
    runtime_inference_compatibility.RuntimeInferenceCompatibilityEvidence(
        'installed-runtime-primary', 'installed-secondary'),
    runtime_inference_compatibility.RuntimeInferenceCompatibilityEvidence(
        'installed-runtime-primary', 'installed-primary'),
]
compatibility_result = (
    runtime_inference_compatibility.validate_runtime_inference_compatibility(
        compatibility_values, runtime_options, inference_options))
compatibility_unknown_result = (
    runtime_inference_compatibility.validate_runtime_inference_compatibility(
        [runtime_inference_compatibility.RuntimeInferenceCompatibilityEvidence(
            'installed-runtime-primary', 'missing-option')],
        runtime_options, inference_options))
compatibility_duplicate_result = (
    runtime_inference_compatibility.validate_runtime_inference_compatibility(
        [compatibility_values[0], compatibility_values[0]],
        runtime_options, inference_options))
compatibility_empty_result = (
    runtime_inference_compatibility.validate_runtime_inference_compatibility(
        [], runtime_options, inference_options))
pair_availability_result = (
    runtime_inference_pair_availability.assess_runtime_inference_pair_availability(
        compatibility_values,
        runtime_options,
        inference_options,
        [
            agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
                'installed-runtime-primary',
                agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.AVAILABLE),
            agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
                'installed-runtime-secondary',
                agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.UNAVAILABLE),
        ],
        [inference_option_availability.InferenceOptionAvailabilityObservation(
            'installed-primary',
            inference_option_availability.InferenceOptionAvailabilityState.AVAILABLE)],
    ))
pair_invalid_result = (
    runtime_inference_pair_availability.assess_runtime_inference_pair_availability(
        [compatibility_values[2]],
        runtime_options,
        inference_options,
        [
            agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
                'installed-runtime-primary',
                agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.AVAILABLE),
            agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
                'installed-runtime-primary',
                agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.UNKNOWN),
        ],
        [
            inference_option_availability.InferenceOptionAvailabilityObservation(
                'installed-primary',
                inference_option_availability.InferenceOptionAvailabilityState.AVAILABLE),
            inference_option_availability.InferenceOptionAvailabilityObservation(
                'installed-primary',
                inference_option_availability.InferenceOptionAvailabilityState.UNKNOWN),
        ],
    ))
pair_empty_result = (
    runtime_inference_pair_availability.assess_runtime_inference_pair_availability(
        [], runtime_options, inference_options, [], []))
try:
    schema_resource('runtime-inference-pair-availability.schema.json')
except ValueError:
    pair_availability_schema_absent = True
else:
    pair_availability_schema_absent = False
workflow_catalog = load_workflow_catalog(Path.cwd().parents[1] / 'workflows')
task = {'id': 'LOCAL-123', 'workflow': 'external-flow'}
selection_result = actor_selection.select_actor(
    task,
    'external-stage', 'software-engineer', workflow_catalog, catalog,
    [actor, human_actor], observations)
binding = assignment.Assignment('LOCAL-123', 'external-flow', 'external-stage',
                                'software-engineer', 'installed-agent')
assignment_result = assignment.validate_assignment_set(
    [binding], task,
    workflow_catalog, catalog, [actor])
candidate_runtime_observations = [
    agent_runtime_option_availability.AgentRuntimeOptionAvailabilityObservation(
        'installed-runtime-primary',
        agent_runtime_option_availability.AgentRuntimeOptionAvailabilityState.AVAILABLE),
]
candidate_inference_observations = [
    inference_option_availability.InferenceOptionAvailabilityObservation(
        'installed-primary',
        inference_option_availability.InferenceOptionAvailabilityState.AVAILABLE),
]
candidate_satisfied_result = (
    agent_execution_candidate_prerequisite.
    assess_agent_execution_candidate_prerequisites(
        binding, 'installed-runtime-primary', 'installed-primary', task,
        workflow_catalog, catalog, [actor, human_actor], observations,
        applicability_values, runtime_options, inference_options,
        compatibility_values, candidate_runtime_observations,
        candidate_inference_observations))
candidate_blocked_result = (
    agent_execution_candidate_prerequisite.
    assess_agent_execution_candidate_prerequisites(
        binding, 'installed-runtime-primary', 'installed-primary', task,
        workflow_catalog, catalog, [actor, human_actor],
        [actor_availability.ActorAvailabilityObservation(
            'installed-agent', actor_availability.AvailabilityState.UNAVAILABLE)],
        applicability_values, runtime_options, inference_options,
        compatibility_values, candidate_runtime_observations,
        candidate_inference_observations))
candidate_unresolved_result = (
    agent_execution_candidate_prerequisite.
    assess_agent_execution_candidate_prerequisites(
        binding, 'installed-runtime-primary', 'installed-primary', task,
        workflow_catalog, catalog, [actor, human_actor], observations,
        applicability_values, runtime_options, inference_options, [],
        candidate_runtime_observations, candidate_inference_observations))
candidate_invalid_result = (
    agent_execution_candidate_prerequisite.
    assess_agent_execution_candidate_prerequisites(
        binding, 'installed-runtime-primary', 'installed-primary', task,
        workflow_catalog, catalog, [actor, human_actor],
        [
            actor_availability.ActorAvailabilityObservation(
                'installed-agent', actor_availability.AvailabilityState.AVAILABLE),
            actor_availability.ActorAvailabilityObservation(
                'installed-agent', actor_availability.AvailabilityState.UNKNOWN),
        ],
        applicability_values, runtime_options, inference_options,
        compatibility_values, candidate_runtime_observations,
        candidate_inference_observations))
read_only_preparation_result = (
    read_only_execution_preparation.assess_read_only_execution_preparation(
        candidate_satisfied_result,
        operation_id='repository_file_read',
        resource='workflows/README.md',
        environment_id='installed-environment',
        capability_evidence=(
            read_only_execution_preparation.
            ReadOnlyExecutionCapabilityEvidence(
                'installed-runtime-primary', 'repository_file_read',
                read_only_execution_preparation.
                ReadOnlyExecutionCapabilityState.PRESENT)),
        permission_evidence=(
            read_only_execution_preparation.
            ReadOnlyExecutionPermissionEvidence(
                'installed-runtime-primary', 'installed-environment',
                'repository_file_read', 'workflows/README.md',
                read_only_execution_preparation.
                ReadOnlyExecutionPermissionState.ALLOWED,
                read_only_execution_preparation.
                ReadOnlyExecutionPermissionFreshness.CURRENT)),
        authorization_evidence=(
            read_only_execution_preparation.
            ReadOnlyExecutionAuthorizationEvidence(
                'LOCAL-123', 'external-flow', 'external-stage',
                'software-engineer', 'installed-agent',
                'installed-runtime-primary', 'installed-primary',
                'installed-environment', 'repository_file_read',
                'workflows/README.md',
                read_only_execution_preparation.
                ReadOnlyExecutionAuthorizationSource.HUMAN_PROVIDED,
                read_only_execution_preparation.
                ReadOnlyExecutionAuthorizationState.GRANTED))))
try:
    schema_resource('agent-execution-candidate-prerequisite.schema.json')
except ValueError:
    candidate_prerequisite_schema_absent = True
else:
    candidate_prerequisite_schema_absent = False
with (
    patch('builtins.open', side_effect=AssertionError('no resource I/O')),
    patch.object(Path, 'open', side_effect=AssertionError('no resource I/O')),
    patch.object(Path, 'read_text', side_effect=AssertionError('no resource I/O')),
    patch.object(Path, 'read_bytes', side_effect=AssertionError('no resource I/O')),
    patch.object(Path, 'resolve', side_effect=AssertionError('no path resolution')),
    patch.object(os, 'stat', side_effect=AssertionError('no metadata access')),
    patch.object(subprocess, 'run', side_effect=AssertionError('no process')),
    patch.object(socket, 'create_connection', side_effect=AssertionError('no network')),
    patch.object(urllib.request, 'urlopen', side_effect=AssertionError('no network')),
    patch.object(time, 'time', side_effect=AssertionError('no clock')),
):
    operation_requirement_value = operation_requirement.OperationRequirement(
        'repository_file_read', 'synthetic/install-probe.txt')
    operation_requirement_valid = (
        operation_requirement.validate_operation_requirement(
            operation_requirement_value))
    operation_requirement_unsupported = (
        operation_requirement.validate_operation_requirement(
            operation_requirement.OperationRequirement(
                'repository_file_write', 'synthetic/install-probe.txt')))
    operation_requirement_invalid_resource = (
        operation_requirement.validate_operation_requirement(
            operation_requirement.OperationRequirement(
                'repository_file_read', 'synthetic/../install-probe.txt')))
    capability_present_absent = (
        runtime_operation_capability.validate_runtime_operation_capability(
            [
                runtime_operation_capability.
                RuntimeOperationCapabilityObservation(
                    'installed-runtime-primary', 'repository_file_read',
                    runtime_operation_capability.
                    RuntimeOperationCapabilityState.PRESENT),
                runtime_operation_capability.
                RuntimeOperationCapabilityObservation(
                    'installed-runtime-secondary', 'repository_file_read',
                    runtime_operation_capability.
                    RuntimeOperationCapabilityState.ABSENT),
            ],
            runtime_options))
    capability_unknown_missing = (
        runtime_operation_capability.validate_runtime_operation_capability(
            [runtime_operation_capability.
             RuntimeOperationCapabilityObservation(
                 'installed-runtime-primary', 'repository_file_read',
                 runtime_operation_capability.
                 RuntimeOperationCapabilityState.UNKNOWN)],
            runtime_options))
    capability_duplicate = (
        runtime_operation_capability.validate_runtime_operation_capability(
            [
                runtime_operation_capability.
                RuntimeOperationCapabilityObservation(
                    'installed-runtime-primary', 'repository_file_read',
                    runtime_operation_capability.
                    RuntimeOperationCapabilityState.PRESENT),
                runtime_operation_capability.
                RuntimeOperationCapabilityObservation(
                    'installed-runtime-primary', 'repository_file_read',
                    runtime_operation_capability.
                    RuntimeOperationCapabilityState.ABSENT),
            ],
            runtime_options))
    capability_unknown_runtime = (
        runtime_operation_capability.validate_runtime_operation_capability(
            [runtime_operation_capability.
             RuntimeOperationCapabilityObservation(
                 'missing-runtime', 'repository_file_read',
                 runtime_operation_capability.
                 RuntimeOperationCapabilityState.PRESENT)],
            runtime_options))
    capability_unsupported_operation = (
        runtime_operation_capability.validate_runtime_operation_capability(
            [runtime_operation_capability.
             RuntimeOperationCapabilityObservation(
                 'installed-runtime-primary', 'repository_file_write',
                 runtime_operation_capability.
                 RuntimeOperationCapabilityState.PRESENT)],
            runtime_options))
role_source = role_catalog.find_default_roles_resource()
print(json.dumps({'module': cli.__file__,
    'execution_mode_module': execution_mode.__file__,
    'execution_mode_order': execution_mode.EXECUTION_MODE_ORDER,
    'critical_satisfies_deep': execution_mode.execution_mode_satisfies(
        'critical', 'deep'),
    'availability_module': actor_availability.__file__,
    'actor_runtime_applicability_module': actor_runtime_applicability.__file__,
    'runtime_option_module': agent_runtime_option.__file__,
    'runtime_option_availability_module': agent_runtime_option_availability.__file__,
    'inference_option_module': inference_option.__file__,
    'inference_option_availability_module': inference_option_availability.__file__,
    'runtime_inference_compatibility_module': runtime_inference_compatibility.__file__,
    'runtime_inference_pair_availability_module': runtime_inference_pair_availability.__file__,
    'candidate_prerequisite_module': agent_execution_candidate_prerequisite.__file__,
    'read_only_execution_preparation_module': read_only_execution_preparation.__file__,
    'operation_requirement_module': operation_requirement.__file__,
    'operation_vocabulary_module': operation_vocabulary.__file__,
    'runtime_operation_capability_module': runtime_operation_capability.__file__,
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
    'runtime_inventory_valid': runtime_inventory_result.valid,
    'runtime_option_ids': [option.runtime_option_id for option in
                           runtime_inventory_result.normalized_options],
    'applicability_valid': applicability_result.valid,
    'applicability_edges': [
        [item.actor_id, item.runtime_option_id] for item in
        applicability_result.normalized_evidence],
    'applicability_duplicate_codes': [
        finding.code for finding in applicability_duplicate_result.findings],
    'applicability_duplicate_atomic': (
        not applicability_duplicate_result.valid
        and not applicability_duplicate_result.normalized_evidence),
    'applicability_human_codes': [
        finding.code for finding in applicability_human_result.findings],
    'applicability_human_atomic': (
        not applicability_human_result.valid
        and not applicability_human_result.normalized_evidence),
    'applicability_unknown_actor_codes': [
        finding.code for finding in applicability_unknown_actor_result.findings],
    'applicability_unknown_actor_atomic': (
        not applicability_unknown_actor_result.valid
        and not applicability_unknown_actor_result.normalized_evidence),
    'applicability_unknown_runtime_codes': [
        finding.code for finding in applicability_unknown_runtime_result.findings],
    'applicability_unknown_runtime_atomic': (
        not applicability_unknown_runtime_result.valid
        and not applicability_unknown_runtime_result.normalized_evidence),
    'applicability_empty_valid': (
        applicability_empty_result.valid
        and not applicability_empty_result.normalized_evidence),
    'applicability_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('actor-runtime', 'runtime-applicability',
         'actor-runtime-applicability', 'execution-configurations')),
    'runtime_availability_valid': runtime_availability_result.valid,
    'runtime_availability_states': {
        observation.runtime_option_id: observation.state for observation in
        runtime_availability_result.normalized_observations},
    'runtime_inventory_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('runtimes', 'runtime-options', 'agent-runtimes')),
    'inference_inventory_valid': inference_inventory_result.valid,
    'inference_option_ids': [option.option_id for option in
                             inference_inventory_result.normalized_options],
    'inference_availability_valid': inference_availability_result.valid,
    'inference_availability_states': {
        observation.option_id: observation.state for observation in
        inference_availability_result.normalized_observations},
    'inference_inventory_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('providers', 'models', 'inference-options', 'inventory')),
    'compatibility_valid': compatibility_result.valid,
    'compatibility_edges': [
        [item.runtime_option_id, item.option_id] for item in
        compatibility_result.normalized_evidence],
    'compatibility_unknown_codes': [
        finding.code for finding in compatibility_unknown_result.findings],
    'compatibility_unknown_atomic': (
        not compatibility_unknown_result.valid
        and not compatibility_unknown_result.normalized_evidence),
    'compatibility_duplicate_codes': [
        finding.code for finding in compatibility_duplicate_result.findings],
    'compatibility_duplicate_atomic': (
        not compatibility_duplicate_result.valid
        and not compatibility_duplicate_result.normalized_evidence),
    'compatibility_empty_valid': (
        compatibility_empty_result.valid
        and not compatibility_empty_result.normalized_evidence),
    'compatibility_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('compatibility', 'runtime-inference-compatibility',
         'execution-configurations')),
    'pair_availability_valid': pair_availability_result.valid,
    'pair_availability_assessments': [
        [item.runtime_option_id, item.option_id,
         item.runtime_availability_state, item.inference_availability_state,
         item.outcome]
        for item in pair_availability_result.assessments],
    'pair_availability_invalid_codes': [
        finding.code for finding in pair_invalid_result.findings],
    'pair_availability_invalid_atomic': (
        not pair_invalid_result.valid and not pair_invalid_result.assessments),
    'pair_availability_empty_valid': (
        pair_empty_result.valid and not pair_empty_result.assessments),
    'pair_availability_schema_absent': pair_availability_schema_absent,
    'pair_availability_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('pair-availability', 'runtime-inference-pair-availability',
         'execution-configurations')),
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
    'candidate_satisfied': {
        'valid': candidate_satisfied_result.valid,
        'identity': [candidate_satisfied_result.responsibility_key,
                     candidate_satisfied_result.actor_id,
                     candidate_satisfied_result.runtime_option_id,
                     candidate_satisfied_result.option_id],
        'outcome': candidate_satisfied_result.outcome,
        'reasons': candidate_satisfied_result.reasons},
    'candidate_blocked': {
        'valid': candidate_blocked_result.valid,
        'outcome': candidate_blocked_result.outcome,
        'reasons': candidate_blocked_result.reasons},
    'candidate_unresolved': {
        'valid': candidate_unresolved_result.valid,
        'outcome': candidate_unresolved_result.outcome,
        'reasons': candidate_unresolved_result.reasons},
    'candidate_invalid_codes': [
        finding.code for finding in candidate_invalid_result.findings],
    'candidate_invalid_atomic': (
        not candidate_invalid_result.valid
        and candidate_invalid_result.responsibility_key is None
        and candidate_invalid_result.actor_id is None
        and candidate_invalid_result.runtime_option_id is None
        and candidate_invalid_result.option_id is None
        and candidate_invalid_result.outcome is None
        and not candidate_invalid_result.reasons),
    'candidate_prerequisite_schema_absent': candidate_prerequisite_schema_absent,
    'candidate_prerequisite_storage_absent': not any(
        (Path.cwd().parents[1] / '.ai' / name).exists() for name in
        ('agent-execution-candidates', 'execution-candidates',
         'candidate-assessments', 'agent-execution-candidate-prerequisites')),
    'read_only_preparation': {
        'valid': read_only_preparation_result.valid,
        'candidate_preserved': (
            read_only_preparation_result.candidate_result
            is candidate_satisfied_result),
        'operation': read_only_preparation_result.operation_id,
        'resource': read_only_preparation_result.resource,
        'environment': read_only_preparation_result.environment_id,
        'outcome': read_only_preparation_result.outcome,
        'reasons': read_only_preparation_result.reasons},
    'read_only_preparation_public_export_absent': not hasattr(
        sys.modules['engineering_orchestration'],
        'assess_read_only_execution_preparation'),
    'operation_requirement_valid': {
        'valid': operation_requirement_valid.valid,
        'same_value': operation_requirement_valid.requirement
                      is operation_requirement_value,
        'identity': operation_requirement_valid.requirement.identity},
    'operation_requirement_unsupported': {
        'valid': operation_requirement_unsupported.valid,
        'codes': [finding.code for finding in
                  operation_requirement_unsupported.findings],
        'atomic': operation_requirement_unsupported.requirement is None},
    'operation_requirement_invalid_resource': {
        'valid': operation_requirement_invalid_resource.valid,
        'codes': [finding.code for finding in
                  operation_requirement_invalid_resource.findings],
        'atomic': operation_requirement_invalid_resource.requirement is None},
    'operation_requirement_public_export_absent': not hasattr(
        sys.modules['engineering_orchestration'],
        'validate_operation_requirement'),
    'operation_vocabulary': operation_vocabulary.supported_core_operation_ids(),
    'runtime_operation_capability_present_absent': {
        'valid': capability_present_absent.valid,
        'observations': [
            [observation.runtime_option_id, observation.operation_id,
             observation.state]
            for observation in
            capability_present_absent.normalized_observations]},
    'runtime_operation_capability_unknown_missing': {
        'valid': capability_unknown_missing.valid,
        'observations': [
            [observation.runtime_option_id, observation.operation_id,
             observation.state]
            for observation in
            capability_unknown_missing.normalized_observations]},
    'runtime_operation_capability_duplicate': {
        'codes': [finding.code for finding in capability_duplicate.findings],
        'atomic': (not capability_duplicate.valid
                   and not capability_duplicate.normalized_observations)},
    'runtime_operation_capability_unknown_runtime': {
        'codes': [finding.code for finding in
                  capability_unknown_runtime.findings],
        'atomic': (not capability_unknown_runtime.valid
                   and not capability_unknown_runtime.normalized_observations)},
    'runtime_operation_capability_unsupported_operation': {
        'codes': [finding.code for finding in
                  capability_unsupported_operation.findings],
        'atomic': (not capability_unsupported_operation.valid
                   and not capability_unsupported_operation.
                   normalized_observations)},
    'runtime_operation_capability_public_export_absent': not hasattr(
        sys.modules['engineering_orchestration'],
        'validate_runtime_operation_capability'),
    'roles': [str(role_source.joinpath(name)) for name in
    ('architect.yaml', 'documentation-specialist.yaml', 'reviewer.yaml',
     'security-reviewer.yaml', 'software-engineer.yaml')],
    'schemas': [str(schema_resource(n)) for n in
    ('actor-availability.schema.json', 'actor-runtime-applicability.schema.json',
     'actor.schema.json',
     'agent-runtime-option.schema.json', 'agent-runtime-option-availability.schema.json',
     'assignment.schema.json',
     'environment-operation-permission.schema.json',
     'inference-option.schema.json', 'inference-option-availability.schema.json',
     'operation-requirement.schema.json',
     'runtime-operation-capability.schema.json',
     'runtime-inference-compatibility.schema.json',
     'role.schema.json', 'task.schema.json', 'workflow.schema.json',
     'project-manifest.schema.json')], 'sys_path': sys.path}))
"""
            evidence = json.loads(run([str(python), "-B", "-c", probe], project / "src/nested", run_env))
            authorization_probe = """
import json, os, socket, subprocess, time, urllib.request
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import engineering_orchestration
import engineering_orchestration.agent_execution_authorization_evidence as auth
from engineering_orchestration.agent_runtime_option import AgentRuntimeOptionDefinition
from engineering_orchestration.assignment import Assignment
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.schema_resources import schema_resource
from engineering_orchestration.workflow_catalog import WorkflowCatalog, WorkflowDefinition, WorkflowStage
K = auth.AgentExecutionAuthorizationAuthorityKind
S = auth.AgentExecutionAuthorizationState
E = auth.AgentExecutionAuthorizationEvidence
task = {'id': 'LOCAL-123', 'workflow': 'external-flow'}
workflows = WorkflowCatalog(Path('unused'), {'external-flow': WorkflowDefinition(
    'external-flow', 'External', 'Synthetic installed probe',
    [WorkflowStage('external-stage', 'Synthetic stage', ['software-engineer'])])})
roles = RoleCatalog(None, {'software-engineer': {
    'id': 'software-engineer', 'required_capabilities': ['implementation']}})
agent = {'id': 'installed-agent', 'kind': 'agent',
         'competencies': ['implementation']}
human = {'id': 'installed-human', 'kind': 'human',
         'competencies': ['implementation']}
binding = Assignment('LOCAL-123', 'external-flow', 'external-stage',
                     'software-engineer', 'installed-agent')
human_binding = Assignment('LOCAL-123', 'external-flow', 'external-stage',
                           'software-engineer', 'installed-human')
runtimes = [AgentRuntimeOptionDefinition('installed-runtime-primary')]
options = [InferenceOptionDefinition(
    'installed-primary', 'provider::installed', 'model::installed')]
authorization_schema = str(schema_resource(
    'agent-execution-authorization-evidence.schema.json'))
def item(state=S.GRANTED, kind=K.HUMAN, actor_id='installed-agent',
         authority_id='human::installed-reviewer',
         provenance='approval::installed'):
    return E('LOCAL-123', 'external-flow', 'external-stage',
             'software-engineer', actor_id, 'installed-runtime-primary',
             'installed-primary', 'installed-environment',
             'repository_file_read', 'synthetic/install-authorization.txt',
             kind, authority_id, provenance, state)
def validate(values, assignments=None, actors=None):
    return auth.validate_agent_execution_authorization_evidence(
        values, assignments or [binding], task, workflows, roles,
        actors or [agent], runtimes, options, 'installed-environment')
blocked = AssertionError('authorization validation must remain pure')
guards = (
    patch('builtins.open', side_effect=blocked),
    patch.object(Path, 'open', side_effect=blocked),
    patch.object(Path, 'read_text', side_effect=blocked),
    patch.object(Path, 'read_bytes', side_effect=blocked),
    patch.object(Path, 'stat', side_effect=blocked),
    patch.object(Path, 'resolve', side_effect=blocked),
    patch.object(Path, 'iterdir', side_effect=blocked),
    patch.object(Path, 'glob', side_effect=blocked),
    patch.object(Path, 'rglob', side_effect=blocked),
    patch.object(os, 'stat', side_effect=blocked),
    patch.object(os, 'access', side_effect=blocked),
    patch.object(os, 'listdir', side_effect=blocked),
    patch.object(os, 'scandir', side_effect=blocked),
    patch.object(os, 'getenv', side_effect=blocked),
    patch.object(subprocess, 'run', side_effect=blocked),
    patch.object(subprocess, 'Popen', side_effect=blocked),
    patch.object(socket, 'create_connection', side_effect=blocked),
    patch.object(socket, 'getaddrinfo', side_effect=blocked),
    patch.object(urllib.request, 'urlopen', side_effect=blocked),
    patch.object(time, 'time', side_effect=blocked),
    patch.object(time, 'monotonic', side_effect=blocked),
)
with ExitStack() as stack:
    for guard in guards:
        stack.enter_context(guard)
    value = item()
    valid = validate([value])
    empty = validate([])
    duplicate = validate([value, value])
    conflict = validate([value, item(state=S.DENIED)])
    multi = validate([value, item(
        kind=K.POLICY, authority_id='policy::installed',
        provenance='policy-evaluation::installed')])
    human_result = validate(
        [item(actor_id='installed-human')], [human_binding], [human])
print(json.dumps({
    'agent_execution_authorization_evidence_module': auth.__file__,
    'agent_execution_authorization_schema': authorization_schema,
    'agent_execution_authorization_authority_kinds': [x.value for x in K],
    'agent_execution_authorization_states': [x.value for x in S],
    'agent_execution_authorization_valid': {
        'valid': valid.valid,
        'evidence': [[x.task_id, x.workflow_id, x.stage_id, x.role_id,
                      x.actor_id, x.runtime_option_id, x.option_id,
                      x.environment_id, x.operation_id, x.resource,
                      x.authority_kind, x.authority_id,
                      x.provenance_reference, x.state]
                     for x in valid.normalized_evidence]},
    'agent_execution_authorization_empty': {
        'valid': empty.valid, 'evidence': list(empty.normalized_evidence)},
    'agent_execution_authorization_duplicate': {
        'codes': [x.code for x in duplicate.findings],
        'atomic': not duplicate.valid and not duplicate.normalized_evidence},
    'agent_execution_authorization_conflict': {
        'codes': [x.code for x in conflict.findings],
        'atomic': not conflict.valid and not conflict.normalized_evidence},
    'agent_execution_authorization_multi_authority': {
        'codes': [x.code for x in multi.findings],
        'atomic': not multi.valid and not multi.normalized_evidence},
    'agent_execution_authorization_human_actor': {
        'codes': [x.code for x in human_result.findings],
        'atomic': not human_result.valid and not human_result.normalized_evidence},
    'agent_execution_authorization_public_export_absent': not hasattr(
        engineering_orchestration,
        'validate_agent_execution_authorization_evidence'),
}))
"""
            evidence.update(json.loads(run(
                [str(python), "-B", "-c", authorization_probe],
                project / "src/nested",
                run_env,
            )))
            evidence["schemas"].append(
                evidence["agent_execution_authorization_schema"]
            )
            permission_probe = """
import json, os, socket, subprocess, sys, time, urllib.request
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import engineering_orchestration
import engineering_orchestration._repository_resource as repository_resource
import engineering_orchestration.environment_operation_permission as permission
from engineering_orchestration.agent_runtime_option import AgentRuntimeOptionDefinition
P = permission.EnvironmentOperationPermissionObservation
S = permission.EnvironmentOperationPermissionState
options = [AgentRuntimeOptionDefinition('installed-runtime-primary'),
           AgentRuntimeOptionDefinition('installed-runtime-secondary')]
def validate(observations):
    return permission.validate_environment_operation_permission(
        observations, options, 'installed-environment')
blocked = AssertionError('permission validation must remain pure')
guards = (
    patch('builtins.open', side_effect=blocked),
    patch.object(Path, 'open', side_effect=blocked),
    patch.object(Path, 'read_text', side_effect=blocked),
    patch.object(Path, 'read_bytes', side_effect=blocked),
    patch.object(Path, 'stat', side_effect=blocked),
    patch.object(Path, 'resolve', side_effect=blocked),
    patch.object(Path, 'iterdir', side_effect=blocked),
    patch.object(Path, 'glob', side_effect=blocked),
    patch.object(Path, 'rglob', side_effect=blocked),
    patch.object(os, 'stat', side_effect=blocked),
    patch.object(os, 'access', side_effect=blocked),
    patch.object(os, 'listdir', side_effect=blocked),
    patch.object(os, 'scandir', side_effect=blocked),
    patch.object(os, 'getenv', side_effect=blocked),
    patch.object(os, 'chmod', side_effect=blocked),
    patch.object(subprocess, 'run', side_effect=blocked),
    patch.object(subprocess, 'Popen', side_effect=blocked),
    patch.object(socket, 'create_connection', side_effect=blocked),
    patch.object(socket, 'getaddrinfo', side_effect=blocked),
    patch.object(urllib.request, 'urlopen', side_effect=blocked),
    patch.object(time, 'time', side_effect=blocked),
    patch.object(time, 'monotonic', side_effect=blocked),
)
with ExitStack() as stack:
    for guard in guards:
        stack.enter_context(guard)
    valid = validate([
        P('installed-runtime-secondary', 'installed-environment',
          'repository_file_read', 'synthetic/unknown.txt', S.UNKNOWN),
        P('installed-runtime-primary', 'installed-environment',
          'repository_file_read', 'synthetic/denied.txt', S.DENIED),
        P('installed-runtime-primary', 'installed-environment',
          'repository_file_read', 'synthetic/allowed.txt', S.ALLOWED),
    ])
    mismatch = validate([
        P('installed-runtime-primary', 'different-environment',
          'repository_file_read', 'synthetic/mismatch.txt', S.ALLOWED)])
    duplicate_value = P(
        'installed-runtime-primary', 'installed-environment',
        'repository_file_read', 'synthetic/duplicate.txt', S.DENIED)
    duplicate = validate([duplicate_value, duplicate_value])
    pairs = ((S.ALLOWED, S.DENIED), (S.DENIED, S.ALLOWED),
             (S.ALLOWED, S.UNKNOWN), (S.UNKNOWN, S.ALLOWED),
             (S.DENIED, S.UNKNOWN), (S.UNKNOWN, S.DENIED))
    conflicts = [validate([
        P('installed-runtime-primary', 'installed-environment',
          'repository_file_read', 'synthetic/conflict.txt', left),
        P('installed-runtime-primary', 'installed-environment',
          'repository_file_read', 'synthetic/conflict.txt', right),
    ]) for left, right in pairs]
    invalid_resource = validate([
        P('installed-runtime-primary', 'installed-environment',
          'repository_file_read', 'synthetic/../invalid.txt', S.ALLOWED)])
print(json.dumps({
    'repository_resource_module': repository_resource.__file__,
    'environment_operation_permission_module': permission.__file__,
    'environment_operation_permission_states': [state.value for state in S],
    'environment_operation_permission_allowed_denied_unknown': {
        'valid': valid.valid,
        'observations': [[item.runtime_option_id, item.environment_id,
                          item.operation_id, item.resource, item.state]
                         for item in valid.normalized_observations]},
    'environment_operation_permission_environment_mismatch': {
        'codes': [item.code for item in mismatch.findings],
        'atomic': not mismatch.valid and not mismatch.normalized_observations},
    'environment_operation_permission_identical_duplicate': {
        'codes': [item.code for item in duplicate.findings],
        'atomic': not duplicate.valid and not duplicate.normalized_observations},
    'environment_operation_permission_conflicts': [
        {'codes': [item.code for item in result.findings],
         'atomic': not result.valid and not result.normalized_observations}
        for result in conflicts],
    'environment_operation_permission_conflicts_deterministic': all(
        result == conflicts[0] for result in conflicts),
    'environment_operation_permission_invalid_resource': {
        'codes': [item.code for item in invalid_resource.findings],
        'atomic': (not invalid_resource.valid
                   and not invalid_resource.normalized_observations)},
    'environment_operation_permission_public_export_absent': not hasattr(
        engineering_orchestration, 'validate_environment_operation_permission'),
}))
"""
            evidence.update(json.loads(run(
                [str(python), "-B", "-c", permission_probe],
                project / "src/nested",
                run_env,
            )))
            action_prerequisite_probe = """
import json, os, socket, subprocess, time, urllib.request
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
import engineering_orchestration
import engineering_orchestration.agent_action_prerequisite as action
from engineering_orchestration.agent_execution_authorization_evidence import AgentExecutionAuthorizationAuthorityKind as AuthorityKind, AgentExecutionAuthorizationEvidence as AuthorizationEvidence, AgentExecutionAuthorizationState as AuthorizationState, AgentExecutionAuthorizationValidationResult as AuthorizationResult
from engineering_orchestration.agent_execution_candidate_prerequisite import AgentExecutionCandidatePrerequisiteOutcome as CandidateOutcome, AgentExecutionCandidatePrerequisiteReason as CandidateReason, AgentExecutionCandidatePrerequisiteResult as CandidateResult
from engineering_orchestration.environment_operation_permission import EnvironmentOperationPermissionObservation as PermissionObservation, EnvironmentOperationPermissionState as PermissionState, EnvironmentOperationPermissionValidationResult as PermissionResult
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.runtime_operation_capability import RuntimeOperationCapabilityObservation as CapabilityObservation, RuntimeOperationCapabilityState as CapabilityState, RuntimeOperationCapabilityValidationResult as CapabilityResult
candidate = CandidateResult(
    True, (), ('LOCAL-123', 'external-flow', 'external-stage',
               'software-engineer'), 'installed-agent',
    'installed-runtime-primary', 'installed-primary',
    CandidateOutcome.SATISFIED,
    (CandidateReason.ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,))
requirement = OperationRequirement(
    'repository_file_read', 'synthetic/install-action.txt')
capability = CapabilityResult(True, (), (
    CapabilityObservation('installed-runtime-primary',
                          'repository_file_read', CapabilityState.PRESENT),))
permission = PermissionResult(True, (), (
    PermissionObservation('installed-runtime-primary',
                          'installed-environment', 'repository_file_read',
                          'synthetic/install-action.txt',
                          PermissionState.ALLOWED),))
def authorization(state):
    return AuthorizationResult(True, (), (
        AuthorizationEvidence(
            'LOCAL-123', 'external-flow', 'external-stage',
            'software-engineer', 'installed-agent',
            'installed-runtime-primary', 'installed-primary',
            'installed-environment', 'repository_file_read',
            'synthetic/install-action.txt', AuthorityKind.HUMAN,
            'human::installed-reviewer', 'approval::installed', state),))
blocked = AssertionError('action prerequisite assessment must remain pure')
guards = (
    patch('builtins.open', side_effect=blocked),
    patch.object(Path, 'open', side_effect=blocked),
    patch.object(Path, 'read_text', side_effect=blocked),
    patch.object(Path, 'read_bytes', side_effect=blocked),
    patch.object(Path, 'stat', side_effect=blocked),
    patch.object(Path, 'resolve', side_effect=blocked),
    patch.object(Path, 'iterdir', side_effect=blocked),
    patch.object(Path, 'glob', side_effect=blocked),
    patch.object(Path, 'rglob', side_effect=blocked),
    patch.object(os, 'stat', side_effect=blocked),
    patch.object(os, 'access', side_effect=blocked),
    patch.object(os, 'listdir', side_effect=blocked),
    patch.object(os, 'scandir', side_effect=blocked),
    patch.object(os, 'getenv', side_effect=blocked),
    patch.object(subprocess, 'run', side_effect=blocked),
    patch.object(subprocess, 'Popen', side_effect=blocked),
    patch.object(socket, 'create_connection', side_effect=blocked),
    patch.object(socket, 'getaddrinfo', side_effect=blocked),
    patch.object(urllib.request, 'urlopen', side_effect=blocked),
    patch.object(time, 'time', side_effect=blocked),
    patch.object(time, 'monotonic', side_effect=blocked),
)
with ExitStack() as stack:
    for guard in guards:
        stack.enter_context(guard)
    satisfied = action.assess_agent_action_prerequisites(
        candidate, requirement, capability, permission,
        authorization(AuthorizationState.GRANTED),
        environment_id='installed-environment')
    denied = action.assess_agent_action_prerequisites(
        candidate, requirement, capability, permission,
        authorization(AuthorizationState.DENIED),
        environment_id='installed-environment')
    missing = action.assess_agent_action_prerequisites(
        candidate, requirement, capability, permission,
        AuthorizationResult(True, (), ()),
        environment_id='installed-environment')
def compact(result):
    return {
        'valid': result.valid,
        'identity': [list(result.responsibility_key), result.actor_id,
                     result.runtime_option_id, result.option_id,
                     result.environment_id, result.operation_id,
                     result.resource],
        'outcome': result.outcome,
        'reasons': list(result.reasons),
    }
print(json.dumps({
    'agent_action_prerequisite_module': action.__file__,
    'agent_action_prerequisite_outcomes': [item.value for item in
                                           action.AgentActionPrerequisiteOutcome],
    'agent_action_prerequisite_reasons': [item.value for item in
                                          action.AgentActionPrerequisiteReason],
    'agent_action_prerequisite_satisfied': compact(satisfied),
    'agent_action_prerequisite_denied': compact(denied),
    'agent_action_prerequisite_missing': compact(missing),
    'agent_action_prerequisite_public_export_absent': not hasattr(
        engineering_orchestration, 'assess_agent_action_prerequisites'),
}))
"""
            evidence.update(json.loads(run(
                [str(python), "-B", "-c", action_prerequisite_probe],
                project / "src/nested",
                run_env,
            )))
            contract_probe = """
import json, os, socket, subprocess, time, urllib.request
from contextlib import ExitStack
from dataclasses import asdict, fields, replace
from pathlib import Path
from unittest.mock import patch
import engineering_orchestration
import engineering_orchestration.agent_action_prerequisite as action
import engineering_orchestration.agent_execution_contract as contract
from engineering_orchestration.agent_action_prerequisite import AgentActionPrerequisiteOutcome as Outcome, AgentActionPrerequisiteReason as Reason, AgentActionPrerequisiteResult as PrerequisiteResult
from engineering_orchestration.operation_requirement import OperationRequirement, validate_operation_requirement
from engineering_orchestration.schema_resources import load_validator, schema_resource
def prerequisite(outcome, reasons):
    return PrerequisiteResult(
        True, (), ('LOCAL-123', 'external-flow', 'external-stage',
                   'software-engineer'), 'installed-agent',
        'installed-runtime-primary', 'installed-primary',
        'installed-environment', 'repository_file_read',
        'synthetic/install-contract.txt', outcome, reasons)
satisfied = prerequisite(
    Outcome.SATISFIED,
    (Reason.ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED,))
blocked_result = prerequisite(
    Outcome.BLOCKED, (Reason.AGENT_EXECUTION_AUTHORIZATION_DENIED,))
unresolved_result = prerequisite(
    Outcome.UNRESOLVED, (Reason.AGENT_EXECUTION_AUTHORIZATION_MISSING,))
contract_schema_resource = schema_resource('agent-execution-contract.schema.json')
contract_schema_path = str(contract_schema_resource)
contract_validator = load_validator('agent-execution-contract.schema.json')
blocked_io = AssertionError('contract preparation and validation must remain pure')
blocked_invocation = AssertionError('contract preparation must not reassess or invoke')
guards = (
    patch('builtins.open', side_effect=blocked_io),
    patch.object(Path, 'open', side_effect=blocked_io),
    patch.object(Path, 'read_text', side_effect=blocked_io),
    patch.object(Path, 'read_bytes', side_effect=blocked_io),
    patch.object(Path, 'stat', side_effect=blocked_io),
    patch.object(Path, 'resolve', side_effect=blocked_io),
    patch.object(Path, 'iterdir', side_effect=blocked_io),
    patch.object(Path, 'glob', side_effect=blocked_io),
    patch.object(Path, 'rglob', side_effect=blocked_io),
    patch.object(os, 'stat', side_effect=blocked_io),
    patch.object(os, 'access', side_effect=blocked_io),
    patch.object(os, 'listdir', side_effect=blocked_io),
    patch.object(os, 'scandir', side_effect=blocked_io),
    patch.object(os, 'getenv', side_effect=blocked_io),
    patch.object(subprocess, 'run', side_effect=blocked_io),
    patch.object(subprocess, 'Popen', side_effect=blocked_io),
    patch.object(socket, 'create_connection', side_effect=blocked_io),
    patch.object(socket, 'getaddrinfo', side_effect=blocked_io),
    patch.object(urllib.request, 'urlopen', side_effect=blocked_io),
    patch.object(time, 'time', side_effect=blocked_io),
    patch.object(time, 'monotonic', side_effect=blocked_io),
    patch.object(action, 'assess_agent_action_prerequisites',
                 side_effect=blocked_invocation),
)
with ExitStack() as stack:
    for guard in guards:
        stack.enter_context(guard)
    prepared_by_mode = {
        mode: contract.prepare_agent_execution_contract(
            satisfied, execution_mode=mode)
        for mode in ('lite', 'standard', 'deep', 'critical')
    }
    repeated = contract.prepare_agent_execution_contract(
        satisfied, execution_mode='deep')
    direct_value = contract.AgentExecutionContract(
        'LOCAL-123', 'external-flow', 'external-stage',
        'software-engineer', 'installed-agent',
        'installed-runtime-primary', 'installed-primary',
        'installed-environment', 'repository_file_read',
        'synthetic/install-contract.txt', 'deep')
    intrinsic = contract.validate_agent_execution_contract(direct_value)
    invalid_identity = contract.validate_agent_execution_contract(
        replace(direct_value, stage_id=''))
    unsupported_operation = contract.validate_agent_execution_contract(
        replace(direct_value, operation_id='repository_file_write'))
    invalid_resource = contract.validate_agent_execution_contract(
        replace(direct_value, resource='synthetic/../install-contract.txt'))
    operation_reference = validate_operation_requirement(OperationRequirement(
        'repository_file_write', 'synthetic/install-contract.txt'))
    resource_reference = validate_operation_requirement(OperationRequirement(
        'repository_file_read', 'synthetic/../install-contract.txt'))
    blocked = contract.prepare_agent_execution_contract(
        blocked_result, execution_mode='deep')
    unresolved = contract.prepare_agent_execution_contract(
        unresolved_result, execution_mode='deep')
    schema_accepts_modes = True
    for result in prepared_by_mode.values():
        contract_validator.validate(asdict(result.contract))
    roundtrip_value = contract.AgentExecutionContract(**json.loads(
        json.dumps(asdict(prepared_by_mode['deep'].contract))))
    roundtrip = contract.validate_agent_execution_contract(roundtrip_value)
print(json.dumps({
    'agent_execution_contract_module': contract.__file__,
    'agent_execution_contract_schema': contract_schema_path,
    'agent_execution_contract_fields': [
        item.name for item in fields(contract.AgentExecutionContract)],
    'agent_execution_contract_prepared_modes': {
        mode: {
            'valid': result.valid,
            'findings': [item.code for item in result.findings],
            'value': asdict(result.contract) if result.contract else None,
        }
        for mode, result in prepared_by_mode.items()
    },
    'agent_execution_contract_repeat_equal': (
        repeated == prepared_by_mode['deep']),
    'agent_execution_contract_intrinsic': {
        'valid': intrinsic.valid,
        'same_value': intrinsic.contract is direct_value,
        'findings': [item.code for item in intrinsic.findings],
    },
    'agent_execution_contract_invalid_identity': {
        'codes': [item.code for item in invalid_identity.findings],
        'atomic': (not invalid_identity.valid
                   and invalid_identity.contract is None),
    },
    'agent_execution_contract_blocked': {
        'codes': [item.code for item in blocked.findings],
        'atomic': not blocked.valid and blocked.contract is None,
    },
    'agent_execution_contract_unresolved': {
        'codes': [item.code for item in unresolved.findings],
        'atomic': not unresolved.valid and unresolved.contract is None,
    },
    'agent_execution_contract_operation_parity': {
        'contract_codes': [item.code for item in unsupported_operation.findings],
        'requirement_codes': [item.code for item in operation_reference.findings],
        'atomic': (not unsupported_operation.valid
                   and unsupported_operation.contract is None),
    },
    'agent_execution_contract_resource_parity': {
        'contract_codes': [item.code for item in invalid_resource.findings],
        'requirement_codes': [item.code for item in resource_reference.findings],
        'atomic': (not invalid_resource.valid
                   and invalid_resource.contract is None),
    },
    'agent_execution_contract_schema_accepts_modes': schema_accepts_modes,
    'agent_execution_contract_roundtrip': {
        'valid': roundtrip.valid,
        'equal': roundtrip.contract == prepared_by_mode['deep'].contract,
    },
    'agent_execution_contract_pure_noninvoking_probe': True,
    'agent_execution_contract_public_export_absent': all(
        not hasattr(engineering_orchestration, name) for name in (
            'AgentExecutionContract',
            'prepare_agent_execution_contract',
            'validate_agent_execution_contract')),
}))
"""
            evidence.update(json.loads(run(
                [str(python), "-B", "-c", contract_probe],
                project / "src/nested",
                run_env,
            )))
            evidence["schemas"].append(
                evidence["agent_execution_contract_schema"]
            )
            print(f"{mode.upper()} IMPORT/RESOURCE EVIDENCE: {json.dumps(evidence)}", flush=True)
            if mode == "normal":
                require(Path(evidence["module"]).resolve().is_relative_to(environment),
                        "Normal install imports leaked to source")
                require(Path(evidence["execution_mode_module"]).resolve().is_relative_to(environment),
                        "Normal Execution Mode import leaked to source")
                require(Path(evidence["runner_module"]).resolve().is_relative_to(environment),
                        "Normal runner import leaked to source")
                require(Path(evidence["availability_module"]).resolve().is_relative_to(environment),
                        "Normal Actor Availability validator import leaked to source")
                require(Path(evidence["actor_runtime_applicability_module"]).resolve().is_relative_to(environment),
                        "Normal Actor-to-Runtime Applicability validator import leaked to source")
                require(Path(evidence["runtime_option_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Runtime Option validator import leaked to source")
                require(Path(evidence["runtime_option_availability_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Runtime Option Availability validator import leaked to source")
                require(Path(evidence["inference_option_module"]).resolve().is_relative_to(environment),
                        "Normal Inference Option validator import leaked to source")
                require(Path(evidence["inference_option_availability_module"]).resolve().is_relative_to(environment),
                        "Normal Inference Option Availability validator import leaked to source")
                require(Path(evidence["runtime_inference_compatibility_module"]).resolve().is_relative_to(environment),
                        "Normal Runtime-to-Inference Compatibility validator import leaked to source")
                require(Path(evidence["runtime_inference_pair_availability_module"]).resolve().is_relative_to(environment),
                        "Normal Runtime-to-Inference Pair Availability import leaked to source")
                require(Path(evidence["candidate_prerequisite_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Execution Candidate Prerequisite import leaked to source")
                require(Path(evidence["agent_execution_authorization_evidence_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Execution Authorization Evidence import leaked to source")
                require(Path(evidence["agent_action_prerequisite_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Action Prerequisite import leaked to source")
                require(Path(evidence["agent_execution_contract_module"]).resolve().is_relative_to(environment),
                        "Normal Agent Execution Contract import leaked to source")
                require(Path(evidence["read_only_execution_preparation_module"]).resolve().is_relative_to(environment),
                        "Normal read-only execution preparation import leaked to source")
                require(Path(evidence["operation_requirement_module"]).resolve().is_relative_to(environment),
                        "Normal Operation Requirement import leaked to source")
                require(Path(evidence["operation_vocabulary_module"]).resolve().is_relative_to(environment),
                        "Normal Core operation vocabulary import leaked to source")
                require(Path(evidence["repository_resource_module"]).resolve().is_relative_to(environment),
                        "Normal repository-resource helper import leaked to source")
                require(Path(evidence["environment_operation_permission_module"]).resolve().is_relative_to(environment),
                        "Normal Environment Operation Permission import leaked to source")
                require(Path(evidence["runtime_operation_capability_module"]).resolve().is_relative_to(environment),
                        "Normal Runtime Operation Capability import leaked to source")
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
            require(evidence["execution_mode_order"] == ["lite", "standard", "deep", "critical"]
                    and evidence["critical_satisfies_deep"],
                    "Installed Execution Mode semantics are incorrect")
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
            require(evidence["runtime_inventory_valid"]
                    and evidence["runtime_option_ids"] == [
                        "installed-runtime-primary", "installed-runtime-secondary"],
                    "Installed Agent Runtime Option inventory validation failed")
            require(evidence["applicability_valid"]
                    and evidence["applicability_edges"] == [
                        ["installed-agent", "installed-runtime-primary"],
                        ["installed-agent", "installed-runtime-secondary"]],
                    "Installed Actor-to-Runtime applicability validation failed")
            require(evidence["applicability_duplicate_codes"] == [
                        "duplicate_actor_runtime_applicability"]
                    and evidence["applicability_duplicate_atomic"],
                    "Installed applicability duplicate rejection failed")
            require(evidence["applicability_human_codes"] == [
                        "actor_runtime_applicability_requires_agent_actor"]
                    and evidence["applicability_human_atomic"],
                    "Installed applicability Human endpoint rejection failed")
            require(evidence["applicability_unknown_actor_codes"] == [
                        "actor_not_found"]
                    and evidence["applicability_unknown_actor_atomic"],
                    "Installed applicability unknown Actor rejection failed")
            require(evidence["applicability_unknown_runtime_codes"] == [
                        "agent_runtime_option_not_found"]
                    and evidence["applicability_unknown_runtime_atomic"],
                    "Installed applicability unknown Runtime rejection failed")
            require(evidence["applicability_empty_valid"],
                    "Installed empty applicability relation should be valid")
            require(evidence["applicability_storage_absent"],
                    "Applicability validation unexpectedly required project storage")
            require(evidence["runtime_availability_valid"]
                    and evidence["runtime_availability_states"] == {
                        "installed-runtime-primary": "available",
                        "installed-runtime-secondary": "unknown"},
                    "Installed Agent Runtime Option Availability normalization failed")
            require(evidence["runtime_inventory_storage_absent"],
                    "Agent Runtime Option validation unexpectedly required project storage")
            require(evidence["inference_inventory_valid"]
                    and evidence["inference_option_ids"] == [
                        "installed-primary", "installed-secondary"],
                    "Installed Inference Option inventory validation failed")
            require(evidence["inference_availability_valid"]
                    and evidence["inference_availability_states"] == {
                        "installed-primary": "available",
                        "installed-secondary": "unknown"},
                    "Installed Inference Option Availability normalization failed")
            require(evidence["inference_inventory_storage_absent"],
                    "Inference Option validation unexpectedly required project storage")
            require(evidence["compatibility_valid"]
                    and evidence["compatibility_edges"] == [
                        ["installed-runtime-primary", "installed-primary"],
                        ["installed-runtime-primary", "installed-secondary"],
                        ["installed-runtime-secondary", "installed-primary"]],
                    "Installed Runtime-to-Inference compatibility validation failed")
            require(evidence["compatibility_unknown_codes"] == [
                        "inference_option_not_found"]
                    and evidence["compatibility_unknown_atomic"],
                    "Installed compatibility unknown-reference rejection failed")
            require(evidence["compatibility_duplicate_codes"] == [
                        "duplicate_runtime_inference_compatibility"]
                    and evidence["compatibility_duplicate_atomic"],
                    "Installed compatibility duplicate rejection failed")
            require(evidence["compatibility_empty_valid"],
                    "Installed empty compatibility relation should be valid")
            require(evidence["compatibility_storage_absent"],
                    "Compatibility validation unexpectedly required project storage")
            require(evidence["pair_availability_valid"]
                    and evidence["pair_availability_assessments"] == [
                        ["installed-runtime-primary", "installed-primary",
                         "available", "available", "established"],
                        ["installed-runtime-primary", "installed-secondary",
                         "available", "unknown", "unresolved"],
                        ["installed-runtime-secondary", "installed-primary",
                         "unavailable", "available", "blocked"]],
                    "Installed pair availability outcomes are incorrect")
            require(evidence["pair_availability_invalid_codes"] == [
                        "duplicate_agent_runtime_option_availability",
                        "duplicate_inference_option_availability"]
                    and evidence["pair_availability_invalid_atomic"],
                    "Installed pair availability diagnostic composition failed")
            require(evidence["pair_availability_empty_valid"],
                    "Installed empty pair availability relation should be valid")
            require(evidence["pair_availability_schema_absent"],
                    "Pair Availability Assessment unexpectedly added a schema resource")
            require(evidence["pair_availability_storage_absent"],
                    "Pair Availability Assessment unexpectedly required project storage")
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
            require(evidence["candidate_satisfied"] == {
                        "valid": True,
                        "identity": [["LOCAL-123", "external-flow", "external-stage",
                                      "software-engineer"], "installed-agent",
                                     "installed-runtime-primary", "installed-primary"],
                        "outcome": "satisfied",
                        "reasons": [
                            "all_currently_modeled_prerequisites_satisfied"]},
                    "Installed Agent candidate satisfied assessment failed")
            require(evidence["candidate_blocked"] == {
                        "valid": True, "outcome": "blocked",
                        "reasons": ["actor_unavailable"]},
                    "Installed Agent candidate blocked assessment failed")
            require(evidence["candidate_unresolved"] == {
                        "valid": True, "outcome": "unresolved",
                        "reasons": [
                            "runtime_inference_compatibility_not_supplied"]},
                    "Installed Agent candidate unresolved assessment failed")
            require(evidence["candidate_invalid_codes"] == [
                        "duplicate_actor_availability"]
                    and evidence["candidate_invalid_atomic"],
                    "Installed Agent candidate invalid assessment was not atomic")
            require(evidence["candidate_prerequisite_schema_absent"],
                    "Agent candidate prerequisite assessment unexpectedly added a schema")
            require(evidence["candidate_prerequisite_storage_absent"],
                    "Agent candidate prerequisite assessment unexpectedly required storage")
            require(evidence["read_only_preparation"] == {
                        "valid": True,
                        "candidate_preserved": True,
                        "operation": "repository_file_read",
                        "resource": "workflows/README.md",
                        "environment": "installed-environment",
                        "outcome": "potentially_executable",
                        "reasons": ["all_preparation_evidence_positive"]},
                    "Installed read-only execution preparation probe failed")
            require(evidence["read_only_preparation_public_export_absent"],
                    "Read-only execution preparation unexpectedly became public")
            require(evidence["agent_execution_authorization_authority_kinds"] == [
                        "human", "policy"],
                    "Installed authorization authority kinds differ")
            require(evidence["agent_execution_authorization_states"] == [
                        "granted", "denied"],
                    "Installed authorization states differ")
            require(evidence["agent_execution_authorization_valid"] == {
                        "valid": True,
                        "evidence": [[
                            "LOCAL-123", "external-flow", "external-stage",
                            "software-engineer", "installed-agent",
                            "installed-runtime-primary", "installed-primary",
                            "installed-environment", "repository_file_read",
                            "synthetic/install-authorization.txt", "human",
                            "human::installed-reviewer", "approval::installed",
                            "granted"]]},
                    "Installed authorization valid probe failed")
            require(evidence["agent_execution_authorization_empty"] == {
                        "valid": True, "evidence": []},
                    "Installed authorization absence probe failed")
            require(evidence["agent_execution_authorization_duplicate"] == {
                        "codes": [
                            "duplicate_agent_execution_authorization_evidence"
                        ],
                        "atomic": True},
                    "Installed authorization duplicate rejection failed")
            require(evidence["agent_execution_authorization_conflict"] == {
                        "codes": [
                            "conflicting_agent_execution_authorization_evidence"
                        ],
                        "atomic": True},
                    "Installed authorization conflict rejection failed")
            require(
                evidence["agent_execution_authorization_multi_authority"] == {
                    "codes": [
                        "unsupported_multi_authority_"
                        "agent_execution_authorization_evidence"
                    ],
                    "atomic": True,
                },
                "Installed authorization multi-authority rejection failed",
            )
            require(evidence["agent_execution_authorization_human_actor"] == {
                        "codes": [
                            "agent_execution_authorization_not_applicable_to_"
                            "human_actor"
                        ],
                        "atomic": True},
                    "Installed authorization Human Actor boundary failed")
            require(evidence["agent_execution_authorization_public_export_absent"],
                    "Authorization Evidence unexpectedly gained a root export")
            require(evidence["agent_action_prerequisite_outcomes"] == [
                        "satisfied", "blocked", "unresolved"],
                    "Installed action prerequisite outcomes differ")
            require(evidence["agent_action_prerequisite_reasons"] == [
                        "candidate_prerequisites_blocked",
                        "candidate_prerequisites_unresolved",
                        "runtime_operation_capability_absent",
                        "runtime_operation_capability_unknown",
                        "environment_operation_permission_denied",
                        "environment_operation_permission_unknown",
                        "agent_execution_authorization_denied",
                        "agent_execution_authorization_missing",
                        "all_currently_modeled_action_prerequisites_satisfied"],
                    "Installed action prerequisite reasons differ")
            require(evidence["agent_action_prerequisite_satisfied"] == {
                        "valid": True,
                        "identity": [["LOCAL-123", "external-flow",
                                      "external-stage", "software-engineer"],
                                     "installed-agent",
                                     "installed-runtime-primary",
                                     "installed-primary",
                                     "installed-environment",
                                     "repository_file_read",
                                     "synthetic/install-action.txt"],
                        "outcome": "satisfied",
                        "reasons": [
                            "all_currently_modeled_action_prerequisites_satisfied"]},
                    "Installed action prerequisite satisfied probe failed")
            require(evidence["agent_action_prerequisite_denied"]["outcome"]
                    == "blocked"
                    and evidence["agent_action_prerequisite_denied"]["reasons"]
                    == ["agent_execution_authorization_denied"],
                    "Installed action prerequisite denied probe failed")
            require(evidence["agent_action_prerequisite_missing"]["outcome"]
                    == "unresolved"
                    and evidence["agent_action_prerequisite_missing"]["reasons"]
                    == ["agent_execution_authorization_missing"],
                    "Installed action prerequisite missing probe failed")
            require(evidence["agent_action_prerequisite_public_export_absent"],
                    "Agent Action Prerequisite unexpectedly gained a root export")
            contract_field_names = [
                "task_id", "workflow_id", "stage_id", "role_id", "actor_id",
                "runtime_option_id", "option_id", "environment_id",
                "operation_id", "resource", "execution_mode",
            ]
            require(
                evidence["agent_execution_contract_fields"]
                == contract_field_names,
                "Installed Agent Execution Contract fields differ",
            )
            prepared_modes = evidence[
                "agent_execution_contract_prepared_modes"
            ]
            require(
                list(prepared_modes) == ["lite", "standard", "deep", "critical"]
                and all(
                    item["valid"]
                    and item["findings"] == []
                    and item["value"]["execution_mode"] == mode_name
                    and list(item["value"]) == contract_field_names
                    for mode_name, item in prepared_modes.items()
                ),
                "Installed Agent Execution Contract mode preparation failed",
            )
            require(
                evidence["agent_execution_contract_repeat_equal"],
                "Repeated Agent Execution Contract preparation differed",
            )
            require(
                evidence["agent_execution_contract_intrinsic"] == {
                    "valid": True, "same_value": True, "findings": []},
                "Installed Agent Execution Contract intrinsic validation failed",
            )
            require(
                evidence["agent_execution_contract_invalid_identity"] == {
                    "codes": ["agent_execution_contract_stage_id_invalid"],
                    "atomic": True,
                },
                "Installed Agent Execution Contract identity rejection failed",
            )
            require(
                evidence["agent_execution_contract_blocked"] == {
                    "codes": ["agent_execution_contract_prerequisites_blocked"],
                    "atomic": True,
                },
                "Installed Agent Execution Contract blocked rejection failed",
            )
            require(
                evidence["agent_execution_contract_unresolved"] == {
                    "codes": [
                        "agent_execution_contract_prerequisites_unresolved"
                    ],
                    "atomic": True,
                },
                "Installed Agent Execution Contract unresolved rejection failed",
            )
            require(
                evidence["agent_execution_contract_operation_parity"] == {
                    "contract_codes": ["operation_id_not_supported"],
                    "requirement_codes": ["operation_id_not_supported"],
                    "atomic": True,
                },
                "Agent Execution Contract operation semantics diverged from AIO-036",
            )
            require(
                evidence["agent_execution_contract_resource_parity"] == {
                    "contract_codes": ["resource_parent_segment"],
                    "requirement_codes": ["resource_parent_segment"],
                    "atomic": True,
                },
                "Agent Execution Contract resource semantics diverged from AIO-036",
            )
            require(
                evidence["agent_execution_contract_schema_accepts_modes"]
                and evidence["agent_execution_contract_roundtrip"] == {
                    "valid": True, "equal": True},
                "Installed Agent Execution Contract schema/round-trip failed",
            )
            require(
                evidence["agent_execution_contract_pure_noninvoking_probe"],
                "Agent Execution Contract probe did not establish purity",
            )
            require(
                evidence["agent_execution_contract_public_export_absent"],
                "Agent Execution Contract unexpectedly gained a root export",
            )
            require(evidence["operation_requirement_valid"] == {
                        "valid": True,
                        "same_value": True,
                        "identity": ["repository_file_read",
                                     "synthetic/install-probe.txt"]},
                    "Installed Operation Requirement valid probe failed")
            require(evidence["operation_requirement_unsupported"] == {
                        "valid": False,
                        "codes": ["operation_id_not_supported"],
                        "atomic": True},
                    "Installed Operation Requirement support probe failed")
            require(evidence["operation_requirement_invalid_resource"] == {
                        "valid": False,
                        "codes": ["resource_parent_segment"],
                        "atomic": True},
                    "Installed Operation Requirement resource probe failed")
            require(evidence["operation_requirement_public_export_absent"],
                    "Operation Requirement unexpectedly gained a package-root export")
            require(evidence["operation_vocabulary"] == ["repository_file_read"],
                    "Installed Core operation vocabulary differs from canonical source")
            require(evidence["runtime_operation_capability_present_absent"] == {
                        "valid": True,
                        "observations": [
                            ["installed-runtime-primary", "repository_file_read",
                             "present"],
                            ["installed-runtime-secondary", "repository_file_read",
                             "absent"]]},
                    "Installed Runtime capability present/absent probe failed")
            require(evidence["runtime_operation_capability_unknown_missing"] == {
                        "valid": True,
                        "observations": [
                            ["installed-runtime-primary", "repository_file_read",
                             "unknown"],
                            ["installed-runtime-secondary", "repository_file_read",
                             "unknown"]]},
                    "Installed Runtime capability unknown normalization failed")
            require(evidence["runtime_operation_capability_duplicate"] == {
                        "codes": ["duplicate_runtime_operation_capability"],
                        "atomic": True},
                    "Installed Runtime capability duplicate rejection failed")
            require(evidence["runtime_operation_capability_unknown_runtime"] == {
                        "codes": ["agent_runtime_option_not_found"],
                        "atomic": True},
                    "Installed Runtime capability unknown Runtime rejection failed")
            require(
                evidence["runtime_operation_capability_unsupported_operation"] == {
                    "codes": ["operation_id_not_supported"],
                    "atomic": True},
                "Installed Runtime capability unsupported operation rejection failed")
            require(evidence["runtime_operation_capability_public_export_absent"],
                    "Runtime Operation Capability unexpectedly gained a package-root export")
            require(evidence["environment_operation_permission_states"] == [
                        "allowed", "denied", "unknown"],
                    "Installed Environment Operation Permission states differ")
            require(
                evidence[
                    "environment_operation_permission_allowed_denied_unknown"
                ] == {
                    "valid": True,
                    "observations": [
                        ["installed-runtime-primary", "installed-environment",
                         "repository_file_read", "synthetic/allowed.txt",
                         "allowed"],
                        ["installed-runtime-primary", "installed-environment",
                         "repository_file_read", "synthetic/denied.txt",
                         "denied"],
                        ["installed-runtime-secondary", "installed-environment",
                         "repository_file_read", "synthetic/unknown.txt",
                         "unknown"],
                    ],
                },
                "Installed Environment Operation Permission valid states failed",
            )
            require(
                evidence[
                    "environment_operation_permission_environment_mismatch"
                ] == {
                    "codes": [
                        "environment_operation_permission_environment_mismatch"
                    ],
                    "atomic": True,
                },
                "Installed Environment Operation Permission mismatch failed",
            )
            require(
                evidence[
                    "environment_operation_permission_identical_duplicate"
                ] == {
                    "codes": ["duplicate_environment_operation_permission"],
                    "atomic": True,
                },
                "Installed Environment Operation Permission duplicate failed",
            )
            require(
                evidence["environment_operation_permission_conflicts"]
                == [
                    {
                        "codes": [
                            "conflicting_environment_operation_permission"
                        ],
                        "atomic": True,
                    }
                ]
                * 6
                and evidence[
                    "environment_operation_permission_conflicts_deterministic"
                ],
                "Installed Environment Operation Permission conflicts failed",
            )
            require(
                evidence[
                    "environment_operation_permission_invalid_resource"
                ] == {
                    "codes": ["resource_parent_segment"],
                    "atomic": True,
                },
                "Installed Environment Operation Permission resource failure failed",
            )
            require(
                evidence[
                    "environment_operation_permission_public_export_absent"
                ],
                "Environment Operation Permission unexpectedly gained a package-root export",
            )
            if target_safe:
                print(
                    "SKIP checkout tasks/inspect/structural/full verification: "
                    "target-safe mode avoids repository Workflow enumeration; "
                    "run focused checks separately",
                    flush=True,
                )
            else:
                for cwd in (ROOT, ROOT / "scripts"):
                    for args, marker in [
                        (["--help"], "{tasks,inspect,verify}"),
                        (["tasks"], "AIO-016"),
                        (["inspect", "AIO-015"], "Schema: VALID"),
                    ]:
                        output = run([str(aio), *args], cwd, run_env)
                        require(
                            marker in output,
                            f"Missing expected output: {marker}",
                        )
                output = run(
                    [str(aio), "verify", "--structure"],
                    ROOT / "scripts",
                    run_env,
                )
                require(
                    "Supported AIO Structure" in output,
                    "Installed structure mode failed",
                )
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
