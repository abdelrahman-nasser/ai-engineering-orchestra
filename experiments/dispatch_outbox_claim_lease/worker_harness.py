"""Private worker and lifecycle harness for the AIO-054 experiment.

NONCANONICAL EXPERIMENT DISCLAIMER
==================================

This module is disposable experiment support.  It is not an AIO Core contract,
an AIO-049 ownership adapter, a dispatch transport, or invocation authority.
The in-process lifecycle surrogate and the spawned-process raw SQLite probes
are deliberately separate evidence lanes.  Success in either lane does not
establish canonical AIO-049 integration or a multiprocess operational-worker
guarantee.

Only Python's standard library and the adjacent private experiment Store are
used.  Production modules must never import this module.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime
from enum import Enum
import json
import multiprocessing
import os
from pathlib import Path
import queue
import secrets
import shutil
import sqlite3
import stat as stat_module
import subprocess
import sys
import tempfile
import threading
import time
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Protocol, TypeVar


NONCANONICAL_DISCLAIMER = (
    "AIO-054 private experiment evidence only; not canonical AIO-049 "
    "integration, dispatch transport, or invocation authority"
)

LEASE_DURATION_US = 30_000_000
PROBE_HARD_EXIT_CODE = 91
PROBE_TIMEOUT_EXIT_CODE = 92
DEFAULT_PROBE_TIMEOUT_SECONDS = 30.0

T3_APPROVED_PYTHON = Path(
    r"C:\Users\Abdelrahman\AppData\Local\Programs\Python\Python312\python.exe"
)
T3_USER_PROFILE_ROOT = Path(r"C:\Users\Abdelrahman")
T3_LOCAL_APPDATA_ROOT = Path(r"C:\Users\Abdelrahman\AppData\Local")
T3_TEMP_PARENT = Path(r"C:\Users\Abdelrahman\AppData\Local\Temp")
T3_DEV_ROOT = Path(r"D:\Dev")
T3_ROOT_PREFIX = "aio-054-t3-"
T3_MARKER_NAME = ".aio054-t3-owned-root.json"
T3_CHILD_READY_TIMEOUT_SECONDS = 15.0
T3_CHILD_OPERATION_TIMEOUT_SECONDS = 0.25
T3_CHILD_GRACEFUL_STOP_TIMEOUT_SECONDS = 5.0
T3_CHILD_TERMINATE_TIMEOUT_SECONDS = 5.0
T3_CHILD_KILL_TIMEOUT_SECONDS = 5.0
T3_CHILD_SELF_TIMEOUT_SECONDS = 30.0
_T3_OWNED_ROOT_PROOF = object()
_T3_DRIVE_FIXED = 3


class ExperimentHarnessError(RuntimeError):
    """Base error for the private experiment harness."""


class ExecutorCapabilityError(ExperimentHarnessError):
    """The process-local Executor capability is absent, stale, or invalid."""


class LifecycleError(ExperimentHarnessError):
    """The experiment-only lifecycle surrogate cannot prove operation entry."""


class LifecyclePrecheckError(LifecycleError):
    """Authority could not be proven before private Store access."""

    def __init__(self, detail: str, *, terminal: bool = False) -> None:
        super().__init__(detail)
        self.terminal = terminal


class LifecyclePostcheckError(LifecycleError):
    """Authority could not be proven after private Store access."""

    def __init__(self, detail: str, *, terminal: bool) -> None:
        super().__init__(detail)
        self.terminal = terminal


class LifecycleTimeoutError(LifecycleError):
    """A release or fence did not quiesce in its explicit wait bound."""


class ProbeConfigurationError(ExperimentHarnessError):
    """A raw storage-mechanism probe specification is invalid."""


class SyntheticProbeFault(RuntimeError):
    """A non-crashing named experiment fault cut was reached."""


def _deny_copy_or_pickle(kind: str) -> TypeError:
    return TypeError(f"{kind} is process-local, noncopyable, and nonserializable")


class ExecutorCapability:
    """One nonserializable capability for the creating process incarnation.

    The opaque ID is generated internally.  No constructor or coordinator API
    accepts an existing Executor ID, so a restarted process cannot reconstruct
    the former coordinator capability.  This is process encapsulation for the
    experiment, not cryptographic enforcement at the raw SQLite Store boundary.
    """

    __slots__ = ("_executor_instance_id", "_creating_pid", "_proof")

    def __init__(self) -> None:
        self._executor_instance_id = f"executor::{secrets.token_hex(32)}"
        self._creating_pid = os.getpid()
        self._proof = object()

    @property
    def executor_instance_id(self) -> str:
        self._assert_current_process()
        return self._executor_instance_id

    def _assert_current_process(self) -> None:
        if os.getpid() != self._creating_pid or self._proof is None:
            raise ExecutorCapabilityError(
                "Executor capability does not belong to this process incarnation"
            )

    def __copy__(self) -> ExecutorCapability:
        raise _deny_copy_or_pickle(type(self).__name__)

    def __deepcopy__(self, memo: object) -> ExecutorCapability:
        del memo
        raise _deny_copy_or_pickle(type(self).__name__)

    def __reduce__(self) -> object:
        raise _deny_copy_or_pickle(type(self).__name__)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise _deny_copy_or_pickle(type(self).__name__)

    def __repr__(self) -> str:
        return "ExecutorCapability(<process-local opaque identity>)"


def create_executor_capability() -> ExecutorCapability:
    """Create a fresh capability; the caller cannot select or restore its ID."""

    return ExecutorCapability()


class LifecycleState(str, Enum):
    """Private surrogate states; these are not canonical AIO-049 states."""

    RELEASED = "released"
    ACTIVE = "active"
    RELEASING = "releasing"
    LOST = "lost"
    FENCING = "fencing"
    FENCED = "fenced"


LifecycleCheck = Callable[[], object]


def _perform_lifecycle_check(check: LifecycleCheck | None, phase: str) -> None:
    if check is None:
        return
    try:
        checked = check()
    except BaseException as error:
        raise LifecycleError(f"lifecycle {phase} check raised: {error}") from error
    if checked is False:
        raise LifecycleError(f"lifecycle {phase} check rejected authority")


class LifecycleSurrogate:
    """Experiment-only acquire/guard/release/fence lifecycle model.

    Sessions are process-local and distinct across clean reacquisition.  Active
    operation guards may coexist.  Clean release stops new entry and lets
    already-entered operations complete.  Fencing stops new entry immediately,
    makes active post-checks fail, waits for quiescence, and ends permanently in
    ``fenced``.  SQLite, not this surrogate, serializes Store writers.
    """

    def __init__(
        self,
        *,
        precheck: LifecycleCheck | None = None,
        postcheck: LifecycleCheck | None = None,
    ) -> None:
        self._condition = threading.Condition(threading.RLock())
        self._state = LifecycleState.RELEASED
        self._precheck = precheck
        self._postcheck = postcheck
        self._session_serial = 0
        self._current_session_serial: int | None = None
        self._accepting_operations = False
        self._active_operations: set[int] = set()
        self._operation_serial = 0

    @property
    def state(self) -> LifecycleState:
        with self._condition:
            return self._state

    @property
    def active_operation_count(self) -> int:
        with self._condition:
            return len(self._active_operations)

    def acquire(self) -> LifecycleSession:
        """Acquire a distinct active surrogate session after clean release."""

        with self._condition:
            if self._state is LifecycleState.FENCED:
                raise LifecycleError("terminally fenced lifecycle cannot reacquire")
            if self._state is not LifecycleState.RELEASED:
                raise LifecycleError(
                    f"lifecycle cannot acquire while {self._state.value}"
                )
            self._session_serial += 1
            serial = self._session_serial
            self._current_session_serial = serial
            self._accepting_operations = True
            self._state = LifecycleState.ACTIVE
            return LifecycleSession._create(self, serial)

    def recover_after_loss(self, *, timeout: float | None = None) -> None:
        """Model external recovery to a state from which a new session may acquire.

        This is an explicit experiment control action.  It does not revive the
        lost session and does not claim canonical provider recovery.
        """

        with self._condition:
            if self._state is LifecycleState.FENCED:
                raise LifecycleError("terminally fenced lifecycle cannot recover")
            if self._state is not LifecycleState.LOST:
                raise LifecycleError("only a lost lifecycle may be recovered")
            self._wait_for_quiescence_locked(timeout)
            self._current_session_serial = None
            self._state = LifecycleState.RELEASED

    def _enter_operation(self, session_serial: int) -> int:
        try:
            _perform_lifecycle_check(self._precheck, "pre")
        except LifecycleError as error:
            with self._condition:
                terminal = self._state in (
                    LifecycleState.FENCING,
                    LifecycleState.FENCED,
                )
                if (
                    self._current_session_serial == session_serial
                    and self._state is LifecycleState.ACTIVE
                    and self._accepting_operations
                ):
                    self._accepting_operations = False
                    self._state = LifecycleState.LOST
                    self._condition.notify_all()
            raise LifecyclePrecheckError(
                str(error),
                terminal=terminal,
            ) from error

        with self._condition:
            if (
                self._state is not LifecycleState.ACTIVE
                or not self._accepting_operations
                or self._current_session_serial != session_serial
            ):
                terminal = self._state in (
                    LifecycleState.FENCING,
                    LifecycleState.FENCED,
                )
                raise LifecyclePrecheckError(
                    "surrogate session is not active and accepting operations",
                    terminal=terminal,
                )
            self._operation_serial += 1
            token = self._operation_serial
            self._active_operations.add(token)
            return token

    def _complete_operation(
        self,
        session_serial: int,
        operation_token: int,
    ) -> None:
        check_error: LifecycleError | None = None
        try:
            _perform_lifecycle_check(self._postcheck, "post")
        except LifecycleError as error:
            check_error = error

        with self._condition:
            if operation_token not in self._active_operations:
                raise LifecyclePostcheckError(
                    "operation guard is no longer active",
                    terminal=self._state in (
                        LifecycleState.FENCING,
                        LifecycleState.FENCED,
                    ),
                )

            terminal = self._state in (
                LifecycleState.FENCING,
                LifecycleState.FENCED,
            )
            session_current = self._current_session_serial == session_serial
            state_allows_completion = self._state in (
                LifecycleState.ACTIVE,
                LifecycleState.RELEASING,
            )

            if check_error is not None and not terminal:
                self._accepting_operations = False
                self._state = LifecycleState.LOST

            self._active_operations.remove(operation_token)
            self._condition.notify_all()

            if check_error is not None:
                raise LifecyclePostcheckError(
                    str(check_error),
                    terminal=terminal,
                ) from check_error
            if not session_current or not state_allows_completion:
                raise LifecyclePostcheckError(
                    "surrogate authority changed before response completion",
                    terminal=terminal,
                )

    def _abort_operation(self, operation_token: int) -> None:
        with self._condition:
            if operation_token in self._active_operations:
                self._active_operations.remove(operation_token)
                self._condition.notify_all()

    def _release(self, session_serial: int, timeout: float | None) -> None:
        with self._condition:
            self._require_current_session_locked(session_serial)
            if self._state is LifecycleState.ACTIVE:
                self._accepting_operations = False
                self._state = LifecycleState.RELEASING
            elif self._state is not LifecycleState.RELEASING:
                raise LifecycleError(
                    f"session cannot release while {self._state.value}"
                )
            self._wait_for_quiescence_locked(timeout)
            if self._state is not LifecycleState.RELEASING:
                raise LifecycleError(
                    "clean release was superseded by lifecycle loss or fencing"
                )
            self._current_session_serial = None
            self._state = LifecycleState.RELEASED
            self._condition.notify_all()

    def _lose(self, session_serial: int) -> None:
        with self._condition:
            self._require_current_session_locked(session_serial)
            if self._state in (LifecycleState.FENCING, LifecycleState.FENCED):
                raise LifecycleError("terminal fencing dominates ordinary loss")
            self._accepting_operations = False
            self._state = LifecycleState.LOST
            self._condition.notify_all()

    def _fence(self, session_serial: int, timeout: float | None) -> None:
        with self._condition:
            self._require_current_session_locked(session_serial)
            if self._state in (LifecycleState.ACTIVE, LifecycleState.RELEASING):
                self._accepting_operations = False
                self._state = LifecycleState.FENCING
            elif self._state is not LifecycleState.FENCING:
                raise LifecycleError(
                    f"session cannot fence while {self._state.value}"
                )
            self._condition.notify_all()
            self._wait_for_quiescence_locked(timeout)
            self._current_session_serial = None
            self._state = LifecycleState.FENCED
            self._condition.notify_all()

    def _require_current_session_locked(self, session_serial: int) -> None:
        if self._current_session_serial != session_serial:
            raise LifecycleError("surrogate session is stale or no longer current")

    def _wait_for_quiescence_locked(self, timeout: float | None) -> None:
        if timeout is not None and (type(timeout) not in (int, float) or timeout < 0):
            raise TypeError("timeout must be a nonnegative number or None")
        deadline = None if timeout is None else time.monotonic() + float(timeout)
        while self._active_operations:
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise LifecycleTimeoutError(
                    "lifecycle did not quiesce within the requested timeout"
                )
            self._condition.wait(remaining)

    def __copy__(self) -> LifecycleSurrogate:
        raise _deny_copy_or_pickle(type(self).__name__)

    def __deepcopy__(self, memo: object) -> LifecycleSurrogate:
        del memo
        raise _deny_copy_or_pickle(type(self).__name__)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise _deny_copy_or_pickle(type(self).__name__)


_SESSION_FACTORY = object()


class LifecycleSession:
    """One process-local surrogate acquisition; never canonical authority."""

    __slots__ = ("_owner", "_serial", "_creating_pid")

    def __init__(
        self,
        marker: object,
        owner: LifecycleSurrogate,
        serial: int,
    ) -> None:
        if marker is not _SESSION_FACTORY:
            raise TypeError("LifecycleSession is created only by LifecycleSurrogate")
        self._owner = owner
        self._serial = serial
        self._creating_pid = os.getpid()

    @classmethod
    def _create(
        cls,
        owner: LifecycleSurrogate,
        serial: int,
    ) -> LifecycleSession:
        return cls(_SESSION_FACTORY, owner, serial)

    def operation(self) -> LifecycleOperationGuard:
        self._assert_current_process()
        return LifecycleOperationGuard._create(self._owner, self._serial)

    def release(self, *, timeout: float | None = None) -> None:
        self._assert_current_process()
        self._owner._release(self._serial, timeout)

    def lose_authority(self) -> None:
        self._assert_current_process()
        self._owner._lose(self._serial)

    def fence(self, *, timeout: float | None = None) -> None:
        self._assert_current_process()
        self._owner._fence(self._serial, timeout)

    def _assert_current_process(self) -> None:
        if os.getpid() != self._creating_pid:
            raise LifecycleError("surrogate session crossed a process boundary")

    def __copy__(self) -> LifecycleSession:
        raise _deny_copy_or_pickle(type(self).__name__)

    def __deepcopy__(self, memo: object) -> LifecycleSession:
        del memo
        raise _deny_copy_or_pickle(type(self).__name__)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise _deny_copy_or_pickle(type(self).__name__)


_GUARD_FACTORY = object()
T = TypeVar("T")


class LifecycleOperationGuard(AbstractContextManager["LifecycleOperationGuard"]):
    """One complete-operation guard with an atomic final post-check."""

    __slots__ = (
        "_owner",
        "_session_serial",
        "_operation_token",
        "_entered",
        "_finished",
    )

    def __init__(
        self,
        marker: object,
        owner: LifecycleSurrogate,
        session_serial: int,
    ) -> None:
        if marker is not _GUARD_FACTORY:
            raise TypeError(
                "LifecycleOperationGuard is created only by LifecycleSession"
            )
        self._owner = owner
        self._session_serial = session_serial
        self._operation_token: int | None = None
        self._entered = False
        self._finished = False

    @classmethod
    def _create(
        cls,
        owner: LifecycleSurrogate,
        session_serial: int,
    ) -> LifecycleOperationGuard:
        return cls(_GUARD_FACTORY, owner, session_serial)

    def __enter__(self) -> LifecycleOperationGuard:
        if self._entered:
            raise LifecycleError("operation guard cannot be entered twice")
        self._operation_token = self._owner._enter_operation(self._session_serial)
        self._entered = True
        return self

    def complete(self, response: T) -> T:
        """Post-check and close the guard before returning ``response``."""

        if not self._entered or self._finished or self._operation_token is None:
            raise LifecyclePostcheckError(
                "operation guard is not active",
                terminal=False,
            )
        try:
            self._owner._complete_operation(
                self._session_serial,
                self._operation_token,
            )
        finally:
            self._finished = True
        return response

    def __exit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> bool:
        del exception_type, exception, traceback
        if self._entered and not self._finished and self._operation_token is not None:
            self._owner._abort_operation(self._operation_token)
            self._finished = True
        return False

    def __copy__(self) -> LifecycleOperationGuard:
        raise _deny_copy_or_pickle(type(self).__name__)

    def __deepcopy__(self, memo: object) -> LifecycleOperationGuard:
        del memo
        raise _deny_copy_or_pickle(type(self).__name__)

    def __reduce_ex__(self, protocol: int) -> object:
        del protocol
        raise _deny_copy_or_pickle(type(self).__name__)


@dataclass(frozen=True)
class CoordinatedOperationResult:
    """Private response proving only the surrogate lifecycle result."""

    operation: str
    lifecycle_outcome: str
    store_result: object | None
    detail: str
    postchecked: bool
    terminal: bool
    disclaimer: str = NONCANONICAL_DISCLAIMER

    @property
    def outcome(self) -> str:
        if self.lifecycle_outcome != "completed":
            return self.lifecycle_outcome
        candidate = getattr(self.store_result, "outcome", "completed")
        return str(getattr(candidate, "value", candidate))


class _PrivateStore(Protocol):
    def admit(self, request: object) -> object: ...

    def claim(self, request: object) -> object: ...

    def renew(self, request: object) -> object: ...

    def assess_current_claim(self, request: object) -> object: ...


class ExperimentCoordinator:
    """Bind a private Store to one session and one Executor capability.

    Every wrapper obtains a fresh surrogate guard.  Request construction,
    Store access, candidate response construction, and the final post-check all
    occur before that guard is released.
    """

    def __init__(
        self,
        store: _PrivateStore,
        *,
        session: LifecycleSession,
        executor: ExecutorCapability,
    ) -> None:
        if not isinstance(session, LifecycleSession):
            raise TypeError("session must be a LifecycleSession")
        if not isinstance(executor, ExecutorCapability):
            raise TypeError("executor must be an ExecutorCapability")
        executor._assert_current_process()
        self._store = store
        self._session = session
        self._executor = executor

    @property
    def executor_instance_id(self) -> str:
        return self._executor.executor_instance_id

    def admit(self, request: object) -> CoordinatedOperationResult:
        return self._coordinate("admit", lambda: self._store.admit(request))

    def claim(self, claim_id: str) -> CoordinatedOperationResult:
        def invoke() -> object:
            ClaimRequest, _, _ = _store_request_types()
            request = ClaimRequest(
                claim_id=claim_id,
                executor_instance_id=self._executor.executor_instance_id,
            )
            return self._store.claim(request)

        return self._coordinate("claim", invoke)

    def renew(
        self,
        identity: object,
        claim_id: str,
        lease_generation: int,
        renewal_id: str,
    ) -> CoordinatedOperationResult:
        def invoke() -> object:
            _, RenewalRequest, _ = _store_request_types()
            request = RenewalRequest(
                identity=identity,
                claim_id=claim_id,
                executor_instance_id=self._executor.executor_instance_id,
                lease_generation=lease_generation,
                renewal_id=renewal_id,
            )
            return self._store.renew(request)

        return self._coordinate("renew", invoke)

    def assess_current_claim(
        self,
        identity: object,
        claim_id: str,
        lease_generation: int,
    ) -> CoordinatedOperationResult:
        def invoke() -> object:
            _, _, CurrentClaimRequest = _store_request_types()
            request = CurrentClaimRequest(
                identity=identity,
                claim_id=claim_id,
                executor_instance_id=self._executor.executor_instance_id,
                lease_generation=lease_generation,
            )
            return self._store.assess_current_claim(request)

        return self._coordinate("assess_current_claim", invoke)

    def _coordinate(
        self,
        operation: str,
        invoke: Callable[[], object],
    ) -> CoordinatedOperationResult:
        self._executor._assert_current_process()
        guard = self._session.operation()
        store_result: object | None = None
        try:
            with guard:
                store_result = invoke()
                candidate = CoordinatedOperationResult(
                    operation=operation,
                    lifecycle_outcome="completed",
                    store_result=store_result,
                    detail=(
                        "private Store response completed under one lifecycle "
                        "guard and passed its post-check"
                    ),
                    postchecked=True,
                    terminal=False,
                )
                return guard.complete(candidate)
        except LifecyclePrecheckError as error:
            return CoordinatedOperationResult(
                operation=operation,
                lifecycle_outcome=(
                    "terminal_fence" if error.terminal else "lifecycle_unavailable"
                ),
                store_result=None,
                detail=str(error),
                postchecked=False,
                terminal=error.terminal,
            )
        except LifecyclePostcheckError as error:
            return CoordinatedOperationResult(
                operation=operation,
                lifecycle_outcome=(
                    "terminal_fence" if error.terminal else "commit_unknown"
                ),
                # A candidate Store response never escapes a failed guard.
                # Recoverable history must be obtained by exact retry; after
                # terminal fencing it is visible only through the explicitly
                # non-authoritative administrative audit surface.
                store_result=None,
                detail=(
                    f"{error}; candidate Store response withheld after failed "
                    "lifecycle post-check"
                ),
                postchecked=False,
                terminal=error.terminal,
            )


def _store_request_types() -> tuple[type[Any], type[Any], type[Any]]:
    # Lazy import keeps the process-local lifecycle lane independently
    # inspectable while coupling only request construction to the private Store.
    from experiments.dispatch_outbox_claim_lease.store import (
        ClaimRequest,
        CurrentClaimRequest,
        RenewalRequest,
    )

    return ClaimRequest, RenewalRequest, CurrentClaimRequest


@dataclass(frozen=True)
class ProbeClockSpec:
    """Serializable clock input for one raw storage-mechanism process."""

    value: object | None = None
    failure: str | None = None


class _ProbeClock:
    def __init__(self, specification: ProbeClockSpec) -> None:
        self._specification = specification
        self.sample_count = 0

    def now_utc(self) -> object:
        self.sample_count += 1
        if self._specification.failure is not None:
            raise RuntimeError(self._specification.failure)
        if self._specification.value is None:
            raise RuntimeError("raw storage probe clock is intentionally unconfigured")
        return self._specification.value


@dataclass(frozen=True)
class StorageProbeSpec:
    """Serializable input for one raw SQLite storage-mechanism probe."""

    configuration: object
    operation: str
    request: object | None = None
    clock: ProbeClockSpec = ProbeClockSpec()
    fault_point: str | None = None
    hard_exit_at_fault: bool = False

    def __post_init__(self) -> None:
        if type(self.operation) is not str or not self.operation:
            raise ProbeConfigurationError("probe operation must be a nonempty string")
        if self.operation not in _RAW_OPERATION_NAMES:
            raise ProbeConfigurationError(
                f"unsupported raw storage probe operation: {self.operation}"
            )
        if self.fault_point is not None and (
            type(self.fault_point) is not str or not self.fault_point
        ):
            raise ProbeConfigurationError("fault_point must be a nonempty string")
        if (
            self.fault_point is not None
            and self.fault_point
            not in STORAGE_FAULT_POINTS_BY_OPERATION[self.operation]
        ):
            raise ProbeConfigurationError(
                f"fault point {self.fault_point!r} is not supported for "
                f"{self.operation}"
            )
        if type(self.hard_exit_at_fault) is not bool:
            raise ProbeConfigurationError("hard_exit_at_fault must be an exact bool")
        if self.hard_exit_at_fault and self.fault_point is None:
            raise ProbeConfigurationError(
                "hard_exit_at_fault requires an exact supported fault_point"
            )


@dataclass(frozen=True)
class ProbeResult:
    """Serializable raw-storage evidence; never an ownership result."""

    pid: int | None
    exit_code: int | None
    outcome: str
    detail: str
    payload: object | None
    elapsed_seconds: float
    clock_sample_count: int
    hard_crash: bool
    evidence_scope: str = "raw_sqlite_storage_mechanism_only"
    disclaimer: str = NONCANONICAL_DISCLAIMER


@dataclass(frozen=True)
class CoordinatorClaimProbeSpec:
    """Serializable input for one process-local coordinator Claim probe."""

    configuration: object
    claim_id: str
    clock: ProbeClockSpec = ProbeClockSpec()

    def __post_init__(self) -> None:
        if type(self.claim_id) is not str or not self.claim_id:
            raise ProbeConfigurationError("coordinator claim_id must be nonempty")


@dataclass(frozen=True)
class CoordinatorProbeResult:
    """Bounded evidence returned by one fresh child-local coordinator."""

    pid: int | None
    exit_code: int | None
    outcome: str
    detail: str
    payload: object | None
    executor_instance_id: str | None
    elapsed_seconds: float
    clock_sample_count: int
    evidence_scope: str = "process_local_experiment_coordinator_only"
    disclaimer: str = NONCANONICAL_DISCLAIMER


_RAW_OPERATION_NAMES = frozenset(
    (
        "admit",
        "admit_legacy",
        "claim",
        "renew",
        "assess_current_claim",
        "revoke",
        "audit_admission",
        "audit_claim",
        "audit_renewal",
        "migrate_legacy",
        "open",
    )
)


STORAGE_FAULT_POINTS_BY_OPERATION: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "admit": (
            "admission.before_transaction",
            "admission.after_begin",
            "admission.after_admission_insert",
            "admission.after_intent_insert",
            "admission.after_watermark",
            "admission.before_commit",
            "admission.after_commit",
        ),
        "admit_legacy": (
            "legacy_admission.before_transaction",
            "legacy_admission.after_begin",
            "legacy_admission.after_admission_insert",
            "legacy_admission.after_watermark",
            "legacy_admission.before_commit",
            "legacy_admission.after_commit",
        ),
        "claim": (
            "claim.before_transaction",
            "claim.after_begin",
            "claim.after_invariant_validation",
            "claim.after_clock_sample",
            "claim.after_insert",
            "claim.after_watermark",
            "claim.before_commit",
            "claim.after_commit",
        ),
        "renew": (
            "renewal.before_transaction",
            "renewal.after_begin",
            "renewal.after_invariant_validation",
            "renewal.after_clock_sample",
            "renewal.after_insert",
            "renewal.after_watermark",
            "renewal.before_commit",
            "renewal.after_commit",
        ),
        "assess_current_claim": (
            "assessment.before_transaction",
            "assessment.after_begin",
            "assessment.after_clock_sample",
            "assessment.after_watermark",
            "assessment.before_commit",
            "assessment.after_commit",
        ),
        "revoke": (
            "revocation.before_transaction",
            "revocation.after_begin",
            "revocation.after_insert",
            "revocation.before_commit",
            "revocation.after_commit",
        ),
        "migrate_legacy": (
            "migration.before_transaction",
            "migration.after_begin",
            "migration.after_dirty",
            "migration.after_schema",
            "migration.after_legacy_population",
            "migration.after_clean_transition",
            "migration.before_commit",
            "migration.after_commit",
        ),
        "audit_admission": (),
        "audit_claim": (),
        "audit_renewal": (),
        "open": (),
    }
)
SUPPORTED_STORAGE_FAULT_POINTS = frozenset(
    point
    for operation_points in STORAGE_FAULT_POINTS_BY_OPERATION.values()
    for point in operation_points
)


def _primitive_document(value: object) -> object:
    """Convert private result values to queue-safe evidence documents."""

    if value is None or type(value) in (str, int, float, bool):
        return value
    if isinstance(value, Enum):
        return _primitive_document(value.value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return {"bytes_hex": value.hex()}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _primitive_document(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _primitive_document(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_primitive_document(item) for item in value]
    return {"type": type(value).__name__, "repr": repr(value)}


def _outcome_text(result: object) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, Mapping) and "outcome" in result:
        return str(result["outcome"])
    outcome = getattr(result, "outcome", "completed")
    return str(getattr(outcome, "value", outcome))


def _make_probe_fault_hook(
    specification: StorageProbeSpec,
    phase_event: Any,
    release_event: Any,
) -> Callable[[str], None] | None:
    if specification.fault_point is None:
        return None

    def fault_hook(point: str) -> None:
        if point != specification.fault_point:
            return
        if phase_event is not None:
            phase_event.set()
        if release_event is not None and not release_event.wait(
            DEFAULT_PROBE_TIMEOUT_SECONDS
        ):
            os._exit(PROBE_TIMEOUT_EXIT_CODE)
        if specification.hard_exit_at_fault:
            os._exit(PROBE_HARD_EXIT_CODE)
        raise SyntheticProbeFault(f"synthetic raw-storage fault at {point}")

    return fault_hook


def _execute_storage_operation(
    specification: StorageProbeSpec,
    *,
    phase_event: Any = None,
    release_event: Any = None,
) -> tuple[object, int]:
    if specification.operation not in _RAW_OPERATION_NAMES:
        raise ProbeConfigurationError(
            f"unsupported raw storage probe operation: {specification.operation}"
        )

    from experiments.dispatch_outbox_claim_lease.store import (
        DispatchOutboxClaimLeaseStore,
    )

    clock = _ProbeClock(specification.clock)
    fault_hook = _make_probe_fault_hook(
        specification,
        phase_event,
        release_event,
    )
    operation = specification.operation

    if operation == "migrate_legacy":
        result = DispatchOutboxClaimLeaseStore.migrate_legacy(
            specification.configuration,
            fault_hook=fault_hook,
        )
        return result, clock.sample_count

    if operation == "open":
        store = DispatchOutboxClaimLeaseStore(
            specification.configuration,
            clock=clock,
            fault_hook=fault_hook,
        )
        result = {
            "outcome": "opened",
            "profile": store.connection_profile(),
        }
        return result, clock.sample_count

    if operation == "admit_legacy":
        store = DispatchOutboxClaimLeaseStore.open_legacy(
            specification.configuration,
            clock=clock,
            fault_hook=fault_hook,
        )
    elif operation in ("audit_admission", "audit_claim", "audit_renewal"):
        store = DispatchOutboxClaimLeaseStore(
            specification.configuration,
            clock=clock,
            fault_hook=fault_hook,
            allow_fenced=True,
        )
    else:
        store = DispatchOutboxClaimLeaseStore(
            specification.configuration,
            clock=clock,
            fault_hook=fault_hook,
        )

    method = {
        "admit": store.admit,
        "admit_legacy": store.admit_legacy,
        "claim": store.claim,
        "renew": store.renew,
        "assess_current_claim": store.assess_current_claim,
        "revoke": store.revoke,
        "audit_admission": store.audit_admission,
        "audit_claim": store.audit_claim,
        "audit_renewal": store.audit_renewal,
    }[operation]
    result = method(specification.request)
    return result, clock.sample_count


def _storage_probe_child(
    index: int,
    specification: StorageProbeSpec,
    result_queue: Any,
    ready_event: Any,
    start_event: Any,
    phase_event: Any,
    release_event: Any,
) -> None:
    """Spawn target for raw SQLite evidence; not an operational worker."""

    ready_event.set()
    if not start_event.wait(DEFAULT_PROBE_TIMEOUT_SECONDS):
        os._exit(PROBE_TIMEOUT_EXIT_CODE)

    started = time.monotonic()
    try:
        result, sample_count = _execute_storage_operation(
            specification,
            phase_event=phase_event,
            release_event=release_event,
        )
        message = {
            "pid": os.getpid(),
            "outcome": _outcome_text(result),
            "detail": str(getattr(result, "detail", "")),
            "payload": _primitive_document(result),
            "elapsed_seconds": time.monotonic() - started,
            "clock_sample_count": sample_count,
        }
    except BaseException as error:
        message = {
            "pid": os.getpid(),
            "outcome": "probe_exception",
            "detail": f"{type(error).__name__}: {error}",
            "payload": None,
            "elapsed_seconds": time.monotonic() - started,
            "clock_sample_count": 0,
        }
    result_queue.put((index, message))


def _join_probe_process(
    process: multiprocessing.Process,
    result_queue: Any,
    index: int,
    *,
    timeout: float,
    started_at: float,
) -> ProbeResult:
    process.join(timeout)
    if process.is_alive():
        process.kill()
        process.join(5)
        return ProbeResult(
            pid=process.pid,
            exit_code=process.exitcode,
            outcome="probe_timeout",
            detail="spawned raw-storage probe exceeded its explicit timeout",
            payload=None,
            elapsed_seconds=time.monotonic() - started_at,
            clock_sample_count=0,
            hard_crash=False,
        )

    message: dict[str, object] | None = None
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            candidate_index, candidate = result_queue.get(timeout=0.05)
        except queue.Empty:
            if process.exitcode not in (0, None):
                break
            continue
        if candidate_index == index:
            message = candidate
            break
        # A single-process queue never reaches this branch.  Race collection
        # uses its own indexed collector so no foreign result is discarded.
        raise ProbeConfigurationError("probe result queue index mismatch")

    if message is None:
        hard_crash = process.exitcode == PROBE_HARD_EXIT_CODE
        return ProbeResult(
            pid=process.pid,
            exit_code=process.exitcode,
            outcome="hard_crash" if hard_crash else "probe_no_result",
            detail=(
                "named hard-exit cut terminated the raw SQLite process"
                if hard_crash
                else "spawned raw-storage process exited without a result"
            ),
            payload=None,
            elapsed_seconds=time.monotonic() - started_at,
            clock_sample_count=0,
            hard_crash=hard_crash,
        )

    return ProbeResult(
        pid=int(message["pid"]),
        exit_code=process.exitcode,
        outcome=str(message["outcome"]),
        detail=str(message["detail"]),
        payload=message["payload"],
        elapsed_seconds=float(message["elapsed_seconds"]),
        clock_sample_count=int(message["clock_sample_count"]),
        hard_crash=False,
    )


def run_storage_probe(
    specification: StorageProbeSpec,
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> ProbeResult:
    """Run one raw SQLite operation in a fresh spawned process.

    This function supplies storage-mechanism evidence only.  It intentionally
    bypasses the process-local coordinator and must never be described as a
    conforming AIO-049 worker operation.
    """

    if not isinstance(specification, StorageProbeSpec):
        raise TypeError("specification must be a StorageProbeSpec")
    if type(timeout) not in (int, float) or timeout <= 0:
        raise TypeError("timeout must be a positive number")

    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    ready_event = context.Event()
    start_event = context.Event()
    phase_event = context.Event()
    process = context.Process(
        target=_storage_probe_child,
        args=(0, specification, result_queue, ready_event, start_event, phase_event, None),
    )
    process.start()
    try:
        if not ready_event.wait(float(timeout)):
            process.kill()
            process.join(5)
            return ProbeResult(
                pid=process.pid,
                exit_code=process.exitcode,
                outcome="probe_timeout",
                detail="spawned raw-storage probe did not become ready",
                payload=None,
                elapsed_seconds=float(timeout),
                clock_sample_count=0,
                hard_crash=False,
            )
        started_at = time.monotonic()
        start_event.set()
        return _join_probe_process(
            process,
            result_queue,
            0,
            timeout=float(timeout),
            started_at=started_at,
        )
    finally:
        if process.is_alive():
            process.kill()
            process.join(5)
        result_queue.close()
        result_queue.join_thread()


def _coordinator_claim_probe_child(
    specification: CoordinatorClaimProbeSpec,
    result_queue: Any,
    ready_event: Any,
    start_event: Any,
) -> None:
    """Create the capability, session, and coordinator only in this child."""

    ready_event.set()
    if not start_event.wait(DEFAULT_PROBE_TIMEOUT_SECONDS):
        os._exit(PROBE_TIMEOUT_EXIT_CODE)

    started = time.monotonic()
    executor_instance_id: str | None = None
    clock = _ProbeClock(specification.clock)
    try:
        from experiments.dispatch_outbox_claim_lease.store import (
            DispatchOutboxClaimLeaseStore,
        )

        store = DispatchOutboxClaimLeaseStore(
            specification.configuration,
            clock=clock,
        )
        surrogate = LifecycleSurrogate()
        session = surrogate.acquire()
        executor = create_executor_capability()
        executor_instance_id = executor.executor_instance_id
        coordinator = ExperimentCoordinator(
            store,
            session=session,
            executor=executor,
        )
        result = coordinator.claim(specification.claim_id)
        session.release(timeout=5.0)
        message = {
            "pid": os.getpid(),
            "outcome": result.outcome,
            "detail": result.detail,
            "payload": _primitive_document(result),
            "executor_instance_id": executor_instance_id,
            "elapsed_seconds": time.monotonic() - started,
            "clock_sample_count": clock.sample_count,
        }
    except BaseException as error:
        message = {
            "pid": os.getpid(),
            "outcome": "probe_exception",
            "detail": f"{type(error).__name__}: {error}",
            "payload": None,
            "executor_instance_id": executor_instance_id,
            "elapsed_seconds": time.monotonic() - started,
            "clock_sample_count": clock.sample_count,
        }
    result_queue.put(message)


def run_coordinator_claim_probe(
    specification: CoordinatorClaimProbeSpec,
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> CoordinatorProbeResult:
    """Run one Claim through a capability created inside a fresh child.

    The child is owned by this invocation, has no descendants, and is joined
    within the explicit timeout.  This remains private surrogate evidence and
    does not compose into a canonical multiprocess AIO-049 guarantee.
    """

    if not isinstance(specification, CoordinatorClaimProbeSpec):
        raise TypeError("specification must be a CoordinatorClaimProbeSpec")
    if type(timeout) not in (int, float) or timeout <= 0:
        raise TypeError("timeout must be a positive number")

    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    ready_event = context.Event()
    start_event = context.Event()
    process = context.Process(
        target=_coordinator_claim_probe_child,
        args=(specification, result_queue, ready_event, start_event),
    )
    process.start()
    try:
        if not ready_event.wait(float(timeout)):
            process.kill()
            process.join(5.0)
            return CoordinatorProbeResult(
                pid=process.pid,
                exit_code=process.exitcode,
                outcome="probe_timeout",
                detail="coordinator probe did not become ready",
                payload=None,
                executor_instance_id=None,
                elapsed_seconds=float(timeout),
                clock_sample_count=0,
            )

        started_at = time.monotonic()
        start_event.set()
        process.join(float(timeout))
        if process.is_alive():
            process.kill()
            process.join(5.0)
            return CoordinatorProbeResult(
                pid=process.pid,
                exit_code=process.exitcode,
                outcome="probe_timeout",
                detail="coordinator probe exceeded its explicit timeout",
                payload=None,
                executor_instance_id=None,
                elapsed_seconds=time.monotonic() - started_at,
                clock_sample_count=0,
            )

        message: dict[str, object] | None = None
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            try:
                message = result_queue.get(timeout=0.05)
                break
            except queue.Empty:
                if process.exitcode not in (0, None):
                    break
        if message is None:
            return CoordinatorProbeResult(
                pid=process.pid,
                exit_code=process.exitcode,
                outcome="probe_no_result",
                detail="coordinator child exited without a result",
                payload=None,
                executor_instance_id=None,
                elapsed_seconds=time.monotonic() - started_at,
                clock_sample_count=0,
            )
        return CoordinatorProbeResult(
            pid=int(message["pid"]),
            exit_code=process.exitcode,
            outcome=str(message["outcome"]),
            detail=str(message["detail"]),
            payload=message["payload"],
            executor_instance_id=str(message["executor_instance_id"]),
            elapsed_seconds=float(message["elapsed_seconds"]),
            clock_sample_count=int(message["clock_sample_count"]),
        )
    finally:
        if process.is_alive():
            process.kill()
            process.join(5.0)
        result_queue.close()
        result_queue.join_thread()
        process.close()


def race_storage_probes(
    specifications: Iterable[StorageProbeSpec],
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> tuple[ProbeResult, ...]:
    """Synchronize N spawned raw SQLite probes at one start barrier."""

    probes = tuple(specifications)
    if not probes:
        return ()
    if any(not isinstance(probe, StorageProbeSpec) for probe in probes):
        raise TypeError("every race participant must be a StorageProbeSpec")
    if type(timeout) not in (int, float) or timeout <= 0:
        raise TypeError("timeout must be a positive number")

    context = multiprocessing.get_context("spawn")
    result_queue = context.Queue()
    start_event = context.Event()
    ready_events = [context.Event() for _ in probes]
    processes = [
        context.Process(
            target=_storage_probe_child,
            args=(
                index,
                probe,
                result_queue,
                ready_events[index],
                start_event,
                None,
                None,
            ),
        )
        for index, probe in enumerate(probes)
    ]
    for process in processes:
        process.start()

    try:
        deadline = time.monotonic() + float(timeout)
        for ready_event in ready_events:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not ready_event.wait(remaining):
                raise LifecycleTimeoutError(
                    "raw SQLite race participants did not reach the start barrier"
                )
        started_at = time.monotonic()
        start_event.set()

        messages: dict[int, dict[str, object]] = {}
        while len(messages) < len(processes) and time.monotonic() < deadline:
            try:
                index, message = result_queue.get(timeout=0.05)
            except queue.Empty:
                if all(not process.is_alive() for process in processes):
                    break
                continue
            messages[int(index)] = message

        for process in processes:
            remaining = max(0.0, deadline - time.monotonic())
            process.join(remaining)
            if process.is_alive():
                process.kill()
                process.join(5)

        # A multiprocessing.Queue feeder may publish just after the child has
        # exited.  Give already-joined successful children one short bounded
        # drain window so an arrival is not misclassified as no result.
        drain_deadline = time.monotonic() + 0.5
        while len(messages) < len(processes) and time.monotonic() < drain_deadline:
            try:
                index, message = result_queue.get(timeout=0.05)
            except queue.Empty:
                continue
            messages[int(index)] = message

        results: list[ProbeResult] = []
        for index, process in enumerate(processes):
            message = messages.get(index)
            if message is None:
                hard_crash = process.exitcode == PROBE_HARD_EXIT_CODE
                results.append(
                    ProbeResult(
                        pid=process.pid,
                        exit_code=process.exitcode,
                        outcome="hard_crash" if hard_crash else "probe_no_result",
                        detail=(
                            "named hard-exit cut terminated the raw SQLite process"
                            if hard_crash
                            else "race participant exited without a result"
                        ),
                        payload=None,
                        elapsed_seconds=time.monotonic() - started_at,
                        clock_sample_count=0,
                        hard_crash=hard_crash,
                    )
                )
                continue
            results.append(
                ProbeResult(
                    pid=int(message["pid"]),
                    exit_code=process.exitcode,
                    outcome=str(message["outcome"]),
                    detail=str(message["detail"]),
                    payload=message["payload"],
                    elapsed_seconds=float(message["elapsed_seconds"]),
                    clock_sample_count=int(message["clock_sample_count"]),
                    hard_crash=False,
                )
            )
        return tuple(results)
    finally:
        for process in processes:
            if process.is_alive():
                process.kill()
                process.join(5)
        result_queue.close()
        result_queue.join_thread()


def hold_writer(
    configuration: object,
    ready_event: Any,
    release_event: Any,
    result_queue: Any = None,
) -> None:
    """Spawn target holding ``BEGIN IMMEDIATE`` for the focused busy probe."""

    from experiments.dispatch_outbox_claim_lease.store import (
        open_profiled_connection,
    )

    connection: sqlite3.Connection | None = None
    started = time.monotonic()
    try:
        connection = open_profiled_connection(configuration, establish_wal=False)
        connection.execute("BEGIN IMMEDIATE")
        ready_event.set()
        if not release_event.wait(DEFAULT_PROBE_TIMEOUT_SECONDS):
            os._exit(PROBE_TIMEOUT_EXIT_CODE)
        connection.execute("ROLLBACK")
        if result_queue is not None:
            result_queue.put(
                {
                    "pid": os.getpid(),
                    "outcome": "writer_released",
                    "elapsed_seconds": time.monotonic() - started,
                    "scope": "raw_sqlite_storage_mechanism_only",
                }
            )
    except BaseException as error:
        ready_event.set()
        if result_queue is not None:
            result_queue.put(
                {
                    "pid": os.getpid(),
                    "outcome": "writer_exception",
                    "detail": f"{type(error).__name__}: {error}",
                    "elapsed_seconds": time.monotonic() - started,
                    "scope": "raw_sqlite_storage_mechanism_only",
                }
            )
    finally:
        if connection is not None:
            try:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            connection.close()


def run_held_writer_probe(
    configuration: object,
    contender: StorageProbeSpec,
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> tuple[ProbeResult, Mapping[str, object] | None]:
    """Hold one writer while a fresh raw-storage contender measures busy behavior."""

    context = multiprocessing.get_context("spawn")
    ready_event = context.Event()
    release_event = context.Event()
    holder_queue = context.Queue()
    holder = context.Process(
        target=hold_writer,
        args=(configuration, ready_event, release_event, holder_queue),
    )
    holder.start()
    holder_message: Mapping[str, object] | None = None
    try:
        if not ready_event.wait(float(timeout)):
            raise LifecycleTimeoutError("held writer did not become ready")
        contender_result = run_storage_probe(contender, timeout=timeout)
    finally:
        release_event.set()
        holder.join(float(timeout))
        if holder.is_alive():
            holder.kill()
            holder.join(5)
        try:
            holder_message = holder_queue.get_nowait()
        except queue.Empty:
            holder_message = None
        holder_queue.close()
        holder_queue.join_thread()
    return contender_result, holder_message


def run_crash_restart_probe(
    crash: StorageProbeSpec,
    retry: StorageProbeSpec,
    *,
    timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> tuple[ProbeResult, ProbeResult]:
    """Hard-exit one child, then reopen/retry in a distinct fresh process."""

    if not crash.hard_exit_at_fault or crash.fault_point is None:
        raise ProbeConfigurationError(
            "crash probe requires hard_exit_at_fault and a named fault_point"
        )
    first = run_storage_probe(crash, timeout=timeout)
    second = run_storage_probe(retry, timeout=timeout)
    return first, second


@dataclass(frozen=True)
class T3ProcessSafetyResult:
    """Evidence from the amended, experiment-only T3 process-safety target."""

    child_processes_created: int
    child_processes_reaped: int
    child_handles_closed: int
    child_process_ids: tuple[int, ...]
    owned_temp_roots_created: int
    owned_temp_roots_removed: int
    normal_termination_requests: int
    forced_terminations: int
    unrelated_process_affected: bool
    repository_runtime_artifacts_left: bool
    shell_used: bool
    global_process_enumeration_used: bool
    wildcard_termination_used: bool
    network_used: bool
    protected_target_reachable: bool
    owned_root_path: str


@dataclass(frozen=True)
class _OwnedT3Root:
    proof: object
    root: Path
    temp_parent: Path
    repository_root: Path
    nonce: str
    marker_path: Path
    marker_bytes: bytes
    root_identity: tuple[int, int, int]
    marker_identity: tuple[int, int, int]


def _t3_path_is_link_or_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", lambda: False)
    return path.is_symlink() or bool(is_junction())


def _t3_require_fixed_local_ntfs(path: Path) -> None:
    if os.name != "nt":
        raise ExperimentHarnessError("T3 temp storage requires Windows")
    raw = str(path)
    if raw.startswith(("\\\\", "//", "\\\\?\\", "\\\\.\\")):
        raise ExperimentHarnessError("T3 temp storage cannot use a UNC/device path")
    anchor = path.anchor
    if len(anchor) != 3 or anchor[1:] != ":\\":
        raise ExperimentHarnessError("T3 temp storage requires a drive-root anchor")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_drive_type = kernel32.GetDriveTypeW
    get_drive_type.argtypes = (wintypes.LPCWSTR,)
    get_drive_type.restype = wintypes.UINT
    if get_drive_type(anchor) != _T3_DRIVE_FIXED:
        raise ExperimentHarnessError("T3 temp storage is not a fixed local drive")

    get_volume_information = kernel32.GetVolumeInformationW
    get_volume_information.argtypes = (
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPWSTR,
        wintypes.DWORD,
    )
    get_volume_information.restype = wintypes.BOOL
    filesystem_name = ctypes.create_unicode_buffer(32)
    if not get_volume_information(
        anchor,
        None,
        0,
        None,
        None,
        None,
        filesystem_name,
        len(filesystem_name),
    ):
        raise ExperimentHarnessError(
            f"T3 could not verify its local filesystem: {ctypes.WinError(ctypes.get_last_error())}"
        )
    if filesystem_name.value.upper() != "NTFS":
        raise ExperimentHarnessError("T3 temp storage must be local NTFS")


def _t3_require_unredirected_fixed_directory(path: Path) -> Path:
    """Resolve a fixed local directory without first crossing a reparse point."""

    _t3_require_fixed_local_ntfs(path)
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        try:
            metadata = current.lstat()
        except OSError as error:
            raise ExperimentHarnessError(
                "T3 fixed directory component is unavailable"
            ) from error
        attributes = getattr(metadata, "st_file_attributes", 0)
        if attributes & stat_module.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ExperimentHarnessError("T3 fixed directory path is redirected")
        if not stat_module.S_ISDIR(metadata.st_mode):
            raise ExperimentHarnessError(
                "T3 fixed directory component is not a directory"
            )
    resolved = path.resolve(strict=True)
    if resolved != path:
        raise ExperimentHarnessError("T3 fixed directory identity changed")
    return resolved


def _t3_validate_root_boundary(
    root: Path,
    *,
    temp_parent: Path,
    repository_root: Path,
) -> None:
    if not root.is_absolute() or not root.exists() or not root.is_dir():
        raise ExperimentHarnessError("T3 owned root must be an existing directory")
    if root.parent != temp_parent or not root.name.startswith(T3_ROOT_PREFIX):
        raise ExperimentHarnessError("T3 owned root escaped its captured temp parent")
    if _t3_path_is_link_or_junction(root) or _t3_path_is_link_or_junction(
        temp_parent
    ):
        raise ExperimentHarnessError("T3 owned root or temp parent is redirected")
    _t3_require_fixed_local_ntfs(temp_parent)

    exclusions = {
        Path(root.anchor).resolve(strict=False),
        repository_root,
        repository_root.parent,
        temp_parent,
        T3_USER_PROFILE_ROOT,
        T3_LOCAL_APPDATA_ROOT,
        T3_DEV_ROOT,
    }

    if root in exclusions:
        raise ExperimentHarnessError("T3 owned root equals a protected broad root")
    if root.is_relative_to(repository_root) or repository_root.is_relative_to(root):
        raise ExperimentHarnessError("T3 owned root overlaps the repository")


def _cleanup_partial_t3_root(
    root: Path,
    *,
    temp_parent: Path,
    repository_root: Path,
    root_identity: tuple[int, int, int],
) -> None:
    resolved = root.resolve(strict=True)
    if resolved != root.absolute():
        raise ExperimentHarnessError("partial T3 root resolution changed")
    _t3_validate_root_boundary(
        resolved,
        temp_parent=temp_parent,
        repository_root=repository_root,
    )
    root_stat = resolved.stat()
    if (
        root_stat.st_dev,
        root_stat.st_ino,
        root_stat.st_ctime_ns,
    ) != root_identity:
        raise ExperimentHarnessError("partial T3 root identity changed")
    marker_path = resolved / T3_MARKER_NAME
    if marker_path.exists():
        if not marker_path.is_file() or _t3_path_is_link_or_junction(marker_path):
            raise ExperimentHarnessError("partial T3 marker is unsafe to remove")
        marker_path.unlink()
    resolved.rmdir()
    if resolved.exists():
        raise ExperimentHarnessError("partial T3 root remained after cleanup")


def _create_owned_t3_root() -> _OwnedT3Root:
    repository_root = Path(__file__).resolve(strict=True).parents[2]
    temp_parent = _t3_require_unredirected_fixed_directory(T3_TEMP_PARENT)
    if temp_parent.is_relative_to(repository_root) or repository_root.is_relative_to(
        temp_parent
    ):
        raise ExperimentHarnessError("T3 fixed temp parent overlaps the repository")
    _t3_require_fixed_local_ntfs(temp_parent)
    raw_root = Path(tempfile.mkdtemp(prefix=T3_ROOT_PREFIX, dir=temp_parent))
    raw_identity: tuple[int, int, int] | None = None
    try:
        raw_stat = raw_root.stat()
        raw_identity = (
            raw_stat.st_dev,
            raw_stat.st_ino,
            raw_stat.st_ctime_ns,
        )
        root = raw_root.resolve(strict=True)
        if root != raw_root.absolute():
            raise ExperimentHarnessError("T3 root resolution changed after creation")
        _t3_validate_root_boundary(
            root,
            temp_parent=temp_parent,
            repository_root=repository_root,
        )
        nonce = secrets.token_hex(32)
        marker_path = root / T3_MARKER_NAME
        marker_bytes = (
            json.dumps(
                {
                    "nonce": nonce,
                    "owner_pid": os.getpid(),
                    "purpose": "AIO-054 amended T3 owned temporary root",
                    "root": str(root),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        with marker_path.open("xb") as marker:
            marker.write(marker_bytes)
            marker.flush()
            os.fsync(marker.fileno())
        root_stat = root.stat()
        marker_stat = marker_path.stat()
        return _OwnedT3Root(
            proof=_T3_OWNED_ROOT_PROOF,
            root=root,
            temp_parent=temp_parent,
            repository_root=repository_root,
            nonce=nonce,
            marker_path=marker_path,
            marker_bytes=marker_bytes,
            root_identity=(
                root_stat.st_dev,
                root_stat.st_ino,
                root_stat.st_ctime_ns,
            ),
            marker_identity=(
                marker_stat.st_dev,
                marker_stat.st_ino,
                marker_stat.st_ctime_ns,
            ),
        )
    except BaseException:
        try:
            if raw_identity is None:
                if (
                    raw_root.parent != temp_parent
                    or not raw_root.name.startswith(T3_ROOT_PREFIX)
                    or _t3_path_is_link_or_junction(raw_root)
                ):
                    raise ExperimentHarnessError(
                        "unidentified partial T3 root is unsafe to remove"
                    )
                raw_root.rmdir()
            else:
                _cleanup_partial_t3_root(
                    raw_root,
                    temp_parent=temp_parent,
                    repository_root=repository_root,
                    root_identity=raw_identity,
                )
        except BaseException as cleanup_error:
            raise ExperimentHarnessError(
                "T3 partial root initialization could not be cleaned safely"
            ) from cleanup_error
        raise


def _remove_owned_t3_root(owned: _OwnedT3Root) -> None:
    if owned.proof is not _T3_OWNED_ROOT_PROOF:
        raise ExperimentHarnessError("T3 cleanup proof is not process-owned")
    root = owned.root.resolve(strict=True)
    _t3_validate_root_boundary(
        root,
        temp_parent=owned.temp_parent,
        repository_root=owned.repository_root,
    )
    root_stat = root.stat()
    if (
        root_stat.st_dev,
        root_stat.st_ino,
        root_stat.st_ctime_ns,
    ) != owned.root_identity:
        raise ExperimentHarnessError("T3 owned root identity changed before cleanup")
    if (
        not owned.marker_path.is_file()
        or _t3_path_is_link_or_junction(owned.marker_path)
    ):
        raise ExperimentHarnessError("T3 ownership marker is absent or redirected")
    marker_stat = owned.marker_path.stat()
    if (
        marker_stat.st_dev,
        marker_stat.st_ino,
        marker_stat.st_ctime_ns,
    ) != owned.marker_identity:
        raise ExperimentHarnessError("T3 ownership marker identity changed")
    if owned.marker_path.read_bytes() != owned.marker_bytes:
        raise ExperimentHarnessError("T3 ownership marker content changed")
    shutil.rmtree(root)
    if root.exists():
        raise ExperimentHarnessError("T3 owned root remained after bounded cleanup")


def _t3_minimal_child_environment(owned: _OwnedT3Root) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name in ("SystemRoot", "WINDIR", "ComSpec", "SystemDrive"):
        value = os.environ.get(name)
        if value:
            environment[name] = value
    environment["TEMP"] = str(owned.root)
    environment["TMP"] = str(owned.root)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _t3_read_bounded_log(path: Path) -> str:
    with path.open("rb") as stream:
        data = stream.read(65_537)
    if len(data) > 65_536:
        data = data[:65_536] + b"\n[truncated]"
    return data.decode("utf-8", errors="replace")


def _t3_close_reaped_process_handle(process: subprocess.Popen[bytes]) -> bool:
    if process.returncode is None:
        raise ExperimentHarnessError("T3 child handle cannot close before reap")
    handle = getattr(process, "_handle", None)
    close = getattr(handle, "Close", None)
    if not callable(close):
        raise ExperimentHarnessError(
            "approved Windows Python exposes no closable child process handle"
        )
    close()
    return True


def _t3_request_stop_and_reap(
    process: subprocess.Popen[bytes],
    owned: _OwnedT3Root,
    mode: str,
) -> tuple[bool, bool]:
    """Stop one exact owned child; return (normal_requested, forced)."""

    errors: list[str] = []
    stop_request_error: Exception | None = None
    normal_requested = False
    try:
        if process.poll() is not None:
            return False, False
    except OSError as error:
        errors.append(f"initial poll: {error}")
    stop_path = owned.root / f"{mode}.stop-request"
    stop_bytes = (owned.nonce + "\n").encode("ascii")
    try:
        if stop_path.exists():
            if (
                not stop_path.is_file()
                or _t3_path_is_link_or_junction(stop_path)
                or stop_path.read_bytes() != stop_bytes
            ):
                raise ExperimentHarnessError("T3 child stop request identity changed")
        else:
            with stop_path.open("xb") as stop_file:
                stop_file.write(stop_bytes)
                stop_file.flush()
                os.fsync(stop_file.fileno())
        normal_requested = True
    except (OSError, ExperimentHarnessError) as error:
        stop_request_error = error
        errors.append(f"stop request: {error}")
    try:
        process.wait(timeout=T3_CHILD_GRACEFUL_STOP_TIMEOUT_SECONDS)
        if stop_request_error is not None:
            raise ExperimentHarnessError(
                "T3 stop request failed, but the exact owned child was reaped"
            ) from stop_request_error
        return normal_requested, False
    except subprocess.TimeoutExpired:
        pass
    except OSError as error:
        errors.append(f"graceful wait: {error}")

    forced = True
    try:
        if process.poll() is None:
            process.terminate()
    except OSError as error:
        errors.append(f"terminate: {error}")
    try:
        process.wait(timeout=T3_CHILD_TERMINATE_TIMEOUT_SECONDS)
        if stop_request_error is not None:
            raise ExperimentHarnessError(
                "T3 stop request failed, but the exact owned child was reaped"
            ) from stop_request_error
        return normal_requested, forced
    except subprocess.TimeoutExpired:
        pass
    except OSError as error:
        errors.append(f"post-terminate wait: {error}")

    try:
        if process.poll() is None:
            process.kill()
    except OSError as error:
        errors.append(f"kill: {error}")
    try:
        process.wait(timeout=T3_CHILD_KILL_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as error:
        errors.append(f"final wait: {error}")
        raise ExperimentHarnessError(
            "exact owned T3 child could not be killed and reaped: "
            + "; ".join(errors)
        ) from error
    if stop_request_error is not None:
        raise ExperimentHarnessError(
            "T3 stop request failed, but the exact owned child was reaped"
        ) from stop_request_error
    return normal_requested, forced


def _run_owned_t3_child(
    owned: _OwnedT3Root,
    mode: str,
    created_pids: list[int],
    reaped_pids: list[int],
    closed_handle_pids: list[int],
) -> tuple[int, int, int]:
    if mode not in {"cooperative", "stubborn"}:
        raise ExperimentHarnessError("unsupported amended T3 child mode")
    approved_python = T3_APPROVED_PYTHON.resolve(strict=True)
    if approved_python != T3_APPROVED_PYTHON:
        raise ExperimentHarnessError("approved T3 Python path resolved differently")
    if os.name != "nt" or sys.version_info[:2] != (3, 12):
        raise ExperimentHarnessError("amended T3 requires approved Windows Python 3.12")
    if Path(sys.executable).resolve(strict=True) != approved_python:
        raise ExperimentHarnessError("amended T3 parent is not approved Python 3.12")
    worker_path = Path(__file__).resolve(strict=True)
    command = (
        str(approved_python),
        "-E",
        "-s",
        "-B",
        str(worker_path),
        "--aio-054-t3-child",
        mode,
        str(owned.root),
        owned.nonce,
        str(os.getpid()),
    )
    stdout_path = owned.root / f"{mode}.stdout.log"
    stderr_path = owned.root / f"{mode}.stderr.log"
    process: subprocess.Popen[bytes] | None = None
    normal_requests = 0
    forced_terminations = 0
    with stdout_path.open("xb") as stdout_file, stderr_path.open("xb") as stderr_file:
        try:
            process = subprocess.Popen(
                command,
                cwd=owned.root,
                env=_t3_minimal_child_environment(owned),
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                shell=False,
                close_fds=True,
            )
            created_pids.append(process.pid)
            handle = getattr(process, "_handle", None)
            if not callable(getattr(handle, "Close", None)):
                requested, forced = _t3_request_stop_and_reap(
                    process,
                    owned,
                    mode,
                )
                normal_requests += int(requested)
                forced_terminations += int(forced)
                raise ExperimentHarnessError(
                    "approved Python child handle cannot be closed explicitly"
                )
            ready_path = owned.root / f"{mode}.ready"
            ready_deadline = time.monotonic() + T3_CHILD_READY_TIMEOUT_SECONDS
            while not ready_path.is_file():
                if process.poll() is not None:
                    raise ExperimentHarnessError(
                        f"{mode} T3 child exited before ready"
                    )
                if time.monotonic() >= ready_deadline:
                    requested, forced = _t3_request_stop_and_reap(
                        process,
                        owned,
                        mode,
                    )
                    normal_requests += int(requested)
                    forced_terminations += int(forced)
                    raise ExperimentHarnessError(
                        f"{mode} T3 child did not become ready"
                    )
                time.sleep(0.01)
            try:
                process.wait(timeout=T3_CHILD_OPERATION_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                requested, forced = _t3_request_stop_and_reap(
                    process,
                    owned,
                    mode,
                )
                normal_requests += int(requested)
                forced_terminations += int(forced)
            else:
                raise ExperimentHarnessError(
                    f"{mode} T3 child did not exercise bounded stop"
                )
            if mode == "cooperative":
                if process.returncode != 0 or forced_terminations != 0:
                    raise ExperimentHarnessError(
                        "cooperative T3 child did not stop normally"
                    )
            elif not forced_terminations:
                raise ExperimentHarnessError(
                    "stubborn T3 child did not exercise exact-handle termination"
                )
        finally:
            if process is not None:
                reap_error: BaseException | None = None
                if process.returncode is None:
                    try:
                        requested, forced = _t3_request_stop_and_reap(
                            process,
                            owned,
                            mode,
                        )
                        normal_requests += int(requested)
                        forced_terminations += int(forced)
                    except BaseException as error:
                        reap_error = error
                if process.returncode is not None:
                    if process.pid not in reaped_pids:
                        reaped_pids.append(process.pid)
                    if _t3_close_reaped_process_handle(process):
                        closed_handle_pids.append(process.pid)
                if reap_error is not None:
                    raise reap_error
    if process is None:
        raise ExperimentHarnessError("T3 child was not created")
    if mode == "cooperative" and process.returncode != 0:
        detail = _t3_read_bounded_log(stderr_path)
        raise ExperimentHarnessError(f"T3 child failed: {detail}")
    return process.pid, normal_requests, forced_terminations


def _verify_t3_child_root(
    root_text: str,
    nonce: str,
    parent_pid_text: str,
) -> Path:
    if len(nonce) != 64:
        raise ExperimentHarnessError("T3 child nonce has the wrong length")
    try:
        int(nonce, 16)
    except ValueError as error:
        raise ExperimentHarnessError("T3 child nonce is malformed") from error
    try:
        expected_parent_pid = int(parent_pid_text)
    except ValueError as error:
        raise ExperimentHarnessError("T3 child parent PID is malformed") from error
    if expected_parent_pid <= 0:
        raise ExperimentHarnessError("T3 child parent PID is invalid")
    supplied = Path(root_text)
    if not supplied.is_absolute():
        raise ExperimentHarnessError("T3 child root must be absolute")
    root = supplied.resolve(strict=True)
    if root != supplied or not root.name.startswith(T3_ROOT_PREFIX):
        raise ExperimentHarnessError("T3 child root identity is unexpected")
    if _t3_path_is_link_or_junction(root):
        raise ExperimentHarnessError("T3 child root is redirected")
    repository_root = Path(__file__).resolve(strict=True).parents[2]
    _t3_validate_root_boundary(
        root,
        temp_parent=root.parent,
        repository_root=repository_root,
    )
    marker_path = root / T3_MARKER_NAME
    marker = json.loads(marker_path.read_text(encoding="utf-8"))
    if marker != {
        "nonce": nonce,
        "owner_pid": marker.get("owner_pid"),
        "purpose": "AIO-054 amended T3 owned temporary root",
        "root": str(root),
    }:
        raise ExperimentHarnessError("T3 child ownership marker is invalid")
    if (
        type(marker["owner_pid"]) is not int
        or marker["owner_pid"] <= 0
        or marker["owner_pid"] != expected_parent_pid
    ):
        raise ExperimentHarnessError("T3 child ownership marker PID is invalid")
    return root


def _run_t3_child_entry(
    mode: str,
    root_text: str,
    nonce: str,
    parent_pid_text: str,
) -> int:
    if mode not in {"cooperative", "stubborn"}:
        raise ExperimentHarnessError("T3 child mode is unsupported")
    denied_events = {
        "os.posix_spawn",
        "os.spawn",
        "os.startfile",
        "os.system",
        "subprocess.Popen",
    }

    def deny_external_effects(event: str, arguments: tuple[object, ...]) -> None:
        del arguments
        if event.startswith("socket.") or event in denied_events:
            raise ExperimentHarnessError(
                f"T3 child denied external-effect audit event: {event}"
            )

    sys.addaudithook(deny_external_effects)
    root = _verify_t3_child_root(root_text, nonce, parent_pid_text)
    database_path = root / f"{mode}.sqlite3"
    connection = sqlite3.connect(database_path, timeout=2.0, isolation_level=None)
    try:
        if connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
            raise ExperimentHarnessError("T3 child could not enable WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute(
            "CREATE TABLE t3_child_evidence (mode TEXT PRIMARY KEY, pid INTEGER) STRICT"
        )
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "INSERT INTO t3_child_evidence (mode, pid) VALUES (?, ?)",
            (mode, os.getpid()),
        )
        connection.execute("COMMIT")
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        connection.close()
    result_path = root / f"{mode}.result.json"
    with result_path.open("x", encoding="utf-8", newline="\n") as result_file:
        json.dump(
            {"mode": mode, "pid": os.getpid(), "scope": "aio-054-t3-only"},
            result_file,
            sort_keys=True,
            separators=(",", ":"),
        )
        result_file.write("\n")
        result_file.flush()
        os.fsync(result_file.fileno())
    ready_path = root / f"{mode}.ready"
    ready_path.write_text(nonce + "\n", encoding="ascii", newline="\n")
    stop_path = root / f"{mode}.stop-request"
    deadline = time.monotonic() + T3_CHILD_SELF_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if mode == "cooperative" and stop_path.is_file():
            if stop_path.read_text(encoding="ascii") != nonce + "\n":
                raise ExperimentHarnessError("T3 child stop request is invalid")
            return 0
        time.sleep(0.01)
    return 75


def run_t3_child_process_safety_validation() -> T3ProcessSafetyResult:
    """Run the amended T3 target with only internally owned bounded resources."""

    owned = _create_owned_t3_root()
    created_pids: list[int] = []
    reaped_pids: list[int] = []
    closed_handle_pids: list[int] = []
    normal_requests = 0
    forced_terminations = 0
    removed = 0
    try:
        for mode in ("cooperative", "stubborn"):
            _, requested, forced = _run_owned_t3_child(
                owned,
                mode,
                created_pids,
                reaped_pids,
                closed_handle_pids,
            )
            normal_requests += requested
            forced_terminations += forced
    finally:
        if (
            len(reaped_pids) != len(created_pids)
            or len(closed_handle_pids) != len(created_pids)
        ):
            raise ExperimentHarnessError(
                "T3 cannot clean its root before every child is reaped and closed"
            )
        _remove_owned_t3_root(owned)
        removed = 1
    return T3ProcessSafetyResult(
        child_processes_created=len(created_pids),
        child_processes_reaped=len(reaped_pids),
        child_handles_closed=len(closed_handle_pids),
        child_process_ids=tuple(created_pids),
        owned_temp_roots_created=1,
        owned_temp_roots_removed=removed,
        normal_termination_requests=normal_requests,
        forced_terminations=forced_terminations,
        unrelated_process_affected=False,
        repository_runtime_artifacts_left=False,
        shell_used=False,
        global_process_enumeration_used=False,
        wildcard_termination_used=False,
        network_used=False,
        protected_target_reachable=False,
        owned_root_path=str(owned.root),
    )


def _t3_command_line_entry() -> int:
    if len(sys.argv) != 6 or sys.argv[1] != "--aio-054-t3-child":
        return 64
    try:
        return _run_t3_child_entry(
            sys.argv[2],
            sys.argv[3],
            sys.argv[4],
            sys.argv[5],
        )
    except BaseException as error:
        print(f"AIO-054 T3 child error: {type(error).__name__}: {error}", file=sys.stderr)
        return 74


__all__ = (
    "CoordinatedOperationResult",
    "CoordinatorClaimProbeSpec",
    "CoordinatorProbeResult",
    "DEFAULT_PROBE_TIMEOUT_SECONDS",
    "ExecutorCapability",
    "ExecutorCapabilityError",
    "ExperimentCoordinator",
    "ExperimentHarnessError",
    "LEASE_DURATION_US",
    "LifecycleError",
    "LifecycleOperationGuard",
    "LifecyclePostcheckError",
    "LifecyclePrecheckError",
    "LifecycleSession",
    "LifecycleState",
    "LifecycleSurrogate",
    "LifecycleTimeoutError",
    "NONCANONICAL_DISCLAIMER",
    "PROBE_HARD_EXIT_CODE",
    "PROBE_TIMEOUT_EXIT_CODE",
    "ProbeClockSpec",
    "ProbeConfigurationError",
    "ProbeResult",
    "STORAGE_FAULT_POINTS_BY_OPERATION",
    "SUPPORTED_STORAGE_FAULT_POINTS",
    "StorageProbeSpec",
    "SyntheticProbeFault",
    "T3ProcessSafetyResult",
    "create_executor_capability",
    "hold_writer",
    "race_storage_probes",
    "run_crash_restart_probe",
    "run_coordinator_claim_probe",
    "run_held_writer_probe",
    "run_storage_probe",
    "run_t3_child_process_safety_validation",
)


if __name__ == "__main__":
    raise SystemExit(_t3_command_line_entry())
