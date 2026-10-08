"""Private AIO-056 local ownership composition; no launch or invocation API.

The canonical AIO-049 session supplies operation entry/exit and file pinning.
This adapter adds logical executor incarnations without changing that session.
Private IDs and returned history are not transferable credentials.
"""

from __future__ import annotations

import os
import secrets
import threading

from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainOwnershipError, AuthorizationDomainOwnershipIntegrityError,
    OwnedAuthorizationDomainSessionClosedError,
)
from engineering_orchestration.sqlite_agent_execution_dispatch_admission_store import (
    SqliteAgentExecutionDispatchAdmissionStore, _DispatchClaim, _DispatchRenewal,
    _DispatchResult, _dispatch_result, _dispatch_token, _mint_dispatch_request,
    _parse_decision_time,
    SqliteAdmissionStoreIntegrityError,
)
from engineering_orchestration.windows_local_authorization_domain_owner import (
    _WindowsOwnedAuthorizationDomainSession,
)


_EXECUTOR_AUTHORITY = object()
_FACADE_AUTHORITY = object()


def _validate_owned_dispatch_context(session, store):
    if type(session) is not _WindowsOwnedAuthorizationDomainSession:
        raise ValueError("Dispatch composition requires the genuine local owned session")
    if session._state != "live":
        raise OwnedAuthorizationDomainSessionClosedError("Dispatch session is no longer live")
    if (store is not session._store or type(store) is not SqliteAgentExecutionDispatchAdmissionStore
            or (store.configuration.authorization_domain_id, store.configuration.ledger_instance_id,
                store.configuration.domain_generation) != (
                    session.identity.authorization_domain_id, session.identity.ledger_instance_id,
                    session.identity.domain_generation)):
        raise AuthorizationDomainOwnershipIntegrityError("Dispatch Store/session binding disagrees")
    if session._thread_operations.get(threading.get_ident(), 0) <= 0:
        raise ValueError("Dispatch access requires a complete active canonical operation lease")


class _ExecutorCapability:
    __slots__ = ("_session", "_pid", "_executor_id", "_authority")

    def __new__(cls):
        raise TypeError("Executor incarnations are privately minted")

    def __setattr__(self, name, value):
        raise TypeError("Executor incarnations are immutable")

    def __copy__(self):
        raise TypeError("Executor incarnations cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Executor incarnations cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Executor incarnations cannot be serialized")

    @property
    def executor_instance_id(self):
        return _validate_executor(self, self._session)


def _validate_executor(capability, session):
    if (type(capability) is not _ExecutorCapability
            or getattr(capability, "_authority", None) is not _EXECUTOR_AUTHORITY
            or capability._session is not session or capability._pid != os.getpid()):
        raise ValueError("executor capability is counterfeit, rebound or from another process")
    if type(session) is not _WindowsOwnedAuthorizationDomainSession or session._state != "live":
        raise ValueError("executor's original owned session is no longer live")
    return _dispatch_token(capability._executor_id)


def _checked_result(result, request):
    """Validate operation-specific shapes before the owned lease may disclose."""
    common = {
        "invalid_input", "ownership_lost", "storage_busy", "storage_unavailable",
        "incompatible_schema", "integrity_failure", "clock_failure", "clock_regression", "commit_unknown",
    }
    allowed = {
        "claim": {"newly_claimed", "existing_claim_history", "claim_identity_conflict", "empty",
                  "authority_ineligible", "temporarily_unavailable", "generation_exhausted"},
        "renew": {"newly_renewed", "existing_renewal_history", "renewal_identity_conflict",
                  "claim_identity_conflict", "claim_not_found", "stale_generation", "revoked",
                  "expired_claim", "nonextending", "sequence_exhausted"},
        "query": ({"claim_history", "claim_not_found"} if request.mode == "history" else
                  {"current_claim", "claim_not_found", "claim_identity_conflict", "stale_generation",
                   "revoked", "expired_claim"}),
    }[request.operation] | common
    if (type(result) is not _DispatchResult or type(result.outcome) is not str
            or result.outcome not in allowed or type(result.retry) is not str
            or result.retry != _dispatch_result(result.outcome).retry
            or type(result.history_only) is not bool or type(result.renewals) is not tuple
            or type(result.detail) is not str):
        raise ValueError("incoherent private Dispatch result")
    expects_claim = result.outcome in ("newly_claimed", "existing_claim_history", "claim_history", "current_claim")
    expects_renewal = result.outcome in ("newly_renewed", "existing_renewal_history")
    if (expects_claim != (type(result.claim) is _DispatchClaim)
            or expects_renewal != (type(result.renewal) is _DispatchRenewal)
            or (not expects_claim and result.claim is not None)
            or (not expects_renewal and result.renewal is not None)
            or result.history_only != (result.outcome in (
                "existing_claim_history", "existing_renewal_history", "claim_history"))
            or (result.outcome != "claim_history" and result.renewals)
            or (result.outcome != "current_claim" and result.effective_lease_until is not None)):
        raise ValueError("Dispatch evidence shape disagrees with operation outcome")
    if expects_claim:
        claim = result.claim
        row = dict(zip(("claim_id", "executor_instance_id", "lease_generation", "acquired_at",
                        "acquired_at_key", "lease_until", "lease_until_key"),
                       (claim.claim_id, claim.executor_instance_id, claim.lease_generation, claim.acquired_at,
                        claim.acquired_at_key, claim.lease_until, claim.lease_until_key)))
        row.update(zip(("authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"), claim.identity))
        if SqliteAgentExecutionDispatchAdmissionStore._dispatch_claim_from_row(row) != claim:
            raise ValueError("malformed Claim evidence")
        if claim.claim_id != request.claim_id:
            raise ValueError("Claim evidence rebound")
        if request.mode != "history" and claim.executor_instance_id != request.capability.executor_instance_id:
            raise ValueError("Claim evidence has a different executor")
        if result.outcome == "current_claim":
            if (claim.identity, claim.lease_generation) != (request.identity, request.generation):
                raise ValueError("current Claim evidence has a different subject")
            _, effective = _parse_decision_time(result.effective_lease_until)
            if effective < claim.lease_until_key:
                raise ValueError("effective Claim evidence regresses")
        prior_time, prior_expiry = claim.acquired_at_key, claim.lease_until_key
        for sequence, renewal in enumerate(result.renewals, 1):
            if (type(renewal) is not _DispatchRenewal or renewal.claim_id != claim.claim_id
                    or (renewal.identity, renewal.executor_instance_id, renewal.lease_generation)
                    != (claim.identity, claim.executor_instance_id, claim.lease_generation)):
                raise ValueError("Claim history includes another Renewal subject")
            row = {field: getattr(renewal, field) for field in (
                "renewal_id", "claim_id", "executor_instance_id", "lease_generation", "renewal_sequence",
                "renewed_at", "renewed_at_key", "lease_until", "lease_until_key")}
            row.update(zip(("authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"), renewal.identity))
            if (SqliteAgentExecutionDispatchAdmissionStore._dispatch_renewal_from_row(row) != renewal
                    or renewal.renewal_sequence != sequence
                    or not prior_time <= renewal.renewed_at_key < prior_expiry
                    or renewal.lease_until_key <= prior_expiry):
                raise ValueError("malformed or unordered Renewal history evidence")
            prior_time, prior_expiry = renewal.renewed_at_key, renewal.lease_until_key
    if expects_renewal:
        renewal = result.renewal
        row = {field: getattr(renewal, field) for field in (
            "renewal_id", "claim_id", "executor_instance_id", "lease_generation", "renewal_sequence",
            "renewed_at", "renewed_at_key", "lease_until", "lease_until_key")}
        row.update(zip(("authorization_domain_id", "issuer_kind", "issuer_id", "grant_id"), renewal.identity))
        if SqliteAgentExecutionDispatchAdmissionStore._dispatch_renewal_from_row(row) != renewal:
            raise ValueError("malformed Renewal evidence")
        if (renewal.renewal_id, renewal.claim_id, renewal.identity, renewal.executor_instance_id,
            renewal.lease_generation) != (request.renewal_id, request.claim_id, request.identity,
                                         request.capability.executor_instance_id, request.generation):
            raise ValueError("Renewal evidence rebound")
    return result


