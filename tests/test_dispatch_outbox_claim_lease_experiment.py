"""Focused AIO-054 private dispatch/outbox/claim/lease experiment tests.

The module deliberately imports only the disposable experiment implementation.
It has exactly one discoverable ``unittest`` method for each locked scenario ID
1 through 128.  Shared handlers reduce mechanical duplication, but every
scenario has its own registry entry, name, parameters, and assertions.

Spawned-process work is delegated only to top-level functions in
``worker_harness`` so Windows ``spawn`` never has to pickle a local target.
Every database path is below a per-test ``TemporaryDirectory``.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import inspect
from pathlib import Path
import pickle
import sqlite3
import threading
import time
from tempfile import TemporaryDirectory
import unittest
from unittest import mock

from experiments.dispatch_outbox_claim_lease import store as store_module
from experiments.dispatch_outbox_claim_lease import worker_harness as harness_module
from experiments.dispatch_outbox_claim_lease.store import (
    APPLICATION_ID,
    BUSY_TIMEOUT_MS,
    CURRENT_SCHEMA_VERSION,
    LEASE_DURATION_US,
    MAX_SIGNED_64,
    MINIMUM_SQLITE_VERSION,
    AdmissionRequest,
    ClaimRequest,
    CommitUnknownFault,
    ConfigurationError,
    CurrentClaimRequest,
    DispatchIdentity,
    DispatchOutboxClaimLeaseStore,
    IncompatibleSchemaError,
    InjectedFault,
    IntegrityFailure,
    OperationResult,
    RenewalRequest,
    StoreConfiguration,
    open_profiled_connection,
)
from experiments.dispatch_outbox_claim_lease.worker_harness import (
    CoordinatorClaimProbeSpec,
    NONCANONICAL_DISCLAIMER,
    PROBE_HARD_EXIT_CODE,
    STORAGE_FAULT_POINTS_BY_OPERATION,
    SUPPORTED_STORAGE_FAULT_POINTS,
    ExperimentCoordinator,
    ExecutorCapabilityError,
    LifecycleError,
    LifecycleState,
    LifecycleSurrogate,
    ProbeClockSpec,
    StorageProbeSpec,
    create_executor_capability,
    race_storage_probes,
    run_coordinator_claim_probe,
    run_held_writer_probe,
    run_storage_probe,
    run_t3_child_process_safety_validation,
)


UTC = timezone.utc
BASE_TIME = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class MutableClock:
    """Controllable exact UTC clock with an observable sampling count."""

    def __init__(self, value: object = BASE_TIME) -> None:
        self.value = value
        self.failure: BaseException | None = None
        self.calls = 0

    def now_utc(self) -> object:
        self.calls += 1
        if self.failure is not None:
            raise self.failure
        return self.value

    def set(self, value: object) -> None:
        self.value = value
        self.failure = None

    def fail(self, error: BaseException | None = None) -> None:
        self.failure = error or RuntimeError("synthetic unavailable clock")


class SequenceClock:
    """Return a deterministic sequence of clock values."""

    def __init__(self, *values: object) -> None:
        if not values:
            raise ValueError("SequenceClock requires at least one value")
        self._values = list(values)
        self.calls = 0

    def now_utc(self) -> object:
        index = min(self.calls, len(self._values) - 1)
        self.calls += 1
        return self._values[index]


class FaultAt:
    """Raise exactly once at one named Store cut point."""

    def __init__(self, point: str, error_type: type[BaseException] = InjectedFault) -> None:
        self.point = point
        self.error_type = error_type
        self.reached = 0

    def __call__(self, point: str) -> None:
        if point == self.point:
            self.reached += 1
            raise self.error_type(f"synthetic fault at {point}")


class _LifecycleTransitionStore:
    """Proxy which changes lifecycle state after Store commit, before post-check."""

    def __init__(self, store: object, session: object, *, terminal: bool) -> None:
        self._store = store
        self._session = session
        self._terminal = terminal
        self._fence_thread: threading.Thread | None = None

    def __getattr__(self, name: str) -> object:
        target = getattr(self._store, name)
        if not callable(target):
            return target

        def invoke(*args: object, **kwargs: object) -> object:
            result = target(*args, **kwargs)
            if self._terminal:
                thread = threading.Thread(
                    target=self._session.fence,
                    kwargs={"timeout": 5.0},
                    daemon=True,
                )
                self._fence_thread = thread
                thread.start()
                owner = getattr(self._session, "_owner")
                deadline = time.monotonic() + 5.0
                while owner.state is not LifecycleState.FENCING:
                    if time.monotonic() >= deadline:
                        raise AssertionError("terminal fence did not begin")
                    time.sleep(0.001)
            else:
                self._session.lose_authority()
            return result

        return invoke

    def join(self) -> None:
        if self._fence_thread is not None:
            self._fence_thread.join(5.0)
            if self._fence_thread.is_alive():
                raise AssertionError("terminal fence did not quiesce")


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    handler: str
    arguments: tuple[object, ...] = ()


_SCENARIO_NAMES = {
    1: "new_admission",
    2: "exact_admission_retry_with_unavailable_clock",
    3: "exact_admission_retry_with_regressing_clock",
    4: "admission_crash_before_transaction",
    5: "admission_crash_after_begin",
    6: "admission_crash_after_admission_insert",
    7: "admission_crash_after_intent_insert",
    8: "admission_crash_after_watermark_update",
    9: "admission_ambiguous_commit_not_committed",
    10: "admission_ambiguous_commit_committed",
    11: "existing_admission_migration",
    12: "migration_preflight_mismatch",
    13: "operational_open_old_newer_dirty_or_partial_schema",
    14: "migration_crash_before_commit",
    15: "migration_ambiguous_commit",
    16: "legacy_exact_admission_retry",
    17: "outbox_xor_corruption",
    18: "one_pending_intent",
    19: "multiple_eligible_intents",
    20: "raw_sqlite_two_process_claim_race",
    21: "concurrent_lifecycle_surrogate_operations",
    22: "claim_race_winner",
    23: "active_lease",
    24: "exact_claim_retry_after_lost_response",
    25: "exact_claim_retry_after_expiry",
    26: "exact_claim_retry_after_supersession",
    27: "claim_id_and_executor_rebound",
    28: "stored_claim_binding_rebound",
    29: "exact_claim_expiry_boundary",
    30: "different_worker_reclaim",
    31: "same_worker_reclaim",
    32: "stale_old_claimant",
    33: "claim_crash_before_transaction",
    34: "claim_crash_after_begin_or_insert",
    35: "claim_crash_after_watermark_update",
    36: "claim_ambiguous_commit",
    37: "worker_crash_after_receiving_claim",
    38: "valid_renewal",
    39: "nonextending_renewal",
    40: "exact_committed_renewal_retry",
    41: "committed_renewal_retry_after_expiry_or_supersession",
    42: "renewal_response_loss",
    43: "renewal_id_rebound",
    44: "stale_generation_renewal",
    45: "expired_claim_renewal",
    46: "concurrent_renewals",
    47: "renewal_versus_reclaim_race",
    48: "renewal_crash_before_transaction",
    49: "renewal_crash_after_insert",
    50: "renewal_crash_after_watermark_update",
    51: "inserted_renewal_ambiguous_commit",
    52: "renewal_chain_corruption",
    53: "unavailable_or_throwing_clock",
    54: "naive_non_utc_malformed_or_lossy_clock",
    55: "clock_rollback_below_watermark",
    56: "watermark_semantics",
    57: "forward_wall_clock_jump",
    58: "process_restart_during_active_lease",
    59: "sqlite_wal_restart",
    60: "worker_process_restart",
    61: "repeated_reclaim",
    62: "malformed_gapped_rebound_or_exhausted_generation",
    63: "complete_lifecycle_surrogate_guard",
    64: "domain_fenced_before_claim",
    65: "fencing_racing_with_operations",
    66: "terminal_fence_after_claim",
    67: "post_admission_revocation",
    68: "wrong_admission_identity",
    69: "wrong_run_or_index_payload_relationship",
    70: "tool_substitution",
    71: "runtime_substitution",
    72: "actor_operation_or_resource_widening",
    73: "corrupt_or_newer_experiment_schema",
    74: "sqlite_connection_profile_pressure",
    75: "negative_execution_boundary",
    76: "concurrent_identical_admissions",
    77: "same_grant_with_different_binding",
    78: "different_grant_with_same_run",
    79: "not_yet_valid_grant",
    80: "expired_grant",
    81: "pre_revoked_grant",
    82: "incomplete_revocation_evidence",
    83: "multiple_admission_conflicts",
    84: "admission_post_check_recoverable_loss",
    85: "admission_post_check_terminal_fence",
    86: "migration_crash_after_dirty_transition",
    87: "migration_crash_after_schema_installation",
    88: "migration_crash_after_legacy_population",
    89: "migration_crash_after_metadata_clean_transition",
    90: "empty_intent_queue",
    91: "only_authority_ineligible_intents",
    92: "all_authority_eligible_intents_actively_leased",
    93: "lost_all_active_response",
    94: "lost_empty_queue_response",
    95: "no_row_claim_later_becomes_eligible",
    96: "claim_post_check_recoverable_loss",
    97: "claim_post_check_terminal_fence",
    98: "lost_nonextending_renewal_response",
    99: "lost_expired_renewal_response",
    100: "renewal_crash_after_begin",
    101: "renewal_crash_after_invariant_validation",
    102: "renewal_crash_after_time_sample",
    103: "renewal_post_check_recoverable_loss",
    104: "renewal_post_check_terminal_fence",
    105: "old_executor_tuple_replay_through_coordinator",
    106: "old_executor_tuple_replay_at_raw_store_boundary",
    107: "invalid_lease_duration_configuration",
    108: "equal_time_selection_tie",
    109: "sqlite_below_minimum_version",
    110: "effective_connection_profile_verification",
    111: "claim_crash_after_invariant_validation",
    112: "claim_crash_after_clock_sample",
    113: "rejected_admission_concurrent_with_valid_winner",
    114: "revocation_versus_claim_writer_order",
    115: "admission_post_insert_pre_watermark_crash",
    116: "multiple_equal_time_eligible_intents",
    117: "legacy_retry_after_completed_migration",
    118: "revocation_versus_renewal_writer_order",
    119: "terminal_fence_administrative_reconciliation",
    120: "canonical_integration_boundary",
    121: "exact_claim_history_only_retry",
    122: "exact_renewal_history_only_retry",
    123: "active_current_claim_assessment",
    124: "inactive_current_claim_assessment",
    125: "assessment_clock_failure_or_regression",
    126: "assessment_terminal_post_check_fence",
    127: "renewal_sequence_allocation_and_rollback",
    128: "renewal_sequence_exhaustion_or_corruption",
}


if tuple(sorted(_SCENARIO_NAMES)) != tuple(range(1, 129)):
    raise AssertionError("AIO-054 scenario registry must contain exactly IDs 1..128")
if len(set(_SCENARIO_NAMES.values())) != 128:
    raise AssertionError("AIO-054 scenario registry names must be unique")


class DispatchOutboxClaimLeaseExperimentTests(unittest.TestCase):
    """Reusable fixtures and concrete assertions for all 128 locked scenarios."""

    maxDiff = None

    def setUp(self) -> None:
        self._temporary_directory = TemporaryDirectory(prefix="aio054-test-")
        self.addCleanup(self._temporary_directory.cleanup)
        self.database_path = (
            Path(self._temporary_directory.name).resolve() / "experiment.sqlite3"
        )
        self.configuration = StoreConfiguration(
            database_path=self.database_path,
            authorization_domain_id="domain::aio054",
            ledger_instance_id="ledger::aio054",
        )
        self.clock = MutableClock(BASE_TIME)

    def _request(
        self,
        suffix: str = "a",
        *,
        run_id: str | None = None,
        grant_payload: bytes | None = None,
        binding_payload: bytes | None = None,
        issued_at: datetime | None = None,
        expires_at: datetime | None = None,
    ) -> AdmissionRequest:
        return AdmissionRequest(
            authorization_domain_id=self.configuration.authorization_domain_id,
            issuer_kind="human",
            issuer_id=f"issuer::{suffix}",
            grant_id=f"grant::{suffix}",
            run_id=run_id or f"run::{suffix}",
            grant_payload=grant_payload or f"grant-payload::{suffix}".encode(),
            binding_payload=binding_payload or f"binding-payload::{suffix}".encode(),
            issued_at=issued_at or BASE_TIME - timedelta(hours=1),
            expires_at=expires_at or BASE_TIME + timedelta(days=1),
        )

    def _provision_legacy(self, *, complete: bool = True) -> None:
        result = DispatchOutboxClaimLeaseStore.provision_legacy(
            self.configuration,
            revocation_state_complete=complete,
        )
        self.assertEqual(result.outcome, "provisioned", result)

    def _legacy_store(
        self,
        *,
        clock: object | None = None,
        fault_hook: object | None = None,
    ) -> DispatchOutboxClaimLeaseStore:
        return DispatchOutboxClaimLeaseStore.open_legacy(
            self.configuration,
            clock=clock or self.clock,
            fault_hook=fault_hook,
        )

    def _migrate(self) -> None:
        result = DispatchOutboxClaimLeaseStore.migrate_legacy(self.configuration)
        self.assertEqual(result.outcome, "migrated", result)

    def _new_store(
        self,
        *,
        complete: bool = True,
        clock: object | None = None,
        fault_hook: object | None = None,
        allow_fenced: bool = False,
    ) -> DispatchOutboxClaimLeaseStore:
        self._provision_legacy(complete=complete)
        self._migrate()
        return DispatchOutboxClaimLeaseStore.open(
            self.configuration,
            clock=clock or self.clock,
            fault_hook=fault_hook,
            allow_fenced=allow_fenced,
        )

    def _open_store(
        self,
        *,
        clock: object | None = None,
        fault_hook: object | None = None,
        allow_fenced: bool = False,
    ) -> DispatchOutboxClaimLeaseStore:
        return DispatchOutboxClaimLeaseStore.open(
            self.configuration,
            clock=clock or self.clock,
            fault_hook=fault_hook,
            allow_fenced=allow_fenced,
        )

    def _admit(
        self,
        store: DispatchOutboxClaimLeaseStore,
        request: AdmissionRequest | None = None,
        *,
        at: datetime | None = None,
    ) -> OperationResult:
        if at is not None:
            self.clock.set(at)
        result = store.admit(request or self._request())
        self.assertEqual(result.outcome, "newly_admitted", result)
        self.assertIsNotNone(result.admission)
        self.assertIsNotNone(result.intent)
        return result

    def _claim(
        self,
        store: DispatchOutboxClaimLeaseStore,
        *,
        claim_id: str = "claim::1",
        executor_id: str = "executor::1",
        at: datetime | None = None,
    ) -> OperationResult:
        if at is not None:
            self.clock.set(at)
        result = store.claim(ClaimRequest(claim_id, executor_id))
        self.assertEqual(result.outcome, "newly_claimed", result)
        self.assertIsNotNone(result.claim)
        return result

    def _admitted_claim_store(
        self,
        *,
        claim_at: datetime | None = None,
    ) -> tuple[DispatchOutboxClaimLeaseStore, OperationResult, OperationResult]:
        store = self._new_store()
        admission = self._admit(store, at=BASE_TIME)
        claim = self._claim(store, at=claim_at or BASE_TIME + timedelta(seconds=1))
        return store, admission, claim

    def _renew_request(
        self,
        claim: object,
        renewal_id: str = "renewal::1",
        **changes: object,
    ) -> RenewalRequest:
        values = {
            "identity": claim.identity,
            "claim_id": claim.claim_id,
            "executor_instance_id": claim.executor_instance_id,
            "lease_generation": claim.lease_generation,
            "renewal_id": renewal_id,
        }
        values.update(changes)
        return RenewalRequest(**values)

    def _assessment_request(self, claim: object, **changes: object) -> CurrentClaimRequest:
        values = {
            "identity": claim.identity,
            "claim_id": claim.claim_id,
            "executor_instance_id": claim.executor_instance_id,
            "lease_generation": claim.lease_generation,
        }
        values.update(changes)
        return CurrentClaimRequest(**values)

    def _row_count(self, table: str) -> int:
        if not table.replace("_", "").isalnum():
            raise AssertionError("test table name must be a simple identifier")
        connection = sqlite3.connect(self.database_path)
        try:
            return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        finally:
            connection.close()

    def _metadata(self) -> tuple[object, ...]:
        connection = sqlite3.connect(self.database_path)
        try:
            return tuple(
                connection.execute(
                    "SELECT schema_version, migration_state, activation_state, "
                    "last_decision_time, last_decision_time_key "
                    "FROM experiment_metadata"
                ).fetchone()
            )
        finally:
            connection.close()

    def _ledger_snapshot(self) -> tuple[object, ...]:
        """Capture exact logical schema and row state for no-repair assertions."""

        connection = sqlite3.connect(self.database_path)
        try:
            schema = tuple(
                connection.execute(
                    "SELECT type, name, tbl_name, sql FROM sqlite_schema "
                    "WHERE name NOT LIKE 'sqlite_%' "
                    "ORDER BY type COLLATE BINARY, name COLLATE BINARY"
                ).fetchall()
            )
            tables = tuple(
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_schema "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name COLLATE BINARY"
                ).fetchall()
            )
            contents: list[tuple[str, tuple[tuple[object, ...], ...]]] = []
            for table in tables:
                quoted = table.replace('"', '""')
                rows = tuple(
                    sorted(
                        (
                            tuple(row)
                            for row in connection.execute(
                                f'SELECT * FROM "{quoted}"'
                            ).fetchall()
                        ),
                        key=repr,
                    )
                )
                contents.append((table, rows))
            return (
                int(connection.execute("PRAGMA application_id").fetchone()[0]),
                int(connection.execute("PRAGMA user_version").fetchone()[0]),
                int(connection.execute("PRAGMA schema_version").fetchone()[0]),
                schema,
                tuple(contents),
            )
        finally:
            connection.close()

    def _drop_mutate_restore_triggers(
        self,
        table: str,
        statement: str,
        parameters: tuple[object, ...] = (),
    ) -> None:
        connection = sqlite3.connect(self.database_path, isolation_level=None)
        try:
            triggers = connection.execute(
                "SELECT name, sql FROM sqlite_schema "
                "WHERE type='trigger' AND tbl_name=? ORDER BY name",
                (table,),
            ).fetchall()
            connection.execute("BEGIN IMMEDIATE")
            for name, _ in triggers:
                connection.execute(f'DROP TRIGGER "{name}"')
            connection.execute(statement, parameters)
            for _, sql in triggers:
                connection.execute(sql)
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _assert_renewal_unique_constraint_rejects(
        self,
        statement: str,
        parameters: tuple[object, ...],
        *expected_columns: str,
    ) -> None:
        connection = sqlite3.connect(self.database_path, isolation_level=None)
        try:
            triggers = connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type='trigger' AND tbl_name='lease_renewals' ORDER BY name"
            ).fetchall()
            connection.execute("BEGIN IMMEDIATE")
            for (name,) in triggers:
                connection.execute(f'DROP TRIGGER "{name}"')
            with self.assertRaises(sqlite3.IntegrityError) as rejected:
                connection.execute(statement, parameters)
            detail = str(rejected.exception)
            for column in expected_columns:
                self.assertIn(column, detail)
            connection.execute("ROLLBACK")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _corrupt_schema(self, label: str = "corrupt") -> None:
        connection = sqlite3.connect(self.database_path)
        try:
            connection.execute(f'CREATE TABLE "{label}" (value INTEGER)')
            connection.commit()
        finally:
            connection.close()

    def _coordinator(
        self,
        store: object,
        *,
        surrogate: LifecycleSurrogate | None = None,
        executor: object | None = None,
    ) -> tuple[LifecycleSurrogate, object, object, ExperimentCoordinator]:
        owner = surrogate or LifecycleSurrogate()
        session = owner.acquire()
        capability = executor or create_executor_capability()
        coordinator = ExperimentCoordinator(
            store,
            session=session,
            executor=capability,
        )
        return owner, session, capability, coordinator

    def _probe(
        self,
        operation: str,
        *,
        request: object | None = None,
        at: object = BASE_TIME,
        fault_point: str | None = None,
        hard_exit: bool = False,
    ) -> StorageProbeSpec:
        return StorageProbeSpec(
            configuration=self.configuration,
            operation=operation,
            request=request,
            clock=ProbeClockSpec(value=at),
            fault_point=fault_point,
            hard_exit_at_fault=hard_exit,
        )

    def _assert_store_reopens(self) -> DispatchOutboxClaimLeaseStore:
        return self._open_store(clock=MutableClock(BASE_TIME + timedelta(hours=1)))

    def _execute_scenario(self, scenario_id: int) -> None:
        spec = _SCENARIOS[scenario_id]
        handler = getattr(self, spec.handler)
        handler(*spec.arguments)

    # Admission and migration scenarios -------------------------------------------------

    def _scenario_new_admission(self) -> None:
        store = self._new_store()
        result = self._admit(store)
        self.assertEqual(result.admission.identity, result.intent.identity)
        self.assertEqual(result.admission.run_id, result.intent.run_id)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        self.assertEqual(self._row_count("legacy_admission_markers"), 0)
        self.assertEqual(store.watermark()[1], result.admission.decision_time_key)

    def _scenario_admission_history_clock(self, regression: bool) -> None:
        store = self._new_store()
        original = self._admit(store)
        watermark = store.watermark()
        calls = self.clock.calls
        if regression:
            self.clock.set(BASE_TIME - timedelta(days=1))
        else:
            self.clock.fail()
        retried = store.admit(self._request())
        self.assertEqual(retried.outcome, "existing_exact_admission")
        self.assertTrue(retried.exact_history)
        self.assertEqual(retried.admission, original.admission)
        self.assertEqual(retried.intent, original.intent)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_admission_crash(self, fault_point: str, check_watermark: bool) -> None:
        store = self._new_store()
        baseline = store.watermark()
        request = self._request()
        crash = run_storage_probe(
            self._probe(
                "admit",
                request=request,
                fault_point=fault_point,
                hard_exit=True,
            )
        )
        self.assertTrue(crash.hard_crash)
        self.assertEqual(crash.exit_code, PROBE_HARD_EXIT_CODE)
        reopened = self._assert_store_reopens()
        self.assertEqual(reopened.audit_admission(request.identity).outcome, "not_found")
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)
        self.assertEqual(reopened.watermark(), baseline)

        retry = run_storage_probe(self._probe("admit", request=request))
        self.assertEqual(retry.outcome, "newly_admitted")
        reopened = self._assert_store_reopens()
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        if check_watermark:
            self.assertNotEqual(reopened.watermark(), baseline)

    def _scenario_admission_fault_rolls_back(self, fault_point: str) -> None:
        store = self._new_store()
        baseline = store.watermark()
        hook = FaultAt(fault_point)
        failing = self._open_store(fault_hook=hook)
        result = failing.admit(self._request())
        self.assertEqual(hook.reached, 1)
        self.assertIn(result.outcome, {"fault_injected", "commit_unknown"})
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)
        self.assertEqual(store.watermark(), baseline)

    def _scenario_admission_ambiguous(self, committed: bool) -> None:
        store = self._new_store()
        point = "admission.after_commit" if committed else "admission.before_commit"
        hook = FaultAt(point, CommitUnknownFault)
        uncertain_store = self._open_store(fault_hook=hook)
        request = self._request()
        uncertain = uncertain_store.admit(request)
        self.assertEqual(uncertain.outcome, "commit_unknown")
        self.assertEqual(hook.reached, 1)
        retry = store.admit(request)
        self.assertEqual(
            retry.outcome,
            "existing_exact_admission" if committed else "newly_admitted",
        )
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_migrate_existing(self) -> None:
        self._provision_legacy()
        legacy = self._legacy_store()
        requests = [self._request(str(index)) for index in range(3)]
        for index, request in enumerate(requests):
            self.clock.set(BASE_TIME + timedelta(seconds=index))
            self.assertEqual(legacy.admit_legacy(request).outcome, "newly_legacy_admitted")
        before = [legacy.audit_admission(request.identity).admission for request in requests]
        self._migrate()
        current = self._open_store()
        after = [current.audit_admission(request.identity).admission for request in requests]
        self.assertEqual(after, before)
        self.assertEqual(self._row_count("legacy_admission_markers"), 3)
        self.assertEqual(self._row_count("dispatch_intents"), 0)
        self.assertEqual(self._metadata()[:2], (CURRENT_SCHEMA_VERSION, "clean"))

    def _scenario_migration_preflight_mismatch(self) -> None:
        cases = (
            "version",
            "application",
            "domain",
            "fingerprint",
            "checksum",
            "payload",
        )
        for name in cases:
            with self.subTest(name=name):
                self._reset_ledger()
                self._provision_legacy()
                legacy = self._legacy_store()
                request = self._request(f"preflight-{name}")
                self.assertEqual(
                    legacy.admit_legacy(request).outcome,
                    "newly_legacy_admitted",
                )
                configuration = self.configuration
                if name == "version":
                    connection = sqlite3.connect(self.database_path)
                    try:
                        connection.execute("PRAGMA user_version=99")
                        connection.commit()
                    finally:
                        connection.close()
                elif name == "application":
                    connection = sqlite3.connect(self.database_path)
                    try:
                        connection.execute("PRAGMA application_id=1")
                        connection.commit()
                    finally:
                        connection.close()
                elif name == "domain":
                    configuration = StoreConfiguration(
                        database_path=self.configuration.database_path,
                        authorization_domain_id="domain::wrong",
                        ledger_instance_id=self.configuration.ledger_instance_id,
                        domain_generation=self.configuration.domain_generation,
                        lease_duration_us=self.configuration.lease_duration_us,
                        busy_timeout_ms=self.configuration.busy_timeout_ms,
                    )
                elif name == "fingerprint":
                    self._drop_mutate_restore_triggers(
                        "experiment_metadata",
                        "UPDATE experiment_metadata SET schema_fingerprint=?",
                        ("0" * 64,),
                    )
                elif name == "checksum":
                    self._drop_mutate_restore_triggers(
                        "experiment_schema_migrations",
                        "UPDATE experiment_schema_migrations SET sha256=? "
                        "WHERE migration_id=1",
                        ("0" * 64,),
                    )
                else:
                    self._drop_mutate_restore_triggers(
                        "experiment_admissions",
                        "UPDATE experiment_admissions SET admission_payload=X'00'",
                    )
                before = self._ledger_snapshot()
                result = DispatchOutboxClaimLeaseStore.migrate_legacy(configuration)
                self.assertIn(result.outcome, {"incompatible_schema", "integrity_failure"})
                self.assertEqual(self._ledger_snapshot(), before)

    def _reset_ledger(self) -> None:
        for candidate in (
            self.database_path,
            Path(str(self.database_path) + "-wal"),
            Path(str(self.database_path) + "-shm"),
        ):
            candidate.unlink(missing_ok=True)

    def _scenario_operational_open_rejects_schema_states(self) -> None:
        variants = ("old", "newer", "dirty", "partial")
        for variant in variants:
            with self.subTest(variant=variant):
                self._reset_ledger()
                if variant == "old":
                    self._provision_legacy()
                elif variant == "newer":
                    self._new_store()
                    connection = sqlite3.connect(self.database_path)
                    try:
                        connection.execute("PRAGMA user_version=99")
                        connection.commit()
                    finally:
                        connection.close()
                elif variant == "dirty":
                    self._new_store()
                    self._drop_mutate_restore_triggers(
                        "experiment_metadata",
                        "UPDATE experiment_metadata SET migration_state='dirty'",
                    )
                else:
                    self._new_store()
                    connection = sqlite3.connect(self.database_path)
                    try:
                        connection.execute("DROP TABLE lease_renewals")
                        connection.commit()
                    finally:
                        connection.close()
                before = self._ledger_snapshot()
                with self.assertRaises((IncompatibleSchemaError, IntegrityFailure)):
                    self._open_store()
                self.assertEqual(self._ledger_snapshot(), before)

    def _scenario_migration_crash(self, fault_point: str) -> None:
        self._provision_legacy()
        crash = run_storage_probe(
            self._probe(
                "migrate_legacy",
                fault_point=fault_point,
                hard_exit=True,
            )
        )
        self.assertTrue(crash.hard_crash)
        legacy = self._legacy_store()
        self.assertEqual(self._metadata()[:2], (1, "clean"))
        self.assertIsNotNone(legacy.connection_profile())

        retry = run_storage_probe(self._probe("migrate_legacy"))
        self.assertEqual(retry.outcome, "migrated")
        store = self._assert_store_reopens()
        self.assertEqual(self._metadata()[:2], (CURRENT_SCHEMA_VERSION, "clean"))
        self.assertIsNotNone(store.connection_profile())

        if fault_point == "migration.after_clean_transition":
            # Scenario 89 locks both sides of the commit boundary. The branch
            # above proves the final precommit cut rolls back to the old
            # ledger; now hard-exit after COMMIT and reconcile the new ledger.
            self._reset_ledger()
            self._provision_legacy()
            legacy = self._legacy_store()
            request = self._request("migration-after-commit")
            created = legacy.admit_legacy(request)
            self.assertEqual(created.outcome, "newly_legacy_admitted")
            committed_crash = run_storage_probe(
                self._probe(
                    "migrate_legacy",
                    fault_point="migration.after_commit",
                    hard_exit=True,
                )
            )
            self.assertTrue(committed_crash.hard_crash)
            self.assertEqual(committed_crash.exit_code, PROBE_HARD_EXIT_CODE)
            reconciliation = run_storage_probe(self._probe("migrate_legacy"))
            self.assertEqual(reconciliation.outcome, "already_migrated")
            current = self._assert_store_reopens()
            self.assertEqual(
                self._metadata()[:3],
                (CURRENT_SCHEMA_VERSION, "clean", "active"),
            )
            history = current.audit_admission(request.identity)
            self.assertEqual(history.outcome, "audited_admission_history")
            self.assertTrue(history.exact_history)
            self.assertEqual(history.admission, created.admission)
            self.assertIsNone(history.intent)
            self.assertEqual(self._row_count("experiment_admissions"), 1)
            self.assertEqual(self._row_count("legacy_admission_markers"), 1)
            self.assertEqual(self._row_count("dispatch_intents"), 0)

    def _scenario_migration_ambiguous(self) -> None:
        for committed, point, expected in (
            (False, "migration.before_commit", "migrated"),
            (True, "migration.after_commit", "already_migrated"),
        ):
            with self.subTest(committed=committed):
                self._reset_ledger()
                self._provision_legacy()
                hook = FaultAt(point, CommitUnknownFault)
                uncertain = DispatchOutboxClaimLeaseStore.migrate_legacy(
                    self.configuration,
                    fault_hook=hook,
                )
                self.assertEqual(uncertain.outcome, "commit_unknown")
                reconciled = DispatchOutboxClaimLeaseStore.migrate_legacy(self.configuration)
                self.assertEqual(reconciled.outcome, expected)
                self.assertEqual(self._metadata()[:2], (CURRENT_SCHEMA_VERSION, "clean"))

    def _scenario_legacy_retry(self, reopen: bool) -> None:
        self._provision_legacy()
        legacy = self._legacy_store()
        request = self._request()
        created = legacy.admit_legacy(request)
        self.assertEqual(created.outcome, "newly_legacy_admitted")
        self._migrate()
        clock = MutableClock(BASE_TIME - timedelta(days=3))
        if reopen:
            store = self._open_store(clock=clock)
        else:
            store = DispatchOutboxClaimLeaseStore.open(
                self.configuration, clock=clock
            )
        watermark = store.watermark()
        clock.fail()
        history = store.admit(request)
        self.assertEqual(history.outcome, "existing_legacy_admission")
        self.assertTrue(history.exact_history)
        self.assertIsNone(history.intent)
        self.assertEqual(clock.calls, 0)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("legacy_admission_markers"), 1)

    def _scenario_xor_corruption(self) -> None:
        variants = ("missing", "orphan", "overlap", "duplicate")
        for variant in variants:
            with self.subTest(variant=variant):
                self._reset_ledger()
                store = self._new_store()
                admission = self._admit(store)
                if variant == "missing":
                    self._drop_mutate_restore_triggers(
                        "dispatch_intents",
                        "DELETE FROM dispatch_intents",
                    )
                elif variant == "orphan":
                    connection = sqlite3.connect(self.database_path)
                    try:
                        source = tuple(
                            connection.execute(
                                "SELECT * FROM dispatch_intents"
                            ).fetchone()
                        )
                        orphan = list(source)
                        orphan[3] = b"grant::orphan"
                        connection.execute(
                            "INSERT INTO dispatch_intents VALUES "
                            "(?, ?, ?, ?, ?, ?, ?, ?)",
                            tuple(orphan),
                        )
                        connection.commit()
                    finally:
                        connection.close()
                elif variant == "overlap":
                    identity = tuple(
                        component.encode("utf-8")
                        for component in admission.admission.identity.as_tuple()
                    )
                    self._drop_mutate_restore_triggers(
                        "legacy_admission_markers",
                        "INSERT INTO legacy_admission_markers VALUES "
                        "(?, ?, ?, ?, 2, ?)",
                        (*identity, b"synthetic-overlap"),
                    )
                else:
                    before = self._ledger_snapshot()
                    connection = sqlite3.connect(self.database_path)
                    try:
                        row = tuple(
                            connection.execute(
                                "SELECT * FROM dispatch_intents"
                            ).fetchone()
                        )
                        with self.assertRaises(sqlite3.IntegrityError):
                            connection.execute(
                                "INSERT INTO dispatch_intents VALUES "
                                "(?, ?, ?, ?, ?, ?, ?, ?)",
                                row,
                            )
                        connection.rollback()
                    finally:
                        connection.close()
                    self.assertEqual(self._ledger_snapshot(), before)
                    reopened = self._open_store()
                    self.assertEqual(
                        reopened.audit_admission(admission.admission.identity).intent,
                        admission.intent,
                    )
                    continue
                corrupted = self._ledger_snapshot()
                with self.assertRaises(IntegrityFailure):
                    self._open_store()
                self.assertEqual(self._ledger_snapshot(), corrupted)
                self.assertEqual(admission.admission.identity, self._request().identity)

    # Claim, selection, no-row, reclaim, and assessment scenarios ----------------------

    def _seed_intents(
        self,
        store: DispatchOutboxClaimLeaseStore,
        suffixes: tuple[str, ...],
        *,
        equal_time: bool = False,
    ) -> tuple[OperationResult, ...]:
        results: list[OperationResult] = []
        for index, suffix in enumerate(suffixes):
            at = BASE_TIME if equal_time else BASE_TIME + timedelta(seconds=index)
            results.append(self._admit(store, self._request(suffix), at=at))
        return tuple(results)

    def _scenario_one_pending_intent(self) -> None:
        store = self._new_store()
        admission = self._admit(store, at=BASE_TIME)
        claim = self._claim(store, at=BASE_TIME + timedelta(seconds=1))
        self.assertEqual(claim.claim.identity, admission.intent.identity)
        self.assertEqual(claim.claim.lease_generation, 1)
        self.assertEqual(
            claim.claim.lease_until_key - claim.claim.acquired_at_key,
            LEASE_DURATION_US,
        )
        self.assertEqual(store.watermark()[1], claim.claim.acquired_at_key)

    def _scenario_multiple_eligible_intents(self) -> None:
        store = self._new_store()
        admissions = self._seed_intents(store, ("later", "latest"))
        claim = self._claim(store, at=BASE_TIME + timedelta(seconds=5))
        self.assertEqual(claim.claim.identity, admissions[0].intent.identity)
        self.assertNotEqual(claim.claim.identity, admissions[1].intent.identity)

    def _scenario_raw_claim_race(self) -> None:
        store = self._new_store()
        self._admit(store)
        results = race_storage_probes(
            (
                self._probe(
                    "claim",
                    request=ClaimRequest("claim::race-a", "executor::race-a"),
                    at=BASE_TIME + timedelta(seconds=1),
                ),
                self._probe(
                    "claim",
                    request=ClaimRequest("claim::race-b", "executor::race-b"),
                    at=BASE_TIME + timedelta(seconds=1),
                ),
            )
        )
        self.assertCountEqual(
            [result.outcome for result in results],
            ["newly_claimed", "temporarily_unavailable"],
        )
        self.assertTrue(all(result.evidence_scope == "raw_sqlite_storage_mechanism_only" for result in results))
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_concurrent_lifecycle_operations(self) -> None:
        store = self._new_store()
        self._admit(store)
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        both_entered = threading.Event()
        both_writes_finished = threading.Event()
        release = threading.Event()
        entered = 0
        lock = threading.Lock()
        errors: list[BaseException] = []
        results: list[OperationResult] = []

        def guarded(index: int) -> None:
            nonlocal entered
            try:
                with session.operation() as guard:
                    with lock:
                        entered += 1
                        if entered == 2:
                            both_entered.set()
                    if not both_entered.wait(5):
                        raise AssertionError("both lifecycle guards did not enter")
                    result = store.claim(
                        ClaimRequest(
                            f"claim::lifecycle-{index}",
                            f"executor::lifecycle-{index}",
                        )
                    )
                    with lock:
                        results.append(result)
                        if len(results) == 2:
                            both_writes_finished.set()
                    if not release.wait(5):
                        raise AssertionError("guard release was not signaled")
                    guard.complete("ok")
            except BaseException as error:  # captured for the parent test thread
                errors.append(error)

        threads = [
            threading.Thread(target=guarded, args=(index,)) for index in range(2)
        ]
        for thread in threads:
            thread.start()
        self.assertTrue(both_entered.wait(5))
        self.assertEqual(surrogate.active_operation_count, 2)
        fenced = threading.Event()

        def fence() -> None:
            session.fence(timeout=5)
            fenced.set()

        fence_thread = threading.Thread(target=fence)
        fence_thread.start()
        deadline = time.monotonic() + 5
        while surrogate.state is not LifecycleState.FENCING:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.001)
        self.assertFalse(fenced.is_set())
        self.assertTrue(both_writes_finished.wait(10))
        self.assertCountEqual(
            [result.outcome for result in results],
            ["newly_claimed", "temporarily_unavailable"],
        )
        self.assertEqual(self._row_count("dispatch_claims"), 1)
        self.assertFalse(fenced.is_set())
        release.set()
        for thread in threads:
            thread.join(5)
        fence_thread.join(5)
        self.assertEqual(len(errors), 2)
        self.assertTrue(
            all(
                isinstance(error, harness_module.LifecyclePostcheckError)
                and error.terminal
                for error in errors
            )
        )
        self.assertTrue(fenced.is_set())
        self.assertEqual(surrogate.state, LifecycleState.FENCED)

    def _scenario_claim_race_winner(self) -> None:
        store = self._new_store()
        self._admit(store)
        barrier = threading.Barrier(3)
        results: list[OperationResult] = []

        def claim(index: int) -> None:
            barrier.wait()
            results.append(store.claim(ClaimRequest(f"claim::thread-{index}", f"executor::{index}")))

        threads = [threading.Thread(target=claim, args=(index,)) for index in (1, 2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(10)
        self.assertEqual(len(results), 2)
        self.assertCountEqual(
            [result.outcome for result in results],
            ["newly_claimed", "temporarily_unavailable"],
        )
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_active_lease(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        second = store.claim(ClaimRequest("claim::2", "executor::2"))
        self.assertEqual(second.outcome, "temporarily_unavailable")
        self.assertTrue(second.reevaluation)
        self.assertIsNone(second.claim)
        self.assertEqual(self._row_count("dispatch_claims"), 1)
        self.assertEqual(store.audit_claim("claim::2").outcome, "not_found")
        self.assertEqual(first.claim.lease_generation, 1)

    def _scenario_claim_history(self, state: str) -> None:
        if state == "active":
            store = self._new_store()
            self._admit(store, at=BASE_TIME)
            hook = FaultAt("claim.after_commit", CommitUnknownFault)
            uncertain_store = self._open_store(fault_hook=hook)
            self.clock.set(BASE_TIME + timedelta(seconds=1))
            lost = uncertain_store.claim(ClaimRequest("claim::1", "executor::1"))
            self.assertEqual(lost.outcome, "commit_unknown")
            self.assertEqual(lost.retry, "retry_exact")
            self.assertIsNone(lost.committed)
            self.assertEqual(hook.reached, 1)
            self.assertEqual(self._row_count("dispatch_claims"), 1)
            audited = store.audit_claim("claim::1")
            self.assertEqual(audited.outcome, "audited_claim_history")
            claim = audited.claim
        else:
            store, _, first = self._admitted_claim_store()
            claim = first.claim
        if state == "expired":
            self.clock.set(BASE_TIME + timedelta(seconds=31))
        elif state == "superseded":
            self.clock.set(BASE_TIME + timedelta(seconds=31))
            second = store.claim(ClaimRequest("claim::2", "executor::2"))
            self.assertEqual(second.outcome, "newly_claimed")
        before_calls = self.clock.calls
        before_watermark = store.watermark()
        history = store.claim(ClaimRequest(claim.claim_id, claim.executor_instance_id))
        self.assertEqual(history.outcome, "existing_claim_history")
        self.assertTrue(history.exact_history)
        self.assertEqual(history.claim, claim)
        self.assertIsNone(history.assessment)
        self.assertEqual(self.clock.calls, before_calls)
        self.assertEqual(store.watermark(), before_watermark)
        assessment = store.assess_current_claim(self._assessment_request(claim))
        if state == "active":
            self.assertEqual(assessment.outcome, "active")
        else:
            self.assertEqual(assessment.outcome, "inactive")

    def _scenario_claim_executor_rebound(self) -> None:
        store, _, first = self._admitted_claim_store()
        calls = self.clock.calls
        rebound = store.claim(ClaimRequest(first.claim.claim_id, "executor::different"))
        self.assertEqual(rebound.outcome, "executor_conflict")
        self.assertIsNone(rebound.claim)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_stored_claim_rebound(self) -> None:
        for variant in ("dispatch", "generation"):
            with self.subTest(variant=variant):
                self._reset_ledger()
                store = self._new_store()
                first_admission = self._admit(
                    store,
                    self._request("claim-binding-a"),
                    at=BASE_TIME,
                )
                second_admission = self._admit(
                    store,
                    self._request("claim-binding-b"),
                    at=BASE_TIME + timedelta(seconds=1),
                )
                first = self._claim(
                    store,
                    at=BASE_TIME + timedelta(seconds=2),
                )
                self.assertEqual(first.claim.identity, first_admission.intent.identity)
                if variant == "dispatch":
                    rebound_identity = tuple(
                        component.encode("utf-8")
                        for component in second_admission.intent.identity.as_tuple()
                    )
                    self._drop_mutate_restore_triggers(
                        "dispatch_claims",
                        "UPDATE dispatch_claims SET "
                        "authorization_domain_id=?, issuer_kind=?, "
                        "issuer_id=?, grant_id=? WHERE claim_id=?",
                        (*rebound_identity, first.claim.claim_id.encode("utf-8")),
                    )
                else:
                    self._drop_mutate_restore_triggers(
                        "dispatch_claims",
                        "UPDATE dispatch_claims SET lease_generation=2 "
                        "WHERE claim_id=?",
                        (first.claim.claim_id.encode("utf-8"),),
                    )
                corrupted = self._ledger_snapshot()
                result = store.claim(
                    ClaimRequest(
                        first.claim.claim_id,
                        first.claim.executor_instance_id,
                    )
                )
                self.assertEqual(result.outcome, "integrity_failure")
                self.assertEqual(self._ledger_snapshot(), corrupted)
                self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_expiry_boundary(self) -> None:
        store, _, first = self._admitted_claim_store()
        boundary = BASE_TIME + timedelta(seconds=31)
        self.clock.set(boundary)
        inactive = store.assess_current_claim(self._assessment_request(first.claim))
        self.assertEqual(inactive.outcome, "inactive")
        self.assertEqual(inactive.assessment.reason, "expired")
        reclaimed = store.claim(ClaimRequest("claim::boundary", "executor::2"))
        self.assertEqual(reclaimed.outcome, "newly_claimed")
        self.assertEqual(reclaimed.claim.lease_generation, 2)

    def _scenario_reclaim(self, different_worker: bool) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=31))
        executor = "executor::2" if different_worker else first.claim.executor_instance_id
        same_id = store.claim(ClaimRequest(first.claim.claim_id, executor))
        if different_worker:
            self.assertEqual(same_id.outcome, "executor_conflict")
        else:
            self.assertEqual(same_id.outcome, "existing_claim_history")
        reclaimed = store.claim(ClaimRequest("claim::reclaim", executor))
        self.assertEqual(reclaimed.outcome, "newly_claimed")
        self.assertEqual(reclaimed.claim.lease_generation, 2)
        self.assertEqual(self._row_count("dispatch_claims"), 2)

    def _scenario_stale_claimant(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=31))
        second = store.claim(ClaimRequest("claim::2", "executor::2"))
        calls = self.clock.calls
        stale = store.renew(self._renew_request(first.claim, "renewal::stale"))
        self.assertEqual(stale.outcome, "stale_generation")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("lease_renewals"), 0)
        self.assertEqual(second.claim.lease_generation, 2)

    def _scenario_claim_crash(self, fault_point: str) -> None:
        store = self._new_store()
        admission = self._admit(store)
        baseline = store.watermark()
        claim_id = f"claim::{fault_point}"
        request = ClaimRequest(claim_id, "executor::crash")
        crash = run_storage_probe(
            self._probe(
                "claim",
                request=request,
                at=BASE_TIME + timedelta(seconds=1),
                fault_point=fault_point,
                hard_exit=True,
            )
        )
        self.assertTrue(crash.hard_crash)
        reopened = self._assert_store_reopens()
        self.assertEqual(reopened.audit_claim(claim_id).outcome, "not_found")
        self.assertEqual(reopened.watermark(), baseline)
        self.assertEqual(self._row_count("dispatch_claims"), 0)

        later = reopened.claim(request)
        self.assertEqual(later.outcome, "newly_claimed")
        self.assertEqual(later.claim.identity, admission.intent.identity)
        self.assertEqual(later.claim.lease_generation, 1)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_claim_ambiguous(self) -> None:
        for committed, point, expected in (
            (False, "claim.before_commit", "newly_claimed"),
            (True, "claim.after_commit", "existing_claim_history"),
        ):
            with self.subTest(committed=committed):
                self._reset_ledger()
                store = self._new_store()
                self._admit(store)
                hook = FaultAt(point, CommitUnknownFault)
                uncertain_store = self._open_store(fault_hook=hook)
                request = ClaimRequest("claim::ambiguous", "executor::ambiguous")
                uncertain = uncertain_store.claim(request)
                self.assertEqual(uncertain.outcome, "commit_unknown")
                retry = store.claim(request)
                self.assertEqual(retry.outcome, expected)
                self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_worker_crash_after_claim(self) -> None:
        store = self._new_store()
        self._admit(store)
        first = run_storage_probe(
            self._probe(
                "claim",
                request=ClaimRequest("claim::worker", "executor::old-process"),
                at=BASE_TIME + timedelta(seconds=1),
            )
        )
        self.assertEqual(first.outcome, "newly_claimed")
        self.clock.set(BASE_TIME + timedelta(seconds=31))
        reopened = self._open_store()
        reclaimed = reopened.claim(ClaimRequest("claim::new", "executor::new-process"))
        self.assertEqual(reclaimed.outcome, "newly_claimed")
        self.assertEqual(reclaimed.claim.lease_generation, 2)

    def _scenario_empty_queue(self) -> None:
        store = self._new_store()
        baseline = store.watermark()
        result = store.claim(ClaimRequest("claim::empty", "executor::1"))
        self.assertEqual(result.outcome, "empty")
        self.assertTrue(result.reevaluation)
        self.assertEqual(self.clock.calls, 0)
        self.assertEqual(store.watermark(), baseline)
        self.assertEqual(store.audit_claim("claim::empty").outcome, "not_found")

    def _scenario_authority_ineligible(self) -> None:
        store = self._new_store(complete=False)
        admission = self._admit_with_complete_transition(store)
        # Recreate an incomplete store containing the Intent by changing only
        # the test ledger's completeness bit under restored triggers.
        self._drop_mutate_restore_triggers(
            "experiment_metadata",
            "UPDATE experiment_metadata SET revocation_state_complete=0",
        )
        reopened = self._open_store()
        baseline = reopened.watermark()
        calls = self.clock.calls
        request = ClaimRequest("claim::ineligible", "executor::1")
        result = reopened.claim(request)
        self.assertEqual(result.outcome, "authority_ineligible")
        self.assertTrue(result.reevaluation)
        self.assertFalse(result.exact_history)
        self.assertFalse(result.committed)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(reopened.watermark(), baseline)
        self.assertIsNone(result.admission)
        self.assertIsNone(result.intent)
        self.assertIsNone(result.claim)
        for component in admission.intent.identity.as_tuple():
            self.assertNotIn(component, result.detail)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        self.assertEqual(reopened.audit_claim(request.claim_id).outcome, "not_found")

        # No-row rejection leaves the Claim ID unconsumed.
        self.assertEqual(
            reopened.set_revocation_completeness().outcome,
            "revocation_evidence_complete",
        )
        later = reopened.claim(request)
        self.assertEqual(later.outcome, "newly_claimed")
        self.assertEqual(later.claim.claim_id, request.claim_id)
        self.assertEqual(later.claim.identity, admission.intent.identity)

    def _admit_with_complete_transition(
        self, store: DispatchOutboxClaimLeaseStore
    ) -> OperationResult:
        completed = store.set_revocation_completeness()
        self.assertEqual(completed.outcome, "revocation_evidence_complete")
        return self._admit(store)

    def _scenario_all_active(self) -> None:
        store = self._new_store()
        self._seed_intents(store, ("a", "b"))
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        first = store.claim(ClaimRequest("claim::a", "executor::a"))
        self.assertEqual(first.outcome, "newly_claimed")
        # Claim the second Intent after making only the first temporarily active
        # is impossible through claim-next, so mark the first expired and claim
        # it again only in dedicated reclaim scenarios. One active eligible
        # Intent is sufficient to establish the no-row semantics here.
        result = store.claim(ClaimRequest("claim::no-row", "executor::b"))
        self.assertEqual(result.outcome, "newly_claimed")
        watermark_before = store.watermark()
        calls = self.clock.calls
        self.clock.set(BASE_TIME + timedelta(seconds=3))
        request = ClaimRequest("claim::all-active", "executor::c")
        final = store.claim(request)
        self.assertEqual(final.outcome, "temporarily_unavailable")
        self.assertTrue(final.reevaluation)
        self.assertFalse(final.exact_history)
        self.assertTrue(final.committed)
        self.assertIsNone(final.claim)
        self.assertEqual(self.clock.calls, calls + 1)
        watermark_after = store.watermark()
        self.assertGreater(watermark_after[1], watermark_before[1])
        self.assertEqual(
            watermark_after[1],
            first.claim.acquired_at_key + 1_000_000,
        )
        self.assertLess(watermark_after[1], first.claim.lease_until_key)
        self.assertEqual(store.audit_claim(request.claim_id).outcome, "not_found")
        self.assertEqual(self._row_count("dispatch_claims"), 2)

        # The watermark-only result does not consume the Claim ID.
        self.clock.set(BASE_TIME + timedelta(seconds=33))
        later = store.claim(request)
        self.assertEqual(later.outcome, "newly_claimed")
        self.assertEqual(later.claim.claim_id, request.claim_id)
        self.assertEqual(later.claim.lease_generation, 2)
        self.assertEqual(self._row_count("dispatch_claims"), 3)

    def _scenario_lost_no_row(self, kind: str) -> None:
        if kind == "empty":
            store = self._new_store()
            baseline = store.watermark()
            calls = self.clock.calls
            surrogate = LifecycleSurrogate()
            session = surrogate.acquire()
            executor = create_executor_capability()
            proxy = _LifecycleTransitionStore(store, session, terminal=False)
            coordinator = ExperimentCoordinator(
                proxy,
                session=session,
                executor=executor,
            )
            lost = coordinator.claim("claim::lost")
            proxy.join()
            self.assertEqual(lost.outcome, "commit_unknown")
            self.assertIsNone(lost.store_result)
            self.assertFalse(lost.postchecked)
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(store.watermark(), baseline)
            self.assertEqual(self._row_count("dispatch_claims"), 0)
            self.assertEqual(store.audit_claim("claim::lost").outcome, "not_found")

            surrogate.recover_after_loss(timeout=5)
            second = ExperimentCoordinator(
                store,
                session=surrogate.acquire(),
                executor=executor,
            ).claim("claim::lost")
            self.assertEqual(second.outcome, "empty")
            self.assertTrue(second.postchecked)
            self.assertIsNotNone(second.store_result)
            self.assertTrue(second.store_result.reevaluation)
            self.assertFalse(second.store_result.exact_history)
            self.assertFalse(second.store_result.committed)
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(store.watermark(), baseline)
            self.assertEqual(self._row_count("dispatch_claims"), 0)
        else:
            store = self._new_store()
            admissions = self._seed_intents(store, ("a", "b"))
            self.clock.set(BASE_TIME + timedelta(seconds=2))
            active_a = store.claim(ClaimRequest("claim::active-a", "executor::a"))
            active_b = store.claim(ClaimRequest("claim::active-b", "executor::b"))
            self.assertEqual(active_a.outcome, "newly_claimed")
            self.assertEqual(active_b.outcome, "newly_claimed")
            self.assertEqual(
                {active_a.claim.identity, active_b.claim.identity},
                {admission.intent.identity for admission in admissions},
            )
            self.assertEqual(self._row_count("dispatch_claims"), 2)

            request = ClaimRequest("claim::lost", "executor::lost")
            watermark_before = store.watermark()
            calls = self.clock.calls
            hook = FaultAt("claim.after_commit", CommitUnknownFault)
            uncertain_store = self._open_store(fault_hook=hook)
            self.clock.set(BASE_TIME + timedelta(seconds=3))
            lost = uncertain_store.claim(request)

            self.assertEqual(hook.reached, 1)
            self.assertEqual(lost.outcome, "commit_unknown")
            self.assertEqual(lost.retry, "reevaluate")
            self.assertTrue(lost.reevaluation)
            self.assertFalse(lost.exact_history)
            self.assertIsNone(lost.committed)
            self.assertIsNone(lost.claim)
            self.assertEqual(self.clock.calls, calls + 1)
            watermark_after_loss = store.watermark()
            self.assertGreater(watermark_after_loss[1], watermark_before[1])
            self.assertEqual(
                watermark_after_loss[1],
                active_a.claim.acquired_at_key + 1_000_000,
            )
            self.assertLess(
                watermark_after_loss[1],
                active_a.claim.lease_until_key,
            )
            self.assertEqual(store.audit_claim(request.claim_id).outcome, "not_found")
            self.assertEqual(self._row_count("dispatch_claims"), 2)
            self.assertEqual(self._row_count("lease_renewals"), 0)
            for active in (active_a.claim, active_b.claim):
                history = store.audit_claim(active.claim_id)
                self.assertEqual(history.outcome, "audited_claim_history")
                self.assertEqual(history.claim, active)
                self.assertTrue(history.exact_history)

            retry = store.claim(request)
            self.assertEqual(retry.outcome, "temporarily_unavailable")
            self.assertTrue(retry.reevaluation)
            self.assertFalse(retry.exact_history)
            self.assertTrue(retry.committed)
            self.assertIsNone(retry.claim)
            self.assertEqual(self.clock.calls, calls + 2)
            self.assertEqual(store.watermark(), watermark_after_loss)
            self.assertEqual(store.audit_claim(request.claim_id).outcome, "not_found")
            self.assertEqual(self._row_count("dispatch_claims"), 2)

            self.clock.set(BASE_TIME + timedelta(seconds=32))
            later = store.claim(request)
            self.assertEqual(later.outcome, "newly_claimed")
            self.assertFalse(later.exact_history)
            self.assertTrue(later.committed)
            self.assertEqual(later.claim.claim_id, request.claim_id)
            self.assertEqual(
                later.claim.executor_instance_id,
                request.executor_instance_id,
            )
            self.assertEqual(later.claim.identity, active_a.claim.identity)
            self.assertEqual(later.claim.lease_generation, 2)
            self.assertEqual(
                later.claim.acquired_at_key,
                active_a.claim.lease_until_key,
            )
            self.assertEqual(store.watermark()[1], later.claim.acquired_at_key)
            self.assertEqual(self._row_count("dispatch_claims"), 3)
            self.assertEqual(self._row_count("lease_renewals"), 0)
            recovered = store.audit_claim(request.claim_id)
            self.assertEqual(recovered.outcome, "audited_claim_history")
            self.assertEqual(recovered.claim, later.claim)
            self.assertTrue(recovered.exact_history)

    def _scenario_no_row_later_eligible(self) -> None:
        store = self._new_store()
        first = store.claim(ClaimRequest("claim::later", "executor::1"))
        self.assertEqual(first.outcome, "empty")
        self._admit(store)
        self.clock.set(BASE_TIME + timedelta(seconds=1))
        second = store.claim(ClaimRequest("claim::later", "executor::1"))
        self.assertEqual(second.outcome, "newly_claimed")
        self.assertEqual(second.claim.claim_id, "claim::later")
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_claim_postcheck(self, terminal: bool) -> None:
        store = self._new_store()
        self._admit(store)
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        executor = create_executor_capability()
        proxy = _LifecycleTransitionStore(store, session, terminal=terminal)
        coordinator = ExperimentCoordinator(proxy, session=session, executor=executor)
        result = coordinator.claim("claim::postcheck")
        proxy.join()
        self.assertIsNone(result.store_result)
        self.assertFalse(result.postchecked)
        if terminal:
            self.assertEqual(result.outcome, "terminal_fence")
            audit_store = self._open_store(allow_fenced=True)
            audit = audit_store.audit_claim("claim::postcheck")
            self.assertEqual(audit.outcome, "audited_claim_history")
            self.assertTrue(audit.exact_history)
            self.assertIsNotNone(audit.claim)
            self.assertIn("non-authoritative", audit.detail)
            retry = coordinator.claim("claim::postcheck")
            self.assertEqual(retry.outcome, "terminal_fence")
            self.assertIsNone(retry.store_result)
            renewal = coordinator.renew(
                audit.claim.identity,
                audit.claim.claim_id,
                audit.claim.lease_generation,
                "renewal::terminal-recovery",
            )
            self.assertEqual(renewal.outcome, "terminal_fence")
            self.assertIsNone(renewal.store_result)
            self.assertEqual(self._row_count("dispatch_claims"), 1)
            self.assertEqual(self._row_count("lease_renewals"), 0)
        else:
            self.assertEqual(result.outcome, "commit_unknown")
            audit = self._open_store().audit_claim("claim::postcheck")
            self.assertEqual(audit.outcome, "audited_claim_history")
            self.assertTrue(audit.exact_history)
            surrogate.recover_after_loss(timeout=5)
            new_session = surrogate.acquire()
            recovered_coordinator = ExperimentCoordinator(
                store, session=new_session, executor=executor
            )
            recovered = recovered_coordinator.claim("claim::postcheck")
            self.assertEqual(recovered.outcome, "existing_claim_history")
            self.assertTrue(recovered.postchecked)
            self.assertEqual(recovered.store_result.claim, audit.claim)
            self.assertTrue(recovered.store_result.exact_history)
            self.assertIsNone(recovered.store_result.assessment)
            self.assertEqual(self._row_count("dispatch_claims"), 1)
            self.clock.set(BASE_TIME + timedelta(seconds=2))
            assessment = recovered_coordinator.assess_current_claim(
                audit.claim.identity,
                audit.claim.claim_id,
                audit.claim.lease_generation,
            )
            self.assertEqual(assessment.outcome, "active")
            self.assertEqual(assessment.store_result.assessment.claim, audit.claim)

    def _scenario_old_executor_coordinator(self) -> None:
        store = self._new_store()
        self._admit(store)
        surrogate, session, capability, coordinator = self._coordinator(store)
        old_id = coordinator.executor_instance_id
        session.release(timeout=5)
        with mock.patch.object(store, "claim", wraps=store.claim) as claim_spy:
            replay = coordinator.claim("claim::old-executor-replay")
        self.assertEqual(replay.outcome, "lifecycle_unavailable")
        self.assertIsNone(replay.store_result)
        claim_spy.assert_not_called()
        self.assertEqual(
            store.audit_claim("claim::old-executor-replay").outcome,
            "not_found",
        )
        new_session = surrogate.acquire()
        with mock.patch.object(store, "claim", wraps=store.claim) as claim_spy:
            with self.assertRaises(TypeError):
                ExperimentCoordinator(
                    store,
                    session=new_session,
                    executor=old_id,
                )
        claim_spy.assert_not_called()
        with self.assertRaises(TypeError):
            pickle.dumps(capability)
        self.assertEqual(
            store.audit_claim("claim::old-executor-replay").outcome,
            "not_found",
        )
        new_capability = create_executor_capability()
        self.assertNotEqual(new_capability.executor_instance_id, old_id)
        current = ExperimentCoordinator(
            store, session=new_session, executor=new_capability
        )
        self.assertNotEqual(current.executor_instance_id, old_id)
        accepted = current.claim("claim::old-executor-replay")
        self.assertEqual(accepted.outcome, "newly_claimed")
        self.assertEqual(
            accepted.store_result.claim.executor_instance_id,
            current.executor_instance_id,
        )

    def _scenario_old_executor_raw_store(self) -> None:
        store, _, first = self._admitted_claim_store()
        raw = store.claim(
            ClaimRequest(first.claim.claim_id, first.claim.executor_instance_id)
        )
        self.assertEqual(raw.outcome, "existing_claim_history")
        self.assertTrue(raw.exact_history)
        self.assertIn("not canonical AIO-049", NONCANONICAL_DISCLAIMER)

    def _scenario_invalid_lease_configuration(self) -> None:
        invalid = (None, True, False, 0, -1, 1.0, "30000000", 30_000_001)
        for value in invalid:
            with self.subTest(value=value):
                configuration = StoreConfiguration(
                    database_path=self.database_path,
                    authorization_domain_id="domain::aio054",
                    ledger_instance_id="ledger::aio054",
                    lease_duration_us=value,
                )
                result = DispatchOutboxClaimLeaseStore.provision_legacy(configuration)
                self.assertEqual(result.outcome, "storage_unavailable")
                self.assertFalse(self.database_path.exists())

    def _scenario_equal_time_tie(self, multiple: bool) -> None:
        orders = (("z", "a", "m"), ("m", "z", "a")) if multiple else (("z", "a"),)
        winners: list[tuple[str, str, str, str]] = []
        for order in orders:
            self._reset_ledger()
            store = self._new_store()
            admissions = self._seed_intents(store, order, equal_time=True)
            expected = min(
                (item.intent.identity for item in admissions),
                key=lambda identity: tuple(part.encode("utf-8") for part in identity.as_tuple()),
            )
            if multiple:
                # Establish a real process-restart boundary, then perform the
                # selection itself from a later fresh spawned process.
                restarted = run_storage_probe(
                    self._probe("open", at=BASE_TIME + timedelta(seconds=1))
                )
                self.assertEqual(restarted.outcome, "opened")
                self.assertEqual(restarted.exit_code, 0)
                selected = run_storage_probe(
                    self._probe(
                        "claim",
                        request=ClaimRequest("claim::tie", "executor::tie"),
                        at=BASE_TIME + timedelta(seconds=1),
                    )
                )
                self.assertNotEqual(restarted.pid, selected.pid)
                self.assertGreater(restarted.pid, 0)
                self.assertGreater(selected.pid, 0)
                self.assertEqual(selected.exit_code, 0)
                self.assertEqual(selected.outcome, "newly_claimed")
                self.assertEqual(selected.clock_sample_count, 1)
                claim_document = selected.payload["claim"]
                expected_document = harness_module._primitive_document(expected)
                self.assertEqual(claim_document["identity"], expected_document)
                self.assertEqual(claim_document["lease_generation"], 1)
                winners.append(
                    tuple(
                        claim_document["identity"][field]
                        for field in (
                            "authorization_domain_id",
                            "issuer_kind",
                            "issuer_id",
                            "grant_id",
                        )
                    )
                )
                self.assertEqual(self._row_count("dispatch_claims"), 1)
                self.assertEqual(self._row_count("dispatch_intents"), len(order))

                committed = run_storage_probe(
                    self._probe("audit_claim", request="claim::tie")
                )
                self.assertEqual(committed.exit_code, 0)
                self.assertEqual(committed.outcome, "audited_claim_history")
                self.assertTrue(committed.payload["exact_history"])
                self.assertEqual(committed.payload["claim"], claim_document)

                for admission in admissions:
                    if admission.intent.identity == expected:
                        continue
                    losing = run_storage_probe(
                        self._probe(
                            "audit_admission",
                            request=admission.intent.identity,
                        )
                    )
                    self.assertEqual(
                        losing.outcome,
                        "audited_admission_history",
                    )
                    self.assertEqual(losing.exit_code, 0)
                    self.assertTrue(losing.payload["exact_history"])
                    self.assertEqual(
                        losing.payload["admission"],
                        harness_module._primitive_document(
                            admission.admission
                        ),
                    )
                    self.assertEqual(
                        losing.payload["intent"],
                        harness_module._primitive_document(
                            admission.intent
                        ),
                    )
            else:
                self.clock.set(BASE_TIME + timedelta(seconds=1))
                claim = store.claim(
                    ClaimRequest("claim::tie", "executor::tie")
                )
                self.assertEqual(claim.outcome, "newly_claimed")
                self.assertEqual(claim.claim.identity, expected)
        if multiple:
            self.assertEqual(len(set(winners)), 1)

    def _scenario_claim_history_only(self) -> None:
        store, _, first = self._admitted_claim_store()
        original = first.claim
        watermark = store.watermark()
        calls = self.clock.calls
        self.clock.fail()
        history = store.claim(
            ClaimRequest(first.claim.claim_id, first.claim.executor_instance_id)
        )
        self.assertEqual(history.outcome, "existing_claim_history")
        self.assertTrue(history.exact_history)
        self.assertEqual(history.claim, original)
        self.assertEqual(history.claim.lease_until_key, original.lease_until_key)
        self.assertIsNone(history.assessment)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_assessment(self, mode: str) -> None:
        store, _, first = self._admitted_claim_store()
        claim = first.claim
        if mode == "active":
            self.clock.set(BASE_TIME + timedelta(seconds=2))
            result = store.assess_current_claim(self._assessment_request(claim))
            self.assertEqual(result.outcome, "active")
            self.assertEqual(result.assessment.status, "active")
            self.assertEqual(store.watermark()[1], result.assessment.observed_at_key)
        elif mode == "inactive":
            self.clock.set(BASE_TIME + timedelta(seconds=31))
            expired = store.assess_current_claim(self._assessment_request(claim))
            self.assertEqual(expired.outcome, "inactive")
            self.assertEqual(expired.assessment.status, "inactive")
            self.assertEqual(expired.assessment.reason, "expired")
            self.assertEqual(expired.assessment.claim, claim)
            self.assertEqual(
                expired.assessment.observed_at_key,
                claim.lease_until_key,
            )
            self.assertTrue(expired.committed)
            self.assertEqual(store.watermark()[1], claim.lease_until_key)
            second = store.claim(ClaimRequest("claim::2", "executor::2"))
            calls = self.clock.calls
            superseded = store.assess_current_claim(self._assessment_request(claim))
            self.assertEqual(superseded.outcome, "inactive")
            self.assertEqual(superseded.assessment.reason, "superseded_generation")
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(second.claim.lease_generation, 2)
        elif mode == "clock_failure":
            watermark = store.watermark()
            for value in (RuntimeError("unavailable"), BASE_TIME - timedelta(days=1)):
                if isinstance(value, BaseException):
                    self.clock.fail(value)
                else:
                    self.clock.set(value)
                result = store.assess_current_claim(self._assessment_request(claim))
                self.assertIn(result.outcome, {"clock_failure", "clock_regression"})
                self.assertIsNone(result.assessment)
                self.assertEqual(store.watermark(), watermark)
        else:
            surrogate = LifecycleSurrogate()
            session = surrogate.acquire()
            executor = create_executor_capability()
            # The raw Claim must use the internally derived ID so coordinator
            # assessment can construct the exact tuple.
            self._reset_ledger()
            store = self._new_store()
            self._admit(store)
            raw_claim = store.claim(ClaimRequest("claim::assessment", executor.executor_instance_id))
            self.clock.set(BASE_TIME + timedelta(seconds=2))
            watermark_before = store.watermark()
            proxy = _LifecycleTransitionStore(store, session, terminal=True)
            coordinator = ExperimentCoordinator(proxy, session=session, executor=executor)
            result = coordinator.assess_current_claim(
                raw_claim.claim.identity,
                raw_claim.claim.claim_id,
                raw_claim.claim.lease_generation,
            )
            proxy.join()
            self.assertEqual(result.outcome, "terminal_fence")
            self.assertIsNone(result.store_result)
            administrative = self._open_store(allow_fenced=True)
            self.assertGreater(administrative.watermark()[1], watermark_before[1])
            self.assertEqual(
                administrative.watermark()[1],
                int((BASE_TIME + timedelta(seconds=2)).timestamp() * 1_000_000),
            )
            audit = administrative.audit_claim(raw_claim.claim.claim_id)
            self.assertEqual(audit.outcome, "audited_claim_history")
            self.assertTrue(audit.exact_history)
            self.assertEqual(audit.claim, raw_claim.claim)
            self.assertIn("non-authoritative", audit.detail)

    # Renewal and sequence scenarios ----------------------------------------------------

    def _scenario_valid_renewal(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        renewed = store.renew(self._renew_request(first.claim))
        self.assertEqual(renewed.outcome, "renewed")
        self.assertEqual(renewed.renewal.renewal_sequence, 1)
        self.assertEqual(
            renewed.renewal.lease_until_key - renewed.renewal.renewed_at_key,
            LEASE_DURATION_US,
        )
        self.assertGreater(
            renewed.renewal.lease_until_key,
            first.claim.lease_until_key,
        )
        self.assertEqual(store.watermark()[1], renewed.renewal.renewed_at_key)

    def _scenario_nonextending_renewal(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=1))
        watermark_before = store.watermark()
        calls_before = self.clock.calls
        request = self._renew_request(first.claim)
        result = store.renew(request)
        self.assertEqual(result.outcome, "nonextending")
        self.assertTrue(result.reevaluation)
        self.assertTrue(result.committed)
        self.assertIsNone(result.renewal)
        self.assertEqual(self.clock.calls, calls_before + 1)
        self.assertEqual(self._row_count("lease_renewals"), 0)
        self.assertEqual(store.audit_renewal("renewal::1").outcome, "not_found")
        self.assertEqual(
            store.watermark(),
            (first.claim.acquired_at, first.claim.acquired_at_key),
        )
        self.assertEqual(store.watermark(), watermark_before)

        self.clock.set(BASE_TIME + timedelta(seconds=2))
        later = store.renew(request)
        self.assertEqual(later.outcome, "renewed")
        self.assertEqual(later.renewal.renewal_sequence, 1)
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _committed_renewal(
        self,
    ) -> tuple[DispatchOutboxClaimLeaseStore, OperationResult, OperationResult]:
        store, _, claim = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        renewal = store.renew(self._renew_request(claim.claim))
        self.assertEqual(renewal.outcome, "renewed")
        return store, claim, renewal

    def _scenario_renewal_history(self, state: str) -> None:
        store, claim_result, renewal_result = self._committed_renewal()
        claim = claim_result.claim
        renewal = renewal_result.renewal
        if state == "expired":
            self.clock.set(BASE_TIME + timedelta(seconds=33))
        elif state == "superseded":
            self.clock.set(BASE_TIME + timedelta(seconds=33))
            second = store.claim(ClaimRequest("claim::2", "executor::2"))
            self.assertEqual(second.outcome, "newly_claimed")
        calls = self.clock.calls
        watermark = store.watermark()
        self.clock.fail()
        history = store.renew(self._renew_request(claim, renewal.renewal_id))
        self.assertEqual(history.outcome, "existing_renewal_history")
        self.assertEqual(history.renewal, renewal)
        self.assertTrue(history.exact_history)
        self.assertIsNone(history.assessment)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_renewal_response_loss(self) -> None:
        store, _, claim_result = self._admitted_claim_store()
        request = self._renew_request(
            claim_result.claim,
            "renewal::response-loss",
        )
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        hook = FaultAt("renewal.after_commit", CommitUnknownFault)
        uncertain_store = self._open_store(fault_hook=hook)

        lost = uncertain_store.renew(request)

        self.assertEqual(hook.reached, 1)
        self.assertEqual(lost.outcome, "commit_unknown")
        self.assertEqual(lost.retry, "retry_exact")
        self.assertIsNone(lost.committed)
        self.assertIsNone(lost.renewal)
        self.assertEqual(self._row_count("lease_renewals"), 1)
        durable = store.audit_renewal(request.renewal_id)
        self.assertEqual(durable.outcome, "audited_renewal_history")
        self.assertIn("non-authoritative", durable.detail)

        calls = self.clock.calls
        watermark = store.watermark()
        self.clock.fail()
        recovered = store.renew(request)
        self.assertEqual(recovered.outcome, "existing_renewal_history")
        self.assertTrue(recovered.exact_history)
        self.assertEqual(recovered.renewal, durable.renewal)
        self.assertIsNone(recovered.assessment)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_renewal_rebound(self) -> None:
        store, claim_result, renewal_result = self._committed_renewal()
        claim = claim_result.claim
        renewal_id = renewal_result.renewal.renewal_id
        changes = (
            {"claim_id": "claim::different"},
            {"lease_generation": claim.lease_generation + 1},
            {"executor_instance_id": "executor::different"},
        )
        for change in changes:
            with self.subTest(change=change):
                rebound = store.renew(self._renew_request(claim, renewal_id, **change))
                self.assertEqual(rebound.outcome, "renewal_identity_conflict")
                self.assertIsNone(rebound.renewal)
        self.assertNotIn("renewal_sequence", inspect.signature(RenewalRequest).parameters)
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_stale_generation_renewal(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=31))
        second = store.claim(ClaimRequest("claim::2", "executor::2"))
        calls = self.clock.calls
        result = store.renew(self._renew_request(first.claim, "renewal::stale"))
        self.assertEqual(result.outcome, "stale_generation")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("lease_renewals"), 0)
        self.assertEqual(second.claim.lease_generation, 2)

    def _scenario_expired_renewal(self) -> None:
        store, _, first = self._admitted_claim_store()
        self.clock.set(BASE_TIME + timedelta(seconds=31))
        result = store.renew(self._renew_request(first.claim))
        self.assertEqual(result.outcome, "expired_claim")
        self.assertTrue(result.reevaluation)
        self.assertIsNone(result.renewal)
        self.assertEqual(store.watermark()[1], first.claim.lease_until_key)

    def _scenario_concurrent_renewals(self) -> None:
        clock = SequenceClock(
            BASE_TIME,
            BASE_TIME + timedelta(seconds=1),
            BASE_TIME + timedelta(seconds=2),
            BASE_TIME + timedelta(seconds=3),
        )
        store = self._new_store(clock=clock)
        admission = store.admit(self._request())
        self.assertEqual(admission.outcome, "newly_admitted")
        claim = store.claim(ClaimRequest("claim::1", "executor::1"))
        self.assertEqual(claim.outcome, "newly_claimed")
        barrier = threading.Barrier(3)
        results: list[OperationResult] = []

        def renew(index: int) -> None:
            barrier.wait()
            results.append(
                store.renew(self._renew_request(claim.claim, f"renewal::{index}"))
            )

        threads = [threading.Thread(target=renew, args=(index,)) for index in (1, 2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(10)
        self.assertEqual([result.outcome for result in results].count("renewed"), 2)
        ordered = sorted((result.renewal for result in results), key=lambda item: item.renewal_sequence)
        self.assertEqual([item.renewal_sequence for item in ordered], [1, 2])
        self.assertLess(ordered[0].lease_until_key, ordered[1].lease_until_key)

    def _scenario_renewal_reclaim_race(self) -> None:
        for renewal_first in (True, False):
            with self.subTest(renewal_first=renewal_first):
                self._reset_ledger()
                store, _, first = self._admitted_claim_store()
                if renewal_first:
                    self.clock.set(BASE_TIME + timedelta(seconds=2))
                    renewal = store.renew(self._renew_request(first.claim))
                    self.assertEqual(renewal.outcome, "renewed")
                    self.clock.set(BASE_TIME + timedelta(seconds=31))
                    reclaim = store.claim(ClaimRequest("claim::2", "executor::2"))
                    self.assertEqual(reclaim.outcome, "temporarily_unavailable")
                else:
                    self.clock.set(BASE_TIME + timedelta(seconds=31))
                    reclaim = store.claim(ClaimRequest("claim::2", "executor::2"))
                    self.assertEqual(reclaim.outcome, "newly_claimed")
                    renewal = store.renew(self._renew_request(first.claim))
                    self.assertEqual(renewal.outcome, "stale_generation")

    def _scenario_renewal_crash(self, fault_point: str) -> None:
        store, _, first = self._admitted_claim_store()
        baseline = store.watermark()
        request = self._renew_request(first.claim, f"renewal::{fault_point}")
        crash = run_storage_probe(
            self._probe(
                "renew",
                request=request,
                at=BASE_TIME + timedelta(seconds=2),
                fault_point=fault_point,
                hard_exit=True,
            )
        )
        self.assertTrue(crash.hard_crash)
        reopened = self._assert_store_reopens()
        self.assertEqual(reopened.audit_renewal(request.renewal_id).outcome, "not_found")
        self.assertEqual(reopened.watermark(), baseline)

    def _scenario_renewal_ambiguous(self) -> None:
        for committed, point, expected in (
            (False, "renewal.before_commit", "renewed"),
            (True, "renewal.after_commit", "existing_renewal_history"),
        ):
            with self.subTest(committed=committed):
                self._reset_ledger()
                store, _, first = self._admitted_claim_store()
                hook = FaultAt(point, CommitUnknownFault)
                uncertain_store = self._open_store(fault_hook=hook)
                request = self._renew_request(first.claim)
                self.clock.set(BASE_TIME + timedelta(seconds=2))
                uncertain = uncertain_store.renew(request)
                self.assertEqual(uncertain.outcome, "commit_unknown")
                retry = store.renew(request)
                self.assertEqual(retry.outcome, expected)
                self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_renewal_chain_corruption(self) -> None:
        variants = (
            "duplicate_id",
            "duplicate_sequence",
            "sequence",
            "binding",
            "timestamp",
            "order",
        )
        for variant in variants:
            with self.subTest(variant=variant):
                self._reset_ledger()
                store, claim_result, renewal_result = self._committed_renewal()
                original = renewal_result.renewal
                if variant == "duplicate_id":
                    self.clock.set(BASE_TIME + timedelta(seconds=33))
                    second_claim = store.claim(
                        ClaimRequest("claim::duplicate-id", "executor::duplicate-id")
                    )
                    self.assertEqual(second_claim.outcome, "newly_claimed")
                    self.clock.set(BASE_TIME + timedelta(seconds=34))
                    second_renewal = store.renew(
                        self._renew_request(
                            second_claim.claim,
                            "renewal::duplicate-id-source",
                        )
                    )
                    self.assertEqual(second_renewal.outcome, "renewed")
                    self.assertEqual(self._row_count("lease_renewals"), 2)
                    self._assert_renewal_unique_constraint_rejects(
                        "UPDATE lease_renewals SET renewal_id=? WHERE renewal_id=?",
                        (
                            original.renewal_id.encode(),
                            second_renewal.renewal.renewal_id.encode(),
                        ),
                        "lease_renewals.renewal_id",
                    )
                    reopened = self._open_store()
                    self.assertEqual(self._row_count("lease_renewals"), 2)
                    self.assertEqual(
                        reopened.audit_renewal(original.renewal_id).renewal,
                        original,
                    )
                    self.assertEqual(
                        reopened.audit_renewal(
                            second_renewal.renewal.renewal_id
                        ).renewal,
                        second_renewal.renewal,
                    )
                    continue
                if variant == "duplicate_sequence":
                    self.clock.set(BASE_TIME + timedelta(seconds=3))
                    second_renewal = store.renew(
                        self._renew_request(
                            claim_result.claim,
                            "renewal::duplicate-sequence-source",
                        )
                    )
                    self.assertEqual(second_renewal.outcome, "renewed")
                    self.assertEqual(second_renewal.renewal.renewal_sequence, 2)
                    self.assertEqual(self._row_count("lease_renewals"), 2)
                    self._assert_renewal_unique_constraint_rejects(
                        "UPDATE lease_renewals SET renewal_sequence=1 "
                        "WHERE renewal_id=?",
                        (second_renewal.renewal.renewal_id.encode(),),
                        "lease_renewals.claim_id",
                        "lease_renewals.renewal_sequence",
                    )
                    reopened = self._open_store()
                    self.assertEqual(self._row_count("lease_renewals"), 2)
                    self.assertEqual(
                        reopened.audit_renewal(original.renewal_id).renewal,
                        original,
                    )
                    self.assertEqual(
                        reopened.audit_renewal(
                            second_renewal.renewal.renewal_id
                        ).renewal,
                        second_renewal.renewal,
                    )
                    continue
                if variant == "sequence":
                    statement = "UPDATE lease_renewals SET renewal_sequence=2"
                elif variant == "binding":
                    statement = "UPDATE lease_renewals SET executor_instance_id=X'78'"
                elif variant == "timestamp":
                    statement = "UPDATE lease_renewals SET lease_until='malformed'"
                else:
                    statement = (
                        "UPDATE lease_renewals "
                        "SET lease_until_key=renewed_at_key + 1"
                    )
                self._drop_mutate_restore_triggers("lease_renewals", statement)
                with self.assertRaises(IntegrityFailure):
                    self._open_store()
                self.assertIsNotNone(original)

    def _scenario_lost_noninserted_renewal(self, expired: bool) -> None:
        store, _, first = self._admitted_claim_store()
        request = self._renew_request(first.claim, "renewal::lost-no-row")
        hook = FaultAt("renewal.after_commit", CommitUnknownFault)
        uncertain_store = self._open_store(fault_hook=hook)
        if expired:
            self.clock.set(BASE_TIME + timedelta(seconds=31))
            first_result = uncertain_store.renew(request)
            self.assertEqual(first_result.outcome, "commit_unknown")
            self.assertTrue(first_result.reevaluation)
            self.assertEqual(first_result.retry, "reevaluate")
            self.assertEqual(hook.reached, 1)
            self.assertEqual(store.audit_renewal(request.renewal_id).outcome, "not_found")
            self.clock.set(BASE_TIME + timedelta(seconds=32))
            second = store.renew(request)
            self.assertEqual(second.outcome, "expired_claim")
            self.assertTrue(second.reevaluation)
            self.assertFalse(second.exact_history)
            self.assertEqual(self._row_count("lease_renewals"), 0)
        else:
            self.clock.set(BASE_TIME + timedelta(seconds=1))
            first_result = uncertain_store.renew(request)
            self.assertEqual(first_result.outcome, "commit_unknown")
            self.assertTrue(first_result.reevaluation)
            self.assertEqual(first_result.retry, "reevaluate")
            self.assertEqual(hook.reached, 1)
            self.assertEqual(store.audit_renewal(request.renewal_id).outcome, "not_found")
            self.clock.set(BASE_TIME + timedelta(seconds=2))
            second = store.renew(request)
            self.assertEqual(second.outcome, "renewed")
            self.assertFalse(second.exact_history)
            self.assertEqual(second.renewal.renewal_id, request.renewal_id)
            self.assertEqual(second.renewal.renewal_sequence, 1)
            self.assertEqual(self._row_count("lease_renewals"), 1)
        self.assertFalse(first_result.exact_history)

    def _scenario_renewal_postcheck(self, terminal: bool) -> None:
        self._reset_ledger()
        store = self._new_store()
        self._admit(store)
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        executor = create_executor_capability()
        claim = store.claim(ClaimRequest("claim::postcheck", executor.executor_instance_id))
        self.assertEqual(claim.outcome, "newly_claimed")
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        proxy = _LifecycleTransitionStore(store, session, terminal=terminal)
        coordinator = ExperimentCoordinator(proxy, session=session, executor=executor)
        result = coordinator.renew(
            claim.claim.identity,
            claim.claim.claim_id,
            claim.claim.lease_generation,
            "renewal::postcheck",
        )
        proxy.join()
        self.assertIsNone(result.store_result)
        audit_store = self._open_store(allow_fenced=terminal)
        audit = audit_store.audit_renewal("renewal::postcheck")
        self.assertEqual(audit.outcome, "audited_renewal_history")
        self.assertTrue(audit.exact_history)
        self.assertIsNotNone(audit.renewal)
        self.assertIn("non-authoritative", audit.detail)
        if terminal:
            self.assertEqual(result.outcome, "terminal_fence")
            retry = coordinator.renew(
                claim.claim.identity,
                claim.claim.claim_id,
                claim.claim.lease_generation,
                "renewal::postcheck",
            )
            self.assertEqual(retry.outcome, "terminal_fence")
            self.assertIsNone(retry.store_result)
            self.assertEqual(self._row_count("lease_renewals"), 1)
        else:
            self.assertEqual(result.outcome, "commit_unknown")
            calls = self.clock.calls
            watermark = store.watermark()
            surrogate.recover_after_loss(timeout=5)
            recovered = ExperimentCoordinator(
                store,
                session=surrogate.acquire(),
                executor=executor,
            ).renew(
                claim.claim.identity,
                claim.claim.claim_id,
                claim.claim.lease_generation,
                "renewal::postcheck",
            )
            self.assertEqual(recovered.outcome, "existing_renewal_history")
            self.assertTrue(recovered.postchecked)
            self.assertEqual(recovered.store_result.renewal, audit.renewal)
            self.assertTrue(recovered.store_result.exact_history)
            self.assertIsNone(recovered.store_result.assessment)
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(store.watermark(), watermark)
            self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_renewal_history_only(self) -> None:
        store, claim_result, renewal_result = self._committed_renewal()
        watermark = store.watermark()
        calls = self.clock.calls
        self.clock.fail()
        history = store.renew(
            self._renew_request(
                claim_result.claim,
                renewal_result.renewal.renewal_id,
            )
        )
        self.assertEqual(history.outcome, "existing_renewal_history")
        self.assertTrue(history.exact_history)
        self.assertEqual(history.renewal, renewal_result.renewal)
        self.assertEqual(
            history.renewal.lease_until_key,
            renewal_result.renewal.lease_until_key,
        )
        self.assertIsNone(history.assessment)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), watermark)
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_renewal_sequence_rollback(self) -> None:
        store, _, first = self._admitted_claim_store()
        for index, second in ((1, 2), (2, 3)):
            self.clock.set(BASE_TIME + timedelta(seconds=second))
            result = store.renew(
                self._renew_request(first.claim, f"renewal::{index}")
            )
            self.assertEqual(result.renewal.renewal_sequence, index)
        self.clock.set(BASE_TIME + timedelta(seconds=4))
        hook = FaultAt("renewal.after_insert")
        failing_store = self._open_store(fault_hook=hook)
        rolled_back = failing_store.renew(
            self._renew_request(first.claim, "renewal::rollback")
        )
        self.assertEqual(rolled_back.outcome, "fault_injected")
        committed = store.renew(self._renew_request(first.claim, "renewal::3"))
        self.assertEqual(committed.outcome, "renewed")
        self.assertEqual(committed.renewal.renewal_sequence, 3)

    def _scenario_renewal_sequence_corruption(self) -> None:
        def replace_persisted_renewal(record: object) -> None:
            identity_values = store_module._identity_bytes(record.identity)
            self._drop_mutate_restore_triggers(
                "lease_renewals",
                """
                UPDATE lease_renewals
                SET claim_id=?,
                    authorization_domain_id=?,
                    issuer_kind=?,
                    issuer_id=?,
                    grant_id=?,
                    executor_instance_id=?,
                    lease_generation=?,
                    renewal_sequence=?,
                    renewed_at=?,
                    renewed_at_key=?,
                    lease_until=?,
                    lease_until_key=?,
                    renewal_payload=?
                WHERE renewal_id=?
                """,
                (
                    store_module._text_bytes(record.claim_id, "claim_id"),
                    *identity_values,
                    store_module._text_bytes(
                        record.executor_instance_id,
                        "executor_instance_id",
                    ),
                    record.lease_generation,
                    record.renewal_sequence,
                    record.renewed_at,
                    record.renewed_at_key,
                    record.lease_until,
                    record.lease_until_key,
                    store_module._renewal_payload(record),
                    store_module._text_bytes(record.renewal_id, "renewal_id"),
                ),
            )

            # Prove each fixture is a canonically encoded Renewal and therefore
            # reaches the effective-chain invariant named by this scenario.
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            try:
                row = connection.execute(
                    "SELECT * FROM lease_renewals WHERE renewal_id=?",
                    (
                        store_module._text_bytes(
                            record.renewal_id,
                            "renewal_id",
                        ),
                    ),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(store_module._renewal_from_row(row), record)
            finally:
                connection.close()

        variants = ("maximum", "gap", "duplicate", "nonpositive", "rebound", "order")
        for variant in variants:
            with self.subTest(variant=variant):
                self._reset_ledger()
                store, claim_result, renewal = self._committed_renewal()
                claim = claim_result.claim
                original = renewal.renewal
                if variant == "maximum":
                    class MaximumSequenceCursor:
                        def fetchone(self) -> tuple[int]:
                            return (MAX_SIGNED_64,)

                    class MaximumSequenceConnection:
                        def __init__(self, connection: sqlite3.Connection) -> None:
                            self._connection = connection

                        def execute(
                            self,
                            statement: str,
                            *arguments: object,
                            **keywords: object,
                        ) -> object:
                            normalized = " ".join(statement.split()).upper()
                            if normalized.startswith(
                                "SELECT MAX(RENEWAL_SEQUENCE) FROM LEASE_RENEWALS"
                            ):
                                return MaximumSequenceCursor()
                            return self._connection.execute(
                                statement,
                                *arguments,
                                **keywords,
                            )

                        def __getattr__(self, name: str) -> object:
                            return getattr(self._connection, name)

                    real_open = store_module.open_profiled_connection

                    def open_with_exhausted_sequence(
                        *arguments: object,
                        **keywords: object,
                    ) -> MaximumSequenceConnection:
                        return MaximumSequenceConnection(
                            real_open(*arguments, **keywords)
                        )

                    before = self._ledger_snapshot()
                    self.clock.set(BASE_TIME + timedelta(seconds=3))
                    with mock.patch.object(
                        store_module,
                        "open_profiled_connection",
                        side_effect=open_with_exhausted_sequence,
                    ):
                        exhausted = store.renew(
                            self._renew_request(
                                renewal.renewal,
                                "renewal::exhausted",
                                claim_id=renewal.renewal.claim_id,
                                executor_instance_id=renewal.renewal.executor_instance_id,
                                lease_generation=renewal.renewal.lease_generation,
                            )
                        )
                    self.assertEqual(exhausted.outcome, "integrity_failure")
                    self.assertIn("Renewal sequence is exhausted", exhausted.detail)
                    self.assertEqual(
                        store.audit_renewal("renewal::exhausted").outcome,
                        "not_found",
                    )
                    self.assertEqual(self._ledger_snapshot(), before)
                    continue
                elif variant == "gap":
                    corrupt = replace(original, renewal_sequence=3)
                    expected_failure = (
                        "Renewal sequence is gapped, duplicate, or nonpositive"
                    )
                elif variant == "nonpositive":
                    # The CHECK constraint itself is a fail-closed mechanism.
                    before = self._ledger_snapshot()
                    with self.assertRaises(sqlite3.IntegrityError):
                        self._drop_mutate_restore_triggers(
                            "lease_renewals",
                            "UPDATE lease_renewals SET renewal_sequence=0",
                        )
                    self.assertEqual(self._ledger_snapshot(), before)
                    self._open_store()
                    continue
                elif variant == "rebound":
                    self.clock.set(BASE_TIME + timedelta(seconds=33))
                    successor = store.claim(
                        ClaimRequest("claim::rebound", "executor::rebound")
                    )
                    self.assertEqual(successor.outcome, "newly_claimed")
                    self.assertEqual(successor.claim.lease_generation, 2)
                    corrupt = replace(
                        original,
                        claim_id=successor.claim.claim_id,
                    )
                    expected_failure = "SQLite foreign_key_check failed"
                elif variant == "order":
                    corrupt = replace(
                        original,
                        renewed_at=claim.acquired_at,
                        renewed_at_key=claim.acquired_at_key,
                        lease_until=claim.lease_until,
                        lease_until_key=claim.lease_until_key,
                    )
                    expected_failure = (
                        "Renewal chain does not strictly extend expiry"
                    )
                else:
                    before = self._ledger_snapshot()
                    duplicate_id = replace(original, renewal_sequence=2)
                    self._assert_renewal_unique_constraint_rejects(
                        """
                        INSERT INTO lease_renewals
                        SELECT renewal_id, claim_id,
                               authorization_domain_id, issuer_kind,
                               issuer_id, grant_id, executor_instance_id,
                               lease_generation, ?, renewed_at, renewed_at_key,
                               lease_until, lease_until_key, ?
                        FROM lease_renewals
                        WHERE renewal_id=?
                        """,
                        (
                            duplicate_id.renewal_sequence,
                            store_module._renewal_payload(duplicate_id),
                            store_module._text_bytes(
                                original.renewal_id,
                                "renewal_id",
                            ),
                        ),
                        "lease_renewals.renewal_id",
                    )
                    duplicate_sequence = replace(
                        original,
                        renewal_id="renewal::duplicate-sequence",
                    )
                    self._assert_renewal_unique_constraint_rejects(
                        """
                        INSERT INTO lease_renewals
                        SELECT ?, claim_id,
                               authorization_domain_id, issuer_kind,
                               issuer_id, grant_id, executor_instance_id,
                               lease_generation, renewal_sequence,
                               renewed_at, renewed_at_key,
                               lease_until, lease_until_key, ?
                        FROM lease_renewals
                        WHERE renewal_id=?
                        """,
                        (
                            store_module._text_bytes(
                                duplicate_sequence.renewal_id,
                                "renewal_id",
                            ),
                            store_module._renewal_payload(duplicate_sequence),
                            store_module._text_bytes(
                                original.renewal_id,
                                "renewal_id",
                            ),
                        ),
                        "lease_renewals.claim_id",
                        "lease_renewals.renewal_sequence",
                    )
                    self.assertEqual(self._ledger_snapshot(), before)
                    self._open_store()
                    continue

                replace_persisted_renewal(corrupt)
                corrupted = self._ledger_snapshot()
                with self.assertRaises(IntegrityFailure) as rejected:
                    self._open_store()
                self.assertEqual(str(rejected.exception), expected_failure)
                self.assertEqual(self._ledger_snapshot(), corrupted)

    # Clock, restart, lifecycle, conflict, and integration-boundary scenarios ---------

    def _scenario_clock_unavailable_or_throwing(self) -> None:
        store = self._new_store()
        baseline = store.watermark()
        for suffix, error in (
            ("unavailable", RuntimeError("trusted source unavailable")),
            ("throwing", OSError("synthetic clock read failure")),
        ):
            with self.subTest(clock=suffix):
                self.clock.fail(error)
                result = store.admit(self._request(suffix))
                self.assertEqual(result.outcome, "clock_failure")
                self.assertEqual(result.retry, "remediate")
                self.assertIsNone(result.admission)
                self.assertEqual(store.watermark(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)

        admission = self._admit(
            store,
            self._request("scenario-53"),
            at=BASE_TIME,
        )
        admission_before = store.audit_admission(admission.intent.identity)
        self.assertEqual(admission_before.outcome, "audited_admission_history")
        claim_watermark = store.watermark()
        claim_request = ClaimRequest("claim::scenario-53", "executor::scenario-53")
        claim_clock_error = OSError("scenario 53 controlled Claim clock failure")
        claim_clock = MutableClock()
        claim_clock.fail(claim_clock_error)

        failed_claim = self._open_store(clock=claim_clock).claim(claim_request)

        self.assertEqual(claim_clock.calls, 1)
        self.assertIs(claim_clock.failure, claim_clock_error)
        self.assertEqual(failed_claim.outcome, "clock_failure")
        self.assertEqual(failed_claim.retry, "remediate")
        self.assertEqual(
            failed_claim.detail,
            f"trusted UTC clock failed closed: {claim_clock_error}",
        )
        self.assertIsNone(failed_claim.claim)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        self.assertEqual(store.audit_claim(claim_request.claim_id).outcome, "not_found")
        self.assertEqual(store.watermark(), claim_watermark)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        admission_after = store.audit_admission(admission.intent.identity)
        self.assertEqual(admission_after.admission, admission_before.admission)
        self.assertEqual(admission_after.intent, admission_before.intent)

        self.clock.set(BASE_TIME + timedelta(seconds=1))
        valid_claim = store.claim(claim_request)
        self.assertEqual(valid_claim.outcome, "newly_claimed")
        self.assertTrue(valid_claim.committed)
        self.assertEqual(valid_claim.claim.identity, admission.intent.identity)
        self.assertEqual(valid_claim.claim.lease_generation, 1)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

        claim_before_renewal = store.audit_claim(valid_claim.claim.claim_id)
        self.assertEqual(claim_before_renewal.outcome, "audited_claim_history")
        effective_expiry_before = (
            claim_before_renewal.claim.lease_until,
            claim_before_renewal.claim.lease_until_key,
        )
        renewal_watermark = store.watermark()
        renewal_request = self._renew_request(
            valid_claim.claim,
            "renewal::scenario-53",
        )
        renewal_clock_error = OSError(
            "scenario 53 controlled Renewal clock failure"
        )
        renewal_clock = MutableClock()
        renewal_clock.fail(renewal_clock_error)

        failed_renewal = self._open_store(clock=renewal_clock).renew(renewal_request)

        self.assertEqual(renewal_clock.calls, 1)
        self.assertIs(renewal_clock.failure, renewal_clock_error)
        self.assertEqual(failed_renewal.outcome, "clock_failure")
        self.assertEqual(failed_renewal.retry, "remediate")
        self.assertEqual(
            failed_renewal.detail,
            f"trusted UTC clock failed closed: {renewal_clock_error}",
        )
        self.assertIsNone(failed_renewal.renewal)
        self.assertEqual(self._row_count("lease_renewals"), 0)
        self.assertEqual(
            store.audit_renewal(renewal_request.renewal_id).outcome,
            "not_found",
        )
        self.assertEqual(store.watermark(), renewal_watermark)
        self.assertEqual(self._row_count("dispatch_claims"), 1)
        claim_after_renewal = store.audit_claim(valid_claim.claim.claim_id)
        self.assertEqual(claim_after_renewal.claim, claim_before_renewal.claim)
        self.assertEqual(
            (
                claim_after_renewal.claim.lease_until,
                claim_after_renewal.claim.lease_until_key,
            ),
            effective_expiry_before,
        )

        self.clock.set(BASE_TIME + timedelta(seconds=2))
        valid_renewal = store.renew(renewal_request)
        self.assertEqual(valid_renewal.outcome, "renewed")
        self.assertTrue(valid_renewal.committed)
        self.assertEqual(valid_renewal.renewal.renewal_sequence, 1)
        self.assertGreater(
            valid_renewal.renewal.lease_until_key,
            effective_expiry_before[1],
        )
        self.assertEqual(self._row_count("lease_renewals"), 1)

    def _scenario_malformed_clock(self) -> None:
        store = self._new_store()
        baseline = store.watermark()
        malformed = (
            BASE_TIME.replace(tzinfo=None),
            BASE_TIME.astimezone(timezone(timedelta(hours=2))),
            "2026-01-01T12:00:00Z",
            1_767_268_800.0,
        )
        for index, value in enumerate(malformed):
            with self.subTest(value=value):
                self.clock.set(value)
                result = store.admit(self._request(f"malformed-{index}"))
                self.assertEqual(result.outcome, "clock_failure")
                self.assertIsNone(result.admission)
                self.assertEqual(store.watermark(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 0)

    def _scenario_clock_regression(self) -> None:
        store = self._new_store()
        admitted = self._admit(store, self._request("watermark"), at=BASE_TIME)
        baseline = store.watermark()
        self.clock.set(BASE_TIME - timedelta(microseconds=1))
        rejected = store.admit(self._request("regressing"))
        self.assertEqual(rejected.outcome, "clock_regression")
        self.assertIsNone(rejected.admission)
        self.assertEqual(store.watermark(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(admitted.admission.decision_time_key, baseline[1])

    def _scenario_watermark_semantics(self) -> None:
        store = self._new_store()
        admission = self._admit(store, at=BASE_TIME)
        admitted_watermark = store.watermark()
        self.assertEqual(
            admitted_watermark,
            (
                admission.admission.decision_time,
                admission.admission.decision_time_key,
            ),
        )
        calls = self.clock.calls
        self.clock.fail()
        exact = store.admit(self._request())
        self.assertEqual(exact.outcome, "existing_exact_admission")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(store.watermark(), admitted_watermark)

        self.clock.set(BASE_TIME + timedelta(seconds=1))
        claimed = store.claim(ClaimRequest("claim::watermark", "executor::1"))
        self.assertEqual(claimed.outcome, "newly_claimed")
        claim_watermark = store.watermark()
        self.assertEqual(
            claim_watermark,
            (claimed.claim.acquired_at, claimed.claim.acquired_at_key),
        )
        self.assertNotEqual(claim_watermark[1], claimed.claim.lease_until_key)
        no_row_now = BASE_TIME + timedelta(seconds=2)
        self.clock.set(no_row_now)
        no_row = store.claim(ClaimRequest("claim::no-row", "executor::2"))
        self.assertEqual(no_row.outcome, "temporarily_unavailable")
        no_row_watermark = store.watermark()
        self.assertEqual(
            no_row_watermark,
            (
                no_row_now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                int(no_row_now.timestamp() * 1_000_000),
            ),
        )
        self.assertNotEqual(no_row_watermark[1], claimed.claim.lease_until_key)
        self.clock.set(BASE_TIME + timedelta(seconds=1))
        regression = store.claim(ClaimRequest("claim::regression", "executor::3"))
        self.assertEqual(regression.outcome, "clock_regression")
        self.assertEqual(self._row_count("dispatch_claims"), 1)
        self.assertEqual(admission.intent.identity, claimed.claim.identity)

    def _scenario_forward_wall_clock_jump(self) -> None:
        store, _, first = self._admitted_claim_store()
        old_history_before = store.audit_claim(first.claim.claim_id)
        self.assertEqual(old_history_before.outcome, "audited_claim_history")

        self.clock.set(BASE_TIME + timedelta(seconds=2))
        initially_active = store.assess_current_claim(
            self._assessment_request(first.claim)
        )
        self.assertEqual(initially_active.outcome, "active")
        self.assertEqual(initially_active.assessment.reason, "unexpired")
        self.assertEqual(
            store.watermark()[1], initially_active.assessment.observed_at_key
        )

        jumped = BASE_TIME + timedelta(hours=12)
        self.clock.set(jumped)
        expired = store.assess_current_claim(self._assessment_request(first.claim))
        self.assertEqual(expired.outcome, "inactive")
        self.assertEqual(expired.assessment.reason, "expired")
        self.assertEqual(
            expired.assessment.effective_lease_until_key,
            first.claim.lease_until_key,
        )
        self.assertEqual(expired.assessment.observed_at_key, int(jumped.timestamp() * 1_000_000))
        jumped_watermark = store.watermark()
        self.assertEqual(jumped_watermark[1], expired.assessment.observed_at_key)

        reclaimed = store.claim(
            ClaimRequest("claim::forward-reclaim", "executor::forward-new")
        )
        self.assertEqual(reclaimed.outcome, "newly_claimed")
        self.assertEqual(
            reclaimed.claim.lease_generation,
            first.claim.lease_generation + 1,
        )
        self.assertEqual(reclaimed.claim.lease_generation, 2)
        self.assertEqual(reclaimed.claim.acquired_at_key, jumped_watermark[1])
        self.assertEqual(
            reclaimed.claim.lease_until_key - reclaimed.claim.acquired_at_key,
            LEASE_DURATION_US,
        )
        self.assertEqual(store.watermark(), jumped_watermark)

        stale_clock_calls = self.clock.calls
        stale_assessment = store.assess_current_claim(
            self._assessment_request(first.claim)
        )
        self.assertEqual(stale_assessment.outcome, "inactive")
        self.assertEqual(stale_assessment.assessment.reason, "superseded_generation")
        self.assertIsNone(stale_assessment.assessment.observed_at)
        self.assertIsNone(stale_assessment.assessment.observed_at_key)
        self.assertEqual(self.clock.calls, stale_clock_calls)
        self.assertEqual(store.watermark(), jumped_watermark)

        stale_renewal = store.renew(
            self._renew_request(first.claim, "renewal::forward-stale")
        )
        self.assertEqual(stale_renewal.outcome, "stale_generation")
        self.assertIsNone(stale_renewal.renewal)
        self.assertEqual(self.clock.calls, stale_clock_calls)
        self.assertEqual(store.watermark(), jumped_watermark)
        self.assertEqual(self._row_count("lease_renewals"), 0)

        stale_history = store.claim(
            ClaimRequest(first.claim.claim_id, first.claim.executor_instance_id)
        )
        self.assertEqual(stale_history.outcome, "existing_claim_history")
        self.assertEqual(stale_history.claim, first.claim)
        self.assertTrue(stale_history.exact_history)
        self.assertIsNone(stale_history.assessment)
        self.assertEqual(self.clock.calls, stale_clock_calls)
        self.assertEqual(store.watermark(), jumped_watermark)

        self.clock.set(jumped + timedelta(seconds=1))
        current = store.assess_current_claim(
            self._assessment_request(reclaimed.claim)
        )
        self.assertEqual(current.outcome, "active")
        self.assertEqual(current.assessment.reason, "unexpired")
        self.assertEqual(current.assessment.claim, reclaimed.claim)
        self.assertEqual(store.watermark()[1], current.assessment.observed_at_key)

        self.clock.set(jumped + timedelta(seconds=2))
        current_renewal = store.renew(
            self._renew_request(reclaimed.claim, "renewal::forward-current")
        )
        self.assertEqual(current_renewal.outcome, "renewed")
        self.assertEqual(current_renewal.renewal.lease_generation, 2)
        self.assertEqual(current_renewal.renewal.renewal_sequence, 1)
        self.assertEqual(
            store.watermark()[1], current_renewal.renewal.renewed_at_key
        )

        old_history_after = store.audit_claim(first.claim.claim_id)
        self.assertEqual(old_history_after.outcome, "audited_claim_history")
        self.assertEqual(old_history_after.claim, old_history_before.claim)
        self.assertEqual(self._row_count("dispatch_claims"), 2)
        self.assertEqual(self._row_count("lease_renewals"), 1)

        watermark = store.watermark()
        self.clock.set(BASE_TIME + timedelta(hours=11))
        regressed = store.claim(ClaimRequest("claim::after-jump", "executor::2"))
        self.assertEqual(regressed.outcome, "clock_regression")
        self.assertEqual(store.watermark(), watermark)

    def _scenario_restart_during_active_lease(self) -> None:
        store, _, first = self._admitted_claim_store()
        contender = run_storage_probe(
            self._probe(
                "claim",
                request=ClaimRequest("claim::restart-contender", "executor::restart"),
                at=BASE_TIME + timedelta(seconds=2),
            )
        )
        self.assertEqual(contender.outcome, "temporarily_unavailable")
        history = run_storage_probe(
            self._probe(
                "claim",
                request=ClaimRequest(
                    first.claim.claim_id,
                    first.claim.executor_instance_id,
                ),
                at=BASE_TIME - timedelta(days=1),
            )
        )
        self.assertEqual(history.outcome, "existing_claim_history")
        self.assertEqual(history.clock_sample_count, 0)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

        expired = run_storage_probe(
            self._probe(
                "claim",
                request=ClaimRequest(
                    "claim::restart-after-expiry",
                    "executor::restart-after-expiry",
                ),
                at=BASE_TIME + timedelta(seconds=31),
            )
        )
        self.assertNotEqual(contender.pid, expired.pid)
        self.assertEqual(expired.outcome, "newly_claimed")
        self.assertEqual(expired.payload["claim"]["lease_generation"], 2)
        self.assertEqual(self._row_count("dispatch_claims"), 2)
        old_history = store.audit_claim(first.claim.claim_id)
        self.assertEqual(old_history.outcome, "audited_claim_history")
        self.assertEqual(old_history.claim, first.claim)
        self.assertIsNotNone(store.connection_profile())

    def _scenario_wal_restart(self) -> None:
        store = self._new_store()
        migration_state = self._metadata()[:3]
        self.assertEqual(
            migration_state,
            (CURRENT_SCHEMA_VERSION, "clean", "active"),
        )
        first = run_storage_probe(self._probe("open"))
        self.assertEqual(first.outcome, "opened")
        request = self._request("wal")
        admitted = run_storage_probe(
            self._probe("admit", request=request, at=BASE_TIME)
        )
        self.assertEqual(admitted.outcome, "newly_admitted")

        claim_request = ClaimRequest("claim::wal", "executor::wal")
        claimed = run_storage_probe(
            self._probe(
                "claim",
                request=claim_request,
                at=BASE_TIME + timedelta(seconds=1),
            )
        )
        self.assertEqual(claimed.outcome, "newly_claimed")
        self.assertEqual(claimed.payload["claim"]["lease_generation"], 1)

        renewal_request = RenewalRequest(
            identity=request.identity,
            claim_id=claim_request.claim_id,
            executor_instance_id=claim_request.executor_instance_id,
            lease_generation=1,
            renewal_id="renewal::wal",
        )
        renewed = run_storage_probe(
            self._probe(
                "renew",
                request=renewal_request,
                at=BASE_TIME + timedelta(seconds=2),
            )
        )
        self.assertEqual(renewed.outcome, "renewed")
        self.assertEqual(renewed.payload["renewal"]["renewal_sequence"], 1)

        reopened = run_storage_probe(
            self._probe("open", at=BASE_TIME + timedelta(seconds=3))
        )
        self.assertEqual(reopened.outcome, "opened")
        self.assertNotEqual(first.pid, reopened.pid)
        self.assertEqual(reopened.payload["profile"]["journal_mode"], "wal")
        self.assertEqual(reopened.payload["profile"]["synchronous"], 2)

        admission_history = run_storage_probe(
            self._probe("audit_admission", request=request.identity)
        )
        claim_history = run_storage_probe(
            self._probe("audit_claim", request=claim_request.claim_id)
        )
        renewal_history = run_storage_probe(
            self._probe("audit_renewal", request=renewal_request.renewal_id)
        )
        self.assertEqual(admission_history.outcome, "audited_admission_history")
        self.assertEqual(claim_history.outcome, "audited_claim_history")
        self.assertEqual(renewal_history.outcome, "audited_renewal_history")
        self.assertEqual(admission_history.payload["intent"], admitted.payload["intent"])
        self.assertEqual(claim_history.payload["claim"], claimed.payload["claim"])
        self.assertEqual(
            renewal_history.payload["renewal"],
            renewed.payload["renewal"],
        )

        self.assertEqual(self._row_count("dispatch_intents"), 1)
        self.assertEqual(self._row_count("dispatch_claims"), 1)
        self.assertEqual(self._row_count("lease_renewals"), 1)

        expected_watermark = (
            renewed.payload["renewal"]["renewed_at"],
            renewed.payload["renewal"]["renewed_at_key"],
        )
        metadata_after_restart = self._metadata()
        self.assertEqual(metadata_after_restart[:3], migration_state)
        self.assertEqual(metadata_after_restart[3:], expected_watermark)
        restarted_store = self._open_store(
            clock=MutableClock(BASE_TIME + timedelta(seconds=3))
        )
        self.assertEqual(restarted_store.watermark(), expected_watermark)
        self.assertEqual(restarted_store.connection_profile().journal_mode, "wal")

    def _scenario_worker_process_restart(self) -> None:
        store = self._new_store()
        self._admit(store)
        request_id = "claim::worker-restart"
        first = run_coordinator_claim_probe(
            CoordinatorClaimProbeSpec(
                configuration=self.configuration,
                claim_id=request_id,
                clock=ProbeClockSpec(value=BASE_TIME + timedelta(seconds=1)),
            )
        )
        self.assertEqual(first.outcome, "newly_claimed")
        self.assertTrue(first.payload["postchecked"])
        self.assertEqual(
            first.payload["store_result"]["claim"]["executor_instance_id"],
            first.executor_instance_id,
        )
        self.assertEqual(
            first.payload["store_result"]["claim"]["lease_generation"],
            1,
        )

        replay = run_coordinator_claim_probe(
            CoordinatorClaimProbeSpec(
                configuration=self.configuration,
                claim_id=request_id,
                clock=ProbeClockSpec(value=BASE_TIME + timedelta(seconds=2)),
            )
        )
        self.assertNotEqual(first.pid, replay.pid)
        self.assertNotEqual(
            first.executor_instance_id,
            replay.executor_instance_id,
        )
        self.assertEqual(replay.outcome, "executor_conflict")
        self.assertTrue(replay.payload["postchecked"])
        self.assertEqual(replay.clock_sample_count, 0)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

        audit = store.audit_claim(request_id)
        self.assertEqual(audit.outcome, "audited_claim_history")
        self.assertTrue(audit.exact_history)
        self.assertEqual(
            audit.claim.executor_instance_id,
            first.executor_instance_id,
        )
        self.assertIsNone(audit.assessment)
        self.assertIn("non-authoritative", audit.detail)

        reclaimed = run_coordinator_claim_probe(
            CoordinatorClaimProbeSpec(
                configuration=self.configuration,
                claim_id="claim::new-process",
                clock=ProbeClockSpec(value=BASE_TIME + timedelta(seconds=31)),
            )
        )
        self.assertEqual(reclaimed.outcome, "newly_claimed")
        self.assertTrue(reclaimed.payload["postchecked"])
        self.assertEqual(
            reclaimed.payload["store_result"]["claim"]["lease_generation"],
            2,
        )
        self.assertNotIn(
            reclaimed.executor_instance_id,
            {first.executor_instance_id, replay.executor_instance_id},
        )
        self.assertEqual(self._row_count("dispatch_claims"), 2)

    def _scenario_repeated_reclaim(self) -> None:
        store = self._new_store()
        self._admit(store, at=BASE_TIME)
        claims = []
        for generation, second in enumerate((1, 31, 61, 91), start=1):
            self.clock.set(BASE_TIME + timedelta(seconds=second))
            result = store.claim(
                ClaimRequest(f"claim::generation-{generation}", f"executor::{generation}")
            )
            self.assertEqual(result.outcome, "newly_claimed")
            self.assertEqual(result.claim.lease_generation, generation)
            claims.append(result.claim)
        self.assertEqual(self._row_count("dispatch_claims"), 4)
        self.assertEqual(
            [claim.lease_generation for claim in claims],
            [1, 2, 3, 4],
        )

    def _scenario_generation_corruption(self) -> None:
        variants = ("malformed", "gap", "rebound", "exhausted")
        for variant in variants:
            with self.subTest(variant=variant):
                self._reset_ledger()
                store, _, first = self._admitted_claim_store()
                if variant == "malformed":
                    with self.assertRaises(sqlite3.IntegrityError):
                        self._drop_mutate_restore_triggers(
                            "dispatch_claims",
                            "UPDATE dispatch_claims SET lease_generation=0",
                        )
                    self.assertEqual(
                        store.audit_claim(first.claim.claim_id).outcome,
                        "audited_claim_history",
                    )
                    continue
                if variant == "exhausted":
                    request = ClaimRequest(
                        "claim::generation-exhausted",
                        "executor::generation-exhausted",
                    )
                    self.clock.set(BASE_TIME + timedelta(seconds=31))
                    watermark = store.watermark()
                    calls = self.clock.calls
                    before = self._ledger_snapshot()
                    history_before = store.audit_claim(first.claim.claim_id)
                    self.assertEqual(history_before.outcome, "audited_claim_history")
                    self.assertEqual(history_before.claim, first.claim)
                    self.assertEqual(first.claim.lease_generation, 1)
                    self.assertEqual(self._row_count("lease_renewals"), 0)

                    real_highest_claim = store._highest_claim

                    def highest_at_limit(
                        connection: sqlite3.Connection,
                        identity: object,
                    ) -> object:
                        prior = real_highest_claim(connection, identity)
                        self.assertEqual(prior, first.claim)
                        return replace(
                            prior,
                            lease_generation=MAX_SIGNED_64,
                        )

                    with mock.patch.object(
                        store,
                        "_highest_claim",
                        side_effect=highest_at_limit,
                    ) as highest:
                        exhausted = store.claim(request)

                    self.assertEqual(highest.call_count, 1)
                    self.assertEqual(exhausted.outcome, "integrity_failure")
                    self.assertEqual(exhausted.detail, "Lease generation is exhausted")
                    self.assertEqual(exhausted.retry, "remediate")
                    self.assertIsNone(exhausted.committed)
                    self.assertIsNone(exhausted.claim)
                    self.assertEqual(self.clock.calls, calls + 1)
                    self.assertEqual(store.watermark(), watermark)
                    self.assertEqual(self._ledger_snapshot(), before)
                    self.assertEqual(self._row_count("dispatch_claims"), 1)
                    self.assertEqual(store.audit_claim(request.claim_id).outcome, "not_found")
                    history_after = store.audit_claim(first.claim.claim_id)
                    self.assertEqual(history_after.outcome, "audited_claim_history")
                    self.assertEqual(history_after.claim, history_before.claim)
                    self.assertTrue(history_after.exact_history)

                    later = store.claim(request)
                    self.assertEqual(later.outcome, "newly_claimed")
                    self.assertTrue(later.committed)
                    self.assertEqual(later.claim.claim_id, request.claim_id)
                    self.assertEqual(
                        later.claim.executor_instance_id,
                        request.executor_instance_id,
                    )
                    self.assertEqual(later.claim.identity, first.claim.identity)
                    self.assertEqual(later.claim.lease_generation, 2)
                    self.assertEqual(self._row_count("dispatch_claims"), 2)
                    self.assertEqual(store.watermark()[1], later.claim.acquired_at_key)
                    original = store.audit_claim(first.claim.claim_id)
                    self.assertEqual(original.outcome, "audited_claim_history")
                    self.assertEqual(original.claim, first.claim)
                    self.assertTrue(original.exact_history)
                    continue
                if variant == "gap":
                    statement = "UPDATE dispatch_claims SET lease_generation=2"
                elif variant == "rebound":
                    statement = "UPDATE dispatch_claims SET executor_instance_id=X'78'"
                self._drop_mutate_restore_triggers("dispatch_claims", statement)
                with self.assertRaises(IntegrityFailure):
                    self._open_store()

    def _scenario_complete_lifecycle_guard(self) -> None:
        store = self._new_store()
        surrogate, session, capability, coordinator = self._coordinator(store)
        for value in (capability, surrogate, session):
            with self.subTest(value=type(value).__name__, operation="copy"):
                with self.assertRaises(TypeError):
                    copy.copy(value)
            with self.subTest(value=type(value).__name__, operation="pickle"):
                with self.assertRaises(TypeError):
                    pickle.dumps(value)

        admission = coordinator.admit(self._request("guarded"))
        self.assertEqual(admission.outcome, "newly_admitted")
        self.assertTrue(admission.postchecked)
        claim = coordinator.claim("claim::guarded")
        self.assertEqual(claim.outcome, "newly_claimed")
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        renewal = coordinator.renew(
            claim.store_result.claim.identity,
            claim.store_result.claim.claim_id,
            claim.store_result.claim.lease_generation,
            "renewal::guarded",
        )
        self.assertEqual(renewal.outcome, "renewed")
        self.clock.set(BASE_TIME + timedelta(seconds=3))
        assessment = coordinator.assess_current_claim(
            claim.store_result.claim.identity,
            claim.store_result.claim.claim_id,
            claim.store_result.claim.lease_generation,
        )
        self.assertEqual(assessment.outcome, "active")
        self.assertTrue(all(item.postchecked for item in (admission, claim, renewal, assessment)))
        session.release(timeout=5)
        self.assertEqual(surrogate.state, LifecycleState.RELEASED)
        stale = coordinator.claim("claim::stale-session")
        self.assertEqual(stale.outcome, "lifecycle_unavailable")
        self.assertIsNone(stale.store_result)

    def _scenario_domain_fenced_before_claim(self) -> None:
        store = self._new_store()
        admission = self._admit(store)
        history_before = store.audit_admission(admission.intent.identity)
        self.assertEqual(history_before.outcome, "audited_admission_history")
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        fenced = store.fence()
        self.assertEqual(fenced.outcome, "fenced")
        rejected = store.claim(ClaimRequest("claim::fenced", "executor::1"))
        self.assertEqual(rejected.outcome, "incompatible_schema")
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        with self.assertRaises(IncompatibleSchemaError):
            self._open_store()
        administrative = self._open_store(allow_fenced=True)
        self.assertEqual(administrative.audit_claim("claim::fenced").outcome, "not_found")
        history_after = administrative.audit_admission(admission.intent.identity)
        self.assertEqual(history_after.outcome, "audited_admission_history")
        self.assertEqual(history_after.admission, history_before.admission)
        self.assertEqual(history_after.intent, history_before.intent)
        self.assertTrue(history_after.exact_history)
        self.assertIn("non-authoritative", history_after.detail)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        self.assertEqual(administrative.fence().outcome, "already_fenced")

    def _scenario_fencing_race(self) -> None:
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        guards = (session.operation(), session.operation())
        for guard in guards:
            guard.__enter__()
        self.assertEqual(surrogate.active_operation_count, 2)
        completed = threading.Event()
        errors: list[BaseException] = []

        def fence() -> None:
            try:
                session.fence(timeout=5)
                completed.set()
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=fence)
        thread.start()
        deadline = time.monotonic() + 5
        while surrogate.state is not LifecycleState.FENCING:
            self.assertLess(time.monotonic(), deadline)
            time.sleep(0.001)
        with self.assertRaises(LifecycleError):
            session.operation().__enter__()
        for index, guard in enumerate(guards, start=1):
            with self.assertRaises(LifecycleError):
                guard.complete(f"candidate::{index}")
            if index == 1:
                self.assertFalse(completed.is_set())
                self.assertEqual(surrogate.active_operation_count, 1)
        thread.join(5)
        self.assertFalse(errors)
        self.assertTrue(completed.is_set())
        self.assertEqual(surrogate.state, LifecycleState.FENCED)

        # The lifecycle surrogate deliberately does not serialize Store
        # writers.  Exercise the separate raw-SQLite lane so this scenario
        # proves that concurrent writes are ordered by BEGIN IMMEDIATE.
        self._reset_ledger()
        store = self._new_store()
        self._admit(store, at=BASE_TIME)
        results = race_storage_probes(
            (
                self._probe(
                    "claim",
                    request=ClaimRequest("claim::fence-race-a", "executor::a"),
                    at=BASE_TIME + timedelta(seconds=1),
                ),
                self._probe(
                    "claim",
                    request=ClaimRequest("claim::fence-race-b", "executor::b"),
                    at=BASE_TIME + timedelta(seconds=1),
                ),
            )
        )
        self.assertCountEqual(
            [result.outcome for result in results],
            ["newly_claimed", "temporarily_unavailable"],
        )
        self.assertTrue(
            all(
                result.evidence_scope == "raw_sqlite_storage_mechanism_only"
                for result in results
            )
        )
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_post_admission_revocation(self) -> None:
        store = self._new_store()
        request = self._request("revoked")
        admission = self._admit(store, request, at=BASE_TIME)
        self.clock.set(BASE_TIME + timedelta(seconds=1))
        revoked = store.revoke(request)
        self.assertEqual(revoked.outcome, "newly_revoked")
        exact = store.admit(request)
        self.assertEqual(exact.outcome, "existing_exact_admission")
        claim = store.claim(ClaimRequest("claim::revoked", "executor::1"))
        self.assertEqual(claim.outcome, "authority_ineligible")
        self.assertIsNone(claim.claim)
        self.assertEqual(self._row_count("experiment_revocations"), 1)
        self.assertEqual(admission.admission.identity, exact.admission.identity)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        audited = store.audit_admission(request.identity)
        self.assertEqual(audited.admission, admission.admission)
        self.assertEqual(audited.intent, admission.intent)

        # If Claim wins the writer order, revocation must preserve that
        # immutable history while blocking every modeled later authority path.
        self._reset_ledger()
        store = self._new_store()
        request = self._request("revoked-after-claim")
        admission = self._admit(store, request, at=BASE_TIME)
        claimed = self._claim(store, at=BASE_TIME + timedelta(seconds=1))
        self.clock.set(BASE_TIME + timedelta(seconds=2))
        self.assertEqual(store.revoke(request).outcome, "newly_revoked")
        calls = self.clock.calls
        renewal = store.renew(
            self._renew_request(claimed.claim, "renewal::after-revocation")
        )
        assessment = store.assess_current_claim(
            self._assessment_request(claimed.claim)
        )
        self.assertEqual(renewal.outcome, "revoked")
        self.assertEqual(assessment.outcome, "revoked")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("lease_renewals"), 0)
        self.assertEqual(
            store.audit_claim(claimed.claim.claim_id).claim,
            claimed.claim,
        )
        audited = store.audit_admission(request.identity)
        self.assertEqual(audited.admission, admission.admission)
        self.assertEqual(audited.intent, admission.intent)

        # Incomplete revocation evidence after Admission is independently
        # ordered before Claim time work and likewise cannot rewrite history.
        self._reset_ledger()
        store = self._new_store()
        request = self._request("revocation-incomplete-after-admission")
        admission = self._admit(store, request, at=BASE_TIME)
        self._drop_mutate_restore_triggers(
            "experiment_metadata",
            "UPDATE experiment_metadata SET revocation_state_complete=0",
        )
        reopened = self._open_store()
        calls = self.clock.calls
        rejected = reopened.claim(
            ClaimRequest("claim::revocation-incomplete", "executor::1")
        )
        self.assertEqual(rejected.outcome, "authority_ineligible")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        audited = reopened.audit_admission(request.identity)
        self.assertEqual(audited.admission, admission.admission)
        self.assertEqual(audited.intent, admission.intent)

    def _scenario_wrong_admission_identity(self) -> None:
        store = self._new_store()
        admission = self._admit(store, self._request("wrong-stored-identity"))
        baseline = self._metadata()
        calls = self.clock.calls
        wrong_component = b"issuer::controlled-wrong-admission"
        self._drop_mutate_restore_triggers(
            "dispatch_intents",
            "UPDATE dispatch_intents SET issuer_id=?",
            (wrong_component,),
        )
        corrupted = self._ledger_snapshot()
        result = store.claim(ClaimRequest("claim::wrong-admission", "executor::1"))
        self.assertEqual(result.outcome, "integrity_failure")
        self.assertEqual(result.retry, "remediate")
        self.assertIsNone(result.claim)
        self.assertNotIn(wrong_component.decode(), result.detail)
        self.assertNotIn(admission.admission.identity.issuer_id, result.detail)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._metadata(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        self.assertEqual(self._ledger_snapshot(), corrupted)

    def _scenario_index_payload_corruption(self) -> None:
        variants = (
            ("admission_run", "experiment_admissions", "UPDATE experiment_admissions SET run_id=X'78'"),
            ("intent_run", "dispatch_intents", "UPDATE dispatch_intents SET run_id=X'78'"),
            ("admission_payload", "experiment_admissions", "UPDATE experiment_admissions SET admission_payload=X'7b7d'"),
        )
        for name, table, statement in variants:
            with self.subTest(variant=name):
                self._reset_ledger()
                store = self._new_store()
                self._admit(store)
                self._drop_mutate_restore_triggers(table, statement)
                connection = sqlite3.connect(self.database_path)
                try:
                    corrupted_rows = tuple(
                        connection.execute(
                            f'SELECT * FROM "{table}"'
                        ).fetchall()
                    )
                finally:
                    connection.close()
                metadata = self._metadata()
                calls = self.clock.calls
                result = store.claim(
                    ClaimRequest(f"claim::corrupt::{name}", "executor::corrupt")
                )
                self.assertEqual(result.outcome, "integrity_failure")
                self.assertEqual(result.retry, "remediate")
                self.assertIsNone(result.claim)
                self.assertEqual(self.clock.calls, calls)
                self.assertEqual(self._metadata(), metadata)
                self.assertEqual(self._row_count("dispatch_claims"), 0)
                connection = sqlite3.connect(self.database_path)
                try:
                    self.assertEqual(
                        tuple(
                            connection.execute(
                                f'SELECT * FROM "{table}"'
                            ).fetchall()
                        ),
                        corrupted_rows,
                    )
                finally:
                    connection.close()
                with self.assertRaises(IntegrityFailure):
                    self._open_store()

    def _scenario_binding_substitution(self, label: str) -> None:
        store = self._new_store()
        fields = {
            "actor": "actor::pinned",
            "operation": "operation::pinned",
            "resource": "resource::pinned",
            "runtime": "runtime::pinned",
            "tool": "tool::pinned",
            "binding": "binding::pinned",
        }

        def encoded_binding(values: dict[str, str]) -> bytes:
            return "\n".join(
                f"{key}={values[key]}" for key in sorted(values)
            ).encode("utf-8")

        suffix = f"substitution-{label}"
        request = self._request(
            suffix,
            binding_payload=encoded_binding(fields),
        )
        original = self._admit(store, request)
        substitutions = {
            "tool": (("tool", "tool::substituted"),),
            "runtime": (("runtime", "runtime::substituted"),),
            "actor-operation-resource": (
                ("actor", "actor::widened"),
                ("operation", "operation::widened"),
                ("resource", "resource::widened"),
            ),
            "binding": (("binding", "binding::different"),),
        }[label]
        calls = self.clock.calls
        for field, replacement in substitutions:
            with self.subTest(substitution=field):
                changed = dict(fields)
                changed[field] = replacement
                substituted = self._request(
                    suffix,
                    binding_payload=encoded_binding(changed),
                )
                self.assertEqual(substituted.identity, request.identity)
                self.assertEqual(substituted.run_id, request.run_id)
                self.assertEqual(substituted.grant_payload, request.grant_payload)
                result = store.admit(substituted)
                self.assertEqual(result.outcome, "binding_conflict")
                self.assertEqual(result.retry, "do_not_retry")
                self.assertIsNone(result.admission)
                self.assertIsNone(result.intent)
        self.assertEqual(self.clock.calls, calls)
        audit = store.audit_admission(request.identity)
        self.assertTrue(audit.exact_history)
        self.assertEqual(audit.admission, original.admission)
        self.assertEqual(audit.intent, original.intent)
        self.assertEqual(audit.admission.run_id, request.run_id)
        self.assertEqual(
            audit.admission.binding_payload,
            encoded_binding(fields),
        )
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_corrupt_or_newer_schema(self) -> None:
        def logical_snapshot() -> tuple[object, ...]:
            connection = sqlite3.connect(self.database_path)
            try:
                return (
                    int(connection.execute("PRAGMA application_id").fetchone()[0]),
                    int(connection.execute("PRAGMA user_version").fetchone()[0]),
                    tuple(connection.iterdump()),
                )
            finally:
                connection.close()

        for variant in ("corrupt", "newer"):
            with self.subTest(variant=variant):
                self._reset_ledger()
                self._new_store()
                if variant == "corrupt":
                    self._corrupt_schema("unexpected_schema_object")
                    expected = IntegrityFailure
                else:
                    connection = sqlite3.connect(self.database_path)
                    try:
                        connection.execute("PRAGMA user_version=999")
                        connection.commit()
                    finally:
                        connection.close()
                    expected = IncompatibleSchemaError
                before = logical_snapshot()
                with self.assertRaises(expected):
                    self._open_store()
                self.assertEqual(logical_snapshot(), before)
                if variant == "corrupt":
                    self.assertTrue(
                        any("unexpected_schema_object" in line for line in before[2])
                    )
                else:
                    self.assertEqual(before[1], 999)

    def _scenario_connection_profile_pressure(self) -> None:
        store = self._new_store()
        self._admit(store)
        self.assertEqual(
            store.connection_profile().busy_timeout_ms,
            BUSY_TIMEOUT_MS,
        )
        baseline = store.watermark()
        request = ClaimRequest("claim::busy", "executor::busy")
        contender, holder = run_held_writer_probe(
            self.configuration,
            self._probe(
                "claim",
                request=request,
                at=BASE_TIME + timedelta(seconds=1),
            ),
        )
        self.assertEqual(contender.outcome, "storage_busy")
        self.assertEqual(contender.evidence_scope, "raw_sqlite_storage_mechanism_only")
        self.assertEqual(contender.payload["retry"], "retry_exact")
        self.assertIsNone(contender.payload["claim"])
        self.assertIsNone(contender.payload["committed"])
        self.assertGreaterEqual(contender.elapsed_seconds, 0.5)
        self.assertLessEqual(contender.elapsed_seconds, 15.0)
        self.assertEqual(self._row_count("dispatch_claims"), 0)
        self.assertEqual(store.watermark(), baseline)
        self.assertEqual(store.audit_claim(request.claim_id).outcome, "not_found")
        self.assertIsNotNone(holder)
        self.assertEqual(holder["outcome"], "writer_released")
        self.assertEqual(holder["scope"], "raw_sqlite_storage_mechanism_only")

        # The busy attempt neither fell back nor consumed its Claim ID.
        self.clock.set(BASE_TIME + timedelta(seconds=1))
        retry = store.claim(request)
        self.assertEqual(retry.outcome, "newly_claimed")
        self.assertEqual(retry.claim.claim_id, request.claim_id)
        self.assertEqual(self._row_count("dispatch_claims"), 1)

    def _scenario_negative_execution_boundary(self) -> None:
        self.assertIs(inspect.getmodule(DispatchOutboxClaimLeaseStore), store_module)
        self.assertIs(inspect.getmodule(ExperimentCoordinator), harness_module)
        self.assertTrue(store_module.__name__.startswith("experiments."))
        self.assertTrue(harness_module.__name__.startswith("experiments."))
        public = set(store_module.__all__) | set(harness_module.__all__)
        forbidden = {
            "dispatch",
            "invoke",
            "invoke_agent",
            "execute_agent",
            "publish",
            "send",
            "transport",
            "load_repository",
        }
        self.assertTrue(public.isdisjoint(forbidden))
        self.assertNotIn("tool", inspect.signature(DispatchOutboxClaimLeaseStore.claim).parameters)
        self.assertNotIn("runtime", inspect.signature(ExperimentCoordinator.claim).parameters)
        self.assertIn("not canonical AIO-049", NONCANONICAL_DISCLAIMER)

        # Build a bounded local call/reference closure across only the two
        # exact experiment modules.  This follows module-level helpers used by
        # the Store/coordinator instead of checking only their class bodies.
        modules = {
            store_module.__name__: store_module,
            harness_module.__name__: harness_module,
        }
        trees = {
            name: ast.parse(inspect.getsource(module))
            for name, module in modules.items()
        }
        definitions: dict[tuple[str, str], ast.AST] = {}
        import_aliases: dict[str, dict[str, tuple[str, str | None]]] = {}
        for module_name, tree in trees.items():
            aliases: dict[str, tuple[str, str | None]] = {}
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    definitions[(module_name, node.name)] = node
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        aliases[alias.asname or alias.name.split(".")[0]] = (
                            alias.name,
                            None,
                        )
                elif isinstance(node, ast.ImportFrom) and node.module is not None:
                    for alias in node.names:
                        aliases[alias.asname or alias.name] = (
                            node.module,
                            alias.name,
                        )
            import_aliases[module_name] = aliases

        roots = {
            (store_module.__name__, DispatchOutboxClaimLeaseStore.__name__),
            (harness_module.__name__, ExperimentCoordinator.__name__),
        }
        reachable = set(roots)
        pending = list(roots)
        while pending:
            key = pending.pop()
            module_name, _ = key
            node = definitions[key]
            candidates: set[tuple[str, str]] = set()
            for descendant in ast.walk(node):
                if isinstance(descendant, ast.Name):
                    local = (module_name, descendant.id)
                    if local in definitions:
                        candidates.add(local)
                    imported = import_aliases[module_name].get(descendant.id)
                    if imported is not None:
                        imported_module, imported_name = imported
                        imported_key = (imported_module, imported_name or "")
                        if imported_key in definitions:
                            candidates.add(imported_key)
                elif isinstance(descendant, ast.Attribute) and isinstance(
                    descendant.value, ast.Name
                ):
                    imported = import_aliases[module_name].get(descendant.value.id)
                    if imported is not None and imported[1] is None:
                        imported_key = (imported[0], descendant.attr)
                        if imported_key in definitions:
                            candidates.add(imported_key)
                elif isinstance(descendant, ast.ImportFrom):
                    if descendant.module in modules:
                        for alias in descendant.names:
                            imported_key = (descendant.module, alias.name)
                            if imported_key in definitions:
                                candidates.add(imported_key)
            for candidate in candidates - reachable:
                reachable.add(candidate)
                pending.append(candidate)

        self.assertIn(
            (store_module.__name__, "open_profiled_connection"),
            reachable,
        )
        self.assertIn(
            (store_module.__name__, "_validate_configuration"),
            reachable,
        )
        self.assertIn(
            (harness_module.__name__, "_store_request_types"),
            reachable,
        )
        excluded_harness_lanes = {
            key
            for key in definitions
            if key[0] == harness_module.__name__
            and any(
                fragment in key[1].lower()
                for fragment in ("probe", "t3", "writer")
            )
        }
        self.assertTrue(excluded_harness_lanes)
        self.assertTrue(reachable.isdisjoint(excluded_harness_lanes))

        reachable_identifiers: set[str] = set()
        reachable_calls: set[str] = set()
        reachable_imports: set[str] = set()
        for module_name, definition_name in reachable:
            node = definitions[(module_name, definition_name)]
            reachable_identifiers.add(definition_name)
            for descendant in ast.walk(node):
                if isinstance(
                    descendant,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    reachable_identifiers.add(descendant.name)
                elif isinstance(descendant, ast.Name):
                    reachable_identifiers.add(descendant.id)
                    imported = import_aliases[module_name].get(descendant.id)
                    if imported is not None:
                        reachable_imports.add(imported[0])
                elif isinstance(descendant, ast.Attribute):
                    reachable_identifiers.add(descendant.attr)
                elif isinstance(descendant, ast.Call):
                    if isinstance(descendant.func, ast.Name):
                        reachable_calls.add(descendant.func.id)
                    elif isinstance(descendant.func, ast.Attribute):
                        reachable_calls.add(descendant.func.attr)
                elif isinstance(descendant, ast.Import):
                    reachable_imports.update(alias.name for alias in descendant.names)
                elif isinstance(descendant, ast.ImportFrom):
                    if descendant.module is not None:
                        reachable_imports.add(descendant.module)

        forbidden_import_prefixes = (
            "aiohttp",
            "boto",
            "botocore",
            "ftplib",
            "grpc",
            "http",
            "httpx",
            "multiprocessing",
            "paramiko",
            "requests",
            "smtplib",
            "socket",
            "subprocess",
            "urllib",
            "websockets",
        )
        self.assertEqual(
            sorted(
                imported
                for imported in reachable_imports
                if imported in forbidden_import_prefixes
                or imported.startswith(
                    tuple(prefix + "." for prefix in forbidden_import_prefixes)
                )
            ),
            [],
        )
        forbidden_fragments = (
            "availability_probe",
            "credential",
            "dispatch_transport",
            "probe_availability",
            "repository_file",
            "result_attachment",
            "result_persistence",
            "transport_dispatch",
        )
        forbidden_exact = {
            "__import__",
            "attach_result",
            "execute_agent",
            "import_module",
            "invoke_agent",
            "invoke_tool",
            "load_credentials",
            "load_repository",
            "persist_result",
            "probe_availability",
            "publish",
            "read_bytes",
            "read_text",
            "result_store",
            "send_dispatch",
            "write_bytes",
            "write_text",
        }
        forbidden_reachable = sorted(
            identifier
            for identifier in reachable_identifiers | reachable_calls
            if identifier in forbidden_exact
            or any(fragment in identifier.lower() for fragment in forbidden_fragments)
        )
        self.assertEqual(forbidden_reachable, [])

        declared_faults = {
            point
            for points in STORAGE_FAULT_POINTS_BY_OPERATION.values()
            for point in points
        }
        self.assertEqual(declared_faults, set(SUPPORTED_STORAGE_FAULT_POINTS))
        with mock.patch.object(
            store_module,
            "open_profiled_connection",
            wraps=open_profiled_connection,
        ) as opened:
            store = self._new_store()
            self._admit(store)
            self.assertTrue(opened.called)

    def _scenario_concurrent_identical_admissions(self) -> None:
        store = self._new_store()
        request = self._request("concurrent")
        results = race_storage_probes(
            (
                self._probe("admit", request=request, at=BASE_TIME),
                self._probe("admit", request=request, at=BASE_TIME),
            )
        )
        self.assertCountEqual(
            [result.outcome for result in results],
            ["newly_admitted", "existing_exact_admission"],
        )
        winner = next(
            result for result in results if result.outcome == "newly_admitted"
        )
        loser = next(
            result
            for result in results
            if result.outcome == "existing_exact_admission"
        )
        self.assertNotEqual(winner.pid, loser.pid)
        self.assertIsInstance(winner.payload, dict)
        self.assertIsInstance(loser.payload, dict)
        self.assertEqual(winner.payload["admission"], loser.payload["admission"])
        self.assertEqual(winner.payload["intent"], loser.payload["intent"])
        self.assertTrue(loser.payload["exact_history"])
        audited = store.audit_admission(request.identity)
        self.assertTrue(audited.exact_history)
        self.assertEqual(audited.admission.identity, request.identity)
        self.assertEqual(audited.admission.run_id, request.run_id)
        self.assertEqual(audited.admission.grant_payload, request.grant_payload)
        self.assertEqual(audited.admission.binding_payload, request.binding_payload)
        self.assertEqual(audited.intent.identity, request.identity)
        self.assertEqual(audited.intent.run_id, request.run_id)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_different_grant_same_run(self) -> None:
        store = self._new_store()
        original = self._request("original")
        admitted = self._admit(store, original)
        conflicting = self._request("different", run_id=original.run_id)
        calls = self.clock.calls
        result = store.admit(conflicting)
        self.assertEqual(result.outcome, "run_conflict")
        self.assertEqual(result.retry, "do_not_retry")
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        self.assertEqual(
            store.audit_admission(conflicting.identity).outcome,
            "not_found",
        )
        original_audit = store.audit_admission(original.identity)
        self.assertEqual(original_audit.admission, admitted.admission)
        self.assertEqual(original_audit.intent, admitted.intent)
        connection = sqlite3.connect(self.database_path)
        try:
            orphan_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*)
                    FROM dispatch_intents AS i
                    LEFT JOIN experiment_admissions AS a
                      ON a.authorization_domain_id=i.authorization_domain_id
                     AND a.issuer_kind=i.issuer_kind
                     AND a.issuer_id=i.issuer_id
                     AND a.grant_id=i.grant_id
                    WHERE a.authorization_domain_id IS NULL
                    """
                ).fetchone()[0]
            )
        finally:
            connection.close()
        self.assertEqual(orphan_count, 0)

    def _scenario_temporal_admission(self, mode: str) -> None:
        store = self._new_store()
        if mode == "not_yet":
            request = self._request(
                "future",
                issued_at=BASE_TIME + timedelta(seconds=1),
                expires_at=BASE_TIME + timedelta(hours=1),
            )
            expected = "not_yet_current"
        else:
            request = self._request(
                "expired",
                issued_at=BASE_TIME - timedelta(hours=1),
                expires_at=BASE_TIME,
            )
            expected = "expired"
        baseline = store.watermark()
        result = store.admit(request)
        self.assertEqual(result.outcome, expected)
        self.assertTrue(result.committed)
        self.assertIsNone(result.admission)
        self.assertNotEqual(store.watermark(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)

    def _scenario_pre_revoked_grant(self) -> None:
        store = self._new_store()
        request = self._request("pre-revoked")
        revoked = store.revoke(request)
        self.assertEqual(revoked.outcome, "newly_revoked")
        result = store.admit(request)
        self.assertEqual(result.outcome, "revoked")
        self.assertEqual(result.retry, "do_not_retry")
        self.assertEqual(self._row_count("experiment_revocations"), 1)
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)
        self.assertEqual(store.audit_admission(request.identity).outcome, "not_found")

    def _scenario_incomplete_revocation_evidence(self) -> None:
        store = self._new_store(complete=False)
        request = self._request("incomplete")
        baseline = store.watermark()
        result = store.admit(request)
        self.assertEqual(result.outcome, "revocation_incomplete")
        self.assertEqual(result.retry, "remediate")
        self.assertEqual(self.clock.calls, 0)
        self.assertEqual(store.watermark(), baseline)
        self.assertEqual(self._row_count("experiment_admissions"), 0)
        self.assertEqual(self._row_count("dispatch_intents"), 0)
        self.assertEqual(store.audit_admission(request.identity).outcome, "not_found")
        self.assertEqual(
            store.set_revocation_completeness().outcome,
            "revocation_evidence_complete",
        )
        self.assertEqual(store.admit(request).outcome, "newly_admitted")

    def _scenario_multiple_admission_conflicts(self) -> None:
        store = self._new_store()
        original = self._request("conflicts")
        admitted = self._admit(store, original)
        cases = (
            (
                "binding_conflict",
                "binding_only",
                self._request("conflicts", binding_payload=b"binding::other"),
            ),
            (
                "grant_identity_conflict",
                "grant_precedes_binding",
                self._request(
                    "conflicts",
                    grant_payload=b"grant::other",
                    binding_payload=b"binding::other",
                ),
            ),
            (
                "grant_identity_conflict",
                "identity_precedes_run_and_binding",
                self._request(
                    "conflicts",
                    run_id="run::other",
                    grant_payload=b"grant::other",
                    binding_payload=b"binding::other",
                ),
            ),
            (
                "run_conflict",
                "run_precedes_time_decision",
                self._request(
                    "other-identity",
                    run_id=original.run_id,
                    grant_payload=b"grant::other",
                    binding_payload=b"binding::other",
                    issued_at=BASE_TIME + timedelta(seconds=1),
                    expires_at=BASE_TIME + timedelta(hours=1),
                ),
            ),
        )
        calls = self.clock.calls
        for expected, precedence, request in cases:
            with self.subTest(expected=expected, precedence=precedence):
                result = store.admit(request)
                self.assertEqual(result.outcome, expected)
                self.assertEqual(result.retry, "do_not_retry")
                self.assertIsNone(result.admission)
                self.assertIsNone(result.intent)
        self.assertEqual(self.clock.calls, calls)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        audit = store.audit_admission(original.identity)
        self.assertEqual(audit.admission, admitted.admission)
        self.assertEqual(audit.intent, admitted.intent)
        self.assertEqual(
            store.audit_admission(cases[-1][2].identity).outcome,
            "not_found",
        )

    def _scenario_admission_postcheck(self, terminal: bool) -> None:
        store = self._new_store()
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        executor = create_executor_capability()
        proxy = _LifecycleTransitionStore(store, session, terminal=terminal)
        coordinator = ExperimentCoordinator(proxy, session=session, executor=executor)
        request = self._request("postcheck")
        result = coordinator.admit(request)
        proxy.join()
        self.assertIsNone(result.store_result)
        self.assertFalse(result.postchecked)
        audit = store.audit_admission(request.identity)
        self.assertEqual(audit.outcome, "audited_admission_history")
        self.assertTrue(audit.exact_history)
        self.assertIsNotNone(audit.admission)
        self.assertIsNotNone(audit.intent)
        self.assertEqual(audit.admission.identity, request.identity)
        self.assertEqual(audit.admission.run_id, request.run_id)
        self.assertEqual(audit.admission.grant_payload, request.grant_payload)
        self.assertEqual(audit.admission.binding_payload, request.binding_payload)
        self.assertEqual(audit.intent.identity, request.identity)
        self.assertIn("non-authoritative", audit.detail)
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)
        watermark = store.watermark()
        calls = self.clock.calls
        if terminal:
            self.assertEqual(result.outcome, "terminal_fence")
            self.assertTrue(result.terminal)
            recovery = coordinator.admit(request)
            self.assertEqual(recovery.outcome, "terminal_fence")
            self.assertTrue(recovery.terminal)
            self.assertIsNone(recovery.store_result)
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(store.watermark(), watermark)
            self.assertEqual(self._row_count("experiment_admissions"), 1)
            self.assertEqual(self._row_count("dispatch_intents"), 1)
        else:
            self.assertEqual(result.outcome, "commit_unknown")
            surrogate.recover_after_loss(timeout=5)
            recovered = ExperimentCoordinator(
                store,
                session=surrogate.acquire(),
                executor=executor,
            ).admit(request)
            self.assertEqual(recovered.outcome, "existing_exact_admission")
            self.assertTrue(recovered.postchecked)
            self.assertIsNotNone(recovered.store_result)
            self.assertTrue(recovered.store_result.exact_history)
            self.assertEqual(recovered.store_result.admission, audit.admission)
            self.assertEqual(recovered.store_result.intent, audit.intent)
            self.assertEqual(self.clock.calls, calls)
            self.assertEqual(store.watermark(), watermark)
            self.assertEqual(self._row_count("experiment_admissions"), 1)
            self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_claim_crash_points(self, *fault_points: str) -> None:
        for fault_point in fault_points:
            with self.subTest(fault_point=fault_point):
                self._reset_ledger()
                self._scenario_claim_crash(fault_point)

    def _scenario_renewal_history_after_change(self) -> None:
        for state in ("expired", "superseded"):
            with self.subTest(state=state):
                self._reset_ledger()
                self.clock.set(BASE_TIME)
                store = self._new_store()
                self._admit(store)
                surrogate, session, _, coordinator = self._coordinator(store)
                claimed = coordinator.claim(f"claim::guarded-{state}")
                self.assertEqual(claimed.outcome, "newly_claimed")
                self.assertTrue(claimed.postchecked)
                claim = claimed.store_result.claim

                self.clock.set(BASE_TIME + timedelta(seconds=2))
                renewed = coordinator.renew(
                    claim.identity,
                    claim.claim_id,
                    claim.lease_generation,
                    f"renewal::guarded-{state}",
                )
                self.assertEqual(renewed.outcome, "renewed")
                self.assertTrue(renewed.postchecked)
                renewal = renewed.store_result.renewal

                self.clock.set(BASE_TIME + timedelta(seconds=33))
                if state == "expired":
                    expired = coordinator.assess_current_claim(
                        claim.identity,
                        claim.claim_id,
                        claim.lease_generation,
                    )
                    self.assertEqual(expired.outcome, "inactive")
                    self.assertTrue(expired.postchecked)
                    self.assertEqual(
                        expired.store_result.assessment.reason,
                        "expired",
                    )
                else:
                    second = store.claim(
                        ClaimRequest("claim::guarded-new", "executor::guarded-new")
                    )
                    self.assertEqual(second.outcome, "newly_claimed")
                    self.assertEqual(second.claim.lease_generation, 2)

                calls = self.clock.calls
                watermark = store.watermark()
                self.clock.fail()
                history = coordinator.renew(
                    claim.identity,
                    claim.claim_id,
                    claim.lease_generation,
                    renewal.renewal_id,
                )
                self.assertEqual(history.outcome, "existing_renewal_history")
                self.assertTrue(history.postchecked)
                self.assertEqual(history.store_result.renewal, renewal)
                self.assertTrue(history.store_result.exact_history)
                self.assertIsNone(history.store_result.assessment)
                self.assertEqual(self.clock.calls, calls)
                self.assertEqual(store.watermark(), watermark)
                self.assertEqual(self._row_count("lease_renewals"), 1)
                session.release(timeout=5.0)

    def _scenario_sqlite_below_minimum(self) -> None:
        self.assertEqual(MINIMUM_SQLITE_VERSION, (3, 37, 0))
        with mock.patch.object(store_module.sqlite3, "sqlite_version_info", (3, 36, 0)):
            result = DispatchOutboxClaimLeaseStore.provision_legacy(self.configuration)
            with self.assertRaises(ConfigurationError):
                DispatchOutboxClaimLeaseStore.open(
                    self.configuration,
                    clock=self.clock,
                )
        self.assertEqual(result.outcome, "storage_unavailable")
        self.assertIn("3.37.0", result.detail)
        self.assertFalse(self.database_path.exists())

    def _scenario_effective_connection_profile(self) -> None:
        provisioned = DispatchOutboxClaimLeaseStore.provision_legacy(self.configuration)
        self.assertEqual(provisioned.outcome, "provisioned")
        self.assertIsNotNone(provisioned.profile)
        self._migrate()
        store = self._open_store()
        profile = store.connection_profile()
        self.assertEqual(profile.sqlite_version, sqlite3.sqlite_version)
        self.assertGreaterEqual(sqlite3.sqlite_version_info, MINIMUM_SQLITE_VERSION)
        self.assertEqual(provisioned.profile.sqlite_version, sqlite3.sqlite_version)
        self.assertEqual(profile.journal_mode, "wal")
        self.assertEqual(profile.synchronous, 2)
        self.assertEqual(profile.foreign_keys, 1)
        self.assertEqual(profile.locking_mode, "normal")
        self.assertEqual(profile.busy_timeout_ms, BUSY_TIMEOUT_MS)
        self.assertIsNone(profile.isolation_level)
        self.assertEqual(profile.write_begin, "BEGIN IMMEDIATE")
        connection = open_profiled_connection(self.configuration)
        try:
            self.assertIsNone(connection.isolation_level)
            self.assertEqual(
                int(connection.execute("PRAGMA application_id").fetchone()[0]),
                APPLICATION_ID,
            )
        finally:
            connection.close()

    def _scenario_rejected_admission_with_winner(self) -> None:
        self._new_store()
        valid = self._request("winner")
        invalid = AdmissionRequest(
            authorization_domain_id="domain::not-pinned",
            issuer_kind=valid.issuer_kind,
            issuer_id=valid.issuer_id,
            grant_id=valid.grant_id,
            run_id=valid.run_id,
            grant_payload=valid.grant_payload,
            binding_payload=valid.binding_payload,
            issued_at=valid.issued_at,
            expires_at=valid.expires_at,
        )
        results = race_storage_probes(
            (
                self._probe("admit", request=invalid),
                self._probe("admit", request=valid),
            )
        )
        self.assertCountEqual(
            [result.outcome for result in results],
            ["invalid_input", "newly_admitted"],
        )
        winner = next(result for result in results if result.outcome == "newly_admitted")
        rejected = next(result for result in results if result.outcome == "invalid_input")
        self.assertNotEqual(winner.pid, rejected.pid)
        self.assertEqual(winner.payload["admission"]["run_id"], valid.run_id)
        self.assertEqual(
            winner.payload["admission"]["grant_payload"],
            {"bytes_hex": valid.grant_payload.hex()},
        )
        self.assertEqual(
            winner.payload["admission"]["binding_payload"],
            {"bytes_hex": valid.binding_payload.hex()},
        )
        self.assertEqual(
            winner.payload["admission"]["identity"],
            winner.payload["intent"]["identity"],
        )
        self.assertIsNone(rejected.payload["admission"])
        self.assertIsNone(rejected.payload["intent"])
        audit = self._open_store().audit_admission(valid.identity)
        audit_document = harness_module._primitive_document(audit)
        self.assertEqual(audit_document["admission"], winner.payload["admission"])
        self.assertEqual(audit_document["intent"], winner.payload["intent"])
        self.assertEqual(self._row_count("experiment_admissions"), 1)
        self.assertEqual(self._row_count("dispatch_intents"), 1)

    def _scenario_revocation_claim_order(self) -> None:
        for revocation_first in (True, False):
            with self.subTest(revocation_first=revocation_first):
                self._reset_ledger()
                store = self._new_store()
                request = self._request("revoke-claim")
                self._admit(store, request, at=BASE_TIME)
                if revocation_first:
                    self.clock.set(BASE_TIME + timedelta(seconds=1))
                    self.assertEqual(store.revoke(request).outcome, "newly_revoked")
                    claim = store.claim(ClaimRequest("claim::ordered", "executor::1"))
                    self.assertEqual(claim.outcome, "authority_ineligible")
                    self.assertIsNone(claim.claim)
                    self.assertEqual(self._row_count("dispatch_claims"), 0)
                else:
                    self.clock.set(BASE_TIME + timedelta(seconds=1))
                    claim = store.claim(ClaimRequest("claim::ordered", "executor::1"))
                    self.assertEqual(claim.outcome, "newly_claimed")
                    self.clock.set(BASE_TIME + timedelta(seconds=2))
                    self.assertEqual(store.revoke(request).outcome, "newly_revoked")
                    assessed = store.assess_current_claim(
                        self._assessment_request(claim.claim)
                    )
                    self.assertEqual(assessed.outcome, "revoked")
                    history = store.audit_claim(claim.claim.claim_id)
                    self.assertEqual(history.outcome, "audited_claim_history")
                    self.assertEqual(history.claim, claim.claim)
                    self.assertTrue(history.exact_history)
                    self.assertIn("non-authoritative", history.detail)
                self.assertEqual(self._row_count("experiment_revocations"), 1)

    def _scenario_revocation_renewal_order(self) -> None:
        for revocation_first in (True, False):
            with self.subTest(revocation_first=revocation_first):
                self._reset_ledger()
                store = self._new_store()
                request = self._request("revoke-renew")
                self._admit(store, request, at=BASE_TIME)
                claim = self._claim(store, at=BASE_TIME + timedelta(seconds=1))
                if revocation_first:
                    self.clock.set(BASE_TIME + timedelta(seconds=2))
                    self.assertEqual(store.revoke(request).outcome, "newly_revoked")
                    renewal = store.renew(self._renew_request(claim.claim))
                    self.assertEqual(renewal.outcome, "revoked")
                    self.assertEqual(self._row_count("lease_renewals"), 0)
                else:
                    self.clock.set(BASE_TIME + timedelta(seconds=2))
                    renewal = store.renew(self._renew_request(claim.claim))
                    self.assertEqual(renewal.outcome, "renewed")
                    self.clock.set(BASE_TIME + timedelta(seconds=3))
                    self.assertEqual(store.revoke(request).outcome, "newly_revoked")
                    assessed = store.assess_current_claim(
                        self._assessment_request(claim.claim)
                    )
                    self.assertEqual(assessed.outcome, "revoked")
                    history = store.audit_renewal(renewal.renewal.renewal_id)
                    self.assertEqual(history.outcome, "audited_renewal_history")
                    self.assertEqual(history.renewal, renewal.renewal)
                    self.assertTrue(history.exact_history)
                    self.assertIn("non-authoritative", history.detail)

    def _scenario_terminal_fence_reconciliation(self) -> None:
        store, admission, claim = self._admitted_claim_store()
        before = (
            admission.admission,
            admission.intent,
            claim.claim,
            store.watermark(),
            self._row_count("experiment_admissions"),
            self._row_count("dispatch_intents"),
            self._row_count("dispatch_claims"),
            self._row_count("lease_renewals"),
        )
        fenced = store.fence()
        self.assertEqual(fenced.outcome, "fenced")
        with self.assertRaises(IncompatibleSchemaError):
            self._open_store()
        administrative = self._open_store(allow_fenced=True)
        admission_audit = administrative.audit_admission(admission.admission.identity)
        claim_audit = administrative.audit_claim(claim.claim.claim_id)
        self.assertEqual(admission_audit.outcome, "audited_admission_history")
        self.assertEqual(claim_audit.outcome, "audited_claim_history")
        self.assertTrue(admission_audit.exact_history)
        self.assertTrue(claim_audit.exact_history)
        self.assertIn("non-authoritative", claim_audit.detail)
        self.assertEqual(admission_audit.admission, before[0])
        self.assertEqual(admission_audit.intent, before[1])
        self.assertEqual(claim_audit.claim, before[2])
        after = (
            self._metadata()[3:],
            self._row_count("experiment_admissions"),
            self._row_count("dispatch_intents"),
            self._row_count("dispatch_claims"),
            self._row_count("lease_renewals"),
        )
        self.assertEqual(after, before[3:])
        self.assertEqual(administrative.fence().outcome, "already_fenced")
        with self.assertRaises(IncompatibleSchemaError):
            self._open_store()

    def _scenario_canonical_integration_boundary(self) -> None:
        exported = {
            name: getattr(module, name)
            for module in (store_module, harness_module)
            for name in module.__all__
        }
        self.assertGreater(len(exported), 0)
        for name, value in exported.items():
            with self.subTest(export=name):
                module_name = getattr(value, "__module__", None)
                if module_name is not None:
                    self.assertFalse(module_name.startswith("core."))
                    self.assertFalse(module_name.startswith("orchestra."))
        self.assertEqual(
            DispatchOutboxClaimLeaseStore.__module__,
            "experiments.dispatch_outbox_claim_lease.store",
        )
        self.assertEqual(
            ExperimentCoordinator.__module__,
            "experiments.dispatch_outbox_claim_lease.worker_harness",
        )
        self.assertIn("private experiment evidence only", NONCANONICAL_DISCLAIMER)
        self.assertIn("not canonical AIO-049", NONCANONICAL_DISCLAIMER)
        coordinator_parameters = set(inspect.signature(ExperimentCoordinator).parameters)
        self.assertEqual(coordinator_parameters, {"store", "session", "executor"})
        self.assertNotIn("invoke", harness_module.__all__)
        self.assertNotIn("dispatch", harness_module.__all__)


