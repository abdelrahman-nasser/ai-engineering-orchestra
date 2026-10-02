"""Trusted local composition of Grant production and authoritative Admission.

This module joins the existing AIO-049, AIO-050, AIO-051, and AIO-047
components.  It does not dispatch, invoke a Tool, or read a repository
resource.  The only durable state remains the AIO-047 Admission ledger owned
through AIO-049.
"""

from __future__ import annotations

from threading import Condition, RLock, get_ident
from collections.abc import Callable
from typing import NoReturn

from engineering_orchestration.agent_execution_authorization_grant import (
    AgentExecutionAuthorizationGrant,
)
from engineering_orchestration.agent_execution_authorization_grant_producer import (
    AgentExecutionAuthorizationGrantLifetimePolicy,
    AgentExecutionAuthorizationGrantProducer,
    AgentExecutionAuthorizationGrantProductionOutcome,
    AgentExecutionAuthorizationGrantProductionResult,
    AuthenticatedHumanApproval,
    AuthenticatedIssuerPrincipal,
    AuthenticatedPolicyDecision,
    IssuedAgentExecutionAuthorizationGrant,
    _AgentExecutionAuthorizationGrantAuthenticationPort,
    _AgentExecutionAuthorizationGrantProducerBinding,
    _compose_agent_execution_authorization_grant_producer,
)
from engineering_orchestration.agent_execution_dispatch_admission_store import (
    AgentExecutionDispatchAdmissionStoreResult,
)
from engineering_orchestration.agent_execution_run import AgentExecutionRun
from engineering_orchestration.agent_operation_tool_registry import (
    _AgentOperationToolRegistryOutcome,
    _TrustedAgentOperationToolRegistrySnapshot,
    _build_trusted_agent_operation_tool_registry_snapshot,
    _make_aeo_native_repository_file_read_registration,
)
from engineering_orchestration.agent_operation_tool_resolver import (
    TrustedAgentOperationToolBindingResolver,
)
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainIdentity,
    OwnedAuthorizationDomainSession,
)
from engineering_orchestration.windows_local_authorization_domain_owner import (
    WindowsLocalAuthorizationDomainOwner,
)


__all__ = ("LocalOperationalTrustCoordinator",)


_SUCCESSFUL_PRODUCTION_OUTCOMES = frozenset(
    (
        AgentExecutionAuthorizationGrantProductionOutcome.ISSUED,
        AgentExecutionAuthorizationGrantProductionOutcome.EXISTING_EXACT_ISSUANCE,
    )
)

class _ProcessLocalCapability:
    """Nonconstructible, immutable, nonserializable process-local capability."""

    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> NoReturn:
        del args, kwargs
        raise TypeError(f"{cls.__name__} is minted only by trusted composition")

    def __setattr__(self, name: str, value: object) -> NoReturn:
        del name, value
        raise TypeError(f"{type(self).__name__} is immutable")

    def __copy__(self) -> NoReturn:
        raise TypeError(f"{type(self).__name__} cannot be copied")

    def __deepcopy__(self, memo: object) -> NoReturn:
        del memo
        raise TypeError(f"{type(self).__name__} cannot be copied")

    def __reduce__(self) -> NoReturn:
        raise TypeError(f"{type(self).__name__} cannot be serialized")

    def __reduce_ex__(self, protocol: object) -> NoReturn:
        del protocol
        raise TypeError(f"{type(self).__name__} cannot be serialized")

    def __getstate__(self) -> NoReturn:
        raise TypeError(f"{type(self).__name__} cannot be serialized")


