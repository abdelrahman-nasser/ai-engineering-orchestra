"""Focused production-backend tests for the AIO-047 SQLite authority store."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import multiprocessing
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import threading
import unittest

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import AgentExecutionContract
from engineering_orchestration.agent_execution_dispatch_admission import (
    AgentExecutionDispatchAdmission,
)
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    _mint_admission_request,
    _mint_authoritative_lookup_request,
    _mint_guarded_history_request,
    _mint_revocation_request,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding,
)
import engineering_orchestration.sqlite_agent_execution_dispatch_admission_store as subject
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    SQLITE_APPLICATION_ID,
    SqliteAdmissionStoreConfigurationError,
    SqliteAdmissionStoreIncompatibleSchemaError,
    SqliteAdmissionStoreIntegrityError,
    SqliteAgentExecutionDispatchAdmissionStore,
    SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
)
from tests.agent_execution_dispatch_admission_store_conformance import (
    AdmissionStoreConformanceHarness,
    AgentExecutionDispatchAdmissionStoreConformanceMixin,
    CONFORMANCE_DOMAIN_ID,
)


DOMAIN_ID = "authorization-domain::sqlite-aio-047-tests"
LEDGER_ID = "ledger::sqlite-aio-047-tests"
DECISION_TIME = datetime(2026, 9, 23, 10, 30, tzinfo=timezone.utc)


def make_contract(*, task_id: str = "AIO-047-synthetic") -> AgentExecutionContract:
    """Build synthetic declarative intent; it is never dispatched."""

    return AgentExecutionContract(
        task_id,
        "architecture-change",
        "implement",
        "software-engineer",
        "actor::synthetic",
        "runtime::synthetic",
        "option::synthetic",
        "environment::synthetic",
        "repository_file_read",
        "synthetic/input.txt",
        "critical",
    )


def make_run(
    run_id: str = "run::sqlite-aio-047-one",
    *,
    task_id: str = "AIO-047-synthetic",
) -> AgentExecutionRun:
    return AgentExecutionRun(run_id, make_contract(task_id=task_id))


def make_grant(
    *,
    bound_run: AgentExecutionRun | None = None,
    grant_id: str = "grant::sqlite-aio-047-one",
    domain_id: str = DOMAIN_ID,
    issuer_kind: str = "policy",
    issuer_id: str = "issuer::sqlite-aio-047",
    provenance_reference: str = "approval::synthetic-aio-047",
    issued_at: str = "2026-09-23T10:00:00Z",
    expires_at: str = "2026-09-23T11:00:00Z",
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id,
        make_run() if bound_run is None else bound_run,
        domain_id,
        issuer_kind,
        issuer_id,
        provenance_reference,
        issued_at,
        expires_at,
    )


def make_binding(
    *,
    bound_run: AgentExecutionRun | None = None,
    tool_id: str = "tool::sqlite-aio-047::v1",
) -> AgentOperationToolBinding:
    return AgentOperationToolBinding(
        make_run() if bound_run is None else bound_run,
        tool_id,
    )


@dataclass
class MutableClock:
    value: object = DECISION_TIME
    calls: int = 0

    def now_utc(self) -> object:
        self.calls += 1
        if isinstance(self.value, BaseException):
            raise self.value
        return self.value


class FaultingStore(SqliteAgentExecutionDispatchAdmissionStore):
    """One-shot protected-seam fault; request data cannot choose the point."""

    def __init__(self, *args: object, fault_point: str, **kwargs: object) -> None:
        self.fault_point = fault_point
        self.fault_count = 0
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def _fault(self, point: str) -> None:
        if point == self.fault_point and self.fault_count == 0:
            self.fault_count += 1
            raise OSError(f"synthetic fault at {point}")


class PausingVerificationStore(SqliteAgentExecutionDispatchAdmissionStore):
    """Pause once after metadata read to force a concurrent WAL commit."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.pause_verification = False
        self.metadata_read = threading.Event()
        self.resume_verification = threading.Event()
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def _verify_metadata(
        self,
        connection: sqlite3.Connection,
        *,
        allow_fenced: bool,
    ):
        metadata = super()._verify_metadata(
            connection,
            allow_fenced=allow_fenced,
        )
        if self.pause_verification:
            self.pause_verification = False
            self.metadata_read.set()
            if not self.resume_verification.wait(10):
                raise AssertionError("verification concurrency test timed out")
        return metadata


class MutatingRequestStore(SqliteAgentExecutionDispatchAdmissionStore):
    """Test-only same-process mutation after writer serialization."""

    def __init__(
        self,
        *args: object,
        grant_to_mutate: AgentExecutionAuthorizationGrant,
        replacement_run: AgentExecutionRun,
        **kwargs: object,
    ) -> None:
        self.grant_to_mutate = grant_to_mutate
        self.replacement_run = replacement_run
        self.mutated = False
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def _fault(self, point: str) -> None:
        if point == "after_begin" and not self.mutated:
            self.mutated = True
            object.__setattr__(
                self.grant_to_mutate,
                "run",
                self.replacement_run,
            )


class HardExitStore(SqliteAgentExecutionDispatchAdmissionStore):
    """Process-crash seam used only by disposable-ledger tests."""

    def __init__(self, *args: object, fault_point: str, **kwargs: object) -> None:
        self.fault_point = fault_point
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def _fault(self, point: str) -> None:
        if point == self.fault_point:
            os._exit(73)


