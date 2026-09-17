#!/usr/bin/env python3
"""AI Engineering Orchestra — Task Status Inspection Utility.

Repository-local, read-only inspection utility to inspect and report
machine-readable Task governance status using existing approved contracts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

# Ensure repository root is on sys.path for local imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_catalog import (
    WorkflowCatalog,
    WorkflowDefinition,
    load_workflow_catalog,
)


CANONICAL_ARTIFACTS = (
    "task.yaml",
    "context.md",
    "acceptance-criteria.md",
    "review.md",
)

STANDARD_HUMAN_CONTROL_KEYS = (
    "architecture_changes_require_approval",
    "breaking_contract_changes_require_approval",
    "breaking_schema_changes_require_approval",
    "final_review_required",
)


@dataclass
class TaskInspectionResult:
    """Structured result of a Task governance status inspection."""

    task_dir: Path
    task_id: str | None = None
    title: str | None = None
    task_type: str | None = None
    status: str | None = None
    risk: str | None = None
    risk_source: str = "task"
    complexity: str | None = None
    complexity_source: str = "task"
    execution_mode: str | None = None
    execution_mode_source: str = "task"
    canonical_artifacts: dict[str, bool] = field(default_factory=dict)
    schema_status: str = "UNKNOWN"
    schema_errors: list[str] = field(default_factory=list)
    task_quality_gates: list[str] = field(default_factory=list)
    project_manifest_path: Path | None = None
    project_manifest_available: bool = False
    project_required_gates: list[str] = field(default_factory=list)
    workflow_required_gates: list[str] = field(default_factory=list)
    effective_quality_gates: list[str] = field(default_factory=list)
    machine_readable_gates: list[str] = field(default_factory=list)
    task_human_control: dict[str, bool] = field(default_factory=dict)
    project_human_control: dict[str, bool] = field(default_factory=dict)
    effective_human_control: dict[str, tuple[bool, str]] = field(default_factory=dict)
    workflow: str | None = None
    workflow_binding: str | None = None
    workflow_resolution: str | None = None
    workflow_stages_count: int | None = None
    workflow_stage_ids: list[str] = field(default_factory=list)
    workflow_checkpoints: list[str] = field(default_factory=list)
    workflow_source_path: Path | None = None
    workflow_errors: list[str] = field(default_factory=list)

    @property
    def workflow_status(self) -> str:
        """Backward-compatible workflow status indicator."""
        if self.workflow is not None:
            return self.workflow_binding or "TASK-DECLARED"
        return "NOT DECLARED"

    @property
    def is_valid(self) -> bool:
        """Task is valid if all canonical artifacts are present, schema is VALID,

        and any declared workflow is RESOLVED.
        """
        all_artifacts_present = all(
            self.canonical_artifacts.get(name, False) for name in CANONICAL_ARTIFACTS
        )
        workflow_valid = (
            True if self.workflow is None else (self.workflow_resolution == "RESOLVED")
        )
        return all_artifacts_present and self.schema_status == "VALID" and workflow_valid


def find_default_schema_path() -> Path | None:
    """Locate schemas/task.schema.json relative to this script or current working directory."""
    candidates = [
        Path(__file__).resolve().parent.parent / "schemas" / "task.schema.json",
        Path.cwd() / "schemas" / "task.schema.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def find_project_manifest(task_dir: Path) -> Path | None:
    """Locate .ai/project.yaml or project.yaml by walking up from the task directory."""
    resolved_task_dir = task_dir.resolve()
    current = resolved_task_dir
    for parent in [current] + list(current.parents):
        ai_manifest = parent / ".ai" / "project.yaml"
        if ai_manifest.is_file():
            return ai_manifest.resolve()
        plain_manifest = parent / "project.yaml"
        if plain_manifest.is_file():
            return plain_manifest.resolve()

    cwd_manifest = Path.cwd() / ".ai" / "project.yaml"
    if cwd_manifest.is_file():
        return cwd_manifest.resolve()

    return None


def find_workflows_dir(task_dir: Path | None = None) -> Path | None:
    """Locate workflows/ by walking up from task directory or checking repo root."""
    if task_dir is not None:
        resolved = task_dir.resolve()
        for parent in [resolved] + list(resolved.parents):
            candidate = parent / "workflows"
            if candidate.is_dir():
                return candidate.resolve()

    candidates = [
        Path(__file__).resolve().parent.parent / "workflows",
        Path.cwd() / "workflows",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load and return the JSON schema."""
    with schema_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def inspect_task(
    task_dir: Path | str,
    project_manifest_path: Path | str | None = None,
    schema_path: Path | str | None = None,
    workflows_dir: Path | str | None = None,
) -> TaskInspectionResult:
    """Inspect the given Task directory and return a structured governance result."""
    task_path = Path(task_dir)
    if not task_path.exists():
        raise FileNotFoundError(f"Task directory does not exist: {task_path}")
    if not task_path.is_dir():
        raise NotADirectoryError(f"Task path is not a directory: {task_path}")

    result = TaskInspectionResult(task_dir=task_path)

    # 1. Canonical Artifact Presence
    for artifact_name in CANONICAL_ARTIFACTS:
        artifact_path = task_path / artifact_name
        result.canonical_artifacts[artifact_name] = artifact_path.is_file()

    # 2. Locate and load Project Manifest where available
    proj_path: Path | None = None
    if project_manifest_path is not None:
        explicit_proj = Path(project_manifest_path)
        if explicit_proj.is_file():
            proj_path = explicit_proj.resolve()
    else:
        proj_path = find_project_manifest(task_path)

    project_data: dict[str, Any] | None = None
    if proj_path is not None and proj_path.is_file():
        try:
            with proj_path.open("r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    project_data = loaded
                    result.project_manifest_path = proj_path
                    result.project_manifest_available = True
        except Exception:
            project_data = None

    # Extract project-level defaults, quality gates, human control
    proj_quality_gates: list[str] = []
    proj_human_control: dict[str, bool] = {}
    proj_complexity_default: str | None = None
    proj_risk_default: str | None = None
    proj_execution_mode_default: str | None = None

    if project_data is not None:
        quality_cfg = project_data.get("quality", {})
        if isinstance(quality_cfg, dict):
            if quality_cfg.get("require_documentation_consistency") is True:
                proj_quality_gates.append("documentation_consistency")
            if quality_cfg.get("require_independent_review") is True:
                proj_quality_gates.append("independent_review")

        hc_cfg = project_data.get("human_control", {})
        if isinstance(hc_cfg, dict):
            for k in STANDARD_HUMAN_CONTROL_KEYS:
                if k in hc_cfg and isinstance(hc_cfg[k], bool):
                    proj_human_control[k] = hc_cfg[k]

        comp_cfg = project_data.get("complexity", {})
        if isinstance(comp_cfg, dict) and isinstance(comp_cfg.get("default"), str):
            proj_complexity_default = comp_cfg["default"]

        risk_cfg = project_data.get("risk", {})
        if isinstance(risk_cfg, dict) and isinstance(risk_cfg.get("default"), str):
            proj_risk_default = risk_cfg["default"]

        exec_cfg = project_data.get("execution", {})
        if isinstance(exec_cfg, dict) and isinstance(exec_cfg.get("default_mode"), str):
            proj_execution_mode_default = exec_cfg["default_mode"]

    result.project_required_gates = sorted(proj_quality_gates)
    result.project_human_control = {k: proj_human_control[k] for k in sorted(proj_human_control)}

    # 3. Load and validate task.yaml
    task_yaml_path = task_path / "task.yaml"
    if not task_yaml_path.is_file():
        result.schema_status = "MISSING"
        result.schema_errors = ["task.yaml not found in Task directory"]
        result.effective_quality_gates = sorted(result.project_required_gates)
        result.machine_readable_gates = list(result.effective_quality_gates)
        return result

    raw_yaml: Any = None
    try:
        with task_yaml_path.open("r", encoding="utf-8") as f:
            raw_yaml = yaml.safe_load(f)
    except Exception as exc:
        result.schema_status = "INVALID"
        result.schema_errors = [f"YAML parse error: {exc}"]
        result.effective_quality_gates = sorted(result.project_required_gates)
        result.machine_readable_gates = list(result.effective_quality_gates)
        return result

    if not isinstance(raw_yaml, dict):
        result.schema_status = "INVALID"
        result.schema_errors = ["task.yaml content is not a mapping/object"]
        result.effective_quality_gates = sorted(result.project_required_gates)
        result.machine_readable_gates = list(result.effective_quality_gates)
        return result

    # Resolve schema
    active_schema_path: Path | None = None
    if schema_path is not None:
        sp = Path(schema_path)
        if sp.is_file():
            active_schema_path = sp.resolve()
    else:
        active_schema_path = find_default_schema_path()

    if active_schema_path is None or not active_schema_path.is_file():
        result.schema_status = "ERROR"
        result.schema_errors = ["schemas/task.schema.json could not be located"]
        return result

    try:
        schema_dict = load_schema(active_schema_path)
        validator = Draft202012Validator(schema_dict)
        errors = sorted(
            validator.iter_errors(raw_yaml),
            key=lambda e: (str(list(e.absolute_path)), str(e.validator)),
        )
        if errors:
            result.schema_status = "INVALID"
            for err in errors:
                location = ".".join(str(part) for part in err.absolute_path)
                location = location or "<root>"
                result.schema_errors.append(f"{location} [{err.validator}]: {err.message}")
        else:
            result.schema_status = "VALID"
    except Exception as exc:
        result.schema_status = "ERROR"
        result.schema_errors = [f"Schema validation error: {exc}"]

    # 4. Extract Task metadata
    result.task_id = str(raw_yaml.get("id")) if "id" in raw_yaml else None
    result.title = str(raw_yaml.get("title")) if "title" in raw_yaml else None
    result.task_type = str(raw_yaml.get("type")) if "type" in raw_yaml else None
    result.status = str(raw_yaml.get("status")) if "status" in raw_yaml else None

    # Risk
    if "risk" in raw_yaml and isinstance(raw_yaml["risk"], str):
        result.risk = raw_yaml["risk"]
        result.risk_source = "task"
    elif proj_risk_default is not None:
        result.risk = proj_risk_default
        result.risk_source = "project"
    else:
        result.risk = None

    # Complexity
    if "complexity" in raw_yaml and isinstance(raw_yaml["complexity"], str):
        result.complexity = raw_yaml["complexity"]
        result.complexity_source = "task"
    elif proj_complexity_default is not None:
        result.complexity = proj_complexity_default
        result.complexity_source = "project"
    else:
        result.complexity = None

    # Execution mode
    exec_mode: str | None = None
    exec_block = raw_yaml.get("execution")
    if isinstance(exec_block, dict) and isinstance(exec_block.get("mode"), str):
        exec_mode = exec_block["mode"]
        result.execution_mode = exec_mode
        result.execution_mode_source = "task"
    elif proj_execution_mode_default is not None:
        result.execution_mode = proj_execution_mode_default
        result.execution_mode_source = "project"
    else:
        result.execution_mode = None

    # Task Quality Gates
    raw_qg = raw_yaml.get("quality_gates")
    if isinstance(raw_qg, list):
        result.task_quality_gates = sorted(str(item) for item in raw_qg)

    # Task Human Control
    task_hc = raw_yaml.get("human_control")
    if isinstance(task_hc, dict):
        for k in STANDARD_HUMAN_CONTROL_KEYS:
            if k in task_hc and isinstance(task_hc[k], bool):
                result.task_human_control[k] = task_hc[k]

    # Effective cumulative human control
    effective_hc: dict[str, tuple[bool, str]] = {}
    all_hc_keys = sorted(
        set(STANDARD_HUMAN_CONTROL_KEYS)
        | set(result.task_human_control.keys())
        | set(result.project_human_control.keys())
    )

    for k in all_hc_keys:
        in_task = k in result.task_human_control
        in_proj = k in result.project_human_control
        t_val = result.task_human_control.get(k, False)
        p_val = result.project_human_control.get(k, False)

        eff_val = t_val or p_val
        sources: list[str] = []
        if in_task and t_val:
            sources.append("task")
        if in_proj and p_val:
            sources.append("project")
        if not sources:
            if in_task and not t_val:
                sources.append("task (explicit false)")
            if in_proj and not p_val:
                sources.append("project (explicit false)")
        source_label = ", ".join(sources) if sources else "default"
        effective_hc[k] = (eff_val, source_label)

    result.effective_human_control = effective_hc

    # 5. Workflow Binding and Resolution
    if (
        "workflow" in raw_yaml
        and isinstance(raw_yaml["workflow"], str)
        and len(raw_yaml["workflow"]) > 0
    ):
        result.workflow = raw_yaml["workflow"]
        result.workflow_binding = "TASK-DECLARED"

        # Resolve via catalog
        wf_dir: Path | None = None
        if workflows_dir is not None:
            explicit_wf = Path(workflows_dir)
            if explicit_wf.is_dir():
                wf_dir = explicit_wf.resolve()
        else:
            wf_dir = find_workflows_dir(task_path)

        catalog = load_workflow_catalog(workflows_dir=wf_dir)
        wf_def = catalog.get(result.workflow)

        if wf_def is not None:
            result.workflow_resolution = "RESOLVED"
            result.workflow_stages_count = wf_def.stage_count
            result.workflow_stage_ids = list(wf_def.stage_ids)
            result.workflow_required_gates = sorted(wf_def.workflow_quality_gates)
            result.workflow_checkpoints = sorted(wf_def.checkpoint_stage_ids)
            result.workflow_source_path = wf_def.source_path
        else:
            result.workflow_resolution = "UNRESOLVED"
            if catalog.load_errors:
                result.workflow_errors = list(catalog.load_errors)
            else:
                result.workflow_errors = [
                    f"Workflow '{result.workflow}' not found in catalog ({wf_dir or 'workflows/'})"
                ]

    # 6. Calculate Effective Quality Gate Union (Project ∪ Workflow ∪ Task)
    effective_gates: set[str] = set(result.task_quality_gates)
    if result.project_manifest_available:
        effective_gates.update(result.project_required_gates)
    if result.workflow_resolution == "RESOLVED":
        effective_gates.update(result.workflow_required_gates)

    result.effective_quality_gates = sorted(effective_gates)
    result.machine_readable_gates = list(result.effective_quality_gates)

    return result


def format_report(result: TaskInspectionResult) -> str:
    """Format a deterministic text report from inspection results."""
    lines: list[str] = []

    # Header metadata
    task_id = result.task_id if result.task_id is not None else "UNKNOWN"
    lines.append(f"Task: {task_id}")
    if result.title is not None:
        lines.append(f"Title: {result.title}")
    if result.task_type is not None:
        lines.append(f"Type: {result.task_type}")
    status = result.status if result.status is not None else "UNKNOWN"
    lines.append(f"Status: {status}")

    if result.risk is not None:
        risk_str = (
            f"{result.risk} (inherited: project)"
            if result.risk_source == "project"
            else result.risk
        )
        lines.append(f"Risk: {risk_str}")

    if result.complexity is not None:
        comp_str = (
            f"{result.complexity} (inherited: project)"
            if result.complexity_source == "project"
            else result.complexity
        )
        lines.append(f"Complexity: {comp_str}")

    if result.execution_mode is not None:
        mode_str = (
            f"{result.execution_mode} (inherited: project)"
            if result.execution_mode_source == "project"
            else result.execution_mode
        )
        lines.append(f"Execution Mode: {mode_str}")

    lines.append(f"Schema: {result.schema_status}")

    # Schema errors if any
    if result.schema_errors and result.schema_status != "VALID":
        lines.append("")
        lines.append("Schema Errors")
        lines.append("-------------")
        for err in sorted(result.schema_errors):
            lines.append(f"- {err}")

    # Canonical Artifacts
    lines.append("")
    lines.append("Artifacts")
    lines.append("---------")
    for artifact_name in CANONICAL_ARTIFACTS:
        present = result.canonical_artifacts.get(artifact_name, False)
        status_str = "PRESENT" if present else "MISSING"
        lines.append(f"{artifact_name:<24}{status_str}")

    # Project Required Gates
    lines.append("")
    lines.append("Project Required Gates")
    lines.append("----------------------")
    if not result.project_manifest_available:
        lines.append("NOT AVAILABLE (project manifest not found)")
    elif result.project_required_gates:
        for gate in sorted(result.project_required_gates):
            lines.append(gate)
    else:
        lines.append("None required")

    # Workflow Required Gates
    lines.append("")
    lines.append("Workflow Required Gates")
    lines.append("-----------------------")
    if result.workflow is None:
        lines.append("None (workflow not declared)")
    elif result.workflow_resolution != "RESOLVED":
        lines.append("UNRESOLVED (workflow could not be resolved)")
    elif result.workflow_required_gates:
        for gate in sorted(result.workflow_required_gates):
            lines.append(gate)
    else:
        lines.append("None required")

    # Task Quality Gates
    lines.append("")
    lines.append("Task Quality Gates")
    lines.append("------------------")
    if result.task_quality_gates:
        for gate in sorted(result.task_quality_gates):
            lines.append(gate)
    else:
        lines.append("None declared")

    # Effective Quality Gates
    lines.append("")
    lines.append("Effective Quality Gates")
    lines.append("-----------------------")
    if result.effective_quality_gates:
        for gate in sorted(result.effective_quality_gates):
            lines.append(gate)
    else:
        lines.append("None")
    if result.workflow is not None and result.workflow_resolution != "RESOLVED":
        lines.append(
            "(Note: Excludes Workflow contributions because declared Workflow is UNRESOLVED.)"
        )

    # Human Control
    lines.append("")
    lines.append("Human Control")
    lines.append("-------------")
    if result.effective_human_control:
        for k in sorted(result.effective_human_control.keys()):
            val, src = result.effective_human_control[k]
            val_str = "true" if val else "false"
            lines.append(f"{k}: {val_str} ({src})")
    else:
        lines.append("None declared")

    # Workflow
    lines.append("")
    lines.append("Workflow")
    lines.append("--------")
    if result.workflow is not None:
        lines.append(result.workflow)
        lines.append(f"Binding: {result.workflow_binding}")
        if result.workflow_resolution == "RESOLVED":
            lines.append("Resolution: RESOLVED")
            if result.workflow_stages_count is not None:
                lines.append(f"Stages: {result.workflow_stages_count}")
            if result.workflow_checkpoints:
                lines.append(f"Human Control Checkpoints: {', '.join(result.workflow_checkpoints)}")
        else:
            lines.append("Resolution: UNRESOLVED")
            if result.workflow_errors:
                for err in sorted(result.workflow_errors):
                    lines.append(f"- {err}")
    else:
        lines.append("NOT DECLARED")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Inspect and report machine-readable Task governance status."
    )
    parser.add_argument(
        "task_dir",
        type=Path,
        help="Path to the Task directory to inspect.",
    )
    parser.add_argument(
        "--project-manifest",
        type=Path,
        default=None,
        help="Path to project.yaml (default: auto-discover).",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to task.schema.json (default: schemas/task.schema.json).",
    )
    parser.add_argument(
        "--workflows-dir",
        type=Path,
        default=None,
        help="Path to workflows directory (default: auto-discover).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress formatted output and only return exit code.",
    )

    args = parser.parse_args(argv)

    try:
        result = inspect_task(
            task_dir=args.task_dir,
            project_manifest_path=args.project_manifest,
            schema_path=args.schema,
            workflows_dir=args.workflows_dir,
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(format_report(result))

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
