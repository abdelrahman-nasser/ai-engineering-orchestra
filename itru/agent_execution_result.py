"""Immutable, process-local terminal evidence from original controlled invocation.

There is no public Result constructor, serializer, persistence or execution API.
Structural mapping is separate from original-frame production provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from threading import get_ident
from typing import TYPE_CHECKING
from weakref import ref

from itru.authorization_domain_ownership import AuthorizationDomainIdentity
from itru.agent_operation_tool_binding import (
    AgentOperationToolBinding, validate_agent_operation_tool_binding,
)

if TYPE_CHECKING:
    from itru._execution_entry_and_controlled_invocation import _ExecutionEntry

__all__ = (
    "AgentExecutionResult", "AgentExecutionResultDiagnostic",
    "RepositoryFileReadResultPayload",
)

_BEFORE_CODES = frozenset((
    "adapter_unavailable", "containment_rejected", "resource_missing",
    "resource_changed", "size_limit_exceeded", "read_failure", "guard_lost",
    "ownership_lost",
))
_AMBIGUOUS_CODES = (_BEFORE_CODES - {"guard_lost", "ownership_lost"}) | {"effect_ambiguous"}
_PRODUCTION_SEAL = object()  # Private membership, never a serialized assertion.


class _ResultIntegrityError(RuntimeError):
    def __init__(self):
        super().__init__("canonical Result integrity failure")


@dataclass(frozen=True, slots=True)
class RepositoryFileReadResultPayload:
    data: bytes
    byte_count: int

    def __post_init__(self):
        if (type(self.data) is not bytes or type(self.byte_count) is not int
                or not 0 <= self.byte_count <= 65536
                or self.byte_count != len(self.data)):
            raise ValueError("invalid bounded Result payload")

    def __getstate__(self):
        raise TypeError("Result payload has no serialized format")

    def __setstate__(self, state):
        raise TypeError("Result payload cannot be restored")


@dataclass(frozen=True, slots=True)
class AgentExecutionResultDiagnostic:
    code: str

    def __post_init__(self):
        if type(self.code) is not str or self.code not in _BEFORE_CODES | _AMBIGUOUS_CODES:
            raise ValueError("invalid closed Result diagnostic")

    def __getstate__(self):
        raise TypeError("Result diagnostic has no serialized format")

    def __setstate__(self, state):
        raise TypeError("Result diagnostic cannot be restored")


class _ProducedMembership:
    __slots__ = ("_production", "__weakref__")


@dataclass(frozen=True, slots=True, init=False, repr=False)
class AgentExecutionResult(_ProducedMembership):
    ledger_identity: AuthorizationDomainIdentity
    execution_entry: _ExecutionEntry
    tool_binding: AgentOperationToolBinding
    outcome: str
    payload: RepositoryFileReadResultPayload | None
    diagnostic: AgentExecutionResultDiagnostic | None

    def __new__(cls, *args, **kwargs):
        raise TypeError("Result requires original controlled invocation")

    def __init_subclass__(cls, **kwargs):
        raise TypeError("Result cannot be subclassed")

    def __copy__(self):
        raise TypeError("Result cannot be reconstructed")

    def __deepcopy__(self, memo):
        raise TypeError("Result cannot be reconstructed")

    def __reduce__(self):
        raise TypeError("Result has no serialized format")

    def __reduce_ex__(self, protocol):
        raise TypeError("Result has no serialized format")

    def __getstate__(self):
        raise TypeError("Result has no serialized format")

    def __setstate__(self, state):
        raise TypeError("Result cannot be restored")

    def __repr__(self):
        return f"AgentExecutionResult(outcome={self.outcome!r})"

    @property
    def identity(self):
        return (self.ledger_identity.ledger_instance_id, *self.execution_entry.identity)


def _result_references(value):
    return (value.ledger_identity, value.execution_entry, value.tool_binding,
            value.outcome, value.payload, value.diagnostic)


def _result_leaves(value):
    """Private in-memory membership comparison, never a transport projection."""
    ledger, entry, binding, outcome, payload, diagnostic = _result_references(value)
    run, contract = binding.run, binding.run.contract
    leaves = (
        ledger.authorization_domain_id, ledger.ledger_instance_id, ledger.domain_generation,
        type(entry.identity), *entry.identity, entry.claim_id, entry.executor_instance_id, entry.lease_generation,
        entry.entry_time, entry.entry_time_key, binding.tool_id, run.run_id,
        contract.task_id, contract.workflow_id, contract.stage_id, contract.role_id,
        contract.actor_id, contract.runtime_option_id, contract.option_id,
        contract.environment_id, contract.operation_id, contract.resource, contract.execution_mode,
        outcome, None if payload is None else payload.data,
        None if payload is None else payload.byte_count,
        None if diagnostic is None else diagnostic.code,
    )
    return tuple((type(leaf), leaf) for leaf in leaves)


def _validate_terminal_values(outcome, payload, diagnostic):
    if type(outcome) is not str:
        raise _ResultIntegrityError()
    if outcome == "succeeded":
        if type(payload) is not RepositoryFileReadResultPayload or diagnostic is not None:
            raise _ResultIntegrityError()
        payload.__post_init__()
    elif outcome in ("failed_before_effect", "effect_ambiguous"):
        codes = _BEFORE_CODES if outcome == "failed_before_effect" else _AMBIGUOUS_CODES
        if payload is not None or type(diagnostic) is not AgentExecutionResultDiagnostic:
            raise _ResultIntegrityError()
        diagnostic.__post_init__()
        if diagnostic.code not in codes:
            raise _ResultIntegrityError()
    else:
        raise _ResultIntegrityError()


def _map_invocation(invocation):
    """Pure structural mapping; never constructs an authoritative Result."""
    from itru._execution_entry_and_controlled_invocation import _InvocationOutcome
    try:
        if type(invocation) is not _InvocationOutcome:
            raise _ResultIntegrityError()
        invocation.__post_init__()
        if invocation.status == "completed":
            values = ("succeeded", RepositoryFileReadResultPayload(
                invocation.data, invocation.byte_count), None)
        else:
            if (invocation.data is not None or type(invocation.byte_count) is not int
                    or invocation.byte_count != 0):
                raise _ResultIntegrityError()
            if invocation.status == "failed_before_content":
                outcome = "failed_before_effect"
            elif invocation.status == "failed_after_content":
                outcome = "effect_ambiguous"
            elif invocation.status == "ambiguous" and invocation.reason == "effect_ambiguous":
                outcome = "effect_ambiguous"
            else:
                raise _ResultIntegrityError()
            values = (outcome, None, AgentExecutionResultDiagnostic(invocation.reason))
        _validate_terminal_values(*values)
        return values
    except Exception:
        pass
    raise _ResultIntegrityError() from None


class _InvocationResultProduction:
    """One producer membership owned by one original invocation stack frame.

    Retired production drops execution references. Its published weak reference
    only authenticates passive evidence; it cannot enter, invoke or recover work.
    No global Result registry or physical-identity allocator exists.
    """
    __slots__ = ("seal", "pid", "thread", "frame", "coordinator", "cell", "subject",
                 "snapshot", "entry_result", "published", "closed", "result_state")

    def __new__(cls, *args, **kwargs):
        raise TypeError("private original invocation production required")

    def _original(self, caller):
        from itru._execution_entry_and_controlled_invocation import _ORIGINAL_INVOKE_CODE
        if (self.seal is not _PRODUCTION_SEAL or self.closed
                or self.pid != os.getpid() or self.thread != get_ident()
                or caller is not self.frame or caller.f_code is not _ORIGINAL_INVOKE_CODE
                or caller.f_locals.get("self") is not self.coordinator
                or caller.f_locals.get("result_production") is not self):
            raise _ResultIntegrityError()

    def _subject_intact(self):
        a, s = self.coordinator._a, self.subject
        if (self.cell.subject is not s or s.store is not a.store
                or s.store is not a.session._store or s.ledger_identity != a.state.identity
                or s.ledger_identity != a.session.identity
                or a.cells.get(s.physical_key) is not self.cell
                or a.snapshot is not self.snapshot or a.resolver._snapshot is not self.snapshot
                or s.binding.run != s.run
                or not validate_agent_operation_tool_binding(s.binding).valid):
            raise _ResultIntegrityError()

    def acknowledge(self, entry_result, operation):
        from itru._execution_entry_and_controlled_invocation import _EntryOperation, _EntryResult
        from itru.sqlite_agent_execution_dispatch_admission_store import _parse_decision_time
        self._original(sys._getframe(1))
        self._subject_intact()
        s = self.subject
        from itru.agent_operation_tool_registry import (
            _AgentOperationToolRoute, _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID,
            _AgentOperationToolImplementationSelector,
        )
        c = s.run.contract
        registration = self.snapshot._registrations_by_route.get(
            _AgentOperationToolRoute(c.runtime_option_id, c.environment_id, c.operation_id))
        if (registration is None or registration.tool_id != s.binding.tool_id
                or s.binding.tool_id != _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID
                or registration.implementation_selector
                != _AgentOperationToolImplementationSelector.ITRU_NATIVE_REPOSITORY_FILE_READ_V1
                or c.operation_id != "repository_file_read"):
            raise _ResultIntegrityError()
        e = entry_result.entry
        if (self.entry_result is not None or type(operation) is not _EntryOperation
                or operation.authorizer is not self.coordinator._a or operation.cell is not self.cell
                or type(entry_result) is not _EntryResult or entry_result.outcome != "entered"
                or entry_result.history_only is not False or self.cell.state != "CONSUMED"
                or operation._result_parent is None
                or operation._result_parent.grant.run != s.run
                or operation._result_parent.tool_binding != s.binding):
            raise _ResultIntegrityError()
        from itru._execution_entry_and_controlled_invocation import _ExecutionEntry
        if (type(e) is not _ExecutionEntry
                or (e.identity, e.claim_id, e.executor_instance_id, e.lease_generation)
                != (s.dispatch_identity, s.claim_id, s.executor_id, s.lease_generation)
                or e.identity[0] != s.ledger_identity.authorization_domain_id
                or e.entry_time != operation.sampled or type(e.entry_time_key) is not int
                or _parse_decision_time(e.entry_time)[1] != e.entry_time_key):
            raise _ResultIntegrityError()
        self.entry_result = entry_result

    def publish(self, entry_result, invocation):
        """Only original invoke may publish, after its effect scopes unwind."""
        self._original(sys._getframe(1))
        try:
            self._subject_intact()
            a = self.coordinator._a
            if (self.published is not None or self.entry_result is not entry_result
                    or entry_result is None or self.cell.state != "CONSUMED"
                    or getattr(a.guard.thread, "read", False)
                    or getattr(a.guard.thread, "leaf", False)
                    or a.session._thread_operations.get(get_ident(), 0) != 0):
                raise _ResultIntegrityError()
            values = _map_invocation(invocation)
            result = object.__new__(AgentExecutionResult)
            for name, value in zip(("ledger_identity", "execution_entry", "tool_binding",
                                    "outcome", "payload", "diagnostic"),
                                   (self.subject.ledger_identity, entry_result.entry,
                                    self.subject.binding, *values)):
                object.__setattr__(result, name, value)
            object.__setattr__(result, "_production", self)
            self.result_state = (_result_references(result), result.tool_binding.run,
                                 result.tool_binding.run.contract, _result_leaves(result))
            self.published = ref(result)  # Exact object membership, not value equality.
            return result
        except Exception:
            pass
        raise _ResultIntegrityError() from None

    def retire(self):
        self._original(sys._getframe(1))
        self.closed = True
        self.frame = self.coordinator = self.cell = self.subject = self.snapshot = self.entry_result = None


def _begin_result_production(coordinator, cell):
    from itru._execution_entry_and_controlled_invocation import (
        _ControlledInvocationCoordinator, _ENTRY_WRITER, _ORIGINAL_INVOKE_CODE,
    )
    caller = sys._getframe(1)
    a, s = coordinator._a, cell.subject
    if (caller.f_code is not _ORIGINAL_INVOKE_CODE
            or type(coordinator) is not _ControlledInvocationCoordinator
            or caller.f_locals.get("self") is not coordinator
            or caller.f_locals.get("cell") is not cell
            or getattr(a.store._enter_execution, "__func__", None) is not _ENTRY_WRITER):
        raise _ResultIntegrityError()
    production = object.__new__(_InvocationResultProduction)
    production.seal, production.pid, production.thread = _PRODUCTION_SEAL, os.getpid(), get_ident()
    production.frame, production.coordinator, production.cell = caller, coordinator, cell
    production.subject = s
    production.snapshot = a.snapshot
    production.entry_result = production.published = production.result_state = None
    production.closed = False
    return production


def _is_authoritative_result(value):
    if type(value) is not AgentExecutionResult:
        return False
    production = getattr(value, "_production", None)
    if not (type(production) is _InvocationResultProduction
            and getattr(production, "seal", None) is _PRODUCTION_SEAL
            and production.pid == os.getpid() and production.closed
            and production.published is not None and production.published() is value):
        return False
    try:
        references, run, contract, leaves = production.result_state
        if (all(current is original for current, original in
                zip(_result_references(value), references))
                and value.tool_binding.run is run and run.contract is contract
                and _result_leaves(value) == leaves):
            return True
    except Exception:
        pass
    # Observed mutation irreversibly rejects passive provenance; no effect authority.
    production.published = None
    return False
