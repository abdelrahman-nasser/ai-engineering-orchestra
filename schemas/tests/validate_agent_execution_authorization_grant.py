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

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    validate_agent_execution_authorization_grant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.schema_resources import (
    load_validator,
    schema_resource,
)


GRANT_SCHEMA_NAME = "agent-execution-authorization-grant.schema.json"
RUN_SCHEMA_NAME = "agent-execution-run.schema.json"
CONTRACT_SCHEMA_NAME = "agent-execution-contract.schema.json"
GRANT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-authorization-grant.schema.json"
)
RUN_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-run.schema.json"
)
CONTRACT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-contract.schema.json"
)
TIMESTAMP_PATTERN = (
    r"^(?!0000)[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):"
    r"[0-5][0-9]:[0-5][0-9](?:\.[0-9]{1,6})?Z(?![\s\S])"
)
FIXTURE_DIR = (
    REPO_ROOT
    / "schemas"
    / "tests"
    / "agent-execution-authorization-grant"
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
            "fractional",
            "human",
            "leap-day",
            "nested-run",
            "policy",
        )
    },
    **{
        f"invalid-missing-{field.replace('_', '-')}.yaml": FixtureExpectation(
            _one("required", (), field)
        )
        for field in (
            "grant_id",
            "run",
            "authorization_domain_id",
            "issuer_kind",
            "issuer_id",
            "provenance_reference",
            "issued_at",
            "expires_at",
        )
    },
    **{
        f"invalid-empty-{field.replace('_', '-')}.yaml": FixtureExpectation(
            _one("minLength", (field,))
        )
        for field in (
            "grant_id",
            "authorization_domain_id",
            "issuer_id",
            "provenance_reference",
        )
    },
    **{
        f"invalid-{field.replace('_', '-')}-type.yaml": FixtureExpectation(
            _one("type", (field,))
        )
        for field in (
            "grant_id",
            "run",
            "authorization_domain_id",
            "issuer_id",
            "provenance_reference",
            "issued_at",
            "expires_at",
        )
    },
    "invalid-issuer-kind-type.yaml": FixtureExpectation(
        (
            ExpectedStructuralFailure("type", ("issuer_kind",)),
            ExpectedStructuralFailure("enum", ("issuer_kind",)),
        )
    ),
    "invalid-issuer-kind-value.yaml": FixtureExpectation(
        _one("enum", ("issuer_kind",))
    ),
    **{
        f"invalid-{name}.yaml": FixtureExpectation(
            _one("pattern", (field,))
        )
        for name, field in (
            ("issued-at-lowercase-t", "issued_at"),
            ("issued-at-lowercase-z", "issued_at"),
            ("issued-at-offset", "issued_at"),
            ("issued-at-no-seconds", "issued_at"),
            ("issued-at-empty-fraction", "issued_at"),
            ("issued-at-seven-fraction", "issued_at"),
            ("issued-at-trailing-newline", "issued_at"),
            ("issued-at-year-zero", "issued_at"),
            ("expires-at-hour", "expires_at"),
            ("expires-at-second", "expires_at"),
        )
    },
    "invalid-issued-at-calendar-day.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_authorization_grant_issued_at_invalid"
        )
    ),
    "invalid-expires-at-calendar-day.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_authorization_grant_expires_at_invalid"
        )
    ),
    "invalid-time-order-equal.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_authorization_grant_time_order_invalid"
        )
    ),
    "invalid-time-order-reversed.yaml": FixtureExpectation(
        semantic_finding=(
            "agent_execution_authorization_grant_time_order_invalid"
        )
    ),
    **{
        f"invalid-extra-{name}.yaml": FixtureExpectation(
            _one("additionalProperties", ())
        )
        for name in (
            "algorithm",
            "consumed",
            "key-id",
            "signature",
            "state",
            "status",
            "tool-id",
        )
    },
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
    "invalid-run-contract-unsupported-operation.yaml": FixtureExpectation(
        semantic_finding="operation_id_not_supported"
    ),
    "invalid-run-contract-parent-resource.yaml": FixtureExpectation(
        semantic_finding="resource_parent_segment"
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
        grant_resource = schema_resource(GRANT_SCHEMA_NAME)
        run_resource = schema_resource(RUN_SCHEMA_NAME)
        contract_resource = schema_resource(CONTRACT_SCHEMA_NAME)
        if (
            grant_resource is None
            or run_resource is None
            or contract_resource is None
        ):
            raise FileNotFoundError(
                "Grant, Run, or Contract schema resource is missing"
            )
        grant_schema = json.loads(grant_resource.read_text(encoding="utf-8"))
        run_schema = json.loads(run_resource.read_text(encoding="utf-8"))
        contract_schema = json.loads(
            contract_resource.read_text(encoding="utf-8")
        )
    except Exception as exc:
        print(f"FAIL schema resource load: {exc}")
        return False

    field_names = [
        "grant_id",
        "run",
        "authorization_domain_id",
        "issuer_kind",
        "issuer_id",
        "provenance_reference",
        "issued_at",
        "expires_at",
    ]
    properties = grant_schema.get("properties", {})
    passed = (
        grant_schema.get("$schema")
        == "https://json-schema.org/draft/2020-12/schema"
        and grant_schema.get("$id") == GRANT_SCHEMA_ID
        and grant_schema.get("type") == "object"
        and grant_schema.get("additionalProperties") is False
        and grant_schema.get("required") == field_names
        and list(properties) == field_names
        and properties.get("run", {}).get("$ref") == RUN_SCHEMA_ID
        and properties.get("issuer_kind", {}).get("enum")
        == ["human", "policy"]
        and properties.get("issued_at", {}).get("pattern")
        == TIMESTAMP_PATTERN
        and properties.get("expires_at", {}).get("pattern")
        == TIMESTAMP_PATTERN
        and run_schema.get("$id") == RUN_SCHEMA_ID
        and run_schema.get("properties", {}).get("contract", {}).get("$ref")
        == CONTRACT_SCHEMA_ID
        and contract_schema.get("$id") == CONTRACT_SCHEMA_ID
    )
    print(
        f"{'PASS' if passed else 'FAIL'} schema contract: closed ordered "
        "eight-field Grant and exact packaged Run/Contract reference chain"
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


def _grant_from_document(document: dict[str, Any]) -> AgentExecutionAuthorizationGrant:
    run_document = document["run"]
    run = AgentExecutionRun(
        run_id=run_document["run_id"],
        contract=AgentExecutionContract(**run_document["contract"]),
    )
    return AgentExecutionAuthorizationGrant(
        grant_id=document["grant_id"],
        run=run,
        authorization_domain_id=document["authorization_domain_id"],
        issuer_kind=document["issuer_kind"],
        issuer_id=document["issuer_id"],
        provenance_reference=document["provenance_reference"],
        issued_at=document["issued_at"],
        expires_at=document["expires_at"],
    )


def semantic_result(
    document: dict[str, Any],
    expected_finding: str | None,
    label: str,
) -> bool:
    grant = _grant_from_document(document)
    result = validate_agent_execution_authorization_grant(grant)
    if expected_finding is None:
        passed = result.valid and result.findings == () and result.grant is grant
        expectation = "semantically valid"
    else:
        passed = (
            not result.valid
            and [finding.code for finding in result.findings]
            == [expected_finding]
            and result.grant is None
        )
        expectation = f"semantic finding {expected_finding}"
    print(f"{'PASS' if passed else 'FAIL'} {label} semantic: {expectation}")
    if not passed:
        print(
            "  - actual: "
            f"valid={result.valid}, "
            f"findings={[item.code for item in result.findings]}, "
            f"grant={result.grant!r}"
        )
    return passed


class NetworkAccessAttempted(RuntimeError):
    pass


def main() -> int:
    print(
        "AI Engineering Orchestra - Agent Execution Authorization Grant "
        "Validation"
    )
    print("=" * 78)
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
            validator = load_validator(GRANT_SCHEMA_NAME)
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

            missing_reference_validator = validator.evolve(
                schema={
                    "$ref": "https://example.invalid/"
                    "unregistered.schema.json"
                }
            )
            try:
                missing_reference_validator.validate({})
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
        print("Agent Execution Authorization Grant validation PASSED.")
        return 0
    print("Agent Execution Authorization Grant validation FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
