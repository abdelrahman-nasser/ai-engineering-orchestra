"""Focused Actor-to-Runtime Applicability Evidence tests."""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
from inspect import signature
import os
from pathlib import Path
import socket
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request

from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
    validate_agent_runtime_option_inventory,
)
import engineering_orchestration.actor_runtime_applicability as applicability
from engineering_orchestration.actor_runtime_applicability import (
    ActorRuntimeApplicabilityEvidence,
    ActorRuntimeApplicabilityFinding,
    ActorRuntimeApplicabilityValidationResult,
    validate_actor_runtime_applicability,
)
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]


def actor(actor_id: str, *, kind: str = "agent") -> dict[str, object]:
    return {"id": actor_id, "kind": kind, "competencies": ["implementation"]}


def runtime(runtime_option_id: str) -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def edge(
    actor_id: str,
    runtime_option_id: str,
) -> ActorRuntimeApplicabilityEvidence:
    return ActorRuntimeApplicabilityEvidence(actor_id, runtime_option_id)


class SinglePassIterable:
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


class ExplodingEvidence:
    @property
    def actor_id(self):
        raise AssertionError("invalid foundations must short-circuit relation fields")

    @property
    def runtime_option_id(self):
        raise AssertionError("invalid foundations must short-circuit relation fields")


class ActorRuntimeApplicabilityValueTests(unittest.TestCase):
    def test_evidence_has_exactly_two_fields_in_order_and_is_frozen(self) -> None:
        supplied = edge("actor", "runtime")
        self.assertEqual(
            [field.name for field in fields(supplied)],
            ["actor_id", "runtime_option_id"],
        )
        with self.assertRaises(FrozenInstanceError):
            supplied.actor_id = "changed"  # type: ignore[misc]

    def test_finding_and_result_are_frozen_and_tuple_backed(self) -> None:
        finding = ActorRuntimeApplicabilityFinding("example", "message")
        result = ActorRuntimeApplicabilityValidationResult(False, (finding,), ())
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_evidence, tuple)
        with self.assertRaises(FrozenInstanceError):
            finding.code = "changed"  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_public_function_signature_and_result_fields_are_minimal(self) -> None:
        self.assertEqual(
            list(signature(validate_actor_runtime_applicability).parameters),
            ["evidence", "actors", "runtime_options"],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(ActorRuntimeApplicabilityValidationResult)
            ],
            ["valid", "findings", "normalized_evidence"],
        )

    def test_schema_authorizes_exact_two_field_contract(self) -> None:
        schema = load_validator("actor-runtime-applicability.schema.json").schema
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["required"], ["actor_id", "runtime_option_id"])
        self.assertEqual(
            set(schema["properties"]), {"actor_id", "runtime_option_id"}
        )
        for definition in schema["properties"].values():
            self.assertEqual(definition["type"], "string")
            self.assertEqual(definition["minLength"], 1)
            self.assertNotIn("enum", definition)
            self.assertNotIn("pattern", definition)
            self.assertNotIn("format", definition)

    def test_schema_rejects_excluded_field_categories(self) -> None:
        validator = load_validator("actor-runtime-applicability.schema.json")
        base = {"actor_id": "actor", "runtime_option_id": "runtime"}
        excluded = {
            "applicability_id",
            "task_id",
            "workflow_id",
            "stage_id",
            "role_id",
            "option_id",
            "provider_id",
            "model_id",
            "state",
            "available",
            "compatible",
            "selected",
            "authorized",
            "priority",
            "weight",
            "confidence",
            "source",
            "reason",
            "timestamp",
            "expires_at",
            "tools",
            "permissions",
            "credentials",
            "metadata",
            "extensions",
        }
        for field_name in excluded:
            with self.subTest(field=field_name):
                self.assertTrue(
                    list(validator.iter_errors(base | {field_name: "value"}))
                )


