"""Focused Agent Action Prerequisite Assessment tests."""

from __future__ import annotations

import ast
import builtins
import copy
from dataclasses import FrozenInstanceError, fields
from inspect import Parameter, signature
from pathlib import Path
import unittest
from unittest.mock import patch

import engineering_orchestration
import engineering_orchestration.agent_action_prerequisite as subject
from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteFinding,
    AgentActionPrerequisiteOutcome,
    AgentActionPrerequisiteReason,
    AgentActionPrerequisiteResult,
    assess_agent_action_prerequisites,
)
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationFinding,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteFinding,
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionFinding,
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
)
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityFinding,
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
    validate_runtime_operation_capability,
)


ROOT = Path(__file__).resolve().parents[1]
RESPONSIBILITY_KEY = (
    "AIO-040",
    "architecture-change",
    "implement",
    "software-engineer",
)
ACTOR_ID = "agent::assigned"
RUNTIME_OPTION_ID = "runtime::one"
OPTION_ID = "option::one"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
RESOURCE = "synthetic/input.txt"


def candidate(
    outcome: AgentExecutionCandidatePrerequisiteOutcome = (
        AgentExecutionCandidatePrerequisiteOutcome.SATISFIED
    ),
    *,
    actor_id: str = ACTOR_ID,
    runtime_option_id: str = RUNTIME_OPTION_ID,
    option_id: str = OPTION_ID,
) -> AgentExecutionCandidatePrerequisiteResult:
    """Build one observably coherent AIO-034 result."""

    reasons_by_outcome = {
        AgentExecutionCandidatePrerequisiteOutcome.SATISFIED: (
            AgentExecutionCandidatePrerequisiteReason.
            ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
        ),
        AgentExecutionCandidatePrerequisiteOutcome.BLOCKED: (
            AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
        ),
        AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED: (
            AgentExecutionCandidatePrerequisiteReason.ACTOR_AVAILABILITY_UNKNOWN,
        ),
    }
    return AgentExecutionCandidatePrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=RESPONSIBILITY_KEY,
        actor_id=actor_id,
        runtime_option_id=runtime_option_id,
        option_id=option_id,
        outcome=outcome,
        reasons=reasons_by_outcome[outcome],
    )


def capability(
    state: RuntimeOperationCapabilityState = (
        RuntimeOperationCapabilityState.PRESENT
    ),
    *,
    runtime_option_id: str = RUNTIME_OPTION_ID,
    operation_id: str = OPERATION_ID,
) -> RuntimeOperationCapabilityValidationResult:
    observation = RuntimeOperationCapabilityObservation(
        runtime_option_id,
        operation_id,
        state,
    )
    return RuntimeOperationCapabilityValidationResult(True, (), (observation,))


def permission(
    state: EnvironmentOperationPermissionState | None = (
        EnvironmentOperationPermissionState.ALLOWED
    ),
    *,
    runtime_option_id: str = RUNTIME_OPTION_ID,
    environment_id: str = ENVIRONMENT_ID,
    operation_id: str = OPERATION_ID,
    resource: str = RESOURCE,
) -> EnvironmentOperationPermissionValidationResult:
    if state is None:
        return EnvironmentOperationPermissionValidationResult(True, (), ())
    observation = EnvironmentOperationPermissionObservation(
        runtime_option_id,
        environment_id,
        operation_id,
        resource,
        state,
    )
    return EnvironmentOperationPermissionValidationResult(
        True,
        (),
        (observation,),
    )


def authorization(
    state: AgentExecutionAuthorizationState | None = (
        AgentExecutionAuthorizationState.GRANTED
    ),
    *,
    responsibility_key: tuple[str, str, str, str] = RESPONSIBILITY_KEY,
    actor_id: str = ACTOR_ID,
    runtime_option_id: str = RUNTIME_OPTION_ID,
    option_id: str = OPTION_ID,
    environment_id: str = ENVIRONMENT_ID,
    operation_id: str = OPERATION_ID,
    resource: str = RESOURCE,
) -> AgentExecutionAuthorizationValidationResult:
    if state is None:
        return AgentExecutionAuthorizationValidationResult(True, (), ())
    task_id, workflow_id, stage_id, role_id = responsibility_key
    evidence = AgentExecutionAuthorizationEvidence(
        task_id,
        workflow_id,
        stage_id,
        role_id,
        actor_id,
        runtime_option_id,
        option_id,
        environment_id,
        operation_id,
        resource,
        AgentExecutionAuthorizationAuthorityKind.HUMAN,
        "human::approver",
        "authorization::synthetic",
        state,
    )
    return AgentExecutionAuthorizationValidationResult(True, (), (evidence,))


