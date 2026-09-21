"""Focused contract, preparation, schema, scenario, and purity tests for AIO-041."""

from __future__ import annotations

import ast
import builtins
import copy
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, asdict, fields, replace
import json
import os
from pathlib import Path
import random
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request
import uuid

import engineering_orchestration
import engineering_orchestration.agent_execution_contract as subject
from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteFinding,
    AgentActionPrerequisiteOutcome,
    AgentActionPrerequisiteReason,
    AgentActionPrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
    AgentExecutionContractFinding,
    AgentExecutionContractValidationResult,
    prepare_agent_execution_contract,
    validate_agent_execution_contract,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "engineering_orchestration" / "agent_execution_contract.py"
RESPONSIBILITY_KEY = (
    "AIO-041",
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
SATISFIED_REASON = (
    AgentActionPrerequisiteReason.
    ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED
)


def prerequisite(
    outcome: AgentActionPrerequisiteOutcome = (
        AgentActionPrerequisiteOutcome.SATISFIED
    ),
    *,
    responsibility_key: object = RESPONSIBILITY_KEY,
    actor_id: object = ACTOR_ID,
    runtime_option_id: object = RUNTIME_OPTION_ID,
    option_id: object = OPTION_ID,
    environment_id: object = ENVIRONMENT_ID,
    operation_id: object = OPERATION_ID,
    resource: object = RESOURCE,
    reasons: tuple[AgentActionPrerequisiteReason, ...] | None = None,
) -> AgentActionPrerequisiteResult:
    reasons_by_outcome = {
        AgentActionPrerequisiteOutcome.SATISFIED: (SATISFIED_REASON,),
        AgentActionPrerequisiteOutcome.BLOCKED: (
            AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
        ),
        AgentActionPrerequisiteOutcome.UNRESOLVED: (
            AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED,
        ),
    }
    return AgentActionPrerequisiteResult(
        True,
        (),
        responsibility_key,  # type: ignore[arg-type]
        actor_id,  # type: ignore[arg-type]
        runtime_option_id,  # type: ignore[arg-type]
        option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        resource,  # type: ignore[arg-type]
        outcome,
        reasons if reasons is not None else reasons_by_outcome[outcome],
    )


def invalid_prerequisite(
    findings: tuple[AgentActionPrerequisiteFinding, ...] = (
        AgentActionPrerequisiteFinding("synthetic_parent", "Synthetic parent finding."),
    ),
) -> AgentActionPrerequisiteResult:
    return AgentActionPrerequisiteResult(
        False,
        findings,
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


def contract(
    *,
    task_id: object = RESPONSIBILITY_KEY[0],
    workflow_id: object = RESPONSIBILITY_KEY[1],
    stage_id: object = RESPONSIBILITY_KEY[2],
    role_id: object = RESPONSIBILITY_KEY[3],
    actor_id: object = ACTOR_ID,
    runtime_option_id: object = RUNTIME_OPTION_ID,
    option_id: object = OPTION_ID,
    environment_id: object = ENVIRONMENT_ID,
    operation_id: object = OPERATION_ID,
    resource: object = RESOURCE,
    execution_mode: object = "standard",
) -> AgentExecutionContract:
    return AgentExecutionContract(
        task_id,  # type: ignore[arg-type]
        workflow_id,  # type: ignore[arg-type]
        stage_id,  # type: ignore[arg-type]
        role_id,  # type: ignore[arg-type]
        actor_id,  # type: ignore[arg-type]
        runtime_option_id,  # type: ignore[arg-type]
        option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        resource,  # type: ignore[arg-type]
        execution_mode,  # type: ignore[arg-type]
    )


class AgentExecutionContractFixture(unittest.TestCase):
    def assert_atomic_invalid(
        self,
        result: AgentExecutionContractValidationResult,
        codes: list[str],
    ) -> None:
        self.assertFalse(result.valid)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.contract)

    def assert_no_real_execution(
        self,
        result: AgentExecutionContractValidationResult,
    ) -> None:
        """Record the mandatory no-real-execution assertion per scenario."""

        self.assertNotIn("run_id", vars(result))
        if result.contract is not None:
            forbidden_fields = {
                "tool_id",
                "adapter_id",
                "provider_id",
                "payload",
                "parameters",
                "contract_id",
                "run_id",
                "status",
                "result",
                "error",
                "created_at",
                "authority_id",
                "authorization_state",
                "permission_state",
            }
            self.assertTrue(forbidden_fields.isdisjoint(vars(result.contract)))
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("__")
        }
        self.assertTrue(
            all(
                not any(fragment in name for fragment in ("dispatch", "invoke"))
                for name in exported
            )
        )


