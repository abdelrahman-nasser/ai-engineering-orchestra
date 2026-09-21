"""Fast package-boundary regressions; isolated pip evidence is a separate smoke test."""

import ast
import importlib
import engineering_orchestration.role_catalog as role_catalog
from importlib.metadata import EntryPoint
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from engineering_orchestration import cli
from engineering_orchestration.role_catalog import (
    find_default_roles_resource,
    load_role_catalog,
)
from engineering_orchestration.schema_resources import schema_resource


ROOT = Path(__file__).resolve().parents[1]
PACKAGED_SCHEMAS = (
    "actor.schema.json",
    "actor-availability.schema.json",
    "actor-runtime-applicability.schema.json",
    "agent-runtime-option.schema.json",
    "agent-runtime-option-availability.schema.json",
    "assignment.schema.json",
    "inference-option.schema.json",
    "inference-option-availability.schema.json",
    "operation-requirement.schema.json",
    "runtime-inference-compatibility.schema.json",
    "role.schema.json",
    "task.schema.json",
    "workflow.schema.json",
    "project-manifest.schema.json",
)
PACKAGED_ROLES = (
    "architect.yaml",
    "documentation-specialist.yaml",
    "reviewer.yaml",
    "security-reviewer.yaml",
    "software-engineer.yaml",
)


class PackagingTests(unittest.TestCase):
    def test_metadata_and_only_temporary_console(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(data["project"]["requires-python"], ">=3.12")
        self.assertEqual(set(data["project"]["dependencies"]),
                         {"PyYAML>=6,<7", "jsonschema>=4,<5"})
        self.assertEqual(data["project"]["scripts"],
                         {"aio": "engineering_orchestration.cli:main"})
        self.assertEqual(data["build-system"]["build-backend"], "setuptools.build_meta")

    def test_console_alias_loads_same_callable(self):
        for name in ("aio", "rook"):
            entry = EntryPoint(name=name, value="engineering_orchestration.cli:main",
                               group="console_scripts")
            self.assertIs(entry.load(), cli.main)

    def test_compatibility_modules_are_single_implementation(self):
        for name in ("cli", "list_tasks", "inspect_task", "verify_repo", "workflow_catalog"):
            with self.subTest(name=name):
                legacy = importlib.import_module(f"scripts.{name}")
                packaged = importlib.import_module(f"engineering_orchestration.{name}")
                self.assertIs(legacy, packaged)
                tree = ast.parse((ROOT / "scripts" / f"{name}.py").read_text(encoding="utf-8"))
                self.assertFalse(any(isinstance(n, (ast.FunctionDef, ast.ClassDef))
                                     for n in ast.walk(tree)))

    def test_packaged_schema_content_matches_canonical_source(self):
        for name in PACKAGED_SCHEMAS:
            self.assertEqual(schema_resource(name).read_bytes(),
                             (ROOT / "schemas" / name).read_bytes())

    def test_packaged_role_content_matches_canonical_source(self):
        resources = find_default_roles_resource()
        self.assertIsNotNone(resources)
        actual = sorted(
            item.name for item in resources.iterdir()
            if item.is_file() and item.name.endswith(".yaml")
        )
        self.assertEqual(actual, list(PACKAGED_ROLES))
        for name in PACKAGED_ROLES:
            self.assertEqual(
                resources.joinpath(name).read_bytes(),
                (ROOT / "roles" / name).read_bytes(),
            )

    def test_schema_lookup_does_not_consult_cwd(self):
        with patch("pathlib.Path.cwd", side_effect=AssertionError("CWD is project data")):
            for name in PACKAGED_SCHEMAS:
                self.assertIsInstance(json.loads(schema_resource(name).read_text()), dict)

    def test_role_lookup_does_not_consult_cwd(self):
        with patch("pathlib.Path.cwd", side_effect=AssertionError("CWD is project data")):
            self.assertEqual(len(load_role_catalog().role_ids), 5)

    def test_missing_installed_schema_never_uses_checkout_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("engineering_orchestration.schema_resources.files", return_value=Path(folder)):
                self.assertIsNone(schema_resource("task.schema.json"))

    def test_missing_installed_roles_never_use_checkout_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = ModuleNotFoundError(name="engineering_orchestration._roles")
            with patch("engineering_orchestration.role_catalog.files", side_effect=missing), \
                    patch("engineering_orchestration.role_catalog.__file__",
                          str(Path(folder) / "package" / "role_catalog.py")):
                self.assertIsNone(role_catalog.find_default_roles_resource())

    def test_uninstalled_resource_failure_does_not_search_target(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = ModuleNotFoundError(name="engineering_orchestration._schemas")
            with patch("engineering_orchestration.schema_resources.files", side_effect=missing), \
                    patch("engineering_orchestration.schema_resources.__file__",
                          str(Path(folder) / "package" / "schema_resources.py")):
                self.assertIsNone(schema_resource("task.schema.json"))

    def test_package_location_is_not_a_project_marker(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch("pathlib.Path.cwd", return_value=Path(folder)), \
                    patch("pathlib.Path.is_file", return_value=False):
                with self.assertRaises(FileNotFoundError):
                    cli.find_project_root()

    def test_explicit_resource_allowlist(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        config = data["tool"]["setuptools"]
        self.assertFalse(config["include-package-data"])
        self.assertEqual(config["packages"],
                         ["engineering_orchestration", "engineering_orchestration._schemas",
                          "engineering_orchestration._roles"])
        self.assertEqual(config["package-data"], {
            "engineering_orchestration._schemas": list(PACKAGED_SCHEMAS),
            "engineering_orchestration._roles": ["*.yaml"],
        })

    def test_documented_scope_is_local_and_verify_is_portable(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("project-declared Verification Checks", readme)
        self.assertIn("aio verify --structure", readme)
        self.assertIn("no sandbox", readme)
        self.assertIn("No PyPI publication", readme)
        self.assertIn("does not\ncomplete the future public distribution milestone", readme)


if __name__ == "__main__":
    unittest.main()
