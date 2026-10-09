"""Private AIO-057 ephemeral coordination. Never enters or invokes a Tool.

The Store assessment commits only its existing clock watermark. A future
consumer must add permanent Dispatch-unique Entry storage before any effect.
None of the results or capabilities here is a permission to perform target IO.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from threading import Lock, RLock, get_ident, local

from engineering_orchestration import agent_execution_authorization_grant_producer as producer
from engineering_orchestration._local_dispatch_claim_lease import (
    _validate_executor, _validate_owned_dispatch_context,
)
from engineering_orchestration.agent_action_prerequisite import assess_agent_action_prerequisites
from engineering_orchestration.agent_operation_tool_binding import (
    AgentOperationToolBinding, validate_agent_operation_tool_binding,
)
from engineering_orchestration.agent_operation_tool_registry import (
    _AgentOperationToolRoute, _select_agent_operation_tool_route,
)
from engineering_orchestration.agent_operation_tool_resolver import TrustedAgentOperationToolBindingResolver
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainIdentity, AuthorizationDomainOwnershipError,
)
from engineering_orchestration.execution_mode import execution_mode_satisfies
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    _DispatchClaim, _dispatch_identity, _dispatch_integer, _dispatch_token, _mint_dispatch_request,
    SqliteAdmissionStoreError, SqliteAgentExecutionDispatchAdmissionStore,
)

__all__ = ()
_COMPOSITION = Lock()
_SESSIONS = []  # Non-evictable, including failed/closed composition.
_PARTITIONS = []  # Strong references prevent object-ID reuse and alias bypass.
_AUTHORIZE_FACTORY = object()
_TERMINAL = frozenset(("CONSUMED", "REJECTED", "ABANDONED", "UNCERTAIN"))


class _JitFailure(RuntimeError):
    def __init__(self, outcome):
        super().__init__(outcome)
        self.outcome = outcome
        self.category = (
            "integrity" if outcome in (
                "invalid_integration", "malformed_prerequisite", "integrity_failure",
                "corrupt_snapshot", "registry_invalid")
            else "infrastructure" if outcome in (
                "clock_failure", "clock_regression", "guard_lost", "ownership_lost")
            else "rejection")


@dataclass(frozen=True, slots=True)
class _JitResult:
    outcome: str
    capability: object = None
    decision_time: str | None = None
    category: str = "rejection"
    # Deliberately no entry_committed or effect continuation field.


@dataclass(frozen=True, slots=True)
class _Subject:
    ledger_identity: AuthorizationDomainIdentity
    store: SqliteAgentExecutionDispatchAdmissionStore
    dispatch_identity: tuple[str, str, str, str]
    claim_id: str
    lease_generation: int
    executor: object
    executor_id: str
    run: object
    binding: AgentOperationToolBinding

    def __post_init__(self):
        if (type(self.ledger_identity) is not AuthorizationDomainIdentity
                or type(self.store) is not SqliteAgentExecutionDispatchAdmissionStore):
            raise TypeError("subject requires exact canonical ledger and Store components")
        _dispatch_identity(self.dispatch_identity)
        _dispatch_token(self.claim_id)
        _dispatch_integer(self.lease_generation)

    @property
    def physical_key(self):
        """The sole registry identity; never an independently supplied tuple."""
        return (self.ledger_identity, id(self.store), self.dispatch_identity,
                self.claim_id, self.lease_generation)


def _validate_jit_subject(subject, guard):
    """Reject noncanonical or foreign components before registry/proof writes."""
    if type(subject) is not _Subject:
        raise _JitFailure("invalid_input")
    subject.__post_init__()
    if (subject.ledger_identity != guard.state.identity
            or subject.store is not guard.session._store):
        raise _JitFailure("foreign_ledger")
    return subject.physical_key


@dataclass(slots=True)
class _Cell:
    subject: _Subject
    fingerprint: tuple
    state: str = "PREPARING"
    capability: object = None
    lock: object = field(default_factory=Lock)

    def _transition(self, target):
        """Held-C state mechanics only; never a durable Entry receipt."""
        allowed = {
            "PREPARING": {"PREPARED", "REJECTED", "ABANDONED", "UNCERTAIN"},
            "PREPARED": {"CONSUMING", "ABANDONED", "UNCERTAIN"},
            "CONSUMING": {"CONSUMED", "REJECTED", "ABANDONED", "UNCERTAIN"},
        }
        if target not in allowed.get(self.state, set()):
            raise _JitFailure("terminal_capability")
        self.state = target


class _ExecutionAttemptAuthorization(producer._ProcessLocalCapability):
    __slots__ = ("_authorizer", "_cell", "_pid", "_epoch")


class _AuthorityGuard:
    """Trusted participants must bind every alias of each declared partition.

    Participant handshake:
      _jit_mutable_partitions() -> exact nonempty tuple of underlying objects
      _bind_jit_authority_guard(guard) -> installs mutation_scope on ALL writers
    This is a cooperative trusted-process contract, not a sandbox.
    """
    def __init__(self, session, state, participants):
        self.session = session
        self.state = state
        self.participants = tuple(participants)
        self.lock = RLock()
        self.thread = local()
        self.pid = os.getpid()
        self.closed = False
        self.revision = 0
        self.epoch = object()
        self.authorizer = None

    def _live(self):
        if self.closed or self.pid != os.getpid() or self.state.closed:
            raise _JitFailure("guard_lost")
        if self.session._state != "live" or self.session.identity != self.state.identity:
            raise _JitFailure("ownership_lost")

    @contextmanager
    def protected(self):
        if getattr(self.thread, "leaf", False):
            raise _JitFailure("invalid_integration")
        with self.lock:
            self._live()
            yield

    @contextmanager
    def mutation_scope(self, participant, kind):
        if not any(participant is p for p in (*self.participants, self.state)):
            raise _JitFailure("unsupported_source")
        if type(kind) is not str or not kind:
            raise _JitFailure("invalid_integration")
        if getattr(self.thread, "read", False):
            raise _JitFailure("invalid_integration")
        with self.protected():
            try:
                yield
                self.revision += 1
                if kind == "configuration":
                    self.closed = True  # Immutable configuration needs new binding.
                    self.state.closed = True
            except BaseException:
                self.closed = True  # Ambiguous writes never retain an allow.
                self.state.closed = True
                raise

    @contextmanager
    def leaf(self):
        if not getattr(self.thread, "read", False) or getattr(self.thread, "leaf", False):
            raise _JitFailure("invalid_integration")
        self.thread.leaf = True
        try:
            yield
        finally:
            self.thread.leaf = False

    @contextmanager
    def read_scope(self):
        # S must already be held on this thread; never acquire S under G/P.
        _validate_owned_dispatch_context(self.session, self.session._store)
        with self.protected():
            with self.state.lock:
                if getattr(self.thread, "read", False):
                    raise _JitFailure("invalid_integration")
                self.thread.read = True
                try:
                    yield
                finally:
                    self.thread.read = False


class _ProducerCoordinationLock:
    """Optional private G-before-P wrapper; original public signatures unchanged."""
    def __init__(self, guard, original):
        self.guard = guard
        self.original = original
        self.thread = local()

    def acquire(self):
        if getattr(self.guard.thread, "leaf", False) or getattr(self.thread, "held", False):
            raise _JitFailure("invalid_integration")
        self.guard.lock.acquire()
        try:
            # Closed Producer calls retain their original public closed behavior.
            if self.guard.pid != os.getpid():
                raise _JitFailure("guard_lost")
            if self.guard.closed:
                self.guard.state.closed = True
            self.original.acquire()
            self.thread.held = True
            return True
        except BaseException:
            self.guard.lock.release()
            raise

    def release(self):
        self.thread.held = False
        self.original.release()
        self.guard.lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *error):
        self.release()


def _fingerprint(guard, principal, decision):
    return (id(principal), id(decision), guard.revision, guard.epoch)


def _subject(session, claim, executor, run, binding):
    if type(claim) is not _DispatchClaim:
        raise _JitFailure("invalid_input")
    executor_id = _validate_executor(executor, session)
    if not producer._is_intrinsically_valid_exact_run(run):
        raise _JitFailure("wrong_run")
    checked = validate_agent_operation_tool_binding(binding)
    if type(binding) is not AgentOperationToolBinding or not checked.valid or binding.run != run:
        raise _JitFailure("wrong_binding")
    if claim.executor_instance_id != executor_id:
        raise _JitFailure("wrong_executor")
    if type(claim.identity) is not tuple or len(claim.identity) != 4:
        raise _JitFailure("invalid_input")
    return _Subject(session.identity, session._store, claim.identity, claim.claim_id,
                    claim.lease_generation, executor, executor_id, run, binding)


def _compose_jit_execution_attempt_authorizer(*, session, producer_binding, resolver, current_source):
    """Install once before participants are published. No registry replacement."""
    state = producer_binding.producer._state
    if (type(producer_binding) is not producer._AgentExecutionAuthorizationGrantProducerBinding
            or state.owned_session is not session
            or type(resolver) is not TrustedAgentOperationToolBindingResolver):
        raise _JitFailure("invalid_integration")
    participants = tuple(p for p in (
        state.identity_adapter, state.human_approval_adapter,
        state.policy_decision_adapter, state.issuer_state_authority,
        state.issuer_entitlement_policy, current_source) if p is not None)
    declarations = []
    for participant in participants:
        method = getattr(participant, "_jit_mutable_partitions", None)
        binder = getattr(participant, "_bind_jit_authority_guard", None)
        if not callable(method) or not callable(binder):
            raise _JitFailure("unsupported_source")
        partitions = method()
        if type(partitions) is not tuple or not partitions:
            raise _JitFailure("unsupported_source")
        declarations.append((participant, partitions))
    if not callable(getattr(current_source, "_jit_current_inputs", None)):
        raise _JitFailure("unsupported_source")
    guard = _AuthorityGuard(session, state, participants)
    # Reservation is never held across S/G/P/Store or external bind callbacks.
    with _COMPOSITION:
        if any(s is session for s in _SESSIONS):
            raise _JitFailure("composition_conflict")
        for _, partitions in declarations:
            for partition in partitions:
                if any(p is partition and not owner.closed for p, owner in _PARTITIONS):
                    raise _JitFailure("composition_conflict")
        _SESSIONS.append(session)
        for _, partitions in declarations:
            _PARTITIONS.extend((p, guard) for p in partitions)
    try:
        with session.operation():
            _validate_owned_dispatch_context(session, session._store)
            with guard.lock:
                producer._attach_jit_authority_guard(state, guard)
                for participant, _ in declarations:
                    participant._bind_jit_authority_guard(guard)
        guard._live()
        authorizer = _JitAuthorizer(guard, resolver, current_source, _AUTHORIZE_FACTORY)
        guard.authorizer = authorizer
        return authorizer
    except BaseException:
        guard.closed = True
        state.closed = True
        raise


class _JitAuthorizer:
    def __new__(cls, guard, resolver, source, token=None):
        if token is not _AUTHORIZE_FACTORY:
            raise TypeError("authorizers require install-once trusted composition")
        return object.__new__(cls)

    def __init__(self, guard, resolver, source, token=None):
        self.guard = guard
        self.session = guard.session
        self.store = self.session._store
        self.state = guard.state
        self.resolver = resolver
        self.snapshot = resolver._snapshot
        self.source = source
        self.cells = {}
        self.registry_lock = Lock()
        self.pid = os.getpid()
        self.epoch = object()
        self.closed = False

    def subject(self, claim, executor, run, binding):
        return _subject(self.session, claim, executor, run, binding)

    def mint_entry_decision(self, subject, principal, **decision_fields):
        _validate_jit_subject(subject, self.guard)
        return producer._mint_jit_entry_decision(
            self.state, self.guard, subject, principal, **decision_fields)

    def _live(self):
        self.guard._live()
        if getattr(self.guard.thread, "read", False):
            raise _JitFailure("invalid_integration")
        if self.closed or self.pid != os.getpid() or self.guard.authorizer is not self:
            raise _JitFailure("closed")

    def _cap_cell(self, capability):
        if getattr(self.guard.thread, "read", False):
            raise _JitFailure("invalid_integration")
        if (type(capability) is not _ExecutionAttemptAuthorization
                or getattr(capability, "_authorizer", None) is not self
                or capability._epoch is not self.epoch or capability._pid != os.getpid()):
            raise _JitFailure("invalid_capability")
        cell = capability._cell
        if (self.cells.get(_validate_jit_subject(cell.subject, self.guard)) is not cell
                or cell.capability is not capability):
            raise _JitFailure("invalid_capability")
        return cell

    @staticmethod
    def _failure(error):
        if isinstance(error, _JitFailure):
            return _JitResult(error.outcome, category=error.category)
        if isinstance(error, AuthorizationDomainOwnershipError):
            return _JitResult("ownership_lost", category="infrastructure")
        if isinstance(error, SqliteAdmissionStoreError):
            failure = SqliteAgentExecutionDispatchAdmissionStore._operational_failure(error)
            return _JitResult(failure.outcome.value, category=(
                "integrity" if failure.outcome.value == "integrity_failure" else "infrastructure"))
        if isinstance(error, OSError):
            return _JitResult("storage_unavailable", category="infrastructure")
        if isinstance(error, (ValueError, TypeError, AttributeError)):
            return _JitResult("integrity_failure", category="integrity")
        return _JitResult("state_unavailable", category="infrastructure")

    def prepare(self, subject, principal, decision):
        cell = None
        fresh = False
        try:
            self._live()
            physical_key = _validate_jit_subject(subject, self.guard)
            fp = _fingerprint(self.guard, principal, decision)
            with self.registry_lock:
                self._live()
                cell = self.cells.get(physical_key)
                if cell is None:
                    cell = _Cell(subject, fp)
                    self.cells[physical_key] = cell
                    fresh = True
                else:
                    with cell.lock:
                        if cell.subject != subject:
                            raise _JitFailure("subject_conflict")
                        if cell.state == "PREPARING":
                            return _JitResult("preparation_in_progress")
                        if cell.state != "PREPARED":
                            return _JitResult("terminal_capability")
                        if cell.fingerprint != fp:
                            return _JitResult("already_prepared")
            result = self._assess(cell, principal, decision, "prepare")
            if result.outcome != "assessed":
                if fresh:
                    with cell.lock:
                        cell._transition("UNCERTAIN" if result.outcome == "commit_unknown" else "REJECTED")
                return result
            # S exit has succeeded. Publication uses C only and acquires no G/P/W.
            with cell.lock:
                self._live()
                if fresh:
                    if cell.state != "PREPARING" or cell.fingerprint != _fingerprint(self.guard, principal, decision):
                        cell._transition("UNCERTAIN")
                        return _JitResult("uncertain")
                    cell.capability = producer._mint_capability(
                        _ExecutionAttemptAuthorization,
                        {"_authorizer": self, "_cell": cell, "_pid": self.pid, "_epoch": self.epoch})
                    cell._transition("PREPARED")
                elif cell.state != "PREPARED":
                    return _JitResult("terminal_capability")
                return _JitResult("prepared" if fresh else "exact_retry", cell.capability, result.decision_time, "assessment")
        except BaseException as error:
            if fresh and cell is not None:
                with cell.lock:
                    if cell.state not in _TERMINAL:
                        cell._transition("UNCERTAIN")
            if not isinstance(error, Exception):
                raise
            return self._failure(error)

    def verify(self, capability, principal, decision):
        try:
            cell = self._cap_cell(capability)
            return self._assess(cell, principal, decision, "verify")
        except Exception as error:
            return self._failure(error)

    def _consume_assessment(self, capability, principal, decision):
        """Provisional only: v3 cannot finish durable Entry or permit an effect."""
        try:
            cell = self._cap_cell(capability)
            return self._assess(cell, principal, decision, "consume")
        except Exception as error:
            return self._failure(error)

    def _assess(self, cell, principal, decision, mode):
        operation = _JitAssessmentOperation(self, cell, principal, decision, mode)
        try:
            with self.session.operation():
                self._live()
                _validate_owned_dispatch_context(self.session, self.store)
                subject = cell.subject
                if _validate_executor(subject.executor, self.session) != subject.executor_id:
                    raise _JitFailure("wrong_executor")
                with self.guard.read_scope():
                    request = _mint_dispatch_request(
                        "query", self.session, self.store, capability=subject.executor,
                        claim_id=subject.claim_id, identity=subject.dispatch_identity,
                        generation=subject.lease_generation, mode="current")
                    result = self.store._assess_jit_dispatch(request, operation)
            return result  # No disclosure before owned exit/post-check.
        except BaseException as error:
            if mode == "consume":
                with cell.lock:
                    if cell.state == "CONSUMING":
                        cell._transition("UNCERTAIN")
            if not isinstance(error, Exception):
                raise
            return self._failure(error)

    def abandon(self, capability):
        try:
            cell = self._cap_cell(capability)
            with cell.lock:
                if cell.state not in _TERMINAL:
                    cell._transition("ABANDONED")
            return _JitResult("abandoned")
        except Exception as error:
            return self._failure(error)

    def close(self):
        # G/P then C; no S acquisition and no wait for owned operations.
        with self.guard.lock:
            with self.registry_lock:
                self.closed = True
                self.state.closed = True
                self.guard.closed = True
                self.epoch = object()
                cells = tuple(self.cells.values())
            for cell in cells:
                with cell.lock:
                    if cell.state not in _TERMINAL:
                        cell._transition("ABANDONED")


class _JitAssessmentOperation:
    """Store-owned leaf participant: no connection, SQL or effect callback escapes."""
    def __init__(self, authorizer, cell, principal, decision, mode):
        self.authorizer = authorizer
        self.cell = cell
        self.principal = principal
        self.decision = decision
        self.mode = mode
        self.owner_thread = get_ident()
        self.sampled = None
        self.current_inputs = None

    def _freeze(self, parent):
        a, s = self.authorizer, self.cell.subject
        _validate_jit_subject(s, a.guard)
        if parent.grant.run != s.run or parent.tool_binding != s.binding:
            raise _JitFailure("wrong_run" if parent.grant.run != s.run else "wrong_binding")
        with a.guard.leaf():
            failure = producer._validate_jit_entry_decision(
                a.state, a.guard, s, self.principal, self.decision, None)
            if failure is not None:
                raise _JitFailure(failure)
            inputs, actual, required = a.source._jit_current_inputs()
            self.current_inputs = (dict(inputs), actual, required)

    @contextmanager
    def _cell_scope(self, store):
        a = self.authorizer
        if (store is not a.store or get_ident() != self.owner_thread
                or not getattr(a.guard.thread, "read", False)):
            raise _JitFailure("invalid_integration")
        with self.cell.lock:
            expected = "PREPARING" if self.mode == "prepare" and self.cell.capability is None else "PREPARED"
            if self.cell.state != expected:
                raise _JitFailure("terminal_capability")
            if self.mode == "consume":
                self.cell._transition("CONSUMING")
            try:
                yield
            except _JitFailure:
                if self.mode == "consume" and self.cell.state == "CONSUMING":
                    self.cell._transition("REJECTED")
                raise
            finally:
                # No Entry backend: even successful provisional assessment burns.
                if self.mode == "consume" and self.cell.state == "CONSUMING":
                    self.cell._transition("UNCERTAIN")

    def _check(self, parent, claim, effective_key, now, text, key):
        a, s = self.authorizer, self.cell.subject
        self.sampled = text
        if (not producer._is_intrinsically_valid_exact_run(s.run)
                or type(s.binding) is not AgentOperationToolBinding
                or not validate_agent_operation_tool_binding(s.binding).valid):
            raise _JitFailure("malformed_prerequisite")
        if ((claim.identity, claim.claim_id, claim.lease_generation, claim.executor_instance_id)
                != (s.dispatch_identity, s.claim_id, s.lease_generation, s.executor_id)):
            raise _JitFailure("subject_conflict")
        if parent.grant.run != s.run:
            raise _JitFailure("wrong_run")
        if parent.tool_binding != s.binding:
            raise _JitFailure("wrong_binding")
        if not claim.acquired_at_key <= key < effective_key:
            raise _JitFailure("expired_claim")
        if a.resolver._snapshot is not a.snapshot:
            raise _JitFailure("corrupt_snapshot")
        with a.guard.leaf():
            failure = producer._validate_jit_entry_decision(
                a.state, a.guard, s, self.principal, self.decision, now)
            if failure is not None:
                raise _JitFailure(failure)
            resolution = a.resolver.resolve(parent.grant)
            if resolution.binding != s.binding:
                raise _JitFailure(resolution.outcome.value)
            c = s.run.contract
            selected = _select_agent_operation_tool_route(a.snapshot, route=_AgentOperationToolRoute(
                c.runtime_option_id, c.environment_id, c.operation_id))
            if selected.outcome.value != "resolved" or selected.selected_route is None:
                raise _JitFailure(selected.outcome.value)
            inputs, actual_mode, required_mode = self.current_inputs
            assessment = assess_agent_action_prerequisites(**inputs)
            if not assessment.valid:
                raise _JitFailure("malformed_prerequisite")
            if assessment.outcome.value != "satisfied":
                raise _JitFailure(assessment.outcome.value)
            expected = ((c.task_id, c.workflow_id, c.stage_id, c.role_id),
                        c.actor_id, c.runtime_option_id, c.option_id, c.environment_id,
                        c.operation_id, c.resource)
            actual = (assessment.responsibility_key, assessment.actor_id,
                      assessment.runtime_option_id, assessment.option_id, assessment.environment_id,
                      assessment.operation_id, assessment.resource)
            if actual != expected:
                raise _JitFailure("wrong_run")
            if (type(actual_mode) is not str or type(required_mode) is not str
                    or not execution_mode_satisfies(actual_mode, required_mode)
                    or actual_mode != c.execution_mode):
                raise _JitFailure("changed_mode")
        return _JitResult("assessed", decision_time=text, category="assessment")