_SCENARIOS = {
    1: ScenarioSpec(_SCENARIO_NAMES[1], "_scenario_new_admission"),
    2: ScenarioSpec(_SCENARIO_NAMES[2], "_scenario_admission_history_clock", (False,)),
    3: ScenarioSpec(_SCENARIO_NAMES[3], "_scenario_admission_history_clock", (True,)),
    4: ScenarioSpec(_SCENARIO_NAMES[4], "_scenario_admission_crash", ("admission.before_transaction", False)),
    5: ScenarioSpec(_SCENARIO_NAMES[5], "_scenario_admission_crash", ("admission.after_begin", False)),
    6: ScenarioSpec(_SCENARIO_NAMES[6], "_scenario_admission_crash", ("admission.after_admission_insert", False)),
    7: ScenarioSpec(_SCENARIO_NAMES[7], "_scenario_admission_crash", ("admission.after_intent_insert", False)),
    8: ScenarioSpec(_SCENARIO_NAMES[8], "_scenario_admission_crash", ("admission.after_watermark", True)),
    9: ScenarioSpec(_SCENARIO_NAMES[9], "_scenario_admission_ambiguous", (False,)),
    10: ScenarioSpec(_SCENARIO_NAMES[10], "_scenario_admission_ambiguous", (True,)),
    11: ScenarioSpec(_SCENARIO_NAMES[11], "_scenario_migrate_existing"),
    12: ScenarioSpec(_SCENARIO_NAMES[12], "_scenario_migration_preflight_mismatch"),
    13: ScenarioSpec(_SCENARIO_NAMES[13], "_scenario_operational_open_rejects_schema_states"),
    14: ScenarioSpec(_SCENARIO_NAMES[14], "_scenario_migration_crash", ("migration.before_commit",)),
    15: ScenarioSpec(_SCENARIO_NAMES[15], "_scenario_migration_ambiguous"),
    16: ScenarioSpec(_SCENARIO_NAMES[16], "_scenario_legacy_retry", (False,)),
    17: ScenarioSpec(_SCENARIO_NAMES[17], "_scenario_xor_corruption"),
    18: ScenarioSpec(_SCENARIO_NAMES[18], "_scenario_one_pending_intent"),
    19: ScenarioSpec(_SCENARIO_NAMES[19], "_scenario_multiple_eligible_intents"),
    20: ScenarioSpec(_SCENARIO_NAMES[20], "_scenario_raw_claim_race"),
    21: ScenarioSpec(_SCENARIO_NAMES[21], "_scenario_concurrent_lifecycle_operations"),
    22: ScenarioSpec(_SCENARIO_NAMES[22], "_scenario_claim_race_winner"),
    23: ScenarioSpec(_SCENARIO_NAMES[23], "_scenario_active_lease"),
    24: ScenarioSpec(_SCENARIO_NAMES[24], "_scenario_claim_history", ("active",)),
    25: ScenarioSpec(_SCENARIO_NAMES[25], "_scenario_claim_history", ("expired",)),
    26: ScenarioSpec(_SCENARIO_NAMES[26], "_scenario_claim_history", ("superseded",)),
    27: ScenarioSpec(_SCENARIO_NAMES[27], "_scenario_claim_executor_rebound"),
    28: ScenarioSpec(_SCENARIO_NAMES[28], "_scenario_stored_claim_rebound"),
    29: ScenarioSpec(_SCENARIO_NAMES[29], "_scenario_expiry_boundary"),
    30: ScenarioSpec(_SCENARIO_NAMES[30], "_scenario_reclaim", (True,)),
    31: ScenarioSpec(_SCENARIO_NAMES[31], "_scenario_reclaim", (False,)),
    32: ScenarioSpec(_SCENARIO_NAMES[32], "_scenario_stale_claimant"),
    33: ScenarioSpec(_SCENARIO_NAMES[33], "_scenario_claim_crash", ("claim.before_transaction",)),
    34: ScenarioSpec(_SCENARIO_NAMES[34], "_scenario_claim_crash_points", ("claim.after_begin", "claim.after_insert")),
    35: ScenarioSpec(_SCENARIO_NAMES[35], "_scenario_claim_crash", ("claim.after_watermark",)),
    36: ScenarioSpec(_SCENARIO_NAMES[36], "_scenario_claim_ambiguous"),
    37: ScenarioSpec(_SCENARIO_NAMES[37], "_scenario_worker_crash_after_claim"),
    38: ScenarioSpec(_SCENARIO_NAMES[38], "_scenario_valid_renewal"),
    39: ScenarioSpec(_SCENARIO_NAMES[39], "_scenario_nonextending_renewal"),
    40: ScenarioSpec(_SCENARIO_NAMES[40], "_scenario_renewal_history", ("active",)),
    41: ScenarioSpec(_SCENARIO_NAMES[41], "_scenario_renewal_history_after_change"),
    42: ScenarioSpec(_SCENARIO_NAMES[42], "_scenario_renewal_response_loss"),
    43: ScenarioSpec(_SCENARIO_NAMES[43], "_scenario_renewal_rebound"),
    44: ScenarioSpec(_SCENARIO_NAMES[44], "_scenario_stale_generation_renewal"),
    45: ScenarioSpec(_SCENARIO_NAMES[45], "_scenario_expired_renewal"),
    46: ScenarioSpec(_SCENARIO_NAMES[46], "_scenario_concurrent_renewals"),
    47: ScenarioSpec(_SCENARIO_NAMES[47], "_scenario_renewal_reclaim_race"),
    48: ScenarioSpec(_SCENARIO_NAMES[48], "_scenario_renewal_crash", ("renewal.before_transaction",)),
    49: ScenarioSpec(_SCENARIO_NAMES[49], "_scenario_renewal_crash", ("renewal.after_insert",)),
    50: ScenarioSpec(_SCENARIO_NAMES[50], "_scenario_renewal_crash", ("renewal.after_watermark",)),
    51: ScenarioSpec(_SCENARIO_NAMES[51], "_scenario_renewal_ambiguous"),
    52: ScenarioSpec(_SCENARIO_NAMES[52], "_scenario_renewal_chain_corruption"),
    53: ScenarioSpec(_SCENARIO_NAMES[53], "_scenario_clock_unavailable_or_throwing"),
    54: ScenarioSpec(_SCENARIO_NAMES[54], "_scenario_malformed_clock"),
    55: ScenarioSpec(_SCENARIO_NAMES[55], "_scenario_clock_regression"),
    56: ScenarioSpec(_SCENARIO_NAMES[56], "_scenario_watermark_semantics"),
    57: ScenarioSpec(_SCENARIO_NAMES[57], "_scenario_forward_wall_clock_jump"),
    58: ScenarioSpec(_SCENARIO_NAMES[58], "_scenario_restart_during_active_lease"),
    59: ScenarioSpec(_SCENARIO_NAMES[59], "_scenario_wal_restart"),
    60: ScenarioSpec(_SCENARIO_NAMES[60], "_scenario_worker_process_restart"),
    61: ScenarioSpec(_SCENARIO_NAMES[61], "_scenario_repeated_reclaim"),
    62: ScenarioSpec(_SCENARIO_NAMES[62], "_scenario_generation_corruption"),
    63: ScenarioSpec(_SCENARIO_NAMES[63], "_scenario_complete_lifecycle_guard"),
    64: ScenarioSpec(_SCENARIO_NAMES[64], "_scenario_domain_fenced_before_claim"),
    65: ScenarioSpec(_SCENARIO_NAMES[65], "_scenario_fencing_race"),
    66: ScenarioSpec(_SCENARIO_NAMES[66], "_scenario_claim_postcheck", (True,)),
    67: ScenarioSpec(_SCENARIO_NAMES[67], "_scenario_post_admission_revocation"),
    68: ScenarioSpec(_SCENARIO_NAMES[68], "_scenario_wrong_admission_identity"),
    69: ScenarioSpec(_SCENARIO_NAMES[69], "_scenario_index_payload_corruption"),
    70: ScenarioSpec(_SCENARIO_NAMES[70], "_scenario_binding_substitution", ("tool",)),
    71: ScenarioSpec(_SCENARIO_NAMES[71], "_scenario_binding_substitution", ("runtime",)),
    72: ScenarioSpec(_SCENARIO_NAMES[72], "_scenario_binding_substitution", ("actor-operation-resource",)),
    73: ScenarioSpec(_SCENARIO_NAMES[73], "_scenario_corrupt_or_newer_schema"),
    74: ScenarioSpec(_SCENARIO_NAMES[74], "_scenario_connection_profile_pressure"),
    75: ScenarioSpec(_SCENARIO_NAMES[75], "_scenario_negative_execution_boundary"),
    76: ScenarioSpec(_SCENARIO_NAMES[76], "_scenario_concurrent_identical_admissions"),
    77: ScenarioSpec(_SCENARIO_NAMES[77], "_scenario_binding_substitution", ("binding",)),
    78: ScenarioSpec(_SCENARIO_NAMES[78], "_scenario_different_grant_same_run"),
    79: ScenarioSpec(_SCENARIO_NAMES[79], "_scenario_temporal_admission", ("not_yet",)),
    80: ScenarioSpec(_SCENARIO_NAMES[80], "_scenario_temporal_admission", ("expired",)),
    81: ScenarioSpec(_SCENARIO_NAMES[81], "_scenario_pre_revoked_grant"),
    82: ScenarioSpec(_SCENARIO_NAMES[82], "_scenario_incomplete_revocation_evidence"),
    83: ScenarioSpec(_SCENARIO_NAMES[83], "_scenario_multiple_admission_conflicts"),
    84: ScenarioSpec(_SCENARIO_NAMES[84], "_scenario_admission_postcheck", (False,)),
    85: ScenarioSpec(_SCENARIO_NAMES[85], "_scenario_admission_postcheck", (True,)),
    86: ScenarioSpec(_SCENARIO_NAMES[86], "_scenario_migration_crash", ("migration.after_dirty",)),
    87: ScenarioSpec(_SCENARIO_NAMES[87], "_scenario_migration_crash", ("migration.after_schema",)),
    88: ScenarioSpec(_SCENARIO_NAMES[88], "_scenario_migration_crash", ("migration.after_legacy_population",)),
    89: ScenarioSpec(_SCENARIO_NAMES[89], "_scenario_migration_crash", ("migration.after_clean_transition",)),
    90: ScenarioSpec(_SCENARIO_NAMES[90], "_scenario_empty_queue"),
    91: ScenarioSpec(_SCENARIO_NAMES[91], "_scenario_authority_ineligible"),
    92: ScenarioSpec(_SCENARIO_NAMES[92], "_scenario_all_active"),
    93: ScenarioSpec(_SCENARIO_NAMES[93], "_scenario_lost_no_row", ("active",)),
    94: ScenarioSpec(_SCENARIO_NAMES[94], "_scenario_lost_no_row", ("empty",)),
    95: ScenarioSpec(_SCENARIO_NAMES[95], "_scenario_no_row_later_eligible"),
    96: ScenarioSpec(_SCENARIO_NAMES[96], "_scenario_claim_postcheck", (False,)),
    97: ScenarioSpec(_SCENARIO_NAMES[97], "_scenario_claim_postcheck", (True,)),
    98: ScenarioSpec(_SCENARIO_NAMES[98], "_scenario_lost_noninserted_renewal", (False,)),
    99: ScenarioSpec(_SCENARIO_NAMES[99], "_scenario_lost_noninserted_renewal", (True,)),
    100: ScenarioSpec(_SCENARIO_NAMES[100], "_scenario_renewal_crash", ("renewal.after_begin",)),
    101: ScenarioSpec(_SCENARIO_NAMES[101], "_scenario_renewal_crash", ("renewal.after_invariant_validation",)),
    102: ScenarioSpec(_SCENARIO_NAMES[102], "_scenario_renewal_crash", ("renewal.after_clock_sample",)),
    103: ScenarioSpec(_SCENARIO_NAMES[103], "_scenario_renewal_postcheck", (False,)),
    104: ScenarioSpec(_SCENARIO_NAMES[104], "_scenario_renewal_postcheck", (True,)),
    105: ScenarioSpec(_SCENARIO_NAMES[105], "_scenario_old_executor_coordinator"),
    106: ScenarioSpec(_SCENARIO_NAMES[106], "_scenario_old_executor_raw_store"),
    107: ScenarioSpec(_SCENARIO_NAMES[107], "_scenario_invalid_lease_configuration"),
    108: ScenarioSpec(_SCENARIO_NAMES[108], "_scenario_equal_time_tie", (False,)),
    109: ScenarioSpec(_SCENARIO_NAMES[109], "_scenario_sqlite_below_minimum"),
    110: ScenarioSpec(_SCENARIO_NAMES[110], "_scenario_effective_connection_profile"),
    111: ScenarioSpec(_SCENARIO_NAMES[111], "_scenario_claim_crash", ("claim.after_invariant_validation",)),
    112: ScenarioSpec(_SCENARIO_NAMES[112], "_scenario_claim_crash", ("claim.after_clock_sample",)),
    113: ScenarioSpec(_SCENARIO_NAMES[113], "_scenario_rejected_admission_with_winner"),
    114: ScenarioSpec(_SCENARIO_NAMES[114], "_scenario_revocation_claim_order"),
    115: ScenarioSpec(_SCENARIO_NAMES[115], "_scenario_admission_crash", ("admission.after_intent_insert", False)),
    116: ScenarioSpec(_SCENARIO_NAMES[116], "_scenario_equal_time_tie", (True,)),
    117: ScenarioSpec(_SCENARIO_NAMES[117], "_scenario_legacy_retry", (True,)),
    118: ScenarioSpec(_SCENARIO_NAMES[118], "_scenario_revocation_renewal_order"),
    119: ScenarioSpec(_SCENARIO_NAMES[119], "_scenario_terminal_fence_reconciliation"),
    120: ScenarioSpec(_SCENARIO_NAMES[120], "_scenario_canonical_integration_boundary"),
    121: ScenarioSpec(_SCENARIO_NAMES[121], "_scenario_claim_history_only"),
    122: ScenarioSpec(_SCENARIO_NAMES[122], "_scenario_renewal_history_only"),
    123: ScenarioSpec(_SCENARIO_NAMES[123], "_scenario_assessment", ("active",)),
    124: ScenarioSpec(_SCENARIO_NAMES[124], "_scenario_assessment", ("inactive",)),
    125: ScenarioSpec(_SCENARIO_NAMES[125], "_scenario_assessment", ("clock_failure",)),
    126: ScenarioSpec(_SCENARIO_NAMES[126], "_scenario_assessment", ("terminal",)),
    127: ScenarioSpec(_SCENARIO_NAMES[127], "_scenario_renewal_sequence_rollback"),
    128: ScenarioSpec(_SCENARIO_NAMES[128], "_scenario_renewal_sequence_corruption"),
}


