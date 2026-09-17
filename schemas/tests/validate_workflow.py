from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator

# Repository-local tests only. Canonical Workflow definitions are serialized in YAML.
# Schema validity does not prove semantic/governance correctness.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from engineering_orchestration.workflow_catalog import semantic_uniqueness_errors

from engineering_orchestration.role_catalog import load_role_catalog
from engineering_orchestration.schema_resources import schema_errors

SCHEMA_PATH = REPO_ROOT / "schemas" / "workflow.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "workflow"
CANONICAL_WORKFLOWS = [
    REPO_ROOT / "workflows" / "standard-change.yaml",
    REPO_ROOT / "workflows" / "architecture-change.yaml",
    REPO_ROOT / "workflows" / "security-sensitive-change.yaml",
]


class ExpectedFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


FIXTURE_CASES: dict[str, ExpectedFailure | None] = {
    "valid-minimal.yaml": None,
    "valid-full.yaml": None,
    "valid-structurally-empty-optional-arrays.yaml": None,
    "valid-structurally-duplicate-references.yaml": None,
    "valid-structurally-empty-unconstrained-strings.yaml": None,
    "valid-structurally-duplicate-stage-ids.yaml": None,
    "invalid-missing-id.yaml": ExpectedFailure("required", (), "id"),
    "invalid-missing-name.yaml": ExpectedFailure("required", (), "name"),
    "invalid-missing-purpose.yaml": ExpectedFailure("required", (), "purpose"),
    "invalid-missing-stages.yaml": ExpectedFailure("required", (), "stages"),
    "invalid-stage-missing-id.yaml": ExpectedFailure("required", ("stages", 0), "id"),
    "invalid-stage-missing-purpose.yaml": ExpectedFailure("required", ("stages", 0), "purpose"),
    "invalid-root-type.yaml": ExpectedFailure("type", ()),
    "invalid-id-type.yaml": ExpectedFailure("type", ("id",)),
    "invalid-name-type.yaml": ExpectedFailure("type", ("name",)),
    "invalid-purpose-type.yaml": ExpectedFailure("type", ("purpose",)),
    "invalid-applicable_task_types-type.yaml": ExpectedFailure("type", ("applicable_task_types",)),
    "invalid-stages-type.yaml": ExpectedFailure("type", ("stages",)),
    "invalid-stage-id-type.yaml": ExpectedFailure("type", ("stages", 0, "id")),
    "invalid-stage-purpose-type.yaml": ExpectedFailure("type", ("stages", 0, "purpose")),
    "invalid-stage-required_roles-type.yaml": ExpectedFailure("type", ("stages", 0, "required_roles")),
    "invalid-stage-required_quality_gates-type.yaml": ExpectedFailure("type", ("stages", 0, "required_quality_gates")),
    "invalid-stage-human_control_checkpoint-type.yaml": ExpectedFailure("type", ("stages", 0, "human_control_checkpoint")),
    "invalid-checkpoint-string.yaml": ExpectedFailure("type", ("stages", 0, "human_control_checkpoint")),
    "invalid-checkpoint-null.yaml": ExpectedFailure("type", ("stages", 0, "human_control_checkpoint")),
    "invalid-empty-stages.yaml": ExpectedFailure("minItems", ("stages",)),
    "invalid-stage-item-type.yaml": ExpectedFailure("type", ("stages", 0)),
    "invalid-task-type-item.yaml": ExpectedFailure("type", ("applicable_task_types", 0)),
    "invalid-required_roles-item.yaml": ExpectedFailure("type", ("stages", 0, "required_roles", 0)),
    "invalid-required_quality_gates-item.yaml": ExpectedFailure("type", ("stages", 0, "required_quality_gates", 0)),
    "invalid-empty-name.yaml": ExpectedFailure("minLength", ("name",)),
    "invalid-empty-stage-purpose.yaml": ExpectedFailure("minLength", ("stages", 0, "purpose")),
    "invalid-unknown-top-level.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-unknown-stage-field.yaml": ExpectedFailure("additionalProperties", ("stages", 0)),
}

SAMPLE_WORKFLOW: dict[str, Any] = {
    "id": "example-workflow",
    "name": "Example",
    "purpose": "Govern a change.",
    "applicable_task_types": ["custom/task"],
    "stages": [
        {
            "id": "understand",
            "purpose": "Understand context.",
            "required_roles": ["custom/Role"],
            "required_quality_gates": ["custom.Gate"],
            "human_control_checkpoint": False,
        },
        {"id": "review", "purpose": "Review.", "human_control_checkpoint": True},
    ],
}


