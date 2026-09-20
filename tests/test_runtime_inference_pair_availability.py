"""Focused Runtime-to-Inference Pair Availability Assessment tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from inspect import signature
from pathlib import Path
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request

import engineering_orchestration
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
    validate_agent_runtime_option_availability,
)
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
    validate_inference_option_availability,
)
import engineering_orchestration.runtime_inference_pair_availability as assessment
from engineering_orchestration.runtime_inference_pair_availability import (
    RuntimeInferencePairAvailabilityAssessment,
    RuntimeInferencePairAvailabilityFinding,
    RuntimeInferencePairAvailabilityOutcome,
    RuntimeInferencePairAvailabilityResult,
    assess_runtime_inference_pair_availability,
)
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
    validate_runtime_inference_compatibility,
)


ROOT = Path(__file__).resolve().parents[1]


def runtime(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def option(
    option_id: str,
    provider_id: str = "provider::synthetic",
    model_id: str = "model::synthetic",
) -> InferenceOptionDefinition:
    return InferenceOptionDefinition(option_id, provider_id, model_id)


def edge(
    runtime_option_id: str,
    option_id: str,
) -> RuntimeInferenceCompatibilityEvidence:
    return RuntimeInferenceCompatibilityEvidence(runtime_option_id, option_id)


def runtime_observation(
    runtime_option_id: str,
    state: AgentRuntimeOptionAvailabilityState = (
        AgentRuntimeOptionAvailabilityState.AVAILABLE
    ),
) -> AgentRuntimeOptionAvailabilityObservation:
    return AgentRuntimeOptionAvailabilityObservation(runtime_option_id, state)


def inference_observation(
    option_id: str,
    state: InferenceOptionAvailabilityState = (
        InferenceOptionAvailabilityState.AVAILABLE
    ),
) -> InferenceOptionAvailabilityObservation:
    return InferenceOptionAvailabilityObservation(option_id, state)


class OneShotIterable:
    """Iterable that fails if a caller tries to capture it more than once."""

    def __init__(self, *values: object) -> None:
        self.values = values
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("caller input was read more than once")
        return iter(self.values)


class RuntimeInferencePairAvailabilityValueTests(unittest.TestCase):
    def test_outcome_values_are_exactly_the_closed_contract(self) -> None:
        self.assertEqual(
            [outcome.value for outcome in RuntimeInferencePairAvailabilityOutcome],
            ["established", "blocked", "unresolved"],
        )

    def test_assessment_has_exactly_four_stored_fields_and_is_frozen(self) -> None:
        supplied = RuntimeInferencePairAvailabilityAssessment(
            "runtime::opaque",
            "option::opaque",
            AgentRuntimeOptionAvailabilityState.AVAILABLE,
            InferenceOptionAvailabilityState.AVAILABLE,
        )
        self.assertEqual(
            [field.name for field in fields(supplied)],
            [
                "runtime_option_id",
                "option_id",
                "runtime_availability_state",
                "inference_availability_state",
            ],
        )
        self.assertNotIn("outcome", [field.name for field in fields(supplied)])
        with self.assertRaises(FrozenInstanceError):
            supplied.option_id = "changed"  # type: ignore[misc]

    def test_outcome_is_computed_and_read_only(self) -> None:
        supplied = RuntimeInferencePairAvailabilityAssessment(
            "runtime::opaque",
            "option::opaque",
            AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
            InferenceOptionAvailabilityState.AVAILABLE,
        )
        self.assertEqual(
            supplied.outcome,
            RuntimeInferencePairAvailabilityOutcome.BLOCKED,
        )
        self.assertIsInstance(
            RuntimeInferencePairAvailabilityAssessment.outcome,
            property,
        )
        self.assertIsNone(RuntimeInferencePairAvailabilityAssessment.outcome.fset)
        with self.assertRaises(FrozenInstanceError):
            supplied.outcome = (  # type: ignore[misc]
                RuntimeInferencePairAvailabilityOutcome.ESTABLISHED
            )

    def test_malformed_direct_state_construction_raises_value_error(self) -> None:
        cases = (
            (
                "available",
                InferenceOptionAvailabilityState.AVAILABLE,
            ),
            (
                InferenceOptionAvailabilityState.AVAILABLE,
                InferenceOptionAvailabilityState.AVAILABLE,
            ),
            (
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
                "available",
            ),
            (
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
            ),
        )
        for runtime_state, inference_state in cases:
            with self.subTest(
                runtime_state=runtime_state,
                inference_state=inference_state,
            ):
                with self.assertRaises(ValueError):
                    RuntimeInferencePairAvailabilityAssessment(
                        "runtime::opaque",
                        "option::opaque",
                        runtime_state,  # type: ignore[arg-type]
                        inference_state,  # type: ignore[arg-type]
                    )

    def test_finding_and_result_are_minimal_frozen_and_tuple_backed(self) -> None:
        finding = RuntimeInferencePairAvailabilityFinding("example", "message")
        result = RuntimeInferencePairAvailabilityResult(False, (finding,), ())
        self.assertEqual(
            [field.name for field in fields(finding)],
            ["code", "message"],
        )
        self.assertEqual(
            [field.name for field in fields(result)],
            ["valid", "findings", "assessments"],
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.assessments, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_public_function_signature_has_exactly_five_locked_inputs(self) -> None:
        self.assertEqual(
            list(signature(assess_runtime_inference_pair_availability).parameters),
            [
                "evidence",
                "runtime_options",
                "inference_options",
                "runtime_availability_observations",
                "inference_availability_observations",
            ],
        )


class RuntimeInferencePairAvailabilityOutcomeTests(unittest.TestCase):
    def test_complete_nine_row_truth_table(self) -> None:
        cases = (
            (
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
                InferenceOptionAvailabilityState.AVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.ESTABLISHED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
                InferenceOptionAvailabilityState.UNAVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.BLOCKED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.AVAILABLE,
                InferenceOptionAvailabilityState.UNKNOWN,
                RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                InferenceOptionAvailabilityState.AVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.BLOCKED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                InferenceOptionAvailabilityState.UNAVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.BLOCKED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                InferenceOptionAvailabilityState.UNKNOWN,
                RuntimeInferencePairAvailabilityOutcome.BLOCKED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
                InferenceOptionAvailabilityState.AVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
                InferenceOptionAvailabilityState.UNAVAILABLE,
                RuntimeInferencePairAvailabilityOutcome.BLOCKED,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
                InferenceOptionAvailabilityState.UNKNOWN,
                RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
            ),
        )
        for runtime_state, inference_state, expected_outcome in cases:
            with self.subTest(
                runtime_state=runtime_state,
                inference_state=inference_state,
            ):
                result = assess_runtime_inference_pair_availability(
                    [edge("runtime::truth-table", "option::truth-table")],
                    [runtime("runtime::truth-table")],
                    [option("option::truth-table")],
                    [
                        runtime_observation(
                            "runtime::truth-table",
                            runtime_state,
                        )
                    ],
                    [
                        inference_observation(
                            "option::truth-table",
                            inference_state,
                        )
                    ],
                )
                self.assertTrue(result.valid)
                self.assertEqual(result.findings, ())
                self.assertEqual(len(result.assessments), 1)
                item = result.assessments[0]
                self.assertEqual(item.runtime_availability_state, runtime_state)
                self.assertEqual(
                    item.inference_availability_state,
                    inference_state,
                )
                self.assertEqual(item.outcome, expected_outcome)

    def test_unavailable_plus_unknown_blocks_without_overwriting_unknown(self) -> None:
        cases = (
            (
                AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                InferenceOptionAvailabilityState.UNKNOWN,
            ),
            (
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
                InferenceOptionAvailabilityState.UNAVAILABLE,
            ),
        )
        for runtime_state, inference_state in cases:
            with self.subTest(
                runtime_state=runtime_state,
                inference_state=inference_state,
            ):
                result = assess_runtime_inference_pair_availability(
                    [edge("runtime::mixed", "option::mixed")],
                    [runtime("runtime::mixed")],
                    [option("option::mixed")],
                    [runtime_observation("runtime::mixed", runtime_state)],
                    [inference_observation("option::mixed", inference_state)],
                )
                item = result.assessments[0]
                self.assertEqual(
                    item.outcome,
                    RuntimeInferencePairAvailabilityOutcome.BLOCKED,
                )
                self.assertEqual(item.runtime_availability_state, runtime_state)
                self.assertEqual(
                    item.inference_availability_state,
                    inference_state,
                )

    def test_missing_runtime_observation_equals_explicit_unknown(self) -> None:
        arguments = (
            [edge("runtime::missing", "option::available")],
            [runtime("runtime::missing")],
            [option("option::available")],
        )
        missing = assess_runtime_inference_pair_availability(
            *arguments,
            [],
            [inference_observation("option::available")],
        )
        explicit = assess_runtime_inference_pair_availability(
            *arguments,
            [
                runtime_observation(
                    "runtime::missing",
                    AgentRuntimeOptionAvailabilityState.UNKNOWN,
                )
            ],
            [inference_observation("option::available")],
        )
        self.assertEqual(missing, explicit)
        self.assertEqual(
            missing.assessments[0].outcome,
            RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
        )

    def test_missing_inference_observation_equals_explicit_unknown(self) -> None:
        arguments = (
            [edge("runtime::available", "option::missing")],
            [runtime("runtime::available")],
            [option("option::missing")],
            [runtime_observation("runtime::available")],
        )
        missing = assess_runtime_inference_pair_availability(*arguments, [])
        explicit = assess_runtime_inference_pair_availability(
            *arguments,
            [
                inference_observation(
                    "option::missing",
                    InferenceOptionAvailabilityState.UNKNOWN,
                )
            ],
        )
        self.assertEqual(missing, explicit)
        self.assertEqual(
            missing.assessments[0].outcome,
            RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
        )

    def test_both_missing_observations_equal_both_explicit_unknown(self) -> None:
        arguments = (
            [edge("runtime::missing", "option::missing")],
            [runtime("runtime::missing")],
            [option("option::missing")],
        )
        missing = assess_runtime_inference_pair_availability(
            *arguments,
            [],
            [],
        )
        explicit = assess_runtime_inference_pair_availability(
            *arguments,
            [
                runtime_observation(
                    "runtime::missing",
                    AgentRuntimeOptionAvailabilityState.UNKNOWN,
                )
            ],
            [
                inference_observation(
                    "option::missing",
                    InferenceOptionAvailabilityState.UNKNOWN,
                )
            ],
        )
        self.assertEqual(missing, explicit)
        self.assertEqual(
            missing.assessments[0].outcome,
            RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
        )


class RuntimeInferencePairAvailabilityRelationTests(unittest.TestCase):
    def test_one_to_many_many_to_one_and_mixed_outcomes_assess_edges_only(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [
                edge("runtime::beta", "option::alpha"),
                edge("runtime::alpha", "option::beta"),
                edge("runtime::alpha", "option::alpha"),
            ],
            [
                runtime("runtime::orphan"),
                runtime("runtime::beta"),
                runtime("runtime::alpha"),
            ],
            [
                option("option::orphan"),
                option("option::beta"),
                option("option::alpha"),
            ],
            [
                runtime_observation(
                    "runtime::beta",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                ),
                runtime_observation("runtime::alpha"),
                runtime_observation("runtime::orphan"),
            ],
            [
                inference_observation(
                    "option::orphan",
                    InferenceOptionAvailabilityState.UNAVAILABLE,
                ),
                inference_observation(
                    "option::beta",
                    InferenceOptionAvailabilityState.UNKNOWN,
                ),
                inference_observation("option::alpha"),
            ],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [
                (item.runtime_option_id, item.option_id, item.outcome)
                for item in result.assessments
            ],
            [
                (
                    "runtime::alpha",
                    "option::alpha",
                    RuntimeInferencePairAvailabilityOutcome.ESTABLISHED,
                ),
                (
                    "runtime::alpha",
                    "option::beta",
                    RuntimeInferencePairAvailabilityOutcome.UNRESOLVED,
                ),
                (
                    "runtime::beta",
                    "option::alpha",
                    RuntimeInferencePairAvailabilityOutcome.BLOCKED,
                ),
            ],
        )
        assessed_pairs = {
            (item.runtime_option_id, item.option_id)
            for item in result.assessments
        }
        self.assertNotIn(
            ("runtime::orphan", "option::orphan"),
            assessed_pairs,
        )
        self.assertEqual(len(assessed_pairs), 3)

    def test_valid_empty_relation_returns_valid_empty_assessments(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [],
            [runtime("runtime::internal-or-unlisted")],
            [option("option::unlisted")],
            [
                runtime_observation(
                    "runtime::internal-or-unlisted",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            [inference_observation("option::unlisted")],
        )
        self.assertEqual(
            result,
            RuntimeInferencePairAvailabilityResult(True, (), ()),
        )

    def test_all_empty_inputs_return_valid_empty_assessments(self) -> None:
        self.assertEqual(
            assess_runtime_inference_pair_availability([], [], [], [], []),
            RuntimeInferencePairAvailabilityResult(True, (), ()),
        )

    def test_pair_order_is_exact_case_sensitive_and_declaration_independent(
        self,
    ) -> None:
        supplied_edges = [
            edge("z-runtime", "A-option"),
            edge("A-runtime", "z-option"),
            edge("a-runtime", "a-option"),
            edge("A-runtime", "A-option"),
        ]
        runtime_options = [
            runtime("a-runtime"),
            runtime("z-runtime"),
            runtime("A-runtime"),
        ]
        inference_options = [
            option("a-option"),
            option("z-option"),
            option("A-option"),
        ]
        forward = assess_runtime_inference_pair_availability(
            supplied_edges,
            runtime_options,
            inference_options,
            [],
            [],
        )
        reverse = assess_runtime_inference_pair_availability(
            list(reversed(supplied_edges)),
            list(reversed(runtime_options)),
            list(reversed(inference_options)),
            [],
            [],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [
                (item.runtime_option_id, item.option_id)
                for item in forward.assessments
            ],
            [
                ("A-runtime", "A-option"),
                ("A-runtime", "z-option"),
                ("a-runtime", "a-option"),
                ("z-runtime", "A-option"),
            ],
        )
        self.assertTrue(
            all(
                item.outcome
                is RuntimeInferencePairAvailabilityOutcome.UNRESOLVED
                for item in forward.assessments
            )
        )

    def test_case_only_reference_mismatch_is_invalid_not_unresolved(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [edge("runtime", "option")],
            [runtime("Runtime")],
            [option("Option")],
            [],
            [],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )
        self.assertEqual(result.assessments, ())

    def test_opaque_identifiers_are_preserved_exactly(self) -> None:
        runtime_id = "Runtime/Surface:A@2026?mode=remote"
        option_id = "Provider/Model:B@2026?access=external"
        result = assess_runtime_inference_pair_availability(
            [edge(runtime_id, option_id)],
            [runtime(runtime_id)],
            [option(option_id, "Provider/A?", "model/@:opaque")],
            [runtime_observation(runtime_id)],
            [inference_observation(option_id)],
        )
        self.assertEqual(
            (
                result.assessments[0].runtime_option_id,
                result.assessments[0].option_id,
            ),
            (runtime_id, option_id),
        )


class RuntimeInferencePairAvailabilityValidationTests(unittest.TestCase):
    def test_compatibility_failure_preserves_findings_and_short_circuits_availability(
        self,
    ) -> None:
        supplied_edges = [
            edge("runtime::known", "option::known"),
            edge("runtime::known", "option::known"),
            edge("runtime::missing", "option::missing"),
            edge("runtime::missing", "option::missing"),
        ]
        runtime_options = [runtime("runtime::known")]
        inference_options = [option("option::known")]
        expected = validate_runtime_inference_compatibility(
            supplied_edges,
            runtime_options,
            inference_options,
        )
        with (
            patch.object(
                assessment,
                "validate_agent_runtime_option_availability",
                side_effect=AssertionError(
                    "Runtime availability must be short-circuited"
                ),
            ) as runtime_validator,
            patch.object(
                assessment,
                "validate_inference_option_availability",
                side_effect=AssertionError(
                    "Inference availability must be short-circuited"
                ),
            ) as inference_validator,
        ):
            result = assess_runtime_inference_pair_availability(
                supplied_edges,
                runtime_options,
                inference_options,
                [],
                [],
            )
        runtime_validator.assert_not_called()
        inference_validator.assert_not_called()
        self.assertFalse(result.valid)
        self.assertEqual(
            result.findings,
            tuple(
                RuntimeInferencePairAvailabilityFinding(
                    finding.code,
                    finding.message,
                )
                for finding in expected.findings
            ),
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            [
                "duplicate_runtime_inference_compatibility",
                "duplicate_runtime_inference_compatibility",
                "agent_runtime_option_not_found",
                "inference_option_not_found",
            ],
        )
        self.assertEqual(result.assessments, ())

    def test_all_five_inputs_are_captured_before_compatibility_failure(self) -> None:
        supplied = edge("runtime::duplicate", "option::duplicate")
        evidence = OneShotIterable(supplied, supplied)
        runtime_options = OneShotIterable(runtime("runtime::duplicate"))
        inference_options = OneShotIterable(option("option::duplicate"))
        runtime_observations = OneShotIterable(
            runtime_observation("runtime::duplicate")
        )
        inference_observations = OneShotIterable(
            inference_observation("option::duplicate")
        )
        with (
            patch.object(
                assessment,
                "validate_agent_runtime_option_availability",
            ) as runtime_validator,
            patch.object(
                assessment,
                "validate_inference_option_availability",
            ) as inference_validator,
        ):
            result = assess_runtime_inference_pair_availability(
                evidence,  # type: ignore[arg-type]
                runtime_options,  # type: ignore[arg-type]
                inference_options,  # type: ignore[arg-type]
                runtime_observations,  # type: ignore[arg-type]
                inference_observations,  # type: ignore[arg-type]
            )
        self.assertFalse(result.valid)
        self.assertEqual(
            [
                evidence.iterations,
                runtime_options.iterations,
                inference_options.iterations,
                runtime_observations.iterations,
                inference_observations.iterations,
            ],
            [1, 1, 1, 1, 1],
        )
        runtime_validator.assert_not_called()
        inference_validator.assert_not_called()

    def test_validation_order_and_same_captured_inventories_are_reused(self) -> None:
        supplied_inputs = (
            OneShotIterable(edge("runtime::one-shot", "option::one-shot")),
            OneShotIterable(runtime("runtime::one-shot")),
            OneShotIterable(option("option::one-shot")),
            OneShotIterable(runtime_observation("runtime::one-shot")),
            OneShotIterable(inference_observation("option::one-shot")),
        )
        events: list[str] = []

        def compatibility_spy(evidence, runtime_options, inference_options):
            events.append("compatibility")
            return validate_runtime_inference_compatibility(
                evidence,
                runtime_options,
                inference_options,
            )

        def runtime_spy(observations, options):
            events.append("runtime_availability")
            return validate_agent_runtime_option_availability(
                observations,
                options,
            )

        def inference_spy(observations, options):
            events.append("inference_availability")
            return validate_inference_option_availability(
                observations,
                options,
            )

        with (
            patch.object(
                assessment,
                "validate_runtime_inference_compatibility",
                side_effect=compatibility_spy,
            ) as compatibility_validator,
            patch.object(
                assessment,
                "validate_agent_runtime_option_availability",
                side_effect=runtime_spy,
            ) as runtime_validator,
            patch.object(
                assessment,
                "validate_inference_option_availability",
                side_effect=inference_spy,
            ) as inference_validator,
        ):
            result = assess_runtime_inference_pair_availability(
                *supplied_inputs  # type: ignore[arg-type]
            )
        self.assertTrue(result.valid)
        self.assertEqual(
            events,
            [
                "compatibility",
                "runtime_availability",
                "inference_availability",
            ],
        )
        self.assertEqual(
            [item.iterations for item in supplied_inputs],
            [1, 1, 1, 1, 1],
        )
        compatibility_arguments = compatibility_validator.call_args.args
        runtime_arguments = runtime_validator.call_args.args
        inference_arguments = inference_validator.call_args.args
        self.assertTrue(
            all(
                isinstance(value, tuple)
                for value in (
                    *compatibility_arguments,
                    runtime_arguments[0],
                    inference_arguments[0],
                )
            )
        )
        self.assertIs(compatibility_arguments[1], runtime_arguments[1])
        self.assertIs(compatibility_arguments[2], inference_arguments[1])

    def test_both_availability_validators_run_and_findings_preserve_order(self) -> None:
        runtime_options = [
            runtime("runtime::edge"),
            runtime("runtime::unused"),
        ]
        inference_options = [
            option("option::edge"),
            option("option::unused"),
        ]
        runtime_observations = [
            runtime_observation("runtime::unused"),
            runtime_observation(
                "runtime::unused",
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
            ),
            runtime_observation("runtime::missing"),
        ]
        inference_observations = [
            inference_observation("option::unused"),
            inference_observation(
                "option::unused",
                InferenceOptionAvailabilityState.UNKNOWN,
            ),
            inference_observation("option::missing"),
        ]
        expected_runtime = validate_agent_runtime_option_availability(
            runtime_observations,
            runtime_options,
        )
        expected_inference = validate_inference_option_availability(
            inference_observations,
            inference_options,
        )
        with (
            patch.object(
                assessment,
                "validate_agent_runtime_option_availability",
                wraps=validate_agent_runtime_option_availability,
            ) as runtime_validator,
            patch.object(
                assessment,
                "validate_inference_option_availability",
                wraps=validate_inference_option_availability,
            ) as inference_validator,
        ):
            result = assess_runtime_inference_pair_availability(
                [edge("runtime::edge", "option::edge")],
                runtime_options,
                inference_options,
                runtime_observations,
                inference_observations,
            )
        runtime_validator.assert_called_once()
        inference_validator.assert_called_once()
        self.assertFalse(result.valid)
        self.assertEqual(
            result.findings,
            tuple(
                RuntimeInferencePairAvailabilityFinding(
                    finding.code,
                    finding.message,
                )
                for finding in (
                    *expected_runtime.findings,
                    *expected_inference.findings,
                )
            ),
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            [
                "duplicate_agent_runtime_option_availability",
                "agent_runtime_option_not_found",
                "duplicate_inference_option_availability",
                "inference_option_not_found",
            ],
        )
        self.assertEqual(result.assessments, ())

    def test_empty_relation_still_rejects_unused_invalid_observations(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [],
            [runtime("runtime::known")],
            [option("option::known")],
            [runtime_observation("runtime::not-in-inventory")],
            [inference_observation("option::not-in-inventory")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )
        self.assertEqual(result.assessments, ())

    def test_invalid_inventory_is_atomic_and_not_an_ordinary_outcome(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [],
            [runtime("runtime::duplicate"), runtime("runtime::duplicate")],
            [option("option::duplicate"), option("option::duplicate")],
            [],
            [],
        )
        self.assertFalse(result.valid)
        self.assertNotEqual(result.findings, ())
        self.assertEqual(result.assessments, ())
        self.assertTrue(
            all(
                finding.code
                in {
                    "duplicate_agent_runtime_option_id",
                    "duplicate_inference_option_id",
                }
                for finding in result.findings
            )
        )

    def test_invalid_observation_never_returns_partial_assessments(self) -> None:
        result = assess_runtime_inference_pair_availability(
            [
                edge("runtime::alpha", "option::alpha"),
                edge("runtime::beta", "option::beta"),
            ],
            [runtime("runtime::alpha"), runtime("runtime::beta")],
            [option("option::alpha"), option("option::beta")],
            [
                runtime_observation("runtime::alpha"),
                runtime_observation("runtime::beta"),
                runtime_observation("runtime::beta"),
            ],
            [
                inference_observation("option::alpha"),
                inference_observation("option::beta"),
            ],
        )
        self.assertFalse(result.valid)
        self.assertNotEqual(result.findings, ())
        self.assertEqual(result.assessments, ())

    def test_assessment_does_not_mutate_any_caller_input(self) -> None:
        evidence = [
            edge("runtime::beta", "option::beta"),
            edge("runtime::alpha", "option::alpha"),
        ]
        runtime_options = [runtime("runtime::beta"), runtime("runtime::alpha")]
        inference_options = [option("option::beta"), option("option::alpha")]
        runtime_observations = [
            runtime_observation("runtime::beta"),
            runtime_observation(
                "runtime::alpha",
                AgentRuntimeOptionAvailabilityState.UNKNOWN,
            ),
        ]
        inference_observations = [
            inference_observation("option::beta"),
            inference_observation(
                "option::alpha",
                InferenceOptionAvailabilityState.UNAVAILABLE,
            ),
        ]
        before = tuple(
            list(items)
            for items in (
                evidence,
                runtime_options,
                inference_options,
                runtime_observations,
                inference_observations,
            )
        )
        assess_runtime_inference_pair_availability(
            evidence,
            runtime_options,
            inference_options,
            runtime_observations,
            inference_observations,
        )
        self.assertEqual(
            (
                evidence,
                runtime_options,
                inference_options,
                runtime_observations,
                inference_observations,
            ),
            before,
        )

    def test_repeated_assessment_is_deterministic_without_global_state(self) -> None:
        arguments = (
            [edge("runtime::stable", "option::stable")],
            [runtime("runtime::stable")],
            [option("option::stable")],
            [runtime_observation("runtime::stable")],
            [inference_observation("option::stable")],
        )
        first = assess_runtime_inference_pair_availability(*arguments)
        second = assess_runtime_inference_pair_availability(*arguments)
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertIsNot(first.assessments[0], second.assessments[0])

    def test_assessment_performs_no_io_network_process_clock_or_persistence_work(
        self,
    ) -> None:
        with (
            patch("builtins.open", side_effect=AssertionError("no file access")),
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("no network access"),
            ),
            patch.object(
                socket,
                "getaddrinfo",
                side_effect=AssertionError("no discovery"),
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
            patch.object(
                time,
                "time",
                side_effect=AssertionError("no clock access"),
            ),
            patch.object(
                time,
                "monotonic",
                side_effect=AssertionError("no clock access"),
            ),
            patch.object(
                sqlite3,
                "connect",
                side_effect=AssertionError("no persistence"),
            ),
        ):
            result = assess_runtime_inference_pair_availability(
                [edge("runtime::pure", "option::pure")],
                [runtime("runtime::pure")],
                [option("option::pure")],
                [],
                [],
            )
        self.assertTrue(result.valid)


class RuntimeInferencePairAvailabilityBoundaryTests(unittest.TestCase):
    def test_public_values_contain_no_selection_authority_or_aggregate_fields(
        self,
    ) -> None:
        public_fields = {
            field.name
            for public_type in (
                RuntimeInferencePairAvailabilityAssessment,
                RuntimeInferencePairAvailabilityFinding,
                RuntimeInferencePairAvailabilityResult,
            )
            for field in fields(public_type)
        }
        forbidden = {
            "assessment_id",
            "configuration_id",
            "reason",
            "priority",
            "rank",
            "source",
            "timestamp",
            "selected",
            "authorized",
            "reserved",
            "actor_id",
            "task_id",
            "assignment_id",
            "execution_mode",
            "preferred_pair",
            "has_available_pair",
            "established_assessments",
            "blocked_assessments",
            "unresolved_assessments",
            "metadata",
            "extensions",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_module_imports_only_the_five_composed_domain_contracts(self) -> None:
        tree = ast.parse(
            (
                ROOT
                / "engineering_orchestration"
                / "runtime_inference_pair_availability.py"
            ).read_text(encoding="utf-8")
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
                "engineering_orchestration.agent_runtime_option_availability",
                "engineering_orchestration.inference_option",
                "engineering_orchestration.inference_option_availability",
                "engineering_orchestration.runtime_inference_compatibility",
            },
        )

    def test_no_actor_selection_authorization_adapter_or_invocation_api_exists(
        self,
    ) -> None:
        forbidden = {
            "Actor",
            "ActorSelection",
            "Assignment",
            "ExecutionConfiguration",
            "ExecutionContract",
            "AgentService",
            "select_pair",
            "select_runtime",
            "select_inference_option",
            "rank_pairs",
            "route",
            "authorize",
            "reserve",
            "dispatch",
            "invoke",
            "persist",
            "refresh",
            "poll",
        }
        self.assertTrue(all(not hasattr(assessment, name) for name in forbidden))

    def test_no_new_schema_storage_or_package_root_reexport_exists(self) -> None:
        self.assertFalse(
            (
                ROOT
                / "schemas"
                / "runtime-inference-pair-availability.schema.json"
            ).exists()
        )
        for relative in (
            ".ai/runtime-inference-pair-availability",
            ".ai/runtime-inference-pair-availability.yaml",
            ".ai/execution-configurations",
        ):
            self.assertFalse((ROOT / relative).exists())
        for name in (
            "RuntimeInferencePairAvailabilityOutcome",
            "RuntimeInferencePairAvailabilityAssessment",
            "RuntimeInferencePairAvailabilityFinding",
            "RuntimeInferencePairAvailabilityResult",
            "assess_runtime_inference_pair_availability",
        ):
            self.assertFalse(hasattr(engineering_orchestration, name))

    def test_established_result_exposes_evidence_not_selection_or_authority(
        self,
    ) -> None:
        result = assess_runtime_inference_pair_availability(
            [edge("runtime::available", "option::available")],
            [runtime("runtime::available")],
            [option("option::available")],
            [runtime_observation("runtime::available")],
            [inference_observation("option::available")],
        )
        self.assertEqual(
            result.assessments[0].outcome,
            RuntimeInferencePairAvailabilityOutcome.ESTABLISHED,
        )
        for name in (
            "selected",
            "authorized",
            "executable",
            "reserved",
            "actor_id",
            "task_id",
            "execution_mode",
            "execution_contract",
            "invocation",
        ):
            self.assertFalse(hasattr(result, name))
            self.assertFalse(hasattr(result.assessments[0], name))


if __name__ == "__main__":
    unittest.main()
