"""Contract, semantic, boundary, and purity tests for Operation Requirement."""

from __future__ import annotations

import ast
import asyncio
import builtins
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, fields
import glob
import hashlib
import http.client
import io
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request

import engineering_orchestration
import engineering_orchestration.operation_requirement as operation_requirement
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    OperationRequirementFinding,
    OperationRequirementValidationResult,
    validate_operation_requirement,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "engineering_orchestration" / "operation_requirement.py"


def requirement(
    operation_id: object = "repository_file_read",
    resource: object = "synthetic/input.txt",
) -> OperationRequirement:
    return OperationRequirement(operation_id, resource)  # type: ignore[arg-type]


class OperationRequirementContractTests(unittest.TestCase):
    def test_public_values_are_frozen_with_exact_fields(self) -> None:
        self.assertEqual(
            [field.name for field in fields(OperationRequirement)],
            ["operation_id", "resource"],
        )
        self.assertEqual(
            [field.name for field in fields(OperationRequirementFinding)],
            ["code", "message"],
        )
        self.assertEqual(
            [field.name for field in fields(OperationRequirementValidationResult)],
            ["valid", "findings", "requirement"],
        )
        values = (
            requirement(),
            OperationRequirementFinding("code", "message"),
            OperationRequirementValidationResult(True, (), requirement()),
        )
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    value.valid = False  # type: ignore[attr-defined,misc]

    def test_identity_is_exact_ordered_and_case_sensitive(self) -> None:
        supplied = requirement("repository_file_read", "Synthetic/File.TXT")
        self.assertEqual(
            supplied.identity,
            ("repository_file_read", "Synthetic/File.TXT"),
        )
        self.assertNotEqual(
            supplied.identity,
            ("repository_file_read", "synthetic/file.txt"),
        )

    def test_schema_is_exactly_structural_two_field_contract(self) -> None:
        schema = load_validator("operation-requirement.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["operation_id", "resource"])
        self.assertEqual(
            set(schema["properties"]),
            {"operation_id", "resource"},
        )
        for definition in schema["properties"].values():
            self.assertEqual(definition["type"], "string")
            self.assertEqual(definition["minLength"], 1)
            self.assertNotIn("enum", definition)
            self.assertNotIn("pattern", definition)
            self.assertNotIn("format", definition)

    def test_schema_rejects_excluded_field_categories(self) -> None:
        validator = load_validator("operation-requirement.schema.json")
        base = {
            "operation_id": "repository_file_read",
            "resource": "synthetic/input.txt",
        }
        excluded = {
            "requirement_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "actor_id",
            "runtime_option_id",
            "option_id",
            "environment_id",
            "state",
            "source",
            "reason",
            "timestamp",
            "expires_at",
            "tool",
            "permission",
            "authorization",
            "metadata",
            "extensions",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )

    def test_schema_keeps_semantic_vocabulary_and_path_rules_out(self) -> None:
        validator = load_validator("operation-requirement.schema.json")
        semantic_invalid = (
            {
                "operation_id": "repository_file_write",
                "resource": "synthetic/input.txt",
            },
            {
                "operation_id": "Repository_file_read",
                "resource": "synthetic/input.txt",
            },
            {
                "operation_id": "repository_file_read",
                "resource": "/synthetic/input.txt",
            },
        )
        for document in semantic_invalid:
            with self.subTest(document=document):
                self.assertEqual(list(validator.iter_errors(document)), [])


class OperationRequirementValidationTests(unittest.TestCase):
    def test_valid_value_is_preserved_by_identity(self) -> None:
        supplied = requirement()
        self.assertEqual(
            validate_operation_requirement(supplied),
            OperationRequirementValidationResult(True, (), supplied),
        )
        self.assertIs(validate_operation_requirement(supplied).requirement, supplied)

    def test_nested_case_sensitive_extension_neutral_resources_are_valid(self) -> None:
        resources = (
            "synthetic.txt",
            "nested/deeper/input",
            "Synthetic Data/CaseSensitive/File.JSON",
            ".config/example",
            "folder/name:variant+1",
            "unicode/ملف.txt",
            " spaced segment / trailing space ",
        )
        for resource in resources:
            with self.subTest(resource=resource):
                supplied = requirement(resource=resource)
                result = validate_operation_requirement(supplied)
                self.assertTrue(result.valid)
                self.assertIs(result.requirement, supplied)
                self.assertEqual(result.requirement.resource, resource)

    def test_resource_case_is_identity_not_normalization(self) -> None:
        upper = requirement(resource="Synthetic/File.TXT")
        lower = requirement(resource="synthetic/file.txt")
        upper_result = validate_operation_requirement(upper)
        lower_result = validate_operation_requirement(lower)
        self.assertTrue(upper_result.valid)
        self.assertTrue(lower_result.valid)
        self.assertNotEqual(upper.identity, lower.identity)
        self.assertEqual(upper_result.requirement.resource, upper.resource)
        self.assertEqual(lower_result.requirement.resource, lower.resource)

    def test_only_repository_file_read_is_supported(self) -> None:
        result = validate_operation_requirement(
            requirement(operation_id="repository_file_write")
        )
        self.assertEqual(
            result,
            OperationRequirementValidationResult(
                False,
                (
                    OperationRequirementFinding(
                        "operation_id_not_supported",
                        "Operation ID 'repository_file_write' is not supported by Core.",
                    ),
                ),
                None,
            ),
        )

    def test_well_formed_operation_syntax_is_ascii_lower_snake_case(self) -> None:
        for operation_id in ("read", "read2", "read_2", "sha256_file_read"):
            with self.subTest(operation_id=operation_id):
                result = validate_operation_requirement(
                    requirement(operation_id=operation_id)
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    ["operation_id_not_supported"],
                )

    def test_malformed_operation_ids_are_not_support_checked(self) -> None:
        malformed = (
            "",
            "Repository_file_read",
            "repository_File_read",
            "repository-file-read",
            "repository__file_read",
            "repository_file_read_",
            "_repository_file_read",
            "1repository_file_read",
            "répository_file_read",
            "repository file read",
        )
        for operation_id in malformed:
            with self.subTest(operation_id=operation_id):
                result = validate_operation_requirement(
                    requirement(operation_id=operation_id)
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    ["operation_id_invalid_syntax"],
                )
                self.assertIsNone(result.requirement)

    def test_each_resource_rejection_class_has_locked_finding(self) -> None:
        cases = {
            "": "resource_empty",
            "synthetic/\x00name": "resource_control_character",
            "synthetic/\x1fname": "resource_control_character",
            "synthetic/\x7fname": "resource_control_character",
            "synthetic/\x80name": "resource_control_character",
            "//server/share/input.txt": "resource_unc_path",
            "\\\\server\\share\\input.txt": "resource_unc_path",
            "/synthetic/input.txt": "resource_absolute_path",
            "C:/synthetic/input.txt": "resource_drive_qualified_path",
            "C:synthetic/input.txt": "resource_drive_qualified_path",
            "https://example.invalid/input.txt": "resource_uri_scheme",
            "git+ssh:synthetic/input.txt": "resource_uri_scheme",
            "~/synthetic/input.txt": "resource_leading_tilde",
            "synthetic\\input.txt": "resource_backslash",
            "synthetic/input/": "resource_trailing_slash",
            "synthetic//input.txt": "resource_empty_segment",
            "synthetic/./input.txt": "resource_dot_segment",
            "synthetic/../input.txt": "resource_parent_segment",
        }
        for resource, code in cases.items():
            with self.subTest(resource=resource):
                result = validate_operation_requirement(
                    requirement(resource=resource)
                )
                self.assertFalse(result.valid)
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    [code],
                )
                self.assertIsNone(result.requirement)

    def test_every_locked_glob_meta_character_is_rejected(self) -> None:
        for character in "*?[]{}":
            with self.subTest(character=character):
                result = validate_operation_requirement(
                    requirement(resource=f"synthetic/name{character}.txt")
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    ["resource_glob_meta"],
                )

    def test_resource_precedence_returns_only_first_matching_finding(self) -> None:
        cases = {
            "//server/../*.txt": "resource_unc_path",
            "C:/../*.txt": "resource_drive_qualified_path",
            "https://example.invalid/../*.txt": "resource_uri_scheme",
            "~/../*.txt": "resource_leading_tilde",
            "synthetic\\../*.txt": "resource_backslash",
            "synthetic//../*.txt/": "resource_trailing_slash",
            "synthetic//../*.txt": "resource_empty_segment",
            "synthetic/./../*.txt": "resource_dot_segment",
            "synthetic/../*.txt": "resource_parent_segment",
        }
        for resource, code in cases.items():
            with self.subTest(resource=resource):
                result = validate_operation_requirement(
                    requirement(resource=resource)
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    [code],
                )

    def test_operation_finding_precedes_resource_finding(self) -> None:
        result = validate_operation_requirement(
            requirement("repository_file_write", "synthetic/../*.txt")
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["operation_id_not_supported", "resource_parent_segment"],
        )
        self.assertIsNone(result.requirement)

    def test_exact_value_type_is_required(self) -> None:
        class DerivedRequirement(OperationRequirement):
            pass

        for supplied in (
            None,
            {},
            ("repository_file_read", "synthetic/input.txt"),
            DerivedRequirement("repository_file_read", "synthetic/input.txt"),
        ):
            with self.subTest(type=type(supplied).__name__):
                result = validate_operation_requirement(supplied)
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    ["operation_requirement_invalid_type"],
                )
                self.assertIsNone(result.requirement)

    def test_field_type_findings_are_ordered_and_stop_semantic_validation(self) -> None:
        result = validate_operation_requirement(requirement(7, 8))
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["operation_id_invalid_type", "resource_invalid_type"],
        )
        self.assertIsNone(result.requirement)

        class Text(str):
            pass

        subclass_result = validate_operation_requirement(
            requirement(Text("repository_file_read"), Text("synthetic.txt"))
        )
        self.assertEqual(
            [finding.code for finding in subclass_result.findings],
            ["operation_id_invalid_type", "resource_invalid_type"],
        )

    def test_results_are_repeatable_and_input_is_unchanged(self) -> None:
        supplied = requirement(resource="Synthetic Dir/Exact File.JSON")
        before = (supplied.operation_id, supplied.resource, supplied.identity)
        first = validate_operation_requirement(supplied)
        second = validate_operation_requirement(supplied)
        self.assertEqual(first, second)
        self.assertIs(first.requirement, supplied)
        self.assertIs(second.requirement, supplied)
        self.assertEqual(
            (supplied.operation_id, supplied.resource, supplied.identity),
            before,
        )

    def test_invalid_results_are_atomic(self) -> None:
        cases = (
            requirement("repository_file_write", "synthetic/input.txt"),
            requirement("repository_file_read", "synthetic/../input.txt"),
            requirement("BAD", "/invalid"),
        )
        for supplied in cases:
            with self.subTest(supplied=supplied):
                result = validate_operation_requirement(supplied)
                self.assertFalse(result.valid)
                self.assertTrue(result.findings)
                self.assertIsNone(result.requirement)