def config_for(
    path: Path,
    *,
    domain_id: str = DOMAIN_ID,
    ledger_id: str = LEDGER_ID,
    generation: int = 1,
    busy_timeout_ms: int = 2_000,
) -> SqliteAgentExecutionDispatchAdmissionStoreConfiguration:
    return SqliteAgentExecutionDispatchAdmissionStoreConfiguration(
        path,
        domain_id,
        ledger_id,
        generation,
        busy_timeout_ms,
    )


def admit_request(
    grant: AgentExecutionAuthorizationGrant,
    binding: AgentOperationToolBinding,
):
    return _mint_admission_request(DOMAIN_ID, grant, binding, grant.run)


def history_request(
    grant: AgentExecutionAuthorizationGrant,
    binding: AgentOperationToolBinding,
):
    return _mint_guarded_history_request(DOMAIN_ID, grant, binding)


def _spawn_store_operation(
    database_path: str,
    grant: AgentExecutionAuthorizationGrant,
    binding: AgentOperationToolBinding,
    operation: str,
    start: object,
    results: object,
) -> None:
    """Spawn-safe worker used only with a disposable synthetic ledger."""

    try:
        configuration = config_for(Path(database_path))
        store = SqliteAgentExecutionDispatchAdmissionStore(
            configuration,
            clock=MutableClock(),
        )
        start.wait(15)  # type: ignore[attr-defined]
        if operation == "admit":
            result = store.admit_or_return_existing(
                admit_request(grant, binding)
            )
        elif operation == "revoke":
            result = store.revoke_or_return_existing(
                _mint_revocation_request(DOMAIN_ID, grant)
            )
        else:  # pragma: no cover - test code owns the closed operation set
            raise AssertionError(operation)
        results.put(("ok", result.outcome.value))  # type: ignore[attr-defined]
    except BaseException as error:  # pragma: no cover - reported to parent test
        results.put(("error", type(error).__name__, str(error)))  # type: ignore[attr-defined]


def _spawn_crashing_admission(
    database_path: str,
    grant: AgentExecutionAuthorizationGrant,
    binding: AgentOperationToolBinding,
    fault_point: str,
) -> None:
    """Hard-exit one child at a precise production-backend fault seam."""

    configuration = config_for(Path(database_path))
    store = HardExitStore(
        configuration,
        clock=MutableClock(),
        fault_point=fault_point,
    )
    store.admit_or_return_existing(admit_request(grant, binding))
    os._exit(74)


class SqliteAdmissionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="aio-047-sqlite-tests-"
        )
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name).resolve()
        self.database_path = self.root / "admission.sqlite3"
        self.configuration = config_for(self.database_path)

    def provision(
        self,
        *,
        path: Path | None = None,
        clock: MutableClock | None = None,
        busy_timeout_ms: int = 2_000,
    ) -> tuple[
        SqliteAgentExecutionDispatchAdmissionStoreConfiguration,
        SqliteAgentExecutionDispatchAdmissionStore,
        MutableClock,
    ]:
        configuration = config_for(
            self.database_path if path is None else path,
            busy_timeout_ms=busy_timeout_ms,
        )
        result = SqliteAgentExecutionDispatchAdmissionStore.provision(
            configuration
        )
        self.assertEqual(result.outcome.value, "provisioned", result.detail)
        supplied_clock = MutableClock() if clock is None else clock
        store = SqliteAgentExecutionDispatchAdmissionStore(
            configuration,
            clock=supplied_clock,
        )
        return configuration, store, supplied_clock

    def assert_outcome(self, result: object, expected: str) -> None:
        self.assertEqual(result.outcome.value, expected, result.detail)  # type: ignore[attr-defined]

    def test_explicit_provisioning_open_profile_and_no_implicit_create(self) -> None:
        missing = config_for(self.root / "missing.sqlite3")
        with self.assertRaises(SqliteAdmissionStoreConfigurationError):
            SqliteAgentExecutionDispatchAdmissionStore(
                missing,
                clock=MutableClock(),
            )
        self.assertFalse(missing.database_path.exists())

        migrate_missing = SqliteAgentExecutionDispatchAdmissionStore.migrate(
            missing
        )
        self.assertEqual(migrate_missing.outcome.value, "storage_unavailable")
        self.assertFalse(missing.database_path.exists())

        configuration, store, _ = self.provision()
        settings = store.verified_settings()
        self.assertEqual(settings.journal_mode, "wal")
        self.assertEqual(settings.synchronous, 2)
        self.assertEqual(settings.foreign_keys, 1)
        self.assertEqual(settings.locking_mode, "normal")
        self.assertEqual(settings.busy_timeout_ms, 2_000)
        self.assertIsNone(settings.isolation_level)
        self.assertEqual(settings.write_begin, "BEGIN IMMEDIATE")
        self.assertGreaterEqual(
            tuple(int(part) for part in settings.sqlite_version.split(".")),
            (3, 37, 0),
        )

        second = SqliteAgentExecutionDispatchAdmissionStore.provision(
            configuration
        )
        self.assertEqual(second.outcome.value, "storage_unavailable")
        current = SqliteAgentExecutionDispatchAdmissionStore.migrate(
            configuration
        )
        self.assertEqual(current.outcome.value, "already_current", current.detail)

    def test_configuration_is_pinned_to_domain_instance_and_generation(self) -> None:
        self.provision()
        variants = (
            config_for(self.database_path, domain_id="domain::other"),
            config_for(self.database_path, ledger_id="ledger::other"),
            config_for(self.database_path, generation=2),
        )
        for configuration in variants:
            with self.subTest(configuration=configuration):
                with self.assertRaises(SqliteAdmissionStoreIntegrityError):
                    SqliteAgentExecutionDispatchAdmissionStore(
                        configuration,
                        clock=MutableClock(),
                    )

    def test_admit_history_load_and_restart_preserve_exact_admission(self) -> None:
        configuration, store, clock = self.provision()
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)

        absent = store.classify_guarded_history(history_request(grant, binding))
        self.assert_outcome(absent, "no_existing_admission")
        first = store.admit_or_return_existing(admit_request(grant, binding))
        self.assert_outcome(first, "newly_admitted")
        self.assertEqual(clock.calls, 1)
        self.assertEqual(first.admission.grant, grant)
        self.assertEqual(first.admission.tool_binding, binding)
        self.assertEqual(
            first.admission.decision_time,
            "2026-09-23T10:30:00.000000Z",
        )

        clock.value = RuntimeError("history must not sample the clock")
        exact = store.classify_guarded_history(history_request(grant, binding))
        self.assert_outcome(exact, "existing_exact_admission")
        self.assertEqual(exact.admission, first.admission)
        retried = store.admit_or_return_existing(admit_request(grant, binding))
        self.assert_outcome(retried, "existing_exact_admission")
        self.assertEqual(retried.admission, first.admission)
        self.assertEqual(clock.calls, 1)

        restarted_clock = MutableClock(RuntimeError("do not sample history"))
        restarted = SqliteAgentExecutionDispatchAdmissionStore(
            configuration,
            clock=restarted_clock,
        )
        loaded = restarted.load_authoritative_admission(
            _mint_authoritative_lookup_request(DOMAIN_ID, grant, binding)
        )
        self.assert_outcome(loaded, "existing_exact_admission")
        self.assertEqual(loaded.admission, first.admission)
        self.assertEqual(restarted_clock.calls, 0)

    def test_complete_grant_binding_and_domain_run_conflicts_are_distinct(self) -> None:
        _, store, clock = self.provision()
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)
        self.assert_outcome(
            store.admit_or_return_existing(admit_request(grant, binding)),
            "newly_admitted",
        )

        changed_binding = make_binding(
            bound_run=exact_run,
            tool_id="tool::sqlite-aio-047::v2",
        )
        self.assert_outcome(
            store.classify_guarded_history(
                history_request(grant, changed_binding)
            ),
            "binding_conflict",
        )

        rebound_run = make_run(
            "run::sqlite-aio-047-rebound",
            task_id="AIO-047-rebound",
        )
        rebound = make_grant(bound_run=rebound_run)
        self.assert_outcome(
            store.classify_guarded_history(
                history_request(rebound, make_binding(bound_run=rebound_run))
            ),
            "grant_identity_conflict",
        )

        second_grant = make_grant(
            bound_run=exact_run,
            grant_id="grant::sqlite-aio-047-two",
        )
        self.assert_outcome(
            store.admit_or_return_existing(
                admit_request(second_grant, binding)
            ),
            "run_conflict",
        )
        self.assertEqual(clock.calls, 1, "conflicts must not resample time")

    def test_grant_identity_is_composite_not_bare_grant_id(self) -> None:
        _, store, _ = self.provision()
        first_run = make_run("run::composite-one", task_id="composite-one")
        second_run = make_run("run::composite-two", task_id="composite-two")
        first = make_grant(bound_run=first_run, grant_id="grant::shared")
        second = make_grant(
            bound_run=second_run,
            grant_id="grant::shared",
            issuer_id="issuer::sqlite-aio-047-other",
        )
        self.assert_outcome(
            store.admit_or_return_existing(
                admit_request(first, make_binding(bound_run=first_run))
            ),
            "newly_admitted",
        )
        self.assert_outcome(
            store.admit_or_return_existing(
                admit_request(second, make_binding(bound_run=second_run))
            ),
            "newly_admitted",
        )

    def test_currentness_boundaries_denials_and_watermark_regression(self) -> None:
        clock = MutableClock(
            datetime(2026, 9, 23, 9, 59, 59, tzinfo=timezone.utc)
        )
        _, store, _ = self.provision(clock=clock)
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)

        early = store.admit_or_return_existing(admit_request(grant, binding))
        self.assert_outcome(early, "not_yet_current")
        watermark_text, watermark_key = store.watermark()
        self.assertEqual(watermark_text, "2026-09-23T09:59:59.000000Z")
        self.assertIs(type(watermark_key), int)

        clock.value = datetime(2026, 9, 23, 9, 59, 58, tzinfo=timezone.utc)
        regression = store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(regression, "clock_regression")
        self.assertEqual(store.watermark(), (watermark_text, watermark_key))

        clock.value = datetime(2026, 9, 23, 10, 0, tzinfo=timezone.utc)
        lower_boundary = store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(lower_boundary, "newly_admitted")

        other_path = self.root / "expiration.sqlite3"
        expiration_clock = MutableClock(
            datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc)
        )
        _, expiration_store, _ = self.provision(
            path=other_path,
            clock=expiration_clock,
        )
        expired = expiration_store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(expired, "expired")
        self.assertEqual(
            expiration_store.watermark()[0],
            "2026-09-23T11:00:00.000000Z",
        )

    def test_clock_failure_and_non_utc_values_fail_closed_without_watermark(self) -> None:
        cases = (
            RuntimeError("synthetic clock failure"),
            datetime(2026, 9, 23, 10, 30),
            datetime(
                2026,
                9,
                23,
                12,
                30,
                tzinfo=timezone(timedelta(hours=2)),
            ),
        )
        for index, clock_value in enumerate(cases):
            path = self.root / f"clock-{index}.sqlite3"
            clock = MutableClock(clock_value)
            _, store, _ = self.provision(path=path, clock=clock)
            exact_run = make_run(f"run::clock-{index}", task_id=f"clock-{index}")
            result = store.admit_or_return_existing(
                admit_request(
                    make_grant(bound_run=exact_run, grant_id=f"grant::clock-{index}"),
                    make_binding(bound_run=exact_run),
                )
            )
            self.assert_outcome(result, "clock_failure")
            self.assertEqual(store.watermark(), (None, None))

    def test_revocation_first_and_admission_first_are_irreversible(self) -> None:
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)

        _, revoked_first_store, clock = self.provision()
        revoked = revoked_first_store.revoke_or_return_existing(
            _mint_revocation_request(DOMAIN_ID, grant)
        )
        self.assert_outcome(revoked, "newly_revoked")
        again = revoked_first_store.revoke_or_return_existing(
            _mint_revocation_request(DOMAIN_ID, grant)
        )
        self.assert_outcome(again, "existing_exact_revocation")
        denied = revoked_first_store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(denied, "revoked")
        self.assertEqual(
            clock.calls,
            2,
            "a new revocation-first denial must advance time exactly once",
        )

        other_path = self.root / "admission-first.sqlite3"
        other_clock = MutableClock()
        _, admitted_first_store, _ = self.provision(
            path=other_path,
            clock=other_clock,
        )
        admitted = admitted_first_store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(admitted, "newly_admitted")
        other_clock.value = DECISION_TIME + timedelta(minutes=1)
        later_revocation = admitted_first_store.revoke_or_return_existing(
            _mint_revocation_request(DOMAIN_ID, grant)
        )
        self.assert_outcome(later_revocation, "newly_revoked")
        retry = admitted_first_store.admit_or_return_existing(
            admit_request(grant, binding)
        )
        self.assert_outcome(retry, "existing_exact_admission")
        self.assertEqual(retry.admission, admitted.admission)

    def test_open_verification_uses_one_snapshot_during_concurrent_append(self) -> None:
        configuration, writer, _ = self.provision()
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)
        reader = PausingVerificationStore(
            configuration,
            clock=MutableClock(RuntimeError("history must not sample time")),
        )
        reader.pause_verification = True
        observed: list[object] = []

        def classify() -> None:
            try:
                observed.append(
                    reader.classify_guarded_history(
                        history_request(grant, binding)
                    )
                )
            except BaseException as error:  # pragma: no cover - assertion aid
                observed.append(error)

        thread = threading.Thread(target=classify, daemon=True)
        thread.start()
        self.assertTrue(
            reader.metadata_read.wait(10),
            "reader did not pause after its metadata snapshot",
        )
        try:
            admitted = writer.admit_or_return_existing(
                admit_request(grant, binding)
            )
            self.assert_outcome(admitted, "newly_admitted")
        finally:
            reader.resume_verification.set()
        thread.join(10)
        self.assertFalse(thread.is_alive(), "reader did not finish")
        self.assertEqual(len(observed), 1)
        if isinstance(observed[0], BaseException):
            raise observed[0]
        self.assert_outcome(observed[0], "existing_exact_admission")

    def test_three_way_run_equality_is_rechecked_inside_writer_transaction(self) -> None:
        configuration, _, _ = self.provision()
        original_run = make_run()
        grant = make_grant(bound_run=original_run)
        binding = make_binding(bound_run=original_run)
        clock = MutableClock()
        store = MutatingRequestStore(
            configuration,
            clock=clock,
            grant_to_mutate=grant,
            replacement_run=make_run(
                "run::mutated-after-begin",
                task_id="AIO-047-mutated-after-begin",
            ),
        )

        result = store.admit_or_return_existing(
            _mint_admission_request(DOMAIN_ID, grant, binding, original_run)
        )

        self.assert_outcome(result, "invalid_input")
        self.assertTrue(store.mutated)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(store.watermark(), (None, None))
        with closing(sqlite3.connect(configuration.database_path)) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM agent_execution_dispatch_admissions"
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_busy_writer_is_retryable_and_does_not_fall_back(self) -> None:
        configuration, store, _ = self.provision(busy_timeout_ms=0)
        blocker = sqlite3.connect(
            configuration.database_path,
            timeout=0,
            isolation_level=None,
        )
        self.addCleanup(blocker.close)
        blocker.execute("BEGIN IMMEDIATE")
        self.addCleanup(lambda: blocker.execute("ROLLBACK") if blocker.in_transaction else None)

        exact_run = make_run()
        result = store.admit_or_return_existing(
            admit_request(
                make_grant(bound_run=exact_run),
                make_binding(bound_run=exact_run),
            )
        )
        self.assert_outcome(result, "storage_busy")
        self.assertEqual(store.watermark(), (None, None))

    def test_missing_ledger_after_open_is_unavailable_and_not_recreated(self) -> None:
        configuration, store, _ = self.provision()
        moved = self.root / "moved-ledger.sqlite3"
        configuration.database_path.replace(moved)
        exact_run = make_run()
        result = store.admit_or_return_existing(
            admit_request(
                make_grant(bound_run=exact_run),
                make_binding(bound_run=exact_run),
            )
        )
        self.assert_outcome(result, "storage_unavailable")
        self.assertFalse(configuration.database_path.exists())

    def test_precommit_faults_roll_back_and_postcommit_fault_requires_exact_retry(self) -> None:
        precommit_points = (
            "before_transaction",
            "after_begin",
            "after_checks",
            "after_insert_before_commit",
        )
        for index, point in enumerate(precommit_points):
            path = self.root / f"fault-{index}.sqlite3"
            configuration = config_for(path)
            provisioned = SqliteAgentExecutionDispatchAdmissionStore.provision(
                configuration
            )
            self.assertEqual(provisioned.outcome.value, "provisioned", provisioned.detail)
            faulting = FaultingStore(
                configuration,
                clock=MutableClock(),
                fault_point=point,
            )
            exact_run = make_run(
                f"run::fault-{index}",
                task_id=f"fault-{index}",
            )
            grant = make_grant(
                bound_run=exact_run,
                grant_id=f"grant::fault-{index}",
            )
            binding = make_binding(bound_run=exact_run)
            failed = faulting.admit_or_return_existing(
                admit_request(grant, binding)
            )
            self.assert_outcome(failed, "storage_unavailable")
            normal = SqliteAgentExecutionDispatchAdmissionStore(
                configuration,
                clock=MutableClock(),
            )
            absent = normal.classify_guarded_history(
                history_request(grant, binding)
            )
            self.assert_outcome(absent, "no_existing_admission")

        post_path = self.root / "fault-after-commit.sqlite3"
        post_configuration = config_for(post_path)
        provisioned = SqliteAgentExecutionDispatchAdmissionStore.provision(
            post_configuration
        )
        self.assertEqual(provisioned.outcome.value, "provisioned", provisioned.detail)
        post_store = FaultingStore(
            post_configuration,
            clock=MutableClock(),
            fault_point="after_commit_before_response",
        )
        post_run = make_run("run::postcommit", task_id="postcommit")
        post_grant = make_grant(
            bound_run=post_run,
            grant_id="grant::postcommit",
        )
        post_binding = make_binding(bound_run=post_run)
        unknown = post_store.admit_or_return_existing(
            admit_request(post_grant, post_binding)
        )
        self.assert_outcome(unknown, "commit_unknown")
        normal = SqliteAgentExecutionDispatchAdmissionStore(
            post_configuration,
            clock=MutableClock(RuntimeError("exact retry must not resample")),
        )
        recovered = normal.admit_or_return_existing(
            admit_request(post_grant, post_binding)
        )
        self.assert_outcome(recovered, "existing_exact_admission")

    def test_newer_schema_dirty_state_missing_trigger_and_checksum_fail_closed(self) -> None:
        mutations = (
            ("newer", lambda connection: connection.execute("PRAGMA user_version=2"), SqliteAdmissionStoreIncompatibleSchemaError),
            ("dirty", lambda connection: connection.execute("UPDATE admission_ledger_metadata SET migration_state='dirty' WHERE singleton=1"), SqliteAdmissionStoreIntegrityError),
            ("trigger", lambda connection: connection.execute("DROP TRIGGER agent_execution_dispatch_admissions_no_delete"), SqliteAdmissionStoreIntegrityError),
        )
        for name, mutate, expected_error in mutations:
            path = self.root / f"schema-{name}.sqlite3"
            configuration, _, _ = self.provision(path=path)
            with closing(sqlite3.connect(path)) as connection:
                with connection:
                    mutate(connection)
            with self.assertRaises(expected_error):
                SqliteAgentExecutionDispatchAdmissionStore(
                    configuration,
                    clock=MutableClock(),
                )

        checksum_path = self.root / "schema-checksum.sqlite3"
        checksum_configuration, _, _ = self.provision(path=checksum_path)
        with closing(sqlite3.connect(checksum_path)) as connection:
            with connection:
                trigger_name = "admission_schema_migrations_no_update"
                trigger_sql = connection.execute(
                    "SELECT sql FROM sqlite_schema WHERE type='trigger' AND name=?",
                    (trigger_name,),
                ).fetchone()[0]
                connection.execute(f"DROP TRIGGER {trigger_name}")
                connection.execute(
                    "UPDATE admission_schema_migrations SET sha256=? WHERE migration_id=1",
                    ("0" * 64,),
                )
                connection.execute(trigger_sql)
        with self.assertRaises(SqliteAdmissionStoreIntegrityError):
            SqliteAgentExecutionDispatchAdmissionStore(
                checksum_configuration,
                clock=MutableClock(),
            )

    def test_malformed_payload_and_index_payload_mismatch_fail_closed(self) -> None:
        malformed_path = self.root / "malformed-payload.sqlite3"
        malformed_configuration, _, _ = self.provision(path=malformed_path)
        decision_time = "2026-09-23T10:30:00.000000Z"
        decision_key = subject._parse_decision_time(decision_time)[1]
        with closing(sqlite3.connect(malformed_path)) as connection:
            with connection:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute(
                    """
                    INSERT INTO agent_execution_dispatch_admissions VALUES (
                        ?, 'policy', 'issuer::sqlite-aio-047', 'grant::malformed',
                        'run::malformed', '{}', '{}', '{}', ?, ?
                    )
                    """,
                    (DOMAIN_ID, decision_time, decision_key),
                )
                connection.execute(
                    """
                    UPDATE admission_ledger_metadata
                    SET last_decision_time=?, last_decision_time_key=?
                    WHERE singleton=1
                    """,
                    (decision_time, decision_key),
                )
        with self.assertRaises(SqliteAdmissionStoreIntegrityError):
            SqliteAgentExecutionDispatchAdmissionStore(
                malformed_configuration,
                clock=MutableClock(),
            )

        mismatch_path = self.root / "payload-index-mismatch.sqlite3"
        mismatch_configuration, _, _ = self.provision(path=mismatch_path)
        exact_run = make_run("run::mismatch", task_id="mismatch")
        grant = make_grant(bound_run=exact_run, grant_id="grant::payload")
        binding = make_binding(bound_run=exact_run)
        admission = AgentExecutionDispatchAdmission(
            grant,
            binding,
            decision_time,
        )
        with closing(sqlite3.connect(mismatch_path)) as connection:
            with connection:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute(
                    """
                    INSERT INTO agent_execution_dispatch_admissions VALUES (
                        ?, ?, ?, 'grant::wrong-index', ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        DOMAIN_ID,
                        grant.issuer_kind,
                        grant.issuer_id,
                        exact_run.run_id,
                        subject._encode_grant(grant),
                        subject._encode_binding(binding),
                        subject._encode_admission(admission),
                        decision_time,
                        decision_key,
                    ),
                )
                connection.execute(
                    """
                    UPDATE admission_ledger_metadata
                    SET last_decision_time=?, last_decision_time_key=?
                    WHERE singleton=1
                    """,
                    (decision_time, decision_key),
                )
        with self.assertRaises(SqliteAdmissionStoreIntegrityError):
            SqliteAgentExecutionDispatchAdmissionStore(
                mismatch_configuration,
                clock=MutableClock(),
            )

    def test_corrupt_database_and_wrong_application_identity_fail_closed(self) -> None:
        corrupt_path = self.root / "corrupt.sqlite3"
        corrupt_configuration, _, _ = self.provision(path=corrupt_path)
        corrupt_path.write_bytes(b"not a sqlite database")
        with self.assertRaises((SqliteAdmissionStoreIntegrityError, sqlite3.DatabaseError)):
            SqliteAgentExecutionDispatchAdmissionStore(
                corrupt_configuration,
                clock=MutableClock(),
            )

        identity_path = self.root / "wrong-identity.sqlite3"
        identity_configuration, _, _ = self.provision(path=identity_path)
        with closing(sqlite3.connect(identity_path)) as connection:
            with connection:
                connection.execute(
                    f"PRAGMA application_id={SQLITE_APPLICATION_ID + 1}"
                )
        with self.assertRaises(SqliteAdmissionStoreIncompatibleSchemaError):
            SqliteAgentExecutionDispatchAdmissionStore(
                identity_configuration,
                clock=MutableClock(),
            )

    def test_revocation_serial_time_cannot_precede_same_grant_admission(self) -> None:
        configuration, store, _ = self.provision()
        run = make_run()
        grant = make_grant(bound_run=run)
        binding = make_binding(bound_run=run)
        self.assert_outcome(
            store.admit_or_return_existing(admit_request(grant, binding)),
            "newly_admitted",
        )
        earlier_time = "2026-09-23T10:29:00.000000Z"
        earlier_key = subject._parse_decision_time(earlier_time)[1]
        with closing(sqlite3.connect(configuration.database_path)) as connection:
            with connection:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute(
                    """
                    INSERT INTO agent_execution_grant_revocations (
                        authorization_domain_id,
                        issuer_kind,
                        issuer_id,
                        grant_id,
                        run_id,
                        grant_json,
                        revoker_kind,
                        revoker_id,
                        revocation_time,
                        revocation_time_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        *subject._grant_identity(grant),
                        run.run_id,
                        subject._encode_grant(grant),
                        grant.issuer_kind,
                        grant.issuer_id,
                        earlier_time,
                        earlier_key,
                    ),
                )
        with self.assertRaises(SqliteAdmissionStoreIntegrityError):
            SqliteAgentExecutionDispatchAdmissionStore(
                configuration,
                clock=MutableClock(),
            )

    def test_one_way_fence_and_consistent_fenced_backup(self) -> None:
        configuration, store, _ = self.provision()
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)
        self.assert_outcome(
            store.admit_or_return_existing(admit_request(grant, binding)),
            "newly_admitted",
        )

        backup_path = self.root / "snapshot.sqlite3"
        backup = store.create_fenced_backup(backup_path)
        self.assertEqual(backup.outcome.value, "fenced_backup_created", backup.detail)
        self.assertTrue(backup_path.is_file())
        with closing(sqlite3.connect(backup_path)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT activation_state FROM admission_ledger_metadata"
                ).fetchone()[0],
                "fenced",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM agent_execution_dispatch_admissions"
                ).fetchone()[0],
                1,
            )
        backup_configuration = config_for(backup_path)
        with self.assertRaises(SqliteAdmissionStoreIncompatibleSchemaError):
            SqliteAgentExecutionDispatchAdmissionStore(
                backup_configuration,
                clock=MutableClock(),
            )

        # Creating the inert snapshot does not fence the source authority.
        exact = store.classify_guarded_history(history_request(grant, binding))
        self.assert_outcome(exact, "existing_exact_admission")
        fenced = store.fence()
        self.assertEqual(fenced.outcome.value, "fenced", fenced.detail)
        exact_fence_retry = store.fence()
        self.assertEqual(
            exact_fence_retry.outcome.value,
            "fenced",
            exact_fence_retry.detail,
        )
        with self.assertRaises(SqliteAdmissionStoreIncompatibleSchemaError):
            SqliteAgentExecutionDispatchAdmissionStore(
                configuration,
                clock=MutableClock(),
            )
        with closing(sqlite3.connect(configuration.database_path)) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE admission_ledger_metadata SET activation_state='active'"
                )

    def test_manual_active_copy_demonstrates_explicit_split_ledger_limitation(self) -> None:
        configuration, source, _ = self.provision()
        copied_path = self.root / "unsupported-active-copy.sqlite3"
        shutil.copy2(configuration.database_path, copied_path)
        copied_configuration = config_for(copied_path)
        copied = SqliteAgentExecutionDispatchAdmissionStore(
            copied_configuration,
            clock=MutableClock(),
        )

        source_run = make_run("run::source-only", task_id="source-only")
        source_grant = make_grant(
            bound_run=source_run,
            grant_id="grant::source-only",
        )
        source_binding = make_binding(bound_run=source_run)
        copied_run = make_run("run::copy-only", task_id="copy-only")
        copied_grant = make_grant(
            bound_run=copied_run,
            grant_id="grant::copy-only",
        )
        copied_binding = make_binding(bound_run=copied_run)

        self.assert_outcome(
            source.admit_or_return_existing(
                admit_request(source_grant, source_binding)
            ),
            "newly_admitted",
        )
        self.assert_outcome(
            copied.admit_or_return_existing(
                admit_request(copied_grant, copied_binding)
            ),
            "newly_admitted",
        )
        self.assert_outcome(
            source.classify_guarded_history(
                history_request(copied_grant, copied_binding)
            ),
            "no_existing_admission",
        )
        self.assert_outcome(
            copied.classify_guarded_history(
                history_request(source_grant, source_binding)
            ),
            "no_existing_admission",
        )

        # This deliberately unsupported copy proves why database-local
        # identity/generation metadata cannot provide global fencing.  A
        # future external ownership authority is required; AIO-047 exposes no
        # restore or reactivation operation.

    def run_spawned_pair(
        self,
        path: Path,
        left: tuple[AgentExecutionAuthorizationGrant, AgentOperationToolBinding],
        right: tuple[AgentExecutionAuthorizationGrant, AgentOperationToolBinding],
    ) -> list[str]:
        configuration = config_for(path)
        provisioned = SqliteAgentExecutionDispatchAdmissionStore.provision(
            configuration
        )
        self.assertEqual(provisioned.outcome.value, "provisioned", provisioned.detail)
        context = multiprocessing.get_context("spawn")
        start = context.Event()
        results = context.Queue()
        processes = [
            context.Process(
                target=_spawn_store_operation,
                args=(str(path), *request, "admit", start, results),
            )
            for request in (left, right)
        ]
        for process in processes:
            process.start()
        start.set()
        messages = [results.get(timeout=20) for _ in processes]
        for process in processes:
            process.join(20)
            self.assertFalse(process.is_alive(), "spawned SQLite worker hung")
            self.assertEqual(process.exitcode, 0)
        errors = [message for message in messages if message[0] != "ok"]
        self.assertEqual(errors, [])
        return sorted(message[1] for message in messages)

    def test_spawned_process_same_and_conflicting_requests_serialize(self) -> None:
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)
        same = self.run_spawned_pair(
            self.root / "spawn-same.sqlite3",
            (grant, binding),
            (grant, binding),
        )
        self.assertEqual(same, ["existing_exact_admission", "newly_admitted"])

        binding_conflict = self.run_spawned_pair(
            self.root / "spawn-binding.sqlite3",
            (grant, binding),
            (
                grant,
                make_binding(
                    bound_run=exact_run,
                    tool_id="tool::sqlite-aio-047::conflicting",
                ),
            ),
        )
        self.assertEqual(binding_conflict, ["binding_conflict", "newly_admitted"])

        second_grant = make_grant(
            bound_run=exact_run,
            grant_id="grant::sqlite-aio-047-competing",
        )
        run_conflict = self.run_spawned_pair(
            self.root / "spawn-run.sqlite3",
            (grant, binding),
            (second_grant, binding),
        )
        self.assertEqual(run_conflict, ["newly_admitted", "run_conflict"])

    def test_spawned_admission_and_revocation_race_has_one_serial_order(self) -> None:
        path = self.root / "spawn-admit-revoke.sqlite3"
        configuration = config_for(path)
        provisioned = SqliteAgentExecutionDispatchAdmissionStore.provision(
            configuration
        )
        self.assertEqual(provisioned.outcome.value, "provisioned")
        exact_run = make_run()
        grant = make_grant(bound_run=exact_run)
        binding = make_binding(bound_run=exact_run)
        context = multiprocessing.get_context("spawn")
        start = context.Event()
        results = context.Queue()
        processes = (
            context.Process(
                target=_spawn_store_operation,
                args=(str(path), grant, binding, "admit", start, results),
            ),
            context.Process(
                target=_spawn_store_operation,
                args=(str(path), grant, binding, "revoke", start, results),
            ),
        )
        for process in processes:
            process.start()
        start.set()
        messages = [results.get(timeout=20) for _ in processes]
        for process in processes:
            process.join(20)
            self.assertFalse(process.is_alive(), "spawned race worker hung")
            self.assertEqual(process.exitcode, 0)
        self.assertEqual(
            [message for message in messages if message[0] != "ok"],
            [],
        )
        outcomes = sorted(message[1] for message in messages)
        self.assertIn(
            outcomes,
            (
                ["newly_admitted", "newly_revoked"],
                ["newly_revoked", "revoked"],
            ),
        )

        reopened = SqliteAgentExecutionDispatchAdmissionStore(
            configuration,
            clock=MutableClock(RuntimeError("history must not sample time")),
        )
        history = reopened.classify_guarded_history(
            history_request(grant, binding)
        )
        if "newly_admitted" in outcomes:
            self.assert_outcome(history, "existing_exact_admission")
        else:
            self.assert_outcome(history, "no_existing_admission")
        repeated_revocation = reopened.revoke_or_return_existing(
            _mint_revocation_request(DOMAIN_ID, grant)
        )
        self.assert_outcome(repeated_revocation, "existing_exact_revocation")

    def test_spawned_hard_crashes_rollback_or_recover_exact_commit(self) -> None:
        context = multiprocessing.get_context("spawn")
        cases = (
            ("after_begin", False),
            ("after_insert_before_commit", False),
            ("after_commit_before_response", True),
        )
        for index, (fault_point, committed) in enumerate(cases):
            with self.subTest(fault_point=fault_point):
                path = self.root / f"hard-crash-{index}.sqlite3"
                configuration = config_for(path)
                provisioned = (
                    SqliteAgentExecutionDispatchAdmissionStore.provision(
                        configuration
                    )
                )
                self.assertEqual(provisioned.outcome.value, "provisioned")
                exact_run = make_run(
                    f"run::hard-crash-{index}",
                    task_id=f"hard-crash-{index}",
                )
                grant = make_grant(
                    bound_run=exact_run,
                    grant_id=f"grant::hard-crash-{index}",
                )
                binding = make_binding(bound_run=exact_run)
                process = context.Process(
                    target=_spawn_crashing_admission,
                    args=(str(path), grant, binding, fault_point),
                )
                process.start()
                process.join(20)
                self.assertFalse(process.is_alive(), "crash worker hung")
                self.assertEqual(process.exitcode, 73)

                retry_clock = MutableClock(
                    RuntimeError("exact committed retry must not sample time")
                )
                reopened = SqliteAgentExecutionDispatchAdmissionStore(
                    configuration,
                    clock=retry_clock,
                )
                history = reopened.classify_guarded_history(
                    history_request(grant, binding)
                )
                if committed:
                    self.assert_outcome(history, "existing_exact_admission")
                    retried = reopened.admit_or_return_existing(
                        admit_request(grant, binding)
                    )
                    self.assert_outcome(retried, "existing_exact_admission")
                    self.assertEqual(retried.admission, history.admission)
                    self.assertEqual(retry_clock.calls, 0)
                else:
                    self.assert_outcome(history, "no_existing_admission")
                    self.assertEqual(reopened.watermark(), (None, None))