class AgentActionPrerequisiteFixture(unittest.TestCase):
    """Synthetic fixture containing no live resource or execution handle."""

    def base(self) -> dict[str, object]:
        return {
            "candidate_result": candidate(),
            "requirement": OperationRequirement(OPERATION_ID, RESOURCE),
            "capability_result": capability(),
            "permission_result": permission(),
            "authorization_result": authorization(),
            "environment_id": ENVIRONMENT_ID,
        }

    def assess(self, **changes: object) -> AgentActionPrerequisiteResult:
        supplied = self.base()
        supplied.update(changes)
        return assess_agent_action_prerequisites(
            **supplied  # type: ignore[arg-type]
        )

    def assert_outcome(
        self,
        result: AgentActionPrerequisiteResult,
        outcome: AgentActionPrerequisiteOutcome,
        reasons: tuple[AgentActionPrerequisiteReason, ...],
    ) -> None:
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertIs(result.outcome, outcome)
        self.assertEqual(result.reasons, reasons)
        self.assertEqual(result.responsibility_key, RESPONSIBILITY_KEY)
        self.assertEqual(result.actor_id, ACTOR_ID)
        self.assertEqual(result.runtime_option_id, RUNTIME_OPTION_ID)
        self.assertEqual(result.option_id, OPTION_ID)
        self.assertEqual(result.environment_id, ENVIRONMENT_ID)
        self.assertEqual(result.operation_id, OPERATION_ID)
        self.assertEqual(result.resource, RESOURCE)

    def assert_atomic_invalid(
        self,
        result: AgentActionPrerequisiteResult,
        codes: list[str],
    ) -> None:
        self.assertFalse(result.valid)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.responsibility_key)
        self.assertIsNone(result.actor_id)
        self.assertIsNone(result.runtime_option_id)
        self.assertIsNone(result.option_id)
        self.assertIsNone(result.environment_id)
        self.assertIsNone(result.operation_id)
        self.assertIsNone(result.resource)
        self.assertIsNone(result.outcome)
        self.assertEqual(result.reasons, ())

    def assert_no_execution(
        self,
        result: AgentActionPrerequisiteResult,
    ) -> None:
        """Record the mandated per-scenario proof of no real execution."""

        forbidden_fields = {
            "assessment_id",
            "action_id",
            "candidate_id",
            "execution_id",
            "run_id",
            "execution_contract",
            "tool_binding",
            "command",
            "payload",
            "dispatch",
            "invocation",
            "consumed_at",
        }
        self.assertTrue(forbidden_fields.isdisjoint(vars(result)))
        exported = {name.lower() for name in vars(subject) if not name.startswith("__")}
        self.assertTrue(
            all(
                not any(
                    fragment in name
                    for fragment in ("execute", "dispatch", "invoke", "enforce")
                )
                for name in exported
            )
        )


