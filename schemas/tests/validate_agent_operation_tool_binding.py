from __future__ import annotations

from collections import Counter
from contextlib import ExitStack
import json
import socket
import sys
from pathlib import Path
from typing import Any, NamedTuple
import urllib.request
from unittest.mock import patch

from jsonschema import Draft202012Validator
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
    validate_agent_operation_tool_binding,
)
from engineering_orchestration.schema_resources import (
    load_validator,
    schema_resource,
)


BINDING_SCHEMA_NAME = "agent-operation-tool-binding.schema.json"
RUN_SCHEMA_NAME = "agent-execution-run.schema.json"
CONTRACT_SCHEMA_NAME = "agent-execution-contract.schema.json"
BINDING_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-operation-tool-binding.schema.json"
)
RUN_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-run.schema.json"
)
CONTRACT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-contract.schema.json"
)
FIXTURE_DIR = (
    REPO_ROOT / "schemas" / "tests" / "agent-operation-tool-binding"
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
        f"valid-{name}.yaml": FixtureExpectation()
        for name in (
            "case-sensitive-tool-id",
            "deep",
            "minimal",
            "versioned-tool-id",
            "whitespace-tool-id",
        )
    },
    "invalid-missing-run.yaml": FixtureExpectation(
        _one("required", (), "run")
    ),
    "invalid-missing-tool-id.yaml": FixtureExpectation(
        _one("required", (), "tool_id")
    ),
    "invalid-empty-tool-id.yaml": FixtureExpectation(
        _one("minLength", ("tool_id",))
    ),
    "invalid-tool-id-type.yaml": FixtureExpectation(
        _one("type", ("tool_id",))
    ),
    "invalid-run-type.yaml": FixtureExpectation(_one("type", ("run",))),
    "invalid-run-missing-run-id.yaml": FixtureExpectation(
        _one("required", ("run",), "run_id")
    ),
    "invalid-run-empty-run-id.yaml": FixtureExpectation(
        _one("minLength", ("run", "run_id"))
    ),
    "invalid-run-missing-contract.yaml": FixtureExpectation(
        _one("required", ("run",), "contract")
    ),
    "invalid-run-contract-type.yaml": FixtureExpectation(
        _one("type", ("run", "contract"))
    ),
    "invalid-run-contract-missing-task-id.yaml": FixtureExpectation(
        _one("required", ("run", "contract"), "task_id")
    ),
    "invalid-run-contract-extra-provider-id.yaml": FixtureExpectation(
        _one("additionalProperties", ("run", "contract"))
    ),
    "invalid-run-contract-execution-mode.yaml": FixtureExpectation(
        _one("enum", ("run", "contract", "execution_mode"))
    ),
    "invalid-run-contract-unsupported-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_not_supported"
    ),
    "invalid-run-contract-parent-resource.yaml": FixtureExpectation(
        semantic_finding="resource_parent_segment"
    ),
    "invalid-extra-execution-fields.yaml": FixtureExpectation(
        _one("additionalProperties", ())
    ),
    "invalid-root-type.yaml": FixtureExpectation(_one("type", ())),
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


def check_schema_contract() -> bool:
    try:
        binding_resource = schema_resource(BINDING_SCHEMA_NAME)
        run_resource = schema_resource(RUN_SCHEMA_NAME)
        contract_resource = schema_resource(CONTRACT_SCHEMA_NAME)
        if (
            binding_resource is None
            or run_resource is None
            or contract_resource is None
        ):
            raise FileNotFoundError(
                "Binding, Run, or Contract schema resource is missing"
            )
        binding_schema = json.loads(
            binding_resource.read_text(encoding="utf-8")
        )
        run_schema = json.loads(run_resource.read_text(encoding="utf-8"))
        contract_schema = json.loads(
            contract_resource.read_text(encoding="utf-8")
        )
    except Exception as exc:
        print(f"FAIL schema resource load: {exc}")
        return False

    properties = binding_schema.get("properties", {})
    passed = (
        binding_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
        and binding_schema.get("$id") == BINDING_SCHEMA_ID
        and binding_schema.get("type") == "object"
        and binding_schema.get("additionalProperties") is False
        and binding_schema.get("required") == ["run", "tool_id"]
        and list(properties) == ["run", "tool_id"]
        and properties.get("run", {}).get("$ref") == RUN_SCHEMA_ID
        and properties.get("tool_id", {}).get("type") == "string"
        and properties.get("tool_id", {}).get("minLength") == 1
        and run_schema.get("$id") == RUN_SCHEMA_ID
        and run_schema.get("properties", {}).get("contract", {}).get("$ref")
        == CONTRACT_SCHEMA_ID
        and contract_schema.get("$id") == CONTRACT_SCHEMA_ID
    )
    print(
        f"{'PASS' if passed else 'FAIL'} schema contract: closed ordered "
        "two-field Tool Binding and exact packaged Run/Contract chain"
    )
    return passed


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


def _binding_from_document(document: dict[str, Any]) -> AgentOperationToolBinding:
    run_document = document["run"]
    return AgentOperationToolBinding(
        run=AgentExecutionRun(
            run_id=run_document["run_id"],
            contract=AgentExecutionContract(**run_document["contract"]),
        ),
        tool_id=document["tool_id"],
    )


def semantic_result(
    document: dict[str, Any],
    expected_finding: str | None,
    label: str,
) -> bool:
    binding = _binding_from_document(document)
    result = validate_agent_operation_tool_binding(binding)
    if expected_finding is None:
        passed = (
            result.valid
            and result.findings == ()
            and result.binding is binding
        )
        expectation = "semantically valid"
    else:
        passed = (
            not result.valid
            and [finding.code for finding in result.findings]
            == [expected_finding]
            and result.binding is None
        )
        expectation = f"semantic finding {expected_finding}"
    print(f"{'PASS' if passed else 'FAIL'} {label} semantic: {expectation}")
    if not passed:
        print(
            "  - actual: "
            f"valid={result.valid}, "
            f"findings={[item.code for item in result.findings]}, "
            f"binding={result.binding!r}"
        )
    return passed


class NetworkAccessAttempted(RuntimeError):
    pass


def main() -> int:
    print("AI Engineering Orchestra - Agent Operation Tool Binding Validation")
    print("=" * 72)
    if not check_fixture_coverage() or not check_schema_contract():
        return 1

    blocked_network = NetworkAccessAttempted(
        "schema resolution attempted network access"
    )
    guards = (
        patch.object(socket, "create_connection", side_effect=blocked_network),
        patch.object(socket, "getaddrinfo", side_effect=blocked_network),
        patch.object(urllib.request, "urlopen", side_effect=blocked_network),
        patch(
            "pathlib.Path.cwd",
            side_effect=AssertionError("schema resolution consulted CWD"),
        ),
    )

    structural_passed = 0
    semantic_passed = 0
    semantic_total = 0
    try:
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            validator = load_validator(BINDING_SCHEMA_NAME)
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

            unknown = validator.evolve(
                schema={
                    "$ref": "https://example.invalid/unregistered.schema.json"
                }
            )
            try:
                unknown.validate({})
            except NetworkAccessAttempted:
                print("FAIL unregistered reference attempted network access")
                return 1
            except Exception:
                print("PASS unregistered reference failed closed without network")
            else:
                print("FAIL unregistered reference unexpectedly resolved")
                return 1
    except Exception as exc:
        print(f"FAIL schema load, resolution, or validation: {exc}")
        return 1

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
        print("Agent Operation Tool Binding validation PASSED.")
        return 0
    print("Agent Operation Tool Binding validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
