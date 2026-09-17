#!/usr/bin/env python3
"""AI Engineering Orchestra — Unit tests for Workflow catalog and resolution."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.workflow_catalog import (
    WorkflowCatalog,
    WorkflowCatalogError,
    WorkflowDefinition,
    WorkflowStage,
    load_workflow_catalog,
    resolve_workflow,
)


def create_sample_workflow_dict(
    workflow_id: str = "custom-workflow",
    name: str = "Custom Workflow",
    purpose: str = "Govern custom engineering work.",
    stages: list[dict] | None = None,
    applicable_task_types: list[str] | None = None,
) -> dict:
    if stages is None:
        stages = [
            {"id": "understand", "purpose": "Understand context."},
            {
                "id": "implement",
                "purpose": "Implement change.",
                "required_roles": ["software-engineer"],
            },
            {
                "id": "validate",
                "purpose": "Validate change.",
                "required_quality_gates": ["custom_gate"],
            },
            {
                "id": "review",
                "purpose": "Review change.",
                "required_roles": ["reviewer"],
                "human_control_checkpoint": True,
            },
        ]
    doc = {
        "id": workflow_id,
        "name": name,
        "purpose": purpose,
        "stages": stages,
    }
    if applicable_task_types is not None:
        doc["applicable_task_types"] = applicable_task_types
    return doc


class TestWorkflowCatalog(unittest.TestCase):
    """Unit tests for load_workflow_catalog and resolve_workflow."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_workflows_dir = Path(self.temp_dir.name) / "workflows"
        self.test_workflows_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_yaml(self, filename: str, content: dict | str) -> Path:
        path = self.test_workflows_dir / filename
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            with path.open("w", encoding="utf-8") as f:
                yaml.safe_dump(content, f, sort_keys=False)
        return path

    def test_canonical_workflows_load(self) -> None:
        """Verify the repository's canonical workflows load cleanly without errors."""
        catalog = load_workflow_catalog()
        self.assertTrue(catalog.is_valid)
        self.assertEqual(len(catalog.load_errors), 0)
        self.assertIn("standard-change", catalog)
        self.assertIn("architecture-change", catalog)
        self.assertIn("security-sensitive-change", catalog)

        sc = catalog.get("standard-change")
        self.assertIsNotNone(sc)
        self.assertEqual(sc.id, "standard-change")
        self.assertEqual(sc.stage_count, 4)
        self.assertEqual(sc.stage_ids, ["understand", "implement", "validate", "review"])
        self.assertEqual(sc.checkpoint_stage_ids, ["review"])
        self.assertEqual(sc.workflow_quality_gates, [])

        ac = catalog.get("architecture-change")
        self.assertIsNotNone(ac)
        self.assertEqual(ac.stage_count, 5)
        self.assertEqual(ac.workflow_quality_gates, ["documentation_consistency", "independent_review"])

    def test_multiple_workflows_form_catalog(self) -> None:
        """Verify multiple valid YAML files form a single coherent catalog."""
        self._write_yaml("wf1.yaml", create_sample_workflow_dict("wf-alpha", "Alpha"))
        self._write_yaml("wf2.yaml", create_sample_workflow_dict("wf-beta", "Beta"))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertTrue(catalog.is_valid)
        self.assertEqual(catalog.workflow_ids, ["wf-alpha", "wf-beta"])
        self.assertIsNotNone(catalog.get("wf-alpha"))
        self.assertIsNotNone(catalog.get("wf-beta"))

    def test_resolution_works_by_declared_id_not_filename(self) -> None:
        """Verify resolution matches the declared id inside the file, NOT the filename."""
        # Filename is completely different from declared ID
        self._write_yaml("arbitrary-filename.yaml", create_sample_workflow_dict("declared-unique-id"))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertTrue(catalog.is_valid)
        self.assertIn("declared-unique-id", catalog)
        self.assertNotIn("arbitrary-filename", catalog)

        resolved = catalog.get("declared-unique-id")
        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.id, "declared-unique-id")
        self.assertEqual(resolved.source_path.name, "arbitrary-filename.yaml")

    def test_unknown_workflow_reports_unresolved(self) -> None:
        """Verify querying a non-existent ID returns None."""
        self._write_yaml("wf.yaml", create_sample_workflow_dict("wf-1"))
        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertIsNone(catalog.get("unknown-id"))
        self.assertIsNone(resolve_workflow("unknown-id", workflows_dir=self.test_workflows_dir))

    def test_duplicate_declared_workflow_ids_rejected(self) -> None:
        """Verify two files declaring the same workflow ID are detected and reported."""
        self._write_yaml("file-a.yaml", create_sample_workflow_dict("duplicate-id", "Version A"))
        self._write_yaml("file-b.yaml", create_sample_workflow_dict("duplicate-id", "Version B"))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("Duplicate declared Workflow ID 'duplicate-id'" in err for err in catalog.load_errors))

    def test_malformed_yaml_rejected(self) -> None:
        """Verify malformed YAML syntax produces a load error."""
        self._write_yaml("broken.yaml", "id: [unclosed list\nname: test")
        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("YAML parse error" in err for err in catalog.load_errors))

    def test_non_object_yaml_root_rejected(self) -> None:
        """Verify scalar or list YAML root is rejected."""
        self._write_yaml("list-root.yaml", "- item1\n- item2\n")
        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("root content is not a mapping" in err for err in catalog.load_errors))

    def test_structurally_invalid_workflow_rejected(self) -> None:
        """Verify schema violations (e.g. missing required field) are rejected."""
        data = create_sample_workflow_dict("bad-wf")
        del data["purpose"]  # required field
        self._write_yaml("invalid.yaml", data)

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("purpose" in err for err in catalog.load_errors))

    def test_duplicate_stage_ids_within_workflow_rejected(self) -> None:
        """Verify duplicate stage IDs within a single workflow are rejected."""
        stages = [
            {"id": "understand", "purpose": "First stage."},
            {"id": "understand", "purpose": "Duplicate stage ID."},
        ]
        self._write_yaml("dup-stages.yaml", create_sample_workflow_dict("dup-stages-wf", stages=stages))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("duplicate Stage ID 'understand'" in err for err in catalog.load_errors))

    def test_stage_order_preserved(self) -> None:
        """Verify stage order in the parsed definition strictly matches the source file."""
        stages = [
            {"id": "first", "purpose": "P1"},
            {"id": "second", "purpose": "P2"},
            {"id": "third", "purpose": "P3"},
            {"id": "fourth", "purpose": "P4"},
        ]
        self._write_yaml("ordered.yaml", create_sample_workflow_dict("ordered-wf", stages=stages))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        wf = catalog.get("ordered-wf")
        self.assertIsNotNone(wf)
        self.assertEqual(wf.stage_ids, ["first", "second", "third", "fourth"])

    def test_omitted_optional_fields_remain_omitted(self) -> None:
        """Verify omitted optional fields on stages remain None/empty, not defaulted."""
        stages = [
            {"id": "minimal-stage", "purpose": "Minimal stage purpose."},
        ]
        self._write_yaml("omitted.yaml", create_sample_workflow_dict("omitted-wf", stages=stages))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        wf = catalog.get("omitted-wf")
        self.assertIsNotNone(wf)
        stage = wf.stages[0]
        self.assertIsNone(stage.human_control_checkpoint)
        self.assertEqual(stage.required_roles, [])
        self.assertEqual(stage.required_quality_gates, [])

    def test_explicit_false_checkpoint_distinguishable_from_omission(self) -> None:
        """Verify human_control_checkpoint: false is preserved as False (not None)."""
        stages = [
            {"id": "explicit-false", "purpose": "P1", "human_control_checkpoint": False},
            {"id": "omitted", "purpose": "P2"},
            {"id": "explicit-true", "purpose": "P3", "human_control_checkpoint": True},
        ]
        self._write_yaml("checkpoints.yaml", create_sample_workflow_dict("checkpoints-wf", stages=stages))

        catalog = load_workflow_catalog(workflows_dir=self.test_workflows_dir)
        wf = catalog.get("checkpoints-wf")
        self.assertIsNotNone(wf)
        self.assertIs(wf.stages[0].human_control_checkpoint, False)
        self.assertIsNone(wf.stages[1].human_control_checkpoint)
        self.assertIs(wf.stages[2].human_control_checkpoint, True)
        self.assertEqual(wf.checkpoint_stage_ids, ["explicit-true"])


if __name__ == "__main__":
    unittest.main()
