"""Focused value, schema, no-widening, and purity tests for AIO-045."""

from __future__ import annotations

import ast
import builtins
import copy
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, asdict, fields, replace
import json
import os
from pathlib import Path
import random
import secrets
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request
import uuid

import engineering_orchestration
import engineering_orchestration.agent_operation_tool_binding as subject
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    AgentOperationToolBindingFinding,
    AgentOperationToolBindingValidationResult,
    validate_agent_operation_tool_binding,
)
import engineering_orchestration.schema_resources as schema_resources
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT / "engineering_orchestration" / "agent_operation_tool_binding.py"
)
BINDING_SCHEMA_NAME = "agent-operation-tool-binding.schema.json"
RUN_SCHEMA_NAME = "agent-execution-run.schema.json"
CONTRACT_SCHEMA_NAME = "agent-execution-contract.schema.json"
BINDING_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-operation-tool-binding.schema.json"
)
RUN_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-run.schema.json"
)
CONTRACT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-contract.schema.json"
)
RUN_ID = "run::synthetic-001"
TOOL_ID = "tool::synthetic-repository-reader::v1"


def contract(
    *,
    task_id: object = "synthetic-task",
    workflow_id: object = "architecture-change",
    stage_id: object = "implement",
    role_id: object = "software-engineer",
    actor_id: object = "actor::synthetic",
    runtime_option_id: object = "runtime::synthetic",
    option_id: object = "option::synthetic",
    environment_id: object = "environment::synthetic",
    operation_id: object = "repository_file_read",
    resource: object = "synthetic/input.txt",
    execution_mode: object = "deep",
) -> AgentExecutionContract:
    """Build one synthetic Contract without claiming provenance."""

    return AgentExecutionContract(
        task_id,  # type: ignore[arg-type]
        workflow_id,  # type: ignore[arg-type]
        stage_id,  # type: ignore[arg-type]
        role_id,  # type: ignore[arg-type]
        actor_id,  # type: ignore[arg-type]
        runtime_option_id,  # type: ignore[arg-type]
        option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        resource,  # type: ignore[arg-type]
        execution_mode,  # type: ignore[arg-type]
    )


def run(
    run_id: object = RUN_ID,
    *,
    bound_contract: object | None = None,
) -> AgentExecutionRun:
    """Build one synthetic Run without implying dispatch or invocation."""

    return AgentExecutionRun(
        run_id,  # type: ignore[arg-type]
        contract() if bound_contract is None else bound_contract,  # type: ignore[arg-type]
    )


def binding(
    *,
    bound_run: object | None = None,
    tool_id: object = TOOL_ID,
) -> AgentOperationToolBinding:
    """Build one synthetic binding without implying real Tool resolution."""

    return AgentOperationToolBinding(
        run() if bound_run is None else bound_run,  # type: ignore[arg-type]
        tool_id,  # type: ignore[arg-type]
    )


def restore_binding(payload: str) -> AgentOperationToolBinding:
    """Restore the exact Contract -> Run -> Tool Binding hierarchy."""

    document = json.loads(payload)
    run_document = document["run"]
    restored_run = AgentExecutionRun(
        run_id=run_document["run_id"],
        contract=AgentExecutionContract(**run_document["contract"]),
    )
    return AgentOperationToolBinding(
        run=restored_run,
        tool_id=document["tool_id"],
    )


class _TextResource:
    """Small Traversable-like test double for schema mismatch checks."""

    def __init__(self, document: dict[str, object]) -> None:
        self._text = json.dumps(document)

    def read_text(self, encoding: str = "utf-8") -> str:
        del encoding
        return self._text


