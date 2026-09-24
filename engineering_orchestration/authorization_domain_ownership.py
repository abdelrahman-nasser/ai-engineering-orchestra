"""Provider-neutral authorization-domain ownership contracts.

The live ``OwnedAuthorizationDomainSession`` supplied by a conforming adapter
is the operational capability.  Neither an ``AuthorizationDomainIdentity`` nor
any persisted binding, flag, process identifier, or caller assertion proves
ownership by itself.  Provider-specific locking, storage, and file-identity
mechanisms intentionally live outside this module.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import TracebackType
from typing import TYPE_CHECKING, NoReturn, Protocol, Self, runtime_checkable

if TYPE_CHECKING:
    from engineering_orchestration.agent_execution_dispatch_admission_store import (
        AgentExecutionDispatchAdmissionStoreResult,
    )


__all__ = (
    "AuthorizationDomainAlreadyOwnedError",
    "AuthorizationDomainIdentity",
    "AuthorizationDomainOperationLease",
    "AuthorizationDomainOwnershipAuthority",
    "AuthorizationDomainOwnershipError",
    "AuthorizationDomainOwnershipIntegrityError",
    "AuthorizationDomainOwnershipStateError",
    "AuthorizationDomainOwnershipUnavailableError",
    "AuthorizationDomainOwnershipUnsupportedError",
    "OwnedAuthorizationDomainSession",
    "OwnedAuthorizationDomainSessionClosedError",
    "OwnedAuthorizationDomainSessionError",
    "OwnedAuthorizationDomainSessionLostError",
)


@dataclass(frozen=True, slots=True)
class AuthorizationDomainIdentity:
    """Immutable identity shared by an owner and its authoritative ledger.

    This value is descriptive evidence used for exact binding checks.  It is
    deliberately not a serializable bearer capability and does not establish
    live ownership when copied or reconstructed.
    """

    authorization_domain_id: str
    ledger_instance_id: str
    domain_generation: int

    def __post_init__(self) -> None:
        if type(self.authorization_domain_id) is not str:
            raise TypeError(
                "authorization_domain_id must be an exact string"
            )
        if not self.authorization_domain_id:
            raise ValueError("authorization_domain_id must be nonempty")
        if type(self.ledger_instance_id) is not str:
            raise TypeError("ledger_instance_id must be an exact string")
        if not self.ledger_instance_id:
            raise ValueError("ledger_instance_id must be nonempty")
        if type(self.domain_generation) is not int:
            raise TypeError("domain_generation must be an exact integer")
        if self.domain_generation <= 0:
            raise ValueError("domain_generation must be positive")


class AuthorizationDomainOwnershipError(RuntimeError):
    """Base fail-closed authorization-domain ownership error."""


class AuthorizationDomainAlreadyOwnedError(AuthorizationDomainOwnershipError):
    """Another conforming owner already holds the exact domain."""


class AuthorizationDomainOwnershipUnavailableError(
    AuthorizationDomainOwnershipError
):
    """Required ownership evidence or infrastructure is unavailable."""


class AuthorizationDomainOwnershipUnsupportedError(
    AuthorizationDomainOwnershipError
):
    """The requested platform or storage profile is unsupported."""


class AuthorizationDomainOwnershipIntegrityError(
    AuthorizationDomainOwnershipError
):
    """Binding, identity, durable state, or integrity evidence disagrees."""


class AuthorizationDomainOwnershipStateError(AuthorizationDomainOwnershipError):
    """The domain is not in the state required by the requested operation."""


class OwnedAuthorizationDomainSessionError(AuthorizationDomainOwnershipError):
    """Base error for an unusable live ownership session."""


class OwnedAuthorizationDomainSessionClosedError(
    OwnedAuthorizationDomainSessionError
):
    """The session was irreversibly closed or a terminal transition began."""


class OwnedAuthorizationDomainSessionLostError(
    OwnedAuthorizationDomainSessionError
):
    """The session can no longer prove its complete live authority."""


@runtime_checkable
class AuthorizationDomainOperationLease(Protocol):
    """One non-transferable lease covering a complete coordinator operation.

    A conforming lease validates session authority when entered, retains the
    lifecycle gate until exit, and exposes the same immutable identity as its
    parent session.  The adapter must revalidate authority before and after the
    complete operation; the lease is not a distributed or durable lease.
    """

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        """Return the exact identity fixed for the parent session."""

    def __enter__(self) -> Self:
        """Enter the operation only while complete authority remains live."""

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Revalidate and release the lifecycle gate without hiding failures."""


class OwnedAuthorizationDomainSession(ABC):
    """Live process-local capability for one exact authorization domain.

    Conforming adapters alone create concrete sessions.  Each operational
    method must hold one fresh ``operation()`` lease across the complete
    coordinator call.  Closing or beginning fencing first prevents new leases,
    waits for active operations to quiesce, and makes the object permanently
    unusable.  Failure after fencing begins must never reopen the session.

    This abstract boundary deters accidental composition bypass; it is not a
    sandbox against arbitrary code already executing in the trusted process.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def identity(self) -> AuthorizationDomainIdentity:
        """Return the session's immutable domain/ledger/generation identity."""

    @abstractmethod
    def operation(self) -> AuthorizationDomainOperationLease:
        """Return a fresh lease for exactly one complete coordinator call."""

    @abstractmethod
    def admit(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Run the complete owned Admission operation under one lease."""

    @abstractmethod
    def load_authoritative_admission(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Run the complete owned authoritative-load operation under one lease."""

    @abstractmethod
    def revoke(
        self,
        presented_grant: object,
    ) -> AgentExecutionDispatchAdmissionStoreResult:
        """Run the complete owned revocation operation under one lease."""

    @abstractmethod
    def close(self) -> None:
        """Quiesce operations and irreversibly release the live capability."""

    @abstractmethod
    def fence(self) -> None:
        """Quiesce operations and drive the bound domain terminally forward.

        Once fencing begins, the session remains permanently unusable even if
        the provider reports an ambiguous or failed durable transition.
        """

    def __copy__(self) -> NoReturn:
        raise TypeError("Owned Authorization Domain Sessions cannot be copied")

    def __deepcopy__(self, memo: dict[int, object]) -> NoReturn:
        del memo
        raise TypeError(
            "Owned Authorization Domain Sessions cannot be deep-copied"
        )

    def __reduce__(self) -> NoReturn:
        raise TypeError(
            "Owned Authorization Domain Sessions cannot be serialized"
        )

    def __reduce_ex__(self, protocol: int) -> NoReturn:
        del protocol
        raise TypeError(
            "Owned Authorization Domain Sessions cannot be serialized"
        )

    def __getstate__(self) -> NoReturn:
        raise TypeError(
            "Owned Authorization Domain Sessions cannot be serialized"
        )


@runtime_checkable
class AuthorizationDomainOwnershipAuthority(Protocol):
    """Provider-neutral acquisition boundary for live domain ownership.

    Trusted coordinator dependencies belong to trusted adapter composition.
    The only ownership selector accepted here is the exact domain identifier;
    paths, ledger identities, generations, states, process identifiers, and
    ownership booleans must be derived from and checked against trusted state.
    """

    def acquire(
        self,
        authorization_domain_id: str,
    ) -> OwnedAuthorizationDomainSession:
        """Acquire and fully validate one exact active domain or fail closed."""