class AgentActionPrerequisiteValueTests(AgentActionPrerequisiteFixture):
    def test_outcomes_are_exactly_the_locked_closed_vocabulary(self) -> None:
        self.assertEqual(
            [item.value for item in AgentActionPrerequisiteOutcome],
            ["satisfied", "blocked", "unresolved"],
        )

    def test_reasons_are_exactly_the_locked_ordered_vocabulary(self) -> None:
        self.assertEqual(
            [item.value for item in AgentActionPrerequisiteReason],
            [
                "candidate_prerequisites_blocked",
                "candidate_prerequisites_unresolved",
                "runtime_operation_capability_absent",
                "runtime_operation_capability_unknown",
                "environment_operation_permission_denied",
                "environment_operation_permission_unknown",
                "agent_execution_authorization_denied",
                "agent_execution_authorization_missing",
                "all_currently_modeled_action_prerequisites_satisfied",
            ],
        )

    def test_finding_and_result_fields_are_exact_frozen_and_tuple_backed(
        self,
    ) -> None:
        finding = AgentActionPrerequisiteFinding("example", "message")
        result = AgentActionPrerequisiteResult(
            False,
            (finding,),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            (),
        )
        self.assertEqual([item.name for item in fields(finding)], ["code", "message"])
        self.assertEqual(
            [item.name for item in fields(result)],
            [
                "valid",
                "findings",
                "responsibility_key",
                "actor_id",
                "runtime_option_id",
                "option_id",
                "environment_id",
                "operation_id",
                "resource",
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

    def test_public_signature_is_exactly_the_locked_composition_api(self) -> None:
        parameters = signature(assess_agent_action_prerequisites).parameters
        self.assertEqual(
            list(parameters),
            [
                "candidate_result",
                "requirement",
                "capability_result",
                "permission_result",
                "authorization_result",
                "environment_id",
            ],
        )
        self.assertTrue(
            all(
                parameters[name].kind is Parameter.POSITIONAL_OR_KEYWORD
                for name in list(parameters)[:5]
            )
        )
        self.assertIs(
            parameters["environment_id"].kind,
            Parameter.KEYWORD_ONLY,
        )
        self.assertTrue(
            all(item.default is item.empty for item in parameters.values())
        )

    def test_valid_result_is_exact_action_identity_without_synthetic_id(self) -> None:
        result = self.assess()
        self.assertEqual(
            (
                *result.responsibility_key,  # type: ignore[misc]
                result.actor_id,
                result.runtime_option_id,
                result.option_id,
                result.environment_id,
                result.operation_id,
                result.resource,
            ),
            (
                *RESPONSIBILITY_KEY,
                ACTOR_ID,
                RUNTIME_OPTION_ID,
                OPTION_ID,
                ENVIRONMENT_ID,
                OPERATION_ID,
                RESOURCE,
            ),
        )
        result_fields = {item.name for item in fields(result)}
        self.assertTrue(
            {
                "assessment_id",
                "action_id",
                "candidate_id",
                "execution_id",
                "run_id",
            }.isdisjoint(result_fields)
        )

    def test_no_redundant_assessment_value_or_package_root_exports(self) -> None:
        self.assertFalse(hasattr(subject, "AgentActionPrerequisiteAssessment"))
        for name in (
            "AgentActionPrerequisiteOutcome",
            "AgentActionPrerequisiteReason",
            "AgentActionPrerequisiteFinding",
            "AgentActionPrerequisiteResult",
            "assess_agent_action_prerequisites",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(engineering_orchestration, name))


class AgentActionPrerequisiteScenarioTests(AgentActionPrerequisiteFixture):
    """The 26 locked synthetic scenarios, each proving no real execution."""

    def test_scenario_01_all_positive_is_satisfied(self) -> None:
        result = self.assess()
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.SATISFIED,
            (
                AgentActionPrerequisiteReason.
                ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_02_candidate_blocked_with_positive_action_facts(self) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
            )
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,),
        )
        self.assert_no_execution(result)

    def test_scenario_03_candidate_unresolved_with_positive_action_facts(
        self,
    ) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            )
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,),
        )
        self.assert_no_execution(result)

    def test_scenario_04_candidate_unresolved_and_permission_denied(self) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            ),
            permission_result=permission(
                EnvironmentOperationPermissionState.DENIED
            ),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_DENIED,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_05_capability_absent_blocks(self) -> None:
        result = self.assess(
            capability_result=capability(RuntimeOperationCapabilityState.ABSENT)
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,),
        )
        self.assert_no_execution(result)

    def test_scenario_06_capability_unknown_is_unresolved(self) -> None:
        result = self.assess(
            capability_result=capability(RuntimeOperationCapabilityState.UNKNOWN)
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN,),
        )
        self.assert_no_execution(result)

    def test_scenario_07_permission_denied_blocks(self) -> None:
        result = self.assess(
            permission_result=permission(
                EnvironmentOperationPermissionState.DENIED
            )
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_DENIED,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_08_permission_unknown_is_unresolved(self) -> None:
        result = self.assess(
            permission_result=permission(
                EnvironmentOperationPermissionState.UNKNOWN
            )
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_09_authorization_denied_blocks(self) -> None:
        result = self.assess(
            authorization_result=authorization(
                AgentExecutionAuthorizationState.DENIED
            )
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_DENIED,),
        )
        self.assert_no_execution(result)

    def test_scenario_10_missing_authorization_is_unresolved(self) -> None:
        result = self.assess(authorization_result=authorization(None))
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,),
        )
        self.assert_no_execution(result)

    def test_scenario_11_capability_absent_retains_missing_authorization(
        self,
    ) -> None:
        result = self.assess(
            capability_result=capability(RuntimeOperationCapabilityState.ABSENT),
            authorization_result=authorization(None),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_MISSING,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_12_permission_denied_dominates_unknown_capability(
        self,
    ) -> None:
        result = self.assess(
            capability_result=capability(RuntimeOperationCapabilityState.UNKNOWN),
            permission_result=permission(
                EnvironmentOperationPermissionState.DENIED
            ),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN,
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_DENIED,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_13_authorization_denied_dominates_unknown_permission(
        self,
    ) -> None:
        result = self.assess(
            permission_result=permission(
                EnvironmentOperationPermissionState.UNKNOWN
            ),
            authorization_result=authorization(
                AgentExecutionAuthorizationState.DENIED
            ),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_DENIED,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_14_all_action_uncertainty_is_unresolved(self) -> None:
        result = self.assess(
            capability_result=capability(RuntimeOperationCapabilityState.UNKNOWN),
            permission_result=permission(
                EnvironmentOperationPermissionState.UNKNOWN
            ),
            authorization_result=authorization(None),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (
                AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN,
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_MISSING,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_15_wrong_operation_capability_pair_is_invalid(self) -> None:
        wrong_operation = self.assess(
            capability_result=capability(
                operation_id="repository_file_write",
            )
        )
        self.assert_atomic_invalid(
            wrong_operation,
            ["agent_action_prerequisite_capability_result_incoherent"],
        )
        self.assert_no_execution(wrong_operation)

        missing_required_pair = self.assess(
            capability_result=RuntimeOperationCapabilityValidationResult(
                True,
                (),
                (),
            )
        )
        self.assert_atomic_invalid(
            missing_required_pair,
            ["agent_action_prerequisite_capability_pair_missing"],
        )
        self.assertIn(
            RUNTIME_OPTION_ID,
            missing_required_pair.findings[0].message,
        )
        self.assertIn(OPERATION_ID, missing_required_pair.findings[0].message)
        self.assert_no_execution(missing_required_pair)

    def test_scenario_16_wrong_resource_permission_is_missing_and_unknown(
        self,
    ) -> None:
        result = self.assess(
            permission_result=permission(resource="synthetic/other.txt")
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
            ),
        )
        self.assert_no_execution(result)

    def test_scenario_17_wrong_environment_permission_is_invalid(self) -> None:
        result = self.assess(
            permission_result=permission(environment_id="environment::other")
        )
        self.assert_atomic_invalid(
            result,
            ["agent_action_prerequisite_permission_environment_mismatch"],
        )
        self.assertIn("environment::other", result.findings[0].message)
        self.assertIn(ENVIRONMENT_ID, result.findings[0].message)
        self.assert_no_execution(result)

    def test_scenario_18_wrong_actor_authorization_is_missing(self) -> None:
        result = self.assess(
            authorization_result=authorization(actor_id="agent::other")
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,),
        )
        self.assert_no_execution(result)

    def test_scenario_19_wrong_runtime_authorization_is_missing(self) -> None:
        result = self.assess(
            authorization_result=authorization(runtime_option_id="runtime::other")
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,),
        )
        self.assert_no_execution(result)

    def test_scenario_20_wrong_inference_authorization_is_missing(self) -> None:
        result = self.assess(
            authorization_result=authorization(option_id="option::other")
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,),
        )
        self.assert_no_execution(result)

    def test_scenario_21_invalid_conflicting_permission_propagates(self) -> None:
        parent_finding = EnvironmentOperationPermissionFinding(
            "conflicting_environment_operation_permission",
            "synthetic upstream permission conflict",
        )
        invalid_parent = EnvironmentOperationPermissionValidationResult(
            False,
            (parent_finding,),
            (),
        )
        result = self.assess(permission_result=invalid_parent)
        self.assert_atomic_invalid(
            result,
            ["conflicting_environment_operation_permission"],
        )
        self.assertEqual(result.findings[0].message, parent_finding.message)
        self.assert_no_execution(result)

    def test_scenario_22_invalid_conflicting_authorization_propagates(
        self,
    ) -> None:
        parent_finding = AgentExecutionAuthorizationFinding(
            "conflicting_agent_execution_authorization_evidence",
            "synthetic upstream authorization conflict",
        )
        invalid_parent = AgentExecutionAuthorizationValidationResult(
            False,
            (parent_finding,),
            (),
        )
        result = self.assess(authorization_result=invalid_parent)
        self.assert_atomic_invalid(
            result,
            ["conflicting_agent_execution_authorization_evidence"],
        )
        self.assertEqual(result.findings[0].message, parent_finding.message)
        self.assert_no_execution(result)

    def test_scenario_23_human_assignment_boundary_propagates(self) -> None:
        boundary = AgentExecutionCandidatePrerequisiteFinding(
            "agent_execution_candidate_not_applicable_to_human_actor",
            "Synthetic Human Assignment is outside the Agent-only boundary.",
        )
        invalid_candidate = AgentExecutionCandidatePrerequisiteResult(
            False,
            (boundary,),
            None,
            None,
            None,
            None,
            None,
            (),
        )
        result = self.assess(candidate_result=invalid_candidate)
        self.assert_atomic_invalid(
            result,
            ["agent_execution_candidate_not_applicable_to_human_actor"],
        )
        self.assertEqual(result.findings[0].message, boundary.message)
        self.assert_no_execution(result)

    def test_scenario_24_task_human_approval_does_not_supply_authorization(
        self,
    ) -> None:
        task_human_approval = "approved"
        result = self.assess(authorization_result=authorization(None))
        self.assertEqual(task_human_approval, "approved")
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,),
        )
        self.assert_no_execution(result)

    def test_scenario_25_satisfied_authority_remains_caller_attested(self) -> None:
        parent = authorization()
        result = self.assess(authorization_result=parent)
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.SATISFIED,
            (
                AgentActionPrerequisiteReason.
                ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED,
            ),
        )
        evidence = parent.normalized_evidence[0]
        self.assertEqual(evidence.authority_id, "human::approver")
        self.assertFalse(hasattr(evidence, "authenticated"))
        self.assertFalse(hasattr(result, "trusted_authority"))
        self.assert_no_execution(result)

    def test_scenario_26_satisfied_has_no_contract_binding_or_run(self) -> None:
        result = self.assess()
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.SATISFIED,
            (
                AgentActionPrerequisiteReason.
                ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED,
            ),
        )
        self.assertFalse(hasattr(result, "execution_contract"))
        self.assertFalse(hasattr(result, "tool_binding"))
        self.assertFalse(hasattr(result, "execution_run"))
        self.assert_no_execution(result)

    def test_matrix_contains_exactly_26_explicit_scenarios(self) -> None:
        scenario_names = {
            name
            for name in vars(type(self))
            if name.startswith("test_scenario_")
        }
        self.assertEqual(len(scenario_names), 26)


