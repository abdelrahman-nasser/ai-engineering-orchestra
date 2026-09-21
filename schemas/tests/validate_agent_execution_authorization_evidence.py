from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
    validate_agent_execution_authorization_evidence,
)
from engineering_orchestration.agent_runtime_option import (
    AgentRuntimeOptionDefinition,
)
from engineering_orchestration.assignment import Assignment
from engineering_orchestration.inference_option import InferenceOptionDefinition
from engineering_orchestration.role_catalog import RoleCatalog
from engineering_orchestration.workflow_catalog import (
    WorkflowCatalog,
    WorkflowDefinition,
    WorkflowStage,
)


SCHEMA_PATH = (
    REPO_ROOT
    / "schemas"
    / "agent-execution-authorization-evidence.schema.json"
)
FIXTURE_DIR = (
    REPO_ROOT
    / "schemas"
    / "tests"
    / "agent-execution-authorization-evidence"
)


class ExpectedStructuralFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


class FixtureExpectation(NamedTuple):
    structural_failure: (
        ExpectedStructuralFailure
        | tuple[ExpectedStructuralFailure, ...]
        | None
    ) = None
    semantic_finding: str | None = None


FIXTURE_CASES: dict[str, FixtureExpectation] = {
    "valid-human-granted.yaml": FixtureExpectation(),
    "valid-human-denied.yaml": FixtureExpectation(),
    "valid-policy-granted.yaml": FixtureExpectation(),
    "valid-policy-denied.yaml": FixtureExpectation(),
    "invalid-missing-task-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "task_id")
    ),
    "invalid-missing-workflow-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "workflow_id")
    ),
    "invalid-missing-stage-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "stage_id")
    ),
    "invalid-missing-role-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "role_id")
    ),
    "invalid-missing-actor-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "actor_id")
    ),
    "invalid-missing-runtime-option-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "runtime_option_id")
    ),
    "invalid-missing-option-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "option_id")
    ),
    "invalid-missing-environment-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "environment_id")
    ),
    "invalid-missing-operation-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "operation_id")
    ),
    "invalid-missing-resource.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "resource")
    ),
    "invalid-missing-authority-kind.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "authority_kind")
    ),
    "invalid-missing-authority-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "authority_id")
    ),
    "invalid-missing-provenance-reference.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "provenance_reference")
    ),
    "invalid-missing-state.yaml": FixtureExpectation(
        ExpectedStructuralFailure("required", (), "state")
    ),
    "invalid-task-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("task_id",))
    ),
    "invalid-workflow-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("workflow_id",))
    ),
    "invalid-stage-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("stage_id",))
    ),
    "invalid-role-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("role_id",))
    ),
    "invalid-actor-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("actor_id",))
    ),
    "invalid-runtime-option-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("runtime_option_id",))
    ),
    "invalid-option-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("option_id",))
    ),
    "invalid-environment-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("environment_id",))
    ),
    "invalid-operation-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("operation_id",))
    ),
    "invalid-resource-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("resource",))
    ),
    "invalid-authority-kind-type.yaml": FixtureExpectation(
        (
            ExpectedStructuralFailure("enum", ("authority_kind",)),
            ExpectedStructuralFailure("type", ("authority_kind",)),
        )
    ),
    "invalid-authority-id-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("authority_id",))
    ),
    "invalid-provenance-reference-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ("provenance_reference",))
    ),
    "invalid-state-type.yaml": FixtureExpectation(
        (
            ExpectedStructuralFailure("enum", ("state",)),
            ExpectedStructuralFailure("type", ("state",)),
        )
    ),
    "invalid-empty-task-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("task_id",))
    ),
    "invalid-empty-workflow-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("workflow_id",))
    ),
    "invalid-empty-stage-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("stage_id",))
    ),
    "invalid-empty-role-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("role_id",))
    ),
    "invalid-empty-actor-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("actor_id",))
    ),
    "invalid-empty-runtime-option-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("runtime_option_id",))
    ),
    "invalid-empty-option-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("option_id",))
    ),
    "invalid-empty-environment-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("environment_id",))
    ),
    "invalid-empty-operation-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("operation_id",))
    ),
    "invalid-empty-resource.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("resource",))
    ),
    "invalid-empty-authority-kind.yaml": FixtureExpectation(
        (
            ExpectedStructuralFailure("enum", ("authority_kind",)),
            ExpectedStructuralFailure("minLength", ("authority_kind",)),
        )
    ),
    "invalid-empty-authority-id.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("authority_id",))
    ),
    "invalid-empty-provenance-reference.yaml": FixtureExpectation(
        ExpectedStructuralFailure("minLength", ("provenance_reference",))
    ),
    "invalid-empty-state.yaml": FixtureExpectation(
        (
            ExpectedStructuralFailure("enum", ("state",)),
            ExpectedStructuralFailure("minLength", ("state",)),
        )
    ),
    "invalid-unsupported-authority-kind.yaml": FixtureExpectation(
        ExpectedStructuralFailure("enum", ("authority_kind",))
    ),
    "invalid-unsupported-state.yaml": FixtureExpectation(
        ExpectedStructuralFailure("enum", ("state",))
    ),
    "invalid-extra-field.yaml": FixtureExpectation(
        ExpectedStructuralFailure("additionalProperties", ())
    ),
    "invalid-root-type.yaml": FixtureExpectation(
        ExpectedStructuralFailure("type", ())
    ),
    "invalid-unknown-assignment.yaml": FixtureExpectation(
        semantic_finding="agent_execution_authorization_assignment_not_found"
    ),
    "invalid-unknown-runtime.yaml": FixtureExpectation(
        semantic_finding="agent_runtime_option_not_found"
    ),
    "invalid-unknown-inference-option.yaml": FixtureExpectation(
        semantic_finding="inference_option_not_found"
    ),
    "invalid-environment-mismatch.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_authorization_environment_mismatch"
        )
    ),
    "invalid-malformed-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_invalid_syntax"
    ),
    "invalid-unsupported-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_not_supported"
    ),
    "invalid-resource-parent.yaml": FixtureExpectation(
        semantic_finding="resource_parent_segment"
    ),
}


