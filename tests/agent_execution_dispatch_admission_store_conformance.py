"""Reusable semantic conformance tests for authoritative Admission stores.

Backend test modules subclass the mixin and supply a fresh harness.  The
scenarios contain no SQLite assumptions, so a future PostgreSQL backend can
run the same exact-retry, conflict, currentness, revocation, uniqueness,
concurrency, failure, and retrieval contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Callable

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_contract import (
    AgentExecutionContract,
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


CONFORMANCE_DOMAIN_ID = "authorization-domain::store-conformance"
CONFORMANCE_DECISION_TIME = datetime(
    2026,
    9,
    23,
    10,
    30,
    tzinfo=timezone.utc,
)


@dataclass(frozen=True)
class AdmissionStoreConformanceHarness:
    """Backend adapter for the reusable semantic suite."""

    store: object
    set_clock: Callable[[object], None]
    clock_calls: Callable[[], int]
    make_storage_unavailable: Callable[[], None]


def make_conformance_run(
    run_id: str = "run::store-conformance",
    *,
    task_id: str = "AIO-047-store-conformance",
) -> AgentExecutionRun:
    return AgentExecutionRun(
        run_id,
        AgentExecutionContract(
            task_id,
            "architecture-change",
            "implement",
            "software-engineer",
            "actor::store-conformance",
            "runtime::store-conformance",
            "option::store-conformance",
            "environment::store-conformance",
            "repository_file_read",
            "synthetic/store-conformance.txt",
            "critical",
        ),
    )


def make_conformance_grant(
    *,
    run: AgentExecutionRun | None = None,
    grant_id: str = "grant::store-conformance",
    domain_id: str = CONFORMANCE_DOMAIN_ID,
) -> AgentExecutionAuthorizationGrant:
    return AgentExecutionAuthorizationGrant(
        grant_id,
        make_conformance_run() if run is None else run,
        domain_id,
        "policy",
        "issuer::store-conformance",
        "approval::store-conformance",
        "2026-09-23T10:00:00Z",
        "2026-09-23T11:00:00Z",
    )


def make_conformance_binding(
    run: AgentExecutionRun,
    *,
    tool_id: str = "tool::store-conformance::v1",
) -> AgentOperationToolBinding:
    return AgentOperationToolBinding(run, tool_id)


class AgentExecutionDispatchAdmissionStoreConformanceMixin:
    """Backend-neutral semantic tests; combine with ``unittest.TestCase``."""

    def make_conformance_harness(
        self,
        *,
        decision_time: object = CONFORMANCE_DECISION_TIME,
    ) -> AdmissionStoreConformanceHarness:
        raise NotImplementedError

    def assert_store_outcome(self, result: object, expected: str) -> None:
        self.assertEqual(  # type: ignore[attr-defined]
            result.outcome.value,  # type: ignore[attr-defined]
            expected,
            result.detail,  # type: ignore[attr-defined]
        )

    def run_concurrently(
        self,
        *operations: Callable[[], object],
    ) -> list[object]:
        barrier = threading.Barrier(len(operations))
        values: list[object | None] = [None] * len(operations)

        def invoke(index: int, operation: Callable[[], object]) -> None:
            try:
                barrier.wait(10)
                values[index] = operation()
            except BaseException as error:  # pragma: no cover - assertion aid
                values[index] = error

        threads = [
            threading.Thread(target=invoke, args=(index, operation), daemon=True)
            for index, operation in enumerate(operations)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
            self.assertFalse(  # type: ignore[attr-defined]
                thread.is_alive(),
                "conformance worker hung",
            )
        for value in values:
            if isinstance(value, BaseException):
                raise value
            self.assertIsNotNone(value)  # type: ignore[attr-defined]
        return [value for value in values if value is not None]

    def test_store_conformance_exact_retry_conflicts_and_retrieval(self) -> None:
        harness = self.make_conformance_harness()
        store = harness.store
        run = make_conformance_run()
        grant = make_conformance_grant(run=run)
        binding = make_conformance_binding(run)
        request = _mint_admission_request(
            CONFORMANCE_DOMAIN_ID,
            grant,
            binding,
            run,
        )

        created = store.admit_or_return_existing(request)
        self.assert_store_outcome(created, "newly_admitted")
        original_calls = harness.clock_calls()
        harness.set_clock(RuntimeError("exact retry must not sample time"))
        retried = store.admit_or_return_existing(request)
        self.assert_store_outcome(retried, "existing_exact_admission")
        self.assertEqual(retried.admission, created.admission)  # type: ignore[attr-defined]
        self.assertEqual(harness.clock_calls(), original_calls)  # type: ignore[attr-defined]

        loaded = store.load_authoritative_admission(
            _mint_authoritative_lookup_request(
                CONFORMANCE_DOMAIN_ID,
                grant,
                binding,
            )
        )
        self.assert_store_outcome(loaded, "existing_exact_admission")
        self.assertEqual(loaded.admission, created.admission)  # type: ignore[attr-defined]

        changed_binding = make_conformance_binding(
            run,
            tool_id="tool::store-conformance::changed",
        )
        binding_conflict = store.classify_guarded_history(
            _mint_guarded_history_request(
                CONFORMANCE_DOMAIN_ID,
                grant,
                changed_binding,
            )
        )
        self.assert_store_outcome(binding_conflict, "binding_conflict")

        rebound_run = make_conformance_run(
            "run::store-conformance-rebound",
            task_id="AIO-047-store-conformance-rebound",
        )
        rebound_grant = make_conformance_grant(run=rebound_run)
        grant_conflict = store.classify_guarded_history(
            _mint_guarded_history_request(
                CONFORMANCE_DOMAIN_ID,
                rebound_grant,
                make_conformance_binding(rebound_run),
            )
        )
        self.assert_store_outcome(grant_conflict, "grant_identity_conflict")

        second_grant = make_conformance_grant(
            run=run,
            grant_id="grant::store-conformance-second",
        )
        run_conflict = store.classify_guarded_history(
            _mint_guarded_history_request(
                CONFORMANCE_DOMAIN_ID,
                second_grant,
                binding,
            )
        )
        self.assert_store_outcome(run_conflict, "run_conflict")

        domain_mismatch = store.classify_guarded_history(
            _mint_guarded_history_request("domain::wrong", grant, binding)
        )
        self.assert_store_outcome(domain_mismatch, "domain_mismatch")

        precedence = self.make_conformance_harness()
        revoked_run = make_conformance_run(
            "run::store-conformance-revoked-identity",
            task_id="AIO-047-store-conformance-revoked-identity",
        )
        revoked_grant = make_conformance_grant(
            run=revoked_run,
            grant_id="grant::store-conformance-precedence",
        )
        self.assert_store_outcome(
            precedence.store.revoke_or_return_existing(
                _mint_revocation_request(
                    CONFORMANCE_DOMAIN_ID,
                    revoked_grant,
                )
            ),
            "newly_revoked",
        )
        occupied_run = make_conformance_run(
            "run::store-conformance-occupied",
            task_id="AIO-047-store-conformance-occupied",
        )
        occupying_grant = make_conformance_grant(
            run=occupied_run,
            grant_id="grant::store-conformance-occupant",
        )
        occupied_binding = make_conformance_binding(occupied_run)
        self.assert_store_outcome(
            precedence.store.admit_or_return_existing(
                _mint_admission_request(
                    CONFORMANCE_DOMAIN_ID,
                    occupying_grant,
                    occupied_binding,
                    occupied_run,
                )
            ),
            "newly_admitted",
        )
        rebound_grant = make_conformance_grant(
            run=occupied_run,
            grant_id=revoked_grant.grant_id,
        )
        combined_conflict = precedence.store.classify_guarded_history(
            _mint_guarded_history_request(
                CONFORMANCE_DOMAIN_ID,
                rebound_grant,
                occupied_binding,
            )
        )
        self.assert_store_outcome(
            combined_conflict,
            "grant_identity_conflict",
        )

    def test_store_conformance_currentness_and_clock_failures(self) -> None:
        run = make_conformance_run()
        grant = make_conformance_grant(run=run)
        binding = make_conformance_binding(run)
        request = _mint_admission_request(
            CONFORMANCE_DOMAIN_ID,
            grant,
            binding,
            run,
        )
        early = self.make_conformance_harness(
            decision_time=datetime(2026, 9, 23, 9, 59, tzinfo=timezone.utc)
        )
        self.assert_store_outcome(
            early.store.admit_or_return_existing(request),
            "not_yet_current",
        )
        expired = self.make_conformance_harness(
            decision_time=datetime(2026, 9, 23, 11, 0, tzinfo=timezone.utc)
        )
        self.assert_store_outcome(
            expired.store.admit_or_return_existing(request),
            "expired",
        )
        failed = self.make_conformance_harness(
            decision_time=RuntimeError("synthetic clock failure")
        )
        self.assert_store_outcome(
            failed.store.admit_or_return_existing(request),
            "clock_failure",
        )

        regressed = self.make_conformance_harness()
        first = regressed.store.admit_or_return_existing(request)
        self.assert_store_outcome(first, "newly_admitted")
        later_run = make_conformance_run(
            "run::store-conformance-later",
            task_id="AIO-047-store-conformance-later",
        )
        later_grant = make_conformance_grant(
            run=later_run,
            grant_id="grant::store-conformance-later",
        )
        regressed.set_clock(
            datetime(2026, 9, 23, 10, 29, tzinfo=timezone.utc)
        )
        regression = regressed.store.admit_or_return_existing(
            _mint_admission_request(
                CONFORMANCE_DOMAIN_ID,
                later_grant,
                make_conformance_binding(later_run),
                later_run,
            )
        )
        self.assert_store_outcome(regression, "clock_regression")

    def test_store_conformance_revocation_orders(self) -> None:
        run = make_conformance_run()
        grant = make_conformance_grant(run=run)
        binding = make_conformance_binding(run)
        admission_request = _mint_admission_request(
            CONFORMANCE_DOMAIN_ID,
            grant,
            binding,
            run,
        )
        revocation_request = _mint_revocation_request(
            CONFORMANCE_DOMAIN_ID,
            grant,
        )

        revoked_first = self.make_conformance_harness()
        self.assert_store_outcome(
            revoked_first.store.revoke_or_return_existing(revocation_request),
            "newly_revoked",
        )
        self.assert_store_outcome(
            revoked_first.store.admit_or_return_existing(admission_request),
            "revoked",
        )
        self.assert_store_outcome(
            revoked_first.store.revoke_or_return_existing(revocation_request),
            "existing_exact_revocation",
        )

        admitted_first = self.make_conformance_harness()
        created = admitted_first.store.admit_or_return_existing(
            admission_request
        )
        self.assert_store_outcome(created, "newly_admitted")
        self.assert_store_outcome(
            admitted_first.store.revoke_or_return_existing(revocation_request),
            "newly_revoked",
        )
        recovered = admitted_first.store.admit_or_return_existing(
            admission_request
        )
        self.assert_store_outcome(recovered, "existing_exact_admission")
        self.assertEqual(recovered.admission, created.admission)  # type: ignore[attr-defined]

    def test_store_conformance_concurrent_serialization(self) -> None:
        run = make_conformance_run()
        grant = make_conformance_grant(run=run)
        binding = make_conformance_binding(run)
        request = _mint_admission_request(
            CONFORMANCE_DOMAIN_ID,
            grant,
            binding,
            run,
        )
        same = self.make_conformance_harness()
        same_results = self.run_concurrently(
            lambda: same.store.admit_or_return_existing(request),
            lambda: same.store.admit_or_return_existing(request),
        )
        self.assertEqual(  # type: ignore[attr-defined]
            sorted(result.outcome.value for result in same_results),
            ["existing_exact_admission", "newly_admitted"],
        )

        raced = self.make_conformance_harness()
        race_results = self.run_concurrently(
            lambda: raced.store.admit_or_return_existing(request),
            lambda: raced.store.revoke_or_return_existing(
                _mint_revocation_request(CONFORMANCE_DOMAIN_ID, grant)
            ),
        )
        outcomes = sorted(result.outcome.value for result in race_results)
        self.assertIn(  # type: ignore[attr-defined]
            outcomes,
            (
                ["newly_admitted", "newly_revoked"],
                ["newly_revoked", "revoked"],
            ),
        )

    def test_store_conformance_unavailable_storage_fails_closed(self) -> None:
        harness = self.make_conformance_harness()
        run = make_conformance_run()
        grant = make_conformance_grant(run=run)
        binding = make_conformance_binding(run)
        harness.make_storage_unavailable()
        result = harness.store.classify_guarded_history(
            _mint_guarded_history_request(
                CONFORMANCE_DOMAIN_ID,
                grant,
                binding,
            )
        )
        self.assert_store_outcome(result, "storage_unavailable")


__all__ = (
    "AdmissionStoreConformanceHarness",
    "AgentExecutionDispatchAdmissionStoreConformanceMixin",
    "CONFORMANCE_DECISION_TIME",
    "CONFORMANCE_DOMAIN_ID",
)
