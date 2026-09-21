"""Focused value, preparation, scenario, schema, and purity tests for AIO-042."""

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
import secrets
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request
import uuid

import engineering_orchestration
import engineering_orchestration.agent_execution_run as subject
from engineering_orchestration.agent_action_prerequisite import (
    AgentActionPrerequisiteFinding,
    AgentActionPrerequisiteOutcome,
    AgentActionPrerequisiteReason,
    AgentActionPrerequisiteResult,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
    AgentExecutionContractValidationResult,
    prepare_agent_execution_contract,
)
from engineering_orchestration.agent_execution_run import (
    AgentExecutionRun,
    AgentExecutionRunFinding,
    AgentExecutionRunValidationResult,
    prepare_agent_execution_run,
    validate_agent_execution_run,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "engineering_orchestration" / "agent_execution_run.py"
RESPONSIBILITY_KEY = (
    "AIO-042",
    "architecture-change",
    "implement",
    "software-engineer",
)
ACTOR_ID = "agent::assigned"
RUNTIME_OPTION_ID = "runtime::one"
OPTION_ID = "option::external"
ENVIRONMENT_ID = "environment::synthetic"
OPERATION_ID = "repository_file_read"
RESOURCE = "synthetic/input.txt"
RUN_ID = "run::opaque-one"
SATISFIED_REASON = (
    AgentActionPrerequisiteReason.
    ALL_CURRENTLY_MODELED_ACTION_PREREQUISITES_SATISFIED
)
CONTRACT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-contract.schema.json"
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
    """Build one synthetic, observably coherent AIO-040 result."""

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
        AgentActionPrerequisiteFinding(
            "synthetic_parent",
            "Synthetic parent finding.",
        ),
    ),
) -> AgentActionPrerequisiteResult:
    """Build one coherent atomic-invalid synthetic AIO-040 result."""

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
    """Build one synthetic AIO-041 value without implying provenance."""

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


def run(
    run_id: object = RUN_ID,
    *,
    bound_contract: object | None = None,
) -> AgentExecutionRun:
    """Build one synthetic Run value without implying canonical preparation."""

    return AgentExecutionRun(
        run_id,  # type: ignore[arg-type]
        (
            contract() if bound_contract is None else bound_contract
        ),  # type: ignore[arg-type]
    )


def restore_run(payload: str) -> AgentExecutionRun:
    """Restore the closed nested mapping used by serialization tests."""

    document = json.loads(payload)
    return AgentExecutionRun(
        run_id=document["run_id"],
        contract=AgentExecutionContract(**document["contract"]),
    )


class AgentExecutionRunFixture(unittest.TestCase):
    def assert_atomic_invalid(
        self,
        result: AgentExecutionRunValidationResult,
        codes: list[str],
        messages: list[str] | None = None,
    ) -> None:
        self.assertIs(type(result), AgentExecutionRunValidationResult)
        self.assertFalse(result.valid)
        self.assertIs(type(result.findings), tuple)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.run)
        if messages is not None:
            self.assertEqual(
                [finding.message for finding in result.findings],
                messages,
            )

    def assert_no_lifecycle_dispatch_invocation(
        self,
        result: AgentExecutionRunValidationResult,
    ) -> None:
        """Assert the three mandatory negative boundaries for each scenario."""

        self.assertEqual(
            [field.name for field in fields(AgentExecutionRunValidationResult)],
            ["valid", "findings", "run"],
        )
        if result.run is not None:
            self.assertEqual(
                [field.name for field in fields(result.run)],
                ["run_id", "contract"],
            )
            self.assertTrue(
                {
                    "status",
                    "state",
                    "transition",
                    "created_at",
                    "started_at",
                    "completed_at",
                    "cancelled_at",
                    "failed_at",
                    "tool_id",
                    "result",
                    "error",
                }.isdisjoint(vars(result.run))
            )
        public_names = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        self.assertTrue(
            all(
                not any(
                    fragment in name
                    for fragment in (
                        "lifecycle",
                        "transition",
                        "dispatch",
                        "invoke",
                        "invocation",
                    )
                )
                for name in public_names
            )
        )