SYNTHETIC_TASK: dict[str, object] = {
    "id": "AIO-SYNTHETIC",
    "workflow": "synthetic-workflow",
}
SYNTHETIC_WORKFLOW_CATALOG = WorkflowCatalog(
    workflows_dir=Path("synthetic-workflows"),
    definitions={
        "synthetic-workflow": WorkflowDefinition(
            id="synthetic-workflow",
            name="Synthetic Workflow",
            purpose="Fixture-only responsibility context.",
            stages=[
                WorkflowStage(
                    id="implement",
                    purpose="Fixture-only implementation stage.",
                    required_roles=["software-engineer"],
                )
            ],
        )
    },
)
SYNTHETIC_ROLE_CATALOG = RoleCatalog(
    roles_source=None,
    definitions={
        "software-engineer": {
            "id": "software-engineer",
            "required_capabilities": ["implementation"],
        }
    },
)
SYNTHETIC_ACTORS: tuple[dict[str, object], ...] = (
    {
        "id": "actor::assigned",
        "kind": "agent",
        "competencies": ["implementation"],
    },
)
SYNTHETIC_ASSIGNMENTS = (
    Assignment(
        task_id="AIO-SYNTHETIC",
        workflow_id="synthetic-workflow",
        stage_id="implement",
        role_id="software-engineer",
        actor_id="actor::assigned",
    ),
)
SYNTHETIC_RUNTIME_OPTIONS = (
    AgentRuntimeOptionDefinition("runtime::known"),
)
SYNTHETIC_INFERENCE_OPTIONS = (
    InferenceOptionDefinition(
        "option::known",
        "provider::synthetic",
        "model::synthetic",
    ),
)
SYNTHETIC_ENVIRONMENT_ID = "environment::primary"


def check_fixture_coverage() -> bool:
    expected = set(FIXTURE_CASES)
    if not FIXTURE_DIR.is_dir():
        print(f"FAIL fixture coverage: directory missing: {FIXTURE_DIR}")
        return False
    entries = {path.name for path in FIXTURE_DIR.iterdir()}
    files = {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}
    missing = expected - files
    unexpected = entries - expected
    mismatched = {
        name
        for name, expectation in FIXTURE_CASES.items()
        if not name.startswith(
            "valid-"
            if expectation.structural_failure is None
            and expectation.semantic_finding is None
            else "invalid-"
        )
        or not name.endswith(".yaml")
    }
    for label, names in (
        ("missing fixtures", missing),
        ("unregistered entries", unexpected),
        ("registry naming/result mismatch", mismatched),
    ):
        if names:
            print(f"FAIL fixture coverage: {label}: {', '.join(sorted(names))}")
    return not (missing or unexpected or mismatched)


