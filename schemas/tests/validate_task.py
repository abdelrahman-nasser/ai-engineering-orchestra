from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = REPO_ROOT / "schemas" / "task.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "task"

CANONICAL_TASKS = [
    REPO_ROOT / "templates" / "task" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-001-foundation" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-002-project-manifest" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-003-project-manifest-schema" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-004-task-specification" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-005-task-schema" / "task.yaml",
    REPO_ROOT / ".ai" / "tasks" / "AIO-006-role-specification" / "task.yaml",
]


class ExpectedFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


# None means valid; invalid cases declare the exact intended constraint.
FIXTURE_CASES: dict[str, ExpectedFailure | None] = {
    "valid-minimal.yaml": None,
    "valid-full.yaml": None,
    "valid-empty-dependencies.yaml": None,
    "invalid-duplicate-dependencies.yaml": ExpectedFailure(
        "uniqueItems", ("dependencies",)
    ),
    "invalid-empty-scope-include.yaml": ExpectedFailure(
        "minItems", ("scope", "include")
    ),
    "invalid-human-control-field.yaml": ExpectedFailure(
        "additionalProperties", ("human_control",)
    ),
    "invalid-missing-required.yaml": ExpectedFailure("required", (), "scope"),
    "invalid-quality-gate.yaml": ExpectedFailure("pattern", ("quality_gates", 0)),
    "invalid-status.yaml": ExpectedFailure("enum", ("status",)),
    "invalid-unknown-top-level.yaml": ExpectedFailure("additionalProperties", ()),
}


def check_fixture_coverage() -> bool:
    if not FIXTURE_DIR.is_dir():
        print(f"FAIL fixture coverage: directory missing: {FIXTURE_DIR}")
        return False

    expected = set(FIXTURE_CASES)
    entries = set(path.name for path in FIXTURE_DIR.iterdir())
    files = set(path.name for path in FIXTURE_DIR.iterdir() if path.is_file())
    missing = expected - files
    unexpected = entries - expected
    mismatched = {
        name for name, failure in FIXTURE_CASES.items()
        if not name.startswith("valid-" if failure is None else "invalid-")
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def validate_case(
    validator: Draft202012Validator,
    path: Path,
    expected_valid: bool,
    label: str,
    expected_failure: ExpectedFailure | None = None,
) -> bool:
    try:
        document = load_yaml(path)
    except Exception as exc:
        print(f"FAIL {label}: could not load YAML: {exc}")
        return False

    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (str(list(error.absolute_path)), str(error.validator)),
    )

    actual_valid = not errors

    intended_failure = False
    if expected_failure is not None and len(errors) == 1:
        error = errors[0]
        intended_failure = (
            error.validator == expected_failure.keyword
            and tuple(error.absolute_path) == expected_failure.path
        )
        if expected_failure.missing_property is not None:
            intended_failure = intended_failure and (
                error.validator == "required"
                and isinstance(error.instance, dict)
                and set(error.validator_value) - set(error.instance)
                == {expected_failure.missing_property}
            )

    if (expected_valid and actual_valid and expected_failure is None) or (
        not expected_valid and intended_failure
    ):
        if expected_valid:
            print(f"PASS {label} expected valid")
        else:
            print(f"PASS {label} expected invalid: {expected_failure}")
        return True

    if expected_valid:
        print(f"FAIL {label}: expected valid but validation failed")
    elif actual_valid:
        print(f"FAIL {label}: expected invalid but validation passed")
    else:
        print(f"FAIL {label}: expected exactly one failure: {expected_failure}")

    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path)
        location = location or "<root>"
        print(f"  - {location} [{error.validator}]: {error.message}")

    return False


def main() -> int:
    print("AI Engineering Orchestra - Task Schema Validation")
    print("=" * 63)

    if not check_fixture_coverage():
        return 1

    try:
        schema = load_json(SCHEMA_PATH)
    except Exception as exc:
        print(f"FAIL schema load: {exc}")
        return 1

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        print(f"FAIL schema meta-validation: {exc}")
        return 1

    validator = Draft202012Validator(schema)

    cases: list[tuple[Path, bool, str, ExpectedFailure | None]] = []

    for path in CANONICAL_TASKS:
        relative = path.relative_to(REPO_ROOT)
        cases.append((path, True, str(relative), None))

    for name, failure in sorted(FIXTURE_CASES.items()):
        path = FIXTURE_DIR / name
        cases.append((path, failure is None, path.stem, failure))

    passed = 0

    for path, expected_valid, label, expected_failure in cases:
        if not path.exists():
            print(f"FAIL {label}: file does not exist")
            continue

        if validate_case(
            validator=validator,
            path=path,
            expected_valid=expected_valid,
            label=label,
            expected_failure=expected_failure,
        ):
            passed += 1

    total = len(cases)

    print()
    print(f"Result: {passed}/{total} cases passed")

    if passed == total:
        print("Schema validation PASSED.")
        return 0

    print("Schema validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
