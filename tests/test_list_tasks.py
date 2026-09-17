#!/usr/bin/env python3
"""AI Engineering Orchestra — Unit Tests for Task Inventory and Discovery Utility.

Tests cover all 16 minimum acceptance scenarios required by AIO-013:
1. discovers multiple valid Tasks
2. canonical identity comes from task.yaml.id
3. directory name does not determine Task ID
4. deterministic ordering
5. completed status filtering
6. in-progress filtering
7. Workflow filtering by declared ID
8. Workflow resolution reports RESOLVED
9. omitted Workflow reports NOT DECLARED
10. unknown declared Workflow reports UNRESOLVED
11. directory missing task.yaml handled without crashing entire inventory
12. malformed YAML handled deterministically
13. structurally invalid Task handled deterministically
14. one bad Task does not suppress valid Tasks
15. no subprocess parsing of inspect_task.py
16. no Workflow filename inference
"""

from __future__ import annotations

import ast
import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.list_tasks import (
    REPO_ROOT,
    TaskInventoryResult,
    discover_tasks,
    filter_tasks,
    format_inventory_table,
    main,
)


def create_minimal_task_yaml(
    task_id: str,
    title: str = "Test Task",
    task_type: str = "implementation",
    status: str = "in_progress",
    workflow: str | None = None,
) -> dict:
    """Helper to build a schema-valid task.yaml dictionary."""
    data = {
        "id": task_id,
        "title": title,
        "type": task_type,
        "status": status,
        "objective": f"Objective for {task_id}",
        "scope": {
            "include": ["Some included item"],
        },
    }
    if workflow is not None:
        data["workflow"] = workflow
    return data


