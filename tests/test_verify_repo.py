#!/usr/bin/env python3
"""AI Engineering Orchestra — Unit Tests for Repository Preflight Utility.

Tests cover all required scenarios for AIO-014 without executing recursive
preflight runs during test discovery:
1. all seven checks pass -> exit 0
2. one verification check fails -> remaining checks still execute
3. multiple checks fail -> complete summary produced
4. ordinary check failures -> overall exit 1
5. executable launch failure -> status ERROR
6. infrastructure ERROR -> overall exit 2
7. checks after one ERROR continue where safely possible
8. deterministic check order
9. repository root used as subprocess cwd
10. stdout/stderr captured
11. successful subprocess noise not dumped into normal summary
12. failed check diagnostics available
13. ERROR diagnostics available
14. command execution uses argument lists / shell=False
15. no Task loading or --task flag
16. no Quality Gate IDs or gate-result mapping
17. unit test recursion prevented
18. caller working directory independence
"""

from __future__ import annotations

import ast
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.verify_repo import (
    DEFAULT_CHECKS,
    CheckDefinition,
    CheckResult,
    PreflightResult,
    default_runner,
    find_repo_root,
    format_preflight_output,
    main,
    resolve_executable,
    run_check,
    run_preflight,
)


class TestVerifyRepo(unittest.TestCase):
    """Test suite for repository preflight verification utility."""

    def setUp(self) -> None:
        self.repo_root = find_repo_root()

    def test_all_seven_checks_pass_exit_zero(self) -> None:
        """Scenario 1: All seven checks pass -> exit 0."""
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)

        self.assertEqual(result.total_count, 7)
        self.assertEqual(result.passed_count, 7)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.exit_code, 0)

        output = format_preflight_output(result)
        self.assertIn("Summary: 7/7 checks passed", output)
        self.assertNotIn("--- Failure Diagnostics ---", output)

    def test_one_check_fails_remaining_checks_execute(self) -> None:
        """Scenario 2: One check fails -> remaining checks still execute."""
        executed: list[str] = []

        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            # Fail only Task Validation (second check)
            executed.append(cmd[0])
            if "validate_task.py" in " ".join(cmd):
                return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="Validation error", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)

        self.assertEqual(len(result.results), 7)
        self.assertEqual(result.passed_count, 6)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.results[1].name, "Task Validation")
        self.assertEqual(result.results[1].status, "FAIL")
        # Ensure checks after the failed one still executed
        self.assertEqual(result.results[2].status, "PASS")
        self.assertEqual(result.results[6].status, "PASS")
        self.assertEqual(result.exit_code, 1)

    def test_multiple_checks_fail_complete_summary(self) -> None:
        """Scenario 3: Multiple checks fail -> complete summary produced."""
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            cmd_str = " ".join(cmd)
            if "validate_task.py" in cmd_str or "markdownlint" in cmd_str:
                return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="lint/task fail", stderr="")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)

        self.assertEqual(result.total_count, 7)
        self.assertEqual(result.passed_count, 5)
        self.assertEqual(result.failed_count, 2)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.exit_code, 1)

        output = format_preflight_output(result)
        self.assertIn("Summary: 5/7 checks passed", output)
        self.assertIn("5 PASS", output)
        self.assertIn("2 FAIL", output)
        self.assertIn("0 ERROR", output)

    def test_ordinary_check_failures_exit_code_one(self) -> None:
        """Scenario 4: Ordinary check failures result in overall exit 1."""
        res = PreflightResult(
            repo_root=self.repo_root,
            results=[
                CheckResult(name="Test 1", command=["t1"], status="PASS", exit_code=0),
                CheckResult(name="Test 2", command=["t2"], status="FAIL", exit_code=1),
            ],
        )
        self.assertEqual(res.exit_code, 1)

    def test_executable_launch_failure_reports_error(self) -> None:
        """Scenario 5: Executable launch failure produces status ERROR."""
        check = CheckDefinition(name="Missing Tool", command=["nonexistent_executable_aio_014", "arg1"])
        result = run_check(check, self.repo_root)

        self.assertEqual(result.status, "ERROR")
        self.assertIsNone(result.exit_code)
        self.assertIsNotNone(result.error_message)
        self.assertIn("Unable to launch nonexistent_executable_aio_014", result.error_message)

    def test_infrastructure_error_overall_exit_two(self) -> None:
        """Scenario 6: Infrastructure or execution error results in overall exit 2."""
        res = PreflightResult(
            repo_root=self.repo_root,
            results=[
                CheckResult(name="Test 1", command=["t1"], status="PASS", exit_code=0),
                CheckResult(name="Test 2", command=["t2"], status="ERROR", error_message="cannot launch"),
            ],
        )
        self.assertEqual(res.exit_code, 2)

        # Also verify infrastructure_error field forces exit code 2
        res_infra = PreflightResult(
            repo_root=self.repo_root,
            results=[CheckResult(name="Test 1", command=["t1"], status="PASS", exit_code=0)],
            infrastructure_error="Internal failure",
        )
        self.assertEqual(res_infra.exit_code, 2)

    def test_checks_after_one_error_continue(self) -> None:
        """Scenario 7: Checks continue after one ERROR where safely possible."""
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            cmd_str = " ".join(cmd)
            if "validate_workflow.py" in cmd_str:
                raise OSError("Simulated execution failure")
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="ok", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)

        self.assertEqual(result.total_count, 7)
        self.assertEqual(result.passed_count, 6)
        self.assertEqual(result.error_count, 1)
        self.assertEqual(result.results[2].name, "Workflow Validation")
        self.assertEqual(result.results[2].status, "ERROR")
        # Remaining checks continued
        self.assertEqual(result.results[3].status, "PASS")
        self.assertEqual(result.results[6].status, "PASS")
        self.assertEqual(result.exit_code, 2)

    def test_deterministic_check_order(self) -> None:
        """Scenario 8: Deterministic check order strictly matches DEFAULT_CHECKS."""
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)
        expected_names = [
            "Unit Tests",
            "Task Validation",
            "Workflow Validation",
            "Role Validation",
            "Project Manifest Validation",
            "Markdown Lint",
            "Git Diff Check",
        ]
        actual_names = [r.name for r in result.results]
        self.assertEqual(actual_names, expected_names)

    def test_repository_root_used_as_subprocess_cwd(self) -> None:
        """Scenario 9: Repository root is passed as subprocess cwd for all checks."""
        recorded_cwds: list[Path] = []

        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            recorded_cwds.append(cwd)
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        run_preflight(repo_root=self.repo_root, runner=fake_runner)

        self.assertEqual(len(recorded_cwds), 7)
        for cwd in recorded_cwds:
            self.assertEqual(cwd, self.repo_root)

    def test_stdout_stderr_captured(self) -> None:
        """Scenario 10: Stdout and stderr are captured on check execution."""
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="Standard output content",
                stderr="Standard error content",
            )

        check = CheckDefinition(name="Custom Check", command=[sys.executable, "-c", ""])
        res = run_check(check, self.repo_root, runner=fake_runner)

        self.assertEqual(res.stdout, "Standard output content")
        self.assertEqual(res.stderr, "Standard error content")
        self.assertEqual(res.exit_code, 1)

    def test_successful_subprocess_noise_suppressed(self) -> None:
        """Scenario 11: Successful subprocess noise is not dumped into normal summary."""
        huge_noisy_output = "NOISY TEST LOG LINE\n" * 500

        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=huge_noisy_output, stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)
        output = format_preflight_output(result)

        self.assertNotIn("NOISY TEST LOG LINE", output)
        self.assertIn("Unit Tests                     PASS", output)
        self.assertIn("Summary: 7/7 checks passed", output)

    def test_failed_check_diagnostics_available(self) -> None:
        """Scenario 12: Failed check diagnostics are captured and formatted."""
        res = PreflightResult(
            repo_root=self.repo_root,
            results=[
                CheckResult(
                    name="Task Validation",
                    command=["python", "val.py"],
                    status="FAIL",
                    exit_code=1,
                    stdout="FAIL: schema validation failed at line 42",
                    stderr="",
                )
            ],
        )
        output = format_preflight_output(res)

        self.assertIn("Task Validation                FAIL", output)
        self.assertIn("--- Failure Diagnostics ---", output)
        self.assertIn("[Task Validation] (exit code 1):", output)
        self.assertIn("FAIL: schema validation failed at line 42", output)

    def test_error_diagnostics_available(self) -> None:
        """Scenario 13: ERROR diagnostics are captured and formatted."""
        res = PreflightResult(
            repo_root=self.repo_root,
            results=[
                CheckResult(
                    name="Markdown Lint",
                    command=["npx", "markdownlint-cli2"],
                    status="ERROR",
                    error_message="Unable to launch npx: executable not found on PATH",
                )
            ],
        )
        output = format_preflight_output(res)

        self.assertIn("Markdown Lint                  ERROR", output)
        self.assertIn("Unable to launch npx: executable not found on PATH", output)
        self.assertIn("0 PASS", output)
        self.assertIn("1 ERROR", output)

    def test_command_execution_uses_argument_lists_shell_false(self) -> None:
        """Scenario 14: Commands use argument arrays with shell=False."""
        for check in DEFAULT_CHECKS:
            self.assertIsInstance(check.command, list)
            self.assertGreaterEqual(len(check.command), 1)
            for part in check.command:
                self.assertIsInstance(part, str)

        # Verify default_runner executes with shell=False
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            default_runner(["echo", "hello"], cwd=self.repo_root)
            mock_run.assert_called_once()
            _, kwargs = mock_run.call_args
            self.assertFalse(kwargs.get("shell", True))

    def test_no_task_loading(self) -> None:
        """Scenario 15: No Task loading or --task argument."""
        # Preflight utility rejects --task argument
        with self.assertRaises(SystemExit):
            with redirect_stderr(io.StringIO()):
                main(["--task", "AIO-014"])

        # Check that verify_repo does not import task inspection utilities
        import scripts.verify_repo as vr
        self.assertFalse(hasattr(vr, "inspect_task"))
        self.assertFalse(hasattr(vr, "list_tasks"))
        self.assertFalse(hasattr(vr, "TaskInspectionResult"))

        # Inspect AST of verify_repo.py for task imports
        vr_source = Path(vr.__file__).resolve().read_text(encoding="utf-8")
        tree = ast.parse(vr_source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn("inspect_task", alias.name)
                    self.assertNotIn("list_tasks", alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.assertNotIn("inspect_task", node.module)
                    self.assertNotIn("list_tasks", node.module)

    def test_no_quality_gate_ids_or_gate_mapping(self) -> None:
        """Scenario 16: No Quality Gate IDs or gate-result mapping."""
        gate_ids = [
            "documentation_consistency",
            "independent_review",
            "breaking_change_declaration",
            "quality_gate",
        ]
        # Inspect check definitions
        for check in DEFAULT_CHECKS:
            for gate in gate_ids:
                self.assertNotIn(gate, check.name.lower())
                self.assertNotIn(gate, " ".join(check.command).lower())

        # Inspect preflight output
        def fake_runner(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

        result = run_preflight(repo_root=self.repo_root, runner=fake_runner)
        output = format_preflight_output(result)
        for gate in gate_ids:
            self.assertNotIn(gate, output.lower())

    def test_no_recursive_real_preflight_in_unit_tests(self) -> None:
        """Scenario 17: Verify test suite prevents recursive preflight execution."""
        # Inspect AST of this test file to ensure it never calls verify_repo.py in unmocked subprocess
        test_file = Path(__file__).resolve()
        source = test_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "run" and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                    # Any direct subprocess.run in tests must not execute verify_repo.py
                    for arg in node.args:
                        if isinstance(arg, (ast.Str, ast.Constant)):
                            self.assertNotIn("verify_repo.py", str(arg.value))

    def test_caller_cwd_independence(self) -> None:
        """Scenario 18: Utility resolves repository root independently of caller cwd."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            orig_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                # find_repo_root with default (None) resolves from __file__, not cwd
                resolved_root = find_repo_root()
                self.assertEqual(resolved_root, self.repo_root)
                self.assertTrue((resolved_root / ".ai" / "project.yaml").is_file())
            finally:
                os.chdir(orig_cwd)

    def test_main_cli_execution_clean(self) -> None:
        """Verify main() executes preflight and returns exit code 0 when all checks pass."""
        with patch("scripts.verify_repo.run_preflight") as mock_run:
            mock_run.return_value = PreflightResult(
                repo_root=self.repo_root,
                results=[
                    CheckResult(name=c.name, command=c.command, status="PASS", exit_code=0)
                    for c in DEFAULT_CHECKS
                ],
            )
            with redirect_stdout(io.StringIO()):
                code = main([])
            self.assertEqual(code, 0)

    def test_main_cli_execution_failure(self) -> None:
        """Verify main() returns exit code 1 when a check fails."""
        with patch("scripts.verify_repo.run_preflight") as mock_run:
            mock_run.return_value = PreflightResult(
                repo_root=self.repo_root,
                results=[
                    CheckResult(name="Unit Tests", command=["ut"], status="FAIL", exit_code=1, stdout="fail")
                ],
            )
            with redirect_stdout(io.StringIO()):
                code = main([])
            self.assertEqual(code, 1)

    def test_main_cli_execution_infrastructure_error(self) -> None:
        """Verify main() returns exit code 2 on repository root resolution failure."""
        with patch("scripts.verify_repo.find_repo_root", side_effect=RuntimeError("Cannot find root")):
            with redirect_stderr(io.StringIO()):
                code = main([])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