class AgentOperationToolBindingFixture(unittest.TestCase):
    def assert_atomic_invalid(
        self,
        result: AgentOperationToolBindingValidationResult,
        codes: list[str],
        messages: list[str] | None = None,
    ) -> None:
        self.assertIs(type(result), AgentOperationToolBindingValidationResult)
        self.assertFalse(result.valid)
        self.assertIs(type(result.findings), tuple)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.binding)
        if messages is not None:
            self.assertEqual(
                [finding.message for finding in result.findings],
                messages,
            )

    def assert_no_operational_claims(
        self,
        value: AgentOperationToolBinding,
    ) -> None:
        self.assertEqual(
            [field.name for field in fields(value)],
            ["run", "tool_id"],
        )
        self.assertTrue(
            {
                "binding_id",
                "grant",
                "permission",
                "authorization",
                "authenticated",
                "current",
                "revoked",
                "consumed",
                "admitted",
                "dispatched",
                "invoked",
                "available",
                "executable",
                "trusted",
                "status",
                "result",
            }.isdisjoint(vars(value))
        )


class AgentOperationToolBindingValueTests(AgentOperationToolBindingFixture):
    def test_public_values_are_frozen_tuple_backed_and_exactly_shaped(self) -> None:
        self.assertEqual(
            [field.name for field in fields(AgentOperationToolBinding)],
            ["run", "tool_id"],
        )
        self.assertEqual(
            [field.name for field in fields(AgentOperationToolBindingFinding)],
            ["code", "message"],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(AgentOperationToolBindingValidationResult)
            ],
            ["valid", "findings", "binding"],
        )
        values = (
            binding(),
            AgentOperationToolBindingFinding("code", "message"),
            AgentOperationToolBindingValidationResult(True, (), binding()),
        )
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    value.synthetic = "changed"  # type: ignore[misc]
        self.assertIs(type(values[2].findings), tuple)

    def test_direct_module_api_and_no_package_root_export(self) -> None:
        expected = (
            "AgentOperationToolBinding",
            "AgentOperationToolBindingFinding",
            "AgentOperationToolBindingValidationResult",
            "validate_agent_operation_tool_binding",
        )
        self.assertEqual(subject.__all__, expected)
        for name in expected:
            self.assertIn(name, vars(subject))
            self.assertFalse(hasattr(engineering_orchestration, name))
        self.assertFalse(
            hasattr(subject, "prepare_agent_operation_tool_binding")
        )
        self.assertFalse(
            hasattr(subject, "validate_agent_operation_tool_binding_collection")
        )

    def test_exact_binding_type_is_required_and_subclasses_are_rejected(
        self,
    ) -> None:
        expected = AgentOperationToolBindingValidationResult(
            False,
            (
                AgentOperationToolBindingFinding(
                    "agent_operation_tool_binding_invalid_type",
                    "Agent Operation Tool Binding must be an exact "
                    "AgentOperationToolBinding value.",
                ),
            ),
            None,
        )
        self.assertEqual(validate_agent_operation_tool_binding(object()), expected)
        self.assertEqual(validate_agent_operation_tool_binding(None), expected)

        class DerivedBinding(AgentOperationToolBinding):
            pass

        supplied = binding()
        derived = DerivedBinding(supplied.run, supplied.tool_id)
        self.assertEqual(validate_agent_operation_tool_binding(derived), expected)

    def test_valid_binding_preserves_exact_binding_run_and_contract_objects(
        self,
    ) -> None:
        bound_contract = contract(execution_mode="critical")
        bound_run = run("run::preserved", bound_contract=bound_contract)
        supplied = binding(bound_run=bound_run, tool_id="tool::reader::v7")
        result = validate_agent_operation_tool_binding(supplied)
        self.assertEqual(
            result,
            AgentOperationToolBindingValidationResult(True, (), supplied),
        )
        self.assertIs(result.binding, supplied)
        self.assertIs(result.binding.run, bound_run)
        self.assertIs(result.binding.run.contract, bound_contract)

    def test_tool_id_invalid_values_have_exact_code_and_message(self) -> None:
        class DerivedToolId(str):
            pass

        message = (
            "Agent Operation Tool Binding tool_id must be an exact nonempty "
            "string."
        )
        for value in (
            "",
            None,
            False,
            0,
            object(),
            DerivedToolId("tool::reader::v1"),
        ):
            with self.subTest(value=value):
                self.assert_atomic_invalid(
                    validate_agent_operation_tool_binding(binding(tool_id=value)),
                    ["agent_operation_tool_binding_tool_id_invalid"],
                    [message],
                )

    def test_tool_id_is_opaque_case_sensitive_and_never_normalized(self) -> None:
        values = (
            "tool::synthetic-repository-reader::v1",
            "TOOL::synthetic-repository-reader::v1",
            "tool::synthetic-repository-reader::V1",
            "  tool::reader::v1  ",
            " ",
            "repository-reader",
        )
        results = tuple(
            validate_agent_operation_tool_binding(binding(tool_id=value))
            for value in values
        )
        self.assertTrue(all(result.valid for result in results))
        self.assertEqual(
            [result.binding.tool_id for result in results],  # type: ignore[union-attr]
            list(values),
        )
        self.assertEqual(
            len({result.binding for result in results}),
            len(values),
        )

    def test_nested_run_findings_are_preserved_before_tool_id_finding(
        self,
    ) -> None:
        supplied = binding(
            bound_run=run(
                "",
                bound_contract=contract(
                    task_id="",
                    actor_id=object(),
                    operation_id="Malformed-Operation",
                    resource="synthetic/../input.txt",
                    execution_mode="turbo",
                ),
            ),
            tool_id="",
        )
        result = validate_agent_operation_tool_binding(supplied)
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_run_run_id_invalid",
                "agent_execution_contract_task_id_invalid",
                "agent_execution_contract_actor_id_invalid",
                "operation_id_invalid_syntax",
                "resource_parent_segment",
                "agent_execution_contract_execution_mode_not_supported",
                "agent_operation_tool_binding_tool_id_invalid",
            ],
        )
        nested = subject.validate_agent_execution_run(supplied.run)
        self.assertEqual(
            [(item.code, item.message) for item in result.findings[:-1]],
            [(item.code, item.message) for item in nested.findings],
        )

    def test_wrong_nested_run_type_preserves_parent_finding_exactly(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_operation_tool_binding(binding(bound_run=object())),
            ["agent_execution_run_invalid_type"],
            ["Agent Execution Run must be an exact AgentExecutionRun value."],
        )

    def test_full_value_equality_uses_run_and_tool_id_without_binding_id(
        self,
    ) -> None:
        first = binding()
        duplicate = binding()
        another_tool = binding(tool_id="tool::reader::v2")
        another_run = binding(bound_run=run("run::synthetic-002"))
        self.assertEqual(first, duplicate)
        self.assertNotEqual(first, another_tool)
        self.assertNotEqual(first, another_run)
        self.assertNotIn("binding_id", vars(first))
        self.assertTrue(validate_agent_operation_tool_binding(first).valid)
        self.assertTrue(validate_agent_operation_tool_binding(another_tool).valid)

    def test_all_run_and_contract_mutations_change_the_bound_value(self) -> None:
        original = binding()
        contract_mutations = {
            "task_id": "synthetic-task-other",
            "workflow_id": "code-change",
            "stage_id": "review",
            "role_id": "architect",
            "actor_id": "actor::other",
            "runtime_option_id": "runtime::other",
            "option_id": "option::other",
            "environment_id": "environment::other",
            "operation_id": "repository_file_write",
            "resource": "synthetic/other.txt",
            "execution_mode": "critical",
        }
        for field_name, changed_value in contract_mutations.items():
            with self.subTest(field=field_name):
                changed_contract = replace(
                    original.run.contract,
                    **{field_name: changed_value},
                )
                changed = replace(
                    original,
                    run=replace(original.run, contract=changed_contract),
                )
                self.assertNotEqual(changed, original)
                self.assertEqual(changed.run.contract, changed_contract)
                result = validate_agent_operation_tool_binding(changed)
                if field_name == "operation_id":
                    self.assert_atomic_invalid(
                        result,
                        ["operation_id_not_supported"],
                    )
                else:
                    self.assertTrue(result.valid)
                    self.assertIs(result.binding, changed)

        changed_run_id = replace(
            original,
            run=replace(original.run, run_id="run::synthetic-002"),
        )
        self.assertNotEqual(changed_run_id, original)
        self.assertTrue(
            validate_agent_operation_tool_binding(changed_run_id).valid
        )
        self.assertEqual(original, binding())

    def test_json_round_trip_preserves_value_without_operational_trust(self) -> None:
        original = binding(
            bound_run=run(
                "run::serialized",
                bound_contract=contract(execution_mode="critical"),
            ),
            tool_id="tool::reader::immutable-revision-7",
        )
        payload = json.dumps(asdict(original), sort_keys=True)
        restored = restore_binding(payload)
        result = validate_agent_operation_tool_binding(restored)
        self.assertTrue(result.valid)
        self.assertEqual(result.binding, original)
        self.assertIsNot(result.binding, original)
        self.assertIsNot(result.binding.run, original.run)
        self.assertIsNot(result.binding.run.contract, original.run.contract)
        self.assert_no_operational_claims(restored)

    def test_direct_construction_only_proves_intrinsic_value_semantics(self) -> None:
        directly_constructed = binding(tool_id="mutable-display-alias")
        result = validate_agent_operation_tool_binding(directly_constructed)
        self.assertTrue(result.valid)
        self.assertIs(result.binding, directly_constructed)
        self.assert_no_operational_claims(directly_constructed)

    def test_validation_is_deterministic_atomic_and_nonmutating(self) -> None:
        valid = binding()
        invalid = binding(
            bound_run=run(
                "",
                bound_contract=contract(resource="synthetic/../input.txt"),
            ),
            tool_id="",
        )
        valid_before = copy.deepcopy(valid)
        invalid_before = copy.deepcopy(invalid)
        first_valid = validate_agent_operation_tool_binding(valid)
        second_valid = validate_agent_operation_tool_binding(valid)
        first_invalid = validate_agent_operation_tool_binding(invalid)
        second_invalid = validate_agent_operation_tool_binding(invalid)
        self.assertEqual(first_valid, second_valid)
        self.assertEqual(first_invalid, second_invalid)
        self.assertEqual(valid, valid_before)
        self.assertEqual(invalid, invalid_before)
        self.assertIs(first_valid.binding, valid)
        self.assertIsNone(first_invalid.binding)