class AgentExecutionContractValueAndValidationTests(
    AgentExecutionContractFixture
):
    def test_public_values_are_frozen_tuple_backed_and_exactly_shaped(self) -> None:
        self.assertEqual(
            [field.name for field in fields(AgentExecutionContract)],
            [
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
                "execution_mode",
            ],
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionContractFinding)],
            ["code", "message"],
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionContractValidationResult)],
            ["valid", "findings", "contract"],
        )
        values = (
            contract(),
            AgentExecutionContractFinding("code", "message"),
            AgentExecutionContractValidationResult(True, (), contract()),
        )
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    value.valid = False  # type: ignore[attr-defined,misc]
        self.assertIsInstance(values[2].findings, tuple)

    def test_direct_module_only_public_api_and_no_package_root_export(self) -> None:
        self.assertFalse(hasattr(engineering_orchestration, "AgentExecutionContract"))
        self.assertFalse(
            hasattr(engineering_orchestration, "prepare_agent_execution_contract")
        )
        for name in (
            "AgentExecutionContract",
            "AgentExecutionContractFinding",
            "AgentExecutionContractValidationResult",
            "validate_agent_execution_contract",
            "prepare_agent_execution_contract",
        ):
            self.assertIn(name, vars(subject))

    def test_exact_contract_type_is_required_and_subclasses_are_rejected(self) -> None:
        expected = AgentExecutionContractValidationResult(
            False,
            (
                AgentExecutionContractFinding(
                    "agent_execution_contract_invalid_type",
                    "Agent Execution Contract must be an exact "
                    "AgentExecutionContract value.",
                ),
            ),
            None,
        )
        self.assertEqual(validate_agent_execution_contract(object()), expected)

        class DerivedContract(AgentExecutionContract):
            pass

        supplied = contract()
        derived = DerivedContract(*(getattr(supplied, item.name) for item in fields(supplied)))
        self.assertEqual(validate_agent_execution_contract(derived), expected)

    def test_valid_contract_is_preserved_by_identity_for_all_four_modes(self) -> None:
        for mode in ("lite", "standard", "deep", "critical"):
            with self.subTest(mode=mode):
                supplied = contract(execution_mode=mode)
                result = validate_agent_execution_contract(supplied)
                self.assertEqual(
                    result,
                    AgentExecutionContractValidationResult(True, (), supplied),
                )
                self.assertIs(result.contract, supplied)

    def test_eight_identity_findings_use_locked_order_codes_and_messages(self) -> None:
        supplied = contract(
            task_id="",
            workflow_id=object(),
            stage_id="",
            role_id=object(),
            actor_id="",
            runtime_option_id=object(),
            option_id="",
            environment_id=object(),
        )
        result = validate_agent_execution_contract(supplied)
        field_names = [
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "actor_id",
            "runtime_option_id",
            "option_id",
            "environment_id",
        ]
        self.assert_atomic_invalid(
            result,
            [f"agent_execution_contract_{field}_invalid" for field in field_names],
        )
        self.assertEqual(
            [finding.message for finding in result.findings],
            [
                f"Agent Execution Contract {field} must be an exact nonempty string."
                for field in field_names
            ],
        )

    def test_all_applicable_intrinsic_findings_aggregate_in_locked_order(self) -> None:
        result = validate_agent_execution_contract(
            contract(
                task_id="",
                actor_id=object(),
                operation_id="Malformed-Operation",
                resource="synthetic/../input.txt",
                execution_mode="turbo",
            )
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_contract_task_id_invalid",
                "agent_execution_contract_actor_id_invalid",
                "operation_id_invalid_syntax",
                "resource_parent_segment",
                "agent_execution_contract_execution_mode_not_supported",
            ],
        )

    def test_mode_invalid_type_and_unsupported_variants_are_not_normalized(self) -> None:
        class DerivedMode(str):
            pass

        invalid_type_values = (None, 1, DerivedMode("standard"))
        for value in invalid_type_values:
            with self.subTest(value=value):
                result = validate_agent_execution_contract(
                    contract(execution_mode=value)
                )
                self.assert_atomic_invalid(
                    result,
                    ["agent_execution_contract_execution_mode_invalid_type"],
                )
                self.assertEqual(
                    result.findings[0].message,
                    "Agent Execution Contract execution_mode must be an exact string.",
                )
        for value in ("", "STANDARD", " standard ", "turbo"):
            with self.subTest(value=value):
                result = validate_agent_execution_contract(
                    contract(execution_mode=value)
                )
                self.assert_atomic_invalid(
                    result,
                    ["agent_execution_contract_execution_mode_not_supported"],
                )
                self.assertEqual(
                    result.findings[0].message,
                    "Agent Execution Contract execution_mode must be one of: "
                    "lite, standard, deep, critical.",
                )

    def test_operation_semantics_are_reused_without_adding_operations(self) -> None:
        supported = validate_agent_execution_contract(contract())
        self.assertTrue(supported.valid)
        cases = (
            (
                "Malformed-Operation",
                "operation_id_invalid_syntax",
                "Operation Requirement operation_id must use ASCII "
                "lower_snake_case syntax.",
            ),
            (
                "repository_file_write",
                "operation_id_not_supported",
                "Operation ID 'repository_file_write' is not supported by Core.",
            ),
        )
        for operation_id, code, message in cases:
            with self.subTest(operation_id=operation_id):
                result = validate_agent_execution_contract(
                    contract(operation_id=operation_id)
                )
                self.assert_atomic_invalid(result, [code])
                self.assertEqual(result.findings[0].message, message)

    def test_complete_lexical_resource_taxonomy_is_reused_without_io(self) -> None:
        cases = (
            ("", "resource_empty"),
            ("synthetic/\x00/input.txt", "resource_control_character"),
            ("//server/share/input.txt", "resource_unc_path"),
            ("/synthetic/input.txt", "resource_absolute_path"),
            ("C:synthetic/input.txt", "resource_drive_qualified_path"),
            ("https:synthetic/input.txt", "resource_uri_scheme"),
            ("~/synthetic/input.txt", "resource_leading_tilde"),
            (r"synthetic\input.txt", "resource_backslash"),
            ("synthetic/", "resource_trailing_slash"),
            ("synthetic//input.txt", "resource_empty_segment"),
            ("synthetic/./input.txt", "resource_dot_segment"),
            ("synthetic/../input.txt", "resource_parent_segment"),
            ("synthetic/*.txt", "resource_glob_meta"),
        )
        for resource, code in cases:
            with self.subTest(code=code):
                result = validate_agent_execution_contract(
                    contract(resource=resource)
                )
                self.assert_atomic_invalid(result, [code])

    def test_operation_and_resource_wrong_types_are_copied_in_order(self) -> None:
        result = validate_agent_execution_contract(
            contract(operation_id=object(), resource=object())
        )
        self.assert_atomic_invalid(
            result,
            ["operation_id_invalid_type", "resource_invalid_type"],
        )

    def test_all_eleven_individual_mutations_change_value_equality(self) -> None:
        original = contract()
        mutations = {
            "task_id": "AIO-041-other",
            "workflow_id": "workflow::other",
            "stage_id": "stage::other",
            "role_id": "role::other",
            "actor_id": "actor::other",
            "runtime_option_id": "runtime::other",
            "option_id": "option::other",
            "environment_id": "environment::other",
            "operation_id": "read",  # equality does not imply validity
            "resource": "synthetic/other.txt",
            "execution_mode": "deep",
        }
        for field_name, value in mutations.items():
            with self.subTest(field=field_name):
                self.assertNotEqual(original, replace(original, **{field_name: value}))

    def test_json_mapping_round_trip_preserves_equality_not_provenance(self) -> None:
        original = contract(execution_mode="deep")
        serialized = json.dumps(asdict(original), sort_keys=True)
        restored = AgentExecutionContract(**json.loads(serialized))
        result = validate_agent_execution_contract(restored)
        self.assertTrue(result.valid)
        self.assertEqual(result.contract, original)
        self.assertIsNot(result.contract, original)
        self.assertNotIn("preparation_provenance", asdict(restored))

    def test_schema_is_closed_exactly_structural_and_has_locked_mode_enum(self) -> None:
        schema = load_validator("agent-execution-contract.schema.json").schema
        expected_fields = [field.name for field in fields(AgentExecutionContract)]
        self.assertEqual(schema["required"], expected_fields)
        self.assertEqual(list(schema["properties"]), expected_fields)
        self.assertIs(schema["additionalProperties"], False)
        for field_name, definition in schema["properties"].items():
            self.assertEqual(definition["type"], "string")
            self.assertEqual(definition["minLength"], 1)
            if field_name == "execution_mode":
                self.assertEqual(
                    definition["enum"],
                    ["lite", "standard", "deep", "critical"],
                )
            else:
                self.assertNotIn("enum", definition)
                self.assertNotIn("pattern", definition)
                self.assertNotIn("format", definition)

    def test_schema_rejects_all_locked_execution_layer_leakage_fields(self) -> None:
        validator = load_validator("agent-execution-contract.schema.json")
        base = asdict(contract())
        excluded = (
            "tool_id",
            "adapter_id",
            "provider_id",
            "payload",
            "parameters",
            "contract_id",
            "run_id",
            "status",
            "result",
            "error",
            "created_at",
            "started_at",
            "completed_at",
            "authority_id",
            "authorization_state",
            "permission_state",
        )
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "synthetic"}))
                )


