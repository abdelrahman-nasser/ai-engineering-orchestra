"""Fast package-boundary regressions; isolated pip evidence is a separate smoke test."""

import ast
import hashlib
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
from engineering_orchestration.schema_resources import load_validator, schema_resource
from engineering_orchestration._sqlite_admission_migrations import MIGRATIONS
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    _migration_bytes,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGED_SCHEMAS = (
    "actor.schema.json",
    "actor-availability.schema.json",
    "actor-runtime-applicability.schema.json",
    "agent-operation-tool-binding.schema.json",
    "agent-execution-authorization-grant.schema.json",
    "agent-execution-dispatch-admission.schema.json",
    "agent-execution-authorization-evidence.schema.json",
    "agent-execution-contract.schema.json",
    "agent-execution-run.schema.json",
    "agent-runtime-option.schema.json",
    "agent-runtime-option-availability.schema.json",
    "assignment.schema.json",
    "environment-operation-permission.schema.json",
    "inference-option.schema.json",
    "inference-option-availability.schema.json",
    "operation-requirement.schema.json",
    "runtime-operation-capability.schema.json",
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
                         {"PyYAML>=6,<7", "jsonschema>=4.18,<5",
                          "referencing>=0.28.4,<1"})
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

    def test_packaged_sqlite_admission_migration_is_allowlisted_and_checksummed(self):
        self.assertEqual(len(MIGRATIONS), 1)
        migration = MIGRATIONS[0]
        loaded = _migration_bytes()
        self.assertIn(
            "engineering_orchestration/_sqlite_admission_migrations/*.sql "
            "text eol=lf",
            (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines(),
        )
        self.assertNotIn(b"\r", loaded[0][3])
        self.assertEqual(
            loaded,
            ((
                migration.migration_id,
                migration.resource_name,
                migration.sha256,
                (
                    ROOT
                    / "engineering_orchestration"
                    / "_sqlite_admission_migrations"
                    / migration.resource_name
                ).read_bytes(),
            ),),
        )
        self.assertEqual(
            hashlib.sha256(loaded[0][3]).hexdigest(),
            migration.sha256,
        )

    def test_missing_sqlite_admission_migration_fails_without_fallback(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "engineering_orchestration."
            "sqlite_agent_execution_dispatch_admission_store.files",
            return_value=Path(folder),
        ):
            with self.assertRaisesRegex(
                Exception,
                "packaged migration is unavailable",
            ):
                _migration_bytes()

    def test_schema_lookup_does_not_consult_cwd(self):
        with patch("pathlib.Path.cwd", side_effect=AssertionError("CWD is project data")):
            for name in PACKAGED_SCHEMAS:
                self.assertIsInstance(json.loads(schema_resource(name).read_text()), dict)

    def test_run_schema_resolves_packaged_contract_offline(self):
        document = {
            "run_id": "run::packaging-test",
            "contract": {
                "task_id": "synthetic-task",
                "workflow_id": "architecture-change",
                "stage_id": "implement",
                "role_id": "software-engineer",
                "actor_id": "actor::synthetic",
                "runtime_option_id": "runtime::synthetic",
                "option_id": "option::synthetic",
                "environment_id": "environment::synthetic",
                "operation_id": "repository_file_read",
                "resource": "synthetic/input.txt",
                "execution_mode": "standard",
            },
        }
        blocked = AssertionError("schema resolution attempted external access")
        with patch("pathlib.Path.cwd", side_effect=blocked), \
                patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator("agent-execution-run.schema.json")
            validator.validate(document)
            invalid = json.loads(json.dumps(document))
            invalid["contract"]["actor_id"] = ""
            errors = list(validator.iter_errors(invalid))
        self.assertEqual(
            [(error.validator, tuple(error.absolute_path)) for error in errors],
            [("minLength", ("contract", "actor_id"))],
        )

    def test_run_schema_unregistered_reference_fails_closed(self):
        blocked = AssertionError("schema resolution attempted network access")
        with patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator("agent-execution-run.schema.json")
            unknown = validator.evolve(schema={
                "$ref": "https://example.invalid/unregistered.schema.json",
            })
            with self.assertRaises(Exception) as caught:
                unknown.validate({})
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("unregistered.schema.json", str(caught.exception))

    def test_run_schema_missing_packaged_contract_fails_without_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            resources = Path(folder)
            (resources / "agent-execution-run.schema.json").write_bytes(
                (ROOT / "schemas" / "agent-execution-run.schema.json").read_bytes()
            )
            with patch(
                "engineering_orchestration.schema_resources.files",
                return_value=resources,
            ):
                with self.assertRaisesRegex(
                    FileNotFoundError,
                    "agent-execution-contract.schema.json",
                ):
                    load_validator("agent-execution-run.schema.json")

    def test_run_schema_rejects_mismatched_packaged_contract_id(self):
        with tempfile.TemporaryDirectory() as folder:
            resources = Path(folder)
            (resources / "agent-execution-run.schema.json").write_bytes(
                (ROOT / "schemas" / "agent-execution-run.schema.json").read_bytes()
            )
            contract = json.loads(
                (ROOT / "schemas" / "agent-execution-contract.schema.json")
                .read_text(encoding="utf-8")
            )
            contract["$id"] = "https://example.invalid/substitute.schema.json"
            (resources / "agent-execution-contract.schema.json").write_text(
                json.dumps(contract),
                encoding="utf-8",
            )
            with patch(
                "engineering_orchestration.schema_resources.files",
                return_value=resources,
            ):
                with self.assertRaisesRegex(ValueError, "canonical ID mismatch"):
                    load_validator("agent-execution-run.schema.json")

    def test_tool_binding_schema_resolves_packaged_run_and_contract_offline(self):
        document = {
            "run": {
                "run_id": "run::binding-packaging-test",
                "contract": {
                    "task_id": "synthetic-task",
                    "workflow_id": "architecture-change",
                    "stage_id": "implement",
                    "role_id": "software-engineer",
                    "actor_id": "actor::synthetic",
                    "runtime_option_id": "runtime::synthetic",
                    "option_id": "option::synthetic",
                    "environment_id": "environment::synthetic",
                    "operation_id": "repository_file_read",
                    "resource": "synthetic/input.txt",
                    "execution_mode": "deep",
                },
            },
            "tool_id": "tool::synthetic-repository-reader::v1",
        }
        blocked = AssertionError("schema resolution attempted external access")
        with patch("pathlib.Path.cwd", side_effect=blocked), \
                patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(
                "agent-operation-tool-binding.schema.json"
            )
            validator.validate(document)
            invalid = json.loads(json.dumps(document))
            invalid["run"]["contract"]["actor_id"] = ""
            errors = list(validator.iter_errors(invalid))
        self.assertEqual(
            [(error.validator, tuple(error.absolute_path)) for error in errors],
            [("minLength", ("run", "contract", "actor_id"))],
        )

    def test_tool_binding_schema_unregistered_reference_fails_closed(self):
        blocked = AssertionError("schema resolution attempted network access")
        with patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(
                "agent-operation-tool-binding.schema.json"
            )
            unknown = validator.evolve(schema={
                "$ref": "https://example.invalid/unregistered.schema.json",
            })
            with self.assertRaises(Exception) as caught:
                unknown.validate({})
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("unregistered.schema.json", str(caught.exception))

    def test_tool_binding_schema_missing_references_fail_without_fallback(self):
        dependencies = (
            "agent-execution-run.schema.json",
            "agent-execution-contract.schema.json",
        )
        for missing_name in dependencies:
            with self.subTest(missing=missing_name), \
                    tempfile.TemporaryDirectory() as folder:
                resources = Path(folder)
                for name in (
                    "agent-operation-tool-binding.schema.json",
                    *dependencies,
                ):
                    if name != missing_name:
                        (resources / name).write_bytes(
                            (ROOT / "schemas" / name).read_bytes()
                        )
                with patch(
                    "engineering_orchestration.schema_resources.files",
                    return_value=resources,
                ):
                    with self.assertRaisesRegex(FileNotFoundError, missing_name):
                        load_validator(
                            "agent-operation-tool-binding.schema.json"
                        )

    def test_tool_binding_schema_rejects_mismatched_reference_ids(self):
        dependencies = (
            "agent-execution-run.schema.json",
            "agent-execution-contract.schema.json",
        )
        for mismatched_name in dependencies:
            with self.subTest(reference=mismatched_name), \
                    tempfile.TemporaryDirectory() as folder:
                resources = Path(folder)
                (resources / "agent-operation-tool-binding.schema.json").write_bytes(
                    (
                        ROOT
                        / "schemas"
                        / "agent-operation-tool-binding.schema.json"
                    ).read_bytes()
                )
                for name in dependencies:
                    document = json.loads(
                        (ROOT / "schemas" / name).read_text(encoding="utf-8")
                    )
                    if name == mismatched_name:
                        document["$id"] = (
                            "https://example.invalid/substitute.schema.json"
                        )
                    (resources / name).write_text(
                        json.dumps(document),
                        encoding="utf-8",
                    )
                with patch(
                    "engineering_orchestration.schema_resources.files",
                    return_value=resources,
                ):
                    with self.assertRaisesRegex(ValueError, "canonical ID mismatch"):
                        load_validator(
                            "agent-operation-tool-binding.schema.json"
                        )

    def test_grant_schema_resolves_packaged_run_and_contract_offline(self):
        document = {
            "grant_id": "grant::packaging-test",
            "run": {
                "run_id": "run::packaging-test",
                "contract": {
                    "task_id": "synthetic-task",
                    "workflow_id": "architecture-change",
                    "stage_id": "implement",
                    "role_id": "software-engineer",
                    "actor_id": "actor::synthetic",
                    "runtime_option_id": "runtime::synthetic",
                    "option_id": "option::synthetic",
                    "environment_id": "environment::synthetic",
                    "operation_id": "repository_file_read",
                    "resource": "synthetic/input.txt",
                    "execution_mode": "critical",
                },
            },
            "authorization_domain_id": "authorization-domain::synthetic",
            "issuer_kind": "human",
            "issuer_id": "human::synthetic-reviewer",
            "provenance_reference": "approval::synthetic",
            "issued_at": "2026-09-22T10:00:00Z",
            "expires_at": "2026-09-22T10:05:00Z",
        }
        blocked = AssertionError("schema resolution attempted external access")
        with patch("pathlib.Path.cwd", side_effect=blocked), \
                patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(
                "agent-execution-authorization-grant.schema.json"
            )
            validator.validate(document)
            invalid = json.loads(json.dumps(document))
            invalid["run"]["contract"]["actor_id"] = ""
            errors = list(validator.iter_errors(invalid))
        self.assertEqual(
            [(error.validator, tuple(error.absolute_path)) for error in errors],
            [("minLength", ("run", "contract", "actor_id"))],
        )

    def test_grant_schema_unregistered_reference_fails_closed(self):
        blocked = AssertionError("schema resolution attempted network access")
        with patch("socket.create_connection", side_effect=blocked), \
                patch("socket.getaddrinfo", side_effect=blocked), \
                patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(
                "agent-execution-authorization-grant.schema.json"
            )
            unknown = validator.evolve(schema={
                "$ref": "https://example.invalid/unregistered.schema.json",
            })
            with self.assertRaises(Exception) as caught:
                unknown.validate({})
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("unregistered.schema.json", str(caught.exception))

    def test_grant_schema_missing_packaged_references_fail_without_fallback(self):
        dependencies = (
            "agent-execution-run.schema.json",
            "agent-execution-contract.schema.json",
        )
        for missing_name in dependencies:
            with self.subTest(missing=missing_name), tempfile.TemporaryDirectory() as folder:
                resources = Path(folder)
                for name in (
                    "agent-execution-authorization-grant.schema.json",
                    *dependencies,
                ):
                    if name != missing_name:
                        (resources / name).write_bytes(
                            (ROOT / "schemas" / name).read_bytes()
                        )
                with patch(
                    "engineering_orchestration.schema_resources.files",
                    return_value=resources,
                ):
                    with self.assertRaisesRegex(FileNotFoundError, missing_name):
                        load_validator(
                            "agent-execution-authorization-grant.schema.json"
                        )

    def test_grant_schema_rejects_mismatched_packaged_reference_ids(self):
        dependencies = (
            "agent-execution-run.schema.json",
            "agent-execution-contract.schema.json",
        )
        for mismatched_name in dependencies:
            with self.subTest(reference=mismatched_name), tempfile.TemporaryDirectory() as folder:
                resources = Path(folder)
                (resources / "agent-execution-authorization-grant.schema.json").write_bytes(
                    (
                        ROOT
                        / "schemas"
                        / "agent-execution-authorization-grant.schema.json"
                    ).read_bytes()
                )
                for name in dependencies:
                    document = json.loads(
                        (ROOT / "schemas" / name).read_text(encoding="utf-8")
                    )
                    if name == mismatched_name:
                        document["$id"] = (
                            "https://example.invalid/substitute.schema.json"
                        )
                    (resources / name).write_text(
                        json.dumps(document),
                        encoding="utf-8",
                    )
                with patch(
                    "engineering_orchestration.schema_resources.files",
                    return_value=resources,
                ):
                    with self.assertRaisesRegex(ValueError, "canonical ID mismatch"):
                        load_validator(
                            "agent-execution-authorization-grant.schema.json"
                        )

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
                          "engineering_orchestration._roles",
                          "engineering_orchestration._sqlite_admission_migrations"])
        self.assertEqual(config["package-data"], {
            "engineering_orchestration._schemas": list(PACKAGED_SCHEMAS),
            "engineering_orchestration._roles": ["*.yaml"],
            "engineering_orchestration._sqlite_admission_migrations": ["*.sql"],
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
