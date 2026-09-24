"""Focused provider-neutral AIO-049 ownership-contract tests."""

from __future__ import annotations

import ast
import copy
from dataclasses import FrozenInstanceError
from inspect import signature
from pathlib import Path
import pickle
import unittest

import engineering_orchestration.authorization_domain_ownership as subject
from engineering_orchestration.authorization_domain_ownership import (
    AuthorizationDomainAlreadyOwnedError,
    AuthorizationDomainIdentity,
    AuthorizationDomainOperationLease,
    AuthorizationDomainOwnershipAuthority,
    AuthorizationDomainOwnershipError,
    AuthorizationDomainOwnershipIntegrityError,
    AuthorizationDomainOwnershipStateError,
    AuthorizationDomainOwnershipUnavailableError,
    AuthorizationDomainOwnershipUnsupportedError,
    OwnedAuthorizationDomainSession,
    OwnedAuthorizationDomainSessionClosedError,
    OwnedAuthorizationDomainSessionError,
    OwnedAuthorizationDomainSessionLostError,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "engineering_orchestration"
    / "authorization_domain_ownership.py"
)
IDENTITY = AuthorizationDomainIdentity(
    authorization_domain_id="authorization-domain::synthetic",
    ledger_instance_id="ledger-instance::synthetic",
    domain_generation=7,
)


class _SyntheticOperationLease:
    def __init__(self, identity: AuthorizationDomainIdentity) -> None:
        self._identity = identity
        self.entered = False
        self.exited = False

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return self._identity

    def __enter__(self) -> _SyntheticOperationLease:
        self.entered = True
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object | None,
    ) -> None:
        del exception_type, exception, traceback
        self.exited = True


class _SyntheticOwnedSession(OwnedAuthorizationDomainSession):
    __slots__ = ("_identity", "closed", "fenced")

    def __init__(self, identity: AuthorizationDomainIdentity) -> None:
        self._identity = identity
        self.closed = False
        self.fenced = False

    @property
    def identity(self) -> AuthorizationDomainIdentity:
        return self._identity

    def operation(self) -> AuthorizationDomainOperationLease:
        return _SyntheticOperationLease(self._identity)

    def admit(self, presented_grant: object) -> object:  # type: ignore[override]
        return presented_grant

    def load_authoritative_admission(
        self,
        presented_grant: object,
    ) -> object:  # type: ignore[override]
        return presented_grant

    def revoke(self, presented_grant: object) -> object:  # type: ignore[override]
        return presented_grant

    def close(self) -> None:
        self.closed = True

    def fence(self) -> None:
        self.fenced = True
        self.closed = True


class _SyntheticAuthority:
    def __init__(self, session: OwnedAuthorizationDomainSession) -> None:
        self._session = session

    def acquire(
        self,
        authorization_domain_id: str,
    ) -> OwnedAuthorizationDomainSession:
        if authorization_domain_id != self._session.identity.authorization_domain_id:
            raise AuthorizationDomainOwnershipStateError("unknown domain")
        return self._session


class AuthorizationDomainIdentityTests(unittest.TestCase):
    def test_identity_is_exact_frozen_hashable_value(self) -> None:
        equal = AuthorizationDomainIdentity(
            authorization_domain_id=IDENTITY.authorization_domain_id,
            ledger_instance_id=IDENTITY.ledger_instance_id,
            domain_generation=IDENTITY.domain_generation,
        )

        self.assertEqual(equal, IDENTITY)
        self.assertEqual(hash(equal), hash(IDENTITY))
        with self.assertRaises(FrozenInstanceError):
            IDENTITY.domain_generation = 8  # type: ignore[misc]

    def test_identity_rejects_non_exact_or_empty_strings(self) -> None:
        class StringSubclass(str):
            pass

        for field_name in ("authorization_domain_id", "ledger_instance_id"):
            with self.subTest(field_name=field_name, value=None):
                values = {
                    "authorization_domain_id": "domain",
                    "ledger_instance_id": "ledger",
                    "domain_generation": 1,
                }
                values[field_name] = None
                with self.assertRaises(TypeError):
                    AuthorizationDomainIdentity(**values)  # type: ignore[arg-type]
            with self.subTest(field_name=field_name, value=""):
                values = {
                    "authorization_domain_id": "domain",
                    "ledger_instance_id": "ledger",
                    "domain_generation": 1,
                }
                values[field_name] = ""
                with self.assertRaises(ValueError):
                    AuthorizationDomainIdentity(**values)  # type: ignore[arg-type]
            with self.subTest(field_name=field_name, value="subclass"):
                values = {
                    "authorization_domain_id": "domain",
                    "ledger_instance_id": "ledger",
                    "domain_generation": 1,
                }
                values[field_name] = StringSubclass("synthetic")
                with self.assertRaises(TypeError):
                    AuthorizationDomainIdentity(**values)  # type: ignore[arg-type]

    def test_identity_requires_positive_exact_integer_generation(self) -> None:
        for generation in (True, 1.0, "1", None):
            with self.subTest(generation=generation):
                with self.assertRaises(TypeError):
                    AuthorizationDomainIdentity(
                        "domain",
                        "ledger",
                        generation,  # type: ignore[arg-type]
                    )
        for generation in (0, -1):
            with self.subTest(generation=generation):
                with self.assertRaises(ValueError):
                    AuthorizationDomainIdentity("domain", "ledger", generation)