class AgentExecutionContractPreparationTests(AgentExecutionContractFixture):
    def test_preparation_extracts_only_exact_subject_and_explicit_mode(self) -> None:
        parent = prerequisite(
            responsibility_key=("task", "workflow", "stage", "role"),
            actor_id="actor",
            runtime_option_id="runtime",
            option_id="option",
            environment_id="environment",
            resource="synthetic/exact.txt",
        )
        result = prepare_agent_execution_contract(parent, execution_mode="critical")
        self.assertEqual(
            result.contract,
            AgentExecutionContract(
                "task",
                "workflow",
                "stage",
                "role",
                "actor",
                "runtime",
                "option",
                "environment",
                OPERATION_ID,
                "synthetic/exact.txt",
                "critical",
            ),
        )

    def test_preparation_supports_all_four_modes_without_inference(self) -> None:
        for mode in ("lite", "standard", "deep", "critical"):
            with self.subTest(mode=mode):
                result = prepare_agent_execution_contract(
                    prerequisite(), execution_mode=mode
                )
                self.assertTrue(result.valid)
                self.assertEqual(result.contract.execution_mode, mode)

    def test_blocked_and_unresolved_receive_exact_distinct_findings(self) -> None:
        cases = (
            (
                AgentActionPrerequisiteOutcome.BLOCKED,
                "agent_execution_contract_prerequisites_blocked",
                "Agent Execution Contract preparation requires "
                "prerequisite_result outcome 'satisfied'; received 'blocked'.",
            ),
            (
                AgentActionPrerequisiteOutcome.UNRESOLVED,
                "agent_execution_contract_prerequisites_unresolved",
                "Agent Execution Contract preparation requires "
                "prerequisite_result outcome 'satisfied'; received 'unresolved'.",
            ),
        )
        for outcome, code, message in cases:
            with self.subTest(outcome=outcome.value):
                result = prepare_agent_execution_contract(
                    prerequisite(outcome), execution_mode="standard"
                )
                self.assert_atomic_invalid(result, [code])
                self.assertEqual(result.findings[0].message, message)

    def test_wrong_type_and_exact_subclass_are_rejected(self) -> None:
        expected_code = "agent_execution_contract_prerequisite_result_invalid_type"
        for supplied in (object(), None):
            with self.subTest(supplied=supplied):
                result = prepare_agent_execution_contract(
                    supplied, execution_mode="standard"
                )
                self.assert_atomic_invalid(result, [expected_code])
                self.assertEqual(
                    result.findings[0].message,
                    "prerequisite_result must be an exact "
                    "AgentActionPrerequisiteResult value.",
                )

        class DerivedResult(AgentActionPrerequisiteResult):
            pass

        original = prerequisite()
        derived = DerivedResult(
            *(getattr(original, item.name) for item in fields(original))
        )
        self.assert_atomic_invalid(
            prepare_agent_execution_contract(derived, execution_mode="standard"),
            [expected_code],
        )

    def test_coherent_invalid_parent_findings_pass_through_exactly(self) -> None:
        parent_findings = (
            AgentActionPrerequisiteFinding("same", "Repeated finding."),
            AgentActionPrerequisiteFinding("same", "Repeated finding."),
            AgentActionPrerequisiteFinding("later", "Later finding."),
        )
        result = prepare_agent_execution_contract(
            invalid_prerequisite(parent_findings),
            execution_mode="standard",
        )
        self.assert_atomic_invalid(result, ["same", "same", "later"])
        self.assertEqual(
            [finding.message for finding in result.findings],
            ["Repeated finding.", "Repeated finding.", "Later finding."],
        )

    def test_incoherent_parent_never_contributes_embedded_findings_or_data(self) -> None:
        embedded = AgentActionPrerequisiteFinding(
            "untrusted_embedded", "Must not pass through."
        )
        forged = replace(prerequisite(), findings=(embedded,))
        result = prepare_agent_execution_contract(
            forged, execution_mode="standard"
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisite_result_incoherent"],
        )
        self.assertNotIn("untrusted_embedded", [item.code for item in result.findings])

    def test_required_forged_and_incoherent_variants_fail_atomically(self) -> None:
        synthetic = AgentActionPrerequisiteFinding("forged", "Forged.")
        cases = (
            replace(
                invalid_prerequisite(),
                outcome=AgentActionPrerequisiteOutcome.SATISFIED,
            ),
            replace(prerequisite(), findings=(synthetic,)),
            replace(prerequisite(), actor_id=None),
            replace(
                prerequisite(),
                reasons=(
                    AgentActionPrerequisiteReason.
                    CANDIDATE_PREREQUISITES_UNRESOLVED,
                ),
            ),
            replace(
                prerequisite(),
                reasons=(
                    AgentActionPrerequisiteReason.
                    CANDIDATE_PREREQUISITES_BLOCKED,
                    SATISFIED_REASON,
                ),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(SATISFIED_REASON,),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
                reasons=(SATISFIED_REASON,),
            ),
        )
        for index, forged in enumerate(cases, start=1):
            with self.subTest(case=index):
                self.assert_atomic_invalid(
                    prepare_agent_execution_contract(
                        forged, execution_mode="standard"
                    ),
                    ["agent_execution_contract_prerequisite_result_incoherent"],
                )

    def test_full_coherence_reason_invariants_are_enforced(self) -> None:
        blocked = AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED
        unresolved = (
            AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_UNRESOLVED
        )
        cap_absent = (
            AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_ABSENT
        )
        cap_unknown = (
            AgentActionPrerequisiteReason.RUNTIME_OPERATION_CAPABILITY_UNKNOWN
        )
        permission_unknown = (
            AgentActionPrerequisiteReason.ENVIRONMENT_OPERATION_PERMISSION_UNKNOWN
        )
        cases = (
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(blocked, blocked),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(cap_absent, blocked),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(blocked, unresolved),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(cap_absent, cap_unknown),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                reasons=(permission_unknown,),
            ),
            replace(
                prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
                reasons=(blocked, permission_unknown),
            ),
        )
        for forged in cases:
            with self.subTest(reasons=forged.reasons):
                self.assert_atomic_invalid(
                    prepare_agent_execution_contract(
                        forged, execution_mode="standard"
                    ),
                    ["agent_execution_contract_prerequisite_result_incoherent"],
                )

    def test_atomic_invalid_result_shape_and_container_types_are_enforced(self) -> None:
        cases = (
            replace(invalid_prerequisite(), findings=()),
            replace(invalid_prerequisite(), responsibility_key=RESPONSIBILITY_KEY),
            replace(invalid_prerequisite(), reasons=(SATISFIED_REASON,)),
            replace(prerequisite(), valid=1),
            replace(prerequisite(), findings=[]),  # type: ignore[arg-type]
            replace(prerequisite(), reasons=[SATISFIED_REASON]),  # type: ignore[arg-type]
            replace(prerequisite(), responsibility_key=list(RESPONSIBILITY_KEY)),  # type: ignore[arg-type]
        )
        for forged in cases:
            with self.subTest(forged=forged):
                self.assert_atomic_invalid(
                    prepare_agent_execution_contract(
                        forged, execution_mode="standard"
                    ),
                    ["agent_execution_contract_prerequisite_result_incoherent"],
                )

    def test_parent_operation_and_resource_semantics_are_required_for_coherence(self) -> None:
        for changes in (
            {"operation_id": "repository_file_write"},
            {"operation_id": "Malformed-Operation"},
            {"resource": "synthetic/../input.txt"},
        ):
            with self.subTest(changes=changes):
                forged = replace(prerequisite(), **changes)
                self.assert_atomic_invalid(
                    prepare_agent_execution_contract(
                        forged, execution_mode="standard"
                    ),
                    ["agent_execution_contract_prerequisite_result_incoherent"],
                )

    def test_preparation_category_precedes_mode_and_aggregates_mode_finding(self) -> None:
        cases = (
            (
                object(),
                "agent_execution_contract_prerequisite_result_invalid_type",
            ),
            (
                replace(prerequisite(), actor_id=None),
                "agent_execution_contract_prerequisite_result_incoherent",
            ),
            (
                invalid_prerequisite(),
                "synthetic_parent",
            ),
            (
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                "agent_execution_contract_prerequisites_blocked",
            ),
            (
                prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
                "agent_execution_contract_prerequisites_unresolved",
            ),
        )
        for parent, prerequisite_code in cases:
            with self.subTest(code=prerequisite_code):
                self.assert_atomic_invalid(
                    prepare_agent_execution_contract(parent, execution_mode=None),
                    [
                        prerequisite_code,
                        "agent_execution_contract_execution_mode_invalid_type",
                    ],
                )

    def test_preparation_does_not_mutate_parent_and_is_deterministic(self) -> None:
        parent = prerequisite()
        before = copy.deepcopy(parent)
        first = prepare_agent_execution_contract(parent, execution_mode="deep")
        second = prepare_agent_execution_contract(parent, execution_mode="deep")
        self.assertEqual(parent, before)
        self.assertEqual(first, second)
        self.assertEqual(first.contract, second.contract)
        self.assertIsNot(first.contract, second.contract)


