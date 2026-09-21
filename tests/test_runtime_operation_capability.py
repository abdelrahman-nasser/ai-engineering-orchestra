"""Contract, semantic, boundary, and purity tests for Runtime capability."""

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
from engineering_orchestration._operation_vocabulary import (
    supported_core_operation_ids,
    validate_core_operation_id,
)
from engineering_orchestration.agent_execution_candidate_prerequisite import (
    AgentExecutionCandidatePrerequisiteResult,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.operation_requirement import (
    OperationRequirement,
    validate_operation_requirement,
)
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityFinding,
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
    RuntimeOperationCapabilityValidationResult,
    validate_runtime_operation_capability,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_MODULE = (
    ROOT / "engineering_orchestration" / "runtime_operation_capability.py"
)
VOCABULARY_MODULE = (
    ROOT / "engineering_orchestration" / "_operation_vocabulary.py"
)


def runtime_option(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def observation(
    runtime_option_id: object = "runtime-primary",
    operation_id: object = "repository_file_read",
    state: object = RuntimeOperationCapabilityState.PRESENT,
) -> RuntimeOperationCapabilityObservation:
    return RuntimeOperationCapabilityObservation(
        runtime_option_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        state,  # type: ignore[arg-type]
    )


class OneShotIterable:
    def __init__(self, values: list[object]) -> None:
        self.values = values
        self.iterations = 0

    def __iter__(self):
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("input iterable was consumed more than once")
        return iter(self.values)


class ExplodingObservation:
    @property
    def runtime_option_id(self):
        raise AssertionError("invalid inventory must not inspect observations")


class DerivedObservation(RuntimeOperationCapabilityObservation):
    """Subclass used to prove that exact observation type is required."""


class RuntimeOperationCapabilityValueTests(unittest.TestCase):
    def test_state_values_are_exactly_locked(self) -> None:
        self.assertEqual(
            tuple(state.value for state in RuntimeOperationCapabilityState),
            ("present", "absent", "unknown"),
        )
        self.assertIsNot(
            RuntimeOperationCapabilityState.ABSENT,
            RuntimeOperationCapabilityState.UNKNOWN,
        )

    def test_public_values_are_frozen_and_tuple_backed(self) -> None:
        value = observation()
        finding = RuntimeOperationCapabilityFinding("code", "message")
        result = RuntimeOperationCapabilityValidationResult(
            True,
            (),
            (value,),
        )
        self.assertEqual(
            [field.name for field in fields(value)],
            ["runtime_option_id", "operation_id", "state"],
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
            value.state = RuntimeOperationCapabilityState.ABSENT  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = False  # type: ignore[misc]

    def test_schema_is_exact_three_field_structural_contract(self) -> None:
        schema = load_validator("runtime-operation-capability.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(
            schema["required"],
            ["runtime_option_id", "operation_id", "state"],
        )
        self.assertEqual(
            set(schema["properties"]),
            {"runtime_option_id", "operation_id", "state"},
        )
        self.assertEqual(
            schema["properties"]["state"]["enum"],
            ["present", "absent", "unknown"],
        )
        self.assertNotIn("pattern", schema["properties"]["operation_id"])


class RuntimeOperationCapabilityValidationTests(unittest.TestCase):
    def assert_valid_state(
        self,
        state: RuntimeOperationCapabilityState,
    ) -> None:
        supplied = observation(state=state)
        result = validate_runtime_operation_capability(
            [supplied],
            [runtime_option("runtime-primary")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_observations, (supplied,))
        self.assertIs(result.normalized_observations[0], supplied)

    def test_present_absent_and_explicit_unknown_are_valid(self) -> None:
        for state in RuntimeOperationCapabilityState:
            with self.subTest(state=state):
                self.assert_valid_state(state)

    def test_missing_observation_normalizes_to_unknown(self) -> None:
        result = validate_runtime_operation_capability(
            [],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            result,
            RuntimeOperationCapabilityValidationResult(
                valid=True,
                findings=(),
                normalized_observations=(
                    observation(
                        state=RuntimeOperationCapabilityState.UNKNOWN,
                    ),
                ),
            ),
        )

    def test_missing_and_explicit_unknown_normalize_identically(self) -> None:
        options = [runtime_option("runtime-primary")]
        missing = validate_runtime_operation_capability([], options)
        explicit = validate_runtime_operation_capability(
            [observation(state=RuntimeOperationCapabilityState.UNKNOWN)],
            options,
        )
        self.assertEqual(missing, explicit)

    def test_cartesian_normalization_and_pair_sorting(self) -> None:
        supplied = observation(
            "runtime-z",
            state=RuntimeOperationCapabilityState.ABSENT,
        )
        result = validate_runtime_operation_capability(
            [supplied],
            [runtime_option("runtime-z"), runtime_option("runtime-a")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            [
                (item.runtime_option_id, item.operation_id, item.state)
                for item in result.normalized_observations
            ],
            [
                (
                    "runtime-a",
                    "repository_file_read",
                    RuntimeOperationCapabilityState.UNKNOWN,
                ),
                (
                    "runtime-z",
                    "repository_file_read",
                    RuntimeOperationCapabilityState.ABSENT,
                ),
            ],
        )

    def test_empty_inventory_and_observations_are_valid(self) -> None:
        result = validate_runtime_operation_capability([], [])
        self.assertEqual(
            result,
            RuntimeOperationCapabilityValidationResult(True, (), ()),
        )

    def test_invalid_runtime_inventory_short_circuits_observation_fields(
        self,
    ) -> None:
        result = validate_runtime_operation_capability(
            [ExplodingObservation()],  # type: ignore[list-item]
            [runtime_option("duplicate"), runtime_option("duplicate")],
        )
        self.assertFalse(result.valid)
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_agent_runtime_option_id"],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_exact_observation_type_and_valid_fields_are_required(self) -> None:
        derived = DerivedObservation(
            "runtime-primary",
            "repository_file_read",
            RuntimeOperationCapabilityState.PRESENT,
        )
        malformed = (
            observation(runtime_option_id=1),
            observation(operation_id=1),
            observation(state="present"),
        )
        result = validate_runtime_operation_capability(
            [derived, *malformed],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            [(finding.code, finding.message) for finding in result.findings],
            [
                (
                    "runtime_operation_capability_observation_invalid_type",
                    "Each supplied Runtime Operation Capability Observation "
                    "must be an exact RuntimeOperationCapabilityObservation "
                    "value.",
                ),
                (
                    "runtime_operation_capability_observation_invalid",
                    "A supplied Runtime Operation Capability Observation "
                    "contains malformed fields or state.",
                ),
            ],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_empty_runtime_id_is_invalid_but_empty_operation_uses_syntax(
        self,
    ) -> None:
        invalid_runtime = validate_runtime_operation_capability(
            [observation(runtime_option_id="")],
            [runtime_option("runtime-primary")],
        )
        invalid_operation = validate_runtime_operation_capability(
            [observation(operation_id="")],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            [finding.code for finding in invalid_runtime.findings],
            ["runtime_operation_capability_observation_invalid"],
        )
        self.assertEqual(
            [finding.code for finding in invalid_operation.findings],
            ["operation_id_invalid_syntax"],
        )

    def test_unknown_runtime_is_invalid_and_case_sensitive(self) -> None:
        result = validate_runtime_operation_capability(
            [observation("runtime-primary")],
            [runtime_option("Runtime-Primary")],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["agent_runtime_option_not_found"],
        )
        self.assertEqual(
            result.findings[0].message,
            "Agent Runtime Option 'runtime-primary' was not found in the "
            "supplied inventory.",
        )
        self.assertEqual(result.normalized_observations, ())

    def test_malformed_operation_is_not_support_checked(self) -> None:
        result = validate_runtime_operation_capability(
            [observation(operation_id="Repository_File_Read")],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["operation_id_invalid_syntax"],
        )
        self.assertEqual(
            result.findings[0].message,
            "Runtime Operation Capability Observation operation_id must use "
            "ASCII lower_snake_case syntax.",
        )

    def test_well_formed_unsupported_operation_is_invalid(self) -> None:
        result = validate_runtime_operation_capability(
            [observation(operation_id="repository_file_write")],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["operation_id_not_supported"],
        )
        self.assertEqual(
            result.findings[0].message,
            "Operation ID 'repository_file_write' is not supported by Core.",
        )

    def test_identical_duplicate_pair_is_invalid(self) -> None:
        supplied = observation()
        result = validate_runtime_operation_capability(
            [supplied, supplied],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_runtime_operation_capability"],
        )
        self.assertEqual(
            result.findings[0].message,
            "Agent Runtime Option 'runtime-primary' and Operation ID "
            "'repository_file_read' have more than one supplied Runtime "
            "Operation Capability Observation.",
        )
        self.assertEqual(result.normalized_observations, ())

    def test_conflicting_duplicate_pair_has_no_state_precedence(self) -> None:
        present = observation()
        absent = observation(state=RuntimeOperationCapabilityState.ABSENT)
        forward = validate_runtime_operation_capability(
            [present, absent],
            [runtime_option("runtime-primary")],
        )
        reverse = validate_runtime_operation_capability(
            [absent, present],
            [runtime_option("runtime-primary")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            ["duplicate_runtime_operation_capability"],
        )
        self.assertEqual(
            forward.findings[0].message,
            "Agent Runtime Option 'runtime-primary' and Operation ID "
            "'repository_file_read' have more than one supplied Runtime "
            "Operation Capability Observation.",
        )

    def test_distinct_duplicate_pairs_are_pair_sorted(self) -> None:
        supplied = [
            observation("runtime-z"),
            observation("runtime-a"),
            observation("runtime-z"),
            observation("runtime-a"),
        ]
        result = validate_runtime_operation_capability(
            supplied,
            [runtime_option("runtime-z"), runtime_option("runtime-a")],
        )
        self.assertEqual(
            [finding.message for finding in result.findings],
            [
                "Agent Runtime Option 'runtime-a' and Operation ID "
                "'repository_file_read' have more than one supplied Runtime "
                "Operation Capability Observation.",
                "Agent Runtime Option 'runtime-z' and Operation ID "
                "'repository_file_read' have more than one supplied Runtime "
                "Operation Capability Observation.",
            ],
        )
        self.assertEqual(result.normalized_observations, ())

    def test_finding_categories_and_ids_are_deterministic(self) -> None:
        supplied = [
            observation("known"),
            observation("known", state=RuntimeOperationCapabilityState.ABSENT),
            observation("z-missing"),
            observation("a-missing"),
            observation("known", "Z_bad"),
            observation("known", "A_bad"),
            observation("known", "z_unsupported"),
            observation("known", "a_unsupported"),
        ]
        forward = validate_runtime_operation_capability(
            supplied,
            [runtime_option("known")],
        )
        reverse = validate_runtime_operation_capability(
            list(reversed(supplied)),
            [runtime_option("known")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_runtime_operation_capability",
                "agent_runtime_option_not_found",
                "agent_runtime_option_not_found",
                "operation_id_invalid_syntax",
                "operation_id_invalid_syntax",
                "operation_id_not_supported",
                "operation_id_not_supported",
            ],
        )
        self.assertIn("'a-missing'", forward.findings[1].message)
        self.assertIn("'z-missing'", forward.findings[2].message)
        self.assertIn("'a_unsupported'", forward.findings[-2].message)
        self.assertIn("'z_unsupported'", forward.findings[-1].message)

    def test_inputs_are_captured_once_and_not_mutated(self) -> None:
        options_list = [runtime_option("runtime-z"), runtime_option("runtime-a")]
        observations_list = [observation("runtime-z")]
        options = OneShotIterable(options_list)
        observations = OneShotIterable(observations_list)
        result = validate_runtime_operation_capability(
            observations,  # type: ignore[arg-type]
            options,  # type: ignore[arg-type]
        )
        self.assertTrue(result.valid)
        self.assertEqual(options.iterations, 1)
        self.assertEqual(observations.iterations, 1)
        self.assertEqual(
            options_list,
            [runtime_option("runtime-z"), runtime_option("runtime-a")],
        )
        self.assertEqual(observations_list, [observation("runtime-z")])


class SharedOperationVocabularyTests(unittest.TestCase):
    def test_shared_vocabulary_is_closed_ordered_and_classifies_once(self) -> None:
        self.assertEqual(
            supported_core_operation_ids(),
            ("repository_file_read",),
        )
        self.assertIsNone(validate_core_operation_id("repository_file_read"))
        self.assertEqual(
            validate_core_operation_id("Repository_File_Read"),
            "operation_id_invalid_syntax",
        )
        self.assertEqual(
            validate_core_operation_id("repository_file_write"),
            "operation_id_not_supported",
        )

    def test_operation_requirement_preserves_shared_classification_and_messages(
        self,
    ) -> None:
        malformed = validate_operation_requirement(
            OperationRequirement("Repository_File_Read", "synthetic/input.txt")
        )
        unsupported = validate_operation_requirement(
            OperationRequirement("repository_file_write", "synthetic/input.txt")
        )
        self.assertEqual(
            [(item.code, item.message) for item in malformed.findings],
            [
                (
                    "operation_id_invalid_syntax",
                    "Operation Requirement operation_id must use ASCII "
                    "lower_snake_case syntax.",
                )
            ],
        )
        self.assertEqual(
            [(item.code, item.message) for item in unsupported.findings],
            [
                (
                    "operation_id_not_supported",
                    "Operation ID 'repository_file_write' is not supported by Core.",
                )
            ],
        )

    def test_operation_requirement_does_not_own_duplicate_vocabulary(self) -> None:
        source = (
            ROOT / "engineering_orchestration" / "operation_requirement.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("_OPERATION_ID_PATTERN", source)
        self.assertNotIn("_SUPPORTED_OPERATION_IDS", source)
        self.assertIn("validate_core_operation_id", source)


class RuntimeOperationCapabilityScenarioTests(unittest.TestCase):
    def test_all_twelve_investigation_scenarios(self) -> None:
        options = [runtime_option("R1")]

        for state in RuntimeOperationCapabilityState:
            with self.subTest(scenario=state.value):
                result = validate_runtime_operation_capability(
                    [observation("R1", state=state)],
                    options,
                )
                self.assertTrue(result.valid)
                self.assertIs(result.normalized_observations[0].state, state)

        missing = validate_runtime_operation_capability([], options)
        self.assertIs(
            missing.normalized_observations[0].state,
            RuntimeOperationCapabilityState.UNKNOWN,
        )

        unknown_runtime = validate_runtime_operation_capability(
            [observation("missing")], options
        )
        unsupported = validate_runtime_operation_capability(
            [observation("R1", "repository_file_write")], options
        )
        duplicate_identical = validate_runtime_operation_capability(
            [observation("R1"), observation("R1")], options
        )
        duplicate_conflicting = validate_runtime_operation_capability(
            [
                observation("R1"),
                observation("R1", state=RuntimeOperationCapabilityState.ABSENT),
            ],
            options,
        )
        for result in (
            unknown_runtime,
            unsupported,
            duplicate_identical,
            duplicate_conflicting,
        ):
            self.assertFalse(result.valid)
            self.assertEqual(result.normalized_observations, ())

        second_operation = validate_runtime_operation_capability(
            [
                observation("R1"),
                observation("R1", "repository_file_write"),
            ],
            options,
        )
        self.assertEqual(
            [finding.code for finding in second_operation.findings],
            ["operation_id_not_supported"],
        )

        multiple_runtimes = validate_runtime_operation_capability(
            [
                observation("R2", state=RuntimeOperationCapabilityState.ABSENT),
                observation("R1", state=RuntimeOperationCapabilityState.PRESENT),
            ],
            [runtime_option("R2"), runtime_option("R1")],
        )
        self.assertTrue(multiple_runtimes.valid)
        self.assertEqual(
            [
                (item.runtime_option_id, item.state)
                for item in multiple_runtimes.normalized_observations
            ],
            [
                ("R1", RuntimeOperationCapabilityState.PRESENT),
                ("R2", RuntimeOperationCapabilityState.ABSENT),
            ],
        )

        capability = validate_runtime_operation_capability(
            [observation("R1")], options
        )
        later_permission_fact = {
            "operation_id": "repository_file_read",
            "resource": "synthetic/denied.txt",
            "state": "denied",
        }
        self.assertIs(
            capability.normalized_observations[0].state,
            RuntimeOperationCapabilityState.PRESENT,
        )
        self.assertEqual(later_permission_fact["state"], "denied")
        self.assertFalse(hasattr(capability, "permission"))

        requirement = validate_operation_requirement(
            OperationRequirement(
                "repository_file_read",
                "synthetic/required.txt",
            )
        )
        capability_unknown = validate_runtime_operation_capability([], options)
        self.assertTrue(requirement.valid)
        self.assertIs(
            capability_unknown.normalized_observations[0].state,
            RuntimeOperationCapabilityState.UNKNOWN,
        )
        self.assertFalse(hasattr(capability_unknown, "requirement_satisfied"))


class RuntimeOperationCapabilityPurityTests(unittest.TestCase):
    def test_modules_import_only_pure_dependencies(self) -> None:
        capability_tree = ast.parse(CAPABILITY_MODULE.read_text(encoding="utf-8"))
        vocabulary_tree = ast.parse(VOCABULARY_MODULE.read_text(encoding="utf-8"))

        def imports(tree: ast.AST) -> set[str]:
            names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    names.add(node.module)
            return names

        self.assertEqual(
            imports(capability_tree),
            {
                "__future__",
                "collections",
                "dataclasses",
                "enum",
                "typing",
                "engineering_orchestration._operation_vocabulary",
                "engineering_orchestration.agent_runtime_option",
            },
        )
        self.assertEqual(imports(vocabulary_tree), {"__future__", "re"})

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
        for path in (CAPABILITY_MODULE, VOCABULARY_MODULE):
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
        blocked = AssertionError("capability validation must remain pure")
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
            patch.object(http.client.HTTPConnection, "request", side_effect=blocked),
            patch.object(time, "time", side_effect=blocked),
            patch.object(time, "monotonic", side_effect=blocked),
            patch.object(sqlite3, "connect", side_effect=blocked),
            patch.object(hashlib, "file_digest", side_effect=blocked),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            present = validate_runtime_operation_capability(
                [observation()],
                [runtime_option("runtime-primary")],
            )
            missing = validate_runtime_operation_capability(
                [],
                [runtime_option("runtime-primary")],
            )
            invalid = validate_runtime_operation_capability(
                [observation(operation_id="repository_file_write")],
                [runtime_option("runtime-primary")],
            )
        self.assertTrue(present.valid)
        self.assertTrue(missing.valid)
        self.assertFalse(invalid.valid)


class RuntimeOperationCapabilityBoundaryTests(unittest.TestCase):
    def test_public_contract_contains_no_excluded_fields(self) -> None:
        public_fields = {
            field.name for field in fields(RuntimeOperationCapabilityObservation)
        } | {
            field.name
            for field in fields(RuntimeOperationCapabilityValidationResult)
        }
        forbidden = {
            "capability_id",
            "resource",
            "tool_id",
            "provider_id",
            "model_id",
            "environment_id",
            "timestamp",
            "freshness",
            "source",
            "reason",
            "permission",
            "authorization",
            "metadata",
            "extensions",
            "execution_contract",
            "invocation",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_adjacent_contracts_remain_unchanged(self) -> None:
        runtime_schema = load_validator("agent-runtime-option.schema.json").schema
        availability_schema = load_validator(
            "agent-runtime-option-availability.schema.json"
        ).schema
        requirement_schema = load_validator("operation-requirement.schema.json").schema
        self.assertEqual(set(runtime_schema["properties"]), {"runtime_option_id"})
        self.assertEqual(
            set(availability_schema["properties"]),
            {"runtime_option_id", "state"},
        )
        self.assertEqual(
            set(requirement_schema["properties"]),
            {"operation_id", "resource"},
        )
        self.assertEqual(
            [
                field.name
                for field in fields(AgentExecutionCandidatePrerequisiteResult)
            ],
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

    def test_package_root_has_no_capability_reexports(self) -> None:
        for name in (
            "RuntimeOperationCapabilityState",
            "RuntimeOperationCapabilityObservation",
            "RuntimeOperationCapabilityFinding",
            "RuntimeOperationCapabilityValidationResult",
            "validate_runtime_operation_capability",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(engineering_orchestration, name))

    def test_no_discovery_adapter_permission_or_execution_api_exists(self) -> None:
        import engineering_orchestration.runtime_operation_capability as module

        forbidden = {
            "discover_capabilities",
            "poll_capabilities",
            "bind_tool",
            "check_permission",
            "authorize",
            "create_execution_contract",
            "dispatch",
            "invoke",
            "execute",
        }
        self.assertTrue(all(not hasattr(module, name) for name in forbidden))


if __name__ == "__main__":
    unittest.main()
