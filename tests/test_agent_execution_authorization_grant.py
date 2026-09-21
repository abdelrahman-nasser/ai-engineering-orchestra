"""Focused value, collection, scenario, schema, and purity tests for AIO-043."""

from __future__ import annotations

import ast
import copy
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, asdict, fields, replace
import json
import os
from pathlib import Path
import random
import secrets
import socket
import sqlite3
import subprocess
import time
import unittest
from unittest.mock import patch
import urllib.request
import uuid

import engineering_orchestration
import engineering_orchestration.agent_execution_authorization_grant as subject
from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
    AgentExecutionAuthorizationGrantCollectionValidationResult,
    AgentExecutionAuthorizationGrantFinding,
    AgentExecutionAuthorizationGrantValidationResult,
    validate_agent_execution_authorization_grant,
    validate_agent_execution_authorization_grant_collection,
)
from engineering_orchestration.agent_execution_authorization_evidence import (
    AgentExecutionAuthorizationAuthorityKind,
    AgentExecutionAuthorizationEvidence,
    AgentExecutionAuthorizationState,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.schema_resources import load_validator


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "engineering_orchestration"
    / "agent_execution_authorization_grant.py"
)
DOMAIN_ID = "authorization-domain::synthetic"
RUN_ID = "run::synthetic-one"
ISSUED_AT = "2026-09-22T10:00:00Z"
EXPIRES_AT = "2026-09-22T10:05:00Z"
GRANT_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-authorization-grant.schema.json"
)
RUN_SCHEMA_ID = (
    "https://ai-engineering-orchestra.dev/schemas/"
    "agent-execution-run.schema.json"
)


def contract(
    *,
    task_id: object = "AIO-043",
    workflow_id: object = "architecture-change",
    stage_id: object = "implement",
    role_id: object = "software-engineer",
    actor_id: object = "agent::synthetic",
    runtime_option_id: object = "runtime::synthetic",
    option_id: object = "option::synthetic",
    environment_id: object = "environment::synthetic",
    operation_id: object = "repository_file_read",
    resource: object = "synthetic/input.txt",
    execution_mode: object = "critical",
) -> AgentExecutionContract:
    """Build one synthetic Contract without implying operational trust."""

    return AgentExecutionContract(
        task_id,  # type: ignore[arg-type]
        workflow_id,  # type: ignore[arg-type]
        stage_id,  # type: ignore[arg-type]
        role_id,  # type: ignore[arg-type]
        actor_id,  # type: ignore[arg-type]
        runtime_option_id,  # type: ignore[arg-type]
        option_id,  # type: ignore[arg-type]
        environment_id,  # type: ignore[arg-type]
        operation_id,  # type: ignore[arg-type]
        resource,  # type: ignore[arg-type]
        execution_mode,  # type: ignore[arg-type]
    )


def run(
    run_id: object = RUN_ID,
    *,
    bound_contract: object | None = None,
) -> AgentExecutionRun:
    """Build one synthetic Run without implying dispatch or execution."""

    return AgentExecutionRun(
        run_id,  # type: ignore[arg-type]
        contract() if bound_contract is None else bound_contract,  # type: ignore[arg-type]
    )


def grant(
    grant_id: object = "grant::synthetic-one",
    *,
    bound_run: object | None = None,
    authorization_domain_id: object = DOMAIN_ID,
    issuer_kind: object = "human",
    issuer_id: object = "human::reviewer-one",
    provenance_reference: object = "approval::synthetic-one",
    issued_at: object = ISSUED_AT,
    expires_at: object = EXPIRES_AT,
) -> AgentExecutionAuthorizationGrant:
    """Build one synthetic Grant without implying authenticated issuance."""

    return AgentExecutionAuthorizationGrant(
        grant_id,  # type: ignore[arg-type]
        run() if bound_run is None else bound_run,  # type: ignore[arg-type]
        authorization_domain_id,  # type: ignore[arg-type]
        issuer_kind,  # type: ignore[arg-type]
        issuer_id,  # type: ignore[arg-type]
        provenance_reference,  # type: ignore[arg-type]
        issued_at,  # type: ignore[arg-type]
        expires_at,  # type: ignore[arg-type]
    )


def restore_grant(payload: str) -> AgentExecutionAuthorizationGrant:
    """Restore the exact Contract -> Run -> Grant mapping hierarchy."""

    document = json.loads(payload)
    run_document = document["run"]
    restored_run = AgentExecutionRun(
        run_id=run_document["run_id"],
        contract=AgentExecutionContract(**run_document["contract"]),
    )
    return AgentExecutionAuthorizationGrant(
        grant_id=document["grant_id"],
        run=restored_run,
        authorization_domain_id=document["authorization_domain_id"],
        issuer_kind=document["issuer_kind"],
        issuer_id=document["issuer_id"],
        provenance_reference=document["provenance_reference"],
        issued_at=document["issued_at"],
        expires_at=document["expires_at"],
    )


class AgentExecutionAuthorizationGrantFixture(unittest.TestCase):
    def assert_atomic_invalid(
        self,
        result: AgentExecutionAuthorizationGrantValidationResult,
        codes: list[str],
        messages: list[str] | None = None,
    ) -> None:
        self.assertIs(type(result), AgentExecutionAuthorizationGrantValidationResult)
        self.assertFalse(result.valid)
        self.assertIs(type(result.findings), tuple)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertIsNone(result.grant)
        if messages is not None:
            self.assertEqual(
                [finding.message for finding in result.findings],
                messages,
            )

    def assert_collection_invalid(
        self,
        result: AgentExecutionAuthorizationGrantCollectionValidationResult,
        codes: list[str],
    ) -> None:
        self.assertIs(
            type(result),
            AgentExecutionAuthorizationGrantCollectionValidationResult,
        )
        self.assertFalse(result.valid)
        self.assertIs(type(result.findings), tuple)
        self.assertEqual([finding.code for finding in result.findings], codes)
        self.assertTrue(result.findings)
        self.assertEqual(result.normalized_grants, ())

    def validate_collection(
        self,
        grants: object,
        *,
        authorization_domain_id: object = DOMAIN_ID,
    ) -> AgentExecutionAuthorizationGrantCollectionValidationResult:
        return validate_agent_execution_authorization_grant_collection(
            grants,  # type: ignore[arg-type]
            authorization_domain_id=authorization_domain_id,  # type: ignore[arg-type]
        )

    def assert_no_operational_claims(
        self,
        value: AgentExecutionAuthorizationGrant,
    ) -> None:
        self.assertTrue(
            {
                "state",
                "authenticated",
                "verified",
                "consumed",
                "consumed_at",
                "reusable",
                "use_count",
                "revoked_at",
                "signature",
                "key",
                "token",
                "tool_id",
                "command",
                "payload",
                "status",
                "result",
                "error",
            }.isdisjoint(vars(value))
        )
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        for fragment in (
            "authenticate",
            "consume",
            "replay",
            "revoke",
            "persist",
            "dispatch",
            "invoke",
            "admit",
        ):
            self.assertTrue(all(fragment not in name for name in exported))