class AuthorizationDomainOwnershipProtocolTests(unittest.TestCase):
    def test_session_base_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            OwnedAuthorizationDomainSession()  # type: ignore[abstract]

    def test_structural_authority_and_operation_lease_protocols(self) -> None:
        session = _SyntheticOwnedSession(IDENTITY)
        authority = _SyntheticAuthority(session)
        lease = session.operation()

        self.assertIsInstance(authority, AuthorizationDomainOwnershipAuthority)
        self.assertIsInstance(lease, AuthorizationDomainOperationLease)
        self.assertIs(authority.acquire(IDENTITY.authorization_domain_id), session)
        with lease as entered:
            self.assertIs(entered, lease)
            self.assertEqual(entered.identity, IDENTITY)
        self.assertTrue(lease.entered)  # type: ignore[attr-defined]
        self.assertTrue(lease.exited)  # type: ignore[attr-defined]

    def test_authority_acquisition_selector_is_domain_only(self) -> None:
        parameters = tuple(
            signature(AuthorizationDomainOwnershipAuthority.acquire).parameters
        )

        self.assertEqual(parameters, ("self", "authorization_domain_id"))

    def test_session_base_denies_copy_and_serialization(self) -> None:
        session = _SyntheticOwnedSession(IDENTITY)

        with self.assertRaises(TypeError):
            copy.copy(session)
        with self.assertRaises(TypeError):
            copy.deepcopy(session)
        with self.assertRaises(TypeError):
            pickle.dumps(session)

    def test_session_surface_includes_owned_operations_and_terminal_actions(
        self,
    ) -> None:
        expected = {
            "identity",
            "operation",
            "admit",
            "load_authoritative_admission",
            "revoke",
            "close",
            "fence",
        }

        self.assertTrue(expected.issubset(vars(OwnedAuthorizationDomainSession)))


class AuthorizationDomainOwnershipErrorTests(unittest.TestCase):
    def test_typed_errors_share_one_fail_closed_base(self) -> None:
        error_types = (
            AuthorizationDomainAlreadyOwnedError,
            AuthorizationDomainOwnershipUnavailableError,
            AuthorizationDomainOwnershipUnsupportedError,
            AuthorizationDomainOwnershipIntegrityError,
            AuthorizationDomainOwnershipStateError,
            OwnedAuthorizationDomainSessionError,
            OwnedAuthorizationDomainSessionClosedError,
            OwnedAuthorizationDomainSessionLostError,
        )

        for error_type in error_types:
            with self.subTest(error_type=error_type.__name__):
                self.assertTrue(
                    issubclass(error_type, AuthorizationDomainOwnershipError)
                )

        self.assertTrue(
            issubclass(
                OwnedAuthorizationDomainSessionClosedError,
                OwnedAuthorizationDomainSessionError,
            )
        )
        self.assertTrue(
            issubclass(
                OwnedAuthorizationDomainSessionLostError,
                OwnedAuthorizationDomainSessionError,
            )
        )


class AuthorizationDomainOwnershipSeparationTests(unittest.TestCase):
    def test_provider_neutral_module_has_no_platform_or_backend_import(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".")[0])

        self.assertTrue(
            imported_roots.isdisjoint(
                {"ctypes", "msvcrt", "os", "pathlib", "sqlite3", "win32api"}
            )
        )

    def test_no_public_binding_or_serialized_capability_type_exists(self) -> None:
        self.assertFalse(hasattr(subject, "LocalAuthorizationDomainBinding"))
        self.assertFalse(hasattr(subject, "AuthorizationDomainOwnershipCapability"))


if __name__ == "__main__":
    unittest.main()