class TestListTasks(unittest.TestCase):
    """Test suite for scripts/list_tasks.py."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="aio_test_list_tasks_")
        self.temp_path = Path(self.temp_dir)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # 1. Discovers multiple valid Tasks
    def test_discovers_multiple_valid_tasks(self) -> None:
        """Verify discover_tasks finds multiple valid canonical Tasks in repository."""
        inventory = discover_tasks()
        self.assertGreaterEqual(len(inventory.valid_tasks), 13)
        task_ids = [t.task_id for t in inventory.valid_tasks]
        self.assertIn("AIO-001", task_ids)
        self.assertIn("AIO-011", task_ids)
        self.assertIn("AIO-012", task_ids)
        self.assertIn("AIO-013", task_ids)
        self.assertFalse(inventory.has_anomalies)

    # 2. Canonical identity comes from task.yaml.id
    def test_canonical_identity_comes_from_task_yaml_id(self) -> None:
        """Verify Task identity is read directly from task.yaml.id."""
        task_dir = self.temp_path / "task-folder"
        task_dir.mkdir()
        task_data = create_minimal_task_yaml("CANONICAL-ID-042")
        (task_dir / "task.yaml").write_text(yaml.dump(task_data), encoding="utf-8")

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].task_id, "CANONICAL-ID-042")

    # 3. Directory name does not determine Task ID
    def test_directory_name_does_not_determine_task_id(self) -> None:
        """Verify arbitrary directory names do NOT influence canonical Task identity."""
        arbitrary_dir = self.temp_path / "completely-unrelated-dir-name-999"
        arbitrary_dir.mkdir()
        task_data = create_minimal_task_yaml("TRUE-TASK-ID-007")
        (arbitrary_dir / "task.yaml").write_text(yaml.dump(task_data), encoding="utf-8")

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].task_id, "TRUE-TASK-ID-007")
        self.assertNotIn("completely-unrelated-dir-name-999", inventory.valid_tasks[0].task_id)

    # 4. Deterministic ordering
    def test_deterministic_ordering(self) -> None:
        """Verify valid Tasks are deterministically sorted by declared canonical ID."""
        for tid, dirname in [("TASK-Z", "dir-1"), ("TASK-A", "dir-2"), ("TASK-M", "dir-3")]:
            td = self.temp_path / dirname
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(tid)), encoding="utf-8"
            )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        ordered_ids = [t.task_id for t in inventory.valid_tasks]
        self.assertEqual(ordered_ids, ["TASK-A", "TASK-M", "TASK-Z"])

    # 5. Completed status filtering
    def test_status_filter_completed(self) -> None:
        """Verify --status completed returns only tasks with completed status."""
        for tid, st in [("T-1", "completed"), ("T-2", "in_progress"), ("T-3", "completed")]:
            td = self.temp_path / tid
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(tid, status=st)), encoding="utf-8"
            )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        completed = filter_tasks(inventory.valid_tasks, status="completed")
        self.assertEqual([t.task_id for t in completed], ["T-1", "T-3"])
        for t in completed:
            self.assertEqual(t.status, "completed")

    # 6. In-progress filtering
    def test_status_filter_in_progress(self) -> None:
        """Verify --status in_progress returns only tasks with in_progress status."""
        for tid, st in [("T-1", "completed"), ("T-2", "in_progress"), ("T-3", "in_progress")]:
            td = self.temp_path / tid
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(tid, status=st)), encoding="utf-8"
            )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        in_prog = filter_tasks(inventory.valid_tasks, status="in_progress")
        self.assertEqual([t.task_id for t in in_prog], ["T-2", "T-3"])
        for t in in_prog:
            self.assertEqual(t.status, "in_progress")

    # 7. Workflow filtering by declared ID
    def test_workflow_filter_by_declared_id(self) -> None:
        """Verify --workflow standard-change includes only tasks explicitly declaring it."""
        for tid, wf in [
            ("T-WF1", "standard-change"),
            ("T-WF2", None),
            ("T-WF3", "architecture-change"),
            ("T-WF4", "standard-change"),
        ]:
            td = self.temp_path / tid
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(tid, workflow=wf)), encoding="utf-8"
            )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        wf_filtered = filter_tasks(inventory.valid_tasks, workflow="standard-change")
        self.assertEqual([t.task_id for t in wf_filtered], ["T-WF1", "T-WF4"])
        # Omitted workflows must NOT match
        for t in wf_filtered:
            self.assertEqual(t.workflow, "standard-change")

    # 8. Workflow resolution reports RESOLVED
    def test_workflow_resolution_reports_resolved(self) -> None:
        """Verify a declared resolvable Workflow reports RESOLVED."""
        td = self.temp_path / "task-resolved"
        td.mkdir()
        (td / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("T-RESOLVED", workflow="standard-change")),
            encoding="utf-8",
        )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].workflow, "standard-change")
        self.assertEqual(inventory.valid_tasks[0].resolution, "RESOLVED")

        output = format_inventory_table(inventory)
        self.assertIn("standard-change", output)
        self.assertIn("RESOLVED", output)

    # 9. Omitted Workflow reports NOT DECLARED
    def test_workflow_omitted_reports_not_declared(self) -> None:
        """Verify an omitted Workflow reports '-' and NOT DECLARED."""
        td = self.temp_path / "task-no-wf"
        td.mkdir()
        (td / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("T-NO-WF")), encoding="utf-8"
        )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertIsNone(inventory.valid_tasks[0].workflow)
        self.assertEqual(inventory.valid_tasks[0].resolution, "NOT DECLARED")

        output = format_inventory_table(inventory)
        self.assertIn("NOT DECLARED", output)

    # 10. Unknown declared Workflow reports UNRESOLVED
    def test_unknown_declared_workflow_reports_unresolved(self) -> None:
        """Verify an unknown declared Workflow reports UNRESOLVED and is visible in table."""
        td = self.temp_path / "task-unresolved"
        td.mkdir()
        (td / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("T-UNRESOLVED", workflow="non-existent-wf")),
            encoding="utf-8",
        )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].workflow, "non-existent-wf")
        self.assertEqual(inventory.valid_tasks[0].resolution, "UNRESOLVED")

        output = format_inventory_table(inventory)
        self.assertIn("non-existent-wf", output)
        self.assertIn("UNRESOLVED", output)

    # 11. Directory missing task.yaml handled without crashing entire inventory
    def test_directory_missing_task_yaml_handled_gracefully(self) -> None:
        """Verify child directory lacking task.yaml is handled as anomaly without crash."""
        empty_dir = self.temp_path / "empty-directory"
        empty_dir.mkdir()

        valid_dir = self.temp_path / "valid-task"
        valid_dir.mkdir()
        (valid_dir / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("VALID-1")), encoding="utf-8"
        )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].task_id, "VALID-1")
        self.assertEqual(len(inventory.anomalies), 1)
        self.assertEqual(inventory.anomalies[0].dir_name, "empty-directory")
        self.assertIn("task.yaml not found", inventory.anomalies[0].reason)

        output = format_inventory_table(inventory)
        self.assertIn("VALID-1", output)
        self.assertIn("empty-directory", output)
        self.assertIn("Repository Anomalies / Diagnostics", output)

    # 12. Malformed YAML handled deterministically
    def test_malformed_yaml_handled_deterministically(self) -> None:
        """Verify syntax-corrupt task.yaml is handled as anomaly without crashing."""
        corrupt_dir = self.temp_path / "corrupt-task"
        corrupt_dir.mkdir()
        (corrupt_dir / "task.yaml").write_text("id: [unclosed list", encoding="utf-8")

        valid_dir = self.temp_path / "valid-task"
        valid_dir.mkdir()
        (valid_dir / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("VALID-YAML")), encoding="utf-8"
        )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].task_id, "VALID-YAML")
        self.assertEqual(len(inventory.anomalies), 1)
        self.assertEqual(inventory.anomalies[0].dir_name, "corrupt-task")
        self.assertIn("malformed", inventory.anomalies[0].reason)

    # 13. Structurally invalid Task handled deterministically
    def test_structurally_invalid_task_handled_deterministically(self) -> None:
        """Verify schema-invalid task.yaml is handled as anomaly without crashing."""
        invalid_dir = self.temp_path / "schema-invalid"
        invalid_dir.mkdir()
        # Invalid status enum
        invalid_data = create_minimal_task_yaml("INVALID-ENUM", status="not_a_valid_status")
        (invalid_dir / "task.yaml").write_text(yaml.dump(invalid_data), encoding="utf-8")

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 0)
        self.assertEqual(len(inventory.anomalies), 1)
        self.assertEqual(inventory.anomalies[0].dir_name, "schema-invalid")
        self.assertTrue(len(inventory.anomalies[0].details) > 0)

    # 14. One bad Task does not suppress valid Tasks
    def test_one_bad_task_does_not_suppress_valid_tasks(self) -> None:
        """Verify an anomaly in one directory does not suppress other valid Tasks."""
        for i in range(3):
            td = self.temp_path / f"good-task-{i}"
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(f"GOOD-{i}")), encoding="utf-8"
            )

        bad_td = self.temp_path / "bad-task"
        bad_td.mkdir()
        (bad_td / "task.yaml").write_text("not: valid: yaml: :", encoding="utf-8")

        inventory = discover_tasks(tasks_dir=self.temp_path)
        self.assertEqual(len(inventory.valid_tasks), 3)
        self.assertEqual([t.task_id for t in inventory.valid_tasks], ["GOOD-0", "GOOD-1", "GOOD-2"])
        self.assertEqual(len(inventory.anomalies), 1)
        self.assertEqual(inventory.anomalies[0].dir_name, "bad-task")

    # 15. No subprocess parsing of inspect_task.py
    def test_no_subprocess_parsing_of_inspect_task(self) -> None:
        """Verify list_tasks.py does NOT spawn subprocesses or parse inspect_task stdout."""
        script_file = REPO_ROOT / "engineering_orchestration" / "list_tasks.py"
        source = script_file.read_text(encoding="utf-8")
        tree = ast.parse(source)

        # Check imports for subprocess
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(
                        alias.name,
                        "subprocess",
                        "list_tasks.py must not import subprocess",
                    )
            elif isinstance(node, ast.ImportFrom):
                self.assertNotEqual(
                    node.module,
                    "subprocess",
                    "list_tasks.py must not import from subprocess",
                )

        # Verify execution with subprocess mocked raises AssertionError if invoked
        with patch("subprocess.run", side_effect=AssertionError("subprocess.run called")), \
             patch("subprocess.Popen", side_effect=AssertionError("subprocess.Popen called")):
            inv = discover_tasks(tasks_dir=self.temp_path)
            self.assertIsInstance(inv, TaskInventoryResult)

    # 16. No Workflow filename inference
    def test_no_workflow_filename_inference(self) -> None:
        """Verify Workflow resolution matches declared Workflow ID, independent of filename."""
        wf_dir = self.temp_path / "workflows"
        wf_dir.mkdir()
        # Create a workflow file with arbitrary name declaring id: declared-wf-id
        custom_wf_file = wf_dir / "arbitrary_custom_filename.yaml"
        custom_wf_data = {
            "id": "declared-wf-id",
            "name": "Custom Workflow",
            "purpose": "Test workflow for filename independence",
            "stages": [
                {"id": "step1", "purpose": "First stage"},
            ],
        }
        custom_wf_file.write_text(yaml.dump(custom_wf_data), encoding="utf-8")

        # Create a task declaring workflow: declared-wf-id
        tasks_dir = self.temp_path / "tasks"
        tasks_dir.mkdir()
        td = tasks_dir / "task-1"
        td.mkdir()
        (td / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("T-1", workflow="declared-wf-id")),
            encoding="utf-8",
        )

        inventory = discover_tasks(tasks_dir=tasks_dir, workflows_dir=wf_dir)
        self.assertEqual(len(inventory.valid_tasks), 1)
        self.assertEqual(inventory.valid_tasks[0].workflow, "declared-wf-id")
        self.assertEqual(inventory.valid_tasks[0].resolution, "RESOLVED")

    # Additional CLI and exit code tests
    def test_cli_exit_code_zero_when_clean(self) -> None:
        """Verify main() exits 0 when all tasks are clean and valid."""
        td = self.temp_path / "clean-task"
        td.mkdir()
        (td / "task.yaml").write_text(
            yaml.dump(create_minimal_task_yaml("CLEAN-1")), encoding="utf-8"
        )

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["--tasks-dir", str(self.temp_path)])
        self.assertEqual(exit_code, 0)
        self.assertIn("CLEAN-1", buf.getvalue())

    def test_cli_exit_code_one_when_anomalies_present(self) -> None:
        """Verify main() exits 1 when repository anomalies are detected."""
        empty_dir = self.temp_path / "missing-yaml-dir"
        empty_dir.mkdir()

        buf = io.StringIO()
        with redirect_stdout(buf):
            exit_code = main(["--tasks-dir", str(self.temp_path)])
        self.assertEqual(exit_code, 1)
        self.assertIn("missing-yaml-dir", buf.getvalue())
        self.assertIn("Repository Anomalies / Diagnostics", buf.getvalue())

    def test_combined_filters(self) -> None:
        """Verify conjunctive filtering with both --status and --workflow."""
        for tid, st, wf in [
            ("T-1", "completed", "standard-change"),
            ("T-2", "in_progress", "standard-change"),
            ("T-3", "completed", "architecture-change"),
        ]:
            td = self.temp_path / tid
            td.mkdir()
            (td / "task.yaml").write_text(
                yaml.dump(create_minimal_task_yaml(tid, status=st, workflow=wf)),
                encoding="utf-8",
            )

        inventory = discover_tasks(tasks_dir=self.temp_path)
        matching = filter_tasks(inventory.valid_tasks, status="completed", workflow="standard-change")
        self.assertEqual([t.task_id for t in matching], ["T-1"])


if __name__ == "__main__":
    unittest.main()
