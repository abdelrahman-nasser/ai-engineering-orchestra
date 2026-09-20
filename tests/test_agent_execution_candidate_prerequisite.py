"""Focused Agent Execution Candidate Prerequisite Assessment tests."""

from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError, fields
from inspect import signature
from pathlib import Path
import unittest
from unittest.mock import patch

import engineering_orchestration
import engineering_orchestration.agent_execution_candidate_prerequisite as subject
from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
)
from engineering_orchestration.actor_runtime_applicability import (
    ActorRuntimeApplicabilityEvidence,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteFinding,
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
    assess_agent_execution_candidate_prerequisites,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
)
from engineering_orchestration.assignment import Assignment, validate_assignment
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.inference_option_availability import (
    InferenceOptionAvailabilityObservation,
    InferenceOptionAvailabilityState,
)
from engineering_orchestration.role_catalog import load_role_catalog
from engineering_orchestration.runtime_inference_compatibility import (
    RuntimeInferenceCompatibilityEvidence,
)
from engineering_orchestration.workflow_catalog import load_workflow_catalog


ROOT = Path(__file__).resolve().parents[1]
TASK = {"id": "AIO-034", "workflow": "architecture-change"}


def runtime(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def option(option_id: str) -> InferenceOptionDefinition:
    return InferenceOptionDefinition(
        option_id,
        "provider::synthetic",
        f"model::{option_id}",
    )


def actor_observation(
    actor_id: str,
    state: AvailabilityState = AvailabilityState.AVAILABLE,
) -> ActorAvailabilityObservation:
    return ActorAvailabilityObservation(actor_id, state)


def applicability(
    actor_id: str,
    runtime_option_id: str,
) -> ActorRuntimeApplicabilityEvidence:
    return ActorRuntimeApplicabilityEvidence(actor_id, runtime_option_id)


def compatibility(
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
    """Iterable that records order and rejects a second enumeration."""

    def __init__(self, label: str, values: list[object], events: list[str]):
        self.label = label
        self.values = values
        self.events = events
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError(f"{self.label} was iterated more than once")
        self.events.append(self.label)
        return iter(self.values)


class AgentExecutionCandidateFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflows = load_workflow_catalog(ROOT / "workflows")
        cls.roles = load_role_catalog()
        if not cls.workflows.is_valid:
            raise AssertionError(cls.workflows.load_errors)
        if not cls.roles.is_valid:
            raise AssertionError(cls.roles.load_errors)
        role = cls.roles.get("software-engineer")
        if role is None:
            raise AssertionError("software-engineer Role was not found")
        cls.competencies = list(role["required_capabilities"])

    def actor(
        self,
        actor_id: str = "agent::assigned",
        *,
        kind: str = "agent",
    ) -> dict[str, object]:
        return {
            "id": actor_id,
            "kind": kind,
            "competencies": list(self.competencies),
        }

    def assignment(self, **changes: str) -> Assignment:
        values = {
            "task_id": "AIO-034",
            "workflow_id": "architecture-change",
            "stage_id": "implement",
            "role_id": "software-engineer",
            "actor_id": "agent::assigned",
        }
        values.update(changes)
        return Assignment(**values)

    def base(self) -> dict[str, object]:
        return {
            "assignment": self.assignment(),
            "runtime_option_id": "runtime::one",
            "option_id": "option::one",
            "task": dict(TASK),
            "workflow_catalog": self.workflows,
            "role_catalog": self.roles,
            "actors": [self.actor()],
            "actor_availability_observations": [
                actor_observation("agent::assigned")
            ],
            "actor_runtime_applicability_evidence": [
                applicability("agent::assigned", "runtime::one")
            ],
            "runtime_options": [runtime("runtime::one")],
            "inference_options": [option("option::one")],
            "runtime_inference_compatibility_evidence": [
                compatibility("runtime::one", "option::one")
            ],
            "runtime_availability_observations": [
                runtime_observation("runtime::one")
            ],
            "inference_availability_observations": [
                inference_observation("option::one")
            ],
        }

    def assess(self, **changes: object) -> AgentExecutionCandidatePrerequisiteResult:
        supplied = self.base()
        supplied.update(changes)
        return assess_agent_execution_candidate_prerequisites(**supplied)

    def assert_atomic_invalid(
        self,
        result: AgentExecutionCandidatePrerequisiteResult,
        codes: list[str],
    ) -> None:
        self.assertFalse(result.valid)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.responsibility_key)
        self.assertIsNone(result.actor_id)
        self.assertIsNone(result.runtime_option_id)
        self.assertIsNone(result.option_id)
        self.assertIsNone(result.outcome)
        self.assertEqual(result.reasons, ())


class AgentExecutionCandidateValueTests(AgentExecutionCandidateFixture):
    def test_outcomes_are_exactly_the_locked_closed_vocabulary(self) -> None:
        self.assertEqual(
            [item.value for item in AgentExecutionCandidatePrerequisiteOutcome],
            ["satisfied", "blocked", "unresolved"],
        )

    def test_reasons_are_exactly_the_locked_ordered_vocabulary(self) -> None:
        self.assertEqual(
            [item.value for item in AgentExecutionCandidatePrerequisiteReason],
            [
                "all_currently_modeled_prerequisites_satisfied",
                "actor_unavailable",
                "actor_availability_unknown",
                "actor_runtime_applicability_not_supplied",
                "runtime_inference_compatibility_not_supplied",
                "agent_runtime_option_unavailable",
                "agent_runtime_option_availability_unknown",
                "inference_option_unavailable",
                "inference_option_availability_unknown",
            ],
        )

    def test_finding_and_result_fields_are_exact_frozen_and_tuple_backed(self) -> None:
        finding = AgentExecutionCandidatePrerequisiteFinding("example", "message")
        result = AgentExecutionCandidatePrerequisiteResult(
            False,
            (finding,),
            None,
            None,
            None,
            None,
            None,
            (),
        )
        self.assertEqual(
            [item.name for item in fields(finding)],
            ["code", "message"],
        )
        self.assertEqual(
            [item.name for item in fields(result)],
            [
                "valid",
                "findings",
                "responsibility_key",
                "actor_id",
                "runtime_option_id",
                "option_id",
                "outcome",
                "reasons",
            ],
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.reasons, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_public_signature_is_exactly_the_locked_raw_input_api(self) -> None:
        self.assertEqual(
            list(
                signature(
                    assess_agent_execution_candidate_prerequisites
                ).parameters
            ),
            [
                "assignment",
                "runtime_option_id",
                "option_id",
                "task",
                "workflow_catalog",
                "role_catalog",
                "actors",
                "actor_availability_observations",
                "actor_runtime_applicability_evidence",
                "runtime_options",
                "inference_options",
                "runtime_inference_compatibility_evidence",
                "runtime_availability_observations",
                "inference_availability_observations",
            ],
        )
        parameters = signature(
            assess_agent_execution_candidate_prerequisites
        ).parameters
        self.assertTrue(all(item.default is item.empty for item in parameters.values()))

    def test_valid_result_exposes_flattened_identity_without_candidate_id(self) -> None:
        result = self.assess()
        self.assertTrue(result.valid)
        self.assertEqual(
            result.responsibility_key,
            ("AIO-034", "architecture-change", "implement", "software-engineer"),
        )
        self.assertEqual(result.actor_id, "agent::assigned")
        self.assertEqual(result.runtime_option_id, "runtime::one")
        self.assertEqual(result.option_id, "option::one")
        self.assertNotIn("candidate_id", {item.name for item in fields(result)})


class AgentExecutionCandidateScenarioTests(AgentExecutionCandidateFixture):
    def test_all_modeled_positive_prerequisites_are_satisfied(self) -> None:
        result = self.assess()
        self.assertTrue(result.valid)
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
        )
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
            ),
        )
        self.assertEqual(result.findings, ())

    def test_actor_unavailable_blocks_without_invalidating_assignment(self) -> None:
        assignment = self.assignment()
        actors = [self.actor()]
        assignment_result = validate_assignment(
            assignment,
            TASK,
            self.workflows,
            self.roles,
            actors,
        )
        result = self.assess(
            assignment=assignment,
            actors=actors,
            actor_availability_observations=[
                actor_observation("agent::assigned", AvailabilityState.UNAVAILABLE)
            ],
        )
        self.assertTrue(assignment_result.valid)
        self.assertTrue(result.valid)
        self.assertEqual(result.outcome, AgentExecutionCandidatePrerequisiteOutcome.BLOCKED)
        self.assertEqual(
            result.reasons,
            (AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,),
        )

    def test_missing_actor_observation_normalizes_unknown_and_is_unresolved(self) -> None:
        result = self.assess(actor_availability_observations=[])
        self.assertTrue(result.valid)
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (AgentExecutionCandidatePrerequisiteReason.ACTOR_AVAILABILITY_UNKNOWN,),
        )

    def test_explicit_unknown_actor_state_is_unresolved(self) -> None:
        result = self.assess(
            actor_availability_observations=[
                actor_observation("agent::assigned", AvailabilityState.UNKNOWN)
            ]
        )
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (AgentExecutionCandidatePrerequisiteReason.ACTOR_AVAILABILITY_UNKNOWN,),
        )

    def test_nonempty_relation_missing_exact_applicability_is_unresolved(self) -> None:
        result = self.assess(
            runtime_options=[runtime("runtime::one"), runtime("runtime::other")],
            actor_runtime_applicability_evidence=[
                applicability("agent::assigned", "runtime::other")
            ],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED,
            ),
        )

    def test_no_applicability_edge_supplied_is_unresolved_not_blocked(self) -> None:
        result = self.assess(actor_runtime_applicability_evidence=[])
        self.assertTrue(result.valid)
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED,
            ),
        )

    def test_pair_runtime_unavailable_blocks_with_specific_reason(self) -> None:
        result = self.assess(
            runtime_availability_observations=[
                runtime_observation(
                    "runtime::one",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ]
        )
        self.assertEqual(result.outcome, AgentExecutionCandidatePrerequisiteOutcome.BLOCKED)
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                AGENT_RUNTIME_OPTION_UNAVAILABLE,
            ),
        )

    def test_pair_inference_unavailable_blocks_with_specific_reason(self) -> None:
        result = self.assess(
            inference_availability_observations=[
                inference_observation(
                    "option::one",
                    InferenceOptionAvailabilityState.UNAVAILABLE,
                )
            ]
        )
        self.assertEqual(result.outcome, AgentExecutionCandidatePrerequisiteOutcome.BLOCKED)
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                INFERENCE_OPTION_UNAVAILABLE,
            ),
        )

    def test_pair_unknown_is_unresolved_with_runtime_then_inference_reasons(self) -> None:
        result = self.assess(
            runtime_availability_observations=[],
            inference_availability_observations=[],
        )
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN,
                AgentExecutionCandidatePrerequisiteReason.
                INFERENCE_OPTION_AVAILABILITY_UNKNOWN,
            ),
        )

    def test_missing_compatibility_is_unresolved_and_does_not_synthesize_pair(self) -> None:
        result = self.assess(runtime_inference_compatibility_evidence=[])
        self.assertTrue(result.valid)
        self.assertEqual(
            result.outcome,
            AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED,
        )
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.
                RUNTIME_INFERENCE_COMPATIBILITY_NOT_SUPPLIED,
            ),
        )

    def test_multiple_established_pairs_are_assessed_only_when_designated(self) -> None:
        common = {
            "inference_options": [option("option::one"), option("option::two")],
            "runtime_inference_compatibility_evidence": [
                compatibility("runtime::one", "option::one"),
                compatibility("runtime::one", "option::two"),
            ],
            "inference_availability_observations": [
                inference_observation("option::one"),
                inference_observation("option::two"),
            ],
        }
        first = self.assess(**common)
        second = self.assess(
            **common,
            option_id="option::two",
        )
        self.assertEqual(first.outcome, AgentExecutionCandidatePrerequisiteOutcome.SATISFIED)
        self.assertEqual(second.outcome, AgentExecutionCandidatePrerequisiteOutcome.SATISFIED)
        self.assertEqual(first.runtime_option_id, "runtime::one")
        self.assertEqual(first.option_id, "option::one")
        self.assertEqual(second.runtime_option_id, "runtime::one")
        self.assertEqual(second.option_id, "option::two")
        self.assertFalse(hasattr(first, "assessments"))
        self.assertFalse(hasattr(first, "selected"))

    def test_multiple_applicable_runtimes_do_not_imply_selection(self) -> None:
        common = {
            "runtime_options": [runtime("runtime::one"), runtime("runtime::two")],
            "actor_runtime_applicability_evidence": [
                applicability("agent::assigned", "runtime::one"),
                applicability("agent::assigned", "runtime::two"),
            ],
            "runtime_inference_compatibility_evidence": [
                compatibility("runtime::one", "option::one"),
                compatibility("runtime::two", "option::one"),
            ],
            "runtime_availability_observations": [
                runtime_observation("runtime::one"),
                runtime_observation("runtime::two"),
            ],
        }
        outcomes = {
            runtime_id: self.assess(
                **common,
                runtime_option_id=runtime_id,
            ).outcome
            for runtime_id in ("runtime::one", "runtime::two")
        }
        self.assertEqual(
            outcomes,
            {
                "runtime::one": AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
                "runtime::two": AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
            },
        )

    def test_human_assignment_is_boundary_finding_not_blocked_human(self) -> None:
        human = self.actor("human::assigned", kind="human")
        assignment = self.assignment(actor_id="human::assigned")
        assignment_result = validate_assignment(
            assignment,
            TASK,
            self.workflows,
            self.roles,
            [human],
        )
        result = self.assess(
            assignment=assignment,
            actors=[human],
            actor_availability_observations=[],
            actor_runtime_applicability_evidence=[],
            runtime_options=[],
            inference_options=[],
            runtime_inference_compatibility_evidence=[],
            runtime_availability_observations=[],
            inference_availability_observations=[],
        )
        self.assertTrue(assignment_result.valid)
        self.assert_atomic_invalid(
            result,
            ["agent_execution_candidate_not_applicable_to_human_actor"],
        )
        self.assertIn("does not apply", result.findings[0].message)

    def test_runtime_owned_inference_is_not_represented_or_classified(self) -> None:
        result = self.assess(
            option_id="",
            runtime_inference_compatibility_evidence=[],
        )
        self.assert_atomic_invalid(result, ["inference_option_not_found"])
        self.assertNotIn("runtime_owned", result.findings[0].code)

    def test_invalid_parent_evidence_has_no_ordinary_outcome(self) -> None:
        duplicate = applicability("agent::assigned", "runtime::one")
        result = self.assess(
            actor_runtime_applicability_evidence=[duplicate, duplicate]
        )
        self.assert_atomic_invalid(
            result,
            ["duplicate_actor_runtime_applicability"],
        )


