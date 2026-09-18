"""Focused Inference Option Definition runtime and boundary tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    InferenceOptionFinding,
    InferenceOptionInventoryValidationResult,
    validate_inference_option_inventory,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]


def option(
    option_id: str,
    provider_id: str = "provider-a",
    model_id: str = "model-x",
) -> InferenceOptionDefinition:
    return InferenceOptionDefinition(option_id, provider_id, model_id)


class InferenceOptionValueTests(unittest.TestCase):
    def test_definition_has_exactly_three_fields_and_is_frozen(self) -> None:
        definition = option("primary")
        self.assertEqual(
            [field.name for field in fields(definition)],
            ["option_id", "provider_id", "model_id"],
        )
        with self.assertRaises(FrozenInstanceError):
            definition.option_id = "changed"  # type: ignore[misc]

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = InferenceOptionFinding("example", "message")
        result = InferenceOptionInventoryValidationResult(
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

    def test_schema_authorizes_exact_three_field_contract(self) -> None:
        schema = load_validator("inference-option.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(
            schema["required"],
            ["option_id", "provider_id", "model_id"],
        )
        self.assertEqual(
            set(schema["properties"]),
            {"option_id", "provider_id", "model_id"},
        )
        for definition in schema["properties"].values():
            self.assertEqual(definition["type"], "string")
            self.assertEqual(definition["minLength"], 1)
            self.assertNotIn("enum", definition)
            self.assertNotIn("pattern", definition)

    def test_schema_rejects_all_excluded_field_categories(self) -> None:
        validator = load_validator("inference-option.schema.json")
        base = {
            "option_id": "primary",
            "provider_id": "provider-a",
            "model_id": "model-x",
        }
        excluded = {
            "deployment_id",
            "endpoint",
            "base_url",
            "api_key",
            "provider_metadata",
            "model_family",
            "model_version",
            "lifecycle",
            "context_window",
            "max_output_tokens",
            "modalities",
            "structured_output",
            "function_tools",
            "mcp",
            "code_execution",
            "computer_use",
            "reasoning_controls",
            "execution_mode_supported",
            "price",
            "quota",
            "region",
            "runtime_id",
            "session",
            "state_owner",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )


class InferenceOptionInventoryTests(unittest.TestCase):
    def test_one_valid_option_inventory(self) -> None:
        definition = option("primary")
        result = validate_inference_option_inventory([definition])
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_options, (definition,))

    def test_multiple_unique_options_are_canonicalized_by_option_id(self) -> None:
        result = validate_inference_option_inventory(
            [option("z-option"), option("A-option"), option("a-option")]
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [item.option_id for item in result.normalized_options],
            ["A-option", "a-option", "z-option"],
        )

    def test_empty_inventory_is_valid(self) -> None:
        self.assertEqual(
            validate_inference_option_inventory([]),
            InferenceOptionInventoryValidationResult(True, (), ()),
        )

    def test_duplicate_option_id_invalidates_complete_inventory(self) -> None:
        result = validate_inference_option_inventory(
            [option("duplicate"), option("unique"), option("duplicate")]
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.normalized_options, ())
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_inference_option_id"],
        )
        self.assertIn("duplicate", result.findings[0].message)

    def test_all_duplicate_ids_are_reported_once_in_sorted_order(self) -> None:
        result = validate_inference_option_inventory(
            [
                option("z"),
                option("a"),
                option("z"),
                option("a"),
                option("a"),
            ]
        )
        self.assertFalse(result.valid)
        self.assertTrue(result.findings[0].message.endswith("a, z"))

    def test_duplicate_finding_is_independent_of_declaration_order(self) -> None:
        supplied = [option("b"), option("a"), option("b"), option("a")]
        forward = validate_inference_option_inventory(supplied)
        reverse = validate_inference_option_inventory(list(reversed(supplied)))
        self.assertEqual(forward, reverse)

    def test_same_provider_model_pair_with_different_option_ids_is_valid(self) -> None:
        first = option("primary", "provider-a", "model-x")
        second = option("secondary", "provider-a", "model-x")
        result = validate_inference_option_inventory([second, first])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_options, (first, second))

    def test_provider_and_model_ids_remain_opaque_and_provider_scoped(self) -> None:
        supplied = option(
            "MiXeD option/@:2026",
            "Provider/A:Region?",
            "family-v9-20991231@tier",
        )
        result = validate_inference_option_inventory([supplied])
        self.assertEqual(result.normalized_options, (supplied,))
        self.assertEqual(result.normalized_options[0].provider_id, supplied.provider_id)
        self.assertEqual(result.normalized_options[0].model_id, supplied.model_id)

    def test_provider_and_model_pair_never_replaces_option_identity(self) -> None:
        first = option("one", "provider-a", "model-x")
        second = option("two", "provider-a", "model-x")
        forward = validate_inference_option_inventory([first, second])
        reverse = validate_inference_option_inventory([second, first])
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [item.option_id for item in forward.normalized_options],
            ["one", "two"],
        )

    def test_validation_does_not_mutate_inputs(self) -> None:
        supplied = [option("b"), option("a")]
        original = list(supplied)
        validate_inference_option_inventory(supplied)
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
            result = validate_inference_option_inventory([option("primary")])
        self.assertTrue(result.valid)


class InferenceOptionBoundaryTests(unittest.TestCase):
    def test_result_contains_no_selection_authorization_or_runtime_state(self) -> None:
        self.assertEqual(
            [field.name for field in fields(InferenceOptionInventoryValidationResult)],
            ["valid", "findings", "normalized_options"],
        )
        forbidden = {
            "selected_option_id",
            "provider_selected",
            "authorized",
            "executable",
            "runtime_id",
            "execution_mode",
        }
        self.assertTrue(
            forbidden.isdisjoint(
                field.name for field in fields(InferenceOptionInventoryValidationResult)
            )
        )

    def test_actor_and_assignment_schema_contracts_remain_unchanged(self) -> None:
        actor = load_validator("actor.schema.json").schema
        assignment = load_validator("assignment.schema.json").schema
        self.assertEqual(
            set(actor["properties"]),
            {"id", "kind", "competencies"},
        )
        self.assertEqual(
            set(assignment["properties"]),
            {"task_id", "workflow_id", "stage_id", "role_id", "actor_id"},
        )
        self.assertTrue(
            {"option_id", "provider_id", "model_id"}.isdisjoint(
                actor["properties"]
            )
        )
        self.assertTrue(
            {"option_id", "provider_id", "model_id"}.isdisjoint(
                assignment["properties"]
            )
        )

    def test_no_project_inventory_storage_was_created(self) -> None:
        for relative in (
            ".ai/providers",
            ".ai/models",
            ".ai/inference-options",
            ".ai/inventory",
        ):
            self.assertFalse((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