class AgentExecutionAuthorizationGrantValueTests(
    AgentExecutionAuthorizationGrantFixture
):
    def test_public_values_are_frozen_tuple_backed_and_exactly_shaped(self) -> None:
        self.assertEqual(
            [field.name for field in fields(AgentExecutionAuthorizationGrant)],
            [
                "grant_id",
                "run",
                "authorization_domain_id",
                "issuer_kind",
                "issuer_id",
                "provenance_reference",
                "issued_at",
                "expires_at",
            ],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(AgentExecutionAuthorizationGrantFinding)
            ],
            ["code", "message"],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(
                    AgentExecutionAuthorizationGrantValidationResult
                )
            ],
            ["valid", "findings", "grant"],
        )
        self.assertEqual(
            [
                field.name
                for field in fields(
                    AgentExecutionAuthorizationGrantCollectionValidationResult
                )
            ],
            ["valid", "findings", "normalized_grants"],
        )
        value = grant()
        values = (
            value,
            AgentExecutionAuthorizationGrantFinding("code", "message"),
            AgentExecutionAuthorizationGrantValidationResult(True, (), value),
            AgentExecutionAuthorizationGrantCollectionValidationResult(
                True, (), (value,)
            ),
        )
        for item in values:
            with self.subTest(type=type(item).__name__):
                with self.assertRaises(FrozenInstanceError):
                    item.synthetic = "changed"  # type: ignore[misc]
        self.assertIs(type(values[2].findings), tuple)
        self.assertIs(type(values[3].normalized_grants), tuple)

    def test_direct_module_api_and_package_root_boundary(self) -> None:
        names = (
            "AgentExecutionAuthorizationGrant",
            "AgentExecutionAuthorizationGrantFinding",
            "AgentExecutionAuthorizationGrantValidationResult",
            "AgentExecutionAuthorizationGrantCollectionValidationResult",
            "validate_agent_execution_authorization_grant",
            "validate_agent_execution_authorization_grant_collection",
        )
        for name in names:
            self.assertIn(name, vars(subject))
            self.assertFalse(hasattr(engineering_orchestration, name))

    def test_exact_grant_type_is_required_and_subclasses_are_rejected(self) -> None:
        expected = AgentExecutionAuthorizationGrantValidationResult(
            False,
            (
                AgentExecutionAuthorizationGrantFinding(
                    "agent_execution_authorization_grant_invalid_type",
                    "Agent Execution Authorization Grant must be an exact "
                    "AgentExecutionAuthorizationGrant value.",
                ),
            ),
            None,
        )
        self.assertEqual(validate_agent_execution_authorization_grant(None), expected)
        self.assertEqual(validate_agent_execution_authorization_grant(object()), expected)

        class DerivedGrant(AgentExecutionAuthorizationGrant):
            pass

        supplied = grant()
        derived = DerivedGrant(**asdict(supplied))
        self.assertEqual(validate_agent_execution_authorization_grant(derived), expected)

    def test_valid_grant_preserves_exact_grant_run_and_contract_objects(self) -> None:
        bound_contract = contract(execution_mode="deep")
        bound_run = run("run::preserved", bound_contract=bound_contract)
        supplied = grant("grant::preserved", bound_run=bound_run)
        result = validate_agent_execution_authorization_grant(supplied)
        self.assertEqual(
            result,
            AgentExecutionAuthorizationGrantValidationResult(True, (), supplied),
        )
        self.assertIs(result.grant, supplied)
        self.assertIs(result.grant.run, bound_run)
        self.assertIs(result.grant.run.contract, bound_contract)

    def test_all_exact_nonempty_string_fields_reject_bad_values_in_order(self) -> None:
        class DerivedText(str):
            pass

        field_codes = {
            "grant_id": "agent_execution_authorization_grant_grant_id_invalid",
            "authorization_domain_id": (
                "agent_execution_authorization_grant_"
                "authorization_domain_id_invalid"
            ),
            "issuer_id": "agent_execution_authorization_grant_issuer_id_invalid",
            "provenance_reference": (
                "agent_execution_authorization_grant_"
                "provenance_reference_invalid"
            ),
        }
        for field_name, code in field_codes.items():
            for value in ("", None, False, 0, object(), DerivedText("value")):
                with self.subTest(field=field_name, value=value):
                    self.assert_atomic_invalid(
                        validate_agent_execution_authorization_grant(
                            replace(grant(), **{field_name: value})
                        ),
                        [code],
                    )

    def test_opaque_strings_are_case_sensitive_and_never_normalized(self) -> None:
        values = (
            "Grant::CaseSensitive",
            "grant::casesensitive",
            "  grant id with whitespace  ",
            " ",
            "001",
        )
        validated = tuple(
            validate_agent_execution_authorization_grant(grant(value))
            for value in values
        )
        self.assertTrue(all(result.valid for result in validated))
        self.assertEqual(
            [result.grant.grant_id for result in validated],  # type: ignore[union-attr]
            list(values),
        )
        self.assertEqual(len({result.grant for result in validated}), len(values))

    def test_issuer_kind_is_exactly_human_or_policy(self) -> None:
        self.assertTrue(
            validate_agent_execution_authorization_grant(
                grant(issuer_kind="human")
            ).valid
        )
        self.assertTrue(
            validate_agent_execution_authorization_grant(
                grant(
                    issuer_kind="policy",
                    issuer_id="policy::release",
                )
            ).valid
        )

        class DerivedKind(str):
            pass

        for value in ("Human", "service", "", None, 1, DerivedKind("human")):
            with self.subTest(value=value):
                self.assert_atomic_invalid(
                    validate_agent_execution_authorization_grant(
                        grant(issuer_kind=value)
                    ),
                    ["agent_execution_authorization_grant_issuer_kind_invalid"],
                )

    def test_timestamp_grammar_is_ascii_uppercase_utc_and_bounded(self) -> None:
        valid_pairs = (
            ("0001-01-01T00:00:00Z", "0001-01-01T00:00:01Z"),
            ("9999-12-31T23:59:58Z", "9999-12-31T23:59:59Z"),
            ("2026-09-22T10:00:00.1Z", "2026-09-22T10:00:00.2Z"),
            ("2026-09-22T10:00:00.12345Z", "2026-09-22T10:00:01Z"),
        )
        for issued_at, expires_at in valid_pairs:
            with self.subTest(issued_at=issued_at, expires_at=expires_at):
                self.assertTrue(
                    validate_agent_execution_authorization_grant(
                        grant(issued_at=issued_at, expires_at=expires_at)
                    ).valid
                )

        invalid_values = (
            "0000-01-01T00:00:00Z",
            "２０２６-09-22T10:00:00Z",
            "2026-09-22t10:00:00Z",
            "2026-09-22T10:00:00z",
            "2026-09-22T10:00:00+00:00",
            "2026-09-22T10:00Z",
            "2026-09-22T10:00:00.Z",
            "2026-09-22T10:00:00.1234567Z",
            "2026-09-22T10:00:60Z",
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self.assert_atomic_invalid(
                    validate_agent_execution_authorization_grant(
                        grant(issued_at=value)
                    ),
                    ["agent_execution_authorization_grant_issued_at_invalid"],
                )

    def test_calendar_validity_and_static_time_order_are_enforced(self) -> None:
        cases = (
            (
                grant(issued_at="2026-02-30T10:00:00Z"),
                "agent_execution_authorization_grant_issued_at_invalid",
            ),
            (
                grant(expires_at="2026-02-30T10:05:00Z"),
                "agent_execution_authorization_grant_expires_at_invalid",
            ),
            (
                grant(expires_at=ISSUED_AT),
                "agent_execution_authorization_grant_time_order_invalid",
            ),
            (
                grant(
                    issued_at="2026-09-22T10:06:00Z",
                    expires_at="2026-09-22T10:05:00Z",
                ),
                "agent_execution_authorization_grant_time_order_invalid",
            ),
        )
        for value, code in cases:
            with self.subTest(code=code):
                self.assert_atomic_invalid(
                    validate_agent_execution_authorization_grant(value),
                    [code],
                )
        self.assertTrue(
            validate_agent_execution_authorization_grant(
                grant(
                    issued_at="2024-02-29T23:59:59Z",
                    expires_at="2024-03-01T00:00:00Z",
                )
            ).valid
        )

    def test_nested_run_findings_preserve_code_message_multiplicity_and_order(
        self,
    ) -> None:
        supplied = grant(
            "",
            bound_run=run(
                "",
                bound_contract=contract(
                    task_id="",
                    actor_id=object(),
                    operation_id="Malformed-Operation",
                    resource="synthetic/../input.txt",
                    execution_mode="turbo",
                ),
            ),
            authorization_domain_id="",
            issuer_kind="service",
            issuer_id="",
            provenance_reference="",
            issued_at="bad",
            expires_at="also-bad",
        )
        result = validate_agent_execution_authorization_grant(supplied)
        self.assert_atomic_invalid(
            result,
            [
                "agent_execution_authorization_grant_grant_id_invalid",
                "agent_execution_run_run_id_invalid",
                "agent_execution_contract_task_id_invalid",
                "agent_execution_contract_actor_id_invalid",
                "operation_id_invalid_syntax",
                "resource_parent_segment",
                "agent_execution_contract_execution_mode_not_supported",
                "agent_execution_authorization_grant_"
                "authorization_domain_id_invalid",
                "agent_execution_authorization_grant_issuer_kind_invalid",
                "agent_execution_authorization_grant_issuer_id_invalid",
                "agent_execution_authorization_grant_"
                "provenance_reference_invalid",
                "agent_execution_authorization_grant_issued_at_invalid",
                "agent_execution_authorization_grant_expires_at_invalid",
            ],
        )
        nested = result.findings[1:7]
        nested_reference = subject.validate_agent_execution_run(supplied.run)
        self.assertEqual(
            [(item.code, item.message) for item in nested],
            [(item.code, item.message) for item in nested_reference.findings],
        )

    def test_wrong_nested_run_type_preserves_parent_finding_exactly(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_authorization_grant(
                grant(bound_run=object())
            ),
            ["agent_execution_run_invalid_type"],
            ["Agent Execution Run must be an exact AgentExecutionRun value."],
        )

    def test_json_round_trip_preserves_value_not_operational_trust(self) -> None:
        original = grant(
            "grant::serialized",
            bound_run=run(
                "run::serialized",
                bound_contract=contract(execution_mode="deep"),
            ),
            issuer_kind="policy",
            issuer_id="policy::release",
            issued_at="2026-09-22T10:00:00.123Z",
        )
        restored = restore_grant(json.dumps(asdict(original), sort_keys=True))
        result = validate_agent_execution_authorization_grant(restored)
        self.assertTrue(result.valid)
        self.assertEqual(result.grant, original)
        self.assertIsNot(result.grant, original)
        self.assertIsNot(result.grant.run, original.run)
        self.assertIsNot(result.grant.run.contract, original.run.contract)
        self.assert_no_operational_claims(restored)


class AgentExecutionAuthorizationGrantCollectionTests(
    AgentExecutionAuthorizationGrantFixture
):
    def test_noniterable_collection_fails_closed(self) -> None:
        self.assert_collection_invalid(
            self.validate_collection(None),
            ["agent_execution_authorization_grant_collection_invalid"],
        )

    def test_collection_domain_must_be_an_exact_nonempty_string(self) -> None:
        class DerivedDomain(str):
            pass

        for value in ("", None, False, 0, DerivedDomain(DOMAIN_ID)):
            with self.subTest(value=value):
                self.assert_collection_invalid(
                    self.validate_collection([], authorization_domain_id=value),
                    [
                        "agent_execution_authorization_grant_collection_"
                        "authorization_domain_id_invalid"
                    ],
                )

    def test_empty_domain_collection_is_valid_and_tuple_backed(self) -> None:
        result = self.validate_collection([])
        self.assertEqual(
            result,
            AgentExecutionAuthorizationGrantCollectionValidationResult(
                True, (), ()
            ),
        )

    def test_domain_mismatch_is_deduplicated_sorted_and_atomic(self) -> None:
        result = self.validate_collection(
            [
                grant(authorization_domain_id="domain::z"),
                grant(
                    "grant::two",
                    bound_run=run("run::two"),
                    authorization_domain_id="domain::a",
                ),
                grant(
                    "grant::three",
                    bound_run=run("run::three"),
                    authorization_domain_id="domain::z",
                ),
            ]
        )
        self.assert_collection_invalid(
            result,
            [
                "agent_execution_authorization_grant_domain_mismatch",
                "agent_execution_authorization_grant_domain_mismatch",
            ],
        )
        self.assertIn("'domain::a'", result.findings[0].message)
        self.assertIn("'domain::z'", result.findings[1].message)

    def test_collection_iterable_is_captured_exactly_once(self) -> None:
        events: list[str] = []

        class CaptureOnce:
            def __iter__(self):
                events.append("iter")
                if len(events) > 1:
                    raise AssertionError("collection consumed more than once")
                yield grant()

        result = self.validate_collection(CaptureOnce())
        self.assertTrue(result.valid)
        self.assertEqual(events, ["iter"])

    def test_collection_never_mutates_input_or_values(self) -> None:
        supplied = [
            grant(
                "grant::z",
                bound_run=run("run::z"),
            ),
            grant(
                "grant::a",
                bound_run=run("run::a"),
            ),
        ]
        before = copy.deepcopy(supplied)
        result = self.validate_collection(supplied)
        self.assertTrue(result.valid)
        self.assertEqual(supplied, before)
        self.assertEqual([item.grant_id for item in supplied], ["grant::z", "grant::a"])

    def test_valid_output_is_canonically_ordered_and_preserves_objects(self) -> None:
        values = [
            grant(
                "grant::z",
                bound_run=run("run::z"),
                issuer_kind="policy",
                issuer_id="policy::z",
            ),
            grant(
                "grant::b",
                bound_run=run("run::b"),
                issuer_id="human::b",
            ),
            grant(
                "grant::a",
                bound_run=run("run::a"),
                issuer_id="human::a",
            ),
        ]
        result = self.validate_collection(values)
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_grants, (values[2], values[1], values[0]))
        self.assertIs(result.normalized_grants[0], values[2])

    def test_intrinsic_failures_precede_domain_and_relational_checks(self) -> None:
        bad = grant("", authorization_domain_id="domain::other")
        result = self.validate_collection([bad, bad])
        self.assert_collection_invalid(
            result,
            [
                "agent_execution_authorization_grant_grant_id_invalid",
                "agent_execution_authorization_grant_grant_id_invalid",
            ],
        )

    def test_exact_duplicate_invalidates_whole_collection(self) -> None:
        value = grant()
        self.assert_collection_invalid(
            self.validate_collection([value, value]),
            ["duplicate_agent_execution_authorization_grant"],
        )

    def test_rebound_grant_identity_is_a_conflict(self) -> None:
        original = grant()
        rebound = replace(original, provenance_reference="approval::other")
        self.assert_collection_invalid(
            self.validate_collection([original, rebound]),
            [
                "agent_execution_authorization_grant_"
                "identity_binding_conflict"
            ],
        )

    def test_identity_conflict_takes_precedence_over_duplicate(self) -> None:
        original = grant()
        rebound = replace(original, expires_at="2026-09-22T10:06:00Z")
        self.assert_collection_invalid(
            self.validate_collection([original, original, rebound]),
            [
                "agent_execution_authorization_grant_"
                "identity_binding_conflict"
            ],
        )

    def test_rebound_run_id_is_a_conflict(self) -> None:
        first = grant("grant::one")
        second = grant(
            "grant::two",
            bound_run=run(
                RUN_ID,
                bound_contract=contract(resource="synthetic/other.txt"),
            ),
        )
        self.assert_collection_invalid(
            self.validate_collection([first, second]),
            [
                "agent_execution_authorization_grant_"
                "run_identity_binding_conflict"
            ],
        )

    def test_same_run_with_same_issuer_and_distinct_grants_is_unsupported(self) -> None:
        bound_run = run()
        first = grant("grant::one", bound_run=bound_run)
        second = grant("grant::two", bound_run=bound_run)
        self.assert_collection_invalid(
            self.validate_collection([first, second]),
            [
                "unsupported_multiple_agent_execution_authorization_"
                "grants_for_run"
            ],
        )

    def test_human_and_policy_for_same_run_is_unsupported_multi_authority(
        self,
    ) -> None:
        bound_run = run()
        human = grant("grant::human", bound_run=bound_run)
        policy = grant(
            "grant::policy",
            bound_run=bound_run,
            issuer_kind="policy",
            issuer_id="policy::release",
        )
        self.assert_collection_invalid(
            self.validate_collection([human, policy]),
            ["unsupported_multi_authority_agent_execution_authorization_grant"],
        )

    def test_collision_finding_category_order_is_deterministic(self) -> None:
        duplicate = grant(
            "grant::duplicate", bound_run=run("run::duplicate")
        )
        identity = grant("grant::identity", bound_run=run("run::identity"))
        identity_rebound = replace(
            identity, provenance_reference="approval::rebound"
        )
        rebound_one = grant(
            "grant::run-binding-a", bound_run=run("run::rebound")
        )
        rebound_two = grant(
            "grant::run-binding-b",
            bound_run=run(
                "run::rebound",
                bound_contract=contract(resource="synthetic/rebound.txt"),
            ),
        )
        same_run = run("run::multiple")
        multiple_one = grant("grant::multiple-a", bound_run=same_run)
        multiple_two = grant("grant::multiple-b", bound_run=same_run)
        authority_run = run("run::authority")
        human = grant("grant::human", bound_run=authority_run)
        policy = grant(
            "grant::policy",
            bound_run=authority_run,
            issuer_kind="policy",
            issuer_id="policy::one",
        )
        values = [
            policy,
            multiple_two,
            rebound_two,
            identity_rebound,
            duplicate,
            human,
            multiple_one,
            rebound_one,
            identity,
            duplicate,
        ]
        expected = [
            "duplicate_agent_execution_authorization_grant",
            "agent_execution_authorization_grant_identity_binding_conflict",
            "agent_execution_authorization_grant_run_identity_binding_conflict",
            "unsupported_multiple_agent_execution_authorization_grants_for_run",
            "unsupported_multi_authority_agent_execution_authorization_grant",
        ]
        forward = self.validate_collection(values)
        reverse = self.validate_collection(list(reversed(values)))
        self.assert_collection_invalid(forward, expected)
        self.assertEqual(reverse, forward)

    def test_same_run_and_ids_are_independent_across_explicit_domains(self) -> None:
        first = grant(authorization_domain_id="domain::one")
        second = grant(authorization_domain_id="domain::two")
        self.assertTrue(
            self.validate_collection(
                [first], authorization_domain_id="domain::one"
            ).valid
        )
        self.assertTrue(
            self.validate_collection(
                [second], authorization_domain_id="domain::two"
            ).valid
        )

    def test_same_grant_id_across_issuers_is_not_an_identity_collision(self) -> None:
        human = grant(bound_run=run("run::human"))
        policy = grant(
            bound_run=run("run::policy"),
            issuer_kind="policy",
            issuer_id="policy::release",
        )
        result = self.validate_collection([policy, human])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_grants, (human, policy))