class AgentActionPrerequisiteCompositionTests(AgentActionPrerequisiteFixture):
    def test_all_blocker_uncertainty_categories_retain_canonical_order(
        self,
    ) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            ),
            capability_result=capability(RuntimeOperationCapabilityState.ABSENT),
            permission_result=permission(
                EnvironmentOperationPermissionState.UNKNOWN
            ),
            authorization_result=authorization(None),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.BLOCKED,
            (
                AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,
                AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT,
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_MISSING,
            ),
        )

    def test_each_explicit_blocker_dominates_all_other_uncertainty(self) -> None:
        cases = (
            {
                "candidate_result": candidate(
                    AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
                ),
                "capability_result": capability(
                    RuntimeOperationCapabilityState.UNKNOWN
                ),
                "permission_result": permission(
                    EnvironmentOperationPermissionState.UNKNOWN
                ),
                "authorization_result": authorization(None),
            },
            {
                "candidate_result": candidate(
                    AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
                ),
                "capability_result": capability(
                    RuntimeOperationCapabilityState.ABSENT
                ),
                "permission_result": permission(
                    EnvironmentOperationPermissionState.UNKNOWN
                ),
                "authorization_result": authorization(None),
            },
            {
                "candidate_result": candidate(
                    AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
                ),
                "capability_result": capability(
                    RuntimeOperationCapabilityState.UNKNOWN
                ),
                "permission_result": permission(
                    EnvironmentOperationPermissionState.DENIED
                ),
                "authorization_result": authorization(None),
            },
            {
                "candidate_result": candidate(
                    AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
                ),
                "capability_result": capability(
                    RuntimeOperationCapabilityState.UNKNOWN
                ),
                "permission_result": permission(
                    EnvironmentOperationPermissionState.UNKNOWN
                ),
                "authorization_result": authorization(
                    AgentExecutionAuthorizationState.DENIED
                ),
            },
        )
        for supplied in cases:
            with self.subTest(supplied=supplied):
                result = self.assess(**supplied)
                self.assertTrue(result.valid)
                self.assertIs(result.outcome, AgentActionPrerequisiteOutcome.BLOCKED)
                self.assertGreaterEqual(len(result.reasons), 4)

    def test_all_uncertainty_without_blocker_is_unresolved(self) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            ),
            capability_result=capability(RuntimeOperationCapabilityState.UNKNOWN),
            permission_result=permission(None),
            authorization_result=authorization(None),
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            (
                AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,
                AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN,
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_MISSING,
            ),
        )

    def test_exact_lookup_is_case_sensitive_for_every_action_scope(self) -> None:
        cases = (
            {"candidate_result": candidate(runtime_option_id="Runtime::one")},
            {
                "permission_result": permission(
                    resource="Synthetic/input.txt"
                )
            },
            {
                "authorization_result": authorization(
                    actor_id="Agent::assigned"
                )
            },
        )
        expected = (
            None,
            AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN,
            AgentActionPrerequisiteReason.AGENT_EXECUTION_AUTHORIZATION_MISSING,
        )
        for supplied, expected_reason in zip(cases, expected, strict=True):
            with self.subTest(supplied=supplied):
                result = self.assess(**supplied)
                if expected_reason is None:
                    self.assert_atomic_invalid(
                        result,
                        ["agent_action_prerequisite_capability_pair_missing"],
                    )
                else:
                    self.assertTrue(result.valid)
                    self.assertIn(expected_reason, result.reasons)

    def test_repeated_assessment_is_deterministic_and_does_not_mutate_inputs(
        self,
    ) -> None:
        supplied = self.base()
        before = copy.deepcopy(supplied)
        first = assess_agent_action_prerequisites(
            **supplied  # type: ignore[arg-type]
        )
        second = assess_agent_action_prerequisites(
            **supplied  # type: ignore[arg-type]
        )
        self.assertEqual(first, second)
        self.assertEqual(supplied, before)

    def test_unrelated_canonical_parent_values_do_not_change_exact_lookup(
        self,
    ) -> None:
        target_permission = permission().normalized_observations[0]
        unrelated_permission = EnvironmentOperationPermissionObservation(
            "runtime::two",
            ENVIRONMENT_ID,
            OPERATION_ID,
            RESOURCE,
            EnvironmentOperationPermissionState.DENIED,
        )
        permission_result = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (target_permission, unrelated_permission),
        )

        target_authorization = authorization().normalized_evidence[0]
        unrelated_authorization = authorization(
            actor_id="agent::later"
        ).normalized_evidence[0]
        authorization_result = AgentExecutionAuthorizationValidationResult(
            True,
            (),
            (target_authorization, unrelated_authorization),
        )
        result = self.assess(
            permission_result=permission_result,
            authorization_result=authorization_result,
        )
        self.assert_outcome(
            result,
            AgentActionPrerequisiteOutcome.SATISFIED,
            (
                AgentActionPrerequisiteReason.
                ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED,
            ),
        )


