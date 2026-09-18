from __future__ import annotations

import ast
from dataclasses import fields
from importlib.util import find_spec
import inspect
import json
import pkgutil
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

import engineering_orchestration
from engineering_orchestration import execution_mode
from engineering_orchestration.actor_availability import (
    ActorAvailabilityObservation,
    AvailabilityState,
    validate_actor_availability,
)
from engineering_orchestration.actor_coverage import evaluate_actor_role_coverage
from engineering_orchestration.assignment import Assignment
from engineering_orchestration.execution_mode import (
    EXECUTION_MODE_ORDER,
    execution_mode_satisfies,
)


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_schema(name: str) -> dict[str, object]:
    with (REPO_ROOT / "schemas" / name).open(encoding="utf-8") as file:
        return json.load(file)


class TestExecutionMode(unittest.TestCase):
    def test_canonical_order_is_exact_and_immutable(self) -> None:
        self.assertIsInstance(EXECUTION_MODE_ORDER, tuple)
        self.assertEqual(
            EXECUTION_MODE_ORDER,
            ("lite", "standard", "deep", "critical"),
        )

    def test_task_and_manifest_schema_enums_match_canonical_order(self) -> None:
        task_schema = load_schema("task.schema.json")
        manifest_schema = load_schema("project-manifest.schema.json")

        task_modes = task_schema["properties"]["execution"]["properties"]["mode"][
            "enum"
        ]
        manifest_modes = manifest_schema["properties"]["execution"]["properties"][
            "default_mode"
        ]["enum"]
        self.assertEqual(task_modes, list(EXECUTION_MODE_ORDER))
        self.assertEqual(manifest_modes, list(EXECUTION_MODE_ORDER))

    def test_complete_satisfaction_matrix(self) -> None:
        for actual_rank, actual in enumerate(EXECUTION_MODE_ORDER):
            for required_rank, required in enumerate(EXECUTION_MODE_ORDER):
                with self.subTest(actual=actual, required=required):
                    self.assertEqual(
                        execution_mode_satisfies(actual, required),
                        actual_rank >= required_rank,
                    )

    def test_each_mode_satisfies_itself(self) -> None:
        for mode in EXECUTION_MODE_ORDER:
            with self.subTest(mode=mode):
                self.assertTrue(execution_mode_satisfies(mode, mode))

    def test_higher_modes_satisfy_lower_minimums(self) -> None:
        for higher_rank in range(1, len(EXECUTION_MODE_ORDER)):
            for lower_rank in range(higher_rank):
                with self.subTest(higher=higher_rank, lower=lower_rank):
                    self.assertTrue(
                        execution_mode_satisfies(
                            EXECUTION_MODE_ORDER[higher_rank],
                            EXECUTION_MODE_ORDER[lower_rank],
                        )
                    )

    def test_lower_modes_do_not_satisfy_higher_minimums(self) -> None:
        for lower_rank in range(len(EXECUTION_MODE_ORDER) - 1):
            for higher_rank in range(lower_rank + 1, len(EXECUTION_MODE_ORDER)):
                with self.subTest(lower=lower_rank, higher=higher_rank):
                    self.assertFalse(
                        execution_mode_satisfies(
                            EXECUTION_MODE_ORDER[lower_rank],
                            EXECUTION_MODE_ORDER[higher_rank],
                        )
                    )

    def test_satisfaction_is_transitive(self) -> None:
        for highest_rank in range(len(EXECUTION_MODE_ORDER)):
            for middle_rank in range(highest_rank + 1):
                for lowest_rank in range(middle_rank + 1):
                    highest = EXECUTION_MODE_ORDER[highest_rank]
                    middle = EXECUTION_MODE_ORDER[middle_rank]
                    lowest = EXECUTION_MODE_ORDER[lowest_rank]
                    with self.subTest(
                        highest=highest, middle=middle, lowest=lowest
                    ):
                        self.assertTrue(execution_mode_satisfies(highest, middle))
                        self.assertTrue(execution_mode_satisfies(middle, lowest))
                        self.assertTrue(execution_mode_satisfies(highest, lowest))

    def test_invalid_actual_and_required_modes_are_rejected(self) -> None:
        for actual, required in (
            ("unsupported", "lite"),
            ("lite", "unsupported"),
            ("", "standard"),
            ("critical", ""),
        ):
            with self.subTest(actual=actual, required=required):
                with self.assertRaises(ValueError):
                    execution_mode_satisfies(actual, required)

    def test_helper_api_has_only_execution_posture_inputs(self) -> None:
        signature = inspect.signature(execution_mode_satisfies)
        self.assertEqual(tuple(signature.parameters), ("actual", "required"))
        self.assertEqual(
            {
                name
                for name, value in vars(execution_mode).items()
                if not name.startswith("_")
                and name != "annotations"
            },
            {"EXECUTION_MODE_ORDER", "execution_mode_satisfies"},
        )

        tree = ast.parse(inspect.getsource(execution_mode))
        identifiers = {
            node.id.casefold() for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        identifiers.update(
            node.arg.casefold() for node in ast.walk(tree) if isinstance(node, ast.arg)
        )
        self.assertTrue(
            {"provider", "model", "reasoning"}.isdisjoint(identifiers)
        )

    def test_stage_and_role_schemas_cannot_declare_execution_mode(self) -> None:
        workflow_schema = load_schema("workflow.schema.json")
        role_schema = load_schema("role.schema.json")
        stage_schema = workflow_schema["$defs"]["stage"]

        for schema in (stage_schema, role_schema):
            self.assertIs(schema["additionalProperties"], False)
            self.assertTrue(
                {"mode", "execution", "execution_mode"}.isdisjoint(
                    schema["properties"]
                )
            )

        workflow_with_override = {
            "id": "test-workflow",
            "name": "Test Workflow",
            "purpose": "Exercise the closed Stage contract.",
            "stages": [
                {
                    "id": "test-stage",
                    "purpose": "Exercise one Stage.",
                    "execution_mode": "deep",
                }
            ],
        }
        role_with_override = {
            "id": "test-role",
            "name": "Test Role",
            "purpose": "Exercise the closed Role contract.",
            "responsibilities": [],
            "required_capabilities": [],
            "execution_mode": "deep",
        }
        for schema, instance, path in (
            (workflow_schema, workflow_with_override, ("stages", 0)),
            (role_schema, role_with_override, ()),
        ):
            errors = list(Draft202012Validator(schema).iter_errors(instance))
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0].validator, "additionalProperties")
            self.assertEqual(tuple(errors[0].absolute_path), path)

    def test_execution_config_and_helper_have_no_authority_surface(self) -> None:
        task_schema = load_schema("task.schema.json")
        execution_schema = task_schema["properties"]["execution"]
        self.assertIs(execution_schema["additionalProperties"], False)
        self.assertEqual(set(execution_schema["properties"]), {"mode"})
        self.assertTrue(
            {
                "authority",
                "permission",
                "approval",
                "quality_gate",
                "workflow",
            }.isdisjoint(execution_schema["properties"])
        )

        result = execution_mode_satisfies("critical", "lite")
        self.assertIs(type(result), bool)
        self.assertFalse(hasattr(result, "__dict__"))
        self.assertEqual(
            inspect.signature(execution_mode_satisfies).return_annotation,
            "bool",
        )

    def test_competency_and_availability_surfaces_have_no_mode_input_or_effect(
        self,
    ) -> None:
        actor_schema = load_schema("actor.schema.json")
        availability_schema = load_schema("actor-availability.schema.json")
        self.assertIs(actor_schema["additionalProperties"], False)
        self.assertIs(availability_schema["additionalProperties"], False)
        self.assertEqual(
            set(actor_schema["properties"]), {"id", "kind", "competencies"}
        )
        self.assertEqual(
            set(availability_schema["properties"]), {"actor_id", "state"}
        )

        self.assertEqual(
            tuple(inspect.signature(evaluate_actor_role_coverage).parameters),
            ("actor", "role"),
        )
        self.assertEqual(
            tuple(inspect.signature(validate_actor_availability).parameters),
            ("observations", "actors"),
        )

        actor = {"id": "actor-1", "kind": "agent", "competencies": ["testing"]}
        role = {"id": "role-1", "required_capabilities": ["testing"]}
        observations = (
            ActorAvailabilityObservation("actor-1", AvailabilityState.AVAILABLE),
        )
        coverage_before = evaluate_actor_role_coverage(actor, role)
        availability_before = validate_actor_availability(observations, (actor,))
        self.assertTrue(execution_mode_satisfies("deep", "standard"))
        coverage_after = evaluate_actor_role_coverage(actor, role)
        availability_after = validate_actor_availability(observations, (actor,))

        self.assertEqual(coverage_before, coverage_after)
        self.assertEqual(availability_before, availability_after)
        self.assertTrue(coverage_after.compatible)
        self.assertTrue(availability_after.valid)
        for result in (coverage_after, availability_after):
            self.assertTrue(
                {"mode", "execution_mode"}.isdisjoint(
                    field.name for field in fields(result)
                )
            )

    def test_helper_does_not_import_create_or_return_assignment(self) -> None:
        tree = ast.parse(inspect.getsource(execution_mode))
        references = {
            node.id.casefold() for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        references.update(
            node.attr.casefold()
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        )
        references.update(
            node.module.casefold()
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        references.update(
            alias.name.casefold()
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        )
        self.assertFalse(any("assignment" in reference for reference in references))

        result = execution_mode_satisfies("standard", "lite")
        self.assertIs(type(result), bool)
        self.assertNotIsInstance(result, Assignment)

    def test_model_tier_has_no_schema_module_or_routing_surface(self) -> None:
        task_schema = load_schema("task.schema.json")
        manifest_schema = load_schema("project-manifest.schema.json")
        prohibited_fields = {"model", "model_tier", "tier", "routing"}
        for schema in (task_schema, manifest_schema):
            self.assertTrue(prohibited_fields.isdisjoint(schema["properties"]))
            self.assertTrue(
                prohibited_fields.isdisjoint(
                    schema["properties"]["execution"]["properties"]
                )
            )

        module_names = {
            module.name
            for module in pkgutil.iter_modules(engineering_orchestration.__path__)
        }
        self.assertFalse(
            any(
                "model" in name.casefold() or "routing" in name.casefold()
                for name in module_names
            )
        )
        self.assertIsNone(find_spec("engineering_orchestration.model_tier"))
        self.assertIsNone(find_spec("engineering_orchestration.model_routing"))
        self.assertTrue(
            {"model_tier", "routing"}.isdisjoint(vars(execution_mode))
        )


if __name__ == "__main__":
    unittest.main()