class AgentExecutionAuthorizationGrantSchemaTests(
    AgentExecutionAuthorizationGrantFixture
):
    def test_schema_is_closed_ordered_and_uses_canonical_run_reference(self) -> None:
        document = json.loads(
            (ROOT / "schemas" / "agent-execution-authorization-grant.schema.json")
            .read_text(encoding="utf-8")
        )
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
        self.assertEqual(document["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(document["$id"], GRANT_SCHEMA_ID)
        self.assertEqual(document["type"], "object")
        self.assertIs(document["additionalProperties"], False)
        self.assertEqual(document["required"], field_names)
        self.assertEqual(list(document["properties"]), field_names)
        self.assertEqual(document["properties"]["run"]["$ref"], RUN_SCHEMA_ID)

    def test_schema_timestamp_pattern_matches_runtime_syntax_boundary(self) -> None:
        validator = load_validator(
            "agent-execution-authorization-grant.schema.json"
        )
        valid = asdict(grant())
        validator.validate(valid)
        for field_name, value in (
            ("issued_at", "0000-01-01T00:00:00Z"),
            ("issued_at", "2026-09-22t10:00:00Z"),
            ("issued_at", "2026-09-22T10:00:00.1234567Z"),
            ("issued_at", "2026-09-22T10:00:00Z\n"),
            ("expires_at", "2026-09-22T10:05:60Z"),
            ("expires_at", "2026-09-22T10:05:00Z\n"),
        ):
            with self.subTest(field=field_name, value=value):
                changed = copy.deepcopy(valid)
                changed[field_name] = value
                self.assertTrue(list(validator.iter_errors(changed)))
        calendar_invalid = copy.deepcopy(valid)
        calendar_invalid["issued_at"] = "2026-02-30T10:00:00Z"
        self.assertEqual(list(validator.iter_errors(calendar_invalid)), [])
        self.assertFalse(
            validate_agent_execution_authorization_grant(
                grant(issued_at=calendar_invalid["issued_at"])
            ).valid
        )

    def test_schema_resolves_run_and_contract_offline_without_cwd(self) -> None:
        blocked = AssertionError("schema resolution attempted external access")
        with patch("pathlib.Path.cwd", side_effect=blocked), patch(
            "socket.create_connection", side_effect=blocked
        ), patch("socket.getaddrinfo", side_effect=blocked), patch(
            "urllib.request.urlopen", side_effect=blocked
        ):
            validator = load_validator(
                "agent-execution-authorization-grant.schema.json"
            )
            validator.validate(asdict(grant()))
            invalid = asdict(grant())
            invalid["run"]["contract"]["actor_id"] = ""
            errors = list(validator.iter_errors(invalid))
        self.assertEqual(
            [(error.validator, tuple(error.absolute_path)) for error in errors],
            [("minLength", ("run", "contract", "actor_id"))],
        )

    def test_schema_round_trip_preserves_exact_equality(self) -> None:
        original = grant(issued_at="2026-09-22T10:00:00.123456Z")
        payload = json.dumps(asdict(original))
        validator = load_validator(
            "agent-execution-authorization-grant.schema.json"
        )
        validator.validate(json.loads(payload))
        restored = restore_grant(payload)
        self.assertEqual(restored, original)
        self.assertTrue(
            validate_agent_execution_authorization_grant(restored).valid
        )

    def test_unknown_schema_reference_fails_closed_without_network(self) -> None:
        blocked = AssertionError("schema resolution attempted network access")
        with patch("socket.create_connection", side_effect=blocked), patch(
            "socket.getaddrinfo", side_effect=blocked
        ), patch("urllib.request.urlopen", side_effect=blocked):
            validator = load_validator(
                "agent-execution-authorization-grant.schema.json"
            )
            unknown = validator.evolve(
                schema={
                    "$ref": "https://example.invalid/"
                    "unregistered.schema.json"
                }
            )
            with self.assertRaises(Exception) as caught:
                unknown.validate({})
        self.assertNotIsInstance(caught.exception, AssertionError)
        self.assertIn("unregistered.schema.json", str(caught.exception))


class AgentExecutionAuthorizationGrantScenarioTests(
    AgentExecutionAuthorizationGrantFixture
):
    """The explicit 42-case behavioral and negative-boundary matrix."""

    def test_scenario_01_valid_human_grant(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertEqual(result.findings, ())
        self.assert_no_operational_claims(result.grant)

    def test_scenario_02_valid_policy_grant(self) -> None:
        value = grant(issuer_kind="policy", issuer_id="policy::release")
        result = validate_agent_execution_authorization_grant(value)
        self.assertTrue(result.valid)
        self.assertIs(result.grant, value)
        self.assert_no_operational_claims(result.grant)

    def test_scenario_03_fractional_timestamp_precision(self) -> None:
        for digits in range(1, 7):
            value = grant(
                issued_at=f"2026-09-22T10:00:00.{digits * '1'}Z",
                expires_at="2026-09-22T10:00:01Z",
            )
            self.assertTrue(validate_agent_execution_authorization_grant(value).valid)

    def test_scenario_04_gregorian_leap_day(self) -> None:
        self.assertTrue(
            validate_agent_execution_authorization_grant(
                grant(
                    issued_at="2024-02-29T23:59:59Z",
                    expires_at="2024-03-01T00:00:00Z",
                )
            ).valid
        )

    def test_scenario_05_opaque_identifiers_are_exact(self) -> None:
        value = grant(
            " Grant :: exact  ",
            authorization_domain_id=" Domain :: exact  ",
            issuer_id=" Human :: exact  ",
            provenance_reference=" Audit :: exact  ",
        )
        result = validate_agent_execution_authorization_grant(value)
        self.assertTrue(result.valid)
        self.assertEqual(result.grant, value)

    def test_scenario_06_direct_construction_does_not_authenticate(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertNotIn("authenticated", vars(result.grant))
        self.assert_no_operational_claims(result.grant)

    def test_scenario_07_grant_is_positive_only_without_state(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertNotIn("state", vars(result.grant))
        self.assert_no_operational_claims(result.grant)

    def test_scenario_08_single_use_is_intent_without_counter(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertTrue(
            {"consumed", "use_count", "reusable"}.isdisjoint(vars(result.grant))
        )
        self.assert_no_operational_claims(result.grant)

    def test_scenario_09_complete_run_is_bound(self) -> None:
        bound_run = run(bound_contract=contract(resource="synthetic/exact.txt"))
        result = validate_agent_execution_authorization_grant(
            grant(bound_run=bound_run)
        )
        self.assertTrue(result.valid)
        self.assertIs(result.grant.run, bound_run)
        self.assertEqual(result.grant.run.contract.resource, "synthetic/exact.txt")

    def test_scenario_10_bare_run_id_is_insufficient(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_authorization_grant(
                grant(bound_run=RUN_ID)
            ),
            ["agent_execution_run_invalid_type"],
        )

    def test_scenario_11_domain_is_distinct_from_environment(self) -> None:
        value = grant(
            authorization_domain_id="domain::audience",
            bound_run=run(
                bound_contract=contract(environment_id="environment::execution")
            ),
        )
        result = validate_agent_execution_authorization_grant(value)
        self.assertTrue(result.valid)
        self.assertNotEqual(
            result.grant.authorization_domain_id,
            result.grant.run.contract.environment_id,
        )

    def test_scenario_12_core_does_not_generate_grant_id(self) -> None:
        supplied = "550e8400-e29b-41d4-a716-446655440000"
        with patch.object(
            uuid,
            "uuid4",
            side_effect=AssertionError("Core attempted Grant ID generation"),
        ):
            result = validate_agent_execution_authorization_grant(grant(supplied))
        self.assertTrue(result.valid)
        self.assertEqual(result.grant.grant_id, supplied)

    def test_scenario_13_provenance_is_audit_only(self) -> None:
        value = grant(provenance_reference="audit://opaque/reference")
        result = validate_agent_execution_authorization_grant(value)
        self.assertTrue(result.valid)
        self.assertEqual(result.grant.provenance_reference, "audit://opaque/reference")
        self.assertNotIn("provenance_verified", vars(result.grant))

    def test_scenario_14_issued_at_strictly_precedes_expiry(self) -> None:
        self.assertTrue(validate_agent_execution_authorization_grant(grant()).valid)

    def test_scenario_15_equal_timestamps_fail(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_authorization_grant(
                grant(expires_at=ISSUED_AT)
            ),
            ["agent_execution_authorization_grant_time_order_invalid"],
        )

    def test_scenario_16_reversed_timestamps_fail(self) -> None:
        self.assert_atomic_invalid(
            validate_agent_execution_authorization_grant(
                grant(issued_at=EXPIRES_AT, expires_at=ISSUED_AT)
            ),
            ["agent_execution_authorization_grant_time_order_invalid"],
        )

    def test_scenario_17_no_current_time_is_consulted(self) -> None:
        with patch.object(
            time,
            "time",
            side_effect=AssertionError("wall clock consulted"),
        ):
            old = validate_agent_execution_authorization_grant(
                grant(
                    issued_at="2000-01-01T00:00:00Z",
                    expires_at="2000-01-01T00:00:01Z",
                )
            )
            future = validate_agent_execution_authorization_grant(
                grant(
                    issued_at="9999-12-31T23:59:58Z",
                    expires_at="9999-12-31T23:59:59Z",
                )
            )
        self.assertTrue(old.valid and future.valid)

    def test_scenario_18_no_clock_skew_field_or_policy(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertTrue({"clock_skew", "skew_seconds"}.isdisjoint(vars(result.grant)))

    def test_scenario_19_no_revocation_model(self) -> None:
        result = validate_agent_execution_authorization_grant(grant())
        self.assertTrue(result.valid)
        self.assertTrue({"revoked", "revoked_at"}.isdisjoint(vars(result.grant)))

    def test_scenario_20_empty_domain_snapshot(self) -> None:
        result = self.validate_collection([])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_grants, ())

    def test_scenario_21_canonical_collection_order(self) -> None:
        later = grant("grant::z", bound_run=run("run::z"), issuer_id="issuer::z")
        earlier = grant("grant::a", bound_run=run("run::a"), issuer_id="issuer::a")
        result = self.validate_collection([later, earlier])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_grants, (earlier, later))

    def test_scenario_22_domain_mismatch(self) -> None:
        self.assert_collection_invalid(
            self.validate_collection(
                [grant(authorization_domain_id="domain::other")]
            ),
            ["agent_execution_authorization_grant_domain_mismatch"],
        )

    def test_scenario_23_exact_duplicate(self) -> None:
        value = grant()
        self.assert_collection_invalid(
            self.validate_collection([value, value]),
            ["duplicate_agent_execution_authorization_grant"],
        )

    def test_scenario_24_grant_identity_rebind(self) -> None:
        value = grant()
        self.assert_collection_invalid(
            self.validate_collection(
                [value, replace(value, issued_at="2026-09-22T09:59:59Z")]
            ),
            ["agent_execution_authorization_grant_identity_binding_conflict"],
        )

    def test_scenario_25_identity_conflict_dominates_duplicate(self) -> None:
        value = grant()
        rebound = replace(value, provenance_reference="approval::other")
        self.assert_collection_invalid(
            self.validate_collection([value, value, rebound]),
            ["agent_execution_authorization_grant_identity_binding_conflict"],
        )

    def test_scenario_26_run_id_rebind(self) -> None:
        one = grant("grant::one")
        two = grant(
            "grant::two",
            bound_run=run(
                RUN_ID,
                bound_contract=contract(resource="synthetic/rebound.txt"),
            ),
        )
        self.assert_collection_invalid(
            self.validate_collection([one, two]),
            ["agent_execution_authorization_grant_run_identity_binding_conflict"],
        )

    def test_scenario_27_same_run_reissue_by_same_issuer(self) -> None:
        bound_run = run()
        self.assert_collection_invalid(
            self.validate_collection(
                [
                    grant("grant::one", bound_run=bound_run),
                    grant("grant::two", bound_run=bound_run),
                ]
            ),
            [
                "unsupported_multiple_agent_execution_authorization_"
                "grants_for_run"
            ],
        )

    def test_scenario_28_human_policy_composition(self) -> None:
        bound_run = run()
        self.assert_collection_invalid(
            self.validate_collection(
                [
                    grant("grant::human", bound_run=bound_run),
                    grant(
                        "grant::policy",
                        bound_run=bound_run,
                        issuer_kind="policy",
                        issuer_id="policy::release",
                    ),
                ]
            ),
            ["unsupported_multi_authority_agent_execution_authorization_grant"],
        )

    def test_scenario_29_no_first_last_or_latest_winner(self) -> None:
        bound_run = run()
        first = grant(
            "grant::first",
            bound_run=bound_run,
            expires_at="2026-09-22T10:03:00Z",
        )
        latest = grant(
            "grant::latest",
            bound_run=bound_run,
            expires_at="2026-09-22T10:09:00Z",
        )
        forward = self.validate_collection([first, latest])
        reverse = self.validate_collection([latest, first])
        self.assertEqual(forward, reverse)
        self.assert_collection_invalid(
            forward,
            [
                "unsupported_multiple_agent_execution_authorization_"
                "grants_for_run"
            ],
        )

    def test_scenario_30_same_run_is_independent_across_domains(self) -> None:
        for domain in ("domain::one", "domain::two"):
            result = self.validate_collection(
                [grant(authorization_domain_id=domain)],
                authorization_domain_id=domain,
            )
            self.assertTrue(result.valid)

    def test_scenario_31_same_grant_id_across_issuers(self) -> None:
        values = [
            grant(bound_run=run("run::human")),
            grant(
                bound_run=run("run::policy"),
                issuer_kind="policy",
                issuer_id="policy::release",
            ),
        ]
        self.assertTrue(self.validate_collection(values).valid)

    def test_scenario_32_same_grant_id_across_domains(self) -> None:
        one = grant(authorization_domain_id="domain::one")
        two = grant(authorization_domain_id="domain::two")
        self.assertTrue(
            self.validate_collection(
                [one], authorization_domain_id="domain::one"
            ).valid
        )
        self.assertTrue(
            self.validate_collection(
                [two], authorization_domain_id="domain::two"
            ).valid
        )

    def test_scenario_33_same_composite_identity_cannot_bind_new_run(self) -> None:
        first = grant()
        second = grant(bound_run=run("run::other"))
        self.assert_collection_invalid(
            self.validate_collection([first, second]),
            ["agent_execution_authorization_grant_identity_binding_conflict"],
        )

    def test_scenario_34_new_authority_uses_new_run_and_grant(self) -> None:
        first = grant("grant::one", bound_run=run("run::one"))
        second = grant("grant::two", bound_run=run("run::two"))
        result = self.validate_collection([second, first])
        self.assertTrue(result.valid)
        self.assertEqual(result.normalized_grants, (first, second))

    def test_scenario_35_input_iterable_is_captured_once(self) -> None:
        calls = 0

        def supplied():
            nonlocal calls
            calls += 1
            yield grant()

        result = self.validate_collection(supplied())
        self.assertTrue(result.valid)
        self.assertEqual(calls, 1)

    def test_scenario_36_validation_is_nonmutating(self) -> None:
        values = [grant()]
        before = copy.deepcopy(values)
        self.assertTrue(self.validate_collection(values).valid)
        self.assertEqual(values, before)

    def test_scenario_37_serialization_preserves_value_only(self) -> None:
        original = grant()
        restored = restore_grant(json.dumps(asdict(original)))
        self.assertEqual(restored, original)
        self.assertTrue(validate_agent_execution_authorization_grant(restored).valid)
        self.assert_no_operational_claims(restored)

    def test_scenario_38_one_invalid_value_atomically_invalidates_collection(
        self,
    ) -> None:
        valid = grant()
        invalid = grant("", bound_run=run("run::invalid"))
        result = self.validate_collection([valid, invalid])
        self.assert_collection_invalid(
            result,
            ["agent_execution_authorization_grant_grant_id_invalid"],
        )

    def test_scenario_39_no_core_issuance_or_authentication_api(self) -> None:
        self.assertFalse(hasattr(subject, "issue_agent_execution_authorization_grant"))
        self.assertFalse(hasattr(subject, "authenticate_issuer"))
        self.assert_no_operational_claims(grant())

    def test_scenario_40_no_registry_persistence_or_store(self) -> None:
        exported = {
            name.lower() for name in vars(subject) if not name.startswith("_")
        }
        self.assertTrue(
            all(
                not any(
                    fragment in name
                    for fragment in (
                        "registry",
                        "database",
                        "cache",
                        "queue",
                        "persist",
                        "store",
                        "ledger",
                    )
                )
                for name in exported
            )
        )

    def test_scenario_41_no_consumption_replay_or_revocation_api(self) -> None:
        for name in (
            "consume_agent_execution_authorization_grant",
            "check_grant_replay",
            "revoke_agent_execution_authorization_grant",
        ):
            self.assertFalse(hasattr(subject, name))
        self.assert_no_operational_claims(grant())

    def test_scenario_42_no_tool_binding_dispatch_or_invocation(self) -> None:
        for name in (
            "bind_tool",
            "admit_dispatch",
            "dispatch_agent_execution_run",
            "invoke_agent",
        ):
            self.assertFalse(hasattr(subject, name))
        self.assert_no_operational_claims(grant())

    def test_matrix_contains_exactly_42_explicit_scenarios(self) -> None:
        scenario_names = {
            name
            for name in vars(type(self))
            if name.startswith("test_scenario_")
        }
        self.assertEqual(len(scenario_names), 42)

    def test_spec_records_all_42_investigated_scenario_dispositions(self) -> None:
        specification = (
            ROOT
            / "core"
            / "agent-execution-authorization-grant-specification.md"
        ).read_text(encoding="utf-8")
        section = specification.split(
            "The complete investigated scenario disposition is:\n",
            1,
        )[1].split("\n---", 1)[0]
        for number in range(1, 43):
            with self.subTest(number=number):
                self.assertIn(f"\n{number}. ", f"\n{section}")
        self.assertNotIn("\n43. ", f"\n{section}")
        for boundary in (
            "Two-worker consumption",
            "Consumption followed by a crash",
            "dispatch before successful consumption",
            "No response after consumption",
            "Concurrent consumption",
            "Transaction failure",
            "in-memory store",
            "bearer-token",
            "signed-Grant",
            "protected target",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, section)

    def test_run_and_aio_039_granted_evidence_do_not_create_a_grant(self) -> None:
        existing_run = run()
        evidence = AgentExecutionAuthorizationEvidence(
            "AIO-043",
            "architecture-change",
            "implement",
            "software-engineer",
            "agent::synthetic",
            "runtime::synthetic",
            "option::synthetic",
            "environment::synthetic",
            "repository_file_read",
            "synthetic/input.txt",
            AgentExecutionAuthorizationAuthorityKind.HUMAN,
            "authority::synthetic",
            "provenance::aio-039",
            AgentExecutionAuthorizationState.GRANTED,
        )
        self.assertNotIn("grant", vars(existing_run))
        self.assertEqual(evidence.state, AgentExecutionAuthorizationState.GRANTED)
        self.assertNotIn("grant", vars(evidence))
        self.assertNotIsInstance(existing_run, AgentExecutionAuthorizationGrant)
        self.assertNotIsInstance(evidence, AgentExecutionAuthorizationGrant)

    def test_grant_for_another_complete_run_does_not_match_expected(self) -> None:
        expected_run = run("run::expected")
        supplied = grant(bound_run=run("run::different"))
        result = validate_agent_execution_authorization_grant(supplied)
        self.assertTrue(result.valid)
        self.assertNotEqual(result.grant.run, expected_run)

    def test_short_lifetime_is_valid_but_currentness_is_unproven(self) -> None:
        value = grant(
            issued_at="2026-09-22T10:00:00.000001Z",
            expires_at="2026-09-22T10:00:00.000002Z",
        )
        result = validate_agent_execution_authorization_grant(value)
        self.assertTrue(result.valid)
        self.assertTrue(
            {"current", "trusted_now", "consumed", "admitted", "success"}
            .isdisjoint(vars(result.grant))
        )


class AgentExecutionAuthorizationGrantSafetyTests(
    AgentExecutionAuthorizationGrantFixture
):
    def test_static_module_has_no_io_network_clock_randomness_or_execution_calls(
        self,
    ) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        called_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.split(".", 1)[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(
            imported_roots.isdisjoint(
                {
                    "glob",
                    "hashlib",
                    "http",
                    "os",
                    "pathlib",
                    "random",
                    "secrets",
                    "socket",
                    "sqlite3",
                    "subprocess",
                    "time",
                    "urllib",
                    "uuid",
                }
            )
        )
        self.assertTrue(
            called_names.isdisjoint(
                {
                    "open",
                    "read_text",
                    "read_bytes",
                    "write_text",
                    "write_bytes",
                    "resolve",
                    "stat",
                    "listdir",
                    "scandir",
                    "getenv",
                    "system",
                    "run",
                    "Popen",
                    "now",
                    "today",
                    "utcnow",
                    "time",
                    "monotonic",
                    "perf_counter",
                    "uuid4",
                    "token_hex",
                    "token_urlsafe",
                    "connect",
                    "urlopen",
                    "authenticate",
                    "consume",
                    "replay",
                    "revoke",
                    "persist",
                    "dispatch",
                    "execute",
                    "invoke",
                    "discover",
                    "probe",
                }
            )
        )

    def test_dynamic_guards_cover_intrinsic_collection_and_collision_paths(
        self,
    ) -> None:
        valid = grant()
        invalid = grant("")
        guards = (
            patch("builtins.open", side_effect=AssertionError("external work")),
            patch.object(Path, "open", side_effect=AssertionError("external work")),
            patch.object(Path, "read_text", side_effect=AssertionError("external work")),
            patch.object(Path, "read_bytes", side_effect=AssertionError("external work")),
            patch.object(Path, "stat", side_effect=AssertionError("external work")),
            patch.object(Path, "resolve", side_effect=AssertionError("external work")),
            patch.object(Path, "iterdir", side_effect=AssertionError("external work")),
            patch.object(os, "stat", side_effect=AssertionError("external work")),
            patch.object(os, "access", side_effect=AssertionError("external work")),
            patch.object(os, "listdir", side_effect=AssertionError("external work")),
            patch.object(os, "scandir", side_effect=AssertionError("external work")),
            patch.object(os, "getenv", side_effect=AssertionError("external work")),
            patch.object(socket, "socket", side_effect=AssertionError("external work")),
            patch.object(socket, "create_connection", side_effect=AssertionError("external work")),
            patch.object(sqlite3, "connect", side_effect=AssertionError("external work")),
            patch.object(subprocess, "run", side_effect=AssertionError("external work")),
            patch.object(subprocess, "Popen", side_effect=AssertionError("external work")),
            patch.object(urllib.request, "urlopen", side_effect=AssertionError("external work")),
            patch.object(urllib.request, "urlretrieve", side_effect=AssertionError("external work")),
            patch.object(time, "time", side_effect=AssertionError("external work")),
            patch.object(time, "monotonic", side_effect=AssertionError("external work")),
            patch.object(time, "perf_counter", side_effect=AssertionError("external work")),
            patch.object(random, "random", side_effect=AssertionError("external work")),
            patch.object(random, "getrandbits", side_effect=AssertionError("external work")),
            patch.object(random, "randint", side_effect=AssertionError("external work")),
            patch.object(secrets, "token_hex", side_effect=AssertionError("external work")),
            patch.object(secrets, "token_urlsafe", side_effect=AssertionError("external work")),
            patch.object(uuid, "uuid4", side_effect=AssertionError("external work")),
        )
        with ExitStack() as stack:
            for guard in guards:
                stack.enter_context(guard)
            for name in (
                "authenticate",
                "issue",
                "consume",
                "replay",
                "revoke",
                "persist",
                "dispatch",
                "execute",
                "invoke",
                "discover_tools",
                "probe_runtime",
                "provider_call",
            ):
                stack.enter_context(
                    patch.object(
                        subject,
                        name,
                        create=True,
                        side_effect=AssertionError("operational call"),
                    )
                )
            intrinsic_valid = validate_agent_execution_authorization_grant(valid)
            intrinsic_invalid = validate_agent_execution_authorization_grant(invalid)
            collection_valid = self.validate_collection([valid])
            collection_invalid = self.validate_collection([valid, valid])
        self.assertTrue(intrinsic_valid.valid and collection_valid.valid)
        self.assertFalse(intrinsic_invalid.valid or collection_invalid.valid)

    def test_repeated_validation_has_no_consumption_or_hidden_state(self) -> None:
        value = grant()
        first = validate_agent_execution_authorization_grant(value)
        second = validate_agent_execution_authorization_grant(value)
        first_collection = self.validate_collection([value])
        second_collection = self.validate_collection([value])
        self.assertEqual(first, second)
        self.assertEqual(first_collection, second_collection)
        self.assert_no_operational_claims(value)


if __name__ == "__main__":
    unittest.main()
