#!/usr/bin/env python3
"""AI Engineering Orchestra — Unit tests for inspect_task utility."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.inspect_task import (
    CANONICAL_ARTIFACTS,
    TaskInspectionResult,
    format_report,
    inspect_task,
    main,
)


def create_minimal_valid_task_yaml(
    task_id: str = "AIO-TEST",
    status: str = "in_progress",
    quality_gates: list[str] | None = None,
    human_control: dict[str, bool] | None = None,
    risk: str = "medium",
    complexity: str = "medium",
    execution_mode: str = "standard",
    workflow: str | None = None,
) -> dict:
    doc = {
        "id": task_id,
        "title": "Test Task Title",
        "type": "implementation",
        "status": status,
        "version_target": "0.1.0",
        "complexity": complexity,
        "risk": risk,
        "execution": {
            "mode": execution_mode,
        },
        "objective": "Test task objective statement.",
        "scope": {
            "include": ["test item 1", "test item 2"],
            "exclude": ["excluded item"],
        },
        "dependencies": ["AIO-001"],
    }
    if workflow is not None:
        doc["workflow"] = workflow
    if quality_gates is not None:
        doc["quality_gates"] = quality_gates
    if human_control is not None:
        doc["human_control"] = human_control
    return doc


def create_minimal_project_manifest(
    require_review: bool = True,
    require_doc: bool = True,
    default_risk: str = "medium",
    default_complexity: str = "medium",
    default_mode: str = "standard",
) -> dict:
    return {
        "schema_version": "0.1",
        "project": {
            "id": "test-project",
            "name": "Test Project",
            "type": "framework",
            "lifecycle": "greenfield",
        },
        "orchestra": {
            "version": "0.1.0",
        },
        "complexity": {
            "default": default_complexity,
        },
        "risk": {
            "default": default_risk,
        },
        "execution": {
            "default_mode": default_mode,
        },
        "human_control": {
            "final_review_required": True,
            "architecture_changes_require_approval": True,
            "breaking_schema_changes_require_approval": True,
            "breaking_contract_changes_require_approval": True,
        },
        "quality": {
            "require_independent_review": require_review,
            "require_documentation_consistency": require_doc,
        },
    }


class TestInspectTask(unittest.TestCase):
    """Unit tests for inspect_task utility."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)
        self.task_dir = self.test_root / "tasks" / "AIO-TEST-sample"
        self.task_dir.mkdir(parents=True)

        # Create project manifest in temp root
        self.project_manifest_path = self.test_root / ".ai" / "project.yaml"
        self.project_manifest_path.parent.mkdir(parents=True)
        with self.project_manifest_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(create_minimal_project_manifest(), f)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _populate_canonical_artifacts(
        self,
        task_yaml_content: dict | str | None = None,
        context_content: str = "# Context\nSample context.",
        acceptance_content: str = "# Acceptance Criteria\n- [ ] item",
        review_content: str = "# Review\nSample review.",
    ) -> None:
        if task_yaml_content is not None:
            task_yaml_file = self.task_dir / "task.yaml"
            if isinstance(task_yaml_content, str):
                task_yaml_file.write_text(task_yaml_content, encoding="utf-8")
            else:
                with task_yaml_file.open("w", encoding="utf-8") as f:
                    yaml.safe_dump(task_yaml_content, f)

        if context_content is not None:
            (self.task_dir / "context.md").write_text(context_content, encoding="utf-8")
        if acceptance_content is not None:
            (self.task_dir / "acceptance-criteria.md").write_text(
                acceptance_content, encoding="utf-8"
            )
        if review_content is not None:
            (self.task_dir / "review.md").write_text(review_content, encoding="utf-8")

    def test_valid_task_directory(self) -> None:
        """Verify inspection of a fully valid task directory."""
        self._populate_canonical_artifacts(create_minimal_valid_task_yaml())
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_status, "VALID")
        self.assertEqual(result.task_id, "AIO-TEST")
        self.assertEqual(result.status, "in_progress")
        self.assertTrue(all(result.canonical_artifacts.values()))

        # CLI should return exit code 0
        with patch("sys.stdout", new_callable=io.StringIO):
            exit_code = main(
                [str(self.task_dir), "--project-manifest", str(self.project_manifest_path)]
            )
        self.assertEqual(exit_code, 0)

    def test_invalid_task_yaml_schema(self) -> None:
        """Verify invalid enum or schema violation is caught."""
        data = create_minimal_valid_task_yaml()
        data["status"] = "invalid_status"
        self._populate_canonical_artifacts(data)

        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "INVALID")
        self.assertTrue(len(result.schema_errors) > 0)
        self.assertIn("status", result.schema_errors[0])

        with patch("sys.stdout", new_callable=io.StringIO):
            exit_code = main(
                [str(self.task_dir), "--project-manifest", str(self.project_manifest_path)]
            )
        self.assertEqual(exit_code, 1)

    def test_invalid_task_yaml_syntax(self) -> None:
        """Verify malformed YAML syntax produces an INVALID schema status."""
        self._populate_canonical_artifacts(task_yaml_content="id: [unclosed list")
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "INVALID")
        self.assertTrue(any("YAML parse error" in e for e in result.schema_errors))

    def test_invalid_task_yaml_non_dict(self) -> None:
        """Verify non-dictionary YAML produces an INVALID schema status."""
        self._populate_canonical_artifacts(task_yaml_content="just a string\n")
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "INVALID")
        self.assertTrue(any("not a mapping" in e for e in result.schema_errors))

    def test_missing_task_yaml(self) -> None:
        """Verify missing task.yaml is detected and reported."""
        self._populate_canonical_artifacts(task_yaml_content=None)
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "MISSING")
        self.assertFalse(result.canonical_artifacts["task.yaml"])

        with patch("sys.stdout", new_callable=io.StringIO):
            exit_code = main(
                [str(self.task_dir), "--project-manifest", str(self.project_manifest_path)]
            )
        self.assertEqual(exit_code, 1)

    def test_missing_canonical_markdown_artifact(self) -> None:
        """Verify missing canonical markdown files cause is_valid to be False."""
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(),
            context_content=None,  # context.md missing
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertFalse(result.canonical_artifacts["context.md"])
        self.assertEqual(result.schema_status, "VALID")

        with patch("sys.stdout", new_callable=io.StringIO):
            exit_code = main(
                [str(self.task_dir), "--project-manifest", str(self.project_manifest_path)]
            )
        self.assertEqual(exit_code, 1)

    def test_completed_task(self) -> None:
        """Verify status: completed is inspected correctly and valid."""
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(status="completed")
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, "completed")

    def test_in_progress_task(self) -> None:
        """Verify status: in_progress is inspected correctly and valid."""
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(status="in_progress")
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, "in_progress")

    def test_declared_quality_gates(self) -> None:
        """Verify task-declared quality gates are extracted deterministically."""
        gates = ["independent_review", "documentation_consistency"]
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(quality_gates=gates)
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        # Should be sorted
        self.assertEqual(
            result.task_quality_gates,
            ["documentation_consistency", "independent_review"],
        )

    def test_project_required_quality_gates(self) -> None:
        """Verify project-required quality gates are loaded and combined."""
        gates = ["documentation_consistency"]
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(quality_gates=gates)
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertEqual(
            result.project_required_gates,
            ["documentation_consistency", "independent_review"],
        )
        self.assertEqual(
            result.machine_readable_gates,
            ["documentation_consistency", "independent_review"],
        )

    def test_project_manifest_unavailable(self) -> None:
        """Verify fallback behavior when project manifest does not exist."""
        # Create an isolated task directory outside test_root
        with tempfile.TemporaryDirectory() as isolated_temp:
            isolated_dir = Path(isolated_temp) / "AIO-ISOLATED"
            isolated_dir.mkdir()
            for name in CANONICAL_ARTIFACTS:
                if name == "task.yaml":
                    with (isolated_dir / name).open("w", encoding="utf-8") as f:
                        yaml.safe_dump(
                            create_minimal_valid_task_yaml(
                                quality_gates=["documentation_consistency"]
                            ),
                            f,
                        )
                else:
                    (isolated_dir / name).write_text(f"# {name}", encoding="utf-8")

            # Point to nonexistent manifest
            nonexistent = Path(isolated_temp) / "nonexistent.yaml"
            result = inspect_task(isolated_dir, project_manifest_path=nonexistent)
            self.assertFalse(result.project_manifest_available)
            self.assertEqual(result.project_required_gates, [])
            self.assertEqual(
                result.machine_readable_gates, ["documentation_consistency"]
            )

            report = format_report(result)
            self.assertIn("NOT AVAILABLE (project manifest not found)", report)

    def test_deterministic_output_ordering(self) -> None:
        """Verify format_report outputs fields, artifacts, and gates in deterministic order."""
        data1 = create_minimal_valid_task_yaml(
            quality_gates=["independent_review", "documentation_consistency"]
        )
        self._populate_canonical_artifacts(data1)
        res1 = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        rep1 = format_report(res1)

        # Reverse list in task.yaml
        data2 = create_minimal_valid_task_yaml(
            quality_gates=["documentation_consistency", "independent_review"]
        )
        with (self.task_dir / "task.yaml").open("w", encoding="utf-8") as f:
            yaml.safe_dump(data2, f)
        res2 = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        rep2 = format_report(res2)

        self.assertEqual(rep1, rep2)

    def test_workflow_declared_displayed(self) -> None:
        """Verify declared workflow is reported with TASK-DECLARED binding and RESOLVED status."""
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(workflow="standard-change")
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.workflow, "standard-change")
        self.assertEqual(result.workflow_binding, "TASK-DECLARED")
        self.assertEqual(result.workflow_resolution, "RESOLVED")
        self.assertEqual(result.workflow_stages_count, 4)
        self.assertEqual(result.workflow_checkpoints, ["review"])

        report = format_report(result)
        expected_workflow_block = (
            "Workflow\n"
            "--------\n"
            "standard-change\n"
            "Binding: TASK-DECLARED\n"
            "Resolution: RESOLVED\n"
            "Stages: 4\n"
            "Human Control Checkpoints: review"
        )
        self.assertIn(expected_workflow_block, report)

    def test_workflow_omitted_displayed(self) -> None:
        """Verify omitted workflow is reported as NOT DECLARED."""
        self._populate_canonical_artifacts(create_minimal_valid_task_yaml())
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.workflow)
        self.assertIsNone(result.workflow_binding)
        self.assertIsNone(result.workflow_resolution)

        report = format_report(result)
        self.assertIn("Workflow\n--------\nNOT DECLARED", report)

    def test_workflow_invalid_type(self) -> None:
        """Verify non-string workflow type fails schema validation."""
        data = create_minimal_valid_task_yaml()
        data["workflow"] = 123
        self._populate_canonical_artifacts(data)
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "INVALID")
        self.assertTrue(any("workflow" in e for e in result.schema_errors))

    def test_workflow_empty_string(self) -> None:
        """Verify empty string workflow fails schema validation."""
        data = create_minimal_valid_task_yaml()
        data["workflow"] = ""
        self._populate_canonical_artifacts(data)
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.schema_status, "INVALID")
        self.assertTrue(any("workflow" in e for e in result.schema_errors))

    def test_no_markdown_parsing_from_context(self) -> None:
        """Verify inspect_task does NOT machine-parse workflow from context.md."""
        context_with_workflow = (
            "# Context\n\n"
            "## Governing Workflow\n\n"
            "standard-change\n"
        )
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(),
            context_content=context_with_workflow,
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        report = format_report(result)

        self.assertIsNone(result.workflow)
        self.assertIn("Workflow\n--------\nNOT DECLARED", report)
        self.assertNotIn("Binding: TASK-DECLARED", report)

    def test_workflow_unresolved_unknown_binding(self) -> None:
        """Verify inspect_task reports UNRESOLVED and invalid for unknown workflow binding."""
        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(workflow="arbitrary-custom-wf")
        )
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.workflow, "arbitrary-custom-wf")
        self.assertEqual(result.workflow_binding, "TASK-DECLARED")
        self.assertEqual(result.workflow_resolution, "UNRESOLVED")

        report = format_report(result)
        self.assertIn("arbitrary-custom-wf", report)
        self.assertIn("Resolution: UNRESOLVED", report)

    def test_effective_quality_gates_includes_workflow_contribution(self) -> None:
        """Verify workflow stage quality gates are merged into effective quality gates."""
        no_gates_manifest = self.test_root / "no_gates.yaml"
        with no_gates_manifest.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                create_minimal_project_manifest(require_review=False, require_doc=False), f
            )

        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(quality_gates=[], workflow="architecture-change")
        )
        result = inspect_task(self.task_dir, project_manifest_path=no_gates_manifest)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.workflow_resolution, "RESOLVED")
        self.assertEqual(
            result.workflow_required_gates,
            ["documentation_consistency", "independent_review"],
        )
        self.assertEqual(
            result.effective_quality_gates,
            ["documentation_consistency", "independent_review"],
        )

    def test_resolution_independent_of_filename_in_inspection(self) -> None:
        """Verify inspection resolves workflow by declared ID even when filename differs."""
        custom_wf_dir = self.test_root / "custom_workflows"
        custom_wf_dir.mkdir()
        wf_content = {
            "id": "my-special-flow",
            "name": "Special Flow",
            "purpose": "A special governance flow.",
            "stages": [
                {
                    "id": "stage-one",
                    "purpose": "First stage.",
                    "required_quality_gates": ["custom_stage_gate"],
                }
            ],
        }
        with (custom_wf_dir / "differing_filename.yaml").open("w", encoding="utf-8") as f:
            yaml.safe_dump(wf_content, f)

        self._populate_canonical_artifacts(
            create_minimal_valid_task_yaml(workflow="my-special-flow")
        )
        result = inspect_task(
            self.task_dir,
            project_manifest_path=self.project_manifest_path,
            workflows_dir=custom_wf_dir,
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.workflow_resolution, "RESOLVED")
        self.assertEqual(result.workflow_stages_count, 1)
        self.assertIn("custom_stage_gate", result.effective_quality_gates)

    def test_existing_aio_010_behavior_remains_valid(self) -> None:
        """Verify existing AIO-010 task remains valid without workflow field."""
        aio_010_dir = REPO_ROOT / ".ai" / "tasks" / "AIO-010-task-status-inspection"
        self.assertTrue(aio_010_dir.is_dir())
        result = inspect_task(aio_010_dir)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.schema_status, "VALID")
        self.assertIsNone(result.workflow)

        report = format_report(result)
        self.assertIn("Workflow\n--------\nNOT DECLARED", report)

    def test_unknown_input_nonexistent_directory(self) -> None:
        """Verify CLI and function handle nonexistent path properly."""
        nonexistent = self.test_root / "nonexistent-dir"
        with self.assertRaises(FileNotFoundError):
            inspect_task(nonexistent)

        # CLI should return exit code 2
        with patch("sys.stderr", new_callable=io.StringIO):
            exit_code = main([str(nonexistent)])
        self.assertEqual(exit_code, 2)

    def test_unexpected_input_file_not_directory(self) -> None:
        """Verify CLI and function handle file path input properly."""
        file_path = self.test_root / "somefile.txt"
        file_path.write_text("content", encoding="utf-8")

        with self.assertRaises(NotADirectoryError):
            inspect_task(file_path)

        with patch("sys.stderr", new_callable=io.StringIO):
            exit_code = main([str(file_path)])
        self.assertEqual(exit_code, 2)

    def test_human_control_cumulative_inheritance(self) -> None:
        """Verify human control merging: task cannot weaken project requirement."""
        # Project requires final_review_required=True
        # Task declares final_review_required=False
        data = create_minimal_valid_task_yaml(
            human_control={"final_review_required": False}
        )
        self._populate_canonical_artifacts(data)
        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        # Effective value must remain True because Project requires it
        eff_val, eff_src = result.effective_human_control["final_review_required"]
        self.assertTrue(eff_val)
        self.assertIn("project", eff_src)

    def test_metadata_inheritance_from_project(self) -> None:
        """Verify risk/complexity/execution default inheritance when omitted from task.yaml."""
        data = create_minimal_valid_task_yaml()
        del data["risk"]
        del data["complexity"]
        del data["execution"]
        self._populate_canonical_artifacts(data)

        result = inspect_task(
            self.task_dir, project_manifest_path=self.project_manifest_path
        )
        self.assertEqual(result.risk, "medium")
        self.assertEqual(result.risk_source, "project")
        self.assertEqual(result.complexity, "medium")
        self.assertEqual(result.complexity_source, "project")
        self.assertEqual(result.execution_mode, "standard")
        self.assertEqual(result.execution_mode_source, "project")

        report = format_report(result)
        self.assertIn("Risk: medium (inherited: project)", report)

    def test_metadata_overrides_are_independent(self) -> None:
        """Verify each explicit Task value overrides only its matching Project default."""
        with self.project_manifest_path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(
                create_minimal_project_manifest(
                    default_complexity="low",
                    default_risk="critical",
                    default_mode="lite",
                ),
                file,
            )

        cases = (
            ("complexity", "high"),
            ("risk", "low"),
            ("execution", "deep"),
        )
        for explicit_field, explicit_value in cases:
            with self.subTest(explicit_field=explicit_field):
                data = create_minimal_valid_task_yaml()
                del data["complexity"]
                del data["risk"]
                del data["execution"]
                if explicit_field == "execution":
                    data[explicit_field] = {"mode": explicit_value}
                else:
                    data[explicit_field] = explicit_value
                self._populate_canonical_artifacts(data)

                result = inspect_task(
                    self.task_dir, project_manifest_path=self.project_manifest_path
                )
                expected = {
                    "complexity": (
                        "high" if explicit_field == "complexity" else "low",
                        "task" if explicit_field == "complexity" else "project",
                    ),
                    "risk": (
                        "low" if explicit_field == "risk" else "critical",
                        "task" if explicit_field == "risk" else "project",
                    ),
                    "execution_mode": (
                        "deep" if explicit_field == "execution" else "lite",
                        "task" if explicit_field == "execution" else "project",
                    ),
                }
                self.assertEqual(
                    (result.complexity, result.complexity_source),
                    expected["complexity"],
                )
                self.assertEqual(
                    (result.risk, result.risk_source), expected["risk"]
                )
                self.assertEqual(
                    (result.execution_mode, result.execution_mode_source),
                    expected["execution_mode"],
                )

    def test_workflow_does_not_determine_inherited_execution_mode(self) -> None:
        """Verify distinct Workflows inherit the same independent Project mode."""
        stage_counts = {}
        for workflow in ("standard-change", "architecture-change"):
            data = create_minimal_valid_task_yaml(workflow=workflow)
            del data["execution"]
            self._populate_canonical_artifacts(data)
            result = inspect_task(
                self.task_dir, project_manifest_path=self.project_manifest_path
            )
            self.assertTrue(result.is_valid)
            self.assertEqual(result.execution_mode, "standard")
            self.assertEqual(result.execution_mode_source, "project")
            stage_counts[workflow] = result.workflow_stages_count

        self.assertEqual(
            stage_counts,
            {"standard-change": 4, "architecture-change": 5},
        )

    def test_execution_mode_does_not_choose_workflow(self) -> None:
        """Verify explicit modes do not create a Workflow binding."""
        for mode in ("lite", "critical"):
            with self.subTest(mode=mode):
                data = create_minimal_valid_task_yaml(execution_mode=mode)
                self._populate_canonical_artifacts(data)
                result = inspect_task(
                    self.task_dir, project_manifest_path=self.project_manifest_path
                )
                self.assertTrue(result.is_valid)
                self.assertEqual(result.execution_mode, mode)
                self.assertIsNone(result.workflow)
                self.assertIsNone(result.workflow_resolution)

    def test_execution_mode_does_not_change_workflow_governance(self) -> None:
        """Verify mode changes leave Workflow, Gate, and Human Control facts intact."""
        snapshots = []
        for mode in ("lite", "critical"):
            data = create_minimal_valid_task_yaml(
                execution_mode=mode,
                quality_gates=["task_specific_gate"],
                human_control={"final_review_required": False},
                workflow="architecture-change",
            )
            self._populate_canonical_artifacts(data)
            result = inspect_task(
                self.task_dir, project_manifest_path=self.project_manifest_path
            )
            self.assertTrue(result.is_valid)
            self.assertEqual(result.execution_mode, mode)
            self.assertIn("task_specific_gate", result.effective_quality_gates)
            self.assertIn(
                "independent_review", result.effective_quality_gates
            )
            self.assertTrue(
                result.effective_human_control["final_review_required"][0]
            )
            snapshots.append(
                (
                    result.workflow,
                    result.workflow_stages_count,
                    result.workflow_checkpoints,
                    result.workflow_required_gates,
                    result.effective_quality_gates,
                    result.effective_human_control,
                )
            )

        self.assertEqual(snapshots[0], snapshots[1])


if __name__ == "__main__":
    unittest.main()
