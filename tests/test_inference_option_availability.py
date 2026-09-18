"""Focused Inference Option Availability runtime and boundary tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityFinding,
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
    InferenceOptionAvailabilityValidationResult,
    validate_inference_option_availability,
)
from engineering_orchestration.schema_resources import load_validator


def option(
    option_id: str,
    provider_id: str = "provider-a",
    model_id: str = "model-x",
) -> InferenceOptionDefinition:
    return InferenceOptionDefinition(option_id, provider_id, model_id)


def observation(
    option_id: str,
    state: InferenceOptionAvailabilityState = (
        InferenceOptionAvailabilityState.AVAILABLE
    ),
) -> InferenceOptionAvailabilityObservation:
    return InferenceOptionAvailabilityObservation(option_id, state)


class ExplodingObservation:
    @property
    def option_id(self):
        raise AssertionError("observations must not be inspected")


class InferenceOptionAvailabilityValueTests(unittest.TestCase):
    def test_state_values_are_exactly_the_closed_contract(self) -> None:
        self.assertEqual(
            [state.value for state in InferenceOptionAvailabilityState],
            ["available", "unavailable", "unknown"],
        )

    def test_unknown_is_distinct_from_unavailable(self) -> None:
        self.assertNotEqual(
            InferenceOptionAvailabilityState.UNKNOWN,
            InferenceOptionAvailabilityState.UNAVAILABLE,
        )

    def test_observation_has_exactly_two_fields_and_is_frozen(self) -> None:
        supplied = observation("primary")
        self.assertEqual(
            [field.name for field in fields(supplied)],
            ["option_id", "state"],
        )
        with self.assertRaises(FrozenInstanceError):
            supplied.state = (  # type: ignore[misc]
                InferenceOptionAvailabilityState.UNKNOWN
            )

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = InferenceOptionAvailabilityFinding("example", "message")
        result = InferenceOptionAvailabilityValidationResult(False, (finding,), ())
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_observations, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_schema_authorizes_exact_two_field_contract_and_three_states(self) -> None:
        schema = load_validator("inference-option-availability.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["option_id", "state"])
        self.assertEqual(set(schema["properties"]), {"option_id", "state"})
        self.assertEqual(
            schema["properties"]["state"]["enum"],
            ["available", "unavailable", "unknown"],
        )


class InferenceOptionAvailabilityValidationTests(unittest.TestCase):
    def assert_state(
        self,
        state: InferenceOptionAvailabilityState,
    ) -> None:
        supplied = observation("primary", state)
        result = validate_inference_option_availability(
            [supplied],
            [option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_observations, (supplied,))

    def test_known_option_available(self) -> None:
        self.assert_state(InferenceOptionAvailabilityState.AVAILABLE)

    def test_known_option_unavailable(self) -> None:
        self.assert_state(InferenceOptionAvailabilityState.UNAVAILABLE)

    def test_known_option_unknown(self) -> None:
        self.assert_state(InferenceOptionAvailabilityState.UNKNOWN)

    def test_missing_observation_normalizes_to_unknown_never_unavailable(self) -> None:
        result = validate_inference_option_availability([], [option("primary")])
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_observations,
            (
                observation(
                    "primary",
                    InferenceOptionAvailabilityState.UNKNOWN,
                ),
            ),
        )
        self.assertNotEqual(
            result.normalized_observations[0].state,
            InferenceOptionAvailabilityState.UNAVAILABLE,
        )

    def test_missing_and_explicit_unknown_normalize_equivalently(self) -> None:
        options = [option("primary")]
        missing = validate_inference_option_availability([], options)
        explicit = validate_inference_option_availability(
            [observation("primary", InferenceOptionAvailabilityState.UNKNOWN)],
            options,
        )
        self.assertEqual(missing, explicit)

    def test_normalized_output_is_sorted_by_option_id(self) -> None:
        result = validate_inference_option_availability(
            [
                observation("z", InferenceOptionAvailabilityState.UNAVAILABLE),
                observation("A", InferenceOptionAvailabilityState.AVAILABLE),
            ],
            [option("z"), option("a"), option("A")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [item.option_id for item in result.normalized_observations],
            ["A", "a", "z"],
        )
        self.assertEqual(
            result.normalized_observations[1].state,
            InferenceOptionAvailabilityState.UNKNOWN,
        )

    def test_empty_inventory_and_observations_are_valid(self) -> None:
        self.assertEqual(
            validate_inference_option_availability([], []),
            InferenceOptionAvailabilityValidationResult(True, (), ()),
        )

    def test_unknown_option_is_invalid_and_does_not_create_option(self) -> None:
        result = validate_inference_option_availability(
            [observation("missing")],
            [option("known")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.normalized_observations, ())
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["inference_option_not_found"],
        )

    def test_unknown_findings_are_sorted_and_deduplicated(self) -> None:
        result = validate_inference_option_availability(
            [observation("z"), observation("a")],
            [],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["inference_option_not_found", "inference_option_not_found"],
        )
        self.assertIn("'a'", result.findings[0].message)
        self.assertIn("'z'", result.findings[1].message)

    def test_duplicate_option_inventory_short_circuits_observations(self) -> None:
        result = validate_inference_option_availability(
            [ExplodingObservation()],  # type: ignore[list-item]
            [option("duplicate"), option("duplicate")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_inference_option_id"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_identical_duplicate_observations_are_rejected(self) -> None:
        result = validate_inference_option_availability(
            [observation("primary"), observation("primary")],
            [option("primary")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_inference_option_availability"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_conflicting_duplicates_are_not_resolved_by_order(self) -> None:
        available = observation("primary")
        unavailable = observation(
            "primary",
            InferenceOptionAvailabilityState.UNAVAILABLE,
        )
        forward = validate_inference_option_availability(
            [available, unavailable],
            [option("primary")],
        )
        reverse = validate_inference_option_availability(
            [unavailable, available],
            [option("primary")],
        )
        self.assertEqual(forward, reverse)
        self.assertFalse(forward.valid)

    def test_duplicate_findings_precede_unknown_findings_deterministically(self) -> None:
        supplied = [
            observation("z-missing"),
            observation("a-missing"),
            observation("z-missing"),
            observation("known"),
            observation("known", InferenceOptionAvailabilityState.UNKNOWN),
        ]
        forward = validate_inference_option_availability(
            supplied,
            [option("known")],
        )
        reverse = validate_inference_option_availability(
            list(reversed(supplied)),
            [option("known")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_inference_option_availability",
                "duplicate_inference_option_availability",
                "inference_option_not_found",
                "inference_option_not_found",
            ],
        )
        self.assertEqual(forward.normalized_observations, ())

    def test_same_provider_model_pair_remains_two_available_options(self) -> None:
        options = [
            option("secondary", "provider-a", "model-x"),
            option("primary", "provider-a", "model-x"),
        ]
        result = validate_inference_option_availability(
            [observation("primary")],
            options,
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [item.option_id for item in result.normalized_observations],
            ["primary", "secondary"],
        )
        self.assertEqual(
            result.normalized_observations[1].state,
            InferenceOptionAvailabilityState.UNKNOWN,
        )

    def test_validation_does_not_mutate_definition_or_observation_inputs(self) -> None:
        options = [option("b"), option("a")]
        observations = [observation("b")]
        options_before = list(options)
        observations_before = list(observations)
        validate_inference_option_availability(observations, options)
        self.assertEqual(options, options_before)
        self.assertEqual(observations, observations_before)

    def test_validation_performs_no_io_network_polling_or_process_work(self) -> None:
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
            result = validate_inference_option_availability(
                [],
                [option("primary")],
            )
        self.assertTrue(result.valid)


class InferenceOptionAvailabilityBoundaryTests(unittest.TestCase):
    def test_availability_never_changes_option_identity(self) -> None:
        definition = option("primary", "provider-a", "model-x")
        result = validate_inference_option_availability(
            [observation("primary")],
            [definition],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            definition,
            option("primary", "provider-a", "model-x"),
        )

    def test_available_contains_no_selection_authorization_execution_or_runtime(self) -> None:
        result = validate_inference_option_availability(
            [observation("primary")],
            [option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [field.name for field in fields(result.normalized_observations[0])],
            ["option_id", "state"],
        )
        forbidden = {
            "selected",
            "authorized",
            "executable",
            "runtime_available",
            "execution_mode",
            "provider_id",
            "model_id",
        }
        self.assertTrue(
            forbidden.isdisjoint(
                field.name for field in fields(result.normalized_observations[0])
            )
        )

    def test_availability_schema_has_no_provider_model_runtime_or_capability_fields(self) -> None:
        schema = load_validator("inference-option-availability.schema.json").schema
        forbidden = {
            "provider_id",
            "model_id",
            "runtime_id",
            "authorization",
            "context_window",
            "reasoning_controls",
            "price",
            "quota",
            "capabilities",
        }
        self.assertTrue(forbidden.isdisjoint(schema["properties"]))


if __name__ == "__main__":
    unittest.main()
