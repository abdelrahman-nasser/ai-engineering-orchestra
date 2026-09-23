"""Focused evidence tests for the private AIO-046 SQLite experiment.

The suite uses only synthetic values and temporary local SQLite files.  The
resource value is a lexical sentinel; no test opens, stats, or resolves it.
"""

from __future__ import annotations

import builtins
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import io
import json
import multiprocessing
import os
from pathlib import Path
from queue import Empty
import socket
import sqlite3
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
from experiments.authorization_domain_admission.sqlite_store import (
    FAULT_AFTER_BEGIN,
    FAULT_AFTER_CHECKS,
    FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
    FAULT_AFTER_INSERT_BEFORE_COMMIT,
    FAULT_BEFORE_TRANSACTION,
    ExperimentProvisioningError,
    ExperimentStorageError,
    FixedAuthorityClock,
    SQLiteAuthorizationDomainLedger,
    SyntheticFreshPrerequisiteSource,
    SyntheticTrustCoordinator,
    TrustedLedgerConfiguration,
    decode_binding,
    decode_grant,
    encode_binding,
    encode_grant,
)
from experiments.authorization_domain_admission.worker import (
    lock_holder_worker,
    run_worker,
)


ROOT = Path(__file__).absolute().parents[1]
RESOURCE = "synthetic/input.txt"
DOMAIN = "authorization-domain::aio-046-synthetic"
DECISION = datetime(2026, 9, 23, 10, 0, 0, tzinfo=timezone.utc)


def synthetic_contract(**changes: str) -> AgentExecutionContract:
    values = {
        "task_id": "AIO-046",
        "workflow_id": "architecture-change",
        "stage_id": "implementation",
        "role_id": "software-engineer",
        "actor_id": "actor::synthetic",
        "runtime_option_id": "runtime::synthetic",
        "option_id": "inference::synthetic",
        "environment_id": "environment::synthetic",
        "operation_id": "repository_file_read",
        "resource": RESOURCE,
        "execution_mode": "critical",
    }
    values.update(changes)
    return AgentExecutionContract(**values)


def synthetic_run(
    run_id: str = "run::aio-046-001",
    *,
    contract: AgentExecutionContract | None = None,
) -> AgentExecutionRun:
    return AgentExecutionRun(run_id, contract or synthetic_contract())


def synthetic_grant(
    grant_id: str = "grant::aio-046-001",
    *,
    run: AgentExecutionRun | None = None,
    domain: str = DOMAIN,
    issued_at: str = "2026-09-23T09:00:00Z",
    expires_at: str = "2026-09-23T11:00:00Z",
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id,
        run or synthetic_run(),
        domain,
        "human",
        "human::synthetic-authority",
        "aio-046:synthetic-approval",
        issued_at,
        expires_at,
    )


def synthetic_binding(
    run: AgentExecutionRun,
    tool_id: str = "tool::synthetic-repository-reader::v1",
) -> AgentOperationToolBinding:
    return AgentOperationToolBinding(run, tool_id)


def process_document(value: str) -> dict[str, object]:
    return json.loads(value)