class AgentExecutionCandidateValidationTests(AgentExecutionCandidateFixture):
    def test_invalid_assignment_short_circuits_atomically(self) -> None:
        result = self.assess(assignment=self.assignment(task_id="other"))
        self.assert_atomic_invalid(result, ["task_id_mismatch"])

    def test_duplicate_actor_availability_is_atomic_invalid(self) -> None:
        observation = actor_observation("agent::assigned")
        result = self.assess(
            actor_availability_observations=[observation, observation]
        )
        self.assert_atomic_invalid(result, ["duplicate_actor_availability"])

    def test_unknown_actor_availability_reference_is_atomic_invalid(self) -> None:
        result = self.assess(
            actor_availability_observations=[
                actor_observation("agent::assigned"),
                actor_observation("agent::unknown"),
            ]
        )
        self.assert_atomic_invalid(result, ["actor_not_found"])

    def test_invalid_applicability_relation_is_atomic_invalid(self) -> None:
        result = self.assess(
            actor_runtime_applicability_evidence=[
                applicability("agent::unknown", "runtime::one")
            ]
        )
        self.assert_atomic_invalid(result, ["actor_not_found"])

    def test_invalid_compatibility_relation_is_atomic_invalid(self) -> None:
        duplicate = compatibility("runtime::one", "option::one")
        result = self.assess(
            runtime_inference_compatibility_evidence=[duplicate, duplicate]
        )
        self.assert_atomic_invalid(
            result,
            ["duplicate_runtime_inference_compatibility"],
        )

    def test_invalid_runtime_inventory_is_atomic_invalid(self) -> None:
        result = self.assess(
            runtime_options=[runtime("runtime::one"), runtime("runtime::one")]
        )
        self.assert_atomic_invalid(result, ["duplicate_agent_runtime_option_id"])

    def test_invalid_inference_inventory_is_atomic_invalid(self) -> None:
        result = self.assess(
            inference_options=[option("option::one"), option("option::one")]
        )
        self.assert_atomic_invalid(result, ["duplicate_inference_option_id"])

    def test_invalid_runtime_availability_is_atomic_invalid(self) -> None:
        observation = runtime_observation("runtime::one")
        result = self.assess(
            runtime_availability_observations=[observation, observation]
        )
        self.assert_atomic_invalid(
            result,
            ["duplicate_agent_runtime_option_availability"],
        )

    def test_invalid_inference_availability_is_atomic_invalid(self) -> None:
        observation = inference_observation("option::one")
        result = self.assess(
            inference_availability_observations=[observation, observation]
        )
        self.assert_atomic_invalid(
            result,
            ["duplicate_inference_option_availability"],
        )

    def test_wrong_runtime_and_inference_ids_are_reported_in_locked_order(self) -> None:
        result = self.assess(
            runtime_option_id="runtime::missing",
            option_id="option::missing",
        )
        self.assert_atomic_invalid(
            result,
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )

    def test_candidate_ids_are_exact_and_case_sensitive(self) -> None:
        runtime_result = self.assess(runtime_option_id="Runtime::one")
        option_result = self.assess(option_id="Option::one")
        self.assert_atomic_invalid(runtime_result, ["agent_runtime_option_not_found"])
        self.assert_atomic_invalid(option_result, ["inference_option_not_found"])

    def test_complete_parent_relation_is_validated_before_target_lookup(self) -> None:
        result = self.assess(
            runtime_option_id="runtime::missing",
            actor_runtime_applicability_evidence=[
                applicability("agent::unknown", "runtime::one")
            ],
        )
        self.assert_atomic_invalid(result, ["actor_not_found"])

    def test_parent_findings_keep_runtime_then_inference_order(self) -> None:
        runtime_item = runtime_observation("runtime::one")
        inference_item = inference_observation("option::one")
        result = self.assess(
            runtime_availability_observations=[runtime_item, runtime_item],
            inference_availability_observations=[inference_item, inference_item],
        )
        self.assert_atomic_invalid(
            result,
            [
                "duplicate_agent_runtime_option_availability",
                "duplicate_inference_option_availability",
            ],
        )

    def test_invalid_assignment_stops_all_later_parent_validators(self) -> None:
        with (
            patch.object(
                subject,
                "validate_actor_availability",
                side_effect=AssertionError("Actor availability must not run"),
            ),
            patch.object(
                subject,
                "validate_actor_runtime_applicability",
                side_effect=AssertionError("Applicability must not run"),
            ),
            patch.object(
                subject,
                "assess_runtime_inference_pair_availability",
                side_effect=AssertionError("Pair assessment must not run"),
            ),
        ):
            result = self.assess(assignment=self.assignment(task_id="other"))
        self.assert_atomic_invalid(result, ["task_id_mismatch"])

    def test_human_boundary_stops_agent_parent_validation(self) -> None:
        human = self.actor("human::assigned", kind="human")
        with (
            patch.object(
                subject,
                "validate_actor_availability",
                side_effect=AssertionError("Actor availability must not run"),
            ),
            patch.object(
                subject,
                "validate_actor_runtime_applicability",
                side_effect=AssertionError("Applicability must not run"),
            ),
            patch.object(
                subject,
                "assess_runtime_inference_pair_availability",
                side_effect=AssertionError("Pair assessment must not run"),
            ),
        ):
            result = self.assess(
                assignment=self.assignment(actor_id="human::assigned"),
                actors=[human],
            )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_candidate_not_applicable_to_human_actor"],
        )


