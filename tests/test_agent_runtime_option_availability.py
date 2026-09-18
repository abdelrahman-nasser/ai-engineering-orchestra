"""Focused Agent Runtime Option Availability runtime and boundary tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from inspect import signature
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
)
from engineering_orchestration.actor_selection import (
    ActorSelectionOutcome,
    select_actor,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityFinding,
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
    AgentRuntimeOptionAvailabilityValidationResult,
    validate_agent_runtime_option_availability,
)
from engineering_orchestration.assignment import Assignment, validate_assignment
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
    validate_inference_option_availability,
)
from engineering_orchestration.role_catalog import load_role_catalog
from engineering_orchestration.schema_resources import load_validator
from engineering_orchestration.workflow_catalog import load_workflow_catalog


ROOT = Path(__file__).resolve().parents[1]


def runtime_option(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def observation(
    runtime_option_id: str,
    state: AgentRuntimeOptionAvailabilityState = (
        AgentRuntimeOptionAvailabilityState.AVAILABLE
    ),
) -> AgentRuntimeOptionAvailabilityObservation:
    return AgentRuntimeOptionAvailabilityObservation(runtime_option_id, state)


def actor(
    actor_id: str,
    *,
    kind: str = "agent",
    competencies=(),
) -> dict[str, object]:
    return {
        "id": actor_id,
        "kind": kind,
        "competencies": list(competencies),
    }


class ExplodingObservation:
    @property
    def runtime_option_id(self):
        raise AssertionError("observations must not be inspected")


class AgentRuntimeOptionAvailabilityValueTests(unittest.TestCase):
    def test_state_values_are_exactly_the_closed_contract(self) -> None:
        self.assertEqual(
            [state.value for state in AgentRuntimeOptionAvailabilityState],
            ["available", "unavailable", "unknown"],
        )

    def test_unknown_is_distinct_from_unavailable(self) -> None:
        self.assertNotEqual(
            AgentRuntimeOptionAvailabilityState.UNKNOWN,
            AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
        )

    def test_observation_has_exactly_two_fields_and_is_frozen(self) -> None:
        supplied = observation("primary")
        self.assertEqual(
            [field.name for field in fields(supplied)],
            ["runtime_option_id", "state"],
        )
        with self.assertRaises(FrozenInstanceError):
            supplied.state = (  # type: ignore[misc]
                AgentRuntimeOptionAvailabilityState.UNKNOWN
            )

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = AgentRuntimeOptionAvailabilityFinding("example", "message")
        result = AgentRuntimeOptionAvailabilityValidationResult(
            False,
            (finding,),
            (),
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_observations, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_schema_authorizes_exact_two_field_contract_and_three_states(self) -> None:
        schema = load_validator(
            "agent-runtime-option-availability.schema.json"
        ).schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["runtime_option_id", "state"])
        self.assertEqual(
            set(schema["properties"]),
            {"runtime_option_id", "state"},
        )
        self.assertEqual(
            schema["properties"]["state"]["enum"],
            ["available", "unavailable", "unknown"],
        )


class AgentRuntimeOptionAvailabilityValidationTests(unittest.TestCase):
    def assert_state(
        self,
        state: AgentRuntimeOptionAvailabilityState,
    ) -> None:
        supplied = observation("primary", state)
        result = validate_agent_runtime_option_availability(
            [supplied],
            [runtime_option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_observations, (supplied,))

    def test_known_runtime_available(self) -> None:
        self.assert_state(AgentRuntimeOptionAvailabilityState.AVAILABLE)

    def test_known_runtime_unavailable(self) -> None:
        self.assert_state(AgentRuntimeOptionAvailabilityState.UNAVAILABLE)

    def test_known_runtime_unknown(self) -> None:
        self.assert_state(AgentRuntimeOptionAvailabilityState.UNKNOWN)

    def test_missing_observation_normalizes_to_unknown_never_unavailable(self) -> None:
        result = validate_agent_runtime_option_availability(
            [],
            [runtime_option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_observations,
            (
                observation(
                    "primary",
                    AgentRuntimeOptionAvailabilityState.UNKNOWN,
                ),
            ),
        )
        self.assertNotEqual(
            result.normalized_observations[0].state,
            AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
        )

    def test_missing_and_explicit_unknown_normalize_equivalently(self) -> None:
        options = [runtime_option("primary")]
        missing = validate_agent_runtime_option_availability([], options)
        explicit = validate_agent_runtime_option_availability(
            [observation("primary", AgentRuntimeOptionAvailabilityState.UNKNOWN)],
            options,
        )
        self.assertEqual(missing, explicit)

    def test_normalized_output_is_sorted_by_runtime_option_id(self) -> None:
        result = validate_agent_runtime_option_availability(
            [
                observation(
                    "z",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                ),
                observation("A", AgentRuntimeOptionAvailabilityState.AVAILABLE),
            ],
            [runtime_option("z"), runtime_option("a"), runtime_option("A")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [item.runtime_option_id for item in result.normalized_observations],
            ["A", "a", "z"],
        )
        self.assertEqual(
            result.normalized_observations[1].state,
            AgentRuntimeOptionAvailabilityState.UNKNOWN,
        )

    def test_empty_inventory_and_observations_are_valid(self) -> None:
        self.assertEqual(
            validate_agent_runtime_option_availability([], []),
            AgentRuntimeOptionAvailabilityValidationResult(True, (), ()),
        )

    def test_unknown_runtime_is_invalid_and_does_not_create_option(self) -> None:
        result = validate_agent_runtime_option_availability(
            [observation("missing")],
            [runtime_option("known")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(result.normalized_observations, ())
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found"],
        )

    def test_unknown_findings_are_sorted_and_deduplicated(self) -> None:
        result = validate_agent_runtime_option_availability(
            [observation("z"), observation("a")],
            [],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found", "agent_runtime_option_not_found"],
        )
        self.assertIn("'a'", result.findings[0].message)
        self.assertIn("'z'", result.findings[1].message)

    def test_duplicate_inventory_short_circuits_observations(self) -> None:
        result = validate_agent_runtime_option_availability(
            [ExplodingObservation()],  # type: ignore[list-item]
            [runtime_option("duplicate"), runtime_option("duplicate")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_id"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_identical_duplicate_observations_are_rejected(self) -> None:
        result = validate_agent_runtime_option_availability(
            [observation("primary"), observation("primary")],
            [runtime_option("primary")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_availability"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_conflicting_duplicates_are_not_resolved_by_order(self) -> None:
        available = observation("primary")
        unavailable = observation(
            "primary",
            AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
        )
        forward = validate_agent_runtime_option_availability(
            [available, unavailable],
            [runtime_option("primary")],
        )
        reverse = validate_agent_runtime_option_availability(
            [unavailable, available],
            [runtime_option("primary")],
        )
        self.assertEqual(forward, reverse)
        self.assertFalse(forward.valid)

    def test_duplicate_findings_precede_unknown_findings_deterministically(self) -> None:
        supplied = [
            observation("z-missing"),
            observation("a-missing"),
            observation("z-missing"),
            observation("known"),
            observation("known", AgentRuntimeOptionAvailabilityState.UNKNOWN),
        ]
        forward = validate_agent_runtime_option_availability(
            supplied,
            [runtime_option("known")],
        )
        reverse = validate_agent_runtime_option_availability(
            list(reversed(supplied)),
            [runtime_option("known")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_agent_runtime_option_availability",
                "duplicate_agent_runtime_option_availability",
                "agent_runtime_option_not_found",
                "agent_runtime_option_not_found",
            ],
        )
        self.assertEqual(forward.normalized_observations, ())

    def test_validation_does_not_mutate_definition_or_observation_inputs(self) -> None:
        options = [runtime_option("b"), runtime_option("a")]
        observations = [observation("b")]
        options_before = list(options)
        observations_before = list(observations)
        validate_agent_runtime_option_availability(observations, options)
        self.assertEqual(options, options_before)
        self.assertEqual(observations, observations_before)

    def test_validation_performs_no_io_network_polling_or_process_work(self) -> None:
        with (
            patch("builtins.open", side_effect=AssertionError("no file access")),
            patch.object(
                Path,
                "write_text",
                side_effect=AssertionError("no persistence"),
            ),
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
            result = validate_agent_runtime_option_availability(
                [],
                [runtime_option("primary")],
            )
        self.assertTrue(result.valid)


class AgentRuntimeOptionAvailabilityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.roles = load_role_catalog()
        cls.workflows = load_workflow_catalog(ROOT / "workflows")
        if not cls.roles.is_valid:
            raise AssertionError(cls.roles.load_errors)
        if not cls.workflows.is_valid:
            raise AssertionError(cls.workflows.load_errors)

    def compatible_actor(
        self,
        actor_id: str,
        *,
        kind: str = "agent",
    ) -> dict[str, object]:
        role = self.roles.get("software-engineer")
        return actor(
            actor_id,
            kind=kind,
            competencies=role["required_capabilities"],
        )

    def test_availability_never_changes_runtime_identity(self) -> None:
        definition = runtime_option("primary")
        result = validate_agent_runtime_option_availability(
            [observation("primary")],
            [definition],
        )
        self.assertTrue(result.valid)
        self.assertEqual(definition, runtime_option("primary"))

    def test_available_contains_no_compatibility_authorization_or_execution(self) -> None:
        result = validate_agent_runtime_option_availability(
            [observation("primary")],
            [runtime_option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [field.name for field in fields(result.normalized_observations[0])],
            ["runtime_option_id", "state"],
        )
        forbidden = {
            "actor_compatible",
            "inference_option_available",
            "compatible",
            "selected",
            "authorized",
            "executing",
            "execution_mode",
            "actor_id",
            "option_id",
            "provider_id",
            "model_id",
        }
        self.assertTrue(
            forbidden.isdisjoint(
                field.name for field in fields(result.normalized_observations[0])
            )
        )

    def test_availability_schema_has_no_actor_inference_or_capability_fields(self) -> None:
        schema = load_validator(
            "agent-runtime-option-availability.schema.json"
        ).schema
        forbidden = {
            "actor_id",
            "option_id",
            "provider_id",
            "model_id",
            "compatible",
            "authorized",
            "executing",
            "tools",
            "mcp",
            "capacity",
            "state_owner",
            "session_owner",
        }
        self.assertTrue(forbidden.isdisjoint(schema["properties"]))

    def test_runtime_availability_does_not_affect_actor_identity_or_competency(self) -> None:
        supplied_actor = self.compatible_actor("agent-1")
        before = {
            "id": supplied_actor["id"],
            "kind": supplied_actor["kind"],
            "competencies": list(supplied_actor["competencies"]),
        }
        result = validate_agent_runtime_option_availability(
            [
                observation(
                    "primary",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            [runtime_option("primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(supplied_actor, before)

    def test_runtime_availability_does_not_alter_assignment(self) -> None:
        supplied_actor = self.compatible_actor("agent-1")
        runtime_availability = validate_agent_runtime_option_availability(
            [
                observation(
                    "primary",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            [runtime_option("primary")],
        )
        assignment = Assignment(
            task_id="AIO-029",
            workflow_id="architecture-change",
            stage_id="implement",
            role_id="software-engineer",
            actor_id="agent-1",
        )
        assignment_result = validate_assignment(
            assignment,
            {"id": "AIO-029", "workflow": "architecture-change"},
            self.workflows,
            self.roles,
            [supplied_actor],
        )
        self.assertTrue(runtime_availability.valid)
        self.assertTrue(assignment_result.valid)

    def test_runtime_availability_does_not_alter_actor_selection(self) -> None:
        supplied_actor = self.compatible_actor("agent-1")
        runtime_availability = validate_agent_runtime_option_availability(
            [
                observation(
                    "primary",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            [runtime_option("primary")],
        )
        selection = select_actor(
            {"id": "AIO-029", "workflow": "architecture-change"},
            "implement",
            "software-engineer",
            self.workflows,
            self.roles,
            [supplied_actor],
            [ActorAvailabilityObservation("agent-1", AvailabilityState.AVAILABLE)],
        )
        self.assertTrue(runtime_availability.valid)
        self.assertEqual(selection.outcome, ActorSelectionOutcome.SELECTED)
        self.assertEqual(selection.selected_actor_id, "agent-1")
        self.assertNotIn(
            "runtime",
            " ".join(signature(select_actor).parameters).lower(),
        )

    def test_human_actor_selection_requires_no_runtime_option(self) -> None:
        supplied_actor = self.compatible_actor("human-1", kind="human")
        selection = select_actor(
            {"id": "AIO-029", "workflow": "architecture-change"},
            "implement",
            "software-engineer",
            self.workflows,
            self.roles,
            [supplied_actor],
            [ActorAvailabilityObservation("human-1", AvailabilityState.AVAILABLE)],
        )
        self.assertEqual(selection.outcome, ActorSelectionOutcome.SELECTED)
        self.assertEqual(selection.selected_actor_id, "human-1")

    def test_runtime_available_does_not_imply_inference_available(self) -> None:
        runtime_result = validate_agent_runtime_option_availability(
            [observation("primary")],
            [runtime_option("primary")],
        )
        inference_result = validate_inference_option_availability(
            [
                InferenceOptionAvailabilityObservation(
                    "inference-primary",
                    InferenceOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            [
                InferenceOptionDefinition(
                    "inference-primary",
                    "provider-a",
                    "model-x",
                )
            ],
        )
        self.assertEqual(
            runtime_result.normalized_observations[0].state,
            AgentRuntimeOptionAvailabilityState.AVAILABLE,
        )
        self.assertEqual(
            inference_result.normalized_observations[0].state,
            InferenceOptionAvailabilityState.UNAVAILABLE,
        )

    def test_no_runtime_to_inference_relation_or_selection_is_produced(self) -> None:
        result = validate_agent_runtime_option_availability(
            [observation("primary")],
            [runtime_option("primary")],
        )
        result_fields = {field.name for field in fields(result)}
        self.assertEqual(
            result_fields,
            {"valid", "findings", "normalized_observations"},
        )
        self.assertTrue(
            {
                "compatible_option_ids",
                "inference_option_ids",
                "selected_runtime_option_id",
                "selected_option_id",
                "execution_configuration",
                "execution_contract",
                "invocation",
            }.isdisjoint(result_fields)
        )


if __name__ == "__main__":
    unittest.main()
