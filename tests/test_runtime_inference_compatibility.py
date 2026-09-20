"""Focused Runtime-to-Inference Compatibility Evidence tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from inspect import signature
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)
from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
    validate_inference_option_inventory,
)
import engineering_orchestration.runtime_inference_compatibility as compatibility
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
    RuntimeInferenceCompatibilityFinding,
    RuntimeInferenceCompatibilityValidationResult,
    validate_runtime_inference_compatibility,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]


def runtime(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def option(
    option_id: str,
    provider_id: str = "provider-a",
    model_id: str = "model-x",
) -> InferenceOptionDefinition:
    return InferenceOptionDefinition(option_id, provider_id, model_id)


def edge(
    runtime_option_id: str,
    option_id: str,
) -> RuntimeInferenceCompatibilityEvidence:
    return RuntimeInferenceCompatibilityEvidence(runtime_option_id, option_id)


class ExplodingEvidenceSequence:
    def __iter__(self):
        raise AssertionError("evidence must not be materialized or inspected")

    def __len__(self):
        raise AssertionError("evidence must not be materialized or inspected")

    def __getitem__(self, index):
        raise AssertionError("evidence must not be materialized or inspected")


class RuntimeInferenceCompatibilityValueTests(unittest.TestCase):
    def test_evidence_has_exactly_two_fields_and_is_frozen(self) -> None:
        supplied = edge("runtime", "inference")
        self.assertEqual(
            [field.name for field in fields(supplied)],
            ["runtime_option_id", "option_id"],
        )
        with self.assertRaises(FrozenInstanceError):
            supplied.option_id = "changed"  # type: ignore[misc]

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = RuntimeInferenceCompatibilityFinding("example", "message")
        result = RuntimeInferenceCompatibilityValidationResult(
            False,
            (finding,),
            (),
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_evidence, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_public_function_signature_and_result_fields_are_minimal(self) -> None:
        self.assertEqual(
            list(signature(validate_runtime_inference_compatibility).parameters),
            ["evidence", "runtime_options", "inference_options"],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(RuntimeInferenceCompatibilityValidationResult)
            ],
            ["valid", "findings", "normalized_evidence"],
        )

    def test_schema_authorizes_exact_two_field_contract(self) -> None:
        schema = load_validator(
            "runtime-inference-compatibility.schema.json"
        ).schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["runtime_option_id", "option_id"])
        self.assertEqual(
            set(schema["properties"]),
            {"runtime_option_id", "option_id"},
        )
        for definition in schema["properties"].values():
            self.assertEqual(definition["type"], "string")
            self.assertEqual(definition["minLength"], 1)
            self.assertNotIn("enum", definition)
            self.assertNotIn("pattern", definition)

    def test_schema_rejects_all_excluded_field_categories(self) -> None:
        validator = load_validator("runtime-inference-compatibility.schema.json")
        base = {"runtime_option_id": "runtime", "option_id": "inference"}
        excluded = {
            "compatibility_id",
            "actor_id",
            "provider_id",
            "model_id",
            "state",
            "compatible",
            "priority",
            "weight",
            "confidence",
            "source",
            "reason",
            "timestamp",
            "expires_at",
            "credentials",
            "endpoint",
            "native_config",
            "metadata",
            "extensions",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )


class RuntimeInferenceCompatibilityValidationTests(unittest.TestCase):
    def test_one_valid_edge(self) -> None:
        supplied = edge("runtime", "inference")
        result = validate_runtime_inference_compatibility(
            [supplied],
            [runtime("runtime")],
            [option("inference")],
        )
        self.assertEqual(
            result,
            RuntimeInferenceCompatibilityValidationResult(
                True,
                (),
                (supplied,),
            ),
        )

    def test_one_runtime_supports_multiple_inference_options(self) -> None:
        first = edge("runtime", "inference-a")
        second = edge("runtime", "inference-b")
        result = validate_runtime_inference_compatibility(
            [second, first],
            [runtime("runtime")],
            [option("inference-b"), option("inference-a")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, (first, second))

    def test_one_inference_option_supports_multiple_runtimes(self) -> None:
        first = edge("runtime-a", "inference")
        second = edge("runtime-b", "inference")
        result = validate_runtime_inference_compatibility(
            [second, first],
            [runtime("runtime-b"), runtime("runtime-a")],
            [option("inference")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, (first, second))

    def test_empty_relation_is_valid_for_all_empty_inventories(self) -> None:
        self.assertEqual(
            validate_runtime_inference_compatibility([], [], []),
            RuntimeInferenceCompatibilityValidationResult(True, (), ()),
        )

    def test_empty_relation_is_valid_for_mixed_and_nonempty_inventories(self) -> None:
        cases = (
            ([runtime("runtime")], []),
            ([], [option("inference")]),
            ([runtime("runtime")], [option("inference")]),
        )
        for runtime_options, inference_options in cases:
            with self.subTest(
                runtime_count=len(runtime_options),
                inference_count=len(inference_options),
            ):
                result = validate_runtime_inference_compatibility(
                    [], runtime_options, inference_options
                )
                self.assertEqual(
                    result,
                    RuntimeInferenceCompatibilityValidationResult(True, (), ()),
                )

    def test_exact_case_sensitive_endpoint_matching(self) -> None:
        supplied = [
            edge("Runtime", "Option"),
            edge("Runtime", "option"),
            edge("runtime", "Option"),
            edge("runtime", "option"),
        ]
        result = validate_runtime_inference_compatibility(
            list(reversed(supplied)),
            [runtime("runtime"), runtime("Runtime")],
            [option("option"), option("Option")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_evidence,
            tuple(
                sorted(
                    supplied,
                    key=lambda item: (item.runtime_option_id, item.option_id),
                )
            ),
        )

    def test_case_only_mismatch_is_unknown_for_both_endpoints(self) -> None:
        result = validate_runtime_inference_compatibility(
            [edge("runtime", "option")],
            [runtime("Runtime")],
            [option("Option")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_identifiers_remain_opaque_and_unmodified(self) -> None:
        supplied = edge(
            "Codex/Managed:A@2026?runtime=remote",
            "Provider/Model:B@2026?option=external",
        )
        result = validate_runtime_inference_compatibility(
            [supplied],
            [runtime(supplied.runtime_option_id)],
            [option(supplied.option_id, "Provider/A?", "model/@:opaque")],
        )
        self.assertEqual(result.normalized_evidence, (supplied,))

    def test_duplicate_identical_edge_invalidates_complete_relation(self) -> None:
        supplied = edge("runtime", "inference")
        result = validate_runtime_inference_compatibility(
            [supplied, supplied],
            [runtime("runtime")],
            [option("inference")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.normalized_evidence, ())
        self.assertEqual(
            result.findings,
            (
                RuntimeInferenceCompatibilityFinding(
                    "duplicate_runtime_inference_compatibility",
                    "Agent Runtime Option 'runtime' and Inference Option "
                    "'inference' have more than one supplied compatibility "
                    "evidence value.",
                ),
            ),
        )

    def test_distinct_duplicate_edges_are_sorted_and_order_independent(self) -> None:
        supplied = [
            edge("z-runtime", "a-option"),
            edge("a-runtime", "z-option"),
            edge("z-runtime", "a-option"),
            edge("a-runtime", "z-option"),
        ]
        runtime_options = [runtime("z-runtime"), runtime("a-runtime")]
        inference_options = [option("z-option"), option("a-option")]
        forward = validate_runtime_inference_compatibility(
            supplied, runtime_options, inference_options
        )
        reverse = validate_runtime_inference_compatibility(
            list(reversed(supplied)), runtime_options, inference_options
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_runtime_inference_compatibility",
                "duplicate_runtime_inference_compatibility",
            ],
        )
        self.assertIn("'a-runtime'", forward.findings[0].message)
        self.assertIn("'z-runtime'", forward.findings[1].message)

    def test_unknown_runtime_reference_is_rejected(self) -> None:
        result = validate_runtime_inference_compatibility(
            [edge("missing", "known")],
            [runtime("known")],
            [option("known")],
        )
        self.assertEqual(
            result.findings,
            (
                RuntimeInferenceCompatibilityFinding(
                    "agent_runtime_option_not_found",
                    "Agent Runtime Option 'missing' was not found in the supplied "
                    "inventory.",
                ),
            ),
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_unknown_inference_reference_is_rejected(self) -> None:
        result = validate_runtime_inference_compatibility(
            [edge("known", "missing")],
            [runtime("known")],
            [option("known")],
        )
        self.assertEqual(
            result.findings,
            (
                RuntimeInferenceCompatibilityFinding(
                    "inference_option_not_found",
                    "Inference Option 'missing' was not found in the supplied "
                    "inventory.",
                ),
            ),
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_both_unknown_references_produce_both_findings(self) -> None:
        result = validate_runtime_inference_compatibility(
            [edge("missing-runtime", "missing-option")],
            [],
            [],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_unknown_reference_findings_are_distinct_id_based(self) -> None:
        result = validate_runtime_inference_compatibility(
            [
                edge("missing", "missing-a"),
                edge("missing", "missing-b"),
            ],
            [],
            [],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            [
                "agent_runtime_option_not_found",
                "inference_option_not_found",
                "inference_option_not_found",
            ],
        )

    def test_both_foundational_inventories_are_reused_before_relation_semantics(self) -> None:
        runtime_options = [runtime("duplicate"), runtime("duplicate")]
        inference_options = [option("duplicate"), option("duplicate")]
        with (
            patch.object(
                compatibility,
                "validate_agent_runtime_option_inventory",
                wraps=validate_agent_runtime_option_inventory,
            ) as runtime_validator,
            patch.object(
                compatibility,
                "validate_inference_option_inventory",
                wraps=validate_inference_option_inventory,
            ) as inference_validator,
        ):
            result = validate_runtime_inference_compatibility(
                ExplodingEvidenceSequence(),  # type: ignore[arg-type]
                runtime_options,
                inference_options,
            )
        runtime_validator.assert_called_once_with(runtime_options)
        inference_validator.assert_called_once_with(inference_options)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_id", "duplicate_inference_option_id"],
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_invalid_runtime_inventory_preserves_foundation_finding(self) -> None:
        result = validate_runtime_inference_compatibility(
            [],
            [runtime("duplicate"), runtime("duplicate")],
            [option("valid")],
        )
        expected = validate_agent_runtime_option_inventory(
            [runtime("duplicate"), runtime("duplicate")]
        ).findings[0]
        self.assertEqual(
            result.findings,
            (RuntimeInferenceCompatibilityFinding(expected.code, expected.message),),
        )

    def test_invalid_inference_inventory_preserves_foundation_finding(self) -> None:
        result = validate_runtime_inference_compatibility(
            [],
            [runtime("valid")],
            [option("duplicate"), option("duplicate")],
        )
        expected = validate_inference_option_inventory(
            [option("duplicate"), option("duplicate")]
        ).findings[0]
        self.assertEqual(
            result.findings,
            (RuntimeInferenceCompatibilityFinding(expected.code, expected.message),),
        )

    def test_relation_findings_follow_locked_category_and_identifier_order(self) -> None:
        supplied = [
            edge("z-missing", "z-missing"),
            edge("known", "known"),
            edge("a-missing", "known"),
            edge("known", "a-missing"),
            edge("z-missing", "z-missing"),
            edge("known", "known"),
        ]
        forward = validate_runtime_inference_compatibility(
            supplied,
            [runtime("known")],
            [option("known")],
        )
        reverse = validate_runtime_inference_compatibility(
            list(reversed(supplied)),
            [runtime("known")],
            [option("known")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_runtime_inference_compatibility",
                "duplicate_runtime_inference_compatibility",
                "agent_runtime_option_not_found",
                "agent_runtime_option_not_found",
                "inference_option_not_found",
                "inference_option_not_found",
            ],
        )
        messages = [finding.message for finding in forward.findings]
        self.assertIn("'known'", messages[0])
        self.assertIn("'z-missing'", messages[1])
        self.assertIn("'a-missing'", messages[2])
        self.assertIn("'z-missing'", messages[3])
        self.assertIn("'a-missing'", messages[4])
        self.assertIn("'z-missing'", messages[5])
        self.assertEqual(forward.normalized_evidence, ())

    def test_valid_relation_is_canonicalized_by_exact_pair(self) -> None:
        supplied = [
            edge("z", "A"),
            edge("A", "z"),
            edge("a", "A"),
            edge("A", "a"),
        ]
        expected = (
            edge("A", "a"),
            edge("A", "z"),
            edge("a", "A"),
            edge("z", "A"),
        )
        result = validate_runtime_inference_compatibility(
            supplied,
            [runtime("a"), runtime("z"), runtime("A")],
            [option("z"), option("A"), option("a")],
        )
        self.assertEqual(result.normalized_evidence, expected)
        self.assertEqual(
            result,
            validate_runtime_inference_compatibility(
                list(reversed(supplied)),
                [runtime("A"), runtime("z"), runtime("a")],
                [option("a"), option("z"), option("A")],
            ),
        )

    def test_validation_does_not_mutate_inputs(self) -> None:
        supplied_evidence = [edge("b", "b"), edge("a", "a")]
        runtime_options = [runtime("b"), runtime("a")]
        inference_options = [option("b"), option("a")]
        before = (
            list(supplied_evidence),
            list(runtime_options),
            list(inference_options),
        )
        validate_runtime_inference_compatibility(
            supplied_evidence,
            runtime_options,
            inference_options,
        )
        self.assertEqual(
            (supplied_evidence, runtime_options, inference_options),
            before,
        )

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
            result = validate_runtime_inference_compatibility(
                [edge("runtime", "inference")],
                [runtime("runtime")],
                [option("inference")],
            )
        self.assertTrue(result.valid)


class RuntimeInferenceCompatibilityBoundaryTests(unittest.TestCase):
    def test_endpoint_schema_contracts_remain_unchanged(self) -> None:
        runtime_schema = load_validator("agent-runtime-option.schema.json").schema
        inference_schema = load_validator("inference-option.schema.json").schema
        self.assertEqual(
            set(runtime_schema["properties"]),
            {"runtime_option_id"},
        )
        self.assertEqual(
            set(inference_schema["properties"]),
            {"option_id", "provider_id", "model_id"},
        )
        self.assertNotIn("inference_option_ids", runtime_schema["properties"])
        self.assertNotIn("runtime_option_ids", inference_schema["properties"])

    def test_public_values_contain_no_availability_selection_or_execution_state(self) -> None:
        public_fields = {
            field.name for field in fields(RuntimeInferenceCompatibilityEvidence)
        } | {
            field.name
            for field in fields(RuntimeInferenceCompatibilityValidationResult)
        }
        forbidden = {
            "available",
            "state",
            "compatible",
            "selected",
            "authorized",
            "reserved",
            "dispatched",
            "executing",
            "actor_id",
            "execution_mode",
            "execution_configuration",
            "execution_contract",
            "priority",
            "weight",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_module_imports_only_endpoint_contracts_not_adjacent_domains(self) -> None:
        tree = ast.parse(
            (ROOT / "engineering_orchestration" /
             "runtime_inference_compatibility.py").read_text(encoding="utf-8")
        )
        internal_imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("engineering_orchestration")
        }
        self.assertEqual(
            internal_imports,
            {
                "engineering_orchestration.agent_runtime_option",
                "engineering_orchestration.inference_option",
            },
        )

    def test_missing_edge_is_not_collapsed_into_compatibility_boolean(self) -> None:
        result = validate_runtime_inference_compatibility(
            [],
            [runtime("runtime-with-internal-inference")],
            [option("external-option")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())
        self.assertFalse(hasattr(result, "compatible"))
        self.assertFalse(hasattr(compatibility, "is_compatible"))

    def test_no_configuration_authorization_adapter_or_invocation_api_exists(self) -> None:
        forbidden = {
            "ExecutionConfigurationCandidate",
            "ExecutionContract",
            "AgentDefinition",
            "AgentProfile",
            "AgentService",
            "select_runtime",
            "select_inference_option",
            "select_model",
            "dispatch",
            "invoke",
        }
        self.assertTrue(all(not hasattr(compatibility, name) for name in forbidden))

    def test_no_project_compatibility_storage_was_created(self) -> None:
        for relative in (
            ".ai/compatibility",
            ".ai/runtime-inference-compatibility",
            ".ai/runtime-inference-compatibility.yaml",
            ".ai/execution-configurations",
        ):
            self.assertFalse((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
