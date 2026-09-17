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


def find_project_root(start: Path | None = None) -> Path:
    """Discover the project root by walking up from start to find .ai/project.yaml.

    The active project is determined from the caller's context (current working
    directory), not from the physical location of CLI source files. This ensures
    correct behavior both during source development and after package installation.

    Args:
        start: Starting directory for upward search. Defaults to Path.cwd().

    Returns:
        Resolved Path to the project root directory.

    Raises:
        FileNotFoundError: If no .ai/project.yaml exists in start or any parent.
    """
    if start is None:
        start = Path.cwd()
    candidate = start.resolve()
    if (candidate / ".ai" / "project.yaml").is_file():
        return candidate
    for parent in candidate.parents:
        if (parent / ".ai" / "project.yaml").is_file():
            return parent
    raise FileNotFoundError(
        f"No .ai/project.yaml found in '{start}' or any parent directory."
    )


def cmd_tasks(args: argparse.Namespace, project_root: Path) -> int:
    """Execute the 'tasks' subcommand.

    Delegates to the package's existing Task inventory capability.
    """
    from engineering_orchestration.list_tasks import discover_tasks, format_inventory_table

    tasks_dir = project_root / ".ai" / "tasks"

    try:
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

    tasks_dir = project_root / ".ai" / "tasks"

    try:
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
    """Execute the 'verify' subcommand.

    Delegates to the package's existing repository preflight capability.
    """
    from engineering_orchestration.verify_repo import format_preflight_output, run_preflight

    try:
        preflight = run_preflight(repo_root=project_root)
    except Exception as exc:
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 2

    print(format_preflight_output(preflight))
    return preflight.exit_code


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
        description="List and filter repository Tasks under .ai/tasks/.",
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
    subparsers.add_parser(
        "verify",
        help="Run repository mechanical verification",
        description="Run the repository mechanical verification battery.",
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