class AgentExecutionCandidateDeterminismTests(AgentExecutionCandidateFixture):
    def test_blocking_reason_dominates_but_all_reasons_remain_ordered(self) -> None:
        result = self.assess(
            actor_availability_observations=[],
            actor_runtime_applicability_evidence=[],
            runtime_availability_observations=[],
            inference_availability_observations=[
                inference_observation(
                    "option::one",
                    InferenceOptionAvailabilityState.UNAVAILABLE,
                )
            ],
        )
        self.assertEqual(result.outcome, AgentExecutionCandidatePrerequisiteOutcome.BLOCKED)
        self.assertEqual(
            result.reasons,
            (
                AgentExecutionCandidatePrerequisiteReason.ACTOR_AVAILABILITY_UNKNOWN,
                AgentExecutionCandidatePrerequisiteReason.
                ACTOR_RUNTIME_APPLICABILITY_NOT_SUPPLIED,
                AgentExecutionCandidatePrerequisiteReason.
                AGENT_RUNTIME_OPTION_AVAILABILITY_UNKNOWN,
                AgentExecutionCandidatePrerequisiteReason.
                INFERENCE_OPTION_UNAVAILABLE,
            ),
        )

    def test_declaration_order_does_not_change_result(self) -> None:
        actors = [self.actor(), self.actor("agent::other")]
        runtime_options = [runtime("runtime::one"), runtime("runtime::two")]
        inference_options = [option("option::one"), option("option::two")]
        actor_observations = [
            actor_observation("agent::assigned"),
            actor_observation("agent::other"),
        ]
        applicability_evidence = [
            applicability("agent::assigned", "runtime::one"),
            applicability("agent::other", "runtime::two"),
        ]
        compatibility_evidence = [
            compatibility("runtime::one", "option::one"),
            compatibility("runtime::two", "option::two"),
        ]
        runtime_observations = [
            runtime_observation("runtime::one"),
            runtime_observation("runtime::two"),
        ]
        inference_observations = [
            inference_observation("option::one"),
            inference_observation("option::two"),
        ]
        forward = self.assess(
            actors=actors,
            actor_availability_observations=actor_observations,
            actor_runtime_applicability_evidence=applicability_evidence,
            runtime_options=runtime_options,
            inference_options=inference_options,
            runtime_inference_compatibility_evidence=compatibility_evidence,
            runtime_availability_observations=runtime_observations,
            inference_availability_observations=inference_observations,
        )
        reverse = self.assess(
            actors=list(reversed(actors)),
            actor_availability_observations=list(reversed(actor_observations)),
            actor_runtime_applicability_evidence=list(
                reversed(applicability_evidence)
            ),
            runtime_options=list(reversed(runtime_options)),
            inference_options=list(reversed(inference_options)),
            runtime_inference_compatibility_evidence=list(
                reversed(compatibility_evidence)
            ),
            runtime_availability_observations=list(reversed(runtime_observations)),
            inference_availability_observations=list(
                reversed(inference_observations)
            ),
        )
        self.assertEqual(forward, reverse)

    def test_every_iterable_is_captured_once_in_public_parameter_order(self) -> None:
        events: list[str] = []
        supplied = self.base()
        names = [
            "actors",
            "actor_availability_observations",
            "actor_runtime_applicability_evidence",
            "runtime_options",
            "inference_options",
            "runtime_inference_compatibility_evidence",
            "runtime_availability_observations",
            "inference_availability_observations",
        ]
        iterables = {}
        for name in names:
            value = supplied[name]
            one_shot = OneShotIterable(name, list(value), events)
            supplied[name] = one_shot
            iterables[name] = one_shot
        result = assess_agent_execution_candidate_prerequisites(**supplied)
        self.assertTrue(result.valid)
        self.assertEqual(events, names)
        self.assertTrue(all(item.iterations == 1 for item in iterables.values()))

    def test_all_iterables_are_captured_before_invalid_assignment_short_circuits(self) -> None:
        events: list[str] = []
        supplied = self.base()
        supplied["assignment"] = self.assignment(task_id="other")
        names = [
            "actors",
            "actor_availability_observations",
            "actor_runtime_applicability_evidence",
            "runtime_options",
            "inference_options",
            "runtime_inference_compatibility_evidence",
            "runtime_availability_observations",
            "inference_availability_observations",
        ]
        iterables = {}
        for name in names:
            one_shot = OneShotIterable(name, list(supplied[name]), events)
            supplied[name] = one_shot
            iterables[name] = one_shot
        result = assess_agent_execution_candidate_prerequisites(**supplied)
        self.assert_atomic_invalid(result, ["task_id_mismatch"])
        self.assertEqual(events, names)
        self.assertTrue(all(item.iterations == 1 for item in iterables.values()))

    def test_same_captured_actor_and_runtime_tuples_reach_composed_parents(self) -> None:
        with (
            patch.object(
                subject,
                "validate_assignment",
                wraps=subject.validate_assignment,
            ) as assignment_validator,
            patch.object(
                subject,
                "validate_actor_availability",
                wraps=subject.validate_actor_availability,
            ) as actor_validator,
            patch.object(
                subject,
                "validate_actor_runtime_applicability",
                wraps=subject.validate_actor_runtime_applicability,
            ) as applicability_validator,
            patch.object(
                subject,
                "assess_runtime_inference_pair_availability",
                wraps=subject.assess_runtime_inference_pair_availability,
            ) as pair_assessor,
        ):
            result = self.assess()
        self.assertTrue(result.valid)
        assignment_actors = assignment_validator.call_args.args[4]
        availability_actors = actor_validator.call_args.args[1]
        applicability_actors = applicability_validator.call_args.args[1]
        self.assertIs(assignment_actors, availability_actors)
        self.assertIs(assignment_actors, applicability_actors)
        applicability_runtimes = applicability_validator.call_args.args[2]
        pair_runtimes = pair_assessor.call_args.args[1]
        self.assertIs(applicability_runtimes, pair_runtimes)
        self.assertIsInstance(assignment_actors, tuple)
        self.assertIsInstance(pair_runtimes, tuple)

    def test_caller_inputs_are_not_mutated(self) -> None:
        supplied = self.base()
        before = copy.deepcopy(
            {
                name: value
                for name, value in supplied.items()
                if isinstance(value, (dict, list))
            }
        )
        result = assess_agent_execution_candidate_prerequisites(**supplied)
        after = {
            name: value
            for name, value in supplied.items()
            if isinstance(value, (dict, list))
        }
        self.assertTrue(result.valid)
        self.assertEqual(after, before)

    def test_repeat_calls_are_equal_and_publish_no_collection_of_candidates(self) -> None:
        first = self.assess()
        second = self.assess()
        self.assertEqual(first, second)
        self.assertFalse(hasattr(first, "candidates"))
        self.assertFalse(hasattr(first, "selected_candidate"))


