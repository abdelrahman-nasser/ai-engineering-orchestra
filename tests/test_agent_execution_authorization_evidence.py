"""Focused Agent Execution Authorization Evidence contract tests."""

from __future__ import annotations

import ast
import builtins
import copy
from dataclasses import FrozenInstanceError, fields
from inspect import signature
from pathlib import Path
import unittest
from unittest.mock import patch

import engineering_orchestration
import engineering_orchestration.agent_execution_authorization_evidence as subject
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationFinding,
    AgentExecutionAuthorizationState,
    AgentExecutionAuthorizationValidationResult,
    validate_agent_execution_authorization_evidence,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.assignment import Assignment
from engineering_orchestration.environment_operation_permission import (
    EnvironmentOperationPermissionObservation,
    EnvironmentOperationPermissionState,
)
from engineering_orchestration.inference_option import (
    InferenceOptionDefinition,
)
from engineering_orchestration.operation_requirement import OperationRequirement
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.runtime_operation_capability import (
    RuntimeOperationCapabilityObservation,
    RuntimeOperationCapabilityState,
)
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowDefinition,
    WorkflowStage,
)


ROOT = Path(__file__).resolve().parents[1]
TASK = {"id": "AIO-039", "workflow": "architecture-change"}
SUBJECT_FIELDS = (
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
)


def workflow_catalog() -> WorkflowCatalog:
    definition = WorkflowDefinition(
        id="architecture-change",
        name="Architecture Change",
        purpose="Synthetic authorization-evidence validation.",
        stages=[
            WorkflowStage(
                id="implement",
                purpose="Implement a synthetic change.",
                required_roles=["software-engineer"],
            )
        ],
    )
    return WorkflowCatalog(
        workflows_dir=Path("unused"),
        definitions={definition.id: definition},
    )


def role_catalog() -> RoleCatalog:
    role = {
        "id": "software-engineer",
        "required_capabilities": ["implementation"],
    }
    return RoleCatalog(
        roles_source=None,
        definitions={"software-engineer": role},
    )


def actor(
    actor_id: str = "agent::assigned",
    *,
    kind: str = "agent",
) -> dict[str, object]:
    return {
        "id": actor_id,
        "kind": kind,
        "competencies": ["implementation"],
    }


def assignment(**changes: str) -> Assignment:
    values = {
        "task_id": "AIO-039",
        "workflow_id": "architecture-change",
        "stage_id": "implement",
        "role_id": "software-engineer",
        "actor_id": "agent::assigned",
    }
    values.update(changes)
    return Assignment(**values)


def runtime(runtime_option_id: str = "runtime::one") -> AgentRuntimeOptionDefinition:
    return AgentRuntimeOptionDefinition(runtime_option_id)


def option(option_id: str = "option::one") -> InferenceOptionDefinition:
    return InferenceOptionDefinition(
        option_id,
        "provider::synthetic",
        "model::synthetic",
    )


def authorization(**changes: object) -> AgentExecutionAuthorizationEvidence:
    values: dict[str, object] = {
        "task_id": "AIO-039",
        "workflow_id": "architecture-change",
        "stage_id": "implement",
        "role_id": "software-engineer",
        "actor_id": "agent::assigned",
        "runtime_option_id": "runtime::one",
        "option_id": "option::one",
        "environment_id": "environment::synthetic",
        "operation_id": "repository_file_read",
        "resource": "synthetic/input.txt",
        "authority_kind": AgentExecutionAuthorizationAuthorityKind.HUMAN,
        "authority_id": "human::reviewer",
        "provenance_reference": "approval::synthetic",
        "state": AgentExecutionAuthorizationState.GRANTED,
    }
    values.update(changes)
    return AgentExecutionAuthorizationEvidence(**values)  # type: ignore[arg-type]


class OneShotIterable:
    """Iterable that records capture order and rejects a second enumeration."""

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


