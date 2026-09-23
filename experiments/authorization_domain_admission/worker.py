"""Spawn-safe worker helpers for the private AIO-046 experiment."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any

from experiments.authorization_domain_admission.sqlite_store import (
    AdmissionResult,
    FixedAuthorityClock,
    RevocationResult,
    SQLiteAuthorizationDomainLedger,
    SyntheticFreshPrerequisiteSource,
    SyntheticTrustCoordinator,
    TrustedLedgerConfiguration,
    admission_record_document,
    binding_from_document,
    grant_from_document,
    revocation_record_document,
)


def _clock_from_spec(specification: dict[str, object]) -> FixedAuthorityClock:
    failure = specification.get("clock_failure")
    if failure is not None:
        return FixedAuthorityClock(failure=str(failure))
    supplied = specification.get("clock_instant")
    if type(supplied) is not str:
        return FixedAuthorityClock(failure="worker clock instant is missing")
    try:
        instant = datetime.fromisoformat(supplied.replace("Z", "+00:00"))
    except ValueError:
        return FixedAuthorityClock(failure="worker clock instant is invalid")
    return FixedAuthorityClock(instant)


def _admission_result_document(
    result: AdmissionResult,
    *,
    pid: int,
    fresh_collection_count: int,
    clock_sample_count: int,
) -> dict[str, object]:
    return {
        "pid": pid,
        "outcome": result.outcome,
        "detail": result.detail,
        "retryable": result.retryable,
        "indeterminate": result.indeterminate,
        "record": (
            admission_record_document(result.record)
            if result.record is not None
            else None
        ),
        "fresh_collection_count": fresh_collection_count,
        "clock_sample_count": clock_sample_count,
    }


def _revocation_result_document(
    result: RevocationResult,
    *,
    pid: int,
    clock_sample_count: int,
) -> dict[str, object]:
    return {
        "pid": pid,
        "outcome": result.outcome,
        "detail": result.detail,
        "retryable": result.retryable,
        "indeterminate": result.indeterminate,
        "record": (
            revocation_record_document(result.record)
            if result.record is not None
            else None
        ),
        "fresh_collection_count": 0,
        "clock_sample_count": clock_sample_count,
    }


def run_worker(
    specification: dict[str, object],
    result_queue: Any,
    *,
    ready_event: Any = None,
    start_event: Any = None,
    phase_event: Any = None,
    release_event: Any = None,
) -> None:
    """Run one admission or revocation in a genuinely spawned process.

    Only primitive specification data and synchronization handles cross the
    process boundary.  Every worker creates its own trust stub, clock, ledger
    object, and SQLite connection after process start.
    """

    configuration = TrustedLedgerConfiguration(
        str(specification["authorization_domain_id"]),
        Path(str(specification["database_path"])),
        int(specification.get("busy_timeout_ms", 5_000)),
    )
    clock = _clock_from_spec(specification)
    trust = SyntheticTrustCoordinator()
    ledger = SQLiteAuthorizationDomainLedger(
        configuration,
        authority_clock=clock,
        trust_coordinator=trust,
    )
    grant = grant_from_document(specification["grant"])
    operation = specification.get("operation", "admit")
    expected_domain = str(
        specification.get(
            "expected_authorization_domain_id",
            configuration.authorization_domain_id,
        )
    )
    fault_point = specification.get("fault_point")
    pause_point = specification.get("pause_point")

    def fault_hook(point: str) -> None:
        if point == pause_point:
            if phase_event is not None:
                phase_event.set()
            if release_event is None or not release_event.wait(30):
                os._exit(92)
        if point == fault_point:
            if phase_event is not None:
                phase_event.set()
            os._exit(91)

    if ready_event is not None:
        ready_event.set()
    if start_event is not None and not start_event.wait(30):
        result_queue.put(
            {
                "pid": os.getpid(),
                "outcome": "worker_timeout",
                "detail": "start event was not released",
            }
        )
        return

    if operation == "admit":
        binding = binding_from_document(specification["binding"])
        fresh_source = SyntheticFreshPrerequisiteSource(
            execution_mode=str(
                specification.get(
                    "fresh_execution_mode",
                    grant.run.contract.execution_mode,
                )
            ),
            failure=(
                str(specification["fresh_failure"])
                if specification.get("fresh_failure") is not None
                else None
            ),
        )
        request = trust.trusted_admission(
            grant,
            binding,
            expected_authorization_domain_id=expected_domain,
        )
        result = ledger.admit_or_return_existing(
            request,
            fresh_source=fresh_source,
            fault_hook=(
                fault_hook
                if fault_point is not None or pause_point is not None
                else None
            ),
        )
        result_queue.put(
            _admission_result_document(
                result,
                pid=os.getpid(),
                fresh_collection_count=fresh_source.collection_count,
                clock_sample_count=clock.sample_count,
            )
        )
        return

    if operation == "revoke":
        request = trust.trusted_revocation(
            grant,
            expected_authorization_domain_id=expected_domain,
        )
        result = ledger.revoke(
            request,
            fault_hook=(
                fault_hook
                if fault_point is not None or pause_point is not None
                else None
            ),
        )
        result_queue.put(
            _revocation_result_document(
                result,
                pid=os.getpid(),
                clock_sample_count=clock.sample_count,
            )
        )
        return

    result_queue.put(
        {
            "pid": os.getpid(),
            "outcome": "worker_invalid_operation",
            "detail": str(operation),
        }
    )


def lock_holder_worker(
    specification: dict[str, object],
    ready_event: Any,
    release_event: Any,
) -> None:
    """Hold one writer lock for the focused busy-timeout experiment."""

    import sqlite3

    path = Path(str(specification["database_path"]))
    uri = path.as_uri() + "?mode=rw"
    connection = sqlite3.connect(
        uri,
        uri=True,
        isolation_level=None,
        timeout=5,
    )
    try:
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("BEGIN IMMEDIATE")
        ready_event.set()
        if not release_event.wait(30):
            os._exit(93)
        connection.execute("ROLLBACK")
    finally:
        connection.close()


__all__ = ["lock_holder_worker", "run_worker"]
