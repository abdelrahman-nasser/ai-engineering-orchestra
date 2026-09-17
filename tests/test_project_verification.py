"""Focused programmatic tests for Project Verification planning and execution."""

from __future__ import annotations

import ast
from contextlib import nullcontext
from dataclasses import FrozenInstanceError, fields
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from engineering_orchestration import project_verification as verification
from engineering_orchestration.project_verification import (
    DEFAULT_TIMEOUT_SECONDS,
    DIAGNOSTIC_EXCERPT_LIMIT,
    VerificationCheckResult,
    format_project_verification_output,
    plan_project_checks,
    resolve_executable,
    run_project_checks,
)


class ProjectFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "project"
        (self.root / ".ai").mkdir(parents=True)
        self.manifest = {
            "schema_version": "0.1",
            "project": {
                "id": "fixture",
                "name": "Fixture",
                "type": "application",
                "lifecycle": "greenfield",
            },
            "orchestra": {"version": "0.1.0"},
            "complexity": {"default": "medium"},
            "risk": {"default": "medium"},
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

    def check(
        self,
        check_id: str,
        command: list[str],
        *,
        cwd: str | None = None,
        timeout: int | None = None,
    ) -> dict:
        result: dict = {"id": check_id, "command": command}
        if cwd is not None:
            result["cwd"] = cwd
        if timeout is not None:
            result["timeout_seconds"] = timeout
        return result

    def ready_plan(self):
        planned = plan_project_checks(self.root)
        self.assertTrue(planned.is_ready, planned.findings)
        self.assertIsNotNone(planned.plan)
        return planned.plan

    def python_check(
        self,
        check_id: str,
        code: str,
        *,
        cwd: str | None = None,
        timeout: int | None = None,
        arguments: list[str] | None = None,
    ) -> dict:
        command = [sys.executable, "-c", code]
        if arguments:
            command.extend(arguments)
        return self.check(check_id, command, cwd=cwd, timeout=timeout)

    def make_relative_program(
        self,
        relative_parent: str = "tools",
        name: str = "check",
        *,
        exit_code: int = 0,
    ) -> tuple[Path, str]:
        parent = self.root / relative_parent
        parent.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            path = parent / f"{name}.cmd"
            path.write_text(
                f"@echo off\r\necho relative-stdout\r\nexit /b {exit_code}\r\n",
                encoding="utf-8",
            )
        else:
            path = parent / name
            path.write_text(
                f"#!/bin/sh\necho relative-stdout\nexit {exit_code}\n",
                encoding="utf-8",
            )
            path.chmod(0o755)
        return path, path.relative_to(self.root).as_posix()

    def resolution_loop_patch(self, target: Path):
        """Simulate Python 3.12 Path.resolve's symlink-loop RuntimeError."""

        original_resolve = Path.resolve

        def resolve(path, *args, **kwargs):
            if path == target:
                raise RuntimeError("Symlink loop from test fixture")
            return original_resolve(path, *args, **kwargs)

        return patch.object(Path, "resolve", autospec=True, side_effect=resolve)


class VerificationPlanningTests(ProjectFixture):
    def test_absent_verification_is_successful_empty_plan(self) -> None:
        plan = self.ready_plan()
        self.assertEqual(plan.checks, ())
        run = run_project_checks(plan)
        self.assertEqual(run.status, "PASS")
        self.assertEqual(run.exit_code, 0)
        self.assertIn("0 project checks configured", format_project_verification_output(run))

    def test_empty_checks_is_successful_empty_plan(self) -> None:
        self.set_checks([])
        self.assertEqual(self.ready_plan().checks, ())

    def test_declaration_order_defaults_and_commands_are_materialized(self) -> None:
        self.set_checks([
            self.check("z-first", [sys.executable, "", "a b"]),
            self.check("a-second", [sys.executable], timeout=7),
        ])
        plan = self.ready_plan()
        self.assertEqual([item.id for item in plan.checks], ["z-first", "a-second"])
        self.assertEqual(plan.checks[0].command, (sys.executable, "", "a b"))
        self.assertEqual(plan.checks[0].timeout_seconds, DEFAULT_TIMEOUT_SECONDS)
        self.assertEqual(plan.checks[1].timeout_seconds, 7)
        self.assertEqual(plan.checks[0].cwd, self.root.resolve())
        self.assertIsNone(plan.checks[0].declared_cwd)

    def test_contained_and_space_cwds_resolve(self) -> None:
        first = self.root / "backend"
        second = self.root / "space folder"
        first.mkdir()
        second.mkdir()
        self.set_checks([
            self.check("backend", [sys.executable], cwd="backend"),
            self.check("spaces", [sys.executable], cwd="space folder"),
        ])
        plan = self.ready_plan()
        self.assertEqual(plan.checks[0].cwd, first.resolve())
        self.assertEqual(plan.checks[1].cwd, second.resolve())

    def test_normalized_contained_parent_segment_resolves(self) -> None:
        (self.root / "backend").mkdir()
        frontend = self.root / "frontend"
        frontend.mkdir()
        self.set_checks([
            self.check("normalized", [sys.executable], cwd="backend/../frontend")
        ])
        self.assertEqual(self.ready_plan().checks[0].cwd, frontend.resolve())

    def test_outside_traversal_is_planning_error(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        self.set_checks([
            self.check("escape", [sys.executable], cwd="../outside")
        ])
        result = plan_project_checks(self.root)
        self.assertFalse(result.is_ready)
        self.assertEqual(result.status, "ERROR")
        self.assertIn("outside project root", result.findings[0].message)

    def test_missing_and_file_cwds_are_both_reported_before_a_plan_exists(self) -> None:
        (self.root / "not-a-directory").write_text("file", encoding="utf-8")
        self.set_checks([
            self.check("missing", [sys.executable], cwd="absent"),
            self.check("file", [sys.executable], cwd="not-a-directory"),
        ])
        result = plan_project_checks(self.root)
        self.assertIsNone(result.plan)
        self.assertEqual(len(result.findings), 2)
        self.assertTrue(any("could not be resolved" in item.message for item in result.findings))
        self.assertTrue(any("not a directory" in item.message for item in result.findings))

    def test_cwd_resolution_loop_is_a_per_check_planning_finding(self) -> None:
        loop = self.root / "cwd-loop"
        self.set_checks([
            self.check("loop", [sys.executable], cwd="cwd-loop"),
            self.check("missing", [sys.executable], cwd="also-missing"),
        ])
        if os.name == "nt":
            resolution = self.resolution_loop_patch(loop)
        else:
            loop.symlink_to(loop.name, target_is_directory=True)
            resolution = nullcontext()
        with resolution:
            result = plan_project_checks(self.root)
        self.assertIsNone(result.plan)
        self.assertEqual(len(result.findings), 2, result.findings)
        self.assertTrue(any("'loop' cwd could not be resolved" in item.message
                            for item in result.findings))
        self.assertTrue(any("'missing' cwd could not be resolved" in item.message
                            for item in result.findings))

    def test_symlink_escape_is_rejected(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        link = self.root / "link-to-outside"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        self.set_checks([
            self.check("symlink", [sys.executable], cwd="link-to-outside")
        ])
        result = plan_project_checks(self.root)
        self.assertFalse(result.is_ready)
        self.assertIn("outside project root", result.findings[0].message)

    @unittest.skipUnless(os.name == "nt", "Windows junction evidence")
    def test_windows_junction_escape_is_rejected_live(self) -> None:
        outside = self.base / "junction outside"
        outside.mkdir()
        link = self.root / "junction"
        command = [
            os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"),
            "/d", "/c", "mklink", "/J", str(link), str(outside),
        ]
        created = subprocess.run(
            command, capture_output=True, text=True, shell=False, check=False
        )
        if created.returncode != 0:
            self.skipTest(f"Junction creation unavailable: {created.stderr}")
        self.set_checks([
            self.check("junction", [sys.executable], cwd="junction")
        ])
        result = plan_project_checks(self.root)
        self.assertFalse(result.is_ready)
        self.assertIn("outside project root", result.findings[0].message)

    def test_contained_symlink_is_accepted(self) -> None:
        inside = self.root / "inside"
        inside.mkdir()
        link = self.root / "link-to-inside"
        try:
            link.symlink_to(inside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        self.set_checks([
            self.check("symlink", [sys.executable], cwd="link-to-inside")
        ])
        self.assertEqual(self.ready_plan().checks[0].cwd, inside.resolve())

    def test_invalid_contract_and_duplicate_ids_never_produce_a_plan(self) -> None:
        self.set_checks([
            self.check("duplicate", [sys.executable]),
            self.check("duplicate", [sys.executable]),
        ])
        duplicate = plan_project_checks(self.root)
        self.assertEqual(duplicate.status, "FAIL")
        self.assertIsNone(duplicate.plan)
        self.assertIn("Duplicate Verification Check ID", duplicate.findings[0].message)

        self.manifest["verification"] = {"checks": [{"id": "bad", "command": []}]}
        self.write_manifest()
        malformed = plan_project_checks(self.root)
        self.assertEqual(malformed.status, "FAIL")
        self.assertIsNone(malformed.plan)

    def test_all_cwds_are_planned_without_executable_lookup_or_execution(self) -> None:
        (self.root / "valid").mkdir()
        self.set_checks([
            self.check("valid-prefix", ["missing-prefix-tool"], cwd="valid"),
            self.check("invalid-last", [sys.executable], cwd="missing-last"),
        ])
        with patch("engineering_orchestration.project_verification.resolve_executable") as resolve, \
                patch("engineering_orchestration.project_verification.subprocess.Popen") as popen:
            result = plan_project_checks(self.root)
        self.assertIsNone(result.plan)
        resolve.assert_not_called()
        popen.assert_not_called()

    def test_plan_is_deeply_immutable_for_execution_fields(self) -> None:
        self.set_checks([self.check("immutable", [sys.executable, "arg"])])
        plan = self.ready_plan()
        self.assertIsInstance(plan.checks, tuple)
        self.assertIsInstance(plan.checks[0].command, tuple)
        with self.assertRaises(FrozenInstanceError):
            plan.project_root = self.base  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            plan.checks[0].timeout_seconds = 1  # type: ignore[misc]

    def test_unrelated_task_and_workflow_structure_does_not_gate_planning(self) -> None:
        broken = self.root / ".ai" / "tasks" / "broken"
        broken.mkdir(parents=True)
        (broken / "task.yaml").write_text("not: a valid task", encoding="utf-8")
        self.set_checks([self.python_check("ready", "raise SystemExit(0)")])
        self.assertTrue(plan_project_checks(self.root).is_ready)

    def test_missing_project_root_and_manifest_are_planning_errors(self) -> None:
        missing = plan_project_checks(self.base / "missing")
        self.assertEqual(missing.status, "ERROR")
        (self.root / ".ai" / "project.yaml").unlink()
        no_manifest = plan_project_checks(self.root)
        self.assertEqual(no_manifest.status, "ERROR")
        self.assertIn("Manifest not found", no_manifest.findings[0].message)


class VerificationResolutionTests(ProjectFixture):
    def test_bare_executable_uses_inherited_path(self) -> None:
        executable = Path(sys.executable).resolve()
        with patch.dict(os.environ, {"PATH": str(executable.parent)}, clear=False):
            resolved = resolve_executable(executable.name, self.root)
        self.assertEqual(resolved, executable)

    def test_relative_executable_resolves_from_effective_cwd(self) -> None:
        path, relative = self.make_relative_program()
        other = self.base / "invocation-directory"
        other.mkdir()
        original = Path.cwd()
        try:
            os.chdir(other)
            resolved = resolve_executable(f"./{relative}", self.root)
        finally:
            os.chdir(original)
        self.assertEqual(resolved, path.resolve())

    def test_absolute_external_executable_is_supported(self) -> None:
        self.assertEqual(
            resolve_executable(str(Path(sys.executable).resolve()), self.root),
            Path(sys.executable).resolve(),
        )

    def test_bare_lookup_relative_path_entry_is_anchored_to_check_cwd(self) -> None:
        path, relative = self.make_relative_program(relative_parent="path-tools")
        with patch.dict(os.environ, {"PATH": "path-tools"}, clear=False):
            resolved = resolve_executable(path.name, self.root)
        self.assertEqual(resolved, path.resolve(), relative)

    @unittest.skipUnless(os.name == "nt", "Windows PATHEXT evidence")
    def test_windows_pathext_resolves_cmd_and_bat(self) -> None:
        tools = self.root / "path tools"
        tools.mkdir()
        for extension in (".CMD", ".bat"):
            program = tools / f"runner{extension}"
            program.write_text("@exit /b 0\r\n", encoding="utf-8")
            with self.subTest(extension=extension), patch.dict(
                os.environ,
                {"PATH": str(tools), "PATHEXT": ".COM;.EXE;.BAT;.CMD"},
                clear=False,
            ):
                self.assertEqual(resolve_executable("runner", self.root), program.resolve())

    @unittest.skipUnless(os.name == "nt", "Windows path-form evidence")
    def test_windows_ambiguous_drive_relative_and_rooted_paths_are_rejected_early(self) -> None:
        comspec = Path(os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"))
        rooted_suffix = comspec.relative_to(comspec.anchor).as_posix()
        rooted_backslash_suffix = rooted_suffix.replace("/", "\\")
        forms = (
            f"{self.root.drive}tool.exe",
            f"/{rooted_suffix}",
            f"\\{rooted_backslash_suffix}",
        )
        with patch.object(
            Path,
            "resolve",
            side_effect=AssertionError("ambiguous forms must not be resolved"),
        ) as resolve:
            for executable in forms:
                with self.subTest(executable=executable):
                    self.assertIsNone(resolve_executable(executable, self.root))
        resolve.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows npm wrapper evidence")
    def test_windows_npm_and_npx_bare_wrappers_resolve_when_installed(self) -> None:
        resolved = {name: resolve_executable(name, self.root) for name in ("npm", "npx")}
        if not all(resolved.values()):
            self.skipTest(f"npm/npx unavailable on inherited PATH: {resolved}")
        for name, path in resolved.items():
            self.assertIn(path.suffix.casefold(), (".cmd", ".bat", ".exe"), name)


class VerificationExecutionTests(ProjectFixture):
    def run_checks(self, checks: list[dict]):
        self.set_checks(checks)
        return run_project_checks(self.ready_plan())

    def test_exit_zero_is_pass_and_output_is_separate(self) -> None:
        result = self.run_checks([
            self.python_check(
                "pass",
                "import sys; print('stdout-value'); print('stderr-value', file=sys.stderr)",
            )
        ])
        check = result.results[0]
        self.assertEqual((result.status, result.exit_code), ("PASS", 0))
        self.assertEqual(check.return_code, 0)
        self.assertIn("stdout-value", check.stdout_excerpt)
        self.assertIn("stderr-value", check.stderr_excerpt)
        self.assertNotIn("stderr-value", check.stdout_excerpt)

    def test_bare_executable_is_resolved_then_executed(self) -> None:
        executable = Path(sys.executable).resolve()
        self.set_checks([
            self.check("bare", [executable.name, "-c", "print('bare-pass')"])
        ])
        with patch.dict(os.environ, {"PATH": str(executable.parent)}, clear=False):
            result = run_project_checks(self.ready_plan())
        self.assertEqual(result.results[0].status, "PASS", result.results[0])
        self.assertIn("bare-pass", result.results[0].stdout_excerpt)

    def test_exit_one_and_two_are_fail_and_execution_continues(self) -> None:
        result = self.run_checks([
            self.python_check("one", "raise SystemExit(1)"),
            self.python_check("two", "raise SystemExit(2)"),
            self.python_check("after", "raise SystemExit(0)"),
        ])
        self.assertEqual([item.status for item in result.results], ["FAIL", "FAIL", "PASS"])
        self.assertEqual([item.return_code for item in result.results], [1, 2, 0])
        self.assertEqual((result.status, result.exit_code), ("FAIL", 1))

    @unittest.skipIf(os.name == "nt", "POSIX signal return evidence")
    def test_negative_signal_return_is_fail(self) -> None:
        result = self.run_checks([
            self.python_check(
                "signal", "import os, signal; os.kill(os.getpid(), signal.SIGTERM)"
            )
        ])
        self.assertEqual(result.results[0].status, "FAIL")
        self.assertEqual(result.results[0].return_code, -signal.SIGTERM)

    def test_missing_executable_is_local_error_and_later_check_runs(self) -> None:
        result = self.run_checks([
            self.check("missing", ["missing-aio019-executable"]),
            self.python_check("after", "print('after')"),
        ])
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIsNone(result.results[0].return_code)
        self.assertIn("executable not found", result.results[0].error)
        self.assertEqual(result.exit_code, 2)

    @unittest.skipUnless(os.name == "nt", "Windows path-form evidence")
    def test_windows_ambiguous_executable_forms_do_not_launch_and_later_check_runs(self) -> None:
        wrapper = self.root / "drive-relative.cmd"
        wrapper.write_text("@exit /b 0\r\n", encoding="utf-8")
        drive_relative = f"{self.root.drive}{wrapper.name}"
        comspec = Path(os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"))
        rooted_suffix = comspec.relative_to(comspec.anchor).as_posix()
        rooted_backslash_suffix = rooted_suffix.replace("/", "\\")
        rooted_slash = f"/{rooted_suffix}"
        rooted_backslash = f"\\{rooted_backslash_suffix}"
        self.set_checks([
            self.check("drive-relative", [drive_relative]),
            self.check("rooted-slash", [rooted_slash, "/d", "/c", "exit", "0"]),
            self.check("rooted-backslash", [rooted_backslash, "/d", "/c", "exit", "0"]),
            self.python_check("after", "pass"),
        ])
        real_popen = subprocess.Popen
        launched = []

        def tracking_popen(command, **kwargs):
            launched.append(command)
            return real_popen(command, **kwargs)

        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            side_effect=tracking_popen,
        ):
            result = run_project_checks(self.ready_plan())
        self.assertEqual(
            [item.status for item in result.results],
            ["ERROR", "ERROR", "ERROR", "PASS"],
        )
        self.assertEqual(len(launched), 1, launched)

    def test_launch_oserror_is_local_error(self) -> None:
        self.set_checks([self.python_check("launch", "raise SystemExit(0)")])
        plan = self.ready_plan()
        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            side_effect=OSError("launch denied"),
        ):
            result = run_project_checks(plan)
        self.assertEqual(result.results[0].status, "ERROR")
        self.assertIn("launch denied", result.results[0].error)
        self.assertIsNone(result.fatal_error)

    def test_capture_creation_failure_is_local_and_later_check_runs(self) -> None:
        self.set_checks([
            self.python_check("capture-error", "pass"),
            self.python_check("after", "pass"),
        ])
        plan = self.ready_plan()
        original = verification.tempfile.TemporaryFile
        calls = 0

        def temporary_file(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("temporary storage unavailable")
            return original(*args, **kwargs)

        with patch(
            "engineering_orchestration.project_verification.tempfile.TemporaryFile",
            side_effect=temporary_file,
        ):
            result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIn("temporary storage unavailable", result.results[0].error)

    def test_unlaunchable_relative_file_is_error(self) -> None:
        target = self.root / "not executable.txt"
        target.write_text("plain text", encoding="utf-8")
        if os.name != "nt":
            target.chmod(0o644)
        result = self.run_checks([
            self.check("unlaunchable", ["./not executable.txt"])
        ])
        self.assertEqual(result.results[0].status, "ERROR")
        self.assertIn("Unable to launch", result.results[0].error)

    def test_relative_program_and_path_with_spaces_execute(self) -> None:
        _, relative = self.make_relative_program(
            relative_parent="tool directory", name="check with spaces"
        )
        result = self.run_checks([
            self.check("relative", [f"./{relative}"])
        ])
        self.assertEqual(result.results[0].status, "PASS", result.results[0])
        self.assertIn("relative-stdout", result.results[0].stdout_excerpt)

    @unittest.skipUnless(os.name == "nt", "Windows batch wrapper evidence")
    def test_windows_cmd_and_bat_execute_with_outer_shell_false(self) -> None:
        checks = []
        for extension in ("cmd", "bat"):
            path = self.root / f"wrapper.{extension}"
            path.write_text(
                f"@echo off\r\necho {extension}-stdout\r\nexit /b 0\r\n",
                encoding="utf-8",
            )
            checks.append(self.check(extension, [f"./wrapper.{extension}"]))
        result = self.run_checks(checks)
        self.assertEqual(
            [item.status for item in result.results], ["PASS", "PASS"], result.results
        )

    @unittest.skipUnless(os.name == "nt", "Windows PowerShell evidence")
    def test_explicit_powershell_executable_is_project_selected_and_runs(self) -> None:
        powershell = resolve_executable("powershell.exe", self.root)
        if powershell is None:
            self.skipTest("Windows PowerShell is unavailable on inherited PATH")
        result = self.run_checks([
            self.check(
                "powershell",
                [
                    str(powershell),
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Write-Output 'powershell-pass'",
                ],
            )
        ])
        self.assertEqual(result.results[0].status, "PASS", result.results[0])
        self.assertIn("powershell-pass", result.results[0].stdout_excerpt)

    def test_arguments_remain_literal_for_native_executable(self) -> None:
        arguments = ["", "a b", '"quoted"', "trailing\\", "&&", "|", "*.py", "$HOME"]
        result = self.run_checks([
            self.python_check(
                "arguments",
                "import json, sys; print(json.dumps(sys.argv[1:]))",
                arguments=arguments,
            )
        ])
        self.assertEqual(json.loads(result.results[0].stdout_excerpt), arguments)

    def test_environment_is_inherited_and_stdin_receives_eof(self) -> None:
        checks = [
            self.python_check(
                "environment",
                "import os; print(os.environ['AIO019_INHERITED'])",
            ),
            self.python_check(
                "stdin",
                "import sys; print('stdin-bytes=' + str(len(sys.stdin.buffer.read())))",
            ),
        ]
        self.set_checks(checks)
        with patch.dict(os.environ, {"AIO019_INHERITED": "inherited-value"}, clear=False):
            result = run_project_checks(self.ready_plan())
        self.assertIn("inherited-value", result.results[0].stdout_excerpt)
        self.assertIn("stdin-bytes=0", result.results[1].stdout_excerpt)

    def test_large_output_is_tail_bounded_and_marked(self) -> None:
        amount = DIAGNOSTIC_EXCERPT_LIMIT + 137
        result = self.run_checks([
            self.python_check(
                "large",
                f"import sys; sys.stdout.write('A'*{amount}); "
                f"sys.stderr.write('B'*{amount}); raise SystemExit(1)",
            )
        ])
        check = result.results[0]
        self.assertEqual(check.status, "FAIL")
        self.assertIn("earlier bytes truncated", check.stdout_excerpt)
        self.assertIn("earlier bytes truncated", check.stderr_excerpt)
        self.assertTrue(check.stdout_excerpt.endswith("A" * DIAGNOSTIC_EXCERPT_LIMIT))
        self.assertTrue(check.stderr_excerpt.endswith("B" * DIAGNOSTIC_EXCERPT_LIMIT))

    def test_invalid_output_bytes_do_not_crash_decoding(self) -> None:
        result = self.run_checks([
            self.python_check(
                "bytes",
                "import sys; sys.stdout.buffer.write(bytes([255, 254, 253])); "
                "sys.stderr.buffer.write(bytes([255, 0, 254])); raise SystemExit(1)",
            )
        ])
        self.assertEqual(result.results[0].status, "FAIL")
        self.assertIsInstance(result.results[0].stdout_excerpt, str)
        self.assertIsInstance(result.results[0].stderr_excerpt, str)

    def test_duration_is_recorded_with_monotonic_clock(self) -> None:
        result = self.run_checks([
            self.python_check("duration", "import time; time.sleep(0.05)")
        ])
        self.assertGreaterEqual(result.results[0].duration_seconds, 0.04)

    def test_timeout_is_error_with_partial_diagnostics_and_no_return_code(self) -> None:
        result = self.run_checks([
            self.python_check(
                "timeout",
                "import sys, time; print('partial-out', flush=True); "
                "print('partial-err', file=sys.stderr, flush=True); time.sleep(10)",
                timeout=1,
            )
        ])
        check = result.results[0]
        self.assertEqual(check.status, "ERROR")
        self.assertIsNone(check.return_code)
        self.assertIn("Timed out after 1 seconds", check.error)
        self.assertIn("partial-out", check.stdout_excerpt)
        self.assertIn("partial-err", check.stderr_excerpt)

    def test_timeout_terminates_and_reaps_direct_child(self) -> None:
        self.set_checks([self.python_check("timeout", "pass", timeout=1)])
        plan = self.ready_plan()

        class TimeoutProcess:
            returncode = None

            def __init__(self):
                self.wait_calls = []
                self.terminated = False

            def poll(self):
                return None

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.returncode = -9

            def wait(self, timeout=None):
                self.wait_calls.append(timeout)
                if len(self.wait_calls) == 1:
                    raise subprocess.TimeoutExpired("fixture", timeout)
                self.returncode = -15
                return self.returncode

        process = TimeoutProcess()
        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            return_value=process,
        ):
            result = run_project_checks(plan)
        self.assertEqual(result.results[0].status, "ERROR")
        self.assertTrue(process.terminated)
        self.assertGreaterEqual(len(process.wait_calls), 2)

    def test_keyboard_interrupt_reaps_child_propagates_and_stops(self) -> None:
        self.set_checks([
            self.python_check("interrupt", "pass"),
            self.python_check("must-not-run", "pass"),
        ])
        plan = self.ready_plan()

        class InterruptProcess:
            returncode = None

            def __init__(self):
                self.wait_calls = 0
                self.terminated = False

            def poll(self):
                return None

            def terminate(self):
                self.terminated = True

            def kill(self):
                self.returncode = -9

            def wait(self, timeout=None):
                self.wait_calls += 1
                if self.wait_calls == 1:
                    raise KeyboardInterrupt
                self.returncode = -15
                return self.returncode

        process = InterruptProcess()
        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            return_value=process,
        ) as popen:
            with self.assertRaises(KeyboardInterrupt):
                run_project_checks(plan)
        self.assertTrue(process.terminated)
        self.assertEqual(popen.call_count, 1)

    def test_popen_uses_shell_false_devnull_and_inherited_environment(self) -> None:
        self.set_checks([self.python_check("options", "pass")])
        process = MagicMock()
        process.wait.return_value = 0
        process.poll.return_value = 0
        process.returncode = 0
        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            return_value=process,
        ) as popen:
            result = run_project_checks(self.ready_plan())
        self.assertEqual(result.status, "PASS")
        command, = popen.call_args.args
        kwargs = popen.call_args.kwargs
        self.assertIsInstance(command, list)
        self.assertFalse(kwargs["shell"])
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertIsNone(kwargs["env"])

    def test_cwd_disappearance_is_local_error_and_later_check_runs(self) -> None:
        first = self.root / "first"
        first.mkdir()
        self.set_checks([
            self.python_check("first", "pass", cwd="first"),
            self.python_check("second", "pass"),
        ])
        plan = self.ready_plan()
        first.rmdir()
        result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIn("cwd is not launchable", result.results[0].error)

    def test_launch_time_cwd_resolution_loop_is_local_and_later_check_runs(self) -> None:
        loop = self.root / "cwd-loop"
        loop.mkdir()
        self.set_checks([
            self.python_check("loop", "pass", cwd="cwd-loop"),
            self.python_check("after", "pass"),
        ])
        plan = self.ready_plan()
        if os.name == "nt":
            resolution = self.resolution_loop_patch(loop)
        else:
            loop.rmdir()
            loop.symlink_to(loop.name, target_is_directory=True)
            resolution = nullcontext()
        with resolution:
            result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIsNone(result.fatal_error)
        self.assertIn("cwd is not launchable", result.results[0].error)

    def test_relative_executable_resolution_loop_is_local_and_later_check_runs(self) -> None:
        executable = self.root / "loop-tool"
        self.set_checks([
            self.check("loop", ["./loop-tool"]),
            self.python_check("after", "pass"),
        ])
        plan = self.ready_plan()
        if os.name == "nt":
            resolution = self.resolution_loop_patch(executable)
        else:
            executable.symlink_to(executable.name)
            resolution = nullcontext()
        with resolution:
            result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIsNone(result.fatal_error)
        self.assertIn("executable not found", result.results[0].error)

    def test_project_root_resolution_loop_remains_fatal(self) -> None:
        self.set_checks([
            self.python_check("must-not-run", "pass"),
            self.python_check("also-not-run", "pass"),
        ])
        plan = self.ready_plan()
        with self.resolution_loop_patch(plan.project_root):
            result = run_project_checks(plan)
        self.assertEqual(result.results, ())
        self.assertIn("Project root is no longer usable", result.fatal_error)

    def test_launch_time_symlink_retarget_is_local_error(self) -> None:
        inside = self.root / "inside"
        outside = self.base / "outside"
        inside.mkdir()
        outside.mkdir()
        link = self.root / "mutable-link"
        try:
            link.symlink_to(inside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks unavailable: {exc}")
        self.set_checks([
            self.python_check("retargeted", "pass", cwd="mutable-link"),
            self.python_check("after", "pass"),
        ])
        plan = self.ready_plan()
        link.unlink()
        link.symlink_to(outside, target_is_directory=True)
        result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIn("outside project root", result.results[0].error)

    @unittest.skipUnless(os.name == "nt", "Windows junction revalidation evidence")
    def test_launch_time_junction_retarget_is_local_error_live(self) -> None:
        inside = self.root / "inside"
        outside = self.base / "outside"
        inside.mkdir()
        outside.mkdir()
        link = self.root / "mutable-junction"
        command_prefix = [
            os.environ.get("COMSPEC", r"C:\Windows\System32\cmd.exe"),
            "/d", "/c", "mklink", "/J", str(link),
        ]
        created = subprocess.run(
            [*command_prefix, str(inside)],
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        if created.returncode != 0:
            self.skipTest(f"Junction creation unavailable: {created.stderr}")
        self.set_checks([
            self.python_check("retargeted", "pass", cwd="mutable-junction"),
            self.python_check("after", "pass"),
        ])
        plan = self.ready_plan()
        link.rmdir()
        retargeted = subprocess.run(
            [*command_prefix, str(outside)],
            capture_output=True,
            text=True,
            shell=False,
            check=False,
        )
        self.assertEqual(retargeted.returncode, 0, retargeted.stderr)
        result = run_project_checks(plan)
        self.assertEqual([item.status for item in result.results], ["ERROR", "PASS"])
        self.assertIn("outside project root", result.results[0].error)

    def test_fatal_project_root_failure_stops_without_skip_results(self) -> None:
        self.set_checks([
            self.python_check("first", "pass"),
            self.python_check("second", "pass"),
        ])
        plan = self.ready_plan()
        moved = self.base / "moved-project"

        def execute_then_remove_root(_plan, check):
            self.root.rename(moved)
            return VerificationCheckResult(
                id=check.id,
                command=check.command,
                cwd=check.cwd,
                status="PASS",
                return_code=0,
                duration_seconds=0.0,
            )

        with patch(
            "engineering_orchestration.project_verification._execute_check",
            side_effect=execute_then_remove_root,
        ) as execute:
            result = run_project_checks(plan)
        self.assertEqual(len(result.results), 1)
        self.assertEqual(execute.call_count, 1)
        self.assertIsNotNone(result.fatal_error)
        self.assertEqual(result.status, "ERROR")

    def test_unexpected_internal_failure_is_fatal_and_stops(self) -> None:
        self.set_checks([
            self.python_check("first", "pass"),
            self.python_check("second", "pass"),
        ])
        with patch(
            "engineering_orchestration.project_verification.subprocess.Popen",
            side_effect=RuntimeError("programming fault"),
        ) as popen:
            result = run_project_checks(self.ready_plan())
        self.assertEqual(result.results, ())
        self.assertIn("Unexpected runner failure", result.fatal_error)
        self.assertEqual(popen.call_count, 1)

    def test_formatting_suppresses_pass_output_and_shows_fail_diagnostics(self) -> None:
        result = self.run_checks([
            self.python_check("pass", "print('pass-secret-output')"),
            self.python_check(
                "fail",
                "import sys; print('failure-detail'); print('failure-error', file=sys.stderr); "
                "raise SystemExit(1)",
            ),
        ])
        output = format_project_verification_output(result)
        self.assertNotIn("pass-secret-output", output)
        self.assertIn("failure-detail", output)
        self.assertIn("failure-error", output)


class VerificationBoundaryTests(ProjectFixture):
    def test_result_model_contains_no_skip_or_quality_gate_mapping(self) -> None:
        result_fields = {item.name for item in fields(VerificationCheckResult)}
        self.assertEqual(
            result_fields,
            {
                "id", "command", "cwd", "status", "return_code",
                "duration_seconds", "stdout_excerpt", "stderr_excerpt", "error",
            },
        )
        self.assertNotIn("skip", " ".join(result_fields).lower())
        self.assertNotIn("gate", " ".join(result_fields).lower())

    def test_module_has_no_task_workflow_agent_or_provider_runtime_imports(self) -> None:
        source = Path(verification.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        for forbidden in ("inspect_task", "list_tasks", "workflow_catalog", "agent", "provider"):
            self.assertFalse(any(forbidden in name for name in imported), imported)

    def test_cli_uses_project_verification_without_a_fixed_battery(self) -> None:
        from engineering_orchestration import cli
        from engineering_orchestration import verify_repo

        source = Path(cli.__file__).read_text(encoding="utf-8")
        self.assertIn("project_verification", source)
        self.assertFalse(hasattr(verify_repo, "DEFAULT_CHECKS"))

    def test_orchestra_manifest_dogfoods_declared_verification(self) -> None:
        import yaml

        repository_root = Path(__file__).resolve().parents[1]
        manifest = yaml.safe_load(
            (repository_root / ".ai" / "project.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(len(manifest["verification"]["checks"]), 7)


if __name__ == "__main__":
    unittest.main()
