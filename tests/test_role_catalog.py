"""Runtime Role catalog, compatibility, and Actor-coverage regressions."""

from __future__ import annotations

import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import yaml

from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.role_catalog import (
    CANONICAL_ROLE_IDS,
    RoleCatalogError,
    load_role_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROLE_IDS = list(CANONICAL_ROLE_IDS)
EXPECTED_COMPETENCIES = {
    "architecture-analysis",
    "requirements-analysis",
    "source-code-analysis",
    "evidence-evaluation",
    "documentation-analysis",
    "security-analysis",
    "risk-analysis",
    "software-implementation",
    "automated-testing",
}


def role(role_id: str = "example", required=None) -> dict:
    return {
        "id": role_id,
        "name": "Example",
        "purpose": "Exercise the concrete Role catalog.",
        "responsibilities": ["inspect-evidence"],
        "required_capabilities": list(
            ["evidence-evaluation"] if required is None else required
        ),
    }


class RoleCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.roles_dir = Path(self.temporary.name)

    def write(self, filename: str, data: dict | str) -> Path:
        path = self.roles_dir / filename
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path

    def seed_canonical(self, *, filenames=None, documents=None, omit=()):
        filenames = filenames or {}
        documents = documents or {}
        for role_id in EXPECTED_ROLE_IDS:
            if role_id not in omit:
                self.write(
                    filenames.get(role_id, f"{role_id}.yaml"),
                    documents.get(role_id, role(role_id)),
                )

    def load_test_catalog(self):
        with patch(
            "engineering_orchestration.role_catalog.find_default_roles_resource",
            return_value=self.roles_dir,
        ):
            return load_role_catalog()

    def test_five_canonical_roles_load_with_exact_expected_ids(self):
        catalog = load_role_catalog()
        self.assertTrue(catalog.is_valid, catalog.load_errors)
        self.assertEqual(catalog.role_ids, EXPECTED_ROLE_IDS)
        self.assertEqual(len(catalog.definitions), 5)

    def test_lookup_uses_declared_id_not_filename(self):
        self.seed_canonical(filenames={"software-engineer": "arbitrary-name.yaml"})
        catalog = self.load_test_catalog()
        self.assertTrue(catalog.is_valid)
        self.assertEqual(catalog.get("software-engineer")["id"], "software-engineer")
        self.assertIsNone(catalog.get("arbitrary-name"))

    def test_unknown_role_returns_none_without_corrupting_catalog(self):
        self.seed_canonical()
        catalog = self.load_test_catalog()
        self.assertIsNone(catalog.get("unknown"))
        self.assertTrue(catalog.is_valid)

    def test_duplicate_declared_ids_invalidate_catalog(self):
        self.seed_canonical()
        self.write("duplicate.yaml", role("architect"))
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertEqual(len(catalog.definitions), 5)
        self.assertTrue(any(
            "Duplicate declared Role ID 'architect'" in error
            for error in catalog.load_errors
        ))

    def test_malformed_yaml_is_rejected(self):
        self.seed_canonical()
        self.write("broken.yaml", "id: [unclosed\n")
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("YAML parse error" in error for error in catalog.load_errors))

    def test_non_object_yaml_root_is_rejected(self):
        self.seed_canonical()
        self.write("list.yaml", "- role\n")
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any(
            "root content is not a mapping/object" in error
            for error in catalog.load_errors
        ))

    def test_schema_invalid_role_is_rejected(self):
        self.seed_canonical()
        invalid = role()
        invalid.pop("name")
        self.write("invalid.yaml", invalid)
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any("name" in error for error in catalog.load_errors))

    def test_missing_packaged_schema_is_infrastructure_error(self):
        self.seed_canonical()
        with patch(
            "engineering_orchestration.role_catalog.find_default_roles_resource",
            return_value=self.roles_dir,
        ), patch(
            "engineering_orchestration.role_catalog.find_default_role_schema_path",
            return_value=None,
        ):
            catalog = load_role_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertEqual(catalog.load_errors, catalog.infrastructure_errors)
        self.assertIn("Required tool schema missing", catalog.load_errors[0])

    def test_missing_packaged_role_resources_is_infrastructure_error(self):
        with patch(
            "engineering_orchestration.role_catalog.find_default_roles_resource",
            return_value=None,
        ):
            catalog = load_role_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertEqual(catalog.load_errors, catalog.infrastructure_errors)
        self.assertIn("resources not found", catalog.load_errors[0])

    def test_empty_packaged_role_resources_is_infrastructure_error(self):
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertIn("No packaged canonical Role YAML", catalog.load_errors[0])

    def test_raise_on_error_is_narrow_and_deterministic(self):
        with patch(
            "engineering_orchestration.role_catalog.find_default_roles_resource",
            return_value=None,
        ):
            with self.assertRaisesRegex(RoleCatalogError, "resources not found"):
                load_role_catalog(raise_on_error=True)

    def test_role_ids_are_case_sensitive_ascending_declared_ids(self):
        self.seed_canonical(filenames={
            "architect": "z-file.yaml",
            "software-engineer": "a-file.yaml",
        })
        catalog = self.load_test_catalog()
        self.assertEqual(catalog.role_ids, EXPECTED_ROLE_IDS)

    def test_one_missing_packaged_role_invalidates_catalog(self):
        self.seed_canonical(omit={"documentation-specialist"})
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertEqual(catalog.role_ids, [
            "architect", "reviewer", "security-reviewer", "software-engineer"
        ])
        self.assertTrue(any(
            "missing declared IDs: documentation-specialist" in error
            for error in catalog.infrastructure_errors
        ))

    def test_unexpected_declared_role_invalidates_catalog(self):
        self.seed_canonical()
        self.write("extra.yaml", role("extra-role"))
        catalog = self.load_test_catalog()
        self.assertFalse(catalog.is_valid)
        self.assertTrue(any(
            "unexpected declared IDs: extra-role" in error
            for error in catalog.infrastructure_errors
        ))

    def test_markdown_resources_are_ignored(self):
        self.seed_canonical()
        self.write("shadow.md", "id: markdown-role\nprovider: forbidden\n")
        catalog = self.load_test_catalog()
        self.assertTrue(catalog.is_valid)
        self.assertEqual(catalog.role_ids, EXPECTED_ROLE_IDS)

    def test_runtime_module_contains_no_markdown_parser_path(self):
        import engineering_orchestration.role_catalog as module

        source = inspect.getsource(module)
        self.assertNotIn(".md", source)
        self.assertNotIn("extract_role_from_markdown", source)

    def test_canonical_values_are_not_loaded_from_markdown_stubs(self):
        original = Path.read_text

        def reject_markdown(path, *args, **kwargs):
            if path.suffix == ".md":
                raise AssertionError("Runtime attempted to read Role Markdown")
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", autospec=True, side_effect=reject_markdown):
            catalog = load_role_catalog()
        self.assertTrue(catalog.is_valid, catalog.load_errors)
        self.assertEqual(catalog.get("architect")["name"], "Architect")

    def test_actor_coverage_succeeds_with_loaded_software_engineer(self):
        loaded = load_role_catalog().get("software-engineer")
        actor = {
            "id": "agent-engineer",
            "kind": "agent",
            "competencies": list(loaded["required_capabilities"]),
        }
        self.assertTrue(evaluate_actor_role_coverage(actor, loaded).compatible)

    def test_incomplete_actor_reports_missing_loaded_role_competency(self):
        loaded = load_role_catalog().get("software-engineer")
        actor = {
            "id": "agent-engineer",
            "kind": "agent",
            "competencies": ["source-code-analysis"],
        }
        result = evaluate_actor_role_coverage(actor, loaded)
        self.assertFalse(result.compatible)
        self.assertEqual(
            result.missing_competencies,
            ("automated-testing", "evidence-evaluation", "software-implementation"),
        )

    def test_human_actor_works_with_loaded_role(self):
        loaded = load_role_catalog().get("reviewer")
        actor = {"id": "human-reviewer", "kind": "human",
                 "competencies": list(loaded["required_capabilities"])}
        self.assertTrue(evaluate_actor_role_coverage(actor, loaded).compatible)

    def test_agent_actor_works_with_loaded_role(self):
        loaded = load_role_catalog().get("reviewer")
        actor = {"id": "agent-reviewer", "kind": "agent",
                 "competencies": list(loaded["required_capabilities"])}
        self.assertTrue(evaluate_actor_role_coverage(actor, loaded).compatible)

    def test_empty_required_capabilities_load_but_remain_non_matchable(self):
        self.seed_canonical(documents={
            "software-engineer": role("software-engineer", required=[])
        })
        catalog = self.load_test_catalog()
        self.assertTrue(catalog.is_valid)
        actor = {"id": "candidate", "kind": "human", "competencies": ["anything"]}
        result = evaluate_actor_role_coverage(actor, catalog.get("software-engineer"))
        self.assertFalse(result.compatible)
        self.assertEqual(result.diagnostic, "role_required_capabilities_empty")

    def test_canonical_capability_vocabulary_is_unchanged(self):
        catalog = load_role_catalog()
        actual = {
            capability
            for definition in catalog.definitions.values()
            for capability in definition["required_capabilities"]
        }
        self.assertEqual(actual, EXPECTED_COMPETENCIES)

    def test_canonical_roles_have_only_approved_fields(self):
        allowed = {
            "id", "name", "purpose", "responsibilities",
            "required_capabilities", "applicable_task_types",
        }
        catalog = load_role_catalog()
        for role_id, definition in catalog.definitions.items():
            with self.subTest(role=role_id):
                self.assertEqual(set(definition), allowed)
                self.assertTrue(
                    set(definition).isdisjoint(
                        {"actor", "provider", "model", "runtime", "reasoning",
                         "availability", "authority", "permission", "assignment"}
                    )
                )

    def test_all_markdown_compatibility_paths_link_to_authoritative_yaml(self):
        for role_id in EXPECTED_ROLE_IDS:
            with self.subTest(role=role_id):
                path = ROOT / "roles" / f"{role_id}.md"
                content = path.read_text(encoding="utf-8")
                self.assertIn(f"[`{role_id}.yaml`]({role_id}.yaml)", content)
                self.assertIn("non-authoritative stub", content)
                for duplicated_field in (
                    "responsibilities", "required_capabilities", "applicable_task_types"
                ):
                    self.assertNotIn(duplicated_field, content)


if __name__ == "__main__":
    unittest.main()
