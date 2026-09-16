from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator

# Repository-local tests only. Markdown is not a runtime serialization contract.
# Schema validity does not prove semantic/governance correctness.
REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "workflow.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "workflow"
CANONICAL_WORKFLOWS = [
    REPO_ROOT / "workflows" / "standard-change.md",
    REPO_ROOT / "workflows" / "architecture-change.md",
    REPO_ROOT / "workflows" / "security-sensitive-change.md",
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


NOTICE = (
    "This Workflow is declarative governance choreography. "
    "It does not select actors, grant permissions, or execute commands."
)
TOP_FIELDS = {"id", "name", "purpose", "applicable_task_types", "stages"}
STAGE_FIELDS = {
    "id", "purpose", "required_roles", "required_quality_gates",
    "human_control_checkpoint",
}


class WorkflowExtractionError(ValueError):
    """The current canonical Markdown cannot be projected without ambiguity."""


def code_string(text: str) -> str:
    # Delimiters, not an identifier naming grammar. No trimming of the value.
    match = re.fullmatch(r"\x60([^\x60]*)\x60", text)
    if match is None:
        raise WorkflowExtractionError("Expected one backtick-delimited scalar")
    return match[1]


def plain_string(text: str) -> str:
    # Current canonical prose is a single plain line; unsupported markup fails.
    if (
        not text or text != text.strip()
        or text[0] in "#-*+>0123456789"
        or any(char in text for char in "\x60*_[]<>")
    ):
        raise WorkflowExtractionError("Ambiguous plain scalar formatting")
    return text


def extract_stages(lines: list[str]) -> list[dict[str, Any]]:
    stages: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        heading = re.fullmatch(r"### Stage ([1-9][0-9]*): (\x60[^\x60]*\x60)", lines[index])
        if heading is None or int(heading[1]) != len(stages) + 1:
            raise WorkflowExtractionError("Malformed or inconsistent Stage numbering")
        heading_id = code_string(heading[2])
        index += 1
        stage: dict[str, Any] = {}
        while index < len(lines) and not lines[index].startswith("### "):
            field = re.fullmatch(r"- \*\*\x60([^\x60]+)\x60\*\*:(?: (.*))?", lines[index])
            if field is None:
                raise WorkflowExtractionError("Malformed Stage field or nested list")
            key, value = field[1], field[2]
            if key not in STAGE_FIELDS:
                raise WorkflowExtractionError("Unknown Stage field: " + key)
            if key in stage:
                raise WorkflowExtractionError("Duplicate Stage field: " + key)
            index += 1
            if key in {"required_roles", "required_quality_gates"}:
                if value is not None:
                    raise WorkflowExtractionError("Reference list must use nested bullets")
                items: list[str] = []
                while index < len(lines) and lines[index].startswith("  "):
                    item = re.fullmatch(r"  - (\x60[^\x60]*\x60)", lines[index])
                    if item is None:
                        raise WorkflowExtractionError("Malformed nested reference list")
                    items.append(code_string(item[1]))
                    index += 1
                if not items:
                    raise WorkflowExtractionError("Reference list has no explicit items")
                stage[key] = items
            else:
                if value is None:
                    raise WorkflowExtractionError("Missing Stage scalar value")
                if key == "id":
                    stage[key] = code_string(value)
                elif key == "purpose":
                    stage[key] = plain_string(value)
                else:
                    if value not in {"\x60true\x60", "\x60false\x60"}:
                        raise WorkflowExtractionError("Checkpoint must be literal true or false")
                    stage[key] = value == "\x60true\x60"
        if "id" not in stage:
            raise WorkflowExtractionError("Missing explicit Stage id")
        if stage["id"] != heading_id:
            raise WorkflowExtractionError("Stage heading/id mismatch")
        stages.append(stage)
    return stages


def extract_workflow_from_markdown(content: str) -> dict[str, Any]:
    """Strict test-only projection of the current canonical document structure.

    No defaults, inferred fields, reference resolution, or public parser contract.
    Formatting restrictions here are not normalized-object schema constraints.
    """
    lines = [line for line in content.splitlines() if line.strip()]
    if not lines or not lines[0].startswith("# "):
        raise WorkflowExtractionError("Missing canonical title")
    title = plain_string(lines[0][2:])
    if len(lines) < 3 or lines[-2:] != ["---", NOTICE]:
        raise WorkflowExtractionError("Missing or ambiguous canonical boundary notice")
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines[1:-2]:
        if line.startswith("## "):
            key = code_string(line[3:])
            if key not in TOP_FIELDS:
                raise WorkflowExtractionError("Unknown section: " + key)
            if key in sections:
                raise WorkflowExtractionError("Duplicate section: " + key)
            sections[key] = []
            current = key
        elif current is None:
            raise WorkflowExtractionError("Unexpected content before sections")
        else:
            sections[current].append(line)
    if "stages" not in sections or list(sections)[-1] != "stages":
        raise WorkflowExtractionError("Stages must be the final section")
    result: dict[str, Any] = {}
    for key, body in sections.items():
        if not body:
            raise WorkflowExtractionError("Empty section: " + key)
        if key == "stages":
            result[key] = extract_stages(body)
        elif key == "applicable_task_types":
            items = []
            for line in body:
                match = re.fullmatch(r"- (\x60[^\x60]*\x60)", line)
                if match is None:
                    raise WorkflowExtractionError("Malformed Task-type list")
                items.append(code_string(match[1]))
            result[key] = items
        else:
            if len(body) != 1:
                raise WorkflowExtractionError("Ambiguous multiline scalar: " + key)
            result[key] = code_string(body[0]) if key == "id" else plain_string(body[0])
    if "name" in result and title != result["name"]:
        raise WorkflowExtractionError("Title/name mismatch")
    return result


def semantic_uniqueness_errors(workflows: list[dict[str, Any]]) -> list[str]:
    """Repository semantic validation on schema-valid objects, not JSON Schema."""
    errors = []
    seen_workflows: set[str] = set()
    for workflow in workflows:
        workflow_id = workflow["id"]
        if workflow_id in seen_workflows:
            errors.append("Duplicate Workflow ID: " + workflow_id)
        seen_workflows.add(workflow_id)
        seen_stages: set[str] = set()
        for stage in workflow["stages"]:
            if stage["id"] in seen_stages:
                errors.append(f"Duplicate Stage ID in {workflow_id}: {stage['id']}")
            seen_stages.add(stage["id"])
    return errors


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
    errors = list(validator.iter_errors(document))
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


# Test literals intentionally use the current repository Markdown format only.
EXTRACTION_SAMPLE = """# Example
## \x60id\x60
\x60Example Workflow/1\x60
## \x60name\x60
Example
## \x60purpose\x60
Govern a change.
## \x60applicable_task_types\x60
- \x60custom/task\x60
## \x60stages\x60
### Stage 1: \x60Stage One\x60
- **\x60id\x60**: \x60Stage One\x60
- **\x60purpose\x60**: Implement.
- **\x60required_roles\x60**:
  - \x60custom/Role\x60
- **\x60required_quality_gates\x60**:
  - \x60custom.Gate\x60
- **\x60human_control_checkpoint\x60**: \x60false\x60
### Stage 2: \x60Stage Two\x60
- **\x60id\x60**: \x60Stage Two\x60
- **\x60purpose\x60**: Review.
- **\x60human_control_checkpoint\x60**: \x60true\x60
### Stage 3: \x60Finish\x60
- **\x60id\x60**: \x60Finish\x60
- **\x60purpose\x60**: Finish.
---
""" + NOTICE + "\n"

EXPECTED_PROJECTION = {
    "id": "Example Workflow/1", "name": "Example", "purpose": "Govern a change.",
    "applicable_task_types": ["custom/task"],
    "stages": [
        {"id": "Stage One", "purpose": "Implement.", "required_roles": ["custom/Role"],
         "required_quality_gates": ["custom.Gate"], "human_control_checkpoint": False},
        {"id": "Stage Two", "purpose": "Review.", "human_control_checkpoint": True},
        {"id": "Finish", "purpose": "Finish."},
    ],
}

# Each mutation must actually match the sample; failures check specific diagnostics.
EXTRACTION_FAILURE_CASES = [
    ("duplicate section", "## \x60name\x60", "## \x60id\x60", "Duplicate section"),
    ("unknown section", "## \x60name\x60", "## \x60actor\x60", "Unknown section"),
    ("duplicate Stage field", "- **\x60purpose\x60**: Implement.",
     "- **\x60id\x60**: \x60Stage One\x60", "Duplicate Stage field"),
    ("unknown Stage field", "- **\x60purpose\x60**: Implement.",
     "- **\x60actor\x60**: Human", "Unknown Stage field"),
    ("wrong nesting", "  - \x60custom/Role\x60", "    - \x60custom/Role\x60", "Malformed nested"),
    ("unnested list", "  - \x60custom/Role\x60", "- \x60custom/Role\x60", "no explicit items"),
    ("inline list", "- **\x60required_roles\x60**:", "- **\x60required_roles\x60**: []", "nested bullets"),
    ("multiline scalar", "Govern a change.", "Govern a change.\nExtra prose.", "multiline scalar"),
    ("numbering gap", "Stage 2:", "Stage 4:", "Stage numbering"),
    ("repeated number", "Stage 2:", "Stage 1:", "Stage numbering"),
    ("missing Stage id", "- **\x60id\x60**: \x60Stage One\x60\n", "", "Missing explicit Stage id"),
    ("heading mismatch", "Stage 1: \x60Stage One\x60", "Stage 1: \x60Different\x60", "heading/id mismatch"),
    ("nonliteral boolean", "\x60false\x60", "\x60False\x60", "literal true or false"),
    ("numeric boolean", "\x60false\x60", "\x600\x60", "literal true or false"),
    ("quoted boolean", "\x60false\x60", '"false"', "literal true or false"),
    ("ambiguous ID", "\x60Example Workflow/1\x60", "\x60one\x60 \x60two\x60", "backtick-delimited"),
    ("markup scalar", "Govern a change.", "**Govern a change.**", "Ambiguous plain scalar"),
    ("bad task list", "- \x60custom/task\x60", "  - \x60custom/task\x60", "Malformed Task-type"),
    ("unknown trailing prose", NOTICE, NOTICE + "\nUnknown prose.", "boundary notice"),
    ("missing notice", NOTICE, "", "boundary notice"),
    ("unexpected prefix", "## \x60id\x60", "Extra prose.\n## \x60id\x60", "before sections"),
    ("title mismatch", "# Example\n", "# Different\n", "Title/name mismatch"),
    ("empty section", "Govern a change.\n", "", "Empty section"),
]


def run_extraction_tests(validator: Draft202012Validator) -> list[bool]:
    results = []
    projection = extract_workflow_from_markdown(EXTRACTION_SAMPLE)
    exact = projection == EXPECTED_PROJECTION
    print(f"{'PASS' if exact else 'FAIL'} extraction exact values, order, booleans and omissions")
    results.append(exact)
    results.append(validate_document(validator, projection, "extraction sample schema"))
    without_optional = EXTRACTION_SAMPLE.replace(
        "## \x60applicable_task_types\x60\n- \x60custom/task\x60\n", ""
    )
    expected = {key: value for key, value in EXPECTED_PROJECTION.items()
                if key != "applicable_task_types"}
    omitted = extract_workflow_from_markdown(without_optional) == expected
    print(f"{'PASS' if omitted else 'FAIL'} extraction omitted optional top-level field")
    results.append(omitted)
    for name, old, new, message in EXTRACTION_FAILURE_CASES:
        if old not in EXTRACTION_SAMPLE:
            raise AssertionError("Extraction mutation does not match: " + name)
        try:
            extract_workflow_from_markdown(EXTRACTION_SAMPLE.replace(old, new, 1))
        except WorkflowExtractionError as error:
            passed = message in str(error)
        else:
            passed = False
        print(f"{'PASS' if passed else 'FAIL'} extraction rejection: {name}")
        results.append(passed)
    return results


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
        projections = []
        print("\nCanonical Markdown projections - structural validation")
        for path in CANONICAL_WORKFLOWS:
            projection = extract_workflow_from_markdown(path.read_text(encoding="utf-8"))
            valid = validate_document(validator, projection, str(path.relative_to(REPO_ROOT)))
            results.append(valid)
            if valid:
                projections.append(projection)

        print("\nExtraction tests")
        results.extend(run_extraction_tests(validator))

        print("\nRegistered structural fixtures")
        for name, failure in FIXTURE_CASES.items():
            results.append(validate_document(validator, load_yaml(FIXTURE_DIR / name), name, failure))

        print("\nRepository semantic validation - ID uniqueness only")
        errors = semantic_uniqueness_errors(projections)
        unique = len(projections) == len(CANONICAL_WORKFLOWS) and not errors
        print(f"{'PASS' if unique else 'FAIL'} IDs unique across inspected canonical definitions")
        for error in errors:
            print("  " + error)
        results.append(unique)
        duplicate_stages = load_yaml(FIXTURE_DIR / "valid-structurally-duplicate-stage-ids.yaml")
        semantic_cases = [
            ("duplicate Stage IDs rejected semantically", [duplicate_stages],
             ["Duplicate Stage ID in example: review"]),
            ("duplicate Workflow IDs rejected semantically",
             [EXPECTED_PROJECTION, EXPECTED_PROJECTION],
             ["Duplicate Workflow ID: Example Workflow/1"]),
            ("Stage IDs may repeat across different Workflows",
             [EXPECTED_PROJECTION, dict(EXPECTED_PROJECTION, id="other")], []),
        ]
        for label, documents, expected_errors in semantic_cases:
            passed = semantic_uniqueness_errors(documents) == expected_errors
            print(f"{'PASS' if passed else 'FAIL'} {label}")
            results.append(passed)
        print("Role/Quality Gate existence: manual review; NOT established by this validator.")
    except Exception as error:
        print(f"FAIL validation could not complete: {type(error).__name__}: {error}")
        return 1
    print(f"\nResult: {sum(results)}/{len(results)} checks passed")
    print("Workflow validation " + ("PASSED." if all(results) else "FAILED."))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
