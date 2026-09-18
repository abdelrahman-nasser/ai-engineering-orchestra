"""Focused Actor Availability Observation runtime and boundary tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.actor_availability import (
    ActorAvailabilityFinding,
    ActorAvailabilityObservation,
    ActorAvailabilityValidationResult,
    AvailabilityState,
    validate_actor_availability,
)
from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.assignment import Assignment, validate_assignment
from engineering_orchestration.role_catalog import load_role_catalog
from engineering_orchestration.workflow_catalog import load_workflow_catalog


ROOT = Path(__file__).resolve().parents[1]


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


def observation(
    actor_id: str,
    state: AvailabilityState = AvailabilityState.AVAILABLE,
) -> ActorAvailabilityObservation:
    return ActorAvailabilityObservation(actor_id=actor_id, state=state)


class TrackingActor(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessed: list[str] = []

    def __getitem__(self, key):
        self.accessed.append(key)
        return super().__getitem__(key)


class ExplodingObservation:
    @property
    def actor_id(self):
        raise AssertionError("observations must not be inspected")


class ActorAvailabilityValueTests(unittest.TestCase):
    def test_state_values_are_exactly_the_closed_contract(self):
        self.assertEqual(
            [state.value for state in AvailabilityState],
            ["available", "unavailable", "unknown"],
        )

    def test_unknown_is_distinct_from_unavailable(self):
        self.assertIsNot(AvailabilityState.UNKNOWN, AvailabilityState.UNAVAILABLE)
        self.assertNotEqual(AvailabilityState.UNKNOWN, AvailabilityState.UNAVAILABLE)

    def test_observation_has_exactly_two_fields_and_is_frozen(self):
        supplied = observation("actor-1")
        self.assertEqual(
            [item.name for item in fields(ActorAvailabilityObservation)],
            ["actor_id", "state"],
        )
        with self.assertRaises(FrozenInstanceError):
            supplied.state = AvailabilityState.UNAVAILABLE

    def test_finding_and_result_are_frozen_and_tuple_backed(self):
        finding = ActorAvailabilityFinding("example", "Example")
        result = ActorAvailabilityValidationResult(False, (finding,), ())
        self.assertEqual(
            [item.name for item in fields(ActorAvailabilityValidationResult)],
            ["valid", "findings", "normalized_observations"],
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_observations, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "other"
        with self.assertRaises(FrozenInstanceError):
            result.valid = True


class ActorAvailabilityValidationTests(unittest.TestCase):
    def test_available_observation_for_known_actor(self):
        result = validate_actor_availability(
            [observation("actor-1", AvailabilityState.AVAILABLE)],
            [actor("actor-1")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_observations, (
            observation("actor-1", AvailabilityState.AVAILABLE),
        ))

    def test_unavailable_observation_for_known_actor(self):
        result = validate_actor_availability(
            [observation("actor-1", AvailabilityState.UNAVAILABLE)],
            [actor("actor-1")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_observations[0].state,
            AvailabilityState.UNAVAILABLE,
        )

    def test_unknown_observation_for_known_actor(self):
        result = validate_actor_availability(
            [observation("actor-1", AvailabilityState.UNKNOWN)],
            [actor("actor-1")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_observations[0].state,
            AvailabilityState.UNKNOWN,
        )

    def test_human_and_agent_use_the_same_semantics(self):
        actors = [actor("human-1", kind="human"), actor("agent-1", kind="agent")]
        result = validate_actor_availability(
            [
                observation("human-1", AvailabilityState.AVAILABLE),
                observation("agent-1", AvailabilityState.AVAILABLE),
            ],
            actors,
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [(item.actor_id, item.state) for item in result.normalized_observations],
            [
                ("agent-1", AvailabilityState.AVAILABLE),
                ("human-1", AvailabilityState.AVAILABLE),
            ],
        )

    def test_missing_observation_normalizes_to_unknown_never_unavailable(self):
        result = validate_actor_availability([], [actor("actor-1")])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_observations, (
            observation("actor-1", AvailabilityState.UNKNOWN),
        ))
        self.assertNotEqual(
            result.normalized_observations[0].state,
            AvailabilityState.UNAVAILABLE,
        )

    def test_missing_and_explicit_unknown_normalize_equivalently(self):
        actors = [actor("actor-1")]
        missing = validate_actor_availability([], actors)
        explicit = validate_actor_availability(
            [observation("actor-1", AvailabilityState.UNKNOWN)],
            actors,
        )
        self.assertEqual(
            missing.normalized_observations,
            explicit.normalized_observations,
        )

    def test_normalized_output_is_sorted_by_actor_id(self):
        result = validate_actor_availability(
            [
                observation("z-actor", AvailabilityState.UNAVAILABLE),
                observation("m-actor", AvailabilityState.AVAILABLE),
            ],
            [actor("z-actor"), actor("a-actor"), actor("m-actor")],
        )
        self.assertEqual(
            [item.actor_id for item in result.normalized_observations],
            ["a-actor", "m-actor", "z-actor"],
        )
        self.assertEqual(
            [item.state for item in result.normalized_observations],
            [
                AvailabilityState.UNKNOWN,
                AvailabilityState.AVAILABLE,
                AvailabilityState.UNAVAILABLE,
            ],
        )

    def test_empty_context_is_valid_and_deterministic(self):
        result = validate_actor_availability([], [])
        self.assertEqual(result, ActorAvailabilityValidationResult(True, (), ()))

    def test_unknown_actor_is_invalid_and_does_not_create_actor(self):
        result = validate_actor_availability(
            [observation("missing")],
            [actor("known")],
        )
        self.assertFalse(result.valid)
        self.assertEqual([item.code for item in result.findings], ["actor_not_found"])
        self.assertIn("missing", result.findings[0].message)
        self.assertEqual(result.normalized_observations, ())

    def test_unknown_actor_findings_are_sorted_and_deduplicated(self):
        result = validate_actor_availability(
            [observation("z-missing"), observation("a-missing")],
            [],
        )
        self.assertEqual(
            [item.message for item in result.findings],
            [
                "Actor 'a-missing' was not found in the supplied Actor context.",
                "Actor 'z-missing' was not found in the supplied Actor context.",
            ],
        )

    def test_duplicate_actor_ids_short_circuit_before_observations(self):
        duplicate = actor("same")
        result = validate_actor_availability(
            [ExplodingObservation()],  # type: ignore[list-item]
            [duplicate, dict(duplicate)],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [item.code for item in result.findings],
            ["duplicate_actor_id"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_duplicate_actor_id_message_is_sorted(self):
        result = validate_actor_availability(
            [],
            [actor("z"), actor("a"), actor("z"), actor("a")],
        )
        self.assertEqual(
            result.findings,
            (ActorAvailabilityFinding(
                "duplicate_actor_id",
                "Actor IDs must be unique in the supplied context; duplicates: a, z",
            ),),
        )

    def test_identical_duplicate_observations_are_rejected(self):
        duplicate = observation("actor-1")
        result = validate_actor_availability(
            [duplicate, duplicate],
            [actor("actor-1")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [item.code for item in result.findings],
            ["duplicate_actor_availability"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_conflicting_duplicates_are_not_resolved_by_order(self):
        available = observation("actor-1", AvailabilityState.AVAILABLE)
        unavailable = observation("actor-1", AvailabilityState.UNAVAILABLE)
        forward = validate_actor_availability(
            [available, unavailable],
            [actor("actor-1")],
        )
        reverse = validate_actor_availability(
            [unavailable, available],
            [actor("actor-1")],
        )
        self.assertEqual(forward, reverse)
        self.assertFalse(forward.valid)
        self.assertEqual(
            [item.code for item in forward.findings],
            ["duplicate_actor_availability"],
        )
        self.assertEqual(forward.normalized_observations, ())

    def test_duplicate_and_unknown_findings_have_deterministic_order(self):
        result = validate_actor_availability(
            [
                observation("z-missing", AvailabilityState.AVAILABLE),
                observation("a-known", AvailabilityState.AVAILABLE),
                observation("z-missing", AvailabilityState.UNKNOWN),
                observation("a-known", AvailabilityState.UNAVAILABLE),
            ],
            [actor("a-known")],
        )
        self.assertEqual(
            [(item.code, item.message) for item in result.findings],
            [
                (
                    "duplicate_actor_availability",
                    "Actor 'a-known' has more than one supplied availability "
                    "observation.",
                ),
                (
                    "duplicate_actor_availability",
                    "Actor 'z-missing' has more than one supplied availability "
                    "observation.",
                ),
                (
                    "actor_not_found",
                    "Actor 'z-missing' was not found in the supplied Actor context.",
                ),
            ],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_only_actor_identity_is_read_from_actor_context(self):
        supplied = TrackingActor(actor("actor-1", competencies=["anything"]))
        result = validate_actor_availability([], [supplied])
        self.assertTrue(result.valid)
        self.assertEqual(supplied.accessed, ["id"])

    def test_inputs_and_actor_identity_are_not_mutated(self):
        for state in (AvailabilityState.UNAVAILABLE, AvailabilityState.UNKNOWN):
            with self.subTest(state=state):
                actors = [actor("actor-1", kind="human", competencies=["review"])]
                observations = [observation("actor-1", state)]
                actor_before = {
                    "id": actors[0]["id"],
                    "kind": actors[0]["kind"],
                    "competencies": list(actors[0]["competencies"]),
                }
                observations_before = list(observations)
                validate_actor_availability(observations, actors)
                self.assertEqual(actors[0], actor_before)
                self.assertEqual(observations, observations_before)


class ActorAvailabilityBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roles = load_role_catalog()
        cls.workflows = load_workflow_catalog(ROOT / "workflows")
        if not cls.roles.is_valid:
            raise AssertionError(cls.roles.load_errors)
        if not cls.workflows.is_valid:
            raise AssertionError(cls.workflows.load_errors)

    def test_available_does_not_imply_competency_eligibility(self):
        supplied_actor = actor("actor-1", competencies=["source-code-analysis"])
        role = self.roles.get("software-engineer")
        availability = validate_actor_availability(
            [observation("actor-1", AvailabilityState.AVAILABLE)],
            [supplied_actor],
        )
        coverage = evaluate_actor_role_coverage(supplied_actor, role)
        self.assertTrue(availability.valid)
        self.assertEqual(
            availability.normalized_observations[0].state,
            AvailabilityState.AVAILABLE,
        )
        self.assertFalse(coverage.compatible)

    def test_unavailable_does_not_change_competency_coverage(self):
        role = self.roles.get("software-engineer")
        supplied_actor = actor(
            "actor-1",
            competencies=role["required_capabilities"],
        )
        availability = validate_actor_availability(
            [observation("actor-1", AvailabilityState.UNAVAILABLE)],
            [supplied_actor],
        )
        coverage = evaluate_actor_role_coverage(supplied_actor, role)
        self.assertTrue(availability.valid)
        self.assertTrue(coverage.compatible)

    def test_assignment_validity_is_independent_from_unavailability(self):
        role = self.roles.get("software-engineer")
        supplied_actor = actor(
            "engineer-1",
            competencies=role["required_capabilities"],
        )
        availability = validate_actor_availability(
            [observation("engineer-1", AvailabilityState.UNAVAILABLE)],
            [supplied_actor],
        )
        assignment = Assignment(
            task_id="AIO-024",
            workflow_id="architecture-change",
            stage_id="implement",
            role_id="software-engineer",
            actor_id="engineer-1",
        )
        assignment_result = validate_assignment(
            assignment,
            {"id": "AIO-024", "workflow": "architecture-change"},
            self.workflows,
            self.roles,
            [supplied_actor],
        )
        self.assertTrue(availability.valid)
        self.assertTrue(assignment_result.valid)

    def test_available_produces_no_assignment_selection_or_authority(self):
        result = validate_actor_availability(
            [observation("actor-1")],
            [actor("actor-1")],
        )
        names = {item.name for item in fields(ActorAvailabilityValidationResult)}
        self.assertTrue(names.isdisjoint({
            "assignment", "assigned", "selected", "selection", "rank",
            "recommendation", "permission", "authorized", "authority",
            "execution", "executing", "quality_gate",
        }))

    def test_human_availability_grants_no_approval(self):
        result = validate_actor_availability(
            [observation("human-1")],
            [actor("human-1", kind="human")],
        )
        self.assertTrue(result.valid)
        self.assertFalse(hasattr(result, "approval"))
        self.assertFalse(hasattr(result, "approval_authority"))

    def test_agent_availability_grants_no_execution_authority(self):
        result = validate_actor_availability(
            [observation("agent-1")],
            [actor("agent-1", kind="agent")],
        )
        self.assertTrue(result.valid)
        self.assertFalse(hasattr(result, "execution"))
        self.assertFalse(hasattr(result, "execution_authority"))

    def test_validation_performs_no_io_network_polling_or_persistence(self):
        with patch("builtins.open", side_effect=AssertionError("file I/O")), \
                patch.object(Path, "write_text", side_effect=AssertionError("write")), \
                patch.object(socket, "create_connection",
                             side_effect=AssertionError("network")), \
                patch.object(urllib.request, "urlopen",
                             side_effect=AssertionError("network")), \
                patch.object(subprocess, "run",
                             side_effect=AssertionError("process")):
            result = validate_actor_availability(
                [observation("actor-1")],
                [actor("actor-1")],
            )
        self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main()
