"""Private Task/Workflow/Stage/Role responsibility resolution helpers.

This module is an implementation seam shared by Assignment validation and Actor
Selection.  It deliberately defines no public responsibility domain contract.
"""

from __future__ import annotations

from typing import Mapping, TypeAlias, cast

from engineering_orchestration.role_catalog import RoleCatalog, RoleCatalogError
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowCatalogError,
    WorkflowDefinition,
)


_ResponsibilityKey: TypeAlias = tuple[str, str, str, str]
_ResolutionFailure: TypeAlias = tuple[str, str]


def _require_valid_workflow_catalog(
    catalog: WorkflowCatalog,
    *,
    catalog_consumer: str,
) -> None:
    if catalog.is_valid:
        return
    diagnostics = "; ".join(catalog.load_errors) or "catalog has no definitions"
    raise WorkflowCatalogError(
        f"{catalog_consumer} requires a valid Workflow catalog: " + diagnostics
    )


def _require_valid_role_catalog(
    catalog: RoleCatalog,
    *,
    catalog_consumer: str,
) -> None:
    if catalog.is_valid:
        return
    diagnostics = "; ".join(catalog.load_errors) or "catalog has no definitions"
    raise RoleCatalogError(
        f"{catalog_consumer} requires a valid framework Role catalog: "
        + diagnostics
    )


def _task_workflow_id(
    task: Mapping[str, object],
) -> tuple[str | None, _ResolutionFailure | None]:
    workflow_id = task.get("workflow")
    if not isinstance(workflow_id, str) or not workflow_id:
        return None, (
            "task_workflow_missing",
            "The supplied Task must explicitly declare a Workflow.",
        )
    return workflow_id, None


def _resolve_task_workflow(
    task: Mapping[str, object],
    workflow_catalog: WorkflowCatalog,
    *,
    catalog_consumer: str,
) -> tuple[WorkflowDefinition | None, _ResolutionFailure | None]:
    workflow_id, failure = _task_workflow_id(task)
    if failure is not None:
        return None, failure
    _require_valid_workflow_catalog(
        workflow_catalog,
        catalog_consumer=catalog_consumer,
    )
    workflow = workflow_catalog.get(cast(str, workflow_id))
    if workflow is None:
        return None, (
            "workflow_not_found",
            f"Task Workflow '{workflow_id}' was not found in the supplied catalog.",
        )
    return workflow, None


def _resolve_task_responsibility(
    task: Mapping[str, object],
    stage_id: str,
    role_id: str,
    workflow_catalog: WorkflowCatalog,
    role_catalog: RoleCatalog,
    *,
    catalog_consumer: str,
) -> tuple[_ResponsibilityKey | None, Mapping[str, object] | None,
           _ResolutionFailure | None]:
    """Resolve one required Role without creating a public context object."""

    workflow_id, failure = _task_workflow_id(task)
    if failure is not None:
        return None, None, failure
    workflow_id = cast(str, workflow_id)

    _require_valid_workflow_catalog(
        workflow_catalog,
        catalog_consumer=catalog_consumer,
    )
    workflow = workflow_catalog.get(workflow_id)
    if workflow is None:
        return None, None, (
            "workflow_not_found",
            f"Workflow '{workflow_id}' was not found in the supplied catalog.",
        )

    stage = next(
        (candidate for candidate in workflow.stages if candidate.id == stage_id),
        None,
    )
    if stage is None:
        return None, None, (
            "stage_not_found",
            f"Stage '{stage_id}' was not found in Workflow '{workflow_id}'.",
        )

    _require_valid_role_catalog(
        role_catalog,
        catalog_consumer=catalog_consumer,
    )
    role = role_catalog.get(role_id)
    if role is None:
        return None, None, (
            "role_not_found",
            f"Role '{role_id}' was not found in the framework Role catalog.",
        )

    if role_id not in stage.required_roles:
        return None, None, (
            "role_not_required",
            f"Stage '{stage_id}' does not require Role '{role_id}'.",
        )

    task_id = cast(str, task["id"])
    return (task_id, workflow_id, stage_id, role_id), role, None
