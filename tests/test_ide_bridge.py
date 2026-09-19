"""Focused tests for the closed, read-only IDE bridge."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from engineering_orchestration import ide_bridge


class BridgeProject:
    """Small synthetic managed project with custom Task paths."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.tasks = root / "governance" / "tasks"
        self.workflows = root / "workflows"
        self.tasks.mkdir(parents=True)
        self.workflows.mkdir()
        (root / ".ai").mkdir()
        self.manifest = {
            "schema_version": "0.1",
            "project": {
                "id": "bridge-fixture",
                "name": "Bridge Fixture",
                "type": "application",
                "lifecycle": "greenfield",
            },
            "orchestra": {"version": "0.1.0"},
            "complexity": {"default": "medium"},
            "risk": {"default": "high"},
            "execution": {"default_mode": "standard"},
            "human_control": {"final_review_required": True},
            "quality": {"require_independent_review": True},
            "tasks": {"directory": "governance/tasks"},
        }
        self.write_manifest()
        self.write_workflow()
        self.add_task("odd-directory", "TASK-001")

    def write_manifest(self) -> None:
        (self.root / ".ai" / "project.yaml").write_text(
            json.dumps(self.manifest), encoding="utf-8"
        )

    def write_workflow(self, path: Path | None = None) -> Path:
        target = path or self.workflows / "not-the-id.yaml"
        target.write_text(
            json.dumps(
                {
                    "id": "secure-flow",
                    "name": "Secure Flow",
                    "purpose": "Synthetic declared governance",
                    "stages": [
                        {
                            "id": "implement",
                            "purpose": "Implement the bounded change",
                            "required_roles": ["software-engineer"],
                        },
                        {
                            "id": "review",
                            "purpose": "Review independently",
                            "required_roles": ["reviewer", "security-reviewer"],
                            "required_quality_gates": ["independent_review"],
                            "human_control_checkpoint": True,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        return target

    def add_task(
        self,
        directory_name: str,
        task_id: str,
        *,
        status: str = "in_progress",
        all_artifacts: bool = True,
    ) -> Path:
        directory = self.tasks / directory_name
        directory.mkdir()
        (directory / "task.yaml").write_text(
            json.dumps(
                {
                    "id": task_id,
                    "title": f"Title for {task_id}",
                    "type": "implementation",
                    "status": status,
                    "objective": "Exercise the IDE bridge",
                    "scope": {"include": ["Synthetic fixture"]},
                    "workflow": "secure-flow",
                    "complexity": "high",
                    "quality_gates": ["task_gate"],
                    "human_control": {
                        "architecture_changes_require_approval": True
                    },
                }
            ),
            encoding="utf-8",
        )
        names = ("context.md", "acceptance-criteria.md", "review.md")
        for name in names if all_artifacts else names[:-1]:
            (directory / name).write_text("# Synthetic fixture\n", encoding="utf-8")
        return directory


class IdeBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve() / "selected project"
        self.root.mkdir()
        self.project = BridgeProject(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def request(
        self,
        operation: str = "project_snapshot",
        payload: dict | None = None,
        **overrides,
    ) -> dict:
        if payload is None:
            payload = (
                {"status": None, "workflow": None}
                if operation == "project_snapshot"
                else {"task_id": "TASK-001"}
            )
        document = {
            "protocol": ide_bridge.PROTOCOL,
            "request_id": "request-1",
            "operation": operation,
            "project_root": str(self.root),
            "payload": payload,
        }
        document.update(overrides)
        return ide_bridge.process_request_bytes(json.dumps(document).encode("utf-8"))

    def assert_error(self, response: dict, code: str) -> None:
        self.assertEqual(
            set(response),
            {"protocol", "request_id", "ok", "meta", "error", "diagnostics"},
        )
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], code)
        self.assertLessEqual(len(response["error"]["message"]), 512)
        self.assertLessEqual(len(response["diagnostics"]), 100)

    def test_project_snapshot_uses_real_inventory_filters_and_validation(self):
        self.project.add_task("second-directory", "TASK-002", status="completed")
        response = self.request(
            payload={"status": "in_progress", "workflow": "secure-flow"}
        )
        self.assertTrue(response["ok"], response)
        self.assertEqual(
            set(response),
            {"protocol", "request_id", "ok", "meta", "result", "diagnostics"},
        )
        result = response["result"]
        self.assertEqual(result["project"], {
            "state": "managed", "id": "bridge-fixture", "name": "Bridge Fixture"
        })
        self.assertEqual([task["id"] for task in result["tasks"]], ["TASK-001"])
        self.assertEqual(result["filters"]["statuses"], ["completed", "in_progress"])
        self.assertEqual(result["filters"]["workflows"], ["secure-flow"])
        self.assertEqual(set(result["filters"]), {"statuses", "workflows"})
        self.assertEqual(result["validation"], {"status": "PASS", "findings": []})
        self.assertRegex(result["snapshot_at"], r"Z$")
        task = result["tasks"][0]
        self.assertRegex(task["resource_id"], r"^task-[0-9a-f]{24}$")
        self.assertEqual(task["schema_status"], "VALID")
        self.assertEqual(task["workflow_resolution"], "RESOLVED")
        self.assertEqual(task["artifact_health"], {
            "task_yaml": True,
            "context_md": True,
            "acceptance_criteria_md": True,
            "review_md": True,
        })

    def test_task_detail_exposes_effective_provenance_artifacts_and_definition(self):
        response = self.request("task_detail")
        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertEqual(result["task"]["id"], "TASK-001")
        self.assertEqual(result["effective"]["risk"], {
            "value": "high", "source": "project"
        })
        self.assertEqual(result["effective"]["complexity"], {
            "value": "high", "source": "task"
        })
        self.assertEqual(result["effective"]["execution_mode"], {
            "value": "standard", "source": "project"
        })
        gates = result["effective"]["quality_gates"]
        self.assertEqual(
            gates, ["independent_review", "task_gate"]
        )
        self.assertEqual(
            result["effective"]["human_control"][
                "architecture_changes_require_approval"
            ],
            {"value": True, "source": "task"},
        )
        self.assertEqual(
            [item["label"] for item in result["artifacts"]],
            list(ide_bridge.CANONICAL_ARTIFACTS),
        )
        for artifact in result["artifacts"]:
            self.assertEqual(
                set(artifact), {"artifact_id", "label", "state", "relative_path"}
            )
            self.assertFalse(Path(artifact["relative_path"]).is_absolute())
        workflow = result["workflow"]
        self.assertTrue(workflow["definition_not_execution"])
        self.assertEqual([stage["id"] for stage in workflow["stages"]],
                         ["implement", "review"])
        self.assertEqual(
            [role["id"] for role in workflow["stages"][1]["required_roles"]],
            ["reviewer", "security-reviewer"],
        )
        self.assertNotIn("progress", workflow)

    def test_artifact_health_is_distinct_from_schema_validity(self):
        (self.project.tasks / "odd-directory" / "review.md").unlink()
        snapshot = self.request()
        self.assertTrue(snapshot["ok"], snapshot)
        task = snapshot["result"]["tasks"][0]
        self.assertEqual(task["schema_status"], "VALID")
        self.assertFalse(task["artifact_health"]["review_md"])
        detail = self.request("task_detail")
        missing = next(
            item for item in detail["result"]["artifacts"]
            if item["label"] == "review.md"
        )
        self.assertEqual(missing["state"], "missing")

    def test_invalid_task_is_an_anomaly_and_project_is_invalid(self):
        broken = self.project.tasks / "broken"
        broken.mkdir()
        (broken / "task.yaml").write_text("[]", encoding="utf-8")
        response = self.request()
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["project"]["state"], "invalid")
        self.assertEqual(response["result"]["validation"]["status"], "FAIL")
        self.assertEqual(response["result"]["anomalies"][0]["code"],
                         "task_inventory_anomaly")
        self.assertNotIn(str(self.root), json.dumps(response["result"]["anomalies"]))

    def test_duplicate_declared_task_id_is_ambiguous(self):
        self.project.add_task("duplicate", "TASK-001")
        self.assert_error(self.request("task_detail"), "task_id_ambiguous")
        snapshot = self.request()
        self.assertTrue(snapshot["ok"], snapshot)
        self.assertIn(
            "duplicate_task_id",
            {item["code"] for item in snapshot["result"]["anomalies"]},
        )
        displayed_diagnostics = {
            "anomalies": snapshot["result"]["anomalies"],
            "validation": snapshot["result"]["validation"],
        }
        self.assertNotIn(str(self.root), json.dumps(displayed_diagnostics))

    def test_task_lookup_is_exact_and_not_directory_based(self):
        self.assert_error(
            self.request("task_detail", {"task_id": "odd-directory"}),
            "task_not_found",
        )
        exact = self.request("task_detail", {"task_id": "TASK-001"})
        self.assertTrue(exact["ok"], exact)

    def test_unresolved_workflow_is_reported_without_invented_progress(self):
        task_path = self.project.tasks / "odd-directory" / "task.yaml"
        task = json.loads(task_path.read_text(encoding="utf-8"))
        task["workflow"] = "missing-flow"
        task_path.write_text(json.dumps(task), encoding="utf-8")
        snapshot = self.request()
        self.assertTrue(snapshot["ok"], snapshot)
        self.assertEqual(snapshot["result"]["tasks"][0]["workflow_resolution"],
                         "UNRESOLVED")
        self.assertEqual(snapshot["result"]["project"]["state"], "invalid")
        detail = self.request("task_detail")
        self.assertTrue(detail["ok"], detail)
        self.assertIsNone(detail["result"]["workflow"])

    def test_exact_root_does_not_walk_to_parent_manifest(self):
        nested = self.root / "unmanaged-child"
        nested.mkdir()
        response = self.request(project_root=str(nested))
        self.assert_error(response, "unmanaged_project")

    def test_external_configured_task_directory_is_rejected_before_reader(self):
        outside = self.root.parent / "outside-tasks"
        outside.mkdir()
        self.project.manifest["tasks"] = {"directory": "../outside-tasks"}
        self.project.write_manifest()
        with patch(
            "engineering_orchestration.ide_bridge.discover_tasks",
            side_effect=AssertionError("reader must not run"),
        ):
            response = self.request()
        self.assert_error(response, "out_of_scope_resource")

    def test_manifest_replacement_after_preflight_cannot_redirect_validation(self):
        outside = self.root.parent / "outside-after-preflight"
        outside.mkdir()
        broken = outside / "broken"
        broken.mkdir()
        (broken / "task.yaml").write_text("[]", encoding="utf-8")
        load_inventory = ide_bridge._load_inventory

        def replace_source_manifest(context):
            self.assertNotEqual(context.snapshot_root, context.root)
            self.project.manifest["tasks"] = {
                "directory": "../outside-after-preflight"
            }
            self.project.write_manifest()
            return load_inventory(context)

        with patch(
            "engineering_orchestration.ide_bridge._load_inventory",
            side_effect=replace_source_manifest,
        ):
            response = self.request()

        self.assertTrue(response["ok"], response)
        self.assertEqual(
            [item["id"] for item in response["result"]["tasks"]],
            ["TASK-001"],
        )
        self.assertEqual(response["result"]["validation"], {
            "status": "PASS", "findings": []
        })

    def test_task_added_after_preflight_is_not_enumerated(self):
        load_inventory = ide_bridge._load_inventory

        def add_late_source_entry(context):
            late = self.project.tasks / "late-entry"
            late.mkdir()
            (late / "task.yaml").write_text("[]", encoding="utf-8")
            return load_inventory(context)

        with patch(
            "engineering_orchestration.ide_bridge._load_inventory",
            side_effect=add_late_source_entry,
        ):
            response = self.request()

        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["anomalies"], [])
        self.assertEqual(response["result"]["validation"]["status"], "PASS")
        self.assertEqual(
            [item["id"] for item in response["result"]["tasks"]],
            ["TASK-001"],
        )

    def test_task_file_growth_after_preflight_does_not_change_detail(self):
        load_inventory = ide_bridge._load_inventory

        def replace_source_task_with_oversized_data(context):
            task_yaml = self.project.tasks / "odd-directory" / "task.yaml"
            task_yaml.write_bytes(b"[" + b"x" * ide_bridge.MAX_YAML_BYTES + b"]")
            return load_inventory(context)

        with patch(
            "engineering_orchestration.ide_bridge._load_inventory",
            side_effect=replace_source_task_with_oversized_data,
        ):
            response = self.request("task_detail")

        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["task"]["id"], "TASK-001")
        self.assertEqual(response["result"]["effective"]["complexity"], {
            "value": "high", "source": "task"
        })

    def test_source_directory_retarget_after_preflight_cannot_change_snapshot(self):
        probe_target = self.root.parent / "symlink-probe-target"
        probe_link = self.root.parent / "symlink-probe-link"
        probe_target.mkdir()
        try:
            probe_link.symlink_to(probe_target, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlink creation unavailable: {exc}")
        probe_link.unlink()
        probe_target.rmdir()

        outside = self.root.parent / "retargeted-task"
        outside.mkdir()
        (outside / "task.yaml").write_text("[]", encoding="utf-8")
        source_task = self.project.tasks / "odd-directory"
        captured_task = self.project.tasks / "captured-task"
        load_inventory = ide_bridge._load_inventory

        def retarget_source_directory(context):
            source_task.rename(captured_task)
            source_task.symlink_to(outside, target_is_directory=True)
            return load_inventory(context)

        with patch(
            "engineering_orchestration.ide_bridge._load_inventory",
            side_effect=retarget_source_directory,
        ):
            response = self.request("task_detail")

        self.assertTrue(response["ok"], response)
        task = response["result"]["task"]
        self.assertEqual(task["id"], "TASK-001")
        relative = "governance/tasks/odd-directory"
        expected = hashlib.sha256(
            f"task\0{relative}".encode("utf-8")
        ).hexdigest()[:24]
        self.assertEqual(task["resource_id"], f"task-{expected}")
        self.assertEqual(
            response["result"]["artifacts"][0]["relative_path"],
            f"{relative}/task.yaml",
        )

    def test_symlinked_artifact_escape_is_rejected_before_reader(self):
        artifact = self.project.tasks / "odd-directory" / "context.md"
        outside = self.root.parent / "outside.md"
        outside.write_text("sensitive", encoding="utf-8")
        artifact.unlink()
        try:
            artifact.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with patch(
            "engineering_orchestration.ide_bridge.discover_tasks",
            side_effect=AssertionError("reader must not run"),
        ):
            response = self.request()
        self.assert_error(response, "out_of_scope_resource")

    def test_symlinked_workflow_escape_is_rejected(self):
        workflow = self.project.workflows / "not-the-id.yaml"
        outside = self.root.parent / "outside-workflow.yaml"
        outside.write_text(workflow.read_text(encoding="utf-8"), encoding="utf-8")
        workflow.unlink()
        try:
            workflow.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        self.assert_error(self.request(), "out_of_scope_resource")

    def test_invalid_manifest_is_structured_and_diagnostics_are_bounded(self):
        self.project.manifest["unexpected"] = "x" * 2000
        self.project.write_manifest()
        response = self.request()
        self.assert_error(response, "invalid_project")
        self.assertTrue(response["diagnostics"])
        for item in response["diagnostics"]:
            self.assertLessEqual(len(item["message"]), 512)

    def test_package_catalog_failure_is_structured(self):
        with patch("engineering_orchestration.ide_bridge.schema_resource", return_value=None):
            self.assert_error(self.request(), "invalid_catalog")

    def test_yaml_and_inventory_resource_limits_are_not_partial(self):
        task_yaml = self.project.tasks / "odd-directory" / "task.yaml"
        task_yaml.write_text(task_yaml.read_text(encoding="utf-8") + " " * 1024,
                             encoding="utf-8")
        with patch.object(ide_bridge, "MAX_YAML_BYTES", 512):
            self.assert_error(self.request(), "resource_limit")

        task_yaml.write_text(json.dumps({
            "id": "TASK-001", "title": "Restored", "type": "implementation",
            "status": "in_progress", "objective": "Restore fixture",
            "scope": {"include": ["Test"]}, "workflow": "secure-flow",
        }), encoding="utf-8")
        self.project.add_task("second", "TASK-002")
        with patch.object(ide_bridge, "MAX_TASK_DIRECTORIES", 1):
            self.assert_error(self.request(), "resource_limit")

    def test_bounded_handle_read_detects_growth_after_initial_file_stat(self):
        growing = self.root / "growing.yaml"
        growing.write_bytes(b"{}")
        samestat = os.path.samestat
        grew = False

        def grow_after_stat(opened, confirmed):
            nonlocal grew
            if not grew:
                grew = True
                growing.write_bytes(b"x" * 65)
            return samestat(opened, confirmed)

        with (
            patch.object(ide_bridge, "MAX_YAML_BYTES", 64),
            patch(
                "engineering_orchestration.ide_bridge.os.path.samestat",
                side_effect=grow_after_stat,
            ),
            self.assertRaises(ide_bridge.BridgeError) as raised,
        ):
            ide_bridge._read_bounded_file(growing, "Growing YAML", self.root)

        self.assertTrue(grew)
        self.assertEqual(raised.exception.code, "resource_limit")

    def test_workflow_file_and_combined_diagnostic_limits_are_enforced(self):
        self.project.write_workflow(self.project.workflows / "second.yaml")
        with patch.object(ide_bridge, "MAX_WORKFLOW_FILES", 1):
            self.assert_error(self.request(), "resource_limit")

        (self.project.workflows / "second.yaml").unlink()
        broken = self.project.tasks / "broken"
        broken.mkdir()
        (broken / "task.yaml").write_text("[]", encoding="utf-8")
        with patch.object(ide_bridge, "MAX_DIAGNOSTICS", 1):
            self.assert_error(self.request(), "resource_limit")

    def test_invalid_json_duplicate_keys_trailing_data_and_nonfinite_rejected(self):
        samples = (
            b"{",
            b'{"request_id":"a","request_id":"b"}',
            b"{} {}",
            b'{"value":NaN}',
            b"\xff",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                self.assert_error(ide_bridge.process_request_bytes(sample), "invalid_json")

    def test_oversized_request_is_rejected_before_json_decode(self):
        response = ide_bridge.process_request_bytes(b" " * (ide_bridge.MAX_REQUEST_BYTES + 1))
        self.assert_error(response, "resource_limit")
        self.assertIsNone(response["request_id"])

    def test_closed_envelope_payload_operations_and_protocol(self):
        cases = [
            ({"extra": True}, "invalid_request"),
            ({"operation": "verify"}, "invalid_request"),
            ({"protocol": "aio.ide/2"}, "unsupported_protocol"),
            ({"request_id": "has space"}, "invalid_request"),
            ({"project_root": "relative"}, "invalid_request"),
            ({"payload": {}}, "invalid_request"),
            ({"payload": {"status": None, "workflow": None, "extra": 1}},
             "invalid_request"),
        ]
        for changes, code in cases:
            with self.subTest(changes=changes):
                response = self.request(**changes)
                self.assert_error(response, code)

    def test_task_payload_rejects_unknown_fields_overlong_and_surrogate_ids(self):
        for payload in (
            {"task_id": "TASK-001", "path": "elsewhere"},
            {"task_id": "x" * 257},
            {"task_id": "\ud800"},
        ):
            with self.subTest(payload=repr(payload)):
                self.assert_error(self.request("task_detail", payload), "invalid_request")

    def test_unmanaged_missing_root_and_file_root_errors_are_distinct(self):
        unmanaged = self.root.parent / "unmanaged"
        unmanaged.mkdir()
        self.assert_error(self.request(project_root=str(unmanaged)), "unmanaged_project")
        self.assert_error(
            self.request(project_root=str(self.root.parent / "absent")),
            "invalid_project",
        )
        file_root = self.root.parent / "file-root"
        file_root.write_text("not a directory", encoding="utf-8")
        self.assert_error(self.request(project_root=str(file_root)), "invalid_project")

    def test_unexpected_failures_are_sanitized_internal_errors(self):
        secret = "SHOULD-NOT-LEAK"
        with patch(
            "engineering_orchestration.ide_bridge._preflight_project",
            side_effect=RuntimeError(secret),
        ):
            response = self.request()
        self.assert_error(response, "internal_error")
        self.assertNotIn(secret, json.dumps(response))

    def test_response_serialization_is_bounded_and_replaces_large_success(self):
        response = ide_bridge._response(
            "request-1", result={"large": "x" * 2000}
        )
        with patch.object(ide_bridge, "MAX_RESPONSE_BYTES", 700):
            encoded = ide_bridge._serialized_response(response)
        parsed = json.loads(encoded)
        self.assert_error(parsed, "resource_limit")

    def test_meta_reports_package_version_and_absolute_origin(self):
        response = self.request()
        self.assertEqual(set(response["meta"]), {"package_version", "package_origin"})
        self.assertEqual(response["meta"]["package_version"], "0.1.0")
        origin = Path(response["meta"]["package_origin"])
        self.assertTrue(origin.is_absolute())
        self.assertEqual(origin.name, "engineering_orchestration")

    def test_cli_process_emits_only_one_json_value_and_empty_stderr(self):
        request = {
            "protocol": ide_bridge.PROTOCOL,
            "request_id": "subprocess-1",
            "operation": "task_detail",
            "project_root": str(self.root),
            "payload": {"task_id": "TASK-001"},
        }
        result = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", "-m",
             "engineering_orchestration.ide_bridge"],
            cwd=Path(__file__).resolve().parents[1],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            shell=False,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertEqual(result.stdout.count("\n"), 1)

    def test_cwd_shadow_file_is_never_consulted_by_in_process_bridge(self):
        hostile = self.root.parent / "hostile-cwd"
        fake_package = hostile / "engineering_orchestration"
        fake_package.mkdir(parents=True)
        (fake_package / "__init__.py").write_text(
            "raise RuntimeError('shadow imported')\n", encoding="utf-8"
        )
        previous = Path.cwd()
        try:
            os.chdir(hostile)
            response = self.request("task_detail")
        finally:
            os.chdir(previous)
        self.assertTrue(response["ok"], response)
        self.assertNotIn("hostile-cwd", response["meta"]["package_origin"])


if __name__ == "__main__":
    unittest.main()
