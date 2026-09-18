"""Focused deterministic Actor Selection contract tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import inspect
from pathlib import Path
import random
import socket
import time
import unittest
import urllib.request
from unittest.mock import patch

from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
)
from engineering_orchestration.actor_selection import (
    ActorSelectionFinding,
    ActorSelectionOutcome,
    ActorSelectionReason,
    ActorSelectionResult,
    select_actor,
)
from engineering_orchestration.assignment import Assignment, validate_assignment
from engineering_orchestration.role_catalog import (
    RoleCatalog,
    RoleCatalogError,
    load_role_catalog,
)
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowCatalogError,
    WorkflowDefinition,
    WorkflowStage,
    load_workflow_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
TASK = {"id": "AIO-025", "workflow": "architecture-change"}


def actor(actor_id: str, competencies, *, kind: str = "agent") -> dict[str, object]:
    return {
        "id": actor_id,
        "kind": kind,
        "competencies": list(competencies),
    }


def observation(
    actor_id: str,
    state: AvailabilityState,
) -> ActorAvailabilityObservation:
    return ActorAvailabilityObservation(actor_id, state)


def workflow_catalog(*stages: WorkflowStage) -> WorkflowCatalog:
    definition = WorkflowDefinition(
        id="architecture-change",
        name="Architecture Change",
        purpose="Test Actor Selection semantics.",
        stages=list(stages),
    )
    return WorkflowCatalog(
        workflows_dir=Path("unused"),
        definitions={definition.id: definition},
    )


def role_catalog(*definitions: dict[str, object]) -> RoleCatalog:
    return RoleCatalog(
        roles_source=None,
        definitions={str(item["id"]): item for item in definitions},
    )


class TrackingMapping(dict):
    """Mapping that records accessed keys without changing mapping behavior."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessed: list[str] = []

    def __getitem__(self, key):
        self.accessed.append(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.accessed.append(key)
        return super().get(key, default)


class ActorSelectionFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflows = load_workflow_catalog(ROOT / "workflows")
        cls.roles = load_role_catalog()
        if not cls.workflows.is_valid:
            raise AssertionError(cls.workflows.load_errors)
        if not cls.roles.is_valid:
            raise AssertionError(cls.roles.load_errors)
        cls.engineer_role = cls.roles.get("software-engineer")
        if cls.engineer_role is None:
            raise AssertionError("software-engineer Role missing")
        cls.engineer_competencies = tuple(
            cls.engineer_role["required_capabilities"]
        )

    def compatible(self, actor_id: str, *, kind: str = "agent"):
        return actor(actor_id, self.engineer_competencies, kind=kind)

    @staticmethod
    def incompatible(actor_id: str, *, kind: str = "agent"):
        return actor(actor_id, ["unrelated-competency"], kind=kind)

    def select(
        self,
        actors=(),
        observations=(),
        *,
        task=None,
        stage_id="implement",
        role_id="software-engineer",
        workflows=None,
        roles=None,
    ) -> ActorSelectionResult:
        return select_actor(
            TASK if task is None else task,
            stage_id,
            role_id,
            self.workflows if workflows is None else workflows,
            self.roles if roles is None else roles,
            list(actors),
            list(observations),
        )


class ActorSelectionValueTests(ActorSelectionFixture):
    def test_outcome_values_are_exactly_the_closed_contract(self):
        self.assertEqual(
            {item.value for item in ActorSelectionOutcome},
            {"selected", "ambiguous", "indeterminate", "no_candidate"},
        )

    def test_reason_values_are_exactly_the_closed_contract(self):
        self.assertEqual(
            {item.value for item in ActorSelectionReason},
            {
                "unique_available_actor",
                "multiple_available_actors",
                "availability_unknown",
                "candidate_set_empty",
                "no_eligible_actor",
                "all_eligible_unavailable",
            },
        )

    def test_result_has_exactly_the_canonical_fields(self):
        self.assertEqual(
            [field.name for field in fields(ActorSelectionResult)],
            [
                "valid",
                "responsibility_key",
                "outcome",
                "reason",
                "selected_actor_id",
                "eligible_actor_ids",
                "available_actor_ids",
                "unknown_actor_ids",
                "findings",
            ],
        )

    def test_result_and_finding_are_frozen_and_tuple_backed(self):
        finding = ActorSelectionFinding("example", "Example")
        result = ActorSelectionResult(
            False, None, None, None, None, (), (), (), (finding,)
        )
        for value in (
            result.eligible_actor_ids,
            result.available_actor_ids,
            result.unknown_actor_ids,
            result.findings,
        ):
            self.assertIsInstance(value, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "other"
        with self.assertRaises(FrozenInstanceError):
            result.valid = True

    def test_valid_result_has_responsibility_key_and_no_findings(self):
        result = self.select()
        self.assertTrue(result.valid)
        self.assertEqual(
            result.responsibility_key,
            ("AIO-025", "architecture-change", "implement", "software-engineer"),
        )
        self.assertEqual(result.findings, ())


class ActorSelectionOutcomeTests(ActorSelectionFixture):
    def test_empty_actor_set_is_no_candidate(self):
        result = self.select()
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertEqual(result.reason, ActorSelectionReason.CANDIDATE_SET_EMPTY)

    def test_nonempty_set_with_no_eligible_actor_is_no_candidate(self):
        result = self.select([self.incompatible("incapable")])
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertEqual(result.reason, ActorSelectionReason.NO_ELIGIBLE_ACTOR)
        self.assertEqual(result.eligible_actor_ids, ())

    def test_one_eligible_unavailable_is_no_candidate(self):
        candidate = self.compatible("A")
        result = self.select(
            [candidate], [observation("A", AvailabilityState.UNAVAILABLE)]
        )
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertEqual(
            result.reason, ActorSelectionReason.ALL_ELIGIBLE_UNAVAILABLE
        )

    def test_one_eligible_unknown_is_indeterminate(self):
        candidate = self.compatible("A")
        result = self.select(
            [candidate], [observation("A", AvailabilityState.UNKNOWN)]
        )
        self.assertEqual(result.outcome, ActorSelectionOutcome.INDETERMINATE)
        self.assertEqual(result.reason, ActorSelectionReason.AVAILABILITY_UNKNOWN)
        self.assertIsNone(result.selected_actor_id)

    def test_one_eligible_available_is_selected(self):
        candidate = self.compatible("A")
        result = self.select(
            [candidate], [observation("A", AvailabilityState.AVAILABLE)]
        )
        self.assertEqual(result.outcome, ActorSelectionOutcome.SELECTED)
        self.assertEqual(result.reason, ActorSelectionReason.UNIQUE_AVAILABLE_ACTOR)
        self.assertEqual(result.selected_actor_id, "A")

    def test_two_eligible_available_are_ambiguous(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.AVAILABLE),
            observation("B", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.AMBIGUOUS)
        self.assertEqual(
            result.reason, ActorSelectionReason.MULTIPLE_AVAILABLE_ACTORS
        )
        self.assertIsNone(result.selected_actor_id)

    def test_available_plus_unavailable_is_selected(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.AVAILABLE),
            observation("B", AvailabilityState.UNAVAILABLE),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.SELECTED)
        self.assertEqual(result.selected_actor_id, "A")

    def test_available_plus_unknown_is_indeterminate_critical_case(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.AVAILABLE),
            observation("B", AvailabilityState.UNKNOWN),
        ])
        self.assertTrue(result.valid)
        self.assertEqual(result.outcome, ActorSelectionOutcome.INDETERMINATE)
        self.assertIsNone(result.selected_actor_id)
        self.assertEqual(result.available_actor_ids, ("A",))
        self.assertEqual(result.unknown_actor_ids, ("B",))

    def test_two_unavailable_are_no_candidate(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.UNAVAILABLE),
            observation("B", AvailabilityState.UNAVAILABLE),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertEqual(
            result.reason, ActorSelectionReason.ALL_ELIGIBLE_UNAVAILABLE
        )

    def test_unavailable_plus_unknown_is_indeterminate(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.UNAVAILABLE),
            observation("B", AvailabilityState.UNKNOWN),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.INDETERMINATE)

    def test_two_unknown_are_indeterminate(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.UNKNOWN),
            observation("B", AvailabilityState.UNKNOWN),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.INDETERMINATE)
        self.assertEqual(result.unknown_actor_ids, ("A", "B"))

    def test_two_available_plus_unknown_is_ambiguous_with_unknown_evidence(self):
        candidates = [
            self.compatible("A"), self.compatible("B"), self.compatible("C")
        ]
        result = self.select(candidates, [
            observation("A", AvailabilityState.AVAILABLE),
            observation("B", AvailabilityState.AVAILABLE),
            observation("C", AvailabilityState.UNKNOWN),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.AMBIGUOUS)
        self.assertEqual(result.available_actor_ids, ("A", "B"))
        self.assertEqual(result.unknown_actor_ids, ("C",))

    def test_incompatible_available_actor_is_ignored(self):
        candidates = [self.compatible("A"), self.incompatible("B")]
        result = self.select(candidates, [
            observation("A", AvailabilityState.UNAVAILABLE),
            observation("B", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.eligible_actor_ids, ("A",))
        self.assertEqual(result.available_actor_ids, ())
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)

    def test_compatible_unavailable_actor_is_excluded_from_available(self):
        candidate = self.compatible("A")
        result = self.select(
            [candidate], [observation("A", AvailabilityState.UNAVAILABLE)]
        )
        self.assertEqual(result.eligible_actor_ids, ("A",))
        self.assertEqual(result.available_actor_ids, ())
        self.assertEqual(result.unknown_actor_ids, ())

    def test_missing_observation_behaves_as_unknown(self):
        candidate = self.compatible("A")
        missing = self.select([candidate])
        explicit = self.select(
            [candidate], [observation("A", AvailabilityState.UNKNOWN)]
        )
        self.assertEqual(missing, explicit)
        self.assertEqual(missing.outcome, ActorSelectionOutcome.INDETERMINATE)


class ActorSelectionInvalidContextTests(ActorSelectionFixture):
    def assert_atomic_invalid(self, result, code):
        self.assertFalse(result.valid)
        self.assertIsNone(result.responsibility_key)
        self.assertIsNone(result.outcome)
        self.assertIsNone(result.reason)
        self.assertIsNone(result.selected_actor_id)
        self.assertEqual(result.eligible_actor_ids, ())
        self.assertEqual(result.available_actor_ids, ())
        self.assertEqual(result.unknown_actor_ids, ())
        self.assertEqual([finding.code for finding in result.findings], [code])

    def test_duplicate_actor_ids_are_invalid(self):
        duplicate = self.compatible("same")
        result = self.select([duplicate, dict(duplicate)])
        self.assert_atomic_invalid(result, "duplicate_actor_id")

    def test_duplicate_availability_observations_are_invalid(self):
        candidate = self.compatible("A")
        result = self.select([candidate], [
            observation("A", AvailabilityState.AVAILABLE),
            observation("A", AvailabilityState.AVAILABLE),
        ])
        self.assert_atomic_invalid(result, "duplicate_actor_availability")

    def test_conflicting_availability_observations_are_invalid(self):
        candidate = self.compatible("A")
        forward = self.select([candidate], [
            observation("A", AvailabilityState.AVAILABLE),
            observation("A", AvailabilityState.UNAVAILABLE),
        ])
        reverse = self.select([candidate], [
            observation("A", AvailabilityState.UNAVAILABLE),
            observation("A", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(forward, reverse)
        self.assert_atomic_invalid(forward, "duplicate_actor_availability")

    def test_observation_for_unknown_actor_is_invalid(self):
        result = self.select(
            [self.compatible("A")],
            [observation("missing", AvailabilityState.AVAILABLE)],
        )
        self.assert_atomic_invalid(result, "actor_not_found")

    def test_missing_task_workflow_is_invalid(self):
        result = self.select(task={"id": "AIO-025"})
        self.assert_atomic_invalid(result, "task_workflow_missing")

    def test_unknown_task_workflow_is_invalid(self):
        result = self.select(task={"id": "AIO-025", "workflow": "missing"})
        self.assert_atomic_invalid(result, "workflow_not_found")

    def test_unknown_stage_is_invalid(self):
        result = self.select(stage_id="missing")
        self.assert_atomic_invalid(result, "stage_not_found")

    def test_unknown_role_is_invalid(self):
        result = self.select(role_id="missing")
        self.assert_atomic_invalid(result, "role_not_found")

    def test_existing_role_not_required_by_stage_is_invalid(self):
        result = self.select(role_id="reviewer")
        self.assert_atomic_invalid(result, "role_not_required")

    def test_availability_findings_preserve_existing_order_and_messages(self):
        candidates = [self.compatible("A")]
        observations = [
            observation("z", AvailabilityState.AVAILABLE),
            observation("z", AvailabilityState.UNAVAILABLE),
        ]
        result = self.select(candidates, observations)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_actor_availability", "actor_not_found"],
        )
        self.assertTrue(all("'z'" in finding.message for finding in result.findings))

    def test_corrupt_workflow_catalog_remains_infrastructure_failure(self):
        catalog = WorkflowCatalog(Path("unused"), load_errors=["broken"])
        with self.assertRaisesRegex(
            WorkflowCatalogError,
            "Actor Selection requires a valid Workflow catalog",
        ):
            self.select(workflows=catalog)

    def test_corrupt_role_catalog_remains_infrastructure_failure(self):
        catalog = RoleCatalog(
            None,
            load_errors=["broken"],
            infrastructure_errors=["broken"],
        )
        with self.assertRaisesRegex(
            RoleCatalogError,
            "Actor Selection requires a valid framework Role catalog",
        ):
            self.select(roles=catalog)


class ActorSelectionSymmetryAndDeterminismTests(ActorSelectionFixture):
    def test_human_only_candidate_set(self):
        human = self.compatible("human", kind="human")
        result = self.select(
            [human], [observation("human", AvailabilityState.AVAILABLE)]
        )
        self.assertEqual(result.selected_actor_id, "human")

    def test_agent_only_candidate_set(self):
        agent = self.compatible("agent", kind="agent")
        result = self.select(
            [agent], [observation("agent", AvailabilityState.AVAILABLE)]
        )
        self.assertEqual(result.selected_actor_id, "agent")

    def test_mixed_human_and_agent_candidates_use_the_same_constraints(self):
        candidates = [
            self.compatible("human", kind="human"),
            self.compatible("agent", kind="agent"),
        ]
        result = self.select(candidates, [
            observation("human", AvailabilityState.AVAILABLE),
            observation("agent", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.outcome, ActorSelectionOutcome.AMBIGUOUS)

    def test_human_kind_has_no_preference(self):
        candidates = [
            self.compatible("human", kind="human"),
            self.compatible("agent", kind="agent"),
        ]
        result = self.select(candidates, [
            observation("human", AvailabilityState.UNAVAILABLE),
            observation("agent", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.selected_actor_id, "agent")

    def test_agent_kind_has_no_preference(self):
        candidates = [
            self.compatible("human", kind="human"),
            self.compatible("agent", kind="agent"),
        ]
        result = self.select(candidates, [
            observation("human", AvailabilityState.AVAILABLE),
            observation("agent", AvailabilityState.UNAVAILABLE),
        ])
        self.assertEqual(result.selected_actor_id, "human")

    def test_actor_evidence_is_case_sensitive_ascending(self):
        candidates = [
            self.compatible("a"),
            self.compatible("B"),
            self.compatible("A"),
        ]
        result = self.select(candidates, [
            observation("a", AvailabilityState.UNAVAILABLE),
            observation("B", AvailabilityState.UNKNOWN),
            observation("A", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.eligible_actor_ids, ("A", "B", "a"))
        self.assertEqual(result.available_actor_ids, ("A",))
        self.assertEqual(result.unknown_actor_ids, ("B",))

    def test_declaration_order_does_not_select(self):
        actors = [self.compatible("z"), self.compatible("a")]
        observations = [
            observation("z", AvailabilityState.AVAILABLE),
            observation("a", AvailabilityState.AVAILABLE),
        ]
        forward = self.select(actors, observations)
        reverse = self.select(list(reversed(actors)), list(reversed(observations)))
        self.assertEqual(forward, reverse)
        self.assertEqual(forward.outcome, ActorSelectionOutcome.AMBIGUOUS)

    def test_lexical_order_does_not_select(self):
        actors = [self.compatible("first"), self.compatible("last")]
        result = self.select(actors, [
            observation("first", AvailabilityState.AVAILABLE),
            observation("last", AvailabilityState.AVAILABLE),
        ])
        self.assertEqual(result.available_actor_ids, ("first", "last"))
        self.assertIsNone(result.selected_actor_id)

    def test_selection_uses_no_randomness(self):
        candidate = self.compatible("A")
        with patch.object(random, "choice", side_effect=AssertionError), \
                patch.object(random, "shuffle", side_effect=AssertionError), \
                patch.object(random, "random", side_effect=AssertionError):
            result = self.select(
                [candidate], [observation("A", AvailabilityState.AVAILABLE)]
            )
        self.assertEqual(result.selected_actor_id, "A")

    def test_repeated_identical_input_gives_identical_result(self):
        candidates = [self.compatible("A"), self.compatible("B")]
        observations = [observation("A", AvailabilityState.AVAILABLE)]
        first = self.select(candidates, observations)
        for _ in range(5):
            self.assertEqual(self.select(candidates, observations), first)


class ActorSelectionBoundaryTests(ActorSelectionFixture):
    def selected_result(self):
        candidate = self.compatible("A")
        return self.select(
            [candidate], [observation("A", AvailabilityState.AVAILABLE)]
        ), candidate

    def test_selection_does_not_create_assignment(self):
        with patch(
            "engineering_orchestration.assignment.Assignment",
            side_effect=AssertionError("Assignment construction is forbidden"),
        ):
            result, _ = self.selected_result()
        self.assertNotIsInstance(result, Assignment)

    def test_selection_does_not_call_assignment_validation(self):
        with patch(
            "engineering_orchestration.assignment.validate_assignment",
            side_effect=AssertionError("Assignment validation is forbidden"),
        ):
            result, _ = self.selected_result()
        self.assertEqual(result.selected_actor_id, "A")

    def test_selection_does_not_return_proposed_assignment(self):
        result, _ = self.selected_result()
        result_fields = {field.name for field in fields(result)}
        self.assertTrue(result_fields.isdisjoint({
            "assignment", "proposed_assignment", "pending_assignment"
        }))

    def test_final_assignment_still_passes_aio_023_validation(self):
        result, candidate = self.selected_result()
        binding = Assignment(*result.responsibility_key, result.selected_actor_id)
        validation = validate_assignment(
            binding, TASK, self.workflows, self.roles, [candidate]
        )
        self.assertTrue(validation.valid)

    def test_selection_result_grants_no_authority(self):
        result, _ = self.selected_result()
        self.assertFalse(hasattr(result, "authority"))
        self.assertFalse(hasattr(result, "permissions"))

    def test_selection_result_grants_no_execution_permission(self):
        result, _ = self.selected_result()
        self.assertFalse(hasattr(result, "execution"))
        self.assertFalse(hasattr(result, "runtime"))

    def test_selection_result_grants_no_human_approval(self):
        result, _ = self.selected_result()
        self.assertFalse(hasattr(result, "approval"))
        self.assertFalse(hasattr(result, "human_control"))

    def test_selection_performs_no_reservation(self):
        result, _ = self.selected_result()
        self.assertFalse(hasattr(result, "reservation"))
        self.assertFalse(hasattr(result, "lease"))

    def test_selection_performs_no_provider_or_model_lookup(self):
        supplied = TrackingMapping(self.compatible("A"))
        supplied["provider"] = object()
        supplied["model"] = object()
        result = self.select(
            [supplied], [observation("A", AvailabilityState.AVAILABLE)]
        )
        self.assertEqual(result.selected_actor_id, "A")
        self.assertTrue(set(supplied.accessed) <= {"id", "competencies"})

    def test_selection_performs_no_network_io(self):
        candidate = self.compatible("A")
        with patch.object(socket, "create_connection", side_effect=AssertionError), \
                patch.object(urllib.request, "urlopen", side_effect=AssertionError):
            result = self.select(
                [candidate], [observation("A", AvailabilityState.AVAILABLE)]
            )
        self.assertEqual(result.selected_actor_id, "A")

    def test_selection_performs_no_persistence_or_file_io(self):
        candidate = self.compatible("A")
        with patch("builtins.open", side_effect=AssertionError), \
                patch.object(Path, "open", side_effect=AssertionError), \
                patch.object(Path, "write_text", side_effect=AssertionError):
            result = self.select(
                [candidate], [observation("A", AvailabilityState.AVAILABLE)]
            )
        self.assertEqual(result.selected_actor_id, "A")

    def test_selection_performs_no_clock_access(self):
        candidate = self.compatible("A")
        with patch.object(time, "time", side_effect=AssertionError), \
                patch.object(time, "monotonic", side_effect=AssertionError):
            result = self.select(
                [candidate], [observation("A", AvailabilityState.AVAILABLE)]
            )
        self.assertEqual(result.selected_actor_id, "A")

    def test_selection_does_not_evaluate_quality_gates(self):
        task = TrackingMapping({
            **TASK,
            "quality_gates": ["must-not-be-read"],
        })
        result = self.select(task=task)
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertNotIn("quality_gates", task.accessed)

    def test_selection_does_not_use_task_complexity(self):
        baseline = self.select()
        varied = self.select(task={**TASK, "complexity": "critical"})
        self.assertEqual(varied, baseline)

    def test_selection_does_not_use_task_risk(self):
        baseline = self.select()
        varied = self.select(task={**TASK, "risk": "critical"})
        self.assertEqual(varied, baseline)

    def test_selection_does_not_use_execution_mode(self):
        baseline = self.select()
        varied = self.select(task={**TASK, "execution": {"mode": "critical"}})
        self.assertEqual(varied, baseline)

    def test_selection_accepts_no_existing_assignments_or_policy_input(self):
        parameters = set(inspect.signature(select_actor).parameters)
        self.assertTrue(parameters.isdisjoint({
            "assignments", "existing_assignments", "selection_policy"
        }))

    def test_empty_role_requirements_reuse_coverage_no_eligible_semantics(self):
        empty_role = {"id": "empty-role", "required_capabilities": []}
        workflows = workflow_catalog(WorkflowStage(
            "stage", "Stage", required_roles=["empty-role"]
        ))
        roles = role_catalog(empty_role)
        candidate = actor("A", ["anything"])
        result = self.select(
            [candidate],
            [observation("A", AvailabilityState.AVAILABLE)],
            stage_id="stage",
            role_id="empty-role",
            workflows=workflows,
            roles=roles,
        )
        self.assertEqual(result.outcome, ActorSelectionOutcome.NO_CANDIDATE)
        self.assertEqual(result.reason, ActorSelectionReason.NO_ELIGIBLE_ACTOR)

    def test_selection_schema_is_not_introduced(self):
        self.assertFalse((ROOT / "schemas/actor-selection.schema.json").exists())


if __name__ == "__main__":
    unittest.main()