class AgentOperationToolBindingNoWideningTests(
    AgentOperationToolBindingFixture
):
    def test_scope_can_change_only_by_binding_a_distinct_complete_run(self) -> None:
        original = binding()
        substitutions = {
            "runtime_option_id": "runtime::other",
            "option_id": "option::other",
            "environment_id": "environment::other",
            "operation_id": "repository_file_write",
            "resource": "synthetic/other.txt",
            "execution_mode": "critical",
            "actor_id": "actor::other",
            "role_id": "architect",
        }
        for field_name, changed_value in substitutions.items():
            with self.subTest(field=field_name):
                changed_contract = replace(
                    original.run.contract,
                    **{field_name: changed_value},
                )
                changed_binding = AgentOperationToolBinding(
                    replace(original.run, contract=changed_contract),
                    original.tool_id,
                )
                self.assertNotEqual(changed_binding.run, original.run)
                self.assertNotEqual(changed_binding, original)
                self.assertEqual(original, binding())

    def test_binding_has_no_parallel_scope_or_native_execution_fields(self) -> None:
        excluded = {
            "run_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "actor_id",
            "runtime_option_id",
            "option_id",
            "environment_id",
            "operation_id",
            "resource",
            "execution_mode",
            "adapter_id",
            "provider_id",
            "model_id",
            "endpoint",
            "command",
            "payload",
            "arguments",
            "credentials",
        }
        self.assertTrue(excluded.isdisjoint(vars(binding())))

    def test_capability_or_grant_is_not_accepted_in_place_of_binding(self) -> None:
        for supplied in (
            {"state": "present"},
            {"grant_id": "grant::synthetic"},
            run(),
        ):
            with self.subTest(supplied=supplied):
                self.assert_atomic_invalid(
                    validate_agent_operation_tool_binding(supplied),
                    ["agent_operation_tool_binding_invalid_type"],
                )


