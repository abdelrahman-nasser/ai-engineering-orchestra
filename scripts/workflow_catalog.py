#!/usr/bin/env python3
"""AI Engineering Orchestra — Workflow Catalog and Resolution.

Lightweight, repository-local, read-only component to discover, load,
structurally validate, and resolve canonical Workflow definitions by declared ID.

This module provides data access only. It SHALL NOT execute stages, assign actors,
manage runtime state, schedule tasks, or invoke providers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class WorkflowCatalogError(Exception):
    """Raised when the Workflow catalog cannot be safely loaded or resolved."""


@dataclass
class WorkflowStage:
    """Canonical governance Stage within a Workflow."""

    id: str
    purpose: str
    required_roles: list[str] = field(default_factory=list)
    required_quality_gates: list[str] = field(default_factory=list)
    human_control_checkpoint: bool | None = None  # None indicates omitted


@dataclass
class WorkflowDefinition:
    """Canonical normalized Workflow definition."""

    id: str
    name: str
    purpose: str
    stages: list[WorkflowStage]
    applicable_task_types: list[str] = field(default_factory=list)
    source_path: Path | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    @property
    def stage_ids(self) -> list[str]:
        """Ordered Stage identifiers."""
        return [s.id for s in self.stages]

    @property
    def stage_count(self) -> int:
        """Total number of ordered stages."""
        return len(self.stages)

    @property
    def workflow_quality_gates(self) -> list[str]:
        """All Quality Gate IDs declared across ordered stages (deduplicated, order-preserved)."""
        seen: set[str] = set()
        gates: list[str] = []
        for stage in self.stages:
            for gate in stage.required_quality_gates:
                if gate not in seen:
                    seen.add(gate)
                    gates.append(gate)
        return gates

    @property
    def checkpoint_stage_ids(self) -> list[str]:
        """IDs of stages declaring human_control_checkpoint: true."""
        return [s.id for s in self.stages if s.human_control_checkpoint is True]


@dataclass
class WorkflowCatalog:
    """Catalog of canonical Workflow definitions indexed strictly by declared ID."""

    workflows_dir: Path
    definitions: dict[str, WorkflowDefinition] = field(default_factory=dict)
    load_errors: list[str] = field(default_factory=list)

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        """Resolve a Workflow by its declared ID."""
        return self.definitions.get(workflow_id)

    def __contains__(self, workflow_id: str) -> bool:
        return workflow_id in self.definitions

    @property
    def workflow_ids(self) -> list[str]:
        """Sorted list of all declared Workflow IDs in the catalog."""
        return sorted(self.definitions.keys())

    @property
    def is_valid(self) -> bool:
        """True if definitions loaded without errors."""
        return len(self.load_errors) == 0 and len(self.definitions) > 0


def find_default_workflow_schema_path() -> Path | None:
    """Locate schemas/workflow.schema.json relative to this script or current working directory."""
    candidates = [
        Path(__file__).resolve().parent.parent / "schemas" / "workflow.schema.json",
        Path.cwd() / "schemas" / "workflow.schema.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def find_default_workflows_dir() -> Path | None:
    """Locate workflows/ relative to this script or current working directory."""
    candidates = [
        Path(__file__).resolve().parent.parent / "workflows",
        Path.cwd() / "workflows",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate.resolve()
    return None


def load_workflow_catalog(
    workflows_dir: Path | str | None = None,
    schema_path: Path | str | None = None,
    raise_on_error: bool = False,
) -> WorkflowCatalog:
    """Discover, load, structurally validate, and index Workflow definitions by declared ID.

    Workflow IDs and filenames are separate concepts. This function enumerates all
    YAML files in workflows_dir, safe-loads each, validates against schemas/workflow.schema.json,
    reads the declared 'id', and indexes by that ID. It rejects duplicate declared IDs.
    """
    resolved_dir: Path | None = None
    if workflows_dir is not None:
        resolved_dir = Path(workflows_dir).resolve()
    else:
        resolved_dir = find_default_workflows_dir()

    if resolved_dir is None or not resolved_dir.is_dir():
        err = f"Workflows directory not found: {workflows_dir or 'workflows/'}"
        if raise_on_error:
            raise WorkflowCatalogError(err)
        return WorkflowCatalog(
            workflows_dir=resolved_dir or Path("workflows"),
            load_errors=[err],
        )

    resolved_schema: Path | None = None
    if schema_path is not None:
        resolved_schema = Path(schema_path).resolve()
    else:
        resolved_schema = find_default_workflow_schema_path()

    if resolved_schema is None or not resolved_schema.is_file():
        err = f"Workflow schema not found: {schema_path or 'schemas/workflow.schema.json'}"
        if raise_on_error:
            raise WorkflowCatalogError(err)
        return WorkflowCatalog(
            workflows_dir=resolved_dir,
            load_errors=[err],
        )

    try:
        with resolved_schema.open("r", encoding="utf-8") as f:
            schema_dict = json.load(f)
        Draft202012Validator.check_schema(schema_dict)
        validator = Draft202012Validator(schema_dict)
    except Exception as exc:
        err = f"Failed to load Workflow schema from {resolved_schema}: {exc}"
        if raise_on_error:
            raise WorkflowCatalogError(err)
        return WorkflowCatalog(
            workflows_dir=resolved_dir,
            load_errors=[err],
        )

    catalog = WorkflowCatalog(workflows_dir=resolved_dir)

    yaml_files = sorted(
        [p for p in resolved_dir.iterdir() if p.is_file() and p.suffix.lower() in {".yaml", ".yml"}],
        key=lambda p: p.name,
    )

    for yaml_file in yaml_files:
        try:
            content = yaml_file.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as exc:
            msg = f"{yaml_file.name}: YAML parse error: {exc}"
            catalog.load_errors.append(msg)
            continue

        if not isinstance(data, dict):
            msg = f"{yaml_file.name}: root content is not a mapping/object"
            catalog.load_errors.append(msg)
            continue

        errors = sorted(
            validator.iter_errors(data),
            key=lambda e: (str(list(e.absolute_path)), str(e.validator)),
        )
        if errors:
            for err in errors:
                location = ".".join(str(part) for part in err.absolute_path)
                location = location or "<root>"
                catalog.load_errors.append(
                    f"{yaml_file.name} [{location}]: {err.message}"
                )
            continue

        declared_id = data["id"]
        if declared_id in catalog.definitions:
            existing_file = catalog.definitions[declared_id].source_path
            existing_name = existing_file.name if existing_file else "unknown"
            msg = (
                f"Duplicate declared Workflow ID '{declared_id}' in {yaml_file.name} "
                f"(already defined in {existing_name})"
            )
            catalog.load_errors.append(msg)
            continue

        # Check stage ID uniqueness within this workflow
        seen_stage_ids: set[str] = set()
        stage_has_duplicates = False
        parsed_stages: list[WorkflowStage] = []

        for stage_raw in data.get("stages", []):
            s_id = stage_raw["id"]
            if s_id in seen_stage_ids:
                catalog.load_errors.append(
                    f"{yaml_file.name}: duplicate Stage ID '{s_id}' within workflow '{declared_id}'"
                )
                stage_has_duplicates = True
            seen_stage_ids.add(s_id)

            parsed_stages.append(
                WorkflowStage(
                    id=s_id,
                    purpose=stage_raw["purpose"],
                    required_roles=list(stage_raw.get("required_roles", [])),
                    required_quality_gates=list(stage_raw.get("required_quality_gates", [])),
                    human_control_checkpoint=stage_raw.get("human_control_checkpoint"),
                )
            )

        if stage_has_duplicates:
            continue

        wf_def = WorkflowDefinition(
            id=declared_id,
            name=data["name"],
            purpose=data["purpose"],
            stages=parsed_stages,
            applicable_task_types=list(data.get("applicable_task_types", [])),
            source_path=yaml_file,
            raw_data=data,
        )
        catalog.definitions[declared_id] = wf_def

    if raise_on_error and catalog.load_errors:
        raise WorkflowCatalogError("; ".join(catalog.load_errors))

    return catalog


def resolve_workflow(
    workflow_id: str,
    workflows_dir: Path | str | None = None,
    schema_path: Path | str | None = None,
) -> WorkflowDefinition | None:
    """Resolve a single Workflow definition by its declared ID using the catalog."""
    catalog = load_workflow_catalog(workflows_dir=workflows_dir, schema_path=schema_path)
    return catalog.get(workflow_id)