class ActorRuntimeApplicabilityValidationTests(unittest.TestCase):
    def test_one_valid_edge(self) -> None:
        supplied = edge("actor", "runtime")
        self.assertEqual(
            validate_actor_runtime_applicability(
                [supplied], [actor("actor")], [runtime("runtime")]
            ),
            ActorRuntimeApplicabilityValidationResult(True, (), (supplied,)),
        )

    def test_one_actor_applies_to_multiple_runtimes(self) -> None:
        first = edge("actor", "runtime-a")
        second = edge("actor", "runtime-b")
        result = validate_actor_runtime_applicability(
            [second, first],
            [actor("actor")],
            [runtime("runtime-b"), runtime("runtime-a")],
        )
        self.assertEqual(result.normalized_evidence, (first, second))

    def test_one_runtime_supports_multiple_actors(self) -> None:
        first = edge("actor-a", "runtime")
        second = edge("actor-b", "runtime")
        result = validate_actor_runtime_applicability(
            [second, first],
            [actor("actor-b"), actor("actor-a")],
            [runtime("runtime")],
        )
        self.assertEqual(result.normalized_evidence, (first, second))

    def test_many_to_many_edges_are_valid(self) -> None:
        supplied = [
            edge("actor-b", "runtime-b"),
            edge("actor-a", "runtime-b"),
            edge("actor-b", "runtime-a"),
            edge("actor-a", "runtime-a"),
        ]
        result = validate_actor_runtime_applicability(
            supplied,
            [actor("actor-b"), actor("actor-a")],
            [runtime("runtime-b"), runtime("runtime-a")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_evidence,
            tuple(sorted(supplied, key=lambda item: (item.actor_id,
                                                     item.runtime_option_id))),
        )

    def test_empty_relation_is_valid_for_empty_mixed_and_nonempty_contexts(self) -> None:
        cases = (
            ([], []),
            ([actor("actor")], []),
            ([], [runtime("runtime")]),
            ([actor("actor")], [runtime("runtime")]),
        )
        for actors, runtime_options in cases:
            with self.subTest(actors=len(actors), runtimes=len(runtime_options)):
                self.assertEqual(
                    validate_actor_runtime_applicability(
                        [], actors, runtime_options
                    ),
                    ActorRuntimeApplicabilityValidationResult(True, (), ()),
                )

    def test_exact_case_sensitive_endpoint_matching_and_pair_sorting(self) -> None:
        supplied = [
            edge("Actor", "Runtime"),
            edge("Actor", "runtime"),
            edge("actor", "Runtime"),
            edge("actor", "runtime"),
        ]
        result = validate_actor_runtime_applicability(
            list(reversed(supplied)),
            [actor("actor"), actor("Actor")],
            [runtime("runtime"), runtime("Runtime")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_evidence,
            tuple(sorted(supplied, key=lambda item: (item.actor_id,
                                                     item.runtime_option_id))),
        )

    def test_case_only_mismatches_are_unknown_for_both_endpoints(self) -> None:
        result = validate_actor_runtime_applicability(
            [edge("actor", "runtime")],
            [actor("Actor")],
            [runtime("Runtime")],
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["actor_not_found", "agent_runtime_option_not_found"],
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_identifiers_remain_opaque_and_unmodified(self) -> None:
        supplied = edge(
            "Agent/Team:A@2026?member=1",
            "Runtime/Vendor:B@2026?surface=remote",
        )
        result = validate_actor_runtime_applicability(
            [supplied],
            [actor(supplied.actor_id)],
            [runtime(supplied.runtime_option_id)],
        )
        self.assertEqual(result.normalized_evidence, (supplied,))

    def test_duplicate_identical_edge_invalidates_complete_relation(self) -> None:
        supplied = edge("actor", "runtime")
        result = validate_actor_runtime_applicability(
            [supplied, supplied], [actor("actor")], [runtime("runtime")]
        )
        self.assertEqual(
            result,
            ActorRuntimeApplicabilityValidationResult(
                False,
                (
                    ActorRuntimeApplicabilityFinding(
                        "duplicate_actor_runtime_applicability",
                        "Actor 'actor' and Agent Runtime Option 'runtime' have "
                        "more than one supplied applicability evidence value.",
                    ),
                ),
                (),
            ),
        )

    def test_duplicate_actor_ids_preserve_established_diagnostic(self) -> None:
        result = validate_actor_runtime_applicability(
            [],
            [actor("z"), actor("a"), actor("z"), actor("a")],
            [runtime("runtime")],
        )
        self.assertEqual(
            result.findings,
            (
                ActorRuntimeApplicabilityFinding(
                    "duplicate_actor_id",
                    "Actor IDs must be unique in the supplied context; "
                    "duplicates: a, z",
                ),
            ),
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_duplicate_runtime_ids_reuse_inventory_validator(self) -> None:
        runtime_options = [runtime("duplicate"), runtime("duplicate")]
        expected = validate_agent_runtime_option_inventory(runtime_options).findings
        with patch.object(
            applicability,
            "validate_agent_runtime_option_inventory",
            wraps=validate_agent_runtime_option_inventory,
        ) as validator:
            result = validate_actor_runtime_applicability(
                [], [actor("actor")], runtime_options
            )
        validator.assert_called_once_with(tuple(runtime_options))
        self.assertEqual(
            result.findings,
            tuple(
                ActorRuntimeApplicabilityFinding(item.code, item.message)
                for item in expected
            ),
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_both_foundations_run_and_precede_relation_semantics(self) -> None:
        runtime_options = [runtime("duplicate"), runtime("duplicate")]
        result = validate_actor_runtime_applicability(
            [ExplodingEvidence()],  # type: ignore[list-item]
            [actor("duplicate"), actor("duplicate")],
            runtime_options,
        )
        self.assertEqual(
            [finding.code for finding in result.findings],
            ["duplicate_actor_id", "duplicate_agent_runtime_option_id"],
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_unknown_actor_reference_is_rejected(self) -> None:
        result = validate_actor_runtime_applicability(
            [edge("missing", "runtime")],
            [actor("known")],
            [runtime("runtime")],
        )
        self.assertEqual(
            result.findings,
            (
                ActorRuntimeApplicabilityFinding(
                    "actor_not_found",
                    "Actor 'missing' was not found in the supplied Actor context.",
                ),
            ),
        )

    def test_unknown_runtime_reference_is_rejected(self) -> None:
        result = validate_actor_runtime_applicability(
            [edge("actor", "missing")], [actor("actor")], [runtime("known")]
        )
        self.assertEqual(
            result.findings,
            (
                ActorRuntimeApplicabilityFinding(
                    "agent_runtime_option_not_found",
                    "Agent Runtime Option 'missing' was not found in the "
                    "supplied inventory.",
                ),
            ),
        )

    def test_human_actor_endpoint_is_rejected_without_invalidating_human(self) -> None:
        result = validate_actor_runtime_applicability(
            [edge("human", "runtime")],
            [actor("human", kind="human")],
            [runtime("runtime")],
        )
        self.assertEqual(
            result.findings,
            (
                ActorRuntimeApplicabilityFinding(
                    "actor_runtime_applicability_requires_agent_actor",
                    "Actor 'human' has kind 'human'; Actor-to-Runtime "
                    "Applicability Evidence requires an Agent Actor endpoint.",
                ),
            ),
        )
        self.assertEqual(result.normalized_evidence, ())

    def test_relation_findings_follow_locked_category_and_identifier_order(self) -> None:
        supplied = [
            edge("z-missing", "z-missing"),
            edge("z-human", "known"),
            edge("known", "known"),
            edge("a-missing", "a-missing"),
            edge("a-human", "known"),
            edge("z-missing", "z-missing"),
            edge("known", "known"),
        ]
        actors = [
            actor("known"),
            actor("z-human", kind="human"),
            actor("a-human", kind="human"),
        ]
        forward = validate_actor_runtime_applicability(
            supplied, actors, [runtime("known")]
        )
        reverse = validate_actor_runtime_applicability(
            list(reversed(supplied)), list(reversed(actors)), [runtime("known")]
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(
            [finding.code for finding in forward.findings],
            [
                "duplicate_actor_runtime_applicability",
                "duplicate_actor_runtime_applicability",
                "actor_not_found",
                "actor_not_found",
                "actor_runtime_applicability_requires_agent_actor",
                "actor_runtime_applicability_requires_agent_actor",
                "agent_runtime_option_not_found",
                "agent_runtime_option_not_found",
            ],
        )
        messages = [finding.message for finding in forward.findings]
        self.assertIn("'known'", messages[0])
        self.assertIn("'z-missing'", messages[1])
        self.assertIn("'a-missing'", messages[2])
        self.assertIn("'z-missing'", messages[3])
        self.assertIn("'a-human'", messages[4])
        self.assertIn("'z-human'", messages[5])
        self.assertIn("'a-missing'", messages[6])
        self.assertIn("'z-missing'", messages[7])
        self.assertEqual(forward.normalized_evidence, ())

    def test_valid_pair_order_is_declaration_independent(self) -> None:
        supplied = [
            edge("z", "A"),
            edge("A", "z"),
            edge("a", "A"),
            edge("A", "a"),
        ]
        expected = (
            edge("A", "a"),
            edge("A", "z"),
            edge("a", "A"),
            edge("z", "A"),
        )
        forward = validate_actor_runtime_applicability(
            supplied,
            [actor("a"), actor("z"), actor("A")],
            [runtime("z"), runtime("A"), runtime("a")],
        )
        reverse = validate_actor_runtime_applicability(
            list(reversed(supplied)),
            [actor("A"), actor("z"), actor("a")],
            [runtime("a"), runtime("z"), runtime("A")],
        )
        self.assertEqual(forward, reverse)
        self.assertEqual(forward.normalized_evidence, expected)

    def test_all_inputs_are_captured_once_in_locked_order(self) -> None:
        events: list[str] = []
        actors = SinglePassIterable("actors", [actor("actor")], events)
        runtimes = SinglePassIterable("runtimes", [runtime("runtime")], events)
        evidence = SinglePassIterable("evidence", [edge("actor", "runtime")], events)
        result = validate_actor_runtime_applicability(
            evidence,  # type: ignore[arg-type]
            actors,  # type: ignore[arg-type]
            runtimes,  # type: ignore[arg-type]
        )
        self.assertTrue(result.valid)
        self.assertEqual(events, ["actors", "runtimes", "evidence"])
        self.assertEqual(
            (actors.iterations, runtimes.iterations, evidence.iterations),
            (1, 1, 1),
        )

    def test_validation_does_not_mutate_inputs(self) -> None:
        supplied_evidence = [edge("b", "b"), edge("a", "a")]
        actors = [actor("b"), actor("a")]
        runtime_options = [runtime("b"), runtime("a")]
        before = (
            list(supplied_evidence),
            [dict(item) for item in actors],
            list(runtime_options),
        )
        validate_actor_runtime_applicability(
            supplied_evidence, actors, runtime_options
        )
        self.assertEqual(
            (supplied_evidence, actors, runtime_options),
            before,
        )

    def test_validation_performs_no_io_network_process_clock_or_environment_work(
        self,
    ) -> None:
        with (
            patch("builtins.open", side_effect=AssertionError("no file access")),
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
            patch.object(time, "time", side_effect=AssertionError("no clock")),
            patch.object(
                os,
                "getenv",
                side_effect=AssertionError("no environment access"),
            ),
        ):
            result = validate_actor_runtime_applicability(
                [edge("actor", "runtime")],
                [actor("actor")],
                [runtime("runtime")],
            )
        self.assertTrue(result.valid)


class ActorRuntimeApplicabilityBoundaryTests(unittest.TestCase):
    def test_endpoint_and_assignment_schema_contracts_remain_unchanged(self) -> None:
        actor_schema = load_validator("actor.schema.json").schema
        runtime_schema = load_validator("agent-runtime-option.schema.json").schema
        assignment_schema = load_validator("assignment.schema.json").schema
        self.assertEqual(
            set(actor_schema["properties"]), {"id", "kind", "competencies"}
        )
        self.assertEqual(set(runtime_schema["properties"]), {"runtime_option_id"})
        self.assertNotIn("runtime_option_id", assignment_schema["properties"])
        self.assertNotIn("runtime_option_ids", actor_schema["properties"])
        self.assertNotIn("actor_ids", runtime_schema["properties"])

    def test_public_values_contain_no_adjacent_domain_state(self) -> None:
        public_fields = {
            field.name for field in fields(ActorRuntimeApplicabilityEvidence)
        } | {
            field.name
            for field in fields(ActorRuntimeApplicabilityValidationResult)
        }
        forbidden = {
            "available",
            "state",
            "compatible",
            "selected",
            "authorized",
            "reserved",
            "dispatched",
            "executing",
            "task_id",
            "role_id",
            "option_id",
            "execution_mode",
            "execution_configuration",
            "execution_contract",
            "priority",
            "weight",
            "tools",
            "permissions",
        }
        self.assertTrue(forbidden.isdisjoint(public_fields))

    def test_module_imports_only_runtime_endpoint_contract(self) -> None:
        tree = ast.parse(
            (ROOT / "engineering_orchestration" /
             "actor_runtime_applicability.py").read_text(encoding="utf-8")
        )
        internal_imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("engineering_orchestration")
        }
        self.assertEqual(
            internal_imports,
            {"engineering_orchestration.agent_runtime_option"},
        )

    def test_missing_edge_is_not_collapsed_into_applicability_boolean(self) -> None:
        result = validate_actor_runtime_applicability(
            [], [actor("actor")], [runtime("runtime-owned-inference")]
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())
        self.assertFalse(hasattr(result, "applicable"))
        self.assertFalse(hasattr(applicability, "is_applicable"))

    def test_no_selection_authorization_adapter_or_invocation_api_exists(self) -> None:
        forbidden = {
            "ExecutionConfigurationCandidate",
            "ExecutionContract",
            "ActorInferenceApplicabilityEvidence",
            "select_runtime",
            "rank_runtimes",
            "route",
            "authorize",
            "dispatch",
            "invoke",
        }
        self.assertTrue(all(not hasattr(applicability, name) for name in forbidden))

    def test_no_project_applicability_storage_was_created(self) -> None:
        for relative in (
            ".ai/actor-runtime",
            ".ai/runtime-applicability",
            ".ai/actor-runtime-applicability",
            ".ai/execution-configurations",
        ):
            self.assertFalse((ROOT / relative).exists())


if __name__ == "__main__":
    unittest.main()
