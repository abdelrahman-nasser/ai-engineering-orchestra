"""Read-only structural and cross-resource validation.

Results are evidence, never Quality Gates. No project command execution, Role
assignment, or Task lifecycle behavior is defined.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from engineering_orchestration.project import find_project_root, task_directory
from engineering_orchestration.role_catalog import RoleCatalog, load_role_catalog
from engineering_orchestration.schema_resources import load_validator, schema_errors
from engineering_orchestration.workflow_catalog import WorkflowCatalog, load_workflow_catalog


@dataclass(frozen=True)
class Finding:
    status: Literal["FAIL", "ERROR"]
    path: Path
    message: str


@dataclass
class ValidationResult:
    findings: list[Finding] = field(default_factory=list)

    @property
    def status(self) -> Literal["PASS", "FAIL", "ERROR"]:
        if any(item.status == "ERROR" for item in self.findings):
            return "ERROR"
        return "FAIL" if self.findings else "PASS"


def _document(path: Path, validator, result: ValidationResult) -> Any:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeError) as exc:
        result.findings.append(Finding("FAIL", path, f"Invalid YAML: {exc}"))
        return None
    except FileNotFoundError:
        result.findings.append(Finding("FAIL", path, "Required document missing"))
        return None
    errors = schema_errors(validator, document)
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        result.findings.append(Finding("FAIL", path, f"{location}: {error.message}"))
    return None if errors else document


def manifest_semantic_errors(manifest: dict) -> list[str]:
    """Data-only checks after successful Project Manifest schema validation."""
    errors = []
    seen = set()
    for index, check in enumerate(manifest.get("verification", {}).get("checks", [])):
        check_id = check["id"]
        if check_id in seen:
            errors.append(
                f"verification.checks.{index}.id: Duplicate Verification Check ID: {check_id}")
        seen.add(check_id)
    return errors


def workflow_role_reference_findings(
    workflows: WorkflowCatalog,
    roles: RoleCatalog,
) -> list[Finding]:
    """Resolve Workflow Role references without assigning or selecting Actors."""
    findings: list[Finding] = []
    for workflow_id in workflows.workflow_ids:
        workflow = workflows.definitions[workflow_id]
        path = workflow.source_path or workflows.workflows_dir
        for stage in workflow.stages:
            for role_id in stage.required_roles:
                if roles.get(role_id) is None:
                    findings.append(Finding(
                        "FAIL",
                        path,
                        f"Workflow '{workflow_id}' stage '{stage.id}' references "
                        f"unknown Role: {role_id}",
                    ))
    return findings


def validate_project(start: Path | None = None) -> ValidationResult:
    """Validate the nearest active project's supported AIO data.

    Missing required project structures and invalid data are FAIL. Resource,
    I/O and internal failures are ERROR. ERROR takes precedence in aggregation.
    Task directories are immediate children; identity comes from task.yaml.id.
    """
    result = ValidationResult()
    location = Path.cwd() if start is None else Path(start)
    try:
        try:
            root = find_project_root(location)
        except FileNotFoundError as exc:
            result.findings.append(Finding("FAIL", location, str(exc)))
            return result
        location = root / ".ai/project.yaml"
        manifest_validator = load_validator("project-manifest.schema.json")
        task_validator = load_validator("task.schema.json")
        # Check all required resources even when the project catalog is absent.
        load_validator("workflow.schema.json")
        manifest = _document(location, manifest_validator, result)
        if manifest is None:
            return result
        for message in manifest_semantic_errors(manifest):
            result.findings.append(Finding("FAIL", location, message))
        try:
            tasks = task_directory(root, manifest)
        except ValueError as exc:
            result.findings.append(Finding("FAIL", location, str(exc)))
            return result

        location = root / "workflows"
        catalog = load_workflow_catalog(location)
        for message in catalog.load_errors:
            status = "ERROR" if message in catalog.infrastructure_errors else "FAIL"
            result.findings.append(Finding(status, location, message))
        role_catalog = load_role_catalog()
        if not role_catalog.is_valid:
            diagnostics = "; ".join(role_catalog.load_errors) or "unknown catalog failure"
            result.findings.append(Finding(
                "ERROR",
                location,
                f"Framework Role catalog could not load: {diagnostics}",
            ))
        else:
            result.findings.extend(workflow_role_reference_findings(catalog, role_catalog))
        location = tasks
        if not tasks.is_dir():
            result.findings.append(Finding("FAIL", tasks, "Tasks directory not found"))
            return result
        seen: dict[str, Path] = {}
        for directory in sorted(tasks.iterdir()):
            if not directory.is_dir():
                continue
            location = directory / "task.yaml"
            task = _document(location, task_validator, result)
            if task is None:
                continue
            task_id = task["id"]
            if task_id in seen:
                result.findings.append(Finding(
                    "FAIL", location, f"Duplicate Task ID: {task_id} (also {seen[task_id]})"))
            seen[task_id] = location
            workflow = task.get("workflow")
            if workflow is not None and catalog.get(workflow) is None:
                result.findings.append(Finding("FAIL", location, f"Unknown Workflow: {workflow}"))
    except Exception as exc:
        result.findings.append(Finding("ERROR", location, f"Validation could not finish: {exc}"))
    return result
