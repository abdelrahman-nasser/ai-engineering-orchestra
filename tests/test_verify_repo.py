"""Aggregate verification and compatibility regressions for AIO-020."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from engineering_orchestration import project_verification as verification
from engineering_orchestration.project_verification import (
    VERIFY_DEPTH_ENV,
    ProjectVerificationResult,
    VerificationCheckResult,
    VerificationRunResult,
    format_project_verification_output,
    format_verification_output,
    verify_project,
)
from engineering_orchestration.verify_repo import (
    format_preflight_output,
    run_preflight,
)


ROOT = Path(__file__).resolve().parents[1]


class AggregateProjectFixture(unittest.TestCase):
    def setUp(self) -> None:
        inherited_depth = os.environ.pop(VERIFY_DEPTH_ENV, None)

        def restore_depth() -> None:
            if inherited_depth is None:
                os.environ.pop(VERIFY_DEPTH_ENV, None)
            else:
                os.environ[VERIFY_DEPTH_ENV] = inherited_depth

        self.addCleanup(restore_depth)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve() / "project"
        (self.root / ".ai" / "tasks").mkdir(parents=True)
        (self.root / "workflows").mkdir()
        self.manifest = {
            "schema_version": "0.1",
            "project": {
                "id": "external",
                "name": "External",
                "type": "application",
                "lifecycle": "greenfield",
            },
            "orchestra": {"version": "0.1.0"},
            "complexity": {"default": "medium"},
            "risk": {"default": "low"},
            "execution": {"default_mode": "standard"},
            "human_control": {},
            "quality": {},
        }
        self.write_manifest()

    def write_manifest(self) -> None:
        (self.root / ".ai" / "project.yaml").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

    def set_checks(self, checks: list[dict]) -> None:
        self.manifest["verification"] = {"checks": checks}
        self.write_manifest()

    @staticmethod
    def python_check(check_id: str, code: str, **extra) -> dict:
        return {"id": check_id, "command": [sys.executable, "-c", code], **extra}


class AggregateVerificationTests(AggregateProjectFixture):
    def test_omitted_and_empty_checks_execute_zero_commands(self) -> None:
        for empty in (False, True):
            with self.subTest(empty=empty):
                if empty:
                    self.set_checks([])
                with patch.object(verification, "_execute_check",
                                  side_effect=AssertionError("no command expected")):
                    result = verify_project(self.root)
                self.assertEqual(result.status, "PASS")
                self.assertEqual(result.exit_code, 0)
                self.assertEqual(result.execution.results, ())
                self.assertIn("0 project checks configured", format_verification_output(result))

    def test_all_pass_and_declaration_order(self) -> None:
        self.set_checks([
            self.python_check("first", "print('suppressed-secret')"),
            self.python_check("second", "raise SystemExit(0)"),
        ])
        announced = []
        result = verify_project(
            self.root,
            before_execute=lambda plan: announced.extend(item.id for item in plan.checks),
        )
        self.assertEqual(announced, ["first", "second"])
        self.assertEqual(result.status, "PASS")
        self.assertNotIn("suppressed-secret", format_verification_output(result))

    def test_nonzero_including_two_is_fail_and_later_checks_continue(self) -> None:
        marker = self.root / "continued"
        self.set_checks([
            self.python_check("child-two", "raise SystemExit(2)"),
            self.python_check("later", f"from pathlib import Path; Path({str(marker)!r}).touch()"),
        ])
        result = verify_project(self.root)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.execution.results[0].return_code, 2)
        self.assertEqual(result.execution.results[0].status, "FAIL")
        self.assertTrue(marker.exists())

    def test_missing_executable_is_error_and_later_check_continues(self) -> None:
        marker = self.root / "continued"
        self.set_checks([
            {"id": "missing", "command": ["missing-aio020-executable"]},
            self.python_check("later", f"from pathlib import Path; Path({str(marker)!r}).touch()"),
        ])
        result = verify_project(self.root)
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.exit_code, 2)
        self.assertEqual([item.status for item in result.execution.results], ["ERROR", "PASS"])
        self.assertTrue(marker.exists())

    def test_error_dominates_fail(self) -> None:
        self.set_checks([
            self.python_check("failure", "raise SystemExit(1)"),
            {"id": "missing", "command": ["missing-aio020-executable"]},
        ])
        result = verify_project(self.root)
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.exit_code, 2)

    def test_invalid_task_does_not_block_ready_plan(self) -> None:
        task = self.root / ".ai" / "tasks" / "invalid" / "task.yaml"
        task.parent.mkdir()
        task.write_text("[]", encoding="utf-8")
        marker = self.root / "task-check-ran"
        self.set_checks([
            self.python_check("tests", f"from pathlib import Path; Path({str(marker)!r}).touch()"),
        ])
        result = verify_project(self.root)
        self.assertEqual(result.structural.status, "FAIL")
        self.assertTrue(result.planning.is_ready)
        self.assertEqual(result.execution.status, "PASS")
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(marker.exists())

    def test_invalid_workflow_does_not_block_ready_plan(self) -> None:
        (self.root / "workflows" / "invalid.yaml").write_text("[]", encoding="utf-8")
        marker = self.root / "workflow-check-ran"
        self.set_checks([
            self.python_check("tests", f"from pathlib import Path; Path({str(marker)!r}).touch()"),
        ])
        result = verify_project(self.root)
        self.assertEqual(result.structural.status, "FAIL")
        self.assertTrue(result.planning.is_ready)
        self.assertEqual(result.execution.status, "PASS")
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(marker.exists())

    def test_invalid_manifest_blocks_execution_and_is_not_duplicated(self) -> None:
        self.manifest["unexpected"] = True
        self.write_manifest()
        with patch.object(verification, "run_project_checks",
                          side_effect=AssertionError("runner must not execute")):
            result = verify_project(self.root)
        self.assertEqual(result.structural.status, "FAIL")
        self.assertFalse(result.planning.is_ready)
        self.assertEqual(result.exit_code, 1)
        output = format_verification_output(result)
        self.assertEqual(output.count("Additional properties are not allowed"), 1)

    def test_malformed_manifest_blocks_execution_and_is_not_duplicated(self) -> None:
        (self.root / ".ai" / "project.yaml").write_text("project: [", encoding="utf-8")
        with patch.object(verification, "run_project_checks",
                          side_effect=AssertionError("runner must not execute")):
            result = verify_project(self.root)
        self.assertEqual(result.exit_code, 1)
        output = format_verification_output(result)
        self.assertEqual(output.count("while parsing"), 1)

    def test_duplicate_manifest_ids_block_execution_and_are_not_duplicated(self) -> None:
        duplicate = self.python_check("same", "raise SystemExit(0)")
        self.set_checks([duplicate, dict(duplicate)])
        with patch.object(verification, "run_project_checks",
                          side_effect=AssertionError("runner must not execute")):
            result = verify_project(self.root)
        self.assertEqual(result.exit_code, 1)
        output = format_verification_output(result)
        self.assertEqual(output.count("Duplicate Verification Check ID"), 1)

    def test_planning_cwd_error_blocks_all_commands(self) -> None:
        self.set_checks([
            self.python_check("missing-cwd", "raise SystemExit(0)", cwd="absent"),
            self.python_check("later", "raise AssertionError('must not run')"),
        ])
        with patch.object(verification, "run_project_checks",
                          side_effect=AssertionError("runner must not execute")):
            result = verify_project(self.root)
        self.assertEqual(result.structural.status, "PASS")
        self.assertEqual(result.planning.status, "ERROR")
        self.assertEqual(result.exit_code, 2)

    def test_structure_mode_calls_only_structural_validation(self) -> None:
        os.environ[VERIFY_DEPTH_ENV] = "malformed"
        self.addCleanup(os.environ.pop, VERIFY_DEPTH_ENV, None)
        with patch.object(verification, "validate_project",
                          wraps=verification.validate_project) as validate, \
                patch.object(verification, "plan_project_checks",
                             side_effect=AssertionError("must not plan")), \
                patch.object(verification, "run_project_checks",
                             side_effect=AssertionError("must not run")), \
                patch.object(verification, "resolve_executable",
                             side_effect=AssertionError("must not resolve")):
            result = verify_project(self.root, execute_checks=False)
        validate.assert_called_once_with(self.root)
        self.assertEqual(result.status, "PASS")
        self.assertIsNone(result.planning)
        self.assertIsNone(result.execution)
        self.assertEqual(os.environ[VERIFY_DEPTH_ENV], "malformed")


class RecursionTests(AggregateProjectFixture):
    def test_nonzero_and_malformed_marker_reject_before_planning(self) -> None:
        for value in ("1", "2", "invalid", ""):
            with self.subTest(value=value), patch.dict(os.environ, {VERIFY_DEPTH_ENV: value}), \
                    patch.object(verification, "plan_project_checks",
                                 side_effect=AssertionError("nested call must not plan")):
                result = verify_project(self.root)
            self.assertEqual(result.exit_code, 2)
            self.assertIn("Nested project verification rejected", result.infrastructure_error)

    def test_zero_marker_is_allowed_and_restored(self) -> None:
        self.set_checks([])
        with patch.dict(os.environ, {VERIFY_DEPTH_ENV: "0"}):
            result = verify_project(self.root)
            self.assertEqual(os.environ[VERIFY_DEPTH_ENV], "0")
        self.assertEqual(result.exit_code, 0)

    def test_unset_marker_is_removed_after_execution(self) -> None:
        self.set_checks([])
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(VERIFY_DEPTH_ENV, None)
            result = verify_project(self.root)
            self.assertNotIn(VERIFY_DEPTH_ENV, os.environ)
        self.assertEqual(result.exit_code, 0)

    def test_marker_is_restored_on_keyboard_interrupt(self) -> None:
        self.set_checks([])
        with patch.dict(os.environ, {VERIFY_DEPTH_ENV: "0"}), \
                patch.object(verification, "run_project_checks", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                verify_project(self.root)
            self.assertEqual(os.environ[VERIFY_DEPTH_ENV], "0")

    def test_marker_is_restored_on_unexpected_runner_exception(self) -> None:
        self.set_checks([])
        with patch.dict(os.environ, {VERIFY_DEPTH_ENV: "0"}), \
                patch.object(verification, "run_project_checks",
                             side_effect=RuntimeError("unexpected")):
            with self.assertRaisesRegex(RuntimeError, "unexpected"):
                verify_project(self.root)
            self.assertEqual(os.environ[VERIFY_DEPTH_ENV], "0")

    def test_guard_name_is_brand_neutral(self) -> None:
        self.assertEqual(VERIFY_DEPTH_ENV, "ENGINEERING_ORCHESTRATION_VERIFY_DEPTH")
        self.assertNotIn("AIO", VERIFY_DEPTH_ENV)


class OutputAndCompatibilityTests(AggregateProjectFixture):
    def test_failed_result_shows_return_code_duration_and_bounded_streams(self) -> None:
        plan = verification.plan_project_checks(self.root).plan
        run = VerificationRunResult(
            plan=plan,
            results=(VerificationCheckResult(
                id="failure", command=("tool",), cwd=self.root, status="FAIL",
                return_code=-9, duration_seconds=1.25,
                stdout_excerpt="bounded-out", stderr_excerpt="bounded-error",
            ),),
        )
        output = format_project_verification_output(run)
        for expected in ("failure", "FAIL", "1.250s", "Return code: -9",
                         "bounded-out", "bounded-error"):
            self.assertIn(expected, output)

    def test_fatal_runner_error_is_counted_in_summary(self) -> None:
        plan = verification.plan_project_checks(self.root).plan
        output = format_project_verification_output(
            VerificationRunResult(plan=plan, fatal_error="broken session")
        )
        self.assertIn("1 ERROR", output)

    def test_run_preflight_and_formatter_are_thin_delegates(self) -> None:
        sentinel = ProjectVerificationResult(structural=verification.validate_project(self.root))
        with patch("engineering_orchestration.verify_repo.verify_project",
                   return_value=sentinel) as aggregate:
            self.assertIs(run_preflight(self.root), sentinel)
        aggregate.assert_called_once_with(
            self.root, execute_checks=True, before_execute=None
        )
        self.assertEqual(format_preflight_output(sentinel), format_verification_output(sentinel))

    def test_no_active_default_checks_or_legacy_runner(self) -> None:
        import engineering_orchestration.verify_repo as compatibility

        self.assertFalse(hasattr(compatibility, "DEFAULT_CHECKS"))
        source = Path(compatibility.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.name for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertNotIn("run_check", names)
        self.assertNotIn("default_runner", names)

    def test_orchestra_manifest_is_only_seven_check_source_in_required_order(self) -> None:
        import yaml

        manifest = yaml.safe_load((ROOT / ".ai" / "project.yaml").read_text(encoding="utf-8"))
        checks = manifest["verification"]["checks"]
        self.assertEqual(checks, [
            {"id": "unit-tests", "command": [
                "python", "-B", "-m", "unittest", "discover", "-s", "tests",
                "-p", "test_*.py", "-v",
            ]},
            {"id": "task-validator", "command": [
                "python", "-B", "schemas/tests/validate_task.py",
            ]},
            {"id": "workflow-validator", "command": [
                "python", "-B", "schemas/tests/validate_workflow.py",
            ]},
            {"id": "role-validator", "command": [
                "python", "-B", "schemas/tests/validate_role.py",
            ]},
            {"id": "manifest-validator", "command": [
                "python", "-B", "schemas/tests/validate_project_manifest.py",
            ]},
            {"id": "markdown-lint", "command": [
                "npx", "--yes", "markdownlint-cli2", "**/*.md",
            ]},
            {"id": "git-diff-check", "command": [
                "git", "diff", "--check",
            ]},
        ])
        self.assertTrue(all(set(item) <= {"id", "command", "cwd", "timeout_seconds"}
                            for item in checks))

    def test_four_field_schema_contract_is_unchanged(self) -> None:
        schema = json.loads((ROOT / "schemas" / "project-manifest.schema.json").read_text())
        self.assertEqual(
            set(schema["$defs"]["verificationCheck"]["properties"]),
            {"id", "command", "cwd", "timeout_seconds"},
        )


if __name__ == "__main__":
    unittest.main()