class SqliteAdmissionStoreReusableConformanceTests(
    AgentExecutionDispatchAdmissionStoreConformanceMixin,
    unittest.TestCase,
):
    """Run the backend-neutral semantic harness against production SQLite."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="aio-047-sqlite-conformance-"
        )
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name).resolve()
        self.harness_index = 0

    def make_conformance_harness(
        self,
        *,
        decision_time: object = DECISION_TIME,
    ) -> AdmissionStoreConformanceHarness:
        self.harness_index += 1
        path = self.root / f"conformance-{self.harness_index}.sqlite3"
        configuration = config_for(
            path,
            domain_id=CONFORMANCE_DOMAIN_ID,
            ledger_id=f"ledger::store-conformance::{self.harness_index}",
        )
        provisioned = SqliteAgentExecutionDispatchAdmissionStore.provision(
            configuration
        )
        self.assertEqual(
            provisioned.outcome.value,
            "provisioned",
            provisioned.detail,
        )
        clock = MutableClock(decision_time)
        store = SqliteAgentExecutionDispatchAdmissionStore(
            configuration,
            clock=clock,
        )
        unavailable_path = path.with_name(path.name + ".unavailable")

        def set_clock(value: object) -> None:
            clock.value = value

        def make_storage_unavailable() -> None:
            path.replace(unavailable_path)

        return AdmissionStoreConformanceHarness(
            store=store,
            set_clock=set_clock,
            clock_calls=lambda: clock.calls,
            make_storage_unavailable=make_storage_unavailable,
        )


if __name__ == "__main__":
    unittest.main()
