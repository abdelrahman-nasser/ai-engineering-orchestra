from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
    validate_agent_execution_contract,
)


SCHEMA_PATH = REPO_ROOT / "schemas" / "agent-execution-contract.schema.json"
FIXTURE_DIR = REPO_ROOT / "schemas" / "tests" / "agent-execution-contract"

FIELDS = (
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
    "execution_mode",
)
EXCLUDED_FIELDS = (
    "tool_id",
    "adapter_id",
    "provider_id",
    "payload",
    "parameters",
    "contract_id",
    "run_id",
    "status",
    "result",
    "error",
    "created_at",
    "started_at",
    "completed_at",
    "authority_id",
    "authorization_state",
    "permission_state",
)


class ExpectedStructuralFailure(NamedTuple):
    keyword: str
    path: tuple[str | int, ...]
    missing_property: str | None = None


class FixtureExpectation(NamedTuple):
    structural_failures: tuple[ExpectedStructuralFailure, ...] = ()
    semantic_finding: str | None = None


def _one(
    keyword: str,
    path: tuple[str | int, ...],
    missing_property: str | None = None,
) -> tuple[ExpectedStructuralFailure, ...]:
    return (ExpectedStructuralFailure(keyword, path, missing_property),)


FIXTURE_CASES: dict[str, FixtureExpectation] = {
    **{
        f"valid-{mode}.yaml": FixtureExpectation()
        for mode in ("lite", "standard", "deep", "critical")
    },
    **{
        f"invalid-missing-{field.replace('_', '-')}.yaml": FixtureExpectation(
            _one("required", (), field)
        )
        for field in FIELDS
    },
    **{
        f"invalid-empty-{field.replace('_', '-')}.yaml": FixtureExpectation(
            (
                ExpectedStructuralFailure("minLength", (field,)),
                *(
                    (ExpectedStructuralFailure("enum", (field,)),)
                    if field == "execution_mode"
                    else ()
                ),
            )
        )
        for field in FIELDS
    },
    **{
        f"invalid-{field.replace('_', '-')}-type.yaml": FixtureExpectation(
            (
                ExpectedStructuralFailure("type", (field,)),
                *(
                    (ExpectedStructuralFailure("enum", (field,)),)
                    if field == "execution_mode"
                    else ()
                ),
            )
        )
        for field in FIELDS
    },
    "invalid-execution-mode.yaml": FixtureExpectation(
        _one("enum", ("execution_mode",))
    ),
    **{
        f"invalid-extra-{field.replace('_', '-')}.yaml": FixtureExpectation(
            _one("additionalProperties", ())
        )
        for field in EXCLUDED_FIELDS
    },
    "invalid-root-type.yaml": FixtureExpectation(_one("type", ())),
    "invalid-malformed-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_invalid_syntax"
    ),
    "invalid-unsupported-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_not_supported"
    ),
    "invalid-resource-control.yaml": FixtureExpectation(
        semantic_finding="resource_control_character"
    ),
    "invalid-resource-unc.yaml": FixtureExpectation(
        semantic_finding="resource_unc_path"
    ),
    "invalid-resource-absolute.yaml": FixtureExpectation(
        semantic_finding="resource_absolute_path"
    ),
    "invalid-resource-drive.yaml": FixtureExpectation(
        semantic_finding="resource_drive_qualified_path"
    ),
    "invalid-resource-uri.yaml": FixtureExpectation(
        semantic_finding="resource_uri_scheme"
    ),
    "invalid-resource-tilde.yaml": FixtureExpectation(
        semantic_finding="resource_leading_tilde"
    ),
    "invalid-resource-backslash.yaml": FixtureExpectation(
        semantic_finding="resource_backslash"
    ),
    "invalid-resource-trailing-slash.yaml": FixtureExpectation(
        semantic_finding="resource_trailing_slash"
    ),
    "invalid-resource-empty-segment.yaml": FixtureExpectation(
        semantic_finding="resource_empty_segment"
    ),
    "invalid-resource-dot-segment.yaml": FixtureExpectation(
        semantic_finding="resource_dot_segment"
    ),
    "invalid-resource-parent-segment.yaml": FixtureExpectation(
        semantic_finding="resource_parent_segment"
    ),
    "invalid-resource-glob-meta.yaml": FixtureExpectation(
        semantic_finding="resource_glob_meta"
    ),
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
        for name, expectation in FIXTURE_CASES.items()
        if not name.startswith(
            "valid-"
            if not expectation.structural_failures
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
    expected: tuple[ExpectedStructuralFailure, ...],
    label: str,
) -> bool:
    errors = list(validator.iter_errors(document))
    actual_keys = Counter(
        (str(error.validator), tuple(error.absolute_path)) for error in errors
    )
    expected_keys = Counter((item.keyword, item.path) for item in expected)
    passed = actual_keys == expected_keys
    for item in expected:
        if item.missing_property is None:
            continue
        matches = [
            error
            for error in errors
            if error.validator == item.keyword
            and tuple(error.absolute_path) == item.path
        ]
        passed = passed and len(matches) == 1
        if matches:
            error = matches[0]
            passed = passed and isinstance(error.instance, dict)
            if isinstance(error.instance, dict):
                passed = passed and (
                    set(error.validator_value) - set(error.instance)
                    == {item.missing_property}
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
    contract = AgentExecutionContract(**document)
    result = validate_agent_execution_contract(contract)
    if expected_finding is None:
        passed = result.valid and result.findings == () and result.contract is contract
        expectation = "semantically valid"
    else:
        passed = (
            not result.valid
            and [finding.code for finding in result.findings]
            == [expected_finding]
            and result.contract is None
        )
        expectation = f"semantic finding {expected_finding}"
    print(f"{'PASS' if passed else 'FAIL'} {label} semantic: {expectation}")
    if not passed:
        print(
            "  - actual: "
            f"valid={result.valid}, "
            f"findings={[item.code for item in result.findings]}, "
            f"contract={result.contract!r}"
        )
    return passed


def main() -> int:
    print("AI Engineering Orchestra - Agent Execution Contract Validation")
    print("=" * 68)
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
            expectation.structural_failures,
            path.stem,
        )
        if structurally_correct:
            structural_passed += 1

        if not expectation.structural_failures:
            semantic_total += 1
            if (
                structurally_correct
                and isinstance(document, dict)
                and semantic_result(
                    document,
                    expectation.semantic_finding,
                    path.stem,
                )
            ):
                semantic_passed += 1

    structural_total = len(FIXTURE_CASES)
    print(
        f"\nStructural result: {structural_passed}/{structural_total} fixtures passed"
    )
    print(f"Semantic result: {semantic_passed}/{semantic_total} fixtures passed")
    if (
        structural_passed == structural_total
        and semantic_passed == semantic_total
    ):
        print("Agent Execution Contract validation PASSED.")
        return 0
    print("Agent Execution Contract validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
