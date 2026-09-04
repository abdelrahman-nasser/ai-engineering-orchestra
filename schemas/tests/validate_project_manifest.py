from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "project-manifest.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "project-manifest"

CANONICAL_VALID_MANIFESTS = [
    REPO_ROOT / "templates" / "project.yaml",
    REPO_ROOT / ".ai" / "project.yaml",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def format_error(error) -> str:
    location = ".".join(str(part) for part in error.absolute_path)
    location = location or "<root>"
    return f"{location}: {error.message}"


def validate_manifest(
    validator: Draft202012Validator,
    path: Path,
    expected_valid: bool,
) -> bool:
    try:
        manifest = load_yaml(path)
    except Exception as exc:
        print(f"FAIL  {path.relative_to(REPO_ROOT)}")
        print(f"      Unable to parse YAML: {exc}")
        return False

    errors = sorted(
        validator.iter_errors(manifest),
        key=lambda error: list(error.absolute_path),
    )

    actual_valid = not errors
    passed = actual_valid == expected_valid

    expectation = "valid" if expected_valid else "invalid"

    if passed:
        print(
            f"PASS  {path.relative_to(REPO_ROOT)} "
            f"(expected {expectation})"
        )
        return True

    print(
        f"FAIL  {path.relative_to(REPO_ROOT)} "
        f"(expected {expectation})"
    )

    if errors:
        for error in errors:
            print(f"      {format_error(error)}")
    else:
        print("      Manifest unexpectedly passed schema validation.")

    return False


def main() -> int:
    schema = load_json(SCHEMA_PATH)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    cases: list[tuple[Path, bool]] = []

    for path in CANONICAL_VALID_MANIFESTS:
        cases.append((path, True))

    for path in sorted(FIXTURE_DIR.glob("valid-*.yaml")):
        cases.append((path, True))

    for path in sorted(FIXTURE_DIR.glob("invalid-*.yaml")):
        cases.append((path, False))

    if not cases:
        print("No validation cases were found.")
        return 1

    print("AI Engineering Orchestra - Project Manifest Schema Validation")
    print("=" * 67)

    passed = 0

    for path, expected_valid in cases:
        if validate_manifest(validator, path, expected_valid):
            passed += 1

    total = len(cases)

    print()
    print(f"Result: {passed}/{total} cases passed")

    if passed != total:
        print("Schema validation FAILED.")
        return 1

    print("Schema validation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
