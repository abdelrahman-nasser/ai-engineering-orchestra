from __future__ import annotations

from collections import Counter
from contextlib import ExitStack
import json
from pathlib import Path
import socket
import sys
from typing import Any, NamedTuple
import urllib.request
from unittest.mock import patch

from jsonschema import Draft202012Validator
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
    validate_agent_execution_dispatch_admission,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
from engineering_orchestration.schema_resources import (
    load_validator,
    schema_resource,
)


ADMISSION_SCHEMA_NAME = "agent-execution-dispatch-admission.schema.json"
GRANT_SCHEMA_NAME = "agent-execution-authorization-grant.schema.json"
BINDING_SCHEMA_NAME = "agent-operation-tool-binding.schema.json"
RUN_SCHEMA_NAME = "agent-execution-run.schema.json"
CONTRACT_SCHEMA_NAME = "agent-execution-contract.schema.json"
ADMISSION_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-dispatch-admission.schema.json"
)
GRANT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-authorization-grant.schema.json"
)
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
DECISION_PATTERN = (
    r"^(?!0000)[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):"
    r"[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z(?![\s\S])"
)
FIXTURE_DIR = (
    REPO_ROOT
    / "schemas"
    / "tests"
    / "fixtures"
    / "agent-execution-dispatch-admission"
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
    "valid-inclusive.yaml": FixtureExpectation(),
    "valid-midpoint.yaml": FixtureExpectation(),
    "invalid-binding-extra.yaml": FixtureExpectation(
        _one("additionalProperties", ("tool_binding",))
    ),
    "invalid-decision-calendar.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_dispatch_admission_decision_time_invalid"
        )
    ),
    "invalid-decision-no-fraction.yaml": FixtureExpectation(
        _one("pattern", ("decision_time",))
    ),
    "invalid-expiry-boundary.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_dispatch_admission_currentness_invalid"
        )
    ),
    "invalid-extra-admission-id.yaml": FixtureExpectation(
        _one("additionalProperties", ())
    ),
    "invalid-grant-extra.yaml": FixtureExpectation(
        _one("additionalProperties", ("grant",))
    ),
    "invalid-missing-tool-binding.yaml": FixtureExpectation(
        _one("required", (), "tool_binding")
    ),
    "invalid-root-type.yaml": FixtureExpectation(_one("type", ())),
    "invalid-run-mismatch.yaml": FixtureExpectation(
        semantic_finding="agent_execution_dispatch_admission_run_mismatch"
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


def _load_schema(name: str) -> dict[str, Any]:
    resource = schema_resource(name)
    if resource is None:
        raise FileNotFoundError(f"Required schema resource missing: {name}")
    document = json.loads(resource.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TypeError(f"Schema resource must contain an object: {name}")
    return document


def check_schema_contract() -> bool:
    try:
        admission_schema = _load_schema(ADMISSION_SCHEMA_NAME)
        grant_schema = _load_schema(GRANT_SCHEMA_NAME)
        binding_schema = _load_schema(BINDING_SCHEMA_NAME)
        run_schema = _load_schema(RUN_SCHEMA_NAME)
        contract_schema = _load_schema(CONTRACT_SCHEMA_NAME)
    except Exception as exc:
        print(f"FAIL schema resource load: {exc}")
        return False

    properties = admission_schema.get("properties", {})
    passed = (
        admission_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
        and admission_schema.get("$id") == ADMISSION_SCHEMA_ID
        and admission_schema.get("type") == "object"
        and admission_schema.get("additionalProperties") is False
        and admission_schema.get("required")
        == ["grant", "tool_binding", "decision_time"]
        and list(properties) == ["grant", "tool_binding", "decision_time"]
        and properties.get("grant", {}).get("$ref") == GRANT_SCHEMA_ID
        and properties.get("tool_binding", {}).get("$ref")
        == BINDING_SCHEMA_ID
        and properties.get("decision_time", {}).get("pattern")
        == DECISION_PATTERN
        and grant_schema.get("$id") == GRANT_SCHEMA_ID
        and grant_schema.get("properties", {}).get("run", {}).get("$ref")
        == RUN_SCHEMA_ID
        and binding_schema.get("$id") == BINDING_SCHEMA_ID
        and binding_schema.get("properties", {}).get("run", {}).get("$ref")
        == RUN_SCHEMA_ID
        and run_schema.get("$id") == RUN_SCHEMA_ID
        and run_schema.get("properties", {}).get("contract", {}).get("$ref")
        == CONTRACT_SCHEMA_ID
        and contract_schema.get("$id") == CONTRACT_SCHEMA_ID
    )
    print(
        f"{'PASS' if passed else 'FAIL'} schema contract: closed ordered "
        "three-field Admission and exact packaged Grant/Binding/Run/Contract "
        "reference graph"
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
        if matches and isinstance(matches[0].instance, dict):
            passed = passed and (
                set(matches[0].validator_value) - set(matches[0].instance)
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


def _run_from_document(document: dict[str, Any]) -> AgentExecutionRun:
    return AgentExecutionRun(
        run_id=document["run_id"],
        contract=AgentExecutionContract(**document["contract"]),
    )


def _admission_from_document(
    document: dict[str, Any],
) -> AgentExecutionDispatchAdmission:
    grant_document = document["grant"]
    binding_document = document["tool_binding"]
    grant_run = _run_from_document(grant_document["run"])
    binding_run = _run_from_document(binding_document["run"])
    return AgentExecutionDispatchAdmission(
        grant=AgentExecutionAuthorizationGrant(
            grant_id=grant_document["grant_id"],
            run=grant_run,
            authorization_domain_id=grant_document[
                "authorization_domain_id"
            ],
            issuer_kind=grant_document["issuer_kind"],
            issuer_id=grant_document["issuer_id"],
            provenance_reference=grant_document["provenance_reference"],
            issued_at=grant_document["issued_at"],
            expires_at=grant_document["expires_at"],
        ),
        tool_binding=AgentOperationToolBinding(
            run=binding_run,
            tool_id=binding_document["tool_id"],
        ),
        decision_time=document["decision_time"],
    )


def semantic_result(
    document: dict[str, Any],
    expected_finding: str | None,
    label: str,
) -> bool:
    admission = _admission_from_document(document)
    result = validate_agent_execution_dispatch_admission(admission)
    if expected_finding is None:
        passed = (
            result.valid
            and result.findings == ()
            and result.admission is admission
        )
        expectation = "semantically valid"
    else:
        passed = (
            not result.valid
            and [item.code for item in result.findings]
            == [expected_finding]
            and result.admission is None
        )
        expectation = f"semantic finding {expected_finding}"
    print(f"{'PASS' if passed else 'FAIL'} {label} semantic: {expectation}")
    if not passed:
        print(
            "  - actual: "
            f"valid={result.valid}, "
            f"findings={[item.code for item in result.findings]}, "
            f"admission={result.admission!r}"
        )
    return passed


class NetworkAccessAttempted(RuntimeError):
    pass


def main() -> int:
    print("AI Engineering Orchestra - Agent Execution Dispatch Admission Validation")
    print("=" * 80)
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
            validator = load_validator(ADMISSION_SCHEMA_NAME)
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
                    "$ref": "https://example.invalid/unknown.schema.json"
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
        print("Agent Execution Dispatch Admission validation PASSED.")
        return 0
    print("Agent Execution Dispatch Admission validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
