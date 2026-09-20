"""Focused tests for the internal read-only execution-preparation dry run."""

from __future__ import annotations

import ast
import asyncio
import builtins
import copy
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, fields, replace
import glob
import http.client
import importlib.util
import io
from inspect import Parameter, signature
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import time
from typing import get_type_hints
import unittest
from unittest.mock import patch
import urllib.request

import engineering_orchestration
import engineering_orchestration._read_only_execution_preparation as subject
from engineering_orchestration._read_only_execution_preparation import (
    ReadOnlyExecutionAuthorizationEvidence,
    ReadOnlyExecutionAuthorizationSource,
    ReadOnlyExecutionAuthorizationState,
    ReadOnlyExecutionCapabilityEvidence,
    ReadOnlyExecutionCapabilityState,
    ReadOnlyExecutionPermissionEvidence,
    ReadOnlyExecutionPermissionFreshness,
    ReadOnlyExecutionPermissionState,
    ReadOnlyExecutionPreparationFinding,
    ReadOnlyExecutionPreparationOutcome,
    ReadOnlyExecutionPreparationReason,
    ReadOnlyExecutionPreparationResult,
    assess_read_only_execution_preparation,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteFinding,
    AgentExecutionCandidatePrerequisiteOutcome,
    AgentExecutionCandidatePrerequisiteReason,
    AgentExecutionCandidatePrerequisiteResult,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "engineering_orchestration"
    / "_read_only_execution_preparation.py"
)
OPERATION_ID = "repository_file_read"
RESOURCE = "workflows/README.md"
ENVIRONMENT_ID = "environment::workspace"
RESPONSIBILITY_KEY = (
    "AIO-035",
    "security-sensitive-change",
    "implement",
    "software-engineer",
)
ACTOR_ID = "agent::assigned"
RUNTIME_OPTION_ID = "runtime::one"
OPTION_ID = "option::one"


def candidate(
    outcome: AgentExecutionCandidatePrerequisiteOutcome = (
        AgentExecutionCandidatePrerequisiteOutcome.SATISFIED
    ),
) -> AgentExecutionCandidatePrerequisiteResult:
    """Return one coherent upstream result for the requested ordinary outcome."""

    reasons = {
        AgentExecutionCandidatePrerequisiteOutcome.SATISFIED: (
            AgentExecutionCandidatePrerequisiteReason.
            ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
        ),
        AgentExecutionCandidatePrerequisiteOutcome.BLOCKED: (
            AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
        ),
        AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED: (
            AgentExecutionCandidatePrerequisiteReason.
            ACTOR_AVAILABILITY_UNKNOWN,
        ),
    }[outcome]
    return AgentExecutionCandidatePrerequisiteResult(
        valid=True,
        findings=(),
        responsibility_key=RESPONSIBILITY_KEY,
        actor_id=ACTOR_ID,
        runtime_option_id=RUNTIME_OPTION_ID,
        option_id=OPTION_ID,
        outcome=outcome,
        reasons=reasons,
    )


def invalid_candidate() -> AgentExecutionCandidatePrerequisiteResult:
    """Return one coherent atomic-invalid upstream result."""

    return AgentExecutionCandidatePrerequisiteResult(
        valid=False,
        findings=(
            AgentExecutionCandidatePrerequisiteFinding(
                code="upstream_invalid",
                message="Synthetic invalid upstream result.",
            ),
        ),
        responsibility_key=None,
        actor_id=None,
        runtime_option_id=None,
        option_id=None,
        outcome=None,
        reasons=(),
    )


def capability(
    state: ReadOnlyExecutionCapabilityState = (
        ReadOnlyExecutionCapabilityState.PRESENT
    ),
    **changes: object,
) -> ReadOnlyExecutionCapabilityEvidence:
    values: dict[str, object] = {
        "runtime_option_id": RUNTIME_OPTION_ID,
        "operation_id": OPERATION_ID,
        "state": state,
    }
    values.update(changes)
    return ReadOnlyExecutionCapabilityEvidence(**values)  # type: ignore[arg-type]


def permission(
    state: ReadOnlyExecutionPermissionState = (
        ReadOnlyExecutionPermissionState.ALLOWED
    ),
    freshness: ReadOnlyExecutionPermissionFreshness = (
        ReadOnlyExecutionPermissionFreshness.CURRENT
    ),
    **changes: object,
) -> ReadOnlyExecutionPermissionEvidence:
    values: dict[str, object] = {
        "runtime_option_id": RUNTIME_OPTION_ID,
        "environment_id": ENVIRONMENT_ID,
        "operation_id": OPERATION_ID,
        "resource": RESOURCE,
        "state": state,
        "freshness": freshness,
    }
    values.update(changes)
    return ReadOnlyExecutionPermissionEvidence(**values)  # type: ignore[arg-type]