class AgentOperationToolBindingSchemaTests(AgentOperationToolBindingFixture):
    def test_schema_is_closed_ordered_two_field_shape_with_run_reference(
        self,
    ) -> None:
        schema = load_validator(BINDING_SCHEMA_NAME).schema
        self.assertEqual(
            schema["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(schema["$id"], BINDING_SCHEMA_ID)
        self.assertEqual(schema["type"], "object")
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["run", "tool_id"])
        self.assertEqual(list(schema["properties"]), ["run", "tool_id"])
        self.assertEqual(schema["properties"]["run"]["$ref"], RUN_SCHEMA_ID)
        self.assertNotIn("properties", schema["properties"]["run"])
        self.assertEqual(
            {
                key: schema["properties"]["tool_id"][key]
                for key in ("type", "minLength")
            },
            {"type": "string", "minLength": 1},
        )

    def test_schema_validates_nested_run_and_rejects_wrong_shapes(self) -> None:
        validator = load_validator(BINDING_SCHEMA_NAME)
        valid = asdict(binding())
        self.assertEqual(list(validator.iter_errors(valid)), [])
        cases = (
            {},
            {"run": valid["run"]},
            {"tool_id": TOOL_ID},
            {"run": "not-an-object", "tool_id": TOOL_ID},
            {"run": valid["run"], "tool_id": ""},
            {"run": valid["run"], "tool_id": 7},
            valid | {"run": valid["run"] | {"run_id": ""}},
            valid
            | {
                "run": valid["run"]
                | {
                    "contract": valid["run"]["contract"]
                    | {"execution_mode": "turbo"}
                }
            },
        )
        for document in cases:
            with self.subTest(document=document):
                self.assertTrue(list(validator.iter_errors(document)))

    def test_schema_semantic_boundary_defers_supported_operation_and_resource(
        self,
    ) -> None:
        validator = load_validator(BINDING_SCHEMA_NAME)
        for field_name, changed_value, expected_code in (
            (
                "operation_id",
                "repository_file_write",
                "operation_id_not_supported",
            ),
            (
                "resource",
                "synthetic/../input.txt",
                "resource_parent_segment",
            ),
        ):
            with self.subTest(field=field_name):
                changed_contract = replace(
                    contract(),
                    **{field_name: changed_value},
                )
                supplied = binding(bound_run=run(bound_contract=changed_contract))
                document = asdict(supplied)
                self.assertEqual(list(validator.iter_errors(document)), [])
                self.assert_atomic_invalid(
                    validate_agent_operation_tool_binding(supplied),
                    [expected_code],
                )

    def test_schema_rejects_all_locked_extra_fields(self) -> None:
        validator = load_validator(BINDING_SCHEMA_NAME)
        base = asdict(binding())
        excluded = (
            "binding_id",
            "run_id",
            "task_id",
            "runtime_option_id",
            "option_id",
            "environment_id",
            "operation_id",
            "resource",
            "execution_mode",
            "adapter_id",
            "provider_id",
            "model_id",
            "endpoint",
            "command",
            "payload",
            "arguments",
            "credentials",
            "status",
            "grant",
            "authorization",
            "consumed",
            "admitted",
            "result",
        )
        for field_name in excluded:
            with self.subTest(field=field_name):
                errors = list(
                    validator.iter_errors(
                        base | {field_name: "synthetic-value"}
                    )
                )
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].validator, "additionalProperties")

    def test_schema_resolves_binding_run_and_contract_offline_without_cwd(
        self,
    ) -> None:
        blocked = AssertionError("schema resolution attempted external access")
        with patch("pathlib.Path.cwd", side_effect=blocked), patch(
            "socket.create_connection", side_effect=blocked
        ), patch("socket.getaddrinfo", side_effect=blocked), patch(
            "urllib.request.urlopen", side_effect=blocked
        ):
            validator = load_validator(BINDING_SCHEMA_NAME)
            validator.validate(asdict(binding()))
            invalid = asdict(binding())
            invalid["run"]["contract"]["actor_id"] = ""
            errors = list(validator.iter_errors(invalid))
        self.assertEqual(
            [(error.validator, tuple(error.absolute_path)) for error in errors],
            [("minLength", ("run", "contract", "actor_id"))],
        )

    def test_schema_round_trip_preserves_exact_equality_only(self) -> None:
        original = binding(tool_id="tool::reader::immutable-v9")
        payload = json.dumps(asdict(original))
        validator = load_validator(BINDING_SCHEMA_NAME)
        validator.validate(json.loads(payload))
        restored = restore_binding(payload)
        result = validate_agent_operation_tool_binding(restored)
        self.assertTrue(result.valid)
        self.assertEqual(restored, original)
        self.assert_no_operational_claims(restored)

    def test_unknown_schema_reference_fails_closed_without_network(self) -> None:
        blocked = AssertionError("schema resolution attempted network access")
        with patch("socket.create_connection", side_effect=blocked), patch(
            "socket.getaddrinfo", side_effect=blocked
        ), patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(BINDING_SCHEMA_NAME)
            unknown = validator.evolve(
                schema={
                    "$ref": "https://example.invalid/unregistered.schema.json"
                }
            )
            with self.assertRaises(Exception) as caught:
                unknown.validate({})
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("unregistered.schema.json", str(caught.exception))

    def test_missing_schema_resources_fail_closed(self) -> None:
        original = schema_resources.schema_resource
        for missing_name in (
            BINDING_SCHEMA_NAME,
            RUN_SCHEMA_NAME,
            CONTRACT_SCHEMA_NAME,
        ):
            with self.subTest(missing=missing_name), patch.object(
                schema_resources,
                "schema_resource",
                side_effect=lambda name, missing=missing_name: (
                    None if name == missing else original(name)
                ),
            ):
                with self.assertRaises(FileNotFoundError):
                    load_validator(BINDING_SCHEMA_NAME)

    def test_mismatched_nested_schema_ids_fail_closed(self) -> None:
        original = schema_resources.schema_resource
        for mismatched_name in (RUN_SCHEMA_NAME, CONTRACT_SCHEMA_NAME):
            with self.subTest(mismatched=mismatched_name):
                real = original(mismatched_name)
                self.assertIsNotNone(real)
                document = json.loads(real.read_text(encoding="utf-8"))
                document["$id"] = "https://example.invalid/rebound.schema.json"
                mismatched = _TextResource(document)

                def resource(name: str):
                    if name == mismatched_name:
                        return mismatched
                    return original(name)

                with patch.object(
                    schema_resources,
                    "schema_resource",
                    side_effect=resource,
                ):
                    with self.assertRaises(ValueError):
                        load_validator(BINDING_SCHEMA_NAME)


