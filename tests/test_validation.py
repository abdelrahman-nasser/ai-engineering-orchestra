"""Portable structure validation against independent project data."""

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from engineering_orchestration import cli
from engineering_orchestration.project import task_directory
from engineering_orchestration.schema_resources import load_validator, schema_errors
from engineering_orchestration.validation import manifest_semantic_errors, validate_project


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


class StructuralValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.manifest = {"schema_version": "0.1", "project": {
            "id": "example", "name": "Example", "type": "application",
            "lifecycle": "greenfield"}, "orchestra": {"version": "0.1.0"},
            "tasks": {"directory": "governance/tasks"},
            "complexity": {"default": "medium"}, "risk": {"default": "low"},
            "execution": {"default_mode": "standard"},
            "human_control": {}, "quality": {}}
        self.manifest_path = self.root / ".ai/project.yaml"
        write(self.manifest_path, self.manifest)
        self.task = {"id": "EXAMPLE-001", "title": "Independent Task",
                     "type": "implementation", "status": "in_progress",
                     "objective": "Validate data", "scope": {"include": ["Data"]},
                     "workflow": "example"}
        self.task_path = self.root / "governance/tasks/unrelated/task.yaml"
        write(self.task_path, self.task)
        for artifact in ("context.md", "acceptance-criteria.md", "review.md"):
            self.task_path.with_name(artifact).write_text("# Fixture\n", encoding="utf-8")
        self.workflow = {"id": "example", "name": "Example", "purpose": "Govern",
                         "stages": [{"id": "review", "purpose": "Review"}]}
        self.workflow_path = self.root / "workflows/unrelated.yaml"
        write(self.workflow_path, self.workflow)
        self.nested = self.root / "src/nested"
        self.nested.mkdir(parents=True)

    def assert_status(self, expected, fragment=None):
        result = validate_project(self.nested)
        self.assertEqual(result.status, expected, result.findings)
        if fragment:
            self.assertTrue(any(fragment in item.message for item in result.findings), result)
        return result

    def test_valid_custom_path_and_all_commands_from_nested_cwd(self):
        write(self.root / ".ai/tasks/decoy/task.yaml", {"bad": "ignored"})
        with patch("pathlib.Path.cwd", return_value=self.nested), \
                patch("subprocess.run", side_effect=AssertionError("No commands")), \
                patch("subprocess.Popen", side_effect=AssertionError("No commands")):
            self.assertEqual(validate_project().status, "PASS")
            for arguments in (["tasks"], ["inspect", "EXAMPLE-001"]):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(cli.main(arguments), 0)
                self.assertIn("EXAMPLE-001", output.getvalue())
                self.assertNotIn("decoy", output.getvalue())

    def test_default_directory_when_configuration_omitted(self):
        self.manifest.pop("tasks")
        write(self.manifest_path, self.manifest)
        self.assertEqual(task_directory(self.root), self.root / ".ai/tasks")

    def test_verification_contract_fixtures_through_schema_and_project_validation(self):
        fixtures = Path(__file__).resolve().parents[1] / "schemas/tests/project-manifest"
        validator = load_validator("project-manifest.schema.json")
        paths = sorted(fixtures.glob("*-verification-*.yaml"))
        self.assertGreaterEqual(len(paths), 34)
        for path in paths:
            with self.subTest(fixture=path.name):
                declaration = yaml.safe_load(path.read_text(encoding="utf-8"))["verification"]
                self.manifest["verification"] = declaration
                before = json.dumps(self.manifest)
                errors = schema_errors(validator, self.manifest)
                semantic = [] if errors else manifest_semantic_errors(self.manifest)
                expected_valid = path.name.startswith("valid-")
                self.assertEqual(not errors and not semantic, expected_valid)
                if path.name == "invalid-verification-duplicate-id.yaml":
                    self.assertFalse(errors, "Duplicate identity is semantic, not whole-object equality")
                    self.assertIn("Duplicate Verification Check ID", semantic[0])
                elif not expected_valid:
                    self.assertTrue(errors)
                    self.assertTrue(all(list(e.absolute_path)[0] == "verification" for e in errors))
                write(self.manifest_path, self.manifest)
                with patch("subprocess.run") as run, patch("subprocess.Popen") as popen, \
                        patch("shutil.which") as which:
                    self.assert_status("PASS" if expected_valid else "FAIL")
                run.assert_not_called()
                popen.assert_not_called()
                which.assert_not_called()
                self.assertEqual(json.dumps(self.manifest), before)
                self.assertEqual(json.loads(self.manifest_path.read_text()), self.manifest)

    def test_declared_checks_never_run_during_validation_tasks_or_inspect(self):
        self.manifest["verification"] = {"checks": [{
            "id": "must-not-run", "command": ["unavailable-program", "", "tests/*"],
            "cwd": "../absent-outside-project", "timeout_seconds": 1}]}
        write(self.manifest_path, self.manifest)
        original = self.manifest_path.read_bytes()
        with patch("pathlib.Path.cwd", return_value=self.nested), \
                patch("subprocess.run") as run, patch("subprocess.Popen") as popen, \
                patch("os.system") as system, patch("shutil.which") as which:
            self.assertEqual(validate_project().status, "PASS")
            for arguments in (["tasks"], ["inspect", "EXAMPLE-001"]):
                with redirect_stdout(StringIO()) as output:
                    self.assertEqual(cli.main(arguments), 0)
                self.assertIn("EXAMPLE-001", output.getvalue())
        for operation in (run, popen, system, which):
            operation.assert_not_called()
        self.assertEqual(self.manifest_path.read_bytes(), original)

    def test_checks_preserve_order_arguments_and_omitted_defaults(self):
        checks = [{"id": "z-last", "command": ["tool", "", "  ", "&&", "|", "$HOME", "tests/*"]},
                  {"id": "a-first", "command": ["./relative-tool"]}]
        self.manifest["verification"] = {"checks": checks}
        write(self.manifest_path, self.manifest)
        self.assert_status("PASS")
        self.assertEqual(json.loads(self.manifest_path.read_text())["verification"]["checks"], checks)
        self.assertEqual(manifest_semantic_errors(self.manifest), [])
        self.assertNotIn("cwd", checks[0])
        self.assertNotIn("timeout_seconds", checks[0])

    def test_all_speculative_check_fields_are_rejected(self):
        fields = ("description", "depends_on", "parallel", "env", "environment", "shell",
                  "retry", "continue_on_error", "quality_gate", "task_types", "provider",
                  "agent", "working_directory", "command_name", "executable", "args",
                  "model", "role", "stage")
        for name in fields:
            with self.subTest(field=name):
                self.manifest["verification"] = {"checks": [{
                    "id": "check", "command": ["tool"], name: "unsupported"}]}
                write(self.manifest_path, self.manifest)
                self.assert_status("FAIL", "Additional properties")

    def test_checks_do_not_change_quality_gate_or_task_state(self):
        self.manifest["quality"] = {"require_independent_review": True}
        self.task["quality_gates"] = ["independent_review"]
        write(self.task_path, self.task)
        self.manifest["verification"] = {"checks": [{"id": "tests", "command": ["tool"]}]}
        write(self.manifest_path, self.manifest)
        before = {p: p.read_bytes() for p in (self.manifest_path, self.task_path, self.workflow_path)}
        self.assert_status("PASS")
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_configured_missing_directory_never_falls_back(self):
        self.manifest["tasks"]["directory"] = "absent"
        write(self.manifest_path, self.manifest)
        write(self.root / ".ai/tasks/decoy/task.yaml", self.task)
        self.assert_status("FAIL", "Tasks directory not found")
        with patch("pathlib.Path.cwd", return_value=self.root), redirect_stderr(StringIO()):
            self.assertEqual(cli.main(["tasks"]), 2)
            self.assertEqual(cli.main(["inspect", "EXAMPLE-001"]), 2)

    def test_direct_inventory_missing_configured_path_diagnostic(self):
        from engineering_orchestration.list_tasks import main

        self.manifest["tasks"]["directory"] = "absent"
        write(self.manifest_path, self.manifest)
        error = StringIO()
        with patch("pathlib.Path.cwd", return_value=self.nested), redirect_stderr(error):
            self.assertEqual(main([]), 2)
        self.assertIn(str(self.root / "absent"), error.getvalue())
        self.assertNotIn(".ai/tasks", error.getvalue())

    def test_invalid_manifest_schema_and_yaml(self):
        for content in ('[]', 'tasks: [', '{"tasks": null}'):
            with self.subTest(content=content):
                self.manifest_path.write_text(content, encoding="utf-8")
                self.assert_status("FAIL")

    def test_invalid_task_schema_yaml_and_identity(self):
        for content in ('[]', 'id: [', '{"id": 123}', '{}'):
            with self.subTest(content=content):
                self.task_path.write_text(content, encoding="utf-8")
                self.assert_status("FAIL")

    def test_duplicate_task_ids(self):
        write(self.task_path.parent.parent / "different-name/task.yaml", self.task)
        self.assert_status("FAIL", "Duplicate Task ID: EXAMPLE-001")

    def test_unknown_workflow(self):
        self.task["workflow"] = "missing"
        write(self.task_path, self.task)
        self.assert_status("FAIL", "Unknown Workflow: missing")

    def test_optional_workflow(self):
        self.task.pop("workflow")
        write(self.task_path, self.task)
        self.assert_status("PASS")

    def test_duplicate_workflow_ids(self):
        write(self.workflow_path.with_name("other.yml"), self.workflow)
        self.assert_status("FAIL", "Duplicate declared Workflow ID")

    def test_duplicate_stage_ids(self):
        self.workflow["stages"].append({"id": "review", "purpose": "Again"})
        write(self.workflow_path, self.workflow)
        self.assert_status("FAIL", "Duplicate Stage ID")

    def test_stage_ids_can_repeat_across_workflows(self):
        self.workflow["id"] = "second"
        write(self.workflow_path.with_name("second.yml"), self.workflow)
        self.assert_status("PASS")

    def test_invalid_workflow_schema_and_yaml(self):
        for content in ('[]', 'id: [', '{}'):
            with self.subTest(content=content):
                self.workflow_path.write_text(content, encoding="utf-8")
                self.assert_status("FAIL")

    def test_missing_schema_is_error(self):
        from engineering_orchestration.schema_resources import schema_resource
        for name in ("task.schema.json", "workflow.schema.json", "project-manifest.schema.json"):
            with self.subTest(name=name), patch(
                "engineering_orchestration.schema_resources.schema_resource",
                side_effect=lambda requested: None if requested == name else schema_resource(requested),
            ):
                self.assert_status("ERROR", "Required tool schema missing")

    def test_unreadable_files_are_errors(self):
        original = Path.read_text
        for target in (self.manifest_path, self.task_path, self.workflow_path):
            with self.subTest(target=target), patch.object(
                Path, "read_text", autospec=True,
                side_effect=lambda path, *a, **kw: (_ for _ in ()).throw(PermissionError("denied"))
                if path == target else original(path, *a, **kw),
            ):
                self.assert_status("ERROR", "denied")

    def test_internal_validator_failure_is_error(self):
        with patch("engineering_orchestration.validation.schema_errors",
                   side_effect=RuntimeError("validator failed")):
            self.assert_status("ERROR", "validator failed")

    def test_missing_task_metadata_is_fail(self):
        self.task_path.unlink()
        self.assert_status("FAIL", "Required document missing")

    def test_invalid_task_paths_are_not_defaults(self):
        for directory in ("", None, 123, "/absolute", "C:/absolute", "a\\b"):
            with self.subTest(directory=directory):
                self.manifest["tasks"]["directory"] = directory
                write(self.manifest_path, self.manifest)
                self.assert_status("FAIL")
                with self.assertRaises(ValueError):
                    task_directory(self.root)


if __name__ == "__main__":
    unittest.main()