def authorization(
    state: ReadOnlyExecutionAuthorizationState = (
        ReadOnlyExecutionAuthorizationState.GRANTED
    ),
    source: ReadOnlyExecutionAuthorizationSource = (
        ReadOnlyExecutionAuthorizationSource.HUMAN_PROVIDED
    ),
    **changes: object,
) -> ReadOnlyExecutionAuthorizationEvidence:
    values: dict[str, object] = {
        "task_id": RESPONSIBILITY_KEY[0],
        "workflow_id": RESPONSIBILITY_KEY[1],
        "stage_id": RESPONSIBILITY_KEY[2],
        "role_id": RESPONSIBILITY_KEY[3],
        "actor_id": ACTOR_ID,
        "runtime_option_id": RUNTIME_OPTION_ID,
        "option_id": OPTION_ID,
        "environment_id": ENVIRONMENT_ID,
        "operation_id": OPERATION_ID,
        "resource": RESOURCE,
        "source": source,
        "state": state,
    }
    values.update(changes)
    return ReadOnlyExecutionAuthorizationEvidence(**values)  # type: ignore[arg-type]


def missing_authorization() -> ReadOnlyExecutionAuthorizationEvidence:
    return authorization(
        ReadOnlyExecutionAuthorizationState.MISSING,
        ReadOnlyExecutionAuthorizationSource.NOT_SUPPLIED,
    )


class ReadOnlyExecutionPreparationFixture(unittest.TestCase):
    """Shared assertions and exact positive inputs."""

    def base(self) -> dict[str, object]:
        return {
            "candidate_result": candidate(),
            "operation_id": OPERATION_ID,
            "resource": RESOURCE,
            "environment_id": ENVIRONMENT_ID,
            "capability_evidence": capability(),
            "permission_evidence": permission(),
            "authorization_evidence": authorization(),
        }

    def assess(self, **changes: object) -> ReadOnlyExecutionPreparationResult:
        supplied = self.base()
        supplied.update(changes)
        return assess_read_only_execution_preparation(
            **supplied,  # type: ignore[arg-type]
        )

    def assert_valid_result(
        self,
        result: ReadOnlyExecutionPreparationResult,
        outcome: ReadOnlyExecutionPreparationOutcome,
        reasons: tuple[ReadOnlyExecutionPreparationReason, ...],
    ) -> None:
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.outcome, outcome)
        self.assertEqual(result.reasons, reasons)
        self.assertIsNotNone(result.candidate_result)
        self.assertEqual(result.operation_id, OPERATION_ID)
        self.assertEqual(result.resource, RESOURCE)
        self.assertEqual(result.environment_id, ENVIRONMENT_ID)
        self.assertIsNotNone(result.capability_evidence)
        self.assertIsNotNone(result.permission_evidence)
        self.assertIsNotNone(result.authorization_evidence)

    def assert_atomic_invalid(
        self,
        result: ReadOnlyExecutionPreparationResult,
        codes: list[str],
    ) -> None:
        self.assertFalse(result.valid)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(all(finding.message for finding in result.findings))
        self.assertIsNone(result.candidate_result)
        self.assertIsNone(result.operation_id)
        self.assertIsNone(result.resource)
        self.assertIsNone(result.environment_id)
        self.assertIsNone(result.capability_evidence)
        self.assertIsNone(result.permission_evidence)
        self.assertIsNone(result.authorization_evidence)
        self.assertIsNone(result.outcome)
        self.assertEqual(result.reasons, ())


class ReadOnlyExecutionPreparationContractTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_function_signature_and_annotations_are_locked(self) -> None:
        api = signature(assess_read_only_execution_preparation)
        self.assertEqual(
            list(api.parameters),
            [
                "candidate_result",
                "operation_id",
                "resource",
                "environment_id",
                "capability_evidence",
                "permission_evidence",
                "authorization_evidence",
            ],
        )
        self.assertEqual(
            [parameter.kind for parameter in api.parameters.values()],
            [
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.KEYWORD_ONLY,
                Parameter.KEYWORD_ONLY,
                Parameter.KEYWORD_ONLY,
                Parameter.KEYWORD_ONLY,
                Parameter.KEYWORD_ONLY,
                Parameter.KEYWORD_ONLY,
            ],
        )
        hints = get_type_hints(assess_read_only_execution_preparation)
        self.assertIs(
            hints["candidate_result"],
            AgentExecutionCandidatePrerequisiteResult,
        )
        self.assertIs(hints["operation_id"], str)
        self.assertIs(hints["resource"], str)
        self.assertIs(hints["environment_id"], str)
        self.assertIs(
            hints["capability_evidence"],
            ReadOnlyExecutionCapabilityEvidence,
        )
        self.assertIs(
            hints["permission_evidence"],
            ReadOnlyExecutionPermissionEvidence,
        )
        self.assertIs(
            hints["authorization_evidence"],
            ReadOnlyExecutionAuthorizationEvidence,
        )
        self.assertIs(hints["return"], ReadOnlyExecutionPreparationResult)

    def test_enum_members_values_and_declaration_order_are_locked(self) -> None:
        expectations = {
            ReadOnlyExecutionCapabilityState: [
                ("PRESENT", "present"),
                ("ABSENT", "absent"),
                ("UNKNOWN", "unknown"),
            ],
            ReadOnlyExecutionPermissionState: [
                ("ALLOWED", "allowed"),
                ("DENIED", "denied"),
                ("UNKNOWN", "unknown"),
            ],
            ReadOnlyExecutionPermissionFreshness: [
                ("CURRENT", "current"),
                ("STALE", "stale"),
                ("UNKNOWN", "unknown"),
            ],
            ReadOnlyExecutionAuthorizationState: [
                ("GRANTED", "granted"),
                ("DENIED", "denied"),
                ("MISSING", "missing"),
            ],
            ReadOnlyExecutionAuthorizationSource: [
                ("HUMAN_PROVIDED", "human_provided"),
                ("POLICY_PROVIDED", "policy_provided"),
                ("NOT_SUPPLIED", "not_supplied"),
            ],
            ReadOnlyExecutionPreparationOutcome: [
                ("POTENTIALLY_EXECUTABLE", "potentially_executable"),
                ("BLOCKED", "blocked"),
                ("UNRESOLVED", "unresolved"),
            ],
            ReadOnlyExecutionPreparationReason: [
                (
                    "CANDIDATE_PREREQUISITES_BLOCKED",
                    "candidate_prerequisites_blocked",
                ),
                (
                    "CANDIDATE_PREREQUISITES_UNRESOLVED",
                    "candidate_prerequisites_unresolved",
                ),
                ("CAPABILITY_SCOPE_MISMATCH", "capability_scope_mismatch"),
                ("CAPABILITY_ABSENT", "capability_absent"),
                ("CAPABILITY_UNKNOWN", "capability_unknown"),
                ("PERMISSION_SCOPE_MISMATCH", "permission_scope_mismatch"),
                ("PERMISSION_STALE", "permission_stale"),
                (
                    "PERMISSION_FRESHNESS_UNKNOWN",
                    "permission_freshness_unknown",
                ),
                ("PERMISSION_DENIED", "permission_denied"),
                ("PERMISSION_UNKNOWN", "permission_unknown"),
                (
                    "AUTHORIZATION_SCOPE_MISMATCH",
                    "authorization_scope_mismatch",
                ),
                ("AUTHORIZATION_DENIED", "authorization_denied"),
                ("AUTHORIZATION_MISSING", "authorization_missing"),
                (
                    "AUTHORIZED_BUT_NOT_PERMITTED",
                    "authorized_but_not_permitted",
                ),
                (
                    "PERMITTED_BUT_NOT_AUTHORIZED",
                    "permitted_but_not_authorized",
                ),
                (
                    "ALL_PREPARATION_EVIDENCE_POSITIVE",
                    "all_preparation_evidence_positive",
                ),
            ],
        }
        for enum_type, expected in expectations.items():
            with self.subTest(enum=enum_type.__name__):
                self.assertEqual(
                    [(item.name, item.value) for item in enum_type],
                    expected,
                )

    def test_dataclass_field_order_is_locked(self) -> None:
        expectations = {
            ReadOnlyExecutionCapabilityEvidence: [
                "runtime_option_id",
                "operation_id",
                "state",
            ],
            ReadOnlyExecutionPermissionEvidence: [
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "resource",
                "state",
                "freshness",
            ],
            ReadOnlyExecutionAuthorizationEvidence: [
                "task_id",
                "workflow_id",
                "stage_id",
                "role_id",
                "actor_id",
                "runtime_option_id",
                "option_id",
                "environment_id",
                "operation_id",
                "resource",
                "source",
                "state",
            ],
            ReadOnlyExecutionPreparationFinding: ["code", "message"],
            ReadOnlyExecutionPreparationResult: [
                "valid",
                "findings",
                "candidate_result",
                "operation_id",
                "resource",
                "environment_id",
                "capability_evidence",
                "permission_evidence",
                "authorization_evidence",
                "outcome",
                "reasons",
            ],
        }
        for data_type, expected in expectations.items():
            with self.subTest(dataclass=data_type.__name__):
                self.assertEqual(
                    [item.name for item in fields(data_type)],
                    expected,
                )

    def test_all_published_values_are_frozen(self) -> None:
        values = [
            capability(),
            permission(),
            authorization(),
            ReadOnlyExecutionPreparationFinding("code", "message"),
            self.assess(),
        ]
        for value in values:
            first_field = fields(type(value))[0].name
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(value, first_field, None)

    def test_contract_has_no_request_invocation_or_token_lifecycle_fields(
        self,
    ) -> None:
        field_names = {
            item.name
            for data_type in (
                ReadOnlyExecutionCapabilityEvidence,
                ReadOnlyExecutionPermissionEvidence,
                ReadOnlyExecutionAuthorizationEvidence,
                ReadOnlyExecutionPreparationResult,
            )
            for item in fields(data_type)
        }
        self.assertTrue(
            field_names.isdisjoint(
                {
                    "request",
                    "execution_request",
                    "invoke",
                    "invocation",
                    "dispatch",
                    "execution_contract",
                    "tool_id",
                    "authorization_id",
                    "token",
                    "consumed",
                    "replayed",
                    "revoked",
                    "expires_at",
                    "session",
                    "timestamp",
                }
            )
        )
        self.assertNotIn(
            "freshness",
            {item.name for item in fields(ReadOnlyExecutionAuthorizationEvidence)},
        )
        for name in (
            "create_execution_request",
            "dispatch",
            "execute",
            "invoke",
        ):
            self.assertFalse(hasattr(subject, name))
        self.assertFalse(
            hasattr(
                engineering_orchestration,
                "assess_read_only_execution_preparation",
            )
        )


class ReadOnlyExecutionPreparationScenarioTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_scenario_1_all_exact_current_positive_is_diagnostic_only(
        self,
    ) -> None:
        result = self.assess()
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.POTENTIALLY_EXECUTABLE,
            (
                ReadOnlyExecutionPreparationReason.
                ALL_PREPARATION_EVIDENCE_POSITIVE,
            ),
        )
        self.assertFalse(hasattr(result, "execution_request"))
        self.assertFalse(hasattr(result, "invocation"))

    def test_scenario_2_capability_absent_is_blocked(self) -> None:
        result = self.assess(
            capability_evidence=capability(
                ReadOnlyExecutionCapabilityState.ABSENT
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (ReadOnlyExecutionPreparationReason.CAPABILITY_ABSENT,),
        )

    def test_scenario_3_capability_unknown_or_missing_is_unresolved(
        self,
    ) -> None:
        result = self.assess(
            capability_evidence=capability(
                ReadOnlyExecutionCapabilityState.UNKNOWN
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (ReadOnlyExecutionPreparationReason.CAPABILITY_UNKNOWN,),
        )

    def test_scenario_4_permission_denied_is_blocked(self) -> None:
        result = self.assess(
            permission_evidence=permission(
                ReadOnlyExecutionPermissionState.DENIED
            ),
            authorization_evidence=missing_authorization(),
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (
                ReadOnlyExecutionPreparationReason.PERMISSION_DENIED,
                ReadOnlyExecutionPreparationReason.AUTHORIZATION_MISSING,
            ),
        )

    def test_scenario_5_permitted_but_not_authorized_is_unresolved(
        self,
    ) -> None:
        result = self.assess(
            authorization_evidence=missing_authorization(),
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (
                ReadOnlyExecutionPreparationReason.AUTHORIZATION_MISSING,
                ReadOnlyExecutionPreparationReason.
                PERMITTED_BUT_NOT_AUTHORIZED,
            ),
        )

    def test_scenario_6_authorized_but_not_permitted_is_blocked(
        self,
    ) -> None:
        result = self.assess(
            permission_evidence=permission(
                ReadOnlyExecutionPermissionState.DENIED
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (
                ReadOnlyExecutionPreparationReason.PERMISSION_DENIED,
                ReadOnlyExecutionPreparationReason.
                AUTHORIZED_BUT_NOT_PERMITTED,
            ),
        )

    def test_scenario_7_authorization_does_not_create_capability(self) -> None:
        result = self.assess(
            capability_evidence=capability(
                ReadOnlyExecutionCapabilityState.UNKNOWN
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (ReadOnlyExecutionPreparationReason.CAPABILITY_UNKNOWN,),
        )

    def test_scenario_8_blocked_candidate_is_a_hard_prerequisite(self) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.BLOCKED
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (
                ReadOnlyExecutionPreparationReason.
                CANDIDATE_PREREQUISITES_BLOCKED,
            ),
        )

    def test_scenario_9_unresolved_candidate_is_a_hard_prerequisite(
        self,
    ) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (
                ReadOnlyExecutionPreparationReason.
                CANDIDATE_PREREQUISITES_UNRESOLVED,
            ),
        )

    def test_scenario_10_authorization_for_another_resource_mismatches(
        self,
    ) -> None:
        result = self.assess(
            authorization_evidence=authorization(resource="docs/other.md")
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (
                ReadOnlyExecutionPreparationReason.
                AUTHORIZATION_SCOPE_MISMATCH,
            ),
        )

    def test_scenario_11_authorization_for_another_task_mismatches(
        self,
    ) -> None:
        result = self.assess(
            authorization_evidence=authorization(task_id="AIO-999")
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            (
                ReadOnlyExecutionPreparationReason.
                AUTHORIZATION_SCOPE_MISMATCH,
            ),
        )

    def test_scenario_12_stale_or_now_denied_permission_never_passes(
        self,
    ) -> None:
        cases = (
            (
                "stale_previous_allowance",
                permission(
                    ReadOnlyExecutionPermissionState.ALLOWED,
                    ReadOnlyExecutionPermissionFreshness.STALE,
                ),
                ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                (ReadOnlyExecutionPreparationReason.PERMISSION_STALE,),
            ),
            (
                "current_denial",
                permission(ReadOnlyExecutionPermissionState.DENIED),
                ReadOnlyExecutionPreparationOutcome.BLOCKED,
                (
                    ReadOnlyExecutionPreparationReason.PERMISSION_DENIED,
                    ReadOnlyExecutionPreparationReason.
                    AUTHORIZED_BUT_NOT_PERMITTED,
                ),
            ),
        )
        for label, evidence, outcome, reasons in cases:
            with self.subTest(case=label):
                result = self.assess(permission_evidence=evidence)
                self.assert_valid_result(result, outcome, reasons)
                self.assertNotEqual(
                    result.outcome,
                    ReadOnlyExecutionPreparationOutcome.POTENTIALLY_EXECUTABLE,
                )

    def test_explicit_authorization_denial_is_blocked(self) -> None:
        result = self.assess(
            authorization_evidence=authorization(
                ReadOnlyExecutionAuthorizationState.DENIED
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (ReadOnlyExecutionPreparationReason.AUTHORIZATION_DENIED,),
        )

    def test_permission_unknown_and_freshness_unknown_remain_distinct(
        self,
    ) -> None:
        cases = (
            (
                permission(ReadOnlyExecutionPermissionState.UNKNOWN),
                ReadOnlyExecutionPreparationReason.PERMISSION_UNKNOWN,
            ),
            (
                permission(
                    ReadOnlyExecutionPermissionState.ALLOWED,
                    ReadOnlyExecutionPermissionFreshness.UNKNOWN,
                ),
                ReadOnlyExecutionPreparationReason.
                PERMISSION_FRESHNESS_UNKNOWN,
            ),
        )
        for evidence, reason in cases:
            with self.subTest(reason=reason.value):
                result = self.assess(permission_evidence=evidence)
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    (reason,),
                )

    def test_policy_provided_authorization_is_explicit_positive_evidence(
        self,
    ) -> None:
        result = self.assess(
            authorization_evidence=authorization(
                source=ReadOnlyExecutionAuthorizationSource.POLICY_PROVIDED
            )
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.POTENTIALLY_EXECUTABLE,
            (
                ReadOnlyExecutionPreparationReason.
                ALL_PREPARATION_EVIDENCE_POSITIVE,
            ),
        )


class ReadOnlyExecutionPreparationScopeTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_capability_scope_matches_runtime_and_operation_exactly(self) -> None:
        cases = {
            "runtime": {"runtime_option_id": "runtime::other"},
            "operation": {"operation_id": "repository_file_write"},
        }
        for label, changes in cases.items():
            with self.subTest(dimension=label):
                result = self.assess(
                    capability_evidence=capability(**changes)
                )
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    (
                        ReadOnlyExecutionPreparationReason.
                        CAPABILITY_SCOPE_MISMATCH,
                    ),
                )

    def test_permission_scope_matches_runtime_environment_operation_resource(
        self,
    ) -> None:
        cases = {
            "runtime": {"runtime_option_id": "runtime::other"},
            "environment": {"environment_id": "environment::other"},
            "operation": {"operation_id": "repository_file_write"},
            "resource": {"resource": "docs/other.md"},
        }
        for label, changes in cases.items():
            with self.subTest(dimension=label):
                result = self.assess(
                    permission_evidence=permission(**changes)
                )
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    (
                        ReadOnlyExecutionPreparationReason.
                        PERMISSION_SCOPE_MISMATCH,
                    ),
                )

    def test_authorization_scope_matches_all_candidate_and_action_parts(
        self,
    ) -> None:
        cases = {
            "task": {"task_id": "AIO-999"},
            "workflow": {"workflow_id": "architecture-change"},
            "stage": {"stage_id": "review"},
            "role": {"role_id": "reviewer"},
            "actor": {"actor_id": "agent::other"},
            "runtime": {"runtime_option_id": "runtime::other"},
            "inference": {"option_id": "option::other"},
            "environment": {"environment_id": "environment::other"},
            "operation": {"operation_id": "repository_file_write"},
            "resource": {"resource": "docs/other.md"},
        }
        for label, changes in cases.items():
            with self.subTest(dimension=label):
                result = self.assess(
                    authorization_evidence=authorization(**changes)
                )
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    (
                        ReadOnlyExecutionPreparationReason.
                        AUTHORIZATION_SCOPE_MISMATCH,
                    ),
                )

    def test_scope_mismatch_suppresses_that_evidence_state(self) -> None:
        cases = (
            (
                {
                    "capability_evidence": capability(
                        ReadOnlyExecutionCapabilityState.ABSENT,
                        runtime_option_id="runtime::other",
                    )
                },
                (
                    ReadOnlyExecutionPreparationReason.
                    CAPABILITY_SCOPE_MISMATCH,
                ),
            ),
            (
                {
                    "permission_evidence": permission(
                        ReadOnlyExecutionPermissionState.DENIED,
                        ReadOnlyExecutionPermissionFreshness.STALE,
                        environment_id="environment::other",
                    )
                },
                (
                    ReadOnlyExecutionPreparationReason.
                    PERMISSION_SCOPE_MISMATCH,
                ),
            ),
            (
                {
                    "authorization_evidence": authorization(
                        ReadOnlyExecutionAuthorizationState.DENIED,
                        actor_id="agent::other",
                    )
                },
                (
                    ReadOnlyExecutionPreparationReason.
                    AUTHORIZATION_SCOPE_MISMATCH,
                ),
            ),
        )
        for changes, reasons in cases:
            with self.subTest(reasons=reasons):
                result = self.assess(**changes)
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    reasons,
                )

    def test_case_differences_do_not_match(self) -> None:
        cases = (
            {
                "capability_evidence": capability(
                    runtime_option_id="Runtime::one"
                )
            },
            {
                "permission_evidence": permission(
                    resource="workflows/readme.md"
                )
            },
            {
                "authorization_evidence": authorization(task_id="aio-035")
            },
        )
        expected = (
            ReadOnlyExecutionPreparationReason.CAPABILITY_SCOPE_MISMATCH,
            ReadOnlyExecutionPreparationReason.PERMISSION_SCOPE_MISMATCH,
            ReadOnlyExecutionPreparationReason.AUTHORIZATION_SCOPE_MISMATCH,
        )
        for changes, reason in zip(cases, expected, strict=True):
            with self.subTest(reason=reason.value):
                result = self.assess(**changes)
                self.assertEqual(
                    result.outcome,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                )
                self.assertEqual(result.reasons, (reason,))


class ReadOnlyExecutionPreparationValidationTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_candidate_wrong_type_invalid_and_inconsistent_are_distinct(
        self,
    ) -> None:
        inconsistent = replace(candidate(), actor_id=None)
        cases = (
            (object(), "candidate_result_invalid_type"),
            (invalid_candidate(), "candidate_result_not_valid"),
            (inconsistent, "candidate_result_inconsistent"),
        )
        for supplied, code in cases:
            with self.subTest(code=code):
                result = self.assess(candidate_result=supplied)
                self.assert_atomic_invalid(result, [code])

    def test_incoherent_candidate_identity_enum_and_reason_forms_are_invalid(
        self,
    ) -> None:
        valid = candidate()
        cases = (
            replace(valid, responsibility_key=("AIO-035", "workflow", "stage")),
            replace(
                valid,
                responsibility_key=("",) + RESPONSIBILITY_KEY[1:],
            ),
            replace(valid, actor_id=""),
            replace(valid, runtime_option_id=" runtime::one"),
            replace(valid, option_id=""),
            replace(valid, outcome="satisfied"),
            replace(valid, reasons=("all_currently_modeled_prerequisites_satisfied",)),
            replace(
                valid,
                reasons=(
                    AgentExecutionCandidatePrerequisiteReason.ACTOR_UNAVAILABLE,
                ),
            ),
            replace(
                candidate(AgentExecutionCandidatePrerequisiteOutcome.BLOCKED),
                reasons=(
                    AgentExecutionCandidatePrerequisiteReason.
                    ALL_CURRENTLY_MODELED_PREREQUISITES_SATISFIED,
                ),
            ),
        )
        for index, supplied in enumerate(cases):
            with self.subTest(case=index):
                result = self.assess(candidate_result=supplied)
                self.assert_atomic_invalid(
                    result,
                    ["candidate_result_inconsistent"],
                )

    def test_only_the_exact_provisional_operation_is_supported(self) -> None:
        malformed = (None, 1, "", " repository_file_read", "read\nfile")
        for supplied in malformed:
            with self.subTest(operation=supplied):
                result = self.assess(operation_id=supplied)
                self.assert_atomic_invalid(result, ["operation_id_invalid"])
        result = self.assess(operation_id="repository_file_write")
        self.assert_atomic_invalid(result, ["operation_id_not_supported"])

    def test_only_the_exact_controlled_resource_is_accepted(self) -> None:
        result = self.assess(resource="docs/other.md")
        self.assert_atomic_invalid(result, ["resource_not_controlled"])
        semicolon_is_not_glob_meta = self.assess(
            resource="docs/name;part.md"
        )
        self.assert_atomic_invalid(
            semicolon_is_not_glob_meta,
            ["resource_not_controlled"],
        )

    def test_malformed_resource_forms_are_rejected_lexically(self) -> None:
        malformed = (
            None,
            b"workflows/README.md",
            "",
            " workflows/README.md",
            "workflows/README.md ",
            "workflows/READ\tME.md",
            "workflows/READ\nME.md",
            "workflows/READ\x00ME.md",
            "workflows\\README.md",
            "/workflows/README.md",
            "//server/share/README.md",
            "C:/workflows/README.md",
            "c:workflows/README.md",
            "https://example.test/README.md",
            "~/workflows/README.md",
            "./workflows/README.md",
            "workflows/../README.md",
            "workflows/./README.md",
            "workflows//README.md",
            "workflows/",
            "workflows",
            "workflows/README.txt",
            "workflows/README.MD",
            "workflows/*.md",
            "workflows/READ?ME.md",
            "workflows/[R]EADME.md",
            "workflows/README{1}.md",
            "workflows/README].md",
            "workflows/README}.md",
            "docs/name:part.md",
        )
        for supplied in malformed:
            with self.subTest(resource=repr(supplied)):
                result = self.assess(resource=supplied)
                self.assert_atomic_invalid(result, ["resource_invalid"])

    def test_environment_identity_is_opaque_but_nonempty_and_trimmed(
        self,
    ) -> None:
        for supplied in (None, 1, "", " environment::workspace", "env\nname"):
            with self.subTest(environment=supplied):
                result = self.assess(environment_id=supplied)
                self.assert_atomic_invalid(result, ["environment_id_invalid"])
        opaque = self.assess(environment_id="opaque:host/container#1")
        self.assertTrue(opaque.valid)
        self.assertEqual(
            opaque.outcome,
            ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
        )
        self.assertEqual(
            opaque.reasons,
            (
                ReadOnlyExecutionPreparationReason.
                PERMISSION_SCOPE_MISMATCH,
                ReadOnlyExecutionPreparationReason.
                AUTHORIZATION_SCOPE_MISMATCH,
            ),
        )

    def test_invalid_evidence_type_and_fields_are_atomic_invalid(self) -> None:
        cases = (
            (
                {"capability_evidence": object()},
                "capability_evidence_invalid_type",
            ),
            (
                {
                    "capability_evidence": capability(
                        state="present"
                    )
                },
                "capability_evidence_invalid",
            ),
            (
                {
                    "capability_evidence": capability(
                        runtime_option_id=""
                    )
                },
                "capability_evidence_invalid",
            ),
            (
                {"permission_evidence": object()},
                "permission_evidence_invalid_type",
            ),
            (
                {"permission_evidence": permission(state="allowed")},
                "permission_evidence_invalid",
            ),
            (
                {"permission_evidence": permission(freshness="current")},
                "permission_evidence_invalid",
            ),
            (
                {"permission_evidence": permission(resource="../other.md")},
                "permission_evidence_invalid",
            ),
            (
                {"authorization_evidence": object()},
                "authorization_evidence_invalid_type",
            ),
            (
                {"authorization_evidence": authorization(state="granted")},
                "authorization_evidence_invalid",
            ),
            (
                {"authorization_evidence": authorization(source="human_provided")},
                "authorization_evidence_invalid",
            ),
            (
                {"authorization_evidence": authorization(task_id="")},
                "authorization_evidence_invalid",
            ),
            (
                {
                    "authorization_evidence": authorization(
                        resource="docs/../other.md"
                    )
                },
                "authorization_evidence_invalid",
            ),
        )
        for changes, code in cases:
            with self.subTest(code=code, changes=changes):
                result = self.assess(**changes)
                self.assert_atomic_invalid(result, [code])

    def test_authorization_source_and_state_must_be_consistent(self) -> None:
        cases = (
            authorization(
                ReadOnlyExecutionAuthorizationState.MISSING,
                ReadOnlyExecutionAuthorizationSource.HUMAN_PROVIDED,
            ),
            authorization(
                ReadOnlyExecutionAuthorizationState.MISSING,
                ReadOnlyExecutionAuthorizationSource.POLICY_PROVIDED,
            ),
            authorization(
                ReadOnlyExecutionAuthorizationState.GRANTED,
                ReadOnlyExecutionAuthorizationSource.NOT_SUPPLIED,
            ),
            authorization(
                ReadOnlyExecutionAuthorizationState.DENIED,
                ReadOnlyExecutionAuthorizationSource.NOT_SUPPLIED,
            ),
        )
        for supplied in cases:
            with self.subTest(source=supplied.source, state=supplied.state):
                result = self.assess(authorization_evidence=supplied)
                self.assert_atomic_invalid(
                    result,
                    ["authorization_source_state_inconsistent"],
                )

    def test_findings_accumulate_by_locked_category_order(self) -> None:
        supplied = {
            "candidate_result": object(),
            "operation_id": "",
            "resource": "../README.md",
            "environment_id": "",
            "capability_evidence": object(),
            "permission_evidence": object(),
            "authorization_evidence": object(),
        }
        first = self.assess(**supplied)
        second = self.assess(**supplied)
        expected = [
            "candidate_result_invalid_type",
            "operation_id_invalid",
            "resource_invalid",
            "environment_id_invalid",
            "capability_evidence_invalid_type",
            "permission_evidence_invalid_type",
            "authorization_evidence_invalid_type",
        ]
        self.assert_atomic_invalid(first, expected)
        self.assertEqual(first, second)