class AgentOperationToolBindingSafetyTests(AgentOperationToolBindingFixture):
    def test_static_module_has_no_io_discovery_state_or_execution_calls(
        self,
    ) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "glob",
                    "http",
                    "os",
                    "pathlib",
                    "random",
                    "secrets",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "time",
                    "urllib",
                    "uuid",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "write_text",
                    "write_bytes",
                    "resolve",
                    "stat",
                    "listdir",
                    "scandir",
                    "getenv",
                    "system",
                    "Popen",
                    "now",
                    "today",
                    "utcnow",
                    "time",
                    "monotonic",
                    "perf_counter",
                    "uuid4",
                    "token_hex",
                    "token_urlsafe",
                    "connect",
                    "urlopen",
                    "discover",
                    "probe",
                    "rank",
                    "fallback",
                    "persist",
                    "consume",
                    "revoke",
                    "admit",
                    "dispatch",
                    "execute",
                    "invoke",
                }
            )
        )

    def test_dynamic_guards_cover_valid_and_atomic_invalid_paths(self) -> None:
        valid = binding()
        invalid = binding(bound_run=run(""), tool_id="")
        guards = (
            patch.object(builtins, "open", side_effect=AssertionError("external work")),
            patch.object(Path, "open", side_effect=AssertionError("external work")),
            patch.object(Path, "read_text", side_effect=AssertionError("external work")),
            patch.object(Path, "read_bytes", side_effect=AssertionError("external work")),
            patch.object(Path, "write_text", side_effect=AssertionError("external work")),
            patch.object(Path, "write_bytes", side_effect=AssertionError("external work")),
            patch.object(Path, "stat", side_effect=AssertionError("external work")),
            patch.object(Path, "resolve", side_effect=AssertionError("external work")),
            patch.object(Path, "iterdir", side_effect=AssertionError("external work")),
            patch.object(os, "stat", side_effect=AssertionError("external work")),
            patch.object(os, "access", side_effect=AssertionError("external work")),
            patch.object(os, "listdir", side_effect=AssertionError("external work")),
            patch.object(os, "scandir", side_effect=AssertionError("external work")),
            patch.object(os, "getenv", side_effect=AssertionError("external work")),
            patch.object(socket, "socket", side_effect=AssertionError("external work")),
            patch.object(socket, "create_connection", side_effect=AssertionError("external work")),
            patch.object(sqlite3, "connect", side_effect=AssertionError("external work")),
            patch.object(subprocess, "run", side_effect=AssertionError("external work")),
            patch.object(subprocess, "Popen", side_effect=AssertionError("external work")),
            patch.object(urllib.request, "urlopen", side_effect=AssertionError("external work")),
            patch.object(
                urllib.request,
                "urlretrieve",
                side_effect=AssertionError("external work"),
            ),
            patch.object(time, "time", side_effect=AssertionError("external work")),
            patch.object(time, "monotonic", side_effect=AssertionError("external work")),
            patch.object(time, "perf_counter", side_effect=AssertionError("external work")),
            patch.object(random, "random", side_effect=AssertionError("external work")),
            patch.object(random, "getrandbits", side_effect=AssertionError("external work")),
            patch.object(random, "randint", side_effect=AssertionError("external work")),
            patch.object(secrets, "token_hex", side_effect=AssertionError("external work")),
            patch.object(secrets, "token_urlsafe", side_effect=AssertionError("external work")),
            patch.object(uuid, "uuid4", side_effect=AssertionError("external work")),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            for name in (
                "discover_tools",
                "probe_runtime",
                "rank_tools",
                "select_fallback",
                "persist_binding",
                "consume_grant",
                "admit_dispatch",
                "dispatch",
                "invoke",
                "provider_call",
            ):
                stack.enter_context(
                    patch.object(
                        subject,
                        name,
                        create=True,
                        side_effect=AssertionError("operational call"),
                    )
                )
            valid_result = validate_agent_operation_tool_binding(valid)
            invalid_result = validate_agent_operation_tool_binding(invalid)
        self.assertTrue(valid_result.valid)
        self.assertFalse(invalid_result.valid)
        self.assertIsNone(invalid_result.binding)

    def test_module_exposes_no_discovery_selection_or_execution_api(self) -> None:
        prohibited = (
            "inventory",
            "discover",
            "probe",
            "rank",
            "fallback",
            "reselect",
            "authenticate",
            "consume",
            "revoke",
            "persist",
            "store",
            "admit",
            "dispatch",
            "invoke",
            "execute",
        )
        public_names = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        for name in public_names:
            with self.subTest(name=name):
                self.assertFalse(any(fragment in name for fragment in prohibited))

    def test_repeated_validation_has_no_consumption_or_hidden_state(self) -> None:
        value = binding()
        first = validate_agent_operation_tool_binding(value)
        second = validate_agent_operation_tool_binding(value)
        self.assertEqual(first, second)
        self.assertIs(first.binding, value)
        self.assertIs(second.binding, value)
        self.assert_no_operational_claims(value)


if __name__ == "__main__":
    unittest.main()
