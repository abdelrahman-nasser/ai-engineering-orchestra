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


from itru.project import find_project_root, task_directory


def cmd_tasks(args: argparse.Namespace, project_root: Path) -> int:
    """Execute the 'tasks' subcommand.

    Delegates to the package's existing Task inventory capability.
    """
    from itru.list_tasks import discover_tasks, format_inventory_table

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
    from itru.inspect_task import format_report, inspect_task
    from itru.list_tasks import discover_tasks

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
    from itru.project_verification import (
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
            "ITRU provides no sandbox or isolation."
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


class _AlphaArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        import json
        from itru.alpha_diagnostics import diagnostic
        self.exit(2, json.dumps({'status': 'rejected', **diagnostic('alpha_arguments_invalid')})+'\n')


def build_parser(*, safe_alpha_errors=False) -> argparse.ArgumentParser:
    """Build the CLI argument parser with subcommands."""
    parser_type = _AlphaArgumentParser if safe_alpha_errors else argparse.ArgumentParser
    parser = parser_type(
        description="Repository CLI — unified entry point for repository tooling.",
    )
    from itru import __version__
    parser.add_argument('--version', action='version', version='itru ' + __version__)
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
        help="Validate supported ITRU structure and project verification checks",
        description=(
            "Validate supported ITRU structure and run project-declared verification "
            "checks from .ai/project.yaml using the caller's current environment and "
            "permissions. Declared commands are not sandboxed or isolated."
        ),
    )
    verify_parser.add_argument(
        "--structure",
        action="store_true",
        help=(
            "Validate supported ITRU structure only; do not plan, resolve, or execute "
            "project-declared commands."
        ),
    )

    alpha = subparsers.add_parser('alpha', help='Local Developer Alpha controlled read workflows')
    commands = alpha.add_subparsers(dest='alpha_command', required=True)
    init = commands.add_parser('init', help='Create a new private Windows local workspace')
    init.add_argument('directory')
    diagnose_help = 'Check local configuration and credential presence offline; no network, owner acquisition or execution'
    diagnose = commands.add_parser('diagnose', help=diagnose_help, description=diagnose_help)
    diagnose.add_argument('--config', required=True, help='Existing private workspace/alpha.json; values are never displayed')
    for name in ('load', 'plan', 'run', 'resume', 'complete', 'stop', 'history'):
        p = commands.add_parser(name)
        p.add_argument('--config', required=True)
        if name == 'load':
            p.add_argument('--work', required=True)
        if name == 'history':
            p.add_argument('--after', type=int, default=0, help='Journal sequence cursor; pages contain at most 100 records')
        if name in ('resume', 'complete', 'stop'):
            p.add_argument('--task', required=True)
        if name in ('run', 'resume', 'complete'):
            p.add_argument('--approve')
        if name in ('complete', 'stop'):
            p.add_argument('--reference', required=True)
        if name == 'plan':
            p.add_argument('--action', choices=('run', 'resume', 'complete'), default='run')
            p.add_argument('--task')
            p.add_argument('--reference')
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
    invocation = sys.argv[1:] if argv is None else argv
    parser = build_parser(safe_alpha_errors=bool(invocation and invocation[0] == 'alpha'))
    args = parser.parse_args(invocation)

    if args.command is None:
        parser.print_help()
        return 2

    if args.command == 'alpha':
        import json
        from itru.developer_alpha import command
        try:
            result = command(args)
            print(json.dumps(result, sort_keys=True))
            return 1 if result.get('status') == 'attention_required' else 0
        except KeyboardInterrupt:
            print('Alpha interrupted; inspect state before any continuation.', file=sys.stderr)
            return 130
        except Exception as exc:
            from itru.alpha_diagnostics import exception_diagnostic
            print(json.dumps({'status': 'rejected', **exception_diagnostic(exc)}), file=sys.stderr)
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
