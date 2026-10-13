"""Private AIO-058 durable entry and original synchronous invocation.

An Entry is permanent history, never a recoverable invocation credential.
No public Result, journal, dispatch API or automatic replay is provided.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import os
from threading import get_ident

from itru import _jit_execution_attempt_authorization as jit
from itru import agent_execution_authorization_grant_producer as producer
from itru._local_dispatch_claim_lease import _validate_executor, _validate_owned_dispatch_context
from itru.agent_operation_tool_registry import (
    _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID, _AgentOperationToolRoute,
    _AgentOperationToolImplementationSelector, _select_agent_operation_tool_route,
)
from itru.sqlite_agent_execution_dispatch_admission_store import _mint_dispatch_request

__all__ = ()


@dataclass(frozen=True, slots=True)
class _ExecutionEntry:
    identity: tuple[str, str, str, str]
    claim_id: str
    executor_instance_id: str
    lease_generation: int
    entry_time: str
    entry_time_key: int


@dataclass(frozen=True, slots=True)
class _EntryResult:
    outcome: str
    entry: _ExecutionEntry | None = None
    history_only: bool = True


@dataclass(frozen=True, slots=True)
class _InvocationOutcome:
    status: str
    reason: str
    data: bytes | None = None
    byte_count: int = 0

    def __post_init__(self):
        if self.status not in ('completed', 'failed_before_content', 'failed_after_content', 'ambiguous'):
            raise ValueError('invalid private status')
        if self.reason not in ('effect_completed', 'adapter_unavailable', 'containment_rejected',
                'resource_missing', 'resource_changed', 'size_limit_exceeded', 'read_failure',
                'guard_lost', 'ownership_lost', 'effect_ambiguous', 'entry_rejected'):
            raise ValueError('invalid private reason')
        if self.status == 'completed':
            if type(self.data) is not bytes or self.byte_count != len(self.data) or self.byte_count > 65536:
                raise ValueError('invalid private payload')
            if self.reason != 'effect_completed':
                raise ValueError('invalid successful reason')
        elif self.data is not None or self.byte_count != 0:
            raise ValueError('unsuccessful outcome cannot disclose content')


@dataclass(frozen=True, slots=True)
class _ControlledOutcome:
    entry_result: _EntryResult
    invocation: _InvocationOutcome | None = None


class _EntryOperation(jit._JitAssessmentOperation):
    """Same final predicates as AIO-057, consumed inside the Entry writer."""
    def __init__(self, authorizer, cell, principal, decision):
        super().__init__(authorizer, cell, principal, decision, 'consume')

    def _writer_scope(self, store):
        a=self.authorizer
        if (store is not a.store or get_ident()!=self.owner_thread
                or not getattr(a.guard.thread,'read',False)
                or getattr(a.guard.thread,'leaf',False)):
            raise jit._JitFailure('invalid_integration')
        a.guard._live()

    @contextmanager
    def _cell_scope(self, store):
        with super()._cell_scope(store):
            a, cell = self.authorizer, self.cell
            capability = cell.capability
            if (a.cells.get(jit._validate_jit_subject(cell.subject, a.guard)) is not cell
                    or type(capability) is not jit._ExecutionAttemptAuthorization
                    or capability._cell is not cell or capability._authorizer is not a
                    or capability._pid != os.getpid() or capability._epoch is not a.epoch):
                raise jit._JitFailure('invalid_capability')
            yield


class _Continuation(producer._ProcessLocalCapability):
    __slots__ = ('_coordinator', '_entry', '_cell', '_root', '_pid', '_thread',
                 '_frame', '_authorizer_epoch', '_guard_epoch', '_revision', '_run', '_binding')


class _ControlledInvocationCoordinator:
    """Trusted composition, fixed adapter, no external callback or ticket.

    Root provisioning precedes publication. Its teardown is coordinated outside
    the S/G/P operation; neither native traversal nor cleanup reenters the Store.
    """
    def __init__(self, authorizer, root):
        from itru import _native_repository_file_read as native
        if type(authorizer) is not jit._JitAuthorizer or type(root) is not native._TrustedRoot:
            raise TypeError('exact private composition required')
        if not root._available(authorizer.session, root._environment):
            raise ValueError('root/session mismatch')
        authorizer._live()
        self._a, self._root = authorizer, root
        self._reader = native._invoke_repository_file_read
        self._implementation = self._reader
        self._pid = os.getpid()
        self._active = None
        self._original = None
        self._entry = None
        self._cell = None
        self._once = 'unsealed'

    def _request(self, cell):
        s = cell.subject
        return _mint_dispatch_request('query', self._a.session, self._a.store,
            capability=s.executor, claim_id=s.claim_id, identity=s.dispatch_identity,
            generation=s.lease_generation, mode='current')

    def _begin_native(self, continuation, root, resource):
        """Burn original authority before *any* resource-derived native action."""
        a = self._a
        if (type(continuation) is not _Continuation or continuation is not self._original
                or self._once != 'sealed' or self._active is None
                or continuation._frame is not self._active
                or continuation._coordinator is not self
                or continuation._entry is not self._entry or continuation._cell is not self._cell
                or continuation._run is not self._cell.subject.run
                or continuation._binding is not self._cell.subject.binding
                or self._cell.capability._authorizer is not a
                or self._pid != os.getpid() or continuation._pid != os.getpid()
                or continuation._thread != get_ident()
                or continuation._root is not root or root is not self._root
                or continuation._authorizer_epoch is not a.epoch
                or continuation._guard_epoch is not a.guard.epoch
                or continuation._revision != a.guard.revision
                or continuation._cell.state != 'CONSUMED'
                or continuation._run.contract.resource != resource
                or not getattr(a.guard.thread, 'read', False)
                or not getattr(a.guard.thread, 'leaf', False)):
            raise jit._JitFailure('invalid_capability')
        a.guard._live()
        if not root._available(a.session, continuation._run.contract.environment_id):
            raise jit._JitFailure('invalid_capability')
        _validate_owned_dispatch_context(a.session, a.store)
        if _validate_executor(continuation._cell.subject.executor, a.session) != continuation._entry.executor_instance_id:
            raise jit._JitFailure('wrong_executor')
        self._once = 'started'

    def _availability(self, cell):
        from itru import _native_repository_file_read as native
        a, c = self._a, cell.subject.run.contract
        a.guard._live()
        if (self._reader is not self._implementation or self._implementation is not native._invoke_repository_file_read
                or not self._root._available(a.session, c.environment_id)
                or a.resolver._snapshot is not a.snapshot
                or cell.subject.binding.tool_id != _ITRU_NATIVE_REPOSITORY_FILE_READ_TOOL_ID
                or c.operation_id != 'repository_file_read'):
            return False
        selected = _select_agent_operation_tool_route(a.snapshot, route=_AgentOperationToolRoute(
            c.runtime_option_id, c.environment_id, c.operation_id))
        route = selected.selected_route
        return (selected.outcome.value == 'resolved' and route is not None
                and a.snapshot._registrations_by_route[route.route].implementation_selector == _AgentOperationToolImplementationSelector.ITRU_NATIVE_REPOSITORY_FILE_READ_V1
                and route.tool_id == cell.subject.binding.tool_id)

    def invoke(self, capability, principal, decision):
        a = self._a
        entry_result = _EntryResult('not_entered')
        invoked = False
        try:
            a._live()
            cell = a._cap_cell(capability)  # No reservation lock nests with S/G/P/W.
            if self._active is not None or self._pid != os.getpid():
                raise jit._JitFailure('invalid_integration')
            with self._root._retain(), a.session.operation():
                a._live()
                _validate_owned_dispatch_context(a.session, a.store)
                _validate_executor(cell.subject.executor, a.session)
                with a.guard.read_scope():
                    operation = _EntryOperation(a, cell, principal, decision)
                    entry_result = a.store._enter_execution(self._request(cell), operation)
                    if entry_result.outcome != 'entered':
                        return _ControlledOutcome(entry_result)
                    # W and C are now released, S/G/P remain on this stack.
                    self._entry = entry_result.entry
                    self._cell = cell
                    self._active = object()
                    self._original = producer._mint_capability(_Continuation, dict(
                        _coordinator=self, _entry=entry_result.entry, _cell=cell,
                        _root=self._root, _pid=self._pid, _thread=get_ident(), _frame=self._active,
                        _authorizer_epoch=a.epoch, _guard_epoch=a.guard.epoch,
                        _revision=a.guard.revision, _run=cell.subject.run, _binding=cell.subject.binding))
                    self._once = 'sealed'
                    try:
                        if not self._availability(cell):
                            self._once = 'suppressed'
                            outcome = _InvocationOutcome('failed_before_content', 'adapter_unavailable')
                        else:
                            # Leaf forbids callbacks/reentry into any earlier lock.
                            with a.guard.leaf():
                                outcome = self._reader(self._original, self._root, cell.subject.run.contract.resource)
                            invoked = self._once in ('started', 'finished')
                            if self._once == 'started':
                                self._once = 'finished'
                    finally:
                        invoked = invoked or self._once in ('started', 'finished')
                        if self._once == 'sealed':
                            self._once = 'suppressed'
                        self._active = None
                        self._original = None
            return _ControlledOutcome(entry_result, outcome)  # Disclose only after S postcheck.
        except BaseException as error:
            if 'cell' in locals():
                with cell.lock:  # S/G/P/W have unwound, no backward acquisition.
                    if cell.state == 'CONSUMING':
                        cell._transition('UNCERTAIN')
            if not isinstance(error, Exception):
                raise
            if entry_result.outcome == 'entered':
                reason = ('effect_ambiguous' if invoked else
                    'guard_lost' if isinstance(error, jit._JitFailure) and error.outcome != 'ownership_lost'
                    else 'ownership_lost')
                return _ControlledOutcome(entry_result, _InvocationOutcome(
                    'ambiguous' if invoked else 'failed_before_content', reason))
            return _ControlledOutcome(_EntryResult(a._failure(error).outcome))

    def history(self, capability):
        """Same pinned ledger only. No continuation construction or target IO."""
        a = self._a
        try:
            cell = a._cap_cell(capability)
            with a.session.operation():
                return a.store._classify_execution_entry(self._request(cell))
        except Exception as error:
            return _EntryResult(a._failure(error).outcome)