if tuple(sorted(_SCENARIOS)) != tuple(range(1, 129)):
    raise AssertionError("AIO-054 implementation registry must contain exactly IDs 1..128")
if {scenario_id: spec.name for scenario_id, spec in _SCENARIOS.items()} != _SCENARIO_NAMES:
    raise AssertionError("AIO-054 implementation registry must preserve every locked name")
for _scenario_id, _scenario_spec in _SCENARIOS.items():
    if not hasattr(DispatchOutboxClaimLeaseExperimentTests, _scenario_spec.handler):
        raise AssertionError(
            f"AIO-054 scenario {_scenario_id} has no handler {_scenario_spec.handler}"
        )


def _make_scenario_test(scenario_id: int, scenario_name: str):
    def scenario_test(self: DispatchOutboxClaimLeaseExperimentTests) -> None:
        self._execute_scenario(scenario_id)

    scenario_test.__name__ = f"test_s{scenario_id:03d}_{scenario_name}"
    scenario_test.__qualname__ = (
        f"{DispatchOutboxClaimLeaseExperimentTests.__name__}."
        f"test_s{scenario_id:03d}_{scenario_name}"
    )
    scenario_test.__doc__ = f"AIO-054 scenario {scenario_id}: {scenario_name}."
    return scenario_test