class AuthorizationFixture(unittest.TestCase):
    def base(self) -> dict[str, object]:
        return {
            "evidence": [authorization()],
            "assignments": [assignment()],
            "task": dict(TASK),
            "workflow_catalog": workflow_catalog(),
            "role_catalog": role_catalog(),
            "actors": [actor()],
            "runtime_options": [runtime()],
            "inference_options": [option()],
            "environment_id": "environment::synthetic",
        }

    def validate(
        self,
        **changes: object,
    ) -> AgentExecutionAuthorizationValidationResult:
        supplied = self.base()
        supplied.update(changes)
        return validate_agent_execution_authorization_evidence(
            **supplied  # type: ignore[arg-type]
        )

    def assert_atomic_invalid(
        self,
        result: AgentExecutionAuthorizationValidationResult,
        codes: list[str],
    ) -> None:
        self.assertFalse(result.valid)
        self.assertEqual([item.code for item in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertEqual(result.normalized_evidence, ())


class AuthorizationValueTests(AuthorizationFixture):
    def test_closed_vocabularies_are_exact(self) -> None:
        self.assertEqual(
            [item.value for item in AgentExecutionAuthorizationAuthorityKind],
            ["human", "policy"],
        )
        self.assertEqual(
            [item.value for item in AgentExecutionAuthorizationState],
            ["granted", "denied"],
        )

    def test_evidence_has_exactly_fourteen_frozen_fields_in_locked_order(
        self,
    ) -> None:
        value = authorization()
        self.assertEqual(
            [item.name for item in fields(value)],
            [
                *SUBJECT_FIELDS,
                "authority_kind",
                "authority_id",
                "provenance_reference",
                "state",
            ],
        )
        with self.assertRaises(FrozenInstanceError):
            value.state = AgentExecutionAuthorizationState.DENIED  # type: ignore[misc]

    def test_finding_and_result_are_exact_frozen_tuple_backed_values(self) -> None:
        finding = AgentExecutionAuthorizationFinding("example", "message")
        result = AgentExecutionAuthorizationValidationResult(
            False,
            (finding,),
            (),
        )
        self.assertEqual(
            [item.name for item in fields(finding)],
            ["code", "message"],
        )
        self.assertEqual(
            [item.name for item in fields(result)],
            ["valid", "findings", "normalized_evidence"],
        )
        self.assertIsInstance(result.findings, tuple)
        self.assertIsInstance(result.normalized_evidence, tuple)
        with self.assertRaises(FrozenInstanceError):
            result.valid = True  # type: ignore[misc]

    def test_public_signature_is_exactly_the_locked_raw_input_api(self) -> None:
        parameters = signature(
            validate_agent_execution_authorization_evidence
        ).parameters
        self.assertEqual(
            list(parameters),
            [
                "evidence",
                "assignments",
                "task",
                "workflow_catalog",
                "role_catalog",
                "actors",
                "runtime_options",
                "inference_options",
                "environment_id",
            ],
        )
        self.assertTrue(
            all(item.default is item.empty for item in parameters.values())
        )

    def test_module_is_not_reexported_from_package_root(self) -> None:
        public_names = (
            "AgentExecutionAuthorizationEvidence",
            "AgentExecutionAuthorizationAuthorityKind",
            "AgentExecutionAuthorizationState",
            "validate_agent_execution_authorization_evidence",
        )
        self.assertTrue(
            all(not hasattr(engineering_orchestration, name) for name in public_names)
        )

    def test_no_grant_lifecycle_or_execution_identity_fields_exist(self) -> None:
        field_names = {item.name for item in fields(authorization())}
        self.assertTrue(
            field_names.isdisjoint(
                {
                    "authorization_id",
                    "execution_id",
                    "run_id",
                    "issued_at",
                    "expires_at",
                    "revoked_at",
                    "consumed_at",
                }
            )
        )
        with self.assertRaises(TypeError):
            authorization(expires_at="2099-01-01T00:00:00Z")


class AuthorizationValidationTests(AuthorizationFixture):
    def test_single_grant_is_valid_and_preserves_exact_supplied_value(self) -> None:
        value = authorization()
        result = self.validate(evidence=[value])
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assertEqual(result.normalized_evidence, (value,))
        self.assertIs(result.normalized_evidence[0], value)

    def test_single_denial_is_valid_and_distinct_from_absence(self) -> None:
        denial = authorization(state=AgentExecutionAuthorizationState.DENIED)
        denied = self.validate(evidence=[denial])
        missing = self.validate(evidence=[])
        self.assertTrue(denied.valid)
        self.assertEqual(denied.normalized_evidence, (denial,))
        self.assertTrue(missing.valid)
        self.assertEqual(missing.normalized_evidence, ())

    def test_valid_supplied_values_sort_by_exact_ten_part_subject(self) -> None:
        later = authorization(resource="synthetic/z.txt")
        earlier = authorization(resource="synthetic/a.txt")
        result = self.validate(evidence=[later, earlier])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, (earlier, later))

    def test_duplicate_identical_values_invalidate_atomically(self) -> None:
        value = authorization()
        self.assert_atomic_invalid(
            self.validate(evidence=[value, value]),
            ["duplicate_agent_execution_authorization_evidence"],
        )

    def test_same_subject_differing_states_are_a_conflict(self) -> None:
        grant = authorization()
        denial = authorization(state=AgentExecutionAuthorizationState.DENIED)
        self.assert_atomic_invalid(
            self.validate(evidence=[grant, denial]),
            ["conflicting_agent_execution_authorization_evidence"],
        )

    def test_same_subject_and_state_differing_authority_is_unsupported(self) -> None:
        human = authorization()
        policy = authorization(
            authority_kind=AgentExecutionAuthorizationAuthorityKind.POLICY,
            authority_id="policy::one",
            provenance_reference="policy-evaluation::one",
        )
        self.assert_atomic_invalid(
            self.validate(evidence=[human, policy]),
            [
                "unsupported_multi_authority_"
                "agent_execution_authorization_evidence"
            ],
        )

    def test_state_conflict_precedes_multi_authority_for_one_subject(self) -> None:
        values = [
            authorization(),
            authorization(
                authority_kind=AgentExecutionAuthorizationAuthorityKind.POLICY,
                authority_id="policy::one",
                provenance_reference="policy-evaluation::one",
            ),
            authorization(
                authority_kind=AgentExecutionAuthorizationAuthorityKind.POLICY,
                authority_id="policy::one",
                provenance_reference="policy-evaluation::one",
                state=AgentExecutionAuthorizationState.DENIED,
            ),
        ]
        self.assert_atomic_invalid(
            self.validate(evidence=values),
            ["conflicting_agent_execution_authorization_evidence"],
        )

    def test_repeated_subject_output_category_order_is_locked(self) -> None:
        duplicate = authorization(resource="synthetic/c.txt")
        conflict_grant = authorization(resource="synthetic/a.txt")
        conflict_denial = authorization(
            resource="synthetic/a.txt",
            state=AgentExecutionAuthorizationState.DENIED,
        )
        multi_human = authorization(resource="synthetic/b.txt")
        multi_policy = authorization(
            resource="synthetic/b.txt",
            authority_kind=AgentExecutionAuthorizationAuthorityKind.POLICY,
            authority_id="policy::one",
            provenance_reference="policy-evaluation::one",
        )
        supplied = [
            multi_policy,
            duplicate,
            conflict_denial,
            multi_human,
            conflict_grant,
            duplicate,
        ]
        expected_codes = [
            "duplicate_agent_execution_authorization_evidence",
            "conflicting_agent_execution_authorization_evidence",
            "unsupported_multi_authority_agent_execution_authorization_evidence",
        ]
        forward = self.validate(evidence=supplied)
        reverse = self.validate(evidence=list(reversed(supplied)))
        self.assert_atomic_invalid(forward, expected_codes)
        self.assertEqual(reverse, forward)

    def test_unknown_exact_assignment_reference_is_rejected(self) -> None:
        self.assert_atomic_invalid(
            self.validate(evidence=[authorization(actor_id="agent::other")]),
            ["agent_execution_authorization_assignment_not_found"],
        )

    def test_matched_human_assignment_is_outside_contract(self) -> None:
        human_actor = actor("human::assigned", kind="human")
        human_assignment = assignment(actor_id="human::assigned")
        human_evidence = authorization(actor_id="human::assigned")
        self.assert_atomic_invalid(
            self.validate(
                evidence=[human_evidence],
                assignments=[human_assignment],
                actors=[human_actor],
            ),
            ["agent_execution_authorization_not_applicable_to_human_actor"],
        )

    def test_unknown_runtime_and_inference_references_are_rejected(self) -> None:
        result = self.validate(
            evidence=[
                authorization(
                    runtime_option_id="runtime::missing",
                    option_id="option::missing",
                )
            ]
        )
        self.assert_atomic_invalid(
            result,
            ["agent_runtime_option_not_found", "inference_option_not_found"],
        )

    def test_environment_mismatch_is_rejected(self) -> None:
        self.assert_atomic_invalid(
            self.validate(
                evidence=[authorization(environment_id="environment::other")]
            ),
            ["agent_execution_authorization_environment_mismatch"],
        )

    def test_operation_syntax_and_support_use_canonical_findings(self) -> None:
        result = self.validate(
            evidence=[
                authorization(
                    operation_id="RepositoryRead",
                    resource="synthetic/a.txt",
                ),
                authorization(
                    operation_id="repository_file_write",
                    resource="synthetic/b.txt",
                ),
            ]
        )
        self.assert_atomic_invalid(
            result,
            ["operation_id_invalid_syntax", "operation_id_not_supported"],
        )

    def test_resource_validation_is_lexical_and_canonical(self) -> None:
        result = self.validate(evidence=[authorization(resource="../outside.txt")])
        self.assertFalse(result.valid)
        self.assertEqual(len(result.findings), 1)
        self.assertTrue(result.findings[0].code.startswith("resource_"))
        self.assertEqual(result.normalized_evidence, ())

    def test_invalid_snapshot_environment_short_circuits_relations(self) -> None:
        self.assert_atomic_invalid(
            self.validate(environment_id=""),
            ["agent_execution_authorization_environment_id_invalid"],
        )

    def test_invalid_types_and_malformed_fields_are_bounded_and_ordered(
        self,
    ) -> None:
        malformed = authorization(authority_id="")
        result = self.validate(evidence=[object(), malformed])
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_authorization_evidence_invalid_type",
                "agent_execution_authorization_evidence_invalid",
            ],
        )

    def test_plain_strings_do_not_substitute_for_closed_enums(self) -> None:
        malformed = authorization(
            authority_kind="human",
            state="granted",
        )
        self.assert_atomic_invalid(
            self.validate(evidence=[malformed]),
            ["agent_execution_authorization_evidence_invalid"],
        )

    def test_foundational_assignment_runtime_and_inference_findings_propagate(
        self,
    ) -> None:
        invalid_assignment = self.validate(
            assignments=[assignment(task_id="AIO-other")]
        )
        self.assert_atomic_invalid(invalid_assignment, ["task_id_mismatch"])

        duplicate_runtime = self.validate(
            runtime_options=[runtime(), runtime()]
        )
        self.assert_atomic_invalid(
            duplicate_runtime,
            ["duplicate_agent_runtime_option_id"],
        )

        duplicate_inference = self.validate(
            inference_options=[option(), option()]
        )
        self.assert_atomic_invalid(
            duplicate_inference,
            ["duplicate_inference_option_id"],
        )

    def test_incomplete_assignment_set_does_not_invent_or_block_evidence(self) -> None:
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, (authorization(),))

    def test_all_caller_iterables_are_captured_once_in_locked_order(self) -> None:
        events: list[str] = []
        supplied = self.base()
        supplied.update(
            {
                "assignments": OneShotIterable(
                    "assignments", [assignment()], events
                ),
                "actors": OneShotIterable("actors", [actor()], events),
                "runtime_options": OneShotIterable(
                    "runtime_options", [runtime()], events
                ),
                "inference_options": OneShotIterable(
                    "inference_options", [option()], events
                ),
                "evidence": OneShotIterable(
                    "evidence", [authorization()], events
                ),
            }
        )
        result = validate_agent_execution_authorization_evidence(
            **supplied  # type: ignore[arg-type]
        )
        self.assertTrue(result.valid)
        self.assertEqual(
            events,
            [
                "assignments",
                "actors",
                "runtime_options",
                "inference_options",
                "evidence",
            ],
        )

    def test_validation_does_not_mutate_caller_values(self) -> None:
        supplied = self.base()
        before = copy.deepcopy(supplied)
        result = validate_agent_execution_authorization_evidence(
            **supplied  # type: ignore[arg-type]
        )
        self.assertTrue(result.valid)
        self.assertEqual(supplied, before)