class AgentActionPrerequisiteInvalidInputTests(AgentActionPrerequisiteFixture):
    def test_owned_invalid_type_messages_are_exact_and_category_ordered(
        self,
    ) -> None:
        result = self.assess(
            candidate_result=object(),
            requirement=object(),
            environment_id="",
            capability_result=object(),
            permission_result=object(),
            authorization_result=object(),
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_action_prerequisite_candidate_result_invalid_type",
                "operation_requirement_invalid_type",
                "agent_action_prerequisite_environment_id_invalid",
                "agent_action_prerequisite_capability_result_invalid_type",
                "agent_action_prerequisite_permission_result_invalid_type",
                "agent_action_prerequisite_authorization_result_invalid_type",
            ],
        )
        self.assertEqual(
            [finding.message for finding in result.findings],
            [
                "candidate_result must be an exact "
                "AgentExecutionCandidatePrerequisiteResult value.",
                "Operation Requirement must be an exact OperationRequirement value.",
                "Agent Action Prerequisite Assessment environment_id must be an "
                "exact nonempty string.",
                "capability_result must be an exact "
                "RuntimeOperationCapabilityValidationResult value.",
                "permission_result must be an exact "
                "EnvironmentOperationPermissionValidationResult value.",
                "authorization_result must be an exact "
                "AgentExecutionAuthorizationValidationResult value.",
            ],
        )

    def test_coherent_invalid_parent_findings_propagate_in_category_order(
        self,
    ) -> None:
        candidate_findings = (
            AgentExecutionCandidatePrerequisiteFinding("candidate-a", "A"),
            AgentExecutionCandidatePrerequisiteFinding("candidate-b", "B"),
        )
        invalid_candidate = AgentExecutionCandidatePrerequisiteResult(
            False,
            candidate_findings,
            None,
            None,
            None,
            None,
            None,
            (),
        )
        capability_finding = RuntimeOperationCapabilityFinding("capability", "C")
        invalid_capability = RuntimeOperationCapabilityValidationResult(
            False,
            (capability_finding,),
            (),
        )
        permission_finding = EnvironmentOperationPermissionFinding(
            "permission",
            "P",
        )
        invalid_permission = EnvironmentOperationPermissionValidationResult(
            False,
            (permission_finding,),
            (),
        )
        authorization_finding = AgentExecutionAuthorizationFinding(
            "authorization",
            "Z",
        )
        invalid_authorization = AgentExecutionAuthorizationValidationResult(
            False,
            (authorization_finding,),
            (),
        )
        result = self.assess(
            candidate_result=invalid_candidate,
            capability_result=invalid_capability,
            permission_result=invalid_permission,
            authorization_result=invalid_authorization,
        )
        self.assert_atomic_invalid(
            result,
            ["candidate-a", "candidate-b", "capability", "permission", "authorization"],
        )
        self.assertEqual(
            [finding.message for finding in result.findings],
            ["A", "B", "C", "P", "Z"],
        )

    def test_repeated_canonical_parent_findings_propagate_unchanged(
        self,
    ) -> None:
        parent = validate_runtime_operation_capability(
            (
                RuntimeOperationCapabilityObservation(
                    RUNTIME_OPTION_ID,
                    "Malformed-One",
                    RuntimeOperationCapabilityState.PRESENT,
                ),
                RuntimeOperationCapabilityObservation(
                    RUNTIME_OPTION_ID,
                    "Malformed-Two",
                    RuntimeOperationCapabilityState.PRESENT,
                ),
            ),
            (AgentRuntimeOptionDefinition(RUNTIME_OPTION_ID),),
        )
        self.assertFalse(parent.valid)
        self.assertEqual(
            [finding.code for finding in parent.findings],
            ["operation_id_invalid_syntax", "operation_id_invalid_syntax"],
        )
        self.assertEqual(parent.findings[0], parent.findings[1])

        result = self.assess(capability_result=parent)
        self.assert_atomic_invalid(
            result,
            ["operation_id_invalid_syntax", "operation_id_invalid_syntax"],
        )
        self.assertEqual(
            [finding.message for finding in result.findings],
            [finding.message for finding in parent.findings],
        )

    def test_malformed_freely_constructed_parent_containers_are_incoherent(
        self,
    ) -> None:
        malformed_candidate = AgentExecutionCandidatePrerequisiteResult(
            True,
            (),
            RESPONSIBILITY_KEY,
            ACTOR_ID,
            RUNTIME_OPTION_ID,
            OPTION_ID,
            AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
            (),
        )
        malformed_capability = RuntimeOperationCapabilityValidationResult(
            True,
            (),
            (object(),),  # type: ignore[arg-type]
        )
        malformed_permission = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (object(),),  # type: ignore[arg-type]
        )
        malformed_authorization = AgentExecutionAuthorizationValidationResult(
            True,
            (),
            (object(),),  # type: ignore[arg-type]
        )
        cases = (
            (
                {"candidate_result": malformed_candidate},
                "agent_action_prerequisite_candidate_result_incoherent",
            ),
            (
                {"capability_result": malformed_capability},
                "agent_action_prerequisite_capability_result_incoherent",
            ),
            (
                {"permission_result": malformed_permission},
                "agent_action_prerequisite_permission_result_incoherent",
            ),
            (
                {"authorization_result": malformed_authorization},
                "agent_action_prerequisite_authorization_result_incoherent",
            ),
        )
        for supplied, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self.assert_atomic_invalid(
                    self.assess(**supplied),
                    [expected_code],
                )

    def test_exact_result_types_reject_subclasses(self) -> None:
        class DerivedCandidateResult(AgentExecutionCandidatePrerequisiteResult):
            pass

        class DerivedCapabilityResult(RuntimeOperationCapabilityValidationResult):
            pass

        class DerivedPermissionResult(
            EnvironmentOperationPermissionValidationResult
        ):
            pass

        class DerivedAuthorizationResult(
            AgentExecutionAuthorizationValidationResult
        ):
            pass

        original_candidate = candidate()
        original_capability = capability()
        original_permission = permission()
        original_authorization = authorization()
        cases = (
            (
                {
                    "candidate_result": DerivedCandidateResult(
                        *(
                            getattr(original_candidate, item.name)
                            for item in fields(original_candidate)
                        )
                    )
                },
                "agent_action_prerequisite_candidate_result_invalid_type",
            ),
            (
                {
                    "capability_result": DerivedCapabilityResult(
                        *(
                            getattr(original_capability, item.name)
                            for item in fields(original_capability)
                        )
                    )
                },
                "agent_action_prerequisite_capability_result_invalid_type",
            ),
            (
                {
                    "permission_result": DerivedPermissionResult(
                        *(
                            getattr(original_permission, item.name)
                            for item in fields(original_permission)
                        )
                    )
                },
                "agent_action_prerequisite_permission_result_invalid_type",
            ),
            (
                {
                    "authorization_result": DerivedAuthorizationResult(
                        *(
                            getattr(original_authorization, item.name)
                            for item in fields(original_authorization)
                        )
                    )
                },
                "agent_action_prerequisite_authorization_result_invalid_type",
            ),
        )
        for supplied, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self.assert_atomic_invalid(
                    self.assess(**supplied),
                    [expected_code],
                )

    def test_exact_environment_and_requirement_types_are_required(self) -> None:
        class DerivedEnvironment(str):
            pass

        class DerivedRequirement(OperationRequirement):
            pass

        result = self.assess(
            requirement=DerivedRequirement(OPERATION_ID, RESOURCE),
            environment_id=DerivedEnvironment(ENVIRONMENT_ID),
        )
        self.assert_atomic_invalid(
            result,
            [
                "operation_requirement_invalid_type",
                "agent_action_prerequisite_environment_id_invalid",
            ],
        )

    def test_malformed_valid_and_invalid_atomicity_flags_are_rejected(self) -> None:
        malformed_candidate = AgentExecutionCandidatePrerequisiteResult(
            False,
            (),
            RESPONSIBILITY_KEY,
            ACTOR_ID,
            RUNTIME_OPTION_ID,
            OPTION_ID,
            AgentExecutionCandidatePrerequisiteOutcome.BLOCKED,
            (AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,),
        )
        malformed_capability = RuntimeOperationCapabilityValidationResult(
            False,
            (RuntimeOperationCapabilityFinding("upstream", "invalid"),),
            capability().normalized_observations,
        )
        malformed_permission = EnvironmentOperationPermissionValidationResult(
            True,
            (EnvironmentOperationPermissionFinding("unexpected", "finding"),),
            (),
        )
        malformed_authorization = AgentExecutionAuthorizationValidationResult(
            False,
            (),
            (),
        )
        result = self.assess(
            candidate_result=malformed_candidate,
            capability_result=malformed_capability,
            permission_result=malformed_permission,
            authorization_result=malformed_authorization,
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_action_prerequisite_candidate_result_incoherent",
                "agent_action_prerequisite_capability_result_incoherent",
                "agent_action_prerequisite_permission_result_incoherent",
                "agent_action_prerequisite_authorization_result_incoherent",
            ],
        )

    def test_duplicate_or_noncanonical_parent_payloads_are_incoherent(self) -> None:
        cap_observation = capability().normalized_observations[0]
        duplicate_capability = RuntimeOperationCapabilityValidationResult(
            True,
            (),
            (cap_observation, cap_observation),
        )
        permission_observation = permission().normalized_observations[0]
        duplicate_permission = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (permission_observation, permission_observation),
        )
        authorization_evidence = authorization().normalized_evidence[0]
        duplicate_authorization = AgentExecutionAuthorizationValidationResult(
            True,
            (),
            (authorization_evidence, authorization_evidence),
        )

        other_capability_observation = RuntimeOperationCapabilityObservation(
            "runtime::zero",
            OPERATION_ID,
            RuntimeOperationCapabilityState.PRESENT,
        )
        unsorted_capability = RuntimeOperationCapabilityValidationResult(
            True,
            (),
            (other_capability_observation, cap_observation),
        )
        other_permission_observation = EnvironmentOperationPermissionObservation(
            "runtime::zero",
            ENVIRONMENT_ID,
            OPERATION_ID,
            RESOURCE,
            EnvironmentOperationPermissionState.ALLOWED,
        )
        unsorted_permission = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (other_permission_observation, permission_observation),
        )
        other_authorization_evidence = authorization(
            actor_id="agent::later"
        ).normalized_evidence[0]
        unsorted_authorization = AgentExecutionAuthorizationValidationResult(
            True,
            (),
            (other_authorization_evidence, authorization_evidence),
        )
        cases = (
            (
                {"capability_result": duplicate_capability},
                "agent_action_prerequisite_capability_result_incoherent",
            ),
            (
                {"permission_result": duplicate_permission},
                "agent_action_prerequisite_permission_result_incoherent",
            ),
            (
                {"authorization_result": duplicate_authorization},
                "agent_action_prerequisite_authorization_result_incoherent",
            ),
            (
                {"capability_result": unsorted_capability},
                "agent_action_prerequisite_capability_result_incoherent",
            ),
            (
                {"permission_result": unsorted_permission},
                "agent_action_prerequisite_permission_result_incoherent",
            ),
            (
                {"authorization_result": unsorted_authorization},
                "agent_action_prerequisite_authorization_result_incoherent",
            ),
        )
        for supplied, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                self.assert_atomic_invalid(
                    self.assess(**supplied),
                    [expected_code],
                )

    def test_cross_coherence_findings_are_aggregated_in_locked_order(self) -> None:
        result = self.assess(
            capability_result=capability(runtime_option_id="runtime::other"),
            permission_result=permission(environment_id="environment::other"),
            authorization_result=authorization(
                environment_id="environment::other"
            ),
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_action_prerequisite_capability_pair_missing",
                "agent_action_prerequisite_permission_environment_mismatch",
                "agent_action_prerequisite_authorization_environment_mismatch",
            ],
        )

    def test_available_cross_findings_survive_unrelated_invalid_parents(
        self,
    ) -> None:
        invalid_capability = RuntimeOperationCapabilityValidationResult(
            False,
            (
                RuntimeOperationCapabilityFinding(
                    "invalid-capability-parent",
                    "Synthetic invalid capability parent.",
                ),
            ),
            (),
        )
        invalid_permission = EnvironmentOperationPermissionValidationResult(
            False,
            (
                EnvironmentOperationPermissionFinding(
                    "invalid-permission-parent",
                    "Synthetic invalid permission parent.",
                ),
            ),
            (),
        )
        invalid_authorization = AgentExecutionAuthorizationValidationResult(
            False,
            (
                AgentExecutionAuthorizationFinding(
                    "invalid-authorization-parent",
                    "Synthetic invalid authorization parent.",
                ),
            ),
            (),
        )
        cases = (
            (
                {
                    "capability_result": (
                        RuntimeOperationCapabilityValidationResult(True, (), ())
                    ),
                    "permission_result": invalid_permission,
                },
                [
                    "invalid-permission-parent",
                    "agent_action_prerequisite_capability_pair_missing",
                ],
            ),
            (
                {
                    "permission_result": permission(
                        environment_id="environment::other"
                    ),
                    "authorization_result": invalid_authorization,
                },
                [
                    "invalid-authorization-parent",
                    "agent_action_prerequisite_permission_environment_mismatch",
                ],
            ),
            (
                {
                    "capability_result": invalid_capability,
                    "authorization_result": authorization(
                        environment_id="environment::other"
                    ),
                },
                [
                    "invalid-capability-parent",
                    "agent_action_prerequisite_authorization_environment_mismatch",
                ],
            ),
        )
        for supplied, expected_codes in cases:
            with self.subTest(expected_codes=expected_codes):
                self.assert_atomic_invalid(
                    self.assess(**supplied),
                    expected_codes,
                )

    def test_wrong_environment_authorization_is_invalid_not_missing(self) -> None:
        result = self.assess(
            authorization_result=authorization(
                environment_id="environment::other"
            )
        )
        self.assert_atomic_invalid(
            result,
            ["agent_action_prerequisite_authorization_environment_mismatch"],
        )

    def test_runtime_owned_or_wildcard_inference_cannot_enter_composition(
        self,
    ) -> None:
        runtime_owned = AgentExecutionCandidatePrerequisiteResult(
            True,
            (),
            RESPONSIBILITY_KEY,
            ACTOR_ID,
            RUNTIME_OPTION_ID,
            None,  # type: ignore[arg-type]
            AgentExecutionCandidatePrerequisiteOutcome.SATISFIED,
            (
                AgentExecutionCandidatePrerequisiteReason.
                ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
            ),
        )
        self.assert_atomic_invalid(
            self.assess(candidate_result=runtime_owned),
            ["agent_action_prerequisite_candidate_result_incoherent"],
        )


