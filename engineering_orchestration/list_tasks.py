#!/usr/bin/env python3
"""AI Engineering Orchestra — Task Inventory and Discovery Utility.

Deterministic repository-level inventory and discovery utility to enumerate
and report Tasks in the Manifest-configured directory using existing infrastructure.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from engineering_orchestration.inspect_task import TaskInspectionResult, inspect_task

# Legacy source-location constant; the unified router passes active project paths.
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class TaskSummary:
    """Canonical summary of a discovered valid Task."""

    task_id: str
    title: str
    task_type: str
    status: str
    workflow: str | None
    resolution: str
    task_dir: Path


@dataclass
class TaskAnomaly:
    """Repository discovery anomaly or invalid/unreadable Task entry."""

    dir_name: str
    dir_path: Path
    reason: str
    details: list[str] = field(default_factory=list)


@dataclass
class TaskInventoryResult:
    """Structured inventory of discovered Tasks and repository anomalies."""

    tasks_dir: Path
    valid_tasks: list[TaskSummary] = field(default_factory=list)
    anomalies: list[TaskAnomaly] = field(default_factory=list)

    @property
    def has_anomalies(self) -> bool:
        """True if any genuine repository anomalies were detected."""
        return len(self.anomalies) > 0


def find_default_tasks_dir() -> Path | None:
    """Resolve the active Manifest's Task directory."""
    from engineering_orchestration.project import find_project_root, task_directory

    return task_directory(find_project_root())


def discover_tasks(
    tasks_dir: Path | str | None = None,
    project_manifest_path: Path | str | None = None,
    schema_path: Path | str | None = None,
    workflows_dir: Path | str | None = None,
) -> TaskInventoryResult:
    """Discover and inspect immediate child directories under tasks_dir.

    Enumerate only immediate child directories; do not recursively traverse.
    Canonical identity comes exclusively from task.yaml. Never derive identity
    from directory names.
    """
    resolved_dir: Path | None = None
    if tasks_dir is not None:
        resolved_dir = Path(tasks_dir).resolve()
    else:
        resolved_dir = find_default_tasks_dir()

    if resolved_dir is None or not resolved_dir.is_dir():
        target = resolved_dir or tasks_dir
        raise FileNotFoundError(f"Tasks directory not found: {target}")

    inventory = TaskInventoryResult(tasks_dir=resolved_dir)

    # Enumerate immediate child directories only
    child_dirs = sorted(
        [p for p in resolved_dir.iterdir() if p.is_dir()],
        key=lambda p: p.name,
    )

    for child_dir in child_dirs:
        try:
            result = inspect_task(
                task_dir=child_dir,
                project_manifest_path=project_manifest_path,
                schema_path=schema_path,
                workflows_dir=workflows_dir,
            )
        except Exception as exc:
            inventory.anomalies.append(
                TaskAnomaly(
                    dir_name=child_dir.name,
                    dir_path=child_dir,
                    reason=f"Unexpected error inspecting directory: {exc}",
                    details=[str(exc)],
                )
            )
            continue

        # Handle unreadable / structurally invalid Task directories
        if result.schema_status != "VALID" or result.task_id is None:
            reason = "invalid task"
            if result.schema_status == "MISSING":
                reason = "task.yaml not found in Task directory"
            elif result.schema_status == "INVALID":
                reason = "task.yaml is malformed or violates schema"
            elif result.schema_status == "ERROR":
                reason = "error during schema validation"

            inventory.anomalies.append(
                TaskAnomaly(
                    dir_name=child_dir.name,
                    dir_path=child_dir,
                    reason=reason,
                    details=list(result.schema_errors),
                )
            )
            continue

        # Determine workflow display and resolution semantics
        wf_declared = result.workflow
        if wf_declared is None:
            resolution_label = "NOT DECLARED"
        elif result.workflow_resolution == "RESOLVED":
            resolution_label = "RESOLVED"
        else:
            resolution_label = "UNRESOLVED"

        inventory.valid_tasks.append(
            TaskSummary(
                task_id=result.task_id,
                title=result.title or "",
                task_type=result.task_type or "",
                status=result.status or "",
                workflow=wf_declared,
                resolution=resolution_label,
                task_dir=child_dir,
            )
        )

    # Sort valid tasks deterministically by canonical Task ID
    inventory.valid_tasks.sort(key=lambda t: t.task_id)

    # Sort anomalies deterministically by directory name
    inventory.anomalies.sort(key=lambda a: a.dir_name)

    return inventory


def filter_tasks(
    tasks: list[TaskSummary],
    status: str | None = None,
    workflow: str | None = None,
) -> list[TaskSummary]:
    """Filter valid tasks conjunctively by canonical status and declared workflow ID."""
    filtered = tasks
    if status is not None:
        filtered = [t for t in filtered if t.status == status]
    if workflow is not None:
        filtered = [t for t in filtered if t.workflow == workflow]
    return filtered


def format_inventory_table(
    inventory: TaskInventoryResult,
    status_filter: str | None = None,
    workflow_filter: str | None = None,
) -> str:
    """Format a deterministic human-readable table with optional anomaly diagnostics."""
    matching_tasks = filter_tasks(
        inventory.valid_tasks,
        status=status_filter,
        workflow=workflow_filter,
    )

    lines: list[str] = []

    # Table columns
    headers = ("ID", "Title", "Type", "Status", "Workflow", "Resolution")

    rows: list[tuple[str, str, str, str, str, str]] = []
    for t in matching_tasks:
        wf_display = t.workflow if t.workflow is not None else "-"
        rows.append((
            t.task_id,
            t.title,
            t.task_type,
            t.status,
            wf_display,
            t.resolution,
        ))

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            if len(val) > col_widths[idx]:
                col_widths[idx] = len(val)

    # Build header and separator
    header_line = "  ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    separator_line = "  ".join("-" * col_widths[i] for i in range(len(headers)))

    lines.append(header_line)
    lines.append(separator_line)

    for row in rows:
        row_line = "  ".join(f"{val:<{col_widths[i]}}" for i, val in enumerate(row))
        lines.append(row_line)

    if not rows:
        lines.append("(No matching Tasks found)")

    # Diagnostics section for anomalies
    if inventory.anomalies:
        lines.append("")
        lines.append("Repository Anomalies / Diagnostics")
        lines.append("----------------------------------")
        for anomaly in inventory.anomalies:
            lines.append(f"- {anomaly.dir_name}: {anomaly.reason}")
            for detail in anomaly.details:
                lines.append(f"    * {detail}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="List and inspect Tasks in the Manifest-configured directory."
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter tasks by canonical status (e.g. completed, in_progress).",
    )
    parser.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Filter tasks by declared workflow ID (e.g. standard-change).",
    )
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=None,
        help="Path to tasks directory (default: resolve the active Manifest).",
    )

    args = parser.parse_args(argv)

    try:
        inventory = discover_tasks(tasks_dir=args.tasks_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2

    output = format_inventory_table(
        inventory=inventory,
        status_filter=args.status,
        workflow_filter=args.workflow,
    )
    print(output)

    # Non-zero exit code if genuine repository anomalies were found
    return 1 if inventory.has_anomalies else 0


if __name__ == "__main__":
    sys.exit(main())