class _GrantAuthenticationLatch:
    """Install-once forwarding latch used only inside the trusted root."""

    __slots__ = ("_lock", "_state", "_target")

    def __init__(self) -> None:
        self._lock = RLock()
        self._state = "unbound"
        self._target: _AgentExecutionAuthorizationGrantAuthenticationPort | None = (
            None
        )

    def authenticate_grant(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        with self._lock:
            target = self._target if self._state == "bound" else None
        if target is None:
            return None
        try:
            return target.authenticate_grant(presented_grant)
        except Exception:
            return None

    def fail(self) -> None:
        with self._lock:
            if self._state == "unbound":
                self._state = "failed"
                self._target = None

    def close(self) -> None:
        with self._lock:
            self._target = None
            self._state = "closed"


def _new_grant_authentication_latch() -> tuple[
    _GrantAuthenticationLatch,
    Callable[[object], None],
]:
    """Return one latch and a lexical, one-use binder closure."""

    latch = _GrantAuthenticationLatch()
    consumed = False

    def bind_exact_composed_port(target: object) -> None:
        nonlocal consumed
        with latch._lock:
            if consumed or latch._state != "unbound":
                raise RuntimeError("Grant authentication latch is already terminal")
            consumed = True
            if (
                type(target)
                is not _AgentExecutionAuthorizationGrantAuthenticationPort
            ):
                latch._state = "failed"
                latch._target = None
                raise RuntimeError(
                    "Grant authentication latch rejected a noncanonical target"
                )
            latch._target = target
            latch._state = "bound"

    return latch, bind_exact_composed_port


class _OriginalIssuerRevocationPresentation(_ProcessLocalCapability):
    """Private occurrence tying original-issuer proof to one issued presentation."""

    __slots__ = (
        "_adapter",
        "_adapter_epoch",
        "_domain_identity",
        "_issued_presentation",
        "_intent",
        "_original_issuer_proof",
        "_provenance_reference",
        "_session_ticket",
    )


class _OriginalIssuerRevocationMinter(_ProcessLocalCapability):
    __slots__ = ("_port",)

    def mint(
        self,
        *,
        original_issuer_proof: object,
        issued_presentation: IssuedAgentExecutionAuthorizationGrant,
        provenance_reference: str,
    ) -> _OriginalIssuerRevocationPresentation:
        return self._port._mint(
            original_issuer_proof=original_issuer_proof,
            issued_presentation=issued_presentation,
            provenance_reference=provenance_reference,
        )


class _OriginalIssuerRevocationPort:
    """Authenticate a distinct synthetic issuer proof under the owned session."""

    __slots__ = (
        "_adapter",
        "_closed",
        "_domain_identity",
        "_latch",
        "_lock",
        "_minter_created",
        "_owned_session",
        "_presentations",
        "_session_ticket",
    )

    def __init__(self, *, adapter: object, latch: _GrantAuthenticationLatch) -> None:
        for method_name in (
            "current_epoch",
            "validate_authenticated_original_issuer_revocation",
        ):
            if not callable(getattr(adapter, method_name, None)):
                raise TypeError(f"revocation adapter must implement {method_name}()")
        self._adapter = adapter
        self._closed = False
        self._domain_identity: AuthorizationDomainIdentity | None = None
        self._latch = latch
        self._lock = RLock()
        self._minter_created = False
        self._owned_session: OwnedAuthorizationDomainSession | None = None
        self._presentations: dict[int, _OriginalIssuerRevocationPresentation] = {}
        self._session_ticket: object | None = None

    def bind_session(
        self,
        owned_session: OwnedAuthorizationDomainSession,
    ) -> _OriginalIssuerRevocationMinter:
        if not isinstance(owned_session, OwnedAuthorizationDomainSession):
            raise TypeError("owned_session must be an OwnedAuthorizationDomainSession")
        identity = owned_session.identity
        if type(identity) is not AuthorizationDomainIdentity:
            raise TypeError("owned_session identity must be canonical")
        with self._lock:
            if self._closed or self._owned_session is not None or self._minter_created:
                raise RuntimeError("revocation port session is already terminally bound")
            self._owned_session = owned_session
            self._domain_identity = identity
            self._session_ticket = object()
            minter = object.__new__(_OriginalIssuerRevocationMinter)
            object.__setattr__(minter, "_port", self)
            self._minter_created = True
            return minter

    def _mint(
        self,
        *,
        original_issuer_proof: object,
        issued_presentation: IssuedAgentExecutionAuthorizationGrant,
        provenance_reference: str,
    ) -> _OriginalIssuerRevocationPresentation:
        if (
            type(issued_presentation)
            is not IssuedAgentExecutionAuthorizationGrant
            or original_issuer_proof is issued_presentation
            or type(provenance_reference) is not str
            or not provenance_reference
        ):
            raise ValueError("revocation presentation inputs are not canonical")
        with self._lock:
            if (
                self._closed
                or self._owned_session is None
                or self._session_ticket is None
            ):
                raise RuntimeError("revocation port is not live")
            try:
                adapter_epoch = self._adapter.current_epoch()
            except Exception as error:
                raise RuntimeError(
                    "revocation authority epoch is unavailable"
                ) from error
            presentation = object.__new__(_OriginalIssuerRevocationPresentation)
            object.__setattr__(presentation, "_adapter", self._adapter)
            object.__setattr__(presentation, "_adapter_epoch", adapter_epoch)
            object.__setattr__(
                presentation,
                "_domain_identity",
                self._domain_identity,
            )
            object.__setattr__(
                presentation,
                "_issued_presentation",
                issued_presentation,
            )
            object.__setattr__(presentation, "_intent", "revoke")
            object.__setattr__(
                presentation,
                "_original_issuer_proof",
                original_issuer_proof,
            )
            object.__setattr__(
                presentation,
                "_provenance_reference",
                provenance_reference,
            )
            object.__setattr__(
                presentation,
                "_session_ticket",
                self._session_ticket,
            )
            self._presentations[id(presentation)] = presentation
            return presentation

    def authenticate_original_issuer_revocation(
        self,
        presented_grant: object,
    ) -> AgentExecutionAuthorizationGrant | None:
        with self._lock:
            if (
                self._closed
                or type(presented_grant)
                is not _OriginalIssuerRevocationPresentation
                or self._presentations.get(id(presented_grant))
                is not presented_grant
                or presented_grant._adapter is not self._adapter
                or presented_grant._domain_identity != self._domain_identity
                or presented_grant._intent != "revoke"
                or presented_grant._session_ticket is not self._session_ticket
                or type(presented_grant._provenance_reference) is not str
                or not presented_grant._provenance_reference
            ):
                return None
            session = self._owned_session
            if session is None:
                return None
            try:
                if (
                    session.identity != self._domain_identity
                    or self._adapter.current_epoch()
                    is not presented_grant._adapter_epoch
                ):
                    return None
            except Exception:
                return None
            issued_presentation = presented_grant._issued_presentation
            original_issuer_proof = presented_grant._original_issuer_proof
            provenance_reference = presented_grant._provenance_reference
            domain_identity = self._domain_identity

        grant = self._latch.authenticate_grant(issued_presentation)
        if type(grant) is not AgentExecutionAuthorizationGrant:
            return None
        try:
            authenticated = (
                self._adapter.validate_authenticated_original_issuer_revocation(
                    original_issuer_proof,
                    grant=grant,
                    domain_identity=domain_identity,
                    intent="revoke",
                    provenance_reference=provenance_reference,
                )
            )
        except Exception:
            return None
        if authenticated is not True:
            return None
        if (
            grant.authorization_domain_id
            != domain_identity.authorization_domain_id
        ):
            return None
        return grant

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._presentations.clear()
            self._owned_session = None
            self._domain_identity = None
            self._session_ticket = None


def _build_native_resolver(
    *,
    runtime_option_id: str,
    environment_id: str,
) -> TrustedAgentOperationToolBindingResolver:
    registration = _make_aeo_native_repository_file_read_registration(
        runtime_option_id,
        environment_id,
    )
    build_result = _build_trusted_agent_operation_tool_registry_snapshot(
        (registration,)
    )
    if (
        build_result.outcome is not _AgentOperationToolRegistryOutcome.RESOLVED
        or type(build_result.snapshot)
        is not _TrustedAgentOperationToolRegistrySnapshot
    ):
        raise RuntimeError("trusted Tool registry snapshot construction failed")
    return TrustedAgentOperationToolBindingResolver(build_result.snapshot)


def _cleanup_components(
    *,
    producer: AgentExecutionAuthorizationGrantProducer | None,
    revocation_port: _OriginalIssuerRevocationPort,
    latch: _GrantAuthenticationLatch,
    session: OwnedAuthorizationDomainSession | None,
) -> list[BaseException]:
    """Attempt every close; Producer.close also closes its paired port."""

    failures: list[BaseException] = []
    actions = (
        producer.close if producer is not None else None,
        revocation_port.close,
        latch.close,
        session.close if session is not None else None,
    )
    for action in actions:
        if action is None:
            continue
        try:
            action()
        except BaseException as error:
            failures.append(error)
    return failures


class LocalOperationalTrustCoordinator(_ProcessLocalCapability):
    """Thin trusted coordinator ending at authoritative local Admission."""

    __slots__ = (
        "_condition",
        "_domain_identity",
        "_latch",
        "_operations",
        "_producer",
        "_revocation_minter",
        "_revocation_port",
        "_session",
        "_state",
        "_thread_operations",
    )

    def _begin_operation(self) -> None:
        thread_id = get_ident()
        with self._condition:
            if self._state != "live":
                raise RuntimeError("Local Operational Trust Coordinator is closed")
            object.__setattr__(self, "_operations", self._operations + 1)
            self._thread_operations[thread_id] = (
                self._thread_operations.get(thread_id, 0) + 1
            )

    def _finish_operation(self) -> None:
        thread_id = get_ident()
        with self._condition:
            count = self._thread_operations.get(thread_id, 0)
            if count <= 1:
                self._thread_operations.pop(thread_id, None)
            else:
                self._thread_operations[thread_id] = count - 1
            object.__setattr__(self, "_operations", self._operations - 1)
            self._condition.notify_all()

    def _produce(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
    ) -> tuple[
        AgentExecutionAuthorizationGrantProductionResult,
        IssuedAgentExecutionAuthorizationGrant | None,
    ]:
        result = self._producer.produce(
            run=run,
            authenticated_principal=authenticated_principal,
            authority_proof=authority_proof,
        )
        if type(result) is not AgentExecutionAuthorizationGrantProductionResult:
            raise RuntimeError("AIO-050 returned a noncanonical production result")
        if result.outcome not in _SUCCESSFUL_PRODUCTION_OUTCOMES:
            return result, None
        if type(result.presentation) is not IssuedAgentExecutionAuthorizationGrant:
            raise RuntimeError("successful AIO-050 result omitted its presentation")
        return result, result.presentation

    def admit(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
    ) -> (
        AgentExecutionAuthorizationGrantProductionResult
        | AgentExecutionDispatchAdmissionStoreResult
    ):
        """Produce under one lease, then admit through a second owned lease."""

        self._begin_operation()
        try:
            production, presentation = self._produce(
                run=run,
                authenticated_principal=authenticated_principal,
                authority_proof=authority_proof,
            )
            if presentation is None:
                return production
            return self._session.admit(presentation)
        finally:
            self._finish_operation()

    def load_authoritative_admission(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
    ) -> (
        AgentExecutionAuthorizationGrantProductionResult
        | AgentExecutionDispatchAdmissionStoreResult
    ):
        """Reauthenticate the same presentation before authoritative lookup."""

        self._begin_operation()
        try:
            production, presentation = self._produce(
                run=run,
                authenticated_principal=authenticated_principal,
                authority_proof=authority_proof,
            )
            if presentation is None:
                return production
            return self._session.load_authoritative_admission(presentation)
        finally:
            self._finish_operation()

    def revoke(
        self,
        *,
        run: AgentExecutionRun,
        authenticated_principal: AuthenticatedIssuerPrincipal,
        authority_proof: AuthenticatedHumanApproval | AuthenticatedPolicyDecision,
        original_issuer_proof: object,
        provenance_reference: str,
    ) -> (
        AgentExecutionAuthorizationGrantProductionResult
        | AgentExecutionDispatchAdmissionStoreResult
    ):
        """Use distinct issuer proof and the exact AIO-050 presentation."""

        self._begin_operation()
        try:
            production, issued_presentation = self._produce(
                run=run,
                authenticated_principal=authenticated_principal,
                authority_proof=authority_proof,
            )
            if issued_presentation is None:
                return production
            revocation_presentation = self._revocation_minter.mint(
                original_issuer_proof=original_issuer_proof,
                issued_presentation=issued_presentation,
                provenance_reference=provenance_reference,
            )
            return self._session.revoke(revocation_presentation)
        finally:
            self._finish_operation()

    def close(self) -> None:
        """Terminally drain operations and attempt every component cleanup."""

        thread_id = get_ident()
        with self._condition:
            if self._thread_operations.get(thread_id, 0):
                raise RuntimeError(
                    "coordinator cannot close from one of its own operations"
                )
            if self._state == "closed":
                return
            if self._state == "closing":
                while self._state != "closed":
                    self._condition.wait()
                return
            object.__setattr__(self, "_state", "closing")
            while self._operations:
                self._condition.wait()

        failures = _cleanup_components(
            producer=self._producer,
            revocation_port=self._revocation_port,
            latch=self._latch,
            session=self._session,
        )
        with self._condition:
            object.__setattr__(self, "_state", "closed")
            self._condition.notify_all()
        if failures:
            raise BaseExceptionGroup(
                "Local Operational Trust Coordinator cleanup failed",
                failures,
            )


def _compose_local_operational_trust_coordinator(
    *,
    authorization_domain_id: str,
    runtime_option_id: str,
    environment_id: str,
    identity_adapter: object,
    human_approval_adapter: object | None,
    policy_decision_adapter: object | None,
    issuer_state_authority: object,
    issuer_entitlement_policy: object,
    lifetime_policy: AgentExecutionAuthorizationGrantLifetimePolicy,
    clock: object,
    grant_id_source: object,
    fresh_prerequisite_source: object,
    execution_mode_resolver: object,
    revocation_adapter: object,
    busy_timeout_ms: int = 5_000,
) -> LocalOperationalTrustCoordinator:
    """Compose one fully bound Coordinator or publish nothing.

    This trusted private entrypoint deliberately exposes no alternate owner,
    Store, resolver, Tool, or authentication-port injection seam.
    """

    resolver = _build_native_resolver(
        runtime_option_id=runtime_option_id,
        environment_id=environment_id,
    )
    latch, bind_composed_port = _new_grant_authentication_latch()
    revocation_port = _OriginalIssuerRevocationPort(
        adapter=revocation_adapter,
        latch=latch,
    )
    session: OwnedAuthorizationDomainSession | None = None
    producer: AgentExecutionAuthorizationGrantProducer | None = None
    try:
        owner = WindowsLocalAuthorizationDomainOwner(
            clock=clock,  # type: ignore[arg-type]
            grant_authentication=latch,
            tool_binding_resolver=resolver,
            fresh_prerequisite_source=fresh_prerequisite_source,  # type: ignore[arg-type]
            execution_mode_resolver=execution_mode_resolver,  # type: ignore[arg-type]
            revocation_authentication=revocation_port,
            busy_timeout_ms=busy_timeout_ms,
        )
        session = owner.acquire(authorization_domain_id)
        domain_identity = session.identity
        if type(domain_identity) is not AuthorizationDomainIdentity:
            raise TypeError("acquired session identity is not canonical")
        binding = _compose_agent_execution_authorization_grant_producer(
            owned_session=session,
            identity_adapter=identity_adapter,  # type: ignore[arg-type]
            human_approval_adapter=human_approval_adapter,  # type: ignore[arg-type]
            policy_decision_adapter=policy_decision_adapter,  # type: ignore[arg-type]
            issuer_state_authority=issuer_state_authority,  # type: ignore[arg-type]
            issuer_entitlement_policy=issuer_entitlement_policy,  # type: ignore[arg-type]
            lifetime_policy=lifetime_policy,
            utc_clock=clock,  # type: ignore[arg-type]
            grant_id_source=grant_id_source,  # type: ignore[arg-type]
        )
        if type(binding) is not _AgentExecutionAuthorizationGrantProducerBinding:
            raise RuntimeError("AIO-050 returned a noncanonical binding")
        bound_producer = binding.producer
        if type(bound_producer) is not AgentExecutionAuthorizationGrantProducer:
            raise RuntimeError("AIO-050 returned a noncanonical Producer")
        producer = bound_producer
        if (
            type(binding.grant_authentication)
            is not _AgentExecutionAuthorizationGrantAuthenticationPort
            or session.identity != domain_identity
        ):
            raise RuntimeError(
                "AIO-050 composition did not preserve the exact owned session"
            )
        bind_composed_port(binding.grant_authentication)
        revocation_minter = revocation_port.bind_session(session)
        coordinator = object.__new__(LocalOperationalTrustCoordinator)
        object.__setattr__(coordinator, "_condition", Condition(RLock()))
        object.__setattr__(coordinator, "_domain_identity", domain_identity)
        object.__setattr__(coordinator, "_latch", latch)
        object.__setattr__(coordinator, "_operations", 0)
        object.__setattr__(coordinator, "_producer", producer)
        object.__setattr__(coordinator, "_revocation_minter", revocation_minter)
        object.__setattr__(coordinator, "_revocation_port", revocation_port)
        object.__setattr__(coordinator, "_session", session)
        object.__setattr__(coordinator, "_state", "live")
        object.__setattr__(coordinator, "_thread_operations", {})
        return coordinator
    except BaseException as primary_error:
        latch.fail()
        cleanup_errors = _cleanup_components(
            producer=producer,
            revocation_port=revocation_port,
            latch=latch,
            session=session,
        )
        if cleanup_errors:
            raise BaseExceptionGroup(
                "Local Operational Trust composition and cleanup failed",
                [primary_error, *cleanup_errors],
            ) from primary_error
        raise
