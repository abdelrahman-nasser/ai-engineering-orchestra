"""Focused Actor contract and pure competency-coverage tests."""

from dataclasses import FrozenInstanceError, fields
import unittest

from engineering_orchestration.actor_coverage import (
    ActorRoleCoverage,
    EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC,
    evaluate_actor_role_coverage,
)
from engineering_orchestration.schema_resources import load_validator, schema_errors


ENGINEERING_COMPETENCIES = [
    "software-implementation",
    "source-code-analysis",
    "automated-testing",
    "evidence-evaluation",
]


def actor(kind: str = "agent", competencies=None):
    return {
        "id": f"{kind}-engineer-1",
        "kind": kind,
        "competencies": list(
            ENGINEERING_COMPETENCIES if competencies is None else competencies
        ),
    }


def role(required=None):
    return {
        "id": "software-engineer",
        "required_capabilities": list(
            ENGINEERING_COMPETENCIES if required is None else required
        ),
    }


class TrackingMapping(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessed = []

    def __getitem__(self, key):
        self.accessed.append(key)
        return super().__getitem__(key)


class ActorSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator("actor.schema.json")
        cls.schema = cls.validator.schema

    def assert_valid(self, document):
        self.assertEqual(schema_errors(self.validator, document), [])

    def assert_invalid(self, document, keyword):
        errors = schema_errors(self.validator, document)
        self.assertTrue(errors)
        self.assertIn(keyword, {error.validator for error in errors})

    def test_schema_authorizes_exactly_three_fields(self):
        self.assertEqual(
            set(self.schema["properties"]), {"id", "kind", "competencies"}
        )
        self.assertEqual(
            set(self.schema["required"]), {"id", "kind", "competencies"}
        )
        self.assertFalse(self.schema["additionalProperties"])

    def test_valid_human_actor(self):
        self.assert_valid(actor("human"))

    def test_valid_agent_actor(self):
        self.assert_valid(actor("agent"))

    def test_missing_id_invalid(self):
        document = actor()
        document.pop("id")
        self.assert_invalid(document, "required")

    def test_empty_id_invalid(self):
        document = actor()
        document["id"] = ""
        self.assert_invalid(document, "minLength")

    def test_missing_kind_invalid(self):
        document = actor()
        document.pop("kind")
        self.assert_invalid(document, "required")

    def test_unsupported_kind_invalid(self):
        self.assert_invalid(actor("service"), "enum")

    def test_kind_values_are_exactly_human_and_agent(self):
        self.assertEqual(self.schema["properties"]["kind"]["enum"], ["human", "agent"])

    def test_missing_competencies_invalid(self):
        document = actor()
        document.pop("competencies")
        self.assert_invalid(document, "required")

    def test_empty_competencies_invalid(self):
        self.assert_invalid(actor(competencies=[]), "minItems")

    def test_duplicate_competencies_invalid(self):
        self.assert_invalid(
            actor(competencies=["evidence-evaluation", "evidence-evaluation"]),
            "uniqueItems",
        )

    def test_empty_competency_invalid(self):
        self.assert_invalid(actor(competencies=[""]), "minLength")

    def test_unknown_extra_field_invalid(self):
        document = actor()
        document["name"] = "Agent Engineer"
        self.assert_invalid(document, "additionalProperties")

    def test_human_requires_no_provider(self):
        document = actor("human")
        self.assertNotIn("provider", document)
        self.assert_valid(document)

    def test_agent_requires_no_provider(self):
        document = actor("agent")
        self.assertNotIn("provider", document)
        self.assert_valid(document)

    def test_actor_may_contain_extra_competencies(self):
        document = actor(competencies=ENGINEERING_COMPETENCIES + ["architecture-analysis"])
        self.assert_valid(document)

    def test_unknown_and_case_variant_competencies_are_structurally_valid(self):
        self.assert_valid(actor(competencies=["project-defined", "Software-Implementation"]))

    def test_provider_model_runtime_and_reasoning_are_absent(self):
        properties = set(self.schema["properties"])
        self.assertTrue(
            properties.isdisjoint({"provider", "model", "runtime", "reasoning"})
        )

    def test_authority_availability_and_roles_are_absent(self):
        properties = set(self.schema["properties"])
        self.assertTrue(
            properties.isdisjoint(
                {"authority", "permissions", "approval_authority", "availability", "roles"}
            )
        )


class ActorCoverageTests(unittest.TestCase):
    def test_exact_role_requirements_fully_covered(self):
        result = evaluate_actor_role_coverage(actor(), role())
        self.assertTrue(result.compatible)
        self.assertEqual(result.missing_competencies, ())
        self.assertIsNone(result.diagnostic)

    def test_one_missing_competency_is_incompatible(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["source-code-analysis"]),
            role(required=["source-code-analysis", "automated-testing"]),
        )
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing_competencies, ("automated-testing",))

    def test_multiple_missing_competencies_are_deterministic(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["source-code-analysis"]),
            role(required=["risk-analysis", "architecture-analysis", "automated-testing"]),
        )
        self.assertEqual(
            result.missing_competencies,
            ("architecture-analysis", "automated-testing", "risk-analysis"),
        )

    def test_extra_actor_competencies_do_not_hurt_compatibility(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["source-code-analysis", "unrelated-competency"]),
            role(required=["source-code-analysis"]),
        )
        self.assertTrue(result.compatible)

    def test_matching_is_case_sensitive(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["Software-Implementation"]),
            role(required=["software-implementation"]),
        )
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing_competencies, ("software-implementation",))

    def test_actor_kind_does_not_change_matching(self):
        human = evaluate_actor_role_coverage(actor("human"), role())
        agent = evaluate_actor_role_coverage(actor("agent"), role())
        self.assertEqual(human.compatible, agent.compatible)
        self.assertEqual(human.missing_competencies, agent.missing_competencies)

    def test_human_kind_grants_no_approval_result(self):
        result = evaluate_actor_role_coverage(actor("human"), role())
        self.assertFalse(hasattr(result, "approval"))
        self.assertFalse(hasattr(result, "approval_authority"))

    def test_agent_kind_grants_no_execution_result(self):
        result = evaluate_actor_role_coverage(actor("agent"), role())
        self.assertFalse(hasattr(result, "execution"))
        self.assertFalse(hasattr(result, "execution_authority"))

    def test_empty_role_requirements_are_not_universal_match(self):
        result = evaluate_actor_role_coverage(actor(), role(required=[]))
        self.assertFalse(result.compatible)
        self.assertEqual(result.missing_competencies, ())
        self.assertEqual(result.diagnostic, EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC)

    def test_duplicate_role_requirements_have_set_semantics(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["evidence-evaluation"]),
            role(required=["evidence-evaluation", "evidence-evaluation"]),
        )
        self.assertTrue(result.compatible)

    def test_unknown_actor_competency_does_not_cover_requirement(self):
        result = evaluate_actor_role_coverage(
            actor(competencies=["evidence-evaluaton"]),
            role(required=["evidence-evaluation"]),
        )
        self.assertEqual(result.missing_competencies, ("evidence-evaluation",))

    def test_evaluator_does_not_rank_actors(self):
        names = {item.name for item in fields(ActorRoleCoverage)}
        self.assertTrue(names.isdisjoint({"score", "rank", "recommendation"}))

    def test_evaluator_does_not_assign_actor(self):
        names = {item.name for item in fields(ActorRoleCoverage)}
        self.assertTrue(names.isdisjoint({"assignment", "assigned", "task_id"}))

    def test_evaluator_does_not_inspect_kind_or_availability(self):
        tracked_actor = TrackingMapping(actor())
        tracked_actor["availability"] = object()
        evaluate_actor_role_coverage(tracked_actor, role())
        self.assertEqual(tracked_actor.accessed, ["id", "competencies"])

    def test_evaluator_produces_no_quality_gate_result(self):
        names = {item.name for item in fields(ActorRoleCoverage)}
        self.assertTrue(names.isdisjoint({"quality_gate", "gate_result", "review_result"}))

    def test_result_fields_are_minimal_and_explicit(self):
        self.assertEqual(
            [item.name for item in fields(ActorRoleCoverage)],
            [
                "actor_id",
                "role_id",
                "compatible",
                "missing_competencies",
                "diagnostic",
            ],
        )

    def test_result_is_immutable(self):
        result = evaluate_actor_role_coverage(actor(), role())
        with self.assertRaises(FrozenInstanceError):
            result.compatible = False

    def test_evaluator_does_not_mutate_inputs(self):
        supplied_actor = actor()
        supplied_role = role()
        actor_before = {key: list(value) if isinstance(value, list) else value
                        for key, value in supplied_actor.items()}
        role_before = {key: list(value) if isinstance(value, list) else value
                       for key, value in supplied_role.items()}
        evaluate_actor_role_coverage(supplied_actor, supplied_role)
        self.assertEqual(supplied_actor, actor_before)
        self.assertEqual(supplied_role, role_before)


if __name__ == "__main__":
    unittest.main()
