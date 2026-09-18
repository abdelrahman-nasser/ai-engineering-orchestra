"""Focused Assignment contract and responsibility-binding validation tests."""

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import unittest

from engineering_orchestration.actor_coverage import (
    EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC,
)
from engineering_orchestration.assignment import (
    Assignment,
    AssignmentFinding,
    AssignmentSetValidationResult,
    AssignmentValidationResult,
    validate_assignment,
    validate_assignment_set,
)
from engineering_orchestration.role_catalog import (
    RoleCatalog,
    RoleCatalogError,
    load_role_catalog,
)
from engineering_orchestration.schema_resources import load_validator, schema_errors
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowCatalogError,
    WorkflowDefinition,
    WorkflowStage,
    load_workflow_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
TASK = {"id": "AIO-023", "workflow": "architecture-change"}


def binding(**changes) -> Assignment:
    values = {
        "task_id": "AIO-023",
        "workflow_id": "architecture-change",
        "stage_id": "implement",
        "role_id": "software-engineer",
        "actor_id": "engineer-1",
    }
    values.update(changes)
    return Assignment(**values)


def actor(actor_id: str, competencies) -> dict[str, object]:
    return {
        "id": actor_id,
        "kind": "agent",
        "competencies": list(competencies),
    }


def workflow_catalog(*stages: WorkflowStage) -> WorkflowCatalog:
    definition = WorkflowDefinition(
        id="architecture-change",
        name="Architecture Change",
        purpose="Test Assignment semantics.",
        stages=list(stages),
    )
    return WorkflowCatalog(
        workflows_dir=Path("unused"),
        definitions={definition.id: definition},
    )


def role_catalog(*definitions: dict[str, object]) -> RoleCatalog:
    return RoleCatalog(
        roles_source=None,
        definitions={str(item["id"]): item for item in definitions},
    )


class TrackingActor(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.accessed: list[str] = []

    def __getitem__(self, key):
        self.accessed.append(key)
        return super().__getitem__(key)


class AssignmentFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflows = load_workflow_catalog(ROOT / "workflows")
        cls.roles = load_role_catalog()
        if not cls.workflows.is_valid:
            raise AssertionError(cls.workflows.load_errors)
        if not cls.roles.is_valid:
            raise AssertionError(cls.roles.load_errors)

    def actor_for(self, role_id: str, actor_id: str) -> dict[str, object]:
        role = self.roles.get(role_id)
        self.assertIsNotNone(role)
        return actor(actor_id, role["required_capabilities"])

    def validate(self, assignment=None, task=None, actors=None,
                 workflows=None, roles=None):
        return validate_assignment(
            assignment or binding(),
            TASK if task is None else task,
            self.workflows if workflows is None else workflows,
            self.roles if roles is None else roles,
            actors or [self.actor_for("software-engineer", "engineer-1")],
        )


class AssignmentSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_validator("assignment.schema.json")
        cls.schema = cls.validator.schema

    def test_schema_authorizes_exactly_five_required_fields(self):
        expected = {"task_id", "workflow_id", "stage_id", "role_id", "actor_id"}
        self.assertEqual(set(self.schema["properties"]), expected)
        self.assertEqual(set(self.schema["required"]), expected)
        self.assertFalse(self.schema["additionalProperties"])

    def test_valid_assignment(self):
        self.assertEqual(schema_errors(self.validator, binding().__dict__), [])

    def test_each_missing_field_is_invalid(self):
        document = binding().__dict__
        for name in tuple(document):
            with self.subTest(name=name):
                candidate = dict(document)
                candidate.pop(name)
                errors = schema_errors(self.validator, candidate)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].validator, "required")

    def test_each_empty_field_is_invalid(self):
        document = binding().__dict__
        for name in tuple(document):
            with self.subTest(name=name):
                candidate = dict(document)
                candidate[name] = ""
                errors = schema_errors(self.validator, candidate)
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0].validator, "minLength")

    def test_extra_field_is_rejected(self):
        document = dict(binding().__dict__, provider="example")
        errors = schema_errors(self.validator, document)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].validator, "additionalProperties")

    def test_provider_model_runtime_and_lifecycle_fields_are_absent(self):
        properties = set(self.schema["properties"])
        self.assertTrue(properties.isdisjoint({
            "assignment_id", "status", "provider", "model", "reasoning",
            "availability", "authority", "permissions", "execution", "result",
        }))


