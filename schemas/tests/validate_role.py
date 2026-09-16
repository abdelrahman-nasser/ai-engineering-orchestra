from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator

# Architectural Boundary Notice:
# AIO-007 validates a normalized in-memory projection of the current canonical
# Markdown Role definitions. It does not establish Markdown as the future runtime
# Role serialization format.
#
# Schema-valid does not imply semantically valid, useful, recommended, or review-approved.
# Semantic review remains responsible for determining whether Role responsibilities and
# capabilities satisfy the AIO-006 contract.

REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = REPO_ROOT / "schemas" / "role.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "role"

CANONICAL_ROLES = [
    REPO_ROOT / "roles" / "architect.md",
    REPO_ROOT / "roles" / "documentation-specialist.md",
    REPO_ROOT / "roles" / "reviewer.md",
    REPO_ROOT / "roles" / "security-reviewer.md",
    REPO_ROOT / "roles" / "software-engineer.md",
]


class ExpectedFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


class RoleExtractionError(Exception):
    """Raised when canonical Role Markdown cannot be safely extracted."""
    pass


# Fixture cases registry.
# None indicates valid; ExpectedFailure specifies exact expected violation.
FIXTURE_CASES: dict[str, ExpectedFailure | None] = {
    # Valid cases
    "valid-minimal.yaml": None,
    "valid-full.yaml": None,
    "valid-structurally-empty-required-arrays.yaml": None,
    "valid-structurally-empty-optional-array.yaml": None,
    "valid-structurally-duplicate-items.yaml": None,
    # Invalid cases
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
    "invalid-schema-version-present.yaml": ExpectedFailure(
        "additionalProperties", ()
    ),
    "invalid-empty-id.yaml": ExpectedFailure("minLength", ("id",)),
    "invalid-empty-name.yaml": ExpectedFailure("minLength", ("name",)),
    "invalid-empty-purpose.yaml": ExpectedFailure("minLength", ("purpose",)),
    "invalid-responsibilities-type.yaml": ExpectedFailure(
        "type", ("responsibilities",)
    ),
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

EXTRACTION_FAILURE_CASES: list[tuple[str, str, str]] = [
    (
        "duplicate_section",
        "# Role\n## `id`\n`r1`\n## `name`\nName\n## `purpose`\nP1\n## `purpose`\nP2\n## `responsibilities`\n- r1\n## `required_capabilities`\n- c1\n",
        "Duplicate section heading",
    ),
    (
        "unknown_section",
        "# Role\n## `id`\n`r1`\n## `name`\nName\n## `purpose`\nP1\n## `responsibilities`\n- r1\n## `required_capabilities`\n- c1\n## `unknown`\n- u1\n",
        "Unknown section heading",
    ),
    (
        "empty_section",
        "# Role\n## `id`\n## `name`\nName\n## `purpose`\nP1\n## `responsibilities`\n- r1\n## `required_capabilities`\n- c1\n",
        "has no content",
    ),
    (
        "multiline_id",
        "# Role\n## `id`\n`line1`\n`line2`\n## `name`\nName\n## `purpose`\nP1\n## `responsibilities`\n- r1\n## `required_capabilities`\n- c1\n",
        "must be a single line",
    ),
    (
        "prose_before_bullets",
        "# Role\n## `id`\n`r1`\n## `name`\nName\n## `purpose`\nP1\n## `responsibilities`\nprose here\n- r1\n## `required_capabilities`\n- c1\n",
        "contains non-bullet line before bullet items",
    ),
    (
        "bullet_after_prose",
        "# Role\n## `id`\n`r1`\n## `name`\nName\n## `purpose`\nP1\n## `responsibilities`\n- r1\nprose here\n- r2\n## `required_capabilities`\n- c1\n",
        "contains bullet item after non-bullet text",
    ),
    (
        "no_valid_sections",
        "# Just a title\nSome random content without sections.\n",
        "No valid Role sections found",
    ),
]

ALLOWED_SECTIONS = {
    "id",
    "name",
    "purpose",
    "responsibilities",
    "required_capabilities",
    "applicable_task_types",
}


def extract_role_from_markdown(content: str) -> dict[str, Any]:
    """Test-only repository-local extractor for canonical Role Markdown.

    Limited strictly to current canonical Role structure.
    Does NOT infer missing values or supply defaults.
    Fails visibly on duplicate or ambiguous sections.
    """
    lines = content.splitlines()

    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            header_text = stripped[3:].strip()
            # Normalize heading: e.g. `id` or id
            clean_header = header_text.strip("`").strip()
            if clean_header not in ALLOWED_SECTIONS:
                raise RoleExtractionError(
                    f"Unknown section heading: '{raw_line}'"
                )
            if clean_header in sections:
                raise RoleExtractionError(
                    f"Duplicate section heading: '{raw_line}'"
                )
            current_section = clean_header
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(raw_line)

    if not sections:
        raise RoleExtractionError("No valid Role sections found in Markdown document")

    extracted: dict[str, Any] = {}

    for sec_name, sec_lines in sections.items():
        non_blank = [l.strip() for l in sec_lines if l.strip()]
        if not non_blank:
            raise RoleExtractionError(f"Section '{sec_name}' has no content")

        if sec_name in ("id", "name"):
            if len(non_blank) != 1:
                raise RoleExtractionError(
                    f"Section '{sec_name}' must be a single line, found {len(non_blank)}"
                )
            val = non_blank[0]
            if sec_name == "id":
                val = val.strip("`").strip()
            if not val:
                raise RoleExtractionError(f"Section '{sec_name}' has empty value")
            extracted[sec_name] = val

        elif sec_name == "purpose":
            # Canonical purpose is a concise statement; join wrapped paragraph lines
            extracted["purpose"] = " ".join(non_blank)

        elif sec_name in ("responsibilities", "required_capabilities", "applicable_task_types"):
            items: list[str] = []
            in_trailing_text = False
            for l in sec_lines:
                s = l.strip()
                if not s:
                    continue
                if s.startswith("- "):
                    if in_trailing_text:
                        raise RoleExtractionError(
                            f"Section '{sec_name}' contains bullet item after non-bullet text: '{s}'"
                        )
                    item_val = s[2:].strip()
                    items.append(item_val)
                else:
                    if not items:
                        raise RoleExtractionError(
                            f"Section '{sec_name}' contains non-bullet line before bullet items: '{s}'"
                        )
                    in_trailing_text = True

            if not items:
                raise RoleExtractionError(f"Section '{sec_name}' contains no items")
            extracted[sec_name] = items

    return extracted


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


def validate_document(
    validator: Draft202012Validator,
    document: Any,
    expected_valid: bool,
    label: str,
    expected_failure: ExpectedFailure | None = None,
) -> bool:
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


def run_extraction_failure_tests() -> bool:
    passed = 0
    total = len(EXTRACTION_FAILURE_CASES)
    for name, content, expected_msg in EXTRACTION_FAILURE_CASES:
        try:
            extract_role_from_markdown(content)
            print(f"FAIL extraction failure test '{name}': expected error but extraction succeeded")
        except RoleExtractionError as exc:
            if expected_msg in str(exc):
                print(f"PASS extraction failure test '{name}' raised expected error: {exc}")
                passed += 1
            else:
                print(
                    f"FAIL extraction failure test '{name}': error message '{exc}' did not contain '{expected_msg}'"
                )
        except Exception as exc:
            print(f"FAIL extraction failure test '{name}': unexpected exception type: {type(exc).__name__}: {exc}")

    return passed == total


def main() -> int:
    print("AI Engineering Orchestra - Role Schema Validation")
    print("=" * 63)

    # Optional self-test for nonzero exit behavior demonstration
    if "--test-mismatch" in sys.argv:
        print("Self-test mismatch requested: simulating unexpected validation failure.")
        print("FAIL simulated-mismatch: expected valid but validation failed")
        print("Schema validation FAILED.")
        return 1

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

    total_checks = 0
    passed_checks = 0

    # 1. Validate Canonical Role Markdown Projections
    print("\n--- Canonical Role Markdown Projections ---")
    for path in CANONICAL_ROLES:
        total_checks += 1
        label = str(path.relative_to(REPO_ROOT))
        if not path.exists():
            print(f"FAIL {label}: file does not exist")
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                content = f.read()
            projection = extract_role_from_markdown(content)
        except Exception as exc:
            print(f"FAIL {label}: extraction error: {exc}")
            continue

        if validate_document(validator, projection, expected_valid=True, label=label):
            passed_checks += 1

    # 2. Test Extraction Failure Cases
    print("\n--- Extraction Failure Tests ---")
    if run_extraction_failure_tests():
        passed_checks += len(EXTRACTION_FAILURE_CASES)
    total_checks += len(EXTRACTION_FAILURE_CASES)

    # 3. Validate Fixtures (Valid & Invalid)
    print("\n--- Fixture Cases ---")
    for name, failure in sorted(FIXTURE_CASES.items()):
        total_checks += 1
        path = FIXTURE_DIR / name
        label = path.stem
        if not path.exists():
            print(f"FAIL {label}: file does not exist")
            continue

        try:
            document = load_yaml(path)
        except Exception as exc:
            print(f"FAIL {label}: could not load YAML: {exc}")
            continue

        if validate_document(
            validator=validator,
            document=document,
            expected_valid=failure is None,
            label=label,
            expected_failure=failure,
        ):
            passed_checks += 1

    print()
    print(f"Result: {passed_checks}/{total_checks} checks passed")

    if passed_checks == total_checks:
        print("Schema validation PASSED.")
        return 0

    print("Schema validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

