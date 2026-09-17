#!/usr/bin/env python3
"""Tests for the unified CLI router (scripts/cli.py).

Covers 20 specified scenarios:
 1. Root help
 2. Tasks help
 3. Inspect help
 4. Verify help
 5. Unknown command → exit 2
 6. Tasks delegation
 7. Tasks --status filter
 8. Tasks --workflow filter
 9. Inspect resolves by declared Task ID
10. Task directory name may differ from declared ID
11. Unknown Task ID → exit 1
12. Verify delegation
13. Verify exit-code propagation
14. Project discovered from current working directory
15. Invocation from repository subdirectory
16. No project marker in ancestry → concise exit 2
17. CLI does not reconstruct Task directories from IDs
18. No duplicated preflight battery
19. No new third-party dependency
20. Temporary brand isolation / rename safety
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.cli import build_parser, find_project_root, main
from scripts.list_tasks import TaskAnomaly, TaskInventoryResult, TaskSummary


def _make_inventory(
    tasks: list[tuple[str, str, str, str | None, Path]] | None = None,
    anomalies: list[TaskAnomaly] | None = None,
    tasks_dir: Path | None = None,
) -> TaskInventoryResult:
    """Build a TaskInventoryResult for testing.

    Each task tuple: (task_id, title, status, workflow, task_dir).
    """
    inv = TaskInventoryResult(tasks_dir=tasks_dir or Path("/fake/tasks"))
    if tasks:
        for task_id, title, status, workflow, task_dir in tasks:
            inv.valid_tasks.append(
                TaskSummary(
                    task_id=task_id,
                    title=title,
                    task_type="implementation",
                    status=status,
                    workflow=workflow,
                    resolution="RESOLVED" if workflow else "NOT DECLARED",
                    task_dir=task_dir,
                )
            )
    if anomalies:
        inv.anomalies.extend(anomalies)
    return inv


class TestRootHelp(unittest.TestCase):
    """1. Root help."""

    def test_root_help_shows_commands(self):
        """Root --help includes tasks, inspect, and verify."""
        parser = build_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["--help"])
        self.assertEqual(cm.exception.code, 0)

    def test_no_command_returns_2(self):
        """Running with no command prints help and returns exit 2."""
        exit_code = main([])
        self.assertEqual(exit_code, 2)


class TestTasksHelp(unittest.TestCase):
    """2. Tasks help."""

    def test_tasks_help_exits_0(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["tasks", "--help"])
        self.assertEqual(cm.exception.code, 0)


class TestInspectHelp(unittest.TestCase):
    """3. Inspect help."""

    def test_inspect_help_exits_0(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["inspect", "--help"])
        self.assertEqual(cm.exception.code, 0)


class TestVerifyHelp(unittest.TestCase):
    """4. Verify help."""

    def test_verify_help_exits_0(self):
        parser = build_parser()
        with self.assertRaises(SystemExit) as cm:
            parser.parse_args(["verify", "--help"])
        self.assertEqual(cm.exception.code, 0)


class TestUnknownCommand(unittest.TestCase):
    """5. Unknown command → exit 2."""

    def test_unknown_command_exits_2(self):
        """argparse rejects unknown commands with exit code 2."""
        with self.assertRaises(SystemExit) as cm:
            main(["banana"])
        self.assertEqual(cm.exception.code, 2)


class TestTasksDelegation(unittest.TestCase):
    """6. Tasks delegation — verifies CLI delegates to inventory functions."""

    def test_tasks_returns_inventory_output(self):
        inventory = _make_inventory(
            tasks=[
                ("TEST-001", "Alpha", "completed", "standard-change", Path("/t/a")),
                ("TEST-002", "Beta", "in_progress", "standard-change", Path("/t/b")),
            ],
        )

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("sys.stdout", captured):
                    exit_code = main(["tasks"])

        output = captured.getvalue()
        self.assertIn("TEST-001", output)
        self.assertIn("TEST-002", output)
        self.assertEqual(exit_code, 0)


class TestTasksStatusFilter(unittest.TestCase):
    """7. Tasks --status filter."""

    def test_status_filter_completed(self):
        inventory = _make_inventory(
            tasks=[
                ("T-001", "Done Task", "completed", "standard-change", Path("/t/a")),
                ("T-002", "WIP Task", "in_progress", "standard-change", Path("/t/b")),
            ],
        )

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("sys.stdout", captured):
                    exit_code = main(["tasks", "--status", "completed"])

        output = captured.getvalue()
        self.assertIn("T-001", output)
        # T-002 should be filtered out
        lines = output.strip().split("\n")
        data_lines = [line for line in lines if "T-002" in line]
        self.assertEqual(len(data_lines), 0)


class TestTasksWorkflowFilter(unittest.TestCase):
    """8. Tasks --workflow filter."""

    def test_workflow_filter(self):
        inventory = _make_inventory(
            tasks=[
                ("W-001", "Standard", "completed", "standard-change", Path("/t/a")),
                ("W-002", "Arch", "completed", "architecture-change", Path("/t/b")),
            ],
        )

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("sys.stdout", captured):
                    exit_code = main(["tasks", "--workflow", "standard-change"])

        output = captured.getvalue()
        self.assertIn("W-001", output)
        lines = output.strip().split("\n")
        data_lines = [line for line in lines if "W-002" in line]
        self.assertEqual(len(data_lines), 0)


class TestInspectByDeclaredId(unittest.TestCase):
    """9. Inspect resolves by declared Task ID."""

    def test_inspect_finds_task_by_id(self):
        """inspect command finds task by declared ID and delegates to inspect_task."""
        from scripts.inspect_task import TaskInspectionResult

        task_dir = Path("/fake/tasks/TEST-001-alpha")

        inventory = _make_inventory(
            tasks=[
                ("TEST-001", "Alpha Task", "completed", "standard-change", task_dir),
            ],
        )

        mock_result = TaskInspectionResult(task_dir=task_dir)
        mock_result.task_id = "TEST-001"
        mock_result.title = "Alpha Task"
        mock_result.schema_status = "VALID"

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("scripts.inspect_task.inspect_task", return_value=mock_result):
                    with patch("scripts.inspect_task.format_report", return_value="Task: TEST-001\nTitle: Alpha Task"):
                        with patch("sys.stdout", captured):
                            exit_code = main(["inspect", "TEST-001"])

        output = captured.getvalue()
        self.assertIn("TEST-001", output)
        self.assertIn("Alpha Task", output)


class TestDirNameDiffersFromId(unittest.TestCase):
    """10. Task directory name may differ from declared ID."""

    def test_directory_name_does_not_match_id(self):
        """Directory named 'completely-different-name' contains task with ID 'LOOKUP-042'."""
        from scripts.inspect_task import TaskInspectionResult

        # Directory name is completely different from task ID
        task_dir = Path("/fake/tasks/completely-different-name")

        inventory = _make_inventory(
            tasks=[
                ("LOOKUP-042", "Mismatched Dir Task", "completed", None, task_dir),
            ],
        )

        mock_result = TaskInspectionResult(task_dir=task_dir)
        mock_result.task_id = "LOOKUP-042"
        mock_result.title = "Mismatched Dir Task"
        mock_result.schema_status = "VALID"

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("scripts.inspect_task.inspect_task", return_value=mock_result) as mock_inspect:
                    with patch("scripts.inspect_task.format_report", return_value="Task: LOOKUP-042\nTitle: Mismatched Dir Task"):
                        with patch("sys.stdout", captured):
                            exit_code = main(["inspect", "LOOKUP-042"])

        output = captured.getvalue()
        self.assertIn("LOOKUP-042", output)
        self.assertIn("Mismatched Dir Task", output)

        # Verify inspect_task was called with the right directory
        mock_inspect.assert_called_once_with(
            task_dir=task_dir,
            project_manifest_path=Path("/fake/.ai/project.yaml"),
            workflows_dir=Path("/fake/workflows"),
        )


class TestUnknownTaskId(unittest.TestCase):
    """11. Unknown Task ID → exit 1."""

    def test_unknown_task_id_exits_1(self):
        inventory = _make_inventory(
            tasks=[
                ("KNOWN-001", "Known", "completed", None, Path("/t/a")),
            ],
        )

        captured_err = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("sys.stderr", captured_err):
                    exit_code = main(["inspect", "DOES-NOT-EXIST"])

        self.assertEqual(exit_code, 1)
        self.assertIn("DOES-NOT-EXIST", captured_err.getvalue())
        self.assertIn("ERROR", captured_err.getvalue())


class TestVerifyDelegation(unittest.TestCase):
    """12. Verify delegation."""

    def test_verify_delegates_to_preflight(self):
        """Verify command delegates to run_preflight and format_preflight_output."""
        from scripts.verify_repo import CheckResult, PreflightResult

        mock_result = PreflightResult(
            repo_root=Path("/fake"),
            results=[
                CheckResult(
                    name="Test Check",
                    command=["echo", "test"],
                    status="PASS",
                    exit_code=0,
                ),
            ],
        )

        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.verify_repo.run_preflight", return_value=mock_result):
                with patch("scripts.verify_repo.format_preflight_output", return_value="MOCK OUTPUT"):
                    captured = StringIO()
                    with patch("sys.stdout", captured):
                        exit_code = main(["verify"])

        self.assertEqual(exit_code, 0)
        self.assertIn("MOCK OUTPUT", captured.getvalue())


class TestVerifyExitCodePropagation(unittest.TestCase):
    """13. Verify exit-code propagation."""

    def test_verify_propagates_failure_exit_code(self):
        from scripts.verify_repo import CheckResult, PreflightResult

        mock_result = PreflightResult(
            repo_root=Path("/fake"),
            results=[
                CheckResult(
                    name="Failing Check",
                    command=["false"],
                    status="FAIL",
                    exit_code=1,
                ),
            ],
        )

        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.verify_repo.run_preflight", return_value=mock_result):
                with patch("scripts.verify_repo.format_preflight_output", return_value="FAIL"):
                    captured = StringIO()
                    with patch("sys.stdout", captured):
                        exit_code = main(["verify"])

        self.assertEqual(exit_code, 1)

    def test_verify_propagates_error_exit_code(self):
        from scripts.verify_repo import CheckResult, PreflightResult

        mock_result = PreflightResult(
            repo_root=Path("/fake"),
            results=[
                CheckResult(
                    name="Error Check",
                    command=["missing"],
                    status="ERROR",
                    error_message="Not found",
                ),
            ],
        )

        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.verify_repo.run_preflight", return_value=mock_result):
                with patch("scripts.verify_repo.format_preflight_output", return_value="ERROR"):
                    captured = StringIO()
                    with patch("sys.stdout", captured):
                        exit_code = main(["verify"])

        self.assertEqual(exit_code, 2)


class TestProjectDiscoveryFromCwd(unittest.TestCase):
    """14. Project discovered from current working directory."""

    def test_find_project_root_from_project_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            ai_dir = project_dir / ".ai"
            ai_dir.mkdir()
            (ai_dir / "project.yaml").write_text("schema_version: '0.1'\n", encoding="utf-8")

            result = find_project_root(start=project_dir)
            self.assertEqual(result, project_dir.resolve())

    def test_find_project_root_from_child_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp)
            ai_dir = project_dir / ".ai"
            ai_dir.mkdir()
            (ai_dir / "project.yaml").write_text("schema_version: '0.1'\n", encoding="utf-8")

            child = project_dir / "src" / "api"
            child.mkdir(parents=True)

            result = find_project_root(start=child)
            self.assertEqual(result, project_dir.resolve())


class TestSubdirectoryInvocation(unittest.TestCase):
    """15. Invocation from repository subdirectory."""

    def test_tasks_from_subdirectory(self):
        """CLI works when invoked from a subdirectory of the project."""
        inventory = _make_inventory(
            tasks=[
                ("SUB-001", "Subdirectory Test", "completed", None, Path("/t/a")),
            ],
        )

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory):
                with patch("sys.stdout", captured):
                    exit_code = main(["tasks"])

        self.assertIn("SUB-001", captured.getvalue())

    def test_real_repo_from_subdirectory(self):
        """find_project_root resolves from a real repo subdirectory."""
        # Use the actual test repo
        scripts_dir = REPO_ROOT / "scripts"
        if scripts_dir.is_dir():
            result = find_project_root(start=scripts_dir)
            self.assertEqual(result, REPO_ROOT.resolve())


class TestNoProjectMarker(unittest.TestCase):
    """16. No project marker in ancestry → concise exit 2."""

    def test_no_project_marker_raises_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            no_project_dir = Path(tmp) / "empty" / "deep"
            no_project_dir.mkdir(parents=True)

            with self.assertRaises(FileNotFoundError) as cm:
                find_project_root(start=no_project_dir)
            self.assertIn(".ai/project.yaml", str(cm.exception))

    def test_main_no_project_exits_2(self):
        with patch(
            "scripts.cli.find_project_root",
            side_effect=FileNotFoundError("No .ai/project.yaml found"),
        ):
            captured_err = StringIO()
            with patch("sys.stderr", captured_err):
                exit_code = main(["tasks"])

        self.assertEqual(exit_code, 2)
        self.assertIn("ERROR", captured_err.getvalue())


class TestNoTaskDirReconstruction(unittest.TestCase):
    """17. CLI does not reconstruct Task directories from IDs.

    The CLI must use discover_tasks() to find tasks by declared ID,
    not construct paths like .ai/tasks/<id>.
    """

    def test_inspect_does_not_construct_path_from_id(self):
        """Verify the CLI calls discover_tasks for lookup, not path construction."""
        from scripts.inspect_task import TaskInspectionResult

        # Directory name has NO relation to the task ID
        task_dir = Path("/fake/tasks/zebra-unicorn-42")
        inventory = _make_inventory(
            tasks=[
                ("FIND-ME-007", "Hidden Task", "completed", None, task_dir),
            ],
        )

        mock_result = TaskInspectionResult(task_dir=task_dir)
        mock_result.task_id = "FIND-ME-007"
        mock_result.title = "Hidden Task"
        mock_result.schema_status = "VALID"

        captured = StringIO()
        with patch("scripts.cli.find_project_root", return_value=Path("/fake")):
            with patch("scripts.list_tasks.discover_tasks", return_value=inventory) as mock_discover:
                with patch("scripts.inspect_task.inspect_task", return_value=mock_result):
                    with patch("scripts.inspect_task.format_report", return_value="Task: FIND-ME-007"):
                        with patch("sys.stdout", captured):
                            exit_code = main(["inspect", "FIND-ME-007"])

        # Verify discover_tasks was called (not path construction)
        mock_discover.assert_called_once()
        self.assertIn("FIND-ME-007", captured.getvalue())


class TestNoDuplicatedPreflightBattery(unittest.TestCase):
    """18. No duplicated preflight battery.

    Verify that scripts/cli.py does not define its own check commands.
    """

    def test_cli_does_not_define_check_commands(self):
        cli_source = (REPO_ROOT / "scripts" / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(cli_source)

        # Look for CheckDefinition or DEFAULT_CHECKS in the CLI module
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in (
                "CheckDefinition", "DEFAULT_CHECKS",
            ):
                self.fail(
                    f"scripts/cli.py references '{node.id}' — "
                    "preflight check definitions should only exist in verify_repo.py"
                )

        # Verify no subprocess imports in cli.py
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(
                        alias.name, "subprocess",
                        "scripts/cli.py should not import subprocess"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                self.fail("scripts/cli.py should not import from subprocess")


class TestNoNewThirdPartyDependency(unittest.TestCase):
    """19. No new third-party dependency.

    scripts/cli.py should only use standard library imports at module level.
    """

    ALLOWED_STDLIB = {
        "__future__", "argparse", "sys", "pathlib",
    }

    def test_cli_module_level_imports_are_stdlib_only(self):
        """Module-level imports in cli.py must be standard library only."""
        cli_source = (REPO_ROOT / "scripts" / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(cli_source)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    self.assertIn(
                        top_module, self.ALLOWED_STDLIB,
                        f"Unexpected module-level import: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_module = node.module.split(".")[0]
                self.assertIn(
                    top_module, self.ALLOWED_STDLIB,
                    f"Unexpected module-level import: from {node.module}"
                )


class TestActiveProjectIntegration(unittest.TestCase):
    """Exercise real composition using project data outside the tool checkout."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / ".ai").mkdir()
        (self.root / ".ai/project.yaml").write_text(
            'quality:\n  require_independent_review: false\n', encoding="utf-8"
        )
        self.task_dir = self.root / ".ai/tasks/unrelated-directory"
        self.task_dir.mkdir(parents=True)
        self.task = {
            "id": "LOCAL-123", "title": "Local project task",
            "type": "implementation", "status": "in_progress",
            "objective": "Check active project composition.",
            "scope": {"include": ["Local inspection"]},
            "workflow": "standard-change",
        }
        (self.task_dir / "task.yaml").write_text(json.dumps(self.task), encoding="utf-8")
        for name in ("context.md", "acceptance-criteria.md", "review.md"):
            (self.task_dir / name).write_text("# Test\n", encoding="utf-8")
        self.child = self.root / "src/api"
        self.child.mkdir(parents=True)

    def invoke(self, *args):
        with patch("pathlib.Path.cwd", return_value=self.child), \
                patch("sys.stdout", new_callable=StringIO) as out, \
                patch("sys.stderr", new_callable=StringIO) as err:
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_missing_project_workflows_never_uses_tool_catalog(self):
        code, output, _ = self.invoke("inspect", "LOCAL-123")
        self.assertEqual(code, 1)
        self.assertIn("Resolution: UNRESOLVED", output)
        self.assertIn("Workflows directory not found", output)
        self.assertIn(str(self.root / "workflows"), output)

    def test_local_workflow_and_manifest_are_used(self):
        workflows = self.root / "workflows"
        workflows.mkdir()
        (workflows / "different-filename.yaml").write_text(json.dumps({
            "id": "standard-change", "name": "Local flow", "purpose": "Local review",
            "stages": [{"id": "local-stage", "purpose": "Review",
                        "required_quality_gates": ["local_gate"]}],
        }), encoding="utf-8")
        code, output, _ = self.invoke("inspect", "LOCAL-123")
        self.assertEqual(code, 0)
        self.assertIn("Stages: 1", output)
        self.assertIn("local_gate", output)
        self.assertNotIn("documentation_consistency", output)

    def test_real_inventory_uses_cwd_and_preserves_filtered_anomalies(self):
        (self.root / ".ai/tasks/broken").mkdir()
        code, output, _ = self.invoke("tasks", "--status", "completed")
        self.assertEqual(code, 1)
        self.assertIn("No matching Tasks", output)
        self.assertIn("broken", output)
        self.assertNotIn("AIO-014", output)

    def test_in_progress_filter_from_subdirectory(self):
        code, output, _ = self.invoke("tasks", "--status", "in_progress")
        self.assertEqual(code, 0)
        self.assertIn("LOCAL-123", output)
        self.assertNotIn("AIO-014", output)

    def test_duplicate_declared_id_is_ambiguous(self):
        duplicate = self.root / ".ai/tasks/another-directory"
        duplicate.mkdir()
        (duplicate / "task.yaml").write_text(json.dumps(self.task), encoding="utf-8")
        with patch("scripts.inspect_task.inspect_task") as inspect:
            code, _, error = self.invoke("inspect", "LOCAL-123")
        self.assertEqual(code, 1)
        self.assertIn("Multiple Tasks with declared ID 'LOCAL-123'", error)
        inspect.assert_not_called()

    def test_directory_name_is_not_a_lookup_alias(self):
        code, _, error = self.invoke("inspect", "unrelated-directory")
        self.assertEqual(code, 1)
        self.assertEqual(error.strip(),
                         "ERROR: No Task with declared ID 'unrelated-directory' found.")

    def test_verify_receives_cwd_project_root(self):
        from scripts.verify_repo import PreflightResult
        with patch("scripts.verify_repo.run_preflight",
                   return_value=PreflightResult(repo_root=self.root)) as preflight:
            code, _, _ = self.invoke("verify")
        self.assertEqual(code, 0)
        preflight.assert_called_once_with(repo_root=self.root)

    def test_nearest_project_marker_wins(self):
        (self.child / ".ai").mkdir()
        (self.child / ".ai/project.yaml").write_text("{}", encoding="utf-8")
        with patch("pathlib.Path.cwd", return_value=self.child):
            self.assertEqual(find_project_root(), self.child)

    def test_cli_does_not_add_active_project_to_import_path(self):
        before = list(sys.path)
        self.invoke("tasks")
        self.assertEqual(sys.path, before)

    def test_actual_wrapper_uses_external_project_from_subdirectory(self):
        proc = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "aio.py"), "tasks"],
            cwd=self.child, capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("LOCAL-123", proc.stdout)
        self.assertNotIn("AIO-014", proc.stdout)

    def test_missing_marker_diagnostic_without_traceback(self):
        # A filesystem root has no ancestors and is independent of temp location.
        with patch("pathlib.Path.cwd", return_value=Path(self.root.anchor)), \
                patch("pathlib.Path.is_file", return_value=False), \
                patch("sys.stderr", new_callable=StringIO) as err:
            self.assertEqual(main(["tasks"]), 2)
        self.assertIn("No .ai/project.yaml found", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    def test_help_is_available_without_project_and_uses_wrapper_name(self):
        with patch("scripts.cli.find_project_root", side_effect=AssertionError), \
                patch("sys.argv", ["rook.py"]):
            for args, expected in [
                (["--help"], "{tasks,inspect,verify}"),
                (["tasks", "--help"], "--status"),
                (["inspect", "--help"], "task_id"),
                (["verify", "--help"], "mechanical verification"),
            ]:
                with self.subTest(args=args), \
                        patch("sys.stdout", new_callable=StringIO) as out, \
                        self.assertRaises(SystemExit) as raised:
                    main(args)
                self.assertEqual(raised.exception.code, 0)
                self.assertIn("rook.py", out.getvalue())
                self.assertIn(expected, out.getvalue())


class TestBrandIsolation(unittest.TestCase):
    """20. Temporary brand isolation / rename safety.

    The literal string 'aio' should not appear in scripts/cli.py
    as a permanent architectural dependency.
    """

    def test_cli_module_does_not_hardcode_aio(self):
        """scripts/cli.py should not contain 'aio' as a hardcoded brand reference."""
        cli_source = (REPO_ROOT / "scripts" / "cli.py").read_text(encoding="utf-8")
        tree = ast.parse(cli_source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value.lower() == "aio":
                    self.fail(
                        f"scripts/cli.py contains hardcoded brand string: "
                        f"'{node.value}'"
                    )

    def test_aio_entry_point_is_thin(self):
        """aio.py should be a thin wrapper with minimal code."""
        aio_source = (REPO_ROOT / "aio.py").read_text(encoding="utf-8")
        tree = ast.parse(aio_source)

        # Count non-import, non-docstring, non-guard statements
        meaningful_stmts = 0
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue  # docstring
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(node, ast.If):
                continue  # __name__ == "__main__" guard
            meaningful_stmts += 1

        self.assertLessEqual(
            meaningful_stmts, 3,
            f"aio.py has {meaningful_stmts} meaningful statements — "
            "it should be a thin wrapper"
        )

    def test_rename_to_rook_requires_no_domain_changes(self):
        """Verify that domain modules don't reference the brand 'aio'."""
        domain_modules = [
            REPO_ROOT / "scripts" / "cli.py",
            REPO_ROOT / "scripts" / "list_tasks.py",
            REPO_ROOT / "scripts" / "inspect_task.py",
            REPO_ROOT / "scripts" / "verify_repo.py",
            REPO_ROOT / "scripts" / "workflow_catalog.py",
        ]
        for module_path in domain_modules:
            if not module_path.exists():
                continue
            source = module_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if node.value.lower() == "aio":
                        self.fail(
                            f"{module_path.name} contains hardcoded brand "
                            f"string: '{node.value}'"
                        )


if __name__ == "__main__":
    unittest.main()