class _OwnedDispatchClaimLease:
    __slots__ = ("_session", "_store", "_executor", "_authority")

    def __new__(cls):
        raise TypeError("Dispatch facades are privately composed")

    def __setattr__(self, name, value):
        raise TypeError("Dispatch facades are immutable")

    def __copy__(self):
        raise TypeError("Dispatch facades cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("Dispatch facades cannot be copied")

    def __reduce_ex__(self, protocol):
        raise TypeError("Dispatch facades cannot be serialized")

    @property
    def executor_instance_id(self):
        return self._executor.executor_instance_id

    def _run(self, operation, **values):
        try:
            if getattr(self, "_authority", None) is not _FACADE_AUTHORITY:
                return _dispatch_result("invalid_input")
            with self._session.operation():
                _validate_owned_dispatch_context(self._session, self._store)
                capability = None if values.get("mode") == "history" else self._executor
                request = _mint_dispatch_request(operation, self._session, self._store,
                                                  capability=capability, **values)
                method = {"claim": self._store._claim_dispatch_intent,
                          "renew": self._store._renew_dispatch_claim,
                          "query": self._store._query_dispatch_claim}[operation]
                result = _checked_result(method(request), request)
            # __exit__ must finish successfully before any result is disclosed.
            return result
        except AuthorizationDomainOwnershipError:
            return _dispatch_result("ownership_lost", detail="same-ledger history reconciliation required; no current evidence")
        except (ValueError, TypeError, AttributeError, SqliteAdmissionStoreIntegrityError):
            return _dispatch_result("integrity_failure", detail="owned Dispatch composition or result failed closed")

    def claim(self, claim_id):
        return self._run("claim", claim_id=claim_id)

    def renew(self, renewal_id, identity, claim_id, lease_generation):
        return self._run("renew", renewal_id=renewal_id, identity=identity,
                         claim_id=claim_id, generation=lease_generation)

    def query(self, claim_id, *, mode="history", identity=None, lease_generation=None):
        return self._run("query", claim_id=claim_id, mode=mode,
                         identity=identity, generation=lease_generation)


def _create_owned_dispatch_claim_lease(session):
    """Create a new logical incarnation; accepts no Store, ID, path or override."""
    if type(session) is not _WindowsOwnedAuthorizationDomainSession:
        raise TypeError("only a genuine canonical local session can compose Dispatch")
    with session.operation():
        store = session._store
        _validate_owned_dispatch_context(session, store)
        executor = object.__new__(_ExecutorCapability)
        for name, value in (("_session", session), ("_pid", os.getpid()),
                            ("_executor_id", secrets.token_hex(32)), ("_authority", _EXECUTOR_AUTHORITY)):
            object.__setattr__(executor, name, value)
        facade = object.__new__(_OwnedDispatchClaimLease)
        for name, value in (("_session", session), ("_store", store), ("_executor", executor),
                            ("_authority", _FACADE_AUTHORITY)):
            object.__setattr__(facade, name, value)
    return facade
