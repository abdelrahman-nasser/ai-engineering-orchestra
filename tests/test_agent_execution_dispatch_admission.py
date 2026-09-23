"""Focused value, schema, provenance-boundary, and purity tests for AIO-047."""

from __future__ import annotations

import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, asdict, fields, replace
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
import urllib.request

import engineering_orchestration
import engineering_orchestration.agent_execution_dispatch_admission as subject
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
    AgentExecutionDispatchAdmissionFinding,
    AgentExecutionDispatchAdmissionValidationResult,
    validate_agent_execution_dispatch_admission,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
import engineering_orchestration.schema_resources as schema_resources


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "engineering_orchestration"
    / "agent_execution_dispatch_admission.py"
)
ADMISSION_SCHEMA_NAME = "agent-execution-dispatch-admission.schema.json"
GRANT_SCHEMA_NAME = "agent-execution-authorization-grant.schema.json"
BINDING_SCHEMA_NAME = "agent-operation-tool-binding.schema.json"
RUN_SCHEMA_NAME = "agent-execution-run.schema.json"
CONTRACT_SCHEMA_NAME = "agent-execution-contract.schema.json"
ADMISSION_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-dispatch-admission.schema.json"
)
GRANT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-authorization-grant.schema.json"
)
BINDING_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-operation-tool-binding.schema.json"
)
DECISION_PATTERN = (
    r"^(?!0000)[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):"
    r"[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z(?![\s\S])"
)


def contract(
    *,
    task_id: object = "synthetic-task",
    resource: object = "synthetic/input.txt",
) -> AgentExecutionContract:
    return AgentExecutionContract(
        task_id,  # type: ignore[arg-type]
        "architecture-change",
        "implement",
        "software-engineer",
        "actor::synthetic",
        "runtime::synthetic",
        "option::synthetic",
        "environment::synthetic",
        "repository_file_read",
        resource,  # type: ignore[arg-type]
        "critical",
    )


def run(
    run_id: object = "run::synthetic-001",
    *,
    bound_contract: object | None = None,
) -> AgentExecutionRun:
    return AgentExecutionRun(
        run_id,  # type: ignore[arg-type]
        contract() if bound_contract is None else bound_contract,  # type: ignore[arg-type]
    )


def grant(
    *,
    bound_run: object | None = None,
    grant_id: object = "grant::synthetic-001",
    issued_at: object = "2026-09-23T10:00:00Z",
    expires_at: object = "2026-09-23T11:00:00Z",
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id,  # type: ignore[arg-type]
        run() if bound_run is None else bound_run,  # type: ignore[arg-type]
        "domain::synthetic",
        "policy",
        "issuer::synthetic",
        "provenance::synthetic",
        issued_at,  # type: ignore[arg-type]
        expires_at,  # type: ignore[arg-type]
    )


def binding(
    *,
    bound_run: object | None = None,
    tool_id: object = "tool::synthetic::v1",
) -> AgentOperationToolBinding:
    return AgentOperationToolBinding(
        run() if bound_run is None else bound_run,  # type: ignore[arg-type]
        tool_id,  # type: ignore[arg-type]
    )


def admission(
    *,
    supplied_grant: object | None = None,
    supplied_binding: object | None = None,
    decision_time: object = "2026-09-23T10:30:00.000000Z",
) -> AgentExecutionDispatchAdmission:
    exact_run = run()
    return AgentExecutionDispatchAdmission(
        grant(bound_run=exact_run)
        if supplied_grant is None
        else supplied_grant,  # type: ignore[arg-type]
        binding(bound_run=exact_run)
        if supplied_binding is None
        else supplied_binding,  # type: ignore[arg-type]
        decision_time,  # type: ignore[arg-type]
    )


class _TextResource:
    def __init__(self, document: dict[str, object]) -> None:
        self._text = json.dumps(document)

    def read_text(self, encoding: str = "utf-8") -> str:
        del encoding
        return self._text