def structural_result(
    validator: Draft202012Validator,
    document: Any,
    expected: (
        ExpectedStructuralFailure
        | tuple[ExpectedStructuralFailure, ...]
        | None
    ),
    label: str,
) -> bool:
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (
            str(list(error.absolute_path)),
            str(error.validator),
        ),
    )
    if expected is None:
        passed = not errors
    else:
        expected_failures = expected if type(expected) is tuple else (expected,)
        passed = len(errors) == len(expected_failures)
        for error, failure in zip(errors, expected_failures):
            passed = passed and (
                error.validator == failure.keyword
                and tuple(error.absolute_path) == failure.path
            )
            if failure.missing_property is not None:
                passed = passed and (
                    error.validator == "required"
                    and isinstance(error.instance, dict)
                    and set(error.validator_value) - set(error.instance)
                    == {failure.missing_property}
                )
    expectation = expected or "structurally valid"
    print(f"{'PASS' if passed else 'FAIL'} {label} structural: {expectation}")
    if not passed:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path)
            print(
                f"  - {location or '<root>'} [{error.validator}]: "
                f"{error.message}"
            )
    return passed


def semantic_result(
    document: dict[str, str],
    expected_finding: str | None,
    label: str,
) -> bool:
    evidence = AgentExecutionAuthorizationEvidence(
        task_id=document["task_id"],
        workflow_id=document["workflow_id"],
        stage_id=document["stage_id"],
        role_id=document["role_id"],
        actor_id=document["actor_id"],
        runtime_option_id=document["runtime_option_id"],
        option_id=document["option_id"],
        environment_id=document["environment_id"],
        operation_id=document["operation_id"],
        resource=document["resource"],
        authority_kind=AgentExecutionAuthorizationAuthorityKind(
            document["authority_kind"]
        ),
        authority_id=document["authority_id"],
        provenance_reference=document["provenance_reference"],
        state=AgentExecutionAuthorizationState(document["state"]),
    )
    result = validate_agent_execution_authorization_evidence(
        evidence=(evidence,),
        assignments=SYNTHETIC_ASSIGNMENTS,
        task=SYNTHETIC_TASK,
        workflow_catalog=SYNTHETIC_WORKFLOW_CATALOG,
        role_catalog=SYNTHETIC_ROLE_CATALOG,
        actors=SYNTHETIC_ACTORS,
        runtime_options=SYNTHETIC_RUNTIME_OPTIONS,
        inference_options=SYNTHETIC_INFERENCE_OPTIONS,
        environment_id=SYNTHETIC_ENVIRONMENT_ID,
    )
    if expected_finding is None:
        passed = (
            result.valid
            and result.findings == ()
            and result.normalized_evidence == (evidence,)
        )
        expectation = "semantically valid"
    else:
        passed = (
            not result.valid
            and [finding.code for finding in result.findings]
            == [expected_finding]
            and result.normalized_evidence == ()
        )
        expectation = f"semantic finding {expected_finding}"
    print(f"{'PASS' if passed else 'FAIL'} {label} semantic: {expectation}")
    if not passed:
        print(
            "  - actual: "
            f"valid={result.valid}, "
            f"findings={[item.code for item in result.findings]}, "
            f"normalized_evidence={result.normalized_evidence!r}"
        )
    return passed


def main() -> int:
    print(
        "AI Engineering Orchestra - Agent Execution Authorization Evidence "
        "Validation"
    )
    print("=" * 78)
    if not check_fixture_coverage():
        return 1

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as exc:
        print(f"FAIL schema load or meta-validation: {exc}")
        return 1

    structural_passed = 0
    semantic_passed = 0
    semantic_total = 0
    for name, expectation in sorted(FIXTURE_CASES.items()):
        path = FIXTURE_DIR / name
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FAIL {path.stem}: could not load YAML: {exc}")
            continue

        structurally_correct = structural_result(
            validator,
            document,
            expectation.structural_failure,
            path.stem,
        )
        if structurally_correct:
            structural_passed += 1

        if expectation.structural_failure is None:
            semantic_total += 1
            if structurally_correct and semantic_result(
                document,
                expectation.semantic_finding,
                path.stem,
            ):
                semantic_passed += 1

    structural_total = len(FIXTURE_CASES)
    print(
        f"\nStructural result: {structural_passed}/{structural_total} "
        "fixtures passed"
    )
    print(f"Semantic result: {semantic_passed}/{semantic_total} fixtures passed")
    if (
        structural_passed == structural_total
        and semantic_passed == semantic_total
    ):
        print("Agent Execution Authorization Evidence validation PASSED.")
        return 0
    print("Agent Execution Authorization Evidence validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