for _scenario_id, _scenario_spec in _SCENARIOS.items():
    _method_name = f"test_s{_scenario_id:03d}_{_scenario_spec.name}"
    setattr(
        DispatchOutboxClaimLeaseExperimentTests,
        _method_name,
        _make_scenario_test(_scenario_id, _scenario_spec.name),
    )


_DISCOVERABLE_SCENARIO_METHODS = tuple(
    name
    for name in vars(DispatchOutboxClaimLeaseExperimentTests)
    if name.startswith("test_s")
)
if len(_DISCOVERABLE_SCENARIO_METHODS) != 128:
    raise AssertionError("AIO-054 must expose exactly 128 discoverable scenario methods")
if {
    int(name.removeprefix("test_s")[:3])
    for name in _DISCOVERABLE_SCENARIO_METHODS
} != set(range(1, 129)):
    raise AssertionError("AIO-054 discoverable methods must cover exactly IDs 1..128")


def _verify_aio054_t3_child_process_safety() -> None:
    result = run_t3_child_process_safety_validation()
    if result.child_processes_created != 2:
        raise AssertionError("amended T3 must create exactly two owned children")
    if result.child_processes_reaped != 2:
        raise AssertionError("amended T3 must reap exactly two owned children")
    if result.child_handles_closed != 2:
        raise AssertionError("amended T3 must close exactly two child handles")
    if len(set(result.child_process_ids)) != 2:
        raise AssertionError("amended T3 child identities must be distinct")
    if not all(pid > 0 for pid in result.child_process_ids):
        raise AssertionError("amended T3 child PIDs must be positive")
    if result.owned_temp_roots_created != 1:
        raise AssertionError("amended T3 must create exactly one owned temp root")
    if result.owned_temp_roots_removed != 1:
        raise AssertionError("amended T3 must remove exactly one owned temp root")
    if Path(result.owned_root_path).exists():
        raise AssertionError("amended T3 owned temp root still exists")
    if result.normal_termination_requests != 2:
        raise AssertionError("amended T3 must request two cooperative stops")
    if result.forced_terminations != 1:
        raise AssertionError("amended T3 must force only the stubborn child")
    unsafe = (
        result.unrelated_process_affected,
        result.repository_runtime_artifacts_left,
        result.shell_used,
        result.global_process_enumeration_used,
        result.wildcard_termination_used,
        result.network_used,
        result.protected_target_reachable,
    )
    if any(unsafe):
        raise AssertionError("amended T3 reported an unsafe process effect")
    print(
        "T3_TELEMETRY "
        "child_processes_created=2 "
        "child_processes_reaped=2 "
        "child_handles_closed=2 "
        "owned_temp_roots_created=1 "
        "owned_temp_roots_removed=1 "
        "unrelated_process_affected=no "
        "repository_runtime_artifact_left=no",
        flush=True,
    )


def aio054_t3_child_process_safety_suite() -> unittest.TestSuite:
    """Return the one explicit amended T3 target without adding discovery."""

    return unittest.TestSuite(
        (unittest.FunctionTestCase(_verify_aio054_t3_child_process_safety),)
    )


del _method_name, _scenario_id, _scenario_spec
