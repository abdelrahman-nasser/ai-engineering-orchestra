"""Focused Agent Runtime Option Definition runtime and boundary tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    AgentRuntimeOptionFinding,
    AgentRuntimeOptionInventoryValidationResult,
    validate_agent_runtime_option_inventory,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]


def runtime_option(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


class AgentRuntimeOptionValueTests(unittest.TestCase):
    def test_definition_has_exactly_one_field_and_is_frozen(self) -> None:
        definition = runtime_option("primary")
        self.assertEqual(
            [field.name for field in fields(definition)],
            ["runtime_option_id"],
        )
        with self.assertRaises(FrozenInstanceError):
            definition.runtime_option_id = "changed"  # type: ignore[misc]

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = AgentRuntimeOptionFinding("example", "message")
        result = AgentRuntimeOptionInventoryValidationResult(
            False,
            (finding,),
            (),
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_options, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_schema_authorizes_exact_one_field_contract(self) -> None:
        schema = load_validator("agent-runtime-option.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["runtime_option_id"])
        self.assertEqual(set(schema["properties"]), {"runtime_option_id"})
        definition = schema["properties"]["runtime_option_id"]
        self.assertEqual(definition["type"], "string")
        self.assertEqual(definition["minLength"], 1)
        self.assertNotIn("enum", definition)
        self.assertNotIn("pattern", definition)

    def test_schema_rejects_all_excluded_field_categories(self) -> None:
        validator = load_validator("agent-runtime-option.schema.json")
        base = {"runtime_option_id": "primary"}
        excluded = {
            "kind",
            "provider_id",
            "model_id",
            "implementation",
            "framework",
            "managed",
            "ownership",
            "execution_owner",
            "state_owner",
            "session_owner",
            "tools",
            "mcp",
            "filesystem",
            "shell",
            "web",
            "computer_use",
            "sandbox",
            "state",
            "sessions",
            "memory",
            "scheduling",
            "capacity",
            "endpoint",
            "credentials",
            "api_key",
            "actor_id",
            "option_id",
            "inference_option_ids",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )


class AgentRuntimeOptionInventoryTests(unittest.TestCase):
    def test_one_valid_option_inventory(self) -> None:
        definition = runtime_option("primary")
        result = validate_agent_runtime_option_inventory([definition])
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_options, (definition,))

    def test_multiple_unique_options_are_canonicalized_by_id(self) -> None:
        result = validate_agent_runtime_option_inventory(
            [runtime_option("z-option"), runtime_option("A-option"),
             runtime_option("a-option")]
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [item.runtime_option_id for item in result.normalized_options],
            ["A-option", "a-option", "z-option"],
        )

    def test_empty_inventory_is_valid(self) -> None:
        self.assertEqual(
            validate_agent_runtime_option_inventory([]),
            AgentRuntimeOptionInventoryValidationResult(True, (), ()),
        )

    def test_duplicate_id_invalidates_complete_inventory(self) -> None:
        result = validate_agent_runtime_option_inventory(
            [runtime_option("duplicate"), runtime_option("unique"),
             runtime_option("duplicate")]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.normalized_options, ())
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_id"],
        )
        self.assertIn("duplicate", result.findings[0].message)

    def test_all_duplicate_ids_are_reported_once_in_sorted_order(self) -> None:
        result = validate_agent_runtime_option_inventory(
            [
                runtime_option("z"),
                runtime_option("a"),
                runtime_option("z"),
                runtime_option("a"),
                runtime_option("a"),
            ]
        )
        self.assertFalse(result.valid)
        self.assertTrue(result.findings[0].message.endswith("a, z"))

    def test_duplicate_finding_is_independent_of_declaration_order(self) -> None:
        supplied = [
            runtime_option("b"),
            runtime_option("a"),
            runtime_option("b"),
            runtime_option("a"),
        ]
        forward = validate_agent_runtime_option_inventory(supplied)
        reverse = validate_agent_runtime_option_inventory(list(reversed(supplied)))
        self.assertEqual(forward, reverse)

    def test_declaration_order_does_not_establish_preference(self) -> None:
        supplied = [runtime_option("secondary"), runtime_option("primary")]
        forward = validate_agent_runtime_option_inventory(supplied)
        reverse = validate_agent_runtime_option_inventory(list(reversed(supplied)))
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [item.runtime_option_id for item in forward.normalized_options],
            ["primary", "secondary"],
        )

    def test_runtime_option_id_is_opaque_and_not_vendor_parsed(self) -> None:
        supplied = runtime_option("Codex/Managed:A@2026?runtime=remote")
        result = validate_agent_runtime_option_inventory([supplied])
        self.assertEqual(result.normalized_options, (supplied,))
        self.assertEqual(
            result.normalized_options[0].runtime_option_id,
            supplied.runtime_option_id,
        )

    def test_runtime_option_identity_is_case_sensitive(self) -> None:
        result = validate_agent_runtime_option_inventory(
            [runtime_option("Runtime-A"), runtime_option("runtime-a")]
        )
        self.assertTrue(result.valid)
        self.assertEqual(len(result.normalized_options), 2)

    def test_validation_does_not_mutate_inputs(self) -> None:
        supplied = [runtime_option("b"), runtime_option("a")]
        original = list(supplied)
        validate_agent_runtime_option_inventory(supplied)
        self.assertEqual(supplied, original)

    def test_validation_performs_no_io_network_discovery_or_process_work(self) -> None:
        with (
            patch("builtins.open", side_effect=AssertionError("no file access")),
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("no network access"),
            ),
            patch.object(
                urllib.request,
                "urlopen",
                side_effect=AssertionError("no Provider API access"),
            ),
            patch.object(
                subprocess,
                "run",
                side_effect=AssertionError("no process execution"),
            ),
            patch.object(
                subprocess,
                "Popen",
                side_effect=AssertionError("no process execution"),
            ),
        ):
            result = validate_agent_runtime_option_inventory(
                [runtime_option("primary")]
            )
        self.assertTrue(result.valid)


class AgentRuntimeOptionBoundaryTests(unittest.TestCase):
    def test_result_contains_no_selection_authorization_or_execution_state(self) -> None:
        self.assertEqual(
            [
                field.name
                for field in fields(AgentRuntimeOptionInventoryValidationResult)
            ],
            ["valid", "findings", "normalized_options"],
        )
        forbidden = {
            "selected_runtime_option_id",
            "authorized",
            "executable",
            "executing",
            "execution_mode",
            "actor_id",
            "option_id",
        }
        self.assertTrue(
            forbidden.isdisjoint(
                field.name
                for field in fields(AgentRuntimeOptionInventoryValidationResult)
            )
        )

    def test_actor_inference_and_assignment_contracts_remain_unchanged(self) -> None:
        actor = load_validator("actor.schema.json").schema
        inference = load_validator("inference-option.schema.json").schema
        assignment = load_validator("assignment.schema.json").schema
        self.assertEqual(set(actor["properties"]), {"id", "kind", "competencies"})
        self.assertEqual(
            set(inference["properties"]),
            {"option_id", "provider_id", "model_id"},
        )
        self.assertEqual(
            set(assignment["properties"]),
            {"task_id", "workflow_id", "stage_id", "role_id", "actor_id"},
        )
        self.assertNotIn("runtime_option_id", actor["properties"])
        self.assertNotIn("runtime_option_id", inference["properties"])
        self.assertNotIn("runtime_option_id", assignment["properties"])

    def test_runtime_identity_is_independent_from_actor_and_inference(self) -> None:
        definition = runtime_option("primary")
        self.assertEqual(
            [field.name for field in fields(definition)],
            ["runtime_option_id"],
        )
        self.assertFalse(hasattr(definition, "actor_id"))
        self.assertFalse(hasattr(definition, "option_id"))
        self.assertFalse(hasattr(definition, "provider_id"))
        self.assertFalse(hasattr(definition, "model_id"))

    def test_no_agent_definition_or_actor_runtime_compatibility_was_created(self) -> None:
        for relative in (
            "engineering_orchestration/agent_definition.py",
            "engineering_orchestration/actor_runtime_compatibility.py",
            "schemas/agent-definition.schema.json",
            "schemas/actor-runtime-compatibility.schema.json",
        ):
            self.assertFalse((ROOT / relative).exists())

    def test_no_project_runtime_inventory_storage_was_created(self) -> None:
        for relative in (
            ".ai/runtimes",
            ".ai/runtime-options",
            ".ai/agent-runtimes",
        ):
            self.assertFalse((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
