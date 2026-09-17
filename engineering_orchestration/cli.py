#!/usr/bin/env python3
"""Brand-neutral CLI router for repository tooling.

Provides a unified command surface over proven Foundation utilities:

- tasks:   Task inventory and discovery
- inspect: Task governance inspection by declared Task ID
- verify:  Repository mechanical verification

This module is intentionally brand-neutral. Console naming belongs to package
entry-point metadata and the thin source wrapper that imports and calls main().
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


from engineering_orchestration.project import find_project_root, task_directory


def cmd_tasks(args: argparse.Namespace, project_root: Path) -> int:
    """Execute the 'tasks' subcommand.

    Delegates to the package's existing Task inventory capability.
    """
    from engineering_orchestration.list_tasks import discover_tasks, format_inventory_table

    try:
        tasks_dir = task_directory(project_root)
        inventory = discover_tasks(
            tasks_dir=tasks_dir,
            project_manifest_path=project_root / ".ai" / "project.yaml",
            workflows_dir=project_root / "workflows",
        )
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

    return 1 if inventory.has_anomalies else 0


def cmd_inspect(args: argparse.Namespace, project_root: Path) -> int:
    """Execute the 'inspect' subcommand.

    Resolves declared Task ID through existing inventory discovery,
    then delegates to existing Task inspection capability.
    """
    from engineering_orchestration.inspect_task import format_report, inspect_task
    from engineering_orchestration.list_tasks import discover_tasks

    try:
        tasks_dir = task_directory(project_root)
        inventory = discover_tasks(
            tasks_dir=tasks_dir,
            project_manifest_path=project_root / ".ai" / "project.yaml",
            workflows_dir=project_root / "workflows",
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2

    # Resolve declared Task ID to canonical directory
    matches = [task for task in inventory.valid_tasks if task.task_id == args.task_id]
    if not matches:
        print(
            f"ERROR: No Task with declared ID '{args.task_id}' found.",
            file=sys.stderr,
        )
        return 1

    if len(matches) > 1:
        print(
            f"ERROR: Multiple Tasks with declared ID '{args.task_id}' found.",
            file=sys.stderr,
        )
        return 1

    try:
        result = inspect_task(
            task_dir=matches[0].task_dir,
            project_manifest_path=project_root / ".ai" / "project.yaml",
            workflows_dir=project_root / "workflows",
        )
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2

    print(format_report(result))
    return 0 if result.is_valid else 1


def cmd_verify(args: argparse.Namespace, project_root: Path) -> int:
    """Execute supported structure and optionally declared project Checks."""
    from engineering_orchestration.project_verification import (
        VerificationPlan,
        format_structural_validation_output,
        format_verification_output,
        verify_project,
    )

    def announce(plan: VerificationPlan) -> None:
        print(
            f"Running {len(plan.checks)} project verification checks from "
            f".ai/project.yaml (active project: {plan.project_root}):"
        )
        print(
            "  Commands use the caller's environment and permissions; "
            "AIO provides no sandbox or isolation."
        )
        for check in plan.checks:
            print(f"  {check.id}")
        print(flush=True)

    try:
        if args.structure:
            result = verify_project(project_root, execute_checks=False)
            print(format_structural_validation_output(result.structural))
            return result.exit_code

        result = verify_project(project_root, before_execute=announce)
        print(format_verification_output(result))
        return result.exit_code
    except KeyboardInterrupt:
        print("Verification interrupted by user.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Repository CLI — unified entry point for repository tooling.",
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
    )

    # tasks subcommand
    tasks_parser = subparsers.add_parser(
        "tasks",
        help="List repository Tasks",
        description="List and filter Tasks in the Manifest-configured directory.",
    )
    tasks_parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter by canonical status (e.g. completed, in_progress).",
    )
    tasks_parser.add_argument(
        "--workflow",
        type=str,
        default=None,
        help="Filter by declared workflow ID (e.g. standard-change).",
    )

    # inspect subcommand
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a Task by declared Task ID",
        description="Inspect a Task by its declared Task ID.",
    )
    inspect_parser.add_argument(
        "task_id",
        type=str,
        help="Declared Task ID from task.yaml.",
    )

    # verify subcommand
    verify_parser = subparsers.add_parser(
        "verify",
        help="Validate supported AIO structure and project verification checks",
        description=(
            "Validate supported AIO structure and run project-declared verification "
            "checks from .ai/project.yaml using the caller's current environment and "
            "permissions. Declared commands are not sandboxed or isolated."
        ),
    )
    verify_parser.add_argument(
        "--structure",
        action="store_true",
        help=(
            "Validate supported AIO structure only; do not plan, resolve, or execute "
            "project-declared commands."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Parses arguments, discovers the active project from the current working
    directory, and dispatches to the appropriate subcommand handler.

    Args:
        argv: Argument list. Defaults to sys.argv[1:] when None.

    Returns:
        Exit code: 0 for success, 1 for domain issues, 2 for invocation errors.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    # Discover project root from caller's working directory
    try:
        project_root = find_project_root()
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    dispatch = {
        "tasks": cmd_tasks,
        "inspect": cmd_inspect,
        "verify": cmd_verify,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 2

    return handler(args, project_root)


if __name__ == "__main__":
    sys.exit(main())
