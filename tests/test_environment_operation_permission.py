"""Contract, semantic, boundary, and purity tests for permission evidence."""

from __future__ import annotations

import ast
import asyncio
import builtins
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, fields
import glob
import hashlib
import http.client
import io
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request

import engineering_orchestration
import engineering_orchestration.environment_operation_permission as permission
from engineering_orchestration._repository_resource import (
    RepositoryResourceValidationIssue,
    validate_repository_resource,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.agent_runtime_option_availability import (
    AgentRuntimeOptionAvailabilityObservation,
    AgentRuntimeOptionAvailabilityState,
    validate_agent_runtime_option_availability,
)
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionFinding,
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
    EnvironmentOperationPermissionValidationResult,
    validate_environment_operation_permission,
)
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    validate_operation_requirement,
)
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    validate_runtime_operation_capability,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
PERMISSION_MODULE = (
    ROOT
    / "engineering_orchestration"
    / "environment_operation_permission.py"
)
RESOURCE_MODULE = (
    ROOT / "engineering_orchestration" / "_repository_resource.py"
)


def runtime_option(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def observation(
    runtime_option_id: object = "runtime-primary",
    environment_id: object = "environment-primary",
    operation_id: object = "repository_file_read",
    resource: object = "synthetic/input.txt",
    state: object = EnvironmentOperationPermissionState.ALLOWED,
) -> EnvironmentOperationPermissionObservation:
    return EnvironmentOperationPermissionObservation(
        runtime_option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        resource,  # type: ignore[arg-type]
        state,  # type: ignore[arg-type]
    )


class OneShotIterable:
    def __init__(
        self,
        values: list[object],
        label: str,
        capture_order: list[str],
    ) -> None:
        self.values = values
        self.label = label
        self.capture_order = capture_order
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        self.capture_order.append(self.label)
        if self.iterations > 1:
            raise AssertionError("input iterable was consumed more than once")
        return iter(self.values)


class DerivedObservation(EnvironmentOperationPermissionObservation):
    """Subclass used to prove that exact observation type is required."""


class ExplodingObservation:
    @property
    def runtime_option_id(self):
        raise AssertionError("foundational failure must not inspect observations")


class EnvironmentOperationPermissionValueTests(unittest.TestCase):
    def test_state_values_are_exactly_locked(self) -> None:
        self.assertEqual(
            tuple(state.value for state in EnvironmentOperationPermissionState),
            ("allowed", "denied", "unknown"),
        )
        self.assertIsNot(
            EnvironmentOperationPermissionState.DENIED,
            EnvironmentOperationPermissionState.UNKNOWN,
        )
        self.assertTrue(
            {"allow", "ask", "always-ask", "deny"}.isdisjoint(
                state.value for state in EnvironmentOperationPermissionState
            )
        )

    def test_public_values_are_frozen_exact_and_tuple_backed(self) -> None:
        value = observation()
        finding = EnvironmentOperationPermissionFinding("code", "message")
        result = EnvironmentOperationPermissionValidationResult(
            True,
            (),
            (value,),
        )
        self.assertEqual(
            [field.name for field in fields(value)],
            [
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "resource",
                "state",
            ],
        )
        self.assertEqual(
            [field.name for field in fields(finding)],
            ["code", "message"],
        )
        self.assertEqual(
            [field.name for field in fields(result)],
            ["valid", "findings", "normalized_observations"],
        )
        with self.assertRaises(FrozenInstanceError):
            value.state = (  # type: ignore[misc]
                EnvironmentOperationPermissionState.DENIED
            )
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = False  # type: ignore[misc]

    def test_schema_is_exact_five_field_structural_contract(self) -> None:
        schema = load_validator(
            "environment-operation-permission.schema.json"
        ).schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(
            schema["required"],
            [
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "resource",
                "state",
            ],
        )
        self.assertEqual(
            set(schema["properties"]),
            {
                "runtime_option_id",
                "environment_id",
                "operation_id",
                "resource",
                "state",
            },
        )
        self.assertEqual(
            schema["properties"]["state"]["enum"],
            ["allowed", "denied", "unknown"],
        )
        for field_name in (
            "runtime_option_id",
            "environment_id",
            "operation_id",
            "resource",
        ):
            self.assertEqual(
                schema["properties"][field_name]["minLength"],
                1,
            )

    def test_schema_keeps_semantic_relationships_out(self) -> None:
        validator = load_validator(
            "environment-operation-permission.schema.json"
        )
        semantic_invalid = (
            {
                "runtime_option_id": "runtime-missing",
                "environment_id": "environment-primary",
                "operation_id": "repository_file_read",
                "resource": "synthetic/input.txt",
                "state": "allowed",
            },
            {
                "runtime_option_id": "runtime-primary",
                "environment_id": "environment-other",
                "operation_id": "repository_file_write",
                "resource": "synthetic/../input.txt",
                "state": "denied",
            },
        )
        for document in semantic_invalid:
            with self.subTest(document=document):
                self.assertEqual(list(validator.iter_errors(document)), [])

    def test_schema_rejects_all_excluded_field_categories(self) -> None:
        validator = load_validator(
            "environment-operation-permission.schema.json"
        )
        base = {
            "runtime_option_id": "runtime-primary",
            "environment_id": "environment-primary",
            "operation_id": "repository_file_read",
            "resource": "synthetic/input.txt",
            "state": "allowed",
        }
        excluded = {
            "permission_id",
            "actor_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "option_id",
            "provider_id",
            "model_id",
            "tool_id",
            "timestamp",
            "freshness",
            "expires_at",
            "source",
            "provenance",
            "reason",
            "policy",
            "authorization",
            "metadata",
            "extensions",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )


class EnvironmentOperationPermissionValidationTests(unittest.TestCase):
    def assert_valid_state(
        self,
        state: EnvironmentOperationPermissionState,
    ) -> None:
        supplied = observation(state=state)
        result = validate_environment_operation_permission(
            [supplied],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_observations, (supplied,))
        self.assertIs(result.normalized_observations[0], supplied)

    def test_allowed_denied_and_explicit_unknown_are_valid(self) -> None:
        for state in EnvironmentOperationPermissionState:
            with self.subTest(state=state):
                self.assert_valid_state(state)

    def test_missing_observation_is_not_synthesized_or_denied(self) -> None:
        result = validate_environment_operation_permission(
            [],
            [runtime_option("runtime-a"), runtime_option("runtime-b")],
            "environment-primary",
        )
        self.assertEqual(
            result,
            EnvironmentOperationPermissionValidationResult(True, (), ()),
        )
        later_exact_lookup = next(
            iter(result.normalized_observations),
            EnvironmentOperationPermissionState.UNKNOWN,
        )
        self.assertIs(
            later_exact_lookup,
            EnvironmentOperationPermissionState.UNKNOWN,
        )
        self.assertIsNot(
            later_exact_lookup,
            EnvironmentOperationPermissionState.DENIED,
        )

    def test_valid_supplied_observations_use_exact_identity_sorting(self) -> None:
        supplied = [
            observation(
                "runtime-z",
                resource="synthetic/z.txt",
                state=EnvironmentOperationPermissionState.DENIED,
            ),
            observation(
                "runtime-a",
                resource="synthetic/b.txt",
                state=EnvironmentOperationPermissionState.UNKNOWN,
            ),
            observation(
                "runtime-a",
                resource="Synthetic/A.txt",
                state=EnvironmentOperationPermissionState.ALLOWED,
            ),
        ]
        result = validate_environment_operation_permission(
            supplied,
            [runtime_option("runtime-z"), runtime_option("runtime-a")],
            "environment-primary",
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [
                (
                    item.runtime_option_id,
                    item.environment_id,
                    item.operation_id,
                    item.resource,
                )
                for item in result.normalized_observations
            ],
            [
                (
                    "runtime-a",
                    "environment-primary",
                    "repository_file_read",
                    "Synthetic/A.txt",
                ),
                (
                    "runtime-a",
                    "environment-primary",
                    "repository_file_read",
                    "synthetic/b.txt",
                ),
                (
                    "runtime-z",
                    "environment-primary",
                    "repository_file_read",
                    "synthetic/z.txt",
                ),
            ],
        )
        self.assertEqual(
            {id(item) for item in result.normalized_observations},
            {id(item) for item in supplied},
        )

    def test_multiple_runtimes_and_resources_remain_independent(self) -> None:
        supplied = [
            observation("runtime-a", resource="synthetic/one.txt"),
            observation(
                "runtime-a",
                resource="synthetic/two.txt",
                state=EnvironmentOperationPermissionState.DENIED,
            ),
            observation(
                "runtime-b",
                resource="synthetic/one.txt",
                state=EnvironmentOperationPermissionState.UNKNOWN,
            ),
        ]
        result = validate_environment_operation_permission(
            supplied,
            [runtime_option("runtime-a"), runtime_option("runtime-b")],
            "environment-primary",
        )
        self.assertTrue(result.valid)
        self.assertEqual(len(result.normalized_observations), 3)

    def test_runtime_inventory_is_foundational(self) -> None:
        result = validate_environment_operation_permission(
            [ExplodingObservation()],  # type: ignore[list-item]
            [runtime_option("duplicate"), runtime_option("duplicate")],
            "",
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_id"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_snapshot_environment_must_be_exact_nonempty_string(self) -> None:
        class Text(str):
            pass

        for environment_id in ("", None, Text("environment-primary")):
            with self.subTest(environment_id=environment_id):
                result = validate_environment_operation_permission(
                    [ExplodingObservation()],  # type: ignore[list-item]
                    [runtime_option("runtime-primary")],
                    environment_id,  # type: ignore[arg-type]
                )
                self.assertEqual(
                    [(finding.code, finding.message) for finding in result.findings],
                    [
                        (
                            "environment_operation_permission_environment_id_invalid",
                            "Environment Operation Permission snapshot "
                            "environment_id must be an exact nonempty string.",
                        )
                    ],
                )
                self.assertEqual(result.normalized_observations, ())

    def test_exact_observation_type_and_valid_fields_are_required(self) -> None:
        derived = DerivedObservation(
            "runtime-primary",
            "environment-primary",
            "repository_file_read",
            "synthetic/input.txt",
            EnvironmentOperationPermissionState.ALLOWED,
        )
        malformed = (
            observation(runtime_option_id=1),
            observation(environment_id=1),
            observation(operation_id=1),
            observation(resource=1),
            observation(state="allowed"),
        )
        result = validate_environment_operation_permission(
            [derived, ExplodingObservation(), *malformed],  # type: ignore[list-item]
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in result.findings],
            [
                (
                    "environment_operation_permission_observation_invalid_type",
                    "Each supplied Environment Operation Permission Observation "
                    "must be an exact "
                    "EnvironmentOperationPermissionObservation value.",
                ),
                (
                    "environment_operation_permission_observation_invalid",
                    "A supplied Environment Operation Permission Observation "
                    "contains malformed fields or state.",
                ),
            ],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_empty_fields_follow_locked_semantic_categories(self) -> None:
        invalid_runtime = validate_environment_operation_permission(
            [observation(runtime_option_id="")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        invalid_environment = validate_environment_operation_permission(
            [observation(environment_id="")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        invalid_operation = validate_environment_operation_permission(
            [observation(operation_id="")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        invalid_resource = validate_environment_operation_permission(
            [observation(resource="")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(
            [finding.code for finding in invalid_runtime.findings],
            ["environment_operation_permission_observation_invalid"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_environment.findings],
            ["environment_operation_permission_observation_invalid"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_operation.findings],
            ["operation_id_invalid_syntax"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_resource.findings],
            ["resource_empty"],
        )

    def test_unknown_runtime_is_invalid_and_case_sensitive(self) -> None:
        result = validate_environment_operation_permission(
            [observation("runtime-primary")],
            [runtime_option("Runtime-Primary")],
            "environment-primary",
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in result.findings],
            [
                (
                    "agent_runtime_option_not_found",
                    "Agent Runtime Option 'runtime-primary' was not found in "
                    "the supplied inventory.",
                )
            ],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_environment_scope_is_exact_and_case_sensitive(self) -> None:
        exact = validate_environment_operation_permission(
            [observation(environment_id="Environment-Primary")],
            [runtime_option("runtime-primary")],
            "Environment-Primary",
        )
        mismatch = validate_environment_operation_permission(
            [observation(environment_id="environment-primary")],
            [runtime_option("runtime-primary")],
            "Environment-Primary",
        )
        self.assertTrue(exact.valid)
        self.assertEqual(
            [(finding.code, finding.message) for finding in mismatch.findings],
            [
                (
                    "environment_operation_permission_environment_mismatch",
                    "Environment Operation Permission Observation environment_id "
                    "'environment-primary' does not match snapshot "
                    "environment_id 'Environment-Primary'.",
                )
            ],
        )
        self.assertEqual(mismatch.normalized_observations, ())

    def test_environment_a_cannot_satisfy_environment_b(self) -> None:
        supplied = observation(environment_id="environment-a")
        result = validate_environment_operation_permission(
            [supplied],
            [runtime_option("runtime-primary")],
            "environment-b",
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["environment_operation_permission_environment_mismatch"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_malformed_and_unsupported_operations_are_distinct(self) -> None:
        malformed = validate_environment_operation_permission(
            [observation(operation_id="Repository_File_Read")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        unsupported = validate_environment_operation_permission(
            [observation(operation_id="repository_file_write")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in malformed.findings],
            [
                (
                    "operation_id_invalid_syntax",
                    "Environment Operation Permission Observation operation_id "
                    "must use ASCII lower_snake_case syntax.",
                )
            ],
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in unsupported.findings],
            [
                (
                    "operation_id_not_supported",
                    "Operation ID 'repository_file_write' is not supported by Core.",
                )
            ],
        )

    def test_every_canonical_resource_rejection_class_is_reused(self) -> None:
        cases = {
            "": "resource_empty",
            "synthetic/\x00name": "resource_control_character",
            "synthetic/\x1fname": "resource_control_character",
            "synthetic/\x7fname": "resource_control_character",
            "synthetic/\x80name": "resource_control_character",
            "//server/share/input.txt": "resource_unc_path",
            "\\\\server\\share\\input.txt": "resource_unc_path",
            "/synthetic/input.txt": "resource_absolute_path",
            "C:/synthetic/input.txt": "resource_drive_qualified_path",
            "C:synthetic/input.txt": "resource_drive_qualified_path",
            "https://example.invalid/input.txt": "resource_uri_scheme",
            "git+ssh:synthetic/input.txt": "resource_uri_scheme",
            "~/synthetic/input.txt": "resource_leading_tilde",
            "synthetic\\input.txt": "resource_backslash",
            "synthetic/input/": "resource_trailing_slash",
            "synthetic//input.txt": "resource_empty_segment",
            "synthetic/./input.txt": "resource_dot_segment",
            "synthetic/../input.txt": "resource_parent_segment",
        }
        for resource, code in cases.items():
            with self.subTest(resource=resource):
                result = validate_environment_operation_permission(
                    [observation(resource=resource)],
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    [code],
                )
                self.assertEqual(result.normalized_observations, ())

        for character in "*?[]{}":
            with self.subTest(glob_meta=character):
                result = validate_environment_operation_permission(
                    [observation(resource=f"synthetic/name{character}.txt")],
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertEqual(
                    [finding.code for finding in result.findings],
                    ["resource_glob_meta"],
                )

    def test_resource_precedence_and_message_are_contextual(self) -> None:
        result = validate_environment_operation_permission(
            [observation(resource="synthetic//../*.txt/")],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in result.findings],
            [
                (
                    "resource_trailing_slash",
                    "Environment Operation Permission Observation resource "
                    "'synthetic//../*.txt/' must not end with a slash.",
                )
            ],
        )

    def test_identical_duplicates_are_invalid_for_every_state(self) -> None:
        for state in EnvironmentOperationPermissionState:
            with self.subTest(state=state):
                supplied = observation(state=state)
                result = validate_environment_operation_permission(
                    [supplied, supplied],
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertEqual(
                    [(finding.code, finding.message) for finding in result.findings],
                    [
                        (
                            "duplicate_environment_operation_permission",
                            "Environment Operation Permission Observation "
                            "identity (runtime_option_id='runtime-primary', "
                            "environment_id='environment-primary', "
                            "operation_id='repository_file_read', "
                            "resource='synthetic/input.txt') has more than one "
                            "supplied observation with the same state.",
                        )
                    ],
                )
                self.assertEqual(result.normalized_observations, ())

    def test_all_six_conflict_permutations_are_identical_invalid_input(
        self,
    ) -> None:
        allowed = EnvironmentOperationPermissionState.ALLOWED
        denied = EnvironmentOperationPermissionState.DENIED
        unknown = EnvironmentOperationPermissionState.UNKNOWN
        permutations = (
            (allowed, denied),
            (denied, allowed),
            (allowed, unknown),
            (unknown, allowed),
            (denied, unknown),
            (unknown, denied),
        )
        expected = EnvironmentOperationPermissionValidationResult(
            valid=False,
            findings=(
                EnvironmentOperationPermissionFinding(
                    "conflicting_environment_operation_permission",
                    "Environment Operation Permission Observation identity "
                    "(runtime_option_id='runtime-primary', "
                    "environment_id='environment-primary', "
                    "operation_id='repository_file_read', "
                    "resource='synthetic/input.txt') has conflicting supplied "
                    "states.",
                ),
            ),
            normalized_observations=(),
        )
        for first, second in permutations:
            with self.subTest(first=first, second=second):
                result = validate_environment_operation_permission(
                    [observation(state=first), observation(state=second)],
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertEqual(result, expected)

    def test_conflict_with_repeated_state_is_one_conflict_not_duplicate(self) -> None:
        result = validate_environment_operation_permission(
            [
                observation(state=EnvironmentOperationPermissionState.ALLOWED),
                observation(state=EnvironmentOperationPermissionState.ALLOWED),
                observation(state=EnvironmentOperationPermissionState.DENIED),
            ],
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["conflicting_environment_operation_permission"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_finding_categories_and_values_are_deterministic(self) -> None:
        supplied = [
            observation(resource="synthetic/z-duplicate.txt"),
            observation(resource="synthetic/z-duplicate.txt"),
            observation(resource="synthetic/a-conflict.txt"),
            observation(
                resource="synthetic/a-conflict.txt",
                state=EnvironmentOperationPermissionState.DENIED,
            ),
            observation("z-missing", resource="synthetic/z-missing.txt"),
            observation("a-missing", resource="synthetic/a-missing.txt"),
            observation(
                environment_id="z-environment",
                resource="synthetic/z-environment.txt",
            ),
            observation(
                environment_id="a-environment",
                resource="synthetic/a-environment.txt",
            ),
            observation(
                operation_id="Z_bad",
                resource="synthetic/z-malformed.txt",
            ),
            observation(
                operation_id="A_bad",
                resource="synthetic/a-malformed.txt",
            ),
            observation(
                operation_id="z_unsupported",
                resource="synthetic/z-unsupported.txt",
            ),
            observation(
                operation_id="a_unsupported",
                resource="synthetic/a-unsupported.txt",
            ),
            observation(resource="git+z:synthetic/invalid.txt"),
            observation(resource="a/../invalid.txt"),
        ]
        forward = validate_environment_operation_permission(
            supplied,
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        reverse = validate_environment_operation_permission(
            list(reversed(supplied)),
            [runtime_option("runtime-primary")],
            "environment-primary",
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_environment_operation_permission",
                "conflicting_environment_operation_permission",
                "agent_runtime_option_not_found",
                "agent_runtime_option_not_found",
                "environment_operation_permission_environment_mismatch",
                "environment_operation_permission_environment_mismatch",
                "operation_id_invalid_syntax",
                "operation_id_invalid_syntax",
                "operation_id_not_supported",
                "operation_id_not_supported",
                "resource_uri_scheme",
                "resource_parent_segment",
            ],
        )
        self.assertIn("'a-missing'", forward.findings[2].message)
        self.assertIn("'z-missing'", forward.findings[3].message)
        self.assertIn("'a-environment'", forward.findings[4].message)
        self.assertIn("'z-environment'", forward.findings[5].message)
        self.assertIn(
            "'git+z:synthetic/invalid.txt'",
            forward.findings[-2].message,
        )
        self.assertIn("'a/../invalid.txt'", forward.findings[-1].message)
        self.assertEqual(forward.normalized_observations, ())

    def test_inputs_are_captured_once_in_locked_order_and_not_mutated(self) -> None:
        capture_order: list[str] = []
        options_list = [
            runtime_option("runtime-z"),
            runtime_option("runtime-a"),
        ]
        observations_list = [observation("runtime-z")]
        options = OneShotIterable(
            options_list,  # type: ignore[arg-type]
            "runtime_options",
            capture_order,
        )
        observations = OneShotIterable(
            observations_list,  # type: ignore[arg-type]
            "observations",
            capture_order,
        )
        result = validate_environment_operation_permission(
            observations,  # type: ignore[arg-type]
            options,  # type: ignore[arg-type]
            "environment-primary",
        )
        self.assertTrue(result.valid)
        self.assertEqual(capture_order, ["runtime_options", "observations"])
        self.assertEqual(options.iterations, 1)
        self.assertEqual(observations.iterations, 1)
        self.assertEqual(
            options_list,
            [runtime_option("runtime-z"), runtime_option("runtime-a")],
        )
        self.assertEqual(observations_list, [observation("runtime-z")])

    def test_every_invalid_result_is_atomic(self) -> None:
        cases = (
            [observation("runtime-missing")],
            [observation(environment_id="environment-other")],
            [observation(operation_id="repository_file_write")],
            [observation(resource="synthetic/../invalid.txt")],
            [observation(), observation()],
            [
                observation(),
                observation(state=EnvironmentOperationPermissionState.DENIED),
            ],
        )
        for supplied in cases:
            with self.subTest(supplied=supplied):
                result = validate_environment_operation_permission(
                    supplied,
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertFalse(result.valid)
                self.assertTrue(result.findings)
                self.assertEqual(result.normalized_observations, ())


class SharedRepositoryResourceTests(unittest.TestCase):
    def test_helper_value_is_exact_and_frozen(self) -> None:
        issue = RepositoryResourceValidationIssue("code", "suffix")
        self.assertEqual(
            [field.name for field in fields(issue)],
            ["code", "message_suffix"],
        )
        with self.assertRaises(FrozenInstanceError):
            issue.code = "changed"  # type: ignore[misc]

    def test_helper_owns_exact_canonical_codes_suffixes_and_precedence(
        self,
    ) -> None:
        cases = {
            "": ("resource_empty", "must not be empty."),
            "synthetic/\x00name": (
                "resource_control_character",
                "must not contain control characters.",
            ),
            "//server/../*.txt": (
                "resource_unc_path",
                "must not use a UNC path.",
            ),
            "/synthetic/../*.txt": (
                "resource_absolute_path",
                "must be repository-relative.",
            ),
            "C:/../*.txt": (
                "resource_drive_qualified_path",
                "must not be drive-qualified.",
            ),
            "https://example.invalid/../*.txt": (
                "resource_uri_scheme",
                "must not use a URI scheme.",
            ),
            "~/../*.txt": (
                "resource_leading_tilde",
                "must not start with a tilde.",
            ),
            "synthetic\\../*.txt": (
                "resource_backslash",
                "must use forward-slash separators.",
            ),
            "synthetic//../*.txt/": (
                "resource_trailing_slash",
                "must not end with a slash.",
            ),
            "synthetic//../*.txt": (
                "resource_empty_segment",
                "must not contain an empty segment.",
            ),
            "synthetic/./../*.txt": (
                "resource_dot_segment",
                "must not contain a dot segment.",
            ),
            "synthetic/../*.txt": (
                "resource_parent_segment",
                "must not contain a parent segment.",
            ),
            "synthetic/*.txt": (
                "resource_glob_meta",
                "must not contain glob meta characters.",
            ),
        }
        for resource, expected in cases.items():
            with self.subTest(resource=resource):
                issue = validate_repository_resource(resource)
                self.assertIsNotNone(issue)
                self.assertEqual((issue.code, issue.message_suffix), expected)
        self.assertIsNone(validate_repository_resource("synthetic/valid.txt"))

    def test_operation_requirement_and_permission_share_classification(self) -> None:
        resources = (
            "",
            "synthetic/\x00name",
            "//server/share/input.txt",
            "/synthetic/input.txt",
            "C:/synthetic/input.txt",
            "https://example.invalid/input.txt",
            "~/synthetic/input.txt",
            "synthetic\\input.txt",
            "synthetic/input/",
            "synthetic//input.txt",
            "synthetic/./input.txt",
            "synthetic/../input.txt",
            "synthetic/*.txt",
        )
        for resource in resources:
            with self.subTest(resource=resource):
                requirement_result = validate_operation_requirement(
                    OperationRequirement("repository_file_read", resource)
                )
                permission_result = validate_environment_operation_permission(
                    [observation(resource=resource)],
                    [runtime_option("runtime-primary")],
                    "environment-primary",
                )
                self.assertEqual(
                    requirement_result.findings[0].code,
                    permission_result.findings[0].code,
                )


class EnvironmentOperationPermissionScenarioTests(unittest.TestCase):
    def test_all_twelve_investigation_scenarios(self) -> None:
        options = [runtime_option("R1")]
        capability_present = RuntimeOperationCapabilityObservation(
            "R1",
            "repository_file_read",
            RuntimeOperationCapabilityState.PRESENT,
        )
        capability = validate_runtime_operation_capability(
            [capability_present],
            options,
        )
        self.assertTrue(capability.valid)

        for state in (
            EnvironmentOperationPermissionState.ALLOWED,
            EnvironmentOperationPermissionState.DENIED,
            EnvironmentOperationPermissionState.UNKNOWN,
        ):
            with self.subTest(scenario=f"capability-present-{state.value}"):
                result = validate_environment_operation_permission(
                    [observation("R1", state=state)],
                    options,
                    "environment-primary",
                )
                self.assertTrue(result.valid)
                self.assertIs(result.normalized_observations[0].state, state)
                self.assertIs(
                    capability.normalized_observations[0].state,
                    RuntimeOperationCapabilityState.PRESENT,
                )

        missing = validate_environment_operation_permission(
            [], options, "environment-primary"
        )
        self.assertTrue(missing.valid)
        self.assertEqual(missing.normalized_observations, ())

        unsupported = validate_environment_operation_permission(
            [observation("R1", operation_id="repository_file_write")],
            options,
            "environment-primary",
        )
        invalid_resource = validate_environment_operation_permission(
            [observation("R1", resource="synthetic/../invalid.txt")],
            options,
            "environment-primary",
        )
        wrong_environment = validate_environment_operation_permission(
            [observation("R1", environment_id="environment-missing")],
            options,
            "environment-primary",
        )
        environment_a_for_b = validate_environment_operation_permission(
            [observation("R1", environment_id="environment-a")],
            options,
            "environment-b",
        )
        duplicate = validate_environment_operation_permission(
            [observation("R1"), observation("R1")],
            options,
            "environment-primary",
        )
        conflict = validate_environment_operation_permission(
            [
                observation("R1"),
                observation(
                    "R1", state=EnvironmentOperationPermissionState.DENIED
                ),
            ],
            options,
            "environment-primary",
        )
        for result in (
            unsupported,
            invalid_resource,
            wrong_environment,
            environment_a_for_b,
            duplicate,
            conflict,
        ):
            self.assertFalse(result.valid)
            self.assertEqual(result.normalized_observations, ())

        allowed_without_authority = validate_environment_operation_permission(
            [observation("R1")],
            options,
            "environment-primary",
        )
        human_authorization = None
        self.assertTrue(allowed_without_authority.valid)
        self.assertIsNone(human_authorization)
        self.assertFalse(hasattr(allowed_without_authority, "authorized"))

        denied_with_authority = validate_environment_operation_permission(
            [
                observation(
                    "R1", state=EnvironmentOperationPermissionState.DENIED
                )
            ],
            options,
            "environment-primary",
        )
        human_authorization = True
        self.assertTrue(human_authorization)
        self.assertIs(
            denied_with_authority.normalized_observations[0].state,
            EnvironmentOperationPermissionState.DENIED,
        )

    def test_requirement_capability_permission_and_availability_are_independent(
        self,
    ) -> None:
        options = [runtime_option("runtime-primary")]
        requirement = validate_operation_requirement(
            OperationRequirement(
                "repository_file_read",
                "synthetic/input.txt",
            )
        )
        capability = validate_runtime_operation_capability(
            [
                RuntimeOperationCapabilityObservation(
                    "runtime-primary",
                    "repository_file_read",
                    RuntimeOperationCapabilityState.PRESENT,
                )
            ],
            options,
        )
        permission_denied = validate_environment_operation_permission(
            [
                observation(
                    state=EnvironmentOperationPermissionState.DENIED
                )
            ],
            options,
            "environment-primary",
        )
        availability = validate_agent_runtime_option_availability(
            [
                AgentRuntimeOptionAvailabilityObservation(
                    "runtime-primary",
                    AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
                )
            ],
            options,
        )
        permission_allowed = validate_environment_operation_permission(
            [observation()],
            options,
            "environment-primary",
        )
        self.assertTrue(requirement.valid)
        self.assertIs(
            capability.normalized_observations[0].state,
            RuntimeOperationCapabilityState.PRESENT,
        )
        self.assertIs(
            permission_denied.normalized_observations[0].state,
            EnvironmentOperationPermissionState.DENIED,
        )
        self.assertIs(
            availability.normalized_observations[0].state,
            AgentRuntimeOptionAvailabilityState.UNAVAILABLE,
        )
        self.assertIs(
            permission_allowed.normalized_observations[0].state,
            EnvironmentOperationPermissionState.ALLOWED,
        )


class EnvironmentOperationPermissionPurityTests(unittest.TestCase):
    def test_modules_import_only_pure_dependencies(self) -> None:
        permission_tree = ast.parse(
            PERMISSION_MODULE.read_text(encoding="utf-8")
        )
        resource_tree = ast.parse(RESOURCE_MODULE.read_text(encoding="utf-8"))

        def imports(tree: ast.AST) -> set[str]:
            names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    names.add(node.module)
            return names

        self.assertEqual(
            imports(permission_tree),
            {
                "__future__",
                "collections",
                "dataclasses",
                "enum",
                "typing",
                "engineering_orchestration._operation_vocabulary",
                "engineering_orchestration._repository_resource",
                "engineering_orchestration.agent_runtime_option",
            },
        )
        self.assertEqual(
            imports(resource_tree),
            {"__future__", "dataclasses", "re"},
        )

    def test_static_ast_contains_no_effectful_calls(self) -> None:
        forbidden_names = {"open", "exec", "eval", "compile", "__import__"}
        forbidden_attributes = {
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "open",
            "stat",
            "lstat",
            "exists",
            "is_file",
            "is_dir",
            "resolve",
            "absolute",
            "iterdir",
            "glob",
            "rglob",
            "listdir",
            "scandir",
            "walk",
            "access",
            "getenv",
            "run",
            "Popen",
            "urlopen",
            "create_connection",
            "getaddrinfo",
            "file_digest",
            "connect",
            "time",
            "monotonic",
        }
        for path in (PERMISSION_MODULE, RESOURCE_MODULE):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                calls = [
                    node.func for node in ast.walk(tree) if isinstance(node, ast.Call)
                ]
                self.assertFalse(
                    any(
                        isinstance(call, ast.Name) and call.id in forbidden_names
                        for call in calls
                    )
                )
                self.assertFalse(
                    any(
                        isinstance(call, ast.Attribute)
                        and call.attr in forbidden_attributes
                        for call in calls
                    )
                )

    def test_validation_performs_no_io_discovery_or_persistence(self) -> None:
        blocked = AssertionError("permission validation must remain pure")
        guards = (
            patch.object(builtins, "open", side_effect=blocked),
            patch.object(io, "open", side_effect=blocked),
            patch.object(Path, "open", side_effect=blocked),
            patch.object(Path, "read_text", side_effect=blocked),
            patch.object(Path, "read_bytes", side_effect=blocked),
            patch.object(Path, "write_text", side_effect=blocked),
            patch.object(Path, "write_bytes", side_effect=blocked),
            patch.object(Path, "stat", side_effect=blocked),
            patch.object(Path, "lstat", side_effect=blocked),
            patch.object(Path, "exists", side_effect=blocked),
            patch.object(Path, "is_file", side_effect=blocked),
            patch.object(Path, "is_dir", side_effect=blocked),
            patch.object(Path, "resolve", side_effect=blocked),
            patch.object(Path, "iterdir", side_effect=blocked),
            patch.object(Path, "glob", side_effect=blocked),
            patch.object(Path, "rglob", side_effect=blocked),
            patch.object(os, "stat", side_effect=blocked),
            patch.object(os, "lstat", side_effect=blocked),
            patch.object(os, "access", side_effect=blocked),
            patch.object(os, "listdir", side_effect=blocked),
            patch.object(os, "scandir", side_effect=blocked),
            patch.object(os, "walk", side_effect=blocked),
            patch.object(os, "getenv", side_effect=blocked),
            patch.object(glob, "glob", side_effect=blocked),
            patch.object(glob, "iglob", side_effect=blocked),
            patch.object(subprocess, "run", side_effect=blocked),
            patch.object(subprocess, "Popen", side_effect=blocked),
            patch.object(asyncio, "create_subprocess_exec", side_effect=blocked),
            patch.object(asyncio, "create_subprocess_shell", side_effect=blocked),
            patch.object(socket, "create_connection", side_effect=blocked),
            patch.object(socket, "getaddrinfo", side_effect=blocked),
            patch.object(socket.socket, "connect", side_effect=blocked),
            patch.object(urllib.request, "urlopen", side_effect=blocked),
            patch.object(
                http.client.HTTPConnection,
                "request",
                side_effect=blocked,
            ),
            patch.object(time, "time", side_effect=blocked),
            patch.object(time, "monotonic", side_effect=blocked),
            patch.object(sqlite3, "connect", side_effect=blocked),
            patch.object(hashlib, "file_digest", side_effect=blocked),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            valid = validate_environment_operation_permission(
                [observation()],
                [runtime_option("runtime-primary")],
                "environment-primary",
            )
            missing = validate_environment_operation_permission(
                [],
                [runtime_option("runtime-primary")],
                "environment-primary",
            )
            invalid = validate_environment_operation_permission(
                [observation(resource="synthetic/../invalid.txt")],
                [runtime_option("runtime-primary")],
                "environment-primary",
            )
            conflict = validate_environment_operation_permission(
                [
                    observation(),
                    observation(
                        state=EnvironmentOperationPermissionState.DENIED
                    ),
                ],
                [runtime_option("runtime-primary")],
                "environment-primary",
            )
        self.assertTrue(valid.valid)
        self.assertTrue(missing.valid)
        self.assertFalse(invalid.valid)
        self.assertFalse(conflict.valid)


class EnvironmentOperationPermissionBoundaryTests(unittest.TestCase):
    def test_package_root_has_no_permission_reexports(self) -> None:
        for name in (
            "EnvironmentOperationPermissionState",
            "EnvironmentOperationPermissionObservation",
            "EnvironmentOperationPermissionFinding",
            "EnvironmentOperationPermissionValidationResult",
            "validate_environment_operation_permission",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(engineering_orchestration, name))

    def test_no_environment_policy_authorization_or_execution_api_exists(
        self,
    ) -> None:
        forbidden = {
            "EnvironmentDefinition",
            "PermissionDecision",
            "discover_permissions",
            "poll_permissions",
            "check_permission",
            "mutate_permission",
            "authorize",
            "create_execution_contract",
            "dispatch",
            "invoke",
            "execute",
            "lookup_environment_operation_permission",
        }
        self.assertTrue(all(not hasattr(permission, name) for name in forbidden))

    def test_public_contract_contains_no_excluded_fields(self) -> None:
        public_fields = {
            field.name for field in fields(EnvironmentOperationPermissionObservation)
        } | {
            field.name
            for field in fields(EnvironmentOperationPermissionValidationResult)
        }
        forbidden = {
            "permission_id",
            "actor_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "option_id",
            "provider_id",
            "model_id",
            "tool_id",
            "timestamp",
            "freshness",
            "expires_at",
            "source",
            "provenance",
            "reason",
            "policy",
            "authorization",
            "metadata",
            "extensions",
            "execution_contract",
            "invocation",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_adjacent_structural_contracts_remain_unchanged(self) -> None:
        capability_schema = load_validator(
            "runtime-operation-capability.schema.json"
        ).schema
        availability_schema = load_validator(
            "agent-runtime-option-availability.schema.json"
        ).schema
        requirement_schema = load_validator(
            "operation-requirement.schema.json"
        ).schema
        self.assertEqual(
            set(capability_schema["properties"]),
            {"runtime_option_id", "operation_id", "state"},
        )
        self.assertEqual(
            set(availability_schema["properties"]),
            {"runtime_option_id", "state"},
        )
        self.assertEqual(
            set(requirement_schema["properties"]),
            {"operation_id", "resource"},
        )


if __name__ == "__main__":
    unittest.main()