class AgentExecutionCandidateBoundaryTests(AgentExecutionCandidateFixture):
    def test_runtime_path_performs_no_io_process_network_clock_or_persistence(self) -> None:
        forbidden = AssertionError("forbidden external operation")
        with (
            patch("builtins.open", side_effect=forbidden),
            patch("pathlib.Path.open", side_effect=forbidden),
            patch("pathlib.Path.read_text", side_effect=forbidden),
            patch("pathlib.Path.write_text", side_effect=forbidden),
            patch("socket.socket", side_effect=forbidden),
            patch("subprocess.run", side_effect=forbidden),
            patch("subprocess.Popen", side_effect=forbidden),
            patch("time.time", side_effect=forbidden),
            patch("time.monotonic", side_effect=forbidden),
            patch("urllib.request.urlopen", side_effect=forbidden),
            patch("sqlite3.connect", side_effect=forbidden),
        ):
            result = self.assess()
        self.assertEqual(result.outcome, AgentExecutionCandidatePrerequisiteOutcome.SATISFIED)

    def test_module_imports_only_pure_domain_dependencies(self) -> None:
        tree = ast.parse(
            (ROOT / "engineering_orchestration" /
             "agent_execution_candidate_prerequisite.py").read_text(
                encoding="utf-8"
            )
        )
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "asyncio",
                    "datetime",
                    "http",
                    "os",
                    "pathlib",
                    "requests",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "time",
                    "urllib",
                }
            )
        )

    def test_no_schema_storage_cli_or_package_root_export_is_added(self) -> None:
        schema_names = {
            "agent-execution-candidate-prerequisite.schema.json",
            "agent_execution_candidate_prerequisite.schema.json",
        }
        self.assertTrue(
            all(not (ROOT / "schemas" / name).exists() for name in schema_names)
        )
        self.assertFalse((ROOT / ".ai" / "candidates").exists())
        self.assertFalse(
            hasattr(
                engineering_orchestration,
                "assess_agent_execution_candidate_prerequisites",
            )
        )
        self.assertNotIn(
            "candidate",
            (ROOT / "engineering_orchestration" / "cli.py").read_text(
                encoding="utf-8"
            ).lower(),
        )

    def test_result_contract_has_no_selection_authority_or_execution_fields(self) -> None:
        names = {item.name for item in fields(AgentExecutionCandidatePrerequisiteResult)}
        self.assertTrue(
            names.isdisjoint(
                {
                    "candidate_id",
                    "selected",
                    "preferred",
                    "score",
                    "authorized",
                    "permitted",
                    "reserved",
                    "executable",
                    "executing",
                    "permissions",
                    "credentials",
                    "tools",
                    "execution_mode",
                    "execution_contract",
                    "timestamp",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
