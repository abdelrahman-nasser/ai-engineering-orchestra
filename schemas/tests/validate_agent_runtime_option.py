from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "agent-runtime-option.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "agent-runtime-option"


class ExpectedFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


FIXTURE_CASES: dict[str, ExpectedFailure | None] = {
    "valid-minimal.yaml": None,
    "valid-opaque-identifier.yaml": None,
    "invalid-missing-runtime-option-id.yaml": ExpectedFailure(
        "required", (), "runtime_option_id"
    ),
    "invalid-empty-runtime-option-id.yaml": ExpectedFailure(
        "minLength", ("runtime_option_id",)
    ),
    "invalid-extra-field.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-provider-field.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-model-field.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-actor-field.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-tools-field.yaml": ExpectedFailure("additionalProperties", ()),
    "invalid-credential-field.yaml": ExpectedFailure(
        "additionalProperties", ()
    ),
    "invalid-root-type.yaml": ExpectedFailure("type", ()),
}


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
        for name, failure in FIXTURE_CASES.items()
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


def validate_document(
    validator: Draft202012Validator,
    document: Any,
    failure: ExpectedFailure | None,
    label: str,
) -> bool:
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (str(list(error.absolute_path)), str(error.validator)),
    )
    if failure is None and not errors:
        print(f"PASS {label} expected valid")
        return True

    intended = False
    if failure is not None and len(errors) == 1:
        error = errors[0]
        intended = (
            error.validator == failure.keyword
            and tuple(error.absolute_path) == failure.path
        )
        if failure.missing_property is not None:
            intended = intended and (
                error.validator == "required"
                and isinstance(error.instance, dict)
                and set(error.validator_value) - set(error.instance)
                == {failure.missing_property}
            )
    if intended:
        print(f"PASS {label} expected invalid: {failure}")
        return True

    expectation = "valid" if failure is None else f"exactly one failure: {failure}"
    print(f"FAIL {label}: expected {expectation}")
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        print(f"  - {location} [{error.validator}]: {error.message}")
    return False


def main() -> int:
    print("AI Engineering Orchestra - Agent Runtime Option Schema Validation")
    print("=" * 78)
    if not check_fixture_coverage():
        return 1

    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        print(f"FAIL schema load or meta-validation: {exc}")
        return 1

    validator = Draft202012Validator(schema)
    passed = 0
    for name, failure in sorted(FIXTURE_CASES.items()):
        path = FIXTURE_DIR / name
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"FAIL {path.stem}: could not load YAML: {exc}")
            continue
        if validate_document(validator, document, failure, path.stem):
            passed += 1

    total = len(FIXTURE_CASES)
    print(f"\nResult: {passed}/{total} checks passed")
    if passed == total:
        print("Schema validation PASSED.")
        return 0
    print("Schema validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