class AuthorizationInvestigationScenarioTests(AuthorizationFixture):
    def test_01_complete_positive_facts_remain_independent_and_coherent(
        self,
    ) -> None:
        requirement = OperationRequirement(
            "repository_file_read",
            "synthetic/input.txt",
        )
        capability = RuntimeOperationCapabilityObservation(
            "runtime::one",
            "repository_file_read",
            RuntimeOperationCapabilityState.PRESENT,
        )
        permission = EnvironmentOperationPermissionObservation(
            "runtime::one",
            "environment::synthetic",
            "repository_file_read",
            "synthetic/input.txt",
            EnvironmentOperationPermissionState.ALLOWED,
        )
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertEqual(requirement.identity, ("repository_file_read", "synthetic/input.txt"))
        self.assertEqual(capability.state, RuntimeOperationCapabilityState.PRESENT)
        self.assertEqual(permission.state, EnvironmentOperationPermissionState.ALLOWED)
        self.assertEqual(
            result.normalized_evidence[0].state,
            AgentExecutionAuthorizationState.GRANTED,
        )

    def test_02_permission_allowed_does_not_fill_missing_authorization(self) -> None:
        permission = EnvironmentOperationPermissionObservation(
            "runtime::one",
            "environment::synthetic",
            "repository_file_read",
            "synthetic/input.txt",
            EnvironmentOperationPermissionState.ALLOWED,
        )
        result = self.validate(evidence=[])
        self.assertEqual(permission.state, EnvironmentOperationPermissionState.ALLOWED)
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())

    def test_03_permission_denied_does_not_rewrite_supplied_grant(self) -> None:
        permission = EnvironmentOperationPermissionObservation(
            "runtime::one",
            "environment::synthetic",
            "repository_file_read",
            "synthetic/input.txt",
            EnvironmentOperationPermissionState.DENIED,
        )
        result = self.validate()
        self.assertEqual(permission.state, EnvironmentOperationPermissionState.DENIED)
        self.assertTrue(result.valid)
        self.assertEqual(
            result.normalized_evidence[0].state,
            AgentExecutionAuthorizationState.GRANTED,
        )

    def test_04_permission_allowed_and_explicit_denial_stay_independent(
        self,
    ) -> None:
        permission = EnvironmentOperationPermissionObservation(
            "runtime::one",
            "environment::synthetic",
            "repository_file_read",
            "synthetic/input.txt",
            EnvironmentOperationPermissionState.ALLOWED,
        )
        denial = authorization(state=AgentExecutionAuthorizationState.DENIED)
        result = self.validate(evidence=[denial])
        self.assertEqual(permission.state, EnvironmentOperationPermissionState.ALLOWED)
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, (denial,))

    def test_05_correct_action_with_wrong_task_has_no_assignment_match(self) -> None:
        self.assert_atomic_invalid(
            self.validate(evidence=[authorization(task_id="AIO-other")]),
            ["agent_execution_authorization_assignment_not_found"],
        )

    def test_06_wrong_workflow_or_stage_has_no_assignment_match(self) -> None:
        result = self.validate(
            evidence=[
                authorization(workflow_id="workflow::other"),
                authorization(stage_id="stage::other", resource="synthetic/b.txt"),
            ]
        )
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_authorization_assignment_not_found",
                "agent_execution_authorization_assignment_not_found",
            ],
        )

    def test_07_wrong_actor_has_no_assignment_match(self) -> None:
        self.assert_atomic_invalid(
            self.validate(evidence=[authorization(actor_id="agent::other")]),
            ["agent_execution_authorization_assignment_not_found"],
        )

    def test_08_wrong_runtime_is_rejected_as_unknown(self) -> None:
        self.assert_atomic_invalid(
            self.validate(
                evidence=[authorization(runtime_option_id="runtime::other")]
            ),
            ["agent_runtime_option_not_found"],
        )

    def test_09_wrong_environment_is_rejected(self) -> None:
        self.assert_atomic_invalid(
            self.validate(
                evidence=[authorization(environment_id="environment::other")]
            ),
            ["agent_execution_authorization_environment_mismatch"],
        )

    def test_10_wrong_operation_does_not_match_and_is_not_supported(self) -> None:
        self.assert_atomic_invalid(
            self.validate(
                evidence=[authorization(operation_id="repository_file_write")]
            ),
            ["operation_id_not_supported"],
        )

    def test_11_wrong_valid_resource_remains_a_different_exact_subject(self) -> None:
        wrong = authorization(resource="synthetic/other.txt")
        result = self.validate(evidence=[wrong])
        expected_subject = tuple(
            getattr(authorization(), field_name) for field_name in SUBJECT_FIELDS
        )
        supplied_subjects = {
            tuple(getattr(item, field_name) for field_name in SUBJECT_FIELDS)
            for item in result.normalized_evidence
        }
        self.assertTrue(result.valid)
        self.assertNotIn(expected_subject, supplied_subjects)

    def test_12_task_human_approval_does_not_create_authorization(self) -> None:
        approved_task = {
            **TASK,
            "human_control": {"approval": "approved"},
        }
        result = self.validate(task=approved_task, evidence=[])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())

    def test_13_staleness_and_expiry_are_deliberately_not_modeled(self) -> None:
        self.assertNotIn("expires_at", {item.name for item in fields(authorization())})
        result = self.validate()
        self.assertTrue(result.valid)
        self.assertFalse(hasattr(result.normalized_evidence[0], "issued_at"))

    def test_14_new_denial_is_not_labeled_as_a_revocation_record(self) -> None:
        prior = self.validate()
        denial = authorization(state=AgentExecutionAuthorizationState.DENIED)
        current = self.validate(evidence=[denial])
        self.assertTrue(prior.valid)
        self.assertTrue(current.valid)
        self.assertEqual(current.normalized_evidence, (denial,))
        self.assertFalse(hasattr(denial, "revoked_at"))

    def test_15_repeated_validation_has_no_consumption_or_replay_state(self) -> None:
        value = authorization()
        first = self.validate(evidence=[value])
        second = self.validate(evidence=[value])
        self.assertEqual(first, second)
        self.assertTrue(second.valid)
        self.assertFalse(hasattr(value, "consumed_at"))

    def test_16_duplicate_identical_evidence_is_invalid(self) -> None:
        value = authorization()
        self.assert_atomic_invalid(
            self.validate(evidence=[value, value]),
            ["duplicate_agent_execution_authorization_evidence"],
        )

    def test_17_conflicting_authorization_evidence_is_invalid(self) -> None:
        self.assert_atomic_invalid(
            self.validate(
                evidence=[
                    authorization(),
                    authorization(state=AgentExecutionAuthorizationState.DENIED),
                ]
            ),
            ["conflicting_agent_execution_authorization_evidence"],
        )

    def test_18_policy_allow_without_exact_evidence_remains_missing(self) -> None:
        permission_decision = "allow"
        result = self.validate(evidence=[])
        self.assertEqual(permission_decision, "allow")
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())