class AgentExecutionContractScenarioTests(AgentExecutionContractFixture):
    """The 28 numbered AIO-041 investigation scenarios, explicitly named."""

    def test_scenario_01_valid_satisfied_plus_valid_mode_prepares_contract(self) -> None:
        result = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        self.assertTrue(result.valid)
        self.assert_no_real_execution(result)

    def test_scenario_02_blocked_assessment_produces_no_contract(self) -> None:
        result = prepare_agent_execution_contract(
            prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
            execution_mode="standard",
        )
        self.assert_atomic_invalid(
            result, ["agent_execution_contract_prerequisites_blocked"]
        )
        self.assert_no_real_execution(result)

    def test_scenario_03_unresolved_assessment_produces_no_contract(self) -> None:
        result = prepare_agent_execution_contract(
            prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
            execution_mode="standard",
        )
        self.assert_atomic_invalid(
            result, ["agent_execution_contract_prerequisites_unresolved"]
        )
        self.assert_no_real_execution(result)

    def test_scenario_04_invalid_or_incoherent_assessment_produces_no_contract(self) -> None:
        result = prepare_agent_execution_contract(
            replace(prerequisite(), actor_id=None), execution_mode="standard"
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisite_result_incoherent"],
        )
        self.assert_no_real_execution(result)

    def test_scenario_05_unauthenticated_caller_truth_can_prepare_but_stays_unproven(self) -> None:
        result = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        self.assertTrue(result.valid)
        self.assertNotIn("authority_id", vars(result.contract))
        self.assertNotIn("provenance_reference", vars(result.contract))
        self.assert_no_real_execution(result)

    def test_scenario_06_stale_evidence_does_not_change_intrinsic_intent_validity(self) -> None:
        prepared = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        later = validate_agent_execution_contract(prepared.contract)
        self.assertTrue(later.valid)
        self.assertNotIn("freshness", vars(later.contract))
        self.assert_no_real_execution(later)

    def test_scenario_07_repeated_exact_subject_and_mode_values_are_equal(self) -> None:
        first = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        second = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        self.assertEqual(first.contract, second.contract)
        self.assertIsNot(first.contract, second.contract)
        self.assert_no_real_execution(first)

    def test_scenario_08_different_runtime_produces_a_different_contract(self) -> None:
        first = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        second = prepare_agent_execution_contract(
            prerequisite(runtime_option_id="runtime::two"),
            execution_mode="standard",
        )
        self.assertNotEqual(first.contract, second.contract)
        self.assert_no_real_execution(second)

    def test_scenario_09_different_environment_produces_a_different_contract(self) -> None:
        first = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        second = prepare_agent_execution_contract(
            prerequisite(environment_id="environment::two"),
            execution_mode="standard",
        )
        self.assertNotEqual(first.contract, second.contract)
        self.assert_no_real_execution(second)

    def test_scenario_10_different_inference_option_produces_a_different_contract(self) -> None:
        first = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        second = prepare_agent_execution_contract(
            prerequisite(option_id="option::two"), execution_mode="standard"
        )
        self.assertNotEqual(first.contract, second.contract)
        self.assert_no_real_execution(second)

    def test_scenario_11_different_assignment_produces_a_different_contract(self) -> None:
        first = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        second = prepare_agent_execution_contract(
            prerequisite(
                responsibility_key=(
                    "AIO-041-other",
                    "architecture-change",
                    "implement",
                    "software-engineer",
                )
            ),
            execution_mode="standard",
        )
        self.assertNotEqual(first.contract, second.contract)
        self.assert_no_real_execution(second)

    def test_scenario_12_different_execution_mode_produces_a_different_contract(self) -> None:
        standard = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        deep = prepare_agent_execution_contract(
            prerequisite(), execution_mode="deep"
        )
        self.assertNotEqual(standard.contract, deep.contract)
        self.assert_no_real_execution(deep)

    def test_scenario_13_copied_changed_resource_is_intrinsic_only_not_provenance(self) -> None:
        copied = replace(contract(), resource="synthetic/copied.txt")
        result = validate_agent_execution_contract(copied)
        self.assertTrue(result.valid)
        self.assertNotIn("preparation_provenance", vars(result.contract))
        self.assert_no_real_execution(result)

    def test_scenario_14_contract_without_tool_binding_is_valid(self) -> None:
        result = validate_agent_execution_contract(contract())
        self.assertTrue(result.valid)
        self.assertNotIn("tool_id", vars(result.contract))
        self.assert_no_real_execution(result)

    def test_scenario_15_contract_can_exist_without_any_run(self) -> None:
        result = validate_agent_execution_contract(contract())
        self.assertTrue(result.valid)
        self.assertNotIn("run_id", vars(result.contract))
        self.assert_no_real_execution(result)

    def test_scenario_16_preparation_does_not_consume_authorization(self) -> None:
        parent = prerequisite()
        before = copy.deepcopy(parent)
        result = prepare_agent_execution_contract(parent, execution_mode="standard")
        self.assertEqual(parent, before)
        self.assertNotIn("consumed", vars(result.contract))
        self.assert_no_real_execution(result)

    def test_scenario_17_later_denied_permission_requires_fresh_blocking_assessment(self) -> None:
        prepared = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        denied = prerequisite(
            AgentActionPrerequisiteOutcome.BLOCKED,
            reasons=(
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_DENIED,
            ),
        )
        fresh = prepare_agent_execution_contract(denied, execution_mode="standard")
        self.assertTrue(validate_agent_execution_contract(prepared.contract).valid)
        self.assert_atomic_invalid(
            fresh, ["agent_execution_contract_prerequisites_blocked"]
        )
        self.assert_no_real_execution(fresh)

    def test_scenario_18_later_unavailable_runtime_requires_fresh_blocking_assessment(self) -> None:
        prepared = prepare_agent_execution_contract(
            prerequisite(), execution_mode="standard"
        )
        unavailable = prerequisite(
            AgentActionPrerequisiteOutcome.BLOCKED,
            reasons=(
                AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
            ),
        )
        fresh = prepare_agent_execution_contract(
            unavailable, execution_mode="standard"
        )
        self.assertTrue(validate_agent_execution_contract(prepared.contract).valid)
        self.assert_atomic_invalid(
            fresh, ["agent_execution_contract_prerequisites_blocked"]
        )
        self.assert_no_real_execution(fresh)

    def test_scenario_19_exact_value_serializes_and_deserializes(self) -> None:
        original = contract(execution_mode="critical")
        restored = AgentExecutionContract(**json.loads(json.dumps(asdict(original))))
        result = validate_agent_execution_contract(restored)
        self.assertEqual(result.contract, original)
        self.assert_no_real_execution(result)

    def test_scenario_20_duplicate_serialized_values_validate_individually_and_equal(self) -> None:
        payload = json.dumps(asdict(contract()))
        first = AgentExecutionContract(**json.loads(payload))
        second = AgentExecutionContract(**json.loads(payload))
        first_result = validate_agent_execution_contract(first)
        second_result = validate_agent_execution_contract(second)
        self.assertTrue(first_result.valid and second_result.valid)
        self.assertEqual(first_result.contract, second_result.contract)
        self.assert_no_real_execution(second_result)

    def test_scenario_21_unsupported_operation_fails_intrinsic_and_preparation(self) -> None:
        intrinsic = validate_agent_execution_contract(
            contract(operation_id="repository_file_write")
        )
        prepared = prepare_agent_execution_contract(
            prerequisite(operation_id="repository_file_write"),
            execution_mode="standard",
        )
        self.assert_atomic_invalid(intrinsic, ["operation_id_not_supported"])
        self.assert_atomic_invalid(
            prepared,
            ["agent_execution_contract_prerequisite_result_incoherent"],
        )
        self.assert_no_real_execution(prepared)

    def test_scenario_22_invalid_resource_fails_semantic_validation(self) -> None:
        result = validate_agent_execution_contract(
            contract(resource="synthetic/../input.txt")
        )
        self.assert_atomic_invalid(result, ["resource_parent_segment"])
        self.assert_no_real_execution(result)

    def test_scenario_23_human_assignment_cannot_supply_an_agent_contract(self) -> None:
        parent = invalid_prerequisite(
            (
                AgentActionPrerequisiteFinding(
                    "agent_action_prerequisite_not_applicable_to_human_actor",
                    "Synthetic Human Actor rejection from the Agent-only layer.",
                ),
            )
        )
        result = prepare_agent_execution_contract(parent, execution_mode="standard")
        self.assert_atomic_invalid(
            result, ["agent_action_prerequisite_not_applicable_to_human_actor"]
        )
        self.assert_no_real_execution(result)

    def test_scenario_24_runtime_owned_inference_is_outside_scope(self) -> None:
        result = prepare_agent_execution_contract(
            prerequisite(option_id=None), execution_mode="standard"
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisite_result_incoherent"],
        )
        self.assert_no_real_execution(result)

    def test_scenario_25_schema_rejects_extra_tool_id(self) -> None:
        validator = load_validator("agent-execution-contract.schema.json")
        self.assertTrue(
            list(validator.iter_errors(asdict(contract()) | {"tool_id": "tool"}))
        )
        result = validate_agent_execution_contract(contract())
        self.assert_no_real_execution(result)

    def test_scenario_26_schema_rejects_extra_lifecycle_status(self) -> None:
        validator = load_validator("agent-execution-contract.schema.json")
        self.assertTrue(
            list(validator.iter_errors(asdict(contract()) | {"status": "pending"}))
        )
        result = validate_agent_execution_contract(contract())
        self.assert_no_real_execution(result)

    def test_scenario_27_contract_cannot_be_interpreted_as_authorization(self) -> None:
        result = validate_agent_execution_contract(contract())
        self.assertTrue(result.valid)
        self.assertTrue(
            {
                "authority_kind",
                "authority_id",
                "authorization_state",
                "permission_state",
            }.isdisjoint(vars(result.contract))
        )
        self.assert_no_real_execution(result)

    def test_scenario_28_preparation_and_validation_do_not_dispatch_or_perform_io(self) -> None:
        with ExitStack() as stack:
            failure = AssertionError("Agent Execution Contract attempted external work")
            for target in (
                "builtins.open",
                "os.listdir",
                "os.scandir",
                "os.stat",
                "socket.socket",
                "socket.create_connection",
                "sqlite3.connect",
                "subprocess.run",
                "subprocess.Popen",
                "urllib.request.urlopen",
                "time.time",
                "random.random",
                "uuid.uuid4",
            ):
                stack.enter_context(patch(target, side_effect=failure))
            prepared = prepare_agent_execution_contract(
                prerequisite(), execution_mode="standard"
            )
            validated = validate_agent_execution_contract(prepared.contract)
        self.assertTrue(prepared.valid and validated.valid)
        self.assert_no_real_execution(validated)