class ReadOnlyExecutionPreparationDeterminismTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_reasons_use_locked_order_and_blockers_dominate(self) -> None:
        result = self.assess(
            candidate_result=candidate(
                AgentExecutionCandidatePrerequisiteOutcome.UNRESOLVED
            ),
            capability_evidence=capability(
                ReadOnlyExecutionCapabilityState.ABSENT
            ),
            permission_evidence=permission(
                ReadOnlyExecutionPermissionState.DENIED
            ),
            authorization_evidence=missing_authorization(),
        )
        self.assert_valid_result(
            result,
            ReadOnlyExecutionPreparationOutcome.BLOCKED,
            (
                ReadOnlyExecutionPreparationReason.
                CANDIDATE_PREREQUISITES_UNRESOLVED,
                ReadOnlyExecutionPreparationReason.CAPABILITY_ABSENT,
                ReadOnlyExecutionPreparationReason.PERMISSION_DENIED,
                ReadOnlyExecutionPreparationReason.AUTHORIZATION_MISSING,
            ),
        )

    def test_stale_or_unknown_freshness_suppresses_permission_state(
        self,
    ) -> None:
        cases = (
            (
                ReadOnlyExecutionPermissionFreshness.STALE,
                ReadOnlyExecutionPreparationReason.PERMISSION_STALE,
            ),
            (
                ReadOnlyExecutionPermissionFreshness.UNKNOWN,
                ReadOnlyExecutionPreparationReason.
                PERMISSION_FRESHNESS_UNKNOWN,
            ),
        )
        for freshness, reason in cases:
            with self.subTest(freshness=freshness.value):
                result = self.assess(
                    permission_evidence=permission(
                        ReadOnlyExecutionPermissionState.DENIED,
                        freshness,
                    )
                )
                self.assert_valid_result(
                    result,
                    ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                    (reason,),
                )

    def test_inputs_are_unmodified(self) -> None:
        supplied = self.base()
        before = copy.deepcopy(supplied)
        result = assess_read_only_execution_preparation(
            **supplied,  # type: ignore[arg-type]
        )
        self.assertTrue(result.valid)
        self.assertEqual(supplied, before)

    def test_repeat_calls_are_equal_uncached_and_context_independent(self) -> None:
        supplied = self.base()
        first = assess_read_only_execution_preparation(
            **supplied,  # type: ignore[arg-type]
        )
        denied = self.assess(
            permission_evidence=permission(
                ReadOnlyExecutionPermissionState.DENIED
            )
        )
        second = assess_read_only_execution_preparation(
            **supplied,  # type: ignore[arg-type]
        )
        self.assertEqual(first, second)
        self.assertIsNot(first, second)
        self.assertNotEqual(first, denied)
        self.assertFalse(
            hasattr(assess_read_only_execution_preparation, "cache_info")
        )