class AuthorizationDomainAdmissionExperimentTests(unittest.TestCase):
    """One bounded test fixture per temporary authoritative ledger."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="aio-046-")
        self.temp_path = Path(self.temporary.name)
        self.database_path = self.temp_path / "ledger.sqlite"
        self.configuration = TrustedLedgerConfiguration(
            DOMAIN,
            self.database_path,
        )
        self.settings = SQLiteAuthorizationDomainLedger.provision(
            self.configuration
        )
        self.run = synthetic_run()
        self.grant = synthetic_grant(run=self.run)
        self.binding = synthetic_binding(self.run)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def ledger_bundle(
        self,
        *,
        instant: datetime | None = DECISION,
        clock_failure: str | None = None,
        configuration: TrustedLedgerConfiguration | None = None,
        trust: SyntheticTrustCoordinator | None = None,
    ) -> tuple[
        SQLiteAuthorizationDomainLedger,
        SyntheticTrustCoordinator,
        FixedAuthorityClock,
    ]:
        coordinator = trust or SyntheticTrustCoordinator()
        clock = FixedAuthorityClock(instant, failure=clock_failure)
        ledger = SQLiteAuthorizationDomainLedger(
            configuration or self.configuration,
            authority_clock=clock,
            trust_coordinator=coordinator,
        )
        return ledger, coordinator, clock

    @staticmethod
    def fresh(
        *,
        execution_mode: str = "critical",
        failure: str | None = None,
        **overrides: str,
    ) -> SyntheticFreshPrerequisiteSource:
        return SyntheticFreshPrerequisiteSource(
            execution_mode=execution_mode,
            subject_overrides=overrides or None,
            failure=failure,
        )

    def trusted_request(
        self,
        coordinator: SyntheticTrustCoordinator,
        *,
        grant: AgentExecutionAuthorizationGrant | None = None,
        binding: AgentOperationToolBinding | None = None,
        expected_domain: str = DOMAIN,
    ) -> object:
        return coordinator.trusted_admission(
            grant or self.grant,
            binding or self.binding,
            expected_authorization_domain_id=expected_domain,
        )

    def raw_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.database_path),
            isolation_level=None,
        )
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def worker_spec(
        self,
        *,
        grant: AgentExecutionAuthorizationGrant | None = None,
        binding: AgentOperationToolBinding | None = None,
        instant: datetime = DECISION,
        operation: str = "admit",
        database_path: Path | None = None,
        domain: str = DOMAIN,
        **extra: object,
    ) -> dict[str, object]:
        selected_grant = grant or self.grant
        specification: dict[str, object] = {
            "authorization_domain_id": domain,
            "database_path": str(database_path or self.database_path),
            "clock_instant": instant.isoformat(),
            "operation": operation,
            "grant": process_document(encode_grant(selected_grant)),
        }
        if operation == "admit":
            specification["binding"] = process_document(
                encode_binding(binding or self.binding)
            )
        specification.update(extra)
        return specification

    @staticmethod
    def stop_process(process: multiprocessing.Process) -> None:
        process.join(15)
        if process.is_alive():
            process.terminate()
            process.join(5)
        if process.is_alive():
            process.kill()
            process.join(5)

    def run_spawned(
        self,
        specification: dict[str, object],
    ) -> tuple[dict[str, object], int]:
        context = multiprocessing.get_context("spawn")
        queue = context.Queue(maxsize=2)
        process = context.Process(target=run_worker, args=(specification, queue))
        try:
            process.start()
            self.stop_process(process)
            result = queue.get(timeout=10)
            return result, int(process.exitcode or 0)
        finally:
            if process.is_alive():
                process.terminate()
                process.join(5)
            queue.close()
            queue.join_thread()

    def test_provisioning_records_actual_sqlite_settings(self) -> None:
        self.assertTrue(self.database_path.is_file())
        self.assertEqual(self.settings.sqlite_version, sqlite3.sqlite_version)
        self.assertEqual(self.settings.journal_mode, "wal")
        self.assertEqual(self.settings.synchronous, 2)
        self.assertEqual(self.settings.busy_timeout_ms, 5_000)
        self.assertEqual(self.settings.foreign_keys, 1)
        self.assertEqual(self.settings.locking_mode, "normal")
        self.assertIsNone(self.settings.isolation_level)
        self.assertEqual(self.settings.transaction_mode, "BEGIN IMMEDIATE")
        with self.assertRaises(ExperimentProvisioningError):
            SQLiteAuthorizationDomainLedger.provision(self.configuration)

    def test_configuration_and_operational_open_fail_closed(self) -> None:
        with self.assertRaises(ValueError):
            TrustedLedgerConfiguration("", self.temp_path / "empty.sqlite")
        with self.assertRaises(ValueError):
            TrustedLedgerConfiguration(DOMAIN, Path("relative.sqlite"))
        with self.assertRaises(ValueError):
            TrustedLedgerConfiguration(DOMAIN, Path("//server/share/db.sqlite"))
        with self.assertRaises(ValueError):
            TrustedLedgerConfiguration(DOMAIN, self.temp_path / "x.sqlite", -1)

        missing = self.temp_path / "missing.sqlite"
        configuration = TrustedLedgerConfiguration(DOMAIN, missing)
        ledger, trust, clock = self.ledger_bundle(configuration=configuration)
        source = self.fresh()
        result = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=source,
        )
        self.assertEqual(result.outcome, "storage_failure")
        self.assertFalse(missing.exists())
        self.assertEqual(source.collection_count, 0)
        self.assertEqual(clock.sample_count, 0)

    def test_single_success_exact_round_trip_and_fresh_parents(self) -> None:
        ledger, trust, clock = self.ledger_bundle()
        source = self.fresh()
        first = source.collect(self.run)
        second = source.collect(self.run)
        self.assertNotEqual(
            source.parent_identity_history[0],
            source.parent_identity_history[1],
        )
        self.assertEqual(first.candidate_result, second.candidate_result)

        admission_source = self.fresh()
        result = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=admission_source,
        )
        self.assertEqual(result.outcome, "newly_admitted")
        self.assertEqual(result.record.grant, self.grant)
        self.assertEqual(result.record.binding, self.binding)
        self.assertEqual(result.record.decision_time, "2026-09-23T10:00:00.000000Z")
        self.assertEqual(admission_source.collection_count, 1)
        self.assertEqual(clock.sample_count, 1)
        self.assertEqual(ledger.admissions(), (result.record,))
        self.assertEqual(ledger.revocations(), ())
        self.assertEqual(ledger.watermark()[0], result.record.decision_time)

    def test_exact_retry_returns_history_without_freshness_or_clock(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        request = self.trusted_request(trust)
        first = ledger.admit_or_return_existing(request, fresh_source=self.fresh())
        self.assertEqual(first.outcome, "newly_admitted")

        retry_ledger, retry_trust, retry_clock = self.ledger_bundle(
            clock_failure="must not sample"
        )
        retry_source = self.fresh(failure="must not collect")
        retry = retry_ledger.admit_or_return_existing(
            self.trusted_request(retry_trust),
            fresh_source=retry_source,
        )
        self.assertEqual(retry.outcome, "existing_exact_admission")
        self.assertEqual(retry.record, first.record)
        self.assertEqual(retry_source.collection_count, 0)
        self.assertEqual(retry_clock.sample_count, 0)

    def test_untrusted_domain_and_run_mismatch_reject_before_state(self) -> None:
        ledger, trust, clock = self.ledger_bundle()
        source = self.fresh()
        self.assertEqual(
            ledger.admit_or_return_existing(object(), fresh_source=source).outcome,
            "untrusted",
        )
        other_trust = SyntheticTrustCoordinator()
        foreign = other_trust.trusted_admission(
            self.grant,
            self.binding,
            expected_authorization_domain_id=DOMAIN,
        )
        self.assertEqual(
            ledger.admit_or_return_existing(foreign, fresh_source=source).outcome,
            "untrusted",
        )
        minted = self.trusted_request(trust)
        rebound_envelope = replace(
            minted,
            binding=replace(
                self.binding,
                tool_id="tool::synthetic-envelope-rebound::v1",
            ),
        )
        self.assertEqual(
            ledger.admit_or_return_existing(
                rebound_envelope,
                fresh_source=source,
            ).outcome,
            "untrusted",
        )
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust, expected_domain="domain::other"),
                fresh_source=source,
            ).outcome,
            "domain_mismatch",
        )
        changed_run = synthetic_run(
            self.run.run_id,
            contract=synthetic_contract(actor_id="actor::changed"),
        )
        mismatched_binding = synthetic_binding(changed_run)
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust, binding=mismatched_binding),
                fresh_source=source,
            ).outcome,
            "invalid",
        )
        self.assertEqual(ledger.admissions(), ())
        self.assertEqual(source.collection_count, 0)
        self.assertEqual(clock.sample_count, 0)

    def test_revocation_rejects_a_cloned_rebound_trust_envelope(self) -> None:
        ledger, trust, clock = self.ledger_bundle()
        minted = trust.trusted_revocation(
            self.grant,
            expected_authorization_domain_id=DOMAIN,
        )
        rebound = replace(
            minted,
            grant=replace(
                self.grant,
                provenance_reference="aio-046:forged-envelope",
            ),
        )
        result = ledger.revoke(rebound)
        self.assertEqual(result.outcome, "untrusted")
        self.assertEqual(clock.sample_count, 0)
        self.assertEqual(ledger.revocations(), ())

    def test_fresh_reconstruction_must_match_complete_run_and_mode(self) -> None:
        ledger, trust, clock = self.ledger_bundle()
        changed = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=self.fresh(actor_id="actor::changed"),
        )
        self.assertEqual(changed.outcome, "invalid")
        mode = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=self.fresh(execution_mode="deep"),
        )
        self.assertEqual(mode.outcome, "invalid")
        self.assertEqual(clock.sample_count, 0)
        self.assertEqual(ledger.admissions(), ())

    def test_durable_conflict_classifications(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust), fresh_source=self.fresh()
            ).outcome,
            "newly_admitted",
        )
        changed_binding = replace(
            self.binding,
            tool_id="tool::synthetic-other::v1",
        )
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust, binding=changed_binding),
                fresh_source=self.fresh(failure="must not collect"),
            ).outcome,
            "binding_conflict",
        )
        rebound = replace(
            self.grant,
            provenance_reference="aio-046:changed",
        )
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust, grant=rebound),
                fresh_source=self.fresh(failure="must not collect"),
            ).outcome,
            "grant_identity_conflict",
        )
        second_grant = replace(self.grant, grant_id="grant::aio-046-002")
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust, grant=second_grant),
                fresh_source=self.fresh(failure="must not collect"),
            ).outcome,
            "run_conflict",
        )
        self.assertEqual(len(ledger.admissions()), 1)

    def test_fractional_currentness_boundaries_use_parsed_instants(self) -> None:
        cases = (
            ("2026-09-23T10:00:00.123456Z", "2026-09-23T10:00:01Z", datetime(2026, 9, 23, 10, 0, 0, 123456, tzinfo=timezone.utc), "newly_admitted"),
            ("2026-09-23T10:00:00.123456Z", "2026-09-23T10:00:01Z", datetime(2026, 9, 23, 10, 0, 0, 123455, tzinfo=timezone.utc), "not_yet_current"),
            ("2026-09-23T10:00:00Z", "2026-09-23T10:00:00.750000Z", datetime(2026, 9, 23, 10, 0, 0, 750000, tzinfo=timezone.utc), "expired"),
            ("2026-09-23T10:00:00Z", "2026-09-23T10:00:00.750000Z", datetime(2026, 9, 23, 10, 0, 0, 749999, tzinfo=timezone.utc), "newly_admitted"),
        )
        for index, (issued, expires, decision, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                path = self.temp_path / f"time-{index}.sqlite"
                configuration = TrustedLedgerConfiguration(DOMAIN, path)
                SQLiteAuthorizationDomainLedger.provision(configuration)
                run = synthetic_run(f"run::time-{index}")
                grant = synthetic_grant(
                    f"grant::time-{index}",
                    run=run,
                    issued_at=issued,
                    expires_at=expires,
                )
                binding = synthetic_binding(run)
                ledger, trust, _ = self.ledger_bundle(
                    instant=decision,
                    configuration=configuration,
                )
                result = ledger.admit_or_return_existing(
                    trust.trusted_admission(
                        grant,
                        binding,
                        expected_authorization_domain_id=DOMAIN,
                    ),
                    fresh_source=self.fresh(),
                )
                self.assertEqual(result.outcome, expected)
                self.assertEqual(ledger.watermark()[0], decision.strftime("%Y-%m-%dT%H:%M:%S.%fZ"))

    def test_clock_failure_offset_and_regression_fail_closed(self) -> None:
        for instant, failure in (
            (None, "offline"),
            (datetime(2026, 9, 23, 10, 0), None),
            (datetime(2026, 9, 23, 12, 0, tzinfo=timezone(timedelta(hours=2))), None),
        ):
            ledger, trust, _ = self.ledger_bundle(
                instant=instant,
                clock_failure=failure,
            )
            result = ledger.admit_or_return_existing(
                self.trusted_request(trust),
                fresh_source=self.fresh(),
            )
            self.assertEqual(result.outcome, "clock_failure")
            self.assertEqual(ledger.admissions(), ())
            self.assertEqual(ledger.watermark(), (None, None))

        ledger, trust, _ = self.ledger_bundle()
        first = ledger.admit_or_return_existing(
            self.trusted_request(trust), fresh_source=self.fresh()
        )
        self.assertEqual(first.outcome, "newly_admitted")
        later_run = synthetic_run("run::clock-regression")
        later_grant = synthetic_grant("grant::clock-regression", run=later_run)
        earlier, earlier_trust, _ = self.ledger_bundle(
            instant=DECISION - timedelta(microseconds=1)
        )
        result = earlier.admit_or_return_existing(
            earlier_trust.trusted_admission(
                later_grant,
                synthetic_binding(later_run),
                expected_authorization_domain_id=DOMAIN,
            ),
            fresh_source=self.fresh(),
        )
        self.assertEqual(result.outcome, "clock_regression")
        self.assertEqual(len(ledger.admissions()), 1)
        self.assertEqual(ledger.watermark()[0], first.record.decision_time)

    def test_temporal_and_revoked_denials_advance_watermark(self) -> None:
        expired = replace(self.grant, expires_at="2026-09-23T10:00:00Z")
        ledger, trust, _ = self.ledger_bundle()
        result = ledger.admit_or_return_existing(
            self.trusted_request(trust, grant=expired),
            fresh_source=self.fresh(),
        )
        self.assertEqual(result.outcome, "expired")
        self.assertEqual(ledger.watermark()[0], "2026-09-23T10:00:00.000000Z")
        self.assertEqual(ledger.admissions(), ())

        path = self.temp_path / "revoked-denial.sqlite"
        configuration = TrustedLedgerConfiguration(DOMAIN, path)
        SQLiteAuthorizationDomainLedger.provision(configuration)
        revoker, revoke_trust, _ = self.ledger_bundle(
            instant=DECISION - timedelta(minutes=1),
            configuration=configuration,
        )
        revoked = revoker.revoke(
            revoke_trust.trusted_revocation(
                self.grant,
                expected_authorization_domain_id=DOMAIN,
            )
        )
        self.assertEqual(revoked.outcome, "newly_revoked")
        admitting, admission_trust, _ = self.ledger_bundle(
            configuration=configuration
        )
        denied = admitting.admit_or_return_existing(
            admission_trust.trusted_admission(
                self.grant,
                self.binding,
                expected_authorization_domain_id=DOMAIN,
            ),
            fresh_source=self.fresh(),
        )
        self.assertEqual(denied.outcome, "revoked")
        self.assertEqual(admitting.watermark()[0], "2026-09-23T10:00:00.000000Z")

    def test_revocation_exact_retry_identity_and_both_serial_orders(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        revocation = trust.trusted_revocation(
            self.grant,
            expected_authorization_domain_id=DOMAIN,
        )
        first = ledger.revoke(revocation)
        self.assertEqual(first.outcome, "newly_revoked")
        retry_ledger, retry_trust, retry_clock = self.ledger_bundle(
            clock_failure="must not sample"
        )
        retry = retry_ledger.revoke(
            retry_trust.trusted_revocation(
                self.grant,
                expected_authorization_domain_id=DOMAIN,
            )
        )
        self.assertEqual(retry.outcome, "existing_exact_revocation")
        self.assertEqual(retry.record, first.record)
        self.assertEqual(retry_clock.sample_count, 0)
        admission = ledger.admit_or_return_existing(
            self.trusted_request(trust), fresh_source=self.fresh()
        )
        self.assertEqual(admission.outcome, "revoked")

        path = self.temp_path / "admission-first.sqlite"
        configuration = TrustedLedgerConfiguration(DOMAIN, path)
        SQLiteAuthorizationDomainLedger.provision(configuration)
        admitted_ledger, admitted_trust, _ = self.ledger_bundle(
            configuration=configuration
        )
        admitted = admitted_ledger.admit_or_return_existing(
            admitted_trust.trusted_admission(
                self.grant,
                self.binding,
                expected_authorization_domain_id=DOMAIN,
            ),
            fresh_source=self.fresh(),
        )
        self.assertEqual(admitted.outcome, "newly_admitted")
        revoked = admitted_ledger.revoke(
            admitted_trust.trusted_revocation(
                self.grant,
                expected_authorization_domain_id=DOMAIN,
            )
        )
        self.assertEqual(revoked.outcome, "newly_revoked")
        self.assertEqual(len(admitted_ledger.admissions()), 1)
        self.assertEqual(len(admitted_ledger.revocations()), 1)

    def test_revocation_rejects_identity_rebound_across_tables(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        admitted = ledger.admit_or_return_existing(
            self.trusted_request(trust), fresh_source=self.fresh()
        )
        self.assertEqual(admitted.outcome, "newly_admitted")
        rebound = replace(
            self.grant,
            provenance_reference="aio-046:rebound",
        )
        rejected = ledger.revoke(
            trust.trusted_revocation(
                rebound,
                expected_authorization_domain_id=DOMAIN,
            )
        )
        self.assertEqual(rejected.outcome, "revocation_identity_conflict")
        self.assertEqual(ledger.revocations(), ())
        exact = ledger.revoke(
            trust.trusted_revocation(
                self.grant,
                expected_authorization_domain_id=DOMAIN,
            )
        )
        self.assertEqual(exact.outcome, "newly_revoked")

    def test_distinct_grants_for_one_run_can_each_be_revoked(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        second = replace(self.grant, grant_id="grant::aio-046-002")
        for grant in (self.grant, second):
            result = ledger.revoke(
                trust.trusted_revocation(
                    grant,
                    expected_authorization_domain_id=DOMAIN,
                )
            )
            self.assertEqual(result.outcome, "newly_revoked")
        self.assertEqual(len(ledger.revocations()), 2)

    def test_deterministic_codec_and_corruption_fail_closed(self) -> None:
        encoded_grant = encode_grant(self.grant)
        encoded_binding = encode_binding(self.binding)
        self.assertEqual(encode_grant(self.grant), encoded_grant)
        self.assertEqual(encode_binding(self.binding), encoded_binding)
        self.assertEqual(decode_grant(encoded_grant), self.grant)
        self.assertEqual(decode_binding(encoded_binding), self.binding)
        with self.assertRaises(ValueError):
            decode_grant(" " + encoded_grant)
        with self.assertRaises(ValueError):
            decode_grant('{"grant_id":"a","grant_id":"b"}')

        ledger, trust, _ = self.ledger_bundle()
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust), fresh_source=self.fresh()
            ).outcome,
            "newly_admitted",
        )
        connection = self.raw_connection()
        try:
            connection.execute("DROP TRIGGER admissions_no_update")
            connection.execute(
                "UPDATE admissions SET grant_json = ?",
                (" " + encoded_grant,),
            )
        finally:
            connection.close()
        with self.assertRaises(ExperimentStorageError):
            ledger.admissions()
        retry = ledger.admit_or_return_existing(
            self.trusted_request(trust), fresh_source=self.fresh()
        )
        self.assertEqual(retry.outcome, "storage_failure")

    def test_sql_rows_and_metadata_are_append_only(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        self.assertEqual(
            ledger.admit_or_return_existing(
                self.trusted_request(trust), fresh_source=self.fresh()
            ).outcome,
            "newly_admitted",
        )
        self.assertEqual(
            ledger.revoke(
                trust.trusted_revocation(
                    self.grant,
                    expected_authorization_domain_id=DOMAIN,
                )
            ).outcome,
            "newly_revoked",
        )
        statements = (
            "UPDATE admissions SET decision_time = decision_time",
            "DELETE FROM admissions",
            "UPDATE revocations SET decision_time = decision_time",
            "DELETE FROM revocations",
            "UPDATE ledger_metadata SET schema_version = 2",
            "DELETE FROM ledger_metadata",
        )
        connection = self.raw_connection()
        try:
            for statement in statements:
                with self.subTest(statement=statement):
                    with self.assertRaises(sqlite3.IntegrityError):
                        connection.execute(statement)
        finally:
            connection.close()
        self.assertEqual(len(ledger.admissions()), 1)
        self.assertEqual(len(ledger.revocations()), 1)

    def test_response_loss_returns_commit_unknown_then_exact_retry(self) -> None:
        ledger, trust, _ = self.ledger_bundle()

        def lose_response(point: str) -> None:
            if point == FAULT_AFTER_COMMIT_BEFORE_RESPONSE:
                raise RuntimeError("synthetic response loss")

        first = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=self.fresh(),
            fault_hook=lose_response,
        )
        self.assertEqual(first.outcome, "commit_unknown")
        self.assertTrue(first.retryable)
        self.assertTrue(first.indeterminate)
        self.assertEqual(len(ledger.admissions()), 1)
        retry = ledger.admit_or_return_existing(
            self.trusted_request(trust),
            fresh_source=self.fresh(failure="must not collect"),
        )
        self.assertEqual(retry.outcome, "existing_exact_admission")

    def test_raised_precommit_faults_leave_no_partial_state(self) -> None:
        for index, fault in enumerate(
            (
                FAULT_BEFORE_TRANSACTION,
                FAULT_AFTER_BEGIN,
                FAULT_AFTER_CHECKS,
                FAULT_AFTER_INSERT_BEFORE_COMMIT,
            )
        ):
            path = self.temp_path / f"rollback-{index}.sqlite"
            configuration = TrustedLedgerConfiguration(DOMAIN, path)
            SQLiteAuthorizationDomainLedger.provision(configuration)
            ledger, trust, _ = self.ledger_bundle(configuration=configuration)

            def fail(point: str, expected: str = fault) -> None:
                if point == expected:
                    raise RuntimeError("synthetic precommit failure")

            result = ledger.admit_or_return_existing(
                trust.trusted_admission(
                    self.grant,
                    self.binding,
                    expected_authorization_domain_id=DOMAIN,
                ),
                fresh_source=self.fresh(),
                fault_hook=fail,
            )
            self.assertEqual(result.outcome, "storage_failure")
            self.assertEqual(ledger.admissions(), ())
            self.assertEqual(ledger.watermark(), (None, None))

    def test_spawned_same_request_has_one_new_and_one_existing(self) -> None:
        context = multiprocessing.get_context("spawn")
        queue = context.Queue(maxsize=4)
        start = context.Event()
        ready = (context.Event(), context.Event())
        processes = [
            context.Process(
                target=run_worker,
                args=(self.worker_spec(), queue),
                kwargs={"ready_event": ready[index], "start_event": start},
            )
            for index in range(2)
        ]
        try:
            for process in processes:
                process.start()
            self.assertTrue(ready[0].wait(10))
            self.assertTrue(ready[1].wait(10))
            start.set()
            for process in processes:
                self.stop_process(process)
                self.assertEqual(process.exitcode, 0)
            results = [queue.get(timeout=10), queue.get(timeout=10)]
            self.assertEqual(
                {result["outcome"] for result in results},
                {"newly_admitted", "existing_exact_admission"},
            )
            self.assertEqual(len({result["pid"] for result in results}), 2)
            self.assertNotIn(os.getpid(), {result["pid"] for result in results})
            ledger, _, _ = self.ledger_bundle()
            self.assertEqual(len(ledger.admissions()), 1)
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(5)
            queue.close()
            queue.join_thread()

    def test_spawned_binding_and_run_conflicts_have_one_winner(self) -> None:
        changed_binding = replace(
            self.binding,
            tool_id="tool::synthetic-other::v1",
        )
        cases = (
            (
                self.worker_spec(),
                self.worker_spec(binding=changed_binding),
                {"newly_admitted", "binding_conflict"},
                "binding",
            ),
            (
                self.worker_spec(database_path=self.temp_path / "run.sqlite"),
                self.worker_spec(
                    grant=replace(self.grant, grant_id="grant::second"),
                    database_path=self.temp_path / "run.sqlite",
                ),
                {"newly_admitted", "run_conflict"},
                "run",
            ),
        )
        SQLiteAuthorizationDomainLedger.provision(
            TrustedLedgerConfiguration(DOMAIN, self.temp_path / "run.sqlite")
        )
        for first_spec, second_spec, expected, label in cases:
            with self.subTest(label=label):
                context = multiprocessing.get_context("spawn")
                queue = context.Queue(maxsize=4)
                start = context.Event()
                ready_a = context.Event()
                ready_b = context.Event()
                processes = (
                    context.Process(
                        target=run_worker,
                        args=(first_spec, queue),
                        kwargs={"ready_event": ready_a, "start_event": start},
                    ),
                    context.Process(
                        target=run_worker,
                        args=(second_spec, queue),
                        kwargs={"ready_event": ready_b, "start_event": start},
                    ),
                )
                try:
                    for process in processes:
                        process.start()
                    self.assertTrue(ready_a.wait(10))
                    self.assertTrue(ready_b.wait(10))
                    start.set()
                    for process in processes:
                        self.stop_process(process)
                        self.assertEqual(process.exitcode, 0)
                    results = [queue.get(timeout=10), queue.get(timeout=10)]
                    self.assertEqual(
                        {result["outcome"] for result in results},
                        expected,
                    )
                finally:
                    for process in processes:
                        if process.is_alive():
                            process.terminate()
                            process.join(5)
                    queue.close()
                    queue.join_thread()

    def test_spawned_busy_writer_fails_retryably_without_fallback(self) -> None:
        busy_path = self.temp_path / "busy.sqlite"
        configuration = TrustedLedgerConfiguration(DOMAIN, busy_path, 100)
        SQLiteAuthorizationDomainLedger.provision(configuration)
        context = multiprocessing.get_context("spawn")
        ready = context.Event()
        release = context.Event()
        holder = context.Process(
            target=lock_holder_worker,
            args=({"database_path": str(busy_path)}, ready, release),
        )
        queue = context.Queue(maxsize=2)
        contender = context.Process(
            target=run_worker,
            args=(
                self.worker_spec(
                    database_path=busy_path,
                    busy_timeout_ms=100,
                ),
                queue,
            ),
        )
        try:
            holder.start()
            self.assertTrue(ready.wait(10))
            contender.start()
            self.stop_process(contender)
            result = queue.get(timeout=10)
            self.assertEqual(result["outcome"], "storage_busy")
            self.assertTrue(result["retryable"])
            self.assertEqual(result["clock_sample_count"], 0)
            release.set()
            self.stop_process(holder)
            self.assertEqual(holder.exitcode, 0)
            ledger, _, _ = self.ledger_bundle(configuration=configuration)
            self.assertEqual(ledger.admissions(), ())
        finally:
            release.set()
            for process in (contender, holder):
                if process.is_alive():
                    process.terminate()
                    process.join(5)
            queue.close()
            queue.join_thread()

    def test_hard_exit_faults_roll_back_and_postcommit_retry_recovers(self) -> None:
        for index, point in enumerate(
            (
                FAULT_BEFORE_TRANSACTION,
                FAULT_AFTER_BEGIN,
                FAULT_AFTER_CHECKS,
                FAULT_AFTER_INSERT_BEFORE_COMMIT,
            )
        ):
            path = self.temp_path / f"crash-{index}.sqlite"
            configuration = TrustedLedgerConfiguration(DOMAIN, path)
            SQLiteAuthorizationDomainLedger.provision(configuration)
            context = multiprocessing.get_context("spawn")
            queue = context.Queue(maxsize=1)
            process = context.Process(
                target=run_worker,
                args=(
                    self.worker_spec(database_path=path, fault_point=point),
                    queue,
                ),
            )
            try:
                process.start()
                self.stop_process(process)
                self.assertEqual(process.exitcode, 91)
                with self.assertRaises(Empty):
                    queue.get(timeout=0.2)
                ledger, _, _ = self.ledger_bundle(configuration=configuration)
                self.assertEqual(ledger.admissions(), ())
                self.assertEqual(ledger.watermark(), (None, None))
            finally:
                if process.is_alive():
                    process.terminate()
                    process.join(5)
                queue.close()
                queue.join_thread()

        commit_path = self.temp_path / "crash-after-commit.sqlite"
        commit_config = TrustedLedgerConfiguration(DOMAIN, commit_path)
        SQLiteAuthorizationDomainLedger.provision(commit_config)
        context = multiprocessing.get_context("spawn")
        queue = context.Queue(maxsize=1)
        process = context.Process(
            target=run_worker,
            args=(
                self.worker_spec(
                    database_path=commit_path,
                    fault_point=FAULT_AFTER_COMMIT_BEFORE_RESPONSE,
                ),
                queue,
            ),
        )
        try:
            process.start()
            self.stop_process(process)
            self.assertEqual(process.exitcode, 91)
            with self.assertRaises(Empty):
                queue.get(timeout=0.2)
        finally:
            if process.is_alive():
                process.terminate()
                process.join(5)
            queue.close()
            queue.join_thread()
        retry, exitcode = self.run_spawned(
            self.worker_spec(
                database_path=commit_path,
                fresh_failure="must not collect",
                clock_failure="must not sample",
            )
        )
        self.assertEqual(exitcode, 0)
        self.assertEqual(retry["outcome"], "existing_exact_admission")
        self.assertEqual(retry["fresh_collection_count"], 0)
        self.assertEqual(retry["clock_sample_count"], 0)

    def test_spawned_revocation_and_admission_both_lock_orders(self) -> None:
        cases = (
            ("revoke", "admit", "newly_revoked", "revoked"),
            ("admit", "revoke", "newly_admitted", "newly_revoked"),
        )
        for index, (first_op, second_op, first_outcome, second_outcome) in enumerate(cases):
            with self.subTest(first=first_op):
                path = self.temp_path / f"race-{index}.sqlite"
                configuration = TrustedLedgerConfiguration(DOMAIN, path)
                SQLiteAuthorizationDomainLedger.provision(configuration)
                context = multiprocessing.get_context("spawn")
                queue = context.Queue(maxsize=4)
                phase = context.Event()
                release = context.Event()
                first = context.Process(
                    target=run_worker,
                    args=(
                        self.worker_spec(
                            operation=first_op,
                            database_path=path,
                            pause_point=FAULT_AFTER_INSERT_BEFORE_COMMIT,
                        ),
                        queue,
                    ),
                    kwargs={"phase_event": phase, "release_event": release},
                )
                second = context.Process(
                    target=run_worker,
                    args=(
                        self.worker_spec(operation=second_op, database_path=path),
                        queue,
                    ),
                )
                try:
                    first.start()
                    self.assertTrue(phase.wait(10))
                    second.start()
                    release.set()
                    self.stop_process(first)
                    self.stop_process(second)
                    self.assertEqual(first.exitcode, 0)
                    self.assertEqual(second.exitcode, 0)
                    results = [queue.get(timeout=10), queue.get(timeout=10)]
                    by_outcome = {result["outcome"] for result in results}
                    self.assertEqual(by_outcome, {first_outcome, second_outcome})
                    ledger, _, _ = self.ledger_bundle(configuration=configuration)
                    self.assertEqual(len(ledger.revocations()), 1)
                    self.assertEqual(
                        len(ledger.admissions()),
                        0 if first_op == "revoke" else 1,
                    )
                finally:
                    release.set()
                    for process in (first, second):
                        if process.is_alive():
                            process.terminate()
                            process.join(5)
                    queue.close()
                    queue.join_thread()

    def test_fresh_spawn_restart_reopens_durable_history(self) -> None:
        first, first_code = self.run_spawned(self.worker_spec())
        self.assertEqual(first_code, 0)
        self.assertEqual(first["outcome"], "newly_admitted")
        second, second_code = self.run_spawned(
            self.worker_spec(
                fresh_failure="must not collect",
                clock_failure="must not sample",
            )
        )
        self.assertEqual(second_code, 0)
        self.assertEqual(second["outcome"], "existing_exact_admission")
        self.assertNotEqual(first["pid"], second["pid"])
        self.assertEqual(first["record"], second["record"])

    def test_in_memory_and_split_database_counterexamples(self) -> None:
        memory = sqlite3.connect(":memory:")
        memory.execute("CREATE TABLE admissions (value TEXT)")
        memory.execute("INSERT INTO admissions VALUES ('lost')")
        memory.close()
        restarted = sqlite3.connect(":memory:")
        try:
            with self.assertRaises(sqlite3.OperationalError):
                restarted.execute("SELECT * FROM admissions").fetchall()
        finally:
            restarted.close()

        outcomes = []
        for index in range(2):
            path = self.temp_path / f"split-{index}.sqlite"
            configuration = TrustedLedgerConfiguration(DOMAIN, path)
            SQLiteAuthorizationDomainLedger.provision(configuration)
            ledger, trust, _ = self.ledger_bundle(configuration=configuration)
            outcomes.append(
                ledger.admit_or_return_existing(
                    trust.trusted_admission(
                        self.grant,
                        self.binding,
                        expected_authorization_domain_id=DOMAIN,
                    ),
                    fresh_source=self.fresh(),
                ).outcome
            )
        self.assertEqual(outcomes, ["newly_admitted", "newly_admitted"])

    def test_no_resource_network_subprocess_or_dispatch_access(self) -> None:
        ledger, trust, _ = self.ledger_bundle()
        original_open = builtins.open
        original_io_open = io.open
        original_os_open = os.open
        original_stat = os.stat
        original_resolve = Path.resolve

        def protected(value: object) -> bool:
            return str(value).replace("\\", "/") == RESOURCE

        def guard_open(file: object, *args: object, **kwargs: object) -> object:
            if protected(file):
                raise AssertionError("protected lexical resource was opened")
            return original_open(file, *args, **kwargs)

        def guard_io_open(file: object, *args: object, **kwargs: object) -> object:
            if protected(file):
                raise AssertionError("protected lexical resource was opened")
            return original_io_open(file, *args, **kwargs)

        def guard_os_open(file: object, *args: object, **kwargs: object) -> int:
            if protected(file):
                raise AssertionError("protected lexical resource was opened")
            return original_os_open(file, *args, **kwargs)

        def guard_stat(file: object, *args: object, **kwargs: object) -> os.stat_result:
            if protected(file):
                raise AssertionError("protected lexical resource was stated")
            return original_stat(file, *args, **kwargs)

        def guard_resolve(path: Path, *args: object, **kwargs: object) -> Path:
            if protected(path):
                raise AssertionError("protected lexical resource was resolved")
            return original_resolve(path, *args, **kwargs)

        with (
            patch("builtins.open", side_effect=guard_open),
            patch("io.open", side_effect=guard_io_open),
            patch("os.open", side_effect=guard_os_open),
            patch("os.stat", side_effect=guard_stat),
            patch.object(Path, "resolve", guard_resolve),
            patch.object(socket, "socket", side_effect=AssertionError("network")),
            patch.object(socket, "create_connection", side_effect=AssertionError("network")),
            patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess")),
            patch.object(subprocess, "run", side_effect=AssertionError("subprocess")),
        ):
            result = ledger.admit_or_return_existing(
                self.trusted_request(trust),
                fresh_source=self.fresh(),
            )
        self.assertEqual(result.outcome, "newly_admitted")
        self.assertEqual(result.record.grant.run.contract.resource, RESOURCE)
        self.assertFalse(hasattr(self.grant, "used"))
        self.assertFalse(hasattr(self.grant, "consumed"))
        self.assertFalse(hasattr(self.grant, "revoked"))

    def test_experiment_is_not_packaged_or_exported(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            project = tomllib.load(handle)
        setuptools = project["tool"]["setuptools"]
        self.assertFalse(setuptools["include-package-data"])
        self.assertEqual(
            setuptools["packages"],
            [
                "engineering_orchestration",
                "engineering_orchestration._schemas",
                "engineering_orchestration._roles",
            ],
        )
        self.assertNotIn("experiments", json.dumps(setuptools))


if __name__ == "__main__":
    unittest.main()