class IndividualAssignmentTests(AssignmentFixture):
    def test_assignment_value_is_immutable_and_key_excludes_actor(self):
        assignment = binding()
        self.assertEqual(
            assignment.key,
            ("AIO-023", "architecture-change", "implement", "software-engineer"),
        )
        with self.assertRaises(FrozenInstanceError):
            assignment.actor_id = "other"

    def test_valid_compatible_assignment(self):
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertTrue(result.coverage.compatible)

    def test_task_id_mismatch_short_circuits(self):
        result = self.validate(binding(task_id="OTHER"), task={"id": "AIO-023"})
        self.assertEqual([item.code for item in result.findings], ["task_id_mismatch"])

    def test_task_workflow_missing(self):
        result = self.validate(task={"id": "AIO-023"})
        self.assertEqual([item.code for item in result.findings], ["task_workflow_missing"])

    def test_workflow_id_mismatch(self):
        result = self.validate(binding(workflow_id="standard-change"))
        self.assertEqual([item.code for item in result.findings], ["workflow_id_mismatch"])

    def test_workflow_not_found(self):
        other = WorkflowDefinition("other", "Other", "Other", [
            WorkflowStage("stage", "Stage")
        ])
        catalog = WorkflowCatalog(Path("unused"), definitions={"other": other})
        result = self.validate(workflows=catalog)
        self.assertEqual([item.code for item in result.findings], ["workflow_not_found"])

    def test_corrupt_workflow_catalog_is_infrastructure_failure(self):
        catalog = WorkflowCatalog(Path("unused"), load_errors=["broken"])
        with self.assertRaises(WorkflowCatalogError):
            self.validate(workflows=catalog)

    def test_stage_not_found(self):
        result = self.validate(binding(stage_id="unknown"))
        self.assertEqual([item.code for item in result.findings], ["stage_not_found"])

    def test_role_not_found_precedes_role_requirement_check(self):
        result = self.validate(binding(role_id="unknown"))
        self.assertEqual([item.code for item in result.findings], ["role_not_found"])

    def test_corrupt_role_catalog_is_infrastructure_failure(self):
        catalog = RoleCatalog(None, load_errors=["broken"], infrastructure_errors=["broken"])
        with self.assertRaises(RoleCatalogError):
            self.validate(roles=catalog)

    def test_existing_role_not_required_by_stage(self):
        result = self.validate(binding(role_id="reviewer"))
        self.assertEqual([item.code for item in result.findings], ["role_not_required"])

    def test_actor_not_found(self):
        result = self.validate(binding(actor_id="missing"))
        self.assertEqual([item.code for item in result.findings], ["actor_not_found"])

    def test_duplicate_actor_ids_invalidate_context_before_task_checks(self):
        duplicate = self.actor_for("software-engineer", "same")
        result = self.validate(
            binding(task_id="OTHER"),
            actors=[duplicate, dict(duplicate)],
        )
        self.assertEqual([item.code for item in result.findings], ["duplicate_actor_id"])
        self.assertIsNone(result.coverage)

    def test_missing_competencies_are_preserved_deterministically(self):
        supplied = actor("engineer-1", ["source-code-analysis"])
        result = self.validate(actors=[supplied])
        self.assertFalse(result.valid)
        self.assertEqual([item.code for item in result.findings], [
            "actor_role_incompatible"
        ])
        self.assertEqual(result.coverage.missing_competencies, (
            "automated-testing", "evidence-evaluation", "software-implementation",
        ))

    def test_empty_role_requirement_diagnostic_is_propagated(self):
        workflows = workflow_catalog(WorkflowStage(
            "implement", "Implement", required_roles=["empty-role"]
        ))
        roles = role_catalog({"id": "empty-role", "required_capabilities": []})
        result = self.validate(
            binding(role_id="empty-role"),
            workflows=workflows,
            roles=roles,
            actors=[actor("engineer-1", ["anything"])],
        )
        self.assertEqual(result.coverage.diagnostic,
                         EMPTY_ROLE_REQUIREMENTS_DIAGNOSTIC)
        self.assertEqual(result.findings[0].code, "actor_role_incompatible")

    def test_validator_does_not_select_compatible_alternative(self):
        incapable = actor("engineer-1", ["source-code-analysis"])
        capable = self.actor_for("software-engineer", "alternative")
        result = self.validate(actors=[incapable, capable])
        self.assertFalse(result.valid)
        self.assertEqual(result.coverage.actor_id, "engineer-1")

    def test_availability_authority_and_kind_are_not_inspected_for_matching(self):
        supplied = TrackingActor(self.actor_for("software-engineer", "engineer-1"))
        supplied["availability"] = object()
        supplied["authority"] = object()
        result = self.validate(actors=[supplied])
        self.assertTrue(result.valid)
        self.assertNotIn("availability", supplied.accessed)
        self.assertNotIn("authority", supplied.accessed)
        self.assertNotIn("kind", supplied.accessed)

    def test_result_models_are_frozen_and_tuple_backed(self):
        result = self.validate()
        self.assertIsInstance(result.findings, tuple)
        self.assertEqual(
            [item.name for item in fields(AssignmentValidationResult)],
            ["valid", "findings", "coverage"],
        )
        with self.assertRaises(FrozenInstanceError):
            result.valid = False
        finding = AssignmentFinding("code", "message")
        with self.assertRaises(FrozenInstanceError):
            finding.code = "other"


