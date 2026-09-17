from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "role.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "role"
ROLE_DIR = REPO_ROOT / "roles"
EXPECTED_ROLE_IDS = [
    "architect",
    "documentation-specialist",
    "reviewer",
    "security-reviewer",
    "software-engineer",
]


class ExpectedFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


FIXTURE_CASES: dict[str, ExpectedFailure | None] = {
    "valid-minimal.yaml": None,
    "valid-full.yaml": None,
    "valid-structurally-empty-required-arrays.yaml": None,
    "valid-structurally-empty-optional-array.yaml": None,
    "valid-structurally-duplicate-items.yaml": None,
    "invalid-missing-id.yaml": ExpectedFailure("required", (), "id"),
    "invalid-missing-name.yaml": ExpectedFailure("required", (), "name"),
    "invalid-missing-purpose.yaml": ExpectedFailure("required", (), "purpose"),
    "invalid-missing-responsibilities.yaml": ExpectedFailure(
        "required", (), "responsibilities"
    ),
    "invalid-missing-required-capabilities.yaml": ExpectedFailure(
        "required", (), "required_capabilities"
    ),
    "invalid-unknown-top-level.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-schema-version-present.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-empty-id.yaml": ExpectedFailure("minLength", ("id",)),
    "invalid-empty-name.yaml": ExpectedFailure("minLength", ("name",)),
    "invalid-empty-purpose.yaml": ExpectedFailure("minLength", ("purpose",)),
    "invalid-responsibilities-type.yaml": ExpectedFailure("type", ("responsibilities",)),
    "invalid-required-capabilities-type.yaml": ExpectedFailure(
        "type", ("required_capabilities",)
    ),
    "invalid-applicable-task-types-type.yaml": ExpectedFailure(
        "type", ("applicable_task_types",)
    ),
    "invalid-empty-responsibility-item.yaml": ExpectedFailure(
        "minLength", ("responsibilities", 0)
    ),
    "invalid-empty-capability-item.yaml": ExpectedFailure(
        "minLength", ("required_capabilities", 0)
    ),
    "invalid-empty-task-type-item.yaml": ExpectedFailure(
        "minLength", ("applicable_task_types", 0)
    ),
    "invalid-root-type.yaml": ExpectedFailure("type", ()),
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


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_document(
    validator: Draft202012Validator,
    document: Any,
    label: str,
    expected_failure: ExpectedFailure | None = None,
) -> bool:
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (str(list(error.absolute_path)), str(error.validator)),
    )
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
            print(
                f"  {list(error.absolute_path)} [{error.validator}]: {error.message}"
            )
    return passed


def main() -> int:
    print("AI Engineering Orchestra - Role Schema Validation")
    print("=" * 63)
    if "--test-mismatch" in sys.argv:
        print("Self-test mismatch requested: simulating unexpected validation failure.")
        print("FAIL simulated-mismatch: expected valid but validation failed")
        print("Schema validation FAILED.")
        return 1
    if not check_fixture_coverage():
        return 1

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as exc:
        print(f"FAIL schema load or meta-validation: {exc}")
        return 1

    results: list[bool] = []
    canonical_documents: list[dict[str, Any]] = []
    canonical_paths = sorted(ROLE_DIR.glob("*.yaml"), key=lambda path: path.name)

    print("\n--- Canonical Role YAML Definitions ---")
    for path in canonical_paths:
        label = str(path.relative_to(REPO_ROOT))
        try:
            document = load_yaml(path)
        except Exception as exc:
            print(f"FAIL {label}: could not load YAML: {exc}")
            results.append(False)
            continue
        valid = validate_document(validator, document, label)
        results.append(valid)
        if valid and isinstance(document, dict):
            canonical_documents.append(document)

    actual_ids = [document["id"] for document in canonical_documents]
    coverage_valid = (
        len(canonical_paths) == len(EXPECTED_ROLE_IDS)
        and len(actual_ids) == len(set(actual_ids))
        and sorted(actual_ids) == EXPECTED_ROLE_IDS
    )
    print(
        f"{'PASS' if coverage_valid else 'FAIL'} canonical Role IDs: "
        f"{', '.join(sorted(actual_ids)) or '<none>'}"
    )
    results.append(coverage_valid)

    print("\n--- Fixture Cases ---")
    for name, failure in sorted(FIXTURE_CASES.items()):
        path = FIXTURE_DIR / name
        try:
            document = load_yaml(path)
        except Exception as exc:
            print(f"FAIL {path.stem}: could not load YAML: {exc}")
            results.append(False)
            continue
        results.append(validate_document(validator, document, path.stem, failure))

    print(f"\nResult: {sum(results)}/{len(results)} checks passed")
    if all(results):
        print("Schema validation PASSED.")
        return 0
    print("Schema validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