def check_fixture_coverage() -> bool:
    if not FIXTURE_DIR.is_dir():
        print(f"FAIL fixture coverage: directory missing: {FIXTURE_DIR}")
        return False
    expected = set(FIXTURE_CASES)
    entries = {path.name for path in FIXTURE_DIR.iterdir()}
    files = {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}
    problems = {
        "missing fixtures": expected - files,
        "unregistered entries": entries - expected,
        "registry naming/result mismatch": {
            name for name, failure in FIXTURE_CASES.items()
            if not name.startswith("valid-" if failure is None else "invalid-")
            or not name.endswith(".yaml")
        },
    }
    for label, names in problems.items():
        if names:
            print(f"FAIL fixture coverage: {label}: {', '.join(sorted(names))}")
    return not any(problems.values())


def validate_document(
    validator: Draft202012Validator,
    document: Any,
    label: str,
    expected_failure: ExpectedFailure | None = None,
) -> bool:
    errors = schema_errors(validator, document)
    if expected_failure is None:
        passed = not errors
    else:
        passed = len(errors) == 1
        if passed:
            error = errors[0]
            passed = (
                error.validator == expected_failure.keyword
                and tuple(error.absolute_path) == expected_failure.path
            )
            if expected_failure.missing_property is not None:
                passed = passed and (
                    error.validator == "required"
                    and isinstance(error.instance, dict)
                    and set(error.validator_value) - set(error.instance)
                    == {expected_failure.missing_property}
                )
    print(f"{'PASS' if passed else 'FAIL'} {label}: expected {expected_failure or 'valid'}")
    if not passed:
        for error in errors:
            print(f"  {list(error.absolute_path)} [{error.validator}]: {error.message}")
    return passed


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    print("AI Engineering Orchestra - Workflow validation (repository tests only)")
    if not check_fixture_coverage():
        return 1
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        print("PASS Draft 2020-12 schema meta-validation")
        results = [True]
        definitions: list[dict[str, Any]] = []

        print("\nCanonical YAML definitions - structural validation")
        for path in CANONICAL_WORKFLOWS:
            if not path.is_file():
                print(f"FAIL {path.relative_to(REPO_ROOT)}: file not found")
                results.append(False)
                continue
            try:
                definition = load_yaml(path)
            except Exception as exc:
                print(f"FAIL {path.relative_to(REPO_ROOT)}: YAML parse error: {exc}")
                results.append(False)
                continue

            valid = validate_document(validator, definition, str(path.relative_to(REPO_ROOT)))
            results.append(valid)
            if valid and isinstance(definition, dict):
                definitions.append(definition)

        print("\nRegistered structural fixtures")
        for name, failure in sorted(FIXTURE_CASES.items()):
            results.append(validate_document(validator, load_yaml(FIXTURE_DIR / name), name, failure))

        print("\nRepository semantic validation - ID uniqueness only")
        errors = semantic_uniqueness_errors(definitions)
        unique = len(definitions) == len(CANONICAL_WORKFLOWS) and not errors
        print(f"{'PASS' if unique else 'FAIL'} IDs unique across inspected canonical definitions")
        for error in errors:
            print("  " + error)
        results.append(unique)

        duplicate_stages = load_yaml(FIXTURE_DIR / "valid-structurally-duplicate-stage-ids.yaml")
        semantic_cases = [
            ("duplicate Stage IDs rejected semantically", [duplicate_stages],
             ["Duplicate Stage ID in example: review"]),
            ("duplicate Workflow IDs rejected semantically",
             [SAMPLE_WORKFLOW, SAMPLE_WORKFLOW],
             ["Duplicate Workflow ID: example-workflow"]),
            ("Stage IDs may repeat across different Workflows",
             [SAMPLE_WORKFLOW, dict(SAMPLE_WORKFLOW, id="other")], []),
        ]
        for label, documents, expected_errors in semantic_cases:
            passed = semantic_uniqueness_errors(documents) == expected_errors
            print(f"{'PASS' if passed else 'FAIL'} {label}")
            results.append(passed)

        print("\nRepository semantic validation - Workflow Role references")
        role_catalog = load_role_catalog()
        if role_catalog.is_valid:
            reference_errors = []
            for definition in sorted(definitions, key=lambda item: item["id"]):
                for stage in definition["stages"]:
                    for role_id in stage.get("required_roles", []):
                        if role_catalog.get(role_id) is None:
                            reference_errors.append(
                                f"{definition['id']}.{stage['id']}: unknown Role {role_id}"
                            )
            references_valid = not reference_errors
        else:
            reference_errors = [
                "framework Role catalog could not load: "
                + "; ".join(role_catalog.load_errors)
            ]
            references_valid = False
        print(
            f"{'PASS' if references_valid else 'FAIL'} canonical Workflow Role "
            "references resolve"
        )
        for error in reference_errors:
            print("  " + error)
        results.append(references_valid)
        print("Quality Gate existence remains manual review.")
    except Exception as error:
        print(f"FAIL validation could not complete: {type(error).__name__}: {error}")
        return 1
    print(f"\nResult: {sum(results)}/{len(results)} checks passed")
    print("Workflow validation " + ("PASSED." if all(results) else "FAILED."))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