class AgentActionPrerequisiteSafetyBoundaryTests(
    AgentActionPrerequisiteFixture
):
    def test_static_module_has_no_io_discovery_execution_policy_or_clock_calls(
        self,
    ) -> None:
        tree = ast.parse(
            (ROOT / "engineering_orchestration" /
             "agent_action_prerequisite.py").read_text(encoding="utf-8")
        )
        imported_roots: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "datetime",
                    "os",
                    "pathlib",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "time",
                    "urllib",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "resolve",
                    "stat",
                    "listdir",
                    "scandir",
                    "getenv",
                    "system",
                    "run",
                    "Popen",
                    "time",
                    "dispatch",
                    "execute",
                    "invoke",
                    "enforce",
                }
            )
        )

    def test_dynamic_assessment_performs_no_file_open(self) -> None:
        with patch.object(
            builtins,
            "open",
            side_effect=AssertionError("assessment attempted file I/O"),
        ):
            result = self.assess()
        self.assertTrue(result.valid)

    def test_module_exposes_no_lookup_decision_authority_or_execution_api(
        self,
    ) -> None:
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("__")
        }
        forbidden_fragments = (
            "lookup",
            "permission_decision",
            "policy",
            "authenticate",
            "issue_authorization",
            "consume",
            "replay",
            "dispatch",
            "execute",
            "invoke",
            "enforce",
        )
        self.assertTrue(
            all(
                not any(fragment in name for fragment in forbidden_fragments)
                for name in exported
            )
        )


if __name__ == "__main__":
    unittest.main()