class AgentExecutionContractSafetyBoundaryTests(AgentExecutionContractFixture):
    def test_static_module_has_no_io_randomness_clock_persistence_or_execution_calls(
        self,
    ) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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
                    "glob",
                    "hashlib",
                    "http",
                    "os",
                    "pathlib",
                    "random",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "time",
                    "urllib",
                    "uuid",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "write_text",
                    "write_bytes",
                    "resolve",
                    "stat",
                    "listdir",
                    "scandir",
                    "getenv",
                    "system",
                    "run",
                    "Popen",
                    "time",
                    "uuid4",
                    "dispatch",
                    "execute",
                    "invoke",
                    "enforce",
                }
            )
        )

    def test_dynamic_guards_cover_validation_and_every_preparation_outcome(self) -> None:
        inputs = (
            prerequisite(),
            prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
            prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
            invalid_prerequisite(),
            replace(prerequisite(), actor_id=None),
        )
        with ExitStack() as stack:
            failure = AssertionError("Agent Execution Contract attempted external work")
            for target in (
                "builtins.open",
                "os.listdir",
                "os.scandir",
                "os.stat",
                "socket.socket",
                "sqlite3.connect",
                "subprocess.run",
                "subprocess.Popen",
                "urllib.request.urlopen",
                "time.time",
                "random.random",
                "uuid.uuid4",
            ):
                stack.enter_context(patch(target, side_effect=failure))
            self.assertTrue(validate_agent_execution_contract(contract()).valid)
            results = tuple(
                prepare_agent_execution_contract(item, execution_mode="standard")
                for item in inputs
            )
        self.assertEqual(len(results), 5)
        self.assertTrue(results[0].valid)
        self.assertTrue(all(not result.valid for result in results[1:]))

    def test_module_exposes_no_serializer_registry_persistence_or_execution_api(self) -> None:
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        forbidden_fragments = (
            "serialize",
            "registry",
            "cache",
            "persist",
            "lookup",
            "permission_decision",
            "authenticate",
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