class AgentExecutionDispatchAdmissionTests(unittest.TestCase):
    def assert_atomic_invalid(
        self,
        result: AgentExecutionDispatchAdmissionValidationResult,
        codes: list[str],
    ) -> None:
        self.assertIs(type(result), AgentExecutionDispatchAdmissionValidationResult)
        self.assertFalse(result.valid)
        self.assertIs(type(result.findings), tuple)
        self.assertEqual([item.code for item in result.findings], codes)
        self.assertTrue(all(type(item) is AgentExecutionDispatchAdmissionFinding for item in result.findings))
        self.assertIsNone(result.admission)

    def test_exact_frozen_three_field_value(self) -> None:
        value = admission()
        self.assertEqual(
            [item.name for item in fields(value)],
            ["grant", "tool_binding", "decision_time"],
        )
        prohibited = {
            "admission_id",
            "status",
            "state",
            "attempt",
            "request_id",
            "result",
            "error",
            "lease",
            "metadata",
            "dispatched",
            "invoked",
        }
        self.assertTrue(prohibited.isdisjoint(vars(value)))
        with self.assertRaises(FrozenInstanceError):
            value.decision_time = "2026-09-23T10:31:00.000000Z"  # type: ignore[misc]

    def test_valid_value_preserves_exact_object(self) -> None:
        value = admission()
        result = validate_agent_execution_dispatch_admission(value)
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertIs(result.admission, value)

    def test_wrong_top_level_type_fails_atomically(self) -> None:
        result = validate_agent_execution_dispatch_admission(object())  # type: ignore[arg-type]
        self.assert_atomic_invalid(
            result,
            ["agent_execution_dispatch_admission_invalid_type"],
        )

    def test_subclass_is_not_an_exact_value(self) -> None:
        class DerivedAdmission(AgentExecutionDispatchAdmission):
            pass

        base = admission()
        derived = DerivedAdmission(
            base.grant,
            base.tool_binding,
            base.decision_time,
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(derived),
            ["agent_execution_dispatch_admission_invalid_type"],
        )

    def test_nested_grant_finding_is_preserved(self) -> None:
        exact_run = run()
        bad_grant = grant(bound_run=exact_run, grant_id="")
        value = admission(
            supplied_grant=bad_grant,
            supplied_binding=binding(bound_run=exact_run),
        )
        result = validate_agent_execution_dispatch_admission(value)
        self.assert_atomic_invalid(
            result,
            ["agent_execution_authorization_grant_grant_id_invalid"],
        )
        self.assertIn("grant_id", result.findings[0].message)

    def test_nested_binding_finding_is_preserved(self) -> None:
        exact_run = run()
        value = admission(
            supplied_grant=grant(bound_run=exact_run),
            supplied_binding=binding(bound_run=exact_run, tool_id=""),
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(value),
            ["agent_operation_tool_binding_tool_id_invalid"],
        )

    def test_wrong_nested_types_fail_without_attribute_access(self) -> None:
        value = admission(
            supplied_grant=object(),
            supplied_binding=object(),
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(value),
            [
                "agent_execution_authorization_grant_invalid_type",
                "agent_operation_tool_binding_invalid_type",
            ],
        )

    def test_complete_run_id_mismatch_fails(self) -> None:
        grant_run = run()
        binding_run = run("run::synthetic-002")
        value = admission(
            supplied_grant=grant(bound_run=grant_run),
            supplied_binding=binding(bound_run=binding_run),
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(value),
            ["agent_execution_dispatch_admission_run_mismatch"],
        )

    def test_same_run_id_with_different_contract_fails(self) -> None:
        grant_run = run()
        binding_run = run(bound_contract=contract(resource="synthetic/other.txt"))
        value = admission(
            supplied_grant=grant(bound_run=grant_run),
            supplied_binding=binding(bound_run=binding_run),
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(value),
            ["agent_execution_dispatch_admission_run_mismatch"],
        )

    def test_decision_time_requires_fixed_six_digit_utc_form(self) -> None:
        invalid_values: tuple[object, ...] = (
            "2026-09-23T10:30:00Z",
            "2026-09-23T10:30:00.1Z",
            "2026-09-23T10:30:00.00000Z",
            "2026-09-23T10:30:00.0000000Z",
            "2026-09-23t10:30:00.000000Z",
            "2026-09-23T10:30:00.000000z",
            "2026-09-23T10:30:00.000000+00:00",
            "2026-09-23T10:30:60.000000Z",
            "0000-01-01T00:00:00.000000Z",
            "2026-09-23T10:30:00.000000Z\n",
            1,
        )
        for decision_time in invalid_values:
            with self.subTest(decision_time=decision_time):
                self.assert_atomic_invalid(
                    validate_agent_execution_dispatch_admission(
                        admission(decision_time=decision_time)
                    ),
                    [
                        "agent_execution_dispatch_admission_"
                        "decision_time_invalid"
                    ],
                )

    def test_decision_time_requires_real_calendar_date(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(
                admission(decision_time="2025-02-29T10:30:00.000000Z")
            ),
            ["agent_execution_dispatch_admission_decision_time_invalid"],
        )
        exact_run = run()
        leap_grant = grant(
            bound_run=exact_run,
            issued_at="2024-02-01T00:00:00Z",
            expires_at="2024-03-01T00:00:00Z",
        )
        self.assertTrue(
            validate_agent_execution_dispatch_admission(
                admission(
                    supplied_grant=leap_grant,
                    supplied_binding=binding(bound_run=exact_run),
                    decision_time="2024-02-29T10:30:00.000000Z",
                )
            ).valid
        )

    def test_issued_at_boundary_is_inclusive_using_parsed_instants(self) -> None:
        exact_run = run()
        exact_grant = grant(
            bound_run=exact_run,
            issued_at="2026-09-23T10:00:00.1Z",
        )
        value = admission(
            supplied_grant=exact_grant,
            supplied_binding=binding(bound_run=exact_run),
            decision_time="2026-09-23T10:00:00.100000Z",
        )
        self.assertTrue(validate_agent_execution_dispatch_admission(value).valid)

    def test_before_issuance_is_invalid(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(
                admission(decision_time="2026-09-23T09:59:59.999999Z")
            ),
            ["agent_execution_dispatch_admission_currentness_invalid"],
        )

    def test_expiry_boundary_is_exclusive(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(
                admission(decision_time="2026-09-23T11:00:00.000000Z")
            ),
            ["agent_execution_dispatch_admission_currentness_invalid"],
        )

    def test_last_microsecond_before_expiry_is_valid(self) -> None:
        self.assertTrue(
            validate_agent_execution_dispatch_admission(
                admission(decision_time="2026-09-23T10:59:59.999999Z")
            ).valid
        )

    def test_findings_have_stable_dependency_order(self) -> None:
        exact_run = run()
        value = admission(
            supplied_grant=grant(bound_run=exact_run, grant_id=""),
            supplied_binding=binding(bound_run=exact_run, tool_id=""),
            decision_time="invalid",
        )
        self.assert_atomic_invalid(
            validate_agent_execution_dispatch_admission(value),
            [
                "agent_execution_authorization_grant_grant_id_invalid",
                "agent_operation_tool_binding_tool_id_invalid",
                "agent_execution_dispatch_admission_decision_time_invalid",
            ],
        )

    def test_full_value_equality_and_json_round_trip(self) -> None:
        first = admission()
        same = admission()
        later = replace(first, decision_time="2026-09-23T10:30:00.000001Z")
        self.assertEqual(first, same)
        self.assertNotEqual(first, later)
        self.assertNotEqual(first, replace(first, grant=replace(first.grant, grant_id="grant::other")))
        self.assertNotEqual(first, replace(first, tool_binding=replace(first.tool_binding, tool_id="tool::other")))
        self.assertEqual(json.loads(json.dumps(asdict(first))), asdict(first))

    def test_direct_construction_carries_no_authority_assertion(self) -> None:
        value = admission()
        self.assertTrue(
            {
                "authenticated",
                "trusted",
                "authoritative",
                "revoked",
                "consumed",
                "committed",
                "dispatched",
                "invoked",
                "succeeded",
            }.isdisjoint(vars(value))
        )
        self.assertIn("Direct construction", subject.__doc__ or "")

    def test_module_is_pure_and_has_no_operational_dependencies(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        banned_modules = {
            "asyncio",
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
        imported = {
            node.names[0].name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
        }
        imported.update(
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        self.assertTrue(banned_modules.isdisjoint(imported))
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"open", "exec", "eval", "input"}.isdisjoint(calls))

    def test_public_names_are_direct_import_only(self) -> None:
        expected = {
            "AgentExecutionDispatchAdmission",
            "AgentExecutionDispatchAdmissionFinding",
            "AgentExecutionDispatchAdmissionValidationResult",
            "validate_agent_execution_dispatch_admission",
        }
        self.assertEqual(set(subject.__all__), expected)
        for name in expected:
            self.assertFalse(hasattr(engineering_orchestration, name))

    def test_schema_is_closed_exact_and_references_canonical_values(self) -> None:
        resource = schema_resources.schema_resource(ADMISSION_SCHEMA_NAME)
        self.assertIsNotNone(resource)
        assert resource is not None
        document = json.loads(resource.read_text(encoding="utf-8"))
        self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(document["$id"], ADMISSION_SCHEMA_ID)
        self.assertEqual(document["type"], "object")
        self.assertIs(document["additionalProperties"], False)
        self.assertEqual(document["required"], ["grant", "tool_binding", "decision_time"])
        self.assertEqual(list(document["properties"]), ["grant", "tool_binding", "decision_time"])
        self.assertEqual(document["properties"]["grant"]["$ref"], GRANT_SCHEMA_ID)
        self.assertEqual(document["properties"]["tool_binding"]["$ref"], BINDING_SCHEMA_ID)
        self.assertEqual(document["properties"]["decision_time"]["pattern"], DECISION_PATTERN)

    def test_schema_validates_nested_graph_offline_and_rejects_extras(self) -> None:
        blocked = AssertionError("network access attempted")
        guards = (
            patch.object(socket, "create_connection", side_effect=blocked),
            patch.object(socket, "getaddrinfo", side_effect=blocked),
            patch.object(urllib.request, "urlopen", side_effect=blocked),
            patch("pathlib.Path.cwd", side_effect=blocked),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            validator = schema_resources.load_validator(ADMISSION_SCHEMA_NAME)
            document = asdict(admission())
            self.assertEqual(list(validator.iter_errors(document)), [])
            document["admission_id"] = "admission::forbidden"
            errors = list(validator.iter_errors(document))
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].validator, "additionalProperties")

    def test_missing_nested_schema_resource_fails_closed(self) -> None:
        original = schema_resources.schema_resource

        def missing(name: str):
            if name == GRANT_SCHEMA_NAME:
                return None
            return original(name)

        with patch.object(schema_resources, "schema_resource", side_effect=missing):
            with self.assertRaises(FileNotFoundError):
                schema_resources.load_validator(ADMISSION_SCHEMA_NAME)

    def test_mismatched_nested_schema_id_fails_closed(self) -> None:
        original = schema_resources.schema_resource

        def mismatched(name: str):
            if name == GRANT_SCHEMA_NAME:
                return _TextResource(
                    {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "$id": "https://example.invalid/wrong.json",
                        "type": "object",
                    }
                )
            return original(name)

        with patch.object(schema_resources, "schema_resource", side_effect=mismatched):
            with self.assertRaises(ValueError):
                schema_resources.load_validator(ADMISSION_SCHEMA_NAME)

    def test_unknown_reference_fails_closed_without_network(self) -> None:
        validator = schema_resources.load_validator(ADMISSION_SCHEMA_NAME)
        unknown = validator.evolve(
            schema={"$ref": "https://example.invalid/unknown.schema.json"}
        )
        with patch.object(socket, "create_connection", side_effect=AssertionError("network")), patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")):
            with self.assertRaises(Exception):
                unknown.validate({})

    def test_schema_rejects_missing_fields_and_bad_decision_shape(self) -> None:
        validator = schema_resources.load_validator(ADMISSION_SCHEMA_NAME)
        document = asdict(admission())
        del document["tool_binding"]
        errors = list(validator.iter_errors(document))
        self.assertEqual([(item.validator, tuple(item.absolute_path)) for item in errors], [("required", ())])

        document = asdict(admission())
        document["decision_time"] = "2026-09-23T10:30:00Z"
        errors = list(validator.iter_errors(document))
        self.assertEqual([(item.validator, tuple(item.absolute_path)) for item in errors], [("pattern", ("decision_time",))])

    def test_transitive_schema_resources_declare_expected_ids(self) -> None:
        expected = {
            GRANT_SCHEMA_NAME: GRANT_SCHEMA_ID,
            BINDING_SCHEMA_NAME: BINDING_SCHEMA_ID,
            RUN_SCHEMA_NAME: (
                "https://ai-engineering-orchestra.dev/schemas/"
                "agent-execution-run.schema.json"
            ),
            CONTRACT_SCHEMA_NAME: (
                "https://ai-engineering-orchestra.dev/schemas/"
                "agent-execution-contract.schema.json"
            ),
        }
        for name, schema_id in expected.items():
            with self.subTest(name=name):
                resource = schema_resources.schema_resource(name)
                self.assertIsNotNone(resource)
                assert resource is not None
                document = json.loads(resource.read_text(encoding="utf-8"))
                self.assertEqual(document["$id"], schema_id)


if __name__ == "__main__":
    unittest.main()