class OperationRequirementPurityTests(unittest.TestCase):
    def test_module_imports_only_pure_standard_library_dependencies(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imports.add(node.module)
        self.assertEqual(
            imports,
            {
                "__future__",
                "dataclasses",
                "re",
                "engineering_orchestration._operation_vocabulary",
            },
        )

    def test_static_ast_contains_no_target_access_or_effectful_calls(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        forbidden_names = {
            "open",
            "exec",
            "eval",
            "compile",
            "__import__",
        }
        forbidden_attributes = {
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "open",
            "stat",
            "lstat",
            "exists",
            "is_file",
            "is_dir",
            "resolve",
            "absolute",
            "iterdir",
            "glob",
            "rglob",
            "listdir",
            "scandir",
            "walk",
            "access",
            "run",
            "Popen",
            "urlopen",
            "create_connection",
            "getaddrinfo",
            "file_digest",
            "connect",
        }
        calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
        self.assertFalse(
            any(
                isinstance(call, ast.Name) and call.id in forbidden_names
                for call in calls
            )
        )
        self.assertFalse(
            any(
                isinstance(call, ast.Attribute)
                and call.attr in forbidden_attributes
                for call in calls
            )
        )

    def test_validation_performs_no_io_network_process_clock_or_persistence(
        self,
    ) -> None:
        blocked = AssertionError("Operation Requirement validation must be pure")
        guards = (
            patch.object(builtins, "open", side_effect=blocked),
            patch.object(io, "open", side_effect=blocked),
            patch.object(Path, "open", side_effect=blocked),
            patch.object(Path, "read_text", side_effect=blocked),
            patch.object(Path, "read_bytes", side_effect=blocked),
            patch.object(Path, "write_text", side_effect=blocked),
            patch.object(Path, "write_bytes", side_effect=blocked),
            patch.object(Path, "stat", side_effect=blocked),
            patch.object(Path, "lstat", side_effect=blocked),
            patch.object(Path, "exists", side_effect=blocked),
            patch.object(Path, "is_file", side_effect=blocked),
            patch.object(Path, "is_dir", side_effect=blocked),
            patch.object(Path, "resolve", side_effect=blocked),
            patch.object(Path, "iterdir", side_effect=blocked),
            patch.object(Path, "glob", side_effect=blocked),
            patch.object(Path, "rglob", side_effect=blocked),
            patch.object(os, "stat", side_effect=blocked),
            patch.object(os, "lstat", side_effect=blocked),
            patch.object(os, "access", side_effect=blocked),
            patch.object(os, "listdir", side_effect=blocked),
            patch.object(os, "scandir", side_effect=blocked),
            patch.object(os, "walk", side_effect=blocked),
            patch.object(os, "getenv", side_effect=blocked),
            patch.object(glob, "glob", side_effect=blocked),
            patch.object(glob, "iglob", side_effect=blocked),
            patch.object(subprocess, "run", side_effect=blocked),
            patch.object(subprocess, "Popen", side_effect=blocked),
            patch.object(asyncio, "create_subprocess_exec", side_effect=blocked),
            patch.object(asyncio, "create_subprocess_shell", side_effect=blocked),
            patch.object(socket, "create_connection", side_effect=blocked),
            patch.object(socket, "getaddrinfo", side_effect=blocked),
            patch.object(socket.socket, "connect", side_effect=blocked),
            patch.object(urllib.request, "urlopen", side_effect=blocked),
            patch.object(http.client.HTTPConnection, "request", side_effect=blocked),
            patch.object(time, "time", side_effect=blocked),
            patch.object(time, "monotonic", side_effect=blocked),
            patch.object(sqlite3, "connect", side_effect=blocked),
            patch.object(hashlib, "file_digest", side_effect=blocked),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            valid = validate_operation_requirement(requirement())
            unsupported = validate_operation_requirement(
                requirement(operation_id="repository_file_write")
            )
            invalid_resource = validate_operation_requirement(
                requirement(resource="synthetic/../input.txt")
            )
            invalid_type = validate_operation_requirement(None)
        self.assertTrue(valid.valid)
        self.assertEqual(
            [finding.code for finding in unsupported.findings],
            ["operation_id_not_supported"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_resource.findings],
            ["resource_parent_segment"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_type.findings],
            ["operation_requirement_invalid_type"],
        )


class OperationRequirementBoundaryTests(unittest.TestCase):
    def test_adjacent_structural_contracts_remain_unchanged(self) -> None:
        task_schema = load_validator("task.schema.json").schema
        assignment_schema = load_validator("assignment.schema.json").schema
        runtime_schema = load_validator("agent-runtime-option.schema.json").schema
        self.assertNotIn("operation_requirement", task_schema["properties"])
        self.assertNotIn("operation_requirements", task_schema["properties"])
        self.assertNotIn("resource", task_schema["properties"])
        self.assertEqual(
            set(assignment_schema["properties"]),
            {"task_id", "workflow_id", "stage_id", "role_id", "actor_id"},
        )
        self.assertEqual(
            set(runtime_schema["properties"]),
            {"runtime_option_id"},
        )
        self.assertEqual(
            [
                field.name
                for field in fields(AgentExecutionCandidatePrerequisiteResult)
            ],
            [
                "valid",
                "findings",
                "responsibility_key",
                "actor_id",
                "runtime_option_id",
                "option_id",
                "outcome",
                "reasons",
            ],
        )

    def test_public_value_contains_no_adjacent_domain_state(self) -> None:
        public_fields = {
            field.name for field in fields(OperationRequirement)
        } | {
            field.name for field in fields(OperationRequirementValidationResult)
        }
        forbidden = {
            "requirement_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "actor_id",
            "runtime_option_id",
            "option_id",
            "environment_id",
            "state",
            "source",
            "reason",
            "timestamp",
            "expires_at",
            "tool",
            "capability",
            "permission",
            "authorization",
            "metadata",
            "extensions",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_package_root_does_not_reexport_operation_requirement_api(self) -> None:
        for name in (
            "OperationRequirement",
            "OperationRequirementFinding",
            "OperationRequirementValidationResult",
            "validate_operation_requirement",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(engineering_orchestration, name))

    def test_no_capability_permission_authorization_or_execution_api_exists(
        self,
    ) -> None:
        forbidden = {
            "RuntimeCapability",
            "EnvironmentPermission",
            "ExecutionAuthorization",
            "ExecutionContract",
            "ExecutionRequest",
            "authorize",
            "permit",
            "dispatch",
            "invoke",
            "execute",
            "resolve_resource",
            "normalize_resource",
            "register_operation",
        }
        self.assertTrue(
            all(not hasattr(operation_requirement, name) for name in forbidden)
        )

    def test_no_project_requirement_storage_was_created(self) -> None:
        for relative in (
            ".ai/operation-requirements",
            ".ai/requirements",
            ".ai/operation-registry",
            ".ai/execution-contracts",
        ):
            self.assertFalse((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