class ReadOnlyExecutionPreparationBoundaryTests(
    ReadOnlyExecutionPreparationFixture
):
    def test_module_imports_only_locked_pure_dependencies(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        allowed = {
            "__future__",
            "dataclasses",
            "enum",
            "typing",
            (
                "engineering_orchestration."
                "agent_execution_candidate_prerequisite"
            ),
        }
        self.assertLessEqual(imported_modules, allowed)
        self.assertNotIn(
            "engineering_orchestration.cli",
            imported_modules,
        )
        self.assertFalse(
            any("adapter" in module.lower() for module in imported_modules)
        )

    def test_static_ast_contains_no_io_discovery_or_invocation_calls(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        forbidden_names = {
            "open",
            "stat",
            "exists",
            "access",
            "resolve",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "lstat",
            "listdir",
            "scandir",
            "walk",
            "readlink",
            "run",
            "Popen",
            "call",
            "check_call",
            "check_output",
            "create_subprocess_exec",
            "create_subprocess_shell",
            "urlopen",
            "connect",
            "socket",
            "create_connection",
            "getaddrinfo",
            "gethostbyname",
            "system",
            "popen",
            "getenv",
            "which",
            "find_spec",
            "time",
            "monotonic",
            "dispatch",
            "execute",
            "invoke",
        }
        calls = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        self.assertTrue(forbidden_names.isdisjoint(calls))

    def test_runtime_paths_perform_no_io_discovery_process_or_network(
        self,
    ) -> None:
        forbidden = AssertionError("forbidden external operation")
        guarded_attributes = (
            (builtins, "open"),
            (io, "open"),
            (os, "open"),
            (Path, "open"),
            (Path, "read_text"),
            (Path, "read_bytes"),
            (Path, "write_text"),
            (Path, "write_bytes"),
            (Path, "resolve"),
            (Path, "exists"),
            (Path, "stat"),
            (Path, "lstat"),
            (Path, "is_file"),
            (Path, "is_dir"),
            (Path, "iterdir"),
            (Path, "glob"),
            (Path, "rglob"),
            (os, "stat"),
            (os, "lstat"),
            (os, "access"),
            (os, "listdir"),
            (os, "scandir"),
            (os, "walk"),
            (os, "readlink"),
            (os.path, "exists"),
            (os.path, "lexists"),
            (os.path, "isfile"),
            (os.path, "isdir"),
            (os.path, "realpath"),
            (glob, "glob"),
            (glob, "iglob"),
            (shutil, "which"),
            (importlib.util, "find_spec"),
            (subprocess, "run"),
            (subprocess, "Popen"),
            (subprocess, "call"),
            (subprocess, "check_call"),
            (subprocess, "check_output"),
            (asyncio, "create_subprocess_exec"),
            (asyncio, "create_subprocess_shell"),
            (os, "system"),
            (os, "popen"),
            (socket, "socket"),
            (socket, "create_connection"),
            (socket, "getaddrinfo"),
            (socket, "gethostbyname"),
            (http.client.HTTPConnection, "connect"),
            (http.client.HTTPSConnection, "connect"),
            (http.client.HTTPConnection, "request"),
            (http.client.HTTPSConnection, "request"),
            (urllib.request, "urlopen"),
            (time, "time"),
            (time, "monotonic"),
            (sqlite3, "connect"),
            (os, "getenv"),
        )
        with ExitStack() as stack:
            for owner, name in guarded_attributes:
                stack.enter_context(
                    patch.object(owner, name, side_effect=forbidden)
                )
            results = (
                self.assess(),
                self.assess(resource="../README.md"),
                self.assess(
                    permission_evidence=permission(
                        ReadOnlyExecutionPermissionState.DENIED
                    )
                ),
                self.assess(
                    capability_evidence=capability(
                        ReadOnlyExecutionCapabilityState.UNKNOWN
                    )
                ),
                self.assess(
                    authorization_evidence=authorization(
                        resource="docs/other.md"
                    )
                ),
            )
        self.assertEqual(
            [result.valid for result in results],
            [True, False, True, True, True],
        )
        self.assertEqual(
            [result.outcome for result in results],
            [
                ReadOnlyExecutionPreparationOutcome.POTENTIALLY_EXECUTABLE,
                None,
                ReadOnlyExecutionPreparationOutcome.BLOCKED,
                ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
                ReadOnlyExecutionPreparationOutcome.UNRESOLVED,
            ],
        )


if __name__ == "__main__":
    unittest.main()