class AgentExecutionRunValueAndValidationTests(AgentExecutionRunFixture):
    def test_public_values_are_frozen_tuple_backed_and_exactly_shaped(self) -> None:
        self.assertEqual(
            [field.name for field in fields(AgentExecutionRun)],
            ["run_id", "contract"],
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionRunFinding)],
            ["code", "message"],
        )
        self.assertEqual(
            [field.name for field in fields(AgentExecutionRunValidationResult)],
            ["valid", "findings", "run"],
        )
        values = (
            run(),
            AgentExecutionRunFinding("code", "message"),
            AgentExecutionRunValidationResult(True, (), run()),
        )
        for value in values:
            with self.subTest(type=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    value.synthetic = "changed"  # type: ignore[misc]
        self.assertIs(type(values[2].findings), tuple)

    def test_direct_module_public_api_and_no_package_root_export(self) -> None:
        self.assertFalse(hasattr(engineering_orchestration, "AgentExecutionRun"))
        self.assertFalse(
            hasattr(engineering_orchestration, "prepare_agent_execution_run")
        )
        for name in (
            "AgentExecutionRun",
            "AgentExecutionRunFinding",
            "AgentExecutionRunValidationResult",
            "validate_agent_execution_run",
            "prepare_agent_execution_run",
        ):
            self.assertIn(name, vars(subject))

    def test_exact_run_type_is_required_and_subclasses_are_rejected(self) -> None:
        expected = AgentExecutionRunValidationResult(
            False,
            (
                AgentExecutionRunFinding(
                    "agent_execution_run_invalid_type",
                    "Agent Execution Run must be an exact AgentExecutionRun "
                    "value.",
                ),
            ),
            None,
        )
        self.assertEqual(validate_agent_execution_run(object()), expected)
        self.assertEqual(validate_agent_execution_run(None), expected)

        class DerivedRun(AgentExecutionRun):
            pass

        supplied = run()
        derived = DerivedRun(supplied.run_id, supplied.contract)
        self.assertEqual(validate_agent_execution_run(derived), expected)

    def test_valid_run_preserves_exact_run_and_nested_contract_objects(self) -> None:
        bound_contract = contract(execution_mode="critical")
        supplied = run("opaque::preserved", bound_contract=bound_contract)
        result = validate_agent_execution_run(supplied)
        self.assertEqual(
            result,
            AgentExecutionRunValidationResult(True, (), supplied),
        )
        self.assertIs(result.run, supplied)
        self.assertIs(result.run.contract, bound_contract)

    def test_run_id_invalid_values_have_exact_code_and_message(self) -> None:
        class DerivedRunId(str):
            pass

        message = "Agent Execution Run run_id must be an exact nonempty string."
        for value in ("", None, False, 0, object(), DerivedRunId("run::one")):
            with self.subTest(value=value):
                self.assert_atomic_invalid(
                    validate_agent_execution_run(run(value)),
                    ["agent_execution_run_run_id_invalid"],
                    [message],
                )

    def test_run_id_is_opaque_case_sensitive_and_never_normalized(self) -> None:
        values = (
            "run::CaseSensitive",
            "RUN::casesensitive",
            "  run id with whitespace  ",
            " ",
            "550e8400-e29b-41d4-a716-446655440000",
            "001",
        )
        validated = tuple(validate_agent_execution_run(run(value)) for value in values)
        self.assertTrue(all(result.valid for result in validated))
        self.assertEqual(
            [result.run.run_id for result in validated],  # type: ignore[union-attr]
            list(values),
        )
        self.assertEqual(len({result.run for result in validated}), len(values))

    def test_nested_contract_findings_are_converted_in_locked_order(
        self,
    ) -> None:
        supplied = run(
            "",
            bound_contract=contract(
                task_id="",
                actor_id=object(),
                operation_id="Malformed-Operation",
                resource="synthetic/../input.txt",
                execution_mode="turbo",
            ),
        )
        self.assert_atomic_invalid(
            validate_agent_execution_run(supplied),
            [
                "agent_execution_run_run_id_invalid",
                "agent_execution_contract_task_id_invalid",
                "agent_execution_contract_actor_id_invalid",
                "operation_id_invalid_syntax",
                "resource_parent_segment",
                "agent_execution_contract_execution_mode_not_supported",
            ],
            [
                "Agent Execution Run run_id must be an exact nonempty string.",
                "Agent Execution Contract task_id must be an exact nonempty string.",
                "Agent Execution Contract actor_id must be an exact nonempty string.",
                "Operation Requirement operation_id must use ASCII "
                "lower_snake_case syntax.",
                "Operation Requirement resource must not contain a parent segment.",
                "Agent Execution Contract execution_mode must be one of: "
                "lite, standard, deep, critical.",
            ],
        )

    def test_wrong_nested_contract_type_preserves_parent_finding_exactly(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_run(run(bound_contract=object())),
            ["agent_execution_contract_invalid_type"],
            [
                "Agent Execution Contract must be an exact "
                "AgentExecutionContract value."
            ],
        )

    def test_full_equality_and_logical_identity_have_distinct_semantics(self) -> None:
        first = run("run::shared")
        duplicate = run("run::shared")
        conflict = run(
            "run::shared",
            bound_contract=contract(resource="synthetic/other.txt"),
        )
        another_attempt = run("run::another")
        self.assertEqual(first, duplicate)
        self.assertNotEqual(first, conflict)
        self.assertNotEqual(first, another_attempt)
        self.assertEqual(first.run_id, conflict.run_id)
        self.assertEqual(first.contract, another_attempt.contract)
        self.assertTrue(validate_agent_execution_run(first).valid)
        self.assertTrue(validate_agent_execution_run(conflict).valid)

    def test_json_mapping_round_trip_preserves_value_not_provenance(self) -> None:
        original = run(
            "run::serialized",
            bound_contract=contract(execution_mode="deep"),
        )
        payload = json.dumps(asdict(original), sort_keys=True)
        restored = restore_run(payload)
        result = validate_agent_execution_run(restored)
        self.assertTrue(result.valid)
        self.assertEqual(result.run, original)
        self.assertIsNot(result.run, original)
        self.assertIsNot(result.run.contract, original.contract)
        self.assertTrue(
            {
                "preparation_provenance",
                "freshness",
                "globally_unique",
                "authorized",
            }.isdisjoint(asdict(restored))
        )

    def test_direct_construction_only_proves_intrinsic_value_semantics(self) -> None:
        directly_constructed = AgentExecutionRun(RUN_ID, contract())
        result = validate_agent_execution_run(directly_constructed)
        self.assertTrue(result.valid)
        self.assertTrue(
            {
                "prepared",
                "fresh",
                "provenance",
                "unique",
                "authorized",
                "consumed",
                "ready",
            }.isdisjoint(vars(result.run))
        )


class AgentExecutionRunPreparationTests(AgentExecutionRunFixture):
    def test_preparation_calls_aio_041_once_and_binds_intended_object(
        self,
    ) -> None:
        intended = contract(execution_mode="critical")
        parent = prerequisite()
        with patch.object(
            subject,
            "prepare_agent_execution_contract",
            wraps=prepare_agent_execution_contract,
        ) as prepare_contract:
            result = prepare_agent_execution_run(
                intended,
                parent,
                execution_mode="critical",
                run_id="run::caller-supplied",
            )
        self.assertTrue(result.valid)
        self.assertIs(result.run.contract, intended)
        self.assertEqual(result.run.run_id, "run::caller-supplied")
        prepare_contract.assert_called_once_with(
            parent,
            execution_mode="critical",
        )

    def test_preparation_finding_categories_have_exact_locked_order(self) -> None:
        result = prepare_agent_execution_run(
            contract(task_id="", actor_id=object()),
            prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
            execution_mode=None,  # type: ignore[arg-type]
            run_id="",
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_run_run_id_invalid",
                "agent_execution_contract_task_id_invalid",
                "agent_execution_contract_actor_id_invalid",
                "agent_execution_contract_prerequisites_blocked",
                "agent_execution_contract_execution_mode_invalid_type",
            ],
            [
                "Agent Execution Run run_id must be an exact nonempty string.",
                "Agent Execution Contract task_id must be an exact nonempty string.",
                "Agent Execution Contract actor_id must be an exact nonempty string.",
                "Agent Execution Contract preparation requires "
                "prerequisite_result outcome 'satisfied'; received 'blocked'.",
                "Agent Execution Contract execution_mode must be an exact string.",
            ],
        )

    def test_contract_mismatch_has_exact_code_and_message(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(actor_id="agent::fresh-other"),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_run_contract_mismatch"],
            [
                "Freshly prepared Agent Execution Contract must exactly "
                "equal intended_contract."
            ],
        )

    def test_all_eleven_fresh_contract_field_mismatches_fail_atomically(self) -> None:
        intended = contract()
        mutations = {
            "task_id": "AIO-042-other",
            "workflow_id": "workflow::other",
            "stage_id": "stage::other",
            "role_id": "role::other",
            "actor_id": "actor::other",
            "runtime_option_id": "runtime::other",
            "option_id": "option::other",
            "environment_id": "environment::other",
            # The current Core vocabulary has one operation. This mocked valid
            # AIO-041 result isolates and proves AIO-042's exact equality gate.
            "operation_id": "synthetic_alternate_operation",
            "resource": "synthetic/other.txt",
            "execution_mode": "deep",
        }
        for field_name, value in mutations.items():
            with self.subTest(field=field_name):
                fresh = replace(intended, **{field_name: value})
                parent_result = AgentExecutionContractValidationResult(
                    True,
                    (),
                    fresh,
                )
                with patch.object(
                    subject,
                    "prepare_agent_execution_contract",
                    return_value=parent_result,
                ) as prepare_contract:
                    result = prepare_agent_execution_run(
                        intended,
                        prerequisite(),
                        execution_mode="standard",
                        run_id=RUN_ID,
                    )
                self.assert_atomic_invalid(
                    result,
                    ["agent_execution_run_contract_mismatch"],
                )
                prepare_contract.assert_called_once()

    def test_blocked_and_unresolved_inputs_retain_exact_aio_041_findings(self) -> None:
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
                self.assert_atomic_invalid(
                    prepare_agent_execution_run(
                        contract(),
                        prerequisite(outcome),
                        execution_mode="standard",
                        run_id=RUN_ID,
                    ),
                    [code],
                    [message],
                )

    def test_invalid_parent_findings_preserve_order_and_multiplicity(
        self,
    ) -> None:
        parent_findings = (
            AgentActionPrerequisiteFinding("same", "Repeated finding."),
            AgentActionPrerequisiteFinding("same", "Repeated finding."),
            AgentActionPrerequisiteFinding("later", "Later finding."),
        )
        self.assert_atomic_invalid(
            prepare_agent_execution_run(
                contract(),
                invalid_prerequisite(parent_findings),
                execution_mode="standard",
                run_id=RUN_ID,
            ),
            ["same", "same", "later"],
            ["Repeated finding.", "Repeated finding.", "Later finding."],
        )

    def test_wrong_type_and_incoherent_parent_are_atomic(self) -> None:
        cases = (
            (
                object(),
                "agent_execution_contract_prerequisite_result_invalid_type",
            ),
            (
                replace(prerequisite(), actor_id=None),
                "agent_execution_contract_prerequisite_result_incoherent",
            ),
        )
        for parent, code in cases:
            with self.subTest(code=code):
                self.assert_atomic_invalid(
                    prepare_agent_execution_run(
                        contract(),
                        parent,  # type: ignore[arg-type]
                        execution_mode="standard",
                        run_id=RUN_ID,
                    ),
                    [code],
                )

    def test_wrong_intended_type_is_atomic_and_does_not_add_mismatch(self) -> None:
        self.assert_atomic_invalid(
            prepare_agent_execution_run(
                object(),  # type: ignore[arg-type]
                prerequisite(),
                execution_mode="standard",
                run_id=RUN_ID,
            ),
            ["agent_execution_contract_invalid_type"],
            [
                "Agent Execution Contract must be an exact "
                "AgentExecutionContract value."
            ],
        )

    def test_preparation_is_deterministic_and_mutates_no_inputs(self) -> None:
        intended = contract()
        parent = prerequisite()
        intended_before = copy.deepcopy(intended)
        parent_before = copy.deepcopy(parent)
        first = prepare_agent_execution_run(
            intended,
            parent,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        second = prepare_agent_execution_run(
            intended,
            parent,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertEqual(intended, intended_before)
        self.assertEqual(parent, parent_before)
        self.assertEqual(first, second)
        self.assertIs(first.run.contract, intended)
        self.assertIs(second.run.contract, intended)


class AgentExecutionRunSchemaTests(AgentExecutionRunFixture):
    def test_schema_is_closed_two_field_shape_with_nested_offline_ref(self) -> None:
        schema = load_validator("agent-execution-run.schema.json").schema
        self.assertEqual(schema["required"], ["run_id", "contract"])
        self.assertEqual(list(schema["properties"]), ["run_id", "contract"])
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(
            schema["properties"]["run_id"],
            {
                "type": "string",
                "minLength": 1,
                "description": (
                    "Exact opaque caller-supplied identity of one concrete "
                    "execution attempt."
                ),
            },
        )
        self.assertEqual(
            schema["properties"]["contract"]["$ref"],
            CONTRACT_SCHEMA_ID,
        )
        self.assertNotIn("properties", schema["properties"]["contract"])

    def test_schema_validates_nested_contract_and_rejects_wrong_shapes(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        valid = asdict(run())
        self.assertEqual(list(validator.iter_errors(valid)), [])
        cases = (
            {},
            {"run_id": RUN_ID},
            {"contract": asdict(contract())},
            {"run_id": "", "contract": asdict(contract())},
            {"run_id": 7, "contract": asdict(contract())},
            {"run_id": RUN_ID, "contract": "not-an-object"},
            {
                "run_id": RUN_ID,
                "contract": asdict(contract()) | {"execution_mode": "turbo"},
            },
            {
                "run_id": RUN_ID,
                "contract": asdict(contract()) | {"resource": ""},
            },
        )
        for document in cases:
            with self.subTest(document=document):
                self.assertTrue(list(validator.iter_errors(document)))

    def test_schema_rejects_all_locked_top_level_leakage_fields(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        base = asdict(run())
        excluded = (
            "attempt_id",
            "retry_count",
            "previous_run_id",
            "contract_id",
            "contract_hash",
            "status",
            "state",
            "created_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "tool_id",
            "adapter_id",
            "provider_id",
            "authorization_id",
            "grant_id",
            "consumed",
            "result",
            "error",
            "tokens",
            "cost",
            "duration",
            "events",
            "metadata",
            "extensions",
        )
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(
                        validator.iter_errors(
                            base | {field_name: "synthetic-value"}
                        )
                    )
                )

    def test_nested_schema_resolution_never_calls_network(self) -> None:
        failure = AssertionError("schema resolution attempted network access")
        with patch.object(
            urllib.request,
            "urlopen",
            side_effect=failure,
        ), patch.object(
            socket,
            "create_connection",
            side_effect=failure,
        ), patch.object(
            socket,
            "getaddrinfo",
            side_effect=failure,
        ):
            validator = load_validator("agent-execution-run.schema.json")
            errors = list(validator.iter_errors(asdict(run())))
            unknown_reference = validator.evolve(
                schema={
                    "$ref": (
                        "https://example.invalid/"
                        "unregistered-agent-execution-run.schema.json"
                    )
                }
            )
            with self.assertRaises(Exception) as raised:
                unknown_reference.validate({})
        self.assertEqual(errors, [])
        self.assertNotIsInstance(raised.exception, AssertionError)


class AgentExecutionRunScenarioTests(AgentExecutionRunFixture):
    """The 36 authorized AIO-042 investigation scenarios, explicitly named."""

    def test_scenario_01_first_run_for_valid_contract(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id="run::first",
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.run.run_id, "run::first")
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_02_second_run_for_same_contract_with_new_id(self) -> None:
        intended = contract()
        first = prepare_agent_execution_run(
            intended,
            prerequisite(),
            execution_mode="standard",
            run_id="run::first",
        )
        second = prepare_agent_execution_run(
            intended,
            prerequisite(),
            execution_mode="standard",
            run_id="run::second",
        )
        self.assertTrue(first.valid and second.valid)
        self.assertEqual(first.run.contract, second.run.contract)
        self.assertNotEqual(first.run, second.run)
        self.assert_no_lifecycle_dispatch_invocation(second)

    def test_scenario_03_same_id_plus_same_contract_is_same_run(self) -> None:
        first = run("run::same")
        second = run("run::same")
        first_result = validate_agent_execution_run(first)
        second_result = validate_agent_execution_run(second)
        self.assertTrue(first_result.valid and second_result.valid)
        self.assertEqual(first_result.run, second_result.run)
        self.assert_no_lifecycle_dispatch_invocation(second_result)

    def test_scenario_04_same_id_different_contract_is_external_conflict(
        self,
    ) -> None:
        first_result = validate_agent_execution_run(run("run::conflict"))
        second_result = validate_agent_execution_run(
            run(
                "run::conflict",
                bound_contract=contract(resource="synthetic/other.txt"),
            )
        )
        self.assertTrue(first_result.valid and second_result.valid)
        self.assertEqual(first_result.run.run_id, second_result.run.run_id)
        self.assertNotEqual(first_result.run.contract, second_result.run.contract)
        self.assertNotEqual(first_result.run, second_result.run)
        self.assert_no_lifecycle_dispatch_invocation(second_result)

    def test_scenario_05_different_ids_plus_same_contract_are_distinct(self) -> None:
        intended = contract()
        first_result = validate_agent_execution_run(
            run("run::one", bound_contract=intended)
        )
        second_result = validate_agent_execution_run(
            run("run::two", bound_contract=intended)
        )
        self.assertTrue(first_result.valid and second_result.valid)
        self.assertIs(first_result.run.contract, second_result.run.contract)
        self.assertNotEqual(first_result.run, second_result.run)
        self.assert_no_lifecycle_dispatch_invocation(second_result)

    def test_scenario_06_invalid_contract_produces_no_run(self) -> None:
        result = prepare_agent_execution_run(
            contract(resource="synthetic/../input.txt"),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(result, ["resource_parent_segment"])
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_07_fresh_prerequisite_blocked_produces_no_run(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_blocked"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_08_fresh_prerequisite_unresolved_produces_no_run(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_unresolved"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_09_satisfied_prerequisite_prepares_identity_only(
        self,
    ) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.run, run())
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_10_fresh_mode_mismatch_produces_no_run(self) -> None:
        result = prepare_agent_execution_run(
            contract(execution_mode="standard"),
            prerequisite(),
            execution_mode="deep",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_run_contract_mismatch"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_11_fresh_contract_differs_from_intended(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(actor_id="agent::changed"),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_run_contract_mismatch"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_12_permission_changed_blocks_fresh_preparation(self) -> None:
        changed = prerequisite(
            AgentActionPrerequisiteOutcome.BLOCKED,
            reasons=(
                AgentActionPrerequisiteReason.
                ENVIRONMENT_OPERATION_PERMISSION_DENIED,
            ),
        )
        result = prepare_agent_execution_run(
            contract(),
            changed,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_blocked"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_13_runtime_availability_change_blocks_preparation(
        self,
    ) -> None:
        changed = prerequisite(
            AgentActionPrerequisiteOutcome.BLOCKED,
            reasons=(
                AgentActionPrerequisiteReason.CANDIDATE_PREREQUISITES_BLOCKED,
            ),
        )
        result = prepare_agent_execution_run(
            contract(),
            changed,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_blocked"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_14_authorization_missing_is_unresolved(self) -> None:
        missing = prerequisite(
            AgentActionPrerequisiteOutcome.UNRESOLVED,
            reasons=(
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_MISSING,
            ),
        )
        result = prepare_agent_execution_run(
            contract(),
            missing,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_unresolved"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_15_authorization_denied_is_blocked(self) -> None:
        denied = prerequisite(
            AgentActionPrerequisiteOutcome.BLOCKED,
            reasons=(
                AgentActionPrerequisiteReason.
                AGENT_EXECUTION_AUTHORIZATION_DENIED,
            ),
        )
        result = prepare_agent_execution_run(
            contract(),
            denied,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisites_blocked"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_16_caller_attested_grant_remains_unauthenticated(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertTrue(
            {
                "authority_id",
                "provenance_reference",
                "grant_id",
                "authenticated",
            }.isdisjoint(vars(result.run))
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_17_intrinsic_direct_construction_has_no_fresh_check(self) -> None:
        result = validate_agent_execution_run(AgentExecutionRun(RUN_ID, contract()))
        self.assertTrue(result.valid)
        self.assertNotIn("fresh", vars(result.run))
        self.assertNotIn("preparation_provenance", vars(result.run))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_18_run_preparation_cannot_immediately_dispatch(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertFalse(hasattr(subject, "dispatch_agent_execution_run"))
        self.assertFalse(hasattr(subject, "start_agent_execution_run"))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_19_tool_id_is_outside_closed_run(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        self.assertTrue(
            list(
                validator.iter_errors(
                    asdict(run()) | {"tool_id": "tool::synthetic"}
                )
            )
        )
        with self.assertRaises(TypeError):
            AgentExecutionRun(  # type: ignore[call-arg]
                run_id=RUN_ID,
                contract=contract(),
                tool_id="tool::synthetic",
            )
        result = validate_agent_execution_run(run())
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_20_result_and_error_are_outside_closed_run(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        for field_name in ("result", "error"):
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(
                        validator.iter_errors(
                            asdict(run()) | {field_name: "synthetic"}
                        )
                    )
                )
        result = validate_agent_execution_run(run())
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_21_telemetry_is_outside_closed_run(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        for field_name in ("tokens", "cost", "duration", "usage"):
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(
                        validator.iter_errors(
                            asdict(run()) | {field_name: 1}
                        )
                    )
                )
        result = validate_agent_execution_run(run())
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_22_lifecycle_status_is_outside_closed_run(self) -> None:
        validator = load_validator("agent-execution-run.schema.json")
        self.assertTrue(
            list(
                validator.iter_errors(
                    asdict(run()) | {"status": "running"}
                )
            )
        )
        result = validate_agent_execution_run(run())
        self.assertNotIn("status", vars(result.run))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_23_semantic_retry_uses_new_id(self) -> None:
        intended = contract()
        first = prepare_agent_execution_run(
            intended,
            prerequisite(),
            execution_mode="standard",
            run_id="run::attempt-one",
        )
        retry = prepare_agent_execution_run(
            intended,
            prerequisite(),
            execution_mode="standard",
            run_id="run::attempt-two",
        )
        self.assertTrue(first.valid and retry.valid)
        self.assertNotEqual(first.run.run_id, retry.run.run_id)
        self.assertNotEqual(first.run, retry.run)
        self.assertNotIn("retry_of", vars(retry.run))
        self.assert_no_lifecycle_dispatch_invocation(retry)

    def test_scenario_24_cancellation_is_outside_model(self) -> None:
        result = validate_agent_execution_run(run())
        self.assertTrue(result.valid)
        self.assertTrue(
            {"cancel", "cancelled", "cancelled_at"}.isdisjoint(vars(result.run))
        )
        self.assertFalse(hasattr(subject, "cancel_agent_execution_run"))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_25_identity_requires_no_persistence(self) -> None:
        result = validate_agent_execution_run(run())
        self.assertTrue(result.valid)
        public_names = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        self.assertTrue(
            all(
                not any(
                    fragment in name
                    for fragment in (
                        "persist",
                        "registry",
                        "database",
                        "cache",
                        "queue",
                        "repository",
                        "store",
                    )
                )
                for name in public_names
            )
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_26_cross_session_duplicate_id_is_unproven(
        self,
    ) -> None:
        session_one = validate_agent_execution_run(run("run::cross-session"))
        session_two = validate_agent_execution_run(run("run::cross-session"))
        unseen_conflict = validate_agent_execution_run(
            run(
                "run::cross-session",
                bound_contract=contract(resource="synthetic/session-two.txt"),
            )
        )
        self.assertTrue(
            session_one.valid and session_two.valid and unseen_conflict.valid
        )
        self.assertEqual(session_one.run, session_two.run)
        self.assertNotEqual(session_one.run, unseen_conflict.run)
        self.assert_no_lifecycle_dispatch_invocation(unseen_conflict)

    def test_scenario_27_caller_reuses_id_without_core_registry(self) -> None:
        first = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id="run::reused-by-caller",
        )
        second = prepare_agent_execution_run(
            contract(resource="synthetic/second.txt"),
            prerequisite(resource="synthetic/second.txt"),
            execution_mode="standard",
            run_id="run::reused-by-caller",
        )
        self.assertTrue(first.valid and second.valid)
        self.assertEqual(first.run.run_id, second.run.run_id)
        self.assertNotEqual(first.run.contract, second.run.contract)
        self.assertNotEqual(first.run, second.run)
        self.assert_no_lifecycle_dispatch_invocation(second)

    def test_scenario_28_coordinator_supplied_id_is_preserved_exactly(self) -> None:
        supplied_id = "runtime/coordinator :: opaque ID  "
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=supplied_id,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.run.run_id, supplied_id)
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_29_uuid_looking_input_is_opaque_not_generated(
        self,
    ) -> None:
        supplied_id = "550e8400-e29b-41d4-a716-446655440000"
        with patch.object(
            uuid,
            "uuid4",
            side_effect=AssertionError("Core attempted UUID generation"),
        ):
            result = prepare_agent_execution_run(
                contract(),
                prerequisite(),
                execution_mode="standard",
                run_id=supplied_id,
            )
        self.assertTrue(result.valid)
        self.assertEqual(result.run.run_id, supplied_id)
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_30_contract_round_trip_before_run_preparation(self) -> None:
        original = contract()
        restored = AgentExecutionContract(**json.loads(json.dumps(asdict(original))))
        result = prepare_agent_execution_run(
            restored,
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.run.contract, original)
        self.assertIs(result.run.contract, restored)
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_31_human_assignment_path_is_outside_agent_run(self) -> None:
        human_boundary = invalid_prerequisite(
            (
                AgentActionPrerequisiteFinding(
                    "agent_action_prerequisite_not_applicable_to_human_actor",
                    "Synthetic Human Actor rejection from the Agent-only layer.",
                ),
            )
        )
        result = prepare_agent_execution_run(
            contract(),
            human_boundary,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_action_prerequisite_not_applicable_to_human_actor"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_32_runtime_owned_inference_path_is_outside_scope(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(option_id=None),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assert_atomic_invalid(
            result,
            ["agent_execution_contract_prerequisite_result_incoherent"],
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_33_only_synthetic_resource_is_used(self) -> None:
        self.assertEqual(RESOURCE, "synthetic/input.txt")
        self.assertTrue(RESOURCE.startswith("synthetic/"))
        result = prepare_agent_execution_run(
            contract(resource=RESOURCE),
            prerequisite(resource=RESOURCE),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.run.contract.resource, RESOURCE)
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_34_run_exists_without_authorization_consumption(self) -> None:
        parent = prerequisite()
        before = copy.deepcopy(parent)
        result = prepare_agent_execution_run(
            contract(),
            parent,
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertEqual(parent, before)
        self.assertNotIn("consumed", vars(result.run))
        self.assertNotIn("authorization_id", vars(result.run))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_35_run_exists_without_tool_binding(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertTrue(
            {"tool_id", "adapter_id", "provider_tool_id"}.isdisjoint(
                vars(result.run)
            )
        )
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_scenario_36_run_exists_without_invocation(self) -> None:
        result = prepare_agent_execution_run(
            contract(),
            prerequisite(),
            execution_mode="standard",
            run_id=RUN_ID,
        )
        self.assertTrue(result.valid)
        self.assertFalse(hasattr(subject, "invoke_agent"))
        self.assertFalse(hasattr(subject, "execute_agent_execution_run"))
        self.assert_no_lifecycle_dispatch_invocation(result)

    def test_matrix_contains_exactly_36_explicit_scenarios(self) -> None:
        scenario_names = {
            name
            for name in vars(type(self))
            if name.startswith("test_scenario_")
        }
        self.assertEqual(len(scenario_names), 36)


class AgentExecutionRunSafetyBoundaryTests(AgentExecutionRunFixture):
    def test_static_module_has_no_io_clock_randomness_or_execution_calls(self) -> None:
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
                    "secrets",
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
                    "monotonic",
                    "perf_counter",
                    "uuid4",
                    "token_hex",
                    "token_urlsafe",
                    "connect",
                    "urlopen",
                    "dispatch",
                    "execute",
                    "invoke",
                    "discover",
                    "probe",
                    "persist",
                    "save",
                }
            )
        )

    def test_dynamic_guards_cover_validation_and_all_preparation_outcomes(self) -> None:
        intended = contract()
        inputs = (
            (intended, prerequisite(), "standard", RUN_ID),
            (
                intended,
                prerequisite(AgentActionPrerequisiteOutcome.BLOCKED),
                "standard",
                RUN_ID,
            ),
            (
                intended,
                prerequisite(AgentActionPrerequisiteOutcome.UNRESOLVED),
                "standard",
                RUN_ID,
            ),
            (intended, invalid_prerequisite(), "standard", RUN_ID),
            (intended, replace(prerequisite(), actor_id=None), "standard", RUN_ID),
            (intended, prerequisite(), "deep", RUN_ID),
            (intended, prerequisite(), "standard", ""),
        )
        with ExitStack() as stack:
            failure = AssertionError("Agent Execution Run attempted external work")
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
                "urllib.request.urlretrieve",
                "time.time",
                "time.monotonic",
                "time.perf_counter",
                "random.random",
                "random.getrandbits",
                "random.randint",
                "secrets.token_hex",
                "secrets.token_urlsafe",
                "uuid.uuid4",
            ):
                stack.enter_context(patch(target, side_effect=failure))
            for name in (
                "dispatch",
                "execute",
                "invoke",
                "discover_tools",
                "probe_runtime",
                "provider_call",
                "persist",
            ):
                stack.enter_context(
                    patch.object(
                        subject,
                        name,
                        create=True,
                        side_effect=failure,
                    )
                )
            self.assertTrue(validate_agent_execution_run(run()).valid)
            self.assertFalse(validate_agent_execution_run(run("")).valid)
            results = tuple(
                prepare_agent_execution_run(
                    supplied_contract,
                    parent,
                    execution_mode=mode,
                    run_id=run_id,
                )
                for supplied_contract, parent, mode, run_id in inputs
            )
        self.assertEqual(len(results), 7)
        self.assertTrue(results[0].valid)
        self.assertTrue(all(not result.valid for result in results[1:]))

    def test_module_exposes_no_lifecycle_persistence_authority_or_execution_api(
        self,
    ) -> None:
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        forbidden_fragments = (
            "lifecycle",
            "status",
            "transition",
            "cancel",
            "retry",
            "registry",
            "cache",
            "persist",
            "lookup",
            "permission_decision",
            "authenticate",
            "consume",
            "replay",
            "tool",
            "dispatch",
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