class AssignmentSequenceTests(AssignmentFixture):
    def set_result(self, assignments, task=None, actors=None,
                   workflows=None, roles=None):
        return validate_assignment_set(
            assignments,
            TASK if task is None else task,
            self.workflows if workflows is None else workflows,
            self.roles if roles is None else roles,
            actors or [self.actor_for("software-engineer", "engineer-1")],
        )

    def test_one_valid_binding_is_valid_but_incomplete(self):
        result = self.set_result([binding()])
        self.assertTrue(result.valid)
        self.assertFalse(result.complete)
        self.assertEqual(len(result.unassigned_requirements), 3)

    def test_duplicate_same_actor_binding_is_invalid_and_covers_nothing(self):
        assignment = binding()
        result = self.set_result([assignment, assignment])
        self.assertFalse(result.valid)
        self.assertIn(assignment.key, result.unassigned_requirements)
        self.assertEqual([item.code for item in result.findings], [
            "duplicate_assignment_binding"
        ])

    def test_duplicate_different_actor_binding_is_invalid_and_covers_nothing(self):
        second = self.actor_for("software-engineer", "engineer-2")
        result = self.set_result(
            [binding(), binding(actor_id="engineer-2")],
            actors=[self.actor_for("software-engineer", "engineer-1"), second],
        )
        self.assertFalse(result.valid)
        self.assertIn(binding().key, result.unassigned_requirements)
        self.assertEqual(result.findings[0].code, "duplicate_assignment_binding")

    def test_complete_workflow_has_every_distinct_requirement_bound(self):
        architect = self.actor_for("architect", "architect-1")
        engineer = self.actor_for("software-engineer", "engineer-1")
        reviewer = self.actor_for("reviewer", "reviewer-1")
        assignments = [
            binding(stage_id="design", role_id="architect", actor_id="architect-1"),
            binding(),
            binding(stage_id="review", role_id="reviewer", actor_id="reviewer-1"),
            binding(stage_id="review", role_id="architect", actor_id="architect-1"),
        ]
        result = self.set_result(assignments, actors=[architect, engineer, reviewer])
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertEqual(result.unassigned_requirements, ())

    def test_unassigned_requirements_follow_stage_and_role_declaration_order(self):
        result = self.set_result([])
        self.assertEqual(result.unassigned_requirements, (
            ("AIO-023", "architecture-change", "design", "architect"),
            ("AIO-023", "architecture-change", "implement", "software-engineer"),
            ("AIO-023", "architecture-change", "review", "reviewer"),
            ("AIO-023", "architecture-change", "review", "architect"),
        ))

    def test_stages_without_roles_require_nothing_and_duplicates_collapse(self):
        workflows = workflow_catalog(
            WorkflowStage("understand", "Understand"),
            WorkflowStage("review", "Review", required_roles=["reviewer", "reviewer"]),
        )
        reviewer_role = self.roles.get("reviewer")
        roles = role_catalog(reviewer_role)
        reviewer = actor("reviewer-1", reviewer_role["required_capabilities"])
        result = self.set_result(
            [], workflows=workflows, roles=roles, actors=[reviewer]
        )
        self.assertEqual(result.unassigned_requirements, (
            ("AIO-023", "architecture-change", "review", "reviewer"),
        ))

    def test_invalid_foundational_context_makes_completeness_unknown(self):
        result = self.set_result([], task={"id": "AIO-023"})
        self.assertFalse(result.valid)
        self.assertIsNone(result.complete)
        self.assertEqual(result.findings[0].code, "task_workflow_missing")

    def test_unknown_task_workflow_makes_completeness_unknown(self):
        task = {"id": "AIO-023", "workflow": "missing"}
        result = self.set_result([], task=task)
        self.assertFalse(result.valid)
        self.assertIsNone(result.complete)
        self.assertEqual(result.findings[0].code, "workflow_not_found")

    def test_one_actor_may_hold_multiple_roles_without_separation_rule(self):
        workflows = workflow_catalog(
            WorkflowStage("design", "Design", required_roles=["architect"]),
            WorkflowStage("implement", "Implement", required_roles=["software-engineer"]),
        )
        architect_role = self.roles.get("architect")
        engineer_role = self.roles.get("software-engineer")
        roles = role_catalog(architect_role, engineer_role)
        combined = actor("multi-1", set(architect_role["required_capabilities"])
                         | set(engineer_role["required_capabilities"]))
        result = self.set_result([
            binding(stage_id="design", role_id="architect", actor_id="multi-1"),
            binding(actor_id="multi-1"),
        ], workflows=workflows, roles=roles, actors=[combined])
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertEqual(result.separation_findings, ())

    def test_same_implementer_and_reviewer_produces_only_separation_evidence(self):
        workflows = workflow_catalog(
            WorkflowStage("implement", "Implement", required_roles=["software-engineer"]),
            WorkflowStage("review", "Review", required_roles=["reviewer"]),
        )
        engineer_role = self.roles.get("software-engineer")
        reviewer_role = self.roles.get("reviewer")
        roles = role_catalog(engineer_role, reviewer_role)
        combined = actor("same-1", set(engineer_role["required_capabilities"])
                         | set(reviewer_role["required_capabilities"]))
        result = self.set_result([
            binding(actor_id="same-1"),
            binding(stage_id="review", role_id="reviewer", actor_id="same-1"),
        ], workflows=workflows, roles=roles, actors=[combined])
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertEqual([item.code for item in result.separation_findings], [
            "reviewer_actor_matches_implementer"
        ])
        self.assertFalse(hasattr(result, "quality_gate"))
        self.assertFalse(hasattr(result, "gate_result"))

    def test_different_implementer_and_reviewer_have_no_identity_conflict(self):
        workflows = workflow_catalog(
            WorkflowStage("implement", "Implement", required_roles=["software-engineer"]),
            WorkflowStage("review", "Review", required_roles=["reviewer"]),
        )
        roles = role_catalog(
            self.roles.get("software-engineer"), self.roles.get("reviewer")
        )
        actors = [
            self.actor_for("software-engineer", "engineer-1"),
            self.actor_for("reviewer", "reviewer-1"),
        ]
        result = self.set_result([
            binding(),
            binding(stage_id="review", role_id="reviewer", actor_id="reviewer-1"),
        ], workflows=workflows, roles=roles, actors=actors)
        self.assertTrue(result.valid)
        self.assertEqual(result.separation_findings, ())

    def test_invalid_or_duplicate_bindings_do_not_create_separation_evidence(self):
        shared = self.actor_for("software-engineer", "engineer-1")
        invalid_reviewer = binding(
            stage_id="review", role_id="reviewer", actor_id="engineer-1"
        )
        result = self.set_result([binding(), invalid_reviewer], actors=[shared])
        self.assertFalse(result.valid)
        self.assertEqual(result.separation_findings, ())
        duplicate = self.set_result([binding(), binding()], actors=[shared])
        self.assertEqual(duplicate.separation_findings, ())

    def test_security_reviewer_and_architect_identity_are_not_extra_rules(self):
        workflows = workflow_catalog(WorkflowStage(
            "review", "Review", required_roles=["reviewer", "architect",
                                                 "security-reviewer"]
        ))
        selected_roles = [self.roles.get(name) for name in
                          ("reviewer", "architect", "security-reviewer")]
        roles = role_catalog(*selected_roles)
        competencies = set().union(*(
            set(item["required_capabilities"]) for item in selected_roles
        ))
        shared = actor("shared", competencies)
        result = self.set_result([
            binding(stage_id="review", role_id="reviewer", actor_id="shared"),
            binding(stage_id="review", role_id="architect", actor_id="shared"),
            binding(stage_id="review", role_id="security-reviewer", actor_id="shared"),
        ], workflows=workflows, roles=roles, actors=[shared])
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertEqual(result.separation_findings, ())

    def test_empty_requirement_workflow_is_valid_and_complete(self):
        workflows = workflow_catalog(WorkflowStage("understand", "Understand"))
        result = self.set_result([], workflows=workflows)
        self.assertTrue(result.valid)
        self.assertTrue(result.complete)
        self.assertEqual(result.unassigned_requirements, ())

    def test_set_result_is_frozen_and_tuple_backed(self):
        result = self.set_result([])
        self.assertEqual(
            [item.name for item in fields(AssignmentSetValidationResult)],
            ["valid", "complete", "findings", "unassigned_requirements",
             "separation_findings"],
        )
        for value in (result.findings, result.unassigned_requirements,
                      result.separation_findings):
            self.assertIsInstance(value, tuple)
        with self.assertRaises(FrozenInstanceError):
            result.complete = True


if __name__ == "__main__":
    unittest.main()