class AuthorizationSafetyBoundaryTests(AuthorizationFixture):
    def test_static_module_has_no_io_clock_execution_or_policy_imports(self) -> None:
        tree = ast.parse(
            (ROOT / "engineering_orchestration" /
             "agent_execution_authorization_evidence.py").read_text(
                encoding="utf-8"
            )
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
                    "system",
                    "run",
                    "Popen",
                    "time",
                }
            )
        )

    def test_dynamic_validation_performs_no_file_open(self) -> None:
        with patch.object(
            builtins,
            "open",
            side_effect=AssertionError("validation attempted file I/O"),
        ):
            result = self.validate()
        self.assertTrue(result.valid)

    def test_empty_evidence_never_synthesizes_authority_or_cartesian_values(
        self,
    ) -> None:
        result = self.validate(
            evidence=[],
            runtime_options=[runtime("runtime::a"), runtime("runtime::b")],
            inference_options=[option("option::a"), option("option::b")],
        )
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_evidence, ())

    def test_module_exposes_no_decision_enforcement_or_invocation_api(self) -> None:
        exported = set(vars(subject))
        forbidden_fragments = (
            "dispatch",
            "execute",
            "invoke",
            "enforce",
            "issue_authorization",
            "authenticate",
            "permission_decision",
        )
        self.assertTrue(
            all(
                not any(fragment in name.lower() for fragment in forbidden_fragments)
                for name in exported
                if not name.startswith("__")
            )
        )


if __name__ == "__main__":
    unittest.main()
